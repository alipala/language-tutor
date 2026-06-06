"""
Session Summary Routes
Handles learning session summary generation and storage
"""

import os
import json
import logging
import traceback
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from pydantic import BaseModel
from bson import ObjectId
from openai_client import get_async_openai

from auth import get_current_user
from models import UserResponse, get_session_xp
from session_statistics import SessionStatistics
from cache_helpers import invalidate_coach_context_smart  # PHASE 4.2: Smart cache invalidation
from services.timezone_utils import get_current_local_date
from database import users_collection

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()



# ──────────────────────────────────────────────────────────────────────────────
# Structured session summary — gpt-4.1-mini via function calling
# ──────────────────────────────────────────────────────────────────────────────

_STRUCTURED_SUMMARY_FUNCTION: Dict[str, Any] = {
    "name": "store_session_summary",
    "description": (
        "Store a structured analysis of a language learning session "
        "including vocabulary, corrections, and learner confidence."
    ),
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "vocabulary_practiced": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Up to 8 key words or phrases the learner used or encountered."
            },
            "corrections_made": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "wrong": {"type": "string"},
                        "correct": {"type": "string"},
                        "tip": {"type": "string"}
                    },
                    "required": ["wrong", "correct", "tip"],
                    "additionalProperties": False
                },
                "description": "Up to 5 grammar/vocabulary corrections identified in the session."
            },
            "topics_covered": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Main topics or themes discussed (max 4)."
            },
            "student_confidence": {
                "type": "string",
                "enum": ["low", "building", "moderate", "high"],
                "description": "Estimated confidence level based on participation and hesitation."
            },
            "breakthrough_moment": {
                "type": "string",
                "description": "One specific positive moment or achievement from the session (empty string if none)."
            },
            "focus_next_session": {
                "type": "string",
                "description": "One concrete area the tutor should reinforce in the next session."
            },
            "compressed_summary": {
                "type": "string",
                "description": (
                    "Single sentence (max 20 words) describing what was practised and "
                    "the main takeaway. Format: '[topic/skill] — [key outcome]'."
                )
            }
        },
        "required": [
            "vocabulary_practiced",
            "corrections_made",
            "topics_covered",
            "student_confidence",
            "breakthrough_moment",
            "focus_next_session",
            "compressed_summary"
        ],
        "additionalProperties": False
    }
}


def _build_structured_summary_prompt(
    language: str,
    level: str,
    week_focus: str,
    session_number: int,
    messages: List[Dict[str, Any]],
    basic_summary: Optional[str],
    key_vocabulary: Optional[List[str]],
    key_phrases: Optional[List[str]],
) -> str:
    """Build the prompt for gpt-4.1-mini structured session analysis."""
    # Extract last 20 conversation turns to keep prompt focused
    recent_messages = messages[-20:] if messages else []
    conversation_lines = []
    for msg in recent_messages:
        role = "Student" if msg.get("role") == "user" else "Tutor"
        content = str(msg.get("content", "")).strip()
        if content:
            conversation_lines.append(f"{role}: {content}")
    conversation_block = "\n".join(conversation_lines) if conversation_lines else "(no transcript available)"

    vocab_hint = ""
    if key_vocabulary:
        vocab_hint = f"\nPlan vocabulary for this week: {', '.join(key_vocabulary[:10])}"
    if key_phrases:
        vocab_hint += f"\nPlan phrases for this week: {', '.join(key_phrases[:5])}"

    return f"""Analyse this {language} language learning session (Session {session_number}).

STUDENT LEVEL: {level}
WEEK FOCUS: {week_focus}{vocab_hint}

BASIC SESSION INFO:
{basic_summary or '(not available)'}

CONVERSATION TRANSCRIPT:
{conversation_block}

Identify:
- Vocabulary the student actually used or struggled with
- Grammar/vocabulary errors made and their corrections
- Topics actually discussed
- Student's confidence based on response length, hesitation, and engagement
- Any breakthrough moment (first successful use of a hard word, unexpected fluency, etc.)
- What the tutor should prioritise in the NEXT session to build continuity
- A one-sentence compressed summary for the tutor's memory in future sessions
"""


async def generate_structured_session_summary(
    plan: Dict[str, Any],
    conversation_data: Optional[Dict[str, Any]],
    basic_summary: Optional[str],
    session_number: int,
    plan_id: str,
) -> Dict[str, Any]:
    """
    Generate a rich structured session summary using gpt-4.1-mini.

    Returns a dict with all structured fields.  Falls back to a minimal
    default dict on any error so the caller never has to handle None.
    """
    language = plan.get("language", "english")
    level = plan.get("proficiency_level", "B1")
    sessions_per_week = 4
    week_index = (session_number - 1) // sessions_per_week
    weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
    current_week = weekly_schedule[week_index] if week_index < len(weekly_schedule) else {}
    week_focus = current_week.get("focus", "General language practice")
    key_vocabulary: List[str] = current_week.get("key_vocabulary", [])
    key_phrases: List[str] = current_week.get("key_phrases", [])

    messages: List[Dict[str, Any]] = (
        conversation_data.get("messages", []) if conversation_data else []
    )

    # Fallback used when API call fails or returns incomplete data
    _fallback = {
        "vocabulary_practiced": [],
        "corrections_made": [],
        "topics_covered": [week_focus],
        "student_confidence": "building",
        "breakthrough_moment": "",
        "focus_next_session": week_focus,
        "compressed_summary": (
            basic_summary[:100] if basic_summary else f"{week_focus} — session {session_number} completed"
        ),
        "_generated_by": "fallback",
    }

    try:
        prompt = _build_structured_summary_prompt(
            language=language,
            level=level,
            week_focus=week_focus,
            session_number=session_number,
            messages=messages,
            basic_summary=basic_summary,
            key_vocabulary=key_vocabulary,
            key_phrases=key_phrases,
        )

        response = await get_async_openai().chat.completions.create(
            model="gpt-4.1-mini",
            tools=[{"type": "function", "function": _STRUCTURED_SUMMARY_FUNCTION}],
            tool_choice={"type": "function", "function": {"name": "store_session_summary"}},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert language learning session analyst. "
                        "Analyse the conversation transcript and produce a concise, "
                        "actionable structured summary that the AI tutor can use "
                        "in the next session to maintain continuity."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=700,
        )

        tool_calls = (
            response.choices[0].message.tool_calls
            if response.choices and response.choices[0].message.tool_calls
            else []
        )
        if not tool_calls:
            logger.warning("[STRUCTURED_SUMMARY] No tool_calls in gpt-4.1-mini response — fallback")
            return _fallback

        structured = json.loads(tool_calls[0].function.arguments)

        # Validate required fields exist
        required_keys = {
            "vocabulary_practiced", "corrections_made", "topics_covered",
            "student_confidence", "breakthrough_moment",
            "focus_next_session", "compressed_summary",
        }
        missing = required_keys - structured.keys()
        if missing:
            logger.warning(f"[STRUCTURED_SUMMARY] Missing fields {missing} — merging with fallback")
            structured = {**_fallback, **structured}

        structured["_generated_by"] = "gpt-4.1-mini"
        structured["generated_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(
            f"[STRUCTURED_SUMMARY] ✅ Generated for session {session_number}: "
            f"vocab={len(structured['vocabulary_practiced'])}, "
            f"corrections={len(structured['corrections_made'])}, "
            f"confidence={structured['student_confidence']}"
        )
        return structured

    except json.JSONDecodeError as e:
        logger.warning(f"[STRUCTURED_SUMMARY] JSON parse error: {e} — fallback")
    except (IndexError, AttributeError, KeyError) as e:
        logger.warning(f"[STRUCTURED_SUMMARY] Unexpected response shape: {e} — fallback")
    except Exception as e:
        logger.warning(f"[STRUCTURED_SUMMARY] gpt-4.1-mini call failed: {e} — fallback")

    return _fallback


async def _generate_and_persist_structured_summary_background(
    plan_id: str,
    session_number: int,
    plan: Dict[str, Any],
    conversation_data: Optional[Dict[str, Any]],
    basic_summary: Optional[str],
) -> None:
    """
    Generate structured summary via GPT (async, off the hot path) then persist it.
    Runs as a background task so the session-summary response is not blocked.
    """
    try:
        structured_summary = await generate_structured_session_summary(
            plan=plan,
            conversation_data=conversation_data,
            basic_summary=basic_summary,
            session_number=session_number,
            plan_id=plan_id,
        )
        logger.info(
            f"[STRUCTURED_SUMMARY_BG] ✅ Generated for plan {plan_id} session {session_number}: "
            f"summary_len={len(structured_summary.get('compressed_summary', ''))}"
        )
    except Exception as gen_err:
        logger.warning(f"[STRUCTURED_SUMMARY_BG] ⚠️ Generation failed, using fallback: {gen_err}")
        week_focus = plan.get("plan_content", {}).get("weekly_schedule", [{}])[
            max(0, (session_number - 1) // 4)
        ].get("focus", "General language practice")
        structured_summary = {
            "compressed_summary": (
                basic_summary[:120] if basic_summary else f"Session {session_number} completed."
            ),
            "breakthrough_moment": "",
            "focus_next_session": week_focus,
            "_generated_by": "fallback_bg",
        }

    await _persist_structured_summary_background(
        plan_id=plan_id,
        session_number=session_number,
        structured_summary=structured_summary,
    )


async def _persist_structured_summary_background(
    plan_id: str,
    session_number: int,
    structured_summary: Dict[str, Any],
) -> None:
    """
    Persist the structured summary onto the correct week's session_details entry
    inside the learning plan document.

    Runs as a background task — any failure is logged but does NOT affect
    the session response already sent to the client.
    """
    try:
        from database import database
        plans_collection = database.learning_plans

        plan = await plans_collection.find_one({"id": plan_id}, {"plan_content": 1})
        if not plan:
            logger.warning(f"[STRUCTURED_SUMMARY_PERSIST] Plan {plan_id} not found")
            return

        weekly_schedule: List[Dict[str, Any]] = (
            plan.get("plan_content", {}).get("weekly_schedule", [])
        )

        sessions_per_week = 4
        week_index = (session_number - 1) // sessions_per_week
        session_in_week = ((session_number - 1) % sessions_per_week)  # 0-based index

        if week_index >= len(weekly_schedule):
            logger.warning(
                f"[STRUCTURED_SUMMARY_PERSIST] Week index {week_index} out of range "
                f"(schedule has {len(weekly_schedule)} weeks)"
            )
            return

        week = weekly_schedule[week_index]
        session_details: List[Dict[str, Any]] = week.get("session_details", [])

        if session_in_week < len(session_details):
            session_details[session_in_week]["structured_summary"] = structured_summary
            session_details[session_in_week]["structured_summary_at"] = (
                datetime.now(timezone.utc).isoformat()
            )
        else:
            # session_details entry missing — append one
            session_details.append({
                "session_number": session_in_week + 1,
                "structured_summary": structured_summary,
                "structured_summary_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(
                f"[STRUCTURED_SUMMARY_PERSIST] Appended missing session_details entry "
                f"for week {week_index + 1}, session {session_in_week + 1}"
            )

        weekly_schedule[week_index]["session_details"] = session_details

        result = await plans_collection.update_one(
            {"id": plan_id},
            {"$set": {"plan_content.weekly_schedule": weekly_schedule}},
        )
        if result.modified_count:
            logger.info(
                f"[STRUCTURED_SUMMARY_PERSIST] ✅ Persisted structured summary for "
                f"plan {plan_id}, session {session_number}"
            )
        else:
            logger.warning(
                f"[STRUCTURED_SUMMARY_PERSIST] ⚠️ Update matched but modified 0 docs "
                f"for plan {plan_id}"
            )

    except Exception as e:
        logger.error(
            f"[STRUCTURED_SUMMARY_PERSIST] ❌ Failed for plan {plan_id}, "
            f"session {session_number}: {e}\n{traceback.format_exc()}"
        )

# ──────────────────────────────────────────────────────────────────────────────
# Background task functions — run AFTER response is sent to the client
# ──────────────────────────────────────────────────────────────────────────────

async def _update_journey_state_background(user_id: str):
    """
    Update user's journey state after session completion.

    This runs in the background to avoid blocking the session summary response.
    """
    try:
        from services.journey_state_detector import journey_state_detector

        print(f"[JOURNEY_BG] Updating journey state for user {user_id}")
        journey_state = await journey_state_detector.detect_journey_stage(
            user_id,
            force_recalculate=True  # Force update after session
        )
        print(f"[JOURNEY_BG] ✅ Journey state updated: {journey_state.stage}")
    except Exception as e:
        print(f"[JOURNEY_BG] ❌ Error updating journey state: {str(e)}")
        # Non-critical, don't fail the session

async def _generate_flashcards_background(
    plan_id: str, completed_sessions: int, language: str, level: str,
    topic, summary_text: str, user_id: str
):
    """Generate and persist flashcards without blocking the session-summary response."""
    try:
        from flashcard_service import FlashcardService
        from models import FlashcardGenerationRequest
        from database import database

        session_id = f"learning_plan_{plan_id}_{completed_sessions}_{uuid.uuid4()}"
        req = FlashcardGenerationRequest(
            session_id=session_id,
            language=language,
            level=level,
            topic=topic,
            conversation_content=None,
            session_summary=summary_text,
            count=5,
        )
        print(f"[FLASHCARD_BG] Generating flashcards for session {completed_sessions}")
        flashcard_set = await FlashcardService.generate_flashcards(req, user_id)
        if flashcard_set and flashcard_set.flashcards:
            set_doc = flashcard_set.dict()
            set_doc["_id"] = ObjectId()
            set_doc["created_at"] = datetime.now(timezone.utc)
            card_docs = [dict(**c.dict(), _id=ObjectId()) for c in flashcard_set.flashcards]
            await database.flashcard_sets.insert_one(set_doc)
            if card_docs:
                result = await database.flashcards.insert_many(card_docs)
                print(f"[FLASHCARD_BG] ✅ Saved {len(result.inserted_ids)} flashcards")
        else:
            print(f"[FLASHCARD_BG] ⚠️ Empty result from flashcard generation")
    except Exception as e:
        print(f"[FLASHCARD_BG] ❌ Failed: {e}\n{traceback.format_exc()}")


async def _run_sentence_analysis_background(
    job_id: str,
    user_id: str,
    plan_id: str,
    session_id: str,
    sentences_for_analysis: list,
    language: str,
    level: str
):
    """
    Background task: Run sentence analysis and store results.

    This runs AFTER the session summary response is sent to user.
    Updates the analysis job document with results when complete.
    """
    from database import database
    import logging

    logger = logging.getLogger(__name__)
    jobs_collection = database.sentence_analysis_jobs

    try:
        # Update status to processing
        await jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "processing",
                    "started_at": datetime.now(timezone.utc)
                }
            }
        )
        print(f"[SENTENCE_ANALYSIS_BG] 🔄 Job {job_id} started processing")

        # Pair each sentence with its quality score so we can pick the strongest
        # examples first. Mobile sends `qualityScore` (camelCase); be defensive
        # for older payloads that might use snake_case.
        def _score(item):
            if isinstance(item, dict):
                qs = item.get('qualityScore')
                if qs is None:
                    qs = item.get('quality_score')
                try:
                    return float(qs) if qs is not None else 0.0
                except (TypeError, ValueError):
                    return 0.0
            return 0.0

        # SPEED: analyze the top 3 sentences by quality_score (desc) instead of
        # all available. Job completes faster so mobile's review readiness
        # window catches it inline. If fewer than 3 exist, analyze all.
        TOP_N_FOR_ANALYSIS = 3
        scored_items = [
            (s, _score(s)) for s in sentences_for_analysis
            if isinstance(s, dict) and s.get('text')
        ]
        if len(scored_items) > TOP_N_FOR_ANALYSIS:
            scored_items.sort(key=lambda pair: pair[1], reverse=True)
            scored_items = scored_items[:TOP_N_FOR_ANALYSIS]
        sentence_texts = [item.get('text') for item, _ in scored_items]

        if not sentence_texts:
            # No sentences to analyze
            await jobs_collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc),
                        "analyses": []
                    }
                }
            )
            print(f"[SENTENCE_ANALYSIS_BG] ✅ Job {job_id} completed (no sentences)")
            return

        # Run batch analysis (single GPT-4o-mini call; top-3 cap keeps it fast)
        from background_sentence_analysis import batch_analyze_sentences

        print(f"[SENTENCE_ANALYSIS_BG] 🔍 Analyzing {len(sentence_texts)} sentences (top-{TOP_N_FOR_ANALYSIS} by quality)...")
        analyses = await batch_analyze_sentences(
            sentences=sentence_texts,
            language=language,
            level=level
        )

        # Convert to dict format
        analyses_dict = [a.dict() for a in analyses]

        # Update job with completed analyses
        await jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc),
                    "analyses": analyses_dict
                }
            }
        )

        print(f"[SENTENCE_ANALYSIS_BG] ✅ Job {job_id} completed: {len(analyses)} sentences analyzed")

        # 🎯 Create TaalCoach notification for user (same as practice sessions)
        print(f"[TAALCOACH_NOTIFY] 🚀 STARTING notification creation for session {session_id}, user {user_id}")
        try:
            print(f"[TAALCOACH_NOTIFY] 🔍 Inside try block, about to import...")
            from database import user_notifications_collection, notifications_collection
            from bson import ObjectId
            import asyncio

            # ⏱️ Small delay to ensure MongoDB write propagation (prevent race condition)
            await asyncio.sleep(0.5)

            # ✅ Verify analyses were truly saved before creating notification
            verification_job = await jobs_collection.find_one({"job_id": job_id})
            if not verification_job or not verification_job.get("analyses"):
                print(f"[TAALCOACH_NOTIFY] ⚠️ Analyses not found in database, skipping notification")
                return

            # Step 1: Create notification in notifications_collection
            notification_id = str(ObjectId())
            notification_doc = {
                "_id": notification_id,
                "title": f"Your {language.title()} learning plan analysis is ready!",
                "content": f"I've analyzed {len(analyses)} sentences from your learning plan session. Tap to see detailed feedback and tips!",
                "notification_type": "session_analysis",  # Custom type for TaalCoach
                "created_by": "system",  # System-generated notification
                "created_at": datetime.now(timezone.utc),
                "sent_at": datetime.now(timezone.utc),
                "is_sent": True,
                # Store metadata for frontend
                "session_id": session_id,
                "job_id": job_id,
                "language": language,
                "sentence_count": len(analyses),
                "session_type": "learning_plan"  # Differentiate from practice sessions
            }

            await notifications_collection.insert_one(notification_doc)
            print(f"[TAALCOACH_NOTIFY] 📝 Created notification document: {notification_id}")

            # Step 2: Create user notification in user_notifications_collection
            user_notification_doc = {
                "_id": str(ObjectId()),
                "user_id": user_id,
                "notification_id": notification_id,
                "is_read": False,
                "read_at": None,
                "deleted_at": None,
                "created_at": datetime.now(timezone.utc)
            }

            await user_notifications_collection.insert_one(user_notification_doc)
            print(f"[TAALCOACH_NOTIFY] ✅ Created analysis notification for user {user_id}, session {session_id}")

            # Note: In-app notification is sufficient - user will see badge in TaalCoach
            # Push notifications can be added later if needed

        except Exception as notify_error:
            logger.error(f"[TAALCOACH_NOTIFY] ❌ Failed to create notification: {str(notify_error)}")
            print(f"[TAALCOACH_NOTIFY] ❌ Notification creation failed (non-fatal): {str(notify_error)}\n{traceback.format_exc()}")
            # Don't fail the entire job if notification creation fails

    except Exception as e:
        logger.error(f"[SENTENCE_ANALYSIS_BG] ❌ Job {job_id} failed: {str(e)}")
        print(f"[SENTENCE_ANALYSIS_BG] ❌ Job {job_id} failed: {str(e)}\n{traceback.format_exc()}")

        # Update job with error
        await jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "failed",
                    "completed_at": datetime.now(timezone.utc),
                    "error_message": str(e)
                }
            }
        )


async def _run_dna_and_optimizer_background(
    user_id: str, plan_id: str, language: str, duration_minutes: float,
    user_turns: list, background_analyses: list
):
    """Run DNA analysis and plan optimizer after response is sent."""
    # DNA analysis
    try:
        from services.speaking_dna_service import speaking_dna_service
        # S3.1: no audio in learning-plan sessions — acoustic strands will be pinned
        # S3.2: challenges_offered=0 so Learning strand will be pinned
        dna_session_data = {
            "session_id": plan_id,
            "session_type": "learning",
            "duration_seconds": int(duration_minutes * 60),
            "user_turns": user_turns,
            "corrections_received": background_analyses,
            "challenges_offered": 0,
            "challenges_accepted": 0,
            "topics_discussed": [language],
            # no audio_base64 — triggers acoustic strand pinning via S3.1
        }
        dna_result = await speaking_dna_service.analyze_session_for_dna(
            user_id=user_id, language=language, session_data=dna_session_data
        )
        print(f"[DNA_BG] ✅ Analysis complete. Breakthroughs: {len(dna_result.get('breakthroughs', []))}")
    except Exception as e:
        print(f"[DNA_BG] ❌ Failed: {e}")

    # Plan optimizer
    try:
        from services.learning_plan_optimizer import LearningPlanOptimizer
        optimizer_result = await LearningPlanOptimizer.auto_update_plan_after_session(
            user_id=user_id,
            plan_id=plan_id,
            current_session_analyses=background_analyses if background_analyses else None,
            minimum_sessions_for_update=3,
        )
        if optimizer_result.get("auto_updated"):
            print(f"[OPTIMIZER_BG] ✅ Plan updated in background")
        else:
            print(f"[OPTIMIZER_BG] No updates needed")
    except Exception as e:
        print(f"[OPTIMIZER_BG] ❌ Failed: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

async def generate_comprehensive_session_summary(plan, conversation_data, basic_summary, user_id):
    """
    Generate a comprehensive session summary with AI analysis.

    PHASE 0 OPTIMIZATION: Now returns both full and compressed summaries.
    Compressed summaries reduce token usage by 93% (696 → 40 tokens).
    """
    try:
        # Get plan details
        language = plan.get("language", "english")
        level = plan.get("proficiency_level", "B1")
        completed_sessions = plan.get("completed_sessions", 0) + 1

        # Get current week focus
        sessions_per_week = 4
        current_week = ((completed_sessions - 1) // sessions_per_week) + 1
        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
        current_week_data = weekly_schedule[current_week - 1] if current_week <= len(weekly_schedule) else None
        week_focus = current_week_data.get("focus", "General language practice") if current_week_data else "General language practice"

        print(f"[SESSION_SUMMARY] Generating summary for session {completed_sessions}, week {current_week}")
        print(f"[SESSION_SUMMARY] Week focus: {week_focus}")
        print(f"[SESSION_SUMMARY] Basic summary: {basic_summary}")
        print(f"[SESSION_SUMMARY] Conversation data available: {conversation_data is not None}")

        # Extract conversation content if available
        conversation_content = ""
        if conversation_data and "messages" in conversation_data:
            messages = conversation_data["messages"]
            print(f"[SESSION_SUMMARY] Found {len(messages)} messages in conversation data")
            for msg in messages[-10:]:  # Last 10 messages for context
                role = "Student" if msg.get("role") == "user" else "Tutor"
                content = msg.get("content", "")
                conversation_content += f"{role}: {content}\n"
        else:
            print(f"[SESSION_SUMMARY] No conversation messages found, using basic summary only")

        # Always generate a comprehensive summary, even without conversation data
        if conversation_content:
            # Full analysis with conversation data
            prompt = f"""Analyze this {language} language learning session and create a comprehensive summary.

STUDENT PROFILE:
- Language: {language}
- Level: {level}
- Session: {completed_sessions}
- Current Week Focus: {week_focus}

CONVERSATION EXCERPT:
{conversation_content}

BASIC SESSION INFO:
{basic_summary if basic_summary else "5-minute conversation session completed"}

Create a comprehensive summary that includes:
1. Session overview (duration, topics covered)
2. Language skills demonstrated (pronunciation, grammar, vocabulary, fluency)
3. Progress towards weekly learning objectives
4. Key achievements and improvements observed
5. Areas for continued focus
6. Specific examples from the conversation

Format as a detailed but concise summary suitable for tracking learning progress."""
        else:
            # Generate comprehensive summary based on basic info and learning objectives
            prompt = f"""Create a comprehensive learning session summary based on the available information.

STUDENT PROFILE:
- Language: {language}
- Level: {level}
- Session: {completed_sessions}
- Current Week Focus: {week_focus}

SESSION INFORMATION:
{basic_summary if basic_summary else "5-minute conversation session completed"}

Even without detailed conversation data, create a comprehensive summary that includes:
1. Session overview based on available information
2. Expected language skills practice for {level} level {language}
3. Progress towards weekly learning objectives: "{week_focus}"
4. Likely achievements and improvements for this session type
5. Areas for continued focus based on the weekly objectives
6. Encouragement and next steps

Make it detailed and educational, focusing on the learning objectives and expected outcomes for a {level} level {language} student working on: {week_focus}."""

        print(f"[SESSION_SUMMARY] Sending prompt to OpenAI (length: {len(prompt)} chars)")

        response = await get_async_openai().chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert language learning analyst. Create detailed, insightful summaries of student progress that are educational and encouraging."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.3
        )

        if response and response.choices:
            comprehensive_summary = response.choices[0].message.content.strip()
            print(f"[SESSION_SUMMARY] Generated comprehensive summary: {len(comprehensive_summary)} characters")

            # PHASE 0 OPTIMIZATION: Compress summary for prompt usage
            from prompt_optimization_helpers import compress_session_summary
            compressed_summary = await compress_session_summary(comprehensive_summary)

            print(f"[SESSION_SUMMARY] Compressed summary: {len(compressed_summary)} characters")

            # Return both versions
            return {
                "full": comprehensive_summary,
                "compressed": compressed_summary
            }
        else:
            print(f"[SESSION_SUMMARY] No response from OpenAI")
            # Enhanced fallback summary
            fallback_full = f"""**Session {completed_sessions} Summary**

**Session Overview:**
Completed a {basic_summary if basic_summary else '5-minute conversation session'} focusing on {language} language practice at {level} level.

**Weekly Learning Focus:**
This session addressed the current week's objective: {week_focus}

**Progress Made:**
- Continued development of {language} communication skills
- Practice aligned with {level} proficiency level expectations
- Engagement with weekly learning objectives

**Areas for Continued Focus:**
- Further practice with {week_focus.lower()}
- Continued application of {level} level language structures
- Building confidence in {language} communication

**Next Steps:**
Continue practicing the weekly focus areas and maintain consistent engagement with the learning plan objectives."""

            from prompt_optimization_helpers import compress_session_summary
            fallback_compressed = await compress_session_summary(fallback_full)

            return {
                "full": fallback_full,
                "compressed": fallback_compressed
            }

    except Exception as e:
        print(f"[SESSION_SUMMARY] Error generating comprehensive summary: {str(e)}")
        print(f"[SESSION_SUMMARY] Full traceback: {traceback.format_exc()}")

        # Enhanced fallback summary with error handling
        language = plan.get("language", "english")
        level = plan.get("proficiency_level", "B1")
        completed_sessions = plan.get("completed_sessions", 0) + 1

        sessions_per_week = 4
        current_week = ((completed_sessions - 1) // sessions_per_week) + 1
        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
        current_week_data = weekly_schedule[current_week - 1] if current_week <= len(weekly_schedule) else None
        week_focus = current_week_data.get("focus", "General language practice") if current_week_data else "General language practice"

        error_fallback_full = f"""**Session {completed_sessions} Summary**

**Session Overview:**
Completed a {basic_summary if basic_summary else 'conversation session'} in {language} at {level} level.

**Weekly Learning Focus:**
{week_focus}

**Progress Made:**
- Continued {language} language practice
- Engagement with {level} level content
- Progress towards weekly learning objectives

**Areas for Continued Focus:**
- {week_focus.lower()}
- Consistent practice and application
- Building fluency and confidence

This session contributed to the overall learning journey and weekly objectives."""

        from prompt_optimization_helpers import compress_session_summary
        error_fallback_compressed = await compress_session_summary(error_fallback_full)

        return {
            "full": error_fallback_full,
            "compressed": error_fallback_compressed
        }

# Route Handlers
@router.post("/api/learning/session-summary")
async def store_session_summary(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Store comprehensive conversation analysis summary for a learning plan session
    """
    # Get parameters from query string and request body
    plan_id = request.query_params.get('plan_id')
    basic_summary = request.query_params.get('session_summary')

    # Try to get conversation data from request body for comprehensive analysis
    conversation_data = None
    try:
        body = await request.body()
        if body:
            conversation_data = json.loads(body)
    except:
        conversation_data = None

    if not plan_id:
        raise HTTPException(
            status_code=400,
            detail="Missing required parameter: plan_id"
        )

    print(f"[SESSION_SUMMARY] Processing session summary for plan {plan_id}")
    print(f"[SESSION_SUMMARY] Basic summary: {basic_summary[:100] if basic_summary else 'None'}...")
    print(f"[SESSION_SUMMARY] Conversation data available: {conversation_data is not None}")

    # 🔍 DEBUG: Check what's in conversation_data
    if conversation_data:
        print(f"[SESSION_SUMMARY] 🔍 Conversation data keys: {list(conversation_data.keys())}")
        sfa_val = conversation_data.get("sentences_for_analysis")
        if sfa_val is not None:
            print(f"[SESSION_SUMMARY] 🔍 Found sentences_for_analysis: {len(sfa_val)} sentences")
        else:
            print(f"[SESSION_SUMMARY] ⚠️ 'sentences_for_analysis' is null or absent")

    try:
        from database import database
        learning_plans_collection = database.learning_plans

        # Find the plan
        plan = await learning_plans_collection.find_one({"id": plan_id})

        if not plan:
            raise HTTPException(
                status_code=404,
                detail="Learning plan not found"
            )

        # Check if the plan belongs to the current user
        if plan.get("user_id") and plan.get("user_id") != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to update this learning plan"
            )

        # 🎓 DETECT FINAL ASSESSMENT MODE
        plan_status = plan.get("status", "in_progress")
        is_final_assessment = plan_status in ["awaiting_final_assessment", "failed_assessment"]

        if is_final_assessment:
            print(f"[FINAL_ASSESSMENT] 🎓 Processing final assessment session for plan {plan_id}")
            print(f"[FINAL_ASSESSMENT] Current status: {plan_status}")

            # Delegate to final assessment handler
            from .final_assessment_handler import process_final_assessment
            return await process_final_assessment(
                plan=plan,
                conversation_data=conversation_data,
                basic_summary=basic_summary,
                user_id=current_user.id,
                learning_plans_collection=learning_plans_collection
            )

        # 🔥 FIX: Use basic summary immediately - generate comprehensive one in background
        # This makes the response instant instead of blocking for 10+ seconds
        import time as _time
        _t0 = _time.monotonic()
        summary_data = {
            "full": basic_summary or f"Session {plan.get('completed_sessions', 0) + 1} completed successfully.",
            "compressed": basic_summary or f"Session {plan.get('completed_sessions', 0) + 1} completed."
        }
        print(f"[SESSION_SUMMARY] ⚡ Using basic summary (comprehensive generation moved to background) in {_time.monotonic()-_t0:.1f}s")

        # 🔧 FIX: Calculate completed_sessions early to create predictable session_id
        completed_sessions = plan.get("completed_sessions", 0) + 1

        # Create sentence analysis job for background processing
        analysis_job_id = None
        # 🔧 FIX: Use predictable session_id format instead of random UUID
        # This allows mobile app to construct the same ID: plan_{plan_id}_session_{session_number}
        summary_id = f"plan_{plan_id}_session_{completed_sessions}"

        if conversation_data and "sentences_for_analysis" in conversation_data:
            sentences_for_analysis = conversation_data["sentences_for_analysis"]

            if sentences_for_analysis and len(sentences_for_analysis) > 0:
                # Generate unique job ID
                analysis_job_id = str(uuid.uuid4())

                # Create job document in MongoDB
                from database import database
                jobs_collection = database.sentence_analysis_jobs
                await jobs_collection.insert_one({
                    "job_id": analysis_job_id,
                    "user_id": current_user.id,
                    "plan_id": plan_id,
                    "session_id": summary_id,
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc),
                    "sentences": sentences_for_analysis,
                    "language": plan.get("language", "english"),
                    "level": plan.get("proficiency_level", "B1"),
                    "analyses": []
                })
                print(f"[SESSION_SUMMARY] 📝 Created analysis job {analysis_job_id} with {len(sentences_for_analysis)} sentences")

                # Schedule background task (runs AFTER response is sent)
                background_tasks.add_task(
                    _run_sentence_analysis_background,
                    job_id=analysis_job_id,
                    user_id=current_user.id,
                    plan_id=plan_id,
                    session_id=summary_id,
                    sentences_for_analysis=sentences_for_analysis,
                    language=plan.get("language", "english"),
                    level=plan.get("proficiency_level", "B1")
                )
                print(f"[SESSION_SUMMARY] 🚀 Scheduled background analysis for job {analysis_job_id}")

        background_analyses = []  # Empty - will be populated by background job

        # ── Structured session summary (gpt-4.1-mini, fully async) ──────────
        # Fire-and-forget: generate + persist off the hot path so the response
        # returns immediately (~0ms instead of ~8s). Client polls
        # GET /api/learning/session-structured-summary/{session_id} for the result.
        background_tasks.add_task(
            _generate_and_persist_structured_summary_background,
            plan_id=plan_id,
            session_number=completed_sessions,
            plan=plan,
            conversation_data=conversation_data,
            basic_summary=basic_summary,
        )
        structured_summary: Dict[str, Any] = {}  # always null in the immediate response

        # Get existing session summaries or initialize empty list
        session_summaries = plan.get("session_summaries", [])

        # Store the compressed one-liner for prompt injection in future sessions.
        # Prefer the structured summary's compressed field; fall back to basic_summary.
        compressed_for_prompt = (
            structured_summary.get("compressed_summary")
            or summary_data.get("compressed")
            or summary_data.get("full")
            or basic_summary
            or f"Session {completed_sessions} completed."
        )
        session_summaries.append(compressed_for_prompt)

        # Update completed sessions count and weekly schedule
        # Note: completed_sessions was calculated earlier (line ~505) for session_id generation
        total_sessions = plan.get("total_sessions", 48)
        progress_percentage = min((completed_sessions / total_sessions) * 100, 100.0)

        # Calculate which week this session belongs to
        sessions_per_week = 4
        new_week = ((completed_sessions - 1) // sessions_per_week) + 1
        sessions_in_week = ((completed_sessions - 1) % sessions_per_week) + 1

        # Update weekly schedule progress
        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
        if weekly_schedule:
            week_index = new_week - 1  # Convert to 0-based index
            if week_index < len(weekly_schedule):
                weekly_schedule[week_index]["sessions_completed"] = sessions_in_week
                print(f"[SESSION_SUMMARY] Updated week {new_week} sessions_completed to {sessions_in_week}")

        # Always use the plan's stored preferred_session_duration as the completion threshold.
        # This is the authoritative value — it reflects any update the user made via the
        # plan card after the initial plan creation. The client-supplied selected_duration
        # is only a fallback for legacy plans that pre-date the preferred_session_duration field.
        selected_duration = int(plan.get("preferred_session_duration") or
                                (conversation_data.get("selected_duration", 5) if conversation_data else 5))
        session_duration_minutes = conversation_data.get("duration_minutes", selected_duration) if conversation_data else selected_duration
        # Cap at selected_duration; anything over is a frontend timer glitch
        session_duration_minutes = min(float(session_duration_minutes), float(selected_duration))

        print(f"[SESSION_SUMMARY] ⚡ Session duration: {session_duration_minutes} min")

        # Deduct minutes from the user's subscription quota via BulletproofTracker.
        # This runs server-side so minute deduction is guaranteed — it doesn't depend
        # on the mobile fire-and-forget /api/stripe/track-speaking-time call succeeding.
        # BulletproofTracker is idempotent (deduplicates on session_id), so if the
        # mobile also calls track-speaking-time with the same session_id, the second
        # call is a no-op.
        try:
            from subscription_service_bulletproof_fix_no_transactions import BulletproofTracker
            from models import SpeakingTimeTrackingRequest

            tracking_request = SpeakingTimeTrackingRequest(
                user_id=str(current_user.id),
                session_id=summary_id,  # summary_id is unique per session
                speaking_minutes=session_duration_minutes,
                session_completed=(session_duration_minutes >= selected_duration)
            )
            tracking_success = await BulletproofTracker.track_speaking_time_atomic(tracking_request)
            if tracking_success:
                print(f"[SESSION_SUMMARY] ✅ Minutes deducted: {session_duration_minutes} min for user {current_user.id}")
            else:
                print(f"[SESSION_SUMMARY] ⚠️ Minute deduction failed (insufficient balance or already deducted) for user {current_user.id}")
        except Exception as tracking_err:
            print(f"[SESSION_SUMMARY] ⚠️ Minute tracking error (non-fatal): {tracking_err}")

        # 🎯 NEW: Store session messages for future comparisons
        # Initialize session_history if it doesn't exist
        session_history = plan.get("session_history", [])

        # Note: selected_duration and session_duration_minutes already calculated above for user tracking

        current_session_data = {
            "session_number": completed_sessions,
            "session_id": summary_id,
            "analysis_job_id": analysis_job_id if analysis_job_id else None,
            "messages": conversation_data.get("messages", []) if conversation_data else [],
            "duration_minutes": session_duration_minutes,
            "selected_duration": selected_duration,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            # Rich structured summary — used by the tutor in the NEXT session
            "structured_summary": structured_summary if structured_summary else None,
        }
        session_history.append(current_session_data)

        # Accumulate spoken time on the learning plan
        current_practice_minutes = float(plan.get("practice_minutes_used", 0.0))
        new_practice_minutes = current_practice_minutes + session_duration_minutes

        print(f"[SESSION_SUMMARY] 💾 Stored session {completed_sessions} messages for future comparison")
        print(f"[SESSION_SUMMARY] 💾 Message count: {len(current_session_data['messages'])}, Duration: {session_duration_minutes} min")
        print(f"[SESSION_SUMMARY] ⏱️ Practice minutes: {current_practice_minutes} + {session_duration_minutes} = {new_practice_minutes} min")

        # Update the learning plan with new data (retry on stale connection)
        update_result = None
        for _attempt in range(3):
            try:
                update_result = await learning_plans_collection.update_one(
                    {"id": plan_id},
                    {
                        "$set": {
                            "session_summaries": session_summaries,
                            "completed_sessions": completed_sessions,
                            "progress_percentage": progress_percentage,
                            "plan_content.weekly_schedule": weekly_schedule,
                            "session_history": session_history,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                break
            except Exception as retry_err:
                if _attempt < 2:
                    print(f"[SESSION_SUMMARY] Learning plan update attempt {_attempt+1} failed, retrying: {retry_err}")
                    await asyncio.sleep(0.5)
                else:
                    raise

        if update_result.modified_count > 0:
            print(f"[SESSION_SUMMARY] Successfully updated learning plan {plan_id}")

            # ⚠️ REMOVED DUPLICATE: Minutes already incremented at lines 670-680
            # This was causing double-deduction bug where 3-minute sessions deducted 6+ minutes
            # User practice_minutes_used is deducted by BulletproofTracker above (idempotent).

            # 🔥 NEW: Update daily_stats for weekly practice chart + XP
            try:
                from database import daily_stats_collection
                user_tz = (conversation_data.get("user_timezone") if conversation_data else None) or getattr(current_user, 'timezone', None) or 'UTC'
                local_date = get_current_local_date(timezone_str=user_tz)
                time_seconds = session_duration_minutes * 60
                # XP: base for session duration + correction engagement bonus
                # selected_duration is already validated/clamped above; get_session_xp handles unknowns.
                session_xp = get_session_xp(int(selected_duration))
                raw_bonus = (conversation_data or {}).get("correction_bonus_xp", 0)
                # XP rebalance PR2: bonus clamp range widened to [0, 20].
                bonus_xp = max(0, min(int(raw_bonus or 0), 20))
                # XP rebalance PR2: learning-plan voice gets ×1.5 — speaking-in-plan
                # is the top-rewarded action (premium action × premium context).
                # This routine ONLY runs for plan voice sessions (called from
                # save_learning_plan_session_summary), so the multiplier applies
                # unconditionally here.
                LEARNING_PLAN_XP_MULTIPLIER = 1.5
                total_xp_delta = int(round((session_xp + bonus_xp) * LEARNING_PLAN_XP_MULTIPLIER))

                daily_result = await daily_stats_collection.update_one(
                    {
                        'user_id': str(current_user.id),
                        'local_date': local_date
                    },
                    {
                        '$inc': {
                            'conversation_time_seconds': time_seconds,
                            'total_time_seconds': time_seconds,
                            'total_sessions': 1,
                            'learning_plan_sessions': 1,
                            'total_xp': total_xp_delta,
                        },
                        '$set': {
                            'user_timezone': 'UTC',
                            'updated_at': datetime.now(timezone.utc),
                        },
                        '$setOnInsert': {
                            'created_at': datetime.now(timezone.utc),
                            'is_streak_day': True,
                            'total_challenges': 0,
                            'correct_challenges': 0,
                            'incorrect_challenges': 0,
                        }
                    },
                    upsert=True
                )
                if daily_result.modified_count > 0 or daily_result.upserted_id:
                    print(f"[SESSION_SUMMARY] ✅ daily_stats updated (learning plan): +{session_duration_minutes} min, +{total_xp_delta} XP (base {session_xp} + bonus {bonus_xp})")

                # Also increment the denormalized lifetime XP on the user document
                await users_collection.update_one(
                    {'_id': ObjectId(str(current_user.id))},
                    {'$inc': {
                        'stats.lifetime.total_xp': total_xp_delta,
                        'stats.lifetime.xp_by_source.conversations': total_xp_delta,
                    }}
                )
                print(f"[SESSION_SUMMARY] ✅ lifetime XP updated: +{total_xp_delta} XP")

                # Keep users.stats.current_streak honest for learning-plan
                # sessions. Challenges write the streak via
                # process_session_completion; learning-plan sessions bypass
                # that orchestrator, so without this the Hub streak stays
                # stale for users on plans.
                #
                # Engagement gate mirrors the BulletproofTracker rule used
                # a few lines above (session_completed = duration met the
                # user's selected length). Forward-only date guard inside
                # the helper rejects any historical replay so this write
                # site's known retry path cannot move the streak backwards.
                from services.stats_service import maybe_update_streak_for_voice_session
                session_engaged = bool(session_duration_minutes >= float(selected_duration))
                await maybe_update_streak_for_voice_session(
                    user_id=str(current_user.id),
                    local_date=local_date,
                    timezone_str=user_tz,
                    engaged=session_engaged,
                )
            except Exception as stats_err:
                print(f"[SESSION_SUMMARY] ⚠️ Error updating daily_stats: {stats_err}")

            # 🗑️ CACHE: Invalidate voice check cache (status has changed)
            try:
                from redis_client import delete_cached
                cache_key = f"voice_check_status:{plan_id}"
                await delete_cached(cache_key)
                print(f"[SESSION_SUMMARY] 🗑️ Invalidated voice check cache for plan {plan_id}")
            except Exception as cache_error:
                print(f"[SESSION_SUMMARY] ⚠️ Cache invalidation error (non-fatal): {cache_error}")

            # ⚡ BACKGROUND: Flashcard generation is scheduled LAST (after DNA and
            # journey state) so it never blocks the sentence-analysis job that
            # mobile waits on. The actual add_task call lives further below;
            # we just prepare the kwargs here while summary_text is in scope.
            flashcard_generation_success = True   # optimistic — will complete in background
            generated_flashcards = 5              # expected count
            _summary_text = summary_data.get("full", basic_summary)
            _flashcard_kwargs = dict(
                plan_id=plan_id,
                completed_sessions=completed_sessions,
                language=plan.get("language", "english"),
                level=plan.get("proficiency_level", "B1"),
                topic=conversation_data.get("topic") if conversation_data else None,
                summary_text=_summary_text,
                user_id=str(current_user.id),
            )

            # 🔥 FIX: Calculate ONLY essential stats immediately (fast operations only)
            # Move complex calculations to background for instant response
            enhanced_stats = {}
            try:
                # Extract basic info (FAST - no DB queries, no heavy calculations)
                messages = []
                duration_minutes = 0.0
                if conversation_data and "messages" in conversation_data:
                    messages = conversation_data["messages"]
                    duration_minutes = conversation_data.get("duration_minutes", 5.0)

                # Calculate LIGHTWEIGHT session_number and week_number (FAST)
                sessions_per_week = 4
                session_number = completed_sessions
                week_number = ((completed_sessions - 1) // sessions_per_week) + 1

                # Get week focus (FAST - already in memory)
                week_focus = "General language practice"
                if weekly_schedule and week_number <= len(weekly_schedule):
                    week_focus = weekly_schedule[week_number - 1].get("focus", week_focus)

                # FAST stats calculation (no DB queries, minimal processing)
                session_stats = SessionStatistics.calculate_session_stats(
                    messages=messages,
                    duration_minutes=duration_minutes,
                    background_analyses=[],  # Empty - will be populated by background job
                    session_number=session_number,
                    week_number=week_number,
                    week_focus=week_focus
                )

                # FAST comparison calculation (use data already in memory)
                previous_session_data = None
                if session_number > 1:
                    plan_session_history = plan.get("session_history", [])
                    for hist_session in plan_session_history:
                        if hist_session.get("session_number") == session_number - 1:
                            previous_session_data = hist_session
                            break

                comparison = SessionStatistics.calculate_comparison(session_stats, previous_session_data)

                # 🔥 FIX: Minimal overall_progress (no DB queries - use data already in memory)
                minimal_overall_progress = {
                    "plan_progress_percentage": progress_percentage,
                    "plan_completed_sessions": completed_sessions,
                    "plan_total_sessions": plan.get("total_sessions", 48),
                    # Other fields will be fetched separately by mobile app if needed
                }

                enhanced_stats = {
                    "session_stats": session_stats,
                    "comparison": comparison,
                    "overall_progress": minimal_overall_progress,
                }

                print(f"[SESSION_SUMMARY] ✅ Lightweight statistics calculated (heavy calculations skipped)")

            except Exception as stats_error:
                print(f"[SESSION_SUMMARY] ⚠️ Error calculating stats: {str(stats_error)}")
                enhanced_stats = {}

            # ⚡ BACKGROUND: DNA analysis and plan optimization run after response is sent (saves 1-3s)
            if current_user.subscription_status in ["active", "trialing"]:
                _dna_kwargs = dict(
                    user_id=str(current_user.id),
                    plan_id=plan_id,
                    language=plan.get("language", "english"),
                    duration_minutes=conversation_data.get("duration_minutes", 5.0) if conversation_data else 5.0,
                    user_turns=conversation_data.get("user_turns", []) if conversation_data else [],
                    background_analyses=background_analyses,
                )
                background_tasks.add_task(_run_dna_and_optimizer_background, **_dna_kwargs)
                print(f"[DNA] ⚡ Scheduled DNA analysis + plan optimization as background task")

            # PHASE 4.2: Invalidate TaalCoach cache after session completion
            await invalidate_coach_context_smart(
                str(current_user.id),
                ["session", "learning_plan", "dna", "sentence_analysis", "achievement"]
            )
            print(f"[CACHE] ✅ Invalidated TaalCoach cache after session completion")

            # 🎯 JOURNEY ORCHESTRATOR: Generate post-session challenge recommendations
            recommended_challenges = []
            try:
                from services.session_challenge_matcher import session_challenge_matcher

                # Build session analysis from enhanced_stats for challenge matching
                session_analysis = {
                    "enhanced_analysis": {
                        "grammar_analysis": conversation_data.get("grammar_issues", "") if conversation_data else "",
                        "new_vocabulary": conversation_data.get("new_vocabulary", []) if conversation_data else [],
                        "confidence_score": enhanced_stats.get("session_stats", {}).get("confidence_score", 1.0),
                        "highlights_for_improvement": conversation_data.get("improvements", []) if conversation_data else []
                    }
                }

                recommended_challenges = await session_challenge_matcher.generate_post_session_recommendations(
                    user_id=str(current_user.id),
                    session_id=summary_id,
                    session_analysis=session_analysis,
                    language=plan.get("language", "english"),
                    level=plan.get("proficiency_level", "B1"),
                    max_recommendations=3
                )

                if recommended_challenges:
                    print(f"[JOURNEY] ✅ Generated {len(recommended_challenges)} challenge recommendations")
            except Exception as rec_error:
                print(f"[JOURNEY] ⚠️ Error generating challenge recommendations: {str(rec_error)}")
                recommended_challenges = []

            # 🎯 JOURNEY ORCHESTRATOR: Update journey state (run in background)
            background_tasks.add_task(_update_journey_state_background, user_id=str(current_user.id))

            # 🚀 Flashcard generation LAST (off the critical path).
            # Sentence-analysis, DNA, optimizer, and journey state are dispatched
            # earlier so they aren't gated by the flashcard LLM call.
            background_tasks.add_task(_generate_flashcards_background, **_flashcard_kwargs)
            print(f"[FLASHCARD_GENERATION] ⚡ Scheduled flashcard generation (LAST) as background task")

            # ⚡ Return immediately — flashcards, DNA, optimizer, and sentence analysis run in background
            print(f"[SESSION_SUMMARY] ✅ Returning response (background tasks scheduled)")
            return {
                "success": True,
                "message": "Session summary stored successfully",
                "completed_sessions": completed_sessions,
                "progress_percentage": progress_percentage,
                "current_week": new_week,
                "session_summary": summary_data.get("full", summary_data),
                "background_analyses": background_analyses,  # Empty - being processed in background
                "analysis_job_id": analysis_job_id,  # NEW: Job ID for polling
                "analysis_status": "processing" if analysis_job_id else "none",  # NEW
                "flashcards_generated": generated_flashcards,
                "flashcard_generation_success": flashcard_generation_success,
                "plan_adapted": False,   # optimizer runs in background; client can poll if needed
                "adaptation": {},
                "session_stats": enhanced_stats.get("session_stats"),
                "comparison": enhanced_stats.get("comparison"),
                "overall_progress": enhanced_stats.get("overall_progress"),
                "structured_summary": structured_summary if structured_summary else None,
                "dna_breakthroughs": [],   # populated by background task
                "dna_insights": {},        # populated by background task
                "recommended_challenges": recommended_challenges  # 🎯 NEW: Post-session challenge recommendations
            }
        else:
            print(f"[SESSION_SUMMARY] Warning: No documents were modified for plan {plan_id}")

            # Still calculate enhanced stats even if no changes were made
            enhanced_stats = {}

            return {
                "success": True,
                "message": "Session summary processed (no changes needed)",
                "completed_sessions": completed_sessions,
                "progress_percentage": progress_percentage,
                "current_week": new_week,
                "session_summary": summary_data.get("full", summary_data),
                "background_analyses": background_analyses,  # Empty - being processed in background
                "analysis_job_id": analysis_job_id,  # NEW: Job ID for polling
                "analysis_status": "processing" if analysis_job_id else "none",  # NEW
                "flashcards_generated": 0,  # No flashcards if plan wasn't updated
                "flashcard_generation_success": False,
                "session_stats": enhanced_stats.get("session_stats"),  # 🎯 NEW: Enhanced statistics
                "comparison": enhanced_stats.get("comparison"),  # 🎯 NEW: Comparison
                "overall_progress": enhanced_stats.get("overall_progress"),  # 🎯 NEW: Overall progress
                "structured_summary": structured_summary if structured_summary else None,
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[SESSION_SUMMARY] Error storing session summary: {str(e)}")
        print(f"[SESSION_SUMMARY] Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error storing session summary: {str(e)}"
        )


@router.get("/api/learning/session-structured-summary/{session_id}")
async def get_session_structured_summary(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Poll for the structured summary generated in the background.

    Returns {"ready": true, "structured_summary": {...}} once the GPT background
    task has completed and persisted the result, or {"ready": false} while it's
    still in-flight.

    session_id format: plan_{plan_id}_session_{N}
    """
    try:
        from database import database
        plans_collection = database.learning_plans

        # Decode session_id → plan_id + session_number
        # Format: "plan_{uuid}_session_{N}"
        parts = session_id.split("_session_")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid session_id format")

        plan_id = parts[0].removeprefix("plan_")
        try:
            session_number = int(parts[1])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session_number in session_id")

        plan = await plans_collection.find_one(
            {"id": plan_id, "user_id": str(current_user.id)},
            {"plan_content.weekly_schedule": 1}
        )
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        sessions_per_week = 4
        week_index = (session_number - 1) // sessions_per_week
        session_in_week = (session_number - 1) % sessions_per_week

        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
        if week_index >= len(weekly_schedule):
            return {"ready": False}

        session_details = weekly_schedule[week_index].get("session_details", [])
        if session_in_week >= len(session_details):
            return {"ready": False}

        ss = session_details[session_in_week].get("structured_summary")
        if not ss:
            return {"ready": False}

        return {"ready": True, "structured_summary": ss}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[STRUCTURED_SUMMARY_POLL] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/learning/sentence-analysis-status/{job_id}")
async def get_sentence_analysis_status(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Poll for sentence analysis job status and results.

    Returns:
    - status: "pending", "processing", "completed", "failed"
    - analyses: Array of sentence analyses (when completed)
    - progress: Estimated progress percentage
    """
    from database import database

    jobs_collection = database.sentence_analysis_jobs

    # Find job
    job = await jobs_collection.find_one({
        "job_id": job_id,
        "user_id": current_user.id  # Security: ensure user owns this job
    })

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Analysis job not found"
        )

    # Calculate progress estimate
    progress = 0
    if job["status"] == "pending":
        progress = 0
    elif job["status"] == "processing":
        # Estimate based on time elapsed
        if job.get("started_at"):
            started = job["started_at"]
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - started).total_seconds()
            # Assume 20 seconds total processing time
            progress = min(int((elapsed / 20) * 100), 95)
        else:
            progress = 10
    elif job["status"] == "completed":
        progress = 100
    elif job["status"] == "failed":
        progress = 0

    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": progress,
        "created_at": job["created_at"].isoformat(),
        "started_at": job.get("started_at").isoformat() if job.get("started_at") else None,
        "completed_at": job.get("completed_at").isoformat() if job.get("completed_at") else None,
        "analyses": job.get("analyses", []),
        "error_message": job.get("error_message"),
        "sentence_count": len(job.get("sentences", []))
    }
