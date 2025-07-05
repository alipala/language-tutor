#!/usr/bin/env python3
"""
Test script for the Instagram/WhatsApp sharing feature
"""
import asyncio
import json
from database import init_db, database
from bson import ObjectId
import requests
from datetime import datetime

async def create_test_progress_data():
    """Create some test progress data for users with learning plans"""
    await init_db()
    
    # Find a user with a learning plan
    learning_plan = await database.learning_plans.find_one({"user_id": {"$ne": None}})
    
    if not learning_plan:
        print("❌ No learning plans with user_id found")
        return None
    
    user_id = learning_plan["user_id"]
    plan_id = learning_plan["id"]
    
    print(f"✅ Found user {user_id} with learning plan {plan_id}")
    
    # Update the learning plan with some progress
    await database.learning_plans.update_one(
        {"id": plan_id},
        {
            "$set": {
                "completed_sessions": 15,
                "total_sessions": 96,
                "progress_percentage": 15.6
            }
        }
    )
    
    # Create some assessment data for this user
    assessment_data = {
        "user_id": user_id,
        "overall_score": 78,
        "confidence": 85,
        "pronunciation": {"score": 75, "feedback": "Good pronunciation with minor accent issues"},
        "grammar": {"score": 82, "feedback": "Strong grammar foundation, occasional tense errors"},
        "vocabulary": {"score": 80, "feedback": "Good vocabulary range for B1 level"},
        "fluency": {"score": 76, "feedback": "Speaks with good pace, some hesitation"},
        "coherence": {"score": 79, "feedback": "Ideas are well connected and logical"},
        "strengths": [
            "Strong vocabulary for intermediate level",
            "Good understanding of grammar structures",
            "Confident speaking style"
        ],
        "areas_for_improvement": [
            "Pronunciation of certain consonant clusters",
            "Use of advanced tenses",
            "Reducing hesitation in speech"
        ],
        "next_steps": [
            "Practice pronunciation drills",
            "Focus on past perfect and future perfect tenses",
            "Engage in more spontaneous conversations"
        ],
        "recommended_level": "B1",
        "language": "English",
        "level": "B1",
        "date": datetime.now().isoformat(),
        "source": "speaking_assessment"
    }
    
    # Store assessment data in user's profile or create a separate collection
    await database.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "latest_assessment": assessment_data,
                "assessment_history": [assessment_data]
            }
        }
    )
    
    print(f"✅ Created test progress data for user {user_id}")
    print(f"   - Learning Plan: {learning_plan['language']} {learning_plan['proficiency_level']}")
    print(f"   - Progress: 15/96 sessions (15.6%)")
    print(f"   - Assessment Score: 78/100")
    
    return {
        "user_id": user_id,
        "plan_id": plan_id,
        "assessment": assessment_data,
        "learning_plan": learning_plan
    }

def test_sharing_api(user_id, plan_id):
    """Test the sharing API endpoint"""
    
    # First, get a JWT token for this user (simulate login)
    # For testing, we'll create a simple test request
    
    test_data = {
        "assessment_id": "test_assessment_" + datetime.now().strftime("%Y%m%d"),
        "learning_plan_id": plan_id,
        "share_type": "progress",
        "platform": "instagram",
        "custom_message": "Testing my progress sharing feature!"
    }
    
    print(f"\n🧪 Testing sharing API with data:")
    print(json.dumps(test_data, indent=2))
    
    try:
        # Test the API endpoint
        response = requests.post(
            "http://localhost:8000/api/share/generate-progress-image",
            json=test_data,
            headers={
                "Content-Type": "application/json",
                # Note: In real usage, we'd need a valid JWT token
                # "Authorization": f"Bearer {jwt_token}"
            }
        )
        
        print(f"\n📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Sharing API test successful!")
            print(f"   - Image URL: {result.get('image_url', 'N/A')}")
            print(f"   - Share Text: {result.get('share_text', 'N/A')}")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

async def main():
    print("🚀 Testing Instagram/WhatsApp Sharing Feature")
    print("=" * 50)
    
    # Create test data
    test_data = await create_test_progress_data()
    
    if test_data:
        print(f"\n📊 Test Data Summary:")
        print(f"   User ID: {test_data['user_id']}")
        print(f"   Plan ID: {test_data['plan_id']}")
        print(f"   Language: {test_data['learning_plan']['language']}")
        print(f"   Level: {test_data['learning_plan']['proficiency_level']}")
        
        # Test the API
        test_sharing_api(test_data['user_id'], test_data['plan_id'])
        
        print(f"\n🎯 To test in the frontend:")
        print(f"   1. Login as user: {test_data['user_id']}")
        print(f"   2. Go to profile/dashboard")
        print(f"   3. Look for Assessment & Learning Journey cards")
        print(f"   4. Click 'Share Progress' button")
        print(f"   5. Test different platforms and share types")
    
    print("\n✅ Test setup complete!")

if __name__ == "__main__":
    asyncio.run(main())
