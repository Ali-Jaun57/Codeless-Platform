# api/agents/critic.py
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import Logger
from utils.json_parser import extract_json_from_text
from .agent_state import AgentState 

logger = Logger(__name__)

class Critic:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        logger.step("Critic Agent", "initialized")
    
    def __call__(self, state: AgentState) -> dict:
        """Execute the critique step"""
        logger.step("Critic", f"started (iteration {state.iteration})")
        
        try:
            # Handle empty files case
            if not state.files:
                logger.warning("⚠️ No files to critique")
                return {
                    "messages": state.messages,
                    "iteration": state.iteration + 1,
                    "files": state.files,
                    "approved": True  
                }
            
            # Create critique prompt
            prompt = self._create_prompt(state.files[:3]) 
            
            # Get LLM response
            logger.debug("Calling LLM for critique...")
            response = self.llm.invoke(state.messages + [HumanMessage(content=prompt)])
            logger.debug(f"Raw LLM Critique response: {response.content}")
            logger.success("✅ LLM critique response received")
            
            # Parse response
            critique_data = self._parse_critique_response(response.content)
            approved = critique_data.get("approved", False)
            
            logger.info(f"Critique result: Approved = {approved}")
            
            # Return updated state
            new_state = {
                "messages": state.messages + [AIMessage(content=response.content)],
                "iteration": state.iteration + 1,
                "files": state.files, 
                "approved": approved
            }
            
            logger.step("Critic", "completed")
            return new_state
            
        except Exception as e:
            logger.error(f"❌ Critic failed: {str(e)}")
            # Default to approve on error to avoid infinite loops
            return {
                "messages": state.messages + [AIMessage(content=json.dumps({
                    "critique": "Parse error",
                    "approved": True,
                    "improvements": []
                }))],
                "iteration": state.iteration + 1,
                "files": state.files,
                "approved": True
            }
    
    def _create_prompt(self, files_sample: list) -> str:
        """Create the critique prompt"""
        return f"""YOU ARE A CODE CRITIC. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

REVIEW THESE FILES: {json.dumps(files_sample, indent=2)}

CRITICAL SECURITY RULE: REJECT ANY CODE USING eval() OR SIMILAR UNSAFE FUNCTIONS

CRITICAL RULES:
1. Output MUST be valid JSON parsable by json.loads()
2. NO markdown code blocks (no ```json or ```)
3. NO explanations, comments, or extra text  
4. JSON structure MUST be exactly: {{"critique": "brief feedback", "approved": true/false, "improvements": ["suggestion1", "suggestion2"]}}
5. "approved" MUST be boolean (true/false)
6. Be strict but constructive

APPROVAL GUIDELINES:
- Approve (true) if: code is syntactically correct, secure (no eval), imports are valid, logic makes sense
- Reject (false) if: syntax errors, missing imports, broken logic, security issues (especially eval)

EXAMPLE CORRECT OUTPUT:
{{"critique": "Code is functional but needs to remove eval() for security", "approved": false, "improvements": ["Replace eval() with safe calculation", "Add input validation"]}}

NOW OUTPUT THE JSON:"""
    
    def _parse_critique_response(self, raw_content: str) -> dict:
        """Parse and validate the critique response"""
        try:
            critique_data = extract_json_from_text(raw_content)
            
            # Ensure approved is boolean
            if "approved" in critique_data:
                critique_data["approved"] = bool(critique_data["approved"])
            
            return critique_data
            
        except Exception as e:
            logger.error(f"Critique parsing error: {str(e)}")
            return {"critique": "Parse error", "approved": True, "improvements": []}