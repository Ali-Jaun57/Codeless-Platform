

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import UUID
import asyncio
import time

from langchain_core.messages import HumanMessage, AIMessage

from config import Config
from utils.logger import Logger
from workflows.main_workflow import main_workflow
from supabase_client import supabase

# Import services
from services.local_dev_service import local_dev_service
from services.netlify_service import netlify_service

logger = Logger(__name__)
router = APIRouter(prefix="/generate", tags=["generation"])
security = HTTPBearer()

class GenerateRequest(BaseModel):
    prompt: str
    project_id: UUID
    clarification: Optional[str] = None
    detected_class: Optional[str] = None

class GenerateResponse(BaseModel):
    type: str
    message: Optional[str] = None
    files: list = []
    preview_url: Optional[str] = None
    detected_class: Optional[str] = None
    confidence: Optional[str] = None
    conversation_id: Optional[int] = None
    supabase_ref: Optional[str] = None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = supabase.verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

@router.post("/project", response_model=GenerateResponse)
async def generate_project(
    request: GenerateRequest,
    current_user = Depends(get_current_user)
):
    """Generate a project with conversation history"""
    logger.step("Project Generation", f"started for project: {request.project_id}")
    
    try:
        # 1. Verify user owns this project
        project = supabase.get_project(request.project_id, current_user.id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # 2. Fetch existing files (if any) for enhancement mode
        existing_files = project.get("latest_files", []) or []
        is_enhancement = bool(existing_files)
        
        # 3. Load full conversation history
        conversation_messages = supabase.get_project_conversations(
            request.project_id, current_user.id
        )
        
        # Convert to LangChain message objects
        history_messages: List = []
        for msg in conversation_messages:
            if msg["role"] == "user":
                history_messages.append(HumanMessage(content=msg["content"]))
            else:  # assistant
                # Assistant messages may contain JSON or text; preserve as string
                history_messages.append(AIMessage(content=msg["content"]))
        
        # Append the new user prompt
        history_messages.append(HumanMessage(content=request.prompt))
        
        # 4. Save user message to conversation (for persistence)
        supabase.save_user_message(
            project_id=request.project_id,
            content=request.prompt
        )
        
        # 5. Prepare inputs for workflow
        inputs = {
            "messages": history_messages,               # Full conversation history
            "files": [],                                 # Will be generated
            "iteration": 0,
            "max_iterations": Config.MAX_ITERATIONS,
            "approved": False,
            "detected_class": None,
            "confidence": None,
            "needs_clarification": False,
            "clarification_question": None,
            "app_requirements": None,
            "project_id": str(request.project_id),
            "user_id": current_user.id,
            "existing_files": existing_files,
            "is_enhancement": is_enhancement
        }
        
        # 6. Execute workflow
        logger.debug(f"Starting workflow with timeout: {Config.WORKFLOW_TIMEOUT}s")
        result = await asyncio.wait_for(
            asyncio.to_thread(main_workflow.invoke, inputs),
            timeout=Config.WORKFLOW_TIMEOUT
        )
        
        # 7. Check if clarification needed
        if result.get("needs_clarification", False):
            return GenerateResponse(
                type="clarification_needed",
                message=result.get("clarification_question", "Please clarify your request"),
                detected_class=result.get("detected_class"),
                confidence=result.get("confidence")
            )
        
        # 8. Check if unsupported class
        detected_class = result.get("detected_class")
        
        supported_classes = ["Class A", "Class B"]   # Add Class B
        if detected_class and detected_class not in supported_classes:
            return GenerateResponse(
                type="unsupported_class",
                message=f"{detected_class} is not currently supported. Only Class A and Class B are available.",
                detected_class=detected_class
            )
        
        # 9. Get generated files from workflow
        new_files = result.get("files", [])
        
        # 10. MERGE with existing files if in enhancement mode
        if existing_files:
            file_dict = {f["path"]: f for f in existing_files}
            for new_file in new_files:
                file_dict[new_file["path"]] = new_file   # overwrite or add
            merged_files = list(file_dict.values())
            logger.info(f"🔄 Merged {len(existing_files)} existing + {len(new_files)} new = {len(merged_files)} total files")
        else:
            merged_files = new_files
        
        preview_url = None

        # 11a. Class B — get preview_url from deployer result
        if detected_class == "Class B":
            preview_url = result.get("preview_url")

        # 11b. Class A — start local dev server
        if detected_class == "Class A" and merged_files:
            logger.info("🚀 Starting LOCAL development server for preview...")
            try:
                app_id = f"project_{request.project_id}_{int(time.time())}"
                app_folder = local_dev_service.save_files_locally(app_id, merged_files)
                
                if app_folder:
                    preview_url = local_dev_service.start_local_server(app_folder)
                    if preview_url:
                        logger.success(f"✅ Local preview available at: {preview_url}")
                        result["preview_url"] = preview_url
                    else:
                        logger.warning("⚠️ Local server started but no URL returned")
                else:
                    logger.warning("⚠️ Failed to save files locally")
            except Exception as deploy_err:
                logger.error(f"❌ Local preview deployment failed: {str(deploy_err)}")
        
        # 12. Save assistant message with MERGED files and preview
        assistant_message = supabase.save_assistant_message(
            project_id=request.project_id,
            content="Your app has been generated successfully!",
            files=merged_files,
            preview_url=preview_url,
            classification={
                "class": result.get("detected_class"),
                "confidence": result.get("confidence"),
                "needs_clarification": result.get("needs_clarification", False),
                "clarification_question": result.get("clarification_question")
            },
            project_name=result.get("project_name"),
            app_title=result.get("app_title"),
            supabase_ref=result.get("supabase_ref"),
            supabase_service_key=result.get("supabase_service_key"),
        )
        
        logger.success(f"✅ Generation complete: {len(merged_files)} files, preview: {preview_url}")
        
        return GenerateResponse(
            type="success",
            files=merged_files,
            preview_url=preview_url,
            detected_class=detected_class,
            conversation_id=assistant_message.get("id"),
            supabase_ref=result.get("supabase_ref"),
        )
        
    except asyncio.TimeoutError:
        logger.error("⏰ Workflow timeout")
        raise HTTPException(status_code=504, detail="Generation timeout - try a simpler prompt")
    except Exception as e:
        logger.error(f"❌ Generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))