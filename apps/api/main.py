
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

# In main.py, use:
from config import Config
from utils.logger import Logger
from endpoints.generate_project import handler as generate_handler
from endpoints.export_project import handler as export_handler
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class GenerateRequest(BaseModel):
    prompt: str

class ExportRequest(BaseModel):
    repo_name: str
    files: List[Dict[str, Any]]

# Health check endpoint
@app.get("/health")
async def health():
    logger.debug("Health check requested")
    return {"status": "ok", "service": "codeless-api"}

# Project generation endpoint
@app.post("/generate-project")
async def generate_project(request: GenerateRequest):
    logger.info(f"📨 Received generate request: {request.prompt[:50]}...")
    return await generate_handler.handle(request.prompt)

# Project export endpoint
@app.post("/export-project")
async def export_project(request: ExportRequest):
    logger.info(f"📤 Received export request for repo: {request.repo_name}")
    return await export_handler.handle(request.repo_name, request.files)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.success("🚀 Codeless API starting up...")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)