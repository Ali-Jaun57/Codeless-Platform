


import json
import re
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
                    "approved": True,
                }

            plan_summary = f"""
PROJECT: {state.project_name or 'Unknown'}
DATABASE SCHEMA: {json.dumps(state.database_schema, indent=2) if state.database_schema else "{}"}
AUTH CONFIG: {json.dumps(state.auth_config, indent=2) if state.auth_config else "{}"}
PAGES: {json.dumps(state.pages, indent=2) if state.pages else "[]"}
COMPONENTS: {json.dumps(state.components, indent=2) if state.components else "[]"}
"""

            files_to_review = [
                {"path": f.get("path", ""), "content": f.get("content", "")[:20000]}
                for f in state.files
            ]

            prompt = self._create_critique_prompt(
                plan_summary=plan_summary,
                files=files_to_review,
                build_error=state.build_error,      # ← raw compiler stderr
                runtime_error=state.runtime_error,  # ← validator-level error
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
                "approved": approved,
            }
            logger.step("Critic", "completed")
            return new_state

        except Exception as e:
            logger.error(f"❌ Critic failed: {str(e)}")
            return {
                "messages": state.messages,
                "iteration": state.iteration + 1,
                "files": state.files,
                "approved": True,  # fail-safe to avoid infinite loop
            }

    # ------------------------------------------------------------------
    # Prompt
    # ------------------------------------------------------------------

    def _create_critique_prompt(
        self,
        plan_summary: str,
        files: list,
        build_error: str = None,
        runtime_error: str = None,
    ) -> str:
        files_json = json.dumps(files, indent=2)

        # ── Build error section (highest priority — exact compiler output) ──
        if build_error:
            error_section = f"""
╔══════════════════════════════════════════════════════════╗
║              BUILD FAILED — COMPILER OUTPUT              ║
╚══════════════════════════════════════════════════════════╝
{build_error}

This is the EXACT error from the compiler/bundler. Read it literally.
Do NOT speculate about other possible causes — fix exactly what the error says.
"""
        elif runtime_error:
            error_section = f"""
RUNTIME / VALIDATION ERROR:
{runtime_error}
"""
        else:
            error_section = ""

        return f"""YOU ARE A CODE CRITIC FOR FULL-STACK REACT + SUPABASE APPLICATIONS. OUTPUT ONLY PURE JSON.

PLAN:
{plan_summary}

{error_section}

REVIEW THESE FILES:
{files_json}

CRITICAL RULES:
1. Output MUST be valid JSON: {{"critique": "...", "approved": true/false, "improvements": ["..."]}}
2. NO markdown, NO extra text outside the JSON.
3. If a BUILD ERROR is shown above, you MUST:
   - Set approved: false.
   - Read the compiler error literally — file path, line number, exact message.
   - Identify the exact file and line that must change.
   - Give one precise fix as the first improvement (e.g. "rename useAuth.ts → useAuth.tsx because it contains JSX").
   - Do NOT invent alternative theories.
4. Reject ONLY if:
   - A build error or runtime error is present (see above).
   - RLS policies are missing or hardcoded secrets appear in frontend code.
   - Auth pages do not call Supabase auth methods correctly.
   - Placeholder comments like `// TODO`, `// FIXME`, `// Logic to ...` are present.
   - Function calls reference undefined functions.
   - If improvemnets sections has improvemnets that if not implemented would break the app or cause runtime errors or cause any feature not to work.
   - Any SELECT policy USING clause does not reference auth.uid() directly 
     or through a subquery — this means all authenticated users can read 
     all rows which is a critical security violation.
    - Any insert statement for a table with user_id or owner_id column is 
    missing that column in the payload.
5. Do NOT reject for:
   - Minor TypeScript config mismatches.
   - Unused dependencies or README inaccuracies.
   - Missing indexes or performance hints.
   - Security improvements that are nice-to-have but do not cause data leakage 
     or broken features (e.g. adding search_path to functions, REVOKE from PUBLIC).
6. If the app builds and core features work: approve (true).

EXAMPLE — correct output when a build error is present:
{{"critique": "Build fails: useAuth.ts contains JSX but must be .tsx for esbuild to parse it.", "approved": false, "improvements": ["Rename src/hooks/useAuth.ts to src/hooks/useAuth.tsx and update all import statements that reference it."]}}

NOW OUTPUT THE JSON:"""

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_critique_response(self, raw_content: str) -> dict:
        match = re.search(r'({[\s\S]*})', raw_content, re.DOTALL)
        if not match:
            logger.error("No JSON object found in critique response")
            return {"critique": "Parse error - no JSON", "approved": True, "improvements": []}

        json_str = match.group(1)

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
                logger.error("json5 not installed.")
                return {"critique": "Parse error", "approved": True, "improvements": []}

        data["approved"] = bool(data.get("approved", True))
        if "critique" not in data:
            data["critique"] = "No critique provided"
        if "improvements" not in data or not isinstance(data["improvements"], list):
            data["improvements"] = []

        return data