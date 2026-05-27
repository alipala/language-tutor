"""
Sprint 3 Unit I — Voice Journal (S3.6)
=======================================
Static source-inspection tests.  No imports from the live backend — all assertions
are string searches on the raw source files, following the --noconftest pattern
used by the rest of the Sprint 3 test suite.

Business rules verified:
  BR-I1   voice_journal_routes.py exists
  BR-I2   voice_journal_service.py exists
  BR-I3   GET /today endpoint defined in routes
  BR-I4   POST /record endpoint defined with duration validation (≤ 95s)
  BR-I5   Duplicate recording rejected with 409
  BR-I6   DNA background task fires; audio_base64 passed through to enable has_audio
  BR-I7   "voice_journal" key present in SESSION_WEIGHTS (speaking_dna_service.py)
  BR-I8   voice_journal router registered in main.py
  BR-I9   VoiceJournalScreen.tsx exists (mobile)
  BR-I10  JournalArchiveScreen.tsx exists (mobile)
  BR-I11  DailyHubScreen includes a voice journal card / navigates to VoiceJournal
  BR-I12  App.js registers VoiceJournal and JournalArchive screens
  BR-I13  App.js deep-link config includes "voice-journal"

Run with: pytest tests/test_sprint3_uniti_voice_journal.py --noconftest -v
"""

import os
import pytest

# ── Path helpers ──────────────────────────────────────────────────────────────

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
MOBILE_DIR  = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "github", "MyTacoAIMobile")

ROUTES_FILE       = os.path.join(BACKEND_DIR, "routes", "voice_journal_routes.py")
SERVICE_FILE      = os.path.join(BACKEND_DIR, "services", "voice_journal_service.py")
DNA_SERVICE_FILE  = os.path.join(BACKEND_DIR, "services", "speaking_dna_service.py")
MAIN_FILE         = os.path.join(BACKEND_DIR, "main.py")

VJ_SCREEN_FILE    = os.path.join(MOBILE_DIR, "src", "screens", "VoiceJournal", "VoiceJournalScreen.tsx")
ARCH_SCREEN_FILE  = os.path.join(MOBILE_DIR, "src", "screens", "VoiceJournal", "JournalArchiveScreen.tsx")
HUB_SCREEN_FILE   = os.path.join(MOBILE_DIR, "src", "screens", "Dashboard", "DailyHubScreen.tsx")
APP_JS_FILE       = os.path.join(MOBILE_DIR, "App.js")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


# ═══════════════════════════════════════════════════════════════════════════════
# BR-I1 / BR-I2 — files exist
# ═══════════════════════════════════════════════════════════════════════════════

class TestFilesExist:

    def test_voice_journal_routes_exists(self):
        assert os.path.isfile(ROUTES_FILE), f"Missing: {ROUTES_FILE}"

    def test_voice_journal_service_exists(self):
        assert os.path.isfile(SERVICE_FILE), f"Missing: {SERVICE_FILE}"

    def test_vj_screen_exists(self):
        assert os.path.isfile(VJ_SCREEN_FILE), f"Missing: {VJ_SCREEN_FILE}"

    def test_archive_screen_exists(self):
        assert os.path.isfile(ARCH_SCREEN_FILE), f"Missing: {ARCH_SCREEN_FILE}"


# ═══════════════════════════════════════════════════════════════════════════════
# BR-I3 — GET /today endpoint
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetTodayEndpoint:

    def test_today_route_defined(self):
        src = _read(ROUTES_FILE)
        assert '"/today"' in src or "'/today'" in src, \
            "GET /today endpoint must be defined in voice_journal_routes.py"

    def test_today_returns_prompt_and_status(self):
        src = _read(ROUTES_FILE)
        assert "already_recorded" in src, \
            "Response must include already_recorded field"
        assert "prompt" in src, \
            "Response must include prompt field"


# ═══════════════════════════════════════════════════════════════════════════════
# BR-I4 — POST /record with duration validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestPostRecordEndpoint:

    def test_record_route_defined(self):
        src = _read(ROUTES_FILE)
        assert '"/record"' in src or "'/record'" in src, \
            "POST /record endpoint must be defined in voice_journal_routes.py"

    def test_duration_validation_present(self):
        src = _read(ROUTES_FILE)
        # Must check duration against the 95-second grace limit
        assert "95" in src, \
            "POST /record must validate duration ≤ 95 seconds"
        assert "duration_seconds" in src, \
            "POST /record must reference duration_seconds field"

    def test_duration_validation_raises_error(self):
        src = _read(ROUTES_FILE)
        # Must raise HTTP exception when duration is too long
        assert "422" in src or "HTTPException" in src, \
            "POST /record must raise an HTTP error for duration violations"


# ═══════════════════════════════════════════════════════════════════════════════
# BR-I5 — Duplicate rejection (409)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDuplicateRejection:

    def test_409_on_duplicate(self):
        src = _read(ROUTES_FILE)
        assert "409" in src, \
            "POST /record must return 409 when user has already recorded today"

    def test_idempotency_check_present(self):
        src = _read(ROUTES_FILE)
        # Must look up existing entry before inserting
        assert "find_one" in src, \
            "POST /record must check for an existing entry before inserting"


# ═══════════════════════════════════════════════════════════════════════════════
# BR-I6 — DNA background task with has_audio consideration
# ═══════════════════════════════════════════════════════════════════════════════

class TestDNABackgroundTask:

    def test_dna_background_task_scheduled(self):
        src = _read(ROUTES_FILE)
        assert "background_tasks.add_task" in src, \
            "POST /record must schedule a background task for DNA update"
        assert "_dna_update_background" in src or "dna" in src.lower(), \
            "DNA update background task must be present"

    def test_audio_base64_passed_to_dna(self):
        src = _read(ROUTES_FILE)
        # audio_base64 must be forwarded to the DNA task so has_audio=True when present
        assert "audio_base64" in src, \
            "audio_base64 must be passed through to the DNA background task"

    def test_flashcard_task_scheduled(self):
        src = _read(ROUTES_FILE)
        assert "_flashcard_background" in src or "flashcard" in src.lower(), \
            "POST /record must schedule flashcard generation in the background"


# ═══════════════════════════════════════════════════════════════════════════════
# BR-I7 — voice_journal in SESSION_WEIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionWeights:

    def test_voice_journal_in_session_weights(self):
        src = _read(DNA_SERVICE_FILE)
        assert '"voice_journal"' in src, \
            '"voice_journal" must be a key in SESSION_WEIGHTS in speaking_dna_service.py'

    def test_voice_journal_has_all_six_strands(self):
        src = _read(DNA_SERVICE_FILE)
        # Find the voice_journal block and verify all 6 strands are present
        idx = src.find('"voice_journal"')
        assert idx != -1, '"voice_journal" not found in speaking_dna_service.py'
        snippet = src[idx: idx + 400]
        for strand in ("rhythm", "confidence", "emotional", "vocabulary", "accuracy", "learning"):
            assert strand in snippet, \
                f'Strand "{strand}" missing from voice_journal SESSION_WEIGHTS entry'

    def test_voice_journal_acoustic_weights_are_nonzero(self):
        src = _read(DNA_SERVICE_FILE)
        idx = src.find('"voice_journal"')
        snippet = src[idx: idx + 400]
        # rhythm, confidence, emotional should all be 1.0 (full audio captured)
        assert "1.0" in snippet, \
            "voice_journal acoustic strands (rhythm/confidence/emotional) should be 1.0 — full audio is captured"


# ═══════════════════════════════════════════════════════════════════════════════
# BR-I8 — Router registered in main.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestMainPyRegistration:

    def test_voice_journal_router_imported(self):
        src = _read(MAIN_FILE)
        assert "voice_journal" in src, \
            "voice_journal router must be imported and registered in main.py"

    def test_voice_journal_router_included(self):
        src = _read(MAIN_FILE)
        assert "include_router" in src and "voice_journal" in src, \
            "app.include_router must be called with the voice_journal router in main.py"


# ═══════════════════════════════════════════════════════════════════════════════
# BR-I9 / BR-I10 — Mobile screens content
# ═══════════════════════════════════════════════════════════════════════════════

class TestMobileScreens:

    def test_vj_screen_has_record_button(self):
        src = _read(VJ_SCREEN_FILE)
        assert "record" in src.lower() or "Record" in src, \
            "VoiceJournalScreen must contain a record button"

    def test_vj_screen_has_timer(self):
        src = _read(VJ_SCREEN_FILE)
        assert "timer" in src.lower() or "duration" in src.lower() or "seconds" in src.lower(), \
            "VoiceJournalScreen must show a recording timer"

    def test_vj_screen_calls_today_api(self):
        src = _read(VJ_SCREEN_FILE)
        assert "voice-journal/today" in src or "voice_journal/today" in src or "/today" in src, \
            "VoiceJournalScreen must call the GET /today API endpoint"

    def test_vj_screen_calls_record_api(self):
        src = _read(VJ_SCREEN_FILE)
        assert "voice-journal/record" in src or "/record" in src, \
            "VoiceJournalScreen must call the POST /record API endpoint"

    def test_archive_screen_calls_archive_api(self):
        src = _read(ARCH_SCREEN_FILE)
        assert "voice-journal/archive" in src or "/archive" in src, \
            "JournalArchiveScreen must call the GET /archive API endpoint"

    def test_archive_screen_has_list(self):
        src = _read(ARCH_SCREEN_FILE)
        assert "FlatList" in src or "ScrollView" in src or "map" in src, \
            "JournalArchiveScreen must render a list of entries"

    def test_archive_screen_has_empty_state(self):
        src = _read(ARCH_SCREEN_FILE)
        assert "empty" in src.lower() or "no " in src.lower() or "yet" in src.lower(), \
            "JournalArchiveScreen must show an empty state message"


# ═══════════════════════════════════════════════════════════════════════════════
# BR-I11 — DailyHub has Voice Journal card
# ═══════════════════════════════════════════════════════════════════════════════

class TestDailyHubCard:

    def test_hub_navigates_to_voice_journal(self):
        src = _read(HUB_SCREEN_FILE)
        assert "VoiceJournal" in src, \
            "DailyHubScreen must navigate to VoiceJournal screen"

    def test_hub_shows_archive_cta_when_recorded(self):
        src = _read(HUB_SCREEN_FILE)
        assert "JournalArchive" in src or "archive" in src.lower(), \
            "DailyHubScreen must offer a View Archive CTA when already recorded"


# ═══════════════════════════════════════════════════════════════════════════════
# BR-I12 — App.js screen registrations
# ═══════════════════════════════════════════════════════════════════════════════

class TestAppJsRegistrations:

    def test_vj_screen_registered(self):
        src = _read(APP_JS_FILE)
        assert 'name="VoiceJournal"' in src, \
            'App.js must register a Stack.Screen with name="VoiceJournal"'

    def test_archive_screen_registered(self):
        src = _read(APP_JS_FILE)
        assert 'name="JournalArchive"' in src, \
            'App.js must register a Stack.Screen with name="JournalArchive"'


# ═══════════════════════════════════════════════════════════════════════════════
# BR-I13 — Deep link
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeepLink:

    def test_deep_link_registered(self):
        src = _read(APP_JS_FILE)
        assert "voice-journal" in src, \
            'App.js linking config must include "voice-journal" deep link path'
