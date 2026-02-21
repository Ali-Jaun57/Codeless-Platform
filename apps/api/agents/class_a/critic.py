# -------------------------------------------------------------------------------
# CHAT-GPT CRITIC AGENT
# -------------------------------------------------------------------------------

import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import Logger
from utils.json_parser import extract_json_from_text
# from .agent_state import AgentState
from ..shared.agent_state import AgentState

logger = Logger(__name__)

class Critic:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        logger.step("Critic Agent", "initialized")

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

            conversation_history = self._build_conversation_history(state.messages)

            planner_output = ""
            for msg in reversed(state.messages):
                if isinstance(msg, AIMessage):
                    try:
                        json.loads(msg.content)
                        planner_output = msg.content
                        break
                    except:
                        continue

            files_to_review = []
            for f in state.files:
                files_to_review.append({
                    "path": f.get("path", ""),
                    "content": f.get("content", "")
                })

            prompt = self._create_prompt(files_to_review, conversation_history, planner_output, state.runtime_error)

            logger.debug("Calling LLM for critique...")
            response = self.llm.invoke(state.messages + [HumanMessage(content=prompt)])
            logger.debug(f"Raw LLM Critique response: {response.content}")
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

    def _create_prompt(self, files_to_review: list, conversation_history: str, planner_output: str, runtime_error: str = None) -> str:
        max_chars_per_file = 200000000000000000000000000000000000000000000000
        truncated_files = []
        for f in files_to_review:
            path = f["path"]
            content = f["content"]
            if len(content) > max_chars_per_file:
                content = content[:max_chars_per_file] + "\n... (truncated)"
            truncated_files.append({"path": path, "content": content})

        runtime_section = ""
        if runtime_error:
            runtime_section = f"\nRUNTIME ERROR DETECTED:\n{runtime_error}\n"

        return f"""YOU ARE A CODE CRITIC. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

{conversation_history}

PLANNER OUTPUT:
{planner_output}

{runtime_section}

REVIEW THESE FILES:
{json.dumps(truncated_files, indent=2)}

CRITICAL RULES:
1. Output MUST be valid JSON parsable by json.loads()
2. NO markdown code blocks (no ```json or ```)
3. NO explanations, comments, or extra text  
4. JSON structure MUST be exactly: {{"critique": "brief feedback", "approved": true/false, "improvements": ["suggestion1", "suggestion2"]}}
5. "approved" MUST be boolean (true/false)
6. **Be strict: Reject any code that contains placeholder comments (e.g., `// Logic to ...`, `TODO`, `FIXME`).**
7. **Check that every function call refers to a defined function (look for `functionName(`) and ensure that function is either imported or defined in the file.**
8. **Flag any missing imports or references to undefined variables.**
9. **If a runtime error is provided above, set `approved: false` and include a suggestion to fix that specific error.**

APPROVAL GUIDELINES:
- Approve (true) if: code is syntactically correct, secure (no eval), imports are valid, logic makes sense, and it fulfills the user's request.
- Reject (false) if: syntax errors, missing imports, broken logic, security issues, placeholder comments, undefined function calls, or any runtime error occurred.

EXAMPLE CORRECT OUTPUT:
{{"critique": "Code is functional but needs to remove eval() for security", "approved": false, "improvements": ["Replace eval() with safe calculation", "Add input validation"]}}

NOW OUTPUT THE JSON:"""

    def _parse_critique_response(self, raw_content: str) -> dict:
        try:
            critique_data = extract_json_from_text(raw_content)
            if "approved" in critique_data:
                critique_data["approved"] = bool(critique_data["approved"])
            return critique_data
        except Exception as e:
            logger.error(f"Critique parsing error: {str(e)}")
            return {"critique": "Parse error", "approved": True, "improvements": []}




# -------------------------------------------------------------------------------
# ANTHROPIC CRITIC AGENT
# -------------------------------------------------------------------------------


# import json
# from langchain_anthropic import ChatAnthropic
# from langchain_core.messages import HumanMessage, AIMessage
# from utils.logger import Logger
# from utils.json_parser import extract_json_from_text
# # from .agent_state import AgentState
# from ..shared.agent_state import AgentState

# logger = Logger(__name__)

# class Critic:
#     def __init__(self, llm: ChatAnthropic):
#         self.llm = llm
#         logger.step("Critic Agent", "initialized")

#     def __call__(self, state: AgentState) -> dict:
#         logger.step("Critic", f"started (iteration {state.iteration})")

#         try:
#             if not state.files:
#                 logger.warning("⚠️ No files to critique")
#                 return {
#                     "messages": state.messages,
#                     "iteration": state.iteration + 1,
#                     "files": state.files,
#                     "approved": True
#                 }

#             conversation_history = self._build_conversation_history(state.messages)

#             planner_output = ""
#             for msg in reversed(state.messages):
#                 if isinstance(msg, AIMessage):
#                     try:
#                         json.loads(msg.content)
#                         planner_output = msg.content
#                         break
#                     except:
#                         continue

#             files_to_review = []
#             for f in state.files:
#                 files_to_review.append({
#                     "path": f.get("path", ""),
#                     "content": f.get("content", "")
#                 })

#             prompt = self._create_prompt(files_to_review, conversation_history, planner_output, state.runtime_error)

#             logger.debug("Calling LLM for critique...")
#             response = self.llm.invoke(state.messages + [HumanMessage(content=prompt)])
#             logger.debug(f"Raw LLM Critique response: {response.content}")
#             logger.success("✅ LLM critique response received")

#             critique_data = self._parse_critique_response(response.content)
#             approved = critique_data.get("approved", False)

#             logger.info(f"Critique result: Approved = {approved}")

#             new_state = {
#                 "messages": state.messages + [AIMessage(content=response.content)],
#                 "iteration": state.iteration + 1,
#                 "files": state.files,
#                 "approved": approved
#             }

#             logger.step("Critic", "completed")
#             return new_state

#         except Exception as e:
#             logger.error(f"❌ Critic failed: {str(e)}")
#             return {
#                 "messages": state.messages + [AIMessage(content=json.dumps({
#                     "critique": "Parse error",
#                     "approved": True,
#                     "improvements": []
#                 }))],
#                 "iteration": state.iteration + 1,
#                 "files": state.files,
#                 "approved": True
#             }

#     def _build_conversation_history(self, messages: list) -> str:
#         lines = ["\nCONVERSATION HISTORY:"]
#         for msg in messages:
#             if isinstance(msg, HumanMessage):
#                 lines.append(f"user: {msg.content}")
#             elif isinstance(msg, AIMessage):
#                 content = msg.content
#                 if len(content) > 500:
#                     content = content[:500] + "..."
#                 lines.append(f"assistant: {content}")
#         return "\n".join(lines)

#     def _create_prompt(self, files_to_review: list, conversation_history: str, planner_output: str, runtime_error: str = None) -> str:
#         max_chars_per_file = 200000000000000000000000000000000000000000000000
#         truncated_files = []
#         for f in files_to_review:
#             path = f["path"]
#             content = f["content"]
#             if len(content) > max_chars_per_file:
#                 content = content[:max_chars_per_file] + "\n... (truncated)"
#             truncated_files.append({"path": path, "content": content})

#         runtime_section = ""
#         if runtime_error:
#             runtime_section = f"\nRUNTIME ERROR DETECTED:\n{runtime_error}\n"

#         return f"""YOU ARE A CODE CRITIC. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

# {conversation_history}

# PLANNER OUTPUT:
# {planner_output}

# {runtime_section}

# REVIEW THESE FILES:
# {json.dumps(truncated_files, indent=2)}

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

# APPROVAL GUIDELINES:
# - Approve (true) if: code is syntactically correct, secure (no eval), imports are valid, logic makes sense, and it fulfills the user's request.
# - Reject (false) if: syntax errors, missing imports, broken logic, security issues, placeholder comments, undefined function calls, or any runtime error occurred.

# EXAMPLE CORRECT OUTPUT:
# {{"critique": "Code is functional but needs to remove eval() for security", "approved": false, "improvements": ["Replace eval() with safe calculation", "Add input validation"]}}

# NOW OUTPUT THE JSON:"""

#     def _parse_critique_response(self, raw_content: str) -> dict:
#         try:
#             critique_data = extract_json_from_text(raw_content)
#             if "approved" in critique_data:
#                 critique_data["approved"] = bool(critique_data["approved"])
#             return critique_data
#         except Exception as e:
#             logger.error(f"Critique parsing error: {str(e)}")
#             return {"critique": "Parse error", "approved": True, "improvements": []}