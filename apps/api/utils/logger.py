
import sys
from datetime import datetime
from typing import Any

class Logger:
    def __init__(self, name: str):
        self.name = name
        self.colors = {
            'info': '\033[94m',     # Blue
            'success': '\033[92m',  # Green
            'warning': '\033[93m',  # Yellow
            'error': '\033[91m',    # Red
            'debug': '\033[90m',    # Gray
            'reset': '\033[0m'      # Reset
        }
    
    def _log(self, level: str, message: str, *args: Any):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        color = self.colors.get(level, self.colors['reset'])
        
        formatted_message = f"{color}[{timestamp}] [{level.upper()}] [{self.name}]: {message}{self.colors['reset']}"
        
        if args:
            formatted_message += " " + " ".join(str(arg) for arg in args)
        
        print(formatted_message, file=sys.stderr if level == 'error' else sys.stdout)
    
    def info(self, message: str, *args: Any):
        self._log('info', message, *args)
    
    def success(self, message: str, *args: Any):
        self._log('success', message, *args)
    
    def warning(self, message: str, *args: Any):
        self._log('warning', message, *args)
    
    def error(self, message: str, *args: Any):
        self._log('error', message, *args)
    
    def debug(self, message: str, *args: Any):
        self._log('debug', message, *args)
    
    def step(self, step_name: str, status: str = "started"):
        """Special method for workflow steps"""
        emoji = "🟢" if status == "started" else "✅" if status == "completed" else "⚠️"
        self.info(f"{emoji} {step_name} - {status.upper()}")
    
    # NEW: Classification-specific logging methods
    def classify(self, prompt: str, result: dict):
        """Log classification results"""
        class_name = result.get("class", "Unknown")
        confidence = result.get("confidence", "Unknown")
        needs_clarification = result.get("needs_clarification", False)
        
        self.info(f"📊 CLASSIFICATION: '{prompt[:50]}...'")
        self.info(f"   Class: {class_name}")
        self.info(f"   Confidence: {confidence}")
        self.info(f"   Needs clarification: {needs_clarification}")
        
        if needs_clarification:
            question = result.get("clarification_question", "")
            self.info(f"   Clarification question: {question}")
        
        if class_name == "Unable to determine":
            requirements = result.get("app_requirements", "")
            self.warning(f"   No class matched: {requirements}")
    
    def route(self, detected_class: str, action: str):
        """Log routing decisions"""
        emoji = "✅" if action == "route" else "❌" if action == "reject" else "🔄"
        self.info(f"{emoji} ROUTING: {detected_class} -> {action}")
    
    def workflow_start(self, workflow_type: str, prompt: str):
        """Log workflow start"""
        self.info(f"🚀 WORKFLOW START: {workflow_type}")
        self.debug(f"   Prompt: {prompt[:100]}...")
    
    def workflow_end(self, workflow_type: str, result: dict):
        """Log workflow completion"""
        files_count = len(result.get("files", []))
        iterations = result.get("iteration", 0)
        approved = result.get("approved", False)
        
        self.success(f"🏁 WORKFLOW END: {workflow_type}")
        self.info(f"   Files generated: {files_count}")
        self.info(f"   Iterations: {iterations}")
        self.info(f"   Approved: {approved}")
    
    def performance(self, operation: str, duration_ms: float):
        """Log performance metrics"""
        if duration_ms > 1000:
            self.warning(f"⏱️ PERFORMANCE: {operation} took {duration_ms:.0f}ms (SLOW)")
        else:
            self.debug(f"⏱️ PERFORMANCE: {operation} took {duration_ms:.0f}ms")
    
    def validation(self, component: str, status: bool, message: str = ""):
        """Log validation results"""
        emoji = "✅" if status else "❌"
        level = "info" if status else "warning"
        self._log(level, f"{emoji} VALIDATION: {component} - {'PASS' if status else 'FAIL'} {message}")