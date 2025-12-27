"""
Create a test English A1 learning plan with all sessions completed
for testing the final assessment system (2-minute duration)

User: Ali Pala (alipala.ist@gmail.com)
User ID: 688921c268819565ef1ce3dc
"""

import sys
import os
from datetime import datetime, timedelta
from bson import ObjectId
import uuid

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_database
import asyncio

async def create_a1_test_plan():
    """Create English A1 test learning plan"""

    db = await get_database()
    learning_plans = db["learning_plans"]

    # User info
    user_id = "688921c268819565ef1ce3dc"  # Store as STRING to match existing plans
    user_email = "alipala.ist@gmail.com"

    # Check if similar plan already exists
    existing = await learning_plans.find_one({
        "user_id": user_id,
        "language": "english",
        "proficiency_level": "A1",
        "duration_months": 1,
        "status": "awaiting_final_assessment"
    })

    if existing:
        print(f"⚠️  Similar A1 plan already exists: {existing['id']}")
        response = input("Delete existing plan and create new one? (y/n): ")
        if response.lower() == 'y':
            await learning_plans.delete_one({"_id": existing["_id"]})
            print(f"✅ Deleted existing plan")
        else:
            print("Cancelled")
            return

    # Generate unique plan ID
    plan_id = str(uuid.uuid4())

    # Create A1 level plan content
    plan_content = {
        "title": "English A1 - 1 Month Beginner Plan",
        "overview": "Build foundational English skills for everyday situations",
        "weekly_schedule": [
            {
                "week": 1,
                "focus": "Basic Greetings and Introductions",
                "activities": [
                    "Introduce yourself (name, age, country)",
                    "Practice basic greetings (Hello, Good morning, How are you?)",
                    "Learn to say goodbye politely",
                    "Simple questions: What's your name? Where are you from?"
                ]
            },
            {
                "week": 2,
                "focus": "Family and Daily Routines",
                "activities": [
                    "Describe family members (mother, father, sister, brother)",
                    "Talk about daily activities (wake up, eat, sleep)",
                    "Use present simple tense",
                    "Tell time: What time do you...?"
                ]
            },
            {
                "week": 3,
                "focus": "Food and Shopping",
                "activities": [
                    "Name common foods (apple, bread, water, coffee)",
                    "Order food: I would like..., Can I have...?",
                    "Ask prices: How much is...?",
                    "Numbers 1-100"
                ]
            },
            {
                "week": 4,
                "focus": "Hobbies and Free Time",
                "activities": [
                    "Talk about hobbies: I like..., I enjoy...",
                    "Common activities (reading, watching TV, playing)",
                    "Yes/No questions: Do you like...?",
                    "Express simple preferences"
                ]
            }
        ],
        "assessment_summary": {
            "overall_score": 45,
            "recommended_level": "A1",
            "strengths": ["Basic vocabulary", "Simple greetings"],
            "areas_for_improvement": ["Grammar structures", "Pronunciation", "Fluency"],
            "grammar": {"score": 40, "feedback": "Basic present tense usage"},
            "vocabulary": {"score": 50, "feedback": "Elementary word knowledge"},
            "fluency": {"score": 35, "feedback": "Slow pace, frequent pauses"},
            "coherence": {"score": 45, "feedback": "Simple connected ideas"},
            "pronunciation": {"score": 40, "feedback": "Clear but basic"}
        }
    }

    # Create 8 completed sessions with realistic timestamps
    # NOTE: session_summaries must be List[str], not List[dict]!
    session_summaries = []
    base_date = datetime.utcnow() - timedelta(days=28)  # 4 weeks ago

    for i in range(8):
        week_num = (i // 2) + 1  # 2 sessions per week
        session_date = base_date + timedelta(days=i * 3.5)  # Every ~3.5 days
        focus = plan_content["weekly_schedule"][week_num - 1]["focus"]

        # Format as string summary (not dict!)
        summary_str = f"Session {i+1} - Week {week_num}: {focus}. Duration: 5 min. Practiced {focus.lower()} with good progress."
        session_summaries.append(summary_str)

    # Create the learning plan document
    learning_plan = {
        "id": plan_id,
        "user_id": user_id,
        "language": "english",
        "target_language": "english",
        "proficiency_level": "A1",
        "target_cefr_level": "A1",
        "duration_months": 1,
        "goals": [  # REQUIRED field!
            "Basic Greetings and Introductions",
            "Family and Daily Routines",
            "Food and Shopping",
            "Hobbies and Free Time"
        ],
        "plan_content": plan_content,
        "created_at": (datetime.utcnow() - timedelta(days=28)).isoformat(),
        "updated_at": datetime.utcnow().isoformat(),

        # Progress tracking
        "completed_sessions": 8,
        "total_sessions": 8,
        "progress_percentage": 100.0,
        "session_summaries": session_summaries,

        # NEW: Final Assessment Fields
        "status": "awaiting_final_assessment",
        "all_sessions_completed_at": datetime.utcnow().isoformat(),
        "final_assessment": {
            "required": True,
            "completed": False,
            "attempts": [],
            "minimum_duration_minutes": 2,  # A1 = 2 minutes
            "passed": False,
            "last_attempt_date": None
        }
    }

    # Insert into database
    result = await learning_plans.insert_one(learning_plan)

    print("\n" + "="*80)
    print("✅ TEST LEARNING PLAN CREATED SUCCESSFULLY")
    print("="*80)
    print(f"Plan ID: {plan_id}")
    print(f"User: {user_email}")
    print(f"Level: English A1")
    print(f"Duration: 1 month")
    print(f"Sessions: 8/8 completed")
    print(f"Status: awaiting_final_assessment")
    print(f"Assessment Duration: 2 minutes")
    print(f"MongoDB _id: {result.inserted_id}")
    print("="*80)
    print("\n📱 You can now:")
    print("1. Open the iOS app")
    print("2. Navigate to the dashboard")
    print("3. Find the 'English A1 - 1 Month Beginner Plan' card")
    print("4. You should see the amber 'Final Assessment Required' banner")
    print("5. Click 'Take Assessment' to test the 2-minute speaking assessment")
    print("\n🎯 Expected Behavior:")
    print("- Screen title: 'Final Assessment - English A1'")
    print("- AI will conduct warm-up → A1 assessment → A2 stretch")
    print("- Target duration: 2 minutes")
    print("- Topics: Basic greetings, family, food, hobbies (A1 level)")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(create_a1_test_plan())
