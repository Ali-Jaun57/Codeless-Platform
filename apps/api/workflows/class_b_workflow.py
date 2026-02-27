import os
import json
import tempfile
import subprocess
import platform
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI          # or Anthropic if you prefer
from agents.shared.agent_state import AgentState
from agents.class_b.planner import Planner        # you'll create these
from agents.class_b.coder import Coder
from agents.class_b.critic import Critic
from agents.class_b.validator import Validator
from agents.class_b.deployer import Deployer      # new agent
from utils.logger import Logger
from config import Config

logger = Logger(__name__)




def _builder_node(state: AgentState, config=None) -> dict:
    logger.step("Builder", "started")
    if not state.files:
        logger.warning("No files to build")
        return {"app_folder": None}

    import time
    folder_name = f"build_{int(time.time())}"
    base_path = os.path.join(tempfile.gettempdir(), "codeless_builds")
    os.makedirs(base_path, exist_ok=True)
    app_folder = os.path.join(base_path, folder_name)

    # Write all generated files
    for file in state.files:
        file_path = os.path.join(app_folder, file["path"])
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file["content"])

    # Create a dummy .env file for the build
    env_path = os.path.join(app_folder, ".env")
    with open(env_path, "w") as f:
        f.write('VITE_SUPABASE_URL="https://dummy.supabase.co"\n')
        f.write('VITE_SUPABASE_ANON_KEY="dummy-anon-key"\n')
    logger.info("Created dummy .env file for build")

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



class CodeGenerationWorkflow:
    def __init__(self):
        logger.step("Class B Code Generation Workflow", "initializing")

        # Set up LLMs for each agent (adjust models as needed)
        base_kwargs = {
            "temperature": 0.5,
            "max_tokens": 128000,
            "api_key": Config.OPENAI_API_KEY,   # or ANTHROPIC_API_KEY
        }

        # Planner & Critic: 60s timeout
        planner_llm = ChatOpenAI(model=Config.PLANNER_MODEL, timeout=60, **base_kwargs)
        critic_llm  = ChatOpenAI(model=Config.CRITIC_MODEL,  timeout=60, **base_kwargs)

        # Coder: longer timeout
        coder_llm   = ChatOpenAI(model=Config.CODER_MODEL,   timeout=300, **base_kwargs)

        # Deployer does not need an LLM (it uses APIs), so no LLM passed.

        # Instantiate agents (you'll create these classes)
        self.planner = Planner(planner_llm)
        self.coder = Coder(coder_llm)
        self.critic = Critic(critic_llm)
        self.validator = Validator()          # no LLM needed
        self.deployer = Deployer()            # new agent, no LLM

        # Build the graph
        self.graph = self._build_workflow()
        logger.success("✅ Class B Code Generation Workflow initialized")




    def _should_continue(self, state: AgentState, config=None) -> str:
        """Decide next step after critic."""
        logger.debug("\n🔁 Checking continue condition for Class B:")
        logger.debug(f"  Iteration: {state.iteration}/{state.max_iterations}")
        logger.debug(f"  Files count: {len(state.files)}")
        logger.debug(f"  Approved status: {state.approved}")
        logger.debug(f"  Runtime error: {state.runtime_error is not None}")

        if state.approved and len(state.files) > 0 and not state.runtime_error:
            logger.info("✅ Critic approved, no runtime errors – proceeding to deployer")
            return "deployer"

        if state.iteration >= state.max_iterations:
            logger.info("✅ Reached max iterations, ending workflow")
            return END
        if state.iteration > 0 and len(state.files) == 0:
            logger.warning("⚠️ No files to process, ending") 
            return END

        logger.info("↩️ Continuing to coder for improvement")
        return "coder"
 


    def _build_workflow(self):
        logger.debug("Building Class B workflow graph...")

        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("planner", self.planner)
        workflow.add_node("coder", self.coder)
        workflow.add_node("builder", _builder_node)
        workflow.add_node("validator", self.validator)
        workflow.add_node("critic", self.critic)
        workflow.add_node("deployer", self.deployer)

        # Set entry point
        workflow.set_entry_point("planner")

        # Define edges
        workflow.add_edge("planner", "coder")
        workflow.add_edge("coder", "builder")
        workflow.add_edge("builder", "validator")
        workflow.add_edge("validator", "critic")

        # Conditional edge from critic
        workflow.add_conditional_edges(
            "critic",
            self._should_continue,
            {
                "coder": "coder",
                "deployer": "deployer",
                END: END
            }
        )

        # Final edge from deployer to END
        workflow.add_edge("deployer", END)

        compiled_graph = workflow.compile()
        logger.success("✅ Class B workflow graph compiled successfully")
        return compiled_graph

    

    # def _build_workflow(self):
    #     logger.debug("Building Class B workflow graph (Planner -> Coder -> Builder -> End)...")

    #     workflow = StateGraph(AgentState)

    #     # 1. Add the specific nodes needed for this flow
    #     workflow.add_node("planner", self.planner)
    #     workflow.add_node("coder", self.coder)
    #     workflow.add_node("builder", _builder_node) # Using the _builder_node reference from your original code
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
        logger.step("Class B Workflow Execution", "started")
        logger.debug(f"Inputs: {inputs.keys()}")

        try:
            result = self.graph.invoke(inputs)
            logger.step("Class B Workflow Execution", "completed")

            if result.get("detected_class"):
                logger.info(f"📊 Final classification: {result.get('detected_class')}")
            logger.info(f"📁 Generated files: {len(result.get('files', []))}")
            if result.get("preview_url"):
                logger.info(f"🌐 Preview URL: {result.get('preview_url')}")
            return result

        except Exception as e:
            logger.error(f"❌ Class B workflow execution failed: {str(e)}")
            raise


# Singleton instance
workflow = CodeGenerationWorkflow()