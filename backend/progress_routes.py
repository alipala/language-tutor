import os
import json
import uuid
import traceback
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from openai_client import get_async_openai
from bson import ObjectId

from auth import get_current_user
from models import (
    UserResponse, ConversationSession, ConversationMessage,
    SaveConversationRequest, ConversationStats, ConversationHistoryResponse,
    Flashcard, FlashcardSet, get_session_xp,
)
from database import conversation_sessions_collection, users_collection, daily_stats_collection
from services.timezone_utils import get_current_local_date
from enhanced_analysis import generate_enhanced_analysis
from session_statistics import SessionStatistics

# Helper function to sanitize dictionaries by removing None keys
def sanitize_dict(obj: Any) -> Any:
    """
    Recursively remove None keys from dictionaries.
    MongoDB doesn't allow None as dictionary keys.
    """
    if isinstance(obj, dict):
        # Remove any keys that are None and recursively sanitize values
        return {
            k: sanitize_dict(v)
            for k, v in obj.items()
            if k is not None
        }
    elif isinstance(obj, list):
        # Recursively sanitize list items
        return [sanitize_dict(item) for item in obj]
    else:
        # Return primitive values as-is
        return obj


router = APIRouter(prefix="/api/progress", tags=["progress"])

# ──────────────────────────────────────────────────────────────────────────────
# Background task functions for sentence analysis and vector embeddings
# ──────────────────────────────────────────────────────────────────────────────

async def _embed_conversation_background(
    session_id: str,
    user_id: str,
    language: str,
    level: str,
    topic: str,
    transcript: str,
    created_at: datetime
):
    """
    Background task: Embed conversation to Pinecone for semantic search.

    This runs AFTER the session response is sent to user.
    Enables TaalCoach semantic search for new users from their first conversation.
    """
    try:
        from services.vector_db_service import vector_db

        # Build searchable text from conversation metadata + transcript
        text_parts = [
            f"Language: {language}",
            f"Level: {level}",
            f"Topic: {topic}",
        ]

        if transcript:
            text_parts.append(f"Conversation: {transcript}")

        text = " | ".join(text_parts)

        # Embed to Pinecone with metadata
        success = await vector_db.upsert_content(
            content_id=f"conv_{user_id}_{session_id}",
            text=text,
            metadata={
                "user_id": user_id,
                "content_type": "conversation",
                "language": language,
                "level": level,
                "topic": topic,
                "created_at": created_at.isoformat() if created_at else datetime.utcnow().isoformat(),
            }
        )

        if success:
            print(f"[VECTOR_EMBED_BG] ✅ Embedded conversation {session_id} for user {user_id}")
        else:
            print(f"[VECTOR_EMBED_BG] ⏭️  Skipped embedding (Pinecone disabled or failed)")

    except Exception as e:
        print(f"[VECTOR_EMBED_BG] ❌ Failed to embed conversation {session_id}: {e}")
        # Non-fatal - app continues without embedding

async def _run_transcript_dna_background(
    user_id: str,
    language: str,
    session_type: str,
    session_id: str,
    analysis_job_id: str,
    user_turns: list,
    duration_minutes: float,
):
    """
    S3.3 — Background DNA update from transcript-only sessions (freestyle/news/custom_topic).

    Updates Vocabulary and Accuracy strands using transcript signal.
    Acoustic strands (Rhythm/Confidence/Emotional) and Learning are pinned via
    S3.1 (has_audio=False) and S3.2 (has_challenges=False).

    Waits for the sentence-analysis job to complete before reading corrections_received,
    which feeds Accuracy. Times out after 45 seconds and proceeds with partial data.
    """
    import asyncio
    import time

    # Wait for sentence analysis to complete so corrections_received is populated
    if analysis_job_id:
        from database import database
        jobs_collection = database.sentence_analysis_jobs
        deadline = time.monotonic() + 45.0
        while time.monotonic() < deadline:
            job = await jobs_collection.find_one(
                {"job_id": analysis_job_id},
                {"status": 1, "analyses": 1}
            )
            if job and job.get("status") == "completed":
                corrections_received = job.get("analyses", [])
                break
            await asyncio.sleep(1.5)
        else:
            print(f"[TRANSCRIPT_DNA] ⚠️ Sentence analysis timeout for job {analysis_job_id}; proceeding with partial data")
            corrections_received = []
    else:
        corrections_received = []

    try:
        from services.speaking_dna_service import speaking_dna_service

        session_data = {
            "session_id": session_id,
            "session_type": session_type,
            "duration_seconds": int(duration_minutes * 60),
            "user_turns": user_turns,
            "corrections_received": corrections_received,
            "challenges_offered": 0,   # S3.2: no challenges → Learning pinned
            "challenges_accepted": 0,
            # no audio_base64 → S3.1: acoustic strands pinned
        }

        dna_result = await speaking_dna_service.analyze_session_for_dna(
            user_id=user_id,
            language=language,
            session_data=session_data,
        )
        print(
            f"[TRANSCRIPT_DNA] ✅ DNA updated for user={user_id} lang={language} "
            f"type={session_type} breakthroughs={len(dna_result.get('breakthroughs', []))}"
        )
    except Exception as e:
        print(f"[TRANSCRIPT_DNA] ❌ Failed for user={user_id} session={session_id}: {e}")


async def _run_sentence_analysis_background(
    job_id: str,
    user_id: str,
    session_id: str,
    sentences_for_analysis: list,
    language: str,
    level: str
):
    """
    Background task: Run sentence analysis and store results.

    This runs AFTER the session response is sent to user.
    Updates the analysis job document with results when complete.
    """
    from database import database

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

        def _text(item):
            if isinstance(item, dict):
                return item.get('text')
            return item

        # SPEED: analyze the top 3 sentences by quality_score (desc) instead of
        # all available. Job completes faster so mobile's review readiness
        # window catches it inline. If fewer than 3 exist, analyze all.
        TOP_N_FOR_ANALYSIS = 3
        scored_items = [(s, _score(s)) for s in sentences_for_analysis if _text(s)]
        if len(scored_items) > TOP_N_FOR_ANALYSIS:
            scored_items.sort(key=lambda pair: pair[1], reverse=True)
            scored_items = scored_items[:TOP_N_FOR_ANALYSIS]
        sentence_texts = [_text(item) for item, _ in scored_items]

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

        # 🎯 Create TaalCoach notification for user
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
            # Fetch user's UI language preference for localised notification
            from notification_service import get_notification_strings, localise_language_name
            user_doc_for_notif = await users_collection.find_one({"_id": ObjectId(user_id)}) if ObjectId.is_valid(user_id) else None
            user_locale = (user_doc_for_notif or {}).get("app_language") or "en"
            ns = get_notification_strings(user_locale)
            localised_lang = localise_language_name(language, user_locale)
            notif_title = ns["analysis_title"].format(language=localised_lang)
            notif_body = ns["analysis_body"].format(count=len(analyses))

            notification_id = str(ObjectId())
            notification_doc = {
                "_id": notification_id,
                "title": notif_title,
                "content": notif_body,
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
                "session_type": "practice"  # Differentiate from learning plan sessions
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

            from cache_helpers import invalidate_notif_poll_cache
            await invalidate_notif_poll_cache(user_id)  # CAPACITY_FIXES_V1

            # 📤 Send push notification to user's device
            try:
                from notification_service import send_notification_to_users
                from bson import ObjectId as BsonObjectId

                push_result = await send_notification_to_users(
                    user_ids=[BsonObjectId(user_id)],
                    title=notification_doc["title"],
                    content=notification_doc["content"],
                    notification_type="session_analysis",
                    users_collection=users_collection,
                    notification_id=notification_id,
                    priority='high'
                )

                print(f"[TAALCOACH_NOTIFY] 📤 Push notification sent: {push_result.get('success', False)}")
            except Exception as push_error:
                print(f"[TAALCOACH_NOTIFY] ⚠️ Failed to send push notification: {str(push_error)}")
                # Continue even if push fails - notification is still in database

        except Exception as notify_error:
            print(f"[TAALCOACH_NOTIFY] ❌ Failed to create notification: {str(notify_error)}")
            # Don't fail the analysis if notification creation fails

    except Exception as e:
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


async def _generate_flashcards_background(
    session_id: str,
    user_id: str,
    language: str,
    level: str,
    topic: str,
    summary: str
):
    """
    Background task: Generate flashcards for a session.

    This runs AFTER the session response is sent to user.
    Waits for summary to be available if not provided.
    """
    from flashcard_service import _session_flashcards_enabled
    if not _session_flashcards_enabled():
        return
    try:
        print(f"[FLASHCARD_BG] 🎯 Generating flashcards for session {session_id}")

        from flashcard_service import FlashcardService
        from models import FlashcardGenerationRequest
        from database import database
        from bson import ObjectId
        import asyncio

        # If summary is empty, wait for it to be generated by the summary background task
        if not summary:
            print(f"[FLASHCARD_BG] ⏳ Waiting for summary to be generated...")
            max_wait_seconds = 30
            wait_interval = 1
            elapsed = 0

            while elapsed < max_wait_seconds:
                session = await conversation_sessions_collection.find_one({"_id": ObjectId(session_id)})
                if session and session.get("summary"):
                    summary = session["summary"]
                    print(f"[FLASHCARD_BG] ✅ Summary retrieved from session")
                    break
                await asyncio.sleep(wait_interval)
                elapsed += wait_interval

            if not summary:
                print(f"[FLASHCARD_BG] ⚠️ Summary not available after {max_wait_seconds}s, using empty string")
                summary = ""

        flashcard_request = FlashcardGenerationRequest(
            session_id=session_id,
            language=language,
            level=level,
            topic=topic,
            conversation_content=None,
            session_summary=summary,
            count=5
        )

        # Generate flashcards using the service
        flashcard_set = await FlashcardService.generate_flashcards(flashcard_request, user_id)

        # Save flashcard set to database
        flashcard_sets_collection = database.flashcard_sets
        flashcards_collection = database.flashcards

        flashcard_set_doc = flashcard_set.dict()
        flashcard_set_doc["_id"] = ObjectId()
        flashcard_set_doc["created_at"] = datetime.utcnow()

        # Save individual flashcards
        flashcard_docs = []
        for flashcard in flashcard_set.flashcards:
            card_doc = flashcard.dict()
            card_doc["_id"] = ObjectId()
            flashcard_docs.append(card_doc)

        # Insert flashcard set
        await flashcard_sets_collection.insert_one(flashcard_set_doc)

        # Insert individual flashcards
        if flashcard_docs:
            cards_result = await flashcards_collection.insert_many(flashcard_docs)
            print(f"[FLASHCARD_BG] ✅ Saved {len(cards_result.inserted_ids)} flashcards to database")

        print(f"[FLASHCARD_BG] ✅ Generated and saved {len(flashcard_set.flashcards)} flashcards for session {session_id}")
        print(f"[FLASHCARD_BG] 📚 Flashcard set: {flashcard_set.title}")

    except Exception as e:
        print(f"[FLASHCARD_BG] ❌ Failed for session {session_id}: {str(e)}\n{traceback.format_exc()}")

async def _generate_summary_and_analysis_background(
    session_id: str,
    user_id: str,
    messages: List[Dict[str, Any]],
    language: str,
    level: str,
    topic: str,
    duration_minutes: float
):
    """
    Background task: Generate summary and enhanced analysis, save to session.
    This runs AFTER the session response is sent to user.

    Generates:
    - Summary (GPT call - 2-3 seconds)
    - Enhanced analysis (GPT call + DB queries - 10-15 seconds)
    Total: ~15-18 seconds in background
    """
    try:
        from enhanced_analysis import generate_enhanced_analysis
        from bson import ObjectId
        from models import ConversationMessage

        print(f"[SUMMARY_ANALYSIS_BG] 🔄 Generating summary and enhanced analysis for session {session_id}")

        # Convert dict messages back to ConversationMessage objects
        conversation_messages = [ConversationMessage(**msg) for msg in messages]

        # Generate summary (2-3 seconds GPT call)
        summary = await generate_conversation_summary(conversation_messages, language, level)
        print(f"[SUMMARY_ANALYSIS_BG] ✅ Summary generated: {summary[:50]}...")

        # Generate enhanced analysis (10-15 seconds with GPT + DB queries)
        enhanced_analysis = await generate_enhanced_analysis(
            conversation_messages,
            user_id,
            language,
            level,
            topic or "general",
            duration_minutes
        )
        print(f"[SUMMARY_ANALYSIS_BG] ✅ Enhanced analysis generated")

        # Clean enhanced_analysis to remove None keys (recursively)
        def clean_dict(d):
            """Remove None keys and None values recursively"""
            if not isinstance(d, dict):
                return d
            return {
                str(k) if k is not None else "unknown": clean_dict(v) if isinstance(v, dict) else v
                for k, v in d.items()
                if k is not None and v is not None
            }

        enhanced_analysis_clean = clean_dict(enhanced_analysis)

        # Save both to session document
        await conversation_sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {
                "summary": summary,
                "enhanced_analysis": enhanced_analysis_clean
            }}
        )

        print(f"[SUMMARY_ANALYSIS_BG] ✅ Summary and enhanced analysis saved for session {session_id}")

    except Exception as e:
        print(f"[SUMMARY_ANALYSIS_BG] ❌ Failed for session {session_id}: {str(e)}\n{traceback.format_exc()}")

async def _cache_session_statistics_background(
    session_id: str,
    user_id: str,
    messages: List[Dict[str, Any]],
    duration_minutes: float,
    background_analyses: List[Dict[str, Any]],
    session_number: Optional[int] = None,
    week_number: Optional[int] = None,
    week_focus: Optional[str] = None
):
    """
    Background task: Calculate enhanced session statistics and cache in Redis.
    This runs AFTER the session response is sent to user.

    Cached data includes:
    - Comparison with previous session (word count, speed, vocabulary)
    - Overall progress (total sessions, minutes, streaks)
    """
    try:
        print(f"[SESSION_STATS_CACHE] 🔄 Calculating enhanced statistics for session {session_id}")

        # Calculate enhanced statistics (now optimized with aggregation)
        enhanced_stats = await get_enhanced_session_statistics(
            user_id=user_id,
            messages=messages,
            duration_minutes=duration_minutes,
            background_analyses=background_analyses,
            session_number=session_number,
            week_number=week_number,
            week_focus=week_focus
        )

        # Cache in Redis with 5-minute TTL
        from redis_client import set_cached
        cache_key = f"session_stats:{session_id}"
        await set_cached(cache_key, enhanced_stats, ttl_seconds=300)  # 5 minutes

        print(f"[SESSION_STATS_CACHE] ✅ Cached enhanced statistics for session {session_id}")
        print(f"[SESSION_STATS_CACHE] 📊 Comparison: {enhanced_stats.get('comparison', {}).get('has_previous_session', False)}")
        print(f"[SESSION_STATS_CACHE] 📈 Total sessions: {enhanced_stats.get('overall_progress', {}).get('total_sessions', 0)}")

    except Exception as e:
        print(f"[SESSION_STATS_CACHE] ❌ Failed for session {session_id}: {str(e)}\n{traceback.format_exc()}")

@router.get("/dashboard-data")
async def get_dashboard_data(current_user: UserResponse = Depends(get_current_user)):
    """
    🚀 BATCH ENDPOINT: Get all dashboard data in a single request
    
    This endpoint combines multiple API calls into one:
    - Progress stats
    - Recent conversations
    - Achievements
    - Flashcard sets
    - Due flashcards
    - Learning plans
    
    All queries run in parallel for optimal performance.
    """
    try:
        print(f"[DASHBOARD_BATCH] 🚀 Fetching all dashboard data for user {current_user.id}")
        
        import asyncio
        from database import database
        
        # Run all queries in parallel using asyncio.gather
        results = await asyncio.gather(
            # 1. Progress stats
            get_progress_stats(current_user),
            
            # 2. Recent conversations (limit 10)
            get_conversation_history(limit=10, offset=0, current_user=current_user),
            
            # 3. Achievements
            get_user_achievements(current_user),
            
            # 4. Flashcard sets
            _get_flashcard_sets_internal(current_user),
            
            # 5. Due flashcards (limit 10)
            _get_due_flashcards_internal(current_user, limit=10),
            
            # 6. Learning plans
            _get_learning_plans_internal(current_user),
            
            return_exceptions=True  # Don't fail entire request if one query fails
        )
        
        # Unpack results
        progress_stats = results[0] if not isinstance(results[0], Exception) else None
        conversations = results[1] if not isinstance(results[1], Exception) else {"sessions": [], "total_count": 0}
        achievements = results[2] if not isinstance(results[2], Exception) else {"achievements": []}
        flashcard_sets = results[3] if not isinstance(results[3], Exception) else []
        due_flashcards = results[4] if not isinstance(results[4], Exception) else []
        learning_plans = results[5] if not isinstance(results[5], Exception) else []
        
        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                endpoint_names = ["progress_stats", "conversations", "achievements", "flashcard_sets", "due_flashcards", "learning_plans"]
                print(f"[DASHBOARD_BATCH] ⚠️ Error fetching {endpoint_names[i]}: {str(result)}")
        
        # Build response
        response = {
            "progress_stats": progress_stats.dict() if progress_stats else None,
            "conversations": conversations.get("sessions", []) if isinstance(conversations, dict) else [],
            "total_conversations": conversations.get("total_count", 0) if isinstance(conversations, dict) else 0,
            "achievements": achievements.get("achievements", []) if isinstance(achievements, dict) else [],
            "flashcard_sets": [set.dict() for set in flashcard_sets] if flashcard_sets else [],
            "due_flashcards": [card.dict() for card in due_flashcards] if due_flashcards else [],
            "learning_plans": [plan.dict() for plan in learning_plans] if learning_plans else []
        }
        
        print(f"[DASHBOARD_BATCH] ✅ Successfully fetched all dashboard data")
        print(f"[DASHBOARD_BATCH] Stats: {len(response['conversations'])} conversations, {len(response['flashcard_sets'])} flashcard sets, {len(response['learning_plans'])} learning plans")
        
        return response
        
    except Exception as e:
        print(f"[DASHBOARD_BATCH] ❌ Error fetching dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {str(e)}")

# Internal helper functions for batch endpoint
async def _get_flashcard_sets_internal(current_user: UserResponse):
    """Internal function to get flashcard sets without HTTP dependencies"""
    try:
        sets_cursor = database.flashcard_sets.find({"user_id": str(current_user.id)})
        sets_docs = await sets_cursor.to_list(length=500)
        
        flashcard_sets = []
        for doc in sets_docs:
            flashcards = []
            flashcards_field = doc.get("flashcards", [])
            
            if isinstance(flashcards_field, list) and flashcards_field:
                if isinstance(flashcards_field[0], str):
                    flashcard_ids = flashcards_field
                    flashcards_cursor = database.flashcards.find({
                        "id": {"$in": flashcard_ids},
                        "user_id": str(current_user.id)
                    })
                    flashcard_docs = await flashcards_cursor.to_list(length=5000)
                    
                    for card_doc in flashcard_docs:
                        card_doc.pop("_id", None)
                        flashcards.append(Flashcard(**card_doc))
                else:
                    for card_data in flashcards_field:
                        if isinstance(card_data, dict):
                            flashcards.append(Flashcard(**card_data))
            
            doc.pop("_id", None)
            doc["flashcards"] = flashcards
            doc["total_cards"] = len(flashcards)
            flashcard_sets.append(FlashcardSet(**doc))
        
        return flashcard_sets
    except Exception as e:
        print(f"[DASHBOARD_BATCH] Error in _get_flashcard_sets_internal: {str(e)}")
        return []

async def _get_due_flashcards_internal(current_user: UserResponse, limit: int = 10):
    """Internal function to get due flashcards without HTTP dependencies"""
    try:
        now = datetime.utcnow()
        due_cards_cursor = database.flashcards.find({
            "user_id": str(current_user.id),
            "is_active": True,
            "$or": [
                {"next_review_date": {"$lte": now}},
                {"next_review_date": None}
            ]
        }).sort("next_review_date", 1).limit(limit)
        
        due_cards_docs = await due_cards_cursor.to_list(length=limit)
        
        due_cards = []
        for doc in due_cards_docs:
            doc.pop("_id", None)
            due_cards.append(Flashcard(**doc))
        
        return due_cards
    except Exception as e:
        print(f"[DASHBOARD_BATCH] Error in _get_due_flashcards_internal: {str(e)}")
        return []

async def _get_learning_plans_internal(current_user: UserResponse):
    """Internal function to get learning plans without HTTP dependencies"""
    try:
        # Import LearningPlan from learning_routes where it's defined
        from learning_routes import LearningPlan
        
        plans_cursor = database.learning_plans.find({"user_id": current_user.id})
        plans_docs = await plans_cursor.to_list(length=200)
        
        learning_plans = []
        for doc in plans_docs:
            doc.pop("_id", None)
            learning_plans.append(LearningPlan(**doc))
        
        return learning_plans
    except Exception as e:
        print(f"[DASHBOARD_BATCH] Error in _get_learning_plans_internal: {str(e)}")
        return []

async def get_enhanced_session_statistics(
    user_id: str,
    messages: List[Dict[str, Any]],
    duration_minutes: float,
    background_analyses: Optional[List[Dict[str, Any]]] = None,
    session_number: Optional[int] = None,
    week_number: Optional[int] = None,
    week_focus: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate enhanced session statistics including comparison and overall progress

    Returns dict with: session_stats, comparison, overall_progress
    """
    try:
        # Calculate current session stats
        session_stats = SessionStatistics.calculate_session_stats(
            messages=messages,
            duration_minutes=duration_minutes,
            background_analyses=background_analyses,
            session_number=session_number,
            week_number=week_number,
            week_focus=week_focus
        )

        # Fetch previous session for comparison
        previous_session = await conversation_sessions_collection.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)],  # Most recent first
            limit=1
        )

        # Calculate comparison
        comparison = SessionStatistics.calculate_comparison(session_stats, previous_session)

        # Get overall progress stats
        overall_progress = await _calculate_overall_progress(user_id)

        return {
            "session_stats": session_stats,
            "comparison": comparison,
            "overall_progress": overall_progress
        }

    except Exception as e:
        print(f"[ENHANCED_STATS] Error calculating enhanced statistics: {str(e)}")
        # Return minimal stats on error
        return {
            "session_stats": {
                "duration_minutes": duration_minutes,
                "message_count": len(messages),
            },
            "comparison": {"has_previous_session": False},
            "overall_progress": {
                "total_sessions": 0,
                "total_minutes": 0.0,
                "current_streak": 0,
                "longest_streak": 0,
                "sessions_this_week": 0,
                "sessions_this_month": 0
            }
        }

async def _calculate_overall_progress(user_id: str) -> Dict[str, Any]:
    """
    Calculate overall progress statistics for a user using optimized aggregation.
    OPTIMIZED: Uses aggregation pipeline instead of loading all documents (20-30s → <1s).
    """
    try:
        # Calculate date ranges
        now = datetime.utcnow()
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)

        # OPTIMIZED: Use aggregation to get counts and sums in one query
        conversation_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$facet": {
                "total": [
                    {"$group": {
                        "_id": None,
                        "count": {"$sum": 1},
                        "minutes": {"$sum": "$duration_minutes"}
                    }}
                ],
                "this_week": [
                    {"$match": {"created_at": {"$gte": week_start}}},
                    {"$count": "count"}
                ],
                "this_month": [
                    {"$match": {"created_at": {"$gte": month_start}}},
                    {"$count": "count"}
                ]
            }}
        ]

        conversation_result = await conversation_sessions_collection.aggregate(conversation_pipeline).to_list(1)
        conversation_data = conversation_result[0] if conversation_result else {}

        conversation_total_sessions = conversation_data.get("total", [{}])[0].get("count", 0)
        conversation_total_minutes = conversation_data.get("total", [{}])[0].get("minutes", 0.0)
        sessions_this_week = conversation_data.get("this_week", [{}])[0].get("count", 0)
        sessions_this_month = conversation_data.get("this_month", [{}])[0].get("count", 0)

        # OPTIMIZED: Use aggregation for learning plan stats
        from database import database
        learning_plans_collection = database["learning_plans"]

        learning_plan_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "total_sessions": {"$sum": "$completed_sessions"},
                "total_minutes": {"$sum": "$practice_minutes_used"}
            }}
        ]

        learning_plan_result = await learning_plans_collection.aggregate(learning_plan_pipeline).to_list(1)
        learning_plan_data = learning_plan_result[0] if learning_plan_result else {}

        learning_plan_total_sessions = learning_plan_data.get("total_sessions", 0)
        learning_plan_total_minutes = learning_plan_data.get("total_minutes", 0.0)

        # Unified totals
        total_sessions = conversation_total_sessions + learning_plan_total_sessions
        total_minutes = conversation_total_minutes + learning_plan_total_minutes

        # Calculate streak (this is already optimized)
        current_streak, longest_streak = await calculate_streaks(user_id)

        return SessionStatistics.get_overall_progress(
            user_id=user_id,
            total_sessions=total_sessions,
            total_minutes=total_minutes,
            current_streak=current_streak,
            longest_streak=longest_streak,
            sessions_this_week=sessions_this_week,
            sessions_this_month=sessions_this_month
        )

    except Exception as e:
        print(f"[ENHANCED_STATS] Error calculating overall progress: {str(e)}")
        traceback.print_exc()
        return {
            "total_sessions": 0,
            "total_minutes": 0.0,
            "current_streak": 0,
            "longest_streak": 0,
            "sessions_this_week": 0,
            "sessions_this_month": 0
        }

async def _deduct_practice_minutes(user_id: str, session_id: str, duration_minutes: float, selected_duration: float):
    """Deduct speaking minutes from user quota via BulletproofTracker (idempotent, server-side)."""
    try:
        from subscription_service_bulletproof_fix_no_transactions import BulletproofTracker
        from models import SpeakingTimeTrackingRequest
        tracking_request = SpeakingTimeTrackingRequest(
            user_id=user_id,
            session_id=session_id,
            speaking_minutes=duration_minutes,
            session_completed=(duration_minutes >= selected_duration)
        )
        success = await BulletproofTracker.track_speaking_time_atomic(tracking_request)
        if success:
            print(f"[PROGRESS] ✅ Minutes deducted: {duration_minutes} min for user {user_id}")
        else:
            print(f"[PROGRESS] ⚠️ Minute deduction returned False for user {user_id} (insufficient balance or already deducted)")
    except Exception as e:
        print(f"[PROGRESS] ⚠️ Minute deduction error (non-fatal): {e}")


@router.post("/save-conversation")
async def save_conversation(
    request: SaveConversationRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user)
):
    """Save a conversation session for a registered user with batch sentence analysis"""
    try:
        print(f"[PROGRESS] Saving conversation for user {current_user.id}")
        print(f"[PROGRESS] Language: {request.language}, Level: {request.level}")
        print(f"[PROGRESS] Duration: {request.duration_minutes} minutes")
        print(f"[PROGRESS] Messages count: {len(request.messages)}")
        print(f"[BATCH_SAVE] Received {len(request.sentences_for_analysis)} sentences for batch analysis")
        
        # Check if this is a learning plan conversation
        learning_plan_id = getattr(request, 'learning_plan_id', None)
        conversation_type = getattr(request, 'conversation_type', 'practice')

        print(f"[PROGRESS] Learning Plan ID: {learning_plan_id}")
        print(f"[PROGRESS] Conversation Type: {conversation_type}")

        # Only handle as learning plan if it explicitly has a learning_plan_id
        # News and other conversation types should go through normal flow
        if learning_plan_id is not None:
            print(f"[PROGRESS] 📚 This is a learning plan session - updating learning plan progress")
            print(f"[PROGRESS] Learning plan conversations should not appear in conversation history")

            # Server-side voice-check guard. Mirrors the one in
            # routes/session_summary_routes.py so neither LP write
            # path can land while a scheduled voice check is still
            # pending — even if a stale client bypasses the mobile
            # CTA reroute.
            from database import learning_plans_collection as _lp_coll
            from services.voice_check_service import voice_check_service as _vc_svc
            _guard_plan = await _lp_coll.find_one({"id": learning_plan_id})
            if _guard_plan and _vc_svc.has_pending_voice_check(_guard_plan):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "VOICE_CHECK_PENDING",
                        "plan_id": learning_plan_id,
                        "session_number": int(_guard_plan.get("completed_sessions", 0) or 0),
                        "message": "Finish your voice check first — it unlocks the rest of your plan.",
                    },
                )

            # Generate session summary for learning plan
            session_summary = await generate_conversation_summary(conversation_messages, request.language, request.level)
            
            # Save session summary to learning plan using the new endpoint structure
            selected_duration = getattr(request, 'selected_duration', None) or 5  # Get selected duration
            await save_learning_plan_session_summary(current_user.id, learning_plan_id, session_summary, request.duration_minutes, conversation_messages, selected_duration)
            
            # Track subscription usage for learning plan sessions
            await track_subscription_usage(current_user.id, "practice_session")
            
            # LP sessions don't go through the standard XP pipeline yet
            # (that lives in the non-LP branch below). Mirror the legacy
            # calc for now so the client gets a real number instead of the
            # baseXP fallback.
            lp_session_xp = get_session_xp(selected_duration) + max(
                0, min(int(getattr(request, "correction_bonus_xp", 0) or 0), 20)
            )
            return {
                "success": True,
                "session_id": "learning_plan_session",
                "message": "Learning plan session saved successfully",
                "is_streak_eligible": False,
                "summary": session_summary,
                "xp_earned": lp_session_xp,
                "action": "learning_plan_session_saved"
            }
        
        # Convert messages to ConversationMessage objects
        conversation_messages = []
        for msg in request.messages:
            # Handle timestamp parsing - convert 'Z' suffix to proper timezone format
            timestamp_str = msg.get('timestamp', datetime.utcnow().isoformat())
            if timestamp_str.endswith('Z'):
                # Replace 'Z' with '+00:00' for proper ISO format parsing
                timestamp_str = timestamp_str[:-1] + '+00:00'
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                # Convert to UTC if timezone-aware
                if timestamp.tzinfo is not None:
                    timestamp = timestamp.replace(tzinfo=None)
            except ValueError:
                # Fallback to current time if parsing fails
                timestamp = datetime.utcnow()
            
            conversation_messages.append(ConversationMessage(
                role=msg.get('role', 'user'),
                content=msg.get('content', ''),
                timestamp=timestamp
            ))
        
        # 🚀 MOVED TO BACKGROUND: Summary and enhanced analysis will be generated in background task
        # This removes 15-18 seconds of blocking GPT calls from the response path
        print(f"[PROGRESS] Summary and enhanced analysis will be generated in background (duration: {request.duration_minutes}min, messages: {len(conversation_messages)})")

        # 🔥 UPDATED: Move sentence analysis to background processing
        background_analyses = []
        analysis_job_id = None

        if request.sentences_for_analysis:
            # Generate unique job ID
            analysis_job_id = str(uuid.uuid4())

            # We'll create the job after we have the session_id
            print(f"[BATCH_SAVE] Will create analysis job {analysis_job_id} for {len(request.sentences_for_analysis)} sentences")
        
        # 🆕 UPDATED: Use selected_duration as threshold for streak eligibility
        selected_duration = getattr(request, 'selected_duration', None) or 5  # Default 5 for backward compatibility
        integer_duration = selected_duration if request.duration_minutes >= selected_duration else max(1, int(round(request.duration_minutes)))
        is_streak_eligible = request.duration_minutes >= selected_duration

        print(f"[PROGRESS] Streak eligibility: selected_duration={selected_duration}, actual={request.duration_minutes}, eligible: {is_streak_eligible}")
        
        # Check if there's an existing session for this user today with the same language/level/topic
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        existing_session = await conversation_sessions_collection.find_one({
            "user_id": current_user.id,
            "language": request.language,
            "level": request.level,
            "topic": request.topic,
            "created_at": {
                "$gte": today_start,
                "$lte": today_end
            }
        })
        
        if existing_session:
            # Update existing session
            print(f"[PROGRESS] Updating existing session: {existing_session['_id']}")
            
            # 🆕 UPDATED: Use selected_duration as threshold
            selected_duration = getattr(request, 'selected_duration', None) or 5
            integer_duration = selected_duration if request.duration_minutes >= selected_duration else max(1, int(round(request.duration_minutes)))

            # Pre-compute XP so we can stamp it on the session document
            session_xp_pre = get_session_xp(selected_duration)
            # XP rebalance PR2: bonus clamp range widened to [0, 20].
            bonus_xp_pre = max(0, min(int(request.correction_bonus_xp or 0), 20))
            xp_earned_total = session_xp_pre + bonus_xp_pre

            update_data = {
                "messages": [msg.dict() for msg in conversation_messages],
                "duration_minutes": integer_duration,
                "selected_duration": selected_duration,
                "message_count": len(conversation_messages),
                "conversation_type": conversation_type,
                "is_streak_eligible": is_streak_eligible,
                "xp_earned": xp_earned_total,  # stored so lifetime_progress_service can aggregate it
                "updated_at": datetime.utcnow()
            }
            
            print(f"[PROGRESS] Update duration enforced as INTEGER: {request.duration_minutes} → {integer_duration} minutes")

            # Sanitize update_data to remove any None keys before updating MongoDB
            update_data = sanitize_dict(update_data)

            result = await conversation_sessions_collection.update_one(
                {"_id": existing_session["_id"]},
                {"$set": update_data}
            )
            
            print(f"[PROGRESS] ✅ Conversation updated with ID: {existing_session['_id']}")

            # Update daily_stats + lifetime XP (existing session path)
            try:
                local_date = get_current_local_date(timezone_str=getattr(request, 'user_timezone', None) or 'UTC')
                time_seconds = integer_duration * 60
                # xp_earned_total already computed above when building update_data
                await daily_stats_collection.update_one(
                    {'user_id': current_user.id, 'local_date': local_date},
                    {
                        '$inc': {
                            'conversation_time_seconds': time_seconds,
                            'total_time_seconds': time_seconds,
                            'total_sessions': 1,
                            'total_xp': xp_earned_total,
                            # Source-tagged XP — Games tab progression
                            # bar reads /progression?source=games which
                            # subtracts conversation_xp from total. This
                            # keeps freestyle / news conversations out
                            # of the games daily-goal counter.
                            'conversation_xp': xp_earned_total,
                        },
                        '$set': {'updated_at': datetime.now(timezone.utc)},
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
                # Also increment the denormalized lifetime XP + session
                # counters on the user document. `lifetime.total_sessions`
                # is what BADGE_REGISTRY reads to unlock "First
                # Conversation" / "Voice Warmup" / etc; news sessions
                # additionally bump `lifetime.news_sessions` so the News
                # Reader / Daily Newsie badges fire only on actual news
                # sessions instead of riding the generic total counter.
                lifetime_inc = {
                    'stats.lifetime.total_xp': xp_earned_total,
                    'stats.lifetime.xp_by_source.conversations': xp_earned_total,
                    'stats.lifetime.total_sessions': 1,
                    # Conversation-only counter — `total_sessions` is also
                    # bumped by the challenge pipeline, which let game
                    # sessions satisfy "Five conversations in" badges. The
                    # speaking badge family reads this honest counter.
                    'stats.lifetime.conversation_sessions': 1,
                    'stats.lifetime.total_time_minutes': integer_duration,
                }
                if conversation_type == 'news':
                    lifetime_inc['stats.lifetime.news_sessions'] = 1
                    # Per-language news bucket — Polyglot Reader badge needs
                    # to know news activity per language, not just the total.
                    lifetime_inc[f'stats.lifetime.news_by_language.{(request.language or "unknown").lower()}'] = 1
                    # Per-category interest bucket — powers category-targeted
                    # smart reminders ("fresh Technology news is ready"). The
                    # client sends the article's category on news sessions;
                    # skip silently when absent (older clients / missing data).
                    _news_cat = (getattr(request, 'news_category', None) or '').strip().lower()
                    if _news_cat:
                        lifetime_inc[f'stats.lifetime.news_by_category.{_news_cat}'] = 1
                # Time-window counters for Early Bird (<8am) and Late
                # Night Talker (≥10pm). Read against the user's own
                # timezone so the badges fire on the time they
                # experienced, not server-local UTC.
                from services.timezone_utils import get_user_timezone_obj
                _local_hour = datetime.now(get_user_timezone_obj(
                    getattr(request, 'user_timezone', None) or 'UTC'
                )).hour
                if _local_hour < 8:
                    lifetime_inc['stats.lifetime.early_bird_sessions'] = 1
                if _local_hour >= 22:
                    lifetime_inc['stats.lifetime.late_night_sessions'] = 1
                # Recency stamps for smart reminders: "hasn't done a news
                # session in N days" needs a timestamp, not just a counter.
                lifetime_set = {}
                if conversation_type == 'news':
                    lifetime_set['stats.lifetime.last_news_session_at'] = datetime.utcnow()
                _update_doc = {'$inc': lifetime_inc}
                if lifetime_set:
                    _update_doc['$set'] = lifetime_set
                await users_collection.update_one(
                    {'_id': ObjectId(current_user.id)},
                    _update_doc
                )
                print(f"[PROGRESS] ✅ XP applied (existing session): daily_stats +{xp_earned_total} XP, lifetime +{xp_earned_total} XP (base {session_xp_pre} + bonus {bonus_xp_pre}), local_hour={_local_hour}")

                # Keep users.stats.current_streak honest for the voice product.
                # Challenges write the streak via process_session_completion; the
                # conversation path bypasses that orchestrator so without this the
                # Hub's streak field stays stale for voice-only users. Guarded by
                # engagement (is_streak_eligible) + forward-only date window.
                from services.stats_service import maybe_update_streak_for_voice_session
                await maybe_update_streak_for_voice_session(
                    user_id=str(current_user.id),
                    local_date=local_date,
                    timezone_str=getattr(request, 'user_timezone', None) or 'UTC',
                    engaged=is_streak_eligible,
                )
            except Exception as stats_err:
                print(f"[PROGRESS] ⚠️ Error updating stats for XP (non-fatal): {stats_err}")

            # 🚀 Create sentence analysis job FIRST so the background task fires
            # before the heavier GPT-4o summary/enhanced/embedding/cache tasks.
            # FastAPI runs BackgroundTasks sequentially in registration order;
            # mobile post-session review depends on this job reaching
            # status='completed' within its readiness window.
            if analysis_job_id and request.sentences_for_analysis:
                from database import database
                jobs_collection = database.sentence_analysis_jobs

                await jobs_collection.insert_one({
                    "job_id": analysis_job_id,
                    "user_id": current_user.id,
                    "plan_id": None,  # Practice sessions don't have plan_id
                    "session_id": str(existing_session["_id"]),
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc),
                    "sentences": request.sentences_for_analysis,
                    "language": request.language,
                    "level": request.level,
                    "analyses": []
                })
                print(f"[BATCH_SAVE] 📝 Created analysis job {analysis_job_id} with {len(request.sentences_for_analysis)} sentences")

                # Schedule background task FIRST (runs AFTER response is sent)
                background_tasks.add_task(
                    _run_sentence_analysis_background,
                    job_id=analysis_job_id,
                    user_id=current_user.id,
                    session_id=str(existing_session["_id"]),
                    sentences_for_analysis=request.sentences_for_analysis,
                    language=request.language,
                    level=request.level
                )
                print(f"[BATCH_SAVE] 🚀 Scheduled background analysis (FIRST) for job {analysis_job_id}")

            # 🚀 Schedule summary and enhanced analysis generation in background (runs AFTER sentence analysis)
            background_tasks.add_task(
                _generate_summary_and_analysis_background,
                session_id=str(existing_session["_id"]),
                user_id=current_user.id,
                messages=[msg.dict() for msg in conversation_messages],
                language=request.language,
                level=request.level,
                topic=request.topic or "general",
                duration_minutes=request.duration_minutes
            )
            print(f"[SUMMARY_ANALYSIS_BG] 🚀 Scheduled summary and enhanced analysis for session {existing_session['_id']}")

            # 🔍 VECTOR EMBEDDING: Schedule conversation embedding for semantic search
            transcript = " ".join([msg.content for msg in conversation_messages if msg.role == "user"])
            background_tasks.add_task(
                _embed_conversation_background,
                session_id=str(existing_session["_id"]),
                user_id=current_user.id,
                language=request.language,
                level=request.level,
                topic=request.topic or "general",
                transcript=transcript,
                created_at=existing_session.get("created_at", datetime.utcnow())
            )
            print(f"[VECTOR_EMBED] 🚀 Scheduled embedding for session {existing_session['_id']}")

            # 🚀 Schedule session statistics caching in background (runs AFTER response is sent)
            background_tasks.add_task(
                _cache_session_statistics_background,
                session_id=str(existing_session["_id"]),
                user_id=current_user.id,
                messages=[msg.dict() for msg in conversation_messages],
                duration_minutes=request.duration_minutes,
                background_analyses=background_analyses
            )
            print(f"[SESSION_STATS_CACHE] 🚀 Scheduled statistics caching for session {existing_session['_id']}")

            # S3.3 — Transcript DNA update for premium users (existing session path)
            # Kept AFTER sentence-analysis per guardrail (DNA depends on analyses being ready).
            _dna_session_type = conversation_type if conversation_type in (
                "freestyle", "news", "custom_topic", "practice"
            ) else "practice"
            if current_user.subscription_status in ["active", "trialing"]:
                user_turns = [msg.dict() for msg in conversation_messages if msg.role == "user"]
                background_tasks.add_task(
                    _run_transcript_dna_background,
                    user_id=str(current_user.id),
                    language=request.language,
                    session_type=_dna_session_type,
                    session_id=str(existing_session["_id"]),
                    analysis_job_id=analysis_job_id,
                    user_turns=user_turns,
                    duration_minutes=request.duration_minutes,
                )
                print(f"[TRANSCRIPT_DNA] 🚀 Scheduled DNA update for existing session {existing_session['_id']}")

            # Deduct minutes from user subscription quota (server-side, idempotent)
            await _deduct_practice_minutes(
                user_id=str(current_user.id),
                session_id=str(existing_session["_id"]),
                duration_minutes=request.duration_minutes,
                selected_duration=selected_duration
            )

            _dna_cache_invalidate = current_user.subscription_status in ["active", "trialing"]

            # 🎯 Check Redis cache for enhanced statistics
            from redis_client import get_cached
            cache_key = f"session_stats:{existing_session['_id']}"
            cached_stats = await get_cached(cache_key)

            if cached_stats:
                # Return cached enhanced statistics
                print(f"[SESSION_STATS_CACHE] ✅ Found cached statistics for session {existing_session['_id']}")
                return {
                    "success": True,
                    "session_id": str(existing_session["_id"]),
                    "message": "Conversation updated successfully",
                    "is_streak_eligible": is_streak_eligible,
                    "summary": "",  # Will be generated in background
                    "background_analyses": background_analyses,
                    "session_stats": cached_stats.get("session_stats", {}),
                    "comparison": cached_stats.get("comparison", {}),
                    "overall_progress": cached_stats.get("overall_progress", {}),
                    "dna_cache_invalidate": _dna_cache_invalidate,
                    "xp_earned": xp_earned_total,
                    "action": "updated"
                }
            else:
                # Return basic stats - background task will populate cache
                print(f"[SESSION_STATS_CACHE] ⏳ Cache miss for session {existing_session['_id']}, returning basic stats")
                basic_session_stats = SessionStatistics.calculate_session_stats(
                    messages=[msg.dict() for msg in conversation_messages],
                    duration_minutes=request.duration_minutes,
                    background_analyses=background_analyses
                )

                return {
                    "success": True,
                    "session_id": str(existing_session["_id"]),
                    "message": "Conversation updated successfully",
                    "is_streak_eligible": is_streak_eligible,
                    "summary": "",  # Will be generated in background
                    "background_analyses": background_analyses,
                    "session_stats": basic_session_stats,  # Basic stats only (no DB queries)
                    "comparison": {"has_previous_session": False},  # Will be available in cache soon
                    "overall_progress": {"total_sessions": 0, "total_minutes": 0},  # Will be available in cache soon
                    "stats_loading": True,  # NEW: Indicates stats are being calculated
                    "dna_cache_invalidate": _dna_cache_invalidate,
                    "xp_earned": xp_earned_total,
                    "action": "updated"
                }
        else:
            # Create new session
            print(f"[PROGRESS] Creating new conversation session")
            
            # 🆕 UPDATED: Use selected_duration as threshold
            selected_duration = getattr(request, 'selected_duration', None) or 5
            integer_duration = selected_duration if request.duration_minutes >= selected_duration else max(1, int(round(request.duration_minutes)))

            # Pre-compute XP so we can stamp it on the session document
            session_xp_pre = get_session_xp(selected_duration)
            # XP rebalance PR2: bonus clamp range widened to [0, 20].
            bonus_xp_pre = max(0, min(int(request.correction_bonus_xp or 0), 20))
            xp_earned_total = session_xp_pre + bonus_xp_pre

            session_dict = {
                "user_id": current_user.id,
                "language": request.language,
                "level": request.level,
                "topic": request.topic,
                "conversation_type": conversation_type,
                "messages": [msg.dict() for msg in conversation_messages],
                "duration_minutes": integer_duration,
                "selected_duration": selected_duration,
                "message_count": len(conversation_messages),
                "is_streak_eligible": is_streak_eligible,
                "xp_earned": xp_earned_total,  # stored so lifetime_progress_service can aggregate it
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            print(f"[PROGRESS] Duration enforced as INTEGER: {request.duration_minutes} → {integer_duration} minutes")

            # Sanitize session_dict to remove any None keys before inserting to MongoDB
            session_dict = sanitize_dict(session_dict)

            result = await conversation_sessions_collection.insert_one(session_dict)

            print(f"[PROGRESS] ✅ New conversation saved with ID: {result.inserted_id}")

            # Update daily_stats + lifetime XP (new session path)
            try:
                local_date = get_current_local_date(timezone_str=getattr(request, 'user_timezone', None) or 'UTC')
                time_seconds = integer_duration * 60
                # xp_earned_total already computed above when building session_dict
                await daily_stats_collection.update_one(
                    {'user_id': current_user.id, 'local_date': local_date},
                    {
                        '$inc': {
                            'conversation_time_seconds': time_seconds,
                            'total_time_seconds': time_seconds,
                            'total_sessions': 1,
                            'total_xp': xp_earned_total,
                            # Source-tagged XP — same reason as the
                            # existing-session branch above. Keeps
                            # freestyle / news conversations out of the
                            # Games tab daily goal counter.
                            'conversation_xp': xp_earned_total,
                        },
                        '$set': {'updated_at': datetime.now(timezone.utc)},
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
                # Mirror of the existing-session branch above — same
                # session/time counters, plus the news bucket when this
                # conversation came in via the news flow.
                lifetime_inc = {
                    'stats.lifetime.total_xp': xp_earned_total,
                    'stats.lifetime.xp_by_source.conversations': xp_earned_total,
                    'stats.lifetime.total_sessions': 1,
                    # Conversation-only counter — mirrors the existing-session
                    # branch above; see comment there.
                    'stats.lifetime.conversation_sessions': 1,
                    'stats.lifetime.total_time_minutes': integer_duration,
                }
                if conversation_type == 'news':
                    lifetime_inc['stats.lifetime.news_sessions'] = 1
                    # Per-language news bucket — mirrors the existing-session
                    # branch above for the Polyglot Reader badge.
                    lifetime_inc[f'stats.lifetime.news_by_language.{(request.language or "unknown").lower()}'] = 1
                    # Per-category interest bucket (see existing-session branch).
                    _news_cat = (getattr(request, 'news_category', None) or '').strip().lower()
                    if _news_cat:
                        lifetime_inc[f'stats.lifetime.news_by_category.{_news_cat}'] = 1
                # Same time-window logic as the existing-session branch.
                from services.timezone_utils import get_user_timezone_obj
                _local_hour = datetime.now(get_user_timezone_obj(
                    getattr(request, 'user_timezone', None) or 'UTC'
                )).hour
                if _local_hour < 8:
                    lifetime_inc['stats.lifetime.early_bird_sessions'] = 1
                if _local_hour >= 22:
                    lifetime_inc['stats.lifetime.late_night_sessions'] = 1
                lifetime_set = {}
                if conversation_type == 'news':
                    lifetime_set['stats.lifetime.last_news_session_at'] = datetime.utcnow()
                _update_doc = {'$inc': lifetime_inc}
                if lifetime_set:
                    _update_doc['$set'] = lifetime_set
                await users_collection.update_one(
                    {'_id': ObjectId(current_user.id)},
                    _update_doc
                )
                print(f"[PROGRESS] ✅ XP applied (new session): daily_stats +{xp_earned_total} XP, lifetime +{xp_earned_total} XP (base {session_xp_pre} + bonus {bonus_xp_pre}), local_hour={_local_hour}")

                # Keep users.stats.current_streak honest for the voice product —
                # see notes at the existing-session insertion above. Same guards.
                from services.stats_service import maybe_update_streak_for_voice_session
                await maybe_update_streak_for_voice_session(
                    user_id=str(current_user.id),
                    local_date=local_date,
                    timezone_str=getattr(request, 'user_timezone', None) or 'UTC',
                    engaged=is_streak_eligible,
                )
            except Exception as stats_err:
                print(f"[PROGRESS] ⚠️ Error updating stats for XP (non-fatal): {stats_err}")

            # 🚀 Create sentence analysis job for background processing
            if analysis_job_id and request.sentences_for_analysis:
                from database import database
                jobs_collection = database.sentence_analysis_jobs

                await jobs_collection.insert_one({
                    "job_id": analysis_job_id,
                    "user_id": current_user.id,
                    "plan_id": None,  # Practice sessions don't have plan_id
                    "session_id": str(result.inserted_id),
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc),
                    "sentences": request.sentences_for_analysis,
                    "language": request.language,
                    "level": request.level,
                    "analyses": []
                })
                print(f"[BATCH_SAVE] 📝 Created analysis job {analysis_job_id} with {len(request.sentences_for_analysis)} sentences")

                # Schedule background task (runs AFTER response is sent)
                background_tasks.add_task(
                    _run_sentence_analysis_background,
                    job_id=analysis_job_id,
                    user_id=current_user.id,
                    session_id=str(result.inserted_id),
                    sentences_for_analysis=request.sentences_for_analysis,
                    language=request.language,
                    level=request.level
                )
                print(f"[BATCH_SAVE] 🚀 Scheduled background analysis (FIRST) for job {analysis_job_id}")

            # 🚀 Schedule summary and enhanced analysis generation in background (runs AFTER sentence analysis)
            background_tasks.add_task(
                _generate_summary_and_analysis_background,
                session_id=str(result.inserted_id),
                user_id=current_user.id,
                messages=[msg.dict() for msg in conversation_messages],
                language=request.language,
                level=request.level,
                topic=request.topic or "general",
                duration_minutes=request.duration_minutes
            )
            print(f"[SUMMARY_ANALYSIS_BG] 🚀 Scheduled summary and enhanced analysis for session {result.inserted_id}")

            # 🔍 VECTOR EMBEDDING: Schedule conversation embedding for semantic search
            transcript = " ".join([msg.content for msg in conversation_messages if msg.role == "user"])
            background_tasks.add_task(
                _embed_conversation_background,
                session_id=str(result.inserted_id),
                user_id=current_user.id,
                language=request.language,
                level=request.level,
                topic=request.topic or "general",
                transcript=transcript,
                created_at=datetime.utcnow()
            )
            print(f"[VECTOR_EMBED] 🚀 Scheduled embedding for NEW session {result.inserted_id}")

            # 🚀 Schedule session statistics caching in background (runs AFTER response is sent)
            background_tasks.add_task(
                _cache_session_statistics_background,
                session_id=str(result.inserted_id),
                user_id=current_user.id,
                messages=[msg.dict() for msg in conversation_messages],
                duration_minutes=request.duration_minutes,
                background_analyses=background_analyses
            )
            print(f"[SESSION_STATS_CACHE] 🚀 Scheduled statistics caching for session {result.inserted_id}")

            # S3.3 — Transcript DNA update for premium users (new session path)
            # Kept AFTER sentence-analysis per guardrail (DNA depends on analyses being ready).
            _dna_session_type = conversation_type if conversation_type in (
                "freestyle", "news", "custom_topic", "practice"
            ) else "practice"
            if current_user.subscription_status in ["active", "trialing"]:
                user_turns = [msg.dict() for msg in conversation_messages if msg.role == "user"]
                background_tasks.add_task(
                    _run_transcript_dna_background,
                    user_id=str(current_user.id),
                    language=request.language,
                    session_type=_dna_session_type,
                    session_id=str(result.inserted_id),
                    analysis_job_id=analysis_job_id,
                    user_turns=user_turns,
                    duration_minutes=request.duration_minutes,
                )
                print(f"[TRANSCRIPT_DNA] 🚀 Scheduled DNA update for new session {result.inserted_id}")

            # 🚀 Schedule flashcard generation LAST (off the critical path).
            # Flashcards still generate; they just don't delay the
            # sentence-analysis job that mobile waits on.
            background_tasks.add_task(
                _generate_flashcards_background,
                session_id=str(result.inserted_id),
                user_id=current_user.id,
                language=request.language,
                level=request.level,
                topic=request.topic,
                summary=""  # Summary will be generated in background, flashcards will fetch from session
            )
            print(f"[FLASHCARD_BG] 🚀 Scheduled flashcard generation (LAST) for session {result.inserted_id}")

            # Deduct minutes from user subscription quota (server-side, idempotent)
            await _deduct_practice_minutes(
                user_id=str(current_user.id),
                session_id=str(result.inserted_id),
                duration_minutes=request.duration_minutes,
                selected_duration=selected_duration
            )

            _dna_cache_invalidate = current_user.subscription_status in ["active", "trialing"]

            # 🎯 Check Redis cache for enhanced statistics
            from redis_client import get_cached
            cache_key = f"session_stats:{result.inserted_id}"
            cached_stats = await get_cached(cache_key)

            if cached_stats:
                # Return cached enhanced statistics
                print(f"[SESSION_STATS_CACHE] ✅ Found cached statistics for session {result.inserted_id}")
                return {
                    "success": True,
                    "session_id": str(result.inserted_id),
                    "message": "Conversation saved successfully",
                    "is_streak_eligible": is_streak_eligible,
                    "summary": "",  # Will be generated in background
                    "background_analyses": background_analyses,  # Empty initially - being processed
                    "analysis_job_id": analysis_job_id,
                    "analysis_status": "processing" if analysis_job_id else "none",
                    "session_stats": cached_stats.get("session_stats", {}),
                    "comparison": cached_stats.get("comparison", {}),
                    "overall_progress": cached_stats.get("overall_progress", {}),
                    "dna_cache_invalidate": _dna_cache_invalidate,
                    "xp_earned": xp_earned_total,
                    "action": "created"
                }
            else:
                # Return basic stats - background task will populate cache
                print(f"[SESSION_STATS_CACHE] ⏳ Cache miss for session {result.inserted_id}, returning basic stats")
                basic_session_stats = SessionStatistics.calculate_session_stats(
                    messages=[msg.dict() for msg in conversation_messages],
                    duration_minutes=request.duration_minutes,
                    background_analyses=background_analyses
                )

                return {
                    "success": True,
                    "session_id": str(result.inserted_id),
                    "message": "Conversation saved successfully",
                    "is_streak_eligible": is_streak_eligible,
                    "summary": "",  # Will be generated in background
                    "background_analyses": background_analyses,  # Empty - being processed in background
                    "analysis_job_id": analysis_job_id,
                    "analysis_status": "processing" if analysis_job_id else "none",
                    "session_stats": basic_session_stats,  # Basic stats only (no DB queries)
                    "comparison": {"has_previous_session": False},  # Will be available in cache soon
                    "overall_progress": {"total_sessions": 0, "total_minutes": 0},  # Will be available in cache soon
                    "stats_loading": True,  # NEW: Indicates stats are being calculated
                    "dna_cache_invalidate": _dna_cache_invalidate,
                    "xp_earned": xp_earned_total,
                    "action": "created"
                }
        
    except Exception as e:
        print(f"[PROGRESS] ❌ Error saving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save conversation: {str(e)}")

@router.get("/stats")
async def get_progress_stats(current_user: UserResponse = Depends(get_current_user)):
    """🔥 FIXED: Get user's conversation statistics INCLUDING learning plan sessions"""
    try:
        print(f"[PROGRESS] 🔥 FIXED: Getting stats for user {current_user.id}")
        
        # 🔥 CRITICAL FIX: Include BOTH conversation sessions AND learning plan sessions
        
        # Get conversation sessions (practice sessions)
        sessions_cursor = conversation_sessions_collection.find({"user_id": current_user.id})
        conversation_sessions = await sessions_cursor.to_list(length=2000)
        
        conversation_total_sessions = len(conversation_sessions)
        conversation_total_minutes = sum(session.get('duration_minutes', 0) for session in conversation_sessions)

        print(f"[PROGRESS] 📝 Conversation sessions: {conversation_total_sessions} sessions, {conversation_total_minutes} minutes")

        # Get learning plan sessions
        from database import database
        from bson import ObjectId
        learning_plans_collection = database["learning_plans"]
        learning_plans_cursor = learning_plans_collection.find({"user_id": current_user.id})
        learning_plans = await learning_plans_cursor.to_list(length=200)

        learning_plan_total_sessions = 0
        learning_plan_total_minutes = 0.0

        for plan in learning_plans:
            plan_sessions = plan.get("completed_sessions", 0)
            plan_minutes = plan.get("practice_minutes_used", 0.0)
            learning_plan_total_sessions += plan_sessions
            learning_plan_total_minutes += plan_minutes

            print(f"[PROGRESS] 📚 Learning plan {plan.get('language', 'unknown')}: {plan_sessions} sessions, {plan_minutes} minutes")

        print(f"[PROGRESS] 📚 Learning plan totals: {learning_plan_total_sessions} sessions, {learning_plan_total_minutes} minutes")

        # 🔥 UNIFIED TOTALS: Combine both types of sessions
        total_sessions = conversation_total_sessions + learning_plan_total_sessions

        # 🔥 FIX: Use practice_minutes_used from user document as the authoritative
        # minutes source. This field is incremented by BulletproofTracker for ALL
        # session types (complete, partial, abandoned, learning plan, freestyle, news).
        # conversation_sessions only contain saved/completed sessions so their
        # duration_minutes sum misses partial/abandoned sessions entirely.
        from bson import ObjectId as ObjId
        try:
            user_doc = await users_collection.find_one(
                {"_id": ObjId(current_user.id)},
                {"practice_minutes_used": 1}
            )
            authoritative_minutes = float(user_doc.get("practice_minutes_used", 0.0)) if user_doc else 0.0
        except Exception:
            authoritative_minutes = conversation_total_minutes + learning_plan_total_minutes

        # Use the larger of the two sources to never under-report
        # (authoritative_minutes is the billing tracker; the session sum is a sanity check)
        total_minutes = max(authoritative_minutes, conversation_total_minutes + learning_plan_total_minutes)

        print(f"[PROGRESS] 🎯 UNIFIED TOTALS: {total_sessions} sessions")
        print(f"[PROGRESS] 🎯 AUTHORITATIVE minutes (user.practice_minutes_used): {authoritative_minutes}")
        print(f"[PROGRESS] 🎯 TOTAL MINUTES (authoritative): {total_minutes} minutes")
        
        # Calculate streak (still based on conversation sessions for now)
        current_streak, longest_streak = await calculate_streaks(current_user.id)
        
        # Calculate sessions this week/month (include both types)
        now = datetime.utcnow()
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        
        # Count conversation sessions in time periods
        # 🔥 FIX: Convert created_at to datetime before comparison (can be string in DB)
        conversation_sessions_this_week = []
        conversation_sessions_this_month = []

        for s in conversation_sessions:
            created_at = s.get('created_at')
            if created_at:
                # Convert string to datetime if needed
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00')).replace(tzinfo=None)
                    except:
                        created_at = datetime.min

                if created_at >= week_start:
                    conversation_sessions_this_week.append(s)
                if created_at >= month_start:
                    conversation_sessions_this_month.append(s)

        conversation_sessions_this_week = len(conversation_sessions_this_week)
        conversation_sessions_this_month = len(conversation_sessions_this_month)
        
        # Count learning plan sessions in time periods (approximate based on updated_at)
        learning_plan_sessions_this_week = 0
        learning_plan_sessions_this_month = 0
        
        for plan in learning_plans:
            plan_updated = plan.get('updated_at')
            if plan_updated:
                if isinstance(plan_updated, str):
                    try:
                        plan_updated = datetime.fromisoformat(plan_updated.replace('Z', '+00:00')).replace(tzinfo=None)
                    except:
                        plan_updated = datetime.min
                
                if plan_updated >= week_start:
                    # Estimate sessions this week (could be more precise with session_details)
                    recent_sessions = min(plan.get("completed_sessions", 0), 4)  # Max 4 sessions per week
                    learning_plan_sessions_this_week += recent_sessions
                
                if plan_updated >= month_start:
                    # Estimate sessions this month
                    recent_sessions = plan.get("completed_sessions", 0)
                    learning_plan_sessions_this_month += recent_sessions
        
        # Combine totals
        sessions_this_week = conversation_sessions_this_week + learning_plan_sessions_this_week
        sessions_this_month = conversation_sessions_this_month + learning_plan_sessions_this_month
        
        print(f"[PROGRESS] 📊 This week: {sessions_this_week} sessions ({conversation_sessions_this_week} conversation + {learning_plan_sessions_this_week} learning plan)")
        print(f"[PROGRESS] 📊 This month: {sessions_this_month} sessions ({conversation_sessions_this_month} conversation + {learning_plan_sessions_this_month} learning plan)")

        # 🔥 NEW: Calculate average minutes per day since first practice
        average_minutes_per_day = 0.0
        days_since_first_practice = 0
        first_practice_date = None

        if conversation_sessions or learning_plans:
            # Find earliest practice date from both conversation sessions and learning plans
            earliest_dates = []

            # Get earliest conversation session
            # 🔥 FIX: Convert all dates to datetime before using min()
            if conversation_sessions:
                conv_dates = []
                for s in conversation_sessions:
                    created_at = s.get('created_at')
                    if created_at:
                        if isinstance(created_at, str):
                            try:
                                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00')).replace(tzinfo=None)
                            except:
                                created_at = None
                        if created_at and isinstance(created_at, datetime):
                            conv_dates.append(created_at)

                if conv_dates:
                    earliest_conv = min(conv_dates)
                    earliest_dates.append(earliest_conv)

            # Get earliest learning plan
            # 🔥 FIX: Convert all dates to datetime before using min()
            if learning_plans:
                plan_dates = []
                for p in learning_plans:
                    created_at = p.get('created_at')
                    if created_at:
                        if isinstance(created_at, str):
                            try:
                                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00')).replace(tzinfo=None)
                            except:
                                created_at = None
                        if created_at and isinstance(created_at, datetime):
                            plan_dates.append(created_at)

                if plan_dates:
                    earliest_plan = min(plan_dates)
                    earliest_dates.append(earliest_plan)

            # Use the earliest date found
            if earliest_dates:
                first_practice_date = min(earliest_dates)
                now = datetime.utcnow()

                # Calculate days since first practice (minimum 1 day to avoid division by zero)
                days_since_first_practice = max(1, (now - first_practice_date).days)

                # Calculate average (handles 0 total_minutes gracefully)
                if total_minutes > 0:
                    average_minutes_per_day = round(total_minutes / days_since_first_practice, 1)

                print(f"[PROGRESS] 📊 First practice: {first_practice_date.strftime('%Y-%m-%d')}")
                print(f"[PROGRESS] 📊 Days since first practice: {days_since_first_practice}")
                print(f"[PROGRESS] 📊 Average minutes per day: {average_minutes_per_day}")

        stats = ConversationStats(
            total_sessions=total_sessions,
            total_minutes=total_minutes,
            current_streak=current_streak,
            longest_streak=longest_streak,
            sessions_this_week=sessions_this_week,
            sessions_this_month=sessions_this_month,
            average_minutes_per_day=average_minutes_per_day,
            days_since_first_practice=days_since_first_practice,
            first_practice_date=first_practice_date.isoformat() if first_practice_date else None
        )

        print(f"[PROGRESS] ✅ FIXED STATS calculated: {stats.dict()}")
        return stats
        
    except Exception as e:
        print(f"[PROGRESS] ❌ Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/conversations")
async def get_conversation_history(
    limit: int = 10,
    offset: int = 0,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's conversation history"""
    try:
        print(f"[PROGRESS] ===== CONVERSATION HISTORY DEBUG START =====")
        print(f"[PROGRESS] Getting conversation history for user {current_user.id}")
        print(f"[PROGRESS] Limit: {limit}, Offset: {offset}")

        # Get total count
        total_count = await conversation_sessions_collection.count_documents({"user_id": current_user.id})
        print(f"[PROGRESS] Total count: {total_count}")

        # Get sessions with pagination, sorted by creation date (newest first)
        sessions_cursor = conversation_sessions_collection.find(
            {"user_id": current_user.id}
        ).sort("created_at", -1).skip(offset).limit(limit)
        
        sessions_data = await sessions_cursor.to_list(length=limit)
        print(f"[PROGRESS] Raw sessions data count: {len(sessions_data)}")
        
        # Debug: Print first session structure
        if sessions_data:
            print(f"[PROGRESS] First session structure: {list(sessions_data[0].keys())}")
            print(f"[PROGRESS] First session messages type: {type(sessions_data[0].get('messages', []))}")
            if sessions_data[0].get('messages'):
                print(f"[PROGRESS] First message structure: {list(sessions_data[0]['messages'][0].keys()) if sessions_data[0]['messages'] else 'No messages'}")
        
        # Convert to simple dictionaries - NO PYDANTIC MODELS AT ALL
        sessions = []
        for i, session_data in enumerate(sessions_data):
            try:
                # Convert messages to simple dictionaries
                messages = []
                for j, msg_data in enumerate(session_data.get('messages', [])):
                    # Handle timestamp - keep it simple
                    timestamp = msg_data.get('timestamp', datetime.utcnow())
                    if isinstance(timestamp, str):
                        try:
                            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        except ValueError:
                            timestamp = datetime.utcnow()
                    
                    # Create simple message dict
                    message_dict = {
                        'role': msg_data.get('role', 'user'),
                        'content': msg_data.get('content', ''),
                        'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp)
                    }
                    messages.append(message_dict)
                
                # Handle session timestamps
                created_at = session_data.get('created_at', datetime.utcnow())
                updated_at = session_data.get('updated_at', datetime.utcnow())
                
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except ValueError:
                        created_at = datetime.utcnow()
                
                if isinstance(updated_at, str):
                    try:
                        updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    except ValueError:
                        updated_at = datetime.utcnow()
                
                # Create simple session dictionary - NO PYDANTIC
                session_dict = {
                    'id': str(session_data.get('_id', '')),
                    'user_id': session_data.get('user_id', ''),
                    'language': session_data.get('language', ''),
                    'level': session_data.get('level', ''),
                    'topic': session_data.get('topic'),
                    'messages': messages,
                    'duration_minutes': float(session_data.get('duration_minutes', 0.0)),
                    'message_count': int(session_data.get('message_count', 0)),
                    'summary': session_data.get('summary'),
                    'enhanced_analysis': session_data.get('enhanced_analysis'),
                    'is_streak_eligible': bool(session_data.get('is_streak_eligible', False)),
                    'created_at': created_at.isoformat() if isinstance(created_at, datetime) else str(created_at),
                    'updated_at': updated_at.isoformat() if isinstance(updated_at, datetime) else str(updated_at)
                }
                sessions.append(session_dict)
                print(f"[PROGRESS] Session {i+1} processed successfully")
                
            except Exception as session_error:
                print(f"[PROGRESS] ❌ Error processing session {i+1}: {str(session_error)}")
                print(f"[PROGRESS] Session data keys: {list(session_data.keys())}")
                # Skip this session and continue
                continue
        
        # Get stats
        print(f"[PROGRESS] Getting stats...")
        stats = await get_progress_stats(current_user)
        print(f"[PROGRESS] Stats retrieved successfully")
        
        # Return simple dictionary - NO PYDANTIC
        response = {
            'sessions': sessions,
            'total_count': total_count,
            'stats': stats.dict()
        }
        
        print(f"[PROGRESS] ✅ Retrieved {len(sessions)} conversations successfully")
        print(f"[PROGRESS] ===== CONVERSATION HISTORY DEBUG END =====")
        return response
        
    except Exception as e:
        print(f"[PROGRESS] ❌ CRITICAL ERROR in conversation history: {str(e)}")
        print(f"[PROGRESS] Error type: {type(e)}")
        import traceback
        print(f"[PROGRESS] Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation history: {str(e)}")

@router.get("/conversation/{session_id}/analysis")
async def get_conversation_analysis(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get enhanced analysis for a specific conversation session"""
    try:
        print(f"[PROGRESS] Getting enhanced analysis for session {session_id}")
        
        # Validate ObjectId format
        from bson import ObjectId
        try:
            session_object_id = ObjectId(session_id)
        except:
            raise HTTPException(
                status_code=400,
                detail="Invalid session ID format"
            )
        
        # Find the session
        session = await conversation_sessions_collection.find_one({
            "_id": session_object_id,
            "user_id": current_user.id
        })
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Conversation session not found"
            )
        
        # Get enhanced analysis
        enhanced_analysis = session.get('enhanced_analysis')
        
        if not enhanced_analysis:
            # If no enhanced analysis exists, generate it
            print(f"[PROGRESS] No enhanced analysis found, generating...")
            
            # Convert messages to ConversationMessage objects
            conversation_messages = []
            for msg in session.get('messages', []):
                conversation_messages.append(ConversationMessage(
                    role=msg.get('role', 'user'),
                    content=msg.get('content', ''),
                    timestamp=msg.get('timestamp', datetime.utcnow())
                ))
            
            # Generate enhanced analysis
            enhanced_analysis = await generate_enhanced_analysis(
                conversation_messages,
                current_user.id,
                session.get('language', 'english'),
                session.get('level', 'B1'),
                session.get('topic', 'general'),
                session.get('duration_minutes', 0)
            )
            
            # Save the generated analysis
            await conversation_sessions_collection.update_one(
                {"_id": session_object_id},
                {"$set": {"enhanced_analysis": enhanced_analysis}}
            )
        
        return {
            "session_id": session_id,
            "enhanced_analysis": enhanced_analysis,
            "session_info": {
                "language": session.get('language'),
                "level": session.get('level'),
                "topic": session.get('topic'),
                "duration_minutes": session.get('duration_minutes'),
                "message_count": session.get('message_count'),
                "created_at": session.get('created_at')
            },
            "conversation_messages": session.get('messages', [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PROGRESS] ❌ Error getting conversation analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation analysis: {str(e)}")

@router.get("/achievements")
async def get_user_achievements(current_user: UserResponse = Depends(get_current_user)):
    """Get user's achievements based on their progress"""
    try:
        print(f"[PROGRESS] Getting achievements for user {current_user.id}")
        
        # Get user stats
        stats = await get_progress_stats(current_user)
        
        # Define achievements
        achievements = []
        
        # First Steps (1 conversation)
        if stats.total_sessions >= 1:
            achievements.append({
                "name": "First Steps",
                "icon": "🎯",
                "description": "Complete your first conversation",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Chatterbox (5 conversations)
        if stats.total_sessions >= 5:
            achievements.append({
                "name": "Chatterbox",
                "icon": "💬",
                "description": "Complete 5 conversations",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Dedicated Learner (30 minutes total)
        if stats.total_minutes >= 30:
            achievements.append({
                "name": "Dedicated Learner",
                "icon": "📚",
                "description": "Practice for 30 minutes total",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Consistency King (3-day streak)
        if stats.current_streak >= 3:
            achievements.append({
                "name": "Consistency King",
                "icon": "👑",
                "description": "Maintain a 3-day streak",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Week Warrior (7-day streak)
        if stats.current_streak >= 7:
            achievements.append({
                "name": "Week Warrior",
                "icon": "🔥",
                "description": "Maintain a 7-day streak",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Marathon Master (60 minutes total)
        if stats.total_minutes >= 60:
            achievements.append({
                "name": "Marathon Master",
                "icon": "🏃",
                "description": "Practice for 60 minutes total",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Conversation Pro (10 conversations)
        if stats.total_sessions >= 10:
            achievements.append({
                "name": "Conversation Pro",
                "icon": "⭐",
                "description": "Complete 10 conversations",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Monthly Master (30-day streak)
        if stats.current_streak >= 30:
            achievements.append({
                "name": "Monthly Master",
                "icon": "🏆",
                "description": "Maintain a 30-day streak",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        print(f"[PROGRESS] ✅ User has {len(achievements)} achievements")
        return {"achievements": achievements}
        
    except Exception as e:
        print(f"[PROGRESS] ❌ Error getting achievements: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get achievements: {str(e)}")

async def generate_conversation_summary(messages: List[ConversationMessage], language: str, level: str) -> str:
    """Generate a summary of the conversation using OpenAI"""
    try:
        if not messages:
            return "Empty conversation"
        
        # Create conversation text
        conversation_text = ""
        for msg in messages:
            role = "Student" if msg.role == "user" else "Tutor"
            conversation_text += f"{role}: {msg.content}\n"
        
        # Generate summary
        prompt = f"""Summarize this {language} language learning conversation at {level} level in 1-2 sentences. Focus on the main topics discussed and learning progress shown.

Conversation:
{conversation_text}

Summary:"""
        
        response = await get_async_openai().chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a language learning assistant. Create brief, helpful summaries of student conversations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        print(f"[PROGRESS] Generated summary: {summary}")
        return summary
        
    except Exception as e:
        print(f"[PROGRESS] ❌ Error generating summary: {str(e)}")
        return f"Conversation in {language} ({level} level) - {len(messages)} messages"

def determine_analysis_level(duration_minutes: float, message_count: int) -> str:
    """
    Determine the level of analysis to perform based on session quality
    
    Returns:
    - "enhanced": Full enhanced analysis for quality sessions
    - "basic": Basic summary only for short/low-quality sessions
    """
    # Enhanced analysis criteria:
    # - Duration >= 5 minutes AND message_count >= 10
    # - OR Duration >= 3 minutes AND message_count >= 15 (very active short session)
    
    if duration_minutes >= 5.0 and message_count >= 10:
        return "enhanced"
    elif duration_minutes >= 3.0 and message_count >= 15:
        return "enhanced"
    else:
        return "basic"

async def calculate_streaks(user_id: str) -> tuple[int, int]:
    """Calculate current and longest streak for a user based on daily_stats"""
    try:
        from database import daily_stats_collection

        # Get all daily_stats entries with practice activity (conversation OR challenges)
        daily_stats_cursor = daily_stats_collection.find(
            {"user_id": user_id}
        ).sort("local_date", 1)

        daily_stats = await daily_stats_cursor.to_list(length=1000)

        if not daily_stats:
            return 0, 0

        # Get dates where user had any practice activity
        practice_dates = set()
        for stat in daily_stats:
            # Count as practice day if they did conversations OR challenges
            conv_time = stat.get('conversation_time_seconds', 0)
            challenges = stat.get('total_challenges', 0)

            if conv_time > 0 or challenges > 0:
                # Parse local_date string to date object
                local_date_str = stat.get('local_date')
                if local_date_str:
                    try:
                        date = datetime.strptime(local_date_str, '%Y-%m-%d').date()
                        practice_dates.add(date)
                    except:
                        pass

        if not practice_dates:
            return 0, 0

        sorted_dates = sorted(practice_dates)
        
        # Calculate current streak
        current_streak = 0
        today = datetime.utcnow().date()
        
        # Check if user practiced today or yesterday
        if today in sorted_dates:
            current_date = today
        elif (today - timedelta(days=1)) in sorted_dates:
            current_date = today - timedelta(days=1)
        else:
            current_streak = 0
            current_date = None
        
        if current_date:
            for date in reversed(sorted_dates):
                if date == current_date:
                    current_streak += 1
                    current_date -= timedelta(days=1)
                elif date == current_date:
                    continue
                else:
                    break
        
        # Calculate longest streak
        longest_streak = 0
        temp_streak = 0
        prev_date = None
        
        for date in sorted_dates:
            if prev_date is None or date == prev_date + timedelta(days=1):
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1
            prev_date = date
        
        print(f"[PROGRESS] Calculated streaks - Current: {current_streak}, Longest: {longest_streak}")
        return current_streak, longest_streak
        
    except Exception as e:
        print(f"[PROGRESS] ❌ Error calculating streaks: {str(e)}")
        return 0, 0

async def track_subscription_usage(user_id: str, usage_type: str):
    """Track subscription usage for learning plan sessions"""
    try:
        from database import database
        from bson import ObjectId
        users_collection = database.users
        
        print(f"[SUBSCRIPTION] Tracking {usage_type} usage for user {user_id}")
        
        # Update usage counter
        update_field = "practice_sessions_used" if usage_type == "practice_session" else "assessments_used"
        
        # Convert user_id to ObjectId for MongoDB query
        try:
            user_object_id = ObjectId(user_id)
            query = {"_id": user_object_id}
        except Exception:
            # Fallback to string ID if ObjectId conversion fails
            query = {"_id": user_id}
        
        result = await users_collection.update_one(
            query,
            {"$inc": {update_field: 1}}
        )
        
        if result.modified_count > 0:
            print(f"[SUBSCRIPTION] ✅ Tracked {usage_type} usage for user {user_id}")
        else:
            print(f"[SUBSCRIPTION] ⚠️ No changes made when tracking {usage_type} usage for user {user_id}")
            # Try alternative query format
            try:
                alt_query = {"_id": user_id} if query.get("_id") != user_id else {"_id": ObjectId(user_id)}
                alt_result = await users_collection.update_one(
                    alt_query,
                    {"$inc": {update_field: 1}}
                )
                if alt_result.modified_count > 0:
                    print(f"[SUBSCRIPTION] ✅ Tracked {usage_type} usage with alternative query for user {user_id}")
                else:
                    print(f"[SUBSCRIPTION] ❌ Failed to track usage with both query formats for user {user_id}")
            except Exception as alt_e:
                print(f"[SUBSCRIPTION] ❌ Alternative query also failed: {str(alt_e)}")
            
    except Exception as e:
        print(f"[SUBSCRIPTION] ❌ Error tracking subscription usage: {str(e)}")
        # Don't raise the exception - this is a non-critical operation

async def save_learning_plan_session_summary(user_id: str, learning_plan_id: Optional[str], session_summary: str, duration_minutes: float, conversation_messages: List[ConversationMessage], selected_duration: int = 5):
    """Save session summary to learning plan using the new weekly structure"""
    try:
        from database import database
        learning_plans_collection = database.learning_plans
        
        print(f"[SESSION_SUMMARY] Saving session summary for user {user_id}, plan: {learning_plan_id}")
        
        # Find the learning plan - if no plan_id provided, find by user
        if learning_plan_id:
            learning_plan = await learning_plans_collection.find_one({"id": learning_plan_id})
        else:
            # Find the most recent learning plan for this user
            learning_plan = await learning_plans_collection.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
        
        if not learning_plan:
            print(f"[SESSION_SUMMARY] No learning plan found for user {user_id}")
            return
        
        print(f"[SESSION_SUMMARY] Found learning plan {learning_plan.get('id')} for user {user_id}")
        
        # Get current progress
        current_completed = learning_plan.get("completed_sessions", 0)
        total_sessions = learning_plan.get("total_sessions", 96)
        sessions_per_week = 4
        
        # Calculate which week and session this belongs to
        session_number = current_completed + 1  # Next session to be completed
        week_index = (session_number - 1) // sessions_per_week  # 0-based week index
        session_in_week = ((session_number - 1) % sessions_per_week) + 1  # 1-based session in week
        
        print(f"[SESSION_SUMMARY] Saving session {session_number} to Week {week_index + 1}, Session {session_in_week}")
        
        # Get the weekly schedule
        weekly_schedule = learning_plan.get("plan_content", {}).get("weekly_schedule", [])
        
        if week_index >= len(weekly_schedule):
            print(f"[SESSION_SUMMARY] ⚠️ Session {session_number} exceeds available weeks in the plan")
            return
        
        # Update the specific week with session details
        week = weekly_schedule[week_index]
        
        # Initialize session_details if it doesn't exist
        if 'session_details' not in week:
            week['session_details'] = []
        
        # Determine if session is completed or partial based on duration threshold
        session_status = "completed" if duration_minutes >= selected_duration else "partial"
        integer_duration = selected_duration if session_status == "completed" else max(1, int(round(duration_minutes)))

        print(f"[SESSION_SUMMARY] Duration: {duration_minutes:.1f}min, threshold: {selected_duration}min → status: {session_status}")
        print(f"[SESSION_SUMMARY] Duration enforced as INTEGER: {duration_minutes} → {integer_duration} minutes")

        # Build the completion fields that overlay the (likely pending)
        # entry. We preserve `focus` and any structured_summary written by
        # the transcript pipeline — only completion-time fields get set.
        completion_fields = {
            "session_number": session_in_week,
            "global_session_number": session_number,
            "summary": session_summary,
            "completed_at": datetime.utcnow().isoformat(),
            "status": session_status,
            "selected_duration": selected_duration,
            "duration_minutes": integer_duration,
            "message_count": len(conversation_messages),
        }

        # session_details is pre-populated at plan creation with one entry
        # per session_in_week, all `status: "pending"`. Completion must
        # update the matching entry IN PLACE — appending a duplicate
        # leaves a stale "pending" twin alongside the completed one (which
        # is exactly the bug observed for Jason: 5 entries instead of 4,
        # and #1 still pending while completed_sessions said 1).
        existing_idx = next(
            (
                i
                for i, s in enumerate(week['session_details'])
                if s.get('session_number') == session_in_week
            ),
            None,
        )
        if existing_idx is not None:
            week['session_details'][existing_idx] = {
                **week['session_details'][existing_idx],
                **completion_fields,
            }
        else:
            week['session_details'].append(completion_fields)

        # Only count fully completed sessions toward plan progress and missions
        completed_in_week = sum(1 for s in week['session_details'] if s.get('status') == 'completed')
        week['sessions_completed'] = completed_in_week

        # Calculate new progress using only completed sessions
        total_completed = sum(w.get('sessions_completed', 0) for w in weekly_schedule)
        progress_percentage = (total_completed / total_sessions) * 100 if total_sessions > 0 else 0.0

        update_fields: dict = {
            "plan_content.weekly_schedule": weekly_schedule,
            "progress_percentage": progress_percentage,
            "updated_at": datetime.utcnow().isoformat()
        }

        # Only advance completed_sessions counter for fully completed sessions
        if session_status == "completed":
            update_fields["completed_sessions"] = total_completed

        # Update the learning plan
        result = await learning_plans_collection.update_one(
            {"_id": learning_plan["_id"]},
            {"$set": update_fields}
        )

        if result.modified_count > 0:
            print(f"[SESSION_SUMMARY] ✅ Session summary saved to Week {week_index + 1}, Session {session_in_week} [{session_status}]")
            print(f"[SESSION_SUMMARY] ✅ Updated progress: {total_completed}/{total_sessions} sessions ({progress_percentage:.1f}%)")
        else:
            print(f"[SESSION_SUMMARY] ❌ Failed to save session summary")
            
    except Exception as e:
        print(f"[SESSION_SUMMARY] ❌ Error saving session summary: {str(e)}")
        # Don't raise the exception - this is a non-critical operation

async def update_learning_plan_progress(user_id: str, language: str, level: str, topic: Optional[str] = None):
    """Update learning plan progress when a conversation is completed"""
    try:
        from database import database
        learning_plans_collection = database.learning_plans
        
        print(f"[LEARNING_PLAN] Checking for learning plan updates for user {user_id}")
        print(f"[LEARNING_PLAN] Session details: {language}, {level}, topic: {topic}")
        
        # Find learning plan for this user
        learning_plan = await learning_plans_collection.find_one({
            "user_id": user_id,
            "language": language,
            "proficiency_level": level
        })
        
        if not learning_plan:
            print(f"[LEARNING_PLAN] No learning plan found for user {user_id}")
            return
        
        print(f"[LEARNING_PLAN] Found learning plan {learning_plan.get('id')} for user {user_id}")
        
        # Get current progress
        current_completed = learning_plan.get("completed_sessions", 0)
        total_sessions = learning_plan.get("total_sessions", 48)  # Based on the user data
        
        # Get today's sessions count for this user
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Count sessions for this user today (learning plan sessions only)
        today_sessions = len(learning_plan.get("session_summaries", []))
        
        print(f"[LEARNING_PLAN] User has {today_sessions} session(s) recorded in learning plan")
        
        # Calculate sessions per week (4 sessions per week)
        sessions_per_week = 4
        
        # Calculate current week based on completed sessions
        current_week = (current_completed // sessions_per_week) + 1
        sessions_in_current_week = current_completed % sessions_per_week
        
        print(f"[LEARNING_PLAN] Current progress: Week {current_week}, {sessions_in_current_week}/{sessions_per_week} sessions in week")
        print(f"[LEARNING_PLAN] Total progress: {current_completed}/{total_sessions} sessions")
        
        # Always increment for learning plan sessions (they should be tracked)
        should_increment = True
        print(f"[LEARNING_PLAN] Incrementing learning plan progress")
        
        if should_increment:
            # Increment completed sessions
            new_completed = current_completed + 1
            
            # Don't exceed total sessions
            if new_completed > total_sessions:
                new_completed = total_sessions
            
            # Calculate new progress percentage
            progress_percentage = (new_completed / total_sessions) * 100 if total_sessions > 0 else 0.0
            
            # Calculate which week this session belongs to
            new_week = ((new_completed - 1) // sessions_per_week) + 1  # Week for this session
            sessions_in_week = ((new_completed - 1) % sessions_per_week) + 1  # Position in week (1 or 2)
            
            print(f"[LEARNING_PLAN] This session belongs to Week {new_week}, session {sessions_in_week} of {sessions_per_week}")
            
            # Update weekly schedule progress
            weekly_schedule = learning_plan.get("plan_content", {}).get("weekly_schedule", [])
            if weekly_schedule:
                # Update the sessions_completed for the specific week
                week_index = new_week - 1  # Convert to 0-based index
                if week_index < len(weekly_schedule):
                    # Set the sessions_completed to the number of sessions completed in this week
                    weekly_schedule[week_index]["sessions_completed"] = sessions_in_week
                    print(f"[LEARNING_PLAN] Updated week {new_week} sessions_completed to {sessions_in_week}")
                    
                    # Also ensure previous weeks are marked as complete if needed
                    for prev_week_idx in range(week_index):
                        if weekly_schedule[prev_week_idx]["sessions_completed"] < sessions_per_week:
                            weekly_schedule[prev_week_idx]["sessions_completed"] = sessions_per_week
                            print(f"[LEARNING_PLAN] Marked week {prev_week_idx + 1} as complete with {sessions_per_week} sessions")
            
            # Update the learning plan document
            update_data = {
                "completed_sessions": new_completed,
                "progress_percentage": progress_percentage,
                "updated_at": datetime.utcnow()
            }
            
            # Update weekly schedule if modified
            if weekly_schedule:
                update_data["plan_content.weekly_schedule"] = weekly_schedule
            
            result = await learning_plans_collection.update_one(
                {"_id": learning_plan["_id"]},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                print(f"[LEARNING_PLAN] ✅ Updated learning plan {learning_plan.get('id')}: {new_completed}/{total_sessions} sessions ({progress_percentage:.1f}%)")
                print(f"[LEARNING_PLAN] ✅ Week {new_week} now has {sessions_in_week}/{sessions_per_week} sessions completed")
            else:
                print(f"[LEARNING_PLAN] ⚠️ No changes made to learning plan {learning_plan.get('id')}")
        else:
            print(f"[LEARNING_PLAN] ℹ️ No increment needed for learning plan {learning_plan.get('id')}")
                
    except Exception as e:
        print(f"[LEARNING_PLAN] ❌ Error updating learning plan progress: {str(e)}")
        # Don't raise the exception - this is a non-critical operation


@router.get("/sentence-analysis-status/{job_id}")
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

@router.get("/conversation/{session_id}/sentence-analysis")
async def get_session_sentence_analysis(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get sentence analysis for a completed session.

    This endpoint is called from TaalCoach when user clicks "View Analysis" button.

    Returns:
    - status: "ready" (analyses available), "processing" (still analyzing), "not_found" (no job)
    - analyses: Array of sentence analyses (when status is "ready")
    - job_id: The analysis job ID
    """
    from database import database
    from bson import ObjectId

    jobs_collection = database.sentence_analysis_jobs

    # 🔧 FIX: Handle both practice sessions and learning plan sessions
    is_learning_plan_session = session_id.startswith("plan_") and "_session_" in session_id

    if not is_learning_plan_session:
        # Verify user owns this practice session
        session = await conversation_sessions_collection.find_one({
            "_id": ObjectId(session_id) if ObjectId.is_valid(session_id) else session_id,
            "user_id": current_user.id
        })

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found or you don't have permission to access it"
            )
    else:
        print(f"[SENTENCE_ANALYSIS] Detected learning plan session: {session_id}")

    # Find the analysis job for this session (works for both types)
    job = await jobs_collection.find_one({
        "session_id": session_id,
        "user_id": current_user.id
    })

    if not job:
        return {
            "status": "not_found",
            "message": "No sentence analysis found for this session"
        }

    # Check job status
    if job["status"] == "completed":
        analyses = job.get("analyses", [])
        return {
            "status": "ready",
            "analyses": analyses,
            "job_id": job["job_id"],
            "sentence_count": len(analyses)
        }
    elif job["status"] == "processing":
        return {
            "status": "processing",
            "job_id": job["job_id"],
            "message": "Analysis is still in progress. Please wait a moment."
        }
    elif job["status"] == "failed":
        return {
            "status": "failed",
            "job_id": job["job_id"],
            "message": "Analysis failed. Please try again later."
        }
    else:  # pending
        return {
            "status": "processing",
            "job_id": job["job_id"],
            "message": "Analysis will start shortly."
        }

@router.get("/session-stats/{session_id}")
async def get_session_statistics(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Poll for cached session statistics.

    Mobile app can use this endpoint to check if enhanced statistics are ready.

    Returns:
    - stats_ready: true if stats are in cache, false otherwise
    - session_stats: Session statistics (if ready)
    - comparison: Comparison with previous session (if ready)
    - overall_progress: Overall user progress (if ready)
    """
    from redis_client import get_cached

    # Verify user owns this session
    session = await conversation_sessions_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": current_user.id  # Security: ensure user owns this session
    })

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    # Check Redis cache
    cache_key = f"session_stats:{session_id}"
    cached_stats = await get_cached(cache_key)

    if cached_stats:
        return {
            "session_id": session_id,
            "stats_ready": True,
            "session_stats": cached_stats.get("session_stats", {}),
            "comparison": cached_stats.get("comparison", {}),
            "overall_progress": cached_stats.get("overall_progress", {})
        }
    else:
        return {
            "session_id": session_id,
            "stats_ready": False,
            "message": "Statistics are being calculated in background"
        }
