




import re
import time
from config import Config
from utils.logger import Logger
from services.supabase_mgmt_service import supabase_mgmt
from services.vercel_service import vercel_service
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
        # 1. Sanitized project name
        # ------------------------------------------------------------------
        base_name  = state.app_title or state.project_name or "my-app"
        safe_name  = self._sanitize_project_name(base_name)
        unique_name = f"{safe_name}-{int(time.time())}"
        logger.info(f"Creating Supabase project: {unique_name}")

        # ------------------------------------------------------------------
        # 2. Create Supabase project and retrieve keys
        # ------------------------------------------------------------------
        try:
            supabase_project = supabase_mgmt.create_project(unique_name)
            supabase_ref = supabase_project["ref"]
            anon_key     = supabase_project["anon_key"]
            service_key  = supabase_project["service_role_key"]
            logger.info(f"Supabase project created: {supabase_ref}")
        except Exception as e:
            logger.error(f"Supabase creation failed: {str(e)}")
            return {
                "supabase_ref":         None,
                "supabase_anon_key":    None,
                "supabase_service_key": None,
                "preview_url":          None,
            }

        # ------------------------------------------------------------------
        # 3. Apply SQL migrations (if any)
        # ------------------------------------------------------------------
        # migrations = [
        #     f["content"]
        #     for f in state.files
        #     if f["path"].startswith("supabase/migrations/") and f["path"].endswith(".sql")
        # ]
        # if migrations:
        #     full_sql = "\n\n".join(migrations)
        #     success  = supabase_mgmt.apply_migrations(supabase_ref, full_sql)
        #     if not success:
        #         logger.error("Migration failed — continuing with deployment")
        migrations = sorted(
            [f for f in state.files
            if f["path"].startswith("supabase/migrations/") and f["path"].endswith(".sql")],
            key=lambda f: f["path"]  # sort by filename = timestamp order
        )
        if migrations:
            success = supabase_mgmt.apply_migrations_list(
                supabase_ref,
                [f["content"] for f in migrations]
            )
            if not success:
                logger.error("Migration failed — continuing with deployment")

        # ------------------------------------------------------------------
        # 4. Deploy to Vercel with real Supabase env vars baked in
        # ------------------------------------------------------------------
        supabase_url = f"https://{supabase_ref}.supabase.co"
        env_vars = {
            "VITE_SUPABASE_URL":      supabase_url,
            "VITE_SUPABASE_ANON_KEY": anon_key,
        }

        logger.info("Deploying to Vercel...")
        preview_url = vercel_service.deploy(
            files        = state.files,
            project_name = unique_name,
            env_vars     = env_vars,
        )

        if not preview_url:
            logger.error("Vercel deployment failed")
        else:
            logger.success(f"✅ Live at: {preview_url}")

        logger.step("Deployer", "completed")
        return {
            "supabase_ref":         supabase_ref,
            "supabase_anon_key":    anon_key,
            "supabase_service_key": service_key,
            "preview_url":          preview_url,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sanitize_project_name(self, name: str) -> str:
        name = name.replace(" ", "-")
        name = re.sub(r"[^a-zA-Z0-9\-_]", "", name)
        name = name.lower()
        return name[:40]