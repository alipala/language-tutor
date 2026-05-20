import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables - prioritize .env.local for development
import os
if os.path.exists('.env.local'):
    load_dotenv('.env.local')
    print("Loaded .env.local for local development")
else:
    load_dotenv()
    print("Loaded .env for production")

# Debug Railway environment
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY") == "true":
    print("Detected Railway environment")
    # Print all environment variables with MONGO in them (masking passwords)
    mongo_env_vars = {k: ("***" if "PASSWORD" in k or "password" in k else v) 
                     for k, v in os.environ.items() 
                     if "MONGO" in k.upper()}
    print(f"Available MongoDB environment variables: {mongo_env_vars}")

# Get MongoDB connection string from environment variables
# Check for Railway-specific MongoDB environment variables first
MONGODB_URL = None

# Check for MongoDB URL in various environment variable formats
for var_name in ["MONGODB_URL", "MONGO_URL", "MONGO_PUBLIC_URL"]:
    if os.getenv(var_name):
        MONGODB_URL = os.getenv(var_name)
        print(f"Using MongoDB URL from {var_name}")
        break

# If we're in Railway but no MongoDB URL is found, try to construct it from individual variables
if not MONGODB_URL and (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY") == "true"):
    mongo_host = os.getenv("MONGOHOST")
    mongo_port = os.getenv("MONGOPORT")
    mongo_user = os.getenv("MONGOUSER")
    mongo_password = os.getenv("MONGOPASSWORD")
    
    if mongo_host and mongo_user and mongo_password:
        # Construct MongoDB URL with authentication
        port_str = f":{mongo_port}" if mongo_port else ""
        MONGODB_URL = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}{port_str}"
        print(f"Constructed MongoDB URL for Railway: mongodb://{mongo_user}:***@{mongo_host}{port_str}")

# Fall back to localhost if no MongoDB URL is found
if not MONGODB_URL:
    MONGODB_URL = "mongodb://localhost:27017"
    print("Warning: Using localhost MongoDB. This won't work in Railway unless properly configured.")

DATABASE_NAME = os.getenv("DATABASE_NAME") or os.getenv("MONGO_DATABASE") or "language_tutor"

print(f"Connecting to MongoDB at: {MONGODB_URL.replace(MONGODB_URL.split('@')[0] if '@' in MONGODB_URL else MONGODB_URL, 'mongodb://***:***')}")
print(f"Using database: {DATABASE_NAME}")

# Create a MongoDB client with optimized connection pool for Railway
try:
    client = AsyncIOMotorClient(
        MONGODB_URL,

        # Connection pool optimization
        # 50 per worker: 8 workers × 50 = 400 total, well within MongoDB capacity
        maxPoolSize=50,            # Max connections per worker (was 100 pre-Phase F)
        minPoolSize=5,             # Keep 5 connections warm per worker
        maxIdleTimeMS=45000,       # Close idle connections after 45 seconds
        waitQueueTimeoutMS=5000,   # Fail fast (5s) if pool is exhausted

        # Timeout optimization
        serverSelectionTimeoutMS=30000,  # 30s timeout for server selection
        connectTimeoutMS=10000,    # 10s timeout for initial connection
        socketTimeoutMS=45000,     # 45s timeout for socket operations

        # Retry optimization
        retryWrites=True,          # Retry failed writes once
        retryReads=True,           # Retry failed reads once
    )
    database = client[DATABASE_NAME]
    print("MongoDB client initialized successfully with optimized connection pool")
    print(f"Connection pool: maxPoolSize=50, minPoolSize=5, maxIdleTime=45s")
    
    # Collections - initialize only if database connection was successful
    users_collection = database.users
    sessions_collection = database.sessions
    password_reset_collection = database.password_resets
    email_verification_collection = database.email_verifications
    conversation_sessions_collection = database.conversation_sessions
    learning_plans_collection = database.learning_plans
    notifications_collection = database.notifications
    user_notifications_collection = database.user_notifications
    notification_preferences_collection = database.notification_preferences
    tutors_collection = database.tutors
    institutions_collection = database.institutions
    usage_logs_collection = database.realtime_usage_logs
    reference_challenges_collection = database.reference_challenges
    challenge_pool_collection = database.challenge_pool
    user_achievements_collection = database.user_achievements
    challenge_sessions_collection = database.challenge_sessions

    # NEW: Gamification & Statistics collections
    daily_stats_collection = database.daily_stats
    recent_performance_collection = database.recent_performance

    # NEWS FEATURE: Daily news collections
    news_batches_collection = database.news_batches
    news_articles_collection = database.news_articles

    # SPEAKING DNA FEATURE: DNA profile collections
    speaking_dna_profiles_collection = database.speaking_dna_profiles
    speaking_dna_history_collection = database.speaking_dna_history
    speaking_breakthroughs_collection = database.speaking_breakthroughs
    
    # ADDITIONAL COLLECTIONS FOR TAALCOACH
    heart_events_collection = database.heart_events
    flashcard_sets_collection = database.flashcard_sets
    speaking_time_tracking_collection = database.speaking_time_tracking
    rescue_events_collection = database.rescue_events
    sharing_activity_collection = database.sharing_activity

    # SENTENCE ANALYSIS JOBS: Background processing for sentence analysis
    sentence_analysis_jobs_collection = database.sentence_analysis_jobs

    # SESSION FEEDBACK: User feedback for conversations and challenges
    session_feedback_collection = database.session_feedback

    # HIGH PRIORITY COLLECTIONS FOR COMPREHENSIVE TAALCOACH DATA COVERAGE
    assessments_collection = database.assessments
    session_completions_collection = database.session_completions
    sentence_analysis_feedback_collection = database.sentence_analysis_feedback
    story_contributions_collection = database.story_contributions
    user_story_achievements_collection = database.user_story_achievements
    learning_goals_collection = database.learning_goals
    flashcards_collection = database.flashcards

    # LEARNING JOURNEY ORCHESTRATOR: Intelligent journey guidance collections
    recommended_actions_collection = database.recommended_actions
    journey_checkpoints_collection = database.journey_checkpoints
    daily_digest_messages_collection = database.daily_digest_messages
except Exception as e:
    print(f"Error initializing MongoDB client: {str(e)}")
    # Don't crash the app immediately, let the startup event handle connection issues
    client = None
    database = None
    users_collection = None
    sessions_collection = None
    password_reset_collection = None
    email_verification_collection = None
    conversation_sessions_collection = None
    notification_preferences_collection = None
    reference_challenges_collection = None
    challenge_pool_collection = None
    user_achievements_collection = None
    challenge_sessions_collection = None
    daily_stats_collection = None
    recent_performance_collection = None
    news_batches_collection = None
    news_articles_collection = None
    speaking_dna_profiles_collection = None
    speaking_dna_history_collection = None
    speaking_breakthroughs_collection = None
    heart_events_collection = None
    flashcard_sets_collection = None
    speaking_time_tracking_collection = None
    rescue_events_collection = None
    sharing_activity_collection = None
    sentence_analysis_jobs_collection = None
    session_feedback_collection = None
    assessments_collection = None
    session_completions_collection = None
    sentence_analysis_feedback_collection = None
    story_contributions_collection = None
    user_story_achievements_collection = None
    learning_goals_collection = None
    flashcards_collection = None
    recommended_actions_collection = None
    journey_checkpoints_collection = None
    daily_digest_messages_collection = None

# Initialize TTL index for sessions (expire after 7 days)
async def init_db():
    # Check if database connection is available
    if database is None or client is None:
        print("WARNING: Cannot initialize database indexes - no database connection")
        return
    
    try:
        # Test the connection by pinging the server
        await client.admin.command('ping')
        print("MongoDB connection verified with ping")
        
        # Check if collections are available
        if (users_collection is None or 
            sessions_collection is None or 
            password_reset_collection is None or
            email_verification_collection is None):
            print("WARNING: Cannot initialize database indexes - collections not available")
            return
            
        # Create TTL index for sessions if it doesn't exist
        await sessions_collection.create_index("created_at", expireAfterSeconds=7 * 24 * 60 * 60)
        
        # Create TTL index for password reset tokens (expire after 1 hour)
        await password_reset_collection.create_index("created_at", expireAfterSeconds=60 * 60)
        
        # Create TTL index for email verification tokens (expire after 24 hours)
        await email_verification_collection.create_index("expires_at", expireAfterSeconds=0)
        
        # Create unique index for email in users collection
        await users_collection.create_index("email", unique=True)

        # Create composite index for user_notifications (for soft delete queries)
        await user_notifications_collection.create_index([
            ("user_id", 1),
            ("deleted_at", 1)
        ])

        # Create unique index for notification_preferences (one per user)
        await notification_preferences_collection.create_index("user_id", unique=True)

        # NEW: Create indexes for gamification & statistics collections
        # Challenge sessions indexes
        await challenge_sessions_collection.create_index([("user_id", 1), ("local_date", -1)])
        await challenge_sessions_collection.create_index([("user_id", 1), ("created_at", -1)])
        await challenge_sessions_collection.create_index([("user_id", 1), ("language", 1), ("level", 1), ("created_at", -1)])
        await challenge_sessions_collection.create_index([("user_id", 1), ("challenge_type", 1), ("created_at", -1)])

        # Daily stats indexes
        await daily_stats_collection.create_index([("user_id", 1), ("local_date", -1)], unique=True)
        await daily_stats_collection.create_index("local_date")

        # Recent performance indexes (with TTL)
        await recent_performance_collection.create_index([("user_id", 1), ("expires_at", 1)])
        await recent_performance_collection.create_index("expires_at", expireAfterSeconds=0)  # TTL index

        # NEWS FEATURE: Create indexes for news collections
        # News batches: unique date index
        await news_batches_collection.create_index("date", unique=True)

        # News articles: date-based queries and TTL (expire after 2 days)
        await news_articles_collection.create_index([("date", -1), ("batch_id", 1)])
        await news_articles_collection.create_index("expires_at", expireAfterSeconds=0)  # TTL index
        await news_articles_collection.create_index("original.category")

        # SPEAKING DNA FEATURE: Create indexes for DNA collections
        # DNA profiles: unique user-language pair, query by user_id and language
        await speaking_dna_profiles_collection.create_index(
            [("user_id", 1), ("language", 1)],
            unique=True
        )
        await speaking_dna_profiles_collection.create_index("updated_at")

        # DNA history: query by user-language pair and week, sorted by date
        await speaking_dna_history_collection.create_index(
            [("user_id", 1), ("language", 1), ("week_start", -1)]
        )

        # DNA breakthroughs: query by user-language pair, filter by celebrated status
        await speaking_breakthroughs_collection.create_index(
            [("user_id", 1), ("language", 1), ("created_at", -1)]
        )
        await speaking_breakthroughs_collection.create_index(
            [("user_id", 1), ("celebrated", 1)]
        )

        # SENTENCE ANALYSIS JOBS: Background processing indexes
        await sentence_analysis_jobs_collection.create_index("job_id", unique=True)
        await sentence_analysis_jobs_collection.create_index([("user_id", 1), ("created_at", -1)])
        await sentence_analysis_jobs_collection.create_index([("status", 1), ("created_at", -1)])
        # TTL index: Delete jobs older than 7 days to keep collection clean
        await sentence_analysis_jobs_collection.create_index("created_at", expireAfterSeconds=7 * 24 * 60 * 60)

        # SESSION FEEDBACK: User feedback indexes
        await session_feedback_collection.create_index([("user_id", 1), ("created_at", -1)])
        await session_feedback_collection.create_index([("session_type", 1), ("feedback_type", 1)])
        await session_feedback_collection.create_index("created_at")
        await session_feedback_collection.create_index("is_guest")
        await session_feedback_collection.create_index("session_id", unique=True)

        # LEARNING JOURNEY ORCHESTRATOR: Recommendation and checkpoint indexes
        # Recommended actions: Query by user + status, with TTL for expired recommendations
        await recommended_actions_collection.create_index([("user_id", 1), ("completed", 1), ("dismissed", 1), ("expires_at", -1)])
        await recommended_actions_collection.create_index([("user_id", 1), ("priority", 1), ("recommended_at", -1)])
        await recommended_actions_collection.create_index("expires_at", expireAfterSeconds=0)  # TTL index

        # Journey checkpoints: Query by user + type, chronological order
        await journey_checkpoints_collection.create_index([("user_id", 1), ("timestamp", -1)])
        await journey_checkpoints_collection.create_index([("user_id", 1), ("checkpoint_type", 1), ("timestamp", -1)])
        await journey_checkpoints_collection.create_index([("user_id", 1), ("celebrated", 1), ("notified", 1)])

        # Daily digest messages: Query by user + scheduled time, delivery tracking
        await daily_digest_messages_collection.create_index([("user_id", 1), ("scheduled_for", -1)])
        await daily_digest_messages_collection.create_index([("user_id", 1), ("sent", 1), ("scheduled_for", -1)])
        await daily_digest_messages_collection.create_index("scheduled_for")  # For batch sending jobs
        # TTL index: Delete old digest messages after 30 days
        await daily_digest_messages_collection.create_index("generated_at", expireAfterSeconds=30 * 24 * 60 * 60)

        # Daily missions: unique per user+date+language, TTL after 3 days
        # Drop the old (user_id, local_date) unique index if it exists — it was
        # replaced by the compound (user_id, local_date, language) index to support
        # per-language mission sets when users switch languages.
        daily_missions_collection = database.daily_missions
        try:
            await daily_missions_collection.drop_index("user_id_1_local_date_1")
        except Exception:
            pass  # index didn't exist — that's fine
        await daily_missions_collection.create_index(
            [("user_id", 1), ("local_date", 1), ("language", 1)], unique=True
        )
        await daily_missions_collection.create_index(
            "expires_at", expireAfterSeconds=0
        )

        # ── PHASE E: Capacity scaling indexes ────────────────────────────────
        # conversation_sessions: user dashboard + per-language filtering
        await conversation_sessions_collection.create_index(
            [("user_id", 1), ("created_at", -1)], background=True
        )
        await conversation_sessions_collection.create_index(
            [("user_id", 1), ("language", 1), ("created_at", -1)], background=True
        )

        # flashcards: set membership + due-date queries
        await flashcard_sets_collection.create_index(
            [("user_id", 1)], background=True
        )
        await flashcards_collection.create_index(
            [("user_id", 1), ("set_id", 1)], background=True
        )
        await flashcards_collection.create_index(
            [("user_id", 1), ("due_date", 1)], background=True
        )

        # learning_plans: user plan list (already exists but ensure it's there)
        await learning_plans_collection.create_index(
            [("user_id", 1), ("created_at", -1)], background=True
        )

        # realtime_usage_logs: user query + 90-day TTL auto-purge
        await usage_logs_collection.create_index(
            [("user_id", 1), ("created_at", -1)], background=True
        )
        await usage_logs_collection.create_index(
            "created_at", expireAfterSeconds=90 * 24 * 60 * 60, background=True
        )
        # ── END PHASE E ───────────────────────────────────────────────────────

        print("Database indexes initialized successfully")
    except Exception as e:
        print(f"ERROR initializing database indexes: {str(e)}")
        print("The application may not function correctly without database access")

# Dependency injection function for FastAPI
async def get_database():
    """Get MongoDB database connection for FastAPI dependency injection"""
    if database is None:
        raise Exception("Database not initialized")
    return database
