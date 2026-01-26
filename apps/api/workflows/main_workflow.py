

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from agents.agent_state import AgentState
from agents.classifier import Classifier
from workflows.class_a_workflow import workflow as class_a_workflow
from utils.logger import Logger
from config import Config

logger = Logger(__name__)

class MainWorkflow:
    """Main workflow that routes to appropriate class-specific workflow"""
    
    def __init__(self):
        logger.step("Main Workflow", "initializing")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.5,
            timeout=60,
            api_key=Config.OPENAI_API_KEY
        )
        
        # Initialize classifier
        self.classifier = Classifier(self.llm)
        
        # Store class workflows (add more as we implement them)
        self.class_workflows = {
            "Class A": class_a_workflow,
            # "Class B": class_b_workflow,  # Future
            # "Class C": class_c_workflow,  # Future
        }
        
        # Build main routing workflow
        self.graph = self._build_main_workflow()
        logger.success("✅ Main Workflow initialized")
    
    def _build_main_workflow(self):
        """Build main workflow with classifier and routing"""
        logger.debug("Building main workflow graph...")
        
        workflow = StateGraph(AgentState)
        
        # Add classifier node
        workflow.add_node("classifier", self.classifier)
        
        # Add class workflow execution nodes
        workflow.add_node("execute_class_a", lambda state: self._execute_class_workflow(state, "Class A"))
        # Add more as: workflow.add_node("execute_class_b", lambda state: self._execute_class_workflow(state, "Class B"))
        
        # Set entry point
        workflow.set_entry_point("classifier")
        
        # Add conditional routing
        workflow.add_conditional_edges(
            "classifier",
            self._route_to_class_workflow,
            {
                "clarification_needed": END,
                "no_class_matched": END,
                "unsupported_class": END,
                "Class A": "execute_class_a",
                # "Class B": "execute_class_b",  # When implemented
                # "Class C": "execute_class_c",  # When implemented
            }
        )
        
        # Connect class workflows to END
        workflow.add_edge("execute_class_a", END)
        # workflow.add_edge("execute_class_b", END)  # When implemented
        
        # Compile graph
        compiled_graph = workflow.compile()
        logger.success("✅ Main workflow graph compiled successfully")
        
        return compiled_graph
    
    def _route_to_class_workflow(self, state: AgentState):
        """Route to appropriate class workflow"""
        

        if state.needs_clarification:
            logger.route(state.detected_class, "clarify")
            return "clarification_needed"
        
        if state.detected_class == "Unable to determine":
            logger.route(state.detected_class, "reject")
            return "no_class_matched"
        
        # Check if this class is implemented
        if state.detected_class in self.class_workflows:
            logger.route(state.detected_class, "route")
            return state.detected_class
        else:
            logger.route(state.detected_class, "unsupported")
            return "unsupported_class"
    

    def _execute_class_workflow(self, state: AgentState, class_name: str):
        """Execute the appropriate class workflow"""
        logger.info(f"🚀 Executing {class_name} workflow...")
        
        workflow = self.class_workflows.get(class_name)
        if not workflow:
            logger.error(f"❌ No workflow found for {class_name}")
            return {
                "messages": state.messages,
                "files": [],
                "detected_class": class_name,
                "needs_clarification": False,
                "type": "unsupported_class",
                "message": f"{class_name} is not currently supported. Only Class A (frontend-only apps) are available at this time."
            }
        
        # Convert AgentState to dict with classification info
        state_dict = {
            "messages": state.messages,
            "files": state.files,
            "iteration": state.iteration,
            "max_iterations": state.max_iterations,
            "approved": state.approved,
            # Pass classification results from main workflow
            "detected_class": state.detected_class,
            "confidence": state.confidence,
            "needs_clarification": state.needs_clarification,
            "clarification_question": state.clarification_question,
            "app_requirements": state.app_requirements
        }
        
        # Execute the class-specific workflow (NO classifier inside)
        result = workflow.invoke(state_dict)
        
        # Add metadata
        result["executed_class"] = class_name
        result["main_workflow"] = True
        
        return result
    
    
    def invoke(self, inputs: dict):
        """Execute the main workflow"""
        logger.workflow_start("Main Workflow", str(inputs.get("messages", [])))
        logger.step("Main Workflow Execution", "started")
        
        try:
            result = self.graph.invoke(inputs)
            
            # Check if the result indicates an unsupported class
            # (This can happen if _execute_class_workflow returns unsupported)
            if result.get("type") == "unsupported_class":
                detected_class = result.get("detected_class", "Unknown")
                logger.info(f"🚫 Unsupported class detected: {detected_class}")
                
                # Ensure proper format for frontend
                result = {
                    "messages": result.get("messages", []),
                    "files": [],
                    "detected_class": detected_class,
                    "needs_clarification": False,
                    "type": "unsupported_class",
                    "message": f"{detected_class} is not currently supported. Only Class A (frontend-only apps) are available at this time."
                }
            logger.workflow_end("Main Workflow", result)
            logger.step("Main Workflow Execution", "completed")
            
            if result.get("executed_class"):
                logger.info(f"🎉 Completed {result['executed_class']} workflow")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Main workflow execution failed: {str(e)}")
            raise

# Singleton instance
main_workflow = MainWorkflow()
