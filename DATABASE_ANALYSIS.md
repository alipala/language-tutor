# MongoDB Database Schema Analysis
## Based on Code Review (PR #169 Implementation)

---

## 📊 FINDINGS FROM CODE ANALYSIS

### 1. **Learning Plans Collection** (`learning_plans`)

**Confirmed Fields (from code):**
```python
{
    "id": "uuid",  #custom unique ID
    "user_id": "string",
    "language": "english" | "dutch" | etc,  # ✅ CONFIRMED - field exists!
    "proficiency_level": "A1" | "A2" | "B1" | "B2" | "C1" | "C2",
    "completed_sessions": "integer",
    "total_sessions": "integer",
    "duration_months": "integer",
    "plan_content": {
        "weekly_schedule": []
    },
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

**Evidence:**
- `learning_routes.py:1054`: `learning_plan.get('language', 'N/A')`
- `learning_routes.py:1274`: `language=learning_plan.get("language", "english")`
- `progress_routes.py:1292`: `update_learning_plan_progress(user_id, language, level, topic)`
- `share_routes.py:58`: `language = learning_plan.get("language", "English").title()`

### 2. **Challenge Pool Collection** (`challenge_pool`)

**Current Schema (from code):**
```python
{
    "_id": "ObjectId",
    "user_id": "string",
    "cefr_level": "B1" | "A2" etc,  # ✅ EXISTS
    "challenge_type": "error_spotting" | "swipe_fix" | etc,
    "challenge_data": {...},  # The actual challenge content
    "status": "available" | "completed",
    "created_at": "datetime",
    "completed_at": "datetime | null",
    "expires_at": "datetime"  # 30 days from creation
}
```

**CRITICAL FINDING:**
- ❌ **NO `language` field** in challenge pool!
- ❌ **NO `learning_plan_id` field**
- Current filtering only by: `user_id + cefr_level + challenge_type + status`

**Evidence:**
- `challenge_routes.py:509-514`: Filters by `user_id`, `challenge_type`, `cefr_level`, `status`
- `challenge_pool_helpers.py:217-222`: Counts only check `cefr_level`, not language
- `challenge_pool_replenisher.py:50-54`: No language filtering in replenishment

### 3. **Reference Challenges Collection** (`reference_challenges`)

**Schema (from code):**
```python
{
    "_id": "ObjectId",
    "cefr_level": "string",
    "challenge_type": "string",
    "challenge_data": {...}
}
```

**FINDING:**
- ❌ **NO `language` field** (assumes English only)
- Used for copying to new users' pools

### 4. **Users Collection** (`users`)

**Relevant Fields:**
```python
{
    "_id": "ObjectId",
    "preferred_language": "english" | "dutch" | null,  # Single language
    "preferred_level": "B1" | "A2" | etc,
    "challengeStats": {
        "totalCompleted": "integer",
        "currentStreak": "integer",
        "completedToday": ["challenge_id1", ...],
        "completionHistory": {}
    }
}
```

**Evidence:**
- `models.py:30`: `preferred_language: Optional[str] = None`
- `challenge_routes.py:176`: `user_level = current_user.preferred_level or "B1"`

### 5. **Conversation Sessions Collection** (`conversation_sessions`)

**Relevant Fields:**
```python
{
    "_id": "ObjectId",
    "user_id": "string",
    "language": "english" | "dutch",  # ✅ Has language field
    "level": "B1" | etc,
    "enhanced_analysis": {
        "insights": {
            "grammar_to_review": [],
            "vocabulary_to_learn": []
        }
    },
    "created_at": "datetime"
}
```

---

## 🔍 CURRENT SYSTEM BEHAVIOR

### Challenge Selection Flow (from `challenge_routes.py`)

```python
# 1. User requests daily challenges
GET /api/challenges/daily

# 2. Backend checks:
user_level = current_user.preferred_level or "B1"  # No language used!

# 3. Fetches from pool:
query = {
    "user_id": user_id,
    "challenge_type": type,
    "cefr_level": user_level,  # ONLY LEVEL, NO LANGUAGE!
    "status": "available"
}

# 4. Problem: If user has English B1 and Dutch A2 plans:
#    - Both challenges go to same pool
#    - No way to separate them
#    - User sees mixed English/Dutch challenges!
```

### Challenge Generation (from `challenge_generator_ai.py`)

```python
# 1. Analyzes user data
async def analyze_user_learning_data(user_id):
    # Gets: sessions, flashcards, learning plan
    # BUT: Doesn't filter by language!

# 2. Generates challenges
# - Uses user's preferred_level only
# - No language context in AI prompt
# - Generated challenges have no language tag
```

### Pool Replenishment (from `challenge_pool_replenisher.py`)

```python
# Daily cron job:
for user in active_users:
    user_level = user.get("preferred_level") or "B1"
    # Replenishes based on level only
    # No language consideration
```

---

## 🚨 IDENTIFIED PROBLEMS

### Problem 1: **No Language Separation**
```
User has:
- English B2 learning plan
- Dutch A1 learning plan

Current behavior:
challenge_pool:
  - user_id: "123"
    cefr_level: "B2"  # English challenge

  - user_id: "123"
    cefr_level: "A1"  # Dutch challenge

When user requests challenges at B2:
  → Gets English B2 challenges ✅

When user requests challenges at A1:
  → Gets Dutch A1 challenges ✅

BUT: What if user has English B2 AND English A1 plans?
  → System can't distinguish!
  → Mixes both levels for same language!
```

### Problem 2: **AI Generator Ignores Language**
- Analyzes ALL user sessions (English + Dutch mixed)
- Creates challenges without language context
- No way to generate language-specific weaknesses

### Problem 3: **No Learning Plan Integration**
- Challenges use `preferred_level` (user setting)
- Don't reference specific learning plan
- Can't personalize per plan

### Problem 4: **Single Preferred Language**
- User model: `preferred_language: Optional[str]`
- But users can have MULTIPLE active learning plans!
- System assumes one language at a time

---

## ✅ WHAT WE KNOW FOR SURE

1. ✅ **Learning plans HAVE `language` field** - extensively used in code
2. ✅ **Challenge pool does NOT have `language` field** - confirmed by code review
3. ✅ **Reference challenges do NOT have `language` field** - all English assumed
4. ✅ **Users have `preferred_language` (single)** - not array
5. ✅ **Conversation sessions HAVE `language` field**
6. ✅ **Cron job runs DAILY** - `challenge_pool_replenisher.py` (should be weekly)
7. ✅ **6 challenge types** used throughout system
8. ✅ **No language params in current API endpoints**

---

## 📝 RECOMMENDED SCHEMA CHANGES

### 1. **Update `challenge_pool` Collection**

```javascript
// ADD FIELDS:
{
    "language": "english" | "dutch" | "spanish" | etc,  // NEW!
    "learning_plan_id": "uuid | null",  // NEW! Optional link to plan

    // CHANGE INDEX:
    // OLD: {user_id: 1, cefr_level: 1, challenge_type: 1, status: 1}
    // NEW: {user_id: 1, language: 1, cefr_level: 1, challenge_type: 1, status: 1}
}
```

**Migration Strategy:**
```javascript
// For existing challenge_pool items without language:
db.challenge_pool.updateMany(
    { language: { $exists: false } },
    {
        $set: {
            language: "english",  // Default to English
            learning_plan_id: null
        }
    }
)

// Create new compound index
db.challenge_pool.createIndex({
    user_id: 1,
    language: 1,
    cefr_level: 1,
    challenge_type: 1,
    status: 1
})
```

### 2. **Update `reference_challenges` Collection**

```javascript
// ADD FIELD:
{
    "language": "english" | "dutch" | etc,  // NEW!
}

// Migration:
db.reference_challenges.updateMany(
    { language: { $exists: false } },
    { $set: { language: "english" } }
)
```

### 3. **Update `users` Collection**

```javascript
// CONSIDER CHANGING (optional):
{
    // OLD:
    "preferred_language": "string | null",

    // NEW (if we want multi-language support):
    "preferred_languages": ["english", "dutch"],  // Array
    "active_learning_plans": [  // Track active plans
        { "plan_id": "uuid", "language": "english", "level": "B2" },
        { "plan_id": "uuid", "language": "dutch", "level": "A1" }
    ]
}
```

---

## 🎯 API CHANGES NEEDED

### Current APIs
```
GET /api/challenges/daily
GET /api/challenges/counts
GET /api/challenges/by-type/{type}
```

### Proposed Changes
```
# Add language parameter:
GET /api/challenges/daily?language=english&plan_id=123
GET /api/challenges/counts?language=dutch
GET /api/challenges/by-type/error_spotting?language=english&level=B2

# New endpoint for user's learning languages:
GET /api/challenges/languages
Response:
{
    "languages": [
        {
            "language": "english",
            "level": "B2",
            "plan_id": "123",
            "available_challenges": 45
        },
        {
            "language": "dutch",
            "level": "A1",
            "plan_id": "456",
            "available_challenges": 38
        }
    ]
}
```

---

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Schema Updates (Backend)
- [ ] Add `language` field to challenge_pool
- [ ] Add `learning_plan_id` field to challenge_pool
- [ ] Add `language` field to reference_challenges
- [ ] Create migration script for existing data
- [ ] Update database indexes

### Phase 2: Code Updates
- [ ] `challenge_pool_helpers.py`: Add language filtering
- [ ] `challenge_generator_ai.py`: Language-aware analysis
- [ ] `challenge_routes.py`: Add language params to endpoints
- [ ] `challenge_pool_replenisher.py`: Per-language replenishment

### Phase 3: Learning Plan Integration
- [ ] Service to get active learning plans
- [ ] Link challenges to specific plans
- [ ] Plan-based challenge generation

### Phase 4: Weekly Cron + AI Agent
- [ ] Change cron from daily to weekly
- [ ] Implement CrewAI-based intelligent curation
- [ ] Challenge quality review system

### Phase 5: Client Integration
- [ ] iOS: Language selection in Explore tab
- [ ] iOS: Device caching for challenges
- [ ] iOS: Logout redirect to greeting

---

## 🎨 USER FLOW EXAMPLES

### Scenario 1: New User (No Learning Plans)
```
1. User signs up
2. User navigates to Explore tab
3. Sees: "Select your language and level"
   - Dropdown: English, Dutch, Spanish, etc.
   - Level: A1, A2, B1, B2, C1, C2
4. Selects: English, B1
5. Backend: Copies reference challenges (English, B1)
6. User sees 60 generic challenges immediately
```

### Scenario 2: User with 1 Learning Plan
```
1. User has: English B2 learning plan
2. Opens Explore tab
3. Backend automatically uses plan: English B2
4. Shows challenges from:
   - User's English B2 sessions (weaknesses)
   - English B2 flashcards (low mastery)
   - AI-generated English B2 challenges
5. No language selection needed (uses active plan)
```

### Scenario 3: User with Multiple Learning Plans
```
1. User has:
   - English B2 plan (active)
   - Dutch A1 plan (active)
2. Opens Explore tab
3. Sees language switcher: [English B2] [Dutch A1]
4. Selects English → Shows English B2 challenges
5. Selects Dutch → Shows Dutch A1 challenges
6. Challenges completely separated
```

---

## 🚀 READY TO IMPLEMENT

This analysis confirms:
1. ✅ Learning plans have language field
2. ❌ Challenge pool needs language field (MUST ADD)
3. ❌ Reference challenges need language field (MUST ADD)
4. ✅ Clear path forward for implementation

Next step: Implement Phase 1 (Schema Updates) with migration script.
