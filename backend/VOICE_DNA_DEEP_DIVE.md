# MyTaco AI — Voice / Speaking DNA: The Definitive Deep-Dive

*Lead-engineer + content-strategist reference. All claims are traced to code (`file:line`) or peer-reviewed sources from the investigators' dossier. Anything not directly evidenced is explicitly marked UNCERTAIN / OPEN.*

---

## 1. What Voice / Speaking DNA Is

Speaking DNA is MyTaco AI's longitudinal, per-user-per-language **voice profile**: a continuously-updated, six-dimension fingerprint of how a learner actually speaks, built from real acoustic measurements and transcript/LLM analysis of every session — not a one-off test score. It is persisted as the "single source of truth" about learner speaking capability that the live tutor, the coach chat, the recommendation engine, the daily digest, and the breakthrough/celebration system all read from. The design intent is explicitly to reflect **authentic** proficiency rather than aspirational scores (the Feb-2026 Azure rework existed precisely because the old model produced unrealistic 66–100% strands disconnected from 12–30% assessment reality — `AZURE_PRONUNCIATION_INTEGRATION.md:14–24`).

**The 6 display dimensions** (the "helix"), with what each measures:

| # | Strand | What it measures (in code) |
|---|--------|----------------------------|
| 1 | **Rhythm** | Speaking pace (WPM), pause patterns, consistency; blended with acoustic `speaking_ratio` when audio present. Classifies `thoughtful_pacer` (<70 WPM) / `steady_speaker` (70–120) / `rapid_responder` (>120). `speaking_dna_service.py:842–899` |
| 2 | **Confidence** | Composite proxy from latency, filler rate, correction rate (+ voice quality when acoustic); assessment override = `(fluency + pronunciation)/200`. Levels hesitant/building/comfortable/fluent. `:901–997` |
| 3 | **Pronunciation** | Acoustic-only; Azure phoneme accuracy / prosody / completeness / fluency. Pinned when no Azure result. `:1313–1394` |
| 4 | **Vocabulary** | `unique_word_attempt_rate = unique_words/total_words`; style safety_first/balanced/adventurous; uses GPT assessment vocabulary score when available. `:999–1057` |
| 5 | **Accuracy** | `grammar_accuracy = 1 − corrections/turns`, overridden by GPT `grammar_score/100`; extracts top-5 error patterns. `:1183–1237` |
| 6 | **Fluency** | `0.5·filler + 0.3·variance + 0.2·pause`, updated every session, slow EMA. `:1241–1309` |

Two further **internal** strands exist but are **NOT** on the main helix: **Learning** (`challenge_acceptance`/`retry_rate`, `:1396–1428`) and **Emotional** (latency/fillers/hesitations composite + anxiety-trigger detection, `:1620–1681`). These surface only as tutor-dashboard sidebar metrics. ⚠️ **Copy caveat:** an old `faq-section.tsx` wrongly listed "Learning speed" and "Emotional expression" as headline dimensions — that is superseded and must not be used in new marketing.

---

## 2. How We Capture the Data

There are **three capture pathways**, and a critical distinction between **acoustic** features (measured from the audio waveform) and **transcript/LLM-derived** features (computed from text).

### Capture pathways
- **Pathway 1 — WebRTC Realtime (live conversation).** Voice streams point-to-point from browser to the OpenAI Realtime API (`gpt-realtime-mini`). The backend only mints an ephemeral session key at `/api/realtime/token` and tracks duration for billing — **it never receives the raw audio** (`realtime_routes.py:27–47`). Implication: live conversation sessions produce **transcript-derived** DNA only; acoustic strands are **pinned**.
- **Pathway 2 — Speaking Assessment (file upload).** Client uploads base64 WAV/M4A via `POST /api/speaking/assess`; decoded to bytes and validated by `AudioFormatValidator.validate_audio_data()` (`assessment_routes.py:239–287`). This is the path that yields full acoustic + Azure analysis.
- **Pathway 3 — Voice Checks (periodic acoustic monitoring).** Scheduled roughly monthly (every ~16 sessions) by `VoiceCheckScheduleService.calculate_voice_check_schedule()` (`voice_check_service.py:34–67`); short (30–60s) unscripted acoustic snapshots.

### Transcription
Audio is transcribed via `recognize_speech(audio_base64, language)` (`assessment_routes.py:265`). Model is env-controlled by `REALTIME_TRANSCRIBE_MODEL`, default **`gpt-realtime-whisper`** for realtime/streaming (`realtime_routes.py:112`); file-based assessment uses **`gpt-4o-transcribe-diarize`** (transcription migration, commit `af7b5f349`) — this fixed A1/A2 short-accented-speech mis-decoding (e.g. "Ik kijk vaak" → "Ikkaikvak").

### Privacy
Audio is **never written to disk** — processed in-memory via `BytesIO`. A temp WAV is created **only** for Praat (`AudioFormatValidator.create_temp_audio_file()`) and deleted immediately after Parselmouth extraction, with cleanup guaranteed in a `finally` block (`audio_analysis_service.py:170–231`; `assessment_routes.py:489–496`). Marketed as GDPR-compliant.

### Acoustic feature extraction (real DSP, not proxies)
- **librosa** (≥0.9): RMS energy per frame `librosa.feature.rms()` (`:331`); zero-crossing rate `librosa.feature.zero_crossing_rate()` (`:427`); pause detection via voice-activity thresholding (`:343`). Config: 16 kHz sample rate, 25 ms frame / 10 ms hop, energy threshold 0.02, pause threshold 0.3 s, min 5 s for valid analysis (`audio_analysis_service.py:40–55`).
- **praat-parselmouth** (Praat binding): pitch via `call(sound,'To Pitch',…)` floor 75 Hz / ceiling 600 Hz (`:181–186`); **jitter** `Get jitter (local)` (`:270–275`); **shimmer** `Get shimmer (local)` (`:278–283`).
- **Features returned** by `extract_acoustic_metrics()` (`:60–94`): `pitch_mean/std/min/max`, `jitter`, `shimmer`, `speaking_ratio`, `pause_ratio`, `pause_count`, `avg_pause_duration_ms`, `energy_mean/std`, `zero_crossing_rate` (13 metrics).

### Transcript / LLM-derived features (NOT acoustic)
- **WPM** = `word_count/duration × 60` (from transcript + duration, `speaking_assessment_improved.py:92–97`) — **explicitly not** an acoustic measurement.
- **CEFR + grammar/vocabulary/fluency/coherence** scores from **GPT-4.1** (`response_format=json_object`, `speaking_assessment.py:614–630`), using absolute CEFR-2020 Companion anchors with bottleneck (lowest-band) rule.
- **Filler rate, self-corrections, hesitations** via `FILLER_WORDS`/`CORRECTION_MARKERS` dicts (6 languages) in `_extract_session_metrics` (`speaking_dna_service.py:593–718`).
- **Reading detection** (`reading_detection_service.py:54–100`) flags read-aloud (vs spontaneous) speech and applies a 0.6–0.8 penalty before the expensive Azure call.

> **Note:** "All features are real acoustic measurements; no LLM-derived speech-speed proxies" is **partly** true — the *pure-acoustic* metrics are genuine DSP, but WPM and the proficiency scores are transcript/LLM-derived. Be precise in copy: **pitch/jitter/shimmer/energy/pauses = measured DSP; rate + proficiency = transcript/LLM.**

---

## 3. The Tech Stack

| Layer | Component | Role / Location |
|-------|-----------|-----------------|
| Live voice | **OpenAI Realtime API — `gpt-realtime-mini`** | P2P browser↔OpenAI streaming; backend mints ephemeral token (`realtime_routes.py:27`) |
| Transcription | **`gpt-realtime-whisper`** (realtime) / **`gpt-4o-transcribe-diarize`** (file) | env `REALTIME_TRANSCRIBE_MODEL` (`realtime_routes.py:112`) |
| Acoustic DSP | **librosa** + **praat-parselmouth** | `audio_analysis_service.py` |
| Phoneme pronunciation | **Azure Cognitive Services Speech SDK** | `pronunciation_assessment_service.py`; HundredMark + Phoneme granularity; 7 locales (en/fr/es/de/nl/pt/tr) |
| Proficiency / CEFR | **GPT-4.1** (and `gpt-4.1-mini` for summaries / causal sentence) | `speaking_assessment.py`; `speaking_dna_service.py` |
| Intent / coach LLM | **GPT-4o-mini** | intent classification in `coach_service_optimized.py:103–211` |
| Semantic retrieval | **Pinecone / vector DB + cross-encoder reranker** | `coach_service_vector_enhanced.py:78–184` |
| Persistence | **MongoDB** | `speaking_dna_profiles`, `speaking_dna_history`, `speaking_breakthroughs` |
| Caching / cooldowns | **Redis** | coach context cache (TTL 300s), breakthrough push 24h cooldown |
| Frontend | **Next.js landing helix** (`speaking-dna-section.tsx`) + **mobile helix** | marketing + in-app visualization |

Azure gating: enabled at init only if `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION` are set; **no feature flag** — if absent, a conservative `_fallback_assessment` (55–60 base, `assessment_method='estimated'`) is silently used (`pronunciation_assessment_service.py:41–53, 325–360`). Live in prod since commit **`a1711ece1`** (Feb 4 2026). Azure adds ~3 s/assessment; full assessment ~34 s (GPT-4 dominates at ~25 s).

---

## 4. How the 6 Strands Are Computed

### Core update math — EWMA with session-weighted alpha
Every strand is an **Exponential Moving Average**. Base `alpha = 0.3` (`speaking_dna_service.py:765`), multiplied by a per-strand, per-session-type weight:

```
new_score = old_score · (1 − alpha·weight) + raw_score · alpha·weight
```
(`_calculate_strand_updates`, `:737–840`). Two strands override the base alpha: **Fluency alpha = 0.15** (slower — treated as more stable; rationale OPEN) and **Pronunciation alpha = 0.25** (faster acoustic update).

### Session weights (`SESSION_WEIGHTS`, `:40–114`) — which sessions move which strands
- `learning`: rhythm 0.8, confidence 1.0, **pronunciation 0.0**, vocab 0.7, accuracy 1.0, fluency 0.9
- `freestyle`: rhythm/confidence/vocab/fluency 1.0, **pronunciation 0.0**, accuracy 0.7
- `news`: pronunciation 0.0, vocab 1.0, others ~0.8–0.9
- `voice_check` / `speaking_assessment`: **pronunciation 1.0**, rhythm/confidence 1.0, vocab/accuracy 0.3, fluency 0.8
- `custom_topic` / `practice`: transcript-only — rhythm/confidence/**pronunciation 0.0**, vocab/accuracy/fluency 0.5

### Pinning (prevents false drift)
- **Acoustic pinning S3.1** (`:770–795`): no audio → rhythm/confidence/pronunciation/emotional **held at prior value**. Applies to conversation/news/freestyle.
- **Transcript pinning S4** (`:816–827`): voice_check/speaking_assessment have thin 30–60 s transcripts → vocabulary/accuracy/fluency held, so a short monologue can't drag down progress.
- **Learning pinning S3.2** (`:798–805`): no challenges offered → learning held.

### Per-strand raw-score formulas (key ones)
- **Confidence (no audio):** `0.4·latency + 0.3·filler + 0.3·correction`; **(with audio):** `0.25` each + `0.25·voice_quality`; assessment override `(fluency+pronunciation)/200` (`:901–997`).
- **Fluency:** `0.5·filler_component + 0.3·variance_component + 0.2·pause_component` (`:1241–1309`).
- **Accuracy:** `1 − corrections/turns`, override `grammar_score/100` (`:1183–1237`).
- **Vocabulary:** `unique_words/total_words` (`:999–1057`).
- **Pronunciation:** direct from Azure phoneme/prosody/completeness/fluency (`:1313–1394`).

### Error-pattern extraction (`_extract_error_patterns`, `:1064–1181`)
Normalizes raw error types into **17 canonical categories** (subject_verb_agreement, article_usage, tense_conjugation, word_order, preposition_usage, gender_agreement, spelling, pronunciation…) via `ERROR_TYPE_MAPPING`, ranks by severity (critical 1.0 → low 0.25) × frequency, returns **top-5 errors + improving_areas** (errors that dropped out of the set).

### Baselines & deltas
- **Baseline write-once (`:365–380`):** the first acoustic session freezes `baseline_assessment.acoustic_metrics` (13 metrics) as a permanent anchor — **never overwritten**. Later voice checks append to `voice_check_history` and compute **rolling deltas** (current vs *previous* check, not vs baseline).
- **Strand deltas S3.4 (`_compute_strand_deltas`, `:543–591`):** per-strand `{previous, current, delta}` (rhythm=consistency, confidence=score, pronunciation=score, vocab=attempt_rate, accuracy=grammar_accuracy, fluency=score). Emotional/Learning omitted; empty on first session.

### Storage (MongoDB)
- `speaking_dna_profiles` — one doc per user×language: `dna_strands`, `overall_profile` (archetype), `sessions_analyzed`, `total_speaking_minutes`, `baseline_assessment`, `last_session_delta`, per-strand history arrays (capped 50), `voice_check_history`, cached `coach_instructions`.
- `speaking_dna_history` — weekly snapshots (structure preserved but **weekly snapshot creation is commented-out/disabled in prod**, `:486–494`).
- `speaking_breakthroughs` — breakthrough records with celebration copy.

### Archetypes (`_determine_overall_profile`, `:1683–1731`)
Maps `(rhythm_type, accuracy_pattern, learning_type)` → e.g. *The Thoughtful Builder*, *The Fearless Explorer*, *The Steady Progressor*. Only **3 hardcoded** mappings; everything else → *The Unique Learner* (OPEN: likely under-built).

---

## 5. How It Actually Helps the Learner — The LOOP

This is the core differentiator: Speaking DNA is a **closed longitudinal feedback loop**, not a static readout.

1. **Update trigger.** Every session end → `POST /api/speaking-dna/analyze-session` recomputes strands within ~5 min (`speaking_dna_routes.py:69–148`).
2. **Cache invalidation closes the circle.** `invalidate_coach_context_smart(user_id, ['dna','sentence_analysis'])` purges stale coach context (`:129–134`); Redis TTL 300 s means the next chat **always** sees fresh scores — preventing "your accuracy is 70%" when it just dropped to 55%.
3. **Live tutor personalization (premium).** At `/api/realtime/token`, `build_coach_instructions()` injects a DNA-aware prompt fragment into the OpenAI Realtime instructions (`realtime_routes.py:1922–1943`): weakest strand to target, recent pronunciation errors to avoid re-teaching, recommended challenge types. The tutor adapts **without a separate tuner model**.
4. **Coach chat aggregation.** `coach_service.get_user_context()` embeds the DNA scores directly into the system prompt (`coach_service.py:724–734`), turning generic advice into "your accuracy is 52% — focus on grammar mini-lessons." The optimized coach correlates DNA with `sentence_analysis_jobs` ("you confuse de/het 67% of the time → your accuracy strand is 52% → try Error Spotting"). The vector-enhanced coach adds semantic session search + trajectory celebration.
5. **Recommendations & journey state.** `journey_state_detector` reads `dna_improvement_trend` to classify the user (EXPLORING…ACCELERATING…STRUGGLING…). ACCELERATING + high accuracy → "crush harder challenges + celebrate breakthrough"; STRUGGLING + declining → "easy 3-min session + fundamentals" (`recommendation_engine.py`, `journey_state_detector.py`).
6. **Trajectory / breakthrough detection.** `learning_trajectory_analyzer` computes velocity (%/week), plateaus (<3% over 4 wks), breakthroughs (>15% in 2 wks). `_detect_breakthroughs` (`:1737–1932`) fires on confidence_jump ≥0.15, speed +20% WPM, vocab +10 words, fluency crossing 0.75, grammar crossing 0.85, anxiety cleared.
7. **Celebration without fatigue.** First breakthrough returns as `breakthrough_unlocked` → sealed celebration card; `celebrate_breakthrough()` marks it celebrated so the digest stops re-nudging (`:138–148, 450–499`). Push has a 24h Redis cooldown, fail-open.
8. **Proactive digest.** `daily_digest_generator` sends strand-anchored morning nudges ("Your speaking flow is your next unlock — today's session works on that rhythm"), tied to a specific dimension, not generic motivation.

**Net effect:** a static score would show "68% accuracy." The loop instead produces *"Your accuracy went 65%→68% this week — let's focus on articles (your weakest at 45%); try Error Spotting."* Session → DNA update → fresher coach → more-personalized next session → better data → DNA improves → repeat.

---

## 6. Why This Matters Scientifically

### DEFENSIBLE (cite freely)
- **Pronunciation instruction works.** Lee, Jang & Plonsky (2015), 86 studies: **d = 0.80–0.89**, larger with feedback + longer interventions. *Applied Linguistics 36(3):345–366.*
- **Tech-delivered (CAPT) works.** Mahdi & Al Khateeb (2019), 31 studies: **d = 0.68** (medium); stronger for beginner/intermediate. *Review of Education.*
- **ASR-based pronunciation training works.** Ngo, Chen & Lai (2024), 15 studies: **g = 0.69**; explicit corrective feedback **g = 0.86** vs indirect 0.50; beginner g = 1.33; medium-duration (5–8 wk) g = 1.01 vs short (1–4 wk) g = 0.07. *ReCALL 36(1).*
- **Frame goals as intelligibility/comprehensibility, NOT accent removal.** Munro & Derwing (1995): accentedness, comprehensibility, intelligibility are partially independent — "heavily accented but highly intelligible" is real. *Language Learning 45(1):73–97.*
- **Prosody/rhythm matters for intelligibility** — grounds the Rhythm dimension (Derwing & Munro; Kennedy & Trofimovich 2008).
- **Fluency = rate + pausing, especially mid-clause pauses** are the strongest predictor of listener-perceived fluency; pause *location* matters (Suzuki & Kormos; Saito et al. 2018; Kahng; Kormos framework: mid-clause≈formulation, end-clause≈conceptualization). Grounds Fluency.
- **Vocabulary & Accuracy are legitimate comprehensibility drivers** (Saito, Trofimovich & Isaacs 2016).
- **Personalized, specific, repeatable, measured feedback beats generic drills** — Ericsson et al. (1993) deliberate practice; non-generic > generic feedback. Directly justifies the longitudinal voice profile.

### OVERREACH — DO NOT claim
- ⚠️ **Jitter / shimmer / F0 perturbation are voice-QUALITY / clinical markers** (hoarseness, vocal pathology), measured on sustained vowels, reliability described as "thus far unsatisfactory." They are **NOT validated** as language-proficiency or "confidence" signals. *(SAGE Encyclopedia of Human Communication Sciences and Disorders, "Jitter and Shimmer".)* If referenced at all, use neutral "voice-quality / vocal characteristics" framing only — never tie to proficiency. **Engineering note:** the code *does* compute jitter/shimmer and can feed them into the confidence strand's `voice_quality` term — keep that as an internal heuristic, not a marketed scientific construct.
- ⚠️ **"Confidence" has no acoustic gold-standard in SLA.** It is a defensible **proxy** from fluency markers (fewer hesitations/pauses, steadier rate) but must be labeled an *estimate/proxy*, never a validated/clinical measure, and never tied to jitter/shimmer.
- ⚠️ **Machine feedback on suprasegmentals is weaker-evidenced than on segments** (Ngo 2024: segmental g = 0.82 vs suprasegmental g = 0.37). Temper any "we train your rhythm/intonation" claims relative to "we train your sounds."
- ⚠️ **"Rhythm score" and the composite "DNA" itself are proprietary composite indicators**, not established scientific constructs — position them as such.

---

## 7. What Makes It Different

- **A longitudinal personal voice profile, not a quiz score.** Strands are EWMA-smoothed across an entire learning history with a write-once acoustic baseline and rolling voice-check deltas — competitors' generic drills give you a per-exercise number with no memory.
- **DNA is injected live into the tutor.** The weakest-strand + recent-error context is appended to the OpenAI Realtime system prompt *per session*, so the AI tutor self-personalizes with **no separate fine-tuned model** — most CAPT tools just score, they don't re-aim the conversation.
- **Cross-feature correlation.** Coach fuses DNA strands with per-sentence error analytics ("de/het 67%") and trajectory velocity — a single explanation that spans acoustic, grammatical, and temporal signals.
- **Real DSP + real phoneme assessment.** librosa + Praat for genuine acoustics, Azure for phoneme-level scoring with reading-detection so read-aloud speech can't game fluency — more rigorous than transcript-only "fluency" estimates.
- **Honest scoring by design.** The Feb-2026 rework deliberately swapped acoustic proxies for assessment-grounded strands because the old ones were falsely inflated (66–100% → realistic). The product's stated value is truthful measurement, which is itself a differentiator vs. motivation-inflated competitors.
- **The motivational loop is closed.** Breakthrough detection → sealed celebration card → digest de-duplication → journey-stage-aware recommendations form a deliberate-practice flywheel that maps directly onto the meta-analytic moderators (specific feedback + sustained repetition).

---

## 8. Gaps / Caveats / Open Questions

**Behind a flag / not-live / disabled:**
- **Weekly snapshot creation is disabled in prod** (commented out, `:486–494`) — structure preserved but `speaking_dna_history` weekly docs may not be populating; trajectory features that depend on weekly snapshots may rely on session-level history instead. ⚠️ Verify before marketing "12-week evolution timeline."
- **Azure has no feature flag** — silently falls back to *estimated* 55–60 scores if keys are missing; a misconfigured deploy would show plausible-but-fake pronunciation numbers with no error.
- **Live conversation (Realtime) sessions produce no acoustic data** — acoustic strands are pinned; only file-upload assessments and voice checks yield true acoustics. So "we analyze your voice every session" is only acoustically true for assessments/voice-checks; conversations are transcript-derived.

**Marketing-copy discrepancies to fix:**
- Old `faq-section.tsx` lists "Learning speed" + "Emotional expression" as headline dimensions — **incorrect**; the current 6 are Rhythm, Confidence, Pronunciation, Vocabulary, Accuracy, Fluency. Learning/Emotional are internal/sidebar only.
- Landing helix uses fixed demo values (Rhythm 84/Confidence 72/Pronunciation 77/Vocab 60/Accuracy 91/Fluency 68) — illustrative, not a real user.

**Scientific cautions (see §6):** jitter/shimmer ≠ proficiency; Confidence is a proxy; suprasegmental machine-feedback evidence is weaker than segmental.

**Open engineering questions (unresolved in the dossier):**
- Pitch aggregation: does it filter unvoiced (pitch>0) frames before mean/std, or use raw frames? (UNCERTAIN)
- Energy threshold 0.02 and anxiety fallback thresholds (latency>4s, filler>8) — calibrated per-language / per-population? (UNCERTAIN)
- Can Azure run for freestyle/learning if audio is provided, or strictly voice_check/speaking_assessment only? Code paths suggest the latter, but not fully confirmed.
- When pronunciation weight = 0 with no audio, is the strand literally 0 or carried-forward-and-pinned? (Pinning logic at `:770–795` implies carried-forward, but the "pinned to 0.0 for transcript-only" phrasing in one investigator note conflicts — RECONCILE before claiming.)
- Archetype coverage: only 3 hardcoded mappings; most users likely fall to "The Unique Learner."
- Filler detection uses substring match (`'you know'`) → possible false positives without word-boundary regex.
- Where exactly do the override `assessment_scores` originate per session (Azure vs GPT vs assessment endpoint)? Mixed across paths.
- Fluency alpha = 0.15 rationale unconfirmed.
- gpt-realtime-whisper cost (+~$0.83/user/mo) not yet validated against actual Railway usage at scale.
- Meta-analysis precision: only Mahdi (d=0.68) and Ngo (g=0.69) were fully extracted; Almusharraf 2024 and Lee/Kim CAPT figures were paywalled. Pull primaries before quoting exact CIs in copy.

---
*Sources: 6-investigator dossier (code review of capture pipeline, strand computation, Azure pronunciation, pedagogy loop; local docs/git history; SLA/CAPT literature). File:line and citations preserved inline. Prepared for product/marketing copy and team brief.*