



import json
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

from utils.logger import Logger
from utils.json_parser import extract_json_from_text
from ..shared.agent_state import AgentState
from .templates import FOLDER_STRUCTURE_B, EXAMPLE_OUTPUT_B, TEMPLATE_CONTENTS_B

logger = Logger(__name__)


class Planner:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        logger.step("Class B Planner Agent", "initialized")

    def __call__(self, state: AgentState) -> dict:
        logger.step("Planner_B", "started")
        start_time = time.time()

        try:
            user_prompt = ""
            for msg in reversed(state.messages):
                if isinstance(msg, HumanMessage):
                    user_prompt = msg.content
                    break

            if not user_prompt:
                logger.warning("No user prompt found, using fallback")
                user_prompt = "Build a full-stack app with authentication and database"

            conversation_history = self._build_conversation_history(state.messages)

            existing_context = ""
            if state.is_enhancement and state.existing_files:
                existing_context = self._build_existing_files_context(state.existing_files)
                logger.info(f"🔄 Enhancement mode: {len(state.existing_files)} existing files")

            prompt = self._create_prompt(user_prompt, conversation_history, existing_context)

            logger.debug("Calling LLM for Class B planning...")
            response = self.llm.invoke([HumanMessage(content=prompt)])
            logger.debug("the llm response is: " + response.content)
            logger.success("✅ LLM planning response received")

            plan_data = self._parse_plan_response(response.content)

            new_state = {
                "messages": state.messages + [AIMessage(content=json.dumps(plan_data))],
                "project_name": plan_data.get("project_name"),
                "app_title": plan_data.get("app_title"),
                "app_description": plan_data.get("app_description"),
                "database": plan_data.get("database"),
                "auth": plan_data.get("auth"),
                "files": plan_data.get("files", []),
                "approved": False,
                "iteration": state.iteration
            }

            duration_ms = (time.time() - start_time) * 1000
            logger.performance("Planner_B execution", duration_ms)
            logger.step("Planner_B", "completed")

            return new_state

        except Exception as e:
            logger.error(f"❌ Planner_B failed: {str(e)}")
            raise

    # -------------------------------------------------------

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

    # -------------------------------------------------------

    def _get_base_template_files(self) -> list:
        """
        Extract base template file paths dynamically from TEMPLATE_CONTENTS_B.
        """
        base_files = []

        if isinstance(TEMPLATE_CONTENTS_B, dict):
            for path in TEMPLATE_CONTENTS_B.keys():
                base_files.append(path)

        return base_files


    def _create_prompt(self, user_request: str, conversation_history: str, existing_context: str = "") -> str:
        base_template_files = self._get_base_template_files()

        base_files_section = "\n".join(f"- {f}" for f in base_template_files)
        base_prompt = f"""
YOU ARE AN EXPERT FULL-STACK ENGINEER SPECIALIZING IN CLASS B APPLICATIONS.

STRICT CLASS B RULES (NEVER VIOLATE):

- Full-stack app using React + TypeScript + Vite
- Supabase (PostgreSQL + Auth)
- CRUD operations
- Protected routes
- RLS policies REQUIRED
- NO hardcoded secrets
- Use environment variables for Supabase keys
- Use only client-side Supabase SDK (no service_role in frontend)
- Clean production-ready architecture

TECH STACK:
- React + TypeScript
- Tailwind CSS
- Supabase
- react-router-dom
- @supabase/supabase-js
- Optional: @tanstack/react-query

STRICT FOLDER STRUCTURE (MUST FOLLOW EXACTLY):
{FOLDER_STRUCTURE_B}

BASE TEMPLATE FILES (ALREADY EXIST — DO NOT GENERATE AGAIN):

{base_files_section}

IMPORTANT:
- The above files are already provided by the system.
- DO NOT include them in "files_to_generate".
- Only include custom files required by the user request.

FILE PLACEMENT RULES (ENFORCE STRICTLY):

- Main routing logic → src/App.tsx
- Pages → src/pages/*.tsx
- Components → src/components/*.tsx
- Hooks → src/hooks/*.ts
- Utilities → src/lib/*.ts
- Types → src/types/*.ts
- Supabase client → src/integrations/supabase/client.ts
- SQL migrations → supabase/migrations/*.sql
- NEVER create new top-level folders
- NEVER rename existing template files
- NEVER modify base template files unless required
- NEVER include files outside of the above structure
- NEVER plan those files that are already included in the base template (TEMPLATE_CONTENTS_B)

SECURITY RULES:

- All tables MUST include RLS policies
- All queries MUST be scoped by auth.uid()
- Protected routes MUST redirect unauthenticated users
- No bypassing RLS
- No external APIs other than Supabase

{conversation_history}
"""

        if existing_context:
            enhancement_instruction = f"""
{existing_context}

YOU ARE ENHANCING AN EXISTING PROJECT.

Plan ONLY:
- New files
- Modified files
- Required SQL migrations

DO NOT include unchanged files.
"""
        else:
            enhancement_instruction = ""

        user_part = f"""
USER REQUEST:
{user_request}

OUTPUT ONLY PURE VALID JSON.
- NO markdown
- NO explanations
- NO extra text
- Response MUST start with {{
- Response MUST end with }}

REQUIRED JSON FORMAT EXACTLY:
{json.dumps(EXAMPLE_OUTPUT_B, indent=2)}

Rules:
- All required top-level fields MUST exist
- Arrays must be arrays (even if empty)
- Do not rename fields
- Do not omit database or auth objects
- files must contain only files that need to be generated or modified
- Each file must include: path + detailed description
- SQL files must include table structure and RLS description

Generate the optimal full-stack plan now.
"""

        return base_prompt + enhancement_instruction + user_part

    # -------------------------------------------------------

    def _parse_plan_response(self, raw_content: str) -> dict:
        try:
            plan_data = extract_json_from_text(raw_content)

            project_name = plan_data.get("project_name", "class-b-app").lower().strip()
            app_title = plan_data.get("app_title", "Class B App").strip()
            app_description = plan_data.get(
                "app_description",
                "A full-stack app with authentication and database."
            ).strip()

            # files_raw = plan_data.get("files", [])
            files_raw = plan_data.get("files_to_generate", [])
            processed_files = []

            for item in files_raw:
                if isinstance(item, dict):
                    path = item.get("path", "").strip()
                    desc = item.get("description", "").strip()
                    if path:
                        processed_files.append({
                            "path": path,
                            "description": desc or "Implement this file as per plan."
                        })

            return {
                "project_name": project_name,
                "app_title": app_title,
                "app_description": app_description,
                "database": plan_data.get("database", {}),
                "auth": plan_data.get("auth", {}),
                "files": processed_files
            }

        except Exception as e:
            logger.error(f"Plan_B parsing error: {str(e)}")
            return {
                "project_name": "fallback-app",
                "app_title": "Fallback App",
                "app_description": "Basic full-stack app.",
                "database": {},
                "auth": {},
                "files": [
                    {
                        "path": "src/App.tsx",
                        "description": "Main routing and provider setup."
                    }
                ]
            }