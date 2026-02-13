
# api/agents/planner.py
import json
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import Logger
from utils.json_parser import extract_json_from_text
from .agent_state import AgentState
from .templates import FOLDER_STRUCTURE, EXAMPLE_OUTPUT

logger = Logger(__name__)

class Planner:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        logger.step("Planner Agent", "initialized")
    
    def __call__(self, state: AgentState) -> dict:
        """Execute the planning step"""
        logger.step("Planner", "started")
        start_time = time.time()
        
        try:
            # Step 1: Retrieve RAG context
            # rag_context = self._get_rag_context()
            # logger.debug(f"RAG context retrieved: {len(rag_context)} characters")
            logger.debug(f"No RAG retrival now")
            

            # Step 2: Get the user prompt EXACTLY like classifier does
            user_prompt = ""
            for msg in reversed(state.messages):
                if isinstance(msg, HumanMessage):
                    user_prompt = msg.content
                    break
            
            if not user_prompt:
                logger.warning("No user prompt found, using fallback")
                user_prompt = "Create a React app"
            
            logger.debug(f"User prompt: {user_prompt[:100]}...")


            # Step 2: Create planning prompt
            prompt = self._create_prompt(user_prompt)
            
            # Step 3: Get LLM response
            logger.debug("Calling LLM for planning...")
            response = self.llm.invoke([HumanMessage(content=prompt)])
            logger.debug(f"Raw LLM response: {response.content}")
            logger.success("✅ LLM planning response received")
            
            # Step 4: Parse and validate response
            plan_data = self._parse_plan_response(response.content)
            logger.debug(f"Parsed plan: {len(plan_data.get('files', []))} files to generate")
            
            # Step 5: Prepare return state
            new_state = {
                "messages": state.messages + [AIMessage(content=json.dumps(plan_data))],
                "files": plan_data.get("files", []),  # Compatible with existing workflow
                "project_name": plan_data.get("project_name"),
                "app_title": plan_data.get("app_title"),
                "app_description": plan_data.get("app_description"),
                "approved": False,
                "iteration": state.iteration
            }
            
            logger.step("Planner", "completed")
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            logger.performance(f"Planner execution", duration_ms)
            return new_state
            
        except Exception as e:
            logger.error(f"❌ Planner failed: {str(e)}")
            raise
    

    # def _get_rag_context(self) -> str:
    #     """Retrieve relevant previous projects for context"""
    #     try:
    #         from supabase_client import supabase
            
    #         projects = supabase.get_projects(limit=10)
            
    #         if not projects:
    #             return "No previous projects found."
            
    #         relevant_context = "Previous similar projects (for inspiration only):\n"
    #         count = 0
    #         for project in projects:
    #             if count >= 3:
    #                 break
    #             prompt = project.get('prompt', '')
    #             file_names = [f.get("path", "") for f in project.get("files", [])[:5]]
    #             relevant_context += f"- User requested: {prompt[:100]}...\n  Generated files: {file_names}\n\n"
    #             count += 1
            
    #         relevant_context += "\nIMPORTANT: Previous projects may be simple HTML/JS. NOW we build modern React + Vite + Tailwind apps. Use above only for inspiration.\n"
    #         return relevant_context
            
    #     except Exception as e:
    #         logger.error(f"RAG context error: {str(e)}")
    #         return "Error retrieving previous projects. Create new React plan."


    def _create_prompt(self, user_request: str) -> str:
        """Complete improved prompt with strict folder structure enforcement"""
        return f"""YOU ARE AN EXPERT REACT DEVELOPER SPECIALIZING IN CLASS A FRONTEND-ONLY APPS.

STRICT CLASS A RULES (NEVER VIOLATE):
- Pure frontend only: React + Vite + Tailwind CSS
- NO backend, NO auth, NO database, NO external APIs
- NO additional dependencies beyond react, react-dom, @vitejs/plugin-react, tailwindcss, postcss, autoprefixer
- NO react-router-dom, framer-motion, axios, lodash, etc. — ever
- Single-page application preferred (everything in one page with <section id="..."> elements)
- Use <a href="#section-id"> links + CSS smooth scrolling for navigation
- Only use client-side routing if user explicitly requests multi-page behavior
- Local state (useState, useEffect, useRef) and localStorage only when explicitly needed

STRICT FOLDER STRUCTURE (MUST FOLLOW EXACTLY):
{json.dumps(FOLDER_STRUCTURE, indent=4)}

FILE PLACEMENT RULES (ENFORCE WITHOUT EXCEPTION):
- Main application layout and routing logic → ALWAYS src/App.jsx
- All reusable UI components → src/components/ComponentName.jsx
- All custom hooks → src/hooks/useSomething.js
- All utility functions/constants → src/utils/utils.js or specific files
- NEVER create new top-level folders
- NEVER place components/hooks/utils outside src/components/, src/hooks/, src/utils/
- Do NOT plan modifications to base template files (package.json, vite.config.js, index.html, main.jsx, index.css) unless explicitly requested
- Only plan files inside src/ that are custom to this app

PLANNING GUIDELINES:
1. FOR PORTFOLIOS / LANDING PAGES:
   - Single-page with scrollable sections (Hero, About, Skills, Projects, Contact, Footer)
   - Sticky/fixed navbar with smooth-scroll links
   - Hero: full viewport, gradient/overlay background, animated text, profile image
   - Projects: responsive card grid with hover effects (scale, shadow lift)
   - Use advanced Tailwind: gradients, glassmorphism, transitions, @keyframes, dark mode support
   - Always plan src/hooks/useIntersectionObserver.js for scroll fade-in animations
   - Describe using it in Hero, About, Skills, Projects sections for smooth reveal effects

2. FOR "BEST UI/UX" REQUESTS:
   - Maximize modern Tailwind features: gradients, hover/focus effects, smooth transitions, proper typography scale
   - Add subtle micro-interactions (fade-in on scroll via IntersectionObserver if needed)
   - Ensure full responsiveness and accessibility (aria-labels, keyboard nav, contrast)

3. GENERAL:
   - Keep App.jsx clean — import and compose components
   - Split only when it improves readability (avoid too many tiny components)
   - Descriptions must explain: purpose, key features, Tailwind styling approach, responsiveness, state/interactions



USER REQUEST:
{user_request}

OUTPUT ONLY PURE VALID JSON — NO markdown, NO explanations, NO extra text.

REQUIRED JSON FORMAT EXACTLY:
{json.dumps(EXAMPLE_OUTPUT, indent=2)}

In "files_to_generate":
- Use only allowed paths (src/App.jsx, src/components/*.jsx, src/hooks/*.js, src/utils/*.js)
- Every description must be detailed and specific to how it fulfills the user request
- Prioritize exceptional modern UI when user asks for "best" or "beautiful"

Now create the optimal plan."""
    

    def _parse_plan_response(self, raw_content: str) -> dict:
        """Parse and validate the planner response"""
        try:
            plan_data = extract_json_from_text(raw_content)
            
            # Extract project info with sensible defaults
            project_name = plan_data.get("project_name", "my-app").lower().strip()
            app_title = plan_data.get("app_title", "My App").strip()
            app_description = plan_data.get("app_description", "A React application built with Vite and Tailwind CSS.").strip()
            
            # Process files_to_generate
            files_raw = plan_data.get("files_to_generate", [])
            processed_files = []
            
            for item in files_raw:
                if isinstance(item, str):
                    processed_files.append({
                        "path": item,
                        "description": "Implement this component/file."
                    })
                elif isinstance(item, dict):
                    path = item.get("path", "").strip()
                    desc = item.get("description", "No description provided.").strip()
                    if path:
                        processed_files.append({
                            "path": path,
                            "description": desc
                        })
            
            return {
                "project_name": project_name,
                "app_title": app_title,
                "app_description": app_description,
                "files": processed_files
            }
            
        except Exception as e:
            logger.error(f"Plan parsing error: {str(e)}")
            # Fallback to a minimal valid React plan
            return {
                "project_name": "simple-app",
                "app_title": "Simple App",
                "app_description": "A basic React application.",
                "files": [
                    {
                        "path": "src/App.jsx",
                        "description": "Main application component implementing the requested functionality."
                    }
                ]
            }