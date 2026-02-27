

import re

import requests
import time
import secrets
import string
from config import Config
from utils.logger import Logger

logger = Logger(__name__)




class SupabaseManagementService:
    def __init__(self):
        self.access_token = Config.SUPABASE_ACCESS_TOKEN
        self.org_id = Config.SUPABASE_ORG_ID
        self.base_url = "https://api.supabase.com/v1"

    

    def create_project(self, name: str, region: str = "us-east-1", plan: str = "free") -> dict:
        """
        Create a new Supabase project.
        Returns dict with 'ref', 'anon_key', 'service_role_key'.
        """
        url = f"{self.base_url}/projects"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # Generate a random secure password for the database
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        db_pass = ''.join(secrets.choice(alphabet) for _ in range(16))

        payload = {
            "name": name,
            "organization_id": self.org_id,
            "region": region,
            "plan": plan,
            "db_pass": db_pass
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            project_ref = data["id"]
            logger.success(f"✅ Supabase project created: {project_ref}")

            # Wait a few seconds for the project to be ready and keys to be generated
            logger.info("Waiting for project to initialize...")
            time.sleep(10)  # initial wait

            # Retrieve API keys
            keys = self._get_api_keys(project_ref, max_retries=5, delay=5)
            if not keys:
                raise Exception("Failed to retrieve API keys after multiple attempts")

            return {
                "ref": project_ref,
                "anon_key": keys["anon_key"],
                "service_role_key": keys["service_role_key"]
            }

        except Exception as e:
            logger.error(f"❌ Failed to create Supabase project: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise


    def _get_api_keys(self, project_ref: str, max_retries: int = 20, delay: int = 5) -> dict:
        """
        Wait for the Supabase project to become active, then fetch the API keys
        with exponential backoff retries.

        Args:
            project_ref: The project reference ID.
            max_retries: Maximum number of key-fetch attempts.
            delay: Base delay in seconds (used for exponential backoff).

        Returns:
            dict with 'anon_key' and 'service_role_key', or None if unsuccessful.
        """
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # ------------------------------------------------------------------
        # 1. Wait for the project to become active (any ACTIVE_* state)
        # ------------------------------------------------------------------
        status_url = f"{self.base_url}/projects/{project_ref}"
        status_attempts = 30  # up to ~3 minutes (30 * 6s)
        for attempt in range(status_attempts):
            try:
                resp = requests.get(status_url, headers=headers, timeout=30)
                if resp.status_code == 200:
                    status = resp.json().get("status")
                    logger.info(f"Project status: {status}")
                    if status and status.startswith("ACTIVE"):
                        break
                time.sleep(6)
            except Exception as e:
                logger.warning(f"Status check error (attempt {attempt+1}): {e}")
                time.sleep(6)
        else:
            logger.error("Project did not become active in time")
            return None

        # ------------------------------------------------------------------
        # 2. Fetch API keys with exponential backoff
        # ------------------------------------------------------------------
        keys_url = f"{self.base_url}/projects/{project_ref}/api-keys"
        for attempt in range(max_retries):
            try:
                resp = requests.get(keys_url, headers=headers, timeout=30)
                resp.raise_for_status()
                keys_data = resp.json()

                # Log raw response on first attempt to help debugging
                if attempt == 0:
                    logger.debug(f"Raw keys response: {keys_data}")

                anon_key = next((k["api_key"] for k in keys_data if k["name"] == "anon"), None)
                service_key = next((k["api_key"] for k in keys_data if k["name"] == "service_role"), None)

                missing = []
                if not anon_key:
                    missing.append("anon key") 
                if not service_key:
                    missing.append("service_role key")

                if missing:
                    logger.warning(f"Incomplete keys (attempt {attempt+1}): missing {', '.join(missing)}")
                else:
                    logger.info(f"API keys retrieved for project {project_ref}")
                    return {"anon_key": anon_key, "service_role_key": service_key}

            except Exception as e:
                logger.warning(f"Key fetch error (attempt {attempt+1}): {e}")

            # Exponential backoff: delay * (2 ** attempt) capped at 60 seconds
            sleep_time = min(delay * (2 ** attempt), 60)
            logger.debug(f"Waiting {sleep_time}s before next key attempt...")
            time.sleep(sleep_time)

        logger.error(f"Could not retrieve API keys for {project_ref} after {max_retries} attempts")
        return None

    
    def apply_migrations(self, project_ref: str, sql: str) -> bool:
        """Run SQL migration using the database query endpoint."""
        url = f"{self.base_url}/projects/{project_ref}/database/query"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {"query": sql}
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            logger.success(f"✅ Migrations applied to {project_ref}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to apply migrations: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return False
# Singleton instance
supabase_mgmt = SupabaseManagementService()