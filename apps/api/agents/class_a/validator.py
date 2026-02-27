import json
import asyncio
from langchain_core.messages import AIMessage
from utils.logger import Logger
from services.validation_service import validation_service
from ..shared.agent_state import AgentState
logger = Logger(__name__)

class Validator:
    def __init__(self):
        logger.step("Class A Validator Agent", "initialized")

    def __call__(self, state: AgentState) -> dict:
        """Synchronous wrapper that runs the async validation in a new event loop."""
        logger.step("Validator", "started")

        if not state.app_folder:
            logger.warning("No app folder available for validation")
            return {
                "messages": state.messages + [AIMessage(content=json.dumps({"validator": "No app folder"}))],
                "runtime_error": None
            }

        # Run the async validation inside a new event loop
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(validation_service.validate_app(state.app_folder))
            loop.close()
        except Exception as e:
            logger.error(f"Validation failed with exception: {str(e)}")
            result = {"success": False, "errors": [f"Validation exception: {str(e)}"], "logs": []}

        error_str = None
        if not result["success"]:
            error_str = "\n".join(result["errors"])
            logger.error(f"Validation failed: {error_str}")

        new_state = {
            "messages": state.messages + [AIMessage(content=json.dumps({"validator": result}))],
            "runtime_error": error_str
        }
        logger.step("Validator", "completed")
        return new_state