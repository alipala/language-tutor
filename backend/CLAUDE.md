# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Language Tutor Backend is a FastAPI-based REST API that powers the MyTacoAI language learning platform. It provides real-time voice conversations with OpenAI Realtime API, gamified challenges, progress tracking, subscription management, and AI-powered assessments.

## Development Commands

### Starting the Server
```bash
# Local development
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using the start script
./start.sh

# Production (Railway deployment)
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Database Operations
```bash
# Test database connection
python explore_db.py

# Run database queries for debugging
python test_database_queries.py

# Initialize indexes (runs automatically on startup)
# See database.py init_db() function
```

### Challenge Generation
```bash
# Generate reference challenges for all languages/levels
python generate_reference_challenges_crew.py

# Seed challenge pool for users
python seed_challenge_pool.py

# Run challenge pool replenisher (cron job)
python run_scheduler.py
```

### News Generation
```bash
# Generate daily news (separate Railway service)
python run_news_generator.py
```

### Testing
```bash
# Run specific tests
pytest tests/

# Test specific functionality
python test_queries.py
python test_challenge_pool.py
```

## Architecture Overview

### Application Entry Point
- **main.py**: FastAPI app initialization with all route registrations
- Uses Motor (async MongoDB driver) for database operations
- Middleware: CORS, GZip compression, monitoring, request logging
- Startup/shutdown handlers for database initialization and cleanup

### Core Architecture Patterns

#### Database Layer
- **database.py**: MongoDB connection setup and collection references
- **models.py**: Pydantic models for request/response validation and MongoDB documents
- Uses Motor (async MongoDB driver) with AsyncIOMotorClient
- Collections initialized at startup with TTL indexes for automatic expiration
- Environment-aware connection: Railway vs localhost with automatic fallback

Key collections:
- `users`: User accounts, authentication, subscription status
- `conversation_sessions`: Real-time conversation session data
- `learning_plans`: Structured learning paths with session tracking
- `challenge_pool`: User-specific personalized challenges
- `reference_challenges`: Template challenges for all languages/levels
- `challenge_sessions`: Challenge gameplay data and results
- `daily_stats`: Aggregated daily progress metrics
- `news_articles`: Daily news articles for reading practice
- `speaking_dna_profiles`: User's speaking analysis profiles

#### Authentication & Authorization
- **auth_routes.py**: Login, registration, password reset, email verification
- **auth.py**: JWT token generation, validation, password hashing
- Uses `python-jose` for JWT, `passlib` for bcrypt password hashing
- Apple Sign-In and Google OAuth integration
- Token expiration: 30 days (configurable)

#### Real-Time Voice Conversations
- **routes/realtime_routes.py**: WebRTC session management and OpenAI Realtime API integration
- Generates ephemeral keys for client-side WebRTC connections
- Session-based architecture: backend creates session, returns key/model to client
- Tracks realtime usage minutes for billing/limits
- Integrates with conversation help, sentence assessment, and learning plans

#### API Route Organization

**Modular routes** (in `routes/` directory):
- `realtime_routes.py`: Real-time voice conversation sessions
- `assessment_routes.py`: Speaking assessments and evaluations
- `session_summary_routes.py`: Post-conversation analysis and feedback
- `speaking_dna_routes.py`: Speaking profile analysis (premium feature)
- `heart_routes.py`: Heart system (focus energy) for free users
- `achievement_routes.py`: Badge/achievement system
- `stats_routes.py`: Gamification statistics and leaderboards
- `apple_iap_routes.py`: Apple In-App Purchase validation
- `google_play_routes.py`: Google Play Billing validation

**Legacy routes** (root level):
- `auth_routes.py`: Authentication endpoints
- `learning_routes.py`: Learning plan CRUD operations
- `progress_routes.py`: Progress tracking and statistics
- `challenge_routes.py`: Challenge gameplay and pool management
- `notification_routes.py`: Push notifications and WebSocket events
- `news_routes.py`: Daily news articles
- `stripe_routes.py`: Stripe subscription webhooks

#### AI Services & Features

##### Speaking Assessment
- **services/speaking_dna_service.py**: Advanced speaking analysis with audio processing
- **speaking_assessment.py**: Real-time speaking evaluation during conversations
- **pronunciation_assessment_service.py**: Azure-based pronunciation scoring
- **audio_analysis_service.py**: Audio feature extraction (pitch, energy, pace)
- Uses librosa, soundfile, and praat-parselmouth for audio analysis

##### Challenge Generation
- **challenge_generator_crew.py**: CrewAI-powered challenge generation
- **challenge_generator_ai.py**: Simple OpenAI-based challenge generation
- **challenge_pool_replenisher.py**: Scheduled job to replenish user challenge pools
- **challenge_pool_helpers.py**: Challenge pool queries and counting
- Configurable via environment variables: `USE_CREWAI`, `USER_POOL_FREQUENCY`

##### News Generation
- **news_generation/news_generator.py**: AI-powered daily news article generation
- **news_generation/news_scheduler.py**: Scheduled job (runs as separate Railway service)
- **news_generation/crew_agents.py**: CrewAI agents for news curation
- **news_generation/news_tools.py**: News API integration and tools
- Generates news in 7 languages for 6 CEFR levels daily

##### Contextual AI Assistance
- **conversation_help_improved.py**: Real-time conversation help (hints, translations)
- **contextual_chatbot.py**: Context-aware chatbot during practice
- **vector_chatbot.py**: RAG-based chatbot with embeddings
- **services/ai_context_builder.py**: Builds conversation context for AI

#### Subscription & Payments

##### Stripe Integration
- **stripe_routes.py**: Webhook handlers for subscription events
- **subscription_service.py**: Subscription state management and validation
- Handles: customer creation, subscription lifecycle, usage tracking
- Syncs subscription status with user records

##### Apple & Google IAP
- **routes/apple_iap_routes.py**: Apple receipt validation and subscription sync
- **routes/google_play_routes.py**: Google Play purchase verification
- **apple_iap_config.py**: Apple StoreKit configuration
- **google_play_config.py**: Google Play Billing configuration
- Server-side receipt validation ensures subscription integrity

##### Heart System (Free Users)
- **services/heart_service.py**: Heart/energy system for free tier
- **routes/heart_routes.py**: Heart consumption, refill, streak shields
- Separate heart pools per challenge type
- Refill mechanics: time-based or via subscription upgrade

#### Progress & Statistics

##### Daily Stats & Analytics
- **services/stats_service.py**: Aggregated statistics calculations
- **services/recent_performance_service.py**: Recent performance metrics
- **services/lifetime_progress_service.py**: Lifetime progress tracking
- **routes/stats_routes.py**: API endpoints for gamification stats
- Tracks: XP, streaks, completion rates, speaking time, accuracy

##### Learning Plan Management
- **learning_plan_service.py**: Learning plan creation and session tracking
- **learning_plan_session_completion_service.py**: Session completion logic
- **services/learning_plan_optimizer.py**: AI-powered plan optimization
- **intelligent_schedule_generator.py**: Adaptive scheduling based on user performance

#### Notifications & Real-Time
- **notification_service.py**: Expo push notification integration
- **websocket_routes.py**: WebSocket connections for real-time updates
- **websocket_manager.py**: WebSocket connection management
- **notification_triggers.py**: Automated notification triggers
- Tracks notification preferences and sends targeted push notifications

### Service Architecture

**Key services** (in `services/` directory):
- `speaking_dna_service.py`: Speaking profile analysis and breakthrough detection
- `heart_service.py`: Heart system state management
- `learning_plan_final_assessment_service.py`: Learning plan completion assessments
- `recent_performance_service.py`: Recent performance calculations
- `lifetime_progress_service.py`: Lifetime progress aggregations
- `stats_service.py`: Gamification statistics
- `timezone_utils.py`: Timezone-aware date/time utilities
- `upgrade_service.py`: Free to paid subscription upgrade logic
- `voice_check_service.py`: Voice quality check service
- `audio_analysis_service.py`: Audio feature extraction

### Background Jobs & Schedulers

#### Challenge Generation (Separate Railway Service)
- **run_scheduler.py**: Main scheduler entry point
- **cron_jobs/**: Scheduled tasks for challenge pool replenishment
- Runs daily at 2:00 AM UTC (configurable via `USER_POOL_FREQUENCY`)
- Uses CrewAI for high-quality challenges (optional, controlled by `USE_CREWAI`)

#### News Generation (Separate Railway Service)
- **run_news_generator.py**: News generation entry point
- **news_generation/news_scheduler.py**: Daily news generation scheduler
- Runs daily, generates news in 7 languages for 6 CEFR levels
- Uses CrewAI agents for content curation and translation

### Monitoring & Observability
- **monitoring/**: Slack integration for error alerts and performance monitoring
- **logging_config.py**: Production-safe logging configuration
- **duration_monitoring.py**: Session duration tracking and safeguards
- Middleware logs slow requests (>5s threshold)
- Error monitoring with Slack webhook integration

## Development Practices

### Environment Configuration
Create `.env` file (see `.env.example`):
```bash
OPENAI_API_KEY=sk-...
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=language_tutor
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
```

For Railway deployment:
- Uses Railway-provided environment variables
- Auto-detects `RAILWAY_ENVIRONMENT` and configures accordingly
- Supports Railway MongoDB plugin variables: `MONGOHOST`, `MONGOUSER`, etc.

### Database Indexes
Indexes are automatically created on startup (see `database.py init_db()`):
- TTL indexes for sessions, password resets, email verifications
- Unique indexes for emails, user_id + language pairs
- Compound indexes for query optimization (user_id + date, etc.)

### API Client Generation
The mobile app's API client is generated from `openapi.json`:
```bash
# Regenerate openapi.json from FastAPI
curl http://localhost:8000/openapi.json > openapi.json

# Mobile app then regenerates TypeScript client
# (see mobile repo's CLAUDE.md)
```

### Working with Pydantic Models
- All request/response models defined in `models.py`
- Use `BaseModel` for validation
- Custom `PyObjectId` field type for MongoDB ObjectIds
- Nested models for complex structures (e.g., `HeartPool` within `HeartSystemState`)

### CrewAI Integration
- **crewai** library for multi-agent AI workflows
- Used for challenge generation and news curation
- Configurable via `USE_CREWAI` environment variable
- Costs ~5x more than simple OpenAI calls but produces higher quality content
- See `CREWAI_REFERENCE_CHALLENGES.md` for details

### Subscription State Management
Subscription status tracked in user document:
- `subscription_status`: active, canceled, past_due, expired, trialing
- `subscription_plan`: try_learn, fluency_builder, team_mastery
- `subscription_period`: monthly, annual
- `subscription_expires_at`: Expiration timestamp
- `practice_minutes_used`: Speaking minutes used in current period

Validation happens in `subscription_service.py` with real-time checks.

### Audio Processing Pipeline
Speaking DNA analysis pipeline:
1. Client uploads audio via `/api/realtime/session-summary`
2. Backend transcribes with OpenAI Whisper or gpt-4o-transcribe
3. Audio analysis extracts features: pitch, energy, pace, pauses
4. Pronunciation assessment via Azure Speech Services (optional)
5. AI generates feedback and updates speaking profile
6. Results stored in `speaking_dna_profiles` collection

## Common Patterns

### Adding a New API Endpoint
1. Create route file in `routes/` directory (e.g., `routes/my_feature_routes.py`)
2. Define Pydantic request/response models in `models.py`
3. Implement route handlers using FastAPI decorators
4. Register router in `main.py`: `app.include_router(my_feature_router)`
5. Update `openapi.json` (automatically via FastAPI)

### Database Queries
```python
from database import users_collection, database

# Find one user
user = await users_collection.find_one({"email": email})

# Update user
await users_collection.update_one(
    {"_id": ObjectId(user_id)},
    {"$set": {"subscription_status": "active"}}
)

# Aggregation pipeline
pipeline = [
    {"$match": {"user_id": user_id}},
    {"$group": {"_id": "$language", "total": {"$sum": 1}}}
]
results = await collection.aggregate(pipeline).to_list(None)
```

### Authentication Dependency
```python
from auth import get_current_user

@router.get("/protected")
async def protected_route(current_user = Depends(get_current_user)):
    return {"user_id": current_user["_id"]}
```

### Background Jobs
For scheduled tasks, use separate Railway service:
1. Create script in `cron_jobs/` or use existing `run_scheduler.py`
2. Deploy as separate Railway service
3. Set cron schedule in Railway dashboard

## Deployment Configuration

### Railway Environment Variables
Required variables:
- `OPENAI_API_KEY`: OpenAI API key
- `MONGODB_URL`: MongoDB connection string (auto-provided by Railway MongoDB plugin)
- `DATABASE_NAME`: Database name (default: `language_tutor`)
- `ENVIRONMENT`: `production`
- `FRONTEND_URL`: `https://mytacoai.com`

Optional variables:
- `USE_CREWAI`: `true` or `false` (enable CrewAI for challenges)
- `USER_POOL_FREQUENCY`: `daily`, `weekly`, `biweekly`, `monthly`
- `SLACK_WEBHOOK_URL`: Slack webhook for error monitoring
- `SMTP_SERVER`, `SMTP_USERNAME`, `SMTP_PASSWORD`: Email configuration

### Railway Services
This backend runs as multiple Railway services:
1. **Main API**: Handles all HTTP requests (main.py)
2. **Challenge Scheduler**: Runs challenge pool replenishment (run_scheduler.py)
3. **News Generator**: Runs daily news generation (run_news_generator.py)

See `DEPLOYMENT_CHECKLIST.md` and `ENVIRONMENT_VARIABLES_GUIDE.md` for detailed deployment instructions.

### Database Migrations
No formal migration system. Changes are applied via:
1. Manual scripts (e.g., `production_integer_migration.py`)
2. Startup initialization (e.g., `init_db()` creates indexes)
3. Versioned seeding scripts (e.g., `seed_challenges.py`)

## Key Technical Details

### OpenAI Realtime API Integration
1. Client requests session via `/api/realtime/token`
2. Backend creates OpenAI Realtime session, returns ephemeral key
3. Client establishes WebRTC connection using ephemeral key
4. Audio streams directly between client and OpenAI (P2P)
5. Backend tracks session duration for billing
6. Post-session analysis via `/api/realtime/session-summary`

### Challenge Pool Architecture
- **Reference Challenges**: Template challenges (6 languages × 6 levels × 7 types)
- **User Challenge Pools**: Personalized challenges per user (copied from reference)
- Pool replenishment: Daily/weekly via background job
- Real-time counting: Query user's pool for available challenges
- Challenge types: error_spotting, swipe_fix, micro_quiz, story_builder, etc.

### Heart System (Focus Energy)
- Separate heart pools per challenge type
- Refill mechanics: 1 heart per 30 minutes (free), instant (paid)
- Streak shield: 5 correct answers → shield (protects from 1 wrong answer)
- Undo mechanic: 1-second grace period to undo wrong answer
- State persisted in `heart_system_state` field on user document

### Speaking DNA Analysis
- Analyzes speaking patterns: pronunciation, fluency, vocabulary, grammar
- Tracks evolution over time (weekly snapshots)
- Detects breakthroughs (significant improvements)
- Audio features: pitch variance, energy levels, speaking pace, pause patterns
- Uses librosa, praat-parselmouth for audio analysis

## Important Notes

- **Async/Await**: All database operations are async (Motor driver)
- **MongoDB ObjectIds**: Use `str(ObjectId())` when creating new IDs, validate with `ObjectId.is_valid()`
- **CORS**: Configured for `mytacoai.com` and localhost in development
- **GZip Compression**: Automatically compresses responses >1KB (60-80% reduction)
- **Railway Deployment**: Auto-deploys on push to main branch
- **Multiple Railway Services**: Main API + schedulers run as separate services
- **Python 3.10-3.13**: Required for CrewAI compatibility
- **No Traditional Tests**: Uses manual testing scripts and validation utilities

## Related Repository
This backend serves the mobile app at `/Users/alipala/github/MyTacoAIMobile`
