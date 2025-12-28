#!/usr/bin/env python3
"""
Create Test Learning Plan for Final Assessment Testing
=======================================================

Creates a 1-month B1 English learning plan with:
- 8 total sessions (all completed)
- Status: awaiting_final_assessment
- User: Ali Pala (alipala.ist@gmail.com)

This is for testing the final assessment feature without breaking existing plans.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from bson import ObjectId
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import database

async def create_test_learning_plan():
    """Create a test learning plan for final assessment testing"""

    try:
        learning_plans_collection = database["learning_plans"]

        print("=" * 80)
        print("CREATING TEST LEARNING PLAN FOR FINAL ASSESSMENT")
        print("=" * 80)

        # User details
        user_id = "688921c268819565ef1ce3dc"
        user_email = "alipala.ist@gmail.com"
        user_name = "Ali Pala"

        print(f"User: {user_name} ({user_email})")
        print(f"User ID: {user_id}")
        print()

        # Plan details
        plan_id = str(uuid.uuid4())
        created_date = datetime.utcnow() - timedelta(days=28)  # Created 28 days ago
        all_sessions_completed_date = datetime.utcnow() - timedelta(hours=2)  # Completed 2 hours ago

        # Create weekly schedule with 4 weeks, 2 sessions per week = 8 sessions total
        weekly_schedule = []
        session_number = 0

        for week in range(1, 5):  # 4 weeks
            week_data = {
                "week": week,
                "focus": "Mastering intermediate grammar and expanding vocabulary",
                "activities": [
                    "Practice complex sentence structures",
                    "Engage in longer conversations",
                    "Expand vocabulary on various topics"
                ],
                "sessions_completed": 2,  # All sessions completed
                "total_sessions": 2,
                "session_details": []
            }

            # Create 2 sessions per week
            for session_in_week in range(1, 3):
                session_number += 1
                session_date = created_date + timedelta(days=(week - 1) * 7 + (session_in_week - 1) * 3)

                session_data = {
                    "session_number": session_in_week,
                    "focus": "Mastering intermediate grammar and expanding vocabulary",
                    "completed_at": session_date.isoformat(),
                    "duration_minutes": 15.0 + (session_number * 0.5),  # Varying durations
                    "session_summary": f"Completed session {session_number} with good progress on grammar and vocabulary.",
                    "status": "completed"
                }

                week_data["session_details"].append(session_data)

            weekly_schedule.append(week_data)

        # Create the learning plan document
        learning_plan = {
            "_id": ObjectId(),
            "id": plan_id,
            "user_id": user_id,
            "language": "english",
            "proficiency_level": "B1",
            "goals": ["daily", "travel"],
            "duration_months": 1,
            "custom_goal": None,
            "plan_content": {
                "title": "1-Month English Learning Plan for B1 Level",
                "overview": "This comprehensive plan is designed to help you master B1 English skills in 1 month with 8 structured sessions.",
                "assessment_summary": {
                    "overall_score": 75,
                    "recommended_level": "B1",
                    "strengths": [
                        "Good vocabulary range for everyday topics",
                        "Ability to communicate in familiar situations"
                    ],
                    "areas_for_improvement": [
                        "Grammar accuracy in complex sentences",
                        "Fluency in spontaneous conversations"
                    ],
                    "skill_scores": {
                        "pronunciation": 72,
                        "grammar": 70,
                        "vocabulary": 78,
                        "fluency": 68,
                        "coherence": 75
                    }
                },
                "weekly_schedule": weekly_schedule,
                "learning_objectives": [
                    "Master intermediate grammar structures",
                    "Expand vocabulary for daily life and travel",
                    "Improve conversational fluency",
                    "Build confidence in real-world communication",
                    "Prepare for B2 level advancement"
                ],
                "resources": [
                    "English Grammar Guide for B1 Level",
                    "Vocabulary Builder for Travel English",
                    "Conversation Practice Exercises",
                    "Real-life Scenario Simulations"
                ],
                "progress_tracking": {
                    "total_weeks": 4,
                    "sessions_per_week": 2,
                    "total_sessions": 8,
                    "milestone_weeks": [2, 4]
                }
            },
            "assessment_data": {
                "recognized_text": "I want to improve my English for daily conversations and travel.",
                "overall_score": 75,
                "recommended_level": "B1"
            },
            "total_sessions": 8,
            "completed_sessions": 8,  # ALL SESSIONS COMPLETED
            "progress_percentage": 100.0,  # 100% progress
            "practice_minutes_used": 130.0,  # Total practice time
            "total_practice_minutes": 40,  # Expected minimum
            "created_at": created_date.isoformat(),
            "updated_at": all_sessions_completed_date.isoformat(),

            # NEW: Final Assessment Fields
            "status": "awaiting_final_assessment",  # Waiting for final assessment
            "all_sessions_completed_at": all_sessions_completed_date.isoformat(),
            "final_assessment": {
                "required": True,
                "completed": False,
                "attempts": [],  # No attempts yet
                "minimum_duration_minutes": 4,  # B1 requires 4 minutes
                "passed": False,
                "last_attempt_date": None
            }
        }

        # Check if user already has a similar plan
        existing = await learning_plans_collection.find_one({
            "user_id": user_id,
            "language": "english",
            "proficiency_level": "B1",
            "status": "awaiting_final_assessment"
        })

        if existing:
            print("⚠️  User already has an English B1 plan awaiting assessment!")
            print(f"Existing plan ID: {existing.get('id')}")
            print()

            response = input("Delete existing plan and create new one? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cancelled. Keeping existing plan.")
                return

            # Delete existing plan
            result = await learning_plans_collection.delete_one({"_id": existing["_id"]})
            print(f"✓ Deleted existing plan: {existing.get('id')}")
            print()

        # Insert the new plan
        result = await learning_plans_collection.insert_one(learning_plan)

        if result.inserted_id:
            print("✅ TEST LEARNING PLAN CREATED SUCCESSFULLY!")
            print()
            print("Plan Details:")
            print(f"  Plan ID: {plan_id}")
            print(f"  Language: English")
            print(f"  Level: B1")
            print(f"  Duration: 1 month")
            print(f"  Total Sessions: 8")
            print(f"  Completed Sessions: 8 (100%)")
            print(f"  Status: awaiting_final_assessment")
            print(f"  Assessment Required: 4 minutes minimum")
            print()
            print("User can now:")
            print("  ✓ See 'Final Assessment Required' banner in iOS app")
            print("  ✓ Click 'Take Assessment' button")
            print("  ✓ Complete 4-minute speaking assessment")
            print("  ✓ Pass assessment to advance to B2")
            print("  ✓ Or practice more and retry if failed")
            print()
            print("=" * 80)
            print("TEST PLAN READY FOR FINAL ASSESSMENT TESTING!")
            print("=" * 80)
        else:
            print("❌ Failed to create test learning plan")

    except Exception as e:
        print(f"❌ Error creating test plan: {str(e)}")
        import traceback
        traceback.print_exc()


async def verify_test_plan():
    """Verify the test plan was created correctly"""
    try:
        learning_plans_collection = database["learning_plans"]
        user_id = "688921c268819565ef1ce3dc"

        print()
        print("=" * 80)
        print("VERIFICATION")
        print("=" * 80)

        # Find the plan
        plan = await learning_plans_collection.find_one({
            "user_id": user_id,
            "language": "english",
            "proficiency_level": "B1",
            "status": "awaiting_final_assessment"
        })

        if plan:
            print("✅ Test plan found!")
            print(f"  Plan ID: {plan.get('id')}")
            print(f"  Status: {plan.get('status')}")
            print(f"  Completed: {plan.get('completed_sessions')}/{plan.get('total_sessions')}")
            print(f"  Progress: {plan.get('progress_percentage')}%")
            print(f"  Final Assessment Required: {plan.get('final_assessment', {}).get('required')}")
            print(f"  Assessment Duration: {plan.get('final_assessment', {}).get('minimum_duration_minutes')} minutes")
            print(f"  Attempts: {len(plan.get('final_assessment', {}).get('attempts', []))}")
            print()
            print("✅ Plan is ready for testing!")
        else:
            print("❌ Test plan not found!")

        print("=" * 80)

    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")


async def main():
    """Main entry point"""
    await create_test_learning_plan()
    await verify_test_plan()


if __name__ == "__main__":
    asyncio.run(main())
