"""
Comprehensive test suite for the optimized conversation help system.
Tests 7-second guarantee and context-aware responses.
"""

import asyncio
import time
import os
from typing import List, Dict, Any

from conversation_help import ConversationHelpRequest
from optimized_conversation_help import get_optimized_help, ResponseTier

# Test scenarios that must work within 7 seconds
TEST_SCENARIOS = [
    {
        "name": "Morning Routine Description",
        "ai_response": "Try describing your morning routine again, using a different phrase for one of the actions",
        "target_language": "english",
        "user_language": "english",
        "proficiency_level": "B1",
        "expected_patterns": ["wake", "morning", "brush", "teeth", "breakfast", "wash"],
        "context_type": "morning_routine"
    },
    {
        "name": "Vocabulary Practice - Thoroughly",
        "ai_response": "Let's practice some new vocabulary. Can you use the word 'thoroughly' in a sentence?",
        "target_language": "english",
        "user_language": "english",
        "proficiency_level": "B1",
        "expected_patterns": ["thoroughly"],
        "context_type": "vocabulary_thoroughly"
    },
    {
        "name": "Grammar Correction",
        "ai_response": "Instead of 'I usually brush my teeth and also wash my face', try using better sentence structure",
        "target_language": "english",
        "user_language": "english",
        "proficiency_level": "B1",
        "expected_patterns": ["brush", "teeth", "wash", "face"],
        "context_type": "grammar_correction"
    },
    {
        "name": "Spanish Conversation Starter",
        "ai_response": "¡Hola! Cuéntame sobre tu día. ¿Qué hiciste esta mañana?",
        "target_language": "spanish",
        "user_language": "english",
        "proficiency_level": "A2",
        "expected_patterns": ["día", "mañana", "hice"],
        "context_type": "conversation_starter"
    },
    {
        "name": "Dutch Pronunciation Practice",
        "ai_response": "Probeer deze zin na te zeggen: 'Ik ga naar de winkel om boodschappen te doen'",
        "target_language": "dutch",
        "user_language": "english",
        "proficiency_level": "A1",
        "expected_patterns": ["winkel", "boodschappen"],
        "context_type": "repeat_practice"
    },
    {
        "name": "Complex English Discussion",
        "ai_response": "That's an interesting perspective on climate change. Can you elaborate on how renewable energy sources might impact developing economies? Consider both the benefits and potential challenges.",
        "target_language": "english",
        "user_language": "english",
        "proficiency_level": "C1",
        "expected_patterns": ["climate", "renewable", "energy", "economy"],
        "context_type": "complex_discussion"
    }
]

async def test_single_scenario(
    optimized_help, 
    scenario: Dict[str, Any], 
    max_time: float = 7.0
) -> Dict[str, Any]:
    """Test a single scenario and return results"""
    
    print(f"\n🧪 Testing: {scenario['name']}")
    
    # Create request
    request = ConversationHelpRequest(
        ai_response=scenario["ai_response"],
        conversation_context=[],
        target_language=scenario["target_language"],
        user_language=scenario["user_language"],
        proficiency_level=scenario["proficiency_level"]
    )
    
    # Measure response time
    start_time = time.time()
    
    try:
        response = await optimized_help.generate_help(request, max_response_time=max_time)
        elapsed_time = time.time() - start_time
        
        # Check if response time is within limit
        time_check = elapsed_time <= max_time
        
        # Check if responses are contextually relevant
        response_texts = [resp.text.lower() for resp in response.suggested_responses]
        all_text = " ".join(response_texts)
        
        # Check for expected patterns
        pattern_matches = []
        for pattern in scenario["expected_patterns"]:
            found = pattern.lower() in all_text
            pattern_matches.append({"pattern": pattern, "found": found})
        
        # Calculate context relevance score
        patterns_found = sum(1 for match in pattern_matches if match["found"])
        context_score = patterns_found / len(scenario["expected_patterns"]) if scenario["expected_patterns"] else 1.0
        
        # Check response quality
        has_responses = len(response.suggested_responses) >= 2
        has_pronunciations = all(resp.pronunciation for resp in response.suggested_responses)
        has_explanations = all(resp.explanation for resp in response.suggested_responses)
        
        result = {
            "scenario": scenario["name"],
            "success": True,
            "elapsed_time": elapsed_time,
            "time_check": time_check,
            "context_score": context_score,
            "pattern_matches": pattern_matches,
            "response_count": len(response.suggested_responses),
            "has_responses": has_responses,
            "has_pronunciations": has_pronunciations,
            "has_explanations": has_explanations,
            "responses": [
                {
                    "text": resp.text,
                    "pronunciation": resp.pronunciation,
                    "explanation": resp.explanation
                } for resp in response.suggested_responses
            ],
            "summary": response.ai_response_summary,
            "error": None
        }
        
        # Print results
        status = "✅ PASS" if time_check and context_score > 0.3 else "❌ FAIL"
        print(f"   {status} - {elapsed_time:.3f}s (limit: {max_time}s)")
        print(f"   Context Score: {context_score:.2f} ({patterns_found}/{len(scenario['expected_patterns'])} patterns)")
        print(f"   Responses: {len(response.suggested_responses)}")
        
        for i, resp in enumerate(response.suggested_responses, 1):
            print(f"     {i}. \"{resp.text}\"")
            print(f"        Explanation: {resp.explanation}")
        
        return result
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        
        result = {
            "scenario": scenario["name"],
            "success": False,
            "elapsed_time": elapsed_time,
            "time_check": False,
            "context_score": 0.0,
            "pattern_matches": [],
            "response_count": 0,
            "has_responses": False,
            "has_pronunciations": False,
            "has_explanations": False,
            "responses": [],
            "summary": "",
            "error": str(e)
        }
        
        print(f"   ❌ ERROR - {elapsed_time:.3f}s: {str(e)}")
        return result

async def test_cache_performance(optimized_help) -> Dict[str, Any]:
    """Test cache performance with repeated requests"""
    
    print(f"\n🧪 Testing Cache Performance")
    
    # Use first scenario for cache testing
    scenario = TEST_SCENARIOS[0]
    request = ConversationHelpRequest(
        ai_response=scenario["ai_response"],
        conversation_context=[],
        target_language=scenario["target_language"],
        user_language=scenario["user_language"],
        proficiency_level=scenario["proficiency_level"]
    )
    
    # First request (cache miss)
    start_time = time.time()
    response1 = await optimized_help.generate_help(request)
    first_time = time.time() - start_time
    
    # Second request (should be cache hit)
    start_time = time.time()
    response2 = await optimized_help.generate_help(request)
    second_time = time.time() - start_time
    
    # Third request (should also be cache hit)
    start_time = time.time()
    response3 = await optimized_help.generate_help(request)
    third_time = time.time() - start_time
    
    cache_improvement = (first_time - second_time) / first_time * 100
    
    result = {
        "first_request_time": first_time,
        "second_request_time": second_time,
        "third_request_time": third_time,
        "cache_improvement_percent": cache_improvement,
        "cache_working": second_time < 0.1 and third_time < 0.1
    }
    
    print(f"   First request (cache miss): {first_time:.3f}s")
    print(f"   Second request (cache hit): {second_time:.3f}s")
    print(f"   Third request (cache hit): {third_time:.3f}s")
    print(f"   Cache improvement: {cache_improvement:.1f}%")
    print(f"   Cache working: {'✅ YES' if result['cache_working'] else '❌ NO'}")
    
    return result

async def test_concurrent_requests(optimized_help, num_concurrent: int = 5) -> Dict[str, Any]:
    """Test system performance under concurrent load"""
    
    print(f"\n🧪 Testing Concurrent Performance ({num_concurrent} requests)")
    
    # Create multiple requests
    requests = []
    for i in range(num_concurrent):
        scenario = TEST_SCENARIOS[i % len(TEST_SCENARIOS)]
        request = ConversationHelpRequest(
            ai_response=scenario["ai_response"],
            conversation_context=[],
            target_language=scenario["target_language"],
            user_language=scenario["user_language"],
            proficiency_level=scenario["proficiency_level"]
        )
        requests.append(request)
    
    # Execute all requests concurrently
    start_time = time.time()
    
    tasks = [optimized_help.generate_help(req) for req in requests]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful_responses = [r for r in responses if not isinstance(r, Exception)]
    failed_responses = [r for r in responses if isinstance(r, Exception)]
    
    success_rate = len(successful_responses) / len(responses) * 100
    avg_time_per_request = total_time / len(responses)
    
    result = {
        "total_requests": num_concurrent,
        "successful_requests": len(successful_responses),
        "failed_requests": len(failed_responses),
        "success_rate": success_rate,
        "total_time": total_time,
        "avg_time_per_request": avg_time_per_request,
        "all_within_limit": total_time <= 7.0
    }
    
    print(f"   Total time: {total_time:.3f}s")
    print(f"   Success rate: {success_rate:.1f}% ({len(successful_responses)}/{len(responses)})")
    print(f"   Avg time per request: {avg_time_per_request:.3f}s")
    print(f"   Within 7s limit: {'✅ YES' if result['all_within_limit'] else '❌ NO'}")
    
    return result

async def run_comprehensive_test():
    """Run comprehensive test suite"""
    
    print("=" * 80)
    print("🚀 OPTIMIZED CONVERSATION HELP - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    # Initialize optimized help system
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY environment variable not set")
        return
    
    optimized_help = get_optimized_help(api_key)
    
    try:
        # Test individual scenarios
        print("\n📋 INDIVIDUAL SCENARIO TESTS")
        print("-" * 50)
        
        scenario_results = []
        for scenario in TEST_SCENARIOS:
            result = await test_single_scenario(optimized_help, scenario)
            scenario_results.append(result)
        
        # Test cache performance
        cache_result = await test_cache_performance(optimized_help)
        
        # Test concurrent performance
        concurrent_result = await test_concurrent_requests(optimized_help)
        
        # Get performance metrics
        metrics = optimized_help.get_performance_metrics()
        
        # Generate summary report
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY REPORT")
        print("=" * 80)
        
        # Scenario results summary
        total_scenarios = len(scenario_results)
        passed_scenarios = sum(1 for r in scenario_results if r["success"] and r["time_check"] and r["context_score"] > 0.3)
        time_compliant = sum(1 for r in scenario_results if r["time_check"])
        context_relevant = sum(1 for r in scenario_results if r["context_score"] > 0.5)
        
        print(f"\n🎯 SCENARIO TESTS:")
        print(f"   Total scenarios: {total_scenarios}")
        print(f"   Passed scenarios: {passed_scenarios} ({passed_scenarios/total_scenarios*100:.1f}%)")
        print(f"   Time compliant: {time_compliant} ({time_compliant/total_scenarios*100:.1f}%)")
        print(f"   Context relevant: {context_relevant} ({context_relevant/total_scenarios*100:.1f}%)")
        
        # Performance summary
        avg_response_time = sum(r["elapsed_time"] for r in scenario_results) / len(scenario_results)
        max_response_time = max(r["elapsed_time"] for r in scenario_results)
        
        print(f"\n⚡ PERFORMANCE:")
        print(f"   Average response time: {avg_response_time:.3f}s")
        print(f"   Maximum response time: {max_response_time:.3f}s")
        print(f"   7-second guarantee: {'✅ MAINTAINED' if max_response_time <= 7.0 else '❌ VIOLATED'}")
        
        # Cache performance
        print(f"\n💾 CACHE PERFORMANCE:")
        print(f"   Cache hit rate: {metrics['cache_hit_rate']*100:.1f}%")
        print(f"   Cache improvement: {cache_result['cache_improvement_percent']:.1f}%")
        print(f"   Cache working: {'✅ YES' if cache_result['cache_working'] else '❌ NO'}")
        
        # Concurrent performance
        print(f"\n🔄 CONCURRENT PERFORMANCE:")
        print(f"   Success rate: {concurrent_result['success_rate']:.1f}%")
        print(f"   Concurrent limit compliance: {'✅ YES' if concurrent_result['all_within_limit'] else '❌ NO'}")
        
        # Tier usage
        print(f"\n🏆 TIER USAGE:")
        for tier, count in metrics["tier_usage"].items():
            percentage = count / metrics["total_requests"] * 100 if metrics["total_requests"] > 0 else 0
            print(f"   {tier}: {count} ({percentage:.1f}%)")
        
        # Overall assessment
        overall_success = (
            passed_scenarios >= total_scenarios * 0.8 and  # 80% scenarios pass
            max_response_time <= 7.0 and  # 7-second guarantee
            cache_result["cache_working"] and  # Cache working
            concurrent_result["success_rate"] >= 90  # 90% concurrent success
        )
        
        print(f"\n🎉 OVERALL ASSESSMENT:")
        print(f"   System Status: {'✅ PRODUCTION READY' if overall_success else '❌ NEEDS IMPROVEMENT'}")
        
        if overall_success:
            print(f"\n✨ The optimized conversation help system is ready for production!")
            print(f"   - Guarantees responses within 7 seconds")
            print(f"   - Provides contextually relevant suggestions")
            print(f"   - Handles concurrent load efficiently")
            print(f"   - Maintains high cache hit rates")
        else:
            print(f"\n⚠️  System needs improvement before production deployment.")
        
        return {
            "overall_success": overall_success,
            "scenario_results": scenario_results,
            "cache_result": cache_result,
            "concurrent_result": concurrent_result,
            "metrics": metrics
        }
        
    finally:
        await optimized_help.close()

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
