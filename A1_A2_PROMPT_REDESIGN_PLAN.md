# A1/A2 Conversation Prompt Redesign — Design Plan

**Status:** Design document — decisions LOCKED (see below). Ready to implement on approval. No code changed yet.
**Date:** 2026-06-16
**Scope:** `build_beginner_instructions()` in `backend/prompt_optimization_helpers.py` — A1/A2 path, **ONLY these 3 session types: freestyle predefined-topic, freestyle custom-search topic, news.**
**Model:** `gpt-realtime-mini` (small streaming model — instruction-following is weaker than full realtime; prompt must be optimized FOR it).

### ⛔ HARD SCOPE BOUNDARY
- **DO NOT touch learning-plan sessions.** None of these changes apply to the learning-plan branch of `build_beginner_instructions`. Leave that code path exactly as-is.
- Affected paths ONLY: (1) freestyle predefined topic, (2) freestyle custom-search topic, (3) news.

### ✅ Decisions locked (from review)
1. **Talk ratio:** A1 ~60/40, A2 ~70/30 (student-favoured). Approved.
2. **Age-neutral tone.** We do NOT know the user's age. The one thing we know: **A1/A2 users quit the moment it feels hard.** So the whole design optimizes for *never reaching the quit point* — lower anxiety, keep them engaged, always give an easy way forward. No kid-vs-teen branching.
3. **"Why?" — A1: NEVER. A2: rare**, only when the student is already relaxed and producing longer answers. Rationale: CEFR puts "giving reasons" at B1; "why/how" are the hardest question type for new speakers and trigger the exact "it got hard → I quit" moment. Use safe expanders instead ("En jij?", "Vertel meer", "A of B?").
4. **Emoji: REMOVED entirely.** No `{emoji:name}` markers anywhere in V2. (They added no pedagogical value, bloated the prompt, and were the source of the "reads emoji aloud" problem.)

---

## 1. Why we're doing this (evidence, not assumption)

Three real 1-minute Dutch A1 sessions were captured and compared:

| Session | Topic var | AI first message | Words | Verdict |
|---|---|---|---|---|
| Freestyle | `"hobbies"` | "Heb jij een hobby?" | 10 | clean by luck |
| Custom | `"custom"` | "Hallo! Vandaag praten we over de Duitse omroep die stopt met tv. Weet je er iets van?" | 15 | not A1 |
| News | `None` | "Goed! Vandaag lezen we nieuws. Het gaat over: Spanje tegen Kaapverdië kijken. Weet je al over dit nieuws?" | 17 | not A1 + user fled to English |

Measured against the live code:
- The **first-message template** itself produces 15–23 words / 3–5 sentences in ALL paths, directly violating the A1 rule it sits next to (`"ONE sentence per response — maximum 8 words"`).
- The A1 prompt is **~5,600–6,800 tokens, 665 lines, 171 headers, 60–75 CAPITAL imperatives** (NEVER ×23, CRITICAL ×8).
- News injects the **raw English article title** ("What channel is Spain vs Cape Verde on?") into the first message and 4 other places.
- `news` path passes `topic=None`, so the safety block says "stay on **General Conversation**" while the body screams "STAY ON THIS NEWS TOPIC" — a direct conflict.
- The **student/tutor talk ratio (the product's core thesis) is nowhere in the prompt.**

## 2. What the research says (cited, verified)

**Pedagogy (real human A1/A2 tutors):**
- Target **~70/30 student/tutor talk** (CELTA "70/30 rule"; teacher speaks 20–30% — bridge.edu, verified). At **A1 the teacher legitimately talks more** (~55–60/40) because beginners need modeling (CEFR A1: "the other person is prepared to repeat or rephrase… and help me formulate"); by **B1 it shifts hard to the student** (~80/20) and "why/reasons" becomes a CEFR can-do.
- **Wait time 3–5s** measurably increases response length and confidence (Rowe — verified). Don't rescue silence.
- **Demand ladder:** non-verbal → yes/no → either-or → sentence frame → open. Drop a rung if they stall.
- **Recast + affirm**, but beginners miss ~50% of plain recasts (icaltefl — verified) → light stress / confirmation. Don't interrupt free talk; triage one error.
- **Open with a warm personal question, NOT the topic title.** First 60s predictable + low-anxiety.
- **"Why?" is B1**, not A1/A2 (CEFR grid).

**Youth anxiety (kids 8–12, teens 12–18):**
- Lower the **affective filter** (Krashen): normalize mistakes out loud, ask for the gist, allow think-time, no scores/audience.
- **Allow L1 as a bridge** — accept meaning, hand back the target-language version; never freeze a beginner with an English-only redirect (this is exactly what broke the news session).
- **Praise process + specifics, sincerely** — "You reused that pattern!" not "You're so smart!" / not reflexive "Good job!" (Dweck, Brummelman — verified; over-praise backfires).
- **Teens:** never put on the spot, give think-time + autonomy/choice, don't over-correct.
- **Kids:** play frame, predictable rituals, short turns, "beat-your-own-score."

**Model optimization (OpenAI official realtime prompting guide — verified):**
- **"Prefer bullets over paragraphs."**
- **"Be careful with constraint words (must/only/never/always)… overusing them makes the assistant rigid."** → our 60–75 CAPITALs are an anti-pattern.
- **"The model closely follows sample phrases"** and **"may overuse them, making responses robotic"** → our long example first-messages are being mimicked verbatim; fix = short, varied examples.
- **"Start simple. Do not over-prompt."** + a **Variety** section ("Do not repeat the same sentence twice; vary so you don't sound robotic").
- **Verbosity per task** ("1–2 short sentences"), not a global hard word cap.
- **"Conflicting/ambiguous instructions → performs worse."** → kill the topic=None "General Conversation" conflict and the limit-vs-template conflict.

**Convergence:** the product thesis (70/30), the pedagogy, and the model guide all point the same way: **short behavior-described turns + open handoff + lower anxiety + no rigid caps + no conflicts.**

---

## 3. Design principles (the rewrite is built on these)

1. **Describe behavior, don't cap words.** Replace `"maximum 8 words"` with a talk-ratio behavior. (Your note + OpenAI "verbosity per task" + TTQ.)
2. **Encode the 70/30 thesis explicitly, scaled by level.** A1 ~60/40 → A2 ~70/30 → (B1+ ~80/20, for when this logic is unified later).
3. **Open warm + personal, never the title.** One short greeting + one easy question. Same ritual every time.
4. **Hand the floor back every turn** with one open-but-answerable question; then wait.
5. **Ladder + wait-time + L1-bridge** instead of English-only redirect.
6. **Recast + affirm; triage correction; "why?" only A2+ (lightly).**
7. **Cut the prompt hard:** fewer sections, bullets, drop most CAPITALs, no raw English titles, no conflicts. Target ≤ ~3,000 tokens for A1 (from ~5,600).
8. **Add a Variety rule** so the coach doesn't sound robotic.
9. **Praise = process + specific + sincere; no inflation.**

---

## 4. The new prompt skeleton (model-optimized section order)

Mirrors OpenAI's recommended realtime structure, trimmed for a tutor. Bullets, not prose. One concern per section.

```
# {LEVEL} {LANGUAGE} SPEAKING COACH

## Role & Objective
- You are a warm {language} speaking coach for a {level} beginner.
- Goal: the STUDENT speaks most of the time and leaves feeling they can do it.

## Personality & Tone
- Warm, encouraging, patient. Never fawning, never a lecturer.
- Variety: don't reuse the same opener or praise word twice in a row; vary phrasing so you don't sound robotic.

## Talk Balance (the core rule)   ← replaces "max 8 words"
- Keep YOUR turn to {1 sentence (A1) / 1–2 short sentences (A2)}, then ask ONE simple question and stop.
- The student should be doing most of the talking ({~60% A1 / ~70% A2}). If you're talking more than the student, shorten your turns.
- After you ask a question, WAIT. Give the student a few seconds of silence to think — do not fill it or answer for them.

## Language Control
- Use only the {500 (A1) / 1000 (A2)} most common {language} words. Short, clear sentences.
- If a topic needs a hard word, swap it for a simple one (e.g. "broadcaster" → "TV").
- Speak ONLY {language}. (see "If the student uses another language" below — do NOT switch to English.)

## Keep the student in the conversation (anti-quit — top priority)
- A {level} student quits the moment it feels hard. Your #1 job is to NEVER let it feel hard.
- Every question must be answerable with what they already know. If a question would need words/grammar above {level}, make it easier.
- If the student struggles, IMMEDIATELY make the next step smaller — never repeat the same hard question.

## Getting the student to talk (the ladder)
- Start easy, climb only if they're ready: yes/no → "A or B?" → fill-the-gap → open question.
- If the student is silent or stuck: wait a moment, then drop one rung — offer two choices, or give a sentence starter ("Ik hou van ___").
- If they answer in ONE word: accept it warmly, then invite a little more with a SAFE expander — "En jij?" / "Vertel meer" / "A of B?".
- Do NOT ask "why?" at A1 — it's too hard and makes beginners freeze. {A2 only: a gentle "why?" is OK occasionally, and only if the student is already relaxed and giving longer answers.}

## If the student uses their own language or mixes
- Don't stop them and don't switch to English. Accept the meaning, then give them the {language} version and let them try it.
  - Student: "I watch it" → You: "Ah! In het Nederlands: 'Ik kijk.' Probeer maar — kijk je voetbal?"

## Correcting mistakes
- Don't announce errors. Recast: say it back correctly inside your reply, with a tiny stress on the fixed word.
  - Student: "Ik lees boeken" → You: "Mooi, je leest een **boek**! Welk boek?"
- Use the report_grammar_mistake function silently for ONE major error per turn (articles, verb form, word order). Keep talking naturally.
- Don't correct everything. If the meaning is clear, let small things go.

## Praise (keep it real)
- Praise the effort or the specific thing, briefly and sincerely: "Goed — je gebruikte de verleden tijd!"
- Don't gush, don't say "perfect/amazing" on shaky work, don't say "good job" after every single turn.

## This session: {topic_or_news_or_custom}
- {ONE short, level-true opening line built from the SUMMARY/topic — see §5}
- Stay roughly on this topic, but follow the student if they take it somewhere — connection matters more than staying perfectly on rails.

## Safety
- {compact 2-line refusal block — unchanged in spirit, trimmed}
```

Notes for the model's sake:
- **One** function-call instruction block (today it's repeated across emoji_header + conversation_flow + assemble).
- **Emoji REMOVED entirely** — no `{emoji:name}` markers, no emoji table, no "use an emoji every turn" rule anywhere. This also lets us delete the downstream emoji-stripping regex concern for these paths.
- **No** "🚨 CRITICAL … 🚨" walls; at most a couple of CAPITAL words on the single most important rule (talk balance).
- The Personality & Tone "Variety" bullet replaces the old per-turn-emoji crutch as the thing that keeps responses feeling alive.
- **Section ORDER is cache-critical (see §8):** every section above "## This session" is the stable, cacheable prefix; "## This session" + opening line is the only variable tail and MUST come last.

---

## 5. Opening line — the specific fix for all three paths

Replace the multi-sentence `CRITICAL FIRST MESSAGE STRUCTURE` template (which the model mimics literally) with a **behavior + ONE short example**, level-true and title-free.

**Rule given to the model (bulleted):**
- Open with a warm hello + ONE easy question. Keep it to {one sentence (A1) / two short sentences (A2)}.
- Do NOT announce the lesson plan or read out a title. Get the student talking immediately.

**Per path, the example we feed (short, varied — model will vary it):**
- **Freestyle/predefined topic:** `"Hoi! Hou je van {simple topic word}?"` → e.g. "Hoi! Hou je van muziek?"
- **Custom topic:** derive ONE simple word from the user's topic, not the raw phrase. "German broadcaster removes tv" → topic word ≈ "tv". Open: `"Hoi! Kijk je veel tv?"`
- **News:** open from the **summary**, never the English `news_title`. Summary "Vandaag is er een voetbalwedstrijd…" → `"Hoi! Hou je van voetbal?"` Title is dropped from the first message entirely (and from the 4 redundant injections).
- **Learning plan:** `"Hoi! Fijn dat je er bent! Zullen we praten over {week_focus simple word}?"`

This single change fixes: the 17-word news opening, the raw-English-title bleed, AND the template-vs-limit conflict — because the example is now itself A1-true and short.

---

## 6. Level scaling (one knob, three settings)

| Dimension | A1 | A2 | (B1+ later) |
|---|---|---|---|
| Tutor turn | 1 short sentence | 1–2 short sentences | minimal |
| Talk ratio target | ~60/40 student | ~70/30 | ~80/20 |
| Question default | yes/no & "A or B?" | closed→open, simple "what/where" | open referential, "why/how" |
| "Why?" | avoid | occasional, gentle | expected |
| Modeling | high (model frames) | medium | low |
| Vocab | 500 words | 1000 words | unrestricted-ish |

Implementation: these become a small `LEVEL_PROFILE` dict, not scattered `if level=='A1'` branches. Cleaner for the model (consistent wording) and for us.

---

## 7. Token budget (before → after, estimated)

| Path | Now | Target |
|---|---|---|
| A1 freestyle | ~5,600 | ~2,800 |
| A1 news | ~6,800 | ~3,000 |
| A2 | ~6,900 | ~3,200 |

Savings come from: removing 4× title injections, **deleting the entire emoji table/rules**, deduping the function-call block, dropping the 3-sentence first-message templates, cutting CAPITAL walls, and merging conflicting topic instructions. Smaller prompt = `mini` follows it better (OpenAI: "start simple, don't over-prompt").

---

## 8. Prompt caching — design for it (free 90% discount + lower latency)

**Confirmed (verified):** `gpt-realtime-mini` automatically caches the system-prompt (instructions) text tokens. Caching kicks in for any prompt ≥ **1,024 tokens** (our A1/A2 prompts are well above), and cached text input is billed at **$0.06 / 1M** vs **$0.60 / 1M** uncached — a **90% discount** — plus faster prompt processing. It's automatic; nothing to enable. Our setup is ideal because we inject **no per-session dynamic data** before the session — instructions are static for a given language+level+topic. (Sources: OpenAI prompt-caching guide; gpt-realtime-mini model pricing page; Microsoft Q&A on realtime cached_input_tokens.)

**How caching matches — the one rule that matters:** the cache matches the **longest identical PREFIX** of the prompt. Anything that varies must live at the END, or it breaks the cached prefix for everything after it.

**Problem in the current code:** topic/news/custom content is injected into the **middle** of the assembled prompt (`{topic_context}`, `{news_article_context}`), which breaks the cache prefix for every block that follows (safety, absolute rules). So each different topic/article lowers the hit rate.

**V2 design rule (locked):** put all **stable pedagogy blocks FIRST**, and the **variable per-session content LAST**:

```
[STABLE PREFIX — cached, identical across all sessions of same language+level]
  Role & Objective · Personality & Tone + Variety · Talk Balance ·
  Language Control · Ladder / wait-time / L1-bridge · Correction · Praise · Safety
──────────────────────────────────────────────
[VARIABLE TAIL — not cached, kept short]
  ## This session: {topic / news summary / custom}
  Opening line
```

With this order, ~80% of the prompt (the pedagogy) is **topic-independent** → every freestyle/news/custom session at the same language+level shares the same cached prefix → high hit rate. Only the short tail changes.

**⚠️ Measured reality after implementation:** V2 compressed the prompt so hard that the **stable prefix is only ~810–930 tokens — BELOW the 1,024-token cache threshold.** So prompt caching does **not** actually kick in for V2 A1/A2. This is fine, and arguably better:
- V2 already cut the prompt **~82%** (A1: ~5,600 → ~920 tokens). That raw reduction saves far more than caching's ~70% on a much larger prompt would have.
- Caching was a "nice-to-have" that only mattered while the prompt was huge. A prompt small enough to fall under the cache threshold is the better outcome — no caching needed.
- We deliberately do NOT pad the prefix with filler just to cross 1,024 tokens; that would re-bloat the prompt and hurt `mini`'s instruction-following (OpenAI: "start simple").
- The cache-friendly ordering (stable prefix first, variable tail last) is **kept anyway** — it's free, costs nothing, and future additions to the prefix may push it back over the threshold, at which point caching turns on automatically.

(Original estimate, now moot: a ~2,800-token prompt with a ~2,200 cached prefix would have been ~$0.00168 → ~$0.00049/session. The actual ~920-token uncached prompt is ~$0.00055/session — essentially the same, achieved by size alone.)

**Optional hardening:** pass a stable `prompt_cache_key` per (language, level, path) on the session-create call to improve routing/hit-rate. Not required (caching is automatic), but cheap to add.

### 🐛 Cost-log fix (note — separate from prompt work)
`routes/realtime_routes.py` PRICING dict (~line 1366) has `gpt-realtime-mini` `cached_text` = **`0.30 / 1_000_000`**, but the current official price is **`0.06 / 1_000_000`**. Our cost *reporting* over-charges cached text ~5× (billing is unaffected — this is our own log math). Fix to `0.06` when we touch this file. (Also sanity-check `cached_audio`/other rates against the live pricing page while there.)

---

## 10. Rollout & safety

- Gate behind env flag **`BEGINNER_PROMPT_V2`** (default OFF first, flip ON after side-by-side test). One-line rollback, no redeploy. Consistent with how the transcription migration was shipped.
- Keep `build_beginner_instructions` signature identical → zero mobile/API change.
- **Test matrix:** A1 + A2 × {freestyle predefined topic, custom, news} in Dutch + one non-Latin (Arabic/Turkish) to confirm the L1-bridge and opening behave. (**Learning-plan excluded — out of scope.**) Compare against the 3 baseline logs (talk ratio, opening length, no English bleed, no freeze).
- Success metrics from logs: (a) AI first message ≤ ~8 words A1 / ~14 A2; (b) student turns ≥ tutor turns in word count; (c) no raw English title; (d) no English-only redirect on L1 mixing; (e) opening feels warm/personal.

---

## 11. What this explicitly does NOT change

- **Learning-plan sessions — untouched (hard scope boundary).**
- Transcription (already shipped — `gpt-realtime-whisper` / diarize).
- B1–C2 path (separate `build_universal_instructions`; can get the same treatment in a follow-up once A1/A2 is proven).
- The grammar-correction function contract, DNA, news content pipeline.

---

## 12. Decisions — RESOLVED

1. **A1 ratio ~60/40, A2 ~70/30** — approved.
2. **Age-neutral**, optimized around the one known fact: A1/A2 users quit when it feels hard → design for "never let it feel hard." No kid/teen branching.
3. **"Why?": A1 never, A2 rare** (only when student is relaxed + producing longer answers). Safe expanders ("En jij?", "Vertel meer", "A of B?") used instead.
4. **Emoji removed entirely** from these 3 paths.

All four resolved → ready to implement behind `BEGINNER_PROMPT_V2` (default OFF), learning-plan untouched.
```
