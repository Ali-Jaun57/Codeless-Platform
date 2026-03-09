

# -------------------------------------------------------------------------------
# CHAT-GPT CLASSIFIER AGENT
# -------------------------------------------------------------------------------



import json
from .agent_state import AgentState
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import Logger
from utils.json_parser import extract_json_from_text

logger = Logger(__name__)

class Classifier:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        logger.step("Classifier Agent", "initialized")

    def classify_prompt(self, user_prompt: str, existing_files_context: str = "", conversation_history: str = "") -> dict:
        """Classify a user prompt into app class, optionally with existing project context and conversation history."""
        logger.step("Classifier", f"classifying: {user_prompt[:50]}...")

        try:
            prompt = self._create_classification_prompt(user_prompt, existing_files_context, conversation_history)
            logger.debug("Calling LLM for classification...")
            response = self.llm.invoke([HumanMessage(content=prompt)])
            logger.success("✅ Classification response received")

            classification = self._parse_classification(response.content)
            logger.classify(user_prompt, classification)
            return classification

        except Exception as e:
            logger.error(f"❌ Classification failed: {str(e)}")
            return {
                "class": "Unable to determine",
                "confidence": "low",
                "needs_clarification": False,
                "app_requirements": f"Classification error: {str(e)}"
            }

    def _create_classification_prompt(self, user_prompt: str, existing_files_context: str = "", conversation_history: str = "") -> str:
        base_prompt = f"""You are an App Classifier AI. Analyze the user's request and classify it into one of these classes:

🟢 CLASS A — Frontend-Only Apps (NO BACKEND)
✅ Capabilities
React / Next.js UI
-Local state only
-No auth
-No database
-No APIs
-No server logic

🧩 Tech
-React
-Tailwind / CSS
-Local state (useState)
-LocalStorage (optional)

📦 Output
-React project files
-ZIP download

🧪 Examples
-Calculator
-Habit tracker
-Todo app
-Counter
-Stopwatch
-Notes app
-Quiz app
-Form builder
-Unit converter
-Expense tracker (local)
-Timer
-Calendar (local)
-Flashcards
-Portfolio site
-Landing page
-Resume builder

🎯 Purpose
-Foundation class-Proves AI can:
-Understand requirements
-Plan UI


🟡 CLASS B — Auth + Database Apps (CRUD)
✅ Capabilities
-User authentication
-Database
-CRUD operations
-Protected routes

🧩 Tech
-NextAuth / Auth.js
-Prisma
-PostgreSQL / SQLite
-API routes
-Server actions

📦 Output
-Full-stack app
-DB schema
-Migration files

🧪 Examples
-Todo app with login
-Habit tracker with accounts
-Notes app with sync
-Expense tracker (cloud)
-Bookmark manager
-Blog CMS
-Task manager
-Feedback system

🎯 Purpose
-Teaches AI data modeling + auth flows

🔵 CLASS C — API-Driven Apps (External Services)
✅ Capabilities
-Third-party APIs
-OAuth
-Webhooks
-External data sync

🧩 Tech
-REST APIs
-OAuth tokens
-API clients
-Server jobs

🧪 Examples
-Weather app
-Stock tracker
-Crypto dashboard
-News aggregator
-YouTube downloader
-GitHub analytics
-Email sender
-WhatsApp bot dashboard

🎯 Purpose
-AI learns real-world integrations

🟣 CLASS D — AI-Powered Apps
✅ Capabilities
-AI agents
-Prompt pipelines
-RAG
-Embeddings
-Tools
-Memory

🧩 Tech
-OpenAI / Claude
-Vector DB (Pinecone, Chroma)
-RAG pipelines
-Tool calling

🧪 Examples
-AI chatbot
-Resume reviewer
-Customer support bot
-Code assistant
-AI tutor
-AI HR assistant
-AI content generator

🎯 Purpose
-AI builds AI products

🔴 CLASS E — Multi-Agent Systems
✅ Capabilities
-Multiple agents
-Planner / Builder / Reviewer agents
-Task delegation
-Self-correction

🧩 Tech
-Agent orchestration
-Memory per agent
-Task graphs

🧪 Examples
-Auto SaaS builder
-Autonomous researcher
-AI startup generator
-AI dev team simulation

🎯 Purpose
-AI behaves like a team

⚫ CLASS F — Production SaaS Platforms
✅ Capabilities
-Multi-tenant
-Billing
-Roles & permissions
-Monitoring
-CI/CD

🧩 Tech
-Stripe
-RBAC
-Background jobs
-Caching
-Logging

🧪 Examples
-SaaS like Notion
-SaaS like Lovable.dev
-SaaS like Vercel
-AI platforms

🎯 Purpose
-Build real companies

🧭 CLASS G — Self-Improving AI Systems
✅ Capabilities
-Self-evaluation
-Self-refinement
-Learning from failures
-Code feedback loop

🧩 Tech
-Evaluation agents
-Test generation
-Repair loops

🧪 Examples:
-Self-fixing code AI
-Auto-refactoring AI
-Long-running AI workers

🎯 Purpose
-AI that gets better over time
"""

        # Insert conversation history if provided
        if conversation_history:
            history_block = f"""
CONVERSATION HISTORY (previous messages):
{conversation_history}

Please consider the entire conversation context when classifying the new request. The user may be referring to a previously generated app or asking for changes to an existing project.
"""
            base_prompt += history_block

        # Insert existing project context if provided
        if existing_files_context:
            context_block = f"""
EXISTING PROJECT CONTEXT:
The user already has an existing project with the following files:
{existing_files_context}

Please consider this context when classifying the new request. The new request may be an enhancement, fix, or addition to the current project.
"""
            base_prompt += context_block

        user_part = f"""
USER REQUEST: "{user_prompt}"

INSTRUCTIONS:
1. Determine which class best matches the request, taking into account the conversation history and existing project context.
2. If uncertain, ask ONE clarifying question to determine class.
3. If no class matches, explain why.

OUTPUT RULES:
- Output MUST be valid JSON
- NO markdown, NO explanations
- JSON format exactly:
{{
  "class": "Class A" OR "Class B" OR "Class C" OR "Class D" OR "Class E" OR "Class F" OR "Class G" OR "Unable to determine",
  "confidence": "high/medium/low",
  "needs_clarification": true/false,
  "clarification_question": "Question to ask user" (if needs_clarification=true),
  "app_requirements": "Brief summary of app requirements" (if no class matched)
}}

EXAMPLES:
1. For "I want a simple calculator app": {{"class": "Class A", "confidence": "high", "needs_clarification": false}}
2. For "Build me a weather app": {{"class": "Class C", "confidence": "high", "needs_clarification": false}}
3. For "I need a complex business platform": {{"class": "Class F", "confidence": "medium", "needs_clarification": true, "clarification_question": "Will this need user authentication and payment processing?"}}
4. For "Make me an app that reads minds": {{"class": "Unable to determine", "confidence": "high", "needs_clarification": false, "app_requirements": "Request requires capabilities beyond current technology (mind reading)"}}

Now output the JSON classification:"""

        return base_prompt + user_part

    def _parse_classification(self, raw_content: str) -> dict:
        try:
            data = extract_json_from_text(raw_content)

            if "class" not in data:
                raise ValueError("Missing 'class' field")

            class_name = str(data["class"]).strip()
            valid_classes = ["Class A", "Class B", "Class C", "Class D",
                           "Class E", "Class F", "Class G", "Unable to determine"]

            if class_name not in valid_classes:
                logger.warning(f"Invalid class '{class_name}', defaulting to 'Unable to determine'")
                class_name = "Unable to determine"

            return {
                "class": class_name,
                "confidence": data.get("confidence", "medium"),
                "needs_clarification": data.get("needs_clarification", False),
                "clarification_question": data.get("clarification_question", ""),
                "app_requirements": data.get("app_requirements", "")
            }

        except Exception as e:
            logger.error(f"Classification parsing error: {str(e)}")
            return {
                "class": "Unable to determine",
                "confidence": "low",
                "needs_clarification": False,
                "app_requirements": f"Classification parsing failed: {str(e)}"
            }

    def __call__(self, state: 'AgentState') -> dict:
        logger.step("Classifier", f"started (call)")

        try:
            # Get the latest user message
            user_prompt = ""
            for msg in reversed(state.messages):
                if isinstance(msg, HumanMessage):
                    user_prompt = msg.content
                    break

            if not user_prompt:
                logger.warning("⚠️ No user prompt found")
                return self._default_response(state)

            # Build conversation history (excluding the current user message)
            conversation_history = self._build_conversation_history(state.messages)

            # Build existing files context if enhancement mode
            existing_files_context = ""
            if state.is_enhancement and state.existing_files:
                file_list = []
                for f in state.existing_files:
                    path = f.get("path", "")
                    content = f.get("content", "")
                    file_list.append(f"--- {path} ---\n{content}\n")
                existing_files_context = "\n".join(file_list)
                logger.info(f"📁 Including {len(state.existing_files)} existing files with content in classifier context")

            # Classify the prompt with context and history
            classification = self.classify_prompt(user_prompt, existing_files_context, conversation_history)

            # Update state with classification results
            new_state = {
                "messages": state.messages + [AIMessage(content=json.dumps(classification))],
                "detected_class": classification.get("class"),
                "confidence": classification.get("confidence"),
                "needs_clarification": classification.get("needs_clarification", False),
                "clarification_question": classification.get("clarification_question", ""),
                "app_requirements": classification.get("app_requirements", "")
            }

            logger.info(f"📊 Classification complete: {classification.get('class')}")
            return new_state

        except Exception as e:
            logger.error(f"❌ Classifier __call__ failed: {str(e)}")
            return self._default_response(state)

    def _build_conversation_history(self, messages: list) -> str:
        """Build a readable conversation history string, excluding the very last user message (which is the current prompt)."""
        lines = []
        # We'll iterate in order and stop before the last user message if needed.
        # Simpler: just take all messages except the last one (the current prompt).
        # But to keep it readable, we'll include all but mark the last as "current".
        # Actually, we want to give context, so include everything, but maybe truncate.
        # We'll include all messages, but the classifier prompt already includes the current user prompt separately.
        for msg in messages[:-1]:   # exclude the last message (current prompt) because it's passed separately
            if isinstance(msg, HumanMessage):
                lines.append(f"user: {msg.content}")
            elif isinstance(msg, AIMessage):
                content = msg.content
                if len(content) > 500:
                    content = content[:500] + "..."
                lines.append(f"assistant: {content}")
        return "\n".join(lines)

    def _default_response(self, state):
        return {
            "messages": state.messages + [AIMessage(content=json.dumps({
                "class": "Unable to determine",
                "confidence": "low",
                "needs_clarification": False,
                "app_requirements": "Classification system error"
            }))],
            "detected_class": "Unable to determine",
            "confidence": "low",
            "needs_clarification": False,
            "app_requirements": "Classification system error"
        }



# -------------------------------------------------------------------------------
# ANTHROPIC CLASSIFIER AGENT
# -------------------------------------------------------------------------------


# import json
# from .agent_state import AgentState
# from langchain_anthropic import ChatAnthropic
# from langchain_core.messages import HumanMessage, AIMessage
# from utils.logger import Logger
# from utils.json_parser import extract_json_from_text

# logger = Logger(__name__)

# class Classifier:
#     def __init__(self, llm: ChatAnthropic):
#         self.llm = llm
#         logger.step("Classifier Agent", "initialized")

#     def classify_prompt(self, user_prompt: str, existing_files_context: str = "", conversation_history: str = "") -> dict:
#         """Classify a user prompt into app class, optionally with existing project context and conversation history."""
#         logger.step("Classifier", f"classifying: {user_prompt[:50]}...")

#         try:
#             prompt = self._create_classification_prompt(user_prompt, existing_files_context, conversation_history)
#             logger.debug("Calling LLM for classification...")
#             response = self.llm.invoke([HumanMessage(content=prompt)])
#             logger.success("✅ Classification response received")

#             classification = self._parse_classification(response.content)
#             logger.classify(user_prompt, classification)
#             return classification

#         except Exception as e:
#             logger.error(f"❌ Classification failed: {str(e)}")
#             return {
#                 "class": "Unable to determine",
#                 "confidence": "low",
#                 "needs_clarification": False,
#                 "app_requirements": f"Classification error: {str(e)}"
#             }

#     def _create_classification_prompt(self, user_prompt: str, existing_files_context: str = "", conversation_history: str = "") -> str:
#         base_prompt = f"""You are an App Classifier AI. Analyze the user's request and classify it into one of these classes:

# 🟢 CLASS A — Frontend-Only Apps (NO BACKEND)
# ✅ Capabilities
# React / Next.js UI
# -Local state only
# -No auth
# -No database
# -No APIs
# -No server logic

# 🧩 Tech
# -React
# -Tailwind / CSS
# -Local state (useState)
# -LocalStorage (optional)

# 📦 Output
# -React project files
# -ZIP download

# 🧪 Examples
# -Calculator
# -Habit tracker
# -Todo app
# -Counter
# -Stopwatch
# -Notes app
# -Quiz app
# -Form builder
# -Unit converter
# -Expense tracker (local)
# -Timer
# -Calendar (local)
# -Flashcards
# -Portfolio site
# -Landing page
# -Resume builder

# 🎯 Purpose
# -Foundation class-Proves AI can:
# -Understand requirements
# -Plan UI


# 🟡 CLASS B — Auth + Database Apps (CRUD)
# ✅ Capabilities
# -User authentication
# -Database
# -CRUD operations
# -Protected routes

# 🧩 Tech
# -NextAuth / Auth.js
# -Prisma
# -PostgreSQL / SQLite
# -API routes
# -Server actions

# 📦 Output
# -Full-stack app
# -DB schema
# -Migration files

# 🧪 Examples
# -Todo app with login
# -Habit tracker with accounts
# -Notes app with sync
# -Expense tracker (cloud)
# -Bookmark manager
# -Blog CMS
# -Task manager
# -Feedback system

# 🎯 Purpose
# -Teaches AI data modeling + auth flows

# 🔵 CLASS C — API-Driven Apps (External Services)
# ✅ Capabilities
# -Third-party APIs
# -OAuth
# -Webhooks
# -External data sync

# 🧩 Tech
# -REST APIs
# -OAuth tokens
# -API clients
# -Server jobs

# 🧪 Examples
# -Weather app
# -Stock tracker
# -Crypto dashboard
# -News aggregator
# -YouTube downloader
# -GitHub analytics
# -Email sender
# -WhatsApp bot dashboard

# 🎯 Purpose
# -AI learns real-world integrations

# 🟣 CLASS D — AI-Powered Apps
# ✅ Capabilities
# -AI agents
# -Prompt pipelines
# -RAG
# -Embeddings
# -Tools
# -Memory

# 🧩 Tech
# -OpenAI / Claude
# -Vector DB (Pinecone, Chroma)
# -RAG pipelines
# -Tool calling

# 🧪 Examples
# -AI chatbot
# -Resume reviewer
# -Customer support bot
# -Code assistant
# -AI tutor
# -AI HR assistant
# -AI content generator

# 🎯 Purpose
# -AI builds AI products

# 🔴 CLASS E — Multi-Agent Systems
# ✅ Capabilities
# -Multiple agents
# -Planner / Builder / Reviewer agents
# -Task delegation
# -Self-correction

# 🧩 Tech
# -Agent orchestration
# -Memory per agent
# -Task graphs

# 🧪 Examples
# -Auto SaaS builder
# -Autonomous researcher
# -AI startup generator
# -AI dev team simulation

# 🎯 Purpose
# -AI behaves like a team

# ⚫ CLASS F — Production SaaS Platforms
# ✅ Capabilities
# -Multi-tenant
# -Billing
# -Roles & permissions
# -Monitoring
# -CI/CD

# 🧩 Tech
# -Stripe
# -RBAC
# -Background jobs
# -Caching
# -Logging

# 🧪 Examples
# -SaaS like Notion
# -SaaS like Lovable.dev
# -SaaS like Vercel
# -AI platforms

# 🎯 Purpose
# -Build real companies

# 🧭 CLASS G — Self-Improving AI Systems
# ✅ Capabilities
# -Self-evaluation
# -Self-refinement
# -Learning from failures
# -Code feedback loop

# 🧩 Tech
# -Evaluation agents
# -Test generation
# -Repair loops

# 🧪 Examples:
# -Self-fixing code AI
# -Auto-refactoring AI
# -Long-running AI workers

# 🎯 Purpose
# -AI that gets better over time
# """

#         # Insert conversation history if provided
#         if conversation_history:
#             history_block = f"""
# CONVERSATION HISTORY (previous messages):
# {conversation_history}

# Please consider the entire conversation context when classifying the new request. The user may be referring to a previously generated app or asking for changes to an existing project.
# """
#             base_prompt += history_block

#         # Insert existing project context if provided
#         if existing_files_context:
#             context_block = f"""
# EXISTING PROJECT CONTEXT:
# The user already has an existing project with the following files:
# {existing_files_context}

# Please consider this context when classifying the new request. The new request may be an enhancement, fix, or addition to the current project.
# """
#             base_prompt += context_block

#         user_part = f"""
# USER REQUEST: "{user_prompt}"

# INSTRUCTIONS:
# 1. Determine which class best matches the request, taking into account the conversation history and existing project context.
# 2. If uncertain, ask ONE clarifying question to determine class.
# 3. If no class matches, explain why.

# OUTPUT RULES:
# - Output MUST be valid JSON
# - NO markdown, NO explanations
# - JSON format exactly:
# {{
#   "class": "Class A" OR "Class B" OR "Class C" OR "Class D" OR "Class E" OR "Class F" OR "Class G" OR "Unable to determine",
#   "confidence": "high/medium/low",
#   "needs_clarification": true/false,
#   "clarification_question": "Question to ask user" (if needs_clarification=true),
#   "app_requirements": "Brief summary of app requirements" (if no class matched)
# }}

# EXAMPLES:
# 1. For "I want a simple calculator app": {{"class": "Class A", "confidence": "high", "needs_clarification": false}}
# 2. For "Build me a weather app": {{"class": "Class C", "confidence": "high", "needs_clarification": false}}
# 3. For "I need a complex business platform": {{"class": "Class F", "confidence": "medium", "needs_clarification": true, "clarification_question": "Will this need user authentication and payment processing?"}}
# 4. For "Make me an app that reads minds": {{"class": "Unable to determine", "confidence": "high", "needs_clarification": false, "app_requirements": "Request requires capabilities beyond current technology (mind reading)"}}

# Now output the JSON classification:"""

#         return base_prompt + user_part

#     def _parse_classification(self, raw_content: str) -> dict:
#         try:
#             data = extract_json_from_text(raw_content)

#             if "class" not in data:
#                 raise ValueError("Missing 'class' field")

#             class_name = str(data["class"]).strip()
#             valid_classes = ["Class A", "Class B", "Class C", "Class D",
#                            "Class E", "Class F", "Class G", "Unable to determine"]

#             if class_name not in valid_classes:
#                 logger.warning(f"Invalid class '{class_name}', defaulting to 'Unable to determine'")
#                 class_name = "Unable to determine"

#             return {
#                 "class": class_name,
#                 "confidence": data.get("confidence", "medium"),
#                 "needs_clarification": data.get("needs_clarification", False),
#                 "clarification_question": data.get("clarification_question", ""),
#                 "app_requirements": data.get("app_requirements", "")
#             }

#         except Exception as e:
#             logger.error(f"Classification parsing error: {str(e)}")
#             return {
#                 "class": "Unable to determine",
#                 "confidence": "low",
#                 "needs_clarification": False,
#                 "app_requirements": f"Classification parsing failed: {str(e)}"
#             }

#     def __call__(self, state: 'AgentState') -> dict:
#         logger.step("Classifier", f"started (call)")

#         try:
#             # Get the latest user message
#             user_prompt = ""
#             for msg in reversed(state.messages):
#                 if isinstance(msg, HumanMessage):
#                     user_prompt = msg.content
#                     break

#             if not user_prompt:
#                 logger.warning("⚠️ No user prompt found")
#                 return self._default_response(state)

#             # Build conversation history (excluding the current user message)
#             conversation_history = self._build_conversation_history(state.messages)

#             # Build existing files context if enhancement mode
#             existing_files_context = ""
#             if state.is_enhancement and state.existing_files:
#                 file_list = []
#                 for f in state.existing_files:
#                     path = f.get("path", "")
#                     content = f.get("content", "")
#                     file_list.append(f"--- {path} ---\n{content}\n")
#                 existing_files_context = "\n".join(file_list)
#                 logger.info(f"📁 Including {len(state.existing_files)} existing files with content in classifier context")

#             # Classify the prompt with context and history
#             classification = self.classify_prompt(user_prompt, existing_files_context, conversation_history)

#             # Update state with classification results
#             new_state = {
#                 "messages": state.messages + [AIMessage(content=json.dumps(classification))],
#                 "detected_class": classification.get("class"),
#                 "confidence": classification.get("confidence"),
#                 "needs_clarification": classification.get("needs_clarification", False),
#                 "clarification_question": classification.get("clarification_question", ""),
#                 "app_requirements": classification.get("app_requirements", "")
#             }

#             logger.info(f"📊 Classification complete: {classification.get('class')}")
#             return new_state

#         except Exception as e:
#             logger.error(f"❌ Classifier __call__ failed: {str(e)}")
#             return self._default_response(state)

#     def _build_conversation_history(self, messages: list) -> str:
#         """Build a readable conversation history string, excluding the very last user message (which is the current prompt)."""
#         lines = []
#         for msg in messages[:-1]:   # exclude the last message (current prompt) because it's passed separately
#             if isinstance(msg, HumanMessage):
#                 lines.append(f"user: {msg.content}")
#             elif isinstance(msg, AIMessage):
#                 content = msg.content
#                 if len(content) > 500:
#                     content = content[:500] + "..."
#                 lines.append(f"assistant: {content}")
#         return "\n".join(lines)

#     def _default_response(self, state):
#         return {
#             "messages": state.messages + [AIMessage(content=json.dumps({
#                 "class": "Unable to determine",
#                 "confidence": "low",
#                 "needs_clarification": False,
#                 "app_requirements": "Classification system error"
#             }))],
#             "detected_class": "Unable to determine",
#             "confidence": "low",
#             "needs_clarification": False,
#             "app_requirements": "Classification system error"
#         }