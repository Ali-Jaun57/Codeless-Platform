# backend/endpoints/generate_project.py
import json
import asyncio
from fastapi import HTTPException
from langchain_core.messages import HumanMessage
from openai import OpenAI
from config import Config
from supabase_client import supabase
from workflows.code_generation import workflow
from utils.logger import Logger

logger = Logger(__name__)

class GenerateProjectHandler:
    def __init__(self):
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        logger.step("Generate Project Handler", "initialized")
    
    async def handle(self, prompt: str):
        """Handle project generation request"""
        logger.step("Project Generation", f"started for prompt: {prompt[:50]}...")
        
        try:
            # Prepare inputs for workflow
            inputs = {
                "messages": [HumanMessage(content=prompt)],
                "files": [],
                "iteration": 0,
                "approved": False,
                "max_iterations": Config.MAX_ITERATIONS
            }
            
            logger.debug(f"Starting workflow with timeout: {Config.WORKFLOW_TIMEOUT}s")
            
            # Execute workflow with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(workflow.invoke, inputs),
                timeout=Config.WORKFLOW_TIMEOUT
            )
            
            files = result.get("files", [])
            logger.success(f"✅ Workflow completed: {len(files)} files generated")
            logger.info(f"Final approved: {result.get('approved', False)}")
            logger.info(f"Iterations: {result.get('iteration', 0)}")
            
            # Save to Supabase
            self._save_to_supabase(prompt, files)
            
            # Handle empty result with fallback
            if not files:
                logger.warning("⚠️ Workflow returned empty files, using fallback...")
                files = await self._fallback_generation(prompt)
            
            return {"files": files}
            
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
    
    async def _fallback_generation(self, prompt: str) -> list:
        """Fallback generation using direct OpenAI API"""
        logger.step("Fallback Generation", "started")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Generate a complete project as JSON: {\"files\": [{\"path\": \"file.js\", \"content\": \"code\"}]}"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5
            )
            
            data = json.loads(response.choices[0].message.content)
            files = data.get("files", [])
            logger.success(f"✅ Fallback generated {len(files)} files")
            return files
            
        except Exception as e:
            logger.error(f"❌ Fallback generation failed: {str(e)}")
            return []

# Handler instance
handler = GenerateProjectHandler()