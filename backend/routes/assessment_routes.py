"""
Assessment Routes
Handles sentence construction assessment, speaking assessment, and sentence evaluation
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
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

@router.get("/api/speaking/can-assess")
async def check_can_assess(current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)):
    """Lightweight check: can this user start a speaking assessment? Call before recording."""
    if not current_user:
        return {"can_access": True, "message": ""}

    # Assessment limits removed — all users can assess without restriction
    return {"can_access": True, "message": ""}


@router.get("/api/speaking/assessment-prompt")
async def get_assessment_prompt(
    language: str = "english",
    level: Optional[str] = None,
):
    """
    Return a level-appropriate speaking task prompt to show the user
    BEFORE they start recording their assessment.

    Research basis: Structured elicitation tasks produce more reliable CEFR
    evidence than blank-slate monologues.  Prompts are calibrated per level:
      A1/A2 — concrete personal topics (no abstract reasoning required)
      B1    — narrative/experiential (past events, preferences with reasons)
      B2+   — opinion/argument (abstract topics, hypothetical scenarios)

    Query params:
      language: target language (default: english)
      level:    CEFR hint A1/A2/B1/B2/C1/C2 (optional — uses A1/A2 defaults if absent)

    Returns:
      prompt_text:     The task instruction shown to the learner (in English)
      prompt_native:   Same instruction translated into the target language
      tip:             Brief recording tip
      min_words:       Recommended minimum word count for a reliable score
      level_used:      The CEFR band that determined the prompt selection
    """
    # ── Level-appropriate prompt library ────────────────────────────────────
    # Keyed by CEFR band. Each entry has:
    #   task   — what to speak about (A1/A2: always concrete & personal)
    #   tip    — brief encouragement shown below the recording button
    _PROMPTS = {
        "A1": {
            "task": (
                "Tell us about yourself. Say your name, where you are from, "
                "your age, and one thing you like. Speak for about 45-60 seconds."
            ),
            "tip": "Speak slowly and clearly. Simple sentences are perfect!",
            "min_words": 30,
        },
        "A2": {
            "task": (
                "Describe your daily routine. What do you usually do in the morning, "
                "afternoon, and evening? Also tell us about one hobby you enjoy. "
                "Speak for about 60 seconds."
            ),
            "tip": "Use short, clear sentences. It is fine to pause and think.",
            "min_words": 45,
        },
        "B1": {
            "task": (
                "Tell us about a memorable experience — a trip, a celebration, "
                "or something interesting that happened to you. Describe what "
                "happened and how you felt. Speak for about 60 seconds."
            ),
            "tip": "Use past tense and connecting words like 'first', 'then', 'because'.",
            "min_words": 60,
        },
        "B2": {
            "task": (
                "What do you think is the most important skill a person can learn "
                "today, and why? Give your opinion and support it with examples. "
                "Speak for about 60-90 seconds."
            ),
            "tip": "Express your opinion clearly and give reasons for your view.",
            "min_words": 80,
        },
        "C1": {
            "task": (
                "Discuss the advantages and disadvantages of social media on "
                "modern communication. Consider both personal and professional "
                "aspects and give your overall conclusion. Speak for about 90 seconds."
            ),
            "tip": "Use complex structures, varied vocabulary, and a clear argument.",
            "min_words": 100,
        },
        "C2": {
            "task": (
                "To what extent do you think artificial intelligence will change "
                "the nature of human creativity? Develop a nuanced argument with "
                "examples and a conclusion. Speak for about 90-120 seconds."
            ),
            "tip": "Demonstrate sophisticated vocabulary, nuance, and logical structure.",
            "min_words": 120,
        },
    }

    # Normalise level
    _VALID_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
    level_used = (level or "A1").upper().strip()
    if level_used not in _VALID_LEVELS:
        level_used = "A1"

    prompt_cfg = _PROMPTS[level_used]

    # Translate task prompt into the target language using gpt-4.1-mini
    prompt_native = prompt_cfg["task"]  # fallback = English
    try:
        _LANG_NAMES = {
            "english": "English", "dutch": "Dutch", "spanish": "Spanish",
            "french": "French", "german": "German", "portuguese": "Portuguese",
            "italian": "Italian", "turkish": "Turkish",
        }
        target_lang_name = _LANG_NAMES.get(language.lower(), language.capitalize())

        if language.lower() != "english":
            from sentence_assessment import create_openai_client
            _client = create_openai_client()
            tr_resp = await _client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Translate the following speaking task instruction into "
                            f"{target_lang_name}. Keep the tone friendly and clear. "
                            f"Return ONLY the translated text, nothing else."
                        ),
                    },
                    {"role": "user", "content": prompt_cfg["task"]},
                ],
                temperature=0.1,
                max_tokens=200,
            )
            if tr_resp.choices and tr_resp.choices[0].message.content:
                prompt_native = tr_resp.choices[0].message.content.strip()

    except Exception as tr_err:
        print(f"[ASSESSMENT_PROMPT] Translation failed (non-fatal): {tr_err}")
        # Fall back to English prompt — safe

    return {
        "prompt_text":   prompt_cfg["task"],
        "prompt_native": prompt_native,
        "tip":           prompt_cfg["tip"],
        "min_words":     prompt_cfg["min_words"],
        "level_used":    level_used,
        "language":      language.lower(),
    }


@router.post("/api/speaking/assess")
async def assess_speaking(request: SpeakingAssessmentRequest, current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)):
    temp_audio_path = None  # Initialize early so finally block is safe regardless of exit path
    try:
        # Assessment limits removed — all users can assess without restriction

        # 🔥 NEW: Save audio to temp file for both transcription AND Azure pronunciation assessment
        recognized_text = None

        if request.audio_base64:
            try:
                print("Transcribing audio for speaking assessment...")

                # Create temp audio file that persists for the entire assessment
                import base64
                import tempfile
                from audio_format_validator import AudioFormatValidator

                audio_data = base64.b64decode(request.audio_base64)
                is_valid, error_message, metadata = AudioFormatValidator.validate_audio_data(request.audio_base64)

                if is_valid:
                    temp_audio_path, _ = AudioFormatValidator.create_temp_audio_file(audio_data, metadata)
                    print(f"📁 [ASSESSMENT] Created temp audio file for Azure pronunciation: {temp_audio_path}")

                # Transcribe audio
                recognized_text = await recognize_speech(request.audio_base64, request.language)
                print(f"Transcribed text: '{recognized_text}'")
            except Exception as e:
                print(f"Error transcribing audio: {str(e)}")
                # Clean up temp file if transcription fails
                if temp_audio_path:
                    AudioFormatValidator.cleanup_temp_file(temp_audio_path)
                raise HTTPException(status_code=400, detail="Failed to transcribe audio")

        if not recognized_text or recognized_text.strip() == "":
            # Clean up temp file if no speech detected
            if temp_audio_path:
                AudioFormatValidator.cleanup_temp_file(temp_audio_path)
            raise HTTPException(status_code=400, detail="No speech detected")

        # Evaluate language proficiency with audio file path for Azure pronunciation
        assessment = await evaluate_language_proficiency(
            text=recognized_text,
            language=request.language,
            duration=request.duration or 60,
            prompt=request.prompt,
            audio_file_path=temp_audio_path  # 🔥 NEW: Pass audio file path
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
                    "audio_format": "wav",  # ✅ Fixed: Mobile app sends WAV, not M4A
                    # 🔥 NEW: Include assessment scores for accurate DNA strand calculation
                    "assessment_scores": {
                        "grammar": assessment.get("grammar", {}).get("score", 50),
                        "vocabulary": assessment.get("vocabulary", {}).get("score", 50),
                        "fluency": assessment.get("fluency", {}).get("score", 50),
                        "pronunciation": assessment.get("pronunciation", {}).get("score", 50),
                        "coherence": assessment.get("coherence", {}).get("score", 50),
                        "overall_score": assessment.get("overall_score", 50)
                    }
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
                print(f"[DNA_ASSESSMENT] Traceback: {traceback.format_exc()}")
                # Don't fail assessment if DNA analysis fails
                pass

        # RETRY FEATURE: Save assessment data for learning plan creation
        # Assessment quota is ONLY consumed when user creates a learning plan, not during retries
        if current_user:
            try:
                print(f"[ASSESSMENT_SAVE] Saving assessment data to user record for later plan creation")

                from database import users_collection

                result = await users_collection.update_one(
                    {"_id": ObjectId(current_user.id)},
                    {
                        "$set": {"last_assessment_data": assessment},
                        # Lifetime assessment counter at the same `lifetime.*`
                        # level the other lifetime counters use (challenge
                        # pipeline writes `lifetime.total_sessions`,
                        # `lifetime.total_xp`, etc — keeping assessments in
                        # the same namespace lets the lifetime endpoint and
                        # BADGE_REGISTRY surface them without a schema fork).
                        "$inc": {
                            "stats.lifetime.assessments_completed": 1,
                        },
                    }
                )

                if result.modified_count > 0:
                    print(f"[ASSESSMENT_SAVE] Assessment data saved to user record")
                else:
                    print(f"[ASSESSMENT_SAVE] Failed to save assessment data to user record")

            except Exception as save_error:
                print(f"[ASSESSMENT_SAVE] Error saving assessment data: {str(save_error)}")
        else:
            print(f"[ASSESSMENT_SAVE] No authenticated user - skipping data save")

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

        # 🌍 LOCALE TRANSLATION: If the client sent a non-English UI locale,
        # generate translated versions of all user-facing text fields.
        # This is always additive — English fields are never removed.
        # On failure the original English assessment is returned unchanged.
        ui_locale = getattr(request, "ui_locale", None)
        if ui_locale:
            try:
                from assessment_translation_service import translate_assessment
                assessment = await translate_assessment(assessment, ui_locale)
                assessment["ui_locale"] = ui_locale
                print(f"[TRANSLATION] Assessment translated for locale: {ui_locale}")
            except Exception as translation_error:
                print(f"[TRANSLATION] ⚠️ Translation failed (non-fatal): {translation_error}")
                # English fields are always present — safe to continue

        # Save updated assessment (with translations) to user record
        if current_user:
            try:
                from database import users_collection
                from bson import ObjectId as BsonObjectId
                await users_collection.update_one(
                    {"_id": BsonObjectId(current_user.id)},
                    {"$set": {"last_assessment_data": assessment}}
                )
            except Exception as save_error:
                print(f"[ASSESSMENT_SAVE] Re-save after translation failed: {save_error}")

        # HIGH PRIORITY: Invalidate TaalCoach cache so it knows about the new assessment
        if current_user:
            try:
                from cache_helpers import invalidate_coach_context_smart, invalidate_taalcoach_context
                await invalidate_coach_context_smart(current_user.id, ["assessment", "progress"])
                await invalidate_taalcoach_context(current_user.id)
                print(f"[CACHE] Invalidated TaalCoach cache for user {current_user.id} after assessment")
            except Exception as cache_error:
                print(f"[CACHE] Warning: Failed to invalidate cache: {str(cache_error)}")

        print(f"Successfully analyzed speaking proficiency")
        return assessment

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Error in speaking assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error assessing speaking: {str(e)}")
    finally:
        # 🔥 NEW: Clean up temp audio file
        if temp_audio_path:
            try:
                from audio_format_validator import AudioFormatValidator
                AudioFormatValidator.cleanup_temp_file(temp_audio_path)
                print(f"🗑️ [ASSESSMENT] Cleaned up temp audio file: {temp_audio_path}")
            except Exception as cleanup_error:
                print(f"⚠️ [ASSESSMENT] Failed to cleanup temp file: {cleanup_error}")

@router.post("/api/speaking/assess-upload")
async def assess_speaking_upload(
    audio: UploadFile = File(...),
    language: str = Form(...),
    duration: int = Form(60),
    prompt: Optional[str] = Form(None),
    ui_locale: Optional[str] = Form(None),
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request),
):
    """Multipart upload variant of /api/speaking/assess — avoids large base64 JSON body."""
    import base64
    audio_bytes = await audio.read()
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    from speaking_assessment import SpeakingAssessmentRequest
    req = SpeakingAssessmentRequest(
        audio_base64=audio_base64,
        language=language,
        duration=duration,
        prompt=prompt,
        ui_locale=ui_locale,
    )
    return await assess_speaking(req, current_user)


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
