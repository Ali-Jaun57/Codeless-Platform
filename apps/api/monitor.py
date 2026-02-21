
"""
System monitoring and health check
Run with: python monitor.py
"""

import sys
import os
import time
import requests
from datetime import datetime

sys.path.append('.')

from utils.logger import Logger
from config import Config

logger = Logger("monitor")

class SystemMonitor:
    def __init__(self):
        self.services = {
            "api": "http://localhost:8000/health",
            "supabase": Config.SUPABASE_URL,
            "openai": "https://api.openai.com/v1/models"
        }
        
    def check_api(self):
        """Check API health"""
        try:
            response = requests.get(self.services["api"], timeout=5)
            if response.status_code == 200:
                return True, f"API healthy ({response.json().get('status', 'unknown')})"
            else:
                return False, f"API error: {response.status_code}"
        except Exception as e:
            return False, f"API unreachable: {str(e)}"
    
    def check_config(self):
        """Check configuration"""
        issues = []
        
        if not Config.OPENAI_API_KEY or "your-actual" in Config.OPENAI_API_KEY:
            issues.append("OpenAI API key missing or placeholder")
        
        if not Config.SUPABASE_URL or "your-project" in Config.SUPABASE_URL:
            issues.append("Supabase URL missing or placeholder")
        
        if issues:
            return False, f"Config issues: {', '.join(issues)}"
        else:
            return True, "Configuration valid"
    
    def check_agents(self):
        """Check agents can be instantiated"""
        try:
            from agents.classifier import Classifier
            from agents.planner import Planner
            from langchain_openai import ChatOpenAI
            
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=Config.OPENAI_API_KEY
            )
            
            # Test instantiation
            classifier = Classifier(llm)
            planner = Planner(llm)
            
            return True, "Agents initialized successfully"
        except Exception as e:
            return False, f"Agent initialization failed: {str(e)}"
    
    def run_checks(self):
        """Run all system checks"""
        print("🔍 System Health Check")
        print("=" * 50)
        
        checks = [
            ("Configuration", self.check_config),
            ("API Service", self.check_api),
            ("AI Agents", self.check_agents),
        ]
        
        results = []
        
        for check_name, check_func in checks:
            print(f"\n📋 {check_name}:")
            try:
                success, message = check_func()
                if success:
                    print(f"  ✅ {message}")
                    results.append((check_name, True, message))
                else:
                    print(f"  ❌ {message}")
                    results.append((check_name, False, message))
            except Exception as e:
                print(f"  💥 Check failed: {str(e)}")
                results.append((check_name, False, f"Error: {str(e)}"))
        
        # Generate report
        self.generate_report(results)
        
        # Count successes
        success_count = sum(1 for _, success, _ in results if success)
        total_count = len(results)
        
        print(f"\n📊 Summary: {success_count}/{total_count} checks passed")
        
        if success_count == total_count:
            print("🎉 System is healthy!")
            return True
        else:
            print("⚠️ System has issues that need attention")
            return False
    
    def generate_report(self, results):
        """Generate health report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = {
            "timestamp": timestamp,
            "system": "Codeless AI",
            "checks": [
                {
                    "name": name,
                    "status": "PASS" if success else "FAIL",
                    "message": message
                }
                for name, success, message in results
            ]
        }
        
        # Save report
        import json
        with open("health_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📁 Health report saved to: health_report.json")
        
        # Also log with logger
        for name, success, message in results:
            if success:
                logger.success(f"HEALTH CHECK: {name} - PASS")
            else:
                logger.error(f"HEALTH CHECK: {name} - FAIL: {message}")

def main():
    """Run system monitoring"""
    monitor = SystemMonitor()
    
    print("Starting system monitoring...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    healthy = monitor.run_checks()
    
    if healthy: 
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()