# -------------------------------------------------------------------------------
# CHAT-GPT CLASS-A-WORKFLOW AGENT
# -------------------------------------------------------------------------------


import os
import json
import tempfile
import subprocess
import platform
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
# from agents.agent_state import AgentState
# from agents.planner import Planner
# from agents.coder import Coder
# from agents.critic import Critic
# from agents.validator import Validator
from agents.shared.agent_state import AgentState
from agents.class_a.planner import Planner
from agents.class_a.coder import Coder
from agents.class_a.critic import Critic
from agents.class_a.validator import Validator 
from agents.class_a.uiux import UIUXAgent
from utils.logger import Logger
from config import Config
from langchain_anthropic import ChatAnthropic  
# from agents.uiux import UIUXAgent 

logger = Logger(__name__)

class CodeGenerationWorkflow:
    def __init__(self):
        logger.step("Class A Code Generation Workflow", "initializing")

        # Common LLM parameters (except timeout)
        OpenAIClient = {
            "temperature": 0.5,
            "api_key": Config.OPENAI_API_KEY
        }

        # Planner & Critic: 60s timeout
        planner_llm = ChatOpenAI(model=Config.PLANNER_MODEL, timeout=60, **OpenAIClient)
        critic_llm  = ChatOpenAI(model=Config.CRITIC_MODEL,  timeout=60, **OpenAIClient)

        # Coder: longer timeout (5 minutes) for complex code generation
        coder_llm   = ChatOpenAI(model=Config.CODER_MODEL,   timeout=300, **OpenAIClient)
        # Anthropic LLM for UI/UX
        uiux_llm = ChatAnthropic(
            model=Config.UIUX_MODEL,
            temperature=0.3,               # lower temperature for more focused enhancements
            timeout=600, 
            max_tokens=60000,
            api_key=Config.ANTHROPIC_API_KEY
        )


        logger.debug(f"📌 coder_llm type: {type(coder_llm).__name__}")

        self.planner = Planner(planner_llm)
        self.coder = Coder(coder_llm)
        self.critic = Critic(critic_llm)
        self.validator = Validator()
        self.uiux = UIUXAgent(uiux_llm)  

        self.graph = self._build_workflow()
        logger.success("✅ Code Generation Workflow initialized")

    def _builder_node(self, state: AgentState) -> dict:
        """Writes the current files to a temporary folder and runs npm install && npm run build."""
        logger.step("Builder", "started")
        if not state.files:
            logger.warning("No files to build")
            return {"app_folder": None}

        import time
        folder_name = f"build_{int(time.time())}"
        base_path = os.path.join(tempfile.gettempdir(), "codeless_builds")
        os.makedirs(base_path, exist_ok=True)
        app_folder = os.path.join(base_path, folder_name)

        for file in state.files:
            file_path = os.path.join(app_folder, file["path"])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file["content"])

        npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"

        try:
            logger.info("Installing dependencies...")
            install_result = subprocess.run(
                [npm_cmd, "install", "--silent"],
                cwd=app_folder,
                capture_output=True,
                timeout=180,
                check=False
            )
            if install_result.returncode != 0:
                logger.error(f"npm install failed: {install_result.stderr.decode()}")

            logger.info("Building app...")
            build_result = subprocess.run(
                [npm_cmd, "run", "build"],
                cwd=app_folder,
                capture_output=True,
                text=True,
                timeout=180,
                check=False
            )
            if build_result.returncode != 0:
                logger.error(f"Build failed: {build_result.stderr}")
            else:
                logger.success("Build completed")
        except subprocess.TimeoutExpired:
            logger.error("Build timed out")
        except Exception as e:
            logger.error(f"Build exception: {str(e)}")

        logger.step("Builder", "completed")
        return {"app_folder": app_folder}


    def _should_continue(self, state: AgentState):
        logger.debug("\n🔁 Checking continue condition:")
        logger.debug(f"  Iteration: {state.iteration}/{state.max_iterations}")
        logger.debug(f"  Files count: {len(state.files)}")
        logger.debug(f"  Approved status: {state.approved}")
        logger.debug(f"  Runtime error: {state.runtime_error is not None}")

        # If approved, go to UI/UX enhancement (once)
        if state.approved and len(state.files) > 0:
            logger.info("✅ Critic approved – proceeding to UI/UX enhancement")
            return "uiux"

        # Otherwise, continue if under max iterations and files exist
        if state.iteration >= state.max_iterations:
            logger.info("✅ Reached max iterations")
            return END
        if state.iteration > 0 and len(state.files) == 0:
            logger.warning("⚠️ No files to process")
            return END

        logger.info("↩️ Continuing to coder for improvement")
        return "coder"

    def _build_workflow(self):
        logger.debug("Building workflow graph with validator...")

        workflow = StateGraph(AgentState)

        workflow.add_node("planner", self.planner)
        workflow.add_node("coder", self.coder)
        workflow.add_node("builder", self._builder_node)
        workflow.add_node("validator", self.validator)
        workflow.add_node("critic", self.critic)
        workflow.add_node("uiux", self.uiux) 

        workflow.set_entry_point("planner")

        workflow.add_edge("planner", "coder")
        workflow.add_edge("coder", "builder")
        workflow.add_edge("builder", "validator")
        workflow.add_edge("validator", "critic")

        # workflow.add_conditional_edges(
        #     "critic",
        #     self._should_continue,
        #     {END: END, "coder": "coder"}
        # )

        workflow.add_conditional_edges(
            "critic",
            self._should_continue,
            {
                "coder": "coder",
                "uiux": "uiux",               # when approved
                END: END
            }
        )

        workflow.add_edge("uiux", END) 

        compiled_graph = workflow.compile()
        logger.success("✅ Workflow graph compiled successfully")
        return compiled_graph
    

    # def _build_workflow(self):
    #     logger.debug("Building Class A workflow graph (Planner -> Coder -> Builder -> End)...")

    #     workflow = StateGraph(AgentState)

    #     # 1. Add the specific nodes needed for this flow
    #     workflow.add_node("planner", self.planner)
    #     workflow.add_node("coder", self.coder)
    #     workflow.add_node("builder", self._builder_node) # Using the _builder_node reference from your original code
    #     workflow.add_node("validator", self.validator)


    #     # 2. Set the starting point
    #     workflow.set_entry_point("planner")

    #     # 3. Define the sequential edges
    #     workflow.add_edge("planner", "coder")   # Move from Planner to Coder
    #     workflow.add_edge("coder", "builder")   # Move from Coder to Builder
    #     workflow.add_edge("builder", "validator")
    #     workflow.add_edge("validator", END)    # End the workflow after Validator finishes

    #     # 4. Compile the graph
    #     compiled_graph = workflow.compile()
    #     logger.success("✅ Workflow compiled: Planner -> Coder -> Builder -> Validator -> END")
    #     return compiled_graph

    def invoke(self, inputs: dict):
        logger.step("Workflow Execution", "started")
        logger.debug(f"Inputs: {inputs.keys()}")

        try:
            result = self.graph.invoke(inputs)
            logger.step("Workflow Execution", "completed")

            if result.get("detected_class"):
                logger.info(f"📊 Final classification: {result.get('detected_class')}")
            logger.info(f"📁 Generated files: {len(result.get('files', []))}")
            return result

        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {str(e)}")
            raise

# Singleton instance
workflow = CodeGenerationWorkflow()


# -------------------------------------------------------------------------------
# ANTHROPIC CLASS-A-WORKFLOW AGENT
# -------------------------------------------------------------------------------


# import os
# import json
# import tempfile
# import subprocess
# import platform
# from langgraph.graph import StateGraph, END
# from langchain_anthropic import ChatAnthropic
# # from agents.agent_state import AgentState 
# # from agents.planner import Planner
# # from agents.coder import Coder
# # from agents.critic import Critic
# # from agents.validator import Validator
# from agents.shared.agent_state import AgentState
# from agents.class_a.planner import Planner
# from agents.class_a.coder import Coder
# from agents.class_a.critic import Critic
# from agents.class_a.validator import Validator 
# from agents.class_a.uiux import UIUXAgent
# from utils.logger import Logger
# from config import Config

# logger = Logger(__name__)

# class CodeGenerationWorkflow:
#     def __init__(self):
#         logger.step("Code Generation Workflow", "initializing")

#         # Common LLM parameters (except timeout)
#         base_kwargs = {
#             "temperature": 0.5,
#             "api_key": Config.ANTHROPIC_API_KEY
#         }

#         # Planner & Critic: use Sonnet (or your configured model)
#         planner_llm = ChatAnthropic(
#             model=Config.PLANNER_MODEL,
#             timeout=60,
#             **base_kwargs
#         )
#         critic_llm  = ChatAnthropic(
#             model=Config.CRITIC_MODEL,
#             timeout=60,
#             **base_kwargs
#         )

#         # Coder: use Opus (or your configured model) with longer timeout
#         coder_llm = ChatAnthropic(
#             model=Config.CODER_MODEL,
#             timeout=300,
#             **base_kwargs
#         )

#         logger.debug(f"📌 coder_llm type: {type(coder_llm).__name__}")

#         self.planner = Planner(planner_llm)
#         self.coder = Coder(coder_llm)
#         self.critic = Critic(critic_llm)
#         self.validator = Validator()

#         self.graph = self._build_workflow()
#         logger.success("✅ Code Generation Workflow initialized")

#     def _builder_node(self, state: AgentState) -> dict:
#         """Writes the current files to a temporary folder and runs npm install && npm run build."""
#         logger.step("Builder", "started")
#         if not state.files:
#             logger.warning("No files to build")
#             return {"app_folder": None}

#         import time
#         folder_name = f"build_{int(time.time())}"
#         base_path = os.path.join(tempfile.gettempdir(), "codeless_builds")
#         os.makedirs(base_path, exist_ok=True)
#         app_folder = os.path.join(base_path, folder_name)

#         for file in state.files:
#             file_path = os.path.join(app_folder, file["path"])
#             os.makedirs(os.path.dirname(file_path), exist_ok=True)
#             with open(file_path, "w", encoding="utf-8") as f:
#                 f.write(file["content"])

#         npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"

#         try:
#             logger.info("Installing dependencies...")
#             install_result = subprocess.run(
#                 [npm_cmd, "install", "--silent"],
#                 cwd=app_folder,
#                 capture_output=True,
#                 timeout=180,
#                 check=False
#             )
#             if install_result.returncode != 0:
#                 logger.error(f"npm install failed: {install_result.stderr.decode()}")

#             logger.info("Building app...")
#             build_result = subprocess.run(
#                 [npm_cmd, "run", "build"],
#                 cwd=app_folder,
#                 capture_output=True,
#                 text=True,
#                 timeout=180,
#                 check=False
#             )
#             if build_result.returncode != 0:
#                 logger.error(f"Build failed: {build_result.stderr}")
#             else:
#                 logger.success("Build completed")
#         except subprocess.TimeoutExpired:
#             logger.error("Build timed out")
#         except Exception as e:
#             logger.error(f"Build exception: {str(e)}")

#         logger.step("Builder", "completed")
#         return {"app_folder": app_folder}

#     def _should_continue(self, state: AgentState):
#         logger.debug("\n🔁 Checking continue condition:")
#         logger.debug(f"  Iteration: {state.iteration}/{state.max_iterations}")
#         logger.debug(f"  Files count: {len(state.files)}")
#         logger.debug(f"  Approved status: {state.approved}")
#         logger.debug(f"  Runtime error: {state.runtime_error is not None}")

#         should_end = False

#         if state.iteration >= state.max_iterations:
#             logger.info("✅ Reached max iterations")
#             should_end = True
#         elif state.approved and len(state.files) > 0:
#             logger.info("✅ Critic approved with files")
#             should_end = True
#         elif state.iteration > 0 and len(state.files) == 0:
#             logger.warning("⚠️ No files to process")
#             should_end = True

#         if should_end:
#             logger.info("🏁 ENDING workflow")
#             return END
#         logger.info("↩️ Continuing to coder for improvement")
#         return "coder"

#     def _build_workflow(self):
#         logger.debug("Building workflow graph with validator...")

#         workflow = StateGraph(AgentState)

#         workflow.add_node("planner", self.planner)
#         workflow.add_node("coder", self.coder)
#         workflow.add_node("builder", self._builder_node)
#         workflow.add_node("validator", self.validator)
#         workflow.add_node("critic", self.critic)

#         workflow.set_entry_point("planner")

#         workflow.add_edge("planner", "coder")
#         workflow.add_edge("coder", "builder")
#         workflow.add_edge("builder", "validator")
#         workflow.add_edge("validator", "critic")

#         workflow.add_conditional_edges(
#             "critic",
#             self._should_continue,
#             {END: END, "coder": "coder"}
#         )

#         compiled_graph = workflow.compile()
#         logger.success("✅ Workflow graph compiled successfully")
#         return compiled_graph

#     def invoke(self, inputs: dict):
#         logger.step("Workflow Execution", "started")
#         logger.debug(f"Inputs: {inputs.keys()}")

#         try:
#             result = self.graph.invoke(inputs)
#             logger.step("Workflow Execution", "completed")

#             if result.get("detected_class"):
#                 logger.info(f"📊 Final classification: {result.get('detected_class')}")
#             logger.info(f"📁 Generated files: {len(result.get('files', []))}")
#             return result

#         except Exception as e:
#             logger.error(f"❌ Workflow execution failed: {str(e)}")
#             raise

# # Singleton instance
# workflow = CodeGenerationWorkflow()