# backend/agents/planner.py
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from supabase_client import supabase
from utils.logger import Logger
from utils.json_parser import extract_json_from_text
from .agent_state import AgentState

logger = Logger(__name__)

class Planner:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        logger.step("Planner Agent", "initialized")
    
    def __call__(self, state: AgentState) -> dict:
        """Execute the planning step"""
        logger.step("Planner", "started")
        
        try:
            # Step 1: Retrieve RAG context
            rag_context = self._get_rag_context()
            logger.debug(f"RAG context retrieved: {len(rag_context)} projects")
            
            # Step 2: Create planning prompt
            prompt = self._create_prompt(state.messages[-1].content, rag_context)
            
            # Step 3: Get LLM response
            logger.debug("Calling LLM for planning...")
            response = self.llm.invoke([HumanMessage(content=prompt)])
            logger.success("✅ LLM planning response received")
            
            # Step 4: Parse and validate response
            plan_data = self._parse_plan_response(response.content)
            logger.debug(f"Parsed plan: {len(plan_data.get('files', []))} files planned")
            
            # Step 5: Prepare return state
            new_state = {
                "messages": state.messages + [AIMessage(content=json.dumps(plan_data))],
                "files": plan_data.get("files", []),
                "approved": False,  # Reset approval for new plan
                "iteration": state.iteration  # Keep iteration count
            }
            
            logger.step("Planner", "completed")
            return new_state
            
        except Exception as e:
            logger.error(f"❌ Planner failed: {str(e)}")
            raise
    
    def _get_rag_context(self) -> str:
        """Retrieve previous projects for context"""
        try:
            projects = supabase.get_projects(limit=5)
            
            if not projects:
                return "No previous projects found."
            
            context = "Previous projects (most recent):\n"
            for project in projects:
                file_names = [f["path"] for f in project["files"][:3]]
                context += f"- Prompt: {project['prompt']}\n  Files: {file_names}\n\n"
            
            return context
        except Exception as e:
            logger.error(f"RAG context error: {str(e)}")
            return "Error retrieving previous projects."
    
    def _create_prompt(self, user_request: str, context: str) -> str:
        """Create the planning prompt"""
        return f"""{context}
        
USER REQUEST: {user_request}

Plan the project (improve previous if relevant). Output ONLY JSON: {{"plan": "description", "files": ["path1.js", ...]}}"""
    
    def _parse_plan_response(self, raw_content: str) -> dict:
        """Parse and validate the planner response"""
        try:
            # Extract JSON
            plan_data = extract_json_from_text(raw_content)
            
            # Process files list
            files = plan_data.get("files", [])
            processed_files = []
            
            for file_item in files:
                if isinstance(file_item, str):
                    processed_files.append({
                        "path": file_item,
                        "description": f"File: {file_item}"
                    })
                elif isinstance(file_item, dict):
                    processed_files.append(file_item)
            
            plan_data["files"] = processed_files
            return plan_data
            
        except Exception as e:
            logger.error(f"Plan parsing error: {str(e)}")
            # Return default plan
            return {
                "plan": "Basic project plan",
                "files": [
                    {"path": "index.html", "description": "HTML entry point"},
                    {"path": "App.js", "description": "Main React component"},
                    {"path": "styles.css", "description": "CSS styling"}
                ]
            }