# Phase 3.1 Testing Guide

## Test User Credentials

**Email:** `d77240fe-5821-486a-a6cc-d61396fffa58@mailslurp.biz`
**Password:** `040050803`

**User Profile:**
- Registered user
- **NO learning plan** (perfect for testing flexible selection!)
- Can test all 3 scenarios:
  1. Explicit language/level selection
  2. Fallback behavior
  3. Auto-population from reference challenges

---

## Prerequisites

1. **Backend must be running:**
   ```bash
   cd /home/user/language-tutor/backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **MongoDB must be running** with Phase 1.5 reference challenges loaded

3. **Check base URL:** Default is `http://localhost:8000` (change in scripts if different)

---

## Option 1: Python Test Script (Recommended)

### Requirements
- Python 3.8+
- `requests` library

### Install Dependencies
```bash
pip install requests
```

### Run Tests
```bash
cd /home/user/language-tutor
./test_phase3.1.py
```

### What It Tests
- ✅ Authentication (login with test user)
- ✅ `/api/challenges/counts` with multiple language/level combinations
- ✅ `/api/challenges/daily` with explicit params and fallback
- ✅ `/api/challenges/by-type/{type}` with different languages
- ✅ `/api/challenges/languages` endpoint
- ✅ Smart resolution priority logic
- ✅ Invalid parameter handling

### Sample Output
```
================================================================================
  PHASE 3.1 TEST SUITE - Flexible Language/Level Selection
  Testing with: User WITHOUT learning plan
================================================================================

================================================================================
1. AUTHENTICATION TEST
================================================================================

ℹ️  Logging in with: d77240fe-5821-486a-a6cc-d61396fffa58@mailslurp.biz
✅ Login successful!
ℹ️  User ID: 123456789
ℹ️  Preferred Level: B1

================================================================================
2. CHALLENGE COUNTS ENDPOINT TESTS
================================================================================

Test 1/4: Spanish A1 (explicit params)
ℹ️  Should show counts for Spanish A1
✅ Status: 200
ℹ️  Total challenges: 300
  error_spotting: 50
  swipe_fix: 50
  micro_quiz: 50
  smart_flashcard: 50
  native_check: 50
  brain_tickler: 50
✅ Challenges available!
```

---

## Option 2: Curl Test Script (Lightweight)

### Requirements
- `curl` (pre-installed on most systems)
- `python3` (for JSON formatting)

### Run Tests
```bash
cd /home/user/language-tutor
./test_phase3.1_curl.sh
```

### What It Tests
- ✅ Authentication
- ✅ `/api/challenges/counts` with Spanish A1, German B2, and fallback
- ✅ `/api/challenges/daily` with Spanish A1 and Dutch B1
- ✅ `/api/challenges/by-type/error_spotting` with Spanish A1
- ✅ `/api/challenges/by-type/swipe_fix` with German A2
- ✅ `/api/challenges/languages` with A1 level and fallback

### Sample Commands
```bash
# Test Spanish A1 challenges
curl -X GET "http://localhost:8000/api/challenges/counts?language=spanish&level=A1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | python3 -m json.tool

# Test daily challenges
curl -X GET "http://localhost:8000/api/challenges/daily?language=german&level=A2" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | python3 -m json.tool
```

---

## Option 3: Manual Testing (Individual Endpoints)

### Step 1: Get Auth Token
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"d77240fe-5821-486a-a6cc-d61396fffa58@mailslurp.biz","password":"040050803"}'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "123456789",
    "preferred_level": "B1"
  }
}
```

Copy the `access_token` value.

---

### Step 2: Test Challenge Counts

**Test 1: Spanish A1 (explicit params)**
```bash
curl -X GET "http://localhost:8000/api/challenges/counts?language=spanish&level=A1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | python3 -m json.tool
```

**Expected Response:**
```json
{
  "error_spotting": 50,
  "swipe_fix": 50,
  "micro_quiz": 50,
  "smart_flashcard": 50,
  "native_check": 50,
  "brain_tickler": 50
}
```

**Test 2: German B2 (explicit params)**
```bash
curl -X GET "http://localhost:8000/api/challenges/counts?language=german&level=B2" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | python3 -m json.tool
```

**Test 3: No params (fallback to english/B1)**
```bash
curl -X GET "http://localhost:8000/api/challenges/counts" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | python3 -m json.tool
```

---

### Step 3: Test Daily Challenges

**Test 1: French A1**
```bash
curl -X GET "http://localhost:8000/api/challenges/daily?language=french&level=A1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | python3 -m json.tool
```

**Expected Response:**
```json
{
  "challenges": [
    {
      "id": "challenge_id_1",
      "type": "error_spotting",
      "language": "french",
      "cefrLevel": "A1",
      "title": "Spot the Mistake",
      "completed": false
    },
    // ... 5 more challenges
  ],
  "total_completed_today": 0,
  "streak": 0,
  "last_updated": "2025-12-16T12:00:00"
}
```

**Test 2: No params (fallback)**
```bash
curl -X GET "http://localhost:8000/api/challenges/daily" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | python3 -m json.tool
```

---

### Step 4: Test By-Type Endpoint

**Test 1: Spanish A1 error_spotting**
```bash
curl -X GET "http://localhost:8000/api/challenges/by-type/error_spotting?language=spanish&level=A1&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | python3 -m json.tool
```

**Expected Response:**
```json
{
  "challenges": [
    {
      "id": "challenge_1",
      "type": "error_spotting",
      "language": "spanish",
      "cefrLevel": "A1",
      "sentence": "Yo va al mercado.",
      "options": [...]
    },
    // ... more challenges
  ],
  "total": 5,
  "type": "error_spotting"
}
```

**Test 2: German A2 swipe_fix**
```bash
curl -X GET "http://localhost:8000/api/challenges/by-type/swipe_fix?language=german&level=A2&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | python3 -m json.tool
```

---

### Step 5: Test Languages Endpoint

**Test 1: All languages for A1**
```bash
curl -X GET "http://localhost:8000/api/challenges/languages?level=A1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | python3 -m json.tool
```

**Expected Response:**
```json
{
  "success": true,
  "active_language": null,
  "languages": [
    {
      "language": "english",
      "has_learning_plan": false,
      "is_active": false,
      "available_challenges": 0
    },
    {
      "language": "spanish",
      "has_learning_plan": false,
      "is_active": false,
      "available_challenges": 300
    },
    // ... other languages
  ]
}
```

**Test 2: No params (user's level)**
```bash
curl -X GET "http://localhost:8000/api/challenges/languages" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | python3 -m json.tool
```

---

## Expected Behavior for User WITHOUT Learning Plan

### Initial State
- User has **NO** learning plan
- User has **NO** challenges in their pool
- `active_language` should be `null`
- `available_challenges` should be `0` for all languages

### After First Request
When user requests challenges (e.g., Spanish A1):
1. **Backend detects empty pool** for Spanish A1
2. **Auto-copies reference challenges** from `challenge_reference` collection
3. **Returns challenges immediately** (no manual setup needed!)
4. **User now has 300 Spanish A1 challenges** in their pool

### Subsequent Requests
- User can switch to ANY language/level anytime
- Backend auto-populates on first request
- Each language/level combination is independent

### Example Flow
```bash
# First request: Spanish A1
curl -X GET ".../counts?language=spanish&level=A1" → Returns 0 → Auto-copies → Returns 300

# Second request: German B2
curl -X GET ".../counts?language=german&level=B2" → Returns 0 → Auto-copies → Returns 300

# Third request: Spanish A1 (already populated)
curl -X GET ".../counts?language=spanish&level=A1" → Returns 300 (from pool)
```

---

## Validation Tests

### Test Invalid Language
```bash
curl -X GET "http://localhost:8000/api/challenges/counts?language=klingon&level=A1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected:** Backend falls back to `english/A1`

### Test Invalid Level
```bash
curl -X GET "http://localhost:8000/api/challenges/counts?language=spanish&level=Z9" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected:** Backend falls back to `spanish/B1`

### Test Mixed Valid/Invalid
```bash
curl -X GET "http://localhost:8000/api/challenges/counts?language=spanish&level=INVALID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected:** Backend uses `spanish/B1` (valid language, fallback level)

---

## Troubleshooting

### "401 Unauthorized"
- **Cause:** Invalid or expired token
- **Fix:** Re-login to get a fresh token

### "Connection refused"
- **Cause:** Backend not running
- **Fix:** Start backend: `cd backend && uvicorn main:app --reload`

### "0 challenges returned"
- **Cause:** First time requesting this language/level
- **Fix:** Wait 1-2 seconds, backend is auto-copying reference challenges. Request again.

### "ModuleNotFoundError: No module named 'requests'"
- **Cause:** Python requests library not installed
- **Fix:** `pip install requests`

---

## Success Criteria

Phase 3.1 is working correctly if:

✅ User can request **ANY** language/level combination
✅ Backend auto-populates from reference challenges on first request
✅ Explicit params **override** learning plan defaults
✅ No params **fall back** to learning plan or defaults
✅ Invalid params are **validated** and default to safe values
✅ `/languages` endpoint shows all 6 languages
✅ User can switch between languages freely

---

## Quick Test Commands

### Fastest Test (Python)
```bash
./test_phase3.1.py
```

### Fastest Test (Curl)
```bash
./test_phase3.1_curl.sh
```

### Single Endpoint Test
```bash
# Get token first
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"d77240fe-5821-486a-a6cc-d61396fffa58@mailslurp.biz","password":"040050803"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Test Spanish A1
curl -X GET "http://localhost:8000/api/challenges/counts?language=spanish&level=A1" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

---

## Next Steps After Testing

If all tests pass:
1. ✅ Phase 3.1 is complete!
2. 🚀 Ready for iOS integration
3. 📱 iOS can implement language/level pickers
4. 🎉 Users can explore any language without barriers!

Good luck! 🚀
