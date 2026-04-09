"""
Session Summary Routes
Handles learning session summary generation and storage
"""

import os
import json
import traceback
import uuid
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from pydantic import BaseModel
from bson import ObjectId
import httpx
from openai import OpenAI

from auth import get_current_user
from models import UserResponse
from session_statistics import SessionStatistics
from cache_helpers import invalidate_coach_context_smart  # PHASE 4.2: Smart cache invalidation

# Initialize router
router = APIRouter()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables")

# Initialize OpenAI client with error handling
try:
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized successfully (session_summary_routes)")
except TypeError as e:
    if "proxies" in str(e):
        print("Detected 'proxies' error in OpenAI initialization. Using alternative initialization...")
        client = OpenAI(api_key=api_key, http_client=httpx.Client())
        print("OpenAI client initialized with alternative method (session_summary_routes)")
    else:
        print(f"Error initializing OpenAI client: {str(e)}")
        raise

# ──────────────────────────────────────────────────────────────────────────────
# Background task functions — run AFTER response is sent to the client
# ──────────────────────────────────────────────────────────────────────────────

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

        # Extract sentence texts
        sentence_texts = [s.get('text') for s in sentences_for_analysis if s.get('text')]

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

        # Run batch analysis (this is the 15-20 second operation)
        from background_sentence_analysis import batch_analyze_sentences

        print(f"[SENTENCE_ANALYSIS_BG] 🔍 Analyzing {len(sentence_texts)} sentences...")
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
        dna_session_data = {
            "session_id": plan_id,
            "session_type": "learning",
            "duration_seconds": int(duration_minutes * 60),
            "user_turns": user_turns,
            "corrections_received": background_analyses,
            "challenges_offered": 2,
            "challenges_accepted": 1,
            "topics_discussed": [language],
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
        sessions_per_week = 2
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

        response = client.chat.completions.create(
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
            compressed_summary = compress_session_summary(comprehensive_summary)

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
            fallback_compressed = compress_session_summary(fallback_full)

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

        sessions_per_week = 2
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
        error_fallback_compressed = compress_session_summary(error_fallback_full)

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
        if "sentences_for_analysis" in conversation_data:
            print(f"[SESSION_SUMMARY] 🔍 Found sentences_for_analysis: {len(conversation_data['sentences_for_analysis'])} sentences")
        else:
            print(f"[SESSION_SUMMARY] ⚠️ 'sentences_for_analysis' NOT in conversation_data!")

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

        # Get existing session summaries or initialize empty list
        session_summaries = plan.get("session_summaries", [])

        # PHASE 0 OPTIMIZATION: Store compressed summary for prompt usage
        # Store full summary for history/display purposes
        session_summaries.append(summary_data.get("compressed", summary_data.get("full", summary_data)))

        # Update completed sessions count and weekly schedule
        # Note: completed_sessions was calculated earlier (line ~505) for session_id generation
        total_sessions = plan.get("total_sessions", 48)
        progress_percentage = min((completed_sessions / total_sessions) * 100, 100.0)

        # Calculate which week this session belongs to
        sessions_per_week = 2
        new_week = ((completed_sessions - 1) // sessions_per_week) + 1
        sessions_in_week = ((completed_sessions - 1) % sessions_per_week) + 1

        # Update weekly schedule progress
        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
        if weekly_schedule:
            week_index = new_week - 1  # Convert to 0-based index
            if week_index < len(weekly_schedule):
                weekly_schedule[week_index]["sessions_completed"] = sessions_in_week
                print(f"[SESSION_SUMMARY] Updated week {new_week} sessions_completed to {sessions_in_week}")

        # CRITICAL FIX: Track subscription usage when session is completed
        try:
            users_collection = database.users
            for _attempt in range(3):
                try:
                    user_result = await users_collection.update_one(
                        {"_id": ObjectId(current_user.id)},
                        {"$inc": {"practice_sessions_used": 1}}
                    )
                    if user_result.modified_count > 0:
                        print(f"[SESSION_SUMMARY] Incremented subscription usage for user {current_user.id}")
                    else:
                        print(f"[SESSION_SUMMARY] Failed to increment subscription usage for user {current_user.id}")
                    break
                except Exception as retry_err:
                    if _attempt < 2:
                        print(f"[SESSION_SUMMARY] Subscription tracking attempt {_attempt+1} failed, retrying: {retry_err}")
                        await asyncio.sleep(0.5)
                    else:
                        raise
        except Exception as subscription_error:
            print(f"[SESSION_SUMMARY] Error tracking subscription usage: {str(subscription_error)}")
            # Don't fail the session saving if subscription tracking fails
            pass

        # 🎯 NEW: Store session messages for future comparisons
        # Initialize session_history if it doesn't exist
        session_history = plan.get("session_history", [])

        # Store current session data for future comparisons
        selected_duration = conversation_data.get("selected_duration", 5) if conversation_data else 5  # 🆕 Get selected duration
        session_duration_minutes = conversation_data.get("duration_minutes", selected_duration) if conversation_data else selected_duration
        # Cap at selected_duration; anything over is a frontend timer glitch
        session_duration_minutes = min(float(session_duration_minutes), float(selected_duration))

        current_session_data = {
            "session_number": completed_sessions,
            "session_id": summary_id,  # 🔧 FIX: Store session_id so mobile app can fetch analysis
            "analysis_job_id": analysis_job_id if analysis_job_id else None,  # 🔧 FIX: Store job_id for polling
            "messages": conversation_data.get("messages", []) if conversation_data else [],
            "duration_minutes": session_duration_minutes,
            "selected_duration": selected_duration,  # 🆕 Store selected duration
            "completed_at": datetime.now(timezone.utc).isoformat()
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
                            "practice_minutes_used": new_practice_minutes,
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

            # 🗑️ CACHE: Invalidate voice check cache (status has changed)
            try:
                from redis_client import delete_cached
                cache_key = f"voice_check_status:{plan_id}"
                await delete_cached(cache_key)
                print(f"[SESSION_SUMMARY] 🗑️ Invalidated voice check cache for plan {plan_id}")
            except Exception as cache_error:
                print(f"[SESSION_SUMMARY] ⚠️ Cache invalidation error (non-fatal): {cache_error}")

            # ⚡ BACKGROUND: Flashcard generation runs after response is sent (saves 3-10s)
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
            background_tasks.add_task(_generate_flashcards_background, **_flashcard_kwargs)
            print(f"[FLASHCARD_GENERATION] ⚡ Scheduled flashcard generation as background task")

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
                sessions_per_week = 2
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
                "dna_breakthroughs": [],   # populated by background task
                "dna_insights": {}         # populated by background task
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
                "overall_progress": enhanced_stats.get("overall_progress")  # 🎯 NEW: Overall progress
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
            elapsed = (datetime.now(timezone.utc) - job["started_at"]).total_seconds()
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
