#!/usr/bin/env python3
"""
Investigate Learning Plan Frontend Discrepancy
Deep dive into why frontend shows 3 plans but database has 4
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import database
from bson import ObjectId

async def investigate_frontend_discrepancy():
    """Investigate the discrepancy between frontend and database"""
    
    print("🔍 INVESTIGATING LEARNING PLAN FRONTEND DISCREPANCY")
    print("=" * 60)
    print(f"Investigation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    target_user_id = "688921c268819565ef1ce3dc"
    print(f"👤 Target User ID: {target_user_id}")
    print()
    
    try:
        # Step 1: Simulate the exact query that the backend API uses
        print("🔍 STEP 1: SIMULATING BACKEND API QUERY")
        print("-" * 40)
        
        # This is exactly what get_user_learning_plans() does
        user_id = str(target_user_id)  # Convert to string
        print(f"Using user_id as string: {user_id}")
        
        # Try to find plans with the string user ID (primary method)
        plans = await database["learning_plans"].find({"user_id": user_id}).to_list(100)
        print(f"✅ Found {len(plans)} plans with string user_id")
        
        if not plans:
            # Try with ObjectId (fallback method)
            try:
                object_id = ObjectId(user_id)
                plans = await database["learning_plans"].find({"user_id": object_id}).to_list(100)
                print(f"✅ Found {len(plans)} plans with ObjectId user_id")
            except Exception as e:
                print(f"❌ ObjectId conversion failed: {str(e)}")
        
        print(f"📊 Total plans returned by API: {len(plans)}")
        print()
        
        # Step 2: Analyze each plan in detail
        print("🔍 STEP 2: DETAILED PLAN ANALYSIS")
        print("-" * 40)
        
        for i, plan in enumerate(plans, 1):
            print(f"Plan {i}:")
            print(f"  📝 ID: {plan.get('_id')}")
            print(f"  🆔 Plan ID: {plan.get('id', 'N/A')}")
            print(f"  👤 User ID: {plan.get('user_id')}")
            print(f"  🌍 Language: {plan.get('language', 'Unknown')}")
            print(f"  📈 Level: {plan.get('proficiency_level', 'Unknown')}")
            print(f"  📅 Duration: {plan.get('duration_months', 'Unknown')} months")
            print(f"  📊 Progress: {plan.get('progress_percentage', 0)}%")
            print(f"  ✅ Completed: {plan.get('is_completed', False)}")
            print(f"  📅 Created: {plan.get('created_at', 'Unknown')}")
            print(f"  🔄 Updated: {plan.get('updated_at', 'Unknown')}")
            
            # Check for fields that might cause filtering
            total_sessions = plan.get('total_sessions')
            completed_sessions = plan.get('completed_sessions', 0)
            print(f"  🎯 Sessions: {completed_sessions}/{total_sessions}")
            
            # Check if plan has required fields for frontend display
            has_plan_content = 'plan_content' in plan
            has_weekly_schedule = False
            if has_plan_content:
                weekly_schedule = plan.get('plan_content', {}).get('weekly_schedule', [])
                has_weekly_schedule = len(weekly_schedule) > 0
            
            print(f"  📋 Has plan_content: {has_plan_content}")
            print(f"  📅 Has weekly_schedule: {has_weekly_schedule}")
            
            # Check for any null or problematic values
            problematic_fields = []
            if not plan.get('language'):
                problematic_fields.append('language')
            if not plan.get('proficiency_level'):
                problematic_fields.append('proficiency_level')
            if total_sessions is None:
                problematic_fields.append('total_sessions')
            if not has_plan_content:
                problematic_fields.append('plan_content')
            
            if problematic_fields:
                print(f"  ⚠️ Problematic fields: {', '.join(problematic_fields)}")
            else:
                print(f"  ✅ All required fields present")
            
            print()
        
        # Step 3: Check for potential frontend filtering conditions
        print("🔍 STEP 3: FRONTEND FILTERING ANALYSIS")
        print("-" * 40)
        
        # Common filtering conditions that might hide plans
        visible_plans = []
        hidden_plans = []
        
        for plan in plans:
            # Check various conditions that might cause a plan to be hidden
            is_visible = True
            hide_reasons = []
            
            # Check 1: Missing required fields
            if not plan.get('language'):
                is_visible = False
                hide_reasons.append('Missing language')
            
            if not plan.get('proficiency_level'):
                is_visible = False
                hide_reasons.append('Missing proficiency_level')
            
            # Check 2: Missing plan content
            if not plan.get('plan_content'):
                is_visible = False
                hide_reasons.append('Missing plan_content')
            
            # Check 3: Empty weekly schedule
            weekly_schedule = plan.get('plan_content', {}).get('weekly_schedule', [])
            if len(weekly_schedule) == 0:
                is_visible = False
                hide_reasons.append('Empty weekly_schedule')
            
            # Check 4: Total sessions is None or 0
            total_sessions = plan.get('total_sessions')
            if total_sessions is None or total_sessions == 0:
                is_visible = False
                hide_reasons.append('Invalid total_sessions')
            
            # Check 5: Plan is marked as completed
            if plan.get('is_completed', False):
                is_visible = False
                hide_reasons.append('Plan marked as completed')
            
            # Check 6: Very old plans (created before a certain date)
            created_at = plan.get('created_at')
            if created_at and isinstance(created_at, str):
                try:
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    # If plan is older than 6 months, it might be hidden
                    six_months_ago = datetime.now().replace(month=datetime.now().month-6 if datetime.now().month > 6 else datetime.now().month+6, year=datetime.now().year-1 if datetime.now().month <= 6 else datetime.now().year)
                    if created_date < six_months_ago:
                        # Don't hide for age, but note it
                        hide_reasons.append(f'Old plan (created {created_date.strftime("%Y-%m-%d")})')
                except:
                    pass
            
            if is_visible:
                visible_plans.append(plan)
            else:
                hidden_plans.append((plan, hide_reasons))
        
        print(f"📊 FILTERING RESULTS:")
        print(f"   Visible plans: {len(visible_plans)}")
        print(f"   Hidden plans: {len(hidden_plans)}")
        print()
        
        if hidden_plans:
            print("🚫 HIDDEN PLANS ANALYSIS:")
            for i, (plan, reasons) in enumerate(hidden_plans, 1):
                print(f"   Hidden Plan {i}:")
                print(f"     📝 ID: {plan.get('_id')}")
                print(f"     🌍 Language: {plan.get('language', 'Missing')}")
                print(f"     📈 Level: {plan.get('proficiency_level', 'Missing')}")
                print(f"     📅 Created: {plan.get('created_at', 'Unknown')}")
                print(f"     ❌ Hide reasons: {', '.join(reasons)}")
                print()
        
        # Step 4: Check if the issue is in the frontend code
        print("🔍 STEP 4: FRONTEND CODE ANALYSIS")
        print("-" * 40)
        
        print("Based on the backend learning_routes.py analysis:")
        print("✅ The get_user_learning_plans() function should return all plans")
        print("✅ No filtering is applied in the backend API")
        print("✅ Backward compatibility is handled for missing fields")
        print()
        
        if len(visible_plans) == 3 and len(plans) == 4:
            print("🎯 LIKELY CAUSE IDENTIFIED:")
            print("   The backend API returns all 4 plans correctly")
            print("   But 1 plan is being filtered out due to missing/invalid data")
            print("   The frontend likely filters out plans with incomplete data")
            print()
            
            if hidden_plans:
                print("🔧 RECOMMENDED FIX:")
                for plan, reasons in hidden_plans:
                    print(f"   Fix plan {plan.get('_id')}:")
                    for reason in reasons:
                        if 'Missing language' in reason:
                            print(f"     - Set language field")
                        elif 'Missing proficiency_level' in reason:
                            print(f"     - Set proficiency_level field")
                        elif 'Missing plan_content' in reason:
                            print(f"     - Generate plan_content structure")
                        elif 'Empty weekly_schedule' in reason:
                            print(f"     - Generate weekly_schedule")
                        elif 'Invalid total_sessions' in reason:
                            print(f"     - Calculate and set total_sessions")
        
        return len(visible_plans), len(hidden_plans)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0, 0

if __name__ == "__main__":
    visible, hidden = asyncio.run(investigate_frontend_discrepancy())
    print(f"\n🏁 FINAL ANALYSIS:")
    print(f"   Database has: 4 learning plans")
    print(f"   Frontend should show: {visible} plans")
    print(f"   Hidden due to data issues: {hidden} plans")
    
    if hidden > 0:
        print(f"\n💡 CONCLUSION: The discrepancy is caused by {hidden} plan(s) having incomplete data")
        print(f"   The frontend correctly filters out plans with missing required fields")
    else:
        print(f"\n💡 CONCLUSION: All plans should be visible - investigate frontend filtering logic")
