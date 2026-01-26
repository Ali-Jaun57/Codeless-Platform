
# backend/agents/coder.py
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import Logger
from utils.json_parser import extract_json_from_text
from .agent_state import AgentState
from .templates import TEMPLATE_CONTENTS  # ADD THIS IMPORT

logger = Logger(__name__)

class Coder:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        logger.step("Coder Agent", "initialized")
    
    def __call__(self, state: AgentState) -> dict:
        """Execute the coding step — now outputs FULL project (templates + custom)"""
        logger.step("Coder", f"started (iteration {state.iteration})")
        
        try:
            # Validate input
            if not state.files:
                logger.warning("⚠️ No files to code, skipping")
                full_files = self._generate_base_templates(state)
                return {"messages": state.messages, "files": full_files}
            
            # Prepare file information (descriptions only)
            file_info = self._prepare_file_info(state.files)
            logger.debug(f"Preparing to code {len(file_info)} custom files")
            
            # Get context from previous messages
            context = self._extract_context(state.messages)
            
            # Create coding prompt (improved — stricter rules)
            prompt = self._create_prompt(file_info, context, state.messages)
            
            # Get LLM response
            logger.debug("Calling LLM for coding...")
            response = self.llm.invoke(state.messages + [HumanMessage(content=prompt)])
            logger.debug(f"Raw LLM Coding response: {response.content}")
            logger.success("✅ LLM coding response received")
            
            # Parse custom coded files
            coded_files = self._parse_code_response(response.content)
            logger.debug(f"Generated {len(coded_files)} custom files")
            
            # Generate base template files with planner variables
            base_files = self._generate_base_templates(state)
            
            # Combine: CUSTOM FIRST (for critic sampling) + BASE TEMPLATES
            # Use dict to handle any path override (custom wins)
            full_dict = {f["path"]: f for f in base_files}
            for f in coded_files:
                full_dict[f["path"]] = f
            full_files = list(full_dict.values())
            
            logger.debug(f"Full project: {len(full_files)} files (custom + templates)")
            
            # Return updated state with FULL files
            new_state = {
                "messages": state.messages + [AIMessage(content=response.content)],
                "files": full_files
            }
            
            logger.step("Coder", "completed")
            return new_state
            
        except Exception as e:
            logger.error(f"❌ Coder failed: {str(e)}")
            raise
    
    def _generate_base_templates(self, state: AgentState) -> list:
        """Generate all base template files with planner replacements"""
        # Extract planner metadata from messages
        planner_data = {
            "project_name": "my-app",
            "app_title": "My App",
            "app_description": "A React application built with Vite and Tailwind CSS."
        }
        for msg in reversed(state.messages):
            if isinstance(msg, AIMessage):
                try:
                    data = json.loads(msg.content)
                    if "project_name" in data:
                        planner_data = {
                            "project_name": data.get("project_name", "my-app"),
                            "app_title": data.get("app_title", "My App"),
                            "app_description": data.get("app_description", "A React application.")
                        }
                        break
                except:
                    continue
        
        base_files = []
        for path, template_content in TEMPLATE_CONTENTS.items():
            if "BINARY_FILE_CONTENT" in template_content:
                continue  # Skip favicon.ico
            
            content = template_content \
                .replace("{{APP_NAME}}", planner_data["project_name"]) \
                .replace("{{APP_TITLE}}", planner_data["app_title"]) \
                .replace("{{APP_DESCRIPTION}}", planner_data["app_description"])
            
            base_files.append({"path": path, "content": content})
        
        return base_files
    
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
        """Extract project context from messages (keep existing)"""
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
        """Improved prompt — strictly follow descriptions, use hooks, add images, fix navbar overlap"""
        previous_feedback = messages[-1].content if len(messages) > 0 else "None"
        
        return f"""YOU ARE A CODE GENERATOR FOR CLASS A REACT APPS. OUTPUT ONLY PURE JSON.

PROJECT CONTEXT: {context}
PREVIOUS FEEDBACK: {previous_feedback}

TASK: Generate complete, production-ready code for these files EXACTLY as described:
{json.dumps(file_info, indent=2)}

CRITICAL RULES (FOLLOW STRICTLY):
1. Output MUST be valid JSON: {{"files": [{{"path": "filename.ext", "content": "full code"}}]}}
2. NO markdown, NO explanations, NO extra text
3. Implement EVERY feature in the descriptions:
   - You MUST use any planned hooks (e.g., import and apply useIntersectionObserver in relevant components for fade-in on scroll)
   - Add opacity-0 translate-y-10 classes, then transition to opacity-100 translate-y-0 when intersecting
   - Example usage: Wrap sections or cards with ref from the hook and add conditional classes
   - Add placeholder images for products/showcases
   - For single-page apps: add className="scroll-mt-16" to every <section id="...">
   - Use advanced Tailwind: gradients, hover:scale-105, transitions, dark: variants if mentioned
4. Code must be secure, correct imports, responsive
5. Generate code for ALL listed files

NOW OUTPUT THE JSON:"""
    
    def _parse_code_response(self, raw_content: str) -> list:
        """Parse and validate the code response"""
        try:
            data = extract_json_from_text(raw_content)
            generated_files = data.get("files", [])
            
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