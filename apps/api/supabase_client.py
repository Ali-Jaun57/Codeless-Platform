
from supabase import create_client, Client
from config import Config
from utils.logger import Logger
from typing import Optional, Dict, List, Any
from uuid import UUID
from datetime import datetime

logger = Logger(__name__)

class SupabaseClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize both service and auth clients"""
        logger.info("Initializing Supabase client...")
        try:
            # Service client for database operations (bypasses RLS)
            self.client = create_client(
                Config.SUPABASE_URL, 
                Config.SUPABASE_SERVICE_ROLE_KEY
            )
            
            # Auth client for JWT verification (uses anon key)
            self.auth_client = create_client(
                Config.SUPABASE_URL,
                Config.SUPABASE_ANON_KEY
            )
            
            logger.success("✅ Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {str(e)}")
            raise
    
    # ============ AUTHENTICATION METHODS ============
    
    def verify_token(self, token: str) -> Optional[Any]:
        """Verify JWT token and return user"""
        try:
            response = self.auth_client.auth.get_user(token)
            if response and response.user:
                logger.debug(f"Token verified for user: {response.user.id}")
                return response.user
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return None
    
    def get_current_user(self, token: str) -> Optional[Dict]:
        """Get current user from token"""
        user = self.verify_token(token)
        if user:
            return {
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at
            }
        return None
    
    # ============ PROJECT METHODS ============
    
    def get_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active projects for a user"""
        try:
            response = self.client.table("project")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "active")\
                .order("updated_at", desc=True)\
                .execute()
            
            logger.success(f"✅ Retrieved {len(response.data)} projects for user {user_id}")
            return response.data
        except Exception as e:
            logger.error(f"❌ Error fetching projects: {str(e)}")
            raise
    
    def create_project(self, user_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project"""
        try:
            data = {
                "user_id": user_id,
                "name": name,
                "description": description or "",
                "status": "active",
                "latest_files": []
            }
            
            response = self.client.table("project")\
                .insert(data)\
                .execute()
            
            if response.data:
                logger.success(f"✅ Project created: {name} (ID: {response.data[0]['id']})")
                return response.data[0]
            else:
                raise Exception("Failed to create project")
        except Exception as e:
            logger.error(f"❌ Error creating project: {str(e)}")
            raise
    
    def get_project(self, project_id: UUID, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific project and verify ownership"""
        try:
            response = self.client.table("project")\
                .select("*")\
                .eq("id", str(project_id))\
                .eq("user_id", user_id)\
                .eq("status", "active")\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"❌ Error fetching project {project_id}: {str(e)}")
            raise
    
    def update_project(self, project_id: UUID, user_id: str, updates: dict) -> Optional[Dict[str, Any]]:
        """Update a project"""
        try:
            # First verify ownership
            project = self.get_project(project_id, user_id)
            if not project:
                return None
            
            response = self.client.table("project")\
                .update(updates)\
                .eq("id", str(project_id))\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data:
                logger.success(f"✅ Project {project_id} updated")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ Error updating project {project_id}: {str(e)}")
            raise
    
    def delete_project(self, project_id: UUID, user_id: str) -> bool:
        """Soft delete a project"""
        try:
            response = self.client.table("project")\
                .update({"status": "deleted"})\
                .eq("id", str(project_id))\
                .eq("user_id", user_id)\
                .execute()
            
            success = len(response.data) > 0
            if success:
                logger.success(f"✅ Project {project_id} deleted")
            return success
        except Exception as e:
            logger.error(f"❌ Error deleting project {project_id}: {str(e)}")
            raise
    
    # ============ CONVERSATION METHODS ============
    
    def get_project_conversations(self, project_id: UUID, user_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a project (with ownership verification)"""
        try:
            # First verify user owns this project
            project = self.get_project(project_id, user_id)
            if not project:
                logger.warning(f"⚠️ User {user_id} does not own project {project_id}")
                return []
            
            # Get conversations
            response = self.client.table("conversation")\
                .select("*")\
                .eq("project_id", str(project_id))\
                .order("created_at", desc=False)\
                .execute()
            
            logger.success(f"✅ Retrieved {len(response.data)} messages for project {project_id}")
            return response.data
        except Exception as e:
            logger.error(f"❌ Error fetching conversations: {str(e)}")
            raise
    
    def save_user_message(self, project_id: UUID, content: str) -> Dict[str, Any]:
        """Save a user message"""
        try:
            data = {
                "project_id": str(project_id),
                "role": "user",
                "content": content
            }
            
            response = self.client.table("conversation")\
                .insert(data)\
                .execute()
            
            if response.data:
                logger.debug(f"✅ User message saved for project {project_id}")
                return response.data[0]
            raise Exception("Failed to save user message")
        except Exception as e:
            logger.error(f"❌ Error saving user message: {str(e)}")
            raise
    
    def save_assistant_message(
        self, 
        project_id: UUID, 
        content: str, 
        files: Optional[List[Dict]] = None,
        preview_url: Optional[str] = None,
        classification: Optional[Dict] = None,
        project_name: Optional[str] = None,
        app_title: Optional[str] = None,
        supabase_ref: Optional[str] = None,
        supabase_service_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save an assistant message with generated files and preview"""
        try:
            data = {
                "project_id": str(project_id),
                "role": "assistant",
                "content": content,   
                "files": files or [],
                "preview_url": preview_url
            }
            
            # Add classification data if available
            if classification:
                data.update({
                    "detected_class": classification.get("class"),
                    "confidence": classification.get("confidence"),
                    "needs_clarification": classification.get("needs_clarification", False),
                    "clarification_question": classification.get("clarification_question")
                })
            
            response = self.client.table("conversation")\
                .insert(data)\
                .execute()
            
            if response.data:
                logger.success(f"✅ Assistant message saved for project {project_id}")
                
                # Also update project's latest files/preview
                if files:
                    update_data = {
                        "latest_files": files,
                        "latest_preview_url": preview_url,
                        "updated_at": "now()"
                    }
                    if project_name:
                        update_data["latest_app_name"] = project_name
                    if app_title:
                        update_data["latest_app_title"] = app_title
                    if supabase_ref:
                        update_data["supabase_ref"] = supabase_ref
                    if supabase_service_key:
                        update_data["supabase_service_key"] = supabase_service_key
                    
                    update_response = self.client.table("project")\
                        .update(update_data)\
                        .eq("id", str(project_id))\
                        .execute()
                    
                    if update_response.data:
                        logger.success(f"✅ Project {project_id} updated with latest files/preview")
                    else:
                        logger.error(f"❌ Failed to update project {project_id}: no data returned")
                
                return response.data[0]
            else:
                raise Exception("Failed to save assistant message")
                
        except Exception as e:
            logger.error(f"❌ Error saving assistant message: {str(e)}")
            raise

# Singleton instance
supabase = SupabaseClient()