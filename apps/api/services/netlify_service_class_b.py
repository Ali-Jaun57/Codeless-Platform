

import os
import subprocess
import tempfile
import requests
import zipfile
import platform
from typing import List, Dict, Optional
from config import Config
from utils.logger import Logger

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
        """Create a new Netlify site with the given name."""
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

    def deploy_files(self, site_id: str, files: List[Dict[str, str]], env_vars: dict = None) -> Optional[str]:
        """
        Build the project locally (with optional environment variables),
        zip the dist/ folder, and upload it to Netlify as a raw ZIP body.
        Returns the live URL.
        """
        # Determine npm command based on platform
        npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"

        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = tmpdir

            # Write all source files
            for file in files:
                full_path = os.path.join(project_dir, file["path"])
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(file["content"])

            # Write .env file if environment variables are provided
            if env_vars:
                env_path = os.path.join(project_dir, ".env")
                with open(env_path, "w") as f:
                    for key, value in env_vars.items():
                        f.write(f"{key}={value}\n")
                logger.info(f"Created .env file with {len(env_vars)} variables")

            # Local build (npm install & npm run build)
            try:
                logger.info("Running npm install & build...")
                subprocess.run(
                    [npm_cmd, "install", "--silent"],
                    cwd=project_dir,
                    check=True,
                    capture_output=True,
                    timeout=300
                )
                subprocess.run(
                    [npm_cmd, "run", "build", "--silent"],
                    cwd=project_dir,
                    check=True,
                    capture_output=True,
                    timeout=300
                )
            except subprocess.TimeoutExpired:
                logger.error("Build timed out")
                return None
            except subprocess.CalledProcessError as e:
                logger.error(f"Build failed: {e.stderr.decode() if e.stderr else 'Unknown error'}")
                return None
            except Exception as e:
                logger.error(f"Local build failed: {str(e)}")
                return None

            dist_dir = os.path.join(project_dir, "dist")
            if not os.path.exists(dist_dir):
                logger.error("No dist/ folder after build")
                return None

            # Zip the dist/ folder
            zip_path = os.path.join(tmpdir, "deploy.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, filenames in os.walk(dist_dir):
                    for filename in filenames:
                        filepath = os.path.join(root, filename)
                        arcname = os.path.relpath(filepath, dist_dir).replace("\\", "/")
                        zipf.write(filepath, arcname)

            # Upload the ZIP to Netlify
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
                logger.error(f"Raw ZIP upload failed: {str(e)}")
                return None

# Singleton instance
netlify_service = NetlifyService()