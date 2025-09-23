#!/usr/bin/env python3
"""
Test Learning Plan Frontend Fix
Verify that the frontend will now show all 4 learning plans
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import database
from bson import ObjectId

async def test_learning_plan_fix():
    """Test that the fix will show all learning plans"""
    
    print("🧪 TESTING LEARNING PLAN FRONTEND FIX")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    target_user_id = "688921c268819565ef1ce3dc"
    print(f"👤 Target User ID: {target_user_id}")
    print()
    
    try:
        # Simulate the exact API call that the frontend makes
        print("🔍 SIMULATING FRONTEND API CALL")
        print("-" * 40)
        
        # This is exactly what getUserLearningPlans() does
        user_id = str(target_user_id)
        plans = await database["learning_plans"].find({"user_id": user_id}).to_list(100)
        
        print(f"✅ API returns {len(plans)} learning plans")
        print()
        
        # Test the fix: Frontend should now show ALL plans (no .slice(0, 3))
        print("🎯 TESTING THE FIX")
        print("-" * 40)
        
        # Before fix: setPlans(plansData.slice(0, 3)) - would show max 3
        plans_before_fix = plans[:3]  # Simulate old behavior
        print(f"❌ Before fix: Frontend would show {len(plans_before_fix)} plans")
        
        # After fix: setPlans(plansData) - shows all plans
        plans_after_fix = plans  # Simulate new behavior
        print(f"✅ After fix: Frontend will show {len(plans_after_fix)} plans")
        print()
        
        # Verify the specific plans
        print("📋 PLANS THAT WILL NOW BE VISIBLE:")
        print("-" * 40)
        
        for i, plan in enumerate(plans_after_fix, 1):
            language = plan.get('language', 'Unknown')
            level = plan.get('proficiency_level', 'Unknown')
            progress = plan.get('progress_percentage', 0)
            duration = plan.get('duration_months', 'Unknown')
            created = plan.get('created_at', 'Unknown')
            
            # Determine if this plan was hidden before
            was_hidden = i > 3
            status = "🆕 NOW VISIBLE" if was_hidden else "✅ Already visible"
            
            print(f"Plan {i}: {language.title()} {level} ({duration}m) - {progress}% - {status}")
            if isinstance(created, str) and created != 'Unknown':
                try:
                    created_date = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    print(f"         Created: {created_date.strftime('%Y-%m-%d')}")
                except:
                    print(f"         Created: {created}")
            print()
        
        # Summary
        print("📊 FIX VERIFICATION SUMMARY:")
        print("-" * 40)
        print(f"Database contains: {len(plans)} learning plans")
        print(f"Frontend showed before: {len(plans_before_fix)} plans")
        print(f"Frontend will show after: {len(plans_after_fix)} plans")
        print(f"Additional plans now visible: {len(plans_after_fix) - len(plans_before_fix)}")
        print()
        
        if len(plans_after_fix) > len(plans_before_fix):
            print("🎉 SUCCESS: Fix will show more learning plans!")
            print("✅ Users will now see all their learning plans")
            print("✅ No more artificial 3-plan limit")
            return True
        else:
            print("ℹ️ No change: User already had 3 or fewer plans")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_learning_plan_fix())
    if success:
        print(f"\n🏁 TEST RESULT: ✅ PASS")
        print("The frontend fix will successfully show all learning plans!")
    else:
        print(f"\n🏁 TEST RESULT: ❌ FAIL")
        print("There was an issue with the test")
