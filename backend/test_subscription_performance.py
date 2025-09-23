#!/usr/bin/env python3
"""
Test Script for Subscription Status Performance Optimization
Tests the performance improvement from 5.44s to <2s
"""

import asyncio
import time
from datetime import datetime
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_performance_comparison():
    """Test performance comparison between original and optimized services"""
    
    print("🚀 SUBSCRIPTION STATUS PERFORMANCE TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test user ID (replace with actual user ID for testing)
    test_user_id = "688921c268819565ef1ce3dc"
    
    try:
        # Import services
        from subscription_service import SubscriptionService
        from subscription_service_optimized import OptimizedSubscriptionService, create_performance_indexes
        
        print("📊 CREATING DATABASE INDEXES FOR OPTIMIZATION...")
        await create_performance_indexes()
        print("✅ Database indexes created")
        print()
        
        # Test 1: Original Service Performance
        print("🐌 TESTING ORIGINAL SERVICE PERFORMANCE")
        print("-" * 40)
        
        original_times = []
        for i in range(3):
            start_time = time.time()
            try:
                original_status = await SubscriptionService.get_user_subscription_status(test_user_id)
                end_time = time.time()
                duration = end_time - start_time
                original_times.append(duration)
                print(f"Run {i+1}: {duration:.2f}s - Status: {original_status.status}, Plan: {original_status.plan}")
            except Exception as e:
                print(f"Run {i+1}: ERROR - {str(e)}")
                original_times.append(10.0)  # Assume 10s for error cases
        
        avg_original = sum(original_times) / len(original_times)
        print(f"📈 Original Average: {avg_original:.2f}s")
        print()
        
        # Test 2: Optimized Service Performance (First Run - Cache Miss)
        print("⚡ TESTING OPTIMIZED SERVICE PERFORMANCE (CACHE MISS)")
        print("-" * 50)
        
        optimized_times_cold = []
        for i in range(3):
            # Clear cache before each test
            await OptimizedSubscriptionService.invalidate_user_cache(test_user_id)
            
            start_time = time.time()
            try:
                optimized_status = await OptimizedSubscriptionService.get_user_subscription_status_optimized(test_user_id)
                end_time = time.time()
                duration = end_time - start_time
                optimized_times_cold.append(duration)
                print(f"Run {i+1}: {duration:.2f}s - Status: {optimized_status.status}, Plan: {optimized_status.plan}")
            except Exception as e:
                print(f"Run {i+1}: ERROR - {str(e)}")
                optimized_times_cold.append(5.0)  # Assume 5s for error cases
        
        avg_optimized_cold = sum(optimized_times_cold) / len(optimized_times_cold)
        print(f"📈 Optimized Average (Cold): {avg_optimized_cold:.2f}s")
        print()
        
        # Test 3: Optimized Service Performance (Cache Hit)
        print("🔥 TESTING OPTIMIZED SERVICE PERFORMANCE (CACHE HIT)")
        print("-" * 50)
        
        optimized_times_warm = []
        for i in range(3):
            start_time = time.time()
            try:
                optimized_status = await OptimizedSubscriptionService.get_user_subscription_status_optimized(test_user_id)
                end_time = time.time()
                duration = end_time - start_time
                optimized_times_warm.append(duration)
                print(f"Run {i+1}: {duration:.2f}s - Status: {optimized_status.status}, Plan: {optimized_status.plan}")
            except Exception as e:
                print(f"Run {i+1}: ERROR - {str(e)}")
                optimized_times_warm.append(1.0)  # Assume 1s for error cases
        
        avg_optimized_warm = sum(optimized_times_warm) / len(optimized_times_warm)
        print(f"📈 Optimized Average (Warm): {avg_optimized_warm:.2f}s")
        print()
        
        # Performance Analysis
        print("📊 PERFORMANCE ANALYSIS")
        print("=" * 60)
        
        cold_improvement = ((avg_original - avg_optimized_cold) / avg_original) * 100
        warm_improvement = ((avg_original - avg_optimized_warm) / avg_original) * 100
        
        print(f"Original Service:           {avg_original:.2f}s")
        print(f"Optimized Service (Cold):   {avg_optimized_cold:.2f}s")
        print(f"Optimized Service (Warm):   {avg_optimized_warm:.2f}s")
        print()
        print(f"Cold Cache Improvement:     {cold_improvement:.1f}%")
        print(f"Warm Cache Improvement:     {warm_improvement:.1f}%")
        print()
        
        # Success Criteria
        print("🎯 SUCCESS CRITERIA EVALUATION")
        print("-" * 30)
        
        target_met = avg_optimized_cold < 2.0
        significant_improvement = cold_improvement > 50
        cache_effective = avg_optimized_warm < 0.5
        
        print(f"✅ Target <2s met:           {'YES' if target_met else 'NO'} ({avg_optimized_cold:.2f}s)")
        print(f"✅ >50% improvement:         {'YES' if significant_improvement else 'NO'} ({cold_improvement:.1f}%)")
        print(f"✅ Cache effective:          {'YES' if cache_effective else 'NO'} ({avg_optimized_warm:.2f}s)")
        print()
        
        # Overall Result
        overall_success = target_met and significant_improvement
        
        if overall_success:
            print("🎉 PERFORMANCE OPTIMIZATION SUCCESSFUL!")
            print(f"   Response time reduced from {avg_original:.2f}s to {avg_optimized_cold:.2f}s")
            print(f"   Performance improvement: {cold_improvement:.1f}%")
            print(f"   Cache provides additional {((avg_optimized_cold - avg_optimized_warm) / avg_optimized_cold * 100):.1f}% boost")
        else:
            print("⚠️ PERFORMANCE OPTIMIZATION NEEDS IMPROVEMENT")
            if not target_met:
                print(f"   Target <2s not met: {avg_optimized_cold:.2f}s")
            if not significant_improvement:
                print(f"   Improvement <50%: {cold_improvement:.1f}%")
        
        print()
        print("🔍 DETAILED BREAKDOWN")
        print("-" * 20)
        print("Original times:", [f"{t:.2f}s" for t in original_times])
        print("Optimized (cold):", [f"{t:.2f}s" for t in optimized_times_cold])
        print("Optimized (warm):", [f"{t:.2f}s" for t in optimized_times_warm])
        
        return overall_success
        
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_cache_functionality():
    """Test cache functionality specifically"""
    
    print("\n🧪 CACHE FUNCTIONALITY TEST")
    print("=" * 30)
    
    try:
        from subscription_service_optimized import OptimizedSubscriptionService, subscription_cache
        
        test_user_id = "688921c268819565ef1ce3dc"
        
        # Clear cache
        await OptimizedSubscriptionService.invalidate_user_cache(test_user_id)
        print("✅ Cache cleared")
        
        # First call (cache miss)
        start_time = time.time()
        status1 = await OptimizedSubscriptionService.get_user_subscription_status_optimized(test_user_id)
        time1 = time.time() - start_time
        print(f"✅ First call (cache miss): {time1:.2f}s")
        
        # Second call (cache hit)
        start_time = time.time()
        status2 = await OptimizedSubscriptionService.get_user_subscription_status_optimized(test_user_id)
        time2 = time.time() - start_time
        print(f"✅ Second call (cache hit): {time2:.2f}s")
        
        # Verify results are identical
        if status1.dict() == status2.dict():
            print("✅ Cache returns identical results")
        else:
            print("❌ Cache results differ!")
            return False
        
        # Test cache speedup
        speedup = ((time1 - time2) / time1) * 100
        print(f"✅ Cache speedup: {speedup:.1f}%")
        
        # Test cache invalidation
        await OptimizedSubscriptionService.invalidate_user_cache(test_user_id)
        
        # Third call (cache miss again)
        start_time = time.time()
        status3 = await OptimizedSubscriptionService.get_user_subscription_status_optimized(test_user_id)
        time3 = time.time() - start_time
        print(f"✅ Third call (after invalidation): {time3:.2f}s")
        
        # Verify invalidation worked
        if time3 > time2 * 2:  # Should be significantly slower than cached call
            print("✅ Cache invalidation working correctly")
            return True
        else:
            print("❌ Cache invalidation may not be working")
            return False
            
    except Exception as e:
        print(f"❌ CACHE TEST FAILED: {str(e)}")
        return False

async def test_backward_compatibility():
    """Test that optimized service maintains backward compatibility"""
    
    print("\n🔄 BACKWARD COMPATIBILITY TEST")
    print("=" * 35)
    
    try:
        from subscription_service import SubscriptionService
        from subscription_service_optimized import OptimizedSubscriptionService
        
        test_user_id = "688921c268819565ef1ce3dc"
        
        # Get results from both services
        original_status = await SubscriptionService.get_user_subscription_status(test_user_id)
        optimized_status = await OptimizedSubscriptionService.get_user_subscription_status_optimized(test_user_id)
        
        # Compare key fields
        fields_to_compare = ['status', 'plan', 'period', 'is_in_trial']
        
        compatible = True
        for field in fields_to_compare:
            original_value = getattr(original_status, field, None)
            optimized_value = getattr(optimized_status, field, None)
            
            if original_value != optimized_value:
                print(f"❌ Field '{field}' differs: {original_value} vs {optimized_value}")
                compatible = False
            else:
                print(f"✅ Field '{field}' matches: {original_value}")
        
        # Compare limits if available
        if original_status.limits and optimized_status.limits:
            limits_fields = ['minutes_remaining', 'sessions_remaining', 'is_unlimited']
            for field in limits_fields:
                original_value = getattr(original_status.limits, field, None)
                optimized_value = getattr(optimized_status.limits, field, None)
                
                if original_value != optimized_value:
                    print(f"❌ Limits field '{field}' differs: {original_value} vs {optimized_value}")
                    compatible = False
                else:
                    print(f"✅ Limits field '{field}' matches: {original_value}")
        
        if compatible:
            print("✅ BACKWARD COMPATIBILITY MAINTAINED")
        else:
            print("❌ BACKWARD COMPATIBILITY ISSUES DETECTED")
        
        return compatible
        
    except Exception as e:
        print(f"❌ COMPATIBILITY TEST FAILED: {str(e)}")
        return False

async def main():
    """Main test function"""
    
    print("🧪 SUBSCRIPTION STATUS PERFORMANCE TEST SUITE")
    print("=" * 60)
    print("Testing performance optimization for /api/stripe/subscription-status")
    print("Target: Reduce response time from 5.44s to <2s")
    print()
    
    # Run all tests
    performance_success = await test_performance_comparison()
    cache_success = await test_cache_functionality()
    compatibility_success = await test_backward_compatibility()
    
    # Overall results
    print("\n🏁 FINAL RESULTS")
    print("=" * 20)
    print(f"Performance Test:     {'✅ PASS' if performance_success else '❌ FAIL'}")
    print(f"Cache Test:           {'✅ PASS' if cache_success else '❌ FAIL'}")
    print(f"Compatibility Test:   {'✅ PASS' if compatibility_success else '❌ FAIL'}")
    
    overall_success = performance_success and cache_success and compatibility_success
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Performance optimization is ready for production")
        print("✅ Response time target achieved")
        print("✅ Backward compatibility maintained")
        print("✅ Caching system working correctly")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("❌ Review failed tests before deploying to production")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
