




import os
import json
import tempfile
import subprocess
import platform
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from agents.shared.agent_state import AgentState
from agents.class_b.planner import Planner
from agents.class_b.coder import Coder
from agents.class_b.critic import Critic
from agents.class_b.uiux import UIUX
from agents.class_b.validator import Validator
from agents.class_b.deployer import Deployer
from utils.logger import Logger
from config import Config

logger = Logger(__name__)



def _builder_node(state: AgentState, config=None) -> dict:
    logger.step("Builder", "started")
    if not state.files:
        logger.warning("No files to build")
        return {"app_folder": None, "build_error": None}

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
    build_error = None  # ← will hold raw compiler stderr if build fails

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
            err = install_result.stderr.decode(errors="replace")
            logger.error(f"npm install failed: {err}")
            build_error = f"npm install failed:\n{err[:3000]}"

        if not build_error:
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
                # Combine stdout + stderr — vite sometimes puts errors in stdout
                raw = (build_result.stdout or "") + "\n" + (build_result.stderr or "")
                build_error = raw.strip()[:3000]  # truncate to keep prompt sane
                logger.error(f"Build failed:\n{build_error}")
            else:
                logger.success("Build completed")

    except subprocess.TimeoutExpired:
        build_error = "Build timed out after 180 seconds"
        logger.error(build_error)
    except Exception as e:
        build_error = f"Build exception: {str(e)}"
        logger.error(build_error)

    logger.step("Builder", "completed")
    return {
        "app_folder": app_folder,
        "build_error": build_error,   # ← None on success, real stderr on failure
    }



class CodeGenerationWorkflow:
    def __init__(self):
        logger.step("Class B Code Generation Workflow", "initializing")

        base_kwargs = {
            "temperature": 0.5,
            "max_tokens": 128000,
            "api_key": Config.OPENAI_API_KEY,
        }

        # Planner & Critic: 60s timeout
        planner_llm = ChatOpenAI(model=Config.PLANNER_MODEL, timeout=600,  **base_kwargs)
        critic_llm  = ChatOpenAI(model=Config.CRITIC_MODEL,  timeout=600,  **base_kwargs)

        # Coder: longer timeout
        coder_llm   = ChatOpenAI(model=Config.CODER_MODEL,   timeout=600, **base_kwargs)

        # UI/UX: Claude (Anthropic) — same model as Class A
        uiux_llm = ChatAnthropic(
            model=Config.UIUX_MODEL,
            max_tokens=64000,
            api_key=Config.ANTHROPIC_API_KEY,
            timeout=300,
        )

        # Instantiate agents
        self.planner  = Planner(planner_llm)
        self.coder    = Coder(coder_llm)
        self.critic   = Critic(critic_llm)
        self.uiux     = UIUX(uiux_llm)
        self.validator = Validator()   # no LLM needed
        self.deployer  = Deployer()   # no LLM needed

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

        if state.iteration >= 20:
            logger.warning("⚠️ Hard ceiling reached at 20 iterations — forcing end")
            return END

        # If approved — move forward
        if state.approved and len(state.files) > 0 and not state.runtime_error:
            return "uiux"

        # If no files — something is fundamentally broken, stop
        if state.iteration > 0 and len(state.files) == 0:
            return END

        # Otherwise keep going until approved or hard ceiling
        return "coder"



    def _build_workflow(self):
        logger.debug("Building Class B workflow graph...")

        workflow = StateGraph(AgentState)

        # ── Nodes ──────────────────────────────────────────────────────
        workflow.add_node("planner",   self.planner)
        workflow.add_node("coder",     self.coder)
        workflow.add_node("builder",   _builder_node)
        workflow.add_node("validator", self.validator)
        workflow.add_node("critic",    self.critic)
        workflow.add_node("uiux",      self.uiux)       # ← new node
        workflow.add_node("deployer",  self.deployer)

        # ── Entry point ────────────────────────────────────────────────
        workflow.set_entry_point("planner")

        # ── Static edges ───────────────────────────────────────────────
        workflow.add_edge("planner",   "coder")
        workflow.add_edge("coder",     "builder")
        workflow.add_edge("builder",   "validator")
        workflow.add_edge("validator", "critic")

        # ── Conditional edge from critic ───────────────────────────────
        #   approved  → uiux
        #   not ready → coder  (another iteration)
        #   exhausted → END
        workflow.add_conditional_edges(
            "critic",
            self._should_continue,
            {
                "uiux":    "uiux",
                "coder":   "coder",
                END:       END,
            }
        )

        # ── uiux → deployer → END ─────────────────────────────────────
        workflow.add_edge("uiux",     "deployer")
        workflow.add_edge("deployer", END)

        compiled_graph = workflow.compile()
        logger.success("✅ Class B workflow graph compiled successfully")
        return compiled_graph



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