# MyTacoAI Tutor Dashboard — Insights & Calculations Specification

**Version:** 1.0  
**Date:** May 2026  
**Scope:** Tutor Dashboard → Learner Detail Modal → Overview Tab  
**Audience:** Product, Data Science, QA, Backend Engineers

---

## Overview

When a tutor opens a learner's detail view, the **Overview tab** is the first screen they see. Every value displayed is computed from real behavioral data stored across six MongoDB collections. This document defines the source data, transformation logic, thresholds, and rationale for every metric shown.

All calculations in this document are verified against **Jack Tune** (`mytacoai1@proton.me`, user_id: `69b3fa266a04f39b7c34afbc`), a real user enrolled in Lincoln Academy under tutor Emma Williams.

---

## Data Sources

| Collection | Purpose | Key fields used |
|---|---|---|
| `conversation_sessions` | Realtime voice practice sessions | `user_id`, `created_at`, `duration_seconds`, `language`, `level` |
| `challenge_sessions` | Gamified challenge rounds | `user_id`, `created_at`, `correct_answers`, `total_challenges`, `accuracy`, `total_xp`, `max_combo`, `end_time` |
| `daily_stats` | Aggregated per-day activity | `user_id`, `local_date`, `total_sessions`, `conversation_time_seconds`, `total_xp`, `accuracy_percent`, `streak_count` |
| `speaking_dna_profiles` | AI-analyzed speaking behavior profile | `user_id`, `dna_strands`, `overall_profile`, `sessions_analyzed` |
| `speaking_dna_history` | Weekly snapshots of DNA strands | `user_id`, `week_number`, `strand_snapshots`, `week_stats` |
| `sentence_analysis_jobs` | Per-sentence quality scores | `user_id`, `analyses[].grammatical_score`, `vocabulary_score`, `complexity_score` |
| `assessments` | Formal CEFR-level assessments | `user_id`, `language`, `level`, `score`, `feedback` |
| `learning_plans` | Structured learning path progress | `user_id`, `language`, `proficiency_level`, `progress_percentage`, `completed_sessions` |

---

## API Endpoint

```
GET /tutor/dashboard/{tutor_id}/learner/{user_id}/details
Authorization: Bearer <tutor_jwt>
```

The endpoint fetches all required data in **parallel** using `asyncio.gather()` then formats and returns it as a single JSON response. The frontend performs all display calculations client-side from this payload.

---

## Section 1 — Engagement Health

### What it shows
A colored card with a percentage score, label, and mini progress bar.
Labels: **Highly Engaged** (green) / **Moderately Engaged** (amber) / **Needs Attention** (red)

### Calculation

```
Source: daily_stats.recent_daily[] — sorted newest first, up to 14 records

Step 1: Build a Set of dates where the learner was active:
  activeDateSet = { date | minutes > 0 OR sessions > 0 }

Step 2: For each of the last 7 CALENDAR days (today → today-6):
  activeLast7 += 1  if  date in activeDateSet

Step 3: engagementScore = round((activeLast7 / 7) * 100)

Step 4: Thresholds:
  score >= 57%  → "Highly Engaged"    (≥4 of 7 days)
  score >= 28%  → "Moderately Engaged" (≥2 of 7 days)
  score <  28%  → "Needs Attention"   (0-1 of 7 days)
```

### Real example — Jack Tune (verified 2026-05-11)
```
Active dates in DB: {2026-05-08, 2026-05-06, 2026-05-04, 2026-05-03, ...}
Last 7 calendar days checked: 2026-05-11 to 2026-05-05
Days in set: 2026-05-08 ✓, 2026-05-06 ✓  → activeLast7 = 2
engagementScore = round(2/7 × 100) = 29%  → "Moderately Engaged"
```

### Why calendar days, not record count
Daily stats records only exist for days with activity. Counting records would always show 100% (every record is an active day). Calendar-based counting correctly surfaces gaps — e.g. a learner who practiced 7 times but all in one week shows the real inactivity in the following week.

---

## Section 2 — Completion Rate

### What it shows
Percentage of voice sessions the learner actually completed, with raw count (e.g. "24/24 sessions").

### Calculation

```
Source: practice_sessions[] from conversation_sessions collection

completedSessions = count of sessions where duration_minutes > 0.3

completionRate = round((completedSessions / totalSessions) × 100)
```

### Threshold rationale: 0.3 minutes (18 seconds)
Voice sessions range from 1–30 minutes. A session with `duration_minutes = 0.0` represents a failed WebRTC connection (never started). Sessions of 0.1–0.3 min (6–18 seconds) represent immediate disconnects before meaningful speech. Sessions above 0.3 min reliably contain real practice. Using 1.0 min as the threshold (previous implementation) incorrectly classified all 1-minute sessions as abandoned.

### Real example — Jack Tune
```
Total practice sessions: 24
Sessions with duration_minutes > 0.3: 24
completionRate = 100%
```

### Display thresholds
```
>= 75%  → emerald (healthy)
>= 50%  → amber (moderate)
<  50%  → rose (concerning)
```

---

## Section 3 — Peak Practice Time

### What it shows
The time-of-day block when the learner most frequently practices, plus a 4-bar mini chart showing distribution across Morning/Afternoon/Evening/Night.

### Calculation

```
Source: practice_sessions[].created_at (UTC ISO datetime strings)

For each session with a valid created_at:
  h = UTC hour of created_at

  5 ≤ h < 12  → Morning
  12 ≤ h < 17 → Afternoon
  17 ≤ h < 21 → Evening
  h < 5 or h ≥ 21 → Night

peakTime = bucket with highest count
```

### Important note on timezone
`created_at` is stored in UTC. The peak time label reflects UTC hours. For learners in UTC+1 to UTC+3 (Netherlands, Turkey), displayed values are shifted 1-3 hours earlier than local time. A future improvement would use `user_timezone` (stored in `daily_stats`) to convert to local hours.

### Real example — Jack Tune
```
24 sessions distributed:
  Morning   (05:00–11:59 UTC): 2 sessions
  Afternoon (12:00–16:59 UTC): 11 sessions  ← PEAK
  Evening   (17:00–20:59 UTC): 8 sessions
  Night     (21:00–04:59 UTC): 3 sessions

Peak: Afternoon
```

---

## Section 4 — Confidence Trend

### What it shows
The learner's confidence score this week, and the delta (↑↓→) versus the previous week.

### Data source
`speaking_dna_history` collection — weekly snapshots generated after each speaking session analysis. Each document contains `strand_snapshots.confidence.score` (0.0–1.0) for that week.

### Calculation

```
Source: speaking_dna.weekly_trend[] — pre-formatted by backend
  (sorted chronologically, oldest first)

lastWeek = weekly_trend[last]
prevWeek = weekly_trend[second-to-last]

displayScore = lastWeek.confidence  (already scaled 0–100)
delta = lastWeek.confidence - prevWeek.confidence

delta > 0   → "↑ +Xpts vs last week"  (green)
delta < 0   → "↓ −Xpts vs last week"  (red)
delta = 0   → "→ stable"               (gray)
```

### Backend transformation
Raw DNA `confidence.score` is stored as float 0.0–1.0. Backend multiplies by 100 and rounds to integer:
```python
"confidence": round(conf.get("score", 0) * 100)
```

### Note on DNA profile `trend` field
The `speaking_dna_profiles` document has its own `strands.confidence.trend` field (e.g. `"improving"`). This field is set when the profile is updated and may be stale. The frontend **ignores** this field and uses the live `weekly_trend` delta instead for accuracy.

### Real example — Jack Tune
```
Week 17: confidence = 79%
Week 19: confidence = 71%
delta = 71 − 79 = −8%
Display: "↓ 8% vs last week" (rose color)

Note: Despite the −8% drop, dna_profiles.strands.confidence.trend = "improving"
This contradiction is because the profile was last updated at week 17
when the score was improving from week 13. The weekly_trend correctly
shows the more recent regression.
```

---

## Section 5 — What's Blocking Progress

### What it shows
Two groups of chips:
1. **Language gaps** — specific linguistic skills the learner needs to develop
2. **Emotional triggers** — situations the tutor should avoid to prevent anxiety

### Data sources and calculation

```
Language gaps:
  Source 1: speaking_dna_profiles.overall_profile.growth_areas[]
    → Human-readable weak dimensions (e.g. "vocabulary_variety")
  Source 2: speaking_dna_profiles.dna_strands.accuracy.common_errors[]
    → Recurring grammar error patterns
  Source 3: speaking_dna_profiles.dna_strands.accuracy.improving_areas[]
    → Areas where accuracy is currently low

  Combined, deduplicated, limited to 4 items
  Formatted: underscores → spaces, capitalize first letter

Emotional triggers:
  Source: speaking_dna_profiles.dna_strands.emotional.anxiety_triggers[]
    → Situational patterns that cause confidence drops

  Formatted: underscores → spaces, capitalize first letter
```

### Real example — Jack Tune
```
growth_areas: ["vocabulary_variety", "taking_challenges"]
accuracy.common_errors: []
accuracy.improving_areas: []
emotional.anxiety_triggers: ["thinking_pressure", "speaking_anxiety"]

Displayed language gaps:
  • Vocabulary variety
  • Taking challenges

Displayed triggers to avoid:
  • Thinking pressure
  • Speaking anxiety

Tutor interpretation: This learner is grammatically strong (accuracy=99%)
but needs encouragement to use wider vocabulary and attempt harder challenges.
Avoid time-pressured tasks or situations that create performance anxiety.
```

---

## Section 6 — Activity Heatmap

### What it shows
A 14-day GitHub-style grid where each cell represents one calendar day. Cell color intensity reflects practice volume on that day.

### Calculation

```
Source: daily_stats.recent_daily[] — up to 14 most recent records
  Each record: { date: "YYYY-MM-DD", minutes: float, sessions: int, xp: int }

For each day, intensity is determined by:

  minutes = 0 AND sessions = 0  → intensity 0  (gray,   no activity)
  minutes = 0 AND sessions > 0  → intensity 1  (teal/20, voice sessions with untracked time)
  0 < minutes < 5               → intensity 1  (teal/20, light)
  5 ≤ minutes < 15              → intensity 2  (teal/40, moderate)
  15 ≤ minutes < 30             → intensity 3  (teal/70, good)
  minutes ≥ 30                  → intensity 4  (teal,    excellent)

Color scale:
  0: bg-gray-100
  1: bg-[#4ECFBF]/20
  2: bg-[#4ECFBF]/40
  3: bg-[#4ECFBF]/70
  4: bg-[#4ECFBF]        (full teal = 30+ minutes)
```

### Important: minutes=0 with sessions>0
Some voice sessions store `conversation_time_seconds = 0` in the DB even though the session occurred (timing failure at the session-end webhook). In this case `minutes` calculates to 0.0 but `sessions > 0`. Without the sessions fallback, these days would show as gray (no activity) — incorrectly hiding real learner effort. Intensity 1 is assigned as the minimum acknowledgment.

### Real example — Jack Tune
```
Date        minutes  sessions  intensity  color
2026-05-08   7.0       9         2        teal/40
2026-05-06  21.0      18         3        teal/70
2026-05-04   0.0       4         1        teal/20  ← sessions>0 fallback
2026-05-03   0.0       1         1        teal/20  ← sessions>0 fallback
2026-04-24  18.0       0         3        teal/70
2026-04-23   3.0       2         1        teal/20
2026-04-22   0.0       1         1        teal/20  ← sessions>0 fallback
```

---

## Section 7 — Suggested Action

### What it shows
A single banner at the top of the Overview tab — the most important action the tutor should take right now. Color-coded by urgency: red (high), amber (medium), teal (normal).

### Decision tree

```
Priority order (first match wins):

1. engagementLevel === 'low'  [RED]
   → "Send an encouraging message — student hasn't practiced in a while"
   Trigger: activeLast7/7 < 28% (0–1 active days in last 7 calendar days)

2. completionRate < 60%  [AMBER]
   → "Sessions often abandoned — discuss session length and difficulty"
   Trigger: fewer than 60% of sessions lasted > 0.3 minutes

3. confidenceDelta < -5  [AMBER]
   → "Confidence dropped this week — focus on positive reinforcement"
   Trigger: weekly DNA confidence score dropped more than 5 points

4. weakAreas.length > 0  [TEAL]
   → "Work on: {weakAreas[0]}"
   e.g. "Work on: vocabulary variety"
   Trigger: at least one growth area identified in DNA profile

5. Default  [TEAL]
   → "Student is on track — maintain current pace and introduce
      slightly harder challenges"
```

### Real example — Jack Tune (verified 2026-05-11)
```
engagementLevel: 'medium' (2/7 = 29%) → does NOT trigger rule 1
completionRate: 100% → does NOT trigger rule 2
confidenceDelta: -8% → TRIGGERS rule 3

Displayed action (amber):
"Confidence dropped this week — focus on positive reinforcement
and familiar topics"
```

---

## Section 8 — Speaking DNA Strands

### What it shows
Six horizontal bars (0–100%) representing dimensions of speaking behavior, each with a color, description, and context hint for the tutor.

### How scores are derived

Each strand is stored as a structured object in `speaking_dna_profiles.dna_strands`. The score shown in the bar is computed from the most meaningful sub-field for each strand:

| Strand | Source field | Formula | Jack Tune |
|---|---|---|---|
| **Rhythm** | `consistency_score` (0.0–1.0) | `min(score × 100, 100)` | **30%** |
| **Confidence** | `score` (0.0–1.0) | `score × 100` | **71%** |
| **Vocabulary** | `new_word_attempt_rate` (0.0–1.0) | `min(rate × 100, 100)` | **60%** |
| **Accuracy** | `grammar_accuracy` (0.0–1.0) | `accuracy × 100` | **99%** |
| **Learning Style** | `retry_rate` (0.0–1.0) | `min(rate × 100, 100)` | **59%** |
| **Emotional Arc** | `session_end_confidence` (0.0–1.0) | `end_confidence × 100` | **65%** |

### What each strand means for a tutor

| Strand | High score means | Low score means | Tutor action |
|---|---|---|---|
| **Rhythm** | Consistent, natural pace | Erratic speed, long pauses | Use rhythm exercises, shadowing |
| **Confidence** | Fluent, minimal fillers | Hesitant, many "um/uh" | Positive reinforcement, familiar topics |
| **Vocabulary** | Tries new words regularly | Repeats same simple words | Introduce vocab challenges |
| **Accuracy** | Grammar almost always correct | Frequent grammar errors | Structured grammar focus |
| **Learning Style** | Persists through difficulty | Avoids hard material | Gradually increase difficulty |
| **Emotional Arc** | Ends sessions more confidently | Confidence declines mid-session | Shorter sessions, clear wins |

### Weekly trend (from `speaking_dna_history`)
Each week, a snapshot of all 6 strands is stored. The `weekly_trend` array shows up to 8 weeks of confidence scores, enabling the tutor to see whether improvement is sustained or temporary.

---

## Section 9 — Challenge Performance

### Metrics shown in Challenges tab summary row

| Metric | Formula | Jack Tune |
|---|---|---|
| Sessions Played | `challenge_sessions.length` | 33 |
| Correct Answers | `Σ correct_answers` | 39 |
| "out of N questions" | `Σ total_challenges` | 55 |
| Total XP | `Σ total_xp` | 1,670 |
| Overall Accuracy | `(Σ correct_answers / Σ total_challenges) × 100` | **71%** |

### Why NOT use the per-session `accuracy` field
Each challenge session has its own `accuracy` field. Averaging these across sessions gives a misleading result:
- 15 of 33 sessions were abandoned (no `end_time`) and have `accuracy = 0`
- Simple average: `Σ(accuracy_i) / 33 = 22%` — incorrect
- Correct method: sum all correct answers, divide by sum of all questions = **71%**

This is the same principle as batting average in baseball — you count total hits over total at-bats, not average the per-game averages.

---

## Section 10 — Assessment History

### Data source
`assessments` collection documents with fields: `language`, `level`, `score` (0–100), `feedback` (text), `created_at`.

### Score color coding
```
score ≥ 80  → emerald  (proficient)
score ≥ 60  → amber    (developing)
score <  60 → rose     (needs support)
```

### Real example — Jack Tune
```
Dutch  A1  score: 75  (amber) — "Good pronunciation, work on fluency"
French B1  score: 82  (emerald) — "Excellent vocabulary, minor grammar issues"
```

---

## Appendix: Data Pipeline

```
MongoDB Collections
       │
       ▼
GET /tutor/dashboard/{id}/learner/{uid}/details
  ├── asyncio.gather() — parallel fetch:
  │   ├── learning_plans.find(user_id)
  │   ├── conversation_sessions.find(user_id) [sorted by created_at desc]
  │   ├── challenge_sessions.find(user_id)    [sorted by created_at desc]
  │   ├── daily_stats.find(user_id)           [sorted by date desc, limit 30]
  │   ├── speaking_dna_profiles.find_one(user_id)
  │   ├── speaking_dna_history.find(user_id)  [sorted by week_number desc, limit 8]
  │   ├── sentence_analysis_jobs.find(user_id, status=completed)
  │   └── assessments.find(user_id)           [sorted by created_at desc]
  │
  └── Format & return JSON
       │
       ▼
Frontend (React/Next.js)
  ├── Engagement score    — computed from daily_stats.recent_daily
  ├── Completion rate     — computed from practice_sessions
  ├── Peak time           — computed from practice_sessions created_at hours
  ├── Confidence trend    — computed from speaking_dna.weekly_trend
  ├── Blocking areas      — read from speaking_dna.growth_areas + triggers
  ├── Heatmap             — rendered from daily_stats.recent_daily
  └── Suggested action    — decision tree over all computed metrics
```

---

## Appendix: Threshold Rationale Summary

| Metric | Threshold | Rationale |
|---|---|---|
| Completion rate | `duration > 0.3 min` | 18 seconds separates failed connections from real practice |
| Engagement — High | `≥ 57%` (4/7 days) | Consistent daily practice defined as practicing most days |
| Engagement — Medium | `≥ 28%` (2/7 days) | Some engagement, but irregular |
| Engagement — Low | `< 28%` (0–1 days) | At risk of dropping out; tutor intervention recommended |
| Confidence drop alert | `delta < -5 pts` | Noise filter; minor fluctuations (<5 pts) are normal |
| Heatmap intensity 1 | `sessions > 0, minutes = 0` | Acknowledge session even if time tracking failed |
| Heatmap intensity 4 | `minutes ≥ 30` | 30+ min/day is excellent for language practice |
| Assessment — proficient | `score ≥ 80` | CEFR-aligned; 80+ indicates solid level mastery |
| Assessment — developing | `score ≥ 60` | Pass threshold; more practice needed |
| Challenge accuracy | `Σ correct / Σ total` | Aggregate ratio, not average of ratios (avoids abandoned session bias) |
