#!/usr/bin/env python3
"""
Comprehensive test suite for Codeless AI
Run with: python test_suite.py
"""

import sys
import os
import json
import asyncio
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

class CodelessTestSuite:
    def __init__(self):
        print("🧪 Codeless AI Test Suite")
        print("=" * 60)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }
    
    def run_all_tests(self):
        """Run all test categories"""
        print("\n📋 Running Comprehensive Tests...\n")
        
        # Test categories
        test_categories = [
            ("Classifier Tests", self.test_classifier),
            ("Agent Tests", self.test_agents),
            ("Workflow Tests", self.test_workflows),
            ("Integration Tests", self.test_integration),
            ("Performance Tests", self.test_performance),
        ]
        
        for category_name, test_func in test_categories:
            print(f"\n{'='*50}")
            print(f"📁 {category_name}")
            print(f"{'='*50}")
            test_func()
        
        self.print_summary()
    
    def test_classifier(self):
        """Test classifier agent"""
        print("🧠 Testing Classifier Agent...")
        
        from agents.classifier import Classifier
        
        classifier = Classifier(self.llm)
        
        test_cases = [
            {
                "prompt": "I want a simple calculator app",
                "expected_class": "Class A",
                "description": "Simple frontend app"
            },
            {
                "prompt": "Build a todo app with user login",
                "expected_class": "Class B",
                "description": "App with authentication"
            },
            {
                "prompt": "Create a weather app using API",
                "expected_class": "Class C",
                "description": "API-driven app"
            },
            {
                "prompt": "Make an AI chatbot",
                "expected_class": "Class D",
                "description": "AI-powered app"
            },
            {
                "prompt": "Build a complex SaaS platform",
                "expected_class": "Class F",
                "description": "Complex SaaS"
            },
        ]
        
        for test_case in test_cases:
            print(f"\n  📝 Test: {test_case['description']}")
            print(f"    Prompt: '{test_case['prompt'][:50]}...'")
            
            try:
                result = classifier.classify_prompt(test_case["prompt"])
                detected_class = result.get("class")
                confidence = result.get("confidence")
                
                if detected_class == test_case["expected_class"]:
                    self.test_results["passed"] += 1
                    print(f"    ✅ PASS: Detected {detected_class} (confidence: {confidence})")
                else:
                    self.test_results["failed"] += 1
                    print(f"    ❌ FAIL: Expected {test_case['expected_class']}, got {detected_class}")
                    
            except Exception as e:
                self.test_results["failed"] += 1
                print(f"    💥 ERROR: {str(e)}")
    
    def test_agents(self):
        """Test individual agents"""
        print("🤖 Testing Individual Agents...")
        
        from agents.agent_state import AgentState
        from agents.planner import Planner
        from agents.coder import Coder
        from agents.critic import Critic
        
        # Test Planner
        print("\n  📋 Testing Planner Agent:")
        try:
            planner = Planner(self.llm)
            state = AgentState(messages=[HumanMessage(content="test todo app")])
            result = planner(state)
            
            if "files" in result and len(result["files"]) > 0:
                self.test_results["passed"] += 1
                print(f"    ✅ PASS: Planner generated {len(result['files'])} files")
            else:
                self.test_results["failed"] += 1
                print(f"    ❌ FAIL: Planner didn't generate files")
                
        except Exception as e:
            self.test_results["failed"] += 1
            print(f"    💥 ERROR: {str(e)}")
        
        # Test AgentState
        print("\n  🏗️ Testing AgentState:")
        try:
            state = AgentState(
                messages=[HumanMessage(content="test")],
                files=[],
                iteration=0,
                max_iterations=3,
                approved=False,
                detected_class="Class A",
                confidence="high"
            )
            
            # Test methods
            state.increment_iteration()
            state.set_approved(True)
            
            if state.iteration == 1 and state.approved:
                self.test_results["passed"] += 1
                print(f"    ✅ PASS: AgentState methods work")
            else:
                self.test_results["failed"] += 1
                print(f"    ❌ FAIL: AgentState methods issue")
                
        except Exception as e:
            self.test_results["failed"] += 1
            print(f"    💥 ERROR: {str(e)}")
    
    def test_workflows(self):
        """Test workflow components"""
        print("🔄 Testing Workflows...")
        
        # Test imports
        print("\n  📦 Testing Imports:")
        imports_to_test = [
            ("workflows.class_a_workflow", "Class A Workflow"),
            ("workflows.main_workflow", "Main Workflow"),
            ("agents.classifier", "Classifier"),
            ("agents.planner", "Planner"),
        ]
        
        for import_path, name in imports_to_test:
            try:
                __import__(import_path)
                self.test_results["passed"] += 1
                print(f"    ✅ PASS: {name} imports correctly")
            except ImportError as e:
                self.test_results["failed"] += 1
                print(f"    ❌ FAIL: {name} import failed: {e}")
        
        # Test workflow structure
        print("\n  🏗️ Testing Workflow Structure:")
        try:
            from workflows.main_workflow import main_workflow
            
            # Check required methods
            required_methods = ['invoke', '_build_main_workflow', '_route_to_class_workflow']
            for method in required_methods:
                if hasattr(main_workflow, method):
                    print(f"    ✅ Method exists: {method}")
                else:
                    print(f"    ❌ Missing method: {method}")
                    self.test_results["failed"] += 1
                    
        except Exception as e:
            self.test_results["failed"] += 1
            print(f"    💥 ERROR: {str(e)}")
    
    def test_integration(self):
        """Test integration between components"""
        print("🔗 Testing Integration...")
        
        test_cases = [
            {
                "name": "Class A Simple App",
                "prompt": "Create a simple counter app",
                "should_succeed": True
            },
            {
                "name": "Unsupported Class", 
                "prompt": "Build a complex CRM system with AI",
                "should_succeed": False
            },
        ]
        
        for test_case in test_cases:
            print(f"\n  🔄 Test: {test_case['name']}")
            print(f"    Prompt: '{test_case['prompt'][:50]}...'")
            
            # Simulate the flow
            try:
                from agents.classifier import Classifier
                classifier = Classifier(self.llm)
                
                # Classify
                classification = classifier.classify_prompt(test_case["prompt"])
                detected_class = classification.get("class")
                
                print(f"    Classification: {detected_class}")
                
                # Check if result matches expectation
                if test_case["should_succeed"]:
                    if detected_class == "Class A":
                        self.test_results["passed"] += 1
                        print(f"    ✅ PASS: Correctly identified as Class A")
                    else:
                        self.test_results["failed"] += 1
                        print(f"    ❌ FAIL: Should be Class A but got {detected_class}")
                else:
                    if detected_class != "Class A":
                        self.test_results["passed"] += 1
                        print(f"    ✅ PASS: Correctly identified as non-Class A")
                    else:
                        self.test_results["failed"] += 1
                        print(f"    ❌ FAIL: Should not be Class A")
                        
            except Exception as e:
                self.test_results["failed"] += 1
                print(f"    💥 ERROR: {str(e)}")
    
    def test_performance(self):
        """Test performance metrics"""
        print("⚡ Testing Performance...")
        
        # Test classifier response time
        print("\n  ⏱️ Testing Classifier Performance:")
        
        from agents.classifier import Classifier
        classifier = Classifier(self.llm)
        
        test_prompt = "Create a simple calculator app"
        
        try:
            start_time = time.time()
            result = classifier.classify_prompt(test_prompt)
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            
            if duration_ms < 5000:  # 5 seconds threshold
                self.test_results["passed"] += 1
                print(f"    ✅ PASS: Classification took {duration_ms:.0f}ms (acceptable)")
            else:
                self.test_results["failed"] += 1
                print(f"    ⚠️ SLOW: Classification took {duration_ms:.0f}ms (over 5s)")
                
        except Exception as e:
            self.test_results["failed"] += 1
            print(f"    💥 ERROR: {str(e)}")
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        
        total = sum(self.test_results.values())
        
        print(f"\n✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"⏭️ Skipped: {self.test_results['skipped']}")
        print(f"📈 Total: {total}")
        
        if self.test_results['failed'] == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️ {self.test_results['failed']} tests failed")
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📁 Results saved to: test_results.json")

def main():
    """Main test runner"""
    test_suite = CodelessTestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()