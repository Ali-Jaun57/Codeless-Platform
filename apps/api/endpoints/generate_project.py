


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
import asyncio
import time

from langchain_core.messages import HumanMessage

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
        
        # 2. Save user message to conversation
        supabase.save_user_message(
            project_id=request.project_id,
            content=request.prompt
        )
        
        # 3. Prepare inputs for workflow
        inputs = {
            "messages": [HumanMessage(content=request.prompt)],
            "files": [],
            "iteration": 0,
            "max_iterations": Config.MAX_ITERATIONS,
            "approved": False,
            "detected_class": None,
            "confidence": None,
            "needs_clarification": False,
            "clarification_question": None,
            "app_requirements": None,
            "project_id": str(request.project_id),
            "user_id": current_user.id
        }
        
        # 4. Execute workflow
        logger.debug(f"Starting workflow with timeout: {Config.WORKFLOW_TIMEOUT}s")
        result = await asyncio.wait_for(
            asyncio.to_thread(main_workflow.invoke, inputs),
            timeout=Config.WORKFLOW_TIMEOUT
        )
        
        # 5. Check if clarification needed
        if result.get("needs_clarification", False):
            return GenerateResponse(
                type="clarification_needed",
                message=result.get("clarification_question", "Please clarify your request"),
                detected_class=result.get("detected_class"),
                confidence=result.get("confidence")
            )
        
        # 6. Check if unsupported class
        detected_class = result.get("detected_class")
        if detected_class and detected_class != "Class A":
            return GenerateResponse(
                type="unsupported_class",
                message=f"{detected_class} is not currently supported. Only Class A (frontend-only apps) are available.",
                detected_class=detected_class
            )
        
        # 7. Get generated files
        files = result.get("files", [])
        preview_url = None
        
        # 8. 🖥️ LOCAL PREVIEW ENABLED - Netlify is COMMENTED OUT
        if detected_class == "Class A" and files:
            logger.info("🚀 Starting LOCAL development server for preview...")
            try:
                # Generate a unique app ID for this project
                app_id = f"project_{request.project_id}_{int(time.time())}"
                
                # Save files locally
                app_folder = local_dev_service.save_files_locally(app_id, files)
                
                if app_folder:
                    # Start local server on port 4000
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
                # Continue even if deployment fails
        
        # # 🌐 NETLIFY DEPLOYMENT - COMMENTED OUT
        
        # # Try Netlify deployment for Class A apps
        # if detected_class == "Class A" and files:
        #     logger.info("🚀 Starting Netlify deployment for preview...")
        #     try:
        #         # Get project name from planner result
        #         project_name = result.get("project_name", "codeless-app")
        #         site_name = f"codeless-{project_name}-{int(time.time())}"
                
        #         # Create site and deploy
        #         site = netlify_service.create_site(site_name)
        #         if site and site.get("id"):
        #             preview_url = netlify_service.deploy_files(site["id"], files)
        #             if preview_url:
        #                 logger.success(f"✅ Deployed! Preview URL: {preview_url}")
        #                 result["preview_url"] = preview_url
        #             else:
        #                 logger.warning("⚠️ Netlify deployment succeeded but no URL returned")
        #         else:
        #             logger.warning("⚠️ Failed to create Netlify site")
        #     except Exception as deploy_err:
        #         logger.error(f"❌ Preview deployment failed: {str(deploy_err)}")
        #         preview_url = None
        
        
        # 9. Save assistant message with files and preview
        assistant_message = supabase.save_assistant_message(
            project_id=request.project_id,
            content="Your app has been generated successfully!",
            files=files,
            preview_url=preview_url,
            classification={
                "class": result.get("detected_class"),
                "confidence": result.get("confidence"),
                "needs_clarification": result.get("needs_clarification", False),
                "clarification_question": result.get("clarification_question")
            }
        )
        
        logger.success(f"✅ Generation complete: {len(files)} files, preview: {preview_url}")
        
        return GenerateResponse(
            type="success",
            files=files,
            preview_url=preview_url,
            detected_class=detected_class,
            conversation_id=assistant_message.get("id")
        )
        
    except asyncio.TimeoutError:
        logger.error("⏰ Workflow timeout")
        raise HTTPException(status_code=504, detail="Generation timeout - try a simpler prompt")
    except Exception as e:
        logger.error(f"❌ Generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))