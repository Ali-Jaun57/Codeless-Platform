








import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import Logger
from utils.json_parser import extract_json_from_text
from ..shared.agent_state import AgentState
from .templates import TEMPLATE_CONTENTS_B, FOLDER_STRUCTURE_B

# Optional json5 for lenient parsing
try:
    import json5
    HAS_JSON5 = True
except ImportError:
    HAS_JSON5 = False
    json5 = None

logger = Logger(__name__)


class Coder:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        logger.step("Coder (Class B)", "initialized")

    def __call__(self, state: AgentState) -> dict:
        logger.step("Coder", f"started (iteration {state.iteration})")

        try:
            # ------------------------------------------------------------------
            # 1. Generate base templates (always present)
            # ------------------------------------------------------------------
            base_files = self._generate_base_templates(state)
            base_dict = {f["path"]: f for f in base_files}

            # ------------------------------------------------------------------
            # 2. Determine mode: initial generation or enhancement
            # ------------------------------------------------------------------
            if state.iteration == 0:
                # Initial generation: use planner's full file list
                target_files = state.files
                logger.debug(f"Initial generation: {len(target_files)} custom files planned")
                prompt = self._create_initial_prompt(state, target_files)
            else:
                # Enhancement mode: use critic's feedback and current file contents
                logger.info("🔄 Enhancement mode: generating only modified files")
                critique = self._get_latest_critique(state.messages)
                if not critique:
                    logger.warning("No critique found, using default feedback")
                    critique = "Improve the code based on previous issues."

                # Get current content of custom files (from state.files)
                current_files = {f["path"]: f["content"] for f in state.files}
                prompt = self._create_enhancement_prompt(state, critique, current_files)

            logger.debug("Calling LLM for Class B coding...")
            response = self.llm.invoke(state.messages + [HumanMessage(content=prompt)])
            raw_content = response.content

            # Handle list responses (e.g., from models with reasoning blocks)
            if isinstance(raw_content, list):
                # Extract the first text block
                text_parts = []
                for item in raw_content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                if text_parts:
                    response_text = text_parts[0]
                else:
                    # fallback to string representation
                    response_text = str(raw_content)
            else:
                response_text = str(raw_content)

            logger.debug(f"Raw LLM coding response: {response_text}")
            logger.success("✅ LLM coding response received")

            coded_files = self._parse_code_response(response_text)
            logger.debug(f"LLM generated {len(coded_files)} custom files")

            # ------------------------------------------------------------------
            # 3. Merge: base templates + LLM generated + existing (enhancement)
            # ------------------------------------------------------------------
            full_dict = base_dict.copy()          # base templates first
            for f in coded_files:                 # LLM files override base
                full_dict[f["path"]] = f

            # If enhancement mode, also keep any existing files not regenerated
            if state.iteration > 0:
                for path, content in current_files.items():
                    if path not in full_dict:
                        full_dict[path] = {"path": path, "content": content}

            full_files = list(full_dict.values())
            logger.debug(f"Total files after merge: {len(full_files)} (base + custom)")

            # ------------------------------------------------------------------
            # 4. Prepare new state
            # ------------------------------------------------------------------
            new_state = {
                "messages": state.messages + [AIMessage(content=response_text)],
                "files": full_files
            }

            logger.step("Coder", "completed")
            return new_state

        except Exception as e:
            logger.error(f"❌ Coder failed: {str(e)}")
            raise

    # ----------------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------------

    def _generate_base_templates(self, state: AgentState) -> list:
        """Generate files from TEMPLATE_CONTENTS_B with placeholders replaced."""
        base_files = []
        for path, content in TEMPLATE_CONTENTS_B.items():
            content = content \
                .replace("{{PROJECT_NAME}}", state.project_name or "my-app") \
                .replace("{{APP_TITLE}}", state.app_title or "My App") \
                .replace("{{APP_DESCRIPTION}}", state.app_description or "A full-stack app")
            base_files.append({"path": path, "content": content})
        return base_files

    def _prepare_file_info(self, files: list) -> list:
        """Convert file list to simple strings for prompt."""
        file_info = []
        for item in files:
            if isinstance(item, dict):
                path = item.get("path", "")
                desc = item.get("description", "")
                if path:
                    file_info.append(f"{path}: {desc}")
        return file_info

    def _build_conversation_history(self, messages: list) -> str:
        lines = ["\nCONVERSATION HISTORY:"]
        for msg in messages:
            if isinstance(msg, HumanMessage):
                lines.append(f"user: {msg.content}")
            elif isinstance(msg, AIMessage):
                content = msg.content
                if len(content) > 500:
                    content = content[:500] + "..."
                lines.append(f"assistant: {content}")
        return "\n".join(lines)

    def _get_latest_critique(self, messages: list) -> str:
        """Extract the most recent critique from assistant messages."""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                try:
                    data = json.loads(msg.content)
                    if "critique" in data:
                        return data["critique"]
                except:
                    # Maybe it's plain text
                    if msg.content and ("critique" in msg.content.lower() or "improvements" in msg.content.lower()):
                        return msg.content[:500]
        return ""

    def _create_initial_prompt(self, state: AgentState, target_files: list) -> str:
        """Prompt for first iteration: includes full plan and conversation history."""
        file_info = self._prepare_file_info(target_files)
        conversation_history = self._build_conversation_history(state.messages)

        plan_summary = f"""
PROJECT: {state.project_name}
TITLE: {state.app_title}
DESCRIPTION: {state.app_description}

DATABASE SCHEMA:
{json.dumps(state.database, indent=2) if hasattr(state, 'database') and state.database else "{}"}

AUTH CONFIGURATION:
{json.dumps(state.auth, indent=2) if hasattr(state, 'auth') and state.auth else "{}"}

PAGES:
{json.dumps(state.pages, indent=2) if hasattr(state, 'pages') and state.pages else "[]"}

COMPONENTS:
{json.dumps(state.components, indent=2) if hasattr(state, 'components') and state.components else "[]"}

FILES TO GENERATE (with descriptions):
{json.dumps(state.files, indent=2)}
"""

        base_template_paths = list(TEMPLATE_CONTENTS_B.keys())
        base_template_list = "\n".join(f"  - {p}" for p in base_template_paths)

        return f"""YOU ARE A CODE GENERATOR FOR CLASS B FULL-STACK APPS USING REACT + SUPABASE. OUTPUT ONLY PURE JSON.



PLAN SUMMARY:
{plan_summary}

TASK: Generate complete, production‑ready code for these files EXACTLY as described:
{json.dumps(file_info, indent=2)}

CRITICAL RULES (FOLLOW STRICTLY – VIOLATIONS WILL BREAK THE BUILD):
1. Output MUST be valid JSON only: {{"files": [{{"path": "filename.ext", "content": "full code"}}]}}
2. NO markdown, NO explanations, NO extra text outside JSON.
3. Use TypeScript for all .ts and .tsx files.
4. **NEVER leave placeholder comments like `// Logic to ...` or `TODO`. Every function you call must be fully implemented in the same file or properly imported.**
5. **Every function you reference must be defined. If you need a helper function, define it in the same file or in `src/lib/utils.ts` (which is a base template).**
6. For Supabase:
   - The client is already set up in `src/integrations/supabase/client.ts` (base template). Import and use it.
   - Use `@supabase/supabase-js` for database and auth.
   - Use `react-router-dom` for routing.
   - Optionally use `@tanstack/react-query` for data fetching (already in dependencies).
7. Implement EVERY feature described in the planner’s file descriptions.
8. Code must be secure: use RLS, never expose service role keys, validate user input.
9. Compatible with the Vite + React + Tailwind + Supabase template.
10. Generate code for ALL listed files exactly.
11. For SQL migration files:
    - Place them in `supabase/migrations/` with a timestamp prefix (e.g., `20250225000000_create_todos.sql`).
    - Include `CREATE TABLE` statements, `ENABLE ROW LEVEL SECURITY`, and `CREATE POLICY` statements.
    - Use `gen_random_uuid()` for primary keys, and `auth.uid()` in policies.
12. **CRITICAL: Each file object must contain EXACTLY two keys: `path` and `content`. Do not add any extra keys (e.g., `timestamp`, `id`).**


NOW OUTPUT ONLY THE JSON:
"""

    def _create_enhancement_prompt(self, state: AgentState, critique: str, current_files: dict) -> str:
        """Prompt for subsequent iterations: includes critic feedback and current file contents."""
        # Build a list of files that need changes (all custom files from planner)
        file_sections = []
        for path in state.files:  # state.files is the list from planner (paths with descriptions)
            path_str = path["path"]
            content = current_files.get(path_str, "")
            if content:
                # Truncate very long files
                if len(content) > 2000:
                    content = content[:2000] + "... (truncated)"
                file_sections.append(f"--- {path_str} ---\n{content}\n")

        critique_lower = critique.lower()
        base_candidates = [
            "src/main.tsx",
            "src/integrations/supabase/client.ts",
            "src/integrations/supabase/types.ts",
            "src/App.tsx"
        ]
        for base_path in base_candidates:
            if base_path in critique_lower and base_path in TEMPLATE_CONTENTS_B:
                content = TEMPLATE_CONTENTS_B[base_path]
                file_sections.append(f"--- {base_path} (BASE TEMPLATE) ---\n{content}\n")

        files_context = "\n".join(file_sections)


        base_template_paths = list(TEMPLATE_CONTENTS_B.keys())
        base_template_list = "\n".join(f"  - {p}" for p in base_template_paths)

        return f"""YOU ARE A CODE GENERATOR FOR CLASS B FULL-STACK APPS USING REACT + SUPABASE. YOU ARE NOW IN ENHANCEMENT MODE.

PREVIOUS CRITIQUE (you MUST fix these issues):
{critique}

CURRENT FILES (you may modify these; do NOT change other files unless necessary):
{files_context}

BASE TEMPLATE FILES (automatically provided – DO NOT GENERATE):
{base_template_list}

FOLDER STRUCTURE (for reference):
{FOLDER_STRUCTURE_B}

TASK: Generate updated code for the files listed above to fix all issues mentioned in the critique.
- Output ONLY the files that need changes. Files not included will remain unchanged.
- Each file must be a complete, working version with all fixes applied.
- Follow the same coding rules as before (TypeScript, Supabase, RLS, etc.).

CRITICAL RULES:
1. Output MUST be valid JSON only: {{"files": [{{"path": "filename.ext", "content": "full code"}}]}}
2. NO markdown, NO explanations, NO extra text outside JSON.
3. Use TypeScript for all .ts and .tsx files.
4. **NEVER leave placeholder comments.**
5. For Supabase: use the client from `src/integrations/supabase/client.ts`.
6. SQL migration files must be placed in `supabase/migrations/` with a timestamp prefix, and include RLS policies.
7. Each file object must contain EXACTLY two keys: `path` and `content`.

NOW OUTPUT ONLY THE JSON:
"""

    def _parse_code_response(self, raw_content: str) -> list:
        """
        Extract the first complete JSON object from the response and parse it,
        with fallback to json5. Returns list of file dicts, filtering out extra keys.
        """
        # Use non‑greedy match to get the first complete JSON object
        match = re.search(r'({[\s\S]*})', raw_content, re.DOTALL)
        if not match:
            logger.error("No JSON object found in response")
            return []
        json_str = match.group(1)

        # Try standard JSON parsing
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Standard JSON parsing failed: {e}. Trying json5...")
            if HAS_JSON5:
                try:
                    data = json5.loads(json_str)
                except Exception as e2:
                    logger.error(f"json5 also failed: {e2}")
                    return []
            else:
                logger.error("json5 not installed. Please install with `pip install json5`.")
                return []

        generated_files = data.get("files", [])
        processed_files = []
        for file_item in generated_files:
            if isinstance(file_item, dict):
                path = file_item.get("path")
                content = file_item.get("content")
                if path and content is not None:
                    processed_files.append({"path": path, "content": content})
                else:
                    logger.warning(f"File missing path or content: {file_item}")
            else:
                logger.warning(f"Invalid file structure: {file_item}")
        return processed_files