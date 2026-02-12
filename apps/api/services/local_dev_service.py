import os
import json
import subprocess
import tempfile
import shutil
import threading
import time
import socket
from typing import List, Dict, Optional
from utils.logger import Logger
from pathlib import Path

logger = Logger(__name__)

class LocalDevService:
    def __init__(self):
        self.base_path = "C:/Users/alija/tests"
        self.current_server = None  
        self.PORT = 4000  # FIXED PORT ALWAYS!
        logger.step("Local Dev Service", f"initialized at {self.base_path}")
        
        os.makedirs(self.base_path, exist_ok=True)
    
    def save_files_locally(self, app_id: str, files: List[Dict[str, str]]) -> str:
        """Save all files to local folder"""
        try:
            app_folder = os.path.join(self.base_path, app_id)
            
            if os.path.exists(app_folder):
                shutil.rmtree(app_folder)
            
            os.makedirs(app_folder, exist_ok=True)
            
            file_count = 0
            for file in files:
                file_path = os.path.join(app_folder, file["path"])
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file["content"])
                
                file_count += 1
            
            logger.success(f"✅ Saved {file_count} files to {app_folder}")
            return app_folder
            
        except Exception as e:
            logger.error(f"❌ Failed to save files: {str(e)}")
            return ""
    
    def start_local_server(self, app_folder: str) -> Optional[str]:
        """Build React app and serve it on PORT 4000 ONLY"""
        try:
            # 1. STOP CURRENT SERVER (if any)
            self._stop_current_server()
            
            logger.info(f"📦 Building React app for {os.path.basename(app_folder)}...")
            
            # 2. Save current directory
            original_dir = os.getcwd()
            
            try:
                # 3. Build the React app
                os.chdir(app_folder)
                
                if not os.path.exists("package.json"):
                    logger.error("❌ No package.json found")
                    os.chdir(original_dir)
                    return None
                
                # Install dependencies
                logger.info("Installing npm dependencies...")
                try:
                    subprocess.run(
                        ["npm", "install", "--silent"],
                        capture_output=True,
                        timeout=180,
                        shell=True,
                        check=False
                    )
                except subprocess.TimeoutExpired:
                    logger.warning("⚠️ npm install timeout, continuing anyway")
                
                # Build the app
                logger.info("Building React app...")
                result = subprocess.run(
                    ["npm", "run", "build", "--silent"],
                    capture_output=True,
                    text=True,
                    timeout=180,
                    shell=True
                )
                
                if result.returncode != 0:
                    logger.error(f"❌ Build failed: {result.stderr[:300]}")
                    os.chdir(original_dir)
                    return None
                
                logger.success("✅ React app built successfully")
                
                # 4. Check if dist folder exists
                dist_dir = os.path.join(app_folder, "dist")
                if not os.path.exists(dist_dir):
                    logger.error("❌ No dist folder after build")
                    os.chdir(original_dir)
                    return None
                
                os.chdir(dist_dir)
                
                # 5. MAKE SURE PORT 4000 IS FREE
                self._kill_process_on_port(self.PORT)
                
                # 6. Start HTTP server on PORT 4000
                import http.server
                import socketserver
                
                handler = http.server.SimpleHTTPRequestHandler
                
                # Allow reuse of address
                socketserver.TCPServer.allow_reuse_address = True
                
                try:
                    httpd = socketserver.TCPServer(("", self.PORT), handler)
                except OSError as e:
                    logger.error(f"❌ Port {self.PORT} is busy, trying to kill process...")
                    self._kill_process_on_port(self.PORT)
                    time.sleep(1)
                    httpd = socketserver.TCPServer(("", self.PORT), handler)
                
                server_thread = threading.Thread(
                    target=httpd.serve_forever,
                    daemon=True
                )
                server_thread.start()
                
                url = f"http://localhost:{self.PORT}"
                
                # 7. Track this server
                self.current_server = {
                    "httpd": httpd,
                    "url": url,
                    "thread": server_thread,
                    "folder": app_folder,
                    "original_dir": original_dir
                }
                
                logger.success(f"🌐 Server started on PORT {self.PORT}: {url}")
                
                # 8. Test the server
                time.sleep(2)
                try:
                    import urllib.request
                    response = urllib.request.urlopen(url, timeout=5)
                    if response.status == 200:
                        logger.success(f"✅ Server responding at {url}")
                except Exception as test_err:
                    logger.warning(f"⚠️ Server started but test failed: {test_err}")
                
                return url
                
            except Exception as e:
                os.chdir(original_dir)
                raise e
                
        except Exception as e:
            logger.error(f"❌ Server start failed: {str(e)}")
            return None
    
    def _stop_current_server(self):
        """Stop the currently running server"""
        if self.current_server:
            try:
                self.current_server["httpd"].shutdown()
                os.chdir(self.current_server["original_dir"])
                logger.info("✅ Stopped previous server")
            except Exception as e:
                logger.debug(f"Error stopping server: {str(e)}")
            finally:
                self.current_server = None
    
    def _kill_process_on_port(self, port: int):
        """Kill any process using our port (4000 only)"""
        try:
            import psutil
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    for conn in proc.connections(kind='inet'):
                        if hasattr(conn, 'laddr') and conn.laddr:
                            if conn.laddr.port == port:  # ONLY port 4000
                                proc_name = proc.info['name'].lower()
                                if 'python' in proc_name or 'http' in proc_name:
                                    logger.info(f"Killing process on port {port}")
                                    proc.terminate()
                                    time.sleep(0.5)
                                    break
                except:
                    continue
                    
        except ImportError:
            pass  # psutil not installed
        except Exception:
            pass
    
    def cleanup(self):
        """Clean up when shutting down"""
        self._stop_current_server()
        logger.info("🧹 Cleaned up local server")

# Singleton instance
local_dev_service = LocalDevService()