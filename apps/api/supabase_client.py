# backend/supabase_client.py
from supabase import create_client
from config import Config
from utils.logger import Logger
from dotenv import load_dotenv

load_dotenv


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
    
    def save_project(self, prompt, files, user_id=None):
        """Save generated project to Supabase"""
        logger.debug(f"Saving project to Supabase: {len(files)} files")
        try:
            self.client.table("projects").insert({
                "user_id": user_id,
                "prompt": prompt,
                "files": files
            }).execute()
            logger.success("✅ Project saved to Supabase successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving project: {str(e)}")
            return False

supabase = SupabaseClient()