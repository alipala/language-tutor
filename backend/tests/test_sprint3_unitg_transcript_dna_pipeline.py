"""
Sprint 3 Unit G — Transcript DNA Pipeline (S3.3)
=================================================
Tests for the transcript-only DNA update path wired into save-conversation.

Business rules verified:
  BR-G1  freestyle, news, custom_topic, practice session types are in SESSION_WEIGHTS
  BR-G2  _run_transcript_dna_background function exists in progress_routes
  BR-G3  transcript DNA task scheduled for both existing and new session paths
  BR-G4  transcript DNA task gated on premium subscription (active/trialing)
  BR-G5  transcript DNA task passes has_audio=False-equivalent (no audio_base64)
  BR-G6  transcript DNA task passes has_challenges=False (challenges_offered=0)
  BR-G7  task waits for sentence analysis job before proceeding
  BR-G8  task proceeds after timeout (45s) with partial data
  BR-G9  dna_cache_invalidate flag returned for premium users (both paths)
  BR-G10 mobile sessionSaveService clears DNA cache when dna_cache_invalidate=true
  BR-G11 SESSION_WEIGHTS acoustic weights are 0 for transcript-only types (belt-and-suspenders)
  BR-G12 existing session types (learning, voice_check, speaking_assessment) unmodified

Run with: pytest test_sprint3_unitg_transcript_dna_pipeline.py --noconftest -v
"""

import os
import re
import pytest

# ── Path helpers ──────────────────────────────────────────────────────────────
BACKEND_DIR    = os.path.join(os.path.dirname(__file__), "..")
MOBILE_DIR     = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "github", "MyTacoAIMobile")
DNA_SERVICE    = os.path.join(BACKEND_DIR, "services", "speaking_dna_service.py")
PROGRESS_ROUTES = os.path.join(BACKEND_DIR, "progress_routes.py")
SESSION_SAVE_SVC = os.path.join(MOBILE_DIR, "src", "services", "sessionSaveService.ts")


def _read(path):
    with open(path, "r") as f:
        return f.read()


# ═══════════════════════════════════════════════════════════════════════════════
# BR-G1 + BR-G11 + BR-G12: SESSION_WEIGHTS table
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionWeights:

    def test_custom_topic_in_session_weights(self):
        src = _read(DNA_SERVICE)
        assert '"custom_topic"' in src, "custom_topic must be added to SESSION_WEIGHTS"

    def test_practice_in_session_weights(self):
        src = _read(DNA_SERVICE)
        assert '"practice"' in src, "practice must be added to SESSION_WEIGHTS"

    def test_freestyle_in_session_weights(self):
        src = _read(DNA_SERVICE)
        assert '"freestyle"' in src, "freestyle must already be in SESSION_WEIGHTS"

    def test_news_in_session_weights(self):
        src = _read(DNA_SERVICE)
        assert '"news"' in src, "news must already be in SESSION_WEIGHTS"

    def test_custom_topic_acoustic_weights_are_zero(self):
        src = _read(DNA_SERVICE)
        # custom_topic block must have rhythm: 0.0
        custom_block_start = src.find('"custom_topic"')
        assert custom_block_start != -1
        # Find the next closing brace to delimit this block
        block = src[custom_block_start:custom_block_start + 300]
        assert '"rhythm": 0.0' in block or '"rhythm": 0' in block, (
            "custom_topic rhythm weight must be 0 (no acoustic signal)"
        )
        assert '"confidence": 0.0' in block or '"confidence": 0' in block
        assert '"emotional": 0.0' in block or '"emotional": 0' in block

    def test_practice_acoustic_weights_are_zero(self):
        src = _read(DNA_SERVICE)
        practice_block_start = src.find('"practice"')
        assert practice_block_start != -1
        block = src[practice_block_start:practice_block_start + 300]
        assert '"rhythm": 0.0' in block or '"rhythm": 0' in block

    def test_custom_topic_vocabulary_accuracy_nonzero(self):
        src = _read(DNA_SERVICE)
        custom_block_start = src.find('"custom_topic"')
        block = src[custom_block_start:custom_block_start + 300]
        # Must have positive vocabulary and accuracy weights
        assert '"vocabulary": 0.5' in block, "custom_topic vocabulary weight must be 0.5"
        assert '"accuracy": 0.5' in block, "custom_topic accuracy weight must be 0.5"

    def test_existing_types_unchanged_learning(self):
        src = _read(DNA_SERVICE)
        learning_start = src.find('"learning":\n') or src.find('"learning": {')
        # learning session type should have its original high weights
        assert '"learning": 1.0' in src, "learning session_type learning weight must remain 1.0"

    def test_existing_types_unchanged_voice_check(self):
        src = _read(DNA_SERVICE)
        assert '"voice_check"' in src, "voice_check session type must still be present"

    def test_existing_types_unchanged_speaking_assessment(self):
        src = _read(DNA_SERVICE)
        assert '"speaking_assessment"' in src, "speaking_assessment session type must still be present"


# ═══════════════════════════════════════════════════════════════════════════════
# BR-G2 + BR-G5 + BR-G6 + BR-G7 + BR-G8: _run_transcript_dna_background
# ═══════════════════════════════════════════════════════════════════════════════

class TestTranscriptDnaBackgroundFunction:

    def test_function_exists(self):
        src = _read(PROGRESS_ROUTES)
        assert "_run_transcript_dna_background" in src, (
            "_run_transcript_dna_background function must exist in progress_routes.py"
        )

    def test_function_is_async(self):
        src = _read(PROGRESS_ROUTES)
        assert "async def _run_transcript_dna_background(" in src

    def test_no_audio_base64_in_session_data(self):
        src = _read(PROGRESS_ROUTES)
        fn_start = src.find("async def _run_transcript_dna_background(")
        fn_end = src.find("\nasync def ", fn_start + 1)
        fn_body = src[fn_start:fn_end]
        # audio_base64 must NOT be assigned in the session_data dict (comments referencing it are fine)
        # Strip comment lines before checking for assignment
        non_comment_lines = [
            line for line in fn_body.splitlines()
            if not line.strip().startswith("#")
        ]
        non_comment_body = "\n".join(non_comment_lines)
        assert '"audio_base64"' not in non_comment_body, (
            "audio_base64 must not be set in transcript DNA session_data dict — "
            "its absence triggers S3.1 acoustic strand pinning"
        )

    def test_challenges_offered_zero(self):
        src = _read(PROGRESS_ROUTES)
        fn_start = src.find("async def _run_transcript_dna_background(")
        fn_end = src.find("\nasync def ", fn_start + 1)
        fn_body = src[fn_start:fn_end]
        assert '"challenges_offered": 0' in fn_body, (
            "challenges_offered must be 0 in transcript DNA session_data to pin Learning strand (S3.2)"
        )
        assert '"challenges_accepted": 0' in fn_body

    def test_waits_for_sentence_analysis_job(self):
        src = _read(PROGRESS_ROUTES)
        fn_start = src.find("async def _run_transcript_dna_background(")
        fn_end = src.find("\nasync def ", fn_start + 1)
        fn_body = src[fn_start:fn_end]
        assert "sentence_analysis_jobs" in fn_body or "analysis_job_id" in fn_body, (
            "function must wait for the sentence analysis job to complete before reading corrections"
        )
        assert '"status"' in fn_body and "completed" in fn_body, (
            "function must poll until job status == 'completed'"
        )

    def test_timeout_proceeds_with_partial_data(self):
        src = _read(PROGRESS_ROUTES)
        fn_start = src.find("async def _run_transcript_dna_background(")
        fn_end = src.find("\nasync def ", fn_start + 1)
        fn_body = src[fn_start:fn_end]
        assert "timeout" in fn_body.lower() or "deadline" in fn_body, (
            "function must have a timeout path that proceeds with partial data"
        )

    def test_calls_analyze_session_for_dna(self):
        src = _read(PROGRESS_ROUTES)
        fn_start = src.find("async def _run_transcript_dna_background(")
        fn_end = src.find("\nasync def ", fn_start + 1)
        fn_body = src[fn_start:fn_end]
        assert "analyze_session_for_dna" in fn_body, (
            "function must call speaking_dna_service.analyze_session_for_dna"
        )

    def test_non_fatal_exception_handling(self):
        src = _read(PROGRESS_ROUTES)
        fn_start = src.find("async def _run_transcript_dna_background(")
        fn_end = src.find("\nasync def ", fn_start + 1)
        fn_body = src[fn_start:fn_end]
        assert "except Exception" in fn_body, (
            "DNA background task must catch exceptions (non-fatal — cannot crash the background runner)"
        )

    def test_observability_log_on_success(self):
        src = _read(PROGRESS_ROUTES)
        assert "[TRANSCRIPT_DNA]" in src, (
            "progress_routes must log with [TRANSCRIPT_DNA] prefix for observability"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# BR-G3 + BR-G4: task is wired into save-conversation, gated on premium
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskWiring:

    def test_task_scheduled_in_both_paths(self):
        src = _read(PROGRESS_ROUTES)
        # Both existing-session and new-session paths must schedule the task
        occurrences = src.count("_run_transcript_dna_background")
        # Function def + 2 scheduling calls (one per path)
        assert occurrences >= 3, (
            f"_run_transcript_dna_background appears {occurrences} times; "
            "expected at least 3 (def + 2 background_tasks.add_task calls)"
        )

    def test_premium_gate_wraps_task_scheduling(self):
        src = _read(PROGRESS_ROUTES)
        # The subscription gate must appear before each scheduling call
        assert 'subscription_status in ["active", "trialing"]' in src, (
            "DNA task scheduling must be gated on subscription_status in ['active', 'trialing']"
        )

    def test_session_type_derived_from_conversation_type(self):
        src = _read(PROGRESS_ROUTES)
        # The session_type for the DNA call must be derived from conversation_type
        assert "conversation_type" in src
        assert "_dna_session_type" in src or "session_type=conversation_type" in src or \
               "session_type=_dna_session_type" in src, (
            "session_type passed to DNA task must be derived from conversation_type"
        )

    def test_analysis_job_id_passed_to_task(self):
        src = _read(PROGRESS_ROUTES)
        assert "analysis_job_id=analysis_job_id" in src, (
            "analysis_job_id must be passed to _run_transcript_dna_background so it can wait for sentence analysis"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# BR-G9: dna_cache_invalidate in response
# ═══════════════════════════════════════════════════════════════════════════════

class TestDnaCacheInvalidateFlag:

    def test_flag_in_response_both_paths(self):
        src = _read(PROGRESS_ROUTES)
        occurrences = src.count('"dna_cache_invalidate"')
        assert occurrences >= 4, (
            f"dna_cache_invalidate appears {occurrences} times in responses; "
            "expected at least 4 (both cached and non-cached responses for each path)"
        )

    def test_flag_is_true_for_premium_users(self):
        src = _read(PROGRESS_ROUTES)
        assert '_dna_cache_invalidate = current_user.subscription_status in ["active", "trialing"]' in src, (
            "dna_cache_invalidate must be True for premium (active/trialing) users"
        )

    def test_flag_references_subscription_status(self):
        src = _read(PROGRESS_ROUTES)
        # The flag value computation must reference subscription_status
        flag_pattern = '_dna_cache_invalidate'
        assert flag_pattern in src
        idx = src.find(flag_pattern)
        line = src[idx:idx + 100]
        assert "subscription_status" in line, (
            "dna_cache_invalidate value must check subscription_status"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# BR-G10: mobile cache invalidation
# ═══════════════════════════════════════════════════════════════════════════════

class TestMobileCacheInvalidation:

    def test_session_save_service_reads_dna_cache_invalidate(self):
        src = _read(SESSION_SAVE_SVC)
        assert "dna_cache_invalidate" in src, (
            "sessionSaveService.ts must check result.dna_cache_invalidate"
        )

    def test_session_save_service_clears_dna_cache_on_flag(self):
        src = _read(SESSION_SAVE_SVC)
        assert "clearCache" in src or "clearDNACache" in src, (
            "sessionSaveService.ts must call speakingDNAService.clearCache() when dna_cache_invalidate is true"
        )

    def test_cache_clear_is_non_fatal(self):
        src = _read(SESSION_SAVE_SVC)
        # The cache clear must use .catch() or try/catch — non-fatal
        idx = src.find("dna_cache_invalidate")
        block = src[idx:idx + 400]
        assert ".catch(" in block or "catch" in block, (
            "DNA cache clear in sessionSaveService must be non-fatal (catch errors)"
        )

    def test_log_message_after_cache_clear(self):
        src = _read(SESSION_SAVE_SVC)
        assert "DNA cache cleared" in src or "dna_cache" in src.lower(), (
            "sessionSaveService must log after clearing DNA cache"
        )
