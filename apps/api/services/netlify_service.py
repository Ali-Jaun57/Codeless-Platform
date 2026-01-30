
import os
import subprocess
import tempfile
import requests
from typing import List, Dict, Optional
from config import Config
from utils.logger import Logger
import zipfile
import mimetypes

logger = Logger(__name__)

class NetlifyService:
    def __init__(self):
        self.api_token = Config.NETLIFY_API_TOKEN
        self.team_slug = Config.NETLIFY_TEAM_SLUG or None
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.netlify.com/api/v1"

    def create_site(self, site_name: str) -> Optional[Dict]:
        payload = {"name": site_name}
        if self.team_slug:
            payload["account_slug"] = self.team_slug

        try:
            resp = requests.post(f"{self.base_url}/sites", json=payload, headers=self.headers)
            resp.raise_for_status()
            site = resp.json()
            logger.success(f"Created Netlify site: {site.get('url', 'unknown')}")
            return site
        except Exception as e:
            logger.error(f"Failed to create Netlify site: {str(e)}")
            return None


    def deploy_files(self, site_id: str, files: List[Dict[str, str]]) -> Optional[str]:
        """Build locally, zip dist/, upload as raw ZIP body (Netlify official method)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = tmpdir
            
            # Write source files
            for file in files:
                full_path = os.path.join(project_dir, file["path"])
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(file["content"])
            
            # Local build
            try:
                logger.info("Running npm install & build (Windows mode)...")
                subprocess.run(["npm.cmd", "install", "--silent"], cwd=project_dir, check=True, capture_output=True, timeout=300)
                subprocess.run(["npm.cmd", "run", "build", "--silent"], cwd=project_dir, check=True, capture_output=True, timeout=300)
            except Exception as e:
                logger.error(f"Local build failed: {str(e)}")
                return None
            
            dist_dir = os.path.join(project_dir, "dist")
            if not os.path.exists(dist_dir):
                logger.error("No dist/ folder after build")
                return None
            
            # Zip dist/ (files at root)
            zip_path = os.path.join(tmpdir, "deploy.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, filenames in os.walk(dist_dir):
                    for filename in filenames:
                        filepath = os.path.join(root, filename)
                        arcname = os.path.relpath(filepath, dist_dir).replace("\\", "/")
                        zipf.write(filepath, arcname)
            
            # Upload as raw ZIP body
            url = f"{self.base_url}/sites/{site_id}/deploys"
            try:
                logger.info("Uploading deploy.zip as raw body to Netlify...")
                with open(zip_path, "rb") as f:
                    headers = {
                        "Authorization": self.headers["Authorization"],
                        "Content-Type": "application/zip"
                    }
                    resp = requests.post(url, headers=headers, data=f.read(), timeout=600)
                resp.raise_for_status()
                deploy = resp.json()
                live_url = deploy.get("ssl_url") or deploy.get("url") or deploy.get("deploy_url")
                logger.success(f"Deployed! Live URL: {live_url}")
                return live_url
            except Exception as e:
                logger.error(f"Raw ZIP upload failed: {str(e)} | Response: {resp.text if 'resp' in locals() else 'N/A'}")
                return None

# Singleton
netlify_service = NetlifyService()