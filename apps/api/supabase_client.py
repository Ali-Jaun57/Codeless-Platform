# backend/supabase_client.py
from supabase import create_client
from config import Config
from utils.logger import Logger
from dotenv import load_dotenv
from typing import Dict, List, Optional
from datetime import datetime

load_dotenv()


logger = Logger(__name__)

class SupabaseClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        logger.info("Initializing Supabase client...")
        try:
            self.client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)
            logger.success("✅ Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {str(e)}")
            raise
    
    def get_projects(self, limit=5):
        """Retrieve recent projects for RAG context"""
        logger.debug(f"Fetching {limit} recent projects from Supabase")
        try:
            response = self.client.table("projects")\
                .select("prompt, files")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            logger.success(f"✅ Retrieved {len(response.data)} projects from Supabase")
            return response.data
        except Exception as e:
            logger.error(f"❌ Error fetching projects: {str(e)}")
            return []
    

    def save_project(self, prompt: str, files: list, user_id: Optional[str] = None, preview_url: Optional[str] = None):
        """Save generated project to Supabase with optional preview URL"""
        logger.debug(f"Saving project to Supabase: {len(files)} files")
        try:
            data = {
                "user_id": user_id,
                "prompt": prompt,
                "files": files
            }
            if preview_url:
                data["preview_url"] = preview_url
                logger.info(f"Saving preview URL: {preview_url}")

            response = self.client.table("projects").insert(data).execute()
            
            if response.data:
                logger.success("✅ Project saved to Supabase successfully")
                return response.data[0]
            else:
                logger.error(f"Failed to save project: {response}")
                return None
        except Exception as e:
            logger.error(f"❌ Save error: {str(e)}")
            return None
        

    def save_deployment(self, deployment_info: Dict):
        """Save deployment information to Supabase"""
        try:
            response = self.client.table("deployments").insert(deployment_info).execute()  # Changed self.supabase to self.client
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error saving deployment: {str(e)}")
            raise

    def get_expired_deployments(self):
        """Get deployments that have expired"""
        try:
            from datetime import datetime
            now = datetime.utcnow().isoformat()

            response = self.client.table("deployments") \
                .select("*") \
                .lt("expires_at", now) \
                .eq("cleaned_up", False) \
                .execute()
            
            return response.data
        except Exception as e:
            logger.error(f"Error getting expired deployments: {str(e)}")
            return []

    def mark_deployment_cleaned(self, deployment_id: str):
        """Mark a deployment as cleaned up"""
        try:
            response = self.client.table("deployments") \
                .update({"cleaned_up": True, "cleaned_at": datetime.utcnow().isoformat()}) \
                .eq("id", deployment_id) \
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error marking deployment as cleaned: {str(e)}")
            raise

    def get_project_by_hash(self, project_hash: str):
        """Get project by hash"""
        try:
            response = self.client.table("projects") \
                .select("*") \
                .eq("project_hash", project_hash) \
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting project: {str(e)}")
            return None

    def get_project(self, project_id: str):
        """Get project by ID"""
        try:
            response = self.client.table("projects") \
                .select("*") \
                .eq("id", project_id) \
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting project: {str(e)}")
            return None



supabase = SupabaseClient()