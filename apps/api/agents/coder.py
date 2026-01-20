# backend/agents/coder.py
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import Logger
from utils.json_parser import extract_json_from_text
from .agent_state import AgentState

logger = Logger(__name__)

class Coder:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        logger.step("Coder Agent", "initialized")
    
    def __call__(self, state: AgentState) -> dict:
        """Execute the coding step"""
        logger.step("Coder", f"started (iteration {state.iteration})")
        
        try:
            # Validate input
            if not state.files:
                logger.warning("⚠️ No files to code, skipping")
                return {"messages": state.messages, "files": []}
            
            # Prepare file information
            file_info = self._prepare_file_info(state.files)
            logger.debug(f"Preparing to code {len(file_info)} files")
            
            # Get context from previous messages
            context = self._extract_context(state.messages)
            
            # Create coding prompt
            prompt = self._create_prompt(file_info, context, state.messages)
            
            # Get LLM response
            logger.debug("Calling LLM for coding...")
            response = self.llm.invoke(state.messages + [HumanMessage(content=prompt)])
            logger.success("✅ LLM coding response received")
            
            # Parse response
            coded_files = self._parse_code_response(response.content)
            logger.debug(f"Generated {len(coded_files)} files")
            
            # Return updated state
            new_state = {
                "messages": state.messages + [AIMessage(content=response.content)],
                "files": coded_files
            }
            
            logger.step("Coder", "completed")
            return new_state
            
        except Exception as e:
            logger.error(f"❌ Coder failed: {str(e)}")
            raise
    
    def _prepare_file_info(self, files: list) -> list:
        """Extract file paths and descriptions"""
        file_info = []
        for file_item in files:
            if isinstance(file_item, dict):
                path = file_item.get("path", "")
                desc = file_item.get("description", "")
                if path:
                    file_info.append(f"{path}: {desc}")
            elif isinstance(file_item, str):
                file_info.append(f"{file_item}: File")
        
        return file_info
    
    def _extract_context(self, messages: list) -> str:
        """Extract project context from messages"""
        context = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                try:
                    msg_data = json.loads(msg.content)
                    if "plan" in msg_data:
                        context = f"Project plan: {msg_data['plan']}"
                        break
                except:
                    continue
        return context
    
    def _create_prompt(self, file_info: list, context: str, messages: list) -> str:
        """Create the coding prompt"""
        previous_feedback = messages[-1].content if len(messages) > 0 else "None"
        
        return f"""YOU ARE A CODE GENERATOR. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

PROJECT CONTEXT: {context}
PREVIOUS FEEDBACK: {previous_feedback}

TASK: Generate complete, production-ready code for these files:
{json.dumps(file_info, indent=2)}

CRITICAL RULES:
1. Output MUST be valid JSON parsable by json.loads()
2. NO markdown code blocks (no ```json or ```)  
3. NO explanations, comments, or extra text
4. JSON structure MUST be exactly: {{"files": [{{"path": "filename.ext", "content": "full code here"}}]}}
5. Generate code for ALL listed files
6. Make sure code is secure (NO eval() or security vulnerabilities)
7. Ensure all imports are valid and logic is correct

NOW OUTPUT THE JSON:"""
    
    def _parse_code_response(self, raw_content: str) -> list:
        """Parse and validate the code response"""
        try:
            data = extract_json_from_text(raw_content)
            generated_files = data.get("files", [])
            
            # Validate file structure
            processed_files = []
            for file_item in generated_files:
                if isinstance(file_item, dict) and "path" in file_item and "content" in file_item:
                    processed_files.append(file_item)
                else:
                    logger.warning(f"Invalid file structure: {file_item}")
            
            return processed_files
            
        except Exception as e:
            logger.error(f"Code parsing error: {str(e)}")
            return []