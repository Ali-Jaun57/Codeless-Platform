
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio


from config import Config
from utils.logger import Logger

from endpoints.generate_project import router as generate_router
from workflows.main_workflow import main_workflow
from supabase_client import supabase  
from endpoints.dashboard import router as dashboard_router
from endpoints.generate_project import router as generate_router
from endpoints.export_project import router as export_router


# Initialize logger
logger = Logger("main")

# Validate configuration
try:
    Config.validate()
    logger.success("✅ Configuration validated successfully")
except RuntimeError as e:
    logger.error(f"❌ Configuration error: {e}")
    raise

# Initialize FastAPI app
app = FastAPI(title="Codeless API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        user = supabase.auth.get_user(token)
        if not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# Models
class ProjectBase(BaseModel):
    title: Optional[str] = "Untitled Project"
    prompt: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    preview_url: Optional[str] = None

class MessageBase(BaseModel):
    role: str
    content: Optional[str] = None
    files: Optional[list] = []
    preview_url: Optional[str] = None

class MessageCreate(BaseModel):
    content: str

class MessageResponse(MessageBase):
    id: UUID
    project_id: UUID
    created_at: datetime


# class GenerateRequest(BaseModel):
#     prompt: str
#     clarification: Optional[str] = None
#     detected_class: Optional[str] = None

# @app.post("/generate-project")
# async def old_generate(request: GenerateRequest):
#     # Keep old if needed, or remove
#     return await generate_handler.handle(request.prompt)

# # Export endpoint (keep)
# class ExportRequest(BaseModel):
#     repo_name: str
#     files: List[Dict[str, Any]]

# @app.post("/export-project")
# async def export_project(request: ExportRequest):
#     return await export_handler.handle(request.repo_name, request.files)

# === NEW ENDPOINTS ===
@app.get("/projects", response_model=List[ProjectResponse])
async def list_projects(user = Depends(get_current_user)):
    response = supabase.table("projects")\
        .select("*")\
        .eq("user_id", user.id)\
        .order("created_at", desc=True)\
        .execute()
    return response.data

@app.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, user = Depends(get_current_user)):
    data = {
        "user_id": user.id,
        "title": project.title or "Untitled Project",
        "prompt": project.prompt
    }
    response = supabase.table("projects").insert(data).execute()
    return response.data[0]

@app.get("/projects/{project_id}/messages")
async def get_messages(project_id: UUID, user = Depends(get_current_user)):
    # Check ownership
    proj = supabase.table("projects").select("id").eq("id", project_id).eq("user_id", user.id).execute()
    if not proj.data:
        raise HTTPException(404, "Project not found or access denied")
    
    response = supabase.table("messages")\
        .select("*")\
        .eq("project_id", project_id)\
        .order("created_at")\
        .execute()
    return response.data

@app.post("/projects/{അproject_id}/messages")
async def generate_in_project(
    project_id: UUID,
    message: MessageCreate,
    user = Depends(get_current_user)
):
    # Check ownership
    proj = supabase.table("projects").select("id").eq("id", project_id).eq("user_id", user.id).execute()
    if not proj.data:
        raise HTTPException(404, "Project not found")

    # Save user message
    supabase.table("messages").insert({
        "project_id": project_id,
        "role": "user",
        "content": message.content
    }).execute()

    # Run generation
    inputs = {"messages": [{"role": "user", "content": message.content}]}
    result = await asyncio.to_thread(main_workflow.invoke, inputs)

    # Save assistant message
    assistant_data = {
        "project_id": project_id,
        "role": "assistant",
        "content": "Your app is generated!",
        "files": result.get("files", []),
        "preview_url": result.get("preview_url")
    }
    supabase.table("messages").insert(assistant_data).execute()

    # Update project
    update_data = {"preview_url": result.get("preview_url")}
    if result.get("files"):
        update_data["title"] = result.get("project_name") or "My App"
    supabase.table("projects").update(update_data).eq("id", project_id).execute()

    return {"type": "success", "preview_url": result.get("preview_url")}

app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(export_router)
app.include_router(generate_router, prefix="/api/v1")

# Startup
@app.on_event("startup")
async def startup_event():
    logger.success("🚀 Codeless API starting up...")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

