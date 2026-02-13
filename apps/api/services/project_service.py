
from supabase_client import supabase
from utils.logger import Logger
from typing import List, Dict, Any, Optional
from uuid import UUID

logger = Logger(__name__)

class ProjectService:
    
    async def get_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active projects for a user"""
        try:
            response = supabase.table("project")\
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
    
    async def create_project(self, user_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project"""
        try:
            data = {
                "user_id": user_id,
                "name": name,
                "description": description or "",
                "status": "active",
                "latest_files": []
            }
            
            response = supabase.table("project")\
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
    
    async def get_project(self, project_id: UUID, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific project (verify ownership)"""
        try:
            response = supabase.table("project")\
                .select("*")\
                .eq("id", str(project_id))\
                .eq("user_id", user_id)\
                .eq("status", "active")\
                .execute()
            
            if response.data:
                return response.data[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching project {project_id}: {str(e)}")
            raise
    
    async def update_project(self, project_id: UUID, user_id: str, updates: dict) -> Optional[Dict[str, Any]]:
        """Update a project"""
        try:
            # First verify ownership
            project = await self.get_project(project_id, user_id)
            if not project:
                return None
            
            response = supabase.table("project")\
                .update(updates)\
                .eq("id", str(project_id))\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data:
                logger.success(f"✅ Project {project_id} updated")
                return response.data[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ Error updating project {project_id}: {str(e)}")
            raise
    
    async def delete_project(self, project_id: UUID, user_id: str) -> bool:
        """Soft delete a project"""
        try:
            response = supabase.table("project")\
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

# Singleton instance
project_service = ProjectService()