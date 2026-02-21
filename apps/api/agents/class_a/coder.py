# -------------------------------------------------------------------------------
# CHAT-GPT CODER AGENT
# -------------------------------------------------------------------------------



import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import Logger
from utils.json_parser import extract_json_from_text
# from .agent_state import AgentState
# from .templates import TEMPLATE_CONTENTS
from ..shared.agent_state import AgentState
from .templates import TEMPLATE_CONTENTS

logger = Logger(__name__)

class Coder:
    def __init__(self, llm: ChatOpenAI):  # now accepts ChatOpenAI
        self.llm = llm
        logger.step("Coder Agent", "initialized")

    def __call__(self, state: AgentState) -> dict:
        logger.step("Coder", f"started (iteration {state.iteration})")

        try:
            if not state.files:
                logger.warning("⚠️ No files to code, skipping")
                full_files = self._generate_base_templates(state)
                return {"messages": state.messages, "files": full_files}

            file_info = self._prepare_file_info(state.files)
            logger.debug(f"Preparing to code {len(file_info)} custom files")

            conversation_history = self._build_conversation_history(state.messages)

            existing_files_map = {}
            if state.is_enhancement and state.existing_files:
                for f in state.existing_files:
                    existing_files_map[f["path"]] = f.get("content", "")

            prompt = self._create_prompt(file_info, conversation_history, existing_files_map, state.messages)

            # Invoke chat model with full conversation + new prompt
            logger.debug("Calling LLM for coding (chat model)...")
            response = self.llm.invoke(state.messages + [HumanMessage(content=prompt)])
            response_text = response.content
            logger.debug(f"Raw LLM Coding response: {response_text[:500]}...")
            logger.success("✅ LLM coding response received")

            coded_files = self._parse_code_response(response_text)
            logger.debug(f"Generated {len(coded_files)} custom files")

            base_files = self._generate_base_templates(state)

            full_dict = {f["path"]: f for f in base_files}
            for f in coded_files:
                full_dict[f["path"]] = f
            full_files = list(full_dict.values())

            logger.debug(f"Full project: {len(full_files)} files (custom + templates)")

            new_state = {
                "messages": state.messages + [AIMessage(content=response_text)],
                "files": full_files
            }

            logger.step("Coder", "completed")
            return new_state

        except Exception as e:
            logger.error(f"❌ Coder failed: {str(e)}")
            raise

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

    def _generate_base_templates(self, state: AgentState) -> list:
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
                continue

            content = template_content \
                .replace("{{APP_NAME}}", planner_data["project_name"]) \
                .replace("{{APP_TITLE}}", planner_data["app_title"]) \
                .replace("{{APP_DESCRIPTION}}", planner_data["app_description"])

            base_files.append({"path": path, "content": content})

        return base_files

    def _prepare_file_info(self, files: list) -> list:
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

    def _create_prompt(self, file_info: list, conversation_history: str, existing_files_map: dict, messages: list) -> str:
        planner_output = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                try:
                    json.loads(msg.content)
                    planner_output = msg.content
                    break
                except:
                    continue

        existing_content_section = ""
        for file_desc in file_info:
            path = file_desc.split(":")[0].strip()
            if path in existing_files_map:
                existing_content_section += f"\n--- Current content of {path} ---\n{existing_files_map[path]}\n"

        return f"""YOU ARE A CODE GENERATOR FOR CLASS A REACT APPS USING VITE + REACT 18+ + TAILWIND. OUTPUT ONLY PURE JSON.

{conversation_history}

PLANNER OUTPUT:
{planner_output}

{existing_content_section}

TASK: Generate complete, production‑ready code for these files EXACTLY as described:
{json.dumps(file_info, indent=2)}

CRITICAL RULES (FOLLOW STRICTLY – VIOLATIONS WILL BREAK THE BUILD):
1. Output MUST be valid JSON only: {{"files": [{{"path": "filename.ext", "content": "full code"}}]}}
2. NO markdown, NO explanations, NO extra text outside JSON
3. Use MODERN REACT only:
   - Functional components + hooks only (no class components)
   - React 18+ syntax
   - If routing is needed: use React Router DOM v6+ syntax (but prefer single‑page design)
4. **NEVER leave placeholder comments like `// Logic to ...` or `TODO`. Every function you call must be fully implemented in the same file or properly imported.**
5. **Every function you reference must be defined. If you need a helper function, define it in the same file or in `src/utils/utils.js`.**
6. **Allowed lightweight libraries (if needed):** `react-dnd`, `react-dnd-html5-backend`, `interactjs`, `immer`, `uuid`, `date-fns`, `dayjs`, `lodash`, `clsx`. If you use any of these, you MUST include them in the `dependencies` section of package.json.
7. Implement EVERY feature described in the planner’s file descriptions.
8. Code must be secure, correct imports, fully responsive.
9. Compatible with Vite + React + Tailwind template.
10. Generate code for ALL listed files exactly.

When modifying existing files, use the provided current content as a base and apply the described enhancements. Preserve existing functionality unless the description explicitly changes it.

NOW OUTPUT ONLY THE JSON:"""

    def _parse_code_response(self, raw_content: str) -> list:
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




# -------------------------------------------------------------------------------
# ANTHROPIC CODER AGENT
# -------------------------------------------------------------------------------


# import json
# from langchain_anthropic import ChatAnthropic
# from langchain_core.messages import HumanMessage, AIMessage
# from utils.logger import Logger
# from utils.json_parser import extract_json_from_text
# # from .agent_state import AgentState
# # from .templates import TEMPLATE_CONTENTS
# from ..shared.agent_state import AgentState
# from .templates import TEMPLATE_CONTENTS


# logger = Logger(__name__)

# class Coder:
#     def __init__(self, llm: ChatAnthropic):  # now accepts ChatAnthropic
#         self.llm = llm
#         logger.step("Coder Agent", "initialized")

#     def __call__(self, state: AgentState) -> dict:
#         logger.step("Coder", f"started (iteration {state.iteration})")

#         try:
#             if not state.files:
#                 logger.warning("⚠️ No files to code, skipping")
#                 full_files = self._generate_base_templates(state)
#                 return {"messages": state.messages, "files": full_files}

#             file_info = self._prepare_file_info(state.files)
#             logger.debug(f"Preparing to code {len(file_info)} custom files")

#             conversation_history = self._build_conversation_history(state.messages)

#             existing_files_map = {}
#             if state.is_enhancement and state.existing_files:
#                 for f in state.existing_files:
#                     existing_files_map[f["path"]] = f.get("content", "")

#             prompt = self._create_prompt(file_info, conversation_history, existing_files_map, state.messages)

#             # Invoke chat model with full conversation + new prompt
#             logger.debug("Calling LLM for coding (chat model)...")
#             response = self.llm.invoke(state.messages + [HumanMessage(content=prompt)])
#             response_text = response.content
#             logger.debug(f"Raw LLM Coding response: {response_text[:500]}...")
#             logger.success("✅ LLM coding response received")

#             coded_files = self._parse_code_response(response_text)
#             logger.debug(f"Generated {len(coded_files)} custom files")

#             base_files = self._generate_base_templates(state)

#             full_dict = {f["path"]: f for f in base_files}
#             for f in coded_files:
#                 full_dict[f["path"]] = f
#             full_files = list(full_dict.values())

#             logger.debug(f"Full project: {len(full_files)} files (custom + templates)")

#             new_state = {
#                 "messages": state.messages + [AIMessage(content=response_text)],
#                 "files": full_files
#             }

#             logger.step("Coder", "completed")
#             return new_state

#         except Exception as e:
#             logger.error(f"❌ Coder failed: {str(e)}")
#             raise

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

#     def _generate_base_templates(self, state: AgentState) -> list:
#         planner_data = {
#             "project_name": "my-app",
#             "app_title": "My App",
#             "app_description": "A React application built with Vite and Tailwind CSS."
#         }
#         for msg in reversed(state.messages):
#             if isinstance(msg, AIMessage):
#                 try:
#                     data = json.loads(msg.content)
#                     if "project_name" in data:
#                         planner_data = {
#                             "project_name": data.get("project_name", "my-app"),
#                             "app_title": data.get("app_title", "My App"),
#                             "app_description": data.get("app_description", "A React application.")
#                         }
#                         break
#                 except:
#                     continue

#         base_files = []
#         for path, template_content in TEMPLATE_CONTENTS.items():
#             if "BINARY_FILE_CONTENT" in template_content:
#                 continue

#             content = template_content \
#                 .replace("{{APP_NAME}}", planner_data["project_name"]) \
#                 .replace("{{APP_TITLE}}", planner_data["app_title"]) \
#                 .replace("{{APP_DESCRIPTION}}", planner_data["app_description"])

#             base_files.append({"path": path, "content": content})

#         return base_files

#     def _prepare_file_info(self, files: list) -> list:
#         file_info = []
#         for file_item in files:
#             if isinstance(file_item, dict):
#                 path = file_item.get("path", "")
#                 desc = file_item.get("description", "")
#                 if path:
#                     file_info.append(f"{path}: {desc}")
#             elif isinstance(file_item, str):
#                 file_info.append(f"{file_item}: File")
#         return file_info

#     def _create_prompt(self, file_info: list, conversation_history: str, existing_files_map: dict, messages: list) -> str:
#         planner_output = ""
#         for msg in reversed(messages):
#             if isinstance(msg, AIMessage):
#                 try:
#                     json.loads(msg.content)
#                     planner_output = msg.content
#                     break
#                 except:
#                     continue

#         existing_content_section = ""
#         for file_desc in file_info:
#             path = file_desc.split(":")[0].strip()
#             if path in existing_files_map:
#                 existing_content_section += f"\n--- Current content of {path} ---\n{existing_files_map[path]}\n"

#         return f"""YOU ARE A CODE GENERATOR FOR CLASS A REACT APPS USING VITE + REACT 18+ + TAILWIND. OUTPUT ONLY PURE JSON.

# {conversation_history}

# PLANNER OUTPUT:
# {planner_output}

# {existing_content_section}

# TASK: Generate complete, production‑ready code for these files EXACTLY as described:
# {json.dumps(file_info, indent=2)}

# CRITICAL RULES (FOLLOW STRICTLY – VIOLATIONS WILL BREAK THE BUILD):
# 1. Output MUST be valid JSON only: {{"files": [{{"path": "filename.ext", "content": "full code"}}]}}
# 2. NO markdown, NO explanations, NO extra text outside JSON
# 3. Use MODERN REACT only:
#    - Functional components + hooks only (no class components)
#    - React 18+ syntax
#    - If routing is needed: use React Router DOM v6+ syntax (but prefer single‑page design)
# 4. **NEVER leave placeholder comments like `// Logic to ...` or `TODO`. Every function you call must be fully implemented in the same file or properly imported.**
# 5. **Every function you reference must be defined. If you need a helper function, define it in the same file or in `src/utils/utils.js`.**
# 6. **Allowed lightweight libraries (if needed):** `react-dnd`, `react-dnd-html5-backend`, `interactjs`, `immer`, `uuid`, `date-fns`, `dayjs`, `lodash`, `clsx`. If you use any of these, you MUST include them in the `dependencies` section of package.json.
# 7. Implement EVERY feature described in the planner’s file descriptions.
# 8. Code must be secure, correct imports, fully responsive.
# 9. Compatible with Vite + React + Tailwind template.
# 10. Generate code for ALL listed files exactly.

# When modifying existing files, use the provided current content as a base and apply the described enhancements. Preserve existing functionality unless the description explicitly changes it.

# NOW OUTPUT ONLY THE JSON:"""

#     def _parse_code_response(self, raw_content: str) -> list:
#         try:
#             data = extract_json_from_text(raw_content)
#             generated_files = data.get("files", [])

#             processed_files = []
#             for file_item in generated_files:
#                 if isinstance(file_item, dict) and "path" in file_item and "content" in file_item:
#                     processed_files.append(file_item)
#                 else:
#                     logger.warning(f"Invalid file structure: {file_item}")

#             return processed_files

#         except Exception as e:
#             logger.error(f"Code parsing error: {str(e)}")
#             return []