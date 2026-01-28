
# backend/endpoints/generate_project.py
import json
import asyncio
from fastapi import HTTPException
from langchain_core.messages import HumanMessage

from config import Config
from supabase_client import supabase

from utils.logger import Logger

from workflows.main_workflow import main_workflow

logger = Logger(__name__)

class GenerateProjectHandler:
    def __init__(self):
        
        logger.step("Generate Project Handler", "initialized")
    

    async def handle(self, prompt: str):
        """Handle project generation request with classification"""
        logger.step("Project Generation", f"started for prompt: {prompt[:50]}...")
        
        try:
            # Prepare inputs for ENHANCED workflow
            inputs = {
                "messages": [HumanMessage(content=prompt)],
                "files": [],
                "iteration": 0,
                "max_iterations": Config.MAX_ITERATIONS,
                "approved": False,
                "detected_class": None,
                "confidence": None,
                "needs_clarification": False,
                "clarification_question": None,
                "app_requirements": None
            }
            
            logger.debug(f"Starting ENHANCED workflow with timeout: {Config.WORKFLOW_TIMEOUT}s")
            
            # Execute ENHANCED workflow with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(main_workflow.invoke, inputs),
                timeout=Config.WORKFLOW_TIMEOUT
            )
            
            # Get classification info
            detected_class = result.get("detected_class")
            needs_clarification = result.get("needs_clarification", False)
            clarification_question = result.get("clarification_question", "")
            app_requirements = result.get("app_requirements", "")
            
            logger.info(f"📊 Classification: {detected_class}")
            logger.info(f"   Needs clarification: {needs_clarification}")
            
            # Handle clarification needed
            if needs_clarification:
                logger.info(f"   Clarification question: {clarification_question}")
                return {
                    "type": "clarification_needed",
                    "message": clarification_question,
                    "detected_class": detected_class,
                    "confidence": result.get("confidence")
                }
            
            # Handle no class matched
            if detected_class == "Unable to determine":
                logger.info(f"   No class matched: {app_requirements}")
                return {
                    "type": "no_class_matched",
                    "message": f"Unable to determine app class. {app_requirements}",
                    "app_requirements": app_requirements
                }
            
            # Handle unsupported classes (Class B, C, D, E, F, G)
            if detected_class and detected_class != "Class A":
                logger.info(f"   Unsupported class: {detected_class}")
                return {
                    "type": "unsupported_class",
                    "message": f"{detected_class} is not currently supported. Only Class A (frontend-only apps) are available at this time.",
                    "detected_class": detected_class
                }
            
            # Handle successful classification (Class A - return files)
            files = result.get("files", [])
            logger.success(f"✅ Workflow completed: {len(files)} files generated")
            logger.info(f"Final approved: {result.get('approved', False)}")
            logger.info(f"Iterations: {result.get('iteration', 0)}")
            
            # Save to Supabase
            self._save_to_supabase(prompt, files)
            
            return {
                "type": "success",
                "files": files,
                "detected_class": detected_class
            }
            
        except asyncio.TimeoutError:
            logger.error("⏰ Workflow timeout")
            raise HTTPException(
                status_code=504,
                detail="Generation timeout - try simpler prompt"
            )
            
        except Exception as e:
            logger.error(f"❌ Workflow error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    def _save_to_supabase(self, prompt: str, files: list):
        """Save generated project to Supabase"""
        try:
            success = supabase.save_project(prompt, files)
            if success:
                logger.success("✅ Project saved to Supabase")
            else:
                logger.warning("⚠️ Failed to save project to Supabase")
        except Exception as e:
            logger.error(f"❌ Save error: {str(e)}")

    async def handle_with_clarification(self, original_prompt: str, clarification_answer: str, detected_class: str):
        """Handle a prompt with clarification answer"""
        logger.step("Clarified Project Generation", f"original: {original_prompt[:30]}..., answer: {clarification_answer[:30]}...")
        
        # Combine original prompt with clarification
        combined_prompt = f"Original request: {original_prompt}. Clarification answer: {clarification_answer}. This is a {detected_class} app."
        
        # Now process with the combined context
        return await self.handle(combined_prompt)
    
    

# Handler instance
handler = GenerateProjectHandler()

