"""
Voice Journal Routes  (S3.6)

Daily 90-second voice prompt ritual.

Endpoints:
  GET  /api/voice-journal/today   — today's prompt + recorded status
  POST /api/voice-journal/record  — submit a recording (audio base64 or transcript)
  GET  /api/voice-journal/archive — paginated history of past entries
"""

import traceback
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from database import database
from models import UserResponse
from services.voice_journal_service import (
    get_today_journal_status,
    get_today_prompt,
    _normalise_language,
    _normalise_level,
)

router = APIRouter(prefix="/api/voice-journal", tags=["voice_journal"])

# Collection reference — access via database.voice_journal_entries
_COLLECTION = "voice_journal_entries"

# OpenAI transcription model: mirrors the pattern used elsewhere in the backend
_USE_GPT4O_TRANSCRIBE = os.getenv("USE_GPT4O_TRANSCRIBE", "true").lower() == "true"


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────────────────────────

class RecordJournalRequest(BaseModel):
    language: str
    level: str
    prompt_id: str
    prompt_text: str
    duration_seconds: float
    # Client may send base64 audio OR a pre-transcribed text (or both).
    # audio_base64 is optional — if absent we do transcript-only DNA.
    audio_base64: Optional[str] = None
    transcript: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Background helpers
# ──────────────────────────────────────────────────────────────────────────────

async def _transcribe_audio(audio_base64: str, language: str) -> Optional[str]:
    """Transcribe base64 audio via OpenAI (gpt-4o-transcribe with whisper-1 fallback)."""
    try:
        import base64
        import io
        from openai_client import get_async_openai
        client = get_async_openai()
        audio_data = base64.b64decode(audio_base64)
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "voice_journal.wav"

        if _USE_GPT4O_TRANSCRIBE:
            try:
                resp = await client.audio.transcriptions.create(
                    model="gpt-4o-transcribe",
                    file=audio_file,
                )
                return resp.text
            except Exception as gpt4o_err:
                print(f"[VOICE_JOURNAL] gpt-4o-transcribe failed: {gpt4o_err} — falling back to whisper-1")
                audio_file.seek(0)

        resp = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language[:2] if len(language) >= 2 else None,
        )
        return resp.text
    except Exception as e:
        print(f"[VOICE_JOURNAL] Transcription failed: {e}")
        return None


async def _dna_update_background(
    user_id: str,
    language: str,
    duration_seconds: float,
    transcript: str,
    audio_base64: Optional[str],
) -> None:
    """Fire DNA analysis in the background (S3.6: voice_journal session type)."""
    try:
        from services.speaking_dna_service import speaking_dna_service
        session_data: Dict[str, Any] = {
            "session_id": f"voice_journal_{user_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            "session_type": "voice_journal",
            "duration_seconds": int(duration_seconds),
            "user_turns": [{"text": transcript, "role": "user"}] if transcript else [],
            "corrections_received": [],
            "challenges_offered": 0,
            "challenges_accepted": 0,
            "topics_discussed": [language],
        }
        # S3.1: audio_base64 present → has_audio=True → acoustic strands update
        # audio_base64 absent  → has_audio=False → acoustic strands pinned
        if audio_base64:
            session_data["audio_base64"] = audio_base64

        result = await speaking_dna_service.analyze_session_for_dna(
            user_id=user_id, language=language, session_data=session_data
        )
        print(f"[VOICE_JOURNAL_DNA] DNA update complete. Breakthroughs: {len(result.get('breakthroughs', []))}")
    except Exception as e:
        print(f"[VOICE_JOURNAL_DNA] DNA update failed (non-fatal): {e}\n{traceback.format_exc()}")


async def _flashcard_background(
    user_id: str, language: str, level: str, prompt_text: str, transcript: str
) -> None:
    """Generate flashcards from the journal transcript in the background."""
    try:
        from flashcard_service import FlashcardService
        from models import FlashcardGenerationRequest
        import uuid

        req = FlashcardGenerationRequest(
            session_id=f"voice_journal_{user_id}_{uuid.uuid4()}",
            language=language,
            level=level,
            topic="voice_journal",
            conversation_content=None,
            session_summary=f"Voice journal prompt: {prompt_text}\n\nUser response: {transcript}",
            count=3,
        )
        flashcard_set = await FlashcardService.generate_flashcards(req, user_id)
        if flashcard_set and flashcard_set.flashcards:
            set_doc = flashcard_set.dict()
            set_doc["_id"] = ObjectId()
            set_doc["created_at"] = datetime.now(timezone.utc)
            card_docs = [dict(**c.dict(), _id=ObjectId()) for c in flashcard_set.flashcards]
            await database.flashcard_sets.insert_one(set_doc)
            if card_docs:
                result = await database.flashcards.insert_many(card_docs)
                print(f"[VOICE_JOURNAL_FLASHCARD] Saved {len(result.inserted_ids)} flashcards")
        else:
            print("[VOICE_JOURNAL_FLASHCARD] Empty result — skipped")
    except Exception as e:
        print(f"[VOICE_JOURNAL_FLASHCARD] Failed (non-fatal): {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/today")
async def get_today(
    language: str = "english",
    level: str = "B1",
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Return today's prompt and recording status for the authenticated user.

    Response:
        {
          "prompt": { prompt_id, prompt_text, language, level },
          "already_recorded": bool,
          "entry": <entry doc or null>
        }
    """
    try:
        status = await get_today_journal_status(
            user_id=str(current_user.id),
            language=language,
            level=level,
        )
        return status
    except Exception as e:
        print(f"[VOICE_JOURNAL] /today error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to load today's voice journal prompt")


@router.post("/record", status_code=201)
async def record_entry(
    request: RecordJournalRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Submit today's voice journal recording.

    Validates:
      - Duration ≤ 95 seconds
      - Not already recorded today (idempotent — 409 on duplicate)

    Schedules:
      - DNA update (background)
      - Flashcard generation (background)

    Returns:
        { "entry_id": str, "transcript": str }
    """
    user_id = str(current_user.id)
    lang_key = _normalise_language(request.language)
    level_key = _normalise_level(lang_key, request.level)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── Validation: duration ─────────────────────────────────────────────────
    if request.duration_seconds > 95:
        raise HTTPException(
            status_code=422,
            detail=f"Recording too long ({request.duration_seconds:.0f}s). Maximum is 90 seconds.",
        )

    # ── Idempotency: one entry per user/language/day ─────────────────────────
    collection = database.voice_journal_entries
    existing = await collection.find_one(
        {"user_id": user_id, "language": lang_key, "entry_date": date_str}
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="You have already recorded a voice journal entry for today.",
        )

    # ── Transcription ────────────────────────────────────────────────────────
    transcript = request.transcript or ""
    if not transcript and request.audio_base64:
        transcript = await _transcribe_audio(request.audio_base64, lang_key) or ""

    # ── Snapshot current DNA strands ─────────────────────────────────────────
    dna_snapshot: Dict[str, Any] = {}
    try:
        dna_doc = await database.speaking_dna.find_one(
            {"user_id": user_id, "language": lang_key},
            {"_id": 0, "dna_strands": 1},
        )
        if dna_doc:
            dna_snapshot = dna_doc.get("dna_strands", {})
    except Exception:
        pass  # non-fatal

    # ── Insert entry ─────────────────────────────────────────────────────────
    entry_id = ObjectId()
    entry_doc = {
        "_id": entry_id,
        "user_id": user_id,
        "language": lang_key,
        "entry_date": date_str,
        "prompt_id": request.prompt_id,
        "prompt_text": request.prompt_text,
        "transcript": transcript,
        "duration_seconds": request.duration_seconds,
        "dna_strands_at_recording": dna_snapshot,
        "created_at": datetime.now(timezone.utc),
    }
    await collection.insert_one(entry_doc)
    print(f"[VOICE_JOURNAL] Saved entry {entry_id} for user {user_id} on {date_str}")

    # ── Background: DNA update ───────────────────────────────────────────────
    background_tasks.add_task(
        _dna_update_background,
        user_id=user_id,
        language=lang_key,
        duration_seconds=request.duration_seconds,
        transcript=transcript,
        audio_base64=request.audio_base64,
    )

    # ── Background: flashcards (only when we have a transcript) ─────────────
    if transcript:
        background_tasks.add_task(
            _flashcard_background,
            user_id=user_id,
            language=lang_key,
            level=level_key,
            prompt_text=request.prompt_text,
            transcript=transcript,
        )

    return {"entry_id": str(entry_id), "transcript": transcript}


@router.get("/archive")
async def get_archive(
    language: str = "english",
    page: int = 1,
    page_size: int = 20,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Return the user's past voice journal entries, newest first.

    Query params:
        language  — filter by language (default "english")
        page      — 1-based page number
        page_size — entries per page (max 50)

    Response:
        { "entries": [...], "total": int, "page": int, "page_size": int }
    """
    user_id = str(current_user.id)
    lang_key = _normalise_language(language)
    page_size = min(page_size, 50)
    skip = (max(page, 1) - 1) * page_size

    collection = database.voice_journal_entries
    query = {"user_id": user_id, "language": lang_key}
    total = await collection.count_documents(query)
    cursor = (
        collection.find(query, {"_id": 0, "dna_strands_at_recording": 0})
        .sort("entry_date", -1)
        .skip(skip)
        .limit(page_size)
    )
    entries = await cursor.to_list(length=page_size)

    return {
        "entries": entries,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
