"""
CrewAI Multi-Agent Challenge Generation System
===============================================

This module implements intelligent challenge generation using CrewAI with 3 specialized agents:
1. Learning Analyzer Agent - Analyzes user learning patterns and weak areas
2. Challenge Generator Agent - Creates personalized, contextual challenges
3. Quality Curator Agent - Reviews and ensures challenge quality

Drop-in replacement for challenge_generator_ai.py with the same interface.
"""

import os
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# CrewAI imports
from crewai import Agent, Task, Crew, Process

# OpenAI for LLM
from openai import OpenAI

# Database connection
from database import database

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")  # Configurable model

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)


# ============================================================================
# LEARNING ANALYZER AGENT
# ============================================================================

def create_learning_analyzer_agent() -> Agent:
    """
    Creates the Learning Analyzer Agent

    This agent analyzes user's learning history, conversation sessions,
    challenge performance, and identifies weak areas.
    """
    return Agent(
        role='Learning Pattern Analyzer',
        goal='Analyze user learning patterns and identify areas needing improvement',
        backstory="""You are an expert language learning analyst with deep understanding
        of CEFR levels and pedagogical best practices. You analyze conversation sessions,
        challenge completion rates, weak vocabulary, and grammar struggles to identify
        what types of challenges will be most beneficial for each user. You consider their
        current level, recent topics discussed, and areas where they struggle.""",
        verbose=True,
        allow_delegation=False,
        llm=GPT_MODEL
    )


def create_challenge_generator_agent() -> Agent:
    """
    Creates the Challenge Generator Agent

    This agent generates high-quality, personalized challenges based on
    the analyzer's insights.
    """
    return Agent(
        role='Challenge Content Generator',
        goal='Generate high-quality, personalized language learning challenges',
        backstory="""You are a creative language teacher and content creator who excels
        at crafting engaging, educational challenges. You use insights from learning
        analysis to create challenges that are perfectly tailored to each user's level,
        interests, and learning gaps. You ensure challenges are culturally appropriate,
        grammatically correct, and pedagogically sound. You create diverse challenge
        types including error spotting, sentence fixes, quizzes, flashcards, brain
        ticklers, and more.""",
        verbose=True,
        allow_delegation=False,
        llm=GPT_MODEL
    )


def create_quality_curator_agent() -> Agent:
    """
    Creates the Quality Curator Agent

    This agent reviews generated challenges for quality, correctness,
    and appropriateness.
    """
    return Agent(
        role='Challenge Quality Curator',
        goal='Ensure all generated challenges meet high quality standards',
        backstory="""You are a meticulous quality assurance expert and language educator.
        You review every generated challenge to ensure it is grammatically correct,
        culturally appropriate, level-appropriate, and pedagogically valuable. You check
        that explanations are clear, corrections are accurate, and the challenge will
        genuinely help the learner improve. You reject or fix any challenges that don't
        meet these standards.""",
        verbose=True,
        allow_delegation=False,
        llm=GPT_MODEL
    )


# ============================================================================
# LEARNING ANALYSIS FUNCTIONS
# ============================================================================

async def analyze_user_learning_data(user_id: str, language: str = "english") -> Dict[str, Any]:
    """
    Deep analysis of user's learning history to extract:
    - Common mistakes and error patterns
    - Weak vocabulary areas
    - Grammar struggles
    - Learning plan focus areas

    Args:
        user_id: User ID
        language: Target language (default: "english")

    Returns:
        Comprehensive analysis for AI agents
    """
    analysis = {
        "user_id": user_id,
        "language": language,
        "level": "B1",
        "common_mistakes": [],
        "weak_vocabulary": [],
        "grammar_struggles": [],
        "learning_plan_topics": [],
        "session_summaries": [],
        "challenge_stats": {}
    }

    try:
        from bson import ObjectId

        # Handle special case: reference_user
        if user_id == "reference_user":
            pass
        else:
            # Get user's CEFR level
            user = await database.users.find_one({"_id": ObjectId(user_id)})
            if user:
                analysis["level"] = user.get("preferred_level", "B1") or "B1"

        # Get recent conversation sessions (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        sessions_collection = database.conversation_sessions

        recent_sessions = await sessions_collection.find({
            "user_id": user_id,
            "language": language,
            "enhanced_analysis": {"$exists": True},
            "created_at": {"$gte": thirty_days_ago}
        }).sort("created_at", -1).limit(10).to_list(length=10)

        for session in recent_sessions:
            enhanced = session.get("enhanced_analysis") or {}
            insights = enhanced.get("insights", {})

            # Extract grammar issues
            grammar_points = insights.get("grammar_to_review", [])
            for point in grammar_points:
                analysis["common_mistakes"].append({
                    "type": "grammar",
                    "category": point.get("category", "general"),
                    "example": point.get("example", ""),
                    "explanation": point.get("explanation", "")
                })

            # Extract vocabulary suggestions
            vocab_suggestions = insights.get("vocabulary_to_learn", [])
            for vocab in vocab_suggestions:
                analysis["weak_vocabulary"].append({
                    "word": vocab.get("word", ""),
                    "context": vocab.get("context", ""),
                    "definition": vocab.get("definition", "")
                })

            # Session summary for context
            summary = session.get("summary", "")
            if summary:
                analysis["session_summaries"].append(summary)

        # Get weak flashcards
        flashcards_collection = database.flashcards
        weak_cards = await flashcards_collection.find({
            "user_id": user_id,
            "language": language,
            "mastery_level": {"$lt": 0.5},
            "is_active": True
        }).limit(10).to_list(length=10)

        for card in weak_cards:
            analysis["weak_vocabulary"].append({
                "word": card.get("front", ""),
                "context": card.get("category", ""),
                "definition": card.get("back", "")
            })

        # Get challenge completion statistics
        challenge_pool_collection = database.challenge_pool
        completed_challenges = await challenge_pool_collection.find({
            "user_id": user_id,
            "language": language,
            "status": "completed"
        }).limit(50).to_list(length=50)

        # Calculate stats per challenge type
        type_stats = {}
        for challenge in completed_challenges:
            ctype = challenge.get("challenge_type", "unknown")
            if ctype not in type_stats:
                type_stats[ctype] = {"total": 0, "correct": 0}

            type_stats[ctype]["total"] += 1
            # If challenge has score/result tracking
            if challenge.get("result") == "correct":
                type_stats[ctype]["correct"] += 1

        analysis["challenge_stats"] = type_stats

        # Get learning plan focus areas
        learning_plans_collection = database.learning_plans
        learning_plan = await learning_plans_collection.find_one({
            "user_id": user_id,
            "language": language
        }, sort=[("updated_at", -1)])

        if learning_plan:
            plan_content = learning_plan.get("plan_content", {})
            weekly_schedule = plan_content.get("weekly_schedule", [])

            # Get last 3 weeks of topics
            for week in weekly_schedule[-3:]:
                focus = week.get("focus", "")
                if focus:
                    analysis["learning_plan_topics"].append(focus)

        # Deduplicate and limit
        analysis["common_mistakes"] = analysis["common_mistakes"][:10]
        analysis["weak_vocabulary"] = analysis["weak_vocabulary"][:10]
        analysis["learning_plan_topics"] = list(set(analysis["learning_plan_topics"]))[:5]

        print(f"[CREWAI_ANALYZER] 📊 Analysis complete for user {user_id}")
        print(f"  - Mistakes: {len(analysis['common_mistakes'])}")
        print(f"  - Weak vocab: {len(analysis['weak_vocabulary'])}")
        print(f"  - Learning topics: {len(analysis['learning_plan_topics'])}")
        print(f"  - Recent sessions: {len(analysis['session_summaries'])}")

        return analysis

    except Exception as e:
        print(f"[CREWAI_ANALYZER] ❌ Error analyzing user data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return analysis


# ============================================================================
# CHALLENGE GENERATION WITH CREWAI
# ============================================================================

async def generate_challenges_with_ai(
    user_id: str,
    user_level: str,
    language: str = "english",
    challenge_type: Optional[str] = None,
    count: int = 6
) -> List[Dict[str, Any]]:
    """
    Use CrewAI agents to generate personalized challenges based on user's learning data

    This is a drop-in replacement for the original generate_challenges_with_ai function.

    Args:
        user_id: User ID
        user_level: CEFR level (A1-C2)
        language: Target language (default: "english")
        challenge_type: Optional specific challenge type to generate
        count: Number of challenges to generate (default: 6)

    Returns:
        List of AI-generated challenges
    """
    try:
        print(f"\n[CREWAI] 🤖 Starting intelligent challenge generation")
        print(f"[CREWAI] User: {user_id}, Language: {language}, Level: {user_level}")
        if challenge_type:
            print(f"[CREWAI] Type: {challenge_type}, Count: {count}")
        else:
            print(f"[CREWAI] Generating {count} challenges of all types")

        # Step 1: Analyze user's learning data
        print(f"[CREWAI] Step 1/3: Analyzing user learning patterns...")
        user_analysis = await analyze_user_learning_data(user_id, language)
        user_analysis["level"] = user_level
        user_analysis["language"] = language

        # Step 2: Create CrewAI agents
        print(f"[CREWAI] Step 2/3: Creating 3 specialized agents...")
        analyzer_agent = create_learning_analyzer_agent()
        generator_agent = create_challenge_generator_agent()
        curator_agent = create_quality_curator_agent()

        # Step 3: Define tasks for agents
        print(f"[CREWAI] Step 3/3: Running agent crew...")

        # Task 1: Learning Analysis
        analysis_task = Task(
            description=f"""Analyze this user's learning patterns and recommend
            what types of challenges would be most beneficial:

            User Analysis Data:
            - Language: {language}
            - CEFR Level: {user_level}
            - Common Mistakes: {json.dumps(user_analysis['common_mistakes'][:3], indent=2)}
            - Weak Vocabulary: {json.dumps(user_analysis['weak_vocabulary'][:3], indent=2)}
            - Learning Topics: {json.dumps(user_analysis['learning_plan_topics'], indent=2)}
            - Challenge Stats: {json.dumps(user_analysis['challenge_stats'], indent=2)}

            Provide specific recommendations for challenge topics, difficulty nuances,
            and areas to focus on. {"Focus on " + challenge_type + " challenges." if challenge_type else ""}""",
            agent=analyzer_agent,
            expected_output="Detailed recommendations for challenge topics and focus areas"
        )

        # Task 2: Challenge Generation
        challenge_types_list = [challenge_type] if challenge_type else [
            "error_spotting", "swipe_fix", "micro_quiz",
            "smart_flashcard", "native_check", "brain_tickler"
        ]

        generation_task = Task(
            description=f"""Based on the learning analysis recommendations, generate
            {count} high-quality challenges in {language} for CEFR level {user_level}.

            Challenge types to generate: {', '.join(challenge_types_list)}

            Each challenge must be:
            1. In {language} (native content, not translations)
            2. Appropriate for {user_level} level
            3. Contextual to the user's weak areas and learning topics
            4. Include proper explanations and corrections
            5. Follow standard challenge format with id, type, title, description, etc.

            IMPORTANT: Return ONLY a valid JSON array of challenge objects, no markdown, no extra text.

            Example format:
            [
              {{
                "id": "unique_id_1",
                "type": "brain_tickler",
                "title": "10-Second Challenge",
                "emoji": "⏱️",
                "description": "Beat the clock!",
                "cefrLevel": "{user_level}",
                "estimatedSeconds": 10,
                "timeLimit": 10,
                "question": "Quick question on a weak area",
                "options": [
                  {{"id": "opt1", "text": "option 1", "isCorrect": false}},
                  {{"id": "opt2", "text": "option 2", "isCorrect": true}},
                  {{"id": "opt3", "text": "option 3", "isCorrect": false}}
                ],
                "explanation": "Brief explanation",
                "tags": ["speed", "recall"],
                "completed": false
              }}
            ]

            Return as a JSON array of {count} challenge objects.""",
            agent=generator_agent,
            expected_output=f"JSON array of {count} challenge objects",
            context=[analysis_task]
        )

        # Task 3: Quality Curation
        curation_task = Task(
            description=f"""Review the generated challenges and ensure:

            1. All content is grammatically correct in {language}
            2. Difficulty matches {user_level} level
            3. Explanations are clear and educational
            4. Cultural appropriateness
            5. Format consistency and completeness
            6. All required fields are present

            Fix any issues and return the final curated JSON array.

            CRITICAL: Return ONLY the JSON array, no markdown code blocks, no extra text.""",
            agent=curator_agent,
            expected_output="Curated JSON array of challenges ready for use",
            context=[generation_task]
        )

        # Step 4: Create and run crew
        crew = Crew(
            agents=[analyzer_agent, generator_agent, curator_agent],
            tasks=[analysis_task, generation_task, curation_task],
            process=Process.sequential,
            verbose=True
        )

        print(f"[CREWAI] 🚀 Running crew (this may take 30-60 seconds)...")
        result = crew.kickoff()

        # Step 5: Parse result
        print(f"[CREWAI] 📊 Parsing crew results...")

        try:
            # Extract JSON from result
            result_str = str(result)

            # Remove markdown code blocks if present
            if "```json" in result_str:
                json_start = result_str.find("```json") + 7
                json_end = result_str.find("```", json_start)
                result_str = result_str[json_start:json_end].strip()
            elif "```" in result_str:
                json_start = result_str.find("```") + 3
                json_end = result_str.find("```", json_start)
                result_str = result_str[json_start:json_end].strip()

            # Find JSON array
            if "[" in result_str:
                json_start = result_str.find("[")
                json_end = result_str.rfind("]") + 1
                result_str = result_str[json_start:json_end]

            challenges_data = json.loads(result_str)

            if not isinstance(challenges_data, list):
                raise ValueError("Result is not a JSON array")

            print(f"[CREWAI] ✅ Successfully parsed {len(challenges_data)} challenges")

        except (json.JSONDecodeError, ValueError) as e:
            print(f"[CREWAI] ❌ Failed to parse crew result as JSON: {str(e)}")
            print(f"[CREWAI] Raw result preview: {str(result)[:500]}")
            return []

        # Step 6: Add metadata and ensure unique IDs
        challenges = []
        for challenge_data in challenges_data[:count]:
            # Generate globally unique ID
            original_id = challenge_data.get("id", "challenge")
            unique_id = f"{original_id}_{uuid.uuid4().hex[:8]}"
            challenge_data["id"] = unique_id

            # Add metadata
            challenge_data["language"] = language
            challenge_data["generated_at"] = datetime.utcnow().isoformat()
            challenge_data["source"] = "crewai_generated"

            challenges.append(challenge_data)

        print(f"[CREWAI] ✅ Generated {len(challenges)} challenges successfully")
        return challenges

    except Exception as e:
        print(f"[CREWAI] ❌ Error generating challenges: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []


# ============================================================================
# CACHE MANAGEMENT (Same as original)
# ============================================================================

async def get_or_generate_daily_challenges(
    user_id: str,
    user_level: str,
    language: str = "english"
) -> List[Dict[str, Any]]:
    """
    Main function: Get cached challenges or generate new ones with CrewAI

    - Checks 24h cache first
    - If no cache, generates new challenges with CrewAI
    - Caches for 24 hours

    Args:
        user_id: User ID
        user_level: CEFR level
        language: Target language (default: "english")

    Returns:
        List of challenges (cached or freshly generated)
    """
    try:
        # Check cache first
        cache_collection = database.daily_challenges_cache
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())

        cached = await cache_collection.find_one({
            "user_id": user_id,
            "language": language,
            "date": today_start
        })

        if cached:
            print(f"[CREWAI] ✅ Found cached challenges for today")
            return cached.get("challenges", [])

        # No cache - generate new challenges with CrewAI
        print(f"[CREWAI] 🆕 Generating new daily challenges with CrewAI...")

        challenges = await generate_challenges_with_ai(user_id, user_level, language, count=6)

        if not challenges or len(challenges) == 0:
            print(f"[CREWAI] ⚠️ AI generation failed, returning empty")
            return []

        # Cache for 24 hours
        cache_doc = {
            "user_id": user_id,
            "language": language,
            "date": today_start,
            "challenges": challenges,
            "created_at": datetime.utcnow(),
            "generation_method": "crewai",
            "level": user_level
        }

        # Create TTL index if not exists
        await cache_collection.create_index("created_at", expireAfterSeconds=24*60*60)

        # Insert cache
        await cache_collection.insert_one(cache_doc)

        print(f"[CREWAI] ✅ Cached {len(challenges)} challenges for 24h")

        return challenges

    except Exception as e:
        print(f"[CREWAI] ❌ Error in get_or_generate_daily_challenges: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []
