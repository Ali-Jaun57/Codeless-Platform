from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from agents.agent_state import AgentState
from agents.planner import Planner
from agents.coder import Coder
from agents.critic import Critic
from agents.classifier import Classifier
from utils.logger import Logger
from config import Config

logger = Logger(__name__)

class EnhancedCodeGenerationWorkflow:
    def __init__(self):
        logger.step("Enhanced Code Generation Workflow", "initializing")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.5,
            timeout=60,
            api_key=Config.OPENAI_API_KEY
        )
        
        # Initialize agents
        self.classifier = Classifier(self.llm)
        self.planner = Planner(self.llm)
        self.coder = Coder(self.llm)
        self.critic = Critic(self.llm)
        
        # Build enhanced workflow graph
        self.graph = self._build_enhanced_workflow()
        logger.success("✅ Enhanced Code Generation Workflow initialized")
    
    def _build_enhanced_workflow(self):
        """Build enhanced workflow with classifier"""
        logger.debug("Building enhanced workflow graph...")
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("classifier", self.classifier)
        workflow.add_node("planner", self.planner)
        workflow.add_node("coder", self.coder)
        workflow.add_node("critic", self.critic)
        
        # Set entry point to classifier
        workflow.set_entry_point("classifier")
        
        # Add conditional routing after classification
        workflow.add_conditional_edges(
            "classifier",
            self._route_after_classification,
            {
                "clarification_needed": END,
                "no_class_matched": END,
                "Class A": "planner",
                "Class B": END,  # Placeholder for now
                "Class C": END,  # Placeholder for now
                "Class D": END,  # Placeholder for now
                "Class E": END,  # Placeholder for now
                "Class F": END,  # Placeholder for now
                "Class G": END   # Placeholder for now
            }
        )
        
        # Add original workflow edges (for Class A)
        workflow.add_edge("planner", "coder")
        workflow.add_edge("coder", "critic")
        
        # Add conditional improvement loop
        workflow.add_conditional_edges(
            "critic",
            self._should_continue,
            {END: END, "coder": "coder"}
        )
        
        # Compile graph
        compiled_graph = workflow.compile()
        logger.success("✅ Enhanced workflow graph compiled successfully")
        
        return compiled_graph
    
    def _route_after_classification(self, state: AgentState):
        """Route based on classification result"""
        logger.debug("\n🔄 Classification Routing Decision:")
        logger.debug(f"  Detected class: {state.detected_class}")
        logger.debug(f"  Confidence: {state.confidence}")
        logger.debug(f"  Needs clarification: {state.needs_clarification}")
        logger.debug(f"  App requirements: {state.app_requirements}")
        
        # Handle clarification needed
        if state.needs_clarification:
            logger.info("❓ Needs clarification from user")
            return "clarification_needed"
        
        # Handle no class matched
        if state.detected_class == "Unable to determine":
            logger.info("🚫 No class matched")
            return "no_class_matched"
        
        # Route to appropriate workflow
        if state.detected_class == "Class A":
            logger.info("✅ Routing to Class A workflow (planner)")
            return "Class A"
        else:
            logger.warning(f"⚠️ Unsupported class: {state.detected_class}")
            logger.info(f"   Defaulting to Class A workflow for now")
            return "Class A"  # Default to Class A for unsupported classes
    
    def _should_continue(self, state: AgentState):
        """Determine if workflow should continue (same as before)"""
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
        """Execute the enhanced workflow"""
        logger.step("Enhanced Workflow Execution", "started")
        logger.debug(f"Inputs: {inputs.keys()}")
        
        try:
            result = self.graph.invoke(inputs)
            logger.step("Enhanced Workflow Execution", "completed")
            
            # Log classification result
            if result.get("detected_class"):
                logger.info(f"📊 Final classification: {result.get('detected_class')}")
            
            logger.info(f"📁 Generated files: {len(result.get('files', []))}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced workflow execution failed: {str(e)}")
            raise

# Singleton instance for enhanced workflow
enhanced_workflow = EnhancedCodeGenerationWorkflow()



