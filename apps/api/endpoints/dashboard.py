
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from uuid import UUID

from utils.logger import Logger
from models.project import ProjectCreate, ProjectResponse, ProjectListResponse
from supabase_client import supabase

logger = Logger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from token"""
    token = credentials.credentials
    user = supabase.verify_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

@router.get("/projects", response_model=ProjectListResponse)
async def get_my_projects(current_user = Depends(get_current_user)):
    """Get all projects for the current user"""
    try:
        projects = supabase.get_user_projects(current_user.id)
        return {
            "projects": projects,
            "total": len(projects)
        }
    except Exception as e:
        logger.error(f"Error fetching projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects", response_model=ProjectResponse)
async def create_new_project(
    project_data: ProjectCreate,
    current_user = Depends(get_current_user)
):
    """Create a new project"""
    try:
        project = supabase.create_project(
            user_id=current_user.id,
            name=project_data.name,
            description=project_data.description
        )
        return project
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project_details(
    project_id: UUID,
    current_user = Depends(get_current_user)
):
    """Get a specific project"""
    try:
        project = supabase.get_project(project_id, current_user.id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/projects/{project_id}")
async def delete_project_endpoint(
    project_id: UUID,
    current_user = Depends(get_current_user)
):
    """Delete a project (soft delete)"""
    try:
        success = supabase.delete_project(project_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/conversations")
async def get_project_conversations(
    project_id: UUID,
    current_user = Depends(get_current_user)
):
    """Get all conversations for a project"""
    try:
        conversations = supabase.get_project_conversations(project_id, current_user.id)
        return {"messages": conversations}
    except Exception as e:
        logger.error(f"Error fetching conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))