"""
Intelligent Challenge Generator
Generates personalized challenges from user's actual practice data
50% from user's mistakes/weaknesses, 50% from intelligent seed data
"""

import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from database import database


async def generate_challenges_from_user_data(
    user_id: str,
    user_level: str,
    num_challenges: int = 3
) -> List[Dict[str, Any]]:
    """
    Generate challenges from user's actual practice data:
    - Past mistakes from sessions
    - Weak flashcards
    - Learning plan struggles

    Returns up to num_challenges personalized challenges
    """
    personalized_challenges = []

    try:
        # 1. EXTRACT FROM FLASHCARDS (Low mastery = needs practice)
        flashcards_collection = database.flashcards
        weak_flashcards = await flashcards_collection.find({
            "user_id": user_id,
            "mastery_level": {"$lt": 0.5},
            "is_active": True
        }).limit(5).to_list(length=5)

        for card in weak_flashcards:
            if len(personalized_challenges) >= num_challenges:
                break

            # Generate SMART_FLASHCARD from weak flashcard
            challenge = {
                "id": f"user_fc_{card.get('id', random.randint(1000, 9999))}",
                "type": "smart_flashcard",
                "title": "Review From Your Practice",
                "emoji": "📚",
                "description": "Word you struggled with",
                "cefrLevel": user_level,
                "estimatedSeconds": 15,
                "word": card.get("front", ""),
                "context": card.get("category", "vocabulary"),
                "explanation": card.get("back", ""),
                "exampleSentence": f"Example: {card.get('front', '')}",
                "tags": card.get("tags", []),
                "completed": False,
                "source": "user_flashcard"
            }
            personalized_challenges.append(challenge)

        # 2. EXTRACT FROM SESSION BACKGROUND ANALYSES
        # Look for grammar_issues from past practice sessions
        sessions_collection = database.conversation_sessions
        recent_sessions = await sessions_collection.find({
            "user_id": user_id,
            "enhanced_analysis": {"$exists": True}
        }).sort("created_at", -1).limit(5).to_list(length=5)

        for session in recent_sessions:
            if len(personalized_challenges) >= num_challenges:
                break

            enhanced_analysis = session.get("enhanced_analysis", {})
            insights = enhanced_analysis.get("insights", {})
            grammar_points = insights.get("grammar_to_review", [])

            # Generate ERROR_SPOTTING from user's actual mistakes
            if grammar_points and len(grammar_points) > 0:
                grammar_issue = random.choice(grammar_points)

                # Create challenge from user's mistake
                challenge = {
                    "id": f"user_es_{random.randint(1000, 9999)}",
                    "type": "error_spotting",
                    "title": "From Your Last Session",
                    "emoji": "🧩",
                    "description": "You made this mistake",
                    "cefrLevel": user_level,
                    "estimatedSeconds": 12,
                    "sentence": grammar_issue.get("example", ""),
                    "options": [
                        {"id": "opt1", "text": "part 1", "isCorrect": True},
                        {"id": "opt2", "text": "part 2", "isCorrect": False},
                        {"id": "opt3", "text": "part 3", "isCorrect": False},
                    ],
                    "explanation": grammar_issue.get("explanation", ""),
                    "correctedSentence": grammar_issue.get("correct", ""),
                    "tags": ["user_mistake", grammar_issue.get("category", "grammar")],
                    "completed": False,
                    "source": "user_session"
                }
                personalized_challenges.append(challenge)

        # 3. EXTRACT FROM LEARNING PLAN WEAKNESSES
        learning_plans_collection = database.learning_plans
        learning_plan = await learning_plans_collection.find_one({
            "user_id": user_id
        }, sort=[("updated_at", -1)])

        if learning_plan and len(personalized_challenges) < num_challenges:
            plan_content = learning_plan.get("plan_content", {})
            weekly_schedule = plan_content.get("weekly_schedule", [])

            # Look for topics in current/recent weeks
            for week in weekly_schedule[-3:]:  # Last 3 weeks
                if len(personalized_challenges) >= num_challenges:
                    break

                focus = week.get("focus", "")
                goals = week.get("goals", [])

                if focus:
                    # Generate NATIVE_CHECK based on learning plan focus
                    challenge = {
                        "id": f"user_nc_{random.randint(1000, 9999)}",
                        "type": "native_check",
                        "title": "From Your Learning Plan",
                        "emoji": "🧠",
                        "description": f"Testing: {focus}",
                        "cefrLevel": user_level,
                        "estimatedSeconds": 12,
                        "sentence": f"Example sentence about {focus}",
                        "isNatural": True,
                        "correctedVersion": None,
                        "explanation": f"This tests your understanding of {focus}",
                        "tags": ["learning_plan", focus.lower().replace(" ", "_")],
                        "completed": False,
                        "source": "learning_plan"
                    }
                    personalized_challenges.append(challenge)

        print(f"[CHALLENGE_GEN] Generated {len(personalized_challenges)} personalized challenges from user data")
        return personalized_challenges

    except Exception as e:
        print(f"[CHALLENGE_GEN] Error generating from user data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []


async def get_intelligent_seed_challenges(
    user_level: str,
    num_challenges: int = 3,
    exclude_types: List[str] = []
) -> List[Dict[str, Any]]:
    """
    Get intelligent seed challenges from database
    These are generic but level-appropriate challenges

    Args:
        user_level: CEFR level
        num_challenges: How many to return
        exclude_types: Challenge types to exclude (already covered by user data)

    Returns:
        List of challenges from seed database
    """
    try:
        # Default to B1 if no level provided
        if not user_level or user_level == "None":
            user_level = "B1"
            print(f"[CHALLENGE_GEN] No user level provided, defaulting to B1")

        challenges_collection = database.challenges

        # Define remaining types needed
        all_types = ["error_spotting", "swipe_fix", "micro_quiz", "smart_flashcard", "native_check", "brain_tickler"]
        needed_types = [t for t in all_types if t not in exclude_types]

        # Limit to num_challenges types
        needed_types = needed_types[:num_challenges]

        seed_challenges = []

        for challenge_type in needed_types:
            # Get random challenge of this type at user's level
            pipeline = [
                {
                    "$match": {
                        "type": challenge_type,
                        "cefrLevel": user_level,
                        "source": {"$exists": False}  # Only seed data, not user-generated
                    }
                },
                {"$sample": {"size": 1}}
            ]

            cursor = challenges_collection.aggregate(pipeline)
            results = await cursor.to_list(length=1)

            if results:
                challenge = results[0]
                challenge.pop("_id", None)
                seed_challenges.append(challenge)

        print(f"[CHALLENGE_GEN] Retrieved {len(seed_challenges)} seed challenges")
        return seed_challenges

    except Exception as e:
        print(f"[CHALLENGE_GEN] Error getting seed challenges: {str(e)}")
        return []


async def generate_daily_challenges_intelligent(
    user_id: str,
    user_level: str
) -> List[Dict[str, Any]]:
    """
    MAIN FUNCTION: Generate 6 daily challenges

    Strategy:
    - 50% from user's actual data (mistakes, weaknesses)
    - 50% from intelligent seed data (level-appropriate)

    Returns:
        List of 6 challenges (mixed personalized + seed)
    """
    try:
        print(f"[CHALLENGE_GEN] 🎯 Generating intelligent challenges for user {user_id} (level: {user_level})")

        # Step 1: Try to get 3 personalized challenges from user data
        user_challenges = await generate_challenges_from_user_data(
            user_id=user_id,
            user_level=user_level,
            num_challenges=3
        )

        # Track which types we've covered
        covered_types = [c["type"] for c in user_challenges]

        # Step 2: Fill remaining slots with seed challenges
        remaining_count = 6 - len(user_challenges)

        seed_challenges = await get_intelligent_seed_challenges(
            user_level=user_level,
            num_challenges=remaining_count,
            exclude_types=covered_types
        )

        # Combine both
        all_challenges = user_challenges + seed_challenges

        # Shuffle to mix personalized and seed
        random.shuffle(all_challenges)

        # Ensure we have exactly 6 (fill with more seed if needed)
        if len(all_challenges) < 6:
            additional = await get_intelligent_seed_challenges(
                user_level=user_level,
                num_challenges=6 - len(all_challenges),
                exclude_types=[]
            )
            all_challenges.extend(additional)

        # Limit to 6
        all_challenges = all_challenges[:6]

        print(f"[CHALLENGE_GEN] ✅ Generated {len(all_challenges)} challenges:")
        print(f"[CHALLENGE_GEN]   - {len(user_challenges)} from user data")
        print(f"[CHALLENGE_GEN]   - {len(seed_challenges)} from seed data")

        return all_challenges

    except Exception as e:
        print(f"[CHALLENGE_GEN] ❌ Error in intelligent generation: {str(e)}")
        import traceback
        print(traceback.format_exc())

        # Fallback: Return 6 seed challenges
        return await get_intelligent_seed_challenges(user_level, 6, [])
