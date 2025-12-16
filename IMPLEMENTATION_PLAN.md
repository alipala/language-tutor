# APPROVED IMPLEMENTATION PLAN
## Challenge System Refactoring - DELETE & REGENERATE Approach

**Approved:** December 16, 2025
**Approach:** Delete existing challenges, regenerate with CrewAI
**Timeline:** 5-6 days
**Cost:** $8.80/month (vs $367/month currently = 97.6% savings)

---

## ✅ **APPROVED DECISIONS**

1. **DELETE** all 2,363 existing challenge_pool items (no migration)
2. **USE CrewAI** multi-agent flow with GPT-4o
3. **GENERATE** Dutch/Spanish reference challenges (new feature)
4. **NORMALIZE** all language casing to lowercase
5. **DEPLOY** to staging first, then production

---

## 📅 **PHASE 1: Database Cleanup & Setup** (Day 1)

### Step 1.1: Backup Current State
```bash
# Backup challenge_pool before deletion
mongoexport --uri="$MONGODB_URL" \
  --collection=challenge_pool \
  --out=backup_challenge_pool_20251216.json

# Backup reference_challenges
mongoexport --uri="$MONGODB_URL" \
  --collection=reference_challenges \
  --out=backup_reference_challenges_20251216.json
```

### Step 1.2: Delete Challenge Pool
```javascript
// Delete all challenge pool items
db.challenge_pool.deleteMany({})

// Result: 2,363 documents deleted
// Users will get fresh challenges from system
```

### Step 1.3: Add Language to Reference Challenges
```javascript
// Tag existing 600 as English
db.reference_challenges.updateMany(
    { language: { $exists: false } },
    { $set: { language: "english" } }
)

// Create index
db.reference_challenges.createIndex({
    language: 1,
    cefr_level: 1,
    challenge_type: 1
})
```

### Step 1.4: Normalize Language Casing
```javascript
// Learning plans
db.learning_plans.updateMany(
    { language: { $exists: true } },
    [{ $set: { language: { $toLower: "$language" } } }]
)

// Users
db.users.updateMany(
    { preferred_language: { $exists: true } },
    [{ $set: { preferred_language: { $toLower: "$preferred_language" } } }]
)

// Conversation sessions
db.conversation_sessions.updateMany(
    { language: { $exists: true } },
    [{ $set: { language: { $toLower: "$language" } } }]
)
```

### Step 1.5: Update Challenge Pool Schema
```javascript
// Create new compound index with language
db.challenge_pool.createIndex({
    user_id: 1,
    language: 1,
    cefr_level: 1,
    challenge_type: 1,
    status: 1
})

// Add validation schema
db.runCommand({
    collMod: "challenge_pool",
    validator: {
        $jsonSchema: {
            required: ["user_id", "language", "cefr_level", "challenge_type", "status"],
            properties: {
                language: {
                    bsonType: "string",
                    pattern: "^[a-z]+$",
                    description: "Language must be lowercase (e.g., 'english', 'dutch')"
                }
            }
        }
    }
})
```

**Deliverables:**
- ✅ Backups created
- ✅ Challenge pool cleaned (0 documents)
- ✅ Reference challenges have language field
- ✅ All languages normalized to lowercase
- ✅ New indexes created
- ✅ Schema validation added

---

## 🤖 **PHASE 2: CrewAI Multi-Agent System** (Day 2-3)

### Step 2.1: Install CrewAI
```bash
cd cron-service
pip install crewai crewai-tools
```

### Step 2.2: Create Multi-Agent System

**File:** `cron-service/challenge_crew_ai.py`

```python
"""
Challenge Generation with CrewAI Multi-Agent System
Uses 3 specialized agents for intelligent challenge curation
"""

from crewai import Agent, Crew, Task, Process
from crewai_tools import tool
import os
from openai import OpenAI
from typing import List, Dict, Any
from database import database
from datetime import datetime, timedelta

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==================== TOOLS ====================

@tool
def get_user_learning_data(user_id: str, language: str) -> Dict[str, Any]:
    """
    Retrieve user's learning data filtered by language

    Args:
        user_id: User ID
        language: Language to filter (e.g., 'english', 'dutch')

    Returns:
        Dict with sessions, flashcards, weaknesses
    """
    # Get sessions for this language
    sessions = list(database.conversation_sessions.find({
        "user_id": user_id,
        "language": language.lower()
    }).sort("created_at", -1).limit(10))

    # Get weak flashcards for this language
    weak_flashcards = list(database.flashcards.find({
        "user_id": user_id,
        "language": language.lower(),
        "mastery_level": {"$lt": 0.5}
    }).limit(10))

    # Get learning plan for this language
    learning_plan = database.learning_plans.find_one({
        "user_id": user_id,
        "language": language.lower()
    })

    return {
        "user_id": user_id,
        "language": language,
        "sessions_count": len(sessions),
        "weak_flashcards_count": len(weak_flashcards),
        "has_learning_plan": learning_plan is not None,
        "level": learning_plan.get("proficiency_level") if learning_plan else "B1"
    }


@tool
def get_existing_challenges(user_id: str, language: str) -> List[str]:
    """
    Get list of existing challenge IDs to avoid duplicates

    Args:
        user_id: User ID
        language: Language filter

    Returns:
        List of challenge IDs
    """
    existing = database.challenge_pool.find({
        "user_id": user_id,
        "language": language.lower(),
        "status": "available"
    })

    challenge_ids = []
    for item in existing:
        challenge_data = item.get("challenge_data", {})
        challenge_ids.append(challenge_data.get("id", ""))

    return challenge_ids


# ==================== AGENTS ====================

# Agent 1: Learning Analyzer
learning_analyzer = Agent(
    role="Learning Data Analyzer",
    goal="Analyze user's language learning patterns, weaknesses, and progress",
    backstory="""You are an expert language learning analyst with 15 years of experience.
    You excel at identifying patterns in learner data, spotting areas that need more practice,
    and understanding which grammar/vocabulary concepts are challenging for each student.
    You focus on data-driven insights to personalize learning experiences.""",
    tools=[get_user_learning_data, get_existing_challenges],
    verbose=True,
    llm="gpt-4o"
)

# Agent 2: Challenge Generator
challenge_generator = Agent(
    role="Challenge Creator",
    goal="Generate personalized, engaging language challenges based on user weaknesses",
    backstory="""You are a creative language teacher specializing in micro-learning exercises.
    You create bite-sized challenges that target specific weaknesses while keeping learners
    engaged. Your challenges are perfectly calibrated to the learner's CEFR level and
    focus on practical, real-world language usage. You ensure variety and progression.""",
    verbose=True,
    llm="gpt-4o"
)

# Agent 3: Quality Curator
quality_curator = Agent(
    role="Challenge Quality Curator",
    goal="Review generated challenges for quality, remove duplicates, ensure proper difficulty",
    backstory="""You are a meticulous quality assurance specialist for educational content.
    You ensure challenges are clear, engaging, properly leveled, and free from errors.
    You remove duplicates, verify that explanations are helpful, and ensure a good mix
    of challenge types. You're the final gatekeeper for challenge quality.""",
    verbose=True,
    llm="gpt-4o"
)


# ==================== CREW ====================

def generate_challenges_for_user(user_id: str, language: str, level: str) -> List[Dict[str, Any]]:
    """
    Use CrewAI to generate personalized challenges for a user

    Args:
        user_id: User ID
        language: Language (e.g., 'english', 'dutch')
        level: CEFR level (A1-C2)

    Returns:
        List of generated challenges
    """

    # Task 1: Analyze user data
    analyze_task = Task(
        description=f"""Analyze learning data for user {user_id} learning {language} at {level} level.
        Use the get_user_learning_data tool to retrieve their sessions, flashcards, and progress.
        Identify top 5 areas where they need practice (e.g., past tense, articles, vocabulary gaps).
        Output: JSON with weaknesses and recommendations.""",
        agent=learning_analyzer,
        expected_output="JSON object with user weaknesses and focus areas"
    )

    # Task 2: Generate challenges
    generate_task = Task(
        description=f"""Based on the analysis, generate 12 personalized challenges for {language} at {level} level.
        Create 2 challenges for each type: error_spotting, swipe_fix, micro_quiz, smart_flashcard, native_check, brain_tickler.
        Focus on the identified weaknesses. Ensure challenges are engaging and properly leveled.
        Output: JSON array of 12 challenges with proper structure.""",
        agent=challenge_generator,
        expected_output="JSON array of 12 challenge objects",
        context=[analyze_task]
    )

    # Task 3: Curate and validate
    curate_task = Task(
        description=f"""Review the generated challenges for quality and uniqueness.
        Use get_existing_challenges to check for duplicates.
        Remove any duplicates, verify difficulty matches {level}, ensure variety.
        Keep the best 12 challenges. Output: Final JSON array.""",
        agent=quality_curator,
        expected_output="Curated JSON array of 12 unique, high-quality challenges",
        context=[analyze_task, generate_task]
    )

    # Create crew
    crew = Crew(
        agents=[learning_analyzer, challenge_generator, quality_curator],
        tasks=[analyze_task, generate_task, curate_task],
        process=Process.sequential,
        verbose=True
    )

    # Execute
    result = crew.kickoff()

    # Parse result (CrewAI returns string, need to extract JSON)
    import json
    import re

    # Extract JSON from result
    result_str = str(result)
    json_match = re.search(r'\[.*\]', result_str, re.DOTALL)

    if json_match:
        challenges = json.loads(json_match.group())
        return challenges

    return []


# ==================== WEEKLY CRON JOB ====================

async def weekly_challenge_replenishment():
    """
    Weekly job: Replenish challenges using CrewAI
    """
    print("=" * 80)
    print("🤖 CREWAI WEEKLY CHALLENGE REPLENISHMENT")
    print(f"📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)

    # Get active users (activity in last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    active_sessions = database.conversation_sessions.find({
        "created_at": {"$gte": seven_days_ago}
    }).distinct("user_id")

    active_users = list(database.users.find({
        "_id": {"$in": active_sessions}
    }))

    print(f"👥 Found {len(active_users)} active users\n")

    total_generated = 0

    for idx, user in enumerate(active_users, 1):
        user_id = str(user["_id"])
        print(f"\n[{idx}/{len(active_users)}] Processing user: {user.get('email', 'Unknown')}")

        # Get user's learning plans
        learning_plans = list(database.learning_plans.find({
            "user_id": user_id
        }))

        if not learning_plans:
            print("   ⏭️  No learning plans, skipping")
            continue

        # Process each language separately
        for plan in learning_plans:
            language = plan.get("language", "english").lower()
            level = plan.get("proficiency_level", "B1")

            print(f"   🌍 Language: {language} ({level})")

            # Check current pool size
            current_count = database.challenge_pool.count_documents({
                "user_id": user_id,
                "language": language,
                "status": "available"
            })

            if current_count >= 30:
                print(f"      ✅ Pool sufficient ({current_count} challenges)")
                continue

            print(f"      🤖 Generating with CrewAI...")

            try:
                # Generate with CrewAI
                challenges = generate_challenges_for_user(user_id, language, level)

                if challenges:
                    # Insert into pool
                    pool_items = []
                    for challenge in challenges:
                        pool_items.append({
                            "user_id": user_id,
                            "language": language,
                            "cefr_level": level,
                            "challenge_type": challenge.get("type"),
                            "challenge_data": challenge,
                            "status": "available",
                            "created_at": datetime.utcnow(),
                            "completed_at": None,
                            "expires_at": datetime.utcnow() + timedelta(days=30)
                        })

                    if pool_items:
                        result = database.challenge_pool.insert_many(pool_items)
                        generated = len(result.inserted_ids)
                        total_generated += generated
                        print(f"      ✅ Generated {generated} challenges")
                else:
                    print(f"      ⚠️  No challenges generated")

            except Exception as e:
                print(f"      ❌ Error: {str(e)}")
                continue

    print(f"\n{'=' * 80}")
    print(f"🎉 WEEKLY REPLENISHMENT COMPLETE")
    print(f"📊 Total challenges generated: {total_generated}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(weekly_challenge_replenishment())
```

**Deliverables:**
- ✅ CrewAI installed
- ✅ 3 agents created (Analyzer, Generator, Curator)
- ✅ Tools for data retrieval
- ✅ Weekly cron job function
- ✅ Language-aware challenge generation

---

## 🔧 **PHASE 3: Backend Code Updates** (Day 3-4)

### Step 3.1: Update Challenge Pool Helpers

**File:** `backend/challenge_pool_helpers.py`

Add language parameter to all functions:

```python
async def copy_reference_to_pool(
    user_id: str,
    user_level: str,
    language: str,  # ← NEW!
    challenges_per_type: int = 10
) -> int:
    """Copy reference challenges filtered by language"""

    reference_collection = await get_reference_challenges_collection()
    pool_collection = await get_pool_collection()

    challenge_types = [...]

    for challenge_type in challenge_types:
        cursor = reference_collection.aggregate([
            {
                "$match": {
                    "language": language.lower(),  # ← Filter by language!
                    "cefr_level": user_level,
                    "challenge_type": challenge_type
                }
            },
            {"$sample": {"size": challenges_per_type}}
        ])

        # ... rest of code
```

### Step 3.2: Update Challenge Routes

**File:** `backend/challenge_routes.py`

Add language query parameter:

```python
@router.get("/daily")
async def get_daily_challenges(
    language: str = Query(None),  # ← NEW parameter
    current_user: UserResponse = Depends(get_current_user)
):
    """Get daily challenges filtered by language"""

    user_level = current_user.preferred_level or "B1"

    # Determine language
    if language:
        user_language = language.lower()
    else:
        # Infer from user's active learning plan
        plan = await database.learning_plans.find_one({
            "user_id": current_user.id
        })
        user_language = plan.get("language", "english").lower() if plan else "english"

    challenges = await get_or_generate_daily_challenges(
        user_id=current_user.id,
        user_level=user_level,
        language=user_language  # ← Pass language
    )

    # ... rest of code
```

Add new endpoint for user's languages:

```python
@router.get("/languages")
async def get_user_languages(current_user: UserResponse = Depends(get_current_user)):
    """Get list of languages user is learning with challenge counts"""

    user_id = current_user.id

    # Get user's learning plans
    plans = await database.learning_plans.find({
        "user_id": user_id
    }).to_list(length=10)

    languages = []
    for plan in plans:
        language = plan.get("language", "").lower()
        level = plan.get("proficiency_level", "B1")
        plan_id = plan.get("id")

        # Count available challenges
        count = await database.challenge_pool.count_documents({
            "user_id": user_id,
            "language": language,
            "status": "available"
        })

        languages.append({
            "language": language,
            "level": level,
            "plan_id": plan_id,
            "available_challenges": count
        })

    return {"languages": languages}
```

### Step 3.3: Update AI Generator

**File:** `backend/challenge_generator_ai.py`

Add language filtering:

```python
async def analyze_user_learning_data(user_id: str, language: str) -> Dict[str, Any]:
    """Analyze user data filtered by language"""

    # Filter sessions by language
    recent_sessions = await database.conversation_sessions.find({
        "user_id": user_id,
        "language": language.lower(),  # ← Filter!
        "enhanced_analysis": {"$exists": True}
    }).sort("created_at", -1).limit(10).to_list(length=10)

    # Filter flashcards by language
    weak_cards = await database.flashcards.find({
        "user_id": user_id,
        "language": language.lower(),  # ← Filter!
        "mastery_level": {"$lt": 0.5},
        "is_active": True
    }).limit(10).to_list(length=10)

    # Get learning plan for this language
    learning_plan = await database.learning_plans.find_one({
        "user_id": user_id,
        "language": language.lower()  # ← Filter!
    })

    # ... rest of analysis
```

**Deliverables:**
- ✅ All helper functions language-aware
- ✅ Challenge routes accept language parameter
- ✅ New /api/challenges/languages endpoint
- ✅ AI generator filters by language

---

## 🧪 **PHASE 4: Testing** (Day 4-5)

### Test Cases:

1. **New User Without Learning Plan**
   - Creates account
   - No challenges initially
   - Selects language/level from Explore tab
   - System copies reference challenges instantly

2. **User with English B2 Plan**
   - Has English B2 learning plan
   - Fetches challenges: GET /api/challenges/daily?language=english
   - Receives ONLY English challenges
   - Verifies no Dutch challenges mixed in

3. **User with Multiple Plans (English B2 + Dutch A1)**
   - GET /api/challenges/languages → Shows both
   - GET /api/challenges/daily?language=english → English only
   - GET /api/challenges/daily?language=dutch → Dutch only
   - Verifies complete separation

4. **Language Casing**
   - Queries with "English", "english", "ENGLISH" all work
   - Database stores as lowercase
   - No filtering errors

5. **CrewAI Weekly Cron**
   - Manually trigger cron
   - Verifies 3 agents execute
   - Checks challenges generated
   - Confirms cost tracking

**Deliverables:**
- ✅ All test cases pass
- ✅ English/Dutch separation confirmed
- ✅ Language normalization works
- ✅ CrewAI generates quality challenges

---

## 📅 **PHASE 5: Cron Schedule Update** (Day 5)

### Update Railway Cron:

**File:** `cron-service/railway.json` (or Railway dashboard)

```json
{
  "cron": {
    "schedule": "0 2 * * 0",  // Weekly on Sunday at 2 AM UTC
    "command": "python challenge_crew_ai.py"
  }
}
```

Or via Railway CLI:
```bash
railway cron add \
  --schedule "0 2 * * 0" \
  --command "python challenge_crew_ai.py"
```

**Deliverables:**
- ✅ Cron changed from daily to weekly
- ✅ Uses CrewAI multi-agent system
- ✅ Runs Sunday 2 AM UTC

---

## 📝 **PHASE 6: Documentation** (Day 6)

Create iOS integration guide for the other agent:

**File:** `IOS_INTEGRATION_GUIDE.md`

```markdown
# iOS Integration Guide - Challenge System

## Backend Changes Summary

### New API Endpoints

1. **Get User's Languages**
   ```
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

2. **Get Daily Challenges (Updated)**
   ```
   GET /api/challenges/daily?language=english

   Response: Same structure, but filtered by language
   ```

3. **Get Challenge Counts (Updated)**
   ```
   GET /api/challenges/counts?language=dutch

   Response: Counts per type for specified language
   ```

## iOS Changes Needed

### 1. Logout Redirect
- **Change:** Redirect to greeting screen instead of login
- **File:** (iOS navigation logic)
- **Implementation:** Update navigation flow after logout

### 2. Explore Tab Language Selection
- **Change:** Add language dropdown for users without learning plans
- **UI:** Dropdown showing [English, Dutch, Spanish, etc.]
- **Behavior:**
  - If user has learning plan → auto-select plan's language
  - If user has multiple plans → show switcher
  - If user has no plans → show language selection

### 3. Challenge Caching
- **Implementation:** Store challenges locally in UserDefaults/AsyncStorage
- **Strategy:**
  ```swift
  // Pseudo-code
  func fetchChallenges(language: String) {
      // 1. Load from cache (instant)
      let cached = loadFromCache(language: language)
      displayChallenges(cached)

      // 2. Fetch fresh in background
      API.getChallenges(language: language) { fresh in
          updateCache(fresh, language: language)
          displayChallenges(fresh)
      }
  }
  ```

## Testing Checklist for iOS

- [ ] User without plan can select language
- [ ] User with 1 plan auto-loads that language
- [ ] User with 2+ plans can switch between languages
- [ ] Challenges cached locally for fast loading
- [ ] Logout redirects to greeting screen
- [ ] Language selection persists across sessions
```

**Deliverables:**
- ✅ iOS integration guide created
- ✅ API documentation updated
- ✅ Migration runbook documented
- ✅ Rollback procedures documented

---

## 💰 **COST ANALYSIS**

### Current System (Daily Cron):
- **Frequency:** Daily (30 runs/month)
- **Active users:** 68
- **Cost per user:** ~$0.18/day
- **Monthly total:** **$367/month**

### New System (CrewAI Weekly):
- **Frequency:** Weekly (4 runs/month)
- **Active users:** 20 (realistic)
- **Cost per user:** ~$0.11/week
- **Monthly total:** **$8.80/month**

### **Savings: $358/month (97.6%)** 🎉

### Initial Regeneration Cost:
- **One-time:** $0 - $1.65
- **Or spread over 3 weeks:** $0.55/week

---

## 🎯 **SUCCESS METRICS**

### Technical Success:
- [ ] 0 documents in challenge_pool after deletion
- [ ] All reference_challenges have language field
- [ ] All languages normalized to lowercase
- [ ] English and Dutch challenges completely separated
- [ ] CrewAI generates 12 challenges per user per week
- [ ] API responds with language-filtered challenges

### Business Success:
- [ ] Cost reduced to < $10/month
- [ ] User experience improved (no mixed challenges)
- [ ] Challenge quality improved (personalized per language)
- [ ] System scales to 100+ users easily

---

## ⚠️ **RISKS & MITIGATION**

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Users have no challenges briefly | HIGH | LOW | Regenerates in 30s, acceptable |
| CrewAI slower than expected | MEDIUM | LOW | Fallback to simple GPT-4o call |
| API costs spike | LOW | MEDIUM | Monitor first week, adjust |
| Dutch reference challenges missing | HIGH | MEDIUM | Generate separately (Phase 1) |

---

## 📋 **ROLLBACK PLAN**

If issues occur:

1. **Restore challenge_pool from backup:**
   ```bash
   mongoimport --uri="$MONGODB_URL" \
     --collection=challenge_pool \
     --file=backup_challenge_pool_20251216.json
   ```

2. **Revert code changes:**
   ```bash
   git revert HEAD~5
   git push
   ```

3. **Switch cron back to daily:**
   ```bash
   railway cron update --schedule "0 2 * * *"
   ```

---

## ✅ **READY TO START**

**Timeline:** 5-6 days
**Cost:** $8.80/month (vs $367/month)
**Approach:** DELETE + CrewAI multi-agent
**Risk:** Low

**Next Step:** Begin Phase 1 - Database cleanup
