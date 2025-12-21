# Language Learning Gamification & Statistics System
## Backend Design Specification v1.0

**Date**: 2025-12-21
**Status**: Design Phase
**Author**: Backend Architecture Team

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Requirements Overview](#2-requirements-overview)
3. [Data Model Design](#3-data-model-design)
4. [Aggregation Strategy](#4-aggregation-strategy)
5. [API Contract Design](#5-api-contract-design)
6. [Implementation Plan](#6-implementation-plan)
7. [Migration Strategy](#7-migration-strategy)
8. [Performance Considerations](#8-performance-considerations)

---

## 1. Current State Analysis

### 1.1 Existing Data Structures

#### `users.challengeStats` (Embedded Document)
```javascript
{
  totalCompleted: 0,              // Lifetime total
  currentStreak: 0,               // Consecutive days
  lastChallengeDate: null,        // Last practice date
  completedToday: [],             // Challenge IDs (resets daily)
  completionHistory: {            // Never deleted
    "2025-12-21": [
      {
        challenge_id: "xxx",
        correct: true,
        time_spent: 12,
        completed_at: "2025-12-21T10:30:00Z"
      }
    ]
  }
}
```

**Issues**:
- No language/level granularity
- No challenge type breakdown
- No accuracy metrics per category
- No rolling window support
- Limited analytics capability

#### `challenge_sessions` (Collection)
```javascript
{
  _id: "session_xxx",
  user_id: "user_xxx",
  language: "spanish",
  level: "B1",
  challenge_type: "micro_quiz",
  source: "reference",
  correct_answers: 7,
  wrong_answers: 3,
  max_combo: 5,
  total_xp: 120,
  start_time: ISODate(...),
  end_time: ISODate(...),
  created_at: ISODate(...)
}
```

**Advantages**:
- Event-based data (good for analytics)
- Contains granular metadata
- Can aggregate from this

**Issues**:
- No efficient aggregation (requires full scan)
- Missing timezone support
- No pre-computed summaries

---

## 2. Requirements Overview

### 2.1 Three Statistical Layers

| Layer | Reset Policy | Use Case | Time Window |
|-------|--------------|----------|-------------|
| **Daily Stats** | Every 24h (timezone-aware) | Today's Progress Card, Streak | Current day only |
| **Recent Performance** | Rolling window | Last 7 Days Summary, Trends | 3-7 days rolling |
| **Long-Term Progress** | Never | Profile/Progress screens, AI Tutor | All time |

### 2.2 Supported Dimensions

- **Languages**: dutch, spanish, german, french, portuguese
- **CEFR Levels**: A1, A2, B1, B2, C1, C2
- **Challenge Types**: error_spotting, swipe_fix, micro_quiz, smart_flashcard, native_check, brain_tickler

### 2.3 Key Metrics

#### Daily Stats
- Challenges completed today
- Accuracy today (correct/total)
- Correct/incorrect counts
- Current streak
- XP earned today
- Active languages/levels today

#### Recent Performance (7-day)
- Total challenges (rolling)
- Average accuracy (rolling)
- Most played challenge type
- Most practiced language
- Weakest CEFR level (lowest accuracy)
- Daily activity pattern
- XP trend

#### Long-Term Progress
- Total challenges by language
- Total challenges by CEFR level
- Total challenges by type
- Mastery indicators (% completion per type/level)
- Language progression path
- Time invested per language
- Achievement history

---

## 3. Data Model Design

### 3.1 Enhanced Event Schema: `challenge_sessions`

**Keep existing fields + add:**

```javascript
// challenge_sessions collection (PRIMARY DATA SOURCE)
{
  _id: ObjectId,
  user_id: String,

  // Dimension fields
  language: String,                    // spanish, dutch, etc.
  level: String,                       // A1, A2, B1, etc.
  challenge_type: String,              // micro_quiz, error_spotting, etc.
  source: String,                      // reference, learning_plan

  // Session metrics
  correct_answers: Number,
  wrong_answers: Number,
  total_challenges: Number,            // NEW: correct + wrong
  accuracy: Number,                    // NEW: Pre-calculated (%)
  max_combo: Number,
  total_xp: Number,

  // Timing
  start_time: ISODate,
  end_time: ISODate,
  duration_seconds: Number,            // NEW: Pre-calculated
  created_at: ISODate,

  // NEW: Timezone support
  user_timezone: String,               // e.g., "America/New_York"
  local_date: String,                  // e.g., "2025-12-21" (in user's timezone)

  // Reference
  challenge_ids: [String],             // IDs of challenges in session
  is_active: Boolean,

  // NEW: Analytics tags
  tags: {
    is_first_session: Boolean,
    is_weekend: Boolean,
    session_number_today: Number       // 1st, 2nd, 3rd session of the day
  }
}
```

**Indexes**:
```javascript
// Compound indexes for efficient queries
{ user_id: 1, local_date: -1 }                     // Daily stats
{ user_id: 1, created_at: -1 }                     // Recent activity
{ user_id: 1, language: 1, level: 1, created_at: -1 }  // Language-specific queries
{ user_id: 1, challenge_type: 1, created_at: -1 }      // Type-specific queries
{ local_date: 1, created_at: 1 }                   // TTL index for cleanup
```

---

### 3.2 Daily Statistics Summary: `daily_stats`

**Purpose**: Pre-aggregated daily summaries for fast retrieval
**Reset Policy**: Documents remain; calculations use `local_date` filter
**Update Strategy**: Incremental update on each session completion

```javascript
// daily_stats collection (MATERIALIZED VIEW)
{
  _id: ObjectId,
  user_id: String,
  local_date: String,              // "2025-12-21" (user's timezone)
  user_timezone: String,

  // Overall daily metrics
  total_sessions: Number,
  total_challenges: Number,
  correct_challenges: Number,
  incorrect_challenges: Number,
  accuracy_percent: Number,
  total_xp: Number,
  total_time_seconds: Number,

  // Breakdown by language
  by_language: {
    spanish: {
      challenges: Number,
      correct: Number,
      incorrect: Number,
      accuracy: Number,
      xp: Number
    },
    dutch: { ... }
  },

  // Breakdown by CEFR level
  by_level: {
    A1: {
      challenges: Number,
      correct: Number,
      accuracy: Number
    },
    B1: { ... }
  },

  // Breakdown by challenge type
  by_type: {
    micro_quiz: {
      challenges: Number,
      correct: Number,
      accuracy: Number,
      xp: Number
    },
    error_spotting: { ... }
  },

  // Streak tracking
  is_streak_day: Boolean,          // Did user practice?
  streak_count: Number,            // Streak on this day

  // Metadata
  created_at: ISODate,
  updated_at: ISODate,
  last_session_id: String
}
```

**Indexes**:
```javascript
{ user_id: 1, local_date: -1 }           // Primary query pattern
{ local_date: 1 }                        // Cleanup old data (optional TTL)
```

---

### 3.3 User Profile Statistics: `users.stats`

**Purpose**: Lightweight, denormalized stats in user document
**Update Strategy**: Updated on session completion
**Reset Policy**: Never (cumulative only)

```javascript
// Embedded in users collection
{
  _id: ObjectId,
  email: String,
  // ... existing fields ...

  stats: {
    // Daily (ephemeral - calculated from daily_stats)
    today: {
      challenges: Number,
      accuracy: Number,
      xp: Number,
      last_updated: ISODate
    },

    // Streak (persistent)
    current_streak: Number,
    longest_streak: Number,
    last_practice_date: String,      // "2025-12-21"

    // Lifetime (never reset)
    lifetime: {
      total_challenges: Number,
      total_sessions: Number,
      total_xp: Number,
      total_time_minutes: Number,

      // Language progress
      by_language: {
        spanish: {
          total_challenges: Number,
          highest_level: String,       // "B2"
          total_xp: Number,
          started_at: ISODate,
          last_practiced: ISODate
        }
      },

      // CEFR level progress
      by_level: {
        B1: {
          total_challenges: Number,
          accuracy: Number,
          mastery_percent: Number      // 0-100
        }
      },

      // Challenge type mastery
      by_type: {
        micro_quiz: {
          total_challenges: Number,
          accuracy: Number,
          mastery_level: Number        // 1-5 stars
        }
      }
    },

    // Last updated
    last_calculated: ISODate
  }
}
```

---

### 3.4 Rolling Window View: `recent_performance`

**Purpose**: Pre-computed 7-day rolling metrics
**Update Strategy**: Recomputed nightly OR on-demand with cache
**Reset Policy**: Always shows last 7 days

**Option A: Materialized View (Recommended)**
```javascript
// recent_performance collection
{
  _id: ObjectId,
  user_id: String,
  window_start: ISODate,           // 7 days ago
  window_end: ISODate,             // Today

  // Aggregate metrics
  total_sessions: Number,
  total_challenges: Number,
  average_accuracy: Number,
  total_xp: Number,

  // Most/least practiced
  most_practiced_type: String,     // "micro_quiz"
  most_practiced_language: String, // "spanish"
  weakest_level: String,           // "C1" (lowest accuracy)
  strongest_level: String,         // "A2" (highest accuracy)

  // Trend data (daily breakdown)
  daily_breakdown: [
    {
      date: "2025-12-21",
      challenges: Number,
      accuracy: Number,
      xp: Number,
      active_time_minutes: Number
    }
  ],

  // Language distribution
  language_distribution: {
    spanish: { challenges: Number, percentage: Number },
    dutch: { challenges: Number, percentage: Number }
  },

  // Type distribution
  type_distribution: {
    micro_quiz: { challenges: Number, percentage: Number }
  },

  // Metadata
  calculated_at: ISODate,
  expires_at: ISODate              // Cache for 1 hour
}
```

**Indexes**:
```javascript
{ user_id: 1, expires_at: 1 }    // Cache lookup
{ expires_at: 1 }                // TTL index (auto-delete stale)
```

**Option B: On-Demand Calculation (Simpler)**
- Calculate from `challenge_sessions` where `created_at >= (now - 7 days)`
- Cache result in Redis/memory for 1 hour
- No separate collection needed
- Trade-off: Slower but simpler

---

## 4. Aggregation Strategy

### 4.1 Event-Based Architecture (Recommended)

**Principle**: Source of truth is `challenge_sessions` (event log)

**Flow**:
```
User completes challenge session
         ↓
1. Insert into challenge_sessions (with timezone data)
         ↓
2. Update daily_stats (incremental aggregation)
         ↓
3. Update users.stats.lifetime (counters)
         ↓
4. Invalidate recent_performance cache (if using cache)
         ↓
5. Return response to client
```

**Advantages**:
- Single source of truth (sessions)
- Can rebuild summaries anytime
- Supports time-travel queries
- Easier debugging

**Implementation**:
```python
async def complete_challenge_session(session_data):
    # 1. Calculate derived fields
    session_data['total_challenges'] = session_data['correct_answers'] + session_data['wrong_answers']
    session_data['accuracy'] = (session_data['correct_answers'] / session_data['total_challenges']) * 100
    session_data['duration_seconds'] = (session_data['end_time'] - session_data['start_time']).total_seconds()

    # Get user timezone
    user_timezone = await get_user_timezone(session_data['user_id'])
    session_data['user_timezone'] = user_timezone
    session_data['local_date'] = convert_to_local_date(session_data['created_at'], user_timezone)

    # 2. Insert session event
    session_id = await challenge_sessions_collection.insert_one(session_data)

    # 3. Update daily stats (upsert + increment)
    await update_daily_stats(session_data)

    # 4. Update lifetime stats
    await update_lifetime_stats(session_data)

    # 5. Invalidate rolling window cache
    await invalidate_recent_performance_cache(session_data['user_id'])

    return session_id
```

---

### 4.2 Daily Stats Calculation

**Strategy**: Incremental updates using MongoDB `$inc` operators

```python
async def update_daily_stats(session_data):
    """
    Update daily_stats document for today.
    Creates if doesn't exist (upsert).
    """
    user_id = session_data['user_id']
    local_date = session_data['local_date']
    language = session_data['language']
    level = session_data['level']
    challenge_type = session_data['challenge_type']

    # Prepare increments
    increments = {
        'total_sessions': 1,
        'total_challenges': session_data['total_challenges'],
        'correct_challenges': session_data['correct_answers'],
        'incorrect_challenges': session_data['wrong_answers'],
        'total_xp': session_data['total_xp'],
        'total_time_seconds': session_data['duration_seconds'],

        # Language breakdown
        f'by_language.{language}.challenges': session_data['total_challenges'],
        f'by_language.{language}.correct': session_data['correct_answers'],
        f'by_language.{language}.incorrect': session_data['wrong_answers'],
        f'by_language.{language}.xp': session_data['total_xp'],

        # Level breakdown
        f'by_level.{level}.challenges': session_data['total_challenges'],
        f'by_level.{level}.correct': session_data['correct_answers'],

        # Type breakdown
        f'by_type.{challenge_type}.challenges': session_data['total_challenges'],
        f'by_type.{challenge_type}.correct': session_data['correct_answers'],
        f'by_type.{challenge_type}.xp': session_data['total_xp'],
    }

    # Upsert daily stats
    await daily_stats_collection.update_one(
        {
            'user_id': user_id,
            'local_date': local_date
        },
        {
            '$inc': increments,
            '$set': {
                'user_timezone': session_data['user_timezone'],
                'updated_at': datetime.utcnow(),
                'last_session_id': session_data['_id']
            },
            '$setOnInsert': {
                'created_at': datetime.utcnow(),
                'is_streak_day': True
            }
        },
        upsert=True
    )

    # Recalculate accuracy percentages (post-increment)
    await recalculate_daily_accuracy(user_id, local_date)
```

---

### 4.3 Rolling Window Calculation

**Strategy**: Aggregate from `challenge_sessions` with date filter

```python
async def get_recent_performance(user_id: str, days: int = 7):
    """
    Calculate 7-day rolling performance.
    Uses cache (1 hour TTL).
    """
    # 1. Check cache
    cached = await recent_performance_collection.find_one({
        'user_id': user_id,
        'expires_at': {'$gt': datetime.utcnow()}
    })

    if cached:
        return cached

    # 2. Calculate from events
    window_start = datetime.utcnow() - timedelta(days=days)

    # Aggregate pipeline
    pipeline = [
        {
            '$match': {
                'user_id': user_id,
                'created_at': {'$gte': window_start}
            }
        },
        {
            '$group': {
                '_id': {
                    'date': '$local_date',
                    'language': '$language',
                    'type': '$challenge_type'
                },
                'total_challenges': {'$sum': '$total_challenges'},
                'correct_challenges': {'$sum': '$correct_answers'},
                'total_xp': {'$sum': '$total_xp'},
                'total_time': {'$sum': '$duration_seconds'}
            }
        },
        {
            '$group': {
                '_id': None,
                'total_challenges': {'$sum': '$total_challenges'},
                'total_correct': {'$sum': '$correct_challenges'},
                'total_xp': {'$sum': '$total_xp'},
                'by_language': {'$push': '$$ROOT'},
                'daily_breakdown': {'$push': '$$ROOT'}
            }
        }
    ]

    result = await challenge_sessions_collection.aggregate(pipeline).to_list(1)

    if not result:
        return get_empty_recent_performance()

    # 3. Post-process and cache
    processed = process_recent_performance(result[0], days)
    processed['user_id'] = user_id
    processed['window_start'] = window_start
    processed['window_end'] = datetime.utcnow()
    processed['calculated_at'] = datetime.utcnow()
    processed['expires_at'] = datetime.utcnow() + timedelta(hours=1)

    # 4. Cache result
    await recent_performance_collection.update_one(
        {'user_id': user_id},
        {'$set': processed},
        upsert=True
    )

    return processed
```

---

### 4.4 Lifetime Stats Update

**Strategy**: Incremental counters in user document

```python
async def update_lifetime_stats(session_data):
    """
    Update lifetime statistics in users collection.
    """
    user_id = session_data['user_id']
    language = session_data['language']
    level = session_data['level']
    challenge_type = session_data['challenge_type']

    increments = {
        'stats.lifetime.total_challenges': session_data['total_challenges'],
        'stats.lifetime.total_sessions': 1,
        'stats.lifetime.total_xp': session_data['total_xp'],
        'stats.lifetime.total_time_minutes': session_data['duration_seconds'] / 60,

        f'stats.lifetime.by_language.{language}.total_challenges': session_data['total_challenges'],
        f'stats.lifetime.by_language.{language}.total_xp': session_data['total_xp'],

        f'stats.lifetime.by_level.{level}.total_challenges': session_data['total_challenges'],

        f'stats.lifetime.by_type.{challenge_type}.total_challenges': session_data['total_challenges'],
    }

    updates = {
        'stats.last_calculated': datetime.utcnow(),
        f'stats.lifetime.by_language.{language}.last_practiced': datetime.utcnow(),
    }

    # Update highest level if needed
    current_user = await users_collection.find_one({'_id': ObjectId(user_id)})
    current_highest = current_user.get('stats', {}).get('lifetime', {}).get('by_language', {}).get(language, {}).get('highest_level')

    if not current_highest or level_rank(level) > level_rank(current_highest):
        updates[f'stats.lifetime.by_language.{language}.highest_level'] = level

    await users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {
            '$inc': increments,
            '$set': updates,
            '$setOnInsert': {
                f'stats.lifetime.by_language.{language}.started_at': datetime.utcnow()
            }
        }
    )
```

---

## 5. API Contract Design

### 5.1 Daily Statistics Endpoint

**GET `/api/stats/daily`**

**Purpose**: Get today's progress for "Today's Progress Card"

**Query Parameters**:
- `timezone` (optional): User's timezone (e.g., "America/New_York"). Defaults to user profile timezone.

**Response**:
```json
{
  "success": true,
  "date": "2025-12-21",
  "timezone": "America/New_York",

  "overall": {
    "total_sessions": 3,
    "total_challenges": 30,
    "correct": 24,
    "incorrect": 6,
    "accuracy": 80.0,
    "total_xp": 360,
    "time_minutes": 45
  },

  "by_language": {
    "spanish": {
      "challenges": 20,
      "correct": 16,
      "accuracy": 80.0,
      "xp": 240
    },
    "dutch": {
      "challenges": 10,
      "correct": 8,
      "accuracy": 80.0,
      "xp": 120
    }
  },

  "by_level": {
    "B1": {
      "challenges": 15,
      "correct": 12,
      "accuracy": 80.0
    },
    "B2": {
      "challenges": 15,
      "correct": 12,
      "accuracy": 80.0
    }
  },

  "by_type": {
    "micro_quiz": {
      "challenges": 10,
      "correct": 8,
      "accuracy": 80.0,
      "xp": 120
    },
    "error_spotting": {
      "challenges": 10,
      "correct": 8,
      "accuracy": 80.0,
      "xp": 120
    },
    "brain_tickler": {
      "challenges": 10,
      "correct": 8,
      "accuracy": 80.0,
      "xp": 120
    }
  },

  "streak": {
    "current": 7,
    "is_active_today": true,
    "next_milestone": 10
  },

  "metadata": {
    "last_updated": "2025-12-21T15:30:00Z",
    "has_more_data": false
  }
}
```

**Implementation**:
```python
@router.get("/api/stats/daily")
async def get_daily_stats(
    current_user: UserResponse = Depends(get_current_user),
    timezone: Optional[str] = None
):
    """Get today's statistics."""
    user_id = current_user.id

    # Get user's timezone
    if not timezone:
        timezone = current_user.timezone or "UTC"

    # Get today's date in user's timezone
    local_date = get_local_date(timezone)

    # Fetch daily stats
    daily_stat = await daily_stats_collection.find_one({
        'user_id': user_id,
        'local_date': local_date
    })

    if not daily_stat:
        return get_empty_daily_stats(local_date, timezone)

    # Get streak info from user profile
    user = await users_collection.find_one({'_id': ObjectId(user_id)})
    streak_info = user.get('stats', {}).get('current_streak', 0)

    return {
        'success': True,
        'date': local_date,
        'timezone': timezone,
        'overall': extract_overall_stats(daily_stat),
        'by_language': daily_stat.get('by_language', {}),
        'by_level': daily_stat.get('by_level', {}),
        'by_type': daily_stat.get('by_type', {}),
        'streak': {
            'current': streak_info,
            'is_active_today': True,
            'next_milestone': calculate_next_milestone(streak_info)
        },
        'metadata': {
            'last_updated': daily_stat.get('updated_at'),
            'has_more_data': False
        }
    }
```

---

### 5.2 Recent Performance Endpoint

**GET `/api/stats/recent`**

**Purpose**: Get 7-day rolling window statistics for trend analysis

**Query Parameters**:
- `days` (optional): Number of days to look back (default: 7, max: 30)
- `timezone` (optional): User's timezone

**Response**:
```json
{
  "success": true,
  "window": {
    "start": "2025-12-15",
    "end": "2025-12-21",
    "days": 7
  },

  "summary": {
    "total_sessions": 15,
    "total_challenges": 150,
    "average_accuracy": 82.5,
    "total_xp": 1800,
    "total_time_minutes": 225,
    "active_days": 6
  },

  "insights": {
    "most_practiced_type": "micro_quiz",
    "most_practiced_language": "spanish",
    "weakest_level": "C1",
    "weakest_level_accuracy": 65.0,
    "strongest_level": "B1",
    "strongest_level_accuracy": 90.0,
    "improvement_trend": "positive",
    "accuracy_change_percent": 5.2
  },

  "daily_breakdown": [
    {
      "date": "2025-12-21",
      "challenges": 30,
      "accuracy": 85.0,
      "xp": 360,
      "time_minutes": 45,
      "sessions": 3
    },
    {
      "date": "2025-12-20",
      "challenges": 25,
      "accuracy": 80.0,
      "xp": 300,
      "time_minutes": 38,
      "sessions": 2
    }
    // ... 5 more days
  ],

  "language_distribution": {
    "spanish": {
      "challenges": 100,
      "percentage": 66.7,
      "accuracy": 85.0
    },
    "dutch": {
      "challenges": 50,
      "percentage": 33.3,
      "accuracy": 78.0
    }
  },

  "type_distribution": {
    "micro_quiz": {
      "challenges": 50,
      "percentage": 33.3,
      "accuracy": 82.0
    },
    "error_spotting": {
      "challenges": 40,
      "percentage": 26.7,
      "accuracy": 85.0
    }
    // ... other types
  },

  "level_performance": {
    "A1": {
      "challenges": 20,
      "accuracy": 95.0,
      "rank": "excellent"
    },
    "B1": {
      "challenges": 60,
      "accuracy": 85.0,
      "rank": "good"
    },
    "C1": {
      "challenges": 40,
      "accuracy": 65.0,
      "rank": "needs_work"
    }
  },

  "metadata": {
    "calculated_at": "2025-12-21T15:30:00Z",
    "cached_until": "2025-12-21T16:30:00Z"
  }
}
```

---

### 5.3 Long-Term Progress Endpoint

**GET `/api/stats/lifetime`**

**Purpose**: Get cumulative learning progress for profile screens

**Query Parameters**:
- `language` (optional): Filter by specific language
- `include_achievements` (optional): Include achievement history (default: false)

**Response**:
```json
{
  "success": true,

  "summary": {
    "total_challenges": 1500,
    "total_sessions": 75,
    "total_xp": 18000,
    "total_time_hours": 37.5,
    "member_since": "2025-01-15",
    "longest_streak": 21,
    "current_streak": 7
  },

  "language_progress": {
    "spanish": {
      "total_challenges": 800,
      "highest_level": "B2",
      "total_xp": 9600,
      "started_at": "2025-01-15",
      "last_practiced": "2025-12-21",
      "time_hours": 20.0,
      "mastery_percent": 65.5,
      "level_breakdown": {
        "A1": { "completed": 100, "accuracy": 95.0, "mastered": true },
        "A2": { "completed": 100, "accuracy": 90.0, "mastered": true },
        "B1": { "completed": 200, "accuracy": 85.0, "mastered": true },
        "B2": { "completed": 400, "accuracy": 75.0, "mastered": false }
      }
    },
    "dutch": {
      "total_challenges": 700,
      "highest_level": "B1",
      "total_xp": 8400,
      "started_at": "2025-03-01",
      "last_practiced": "2025-12-20",
      "time_hours": 17.5,
      "mastery_percent": 55.0,
      "level_breakdown": { ... }
    }
  },

  "level_mastery": {
    "A1": {
      "total_challenges": 200,
      "accuracy": 95.0,
      "mastery_stars": 5,
      "languages": ["spanish", "dutch"]
    },
    "B1": {
      "total_challenges": 600,
      "accuracy": 85.0,
      "mastery_stars": 4,
      "languages": ["spanish", "dutch"]
    }
    // ... other levels
  },

  "challenge_type_mastery": {
    "micro_quiz": {
      "total_challenges": 500,
      "accuracy": 85.0,
      "mastery_level": 4,
      "rank": "advanced",
      "favorite": true
    },
    "error_spotting": {
      "total_challenges": 400,
      "accuracy": 82.0,
      "mastery_level": 4,
      "rank": "advanced",
      "favorite": false
    }
    // ... other types
  },

  "learning_path": {
    "current_focus": "spanish B2",
    "suggested_next": "spanish C1",
    "weak_areas": ["dutch C1", "german B2"],
    "ready_for_next_level": ["spanish", "dutch"]
  },

  "achievements": {
    "total_unlocked": 15,
    "total_xp_from_achievements": 1250,
    "recent_achievements": [
      {
        "id": "perfect_session",
        "title": "Perfect Session",
        "unlocked_at": "2025-12-20T10:30:00Z",
        "xp_bonus": 100
      }
    ]
  },

  "milestones": {
    "next_milestone": {
      "type": "total_challenges",
      "current": 1500,
      "target": 2000,
      "progress_percent": 75.0,
      "reward_xp": 500
    },
    "upcoming": [
      {
        "type": "spanish_b2_mastery",
        "current": 65.5,
        "target": 80.0,
        "progress_percent": 81.875
      }
    ]
  },

  "metadata": {
    "calculated_at": "2025-12-21T15:30:00Z",
    "data_since": "2025-01-15"
  }
}
```

---

### 5.4 Unified Stats Endpoint (Optional)

**GET `/api/stats/all`**

**Purpose**: Get all three layers in one request (for mobile app efficiency)

**Response**:
```json
{
  "success": true,
  "daily": { ... },      // Same as /api/stats/daily
  "recent": { ... },     // Same as /api/stats/recent
  "lifetime": { ... }    // Same as /api/stats/lifetime
}
```

**Use Case**: Reduce network requests on app load

---

## 6. Implementation Plan

### Phase 1: Foundation (Week 1)

**Goals**:
- Enhance `challenge_sessions` schema
- Implement timezone support
- Create `daily_stats` collection

**Tasks**:
1. Add migration script to backfill existing sessions:
   - Calculate `total_challenges`, `accuracy`, `duration_seconds`
   - Add default `user_timezone` (UTC)
   - Calculate `local_date` from `created_at`

2. Update session completion endpoint:
   - Calculate new fields
   - Get user timezone from profile
   - Convert to local date

3. Implement `update_daily_stats()` function:
   - Incremental aggregation logic
   - Upsert daily summary documents

4. Create `/api/stats/daily` endpoint:
   - Return today's stats from `daily_stats`
   - Include streak info from user profile

5. Create indexes:
   ```javascript
   db.challenge_sessions.createIndex({ user_id: 1, local_date: -1 })
   db.daily_stats.createIndex({ user_id: 1, local_date: -1 })
   ```

**Testing**:
- Verify daily stats update correctly after session
- Test timezone edge cases (midnight boundary)
- Verify streak logic works across days

---

### Phase 2: Recent Performance (Week 2)

**Goals**:
- Implement rolling window calculations
- Add caching mechanism
- Create insights/trends

**Tasks**:
1. Implement `get_recent_performance()` function:
   - Aggregation pipeline from `challenge_sessions`
   - Calculate averages, distributions
   - Identify weak/strong areas

2. Add caching layer:
   - Option A: `recent_performance` collection with TTL
   - Option B: Redis cache (if available)

3. Create `/api/stats/recent` endpoint:
   - Return 7-day rolling stats
   - Include daily breakdown
   - Add trend calculations

4. Implement invalidation:
   - Clear cache on new session completion

**Testing**:
- Verify rolling window calculates correctly
- Test cache hit/miss scenarios
- Verify trends are accurate

---

### Phase 3: Lifetime Progress (Week 3)

**Goals**:
- Implement lifetime stats tracking
- Add mastery calculations
- Create learning path suggestions

**Tasks**:
1. Update user schema:
   - Add `stats.lifetime` structure
   - Migrate existing data

2. Implement `update_lifetime_stats()`:
   - Increment counters per language/level/type
   - Track highest level achieved
   - Update last practiced timestamps

3. Create `/api/stats/lifetime` endpoint:
   - Return cumulative progress
   - Calculate mastery percentages
   - Suggest learning path

4. Add mastery calculations:
   - Stars/levels based on challenges completed
   - Accuracy thresholds for "mastered"

**Testing**:
- Verify lifetime counters are accurate
- Test mastery calculations
- Verify learning path suggestions

---

### Phase 4: Optimization & AI Integration (Week 4)

**Goals**:
- Performance optimization
- Prepare for AI tutor integration
- Mobile app integration

**Tasks**:
1. Performance optimization:
   - Add compound indexes
   - Optimize aggregation pipelines
   - Profile query performance

2. AI integration preparation:
   - Create data export endpoint for AI
   - Structure stats for LLM consumption
   - Add context builder for prompts

3. Create `/api/stats/all` unified endpoint:
   - Reduce mobile network requests
   - Implement response compression

4. Documentation:
   - API documentation (OpenAPI/Swagger)
   - Mobile integration guide
   - Analytics dashboard guide

**Testing**:
- Load testing (1000+ sessions)
- Mobile integration testing
- AI prompt generation testing

---

## 7. Migration Strategy

### 7.1 Backward Compatibility

**Approach**: Maintain existing endpoints while adding new ones

**Existing Endpoints to Keep**:
- `POST /api/achievements/sessions/complete` - Keep as-is
- `GET /api/challenges/stats` - Keep for backward compatibility

**New Endpoints**:
- `GET /api/stats/daily` - New daily stats
- `GET /api/stats/recent` - New rolling stats
- `GET /api/stats/lifetime` - New lifetime stats

**Mobile App Migration Path**:
1. Backend deploys new endpoints (backward compatible)
2. Mobile app v2.0 uses new endpoints
3. Mobile app v1.x continues using old endpoints
4. After 90% adoption, deprecate old endpoints

---

### 7.2 Data Migration Script

```python
async def migrate_challenge_sessions():
    """
    Backfill existing challenge_sessions with new fields.
    """
    print("[MIGRATION] Starting challenge_sessions migration...")

    cursor = challenge_sessions_collection.find({
        'total_challenges': {'$exists': False}
    })

    migrated = 0
    async for session in cursor:
        # Calculate new fields
        total_challenges = session['correct_answers'] + session['wrong_answers']
        accuracy = (session['correct_answers'] / total_challenges * 100) if total_challenges > 0 else 0
        duration = (session['end_time'] - session['start_time']).total_seconds() if session.get('end_time') else 0

        # Get user timezone (default to UTC for old data)
        user = await users_collection.find_one({'_id': ObjectId(session['user_id'])})
        timezone = user.get('timezone', 'UTC') if user else 'UTC'

        # Calculate local_date
        local_date = convert_to_local_date(session['created_at'], timezone)

        # Update session
        await challenge_sessions_collection.update_one(
            {'_id': session['_id']},
            {
                '$set': {
                    'total_challenges': total_challenges,
                    'accuracy': accuracy,
                    'duration_seconds': duration,
                    'user_timezone': timezone,
                    'local_date': local_date,
                    'tags': {
                        'is_first_session': False,  # Unknown for historical data
                        'is_weekend': is_weekend(session['created_at']),
                        'session_number_today': 1  # Unknown
                    }
                }
            }
        )

        migrated += 1

        if migrated % 100 == 0:
            print(f"[MIGRATION] Migrated {migrated} sessions...")

    print(f"[MIGRATION] ✅ Migrated {migrated} sessions total")


async def rebuild_daily_stats():
    """
    Rebuild daily_stats from migrated challenge_sessions.
    """
    print("[MIGRATION] Rebuilding daily_stats...")

    # Clear existing daily_stats
    await daily_stats_collection.delete_many({})

    # Aggregate from sessions
    pipeline = [
        {
            '$group': {
                '_id': {
                    'user_id': '$user_id',
                    'local_date': '$local_date'
                },
                'sessions': {'$push': '$$ROOT'}
            }
        }
    ]

    cursor = challenge_sessions_collection.aggregate(pipeline)

    rebuilt = 0
    async for group in cursor:
        user_id = group['_id']['user_id']
        local_date = group['_id']['local_date']
        sessions = group['sessions']

        # Aggregate all sessions for this user-date
        daily_stat = aggregate_sessions_to_daily(sessions)
        daily_stat['user_id'] = user_id
        daily_stat['local_date'] = local_date

        await daily_stats_collection.insert_one(daily_stat)

        rebuilt += 1

        if rebuilt % 100 == 0:
            print(f"[MIGRATION] Rebuilt {rebuilt} daily stats...")

    print(f"[MIGRATION] ✅ Rebuilt {rebuilt} daily stats total")
```

---

## 8. Performance Considerations

### 8.1 Query Optimization

**Daily Stats**:
- Single document lookup by `user_id` + `local_date`
- O(1) with index
- Response time: < 10ms

**Recent Performance**:
- Aggregation over 7-30 days
- With caching: O(1) (cache hit)
- Without caching: O(n) where n = sessions in window
- Response time: < 50ms (cached), < 200ms (uncached)

**Lifetime Stats**:
- Single user document lookup (denormalized)
- O(1) with index
- Response time: < 10ms

### 8.2 Caching Strategy

**Redis Cache Structure** (if using Redis):
```
Key: "stats:daily:{user_id}:{date}"
TTL: 1 hour
Value: JSON serialized daily stats

Key: "stats:recent:{user_id}:{days}"
TTL: 1 hour
Value: JSON serialized recent performance

Key: "stats:lifetime:{user_id}"
TTL: 24 hours
Value: JSON serialized lifetime stats
```

**Cache Invalidation**:
- Daily stats: Invalidate on session completion for today
- Recent stats: Invalidate on any session completion
- Lifetime stats: Invalidate on session completion (or update directly)

### 8.3 Scalability Projections

**Assumptions**:
- 10,000 active users
- 5 sessions per user per day
- 50,000 sessions/day
- 18.25M sessions/year

**Storage**:
- `challenge_sessions`: ~1KB per session = 18.25GB/year
- `daily_stats`: ~5KB per user-day = 18.25GB/year (10k users × 365 days)
- Total: ~36.5GB/year (well within MongoDB limits)

**Query Load**:
- Daily stats queries: 50k/day (one per session completion)
- Recent stats queries: 10k/day (one per user login)
- Lifetime stats queries: 5k/day (profile views)

**Optimization Needed At**:
- 100k users: Add read replicas
- 1M users: Shard by `user_id`
- 10M users: Move to time-series database for sessions

---

## 9. API Integration Examples

### 9.1 Frontend: Today's Progress Card

```typescript
// TodayProgressCard.tsx
async function loadTodayStats() {
  const response = await fetch('/api/stats/daily', {
    headers: { Authorization: `Bearer ${token}` }
  });

  const data = await response.json();

  return {
    challenges: data.overall.total_challenges,
    accuracy: data.overall.accuracy,
    xp: data.overall.total_xp,
    streak: data.streak.current,
    breakdown: data.by_type
  };
}
```

### 9.2 Frontend: 7-Day Trend Chart

```typescript
// TrendChart.tsx
async function load7DayTrend() {
  const response = await fetch('/api/stats/recent?days=7', {
    headers: { Authorization: `Bearer ${token}` }
  });

  const data = await response.json();

  const chartData = data.daily_breakdown.map(day => ({
    date: day.date,
    challenges: day.challenges,
    accuracy: day.accuracy
  }));

  return chartData;
}
```

### 9.3 AI Tutor: Context Builder

```python
async def build_ai_tutor_context(user_id: str) -> str:
    """
    Build context string for AI tutor prompt.
    """
    # Get all three stat layers
    daily = await get_daily_stats(user_id)
    recent = await get_recent_performance(user_id)
    lifetime = await get_lifetime_stats(user_id)

    context = f"""
User Learning Context:

TODAY'S ACTIVITY:
- Completed {daily['overall']['total_challenges']} challenges with {daily['overall']['accuracy']}% accuracy
- Current {daily['streak']['current']}-day streak
- Focused on: {', '.join(daily['by_language'].keys())}

RECENT PERFORMANCE (Last 7 Days):
- Average accuracy: {recent['summary']['average_accuracy']}%
- Most practiced: {recent['insights']['most_practiced_language']} at {recent['insights']['most_practiced_type']}
- Weakest area: {recent['insights']['weakest_level']} (needs support)
- Trend: {recent['insights']['improvement_trend']}

LONG-TERM PROGRESS:
- Learning {', '.join(lifetime['language_progress'].keys())}
- Highest level: {max(lp['highest_level'] for lp in lifetime['language_progress'].values())}
- Strong areas: {', '.join([k for k, v in lifetime['challenge_type_mastery'].items() if v['mastery_level'] >= 4])}
- Total practice time: {lifetime['summary']['total_time_hours']} hours

LEARNING PATH:
- Current focus: {lifetime['learning_path']['current_focus']}
- Suggested next: {lifetime['learning_path']['suggested_next']}
- Areas needing work: {', '.join(lifetime['learning_path']['weak_areas'])}
"""

    return context
```

---

## 10. Testing Checklist

### 10.1 Unit Tests

- [ ] `update_daily_stats()` increments correctly
- [ ] `update_lifetime_stats()` updates all fields
- [ ] `get_recent_performance()` calculates averages correctly
- [ ] Timezone conversion works for all timezones
- [ ] Accuracy percentage calculations are correct
- [ ] Streak logic handles consecutive days
- [ ] Streak logic resets after missed day

### 10.2 Integration Tests

- [ ] Session completion updates all three stat layers
- [ ] Daily stats reset at midnight (user's timezone)
- [ ] Recent performance cache invalidates correctly
- [ ] Lifetime stats accumulate over time
- [ ] API endpoints return correct data structure
- [ ] Authentication/authorization works

### 10.3 Performance Tests

- [ ] Daily stats endpoint responds < 50ms
- [ ] Recent stats endpoint responds < 200ms
- [ ] Lifetime stats endpoint responds < 50ms
- [ ] Session completion completes < 500ms
- [ ] System handles 1000 concurrent requests
- [ ] Database indexes are used (check `explain()`)

### 10.4 Edge Cases

- [ ] User completes session at midnight (timezone boundary)
- [ ] User changes timezone mid-day
- [ ] User completes 0 challenges (all wrong or cancelled)
- [ ] New user with no data (empty stats)
- [ ] User in UTC+14 or UTC-12 (extreme timezones)
- [ ] Leap day (Feb 29)

---

## 11. Documentation & Handoff

### 11.1 API Documentation

Generate OpenAPI/Swagger docs:
```bash
python -m backend.generate_openapi_docs > docs/api/stats-api.yaml
```

### 11.2 Database Schema Documentation

Create ER diagrams showing:
- Collection relationships
- Index definitions
- Data flow diagrams

### 11.3 Mobile Integration Guide

**For Mobile App Team**:
1. Authentication required for all endpoints
2. Timezone handling: Always send user's current timezone
3. Caching recommendations: Cache daily stats for 5 minutes
4. Error handling: All endpoints return standard error format

---

## Appendix A: Sample Queries

### A.1 Get User's Daily Stats

```javascript
db.daily_stats.findOne({
  user_id: "user123",
  local_date: "2025-12-21"
})
```

### A.2 Calculate 7-Day Accuracy Trend

```javascript
db.challenge_sessions.aggregate([
  {
    $match: {
      user_id: "user123",
      created_at: {
        $gte: ISODate("2025-12-15T00:00:00Z")
      }
    }
  },
  {
    $group: {
      _id: "$local_date",
      total_correct: { $sum: "$correct_answers" },
      total_challenges: { $sum: "$total_challenges" }
    }
  },
  {
    $project: {
      date: "$_id",
      accuracy: {
        $multiply: [
          { $divide: ["$total_correct", "$total_challenges"] },
          100
        ]
      }
    }
  },
  { $sort: { date: 1 } }
])
```

### A.3 Find Weakest CEFR Level (Last 7 Days)

```javascript
db.challenge_sessions.aggregate([
  {
    $match: {
      user_id: "user123",
      created_at: {
        $gte: ISODate("2025-12-15T00:00:00Z")
      }
    }
  },
  {
    $group: {
      _id: "$level",
      total_correct: { $sum: "$correct_answers" },
      total_challenges: { $sum: "$total_challenges" }
    }
  },
  {
    $project: {
      level: "$_id",
      accuracy: {
        $multiply: [
          { $divide: ["$total_correct", "$total_challenges"] },
          100
        ]
      }
    }
  },
  { $sort: { accuracy: 1 } },
  { $limit: 1 }
])
```

---

## Appendix B: Glossary

- **Daily Stats**: Statistics for the current calendar day (user's timezone)
- **Recent Performance**: Rolling window statistics (typically 7 days)
- **Lifetime Progress**: Cumulative statistics since account creation
- **Local Date**: Calendar date in user's timezone (e.g., "2025-12-21")
- **Mastery**: Percentage of challenges completed for a type/level
- **Streak**: Consecutive days with at least one challenge completed
- **Accuracy**: Percentage of challenges answered correctly
- **XP**: Experience points (gamification currency)
- **Session**: A set of 10 challenges completed in one sitting

---

## Appendix C: Future Enhancements

**v2.0 Features** (Future Scope):
- Weekly/monthly reports (email digest)
- Social features (compare with friends)
- Leaderboards (global/language-specific)
- Personalized goals (AI-suggested)
- Advanced analytics dashboard (admin)
- Export data (CSV/PDF)
- Learning velocity metrics
- Predictive analytics (when will user reach C1?)
- Gamification levels/badges system
- Time-of-day performance analysis
- Difficulty adaptation recommendations

---

**End of Design Document**

**Next Steps**:
1. Review this design with team
2. Approve/modify architecture
3. Create JIRA tickets for Phase 1
4. Begin implementation

**Questions/Feedback**: Contact Backend Architecture Team

