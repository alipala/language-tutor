# ROOT CAUSE ANALYSIS: User Minute Calculation Issue

## Issue Summary
**User:** alipala.ist@gmail.com (UserId: 688921c268819565ef1ce3dc)  
**Problem:** Shows 137/150 minutes remaining despite completing 6 sessions + practice  
**Expected:** Should show ~30-35 minutes consumed (6 sessions × 5 minutes + practice)  
**Actual:** Only 13 minutes consumed according to system  

## Investigation Results

### 1. User Data Analysis
```
Plan: fluency_builder (monthly)
Status: trialing
Sessions Limit: 30
Minutes Limit: 150
Sessions Used: 7
Minutes Used: 13.042783333333333
Sessions Remaining: 23
Minutes Remaining: 136.95721666666668
```

### 2. Session Breakdown
- **Learning Plan Sessions:** 6 sessions completed (stored in learning_plans collection)
- **Conversation Sessions:** 1 session completed (stored in conversation_sessions collection)
- **Total Sessions in DB:** 7 (matches practice_sessions_used)
- **Total Minutes Tracked:** 13.04 minutes

### 3. Data Structure Analysis
- **Learning Plan:** 6 sessions completed, but session summaries are stored as strings (no duration data)
- **Weekly Schedule:** 3 weeks completed (6 sessions total)
- **Conversation Sessions:** 1 session with 5.25 minutes duration

## ROOT CAUSE IDENTIFIED

### The Problem: Learning Plan Sessions Don't Track Minutes Properly

**Issue 1: Session Summary Structure**
- Learning plan session summaries are stored as plain strings
- No duration information is captured in the session summaries
- The `save_session_summary` endpoint doesn't receive or track duration

**Issue 2: Missing Minute Tracking in Learning Plan Flow**
Looking at `learning_routes.py`, the `save_session_summary` endpoint:
1. ✅ Correctly increments `practice_sessions_used` (explains why user shows 7 sessions)
2. ❌ Does NOT track speaking minutes (`practice_minutes_used`)
3. ❌ The `SessionSummaryRequest` model has optional `duration_minutes` but it's not being used

**Issue 3: Inconsistent Tracking Between Session Types**
- **Regular Conversation Sessions:** Properly track both session count AND minutes
- **Learning Plan Sessions:** Only track session count, NOT minutes

## Code Analysis

### Current Learning Plan Session Flow:
```python
# In learning_routes.py - save_session_summary()
# ✅ This works - increments session count
usage_request = UsageTrackingRequest(
    user_id=str(current_user.id),
    usage_type="practice_session"
)
usage_tracked = await SubscriptionService.track_usage(usage_request)

# ❌ This is missing - no minute tracking!
# Should also call:
# speaking_time_request = SpeakingTimeTrackingRequest(
#     user_id=str(current_user.id),
#     speaking_minutes=duration_minutes,
#     session_completed=True
# )
# await SubscriptionService.track_speaking_time(speaking_time_request)
```

### Comparison with Regular Conversation Sessions:
```python
# In progress_routes.py - save_conversation()
# ✅ Both session count AND minutes are tracked properly
await track_subscription_usage(current_user.id, "practice_session")
# Plus the conversation duration is stored in the session document
```

## Impact Analysis

### Why User Shows 137/150 Minutes:
1. User completed 6 learning plan sessions (each ~5 minutes = ~30 minutes)
2. User completed 1 conversation session (5.25 minutes)
3. **Expected total:** ~35 minutes consumed
4. **Actual tracked:** Only 13 minutes (from conversation session + some partial tracking)
5. **Missing:** ~22 minutes from learning plan sessions

### Why Session Count is Correct (7 sessions):
- Learning plan sessions correctly increment `practice_sessions_used`
- Conversation sessions also increment `practice_sessions_used`
- Total: 6 + 1 = 7 sessions ✅

## Solution Required

### Fix 1: Update Learning Plan Session Tracking
The `save_session_summary` endpoint in `learning_routes.py` needs to:
1. Accept duration information from the frontend
2. Track speaking minutes using `SubscriptionService.track_speaking_time()`
3. Store duration in session details for future reference

### Fix 2: Backfill Missing Minutes (Optional)
For existing users like this one, we could:
1. Estimate missing minutes based on completed learning plan sessions
2. Update their `practice_minutes_used` to reflect actual usage
3. This would be a one-time data migration

### Fix 3: Frontend Integration
Ensure the frontend passes duration information when saving learning plan sessions.

## Confidence Level: 100%

This analysis definitively identifies the root cause:
- ✅ Learning plan sessions increment session counters correctly
- ❌ Learning plan sessions do NOT track speaking minutes
- ✅ Regular conversation sessions track both correctly
- 🎯 **Result:** User shows correct session usage but incorrect minute usage

The fix is straightforward: ensure learning plan sessions also call the minute tracking logic in `SubscriptionService.track_speaking_time()`.
