#!/usr/bin/env python3
"""
Check Learning Plans for Specific User
Investigate how many custom learning plans exist for user 688921c268819565ef1ce3dc
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import database
from bson import ObjectId

async def check_user_learning_plans():
    """Check learning plans for the specific user"""
    
    print("🔍 CHECKING USER LEARNING PLANS")
    print("=" * 50)
    print(f"Investigation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    target_user_id = "688921c268819565ef1ce3dc"
    print(f"👤 Target User ID: {target_user_id}")
    print()
    
    try:
        # Convert to ObjectId for MongoDB query
        user_object_id = ObjectId(target_user_id)
        
        # Query 1: Find all learning plans for this user
        print("📋 QUERYING LEARNING PLANS COLLECTION...")
        learning_plans = await database["learning_plans"].find({
            "user_id": target_user_id
        }).to_list(length=None)
        
        print(f"✅ Found {len(learning_plans)} learning plans for user {target_user_id}")
        print()
        
        if learning_plans:
            print("📊 LEARNING PLANS DETAILS:")
            print("-" * 40)
            
            for i, plan in enumerate(learning_plans, 1):
                print(f"Plan {i}:")
                print(f"  📝 ID: {plan.get('_id')}")
                print(f"  🌍 Language: {plan.get('language', 'Unknown')}")
                print(f"  📈 Level: {plan.get('level', 'Unknown')}")
                print(f"  📅 Duration: {plan.get('duration_months', 'Unknown')} months")
                print(f"  🎯 Title: {plan.get('title', 'No title')}")
                print(f"  📊 Progress: {plan.get('progress_percentage', 0)}%")
                print(f"  ✅ Completed: {plan.get('is_completed', False)}")
                print(f"  📅 Created: {plan.get('created_at', 'Unknown')}")
                print(f"  🔄 Updated: {plan.get('updated_at', 'Unknown')}")
                
                # Check sessions
                sessions = plan.get('sessions', [])
                completed_sessions = len([s for s in sessions if s.get('completed')])
                print(f"  🎯 Sessions: {completed_sessions}/{len(sessions)} completed")
                
                # Check if it's a custom plan
                is_custom = plan.get('is_custom', False)
                plan_type = plan.get('plan_type', 'unknown')
                print(f"  🎨 Custom Plan: {is_custom}")
                print(f"  📋 Plan Type: {plan_type}")
                print()
        
        # Query 2: Also check if there are any plans with ObjectId format
        print("🔍 CHECKING WITH OBJECTID FORMAT...")
        learning_plans_objectid = await database["learning_plans"].find({
            "user_id": user_object_id
        }).to_list(length=None)
        
        if learning_plans_objectid:
            print(f"✅ Found {len(learning_plans_objectid)} additional plans with ObjectId format")
            for i, plan in enumerate(learning_plans_objectid, len(learning_plans) + 1):
                print(f"Plan {i} (ObjectId format):")
                print(f"  📝 ID: {plan.get('_id')}")
                print(f"  🌍 Language: {plan.get('language', 'Unknown')}")
                print(f"  📈 Level: {plan.get('level', 'Unknown')}")
                print(f"  🎨 Custom Plan: {plan.get('is_custom', False)}")
                print()
        else:
            print("ℹ️ No additional plans found with ObjectId format")
        
        # Total count
        total_plans = len(learning_plans) + len(learning_plans_objectid)
        print("📊 SUMMARY:")
        print("-" * 20)
        print(f"Total Learning Plans: {total_plans}")
        print(f"String format user_id: {len(learning_plans)}")
        print(f"ObjectId format user_id: {len(learning_plans_objectid)}")
        print()
        
        # Query 3: Check user document to see what the frontend might be reading
        print("👤 CHECKING USER DOCUMENT...")
        user_doc = await database["users"].find_one({"_id": user_object_id})
        
        if user_doc:
            print("✅ User document found")
            
            # Check if user has any learning plan references
            user_learning_plans = user_doc.get('learning_plans', [])
            if user_learning_plans:
                print(f"📋 User document has {len(user_learning_plans)} learning plan references:")
                for plan_ref in user_learning_plans:
                    print(f"  - {plan_ref}")
            else:
                print("ℹ️ No learning plan references in user document")
            
            # Check other relevant fields
            current_plan = user_doc.get('current_learning_plan')
            if current_plan:
                print(f"🎯 Current learning plan: {current_plan}")
            
            active_plans = user_doc.get('active_learning_plans', [])
            if active_plans:
                print(f"🔄 Active learning plans: {len(active_plans)}")
                for plan in active_plans:
                    print(f"  - {plan}")
        else:
            print("❌ User document not found")
        
        print()
        print("🎯 FRONTEND DISCREPANCY ANALYSIS:")
        print("-" * 35)
        print(f"Frontend shows: 3 learning plans")
        print(f"Database has: {total_plans} learning plans")
        
        if total_plans == 3:
            print("✅ MATCH: Database and frontend show the same count (3)")
        elif total_plans == 4:
            print("⚠️ DISCREPANCY: Database has 4 plans but frontend shows 3")
            print("   Possible causes:")
            print("   - One plan is hidden/filtered in frontend")
            print("   - One plan has is_active=false")
            print("   - Frontend query has different filters")
        else:
            print(f"❓ UNEXPECTED: Database has {total_plans} plans, frontend shows 3")
        
        return total_plans
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    count = asyncio.run(check_user_learning_plans())
    print(f"\n🏁 FINAL RESULT: Found {count} learning plans in database")
