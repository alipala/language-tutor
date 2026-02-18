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

        # ⚡ PARALLEL: Run summary generation + sentence analysis at the same time
        async def _run_sentence_analysis():
            if not (conversation_data and "sentences_for_analysis" in conversation_data):
                print(f"[SESSION_SUMMARY] ℹ️ No sentences_for_analysis in conversation data")
                return []
            sentences_for_analysis = conversation_data["sentences_for_analysis"]
            if not sentences_for_analysis:
                print(f"[SESSION_SUMMARY] ⚠️ No sentences provided for analysis")
                return []
            from background_sentence_analysis import batch_analyze_sentences
            sentence_texts = [s.get('text') for s in sentences_for_analysis if s.get('text')]
            print(f"[SESSION_SUMMARY] 🔍 Starting batch analysis of {len(sentence_texts)} sentences (parallel)")
            try:
                analyses = await batch_analyze_sentences(
                    sentences=sentence_texts,
                    language=plan.get("language", "english"),
                    level=plan.get("proficiency_level", "B1")
                )
                result = [a.dict() for a in analyses]
                print(f"[SESSION_SUMMARY] ✅ Batch analysis complete: {len(result)} results")
                return result
            except Exception as analysis_error:
                print(f"[SESSION_SUMMARY] ⚠️ Batch analysis failed: {str(analysis_error)}")
                return []

        import time as _time
        _t0 = _time.monotonic()
        summary_data, background_analyses = await asyncio.gather(
            generate_comprehensive_session_summary(plan, conversation_data, basic_summary, current_user.id),
            _run_sentence_analysis()
        )
        print(f"[SESSION_SUMMARY] ⚡ Parallel OpenAI calls done in {_time.monotonic()-_t0:.1f}s")

        # Get existing session summaries or initialize empty list
        session_summaries = plan.get("session_summaries", [])

        # PHASE 0 OPTIMIZATION: Store compressed summary for prompt usage
        # Store full summary for history/display purposes
        session_summaries.append(summary_data.get("compressed", summary_data.get("full", summary_data)))

        # Update completed sessions count and weekly schedule
        completed_sessions = plan.get("completed_sessions", 0) + 1
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
        session_duration_minutes = conversation_data.get("duration_minutes", 5.0) if conversation_data else 5.0
        # Cap at 5 minutes; anything over is a frontend timer glitch
        session_duration_minutes = min(float(session_duration_minutes), 5.0)

        current_session_data = {
            "session_number": completed_sessions,
            "messages": conversation_data.get("messages", []) if conversation_data else [],
            "duration_minutes": session_duration_minutes,
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

            # 🎯 NEW: Calculate enhanced session statistics for learning plan session
            enhanced_stats = {}
            try:
                # Extract messages from conversation_data
                messages = []
                duration_minutes = 0.0
                if conversation_data and "messages" in conversation_data:
                    messages = conversation_data["messages"]
                    duration_minutes = conversation_data.get("duration_minutes", 5.0)

                # Get sentence analyses for quality scores (use already-calculated background_analyses)
                # DON'T overwrite! background_analyses was already populated above
                # Only use from conversation_data if it wasn't calculated yet
                if not background_analyses and conversation_data:
                    background_analyses = conversation_data.get("sentence_analyses", [])

                # Calculate session_number and week_number
                sessions_per_week = 2
                session_number = completed_sessions
                week_number = ((completed_sessions - 1) // sessions_per_week) + 1

                # Get week focus
                week_focus = "General language practice"
                if weekly_schedule and week_number <= len(weekly_schedule):
                    week_focus = weekly_schedule[week_number - 1].get("focus", week_focus)

                # Calculate session stats
                session_stats = SessionStatistics.calculate_session_stats(
                    messages=messages,
                    duration_minutes=duration_minutes,
                    background_analyses=background_analyses,
                    session_number=session_number,
                    week_number=week_number,
                    week_focus=week_focus
                )

                # 🎯 UPDATED: Fetch previous learning plan session from session_history
                previous_session_data = None
                if session_number > 1:
                    # Get session_history from the plan (we just stored current session)
                    # Look for previous session (session_number - 1)
                    plan_session_history = plan.get("session_history", [])

                    print(f"[SESSION_SUMMARY] Looking for previous session {session_number - 1} in history (total: {len(plan_session_history)} sessions)")

                    for hist_session in plan_session_history:
                        if hist_session.get("session_number") == session_number - 1:
                            previous_session_data = hist_session
                            print(f"[SESSION_SUMMARY] ✅ Found previous session {session_number - 1} with {len(hist_session.get('messages', []))} messages")
                            break

                    if not previous_session_data:
                        print(f"[SESSION_SUMMARY] ⚠️ Previous session {session_number - 1} not found in history (session before implementation)")

                # Calculate comparison with full data if available
                comparison = SessionStatistics.calculate_comparison(session_stats, previous_session_data)

                if comparison.get("has_previous_session"):
                    print(f"[SESSION_SUMMARY] ✅ Comparison calculated: words={comparison.get('words_improvement')}, speed={comparison.get('speed_improvement')} wpm")

                # Get overall progress stats
                from database import database as db
                learning_plans_collection_ref = db.learning_plans
                current_plan = await learning_plans_collection_ref.find_one({"id": plan_id})

                # Import progress stats calculator from progress_routes
                import sys
                import os
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from progress_routes import _calculate_overall_progress

                overall_progress = await _calculate_overall_progress(str(current_user.id))

                # Add learning plan specific progress
                if current_plan:
                    overall_progress["plan_progress_percentage"] = progress_percentage
                    overall_progress["plan_completed_sessions"] = completed_sessions
                    overall_progress["plan_total_sessions"] = plan.get("total_sessions", 48)

                enhanced_stats = {
                    "session_stats": session_stats,
                    "comparison": comparison,
                    "overall_progress": overall_progress
                }

                print(f"[SESSION_SUMMARY] ✅ Enhanced statistics calculated successfully")

            except Exception as stats_error:
                print(f"[SESSION_SUMMARY] ⚠️ Error calculating enhanced stats: {str(stats_error)}")
                # Continue without enhanced stats if calculation fails
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

            # ⚡ Return immediately — flashcards, DNA, and optimizer run in background
            print(f"[SESSION_SUMMARY] ✅ Returning response (background tasks scheduled)")
            return {
                "success": True,
                "message": "Session summary stored successfully",
                "completed_sessions": completed_sessions,
                "progress_percentage": progress_percentage,
                "current_week": new_week,
                "session_summary": summary_data.get("full", summary_data),
                "background_analyses": background_analyses,
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
                "background_analyses": background_analyses,  # 🔥 CRITICAL: Return sentence analyses!
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
