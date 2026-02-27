# apps/api/services/validation_service.py

import asyncio
import os
import subprocess
import time
import sys
from pathlib import Path
from playwright.async_api import async_playwright
from utils.logger import Logger

logger = Logger(__name__)

class ValidationService:
    async def validate_app(self, app_folder: str, timeout_ms: int = 10000) -> dict:
        """
        Build the app, serve it, and capture console errors using Playwright.
        Returns: {"success": bool, "errors": list of error strings, "logs": list of console logs}
        """
        try:
            # 1. Build the app (npm run build) – already done in builder node, so we skip rebuild
            # But we still need the dist folder path.
            dist_path = Path(app_folder) / "dist"
            if not dist_path.exists():
                return {
                    "success": False,
                    "errors": ["dist folder not found after build"],
                    "logs": []
                }

            # 2. Start a static server – try Python first, then fallback to npx serve
            server_process, server_port = await self._start_server(dist_path)
            if server_process is None:
                return {
                    "success": False,
                    "errors": ["Could not start any static server (tried python -m http.server and npx serve)"],
                    "logs": []
                }

            # 3. Use Playwright to open the page and capture errors
            errors = []
            logs = []
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()

                page.on("console", lambda msg: logs.append(msg.text))
                page.on("pageerror", lambda exc: errors.append(str(exc)))

                try:
                    await page.goto(f"http://localhost:{server_port}", timeout=timeout_ms)
                    # Wait a bit for any async errors
                    await asyncio.sleep(2)
                except Exception as e:
                    errors.append(f"Page load error: {str(e)}")
                finally:
                    await browser.close()

            # 4. Clean up server
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

            return {
                "success": len(errors) == 0,
                "errors": errors,
                "logs": logs
            }

        except Exception as e:
            logger.error(f"Validation service error: {str(e)}")
            return {
                "success": False,
                "errors": [f"Validation service crashed: {str(e)}"],
                "logs": []
            }

    async def _start_server(self, directory: Path, preferred_port: int = 8001):
        """Try to start a static HTTP server. Returns (process, port) or (None, None)."""
        # Try Python's http.server first
        try:
            proc = subprocess.Popen(
                [sys.executable, "-m", "http.server", str(preferred_port)],
                cwd=str(directory),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # Give it a moment to bind
            await asyncio.sleep(1)
            # Check if process is still running (i.e., didn't crash)
            if proc.poll() is None:
                logger.info(f"Started Python HTTP server on port {preferred_port}")
                return proc, preferred_port
            else:
                logger.warning("Python HTTP server failed to start")
        except FileNotFoundError:
            logger.warning("Python not found, trying npx serve...")
        except Exception as e:
            logger.warning(f"Python server attempt failed: {e}")

        # Fallback to npx serve
        try:
            # serve often uses port 3000 by default, but we can specify
            proc = subprocess.Popen(
                ["npx", "serve", "-l", str(preferred_port)],
                cwd=str(directory),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL 
            )
            await asyncio.sleep(2)  # serve might take a bit longer
            if proc.poll() is None:
                logger.info(f"Started npx serve on port {preferred_port}")
                return proc, preferred_port
            else:
                logger.error("npx serve failed to start")
        except FileNotFoundError:
            logger.error("npx not found – is Node.js installed and in PATH?")
        except Exception as e:
            logger.error(f"npx serve attempt failed: {e}")

        return None, None

# Singleton instance
validation_service = ValidationService()