"""
CrewAI Multi-Agent Challenge Generation System
==============================================

This module implements a multi-agent system using CrewAI for intelligent
language learning challenge generation. It analyzes user learning patterns,
generates personalized challenges, and curates high-quality outputs.

Architecture:
- Learning Analyzer Agent: Analyzes user progress and learning patterns
- Challenge Generator Agent: Creates contextual, personalized challenges
- Quality Curator Agent: Reviews and ensures challenge quality

Environment Variables:
- GPT_MODEL: LLM model to use (default: gpt-4o)
- LLM_PROVIDER: LLM provider (default: openai)
- OPENAI_API_KEY: OpenAI API key (required)
- MONGODB_URL: MongoDB connection string (required)
- LOG_LEVEL: Logging level (default: INFO)
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from crewai import Agent, Task, Crew, Process
from openai import OpenAI

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load environment variables
load_dotenv()

# LLM Configuration (configurable via environment)
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = "language_tutor"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'crewai_challenges_{datetime.utcnow().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Challenge Configuration
CHALLENGE_TYPES = [
    "error_spotting",
    "swipe_fix",
    "micro_quiz",
    "smart_flashcard",
    "native_check",
    "brain_tickler"
]

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

TARGET_POOL_SIZE = 50  # Target number of challenges per type per user

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class UsageStatistics:
    """Track API usage and costs for the CrewAI system"""
    total_api_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    execution_time_seconds: float = 0.0
    challenges_generated: int = 0
    by_language: Dict[str, Dict] = None
    by_user: Dict[str, Dict] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.by_language is None:
            self.by_language = {}
        if self.by_user is None:
            self.by_user = {}
        if self.errors is None:
            self.errors = []

    def add_api_call(self, input_tokens: int, output_tokens: int, cost: float):
        """Record an API call"""
        self.total_api_calls += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_usd += cost

    def add_challenges(self, language: str, user_id: str, count: int):
        """Record generated challenges"""
        self.challenges_generated += count

        # Track by language
        if language not in self.by_language:
            self.by_language[language] = {"count": 0, "users": []}
        self.by_language[language]["count"] += count
        if user_id not in self.by_language[language]["users"]:
            self.by_language[language]["users"].append(user_id)

        # Track by user
        if user_id not in self.by_user:
            self.by_user[user_id] = {"count": 0, "languages": []}
        self.by_user[user_id]["count"] += count
        if language not in self.by_user[user_id]["languages"]:
            self.by_user[user_id]["languages"].append(language)

    def add_error(self, error_msg: str):
        """Record an error"""
        self.errors.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": error_msg
        })

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    def save_report(self, filepath: str):
        """Save usage report to file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"[STATS] Usage report saved to {filepath}")


# ============================================================================
# CREWAI AGENT DEFINITIONS
# ============================================================================

class ChallengeCrew:
    """CrewAI-powered challenge generation system"""

    def __init__(self, client: AsyncIOMotorClient, stats: UsageStatistics):
        """Initialize the CrewAI system

        Args:
            client: MongoDB client
            stats: Usage statistics tracker
        """
        self.client = client
        self.db = client[DATABASE_NAME]
        self.stats = stats
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)

        logger.info(f"[CREWAI] Initialized with model: {GPT_MODEL}, provider: {LLM_PROVIDER}")

    def _create_learning_analyzer_agent(self) -> Agent:
        """Create the Learning Analyzer agent

        This agent analyzes user learning patterns, conversation history,
        and challenge performance to identify learning gaps and needs.
        """
        return Agent(
            role='Learning Pattern Analyzer',
            goal='Analyze user learning patterns and identify personalized challenge needs',
            backstory="""You are an expert language learning analyst with deep understanding
            of CEFR levels and pedagogical best practices. You analyze conversation sessions,
            challenge completion rates, and learning patterns to identify what types of
            challenges will be most beneficial for each user. You consider their current
            level, recent topics discussed, grammar patterns encountered, and areas where
            they struggle.""",
            verbose=True,
            allow_delegation=False,
            llm=GPT_MODEL
        )

    def _create_challenge_generator_agent(self) -> Agent:
        """Create the Challenge Generator agent

        This agent generates contextual, personalized challenges based on
        the analyzer's insights and reference challenge patterns.
        """
        return Agent(
            role='Challenge Content Generator',
            goal='Generate high-quality, personalized language learning challenges',
            backstory="""You are a creative language teacher and content creator who excels
            at crafting engaging, educational challenges. You use insights from learning
            analysis to create challenges that are perfectly tailored to each user's level,
            interests, and learning gaps. You ensure challenges are culturally appropriate,
            grammatically correct, and pedagogically sound. You create diverse challenge
            types including error spotting, sentence fixes, quizzes, flashcards, and more.""",
            verbose=True,
            allow_delegation=False,
            llm=GPT_MODEL
        )

    def _create_quality_curator_agent(self) -> Agent:
        """Create the Quality Curator agent

        This agent reviews generated challenges for quality, correctness,
        and appropriateness before they are saved to the database.
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

    async def analyze_user_learning_patterns(
        self,
        user_id: str,
        language: str,
        cefr_level: str
    ) -> Dict[str, Any]:
        """Analyze user's learning patterns and conversation history

        Args:
            user_id: User's ObjectId as string
            language: Target language code
            cefr_level: User's CEFR level

        Returns:
            Dictionary with learning pattern analysis
        """
        logger.info(f"[ANALYZER] Analyzing learning patterns for user {user_id}, language: {language}, level: {cefr_level}")

        try:
            # Get recent conversation sessions (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)

            sessions = await self.db.conversation_sessions.find({
                "user_id": user_id,
                "language": language,
                "created_at": {"$gte": thirty_days_ago}
            }).sort("created_at", -1).limit(20).to_list(length=20)

            # Get challenge completion statistics
            challenge_stats = await self.db.challenge_pool.aggregate([
                {
                    "$match": {
                        "user_id": user_id,
                        "language": language,
                        "completed": True
                    }
                },
                {
                    "$group": {
                        "_id": "$challenge_type",
                        "total": {"$sum": 1},
                        "avg_score": {"$avg": "$score"}
                    }
                }
            ]).to_list(length=100)

            # Build analysis context
            analysis = {
                "user_id": user_id,
                "language": language,
                "cefr_level": cefr_level,
                "total_sessions": len(sessions),
                "recent_topics": [],
                "challenge_stats": {stat["_id"]: stat for stat in challenge_stats},
                "weak_areas": [],
                "strong_areas": []
            }

            # Extract topics from recent sessions
            for session in sessions[:5]:  # Last 5 sessions
                if "messages" in session:
                    # Extract key phrases/topics from messages
                    for msg in session["messages"][-3:]:  # Last 3 messages per session
                        if msg.get("role") == "user" and len(msg.get("content", "")) > 20:
                            analysis["recent_topics"].append(msg["content"][:100])

            # Identify weak/strong areas based on challenge performance
            for stat in challenge_stats:
                challenge_type = stat["_id"]
                avg_score = stat.get("avg_score", 0)

                if avg_score < 0.6:  # Less than 60% average
                    analysis["weak_areas"].append(challenge_type)
                elif avg_score > 0.85:  # More than 85% average
                    analysis["strong_areas"].append(challenge_type)

            logger.debug(f"[ANALYZER] Analysis complete: {len(sessions)} sessions, {len(challenge_stats)} challenge types")

            return analysis

        except Exception as e:
            error_msg = f"Error analyzing user patterns: {str(e)}"
            logger.error(f"[ANALYZER] {error_msg}")
            self.stats.add_error(error_msg)
            return {
                "user_id": user_id,
                "language": language,
                "cefr_level": cefr_level,
                "error": error_msg
            }

    async def get_reference_challenges(
        self,
        language: str,
        cefr_level: str,
        challenge_type: str,
        limit: int = 5
    ) -> List[Dict]:
        """Get reference challenges for inspiration

        Args:
            language: Target language code
            cefr_level: CEFR level
            challenge_type: Type of challenge
            limit: Number of reference challenges to retrieve

        Returns:
            List of reference challenges
        """
        try:
            references = await self.db.reference_challenges.find({
                "language": language,
                "cefr_level": cefr_level,
                "challenge_type": challenge_type
            }).limit(limit).to_list(length=limit)

            logger.debug(f"[REFERENCE] Retrieved {len(references)} reference challenges for {language}/{cefr_level}/{challenge_type}")

            return references

        except Exception as e:
            logger.error(f"[REFERENCE] Error retrieving references: {str(e)}")
            return []

    async def generate_challenges_for_user(
        self,
        user_id: str,
        language: str,
        cefr_level: str,
        challenge_type: str,
        count: int = 10
    ) -> List[Dict]:
        """Generate personalized challenges for a user using CrewAI agents

        Args:
            user_id: User's ObjectId as string
            language: Target language code
            cefr_level: User's CEFR level
            challenge_type: Type of challenge to generate
            count: Number of challenges to generate

        Returns:
            List of generated challenge documents
        """
        start_time = datetime.utcnow()
        logger.info(f"[CREWAI] Starting challenge generation for user {user_id}")
        logger.info(f"[CREWAI] Language: {language}, Level: {cefr_level}, Type: {challenge_type}, Count: {count}")

        try:
            # Step 1: Analyze learning patterns
            learning_analysis = await self.analyze_user_learning_patterns(
                user_id, language, cefr_level
            )

            # Step 2: Get reference challenges
            references = await self.get_reference_challenges(
                language, cefr_level, challenge_type, limit=3
            )

            # Step 3: Create CrewAI agents
            analyzer = self._create_learning_analyzer_agent()
            generator = self._create_challenge_generator_agent()
            curator = self._create_quality_curator_agent()

            # Step 4: Create tasks for agents
            analysis_task = Task(
                description=f"""Analyze this user's learning patterns and recommend
                what types of {challenge_type} challenges would be most beneficial:

                User Analysis: {json.dumps(learning_analysis, indent=2)}

                Provide specific recommendations for challenge topics, difficulty nuances,
                and areas to focus on.""",
                agent=analyzer,
                expected_output="Detailed recommendations for challenge topics and focus areas"
            )

            generation_task = Task(
                description=f"""Based on the learning analysis recommendations, generate
                {count} high-quality {challenge_type} challenges in {language} for CEFR level {cefr_level}.

                Use these reference challenges as inspiration for format and structure:
                {json.dumps(references[:2], indent=2, default=str)}

                Each challenge must be:
                1. In {language} (native content, not translations)
                2. Appropriate for {cefr_level} level
                3. Contextual to the user's recent learning topics
                4. Following the {challenge_type} format
                5. Include proper explanations and corrections

                Return as a JSON array of challenge objects.""",
                agent=generator,
                expected_output=f"JSON array of {count} challenge objects",
                context=[analysis_task]
            )

            curation_task = Task(
                description=f"""Review the generated {challenge_type} challenges and ensure:

                1. All content is grammatically correct in {language}
                2. Difficulty matches {cefr_level} level
                3. Explanations are clear and educational
                4. Cultural appropriateness
                5. Format consistency

                Fix any issues and return the final curated JSON array.""",
                agent=curator,
                expected_output="Curated JSON array of challenges ready for database insertion",
                context=[generation_task]
            )

            # Step 5: Create and run crew
            logger.info(f"[CREWAI] Creating crew with 3 agents...")
            crew = Crew(
                agents=[analyzer, generator, curator],
                tasks=[analysis_task, generation_task, curation_task],
                process=Process.sequential,
                verbose=True
            )

            logger.info(f"[CREWAI] Running crew...")
            result = crew.kickoff()

            # Step 6: Parse result and create challenge documents
            logger.info(f"[CREWAI] Crew completed. Parsing results...")

            # The result from curator should be a JSON string
            try:
                # Extract JSON from result (may contain markdown formatting)
                result_str = str(result)
                if "```json" in result_str:
                    # Extract JSON from markdown code block
                    json_start = result_str.find("```json") + 7
                    json_end = result_str.find("```", json_start)
                    result_str = result_str[json_start:json_end].strip()
                elif "```" in result_str:
                    # Extract from generic code block
                    json_start = result_str.find("```") + 3
                    json_end = result_str.find("```", json_start)
                    result_str = result_str[json_start:json_end].strip()

                challenges_data = json.loads(result_str)

                if not isinstance(challenges_data, list):
                    raise ValueError("Result is not a JSON array")

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"[CREWAI] Failed to parse crew result as JSON: {str(e)}")
                logger.debug(f"[CREWAI] Raw result: {result}")
                self.stats.add_error(f"JSON parse error for {language}/{cefr_level}/{challenge_type}: {str(e)}")
                return []

            # Step 7: Build database documents
            challenges = []
            for challenge_data in challenges_data[:count]:  # Ensure we don't exceed requested count
                challenge_doc = {
                    "user_id": user_id,
                    "language": language,
                    "cefr_level": cefr_level,
                    "challenge_type": challenge_type,
                    "challenge_data": challenge_data,
                    "completed": False,
                    "score": None,
                    "created_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(days=30)
                }
                challenges.append(challenge_doc)

            # Step 8: Track statistics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self.stats.execution_time_seconds += execution_time

            # Estimate API costs (CrewAI makes multiple calls per agent)
            # Rough estimate: 3 agents × 2 calls each = 6 calls
            # Average tokens per call: ~1500 input, ~500 output
            estimated_api_calls = 6
            estimated_input_tokens = 1500 * estimated_api_calls
            estimated_output_tokens = 500 * estimated_api_calls

            # GPT-4o pricing: $2.50/1M input, $10/1M output
            estimated_cost = (estimated_input_tokens / 1_000_000 * 2.50) + \
                           (estimated_output_tokens / 1_000_000 * 10.00)

            self.stats.add_api_call(estimated_input_tokens, estimated_output_tokens, estimated_cost)
            self.stats.add_challenges(language, user_id, len(challenges))

            logger.info(f"[CREWAI] Generated {len(challenges)} challenges in {execution_time:.2f}s")
            logger.info(f"[CREWAI] Estimated cost: ${estimated_cost:.4f}")

            return challenges

        except Exception as e:
            error_msg = f"Error generating challenges for user {user_id}: {str(e)}"
            logger.error(f"[CREWAI] {error_msg}")
            self.stats.add_error(error_msg)
            return []

    async def replenish_user_challenges(self, user_id: str, language: str, cefr_level: str):
        """Replenish challenge pool for a user

        Args:
            user_id: User's ObjectId as string
            language: Target language code
            cefr_level: User's CEFR level
        """
        logger.info(f"[REPLENISH] Starting replenishment for user {user_id}, language: {language}")

        try:
            # Check current challenge counts per type
            for challenge_type in CHALLENGE_TYPES:
                # Count available (non-completed, non-expired) challenges
                available_count = await self.db.challenge_pool.count_documents({
                    "user_id": user_id,
                    "language": language,
                    "challenge_type": challenge_type,
                    "completed": False,
                    "expires_at": {"$gt": datetime.utcnow()}
                })

                needed = TARGET_POOL_SIZE - available_count

                if needed > 0:
                    logger.info(f"[REPLENISH] User {user_id} needs {needed} more {challenge_type} challenges")

                    # Generate challenges
                    new_challenges = await self.generate_challenges_for_user(
                        user_id, language, cefr_level, challenge_type, count=needed
                    )

                    # Insert into database
                    if new_challenges:
                        result = await self.db.challenge_pool.insert_many(new_challenges)
                        logger.info(f"[REPLENISH] Inserted {len(result.inserted_ids)} {challenge_type} challenges")
                else:
                    logger.info(f"[REPLENISH] User {user_id} has sufficient {challenge_type} challenges ({available_count}/{TARGET_POOL_SIZE})")

            logger.info(f"[REPLENISH] Completed replenishment for user {user_id}")

        except Exception as e:
            error_msg = f"Error replenishing challenges for user {user_id}: {str(e)}"
            logger.error(f"[REPLENISH] {error_msg}")
            self.stats.add_error(error_msg)


# ============================================================================
# MAIN WEEKLY CRON FUNCTION
# ============================================================================

async def run_weekly_challenge_generation():
    """Main entry point for weekly challenge generation cron job"""

    start_time = datetime.utcnow()
    logger.info("=" * 80)
    logger.info("🤖 CREWAI WEEKLY CHALLENGE GENERATION - START")
    logger.info("=" * 80)
    logger.info(f"Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info(f"LLM Model: {GPT_MODEL}")
    logger.info(f"LLM Provider: {LLM_PROVIDER}")
    logger.info("=" * 80)

    # Validate configuration
    if not OPENAI_API_KEY:
        logger.error("❌ OPENAI_API_KEY not set!")
        return

    if not MONGODB_URL:
        logger.error("❌ MONGODB_URL not set!")
        return

    # Initialize statistics
    stats = UsageStatistics()

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)

    try:
        # Test connection
        await client.admin.command('ping')
        logger.info("✅ Connected to MongoDB")

        db = client[DATABASE_NAME]

        # Initialize CrewAI system
        crew_system = ChallengeCrew(client, stats)

        # Get all active users with learning plans
        # Active = users who logged in or had sessions in last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        active_users = await db.users.find({
            "last_login": {"$gte": seven_days_ago}
        }).to_list(length=1000)

        logger.info(f"📊 Found {len(active_users)} active users")

        # Process each active user
        for user in active_users:
            user_id = str(user["_id"])

            # Get user's active learning plans
            learning_plans = await db.learning_plans.find({
                "user_id": user_id,
                "is_active": True
            }).to_list(length=10)

            logger.info(f"👤 Processing user {user_id}: {len(learning_plans)} active learning plan(s)")

            # Replenish challenges for each learning plan
            for plan in learning_plans:
                language = plan.get("language", "english")
                cefr_level = plan.get("level", "B1")

                logger.info(f"   📚 Learning plan: {language} - {cefr_level}")

                await crew_system.replenish_user_challenges(user_id, language, cefr_level)

        # Save usage statistics report
        end_time = datetime.utcnow()
        stats.execution_time_seconds = (end_time - start_time).total_seconds()

        report_filename = f"crewai_usage_report_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        stats.save_report(report_filename)

        # Log final summary
        logger.info("=" * 80)
        logger.info("✅ CREWAI WEEKLY CHALLENGE GENERATION - COMPLETE")
        logger.info("=" * 80)
        logger.info(f"⏱️  Total execution time: {stats.execution_time_seconds:.2f} seconds")
        logger.info(f"🤖 Total API calls: {stats.total_api_calls}")
        logger.info(f"🪙 Total input tokens: {stats.total_input_tokens:,}")
        logger.info(f"🪙 Total output tokens: {stats.total_output_tokens:,}")
        logger.info(f"💰 Total cost: ${stats.total_cost_usd:.4f}")
        logger.info(f"✨ Challenges generated: {stats.challenges_generated}")
        logger.info(f"🌍 Languages processed: {len(stats.by_language)}")
        logger.info(f"👥 Users processed: {len(stats.by_user)}")
        logger.info(f"❌ Errors: {len(stats.errors)}")
        logger.info(f"📄 Report saved: {report_filename}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        stats.add_error(f"Fatal error: {str(e)}")

    finally:
        client.close()
        logger.info("🔌 MongoDB connection closed")


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    logger.info("🚀 Starting CrewAI Challenge Generation System...")
    asyncio.run(run_weekly_challenge_generation())
