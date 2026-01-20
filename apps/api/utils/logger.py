# backend/utils/logger.py
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
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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