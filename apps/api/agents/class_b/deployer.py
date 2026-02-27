

import os
import time
import re
from config import Config
from utils.logger import Logger
from services.netlify_service_class_b import netlify_service
from services.supabase_mgmt_service import supabase_mgmt
from ..shared.agent_state import AgentState

logger = Logger(__name__)

class Deployer:
    def __init__(self):
        logger.step("Deployer (Class B)", "initialized")

    def __call__(self, state: AgentState) -> dict:
        logger.step("Deployer", "started")

        if not state.files:
            logger.warning("No files to deploy")
            return {}

        # ------------------------------------------------------------------
        # 1. Generate a project name from the app title (sanitized)
        # ------------------------------------------------------------------
        base_name = state.app_title or state.project_name or "my-app"
        safe_name = self._sanitize_project_name(base_name)
        unique_name = f"{safe_name}-{int(time.time())}"
        logger.info(f"Creating Supabase project with name: {unique_name}")

        # ------------------------------------------------------------------
        # 2. Create Supabase project and retrieve keys
        # ------------------------------------------------------------------
        try:
            supabase_project = supabase_mgmt.create_project(unique_name)
            supabase_ref = supabase_project["ref"]
            anon_key = supabase_project["anon_key"]
            service_key = supabase_project["service_role_key"]
            logger.info(f"Supabase project created: {supabase_ref}")
        except Exception as e:
            logger.error(f"Supabase creation failed: {str(e)}")
            return {"preview_url": None, "supabase_ref": None}

        # ------------------------------------------------------------------
        # 3. Apply SQL migrations (if any)
        # ------------------------------------------------------------------
        migrations = []
        for f in state.files:
            if f["path"].startswith("supabase/migrations/") and f["path"].endswith(".sql"):
                migrations.append(f["content"])
        if migrations:
            full_sql = "\n\n".join(migrations)
            success = supabase_mgmt.apply_migrations(supabase_ref, full_sql)
            if not success:
                logger.error("Migration failed, but continuing with deployment")

        # ------------------------------------------------------------------
        # 4. Prepare environment variables for the frontend build
        # ------------------------------------------------------------------
        env_vars = {
            "VITE_SUPABASE_URL": f"https://{supabase_ref}.supabase.co",
            "VITE_SUPABASE_ANON_KEY": anon_key
        }

        # ------------------------------------------------------------------
        # 5. Create Netlify site
        # ------------------------------------------------------------------
        site_name = f"{safe_name}-{int(time.time())}"
        site = netlify_service.create_site(site_name)
        if not site:
            logger.error("Failed to create Netlify site")
            return {"preview_url": None, "supabase_ref": supabase_ref}
        site_id = site["id"]
        logger.info(f"Netlify site created with ID: {site_id}")

        # ------------------------------------------------------------------
        # 6. Deploy files (Netlify will build with env vars)
        # ------------------------------------------------------------------
        preview_url = netlify_service.deploy_files(site_id, state.files, env_vars)
        if not preview_url:
            logger.error("Netlify deployment failed")
            return {"preview_url": None, "supabase_ref": supabase_ref}

        logger.success(f"✅ Deployed! Preview URL: {preview_url}")

        # ------------------------------------------------------------------
        # 7. Return final state
        # ------------------------------------------------------------------
        new_state = {
            "supabase_ref": supabase_ref,
            "supabase_anon_key": anon_key,
            "supabase_service_key": service_key,
            "preview_url": preview_url,
            "netlify_site_name": site_name
        }
        logger.step("Deployer", "completed")
        return new_state

    def _sanitize_project_name(self, name: str) -> str:
        """
        Convert a name to lowercase, replace spaces with hyphens,
        remove any non‑alphanumeric characters (except hyphen/underscore),
        and truncate to 40 characters (safe for Supabase/Netlify).
        """
        # Replace spaces with hyphens
        name = name.replace(' ', '-')
        # Keep only letters, numbers, hyphens, underscores
        name = re.sub(r'[^a-zA-Z0-9\-_]', '', name)
        # Convert to lowercase
        name = name.lower()
        # Truncate to 40 chars
        return name[:40]