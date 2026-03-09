

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
from endpoints.export_project import router as export_router
from endpoints.cloud import router as cloud_router


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

app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(export_router)
app.include_router(generate_router, prefix="/api/v1")
app.include_router(cloud_router, prefix="/api/v1")


# Startup
@app.on_event("startup")
async def startup_event():
    logger.success("🚀 Codeless API starting up...")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)