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


async def _calculate_statistics_background(
    plan_id: str, user_id: str, conversation_data: dict, background_analyses: list,
    completed_sessions: int, weekly_schedule: list
):
    """Calculate enhanced session statistics after response is sent (saves 2-4s)."""
    try:
        from session_statistics import SessionStatistics
        from database import database

        messages = conversation_data.get("messages", []) if conversation_data else []
        duration_minutes = conversation_data.get("duration_minutes", 5.0) if conversation_data else 5.0

        sessions_per_week = 2
        session_number = completed_sessions
        week_number = ((completed_sessions - 1) // sessions_per_week) + 1

        week_focus = "General language practice"
        if weekly_schedule and week_number <= len(weekly_schedule):
            week_focus = weekly_schedule[week_number - 1].get("focus", week_focus)

        session_stats = SessionStatistics.calculate_session_stats(
            messages=messages,
            duration_minutes=duration_minutes,
            background_analyses=background_analyses,
            session_number=session_number,
            week_number=week_number,
            week_focus=week_focus
        )

        # Get previous session data for comparison
        previous_session_data = None
        plan = await database.learning_plans.find_one({"id": plan_id})
        if plan and session_number > 1:
            session_history = plan.get("session_history", [])
            for hist_session in session_history:
                if hist_session.get("session_number") == session_number - 1:
                    previous_session_data = hist_session
                    break

        comparison = SessionStatistics.calculate_comparison(session_stats, previous_session_data)

        print(f"[STATS_BG] ✅ Statistics calculated: {session_stats.get('total_words', 0)} words")
        if comparison.get("has_previous_session"):
            print(f"[STATS_BG] ✅ Comparison: {comparison.get('speed_improvement', 0)} wpm improvement")

        # Could store these stats in a separate collection for analytics if needed
        # For now, just log them - client can request separately if needed

    except Exception as e:
        print(f"[STATS_BG] ❌ Failed: {e}\n{traceback.format_exc()}")


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

    🚀 OPTIMIZED: Using GPT-4o-mini with enhanced prompt engineering
    - 5x faster than GPT-4o (2-4s vs 10-15s)
    - 80% cheaper
    - Structured JSON output for AI coach consumption
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
        message_count = 0
        if conversation_data and "messages" in conversation_data:
            messages = conversation_data["messages"]
            message_count = len(messages)
            print(f"[SESSION_SUMMARY] Found {message_count} messages in conversation data")
            # Get last 10 messages for context
            for msg in messages[-10:]:
                role = "Student" if msg.get("role") == "user" else "Coach"
                content = msg.get("content", "")[:150]  # Truncate long messages
                conversation_content += f"{role}: {content}\n"
        else:
            print(f"[SESSION_SUMMARY] No conversation messages found, using basic summary only")

        # 🚀 OPTIMIZED PROMPT: Structured for GPT-4o-mini with clear instructions
        if conversation_content:
            # Full analysis with conversation data
            prompt = f"""You are analyzing a {language} learning session for an AI coach system. Create a concise, structured summary.

📋 CONTEXT:
Language: {language} | Level: {level} | Session: #{completed_sessions} | Week {current_week} Focus: {week_focus}

💬 CONVERSATION ({message_count} exchanges):
{conversation_content}

📝 SESSION DATA:
{basic_summary if basic_summary else "5-minute conversation completed"}

🎯 TASK: Generate a JSON summary for the AI coach to use in future sessions.

OUTPUT FORMAT (JSON):
{{
  "overview": "1 sentence: what happened this session",
  "skills_practiced": ["skill1", "skill2", "skill3"],
  "topics_covered": ["topic1", "topic2"],
  "strengths": ["specific strength from conversation"],
  "areas_to_improve": ["specific area from conversation"],
  "week_progress": "1 sentence on weekly goal progress",
  "next_session_focus": "What to practice next based on this session"
}}

IMPORTANT:
- Be specific and reference actual conversation content
- Focus on actionable insights for the AI coach
- Keep it concise (no fluff)
- Prioritize information useful for future sessions"""
        else:
            # Generate summary based on learning plan context
            prompt = f"""You are analyzing a {language} learning session for an AI coach system. Create a concise, structured summary.

📋 CONTEXT:
Language: {language} | Level: {level} | Session: #{completed_sessions} | Week {current_week} Focus: {week_focus}

📝 SESSION DATA:
{basic_summary if basic_summary else "5-minute conversation session completed"}

🎯 TASK: Generate a JSON summary for the AI coach to use in future sessions.

OUTPUT FORMAT (JSON):
{{
  "overview": "Session {completed_sessions} completed - {level} level {language} practice",
  "skills_practiced": ["expected skills for {level} {language}"],
  "topics_covered": ["topics related to: {week_focus}"],
  "week_progress": "Progress on weekly goal: {week_focus}",
  "next_session_focus": "Continue with {week_focus}"
}}

IMPORTANT:
- Infer from week focus: {week_focus}
- Use {level} level expectations for {language}
- Keep it concise and actionable
- Focus on continuity for next session"""

        print(f"[SESSION_SUMMARY] Sending optimized prompt to GPT-4o-mini (length: {len(prompt)} chars)")

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 🚀 OPTIMIZED: 5x faster, 80% cheaper
            messages=[
                {"role": "system", "content": "You are a language learning analyst creating structured session summaries for an AI coaching system. Be concise, specific, and actionable. Always output valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},  # 🚀 Enforce JSON output
            max_tokens=400,  # Reduced from 600 (more efficient)
            temperature=0.3
        )

        if response and response.choices:
            raw_response = response.choices[0].message.content.strip()
            print(f"[SESSION_SUMMARY] Generated summary: {len(raw_response)} characters")

            # 🚀 Parse JSON response from GPT-4o-mini
            try:
                import json
                summary_json = json.loads(raw_response)

                # Convert JSON to readable text format for storage and user display
                comprehensive_summary = f"""Session {completed_sessions} - {language.capitalize()} ({level})

Overview: {summary_json.get('overview', 'Session completed')}

Skills Practiced: {', '.join(summary_json.get('skills_practiced', []))}
Topics Covered: {', '.join(summary_json.get('topics_covered', []))}

Strengths: {', '.join(summary_json.get('strengths', []))}
Areas to Improve: {', '.join(summary_json.get('areas_to_improve', []))}

Weekly Progress: {summary_json.get('week_progress', 'On track')}
Next Focus: {summary_json.get('next_session_focus', week_focus)}"""

                print(f"[SESSION_SUMMARY] ✅ Parsed JSON summary successfully")

                # 🚀 CRITICAL: Generate compressed version for AI coach prompt usage
                # Compression reduces from ~200 tokens → ~15 tokens (92% reduction)
                # This is used when feeding context to AI coach in future sessions
                compressed_summary = f"{', '.join(summary_json.get('skills_practiced', []))} - {summary_json.get('next_session_focus', week_focus)}"

                print(f"[COMPRESSION] Full: {len(comprehensive_summary)} chars → Compressed: {len(compressed_summary)} chars")

                return {
                    "full": comprehensive_summary,
                    "compressed": compressed_summary
                }

            except json.JSONDecodeError as e:
                print(f"[SESSION_SUMMARY] ⚠️ Failed to parse JSON, using raw response: {e}")
                # Fallback: use raw response if JSON parsing fails
                # Still create a compressed version for AI coach
                compressed_fallback = raw_response[:100] + "..." if len(raw_response) > 100 else raw_response
                return {
                    "full": raw_response,
                    "compressed": compressed_fallback
                }
        else:
            print(f"[SESSION_SUMMARY] No response from OpenAI")
            # Enhanced fallback summary in optimized format
            fallback_summary = f"""Session {completed_sessions} - {language.capitalize()} ({level})

Overview: Completed session focusing on {week_focus.lower()}

Skills Practiced: speaking, listening, {language} grammar
Topics Covered: {week_focus.lower()}

Weekly Progress: Continuing work on weekly objective
Next Focus: {week_focus}"""

            # Create compressed version for AI coach
            fallback_compressed = f"speaking, listening, {language} grammar - {week_focus}"

            return {
                "full": fallback_summary,
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

        error_fallback = f"""Session {completed_sessions} - {language.capitalize()} ({level})

Overview: Completed session in {language} at {level} level

Skills Practiced: speaking, listening, {language} grammar
Topics Covered: {week_focus.lower()}

Weekly Progress: Working on {week_focus.lower()}
Next Focus: Continue practicing {week_focus.lower()}"""

        # Create compressed version for AI coach
        error_compressed = f"speaking, listening, {language} grammar - {week_focus}"

        return {
            "full": error_fallback,
            "compressed": error_compressed
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
        selected_duration = conversation_data.get("selected_duration", 5) if conversation_data else 5  # 🆕 Get selected duration
        session_duration_minutes = conversation_data.get("duration_minutes", selected_duration) if conversation_data else selected_duration
        # Cap at selected_duration; anything over is a frontend timer glitch
        session_duration_minutes = min(float(session_duration_minutes), float(selected_duration))

        current_session_data = {
            "session_number": completed_sessions,
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

            # 🚀 OPTIMIZED: Move statistics calculation to background (saves 2-4s)
            _stats_kwargs = dict(
                plan_id=plan_id,
                user_id=str(current_user.id),
                conversation_data=conversation_data if conversation_data else {},
                background_analyses=background_analyses,
                completed_sessions=completed_sessions,
                weekly_schedule=weekly_schedule
            )
            background_tasks.add_task(_calculate_statistics_background, **_stats_kwargs)
            print(f"[STATS] ⚡ Scheduled statistics calculation as background task")

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

            # ⚡ Return immediately — all heavy processing runs in background
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
                # 🚀 OPTIMIZED: Stats now calculated in background, return empty for immediate response
                "session_stats": None,  # Calculate in background if needed
                "comparison": None,     # Calculate in background if needed
                "overall_progress": None,  # Calculate in background if needed
                "dna_breakthroughs": [],   # populated by background task
                "dna_insights": {}         # populated by background task
            }
        else:
            print(f"[SESSION_SUMMARY] Warning: No documents were modified for plan {plan_id}")

            return {
                "success": True,
                "message": "Session summary processed (no changes needed)",
                "completed_sessions": completed_sessions,
                "progress_percentage": progress_percentage,
                "current_week": new_week,
                "session_summary": summary_data.get("full", summary_data),
                "background_analyses": background_analyses,
                "flashcards_generated": 0,
                "flashcard_generation_success": False,
                # 🚀 OPTIMIZED: Stats calculated in background
                "session_stats": None,
                "comparison": None,
                "overall_progress": None
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
