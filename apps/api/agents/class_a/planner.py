# -------------------------------------------------------------------------------
# CHAT-GPT PLANNER AGENT
# -------------------------------------------------------------------------------

import json
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import Logger
from utils.json_parser import extract_json_from_text
# from .agent_state import AgentState
# from .templates import FOLDER_STRUCTURE, EXAMPLE_OUTPUT
from ..shared.agent_state import AgentState
from .templates import FOLDER_STRUCTURE, EXAMPLE_OUTPUT

logger = Logger(__name__)

class Planner:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        logger.step("Class A Planner Agent", "initialized")

    def __call__(self, state: AgentState) -> dict:
        logger.step("Planner", "started")
        start_time = time.time()

        try:
            user_prompt = ""
            for msg in reversed(state.messages):
                if isinstance(msg, HumanMessage):
                    user_prompt = msg.content
                    break

            if not user_prompt:
                logger.warning("No user prompt found, using fallback")
                user_prompt = "Create a React app"

            logger.debug(f"User prompt: {user_prompt}")

            conversation_history = self._build_conversation_history(state.messages)

            existing_context = ""
            if state.is_enhancement and state.existing_files:
                existing_context = self._build_existing_files_context(state.existing_files)
                logger.info(f"🔄 Enhancement mode: {len(state.existing_files)} existing files")

            prompt = self._create_prompt(user_prompt, conversation_history, existing_context)

            logger.debug("Calling LLM for planning...")
            response = self.llm.invoke([HumanMessage(content=prompt)])
            logger.debug(f"Raw LLM response: {response.content}")
            logger.success("✅ LLM planning response received")

            plan_data = self._parse_plan_response(response.content)
            logger.debug(f"Parsed plan: {len(plan_data.get('files', []))} files to generate")

            new_state = {
                "messages": state.messages + [AIMessage(content=json.dumps(plan_data))],
                "files": plan_data.get("files", []),
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

    def _build_conversation_history(self, messages: list) -> str:
        history_lines = ["\nCONVERSATION HISTORY:"]
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history_lines.append(f"user: {msg.content}")
            elif isinstance(msg, AIMessage):
                content = msg.content
                if len(content) > 500:
                    content = content[:500] + "..."
                history_lines.append(f"assistant: {content}")
        return "\n".join(history_lines)

    def _build_existing_files_context(self, files: list) -> str:
        lines = ["\nEXISTING PROJECT FILES WITH CONTENT:"]
        for f in files:
            path = f.get("path", "")
            content = f.get("content", "")
            lines.append(f"--- {path} ---")
            lines.append(content)
            lines.append("")
        return "\n".join(lines)

    def _create_prompt(self, user_request: str, conversation_history: str, existing_context: str = "") -> str:
        base_prompt = f"""YOU ARE AN EXPERT REACT DEVELOPER SPECIALIZING IN CLASS A FRONTEND-ONLY APPS.

STRICT CLASS A RULES (NEVER VIOLATE):
- Pure frontend only: React + Vite + Tailwind CSS
- NO backend, NO auth, NO database, NO external APIs
- **You MAY use the following lightweight libraries if they help implement the requested features:**
  - `react-dnd` or `react-dnd-html5-backend` for drag‑and‑drop
  - `interactjs` for advanced interactions
  - `immer` for immutable state updates
  - `uuid` for generating IDs
  - `date-fns` or `dayjs` for date handling
  - `lodash` (only specific functions like debounce, throttle)
  - `clsx` or `classnames` for conditional class names
- **Do NOT** use any library that requires a server, database, or authentication (e.g., firebase, axios, react-router-dom is allowed only if explicitly needed).
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
"""

        history_section = f"""
{conversation_history}
"""

        if existing_context:
            enhancement_instruction = f"""
{existing_context}

YOU ARE NOW ENHANCING AN EXISTING PROJECT. The files listed above already exist.
Your task is to plan ONLY THE FILES THAT NEED TO BE ADDED OR MODIFIED to implement the new user request.
- If an existing file needs to be changed, include it in your plan with an updated description.
- If a new file is required, include it.
- DO NOT include files that remain unchanged.
- After generation, the system will merge your new files with the existing ones.
"""
        else:
            enhancement_instruction = ""

        user_part = f"""
USER REQUEST:
{user_request}

OUTPUT ONLY PURE VALID JSON — NO markdown, NO explanations, NO extra text.

REQUIRED JSON FORMAT EXACTLY:
{json.dumps(EXAMPLE_OUTPUT, indent=2)}

In "files_to_generate":
- Use only allowed paths (src/App.jsx, src/components/*.jsx, src/hooks/*.js, src/utils/*.js)
- Every description must be detailed and specific to how it fulfills the user request
- Prioritize exceptional modern UI when user asks for "best" or "beautiful"
- If you decide to use any of the allowed libraries, mention them in the description and they will be added to package.json automatically.

Now create the optimal plan.
"""
        return base_prompt + history_section + enhancement_instruction + user_part

    def _parse_plan_response(self, raw_content: str) -> dict:
        try:
            plan_data = extract_json_from_text(raw_content)

            project_name = plan_data.get("project_name", "my-app").lower().strip()
            app_title = plan_data.get("app_title", "My App").strip()
            app_description = plan_data.get("app_description", "A React application built with Vite and Tailwind CSS.").strip()

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


# -------------------------------------------------------------------------------
# ANTHROPIC PLANNER AGENT
# -------------------------------------------------------------------------------

# import json
# import time
# from langchain_anthropic import ChatAnthropic
# from langchain_core.messages import HumanMessage, AIMessage
# from utils.logger import Logger
# from utils.json_parser import extract_json_from_text
# # from .agent_state import AgentState
# # from .templates import FOLDER_STRUCTURE, EXAMPLE_OUTPUT
# from ..shared.agent_state import AgentState
# from .templates import FOLDER_STRUCTURE, EXAMPLE_OUTPUT


# logger = Logger(__name__)

# class Planner:
#     def __init__(self, llm: ChatAnthropic):
#         self.llm = llm
#         logger.step("Planner Agent", "initialized")

#     def __call__(self, state: AgentState) -> dict:
#         logger.step("Planner", "started")
#         start_time = time.time()

#         try:
#             user_prompt = ""
#             for msg in reversed(state.messages):
#                 if isinstance(msg, HumanMessage):
#                     user_prompt = msg.content
#                     break

#             if not user_prompt:
#                 logger.warning("No user prompt found, using fallback")
#                 user_prompt = "Create a React app"

#             logger.debug(f"User prompt: {user_prompt[:100]}...")

#             conversation_history = self._build_conversation_history(state.messages)

#             existing_context = ""
#             if state.is_enhancement and state.existing_files:
#                 existing_context = self._build_existing_files_context(state.existing_files)
#                 logger.info(f"🔄 Enhancement mode: {len(state.existing_files)} existing files")

#             prompt = self._create_prompt(user_prompt, conversation_history, existing_context)

#             logger.debug("Calling LLM for planning...")
#             response = self.llm.invoke([HumanMessage(content=prompt)])
#             logger.debug(f"Raw LLM response: {response.content}")
#             logger.success("✅ LLM planning response received")

#             plan_data = self._parse_plan_response(response.content)
#             logger.debug(f"Parsed plan: {len(plan_data.get('files', []))} files to generate")

#             new_state = {
#                 "messages": state.messages + [AIMessage(content=json.dumps(plan_data))],
#                 "files": plan_data.get("files", []),
#                 "project_name": plan_data.get("project_name"),
#                 "app_title": plan_data.get("app_title"),
#                 "app_description": plan_data.get("app_description"),
#                 "approved": False,
#                 "iteration": state.iteration
#             }

#             logger.step("Planner", "completed")
#             end_time = time.time()
#             duration_ms = (end_time - start_time) * 1000
#             logger.performance(f"Planner execution", duration_ms)
#             return new_state

#         except Exception as e:
#             logger.error(f"❌ Planner failed: {str(e)}")
#             raise

#     def _build_conversation_history(self, messages: list) -> str:
#         history_lines = ["\nCONVERSATION HISTORY:"]
#         for msg in messages:
#             if isinstance(msg, HumanMessage):
#                 history_lines.append(f"user: {msg.content}")
#             elif isinstance(msg, AIMessage):
#                 content = msg.content
#                 if len(content) > 500:
#                     content = content[:500] + "..."
#                 history_lines.append(f"assistant: {content}")
#         return "\n".join(history_lines)

#     def _build_existing_files_context(self, files: list) -> str:
#         lines = ["\nEXISTING PROJECT FILES WITH CONTENT:"]
#         for f in files:
#             path = f.get("path", "")
#             content = f.get("content", "")
#             lines.append(f"--- {path} ---")
#             lines.append(content)
#             lines.append("")
#         return "\n".join(lines)

#     def _create_prompt(self, user_request: str, conversation_history: str, existing_context: str = "") -> str:
#         base_prompt = f"""YOU ARE AN EXPERT REACT DEVELOPER SPECIALIZING IN CLASS A FRONTEND-ONLY APPS.

# STRICT CLASS A RULES (NEVER VIOLATE):
# - Pure frontend only: React + Vite + Tailwind CSS
# - NO backend, NO auth, NO database, NO external APIs
# - **You MAY use the following lightweight libraries if they help implement the requested features:**
#   - `react-dnd` or `react-dnd-html5-backend` for drag‑and‑drop
#   - `interactjs` for advanced interactions
#   - `immer` for immutable state updates
#   - `uuid` for generating IDs
#   - `date-fns` or `dayjs` for date handling
#   - `lodash` (only specific functions like debounce, throttle)
#   - `clsx` or `classnames` for conditional class names
# - **Do NOT** use any library that requires a server, database, or authentication (e.g., firebase, axios, react-router-dom is allowed only if explicitly needed).
# - Single-page application preferred (everything in one page with <section id="..."> elements)
# - Use <a href="#section-id"> links + CSS smooth scrolling for navigation
# - Only use client-side routing if user explicitly requests multi-page behavior
# - Local state (useState, useEffect, useRef) and localStorage only when explicitly needed

# STRICT FOLDER STRUCTURE (MUST FOLLOW EXACTLY):
# {json.dumps(FOLDER_STRUCTURE, indent=4)}

# FILE PLACEMENT RULES (ENFORCE WITHOUT EXCEPTION):
# - Main application layout and routing logic → ALWAYS src/App.jsx
# - All reusable UI components → src/components/ComponentName.jsx
# - All custom hooks → src/hooks/useSomething.js
# - All utility functions/constants → src/utils/utils.js or specific files
# - NEVER create new top-level folders
# - NEVER place components/hooks/utils outside src/components/, src/hooks/, src/utils/
# - Do NOT plan modifications to base template files (package.json, vite.config.js, index.html, main.jsx, index.css) unless explicitly requested
# - Only plan files inside src/ that are custom to this app
# """

#         history_section = f"""
# {conversation_history}
# """

#         if existing_context:
#             enhancement_instruction = f"""
# {existing_context}

# YOU ARE NOW ENHANCING AN EXISTING PROJECT. The files listed above already exist.
# Your task is to plan ONLY THE FILES THAT NEED TO BE ADDED OR MODIFIED to implement the new user request.
# - If an existing file needs to be changed, include it in your plan with an updated description.
# - If a new file is required, include it.
# - DO NOT include files that remain unchanged.
# - After generation, the system will merge your new files with the existing ones.
# """
#         else:
#             enhancement_instruction = ""

#         user_part = f"""
# USER REQUEST:
# {user_request}

# OUTPUT ONLY PURE VALID JSON — NO markdown, NO explanations, NO extra text.

# REQUIRED JSON FORMAT EXACTLY:
# {json.dumps(EXAMPLE_OUTPUT, indent=2)}

# In "files_to_generate":
# - Use only allowed paths (src/App.jsx, src/components/*.jsx, src/hooks/*.js, src/utils/*.js)
# - Every description must be detailed and specific to how it fulfills the user request
# - Prioritize exceptional modern UI when user asks for "best" or "beautiful"
# - If you decide to use any of the allowed libraries, mention them in the description and they will be added to package.json automatically.

# Now create the optimal plan.
# """
#         return base_prompt + history_section + enhancement_instruction + user_part

#     def _parse_plan_response(self, raw_content: str) -> dict:
#         try:
#             plan_data = extract_json_from_text(raw_content)

#             project_name = plan_data.get("project_name", "my-app").lower().strip()
#             app_title = plan_data.get("app_title", "My App").strip()
#             app_description = plan_data.get("app_description", "A React application built with Vite and Tailwind CSS.").strip()

#             files_raw = plan_data.get("files_to_generate", [])
#             processed_files = []

#             for item in files_raw:
#                 if isinstance(item, str):
#                     processed_files.append({
#                         "path": item,
#                         "description": "Implement this component/file."
#                     })
#                 elif isinstance(item, dict):
#                     path = item.get("path", "").strip()
#                     desc = item.get("description", "No description provided.").strip()
#                     if path:
#                         processed_files.append({
#                             "path": path,
#                             "description": desc
#                         })

#             return {
#                 "project_name": project_name,
#                 "app_title": app_title,
#                 "app_description": app_description,
#                 "files": processed_files
#             }

#         except Exception as e:
#             logger.error(f"Plan parsing error: {str(e)}")
#             return {
#                 "project_name": "simple-app",
#                 "app_title": "Simple App",
#                 "app_description": "A basic React application.",
#                 "files": [
#                     {
#                         "path": "src/App.jsx",
#                         "description": "Main application component implementing the requested functionality."
#                     }
#                 ]
#             }