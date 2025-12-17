# Phase 3: Backend Language-Aware Updates - Implementation Plan

**Status:** Ready to implement
**Estimated time:** 20-30 minutes
**Files to update:** 3 files

---

## 📋 **Overview**

Add language filtering to backend API so challenges are separated by language. Currently, the system only filters by CEFR level - it doesn't consider which language the user is learning.

---

## 🎯 **Changes Required**

### **File 1: `/backend/challenge_pool_helpers.py`**

#### **Change 1.1: Update `copy_reference_to_pool()` function**

**Location:** Line 28-102

**Current signature:**
```python
async def copy_reference_to_pool(
    user_id: str,
    user_level: str,
    challenges_per_type: int = 10
) -> int:
```

**New signature:**
```python
async def copy_reference_to_pool(
    user_id: str,
    user_level: str,
    language: str = "english",  # ADD THIS
    challenges_per_type: int = 10
) -> int:
```

**Query update (Line 64-69):**
```python
# OLD:
"$match": {
    "cefr_level": user_level,
    "challenge_type": challenge_type
}

# NEW:
"$match": {
    "cefr_level": user_level,
    "challenge_type": challenge_type,
    "language": language  # ADD THIS LINE
}
```

**Pool item update (Line 78-87):**
```python
# ADD this field to pool_item dictionary:
pool_item = {
    "user_id": user_id,
    "language": language,  # ADD THIS LINE
    "cefr_level": user_level,
    "challenge_type": challenge_type,
    # ... rest of fields
}
```

---

#### **Change 1.2: Update `generate_personalized_challenges()` function**

**Location:** Line 104-175

**Current signature:**
```python
async def generate_personalized_challenges(
    user_id: str,
    user_level: str,
    challenges_needed: int
) -> int:
```

**New signature:**
```python
async def generate_personalized_challenges(
    user_id: str,
    user_level: str,
    language: str = "english",  # ADD THIS
    challenges_needed: int
) -> int:
```

**AI generation call update (Line 140):**
```python
# OLD:
batch = await generate_challenges_with_ai(user_id, user_level)

# NEW:
batch = await generate_challenges_with_ai(user_id, user_level, language)
```

**Pool item update (Line 150-162):**
```python
# ADD language field when creating pool items:
pool_item = {
    "user_id": user_id,
    "language": language,  # ADD THIS LINE
    "cefr_level": user_level,
    # ... rest of fields
}
```

---

#### **Change 1.3: Update `ensure_pool_has_challenges()` function**

**Location:** Line 176-283

**Current signature:**
```python
async def ensure_pool_has_challenges(
    user_id: str,
    user_level: str
) -> Dict[str, Any]:
```

**New signature:**
```python
async def ensure_pool_has_challenges(
    user_id: str,
    user_level: str,
    language: str = "english"  # ADD THIS
) -> Dict[str, Any]:
```

**Query updates (multiple locations in this function):**

Find this query pattern (appears ~3 times):
```python
# OLD:
{
    "user_id": user_id,
    "cefr_level": user_level,
    "challenge_type": challenge_type,
    # other filters
}

# NEW:
{
    "user_id": user_id,
    "language": language,  # ADD THIS LINE
    "cefr_level": user_level,
    "challenge_type": challenge_type,
    # other filters
}
```

**Function call updates:**
```python
# When calling copy_reference_to_pool (around line 230):
# OLD:
copied = await copy_reference_to_pool(user_id, user_level, per_type)

# NEW:
copied = await copy_reference_to_pool(user_id, user_level, language, per_type)

# When calling generate_personalized_challenges (around line 260):
# OLD:
generated = await generate_personalized_challenges(user_id, user_level, total_needed)

# NEW:
generated = await generate_personalized_challenges(user_id, user_level, language, total_needed)
```

---

### **File 2: `/backend/challenge_routes.py`**

#### **Change 2.1: Add helper function to get user's language**

**Location:** After line 40, add new function:

```python
async def get_user_active_language(user_id: str) -> str:
    """
    Get user's active learning plan language

    Returns:
        Language code (default: "english")
    """
    try:
        learning_plans_collection = database.learning_plans
        active_plan = await learning_plans_collection.find_one({
            "user_id": user_id,
            "is_active": True
        })

        if active_plan:
            language = active_plan.get("language", "english")
            # Ensure lowercase for consistency
            return language.lower()

        # Fallback: get most recent plan
        recent_plan = await learning_plans_collection.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )

        if recent_plan:
            return recent_plan.get("language", "english").lower()

        return "english"

    except Exception as e:
        print(f"[CHALLENGES] Error getting user language: {str(e)}")
        return "english"
```

---

#### **Change 2.2: Update `select_personalized_challenges()` function**

**Location:** Line 93-161

**Current signature:**
```python
async def select_personalized_challenges(
    user_level: str,
    weakness_tags: List[str],
    exclude_ids: List[str] = []
) -> List[Dict[str, Any]]:
```

**New signature:**
```python
async def select_personalized_challenges(
    user_level: str,
    language: str,  # ADD THIS
    weakness_tags: List[str],
    exclude_ids: List[str] = []
) -> List[Dict[str, Any]]:
```

**Query update (Line 124-128):**
```python
# OLD:
query = {
    "type": challenge_type,
    "cefrLevel": user_level,
    "id": {"$nin": exclude_ids}
}

# NEW:
query = {
    "type": challenge_type,
    "language": language,  # ADD THIS LINE
    "cefrLevel": user_level,
    "id": {"$nin": exclude_ids}
}
```

---

#### **Change 2.3: Update `/daily` endpoint**

**Location:** Line 163-244

**In the `get_daily_challenges()` function, around line 176:**

```python
# ADD this line after line 176:
user_id = current_user.id
user_level = current_user.preferred_level or "B1"
user_language = await get_user_active_language(user_id)  # ADD THIS LINE
```

**Update function call (around line 220):**
```python
# OLD:
weakness_tags = await get_user_weakness_tags(user_id)
challenges = await select_personalized_challenges(
    user_level,
    weakness_tags,
    completed_today
)

# NEW:
weakness_tags = await get_user_weakness_tags(user_id)
challenges = await select_personalized_challenges(
    user_level,
    user_language,  # ADD THIS
    weakness_tags,
    completed_today
)
```

---

#### **Change 2.4: Add new `/languages` endpoint**

**Location:** After line 475, add new endpoint:

```python
@router.get("/languages")
async def get_available_languages(current_user: UserResponse = Depends(get_current_user)):
    """
    Get list of languages available for challenges

    Returns list of language codes with display names
    """
    try:
        # Define supported languages
        languages = [
            {"code": "english", "name": "English", "native": "English"},
            {"code": "dutch", "name": "Dutch", "native": "Nederlands"},
            {"code": "spanish", "name": "Spanish", "native": "Español"},
            {"code": "german", "name": "German", "native": "Deutsch"},
            {"code": "french", "name": "French", "native": "Français"},
            {"code": "portuguese", "name": "Portuguese", "native": "Português"}
        ]

        # Check which languages the user has learning plans for
        user_plans = await database.learning_plans.find({
            "user_id": current_user.id
        }).to_list(length=10)

        user_languages = [plan.get("language", "").lower() for plan in user_plans]

        # Mark user's languages
        for lang in languages:
            lang["is_learning"] = lang["code"] in user_languages
            lang["is_active"] = False

        # Mark active language
        active_plan = await database.learning_plans.find_one({
            "user_id": current_user.id,
            "is_active": True
        })

        if active_plan:
            active_language = active_plan.get("language", "").lower()
            for lang in languages:
                if lang["code"] == active_language:
                    lang["is_active"] = True

        return {
            "languages": languages,
            "user_id": current_user.id
        }

    except Exception as e:
        print(f"[CHALLENGES] Error getting languages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

#### **Change 2.5: Update `/counts` endpoint**

**Location:** Line 437-472

**Around line 450, update query:**
```python
# ADD language to the query:
user_language = await get_user_active_language(current_user.id)

# Update the count queries to include language filter
pool_count = await pool_collection.count_documents({
    "user_id": current_user.id,
    "language": user_language,  # ADD THIS
    "status": "available",
    "expires_at": {"$gt": datetime.utcnow()}
})
```

---

#### **Change 2.6: Update `/by-type/{challenge_type}` endpoint**

**Location:** Line 473-541

**Around line 485, add language:**
```python
user_language = await get_user_active_language(current_user.id)

# Update query at line ~495:
pool_challenges = await pool_collection.find({
    "user_id": current_user.id,
    "language": user_language,  # ADD THIS
    "challenge_type": challenge_type,
    # ... rest of query
}).to_list(length=50)
```

---

### **File 3: `/backend/challenge_generator_ai.py`**

#### **Change 3.1: Update `generate_challenges_with_ai()` function signature**

**Location:** Find the function definition (likely around line 50-100)

**Current signature:**
```python
async def generate_challenges_with_ai(
    user_id: str,
    user_level: str
) -> List[Dict[str, Any]]:
```

**New signature:**
```python
async def generate_challenges_with_ai(
    user_id: str,
    user_level: str,
    language: str = "english"  # ADD THIS
) -> List[Dict[str, Any]]:
```

---

#### **Change 3.2: Filter sessions by language**

**Location:** In the session analysis part of the function

**Find the query that gets conversation sessions (likely around line 60-90):**

```python
# OLD:
recent_sessions = await sessions_collection.find({
    "user_id": user_id
}).sort("created_at", -1).limit(5).to_list(length=5)

# NEW:
recent_sessions = await sessions_collection.find({
    "user_id": user_id,
    "language": language  # ADD THIS LINE
}).sort("created_at", -1).limit(5).to_list(length=5)
```

---

#### **Change 3.3: Include language in AI prompt**

**Location:** Where the AI prompt is constructed

**Add language context to the prompt:**

```python
# In the prompt construction (find the f-string that creates the prompt):
# Add this line to the prompt:
f"Target Language: {language.title()}\n"
f"Generate native {language} content (not translations from English)\n"
```

---

## 🧪 **Testing After Implementation**

### **Test 1: Verify language filtering works**

```bash
# Query database to check challenges are filtered by language
mongosh "YOUR_MONGODB_URL" --eval "
  db.challenge_pool.find({
    user_id: 'USER_ID',
    language: 'spanish'
  }).count()
"
```

### **Test 2: Test new `/languages` endpoint**

```bash
curl -X GET http://localhost:8000/api/challenges/languages \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected response:
```json
{
  "languages": [
    {"code": "english", "name": "English", "is_learning": true, "is_active": false},
    {"code": "spanish", "name": "Spanish", "is_learning": true, "is_active": true},
    ...
  ]
}
```

### **Test 3: Verify daily challenges use correct language**

```bash
curl -X GET http://localhost:8000/api/challenges/daily \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Check that all challenges returned match the user's active learning plan language.

---

## ✅ **Implementation Checklist**

- [ ] Update `challenge_pool_helpers.py` (3 functions)
- [ ] Update `challenge_routes.py` (5 changes + 1 new endpoint)
- [ ] Update `challenge_generator_ai.py` (3 changes)
- [ ] Test locally
- [ ] Commit changes
- [ ] Push to branch
- [ ] Test on Railway

---

## 📝 **Commit Message Template**

```
Add Phase 3: Language-aware challenge filtering

Implement language filtering across backend challenge system to properly
separate challenges by language (English, Spanish, Dutch, German, French, Portuguese).

Changes:
- challenge_pool_helpers.py: Add language parameter to all functions
- challenge_routes.py: Get user's active language from learning plan
- challenge_routes.py: Add new /api/challenges/languages endpoint
- challenge_generator_ai.py: Filter sessions by language, native content

All challenge queries now filter by:
1. User ID
2. Language (from active learning plan)
3. CEFR level
4. Challenge type

Fixes issue where English/Dutch/Spanish challenges were mixing.

Related to Phase 1 (database migration) and Phase 2 (CrewAI setup).
```

---

## 🎯 **Next Steps After Phase 3**

Once Phase 3 is implemented:

1. **Phase 4:** Test multi-language separation
2. **Phase 5:** Deploy to Railway (update cron schedule)
3. **Phase 6:** iOS integration guide

---

**Implementation ready!** All changes are documented with exact line numbers and code snippets.
