"""
Test Enhanced Conversation Help System
Comprehensive testing for all conversation types and edge cases.
"""

import asyncio
import json
from typing import Dict, Any, List
from conversation_help import ConversationHelpRequest
from smart_response_generator import smart_response_generator
from learning_plan_context_provider import LearningPlanContextProvider, UserContextProvider
from conversation_context_analyzer import context_analyzer, ConversationIntent

class ConversationHelpTester:
    """Comprehensive tester for the enhanced conversation help system"""
    
    def __init__(self):
        self.test_results = []
        
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧪 Starting Enhanced Conversation Help System Tests")
        print("=" * 60)
        
        # Test 1: Intent Detection
        await self.test_intent_detection()
        
        # Test 2: Context Analysis
        await self.test_context_analysis()
        
        # Test 3: Smart Response Generation - Practice Conversations
        await self.test_practice_conversation_responses()
        
        # Test 4: Guest User Handling
        await self.test_guest_user_responses()
        
        # Test 5: Learning Plan Context Integration
        await self.test_learning_plan_integration()
        
        # Test 6: Performance and Fallbacks
        await self.test_performance_and_fallbacks()
        
        # Test 7: Edge Cases
        await self.test_edge_cases()
        
        # Print summary
        self.print_test_summary()
    
    async def test_intent_detection(self):
        """Test AI tutor intent detection accuracy"""
        print("\n🎯 Testing Intent Detection")
        print("-" * 30)
        
        test_cases = [
            {
                "ai_response": "Repeat after me: 'Goedemorgen, hoe gaat het met je?'",
                "expected_intent": ConversationIntent.REPEAT_PRACTICE,
                "description": "Dutch pronunciation practice"
            },
            {
                "ai_response": "Actually, the correct form is 'I have been' not 'I have be'. Try again.",
                "expected_intent": ConversationIntent.GRAMMAR_CORRECTION,
                "description": "Grammar correction"
            },
            {
                "ai_response": "The word 'gezellig' is a uniquely Dutch concept that means cozy and pleasant.",
                "expected_intent": ConversationIntent.VOCABULARY_INTRODUCTION,
                "description": "Vocabulary introduction"
            },
            {
                "ai_response": "Tell me about your favorite hobby. What do you like to do in your free time?",
                "expected_intent": ConversationIntent.CONVERSATION_STARTER,
                "description": "Conversation starter"
            },
            {
                "ai_response": "Excellent work! You're really improving your pronunciation.",
                "expected_intent": ConversationIntent.ENCOURAGEMENT,
                "description": "Encouragement"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                analysis = context_analyzer.analyze_context(
                    ai_response=test_case["ai_response"],
                    conversation_history=[],
                    learning_plan_context=None,
                    user_context=None
                )
                
                success = analysis.intent == test_case["expected_intent"]
                confidence = analysis.confidence_score
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"  Test {i}: {status} - {test_case['description']}")
                print(f"    Expected: {test_case['expected_intent'].value}")
                print(f"    Got: {analysis.intent.value} (confidence: {confidence:.2f})")
                
                self.test_results.append({
                    "test": "intent_detection",
                    "case": test_case["description"],
                    "success": success,
                    "details": f"Expected {test_case['expected_intent'].value}, got {analysis.intent.value}"
                })
                
            except Exception as e:
                print(f"  Test {i}: ❌ ERROR - {test_case['description']}: {str(e)}")
                self.test_results.append({
                    "test": "intent_detection",
                    "case": test_case["description"],
                    "success": False,
                    "details": f"Error: {str(e)}"
                })
    
    async def test_context_analysis(self):
        """Test comprehensive context analysis"""
        print("\n🔍 Testing Context Analysis")
        print("-" * 30)
        
        test_cases = [
            {
                "ai_response": "Hallo! Ik ben je Nederlandse taaldocent. Hoe gaat het met jou?",
                "conversation_history": [],
                "expected_language": "dutch",
                "expected_phase": "introduction",
                "description": "Dutch lesson introduction"
            },
            {
                "ai_response": "Let's practice some advanced subjunctive constructions in Spanish.",
                "conversation_history": [{"role": "assistant", "content": "Previous message"}] * 5,
                "expected_language": "spanish",
                "expected_complexity": 7,
                "description": "Advanced Spanish grammar"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                analysis = context_analyzer.analyze_context(
                    ai_response=test_case["ai_response"],
                    conversation_history=test_case["conversation_history"],
                    learning_plan_context=None,
                    user_context={"target_language": test_case.get("expected_language", "english")}
                )
                
                checks = []
                
                # Check language detection
                if "expected_language" in test_case:
                    lang_correct = analysis.detected_language == test_case["expected_language"]
                    checks.append(("language", lang_correct, f"Expected {test_case['expected_language']}, got {analysis.detected_language}"))
                
                # Check complexity
                if "expected_complexity" in test_case:
                    complexity_correct = analysis.complexity_level >= test_case["expected_complexity"]
                    checks.append(("complexity", complexity_correct, f"Expected >={test_case['expected_complexity']}, got {analysis.complexity_level}"))
                
                all_passed = all(check[1] for check in checks)
                status = "✅ PASS" if all_passed else "❌ FAIL"
                
                print(f"  Test {i}: {status} - {test_case['description']}")
                for check_name, passed, details in checks:
                    check_status = "✅" if passed else "❌"
                    print(f"    {check_status} {check_name}: {details}")
                
                self.test_results.append({
                    "test": "context_analysis",
                    "case": test_case["description"],
                    "success": all_passed,
                    "details": str(checks)
                })
                
            except Exception as e:
                print(f"  Test {i}: ❌ ERROR - {test_case['description']}: {str(e)}")
                self.test_results.append({
                    "test": "context_analysis",
                    "case": test_case["description"],
                    "success": False,
                    "details": f"Error: {str(e)}"
                })
    
    async def test_practice_conversation_responses(self):
        """Test response generation for practice conversations (no learning plan)"""
        print("\n💬 Testing Practice Conversation Responses")
        print("-" * 30)
        
        test_cases = [
            {
                "ai_response": "Repeat after me: 'Ik hou van Nederlandse kaas'",
                "target_language": "dutch",
                "proficiency_level": "A2",
                "user_language": "english",
                "description": "Dutch pronunciation practice"
            },
            {
                "ai_response": "¿Qué hiciste el fin de semana pasado?",
                "target_language": "spanish",
                "proficiency_level": "B1",
                "user_language": "english",
                "description": "Spanish conversation question"
            },
            {
                "ai_response": "Excellent! Your French accent is improving significantly.",
                "target_language": "french",
                "proficiency_level": "B2",
                "user_language": "english",
                "description": "French encouragement"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                request = ConversationHelpRequest(
                    ai_response=test_case["ai_response"],
                    conversation_context=[],
                    target_language=test_case["target_language"],
                    user_language=test_case["user_language"],
                    proficiency_level=test_case["proficiency_level"]
                )
                
                user_context = UserContextProvider.create_user_context(
                    target_language=test_case["target_language"],
                    proficiency_level=test_case["proficiency_level"],
                    user_language=test_case["user_language"],
                    is_guest=False
                )
                
                # Test with no learning plan context (practice conversation)
                response = await smart_response_generator.generate_smart_response(
                    request=request,
                    learning_plan_context=None,
                    user_context=user_context,
                    time_budget=7.0
                )
                
                # Validate response
                success = (
                    response is not None and
                    len(response.suggested_responses) >= 1 and
                    response.ai_response_summary and
                    all(sr.text and sr.explanation for sr in response.suggested_responses)
                )
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"  Test {i}: {status} - {test_case['description']}")
                
                if success:
                    print(f"    Generated {len(response.suggested_responses)} suggestions")
                    print(f"    Summary: {response.ai_response_summary[:50]}...")
                    for j, suggestion in enumerate(response.suggested_responses[:2], 1):
                        print(f"    Suggestion {j}: '{suggestion.text}' - {suggestion.explanation}")
                else:
                    print(f"    Failed: Response validation failed")
                
                self.test_results.append({
                    "test": "practice_conversation",
                    "case": test_case["description"],
                    "success": success,
                    "details": f"Generated {len(response.suggested_responses) if response else 0} suggestions"
                })
                
            except Exception as e:
                print(f"  Test {i}: ❌ ERROR - {test_case['description']}: {str(e)}")
                self.test_results.append({
                    "test": "practice_conversation",
                    "case": test_case["description"],
                    "success": False,
                    "details": f"Error: {str(e)}"
                })
    
    async def test_guest_user_responses(self):
        """Test response generation for guest users"""
        print("\n👤 Testing Guest User Responses")
        print("-" * 30)
        
        test_cases = [
            {
                "ai_response": "Hello! Welcome to your English lesson. How are you today?",
                "target_language": "english",
                "proficiency_level": "A1",
                "user_language": "spanish",
                "description": "Guest user English lesson"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                request = ConversationHelpRequest(
                    ai_response=test_case["ai_response"],
                    conversation_context=[],
                    target_language=test_case["target_language"],
                    user_language=test_case["user_language"],
                    proficiency_level=test_case["proficiency_level"]
                )
                
                user_context = UserContextProvider.create_user_context(
                    target_language=test_case["target_language"],
                    proficiency_level=test_case["proficiency_level"],
                    user_language=test_case["user_language"],
                    is_guest=True  # Guest user
                )
                
                response = await smart_response_generator.generate_smart_response(
                    request=request,
                    learning_plan_context=None,  # No learning plan for guests
                    user_context=user_context,
                    time_budget=7.0
                )
                
                success = (
                    response is not None and
                    len(response.suggested_responses) >= 1 and
                    user_context["is_guest"] == True
                )
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"  Test {i}: {status} - {test_case['description']}")
                print(f"    Guest context: {user_context['context_type']}")
                
                self.test_results.append({
                    "test": "guest_user",
                    "case": test_case["description"],
                    "success": success,
                    "details": f"Guest user handled: {user_context['is_guest']}"
                })
                
            except Exception as e:
                print(f"  Test {i}: ❌ ERROR - {test_case['description']}: {str(e)}")
                self.test_results.append({
                    "test": "guest_user",
                    "case": test_case["description"],
                    "success": False,
                    "details": f"Error: {str(e)}"
                })
    
    async def test_learning_plan_integration(self):
        """Test learning plan context integration"""
        print("\n🎯 Testing Learning Plan Integration")
        print("-" * 30)
        
        # Mock learning plan context
        mock_learning_plan_context = {
            "proficiency_level": "B1",
            "language": "dutch",
            "current_focus": "Building on your strengths: communication skills",
            "areas_for_improvement": ["pronunciation", "fluency"],
            "strengths": ["vocabulary", "basic grammar"],
            "current_week": 8,
            "current_activities": [
                "Continue working on pronunciation",
                "Practice communication skills"
            ]
        }
        
        test_cases = [
            {
                "ai_response": "Let's practice your Dutch pronunciation. Say 'Goedemorgen'",
                "target_language": "dutch",
                "proficiency_level": "B1",
                "user_language": "english",
                "description": "Learning plan enhanced pronunciation practice"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                request = ConversationHelpRequest(
                    ai_response=test_case["ai_response"],
                    conversation_context=[],
                    target_language=test_case["target_language"],
                    user_language=test_case["user_language"],
                    proficiency_level=test_case["proficiency_level"]
                )
                
                user_context = UserContextProvider.create_user_context(
                    target_language=test_case["target_language"],
                    proficiency_level=test_case["proficiency_level"],
                    user_language=test_case["user_language"],
                    is_guest=False
                )
                
                # Test with learning plan context
                response = await smart_response_generator.generate_smart_response(
                    request=request,
                    learning_plan_context=mock_learning_plan_context,
                    user_context=user_context,
                    time_budget=7.0
                )
                
                success = (
                    response is not None and
                    len(response.suggested_responses) >= 1
                )
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"  Test {i}: {status} - {test_case['description']}")
                print(f"    Learning plan focus: {mock_learning_plan_context['current_focus']}")
                
                if success and response.suggested_responses:
                    print(f"    Enhanced suggestion: '{response.suggested_responses[0].text}'")
                    print(f"    Explanation: {response.suggested_responses[0].explanation}")
                
                self.test_results.append({
                    "test": "learning_plan_integration",
                    "case": test_case["description"],
                    "success": success,
                    "details": f"Learning plan context used: {mock_learning_plan_context['current_focus']}"
                })
                
            except Exception as e:
                print(f"  Test {i}: ❌ ERROR - {test_case['description']}: {str(e)}")
                self.test_results.append({
                    "test": "learning_plan_integration",
                    "case": test_case["description"],
                    "success": False,
                    "details": f"Error: {str(e)}"
                })
    
    async def test_performance_and_fallbacks(self):
        """Test performance and fallback mechanisms"""
        print("\n⚡ Testing Performance and Fallbacks")
        print("-" * 30)
        
        test_cases = [
            {
                "ai_response": "Test response for performance",
                "target_language": "english",
                "time_budget": 2.0,  # Very tight budget
                "description": "Fast response under time pressure"
            },
            {
                "ai_response": "",  # Empty response
                "target_language": "english",
                "description": "Empty AI response fallback"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                request = ConversationHelpRequest(
                    ai_response=test_case["ai_response"],
                    conversation_context=[],
                    target_language=test_case["target_language"],
                    user_language="english",
                    proficiency_level="B1"
                )
                
                user_context = UserContextProvider.create_user_context(
                    target_language=test_case["target_language"],
                    proficiency_level="B1",
                    user_language="english",
                    is_guest=False
                )
                
                import time
                start_time = time.time()
                
                response = await smart_response_generator.generate_smart_response(
                    request=request,
                    learning_plan_context=None,
                    user_context=user_context,
                    time_budget=test_case.get("time_budget", 7.0)
                )
                
                elapsed_time = time.time() - start_time
                
                # For empty responses, we expect None or fallback
                if not test_case["ai_response"]:
                    success = response is not None  # Should have fallback
                else:
                    success = (
                        response is not None and
                        elapsed_time <= (test_case.get("time_budget", 7.0) + 1.0)  # Allow 1s buffer
                    )
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"  Test {i}: {status} - {test_case['description']}")
                print(f"    Response time: {elapsed_time:.2f}s")
                print(f"    Budget: {test_case.get('time_budget', 7.0)}s")
                
                self.test_results.append({
                    "test": "performance_fallbacks",
                    "case": test_case["description"],
                    "success": success,
                    "details": f"Response time: {elapsed_time:.2f}s"
                })
                
            except Exception as e:
                print(f"  Test {i}: ❌ ERROR - {test_case['description']}: {str(e)}")
                self.test_results.append({
                    "test": "performance_fallbacks",
                    "case": test_case["description"],
                    "success": False,
                    "details": f"Error: {str(e)}"
                })
    
    async def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n🔧 Testing Edge Cases")
        print("-" * 30)
        
        test_cases = [
            {
                "ai_response": "A" * 1000,  # Very long response
                "target_language": "english",
                "description": "Very long AI response"
            },
            {
                "ai_response": "Mixed language response with English and español words",
                "target_language": "spanish",
                "description": "Mixed language detection"
            },
            {
                "ai_response": "Normal response",
                "target_language": "unsupported_language",
                "description": "Unsupported language fallback"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                request = ConversationHelpRequest(
                    ai_response=test_case["ai_response"],
                    conversation_context=[],
                    target_language=test_case["target_language"],
                    user_language="english",
                    proficiency_level="B1"
                )
                
                user_context = UserContextProvider.create_user_context(
                    target_language=test_case["target_language"],
                    proficiency_level="B1",
                    user_language="english",
                    is_guest=False
                )
                
                response = await smart_response_generator.generate_smart_response(
                    request=request,
                    learning_plan_context=None,
                    user_context=user_context,
                    time_budget=7.0
                )
                
                # Edge cases should still return valid responses
                success = (
                    response is not None and
                    len(response.suggested_responses) >= 1
                )
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"  Test {i}: {status} - {test_case['description']}")
                
                self.test_results.append({
                    "test": "edge_cases",
                    "case": test_case["description"],
                    "success": success,
                    "details": f"Handled edge case gracefully"
                })
                
            except Exception as e:
                print(f"  Test {i}: ❌ ERROR - {test_case['description']}: {str(e)}")
                self.test_results.append({
                    "test": "edge_cases",
                    "case": test_case["description"],
                    "success": False,
                    "details": f"Error: {str(e)}"
                })
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("🧪 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Group by test type
        test_types = {}
        for result in self.test_results:
            test_type = result["test"]
            if test_type not in test_types:
                test_types[test_type] = {"passed": 0, "total": 0}
            test_types[test_type]["total"] += 1
            if result["success"]:
                test_types[test_type]["passed"] += 1
        
        print("\nResults by Test Type:")
        for test_type, stats in test_types.items():
            success_rate = (stats["passed"] / stats["total"]) * 100
            print(f"  {test_type}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Show failed tests
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['case']}")
                    print(f"     {result['details']}")

async def main():
    """Run the comprehensive test suite"""
    tester = ConversationHelpTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
