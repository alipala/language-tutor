"""
Assessment Routes
Handles sentence construction assessment, speaking assessment, and sentence evaluation
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from bson import ObjectId

from auth import get_optional_current_user_from_request
from models import UserResponse

# Import assessment modules
from sentence_assessment import (
    SentenceAssessmentRequest,
    SentenceAssessmentResponse,
    recognize_speech,
    analyze_sentence,
    generate_exercises
)

from speaking_assessment import (
    SpeakingAssessmentRequest,
    SpeakingAssessmentResponse,
    evaluate_language_proficiency,
    generate_speaking_prompts
)

from background_sentence_analysis import (
    SentenceEvaluationRequest,
    SentenceEvaluationResponse,
    BackgroundAnalysisRequest,
    BackgroundAnalysisResponse,
    evaluate_sentence_worthiness,
    perform_background_analysis,
    process_sentence_for_background_analysis
)

# Initialize router
router = APIRouter()

# Route Handlers
@router.post("/api/sentence/assess", response_model=SentenceAssessmentResponse)
async def assess_sentence_construction(request: SentenceAssessmentRequest):
    try:
        # Determine the text to analyze - prioritize transcript over audio
        recognized_text = None

        # First check if a transcript is provided - prioritize this
        if request.transcript and request.transcript.strip():
            print(f"Using provided transcript: '{request.transcript}'")
            recognized_text = request.transcript
        # If no transcript, try to transcribe audio if provided
        elif request.audio_base64:
            try:
                print("Attempting to transcribe audio...")
                recognized_text = await recognize_speech(request.audio_base64, request.language)
                print(f"Successfully transcribed audio: '{recognized_text}'")
            except Exception as audio_err:
                print(f"Error transcribing audio: {str(audio_err)}")
        # Use context as last resort if provided
        elif request.context:
            print(f"Using context as fallback: '{request.context}'")
            recognized_text = request.context

        if not recognized_text or recognized_text.strip() == "":
            print("No valid text found for analysis")
            raise HTTPException(status_code=400, detail="No speech detected or text provided for analysis")

        print(f"Proceeding with analysis of: '{recognized_text}'")

        # Analyze sentence
        assessment = await analyze_sentence(
            text=recognized_text,
            language=request.language,
            level=request.level,
            exercise_type=request.exercise_type
        )

        return assessment

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Error in sentence assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing sentence: {str(e)}")

@router.post("/api/speaking/assess", response_model=SpeakingAssessmentResponse)
async def assess_speaking(request: SpeakingAssessmentRequest, current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)):
    try:
        # CRITICAL FIX: Check assessment limits BEFORE processing the assessment
        if current_user:
            try:
                print(f"[ASSESSMENT_LIMIT_CHECK] Checking assessment limits for user {current_user.id}")

                from subscription_service import SubscriptionService
                can_access, access_message = await SubscriptionService.can_access_feature(current_user.id, "assessment")

                if not can_access:
                    print(f"[ASSESSMENT_LIMIT_CHECK] Assessment blocked: {access_message}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=access_message
                    )

                print(f"[ASSESSMENT_LIMIT_CHECK] Assessment limit check passed")

            except HTTPException:
                # Re-raise HTTP exceptions (limit exceeded)
                raise
            except Exception as limit_error:
                print(f"[ASSESSMENT_LIMIT_CHECK] Error checking limits: {str(limit_error)}")
                # Continue with assessment if limit check fails (don't block user)
                pass

        # Transcribe audio if provided
        recognized_text = None
        if request.audio_base64:
            try:
                print("Transcribing audio for speaking assessment...")
                recognized_text = await recognize_speech(request.audio_base64, request.language)
                print(f"Transcribed text: '{recognized_text}'")
            except Exception as e:
                print(f"Error transcribing audio: {str(e)}")
                raise HTTPException(status_code=400, detail="Failed to transcribe audio")

        if not recognized_text or recognized_text.strip() == "":
            raise HTTPException(status_code=400, detail="No speech detected")

        # Evaluate language proficiency
        assessment = await evaluate_language_proficiency(
            text=recognized_text,
            language=request.language,
            duration=request.duration or 60,
            prompt=request.prompt
        )

        # 🧬 NEW: Run DNA analysis on speaking assessment audio for initial acoustic baseline
        if current_user and request.audio_base64:
            try:
                print(f"[DNA_ASSESSMENT] 🧬 Analyzing speaking assessment audio for initial DNA profile")
                print(f"[DNA_ASSESSMENT] User: {current_user.id}, Language: {request.language}")

                from services.speaking_dna_service import SpeakingDNAService
                from datetime import datetime

                # Create session data for DNA analysis
                duration_ms = (request.duration or 60) * 1000  # Convert to milliseconds
                assessment_session_data = {
                    "session_id": f"assessment_{datetime.now().isoformat()}",
                    "session_type": "speaking_assessment",
                    "duration_seconds": request.duration or 60,
                    "user_turns": [{
                        "transcript": recognized_text,  # ✅ Fixed: use "transcript" not "text"
                        "start_time_ms": 0,  # ✅ Fixed: add start_time_ms
                        "end_time_ms": duration_ms,  # ✅ Fixed: add end_time_ms
                        "ai_prompt_end_time_ms": 0  # No AI prompt in assessment
                    }],
                    "corrections_received": [],  # No corrections in assessment
                    "challenges_offered": 0,
                    "challenges_accepted": 0,
                    "topics_discussed": [request.prompt or "Speaking Assessment"],
                    "audio_base64": request.audio_base64,
                    "audio_format": "wav"  # ✅ Fixed: Mobile app sends WAV, not M4A
                }

                # Initialize DNA service and analyze
                dna_service = SpeakingDNAService()
                dna_result = await dna_service.analyze_session_for_dna(
                    user_id=current_user.id,
                    language=request.language.lower(),
                    session_data=assessment_session_data
                )

                print(f"[DNA_ASSESSMENT] ✅ Initial DNA profile created/updated")
                print(f"[DNA_ASSESSMENT] Profile ID: {dna_result.get('profile', {}).get('_id')}")
                print(f"[DNA_ASSESSMENT] Strands analyzed: {len(dna_result.get('profile', {}).get('dna_strands', {}))}")
                print(f"[DNA_ASSESSMENT] Acoustic metrics captured: {bool(dna_result.get('profile', {}).get('baseline_assessment', {}).get('acoustic_metrics'))}")
                print(f"[DNA_ASSESSMENT] Breakthroughs detected: {len(dna_result.get('breakthroughs', []))}")

                # Log acoustic features if available
                acoustic = dna_result.get('profile', {}).get('baseline_assessment', {}).get('acoustic_metrics', {})
                if acoustic:
                    print(f"[DNA_ASSESSMENT] 🎤 Acoustic baseline established:")
                    print(f"[DNA_ASSESSMENT]    - Words per minute: {acoustic.get('words_per_minute', 'N/A')}")
                    print(f"[DNA_ASSESSMENT]    - Pause ratio: {acoustic.get('pause_ratio', 'N/A')}")
                    print(f"[DNA_ASSESSMENT]    - Voice quality: {acoustic.get('voice_quality_factor', 'N/A')}")
                    print(f"[DNA_ASSESSMENT]    - Filler rate: {acoustic.get('filler_rate_per_minute', 'N/A')}")

            except Exception as dna_error:
                print(f"[DNA_ASSESSMENT] ⚠️ DNA analysis failed (non-fatal): {str(dna_error)}")
                import traceback
                print(f"[DNA_ASSESSMENT] Traceback: {traceback.format_exc()}")
                # Don't fail assessment if DNA analysis fails
                pass

        # CRITICAL FIX: Track assessment usage AND save assessment data for authenticated users
        if current_user:
            try:
                print(f"[ASSESSMENT_TRACKING] Tracking assessment usage for user {current_user.id}")

                from subscription_service import SubscriptionService
                from models import UsageTrackingRequest
                from database import users_collection

                # Create usage tracking request
                usage_request = UsageTrackingRequest(
                    user_id=current_user.id,
                    usage_type="assessment",
                    duration_minutes=None
                )

                # Track the usage
                success = await SubscriptionService.track_usage(usage_request)
                if success:
                    print(f"[ASSESSMENT_TRACKING] Successfully tracked assessment usage for user {current_user.id}")
                else:
                    print(f"[ASSESSMENT_TRACKING] Usage tracking returned false for user {current_user.id}")

                # CRITICAL FIX 2: Save assessment data to user record for learning plan creation
                try:
                    print(f"[ASSESSMENT_TRACKING] Saving assessment data to user record")

                    result = await users_collection.update_one(
                        {"_id": ObjectId(current_user.id)},
                        {"$set": {"last_assessment_data": assessment}}
                    )

                    if result.modified_count > 0:
                        print(f"[ASSESSMENT_TRACKING] Assessment data saved to user record")
                    else:
                        print(f"[ASSESSMENT_TRACKING] Failed to save assessment data to user record")

                except Exception as save_error:
                    print(f"[ASSESSMENT_TRACKING] Error saving assessment data: {str(save_error)}")

            except Exception as tracking_error:
                print(f"[ASSESSMENT_TRACKING] Error tracking assessment usage: {str(tracking_error)}")
                # Don't fail the assessment if usage tracking fails
                pass
        else:
            print(f"[ASSESSMENT_TRACKING] No authenticated user - skipping usage tracking")

        # Fetch DNA profile if available (for authenticated users)
        dna_profile = None
        if current_user:
            try:
                from services.speaking_dna_service import SpeakingDNAService
                dna_service = SpeakingDNAService()
                dna_profile = await dna_service.get_dna_profile(current_user.id, request.language.lower())

                if dna_profile:
                    # Convert ObjectId to string for JSON serialization
                    if "_id" in dna_profile:
                        dna_profile["_id"] = str(dna_profile["_id"])
                    print(f"[ASSESSMENT] ✅ DNA profile fetched for response")
                else:
                    print(f"[ASSESSMENT] ℹ️ No DNA profile available yet")
            except Exception as dna_error:
                print(f"[ASSESSMENT] ⚠️ Failed to fetch DNA profile: {str(dna_error)}")

        # Add DNA profile to assessment response
        assessment["dna_profile"] = dna_profile

        print(f"Successfully analyzed speaking proficiency")
        return assessment

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Error in speaking assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error assessing speaking: {str(e)}")

@router.get("/api/speaking/prompts")
async def get_speaking_prompts(language: str, level: str, count: int = 3):
    try:
        prompts = await generate_speaking_prompts(language, level, count)
        return {"prompts": prompts}
    except Exception as e:
        print(f"Error generating speaking prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating prompts: {str(e)}")

@router.post("/api/sentence/evaluate", response_model=SentenceEvaluationResponse)
async def evaluate_sentence_for_analysis(request: SentenceEvaluationRequest):
    """
    Evaluate whether a sentence is substantial enough for analysis.
    This endpoint is used by the frontend to determine if background analysis should be triggered.
    """
    try:
        print(f"[EVALUATION] Evaluating sentence: '{request.text}'")

        evaluation = await evaluate_sentence_worthiness(
            text=request.text,
            language=request.language,
            level=request.level,
            conversation_context=request.conversation_context
        )

        print(f"[EVALUATION] Result: {evaluation['should_analyze']} - {evaluation['reason']}")

        return SentenceEvaluationResponse(
            should_analyze=evaluation["should_analyze"],
            reason=evaluation["reason"],
            confidence=evaluation["confidence"]
        )

    except Exception as e:
        print(f"[EVALUATION] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error evaluating sentence: {str(e)}")

@router.post("/api/sentence/background-analyze", response_model=BackgroundAnalysisResponse)
async def perform_background_sentence_analysis(request: BackgroundAnalysisRequest):
    """
    Perform background sentence analysis without interrupting the conversation.
    This endpoint analyzes the sentence and returns detailed assessment results.
    """
    try:
        print(f"[BACKGROUND_ANALYSIS] Analyzing sentence: '{request.text}'")

        analysis = await perform_background_analysis(
            text=request.text,
            language=request.language,
            level=request.level,
            exercise_type=request.exercise_type,
            conversation_context=request.conversation_context
        )

        print(f"[BACKGROUND_ANALYSIS] Analysis completed for: '{request.text}'")

        return BackgroundAnalysisResponse(
            analysis_id=analysis["analysis_id"],
            recognized_text=analysis["recognized_text"],
            grammatical_score=analysis["grammatical_score"],
            vocabulary_score=analysis["vocabulary_score"],
            complexity_score=analysis["complexity_score"],
            appropriateness_score=analysis["appropriateness_score"],
            overall_score=analysis["overall_score"],
            grammar_issues=analysis["grammar_issues"],
            improvement_suggestions=analysis["improvement_suggestions"],
            corrected_text=analysis.get("corrected_text"),
            level_appropriate_alternatives=analysis.get("level_appropriate_alternatives"),
            timestamp=analysis["timestamp"]
        )

    except Exception as e:
        print(f"[BACKGROUND_ANALYSIS] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error performing background analysis: {str(e)}")

@router.post("/api/sentence/process-background")
async def process_sentence_background(request: BackgroundAnalysisRequest):
    """
    Complete background sentence processing pipeline.
    Evaluates if sentence should be analyzed, and if so, performs the analysis.
    Returns None if sentence doesn't warrant analysis, otherwise returns analysis results.
    """
    try:
        print(f"[BACKGROUND_PROCESS] Processing sentence: '{request.text}'")

        result = await process_sentence_for_background_analysis(
            text=request.text,
            language=request.language,
            level=request.level,
            conversation_context=request.conversation_context
        )

        if not result or not result.get("analyzed"):
            reason = result.get("reason", "Sentence not substantial enough for analysis") if result else "Sentence not substantial enough for analysis"
            print(f"[BACKGROUND_PROCESS] Sentence skipped - {reason}")
            return {"analyzed": False, "reason": reason}

        # Extract analysis data from the result
        analysis_data = result.get("analysis", {})
        if not analysis_data:
            print(f"[BACKGROUND_PROCESS] No analysis data in result")
            return {"analyzed": False, "reason": "No analysis data available"}

        analysis_id = analysis_data.get("analysis_id", "unknown")
        print(f"[BACKGROUND_PROCESS] Analysis completed with ID: {analysis_id}")

        return {
            "analyzed": True,
            "analysis": BackgroundAnalysisResponse(
                analysis_id=analysis_id,
                recognized_text=analysis_data.get("recognized_text", request.text),
                grammatical_score=analysis_data.get("grammatical_score", 50.0),
                vocabulary_score=analysis_data.get("vocabulary_score", 50.0),
                complexity_score=analysis_data.get("complexity_score", 50.0),
                appropriateness_score=analysis_data.get("appropriateness_score", 50.0),
                overall_score=analysis_data.get("overall_score", 50.0),
                grammar_issues=analysis_data.get("grammar_issues", []),
                improvement_suggestions=analysis_data.get("improvement_suggestions", []),
                corrected_text=analysis_data.get("corrected_text"),
                level_appropriate_alternatives=analysis_data.get("level_appropriate_alternatives"),
                timestamp=analysis_data.get("timestamp", "")
            ),
            "evaluation": result.get("evaluation", {})
        }

    except Exception as e:
        print(f"[BACKGROUND_PROCESS] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing sentence: {str(e)}")
