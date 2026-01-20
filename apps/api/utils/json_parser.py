# backend/utils/json_parser.py
import json
from typing import Any, Dict
from .logger import Logger

logger = Logger(__name__)

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Extract JSON object from text, handling markdown and other wrappers"""
    logger.debug(f"Extracting JSON from text (first 200 chars): {text[:200]}...")
    
    try:
        # Try to parse directly first
        return json.loads(text)
    except json.JSONDecodeError:
        # Extract JSON from text
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start != -1 and end != 0:
            json_str = text[start:end]
            logger.debug(f"Extracted JSON substring: {json_str[:200]}...")
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse extracted JSON: {str(e)}")
                raise
        else:
            logger.error("No JSON object found in text")
            raise ValueError("No JSON object found in text")

def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safely parse JSON with fallback"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON, returning default: {text[:100]}...")
        return default