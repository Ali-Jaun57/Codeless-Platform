
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class MessageCreate(BaseModel):
    content: str
    project_id: UUID

class ConversationResponse(BaseModel):
    id: int
    project_id: UUID
    role: str
    content: str
    files: Optional[List[Dict[str, Any]]] = None
    preview_url: Optional[str] = None
    detected_class: Optional[str] = None
    confidence: Optional[str] = None
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True