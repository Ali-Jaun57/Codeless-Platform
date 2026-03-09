




import os
import shutil
import asyncio
from ..shared.agent_state import AgentState
from utils.logger import Logger
from services.validation_service import validation_service

logger = Logger(__name__)

class Validator:
    def __init__(self):
        logger.step("Validator (Class B)", "initialized")

    def __call__(self, state: AgentState) -> dict:
        logger.step("Validator", "started")

        if not state.app_folder:
            logger.warning("No app folder available for validation")
            return {
                "messages": state.messages,
                "runtime_error": None
            }

        # Ensure .env file exists with dummy values for validation
        env_path = os.path.join(state.app_folder, ".env")
        if not os.path.exists(env_path):
            # Copy from .env.example if available
            example_path = os.path.join(state.app_folder, ".env.example")
            if os.path.exists(example_path):
                shutil.copy(example_path, env_path)
                logger.info("Created .env from .env.example for validation")
            else:
                # Create minimal dummy .env
                with open(env_path, "w") as f:
                    f.write("VITE_SUPABASE_URL=https://dummy.supabase.co\n")
                    f.write("VITE_SUPABASE_ANON_KEY=dummy-key\n")
                logger.info("Created dummy .env file for validation")

        # Run validation service
        try:
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
            "messages": state.messages,
            "runtime_error": error_str
        }
        logger.step("Validator", "completed")
        return new_state