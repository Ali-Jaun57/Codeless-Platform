#!/usr/bin/env python3
"""
Quick test for basic functionality
Run with: python quick_test.py
"""

import sys
import os

sys.path.append('apps/api')

def test_basic():
    print("🚀 Quick System Test")
    print("=" * 50)
    
    # Test 1: Basic imports
    print("\n📦 Testing Basic Imports:")
    modules = [
        ("utils.logger", "Logger"),
        ("agents.agent_state", "AgentState"),
        ("agents.classifier", "Classifier"),
        ("workflows.main_workflow", "MainWorkflow"),
    ]
    
    for module, name in modules:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError as e:
            print(f"  ❌ {name}: {e}")
    
    # Test 2: Configuration
    print("\n⚙️ Testing Configuration:")
    from dotenv import load_dotenv
    load_dotenv("apps/api/.env")
    
    required_env_vars = ["OPENAI_API_KEY", "SUPABASE_URL"]
    for var in required_env_vars:
        if os.getenv(var):
            print(f"  ✅ {var}: Set")
        else:
            print(f"  ❌ {var}: Missing")
    
    # Test 3: Logger
    print("\n📝 Testing Logger:")
    from utils.logger import Logger
    test_logger = Logger("quick_test")
    
    try:
        test_logger.info("Test info message")
        test_logger.success("Test success message")
        test_logger.warning("Test warning message")
        print("  ✅ Logger working")
    except Exception as e:
        print(f"  ❌ Logger error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Quick test completed!")

if __name__ == "__main__":
    test_basic()