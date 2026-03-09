
from supabase_client import supabase
from utils.logger import Logger
from typing import List, Dict, Any, Optional
from uuid import UUID

logger = Logger(__name__)

class ConversationService:
    
    async def get_project_conversations(self, project_id: UUID, user_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a project (verify ownership first)"""
        try:
            # First verify user owns this project
            project_response = supabase.table("project")\
                .select("id")\
                .eq("id", str(project_id))\
                .eq("user_id", user_id)\
                .execute()
            
            if not project_response.data:
                logger.warning(f"⚠️ User {user_id} does not own project {project_id}")
                return []
            
            # Get conversations
            response = supabase.table("conversation")\
                .select("*")\
                .eq("project_id", str(project_id))\
                .order("created_at", desc=False)\
                .execute()
            
            logger.success(f"✅ Retrieved {len(response.data)} messages for project {project_id}")
            return response.data
            
        except Exception as e:
            logger.error(f"❌ Error fetching conversations: {str(e)}")
            raise
    
    async def save_user_message(self, project_id: UUID, content: str) -> Dict[str, Any]:
        """Save a user message"""
        try:
            data = {
                "project_id": str(project_id),
                "role": "user",
                "content": content
            }
            
            response = supabase.table("conversation")\
                .insert(data)\
                .execute()
            
            if response.data:
                logger.debug(f"✅ User message saved for project {project_id}")
                return response.data[0]
            else:
                raise Exception("Failed to save user message")
                
        except Exception as e:
            logger.error(f"❌ Error saving user message: {str(e)}")
            raise
    
    async def save_assistant_message(
        self, 
        project_id: UUID, 
        content: str,
        files: Optional[List[Dict]] = None,
        preview_url: Optional[str] = None,
        classification: Optional[Dict] = None
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
            
          
            if classification:
                data.update({
                    "detected_class": classification.get("class"),
                    "confidence": classification.get("confidence"),
                    "needs_clarification": classification.get("needs_clarification", False),
                    "clarification_question": classification.get("clarification_question")
                })
            
            response = supabase.table("conversation")\
                .insert(data)\
                .execute()
            
            if response.data:
                logger.success(f"✅ Assistant message saved for project {project_id}")
                
                # Also update project's latest files/preview
                if files:
                    supabase.table("project")\
                        .update({
                            "latest_files": files,
                            "latest_preview_url": preview_url,
                            "updated_at": "now()"
                        })\
                        .eq("id", str(project_id))\
                        .execute()
                
                return response.data[0]
            else:
                raise Exception("Failed to save assistant message")
                
        except Exception as e:
            logger.error(f"❌ Error saving assistant message: {str(e)}")
            raise

# Singleton instance
conversation_service = ConversationService()