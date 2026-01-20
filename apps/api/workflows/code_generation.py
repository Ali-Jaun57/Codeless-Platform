# backend/workflows/code_generation.py
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from agents.agent_state import AgentState
from agents.planner import Planner
from agents.coder import Coder
from agents.critic import Critic
from utils.logger import Logger
from config import Config


logger = Logger(__name__)

class CodeGenerationWorkflow:
    def __init__(self):
        logger.step("Code Generation Workflow", "initializing")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.5,
            timeout=60,
            api_key=Config.OPENAI_API_KEY
        )
        
        # Initialize agents
        self.planner = Planner(self.llm)
        self.coder = Coder(self.llm)
        self.critic = Critic(self.llm)
        
        # Build workflow graph
        self.graph = self._build_workflow()
        logger.success("✅ Code Generation Workflow initialized")
    
    def _build_workflow(self):
        """Build and compile the LangGraph workflow"""
        logger.debug("Building workflow graph...")
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("planner", self.planner)
        workflow.add_node("coder", self.coder)
        workflow.add_node("critic", self.critic)
        
        # Set entry point
        workflow.set_entry_point("planner")
        
        # Add edges
        workflow.add_edge("planner", "coder")
        workflow.add_edge("coder", "critic")
        
        # Add conditional edge
        workflow.add_conditional_edges(
            "critic",
            self._should_continue,
            {END: END, "coder": "coder"}
        )
        
        # Compile graph
        compiled_graph = workflow.compile()
        logger.success("✅ Workflow graph compiled successfully")
        
        return compiled_graph
    
    def _should_continue(self, state: AgentState):
        """Determine if workflow should continue"""
        logger.debug("\n🔁 Checking continue condition:")
        logger.debug(f"  Iteration: {state.iteration}/{state.max_iterations}")
        logger.debug(f"  Files count: {len(state.files)}")
        logger.debug(f"  Approved status: {state.approved}")
        
        should_end = False
        
        if state.iteration >= state.max_iterations:
            logger.info("✅ Reached max iterations")
            should_end = True
        
        elif state.approved and len(state.files) > 0:
            logger.info("✅ Critic approved with files")
            should_end = True
        
        elif state.iteration > 0 and len(state.files) == 0:
            logger.warning("⚠️ No files to process")
            should_end = True
        
        if should_end:
            logger.info("🏁 ENDING workflow")
            return END
        
        logger.info("↩️ Continuing to coder for improvement")
        return "coder"
    
    def invoke(self, inputs: dict):
        """Execute the workflow with given inputs"""
        logger.step("Workflow Execution", "started")
        logger.debug(f"Inputs: {inputs.keys()}")
        
        try:
            result = self.graph.invoke(inputs)
            logger.step("Workflow Execution", "completed")
            logger.info(f"Result: {len(result.get('files', []))} files generated")
            return result
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {str(e)}")
            raise

# Singleton instance
workflow = CodeGenerationWorkflow()