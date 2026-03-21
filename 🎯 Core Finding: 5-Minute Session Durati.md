🎯 Core Finding: 5-Minute Session Duration Limit

  All practice and learning sessions are strictly capped at 5 minutes maximum. This is enforced across the entire codebase:

  Where the 5-Minute Limit is Enforced:

  1. Learning Plan Sessions (learning_plan_session_completion_service.py:74-83)
    - Sessions >= 5.0 minutes → enforced to exactly 5.0 minutes, marked as "completed"
    - Sessions < 5.0 minutes → rounded to integers (4, 3, 2, 1), marked as "partial"
  2. Practice Sessions (progress_routes.py:465, 491, 544)
    - Same enforcement: cap at 5 minutes for completed sessions
    - Duration stored as integers only (no decimals)
  3. Session Summary Routes (session_summary_routes.py:487)
    - Explicitly caps duration: min(float(session_duration_minutes), 5.0)
    - Protects against frontend timer glitches

  ---
  📚 Session Types Breakdown

  1. Learning Plan Sessions

  Location: learning_routes.py, session_summary_routes.py, learning_plan_session_completion_service.py

  How They Work:
  - Users create a structured learning plan (6-24 weeks)
  - Each week has a specific focus (grammar, vocabulary, etc.)
  - 2 sessions per week by default
  - Each session is 5 minutes of conversation practice
  - Progress tracked in weekly_schedule.session_details
  - Session history stored with messages for future comparisons
  - Comprehensive AI-generated summaries after each session
  - Final assessment required after all sessions completed

  Key Fields:
  {
    "completed_sessions": 10,
    "total_sessions": 48,
    "progress_percentage": 20.8,
    "practice_minutes_used": 50.0,  # Accumulates across sessions
    "session_summaries": ["...", "..."],
    "session_history": [{
      "session_number": 1,
      "messages": [...],
      "duration_minutes": 5.0,
      "completed_at": "2026-02-23T..."
    }]
  }

  ---
  2. Practice Sessions (Free Style)

  Location: progress_routes.py, realtime_routes.py

  Three Variants:

  A. Predefined Topics

  - Built-in conversation topics (travel, business, daily life, etc.)
  - Topics provided by the app based on user's language/level
  - Example: "Ordering food at a restaurant" for A2 Spanish

  B. Custom Topics

  - User enters their own topic/prompt
  - AI researches the topic using gpt-4o-search-preview (routes/content_routes.py:100-150)
  - Provides current information, vocabulary, and discussion points
  - Example: User wants to discuss "recent elections in Netherlands"

  C. News-Based Conversations

  - Daily news articles generated for each language/level
  - Articles stored in news_articles collection
  - User selects a news article and practices conversation about it
  - News context passed to realtime API via news_context parameter

  Practice Session Storage:
  ConversationSession {
    "user_id": "...",
    "language": "spanish",
    "level": "B1",
    "topic": "travel",  # or custom topic or news article title
    "messages": [...],
    "duration_minutes": 5,  # Always integer, max 5
    "message_count": 12,
    "summary": "AI-generated summary...",
    "conversation_type": "practice" | "news",
    "enhanced_analysis": {...},  # Only for qualifying sessions
    "is_streak_eligible": true,  # If duration >= 5 minutes
    "created_at": "...",
    "updated_at": "..."
  }

  ---
  🎚️ Language Levels (CEFR)

  Your app uses the standard CEFR framework:

  | Level | Description        | Final Assessment Duration |
  |-------|--------------------|---------------------------|
  | A1    | Beginner           | 2 minutes                 |
  | A2    | Elementary         | 3 minutes                 |
  | B1    | Intermediate       | 4 minutes                 |
  | B2    | Upper Intermediate | 5 minutes                 |
  | C1    | Advanced           | 5 minutes                 |
  | C2    | Mastery            | 5 minutes                 |

  Usage in Code:
  - Stored in proficiency_level field (learning plans, sessions)
  - Used in AI prompts for appropriate difficulty
  - Affects challenge generation complexity
  - Determines assessment duration and criteria

  ---
  💳 Subscription Limits (subscription_service.py:118-200)

  Try & Learn (Free Tier)

  - 3 sessions per month (5 minutes each = 15 minutes total)
  - 1 speaking assessment monthly
  - Basic heart system for challenges

  Fluency Builder ($19.99/month)

  - 150 minutes monthly (duration-based tracking)
  - 30 sessions monthly
  - 2 speaking assessments monthly
  - 10 hearts for challenges (1-hour refill)

  Language Mastery ($39.99/month)

  - UNLIMITED minutes, sessions, and assessments
  - Unlimited hearts (instant refill)
  - Premium learning plans
  - Advanced analytics

  Important: The system tracks both session count AND minutes to enforce limits properly.

  ---
  🔄 Session Flow Architecture

  Frontend → Backend Flow:

  1. Session Start:
  POST /api/realtime/token
  → Creates OpenAI Realtime session
  → Returns ephemeral key for WebRTC connection
  → Starts session duration tracking
  2. During Session:
  POST /api/session-heartbeat (periodic)
  → Monitors active sessions
  → No deduction/tracking (monitoring only)
  → Prevents double-counting
  3. Session End:

  3. For Learning Plan Sessions:
  POST /api/learning/session-summary?plan_id=...
  → Saves session to learning plan
  → Increments completed_sessions
  → Tracks practice_minutes_used
  → Generates comprehensive summary
  → Updates subscription usage
  → Caps at 5 minutes

  3. For Practice Sessions:
  POST /api/progress/save-conversation
  → Creates/updates ConversationSession
  → Generates summary
  → Batch analyzes sentences (if provided)
  → Calculates enhanced statistics
  → Tracks subscription usage
  → Caps at 5 minutes

  ---
  🎯 Key Implementation Details

  Duration Enforcement Logic:

  # From learning_plan_session_completion_service.py:74-83
  if duration_minutes >= 5.0:
      enforced_duration = 5.0
      session_status = "completed"
  else:
      enforced_duration = float(max(1, int(round(duration_minutes))))
      session_status = "partial"

  Session History Tracking:

  Learning plans now store full session data for AI-powered comparisons:
  session_history = [{
    "session_number": 1,
    "messages": [...],  # Full conversation
    "duration_minutes": 5.0,
    "completed_at": "2026-02-23T10:30:00Z"
  }]

  Streak Eligibility:

  # Only sessions >= 5 minutes count towards streaks
  is_streak_eligible = (duration_minutes >= 5)

  Database Collections:

  - conversation_sessions: Practice/news sessions
  - learning_plans: Learning plan data + session history
  - news_articles: Daily news for conversation practice
  - users: Subscription status + usage tracking (practice_minutes_used, practice_sessions_used)

  ---
  🧩 Architecture Highlights

  1. Real-time Voice: OpenAI Realtime API with WebRTC (P2P audio streaming)
  2. Session Tracking: Dual tracking (session count + minutes)
  3. AI Features:
    - Comprehensive session summaries (GPT-4o)
    - Batch sentence analysis (pronunciation, grammar, vocabulary)
    - Speaking DNA analysis (audio feature extraction)
    - News generation (daily, 7 languages × 6 levels)
  4. Safeguards:
    - Duration capping (max 5 minutes)
    - Heartbeat monitoring (no double-counting)
    - Validation for subscription limits
    - Audit trails for duration changes

  ---
  ✅ Summary of Your Information

  Based on your description:
  - ✅ 5-minute duration limit: Confirmed and enforced throughout codebase
  - ✅ Learning plan sessions: Weekly structure, 2 sessions/week, comprehensive tracking
  - ✅ Practice sessions: Free style with predefined/custom topics ✅
  - ✅ Practice conversation with news: News articles as conversation topics ✅
  - ✅ Language levels A1-C2: CEFR framework fully implemented ✅

  