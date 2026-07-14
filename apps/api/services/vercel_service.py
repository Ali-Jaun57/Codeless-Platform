import os
import hashlib
import subprocess
import tempfile
import platform
import requests
from typing import List, Dict, Optional
from config import Config
from utils.logger import Logger

logger = Logger(__name__)


class VercelService:
    def __init__(self):
        self.token = Config.VERCEL_TOKEN
        self.base_url = "https://api.vercel.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        logger.step("Vercel Service", "initialized")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def deploy(
        self,
        files: List[Dict[str, str]],
        project_name: str,
        env_vars: dict = None,
    ) -> Optional[str]:
        """
        1. Write source files to a temp folder.
        2. Inject .env with real env_vars (Vite bakes them at build time).
        3. npm install + npm run build.
        4. Upload every file in dist/ to Vercel.
        5. Create a static deployment and return the live HTTPS URL.
        """
        npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"

        with tempfile.TemporaryDirectory() as tmpdir:

            # ── 1. Write source files ──────────────────────────────────
            for file in files:
                full_path = os.path.join(tmpdir, file["path"])
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(file["content"])

            # ── 2. Write .env (real credentials baked into Vite build) ─
            if env_vars:
                env_path = os.path.join(tmpdir, ".env")
                with open(env_path, "w") as f:
                    for key, value in env_vars.items():
                        f.write(f'{key}="{value}"\n')
                logger.info(f"Created .env with {len(env_vars)} variables")

            # ── 3. Build ───────────────────────────────────────────────
            try:
                logger.info("Installing npm dependencies...")
                subprocess.run(
                    [npm_cmd, "install", "--silent"],
                    cwd=tmpdir,
                    check=True,
                    capture_output=True,
                    timeout=300,
                )
                logger.info("Building React app...")
                build = subprocess.run(
                    [npm_cmd, "run", "build"],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if build.returncode != 0:
                    err = (build.stdout + "\n" + build.stderr).strip()
                    logger.error(f"Build failed:\n{err[:2000]}")
                    return None
                logger.success("✅ React app built successfully")
            except subprocess.TimeoutExpired:
                logger.error("Build timed out")
                return None
            except Exception as e:
                logger.error(f"Build exception: {str(e)}")
                return None

            dist_dir = os.path.join(tmpdir, "dist")
            if not os.path.exists(dist_dir):
                logger.error("No dist/ folder after build")
                return None

            # ── 4. Collect dist files ──────────────────────────────────
            dist_files = []
            for root, _, filenames in os.walk(dist_dir):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    arcname = os.path.relpath(filepath, dist_dir).replace("\\", "/")
                    with open(filepath, "rb") as f:
                        content = f.read()
                    dist_files.append({"path": arcname, "content": content})

            logger.info(f"Uploading {len(dist_files)} files to Vercel...")

            # ── 5. Upload each file and collect SHA references ─────────
            uploaded = []
            for df in dist_files:
                sha = self._upload_file(df["content"])
                if sha is None:
                    logger.error(f"Failed to upload {df['path']}, aborting")
                    return None
                uploaded.append({
                    "file": df["path"],
                    "sha":  sha,
                    "size": len(df["content"]),
                })

            # ── 6. Create deployment ───────────────────────────────────
            return self._create_deployment(project_name, uploaded)

    # ------------------------------------------------------------------
    # Vercel API helpers
    # ------------------------------------------------------------------

    def _upload_file(self, content: bytes) -> Optional[str]:
        """
        Upload a single file to Vercel's blob store.
        Returns the SHA-1 digest on success, None on failure.
        """
        sha = hashlib.sha1(content).hexdigest()
        try:
            resp = requests.post(
                f"{self.base_url}/v2/files",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/octet-stream",
                    "x-vercel-digest": sha,
                },
                data=content,
                timeout=60,
            )
            # 200 = uploaded now, 409 = already exists (both are fine)
            if resp.status_code in (200, 201, 409):
                return sha
            logger.error(f"File upload failed ({resp.status_code}): {resp.text[:300]}")
            return None
        except Exception as e:
            logger.error(f"File upload exception: {str(e)}")
            return None

    def _create_deployment(self, project_name: str, files: list) -> Optional[str]:
        """
        Create a static Vercel deployment from pre-uploaded file SHAs.
        Includes SPA rewrite rule so client-side routing works on refresh.
        """
        payload = {
            "name": project_name,
            "files": files,
            # SPA fallback: unknown paths → index.html
            "routes": [
                {"handle": "filesystem"},
                {"src": "/(.*)", "dest": "/index.html"},
            ],
            "projectSettings": {
                "framework": None,       # static — no Vercel build step
                "buildCommand": None,
                "outputDirectory": None,
                "installCommand": None,
                "devCommand": None,
            },
            "target": "production",
        }

        try:
            resp = requests.post(
                f"{self.base_url}/v13/deployments",
                headers=self.headers,
                json=payload,
                timeout=120,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                url = data.get("url")
                if url:
                    full_url = f"https://{url}"
                    logger.success(f"✅ Deployed to Vercel: {full_url}")
                    return full_url
            logger.error(
                f"Deployment creation failed ({resp.status_code}): {resp.text[:500]}"
            )
            return None
        except Exception as e:
            logger.error(f"Deployment creation exception: {str(e)}")
            return None


# Singleton
vercel_service = VercelService()