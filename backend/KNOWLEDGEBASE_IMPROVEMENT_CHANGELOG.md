# Tutor Knowledgebase Improvement — Change Reference

Branch: `feature/tutor-knowledgebase-improvement`  
Period: May 2026  

---

## 1. CEFR Assessment (`speaking_assessment.py`, `reading_detection_service.py`)

### Before
- Score-to-level mapping used relative scale: "70-84 = meets level expectations fully" — GPT gave A1 speech a score of 80 because it "met A1 expectations well", which mapped to B2 on the absolute scale
- No bottleneck rule: final level averaged across skills, hiding weak areas
- Reading detection penalised A1/A2 speakers for low WPM and missing fillers (normal beginner behaviour)
- WPM slow-reading threshold: 60 WPM
- GPT model: `gpt-4o`

### After
- **Absolute score anchors** (research-validated): A1: 10–35, A2: 36–50, B1: 51–65, B2: 66–78, C1: 79–90, C2: 91–100
- **Bottleneck rule**: final CEFR = lowest skill band across fluency, grammar, vocabulary, coherence, pronunciation
- **CEFR 2020 intelligibility standard**: removed native-speaker comparison from prompt
- A1/A2 gate in reading detection: filler-word and self-correction signals suppressed for beginners
- WPM slow-reading threshold lowered to 40 WPM; A1/A2 slow floor set at 45 WPM
- GPT model upgraded to `gpt-4.1`
- Short-sample gate: <60 words returns soft warning, never HTTP 4xx

---

## 2. Learning Plan Generation (`learning_routes.py`, `intelligent_schedule_generator.py`)

### Before
- Shallow `gpt-4o` prompt with minimal context
- Sub-goal week allocation: `int(4 * 0.6) // 3 = 0` silent drop (zero weeks generated)
- Short-sample warning string leaked into week titles via `areas_for_improvement[0]`
- Cross-goal sub-goal lookup only searched selected goals, missing enriched goals

### After
- **`gpt-4.1` with function calling** (strict mode) — full context: per-skill feedback, sub-goals with `level_focus`/`key_vocabulary`/`key_phrases`/`skill_priorities`, DNA profile strands, session capacity note, weekly schedule summary
- Week allocation fixed: `max(n_sub_goals, ideal)` guarantees ≥1 week per sub-goal
- Short-sample warning filtered before building week titles
- Two-phase sub-goal lookup: selected goals first, then all enriched goals

---

## 3. Session Summaries (`routes/session_summary_routes.py`)

### Before
- No structured post-session summary stored
- Only free-text summary saved

### After
- **Structured 7-field JSON summary** generated via `gpt-4.1-mini` after every session
- Stored as `compressed_summary` string in `session_summaries` list
- Full structured object stored in `session_history[n].structured_summary`
- Injected into subsequent sessions as context for continuity

---

## 4. Assessment Prompt Endpoint (`routes/assessment_routes.py`)

### Before
- No endpoint to fetch a level-appropriate speaking prompt

### After
- `GET /api/speaking/assessment-prompt` added
- Returns level-appropriate task: A1 = simple self-intro, A2 = daily routine, B1 = narrative, B2 = opinion, C1/C2 = complex discourse
- Translated to target language via `gpt-4.1-mini`

---

## 5. Freestyle Session Instructions (`prompt_optimization_helpers.py`, `tutor_config.py`)

### Before
- `build_beginner_conversation_flow()`: hardcoded "4 minutes", coffee/tea/bread examples, "stay on ONE subtopic entire session" rule causing loops
- Topic ID `"daily"` passed raw → model translated as Dutch adjective "dagelijks"
- Session duration ignored by the model (no turn counts, no subtopic counts)
- A1 predefined questions used `{topic}` variable (raw ID), not display name
- `pacing` dict overwritten by pacing string (variable name collision)

### After
- **`tutor_config.py`** (new file): 20 predefined topics with display names, aliases, per-CEFR vocabulary, 4 subtopic arcs, `SESSION_PACING` for 1/3/5-minute sessions
- `build_beginner_conversation_flow()` fully rewritten: duration-aware phases, subtopic progression rule, no hardcoded examples
- Alias lookup: `"daily"`, `"daily-routine"`, `"daily_routine"` → `"Daily Routines"`
- Duration-aware pacing injected: 1-min = 2-3 questions, 3-min = 7-8, 5-min = 12-14
- Variable collision fixed: pacing dict renamed to `session_pace`

---

## 6. Tutor Silence Fix (`prompt_optimization_helpers.py`)

### Before
- After completing planned subtopics, tutor said wrap-up sentence and went silent
- No instruction to continue if the session timer had not ended

### After
- All duration variants (1/3/5 min) now include: "after wrap-up, ask ONE more question and keep responding until the session ends — do NOT go silent"
- Explicit `## After wrap-up — NEVER go silent` section added to conversation flow

---

## 7. Grammar Correction Tool Narration (`prompt_optimization_helpers.py`)

### Before
- Tutor verbally announced corrections: `"Good! Let's use 'send' correctly."`
- Tutor output literal text: `"{I'll report the grammar mistake now.}"`
- Both violations leaked into audio output

### After
- Explicit ban added to all correction style sections:
  - `"Let's use X correctly"` — forbidden
  - `"{I'll report the grammar mistake now.}"` — forbidden
  - Any text in curly braces describing internal actions — forbidden
- `build_beginner_conversation_flow()` correction notes rewritten to be unambiguous

---

## 8. Conversation Help (`conversation_help_improved.py`, `gpt4o_cost_tracker.py`)

### Before
- Intent analysis and response generation used model `"gpt-5-mini"` (non-existent) → empty responses → JSON parse failure on every call
- Always fell back to generic system, wasting ~$0.007/call and 10+ seconds latency
- Cost tracker printed 20-line `💰 [GPT4O_COST]` block to logs on every call
- Verbose debug prints: RAW RESPONSE, CLEANED CONTENT, PARSED DATA on every call

### After
- Model corrected to `"gpt-4.1-mini"` at both call sites
- Cost tracking calls removed from `conversation_help_improved.py` and `sentence_assessment.py`
- Cost tracker console print block removed from `gpt4o_cost_tracker.py`
- Verbose debug prints removed; only error-level prints remain

---

## 9. f-string Syntax Error (`prompt_optimization_helpers.py`)

### Before
- `{I'll report the grammar mistake now.}` inside triple-quoted f-strings
- Python parsed `{I'll...}` as an f-string expression; apostrophe in `I'll` terminated the string literal
- Caused `SyntaxError: f-string: EOL while scanning string literal` on every custom topic session → 500 error

### After
- Escaped to `{{I'll report the grammar mistake now.}}` (double braces → literal curly braces in output)
- File compiles cleanly

---

## 10. Emoji Format Fix (`prompt_optimization_helpers.py`)

### Before
- Emoji markers in non-f-string blocks written as `{{{{emoji:name}}}}` → literally sent to model as `{{{{emoji:name}}}}`
- Model output `{{{{emoji:happy}}}}` → mobile received quadruple braces → emoji never rendered
- In f-string blocks: `{{{{emoji:name}}}}` → `{{emoji:name}}` (double braces) → still wrong

### After
- Non-f-string blocks (`emoji_section`): corrected to `{emoji:name}` (single braces, plain string)
- f-string blocks: corrected to `{{emoji:name}}` (double braces → produces `{emoji:name}` at runtime)
- Global replace via `sed` ensured all 18+ occurrences fixed consistently
- Available emoji list expanded: added `game`, `console`, `computer`, `books`, `man`, `woman`, `family`, `baby`

---

## 11. Language Code Normalisation (`prompt_optimization_helpers.py`, `routes/realtime_routes.py`)

### Before
- Mobile sent ISO codes: `"en"`, `"nl"`, `"es"`, `"fr"`, `"de"`
- `language_configs` keyed by full names: `"english"`, `"dutch"`, etc.
- Lookup missed → fallback generic rule used for all sessions from mobile

### After
- Normalisation map added at both call sites before lookup:
  ```python
  {"en": "english", "nl": "dutch", "es": "spanish", "fr": "french",
   "de": "german", "pt": "portuguese", "it": "italian"}
  ```
- Correct language-specific redirect rules now applied

---

## 12. False Language Redirect Fix (`prompt_optimization_helpers.py`)

### Before
- English redirect rule: "If student speaks another language, redirect"
- Tutor incorrectly redirected English speech (`"I don't know about this."`) with `"Let's practice English. Please try English."` — user was already speaking English

### After
- Rule rewritten for all languages: only redirect if student **clearly** uses a different language
- Short valid answers (`yes`, `no`, `okay`, `I don't know`) explicitly listed as valid — must not be redirected
- Applied to all 5 language configs (english, dutch, spanish, french, german)

---

## 13. News Session — A1/A2 Topic Drift Fix (`prompt_optimization_helpers.py`)

### Before
- Pre-generated `discussion_questions` (often generic: `"What is your favorite game?"`, `"Do you play games in winter?"`) injected directly into A1 sessions
- A1 news questions guidance had hardcoded examples from a specific article (SEGA, games)
- Summary truncated to 300 chars — model couldn't extract facts to form questions
- Closing instruction hardcoded `"5-minute conversation"` regardless of selected duration

### After
- A1: pre-generated discussion questions bypassed; model instructed to derive yes/no questions directly from the summary
- A2: pre-generated questions retained (appropriate for the level)
- All hardcoded article-specific examples removed from question guidance
- Summary truncation raised to 600 chars
- Closing instruction uses `{selected_duration}` variable

---

## 14. News Session — B1-C2 Level Constraints (`routes/realtime_routes.py`)

### Before
- `level_constraints` only defined for A1 and A2
- B1, B2, C1, C2 received empty string — zero level guidance
- Same language code mismatch (`"en"` vs `"english"`)

### After
- All 6 CEFR levels defined with appropriate constraints:
  - **B1**: topic vocabulary, all basic tenses, introduce 2-3 new words
  - **B2**: abstract vocab, full tense range, nuance and perspectives
  - **C1**: idioms, collocations, sophisticated argumentation
  - **C2**: unrestricted, native-level complexity, critical analysis
- Language code normalisation applied to this path too
- Discussion questions: A1/A2 told to derive from summary; B1-C2 use pre-generated questions

---

## Files Modified

| File | Changes |
|------|---------|
| `speaking_assessment.py` | Absolute CEFR anchors, bottleneck rule, gpt-4.1, CEFR 2020 prompt |
| `reading_detection_service.py` | A1/A2 gate, WPM thresholds |
| `learning_routes.py` | gpt-4.1 function calling, full context injection |
| `intelligent_schedule_generator.py` | Week allocation fix, short-sample filter, cross-goal lookup |
| `routes/session_summary_routes.py` | Structured 7-field JSON summary |
| `routes/assessment_routes.py` | New assessment prompt endpoint |
| `routes/realtime_routes.py` | B1-C2 news level constraints, language normalisation, news questions |
| `prompt_optimization_helpers.py` | Conversation flow rewrite, emoji fix, f-string fix, language redirect, news A1/A2 fix, correction narration ban, silence fix |
| `tutor_config.py` | New file — topic catalogue, session pacing |
| `conversation_help_improved.py` | Model name fix, cost logs removed, verbose prints removed |
| `sentence_assessment.py` | Cost tracking removed |
| `gpt4o_cost_tracker.py` | Console print block removed |
