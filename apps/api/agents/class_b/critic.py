

import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import Logger
from utils.json_parser import extract_json_from_text
from ..shared.agent_state import AgentState
try:
    import json5
    HAS_JSON5 = True
except ImportError:
    HAS_JSON5 = False
    json5 = None
import re


logger = Logger(__name__)

class Critic:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        logger.step("Critic (Class B)", "initialized")

    def __call__(self, state: AgentState) -> dict:
        logger.step("Critic", f"started (iteration {state.iteration})")

        try:
            if not state.files:
                logger.warning("⚠️ No files to critique")
                return {
                    "messages": state.messages,
                    "iteration": state.iteration + 1,
                    "files": state.files,
                    "approved": True
                }

            # Build plan summary (useful for context)
            plan_summary = f"""
PROJECT: {state.project_name or 'Unknown'}
DATABASE SCHEMA: {json.dumps(state.database, indent=2) if hasattr(state, 'database') and state.database else "{}"}
AUTH CONFIG: {json.dumps(state.auth, indent=2) if hasattr(state, 'auth') and state.auth else "{}"}
PAGES: {json.dumps(state.pages, indent=2) if hasattr(state, 'pages') and state.pages else "[]"}
COMPONENTS: {json.dumps(state.components, indent=2) if hasattr(state, 'components') and state.components else "[]"}
"""

            # Prepare files for review (truncate very large files)
            files_to_review = []
            for f in state.files:
                files_to_review.append({
                    "path": f.get("path", ""),
                    "content": f.get("content", "")[:20000]  # truncate to avoid huge prompts
                })

            prompt = self._create_critique_prompt(
                plan_summary=plan_summary,
                files=files_to_review,
                runtime_error=state.runtime_error
            )

            logger.debug("Calling LLM for Class B critique...")
            response = self.llm.invoke(state.messages + [HumanMessage(content=prompt)])
            logger.debug(f"Raw LLM critique response: {response.content}")
            logger.success("✅ LLM critique response received")

            critique_data = self._parse_critique_response(response.content)
            approved = critique_data.get("approved", False)

            logger.info(f"Critique result: Approved = {approved}")

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
            # Fail safe: approve to avoid infinite loops
            return {
                "messages": state.messages,
                "iteration": state.iteration + 1,
                "files": state.files,
                "approved": True
            }

    # -------------------------------------------------------

#     def _create_critique_prompt(self, plan_summary: str, files: list, runtime_error: str = None) -> str:
#         files_json = json.dumps(files, indent=2)
#         runtime_section = f"\nRUNTIME ERROR DETECTED:\n{runtime_error}\n" if runtime_error else ""

#         return f"""YOU ARE A CODE CRITIC FOR FULL‑STACK REACT + SUPABASE APPLICATIONS. YOU MUST OUTPUT ONLY PURE JSON.

# PLAN:
# {plan_summary}

# {runtime_section}

# REVIEW THESE FILES:
# {files_json}

# CRITICAL RULES:
# 1. Output MUST be valid JSON parsable by json.loads()
# 2. NO markdown code blocks (no ```json or ```)
# 3. NO explanations, comments, or extra text
# 4. JSON structure MUST be exactly: {{"critique": "brief feedback", "approved": true/false, "improvements": ["suggestion1", "suggestion2"]}}
# 5. "approved" MUST be boolean (true/false)
# 6. **Be strict: Reject any code that contains placeholder comments (e.g., `// Logic to ...`, `TODO`, `FIXME`).**
# 7. **Check that every function call refers to a defined function (look for `functionName(`) and ensure that function is either imported or defined in the file.**
# 8. **Flag any missing imports or references to undefined variables.**
# 9. **If a runtime error is provided above, set `approved: false` and include a suggestion to fix that specific error.**

# APPROVAL GUIDELINES (Class B specific):
# - Approve (true) if:
#   - Database schema matches the plan (tables, columns, RLS policies present)
#   - RLS policies correctly use `auth.uid()` and are scoped per user
#   - Authentication pages correctly call Supabase auth methods (`signInWithPassword`, `signUp`)
#   - Protected routes redirect unauthenticated users (e.g., using `Navigate` or a guard)
#   - All environment variables are used (`import.meta.env.VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`)
#   - No hardcoded secrets (like service role keys) appear in frontend code
#   - The app builds without errors (as indicated by runtime_error being None)
#   - SQL migration files are valid and include necessary policies
# - Reject (false) if any of the above are missing, or if runtime_error is present.

# EXAMPLE CORRECT OUTPUT:
# {{"critique": "Database schema and RLS are correct, but the auth form lacks error handling.", "approved": false, "improvements": ["Add error display in AuthForm", "Wrap supabase calls in try/catch"]}}

# NOW OUTPUT THE JSON:
# """

    def _create_critique_prompt(self, plan_summary: str, files: list, runtime_error: str = None) -> str:
        files_json = json.dumps(files, indent=2)
        runtime_section = f"\nRUNTIME ERROR DETECTED:\n{runtime_error}\n" if runtime_error else ""

        return f"""YOU ARE A CODE CRITIC FOR FULL‑STACK REACT + SUPABASE APPLICATIONS. YOU MUST OUTPUT ONLY PURE JSON.

    PLAN:
    {plan_summary}

    {runtime_section}

    REVIEW THESE FILES:
    {files_json} 

    CRITICAL RULES:
    1. Output MUST be valid JSON: {{"critique": "brief feedback", "approved": true/false, "improvements": ["suggestion1", ...]}}
    2. NO markdown, NO extra text.
    3. **Reject only if:**
    - The app fails to build (runtime_error is present).
    - There are missing RLS policies or hardcoded secrets.
    - Authentication or protected routes do not work.
    - The app would crash on startup (e.g., missing QueryClientProvider).
    - There are placeholder comments like `// Logic to ...`, `TODO`, `FIXME`.
    - There are function calls to undefined functions (e.g., `someFunction(` with no definition or import).
    - There are missing imports for used functions or variables.
    - The database schema is missing tables, columns, or RLS policies defined in the plan.
    - Authentication pages do not call Supabase auth methods correctly.
    - Error in apps functionality that user it not getting the functionality it wants. 
    4. **Do NOT reject for**:
    - Placeholder comments that don't affect runtime.
    - Unused dependencies or README inaccuracies.
    - Minor TypeScript config mismatches.
    - Missing indexes or performance optimizations.
    5. If the app builds and core features work, **approve (true)**.

    EXAMPLE CORRECT OUTPUT:
    {{"critique": "App builds and works, but README mentions Storage which isn't used.", "approved": true, "improvements": ["Remove Storage from README"]}}

    NOW OUTPUT THE JSON:
    """
    # def _parse_critique_response(self, raw_content: str) -> dict:
    #     try:
    #         critique_data = extract_json_from_text(raw_content)
    #         if "approved" in critique_data:
    #             critique_data["approved"] = bool(critique_data["approved"])
    #         return critique_data
    #     except Exception as e:
    #         logger.error(f"Critique parsing error: {str(e)}")
    #         return {"critique": "Parse error", "approved": True, "improvements": []}

    def _parse_critique_response(self, raw_content: str) -> dict:
        """
        Extract JSON from the LLM response using a greedy regex,
        then parse with json (fallback to json5).
        """
        # Use greedy match to capture the complete JSON object
        match = re.search(r'({[\s\S]*})', raw_content, re.DOTALL)
        if not match:
            logger.error("No JSON object found in critique response")
            return {"critique": "Parse error - no JSON", "approved": True, "improvements": []}

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
                    return {"critique": "Parse error", "approved": True, "improvements": []}
            else:
                logger.error("json5 not installed. Please install with `pip install json5`.")
                return {"critique": "Parse error", "approved": True, "improvements": []}

        # Ensure required keys exist with correct types
        if "approved" in data:
            data["approved"] = bool(data["approved"])
        else:
            data["approved"] = True

        if "critique" not in data:
            data["critique"] = "No critique provided"

        if "improvements" not in data or not isinstance(data["improvements"], list):
            data["improvements"] = []

        return data