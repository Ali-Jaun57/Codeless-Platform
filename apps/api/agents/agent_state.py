# backend/agents/agent_state.py
from pydantic import BaseModel
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage

class AgentState(BaseModel):
    messages: List = []
    files: List[Dict[str, Any]] = []
    iteration: int = 0
    max_iterations: int = 3
    approved: bool = False
    
    def add_message(self, message):
        """Add a message to the state"""
        self.messages.append(message)
    
    def update_files(self, files):
        """Update files in the state"""
        self.files = files
    
    def increment_iteration(self):
        """Increment iteration counter"""
        self.iteration += 1
    
    def set_approved(self, approved: bool):
        """Set approval status"""
        self.approved = approved
    
    def is_complete(self) -> bool:
        """Check if workflow should complete"""
        return (self.iteration >= self.max_iterations or 
                (self.approved and len(self.files) > 0) or
                (self.iteration > 0 and len(self.files) == 0))