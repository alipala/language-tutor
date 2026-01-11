# Standout Features Implementation Guide
## Making MyTaco AI Tutor Unforgettable

**Document Version:** 1.0
**Created:** 2026-01-11
**Status:** Implementation Ready

---

## 🎯 IMPLEMENTATION PRIORITY

⚠️ **START WITH TIER 1 FIRST** ⚠️

Tier 1 features provide the highest ROI and create the most differentiation:
- **Conversational Memory** - Emotional connection & retention
- **Micro-Moment Celebrations** - Solves 5-minute engagement problem
- **Exit Ritual** - Clear value delivery & retention

**Estimated Timeline:**
- Tier 1: 2-3 weeks (MVP for standout features)
- Tier 2: 2-3 weeks (Human-like excellence)
- Tier 3: 1-2 weeks (Technical polish)

**Total: 5-8 weeks for complete implementation**

---

# Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema Changes](#database-schema-changes)
3. [TIER 1 Implementation](#tier-1-implementation)
   - 3.1 [Conversational Memory](#31-conversational-memory)
   - 3.2 [Micro-Moment Celebrations](#32-micro-moment-celebrations)
   - 3.3 [Exit Ritual](#33-exit-ritual)
4. [TIER 2 Implementation](#tier-2-implementation)
   - 4.1 [Charismatic Tutor Personality](#41-charismatic-tutor-personality)
   - 4.2 [Smart Recasting](#42-smart-recasting)
   - 4.3 [Interrupt Intelligence](#43-interrupt-intelligence)
5. [TIER 3 Implementation](#tier-3-implementation)
   - 5.1 [Voice Mirroring](#51-voice-mirroring)
   - 5.2 [Curiosity Following](#52-curiosity-following)
   - 5.3 [Transparent Teaching](#53-transparent-teaching)
   - 5.4 [Intelligent Silence](#54-intelligent-silence)
6. [Integration Guide](#integration-guide)
7. [Testing Strategy](#testing-strategy)
8. [Rollout Plan](#rollout-plan)
9. [Success Metrics](#success-metrics)

---

# Architecture Overview

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT (React Native)                       │
│  - Realtime Audio Connection (WebSocket/WebRTC)                 │
│  - Session State Manager                                         │
│  - Achievement Display                                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    BACKEND (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Session Orchestrator                                     │  │
│  │  - Memory Service                                         │  │
│  │  - Achievement Tracker                                    │  │
│  │  - Personality Engine                                     │  │
│  │  - Interruption Handler                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                                  │
┌───────▼────────┐              ┌─────────▼──────────┐
│   MongoDB      │              │   OpenAI           │
│   - User Data  │              │   Realtime API     │
│   - Memory     │              │   - gpt-realtime   │
│   - Sessions   │              │     -mini-2025-    │
│   - Analytics  │              │     12-15          │
└────────────────┘              └────────────────────┘
```

## Key Design Principles

1. **Non-Blocking**: All memory/achievement processing happens async
2. **Graceful Degradation**: If memory service fails, core tutoring continues
3. **Real-Time Injection**: Context injected via `session.update` and `conversation.item.create`
4. **User Control**: Memory can be edited/deleted by users
5. **Privacy First**: Store only learning-relevant data

---

# Database Schema Changes

## 1. User Profile Extensions

```python
# Add to existing User model in models/user.py

class UserProfile(BaseModel):
    """Extended user profile for conversational memory"""
    user_id: str

    # TIER 1: Conversational Memory
    personal_context: PersonalContext
    learning_history: LearningHistory
    conversation_style: ConversationStyle

    # TIER 2: Personality & Recasting
    preferred_personality: Optional[str] = "warm_encouraging"  # warm_encouraging, playful_humorous, professional_direct
    recasting_level: int = 1  # 1-4, increases with repeated errors

    # TIER 3: Voice Mirroring
    voice_profile: Optional[VoiceProfile] = None

    updated_at: datetime

class PersonalContext(BaseModel):
    """What we know about the user personally"""
    profession: Optional[str] = None
    industry: Optional[str] = None
    interests: List[str] = []  # ["hiking", "cooking", "technology"]
    family: Dict[str, Any] = {}  # {"has_kids": true, "ages": [5, 8]}
    location: Optional[str] = None
    native_language: Optional[str] = None

    # Recent memorable events (last 5)
    recent_events: List[MemorableEvent] = []

class MemorableEvent(BaseModel):
    """Things user mentioned that we should remember"""
    session_id: str
    session_number: int
    timestamp: datetime
    event_type: str  # "personal_story", "upcoming_event", "achievement", "challenge"
    description: str  # "mentioned upcoming vacation to Spain"
    follow_up_suggestion: Optional[str] = None  # "Ask how the Spain trip went"
    expires_at: Optional[datetime] = None  # For time-sensitive events

class LearningHistory(BaseModel):
    """What we know about their learning journey"""

    # Concepts they've mastered
    mastered_concepts: List[MasteredConcept] = []

    # Persistent mistakes they make
    persistent_mistakes: List[PersistentMistake] = []

    # Topics they engage with most
    favorite_topics: List[str] = []  # ["technology", "travel", "food"]

    # Topics they avoid or struggle with
    avoided_topics: List[str] = []

    # Overall progression milestones
    milestones: List[Milestone] = []

class MasteredConcept(BaseModel):
    """Concept they struggled with but now mastered"""
    concept: str  # "past_tense", "ser_vs_estar"
    struggled_session: int  # Session number when they first struggled
    struggled_date: datetime
    mastered_session: int  # Session number when they mastered it
    mastered_date: datetime
    celebration_shown: bool = False  # Have we celebrated this mastery?

class PersistentMistake(BaseModel):
    """Errors they repeatedly make"""
    error_type: str  # "ser_vs_estar", "subjunctive_mood"
    occurrences: int  # How many times seen
    first_seen: datetime
    last_seen: datetime
    correction_attempts: int  # How many times we've tried to correct
    context_examples: List[str] = []  # Examples of when this error occurs

class Milestone(BaseModel):
    """Major learning achievements"""
    milestone_type: str  # "level_up", "100_sessions", "mastered_grammar"
    title: str
    description: str
    achieved_at: datetime
    session_number: int

class ConversationStyle(BaseModel):
    """How user likes to interact"""
    humor_response: str = "neutral"  # "loves_puns", "no_jokes", "neutral"
    challenge_preference: str = "moderate"  # "easy", "moderate", "hard"
    correction_style: str = "gentle_immediate"  # "gentle_immediate", "end_of_session", "minimal"
    pace_preference: str = "moderate"  # "slow", "moderate", "fast"
    example_preference: str = "many"  # "few", "moderate", "many"
```

## 2. Session Tracking Extensions

```python
# Add to existing Session model

class SessionExtended(BaseModel):
    """Extended session data for standout features"""
    session_id: str
    user_id: str
    session_number: int  # User's Nth session overall

    # Existing fields...
    language: str
    level: str
    topic: str
    started_at: datetime
    ended_at: Optional[datetime]

    # TIER 1: Micro-Achievements
    achievements_earned: List[Achievement] = []

    # TIER 1: Exit Ritual Data
    exit_ritual: Optional[ExitRitualData] = None

    # TIER 2: Personality Used
    personality_mode: str = "warm_encouraging"

    # TIER 2: Recasting Events
    recasting_events: List[RecastingEvent] = []

    # TIER 3: Voice Profile Detected
    detected_voice_profile: Optional[VoiceProfile] = None

    # TIER 3: Interests Discussed
    interests_explored: List[str] = []

    # Analytics
    engagement_score: float = 0.0  # 0-100
    dopamine_moments: int = 0  # Number of celebration moments
    interruption_count: int = 0
    average_response_time: float = 0.0  # seconds

class Achievement(BaseModel):
    """Micro-achievement earned during session"""
    achievement_type: str  # "self_correction", "streak", "breakthrough", "level_up", "speed"
    concept: str  # What it was about
    timestamp: datetime
    celebration_text: str  # What the AI said
    dopamine_level: str  # "medium", "high", "very_high"
    user_reaction: Optional[str] = None  # If we can detect it

class ExitRitualData(BaseModel):
    """Data for exit ritual summary"""
    primary_achievement: str  # "mastered past tense"
    improving_skill: str  # "getting more confident with subjunctive"
    insight: str  # "discovered you process grammar better through examples"
    best_moment: str  # "when you self-corrected 'fui'"
    why_it_matters: str  # "shows you're internalizing the pattern"
    next_concept: str  # "past perfect tense"
    personal_hook: str  # "Based on your love of travel stories"
    exciting_outcome: str  # "talk about trips you wish you had taken"

class RecastingEvent(BaseModel):
    """Record of error correction"""
    timestamp: datetime
    error_type: str
    user_utterance: str  # What they said (with error)
    recast_response: str  # How AI corrected it
    recasting_level: int  # 1-4 (invisible, emphasized, explained, questioned)
    user_adopted: Optional[bool] = None  # Did they use correct form after?
```

## 3. New Collections

```python
# memory_snapshots collection
class MemorySnapshot(BaseModel):
    """Snapshot of what AI should remember at session start"""
    user_id: str
    session_id: str
    generated_at: datetime

    # Compiled memory context
    personal_reminders: List[str]  # ["Ask about Spain trip", "User is software engineer"]
    learning_reminders: List[str]  # ["Celebrate mastery of past tense", "Watch for ser vs estar errors"]
    conversation_reminders: List[str]  # ["User loves tech analogies", "Prefers fast pace"]

    # Raw context for instructions
    memory_context_string: str  # Formatted string injected into instructions

# achievement_templates collection
class AchievementTemplate(BaseModel):
    """Templates for celebrations"""
    achievement_type: str
    language: str  # For i18n
    templates: List[str]  # Multiple variations
    dopamine_level: str

    # Example:
    # {
    #   "achievement_type": "self_correction",
    #   "language": "en",
    #   "templates": [
    #     "YES! You caught yourself! That shows real learning.",
    #     "Nice catch! That self-correction is exactly what we want to see.",
    #     "Ooh you corrected yourself - that's the sign it's becoming automatic!"
    #   ],
    #   "dopamine_level": "medium"
    # }
```

---

# TIER 1 Implementation

## 3.1 Conversational Memory

### Overview
Enable AI tutor to remember user's personal context, learning history, and conversation style across sessions.

### Architecture

```
┌────────────────────────────────────────────────────────┐
│  Session Start                                         │
└────────────────┬───────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────┐
│  Memory Service: Build Context                         │
│  1. Fetch UserProfile from DB                          │
│  2. Fetch last 3 session summaries                     │
│  3. Check for follow-up reminders                      │
│  4. Compile memory context string                      │
└────────────────┬───────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────┐
│  Inject into Instructions                              │
│  - Personal context                                    │
│  - Learning history                                    │
│  - Conversation preferences                            │
└────────────────┬───────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────┐
│  During Session: Track New Memories                    │
│  - Listen for personal information shared              │
│  - Detect mastered concepts                            │
│  - Note persistent mistakes                            │
└────────────────┬───────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────┐
│  Session End: Update Memory                            │
│  - Save new personal context                           │
│  - Update learning history                             │
│  - Create follow-up reminders                          │
└────────────────────────────────────────────────────────┘
```

### Implementation Steps

#### Step 1: Create Memory Service

**File:** `backend/services/memory_service.py`

```python
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from models.user import UserProfile, PersonalContext, MemorableEvent, MasteredConcept
from database import users_collection, sessions_collection
from bson import ObjectId

class MemoryService:
    """
    Service for managing conversational memory across sessions.

    Key Responsibilities:
    1. Build memory context for session start
    2. Extract new memories from conversation
    3. Update user profile with learned information
    4. Generate follow-up reminders
    """

    def __init__(self):
        self.users_collection = users_collection
        self.sessions_collection = sessions_collection

    async def build_session_memory_context(
        self,
        user_id: str,
        current_session_number: int
    ) -> Dict[str, Any]:
        """
        Build comprehensive memory context for session start.

        Returns:
        {
            "memory_context_string": str,  # For injection into instructions
            "personal_reminders": List[str],
            "learning_reminders": List[str],
            "conversation_reminders": List[str]
        }
        """
        # Fetch user profile
        user_doc = await self.users_collection.find_one(
            {"_id": ObjectId(user_id)}
        )

        if not user_doc or "profile" not in user_doc:
            return self._get_empty_memory_context()

        profile = user_doc["profile"]

        # Build memory components
        personal_context = self._build_personal_context(profile.get("personal_context", {}))
        learning_context = self._build_learning_context(
            profile.get("learning_history", {}),
            current_session_number
        )
        conversation_context = self._build_conversation_context(
            profile.get("conversation_style", {})
        )

        # Compile into formatted string
        memory_string = self._compile_memory_string(
            personal_context,
            learning_context,
            conversation_context
        )

        return {
            "memory_context_string": memory_string,
            "personal_reminders": personal_context,
            "learning_reminders": learning_context,
            "conversation_reminders": conversation_context
        }

    def _build_personal_context(self, personal_context: Dict) -> List[str]:
        """Extract personal reminders from profile"""
        reminders = []

        # Profession
        if personal_context.get("profession"):
            reminders.append(f"User is a {personal_context['profession']}")

        # Interests
        interests = personal_context.get("interests", [])
        if interests:
            reminders.append(f"User's interests: {', '.join(interests)}")

        # Recent events with follow-ups
        recent_events = personal_context.get("recent_events", [])
        for event in recent_events:
            # Check if event needs follow-up
            if self._should_follow_up(event):
                if event.get("follow_up_suggestion"):
                    reminders.append(event["follow_up_suggestion"])
                else:
                    reminders.append(f"Follow up: {event['description']}")

        # Family context
        family = personal_context.get("family", {})
        if family.get("has_kids"):
            reminders.append(f"User has {len(family.get('ages', []))} children")

        return reminders

    def _build_learning_context(
        self,
        learning_history: Dict,
        current_session: int
    ) -> List[str]:
        """Extract learning reminders"""
        reminders = []

        # Recently mastered concepts (celebrate if not yet done)
        mastered = learning_history.get("mastered_concepts", [])
        for concept in mastered:
            if not concept.get("celebration_shown"):
                reminders.append(
                    f"CELEBRATE: User mastered '{concept['concept']}' "
                    f"(struggled in session {concept['struggled_session']}, "
                    f"mastered in session {concept['mastered_session']})"
                )

        # Persistent mistakes (be watchful)
        mistakes = learning_history.get("persistent_mistakes", [])
        for mistake in mistakes:
            if mistake.get("occurrences", 0) >= 3:
                reminders.append(
                    f"WATCH: User struggles with '{mistake['error_type']}' "
                    f"({mistake['occurrences']} times). "
                    f"Use level {min(4, mistake.get('correction_attempts', 0) + 1)} recasting."
                )

        # Favorite topics (use for engagement)
        favorite_topics = learning_history.get("favorite_topics", [])
        if favorite_topics:
            reminders.append(
                f"User engages most with: {', '.join(favorite_topics[:3])}"
            )

        return reminders

    def _build_conversation_context(self, conversation_style: Dict) -> List[str]:
        """Extract conversation style preferences"""
        reminders = []

        humor = conversation_style.get("humor_response", "neutral")
        if humor == "loves_puns":
            reminders.append("User loves wordplay and puns - use them!")
        elif humor == "no_jokes":
            reminders.append("User prefers serious approach - skip humor")

        challenge = conversation_style.get("challenge_preference", "moderate")
        reminders.append(f"Challenge preference: {challenge}")

        correction = conversation_style.get("correction_style", "gentle_immediate")
        reminders.append(f"Correction style: {correction}")

        pace = conversation_style.get("pace_preference", "moderate")
        reminders.append(f"Speaking pace: {pace}")

        return reminders

    def _compile_memory_string(
        self,
        personal: List[str],
        learning: List[str],
        conversation: List[str]
    ) -> str:
        """Compile memory reminders into formatted instruction string"""

        if not any([personal, learning, conversation]):
            return ""

        memory_string = "\n\n[CONVERSATIONAL MEMORY - READ CAREFULLY]\n\n"

        if personal:
            memory_string += "PERSONAL CONTEXT (Reference naturally in conversation):\n"
            for reminder in personal:
                memory_string += f"- {reminder}\n"
            memory_string += "\n"

        if learning:
            memory_string += "LEARNING HISTORY (Use this to personalize teaching):\n"
            for reminder in learning:
                memory_string += f"- {reminder}\n"
            memory_string += "\n"

        if conversation:
            memory_string += "CONVERSATION PREFERENCES (Adapt your style):\n"
            for reminder in conversation:
                memory_string += f"- {reminder}\n"

        memory_string += "\nIMPORTANT: Use this memory to make the conversation feel continuous and personal.\n"
        memory_string += "Reference past sessions naturally, celebrate progress, and adapt to their preferences.\n"

        return memory_string

    def _should_follow_up(self, event: Dict) -> bool:
        """Determine if event needs follow-up"""
        # Events from 1-3 sessions ago should be followed up
        event_session = event.get("session_number", 0)
        # This would be compared against current session number in actual usage

        # Check if expired
        if event.get("expires_at"):
            if datetime.fromisoformat(event["expires_at"]) < datetime.now():
                return False

        # Follow up on personal stories and upcoming events
        return event.get("event_type") in ["personal_story", "upcoming_event"]

    def _get_empty_memory_context(self) -> Dict:
        """Return empty context for new users"""
        return {
            "memory_context_string": "",
            "personal_reminders": [],
            "learning_reminders": [],
            "conversation_reminders": []
        }

    async def extract_memories_from_session(
        self,
        user_id: str,
        session_id: str,
        session_number: int,
        transcript: str,
        ai_analysis: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Extract memorable information from session transcript.

        Uses GPT-4 to analyze conversation and identify:
        1. Personal information shared
        2. Concepts mastered
        3. Persistent errors
        4. Conversation style preferences

        Returns: Updates to apply to user profile
        """
        from openai import AsyncOpenAI
        import os

        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Use GPT-4 to extract structured memories
        analysis_prompt = f"""
Analyze this language learning session transcript and extract structured memory information.

TRANSCRIPT:
{transcript}

Extract and return JSON with:
{{
    "personal_information": [
        {{"type": "profession", "value": "software engineer"}},
        {{"type": "interest", "value": "hiking"}},
        {{"type": "family", "value": "has 2 kids"}},
        {{"type": "event", "description": "going to Spain next month", "follow_up": "Ask how Spain trip went", "expires_in_days": 45}}
    ],
    "learning_progress": [
        {{"concept": "past_tense", "status": "mastered", "evidence": "used correctly 5 times"}},
        {{"concept": "ser_vs_estar", "status": "struggling", "occurrences": 3}}
    ],
    "conversation_style": {{
        "humor_response": "loves_puns | no_jokes | neutral",
        "challenge_preference": "easy | moderate | hard",
        "engagement_topics": ["technology", "travel"]
    }}
}}

Focus on:
- Information the user explicitly shared about themselves
- Clear evidence of learning progress or struggles
- User's response to different teaching approaches

Return ONLY valid JSON.
        """

        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a memory extraction system for language learning sessions."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            extracted = json.loads(response.choices[0].message.content)

            # Apply extracted memories to user profile
            await self._apply_memory_updates(user_id, session_id, session_number, extracted)

            return extracted

        except Exception as e:
            print(f"[MEMORY] Error extracting memories: {str(e)}")
            return {}

    async def _apply_memory_updates(
        self,
        user_id: str,
        session_id: str,
        session_number: int,
        extracted: Dict
    ):
        """Apply extracted memories to user profile"""

        update_operations = {}

        # Process personal information
        personal_info = extracted.get("personal_information", [])
        for info in personal_info:
            if info["type"] == "profession":
                update_operations["profile.personal_context.profession"] = info["value"]
            elif info["type"] == "interest":
                update_operations.setdefault("$addToSet", {})
                update_operations["$addToSet"]["profile.personal_context.interests"] = info["value"]
            elif info["type"] == "event":
                event = {
                    "session_id": session_id,
                    "session_number": session_number,
                    "timestamp": datetime.now(),
                    "event_type": "personal_story" if "event" not in info else "upcoming_event",
                    "description": info["description"],
                    "follow_up_suggestion": info.get("follow_up"),
                    "expires_at": datetime.now() + timedelta(days=info.get("expires_in_days", 30)) if info.get("expires_in_days") else None
                }
                update_operations.setdefault("$push", {})
                update_operations["$push"]["profile.personal_context.recent_events"] = {
                    "$each": [event],
                    "$slice": -5  # Keep only last 5 events
                }

        # Process learning progress
        learning_progress = extracted.get("learning_progress", [])
        for progress in learning_progress:
            if progress["status"] == "mastered":
                # Check if this was previously a struggle
                user_doc = await self.users_collection.find_one({"_id": ObjectId(user_id)})
                if user_doc:
                    mistakes = user_doc.get("profile", {}).get("learning_history", {}).get("persistent_mistakes", [])
                    struggled_session = None
                    for mistake in mistakes:
                        if mistake.get("error_type") == progress["concept"]:
                            struggled_session = mistake.get("first_seen")
                            break

                    if struggled_session:
                        # This is a breakthrough - add to mastered concepts
                        mastered = {
                            "concept": progress["concept"],
                            "struggled_session": struggled_session,
                            "struggled_date": struggled_session,
                            "mastered_session": session_number,
                            "mastered_date": datetime.now(),
                            "celebration_shown": False
                        }
                        update_operations.setdefault("$push", {})
                        update_operations["$push"]["profile.learning_history.mastered_concepts"] = mastered

            elif progress["status"] == "struggling":
                # Add or update persistent mistake
                # This requires more complex logic - simplified here
                update_operations.setdefault("$push", {})
                update_operations["$push"]["profile.learning_history.persistent_mistakes"] = {
                    "error_type": progress["concept"],
                    "occurrences": progress.get("occurrences", 1),
                    "first_seen": datetime.now(),
                    "last_seen": datetime.now(),
                    "correction_attempts": 0,
                    "context_examples": []
                }

        # Apply updates
        if update_operations:
            await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                update_operations
            )
            print(f"[MEMORY] Applied memory updates for user {user_id}")
```

#### Step 2: Integrate Memory into Session Start

**File:** `backend/routes/realtime_routes.py` (Modify existing)

```python
# Add to imports
from services.memory_service import MemoryService

# Modify generate_token function (around line 1038)
@router.post("/api/realtime/token")
async def generate_token(
    request: TutorSessionRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)
):
    # ... existing code ...

    # NEW: Build memory context if authenticated user
    memory_context = ""
    if current_user:
        try:
            memory_service = MemoryService()

            # Get user's total session count
            session_count = await sessions_collection.count_documents(
                {"user_id": current_user.id}
            )

            # Build memory context
            memory_data = await memory_service.build_session_memory_context(
                user_id=current_user.id,
                current_session_number=session_count + 1
            )

            memory_context = memory_data["memory_context_string"]

            print(f"[MEMORY] Built context with {len(memory_data['personal_reminders'])} personal reminders")

        except Exception as e:
            print(f"[MEMORY] Error building context (non-blocking): {str(e)}")
            # Continue without memory context

    # Build instructions with memory context
    base_instructions = build_universal_instructions(request)
    instructions = base_instructions + memory_context

    # ... rest of existing code ...
```

#### Step 3: Extract Memories After Session

**File:** `backend/routes/realtime_routes.py` (Modify existing usage endpoint)

```python
# Modify log_realtime_usage function to extract memories
@router.post("/api/realtime/usage-log")
async def log_realtime_usage(
    usage_data: RealtimeUsageData,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # ... existing code ...

    # NEW: Extract memories in background (non-blocking)
    if current_user and usage_data.transcript:
        async def extract_and_save_memories():
            try:
                memory_service = MemoryService()
                await memory_service.extract_memories_from_session(
                    user_id=current_user.id,
                    session_id=usage_data.session_id,
                    session_number=session_number,
                    transcript=usage_data.transcript
                )
                print(f"[MEMORY] Extracted memories from session {usage_data.session_id}")
            except Exception as e:
                print(f"[MEMORY] Error extracting memories: {str(e)}")

        background_tasks.add_task(extract_and_save_memories)

    # ... rest of existing code ...
```

---

## 3.2 Micro-Moment Celebrations

### Overview
Detect and celebrate learning achievements in real-time during 5-minute sessions to create dopamine-driven engagement.

### Architecture

```
┌────────────────────────────────────────────────────────┐
│  During Session: Real-Time Achievement Detection       │
└────────────────┬───────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────┐
│  Achievement Tracker Service                           │
│  - Listen to conversation events                       │
│  - Detect achievement patterns                         │
│  - Trigger celebrations                                │
└────────────────┬───────────────────────────────────────┘
                 │
        ┌────────┼────────┐
        │                 │
┌───────▼────────┐  ┌────▼───────────┐
│  Inject        │  │  Track in      │
│  Celebration   │  │  Database      │
│  Context       │  │  for Analytics │
└────────────────┘  └────────────────┘
```

### Implementation Steps

#### Step 1: Create Achievement Tracker Service

**File:** `backend/services/achievement_tracker_service.py`

```python
from typing import Dict, List, Optional
from datetime import datetime
from models.user import Achievement
import random

class AchievementTrackerService:
    """
    Real-time achievement detection and celebration system.

    Detects:
    1. Self-corrections
    2. Streaks (3+ correct uses)
    3. Breakthroughs (mastered previously struggled concept)
    4. Speed improvements
    5. Level-up readiness
    """

    # Achievement patterns
    ACHIEVEMENT_TYPES = {
        "self_correction": {
            "dopamine_level": "medium",
            "celebration_templates": [
                "YES! You caught yourself! That shows real learning.",
                "Nice catch! That self-correction is exactly what we want to see.",
                "Ooh you corrected yourself - that's the sign it's becoming automatic!",
                "Love that you caught your own mistake - that's progress!"
            ]
        },
        "streak": {
            "dopamine_level": "high",
            "celebration_templates": [
                "Okay you just used {concept} {count} times perfectly - you're getting this!",
                "That's {count} in a row! You're on fire with {concept}!",
                "Wait, that's {count} correct uses of {concept}! This is clicking for you!",
                "{count} perfect examples of {concept} - you've got this down!"
            ]
        },
        "breakthrough": {
            "dopamine_level": "very_high",
            "celebration_templates": [
                "Wait - you just used {concept} naturally! Remember when that was tricky for you?",
                "Okay I'm noticing you just used {concept} without even thinking about it. That's HUGE!",
                "Did you realize you just used {concept} perfectly? Last week that was hard for you!",
                "That's breakthrough moment - you used {concept} like a native speaker!"
            ]
        },
        "speed": {
            "dopamine_level": "medium",
            "celebration_templates": [
                "You answered that so quickly! It's becoming automatic.",
                "That was instant - no hesitation. You're getting fluent with this!",
                "Wow, that came out fast! Your brain is processing {concept} automatically now.",
                "That speed! You didn't even have to think about {concept}."
            ]
        },
        "level_up": {
            "dopamine_level": "high",
            "celebration_templates": [
                "You're ready for something harder. Let's try {next_concept}.",
                "Okay you're consistently performing above {current_level}. Time to challenge you more!",
                "You've mastered {current_level} content. Ready for {next_concept}?",
                "That's it - you've outgrown {current_level}. Let's level up to {next_concept}!"
            ]
        }
    }

    def __init__(self):
        self.session_state = {}  # Track state per session

    def initialize_session(self, session_id: str, user_learning_history: Dict):
        """Initialize tracking for new session"""
        self.session_state[session_id] = {
            "achievements": [],
            "concept_usage": {},  # Track correct uses per concept
            "recent_errors": [],
            "struggled_concepts": self._extract_struggled_concepts(user_learning_history),
            "start_time": datetime.now(),
            "response_times": []
        }

    def _extract_struggled_concepts(self, learning_history: Dict) -> List[str]:
        """Get concepts user previously struggled with"""
        mistakes = learning_history.get("persistent_mistakes", [])
        return [m["error_type"] for m in mistakes]

    def detect_achievement(
        self,
        session_id: str,
        event_type: str,
        event_data: Dict
    ) -> Optional[Dict]:
        """
        Detect if an achievement occurred.

        Returns: {
            "achievement_type": str,
            "celebration_text": str,
            "dopamine_level": str,
            "inject_immediately": bool
        }
        """
        if session_id not in self.session_state:
            return None

        state = self.session_state[session_id]

        # Route to appropriate detector
        if event_type == "self_correction":
            return self._detect_self_correction(state, event_data)
        elif event_type == "correct_usage":
            return self._detect_streak_or_breakthrough(state, event_data)
        elif event_type == "fast_response":
            return self._detect_speed_improvement(state, event_data)
        elif event_type == "level_assessment":
            return self._detect_level_up(state, event_data)

        return None

    def _detect_self_correction(self, state: Dict, data: Dict) -> Optional[Dict]:
        """User caught their own mistake"""
        concept = data.get("concept", "that")

        achievement = {
            "achievement_type": "self_correction",
            "concept": concept,
            "celebration_text": self._get_random_template("self_correction", {}),
            "dopamine_level": "medium",
            "inject_immediately": True,
            "timestamp": datetime.now()
        }

        state["achievements"].append(achievement)
        return achievement

    def _detect_streak_or_breakthrough(self, state: Dict, data: Dict) -> Optional[Dict]:
        """Detect streak (3+ correct) or breakthrough (mastered struggled concept)"""
        concept = data.get("concept")
        is_correct = data.get("is_correct", False)

        if not is_correct:
            # Reset streak
            state["concept_usage"][concept] = 0
            return None

        # Increment correct usage count
        state["concept_usage"][concept] = state["concept_usage"].get(concept, 0) + 1
        count = state["concept_usage"][concept]

        # Check for breakthrough first (higher priority)
        if count == 1 and concept in state["struggled_concepts"]:
            achievement = {
                "achievement_type": "breakthrough",
                "concept": concept,
                "celebration_text": self._get_random_template("breakthrough", {"concept": concept}),
                "dopamine_level": "very_high",
                "inject_immediately": True,
                "timestamp": datetime.now()
            }
            state["achievements"].append(achievement)
            return achievement

        # Check for streak (3, 5, 7...)
        if count >= 3 and count % 2 == 1:  # Celebrate at 3, 5, 7...
            achievement = {
                "achievement_type": "streak",
                "concept": concept,
                "celebration_text": self._get_random_template("streak", {"concept": concept, "count": count}),
                "dopamine_level": "high",
                "inject_immediately": True,
                "timestamp": datetime.now()
            }
            state["achievements"].append(achievement)
            return achievement

        return None

    def _detect_speed_improvement(self, state: Dict, data: Dict) -> Optional[Dict]:
        """User responded faster than usual"""
        response_time = data.get("response_time", 0)
        concept = data.get("concept", "that")

        state["response_times"].append(response_time)

        # Need at least 5 responses to establish baseline
        if len(state["response_times"]) < 5:
            return None

        avg_time = sum(state["response_times"][:-1]) / len(state["response_times"][:-1])

        # Current response is 30%+ faster than average
        if response_time < avg_time * 0.7:
            achievement = {
                "achievement_type": "speed",
                "concept": concept,
                "celebration_text": self._get_random_template("speed", {"concept": concept}),
                "dopamine_level": "medium",
                "inject_immediately": True,
                "timestamp": datetime.now()
            }
            state["achievements"].append(achievement)
            return achievement

        return None

    def _detect_level_up(self, state: Dict, data: Dict) -> Optional[Dict]:
        """User is ready for higher difficulty"""
        current_level = data.get("current_level")
        next_concept = data.get("next_concept")

        # This would be triggered by external assessment logic
        achievement = {
            "achievement_type": "level_up",
            "concept": next_concept,
            "celebration_text": self._get_random_template(
                "level_up",
                {"current_level": current_level, "next_concept": next_concept}
            ),
            "dopamine_level": "high",
            "inject_immediately": True,
            "timestamp": datetime.now()
        }
        state["achievements"].append(achievement)
        return achievement

    def _get_random_template(self, achievement_type: str, variables: Dict) -> str:
        """Get random celebration template and fill variables"""
        templates = self.ACHIEVEMENT_TYPES[achievement_type]["celebration_templates"]
        template = random.choice(templates)

        # Fill in variables
        for key, value in variables.items():
            template = template.replace(f"{{{key}}}", str(value))

        return template

    def get_session_summary(self, session_id: str) -> Dict:
        """Get achievement summary for session end"""
        if session_id not in self.session_state:
            return {"total_achievements": 0, "dopamine_moments": 0}

        state = self.session_state[session_id]
        achievements = state["achievements"]

        return {
            "total_achievements": len(achievements),
            "dopamine_moments": len([a for a in achievements if a["dopamine_level"] in ["high", "very_high"]]),
            "achievements": achievements,
            "most_practiced_concept": max(state["concept_usage"].items(), key=lambda x: x[1])[0] if state["concept_usage"] else None
        }

    def cleanup_session(self, session_id: str):
        """Clean up session state"""
        if session_id in self.session_state:
            del self.session_state[session_id]
```

#### Step 2: Create Achievement Detection Function for Realtime API

**File:** `backend/routes/realtime_routes.py` (Add to payload)

```python
# Modify generate_token to include achievement detection function

# Add achievement tracker as session-scoped variable
achievement_tracker = AchievementTrackerService()

@router.post("/api/realtime/token")
async def generate_token(request: TutorSessionRequest, current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)):
    # ... existing code ...

    payload = {
        "model": model,
        "voice": selected_voice,
        "instructions": instructions,
        "modalities": ["audio", "text"],
        # ... existing config ...

        # NEW: Add function for achievement detection
        "tools": [
            {
                "type": "function",
                "name": "report_learning_event",
                "description": "Report significant learning events during the conversation for real-time celebration and tracking",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_type": {
                            "type": "string",
                            "enum": ["self_correction", "correct_usage", "error", "fast_response"],
                            "description": "Type of learning event"
                        },
                        "concept": {
                            "type": "string",
                            "description": "The grammar/vocabulary concept involved (e.g., 'past_tense', 'ser_vs_estar')"
                        },
                        "is_correct": {
                            "type": "boolean",
                            "description": "Whether the usage was correct"
                        },
                        "user_utterance": {
                            "type": "string",
                            "description": "What the user said"
                        },
                        "response_time": {
                            "type": "number",
                            "description": "Approximate seconds user took to respond"
                        }
                    },
                    "required": ["event_type", "concept"]
                }
            }
        ]
    }

    # ... rest of code ...
```

#### Step 3: Add Achievement Instructions to Prompt

**File:** `backend/prompt_optimization_helpers.py` (Modify `build_universal_instructions`)

```python
def build_universal_instructions(request: TutorSessionRequest) -> str:
    """Build universal instructions with achievement tracking"""

    # ... existing instruction building ...

    # NEW: Add achievement tracking instructions
    achievement_instructions = """

[REAL-TIME ACHIEVEMENT CELEBRATION]

CRITICAL: You must actively detect and celebrate learning moments DURING the conversation.

CALL report_learning_event() function when you observe:

1. SELF-CORRECTION (event_type: "self_correction"):
   User: "Yesterday I go... went to the park"
   → IMMEDIATELY: "YES! You caught yourself! That shows real learning."
   → Call: report_learning_event(event_type="self_correction", concept="past_tense", user_utterance="...")

2. CORRECT USAGE (event_type: "correct_usage"):
   User uses target concept correctly
   → Track internally for streaks
   → Call: report_learning_event(event_type="correct_usage", concept="past_tense", is_correct=true)
   → If 3rd+ correct use: "Okay that's 3 perfect uses of past tense - you're getting this!"

3. ERRORS (event_type: "error"):
   User makes mistake
   → Don't over-celebrate, but track for learning
   → Call: report_learning_event(event_type="error", concept="ser_vs_estar", is_correct=false)

4. FAST RESPONSE (event_type: "fast_response"):
   User responds quickly without hesitation
   → "That was instant - no hesitation!"
   → Call: report_learning_event(event_type="fast_response", concept="...", response_time=1.5)

CELEBRATION FREQUENCY:
- Aim for 3-5 micro-celebrations per 5-minute session
- Space them out (not every single correct usage)
- Make celebrations feel natural, not robotic

CELEBRATION STYLE:
- Genuine excitement: "Okay I'm noticing something..."
- Specific: "You just used [X] three times perfectly"
- Progress-focused: "Remember when this was hard?"
- Brief: 1 sentence celebration, then continue

DO NOT:
- Celebrate every tiny thing (diminishes impact)
- Use same celebration twice in one session
- Interrupt important moments just to celebrate
- Make it feel forced or artificial
    """

    instructions = base_instructions + achievement_instructions

    return instructions
```

#### Step 4: Handle Achievement Function Calls (WebSocket Handler)

**File:** `backend/routes/realtime_routes.py` (New WebSocket endpoint)

```python
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/realtime/achievements/{session_id}")
async def achievement_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket handler for real-time achievement processing.

    Listens for function calls from OpenAI Realtime API and:
    1. Detects achievements
    2. Injects celebration context
    3. Tracks for analytics
    """
    await websocket.accept()

    tracker = AchievementTrackerService()

    # Initialize session
    # (Would fetch user learning history here)
    tracker.initialize_session(session_id, {})

    try:
        while True:
            # Receive function call from OpenAI
            data = await websocket.receive_json()

            if data.get("type") == "function_call":
                function_name = data.get("name")
                arguments = data.get("arguments", {})

                if function_name == "report_learning_event":
                    # Detect achievement
                    achievement = tracker.detect_achievement(
                        session_id=session_id,
                        event_type=arguments.get("event_type"),
                        event_data=arguments
                    )

                    if achievement and achievement["inject_immediately"]:
                        # Send celebration back to client
                        await websocket.send_json({
                            "type": "celebration",
                            "text": achievement["celebration_text"],
                            "dopamine_level": achievement["dopamine_level"]
                        })

                        print(f"[ACHIEVEMENT] {achievement['achievement_type']}: {achievement['celebration_text']}")

    except WebSocketDisconnect:
        # Session ended - get summary
        summary = tracker.get_session_summary(session_id)
        print(f"[ACHIEVEMENT] Session {session_id} summary: {summary}")
        tracker.cleanup_session(session_id)
```

---

## 3.3 Exit Ritual

### Overview
Create a memorable, structured ending to every session that:
1. Summarizes victories
2. Highlights best moment
3. Sets up cliffhanger for next session

### Implementation Steps

#### Step 1: Create Exit Ritual Service

**File:** `backend/services/exit_ritual_service.py`

```python
from typing import Dict, Optional
from datetime import datetime

class ExitRitualService:
    """
    Generate personalized, memorable session endings.

    Structure:
    1. Victory Summary (10s): What they accomplished
    2. Highlight Reel (10s): Best moment of the session
    3. Cliffhanger Hook (10s): Exciting preview of next session
    """

    def __init__(self):
        pass

    def generate_exit_ritual(
        self,
        session_data: Dict,
        user_profile: Optional[Dict] = None
    ) -> str:
        """
        Generate personalized exit ritual text.

        Args:
            session_data: {
                "achievements": List[Achievement],
                "primary_concept": str,
                "secondary_concept": str,
                "errors": List[str],
                "best_moment": str,
                "engagement_topics": List[str]
            }
            user_profile: {
                "interests": List[str],
                "learning_history": Dict
            }

        Returns:
            Formatted exit ritual script
        """

        # Extract key information
        primary_achievement = self._identify_primary_achievement(session_data)
        improving_skill = self._identify_improving_skill(session_data)
        insight = self._generate_insight(session_data)
        best_moment = self._format_best_moment(session_data)
        next_concept = self._determine_next_concept(session_data, user_profile)
        personal_hook = self._create_personal_hook(next_concept, user_profile)

        # Build exit ritual script
        ritual = f"""
Alright, amazing session! Here's what happened today:

✅ VICTORIES:
- You {primary_achievement}
- You're getting more confident with {improving_skill}
- You discovered {insight}

🌟 HIGHLIGHT:
My favorite moment was {best_moment['description']} - {best_moment['why_it_matters']}

🎯 NEXT TIME:
I want to show you {next_concept['name']}. {personal_hook}
It's going to unlock {next_concept['exciting_outcome']}.

Great work today - see you next time!
        """.strip()

        return ritual

    def _identify_primary_achievement(self, session_data: Dict) -> str:
        """Identify the main thing they accomplished"""
        achievements = session_data.get("achievements", [])

        # Prioritize breakthroughs and level-ups
        for achievement in achievements:
            if achievement["achievement_type"] in ["breakthrough", "level_up"]:
                return f"mastered {achievement['concept']}"

        # Otherwise use primary concept
        primary = session_data.get("primary_concept", "past tense")
        return f"practiced {primary} successfully"

    def _identify_improving_skill(self, session_data: Dict) -> str:
        """Identify what they're getting better at"""
        # Look at secondary concept or most practiced
        secondary = session_data.get("secondary_concept")
        if secondary:
            return secondary

        # Default
        return "speaking fluency"

    def _generate_insight(self, session_data: Dict) -> str:
        """Generate a learning insight"""
        achievements = session_data.get("achievements", [])

        # Count self-corrections
        self_corrections = len([a for a in achievements if a["achievement_type"] == "self_correction"])
        if self_corrections >= 2:
            return "you're starting to catch your own mistakes - that's real progress"

        # Check for speed improvements
        speed_achievements = [a for a in achievements if a["achievement_type"] == "speed"]
        if speed_achievements:
            return "your responses are getting faster and more automatic"

        # Default
        return "your comfort level with the language is growing"

    def _format_best_moment(self, session_data: Dict) -> Dict[str, str]:
        """Format the best moment highlight"""
        achievements = session_data.get("achievements", [])

        # Find highest dopamine moment
        best = None
        for achievement in achievements:
            if achievement.get("dopamine_level") == "very_high":
                best = achievement
                break

        if not best and achievements:
            best = achievements[0]

        if best:
            return {
                "description": f"when you {self._humanize_achievement(best)}",
                "why_it_matters": self._explain_why_matters(best)
            }

        # Default
        return {
            "description": "when you pushed through that difficult concept",
            "why_it_matters": "it shows you're building real resilience"
        }

    def _humanize_achievement(self, achievement: Dict) -> str:
        """Convert achievement to human-readable description"""
        atype = achievement["achievement_type"]
        concept = achievement.get("concept", "that")

        if atype == "self_correction":
            return f"caught yourself on {concept}"
        elif atype == "breakthrough":
            return f"naturally used {concept} without thinking"
        elif atype == "streak":
            return f"used {concept} perfectly three times in a row"
        elif atype == "speed":
            return f"answered instantly with {concept}"
        else:
            return f"mastered {concept}"

    def _explain_why_matters(self, achievement: Dict) -> str:
        """Explain why this achievement matters"""
        atype = achievement["achievement_type"]

        explanations = {
            "self_correction": "that's the sign you're internalizing the pattern",
            "breakthrough": "that's when learning becomes automatic",
            "streak": "that's consistency, which builds fluency",
            "speed": "that's your brain processing without translation",
            "level_up": "that's real progression in your learning journey"
        }

        return explanations.get(atype, "that's real progress")

    def _determine_next_concept(
        self,
        session_data: Dict,
        user_profile: Optional[Dict]
    ) -> Dict[str, str]:
        """Determine what to teach next"""

        # This would be more sophisticated in production
        # For now, use simple progression logic

        primary = session_data.get("primary_concept", "")

        # Example progression paths
        progressions = {
            "past_tense": {
                "name": "past perfect tense",
                "exciting_outcome": "talk about things you wish you had done differently"
            },
            "ser_vs_estar": {
                "name": "advanced adjective usage",
                "exciting_outcome": "describe subtle differences in how things are vs how they seem"
            },
            "present_tense": {
                "name": "present continuous",
                "exciting_outcome": "talk about what's happening right now in real-time"
            }
        }

        if primary in progressions:
            return progressions[primary]

        # Default
        return {
            "name": "the next level",
            "exciting_outcome": "unlock more natural conversations"
        }

    def _create_personal_hook(
        self,
        next_concept: Dict,
        user_profile: Optional[Dict]
    ) -> str:
        """Create personalized hook based on user interests"""
        if not user_profile:
            return "This is going to be really useful."

        interests = user_profile.get("interests", [])
        profession = user_profile.get("profession")

        # Match interest to concept
        if "travel" in interests:
            return f"Based on your love of travel, {next_concept['name']} will let you tell richer stories about your trips."
        elif "technology" in interests or profession == "software engineer":
            return f"As a tech person, you'll love how {next_concept['name']} adds precision to technical discussions."
        elif "cooking" in interests:
            return f"Since you love cooking, {next_concept['name']} will help you follow recipes and describe techniques better."

        # Default
        return f"You're ready for this and I think you'll really enjoy {next_concept['name']}."
```

#### Step 2: Integrate into Session End

**File:** `backend/routes/realtime_routes.py` (Modify usage log endpoint)

```python
@router.post("/api/realtime/usage-log")
async def log_realtime_usage(
    usage_data: RealtimeUsageData,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # ... existing code ...

    # NEW: Generate exit ritual data
    if current_user and usage_data.session_id:
        async def generate_and_save_exit_ritual():
            try:
                # Get achievement summary
                achievement_summary = achievement_tracker.get_session_summary(usage_data.session_id)

                # Get user profile
                user_doc = await users_collection.find_one({"_id": ObjectId(current_user.id)})
                user_profile = user_doc.get("profile", {}) if user_doc else {}

                # Generate exit ritual
                exit_ritual_service = ExitRitualService()
                ritual_text = exit_ritual_service.generate_exit_ritual(
                    session_data={
                        "achievements": achievement_summary.get("achievements", []),
                        "primary_concept": "past_tense",  # Would extract from session
                        "best_moment": "self-correction"
                    },
                    user_profile=user_profile
                )

                # Save to session record
                await sessions_collection.update_one(
                    {"session_id": usage_data.session_id},
                    {"$set": {"exit_ritual_text": ritual_text}}
                )

                print(f"[EXIT_RITUAL] Generated for session {usage_data.session_id}")

            except Exception as e:
                print(f"[EXIT_RITUAL] Error: {str(e)}")

        background_tasks.add_task(generate_and_save_exit_ritual)

    # ... rest of code ...
```

#### Step 3: Add Exit Ritual to Instructions

**File:** `backend/prompt_optimization_helpers.py`

```python
def build_universal_instructions(request: TutorSessionRequest) -> str:
    """Add exit ritual instructions"""

    # ... existing instructions ...

    exit_ritual_instructions = """

[SESSION EXIT RITUAL]

IMPORTANT: When the session is ending (around 4:30-4:45 mark of a 5-minute session):

Structure your final message as:

1. VICTORY SUMMARY (3 specific things):
   "Alright, amazing session! Today you:
   - [Primary achievement - specific]
   - [Secondary skill improvement]
   - [Learning insight discovered]"

2. HIGHLIGHT MOMENT (1 memorable example):
   "My favorite moment was when you [specific example] - [why it matters]"

   Examples:
   - "...when you caught yourself on 'fui' - that shows you're internalizing it"
   - "...when you used subjunctive naturally - that's advanced for your level"
   - "...when you told that story using only past tense - totally natural"

3. CLIFFHANGER FOR NEXT SESSION (create excitement):
   "Next time: [specific next concept]. [Personal reason based on their interests].
   It's going to unlock [exciting outcome]."

   Examples:
   - "Next time: past perfect. Since you love travel, you'll be able to talk about trips you wish you had taken differently."
   - "Next time: subjunctive mood. This is the 'secret sauce' of sounding like a native speaker."

RULES:
- Be SPECIFIC (not "you did great" but "you mastered past tense through that story about your weekend")
- Make them FEEL progress (reference where they were before)
- Create ANTICIPATION for next session (make next concept sound exciting)
- Keep it BRIEF (30 seconds total)
- End with energy and confidence

DO NOT:
- Give generic praise ("good job")
- List everything they learned (pick 2-3 highlights)
- End abruptly without a proper ritual
- Forget to set up the next session
    """

    instructions = base_instructions + exit_ritual_instructions

    return instructions
```

---

# TIER 2 Implementation

## 4.1 Charismatic Tutor Personality

### Overview
Inject genuine personality, humor, warmth, and cultural references to make the AI memorable and engaging.

### Implementation Steps

#### Step 1: Create Personality Engine

**File:** `backend/services/personality_engine.py`

```python
from typing import Dict, List
import random

class PersonalityEngine:
    """
    Generate personality-infused responses and teaching moments.

    Personality Dimensions:
    1. Humor (wordplay, self-deprecation, playful teasing)
    2. Warmth (empathy, encouragement, vulnerability)
    3. Cultural References (relatable analogies, pop culture)
    """

    HUMOR_LIBRARY = {
        "dad_jokes": [
            "Why did the Spanish verb go to therapy? Too many conjugations!",
            "What's a grammar teacher's favorite drink? Punctuation!",
            "I'd tell you a joke about past tense, but you probably already heard it.",
        ],
        "playful_teasing": [
            "Okay that mistake was creative - I've never heard anyone conjugate THAT way!",
            "Did you just invent a new tense? Because that's not in the textbook!",
            "That's a bold choice! Wrong, but bold!",
        ],
        "self_deprecating": [
            "Even I mess up 'ser vs estar' sometimes - and I'm an AI!",
            "Native speakers get this wrong too - don't feel bad!",
            "This is genuinely hard - I'd struggle with this if I were learning.",
        ]
    }

    WARMTH_LIBRARY = {
        "genuine_excitement": [
            "Okay I'm legitimately excited you got that!",
            "YES! That was SO smooth!",
            "Wait wait wait - did you just use that naturally? That's HUGE!",
        ],
        "empathy": [
            "I know this feels overwhelming right now...",
            "That's frustrating, right? I get it.",
            "This is a tough one - you're not alone in struggling here.",
        ],
        "vulnerability": [
            "Honestly, this confused me when I first learned about it too.",
            "I wish there was an easier way to explain this, but...",
            "Yeah, language is weird sometimes.",
        ]
    }

    def __init__(self):
        pass

    def get_personality_instructions(
        self,
        user_profile: Optional[Dict] = None
    ) -> str:
        """Generate personality-infused instruction block"""

        humor_preference = "neutral"
        if user_profile:
            humor_preference = user_profile.get("conversation_style", {}).get("humor_response", "neutral")

        # Base personality
        personality = """
YOUR PERSONALITY:

You are a passionate, warm, and slightly quirky language tutor with:
- GENUINE excitement about language learning
- A sense of humor (but never at student's expense)
- Empathy for the challenges of learning
- Ability to make vivid analogies and cultural references
        """

        # Adjust based on user preference
        if humor_preference == "loves_puns":
            personality += """
HUMOR STYLE: User loves wordplay!
- Use puns and dad jokes liberally
- Make playful observations about language quirks
- Tease mistakes gently and humorously
- Examples:
  * "Why did the verb break up with the noun? It needed more space... grammatical space!"
  * "That conjugation was... creative! Let's try the version that actually exists."
            """
        elif humor_preference == "no_jokes":
            personality += """
HUMOR STYLE: User prefers professional approach
- Skip jokes and puns
- Use warmth and encouragement instead
- Keep tone supportive but not silly
            """
        else:
            personality += """
HUMOR STYLE: Moderate (gauge their response)
- Use humor occasionally, not constantly
- Watch their reaction - if they laugh, do more
- Balance between professional and playful
            """

        # Add analogy guidance
        profession = user_profile.get("personal_context", {}).get("profession") if user_profile else None

        if profession:
            personality += f"""

ANALOGY STYLE: User is a {profession}
- Make analogies related to their field
- Use professional context to explain grammar
- Connect language patterns to their work

Examples for {profession}:
            """

            # Profession-specific analogies
            if "engineer" in profession.lower() or "developer" in profession.lower():
                personality += """
* "Think of grammatical gender like type systems - it's arbitrary but consistent"
* "Verb conjugation is like function parameters - same action, different contexts"
* "Past tense is like version control - tracking what already happened"
                """
            elif "teacher" in profession.lower():
                personality += """
* "This grammar rule is like classroom management - seems arbitrary but has good reasons"
* "Think of tenses like lesson plans - structuring time and sequence"
                """
            elif "doctor" in profession.lower() or "nurse" in profession.lower():
                personality += """
* "Grammar rules are like anatomy - follow the structure and it all works together"
* "Think of tenses like patient history - present, past, future conditions"
                """

        return personality

    def inject_personality_moment(
        self,
        moment_type: str,
        context: Dict
    ) -> str:
        """Generate personality-infused response for specific moments"""

        if moment_type == "celebration":
            return random.choice(self.WARMTH_LIBRARY["genuine_excitement"])
        elif moment_type == "struggle":
            return random.choice(self.WARMTH_LIBRARY["empathy"])
        elif moment_type == "creative_mistake":
            return random.choice(self.HUMOR_LIBRARY["playful_teasing"])
        elif moment_type == "difficult_concept":
            return random.choice(self.WARMTH_LIBRARY["vulnerability"])

        return ""
```

#### Step 2: Integrate into Instructions

**File:** `backend/routes/realtime_routes.py`

```python
# Modify generate_token to include personality
@router.post("/api/realtime/token")
async def generate_token(request: TutorSessionRequest, current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)):
    # ... existing code ...

    # NEW: Add personality layer
    user_profile = None
    if current_user:
        user_doc = await users_collection.find_one({"_id": ObjectId(current_user.id)})
        user_profile = user_doc.get("profile") if user_doc else None

    personality_engine = PersonalityEngine()
    personality_instructions = personality_engine.get_personality_instructions(user_profile)

    # Build instructions with personality
    base_instructions = build_universal_instructions(request)
    memory_context = # ... (from Tier 1)

    instructions = base_instructions + personality_instructions + memory_context

    # ... rest of code ...
```

---

## 4.2 Smart Recasting (Levels 1-4)

### Overview
Implement sophisticated error correction through natural recasting with escalating levels based on error frequency.

### Implementation Steps

**File:** `backend/services/recasting_service.py`

```python
class RecastingService:
    """
    Multi-level error correction system.

    Levels:
    1. Invisible Recasting: Minor errors, maintain flow
    2. Emphasized Recasting: Repeated error, gentle highlight
    3. Pattern Explanation: Persistent error, teach the pattern
    4. Curious Question: Understand root cause
    """

    def __init__(self):
        self.session_errors = {}  # Track errors during session

    def determine_recasting_level(
        self,
        session_id: str,
        error_type: str,
        user_learning_history: Dict
    ) -> int:
        """Determine which recasting level to use"""

        # Check session frequency
        session_key = f"{session_id}:{error_type}"
        session_count = self.session_errors.get(session_key, 0)
        self.session_errors[session_key] = session_count + 1

        # Check historical frequency
        persistent_mistakes = user_learning_history.get("persistent_mistakes", [])
        historical_count = 0
        for mistake in persistent_mistakes:
            if mistake.get("error_type") == error_type:
                historical_count = mistake.get("occurrences", 0)
                break

        # Determine level
        if session_count == 1 and historical_count < 3:
            return 1  # Invisible recasting
        elif session_count <= 2 and historical_count < 5:
            return 2  # Emphasized recasting
        elif session_count >= 3 or historical_count >= 5:
            return 3  # Pattern explanation
        else:
            return 4  # Curious question

    def get_recasting_instructions(self, level: int, error_context: Dict) -> str:
        """Get instructions for specific recasting level"""

        error_type = error_context.get("error_type", "that")
        user_utterance = error_context.get("user_utterance", "")
        correct_form = error_context.get("correct_form", "")

        if level == 1:
            return f"""
LEVEL 1 - INVISIBLE RECASTING:
User said: "{user_utterance}"
Correct naturally in your response without emphasis:
"Oh nice! [Restate using correct form naturally]. [Continue conversation]"

Example:
User: "Yesterday I go to store"
You: "Oh nice! What did you buy when you went to the store?"
[Corrected 'go' to 'went' naturally, no emphasis]
            """

        elif level == 2:
            return f"""
LEVEL 2 - EMPHASIZED RECASTING:
User said: "{user_utterance}" (repeated error with {error_type})
Gently emphasize the correct form:
"Ah, so you WENT to the store - what'd you get?"
[Emphasize correct form with vocal stress, but keep conversational]
            """

        elif level == 3:
            return f"""
LEVEL 3 - PATTERN EXPLANATION:
User keeps making {error_type} error
Time to teach the pattern:
"Okay I'm noticing something with {error_type}. [Brief explanation of rule].
Can you try: '{correct_form}'?"

Example:
"I'm noticing you're using 'go' for past events. In English, past actions
use 'went' (it's irregular, which is annoying!). Can you try:
'Yesterday I went to the store'?"
            """

        elif level == 4:
            return f"""
LEVEL 4 - CURIOUS QUESTION:
User error pattern suggests deeper confusion
Ask diagnostic question:
"Interesting - what made you use [incorrect form] instead of [correct form]?
I'm curious about your thinking."

This helps understand their mental model and correct the root cause.
            """

        return ""
```

#### Integration into Instructions

```python
# Add to prompt_optimization_helpers.py

def build_universal_instructions(request: TutorSessionRequest) -> str:
    # ... existing code ...

    recasting_instructions = """

[SMART RECASTING - ERROR CORRECTION LEVELS]

CRITICAL: You must adapt your error correction based on error frequency.

LEVEL 1 - INVISIBLE RECASTING (first occurrence, minor error):
- Correct naturally in your response
- NO emphasis, NO explicit correction
- Just model the correct form
User: "Yesterday I go to park"
You: "Nice! What did you do at the park when you went?"

LEVEL 2 - EMPHASIZED RECASTING (2nd-3rd occurrence):
- Vocally emphasize the correct form
- Still conversational, not drill-like
User: "Yesterday I go to park" [3rd time]
You: "Ah, so you WENT to the park. Tell me more!"

LEVEL 3 - PATTERN EXPLANATION (persistent error):
- Stop and teach the pattern
- Brief explanation + example
- Ask them to try it
User: [Makes same error 4+ times]
You: "Okay let's pause on this. When talking about the past,
     'go' becomes 'went'. It's irregular. Try: 'Yesterday I went...'"

LEVEL 4 - CURIOUS QUESTION (confusion about root cause):
- Ask why they're making the error
- Understand their mental model
User: [Makes unusual error pattern]
You: "Interesting - what made you use 'go' there? I'm curious."

AUTOMATIC ESCALATION:
- 1st error: Level 1
- 2nd-3rd error in session: Level 2
- 4+ times in session OR persistent across sessions: Level 3
- Unusual pattern or fundamental misunderstanding: Level 4

NEVER:
- Drill ("Repeat after me")
- Shame ("That's wrong")
- Over-correct (every tiny mistake)
- Stay at wrong level (escalate when needed)
    """

    instructions = base_instructions + recasting_instructions
    return instructions
```

---

## 4.3 Interrupt Intelligence

### Overview
Handle interruptions naturally with human-like backchannel responses.

### Implementation

**File:** `backend/services/interruption_handler.py`

```python
class InterruptionHandler:
    """
    Classify and respond to interruptions naturally.

    Types:
    - Question (urgent clarification needed)
    - Confusion (user lost)
    - Excitement (breakthrough moment)
    - Thinking Pause (user processing)
    """

    BACKCHANNEL_RESPONSES = {
        "question": [
            "Oh! Great question -",
            "Ah yes, so",
            "Let me explain that -",
        ],
        "confusion": [
            "Okay let's slow down -",
            "No worries, let me rephrase -",
            "Hmm, let me try a different way -",
        ],
        "excitement": [
            "Exactly!",
            "Yes! You got it!",
            "Right?!",
        ],
        "thinking_pause": [
            "Take your time...",
            "Thinking it through? That's good!",
            "[patient silence]",
        ]
    }

    def classify_interruption(self, user_speech: str, context: Dict) -> str:
        """Classify type of interruption"""

        lower_speech = user_speech.lower()

        # Question markers
        if any(word in lower_speech for word in ["what", "why", "how", "can you", "wait"]):
            return "question"

        # Confusion markers
        if any(word in lower_speech for word in ["huh", "confused", "don't understand", "lost"]):
            return "confusion"

        # Excitement markers
        if any(word in lower_speech for word in ["oh!", "yes!", "i see", "got it", "ah!"]):
            return "excitement"

        # Thinking pause (empty or very short)
        if len(user_speech.strip()) < 3:
            return "thinking_pause"

        return "question"  # default

    def get_backchannel_response(self, interruption_type: str) -> str:
        """Get natural backchannel response"""
        import random
        responses = self.BACKCHANNEL_RESPONSES.get(interruption_type, ["So,"])
        return random.choice(responses)
```

**Add to Instructions:**

```python
# In prompt_optimization_helpers.py

interruption_instructions = """

[INTERRUPT INTELLIGENCE - BACKCHANNEL RESPONSES]

When user interrupts you, respond naturally like a human would:

INTERRUPTION TYPE: QUESTION
User: "Wait, what does 'estar' mean?"
You: [STOP IMMEDIATELY] "Oh! Great question - 'estar' is for temporary states..."
[Enthusiastic, immediate answer]

INTERRUPTION TYPE: CONFUSION
User: "Huh? I'm lost"
You: [STOP IMMEDIATELY] "Okay let's slow down - [rephrase simply]"
[Patient, supportive]

INTERRUPTION TYPE: EXCITEMENT
User: "Oh I see!"
You: [STOP] "Exactly!" [Brief acknowledgment then continue]
[Match their energy]

INTERRUPTION TYPE: THINKING PAUSE
User: "Umm..." [long pause]
You: [WAIT 3 seconds] "Take your time..."
[Patient, non-verbal encouragement]

RULES:
- ALWAYS stop talking immediately when interrupted
- Classify interruption type instantly
- Respond with appropriate backchannel phrase
- Then address their need

This makes you feel responsive and human, not robotic.
"""
```

---

# TIER 3 Implementation

## 5.1 Voice Mirroring

**File:** `backend/services/voice_mirroring_service.py`

```python
class VoiceMirroringService:
    """
    Detect and mirror user's speech patterns.

    Analyzes:
    - Speaking speed (WPM)
    - Energy level
    - Formality ("yeah" vs "yes")
    - Sentence length preference
    """

    def analyze_voice_profile(self, transcript: str, audio_duration: float) -> Dict:
        """Analyze user's speaking style from first minute"""

        words = transcript.split()
        word_count = len(words)

        # Calculate speed
        wpm = (word_count / audio_duration) * 60
        speed = "slow" if wpm < 100 else "moderate" if wpm < 140 else "fast"

        # Detect formality
        casual_markers = ["yeah", "yup", "gonna", "wanna", "kinda"]
        formal_markers = ["yes", "certainly", "going to", "want to"]

        casual_count = sum(1 for word in words if word.lower() in casual_markers)
        formal_count = sum(1 for word in words if word.lower() in formal_markers)

        formality = "casual" if casual_count > formal_count else "formal"

        # Detect sentence length preference
        sentences = transcript.split(".")
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

        sentence_pref = "short" if avg_sentence_length < 8 else "moderate" if avg_sentence_length < 15 else "long"

        return {
            "speed": speed,
            "formality": formality,
            "sentence_length": sentence_pref,
            "wpm": wpm
        }

    def get_mirroring_instructions(self, voice_profile: Dict) -> str:
        """Generate instructions to mirror user's style"""

        return f"""
[VOICE MIRRORING]

User's speaking style detected:
- Speed: {voice_profile['speed']} ({voice_profile['wpm']} WPM)
- Formality: {voice_profile['formality']}
- Sentence length: {voice_profile['sentence_length']}

ADAPT YOUR STYLE:
- Match their speaking speed (speak {voice_profile['speed']})
- Use {'casual language' if voice_profile['formality'] == 'casual' else 'professional language'}
- Use {voice_profile['sentence_length']} sentences like they do

This makes conversation feel natural and comfortable for them.
        """
```

## 5.2 Curiosity Following

```python
# Add to instructions

curiosity_instructions = """

[CURIOSITY-DRIVEN LEARNING]

When user mentions ANY topic they're interested in or excited about:

1. DETECT INTEREST SIGNALS:
   - "I've been reading about..."
   - "I love..."
   - "I'm working on..."
   - Enthusiasm in voice
   - Elaborates without prompting

2. PIVOT TO THAT TOPIC:
   "Oh that's interesting! Let's practice using THAT topic instead.
    Tell me in [target language]: [question about their interest]"

3. BUILD ENTIRE SESSION AROUND IT:
   - Use their passion as practice material
   - Keep them engaged with personally relevant content
   - They'll learn more because they care about the topic

EXAMPLES:
User mentions cooking → Practice food vocabulary through recipe discussion
User mentions job project → Use work context for grammar practice
User mentions travel plans → Practice future tense planning the trip

RULE: Personal relevance > generic lesson plans
"""
```

## 5.3 Transparent Teaching

```python
# Add to instructions

transparent_teaching_instructions = """

[TRANSPARENT TEACHING - META-AWARENESS]

Explain WHAT you're doing and WHY:

BEFORE TECHNIQUE CHANGE:
"Okay I'm going to try something new now. For the next 90 seconds,
 I'll only speak in [target language]. This is called 'immersion practice' -
 it trains your brain to think IN the language, not translate.
 If you get lost, just say 'English' and I'll switch back. Ready?"

WHEN GIVING FEEDBACK:
"I'm going to give you feedback in 'sandwich method' -
 one thing you did great, one thing to improve, one thing you did great.
 It helps you hear corrections without feeling discouraged."

WHEN CHALLENGING THEM:
"I'm going to make this harder now because you're ready for it.
 This might feel uncomfortable - that's the sign of growth."

BENEFITS:
- User feels in control
- Understands the pedagogy
- Trusts your methods
- Can advocate for their preferences

RULE: Be transparent about your teaching decisions.
"""
```

## 5.4 Intelligent Silence

```python
# Modify turn_detection config in realtime_routes.py

"turn_detection": {
    "type": "semantic_vad",
    "eagerness": "low",  # Already doing this
    "create_response": False,  # Manual control for intelligent waiting
    "interrupt_response": True
}

# Add to instructions

intelligent_silence_instructions = """

[INTELLIGENT SILENCE - PATIENCE WITH THINKING]

When user pauses mid-sentence:

PHASE 1 (0-3 seconds):
- WAIT SILENTLY
- They're thinking - this is good!
- Don't interrupt their processing

PHASE 2 (3-5 seconds):
- Give non-verbal encouragement: "Mm-hmm" or "Take your time..."
- Still don't rush them

PHASE 3 (5-8 seconds):
- Offer gentle help: "Want a hint?" or "Should I rephrase the question?"
- Give them option to ask for help

PHASE 4 (8+ seconds):
- Provide scaffold: "How about we try [easier version]?"
- Or suggest moving on: "Want to come back to this?"

CRITICAL:
- Silence = learning (they're processing)
- Don't fill every pause
- Give them space to think
- Patience builds confidence

NEVER:
- Interrupt thinking pauses
- Rush them
- Make them feel slow
- Fill silence just because it's there
"""
```

---

# Integration Guide

## Step-by-Step Integration Order

### Week 1-2: TIER 1 Foundation

**Day 1-3:**
1. Set up database schema extensions (UserProfile, SessionExtended)
2. Create MemoryService
3. Test memory extraction with sample conversations

**Day 4-7:**
4. Integrate memory into session start (realtime_routes.py)
5. Create AchievementTrackerService
6. Add achievement function to Realtime API payload

**Day 8-10:**
7. Create ExitRitualService
8. Integrate exit ritual generation
9. Test end-to-end Tier 1 flow

**Day 11-14:**
10. Add all Tier 1 instructions to prompt
11. Test with beta users
12. Collect feedback and iterate

### Week 3-4: TIER 2 Enhancement

**Day 1-5:**
1. Create PersonalityEngine
2. Create RecastingService
3. Create InterruptionHandler
4. Integrate all three services

**Day 6-10:**
5. Add Tier 2 instructions
6. Test personality variations
7. Test recasting escalation
8. Test interruption handling

**Day 11-14:**
9. Beta testing with real users
10. Collect engagement metrics
11. Iterate based on feedback

### Week 5-6: TIER 3 Polish

**Day 1-7:**
1. Create VoiceMirroringService
2. Add curiosity following detection
3. Add transparent teaching phrases
4. Tune VAD for intelligent silence

**Day 8-14:**
5. Full integration testing
6. A/B testing against baseline
7. Final polish and deployment

---

# Testing Strategy

## Unit Tests

```python
# tests/test_memory_service.py
def test_build_personal_context():
    service = MemoryService()
    context = service._build_personal_context({
        "profession": "software engineer",
        "interests": ["hiking", "cooking"]
    })
    assert "software engineer" in context[0]
    assert "hiking" in context[1]

# tests/test_achievement_tracker.py
def test_detect_streak():
    tracker = AchievementTrackerService()
    tracker.initialize_session("session_1", {})

    # Simulate 3 correct uses
    for i in range(3):
        result = tracker.detect_achievement(
            "session_1",
            "correct_usage",
            {"concept": "past_tense", "is_correct": True}
        )

    # Should trigger streak achievement on 3rd
    assert result is not None
    assert result["achievement_type"] == "streak"
```

## Integration Tests

```python
# tests/integration/test_tier1_flow.py
async def test_full_session_with_memory():
    """Test complete flow from session start to exit ritual"""

    # 1. Create session with memory
    token_response = await client.post("/api/realtime/token", json={
        "language": "spanish",
        "level": "B1",
        "topic": "travel"
    })

    # 2. Verify memory context in instructions
    assert "software engineer" in token_response.json()["instructions"]

    # 3. Simulate session events
    # ... (achievement triggers, etc.)

    # 4. End session and verify exit ritual generated
    usage_response = await client.post("/api/realtime/usage-log", json={
        "session_id": session_id,
        "transcript": "..."
    })

    # 5. Verify exit ritual saved
    session_doc = await sessions_collection.find_one({"session_id": session_id})
    assert "exit_ritual_text" in session_doc
```

## User Acceptance Testing

**Metrics to track:**
1. **Memory Accuracy**: Do users feel "remembered"?
2. **Achievement Engagement**: How many dopamine moments per session?
3. **Exit Ritual Impact**: Do users return for next session?
4. **Personality Reception**: Do users comment on tutor's personality?
5. **Overall Satisfaction**: NPS score improvement

**Test scenarios:**
- New user (no memory) → Verify graceful defaults
- Returning user (rich memory) → Verify personalization
- Error-prone user → Verify recasting escalation
- High-engagement user → Verify achievement celebrations

---

# Rollout Plan

## Phase 1: Alpha (Internal Testing)
- Team members test all features
- Fix critical bugs
- Tune thresholds (achievement frequency, recasting levels)

## Phase 2: Beta (50 Users)
- Invite power users
- A/B test: 25 with features, 25 without
- Collect detailed feedback
- Measure engagement metrics

## Phase 3: Gradual Rollout (10% → 50% → 100%)
- Monitor error rates
- Watch for performance issues
- Iterate based on real usage patterns

## Phase 4: Full Launch
- All users get standout features
- Marketing campaign highlighting differentiation
- Monitor success metrics

---

# Success Metrics

## Tier 1 Metrics

**Memory:**
- % of sessions where memory is referenced
- User feedback: "Does the AI remember you?" survey
- Session-to-session retention rate

**Achievements:**
- Average achievements per session (target: 3-5)
- % of sessions with at least one "very_high" dopamine moment
- User comments mentioning progress/celebration

**Exit Ritual:**
- % of users who return for next session (target: +15%)
- Time to next session (target: decrease by 20%)
- User ratings of session endings

## Tier 2 Metrics

**Personality:**
- User comments mentioning personality/humor
- Session enjoyment ratings (target: +10%)
- Brand differentiation scores

**Recasting:**
- Error correction effectiveness (% of errors not repeated)
- User frustration scores (target: decrease)
- Learning speed (concepts mastered per session)

**Interruptions:**
- Interruption handling satisfaction
- Flow disruption scores (target: decrease)

## Tier 3 Metrics

**Voice Mirroring:**
- User comfort ratings
- Conversation naturalness scores

**Curiosity Following:**
- % of sessions with topic pivots
- Engagement during personal topic sessions vs generic

**Overall Impact:**
- NPS score improvement
- Paid conversion rate improvement
- Average sessions per user improvement
- Churn rate reduction

---

# Appendix: Configuration Reference

## Environment Variables

```bash
# Existing
OPENAI_API_KEY=sk-...
OPENAI_REALTIME_MODEL=gpt-realtime-mini-2025-12-15

# New for standout features
ACHIEVEMENT_CELEBRATION_FREQUENCY=moderate  # low, moderate, high
PERSONALITY_MODE=warm_encouraging  # warm_encouraging, playful_humorous, professional_direct
MEMORY_EXTRACTION_ENABLED=true
EXIT_RITUAL_ENABLED=true
VOICE_MIRRORING_ENABLED=false  # Phase 3 feature
```

## Feature Flags

```python
# backend/config/feature_flags.py

FEATURE_FLAGS = {
    "tier1_memory": True,
    "tier1_achievements": True,
    "tier1_exit_ritual": True,

    "tier2_personality": True,
    "tier2_recasting": True,
    "tier2_interruption": True,

    "tier3_voice_mirroring": False,  # Not ready yet
    "tier3_curiosity": False,
    "tier3_transparent_teaching": False,
    "tier3_intelligent_silence": False,
}

def is_feature_enabled(feature_name: str) -> bool:
    return FEATURE_FLAGS.get(feature_name, False)
```

---

# Next Steps

1. **Review this document** with the team
2. **Prioritize Tier 1** for immediate implementation
3. **Set up project tracking** (Jira/Linear/etc.)
4. **Assign ownership** for each service
5. **Begin implementation** starting with database schema
6. **Test incrementally** - don't wait for everything to be done
7. **Collect user feedback early** - beta test as soon as Tier 1 is ready

---

**Document maintained by:** Engineering Team
**Last updated:** 2026-01-11
**Status:** Ready for Implementation

**Questions?** Review the Implementation Steps sections for detailed code and integration guidance.
