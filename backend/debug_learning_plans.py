#!/usr/bin/env python3
"""
Debug learning plans query to understand why we're not finding them
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Production MongoDB connection
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

async def debug_learning_plans():
    """Debug learning plans query"""
    
    print("🔍 DEBUGGING LEARNING PLANS QUERY")
    print("=" * 50)
    
    # Connect to production MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    user_id = "688921c268819565ef1ce3dc"
    user_object_id = ObjectId(user_id)
    
    print(f"👤 User ID: {user_id}")
    print(f"👤 User ObjectId: {user_object_id}")
    print()
    
    # Check different ways to query learning plans
    print("🔍 Method 1: Query by user_id as ObjectId")
    plans1 = await db.learning_plans.find({"user_id": user_object_id}).to_list(None)
    print(f"   Found: {len(plans1)} plans")
    
    print("🔍 Method 2: Query by user_id as string")
    plans2 = await db.learning_plans.find({"user_id": user_id}).to_list(None)
    print(f"   Found: {len(plans2)} plans")
    
    print("🔍 Method 3: Query by userId as ObjectId")
    plans3 = await db.learning_plans.find({"userId": user_object_id}).to_list(None)
    print(f"   Found: {len(plans3)} plans")
    
    print("🔍 Method 4: Query by userId as string")
    plans4 = await db.learning_plans.find({"userId": user_id}).to_list(None)
    print(f"   Found: {len(plans4)} plans")
    
    # Get a sample of all learning plans to see the structure
    print("\n🔍 Sample learning plans structure:")
    sample_plans = await db.learning_plans.find().limit(3).to_list(None)
    for i, plan in enumerate(sample_plans):
        print(f"   Plan {i+1}:")
        print(f"      _id: {plan.get('_id')}")
        print(f"      user_id: {plan.get('user_id')} (type: {type(plan.get('user_id'))})")
        print(f"      userId: {plan.get('userId')} (type: {type(plan.get('userId'))})")
        print(f"      name: {plan.get('name', 'N/A')}")
        print(f"      sessions count: {len(plan.get('sessions', []))}")
        print()
    
    # Find the correct plans
    all_methods = [plans1, plans2, plans3, plans4]
    correct_plans = None
    for i, plans in enumerate(all_methods, 1):
        if len(plans) > 0:
            print(f"✅ Method {i} found plans! Using this method.")
            correct_plans = plans
            break
    
    if correct_plans:
        print(f"\n📋 FOUND {len(correct_plans)} LEARNING PLANS:")
        total_conversation_minutes = 0.0
        
        for i, plan in enumerate(correct_plans, 1):
            plan_name = plan.get('name', f'Plan {i}')
            sessions = plan.get('sessions', [])
            
            print(f"\n   Plan {i}: {plan_name}")
            print(f"      Plan ID: {plan['_id']}")
            print(f"      Sessions: {len(sessions)}")
            
            plan_minutes = 0.0
            for j, session in enumerate(sessions):
                if session.get('completed_at'):
                    # Check various duration fields
                    duration = 0.0
                    if 'conversation_duration' in session:
                        duration = float(session['conversation_duration'])
                    elif 'duration' in session:
                        duration = float(session['duration'])
                    elif 'conversation_data' in session and session['conversation_data']:
                        conv_data = session['conversation_data']
                        if isinstance(conv_data, dict) and 'duration' in conv_data:
                            duration = float(conv_data['duration'])
                    
                    if duration > 0:
                        plan_minutes += duration
                        print(f"         Session {j+1}: {duration:.2f} min on {session.get('completed_at')}")
            
            print(f"      Total conversation minutes: {plan_minutes:.2f}")
            total_conversation_minutes += plan_minutes
        
        print(f"\n🎯 TOTAL LEARNING PLAN CONVERSATION MINUTES: {total_conversation_minutes:.2f}")
    else:
        print("❌ No learning plans found with any method!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(debug_learning_plans())
