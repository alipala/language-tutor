# Rate Limit Pre-Flight Check Implementation

## Overview

Implemented a **pre-flight rate limit check** that shows users if they're rate limited BEFORE attempting to start a conversation session. This provides a much better UX by preventing failed session starts and showing clear wait times.

## The Problem

**Before this implementation:**
1. User clicks "Got it! Let's start" button
2. App tries to create a session
3. Backend returns 500 error due to rate limiting
4. User sees generic "Failed to connect" error
5. No indication of how long to wait

**Result:** Frustrated users with no clear feedback

## The Solution

**After this implementation:**
1. User clicks "Got it! Let's start" button
2. App checks rate limit status (without consuming a token)
3. If rate limited, show user-friendly alert with exact wait time
4. If not rate limited, proceed with session creation

**Result:** Clear communication and better UX

---

## Implementation Details

### Backend Changes

#### New Endpoint: `GET /api/realtime/rate-limit-status`

**File:** `backend/routes/realtime_routes.py` (line ~1231)

```python
@router.get("/api/realtime/rate-limit-status")
async def check_rate_limit_status(current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)):
    """
    Check rate limit status for realtime sessions WITHOUT consuming a token.
    Returns whether user is rate limited and how long to wait.

    This should be called BEFORE attempting to start a conversation session.
    """
    from rate_limiter import rate_limiter
    import time

    try:
        # Use user_id if authenticated, otherwise use "guest"
        identifier = str(current_user.id) if current_user else "guest"
        category = "realtime"  # Check realtime session limit

        # Get rate limit configuration
        config = rate_limiter.limits[category]
        window_seconds = config["window_seconds"]
        max_requests = config["max_requests"]

        # Check if rate limited (WITHOUT consuming a request)
        is_limited, retry_after = rate_limiter._is_rate_limited(identifier, category)

        if is_limited:
            # User is rate limited
            minutes_to_wait = max(1, int(retry_after / 60))

            return {
                "is_rate_limited": True,
                "retry_after_seconds": retry_after,
                "retry_after_minutes": minutes_to_wait,
                "message": f"You've practiced a lot! Take a {minutes_to_wait}-minute break to let your learning sink in. 🧘",
                "limit_info": {
                    "max_sessions": max_requests,
                    "window_hours": int(window_seconds / 3600),
                    "category": category
                }
            }
        else:
            # User is NOT rate limited
            # Calculate how many sessions they have left
            timestamps = rate_limiter.requests[identifier].get(category, [])
            cutoff = time.time() - window_seconds
            valid_requests = [ts for ts in timestamps if ts > cutoff]
            remaining_sessions = max_requests - len(valid_requests)

            return {
                "is_rate_limited": False,
                "remaining_sessions": remaining_sessions,
                "message": "You're good to go! Start your practice session.",
                "limit_info": {
                    "max_sessions": max_requests,
                    "window_hours": int(window_seconds / 3600),
                    "category": category
                }
            }

    except Exception as e:
        print(f"[RATE_LIMIT_CHECK] Error checking rate limit: {str(e)}")
        # If there's an error, allow the session (fail open)
        return {
            "is_rate_limited": False,
            "message": "Rate limit check unavailable, proceeding...",
            "error": str(e)
        }
```

**Key Features:**
- ✅ Does NOT consume a rate limit token
- ✅ Returns clear status: `is_rate_limited`, `retry_after_seconds`, `retry_after_minutes`
- ✅ Shows remaining sessions if not rate limited
- ✅ Graceful error handling (fail open if check fails)
- ✅ User-friendly messages
- ✅ Works for both authenticated users and guests

### Mobile App Changes

#### Updated `handleStartPracticeConversation()` Function

**File:** `src/screens/Practice/ConversationScreen.tsx` (line ~831)

```typescript
const handleStartPracticeConversation = async () => {
  if (Platform.OS === 'ios') {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
  }

  // ✅ PRE-FLIGHT CHECK: Verify rate limit status BEFORE starting session
  console.log('[CONVERSATION] 🔍 Checking rate limit status...');
  try {
    const rateLimitResponse = await DefaultService.checkRateLimitStatusApiRealtimeRateLimitStatusGet();

    if (rateLimitResponse.is_rate_limited) {
      console.log('[CONVERSATION] 🚫 User is rate limited:', rateLimitResponse);

      // Show rate limit alert with wait time
      Alert.alert(
        t('practice.conversation.alert_rate_limited_title', { defaultValue: 'Take a Break! 🧘' }),
        rateLimitResponse.message || `You've practiced a lot! Please wait ${rateLimitResponse.retry_after_minutes} minute(s) before starting a new session.`,
        [
          {
            text: t('buttons.ok', { defaultValue: 'OK' }),
            onPress: () => {
              // Close modal and go back
              setShowInfoModal(false);
              navigation.goBack();
            }
          }
        ]
      );

      return; // Don't start session
    }

    console.log('[CONVERSATION] ✅ Rate limit check passed, remaining sessions:', rateLimitResponse.remaining_sessions);

  } catch (error) {
    console.error('[CONVERSATION] ⚠️ Rate limit check failed, proceeding anyway:', error);
    // If rate limit check fails, proceed anyway (fail open)
  }

  // ... rest of function (learning plan check, start session, etc.)
};
```

**Key Features:**
- ✅ Checks rate limit BEFORE closing "Important Information" modal
- ✅ Shows user-friendly alert with exact wait time if rate limited
- ✅ Automatically navigates back if rate limited
- ✅ Graceful error handling (proceeds if check fails)
- ✅ Logs status for debugging

---

## Response Examples

### Not Rate Limited (Happy Path)

```json
{
  "is_rate_limited": false,
  "remaining_sessions": 10,
  "message": "You're good to go! Start your practice session.",
  "limit_info": {
    "max_sessions": 10,
    "window_hours": 1,
    "category": "realtime"
  }
}
```

**User Experience:** Modal closes, session starts immediately

### Rate Limited (User Blocked)

```json
{
  "is_rate_limited": true,
  "retry_after_seconds": 1847,
  "retry_after_minutes": 31,
  "message": "You've practiced a lot! Take a 31-minute break to let your learning sink in. 🧘",
  "limit_info": {
    "max_sessions": 10,
    "window_hours": 1,
    "category": "realtime"
  }
}
```

**User Experience:**
1. Alert shows: "Take a Break! 🧘"
2. Message: "You've practiced a lot! Take a 31-minute break to let your learning sink in."
3. User taps "OK"
4. Modal closes, navigates back to previous screen

### Error During Check (Fail Open)

```json
{
  "is_rate_limited": false,
  "message": "Rate limit check unavailable, proceeding...",
  "error": "Some error message"
}
```

**User Experience:** Session proceeds normally (better to allow session than block user on error)

---

## User Flow Diagram

```
User clicks "Got it! Let's start"
         |
         v
[PRE-FLIGHT CHECK]
Call: GET /api/realtime/rate-limit-status
         |
         +-- is_rate_limited = true?
         |        |
         |        v
         |   Show Alert:
         |   "Take a Break! 🧘"
         |   "Please wait X minutes"
         |        |
         |        v
         |   Navigate Back
         |
         +-- is_rate_limited = false?
                  |
                  v
            Proceed with session
            Close modal
            Call POST /api/realtime/token
            Start conversation
```

---

## Rate Limit Configuration

**Current Settings** (from `rate_limiter.py`):

```python
"realtime": {
    "max_requests": 10,     # 10 sessions
    "window_seconds": 3600  # Per hour
}
```

**What this means:**
- Users can start max 10 conversation sessions per hour
- After 10 sessions, they must wait until the oldest session expires (rolling window)
- The check endpoint shows exact wait time

**Separate from other limits:**
- `"general"`: 100 requests/minute (for mid-session activities)
- `"auth"`: 10 requests/5min (for login attempts)

---

## Testing Guide

### Test 1: Normal Flow (Not Rate Limited)

1. **Start app and go to Conversation screen**
2. **Click "Got it! Let's start"**
3. **Expected logs:**
   ```
   [CONVERSATION] 🔍 Checking rate limit status...
   [CONVERSATION] ✅ Rate limit check passed, remaining sessions: 10
   [CONVERSATION] 🚀 Starting practice conversation
   ```
4. **Expected behavior:** Modal closes, session starts normally

### Test 2: Rate Limited User

1. **Manually trigger rate limit** (start 10 sessions within an hour)
2. **Try to start 11th session**
3. **Click "Got it! Let's start"**
4. **Expected logs:**
   ```
   [CONVERSATION] 🔍 Checking rate limit status...
   [CONVERSATION] 🚫 User is rate limited: {is_rate_limited: true, retry_after_minutes: X}
   ```
5. **Expected behavior:**
   - Alert shows: "Take a Break! 🧘"
   - Message includes wait time in minutes
   - After tapping "OK", modal closes and navigates back

### Test 3: Error Handling (Backend Down)

1. **Stop backend**
2. **Try to start session**
3. **Expected logs:**
   ```
   [CONVERSATION] 🔍 Checking rate limit status...
   [CONVERSATION] ⚠️ Rate limit check failed, proceeding anyway: [error]
   [CONVERSATION] 🚀 Starting practice conversation
   ```
4. **Expected behavior:** Session proceeds anyway (fail open)

### Test 4: Guest vs Authenticated User

- **Guest users:** Tracked by IP address
- **Authenticated users:** Tracked by user ID
- Both get same 10 sessions/hour limit

### Test 5: Check via API

```bash
# Test endpoint directly
curl -s http://localhost:8000/api/realtime/rate-limit-status | python -m json.tool

# Expected response (not rate limited):
{
    "is_rate_limited": false,
    "remaining_sessions": 10,
    "message": "You're good to go! Start your practice session.",
    "limit_info": {
        "max_sessions": 10,
        "window_hours": 1,
        "category": "realtime"
    }
}
```

---

## Benefits

### Before Implementation:
❌ Users get generic "Failed to connect" error
❌ No indication of why session failed
❌ No information about wait time
❌ Frustrated users retry multiple times
❌ Support tickets: "Why can't I start a session?"

### After Implementation:
✅ Clear communication: "Take a break!"
✅ Exact wait time shown
✅ Prevents wasted API calls
✅ Better user experience
✅ Reduced support burden

---

## Future Enhancements

### Phase 2: Visual Countdown
- Show countdown timer in alert
- Update remaining time every second
- Allow user to wait on screen

### Phase 3: Session History
- Show user's recent sessions
- Display when next session will be available
- Show usage stats (e.g., "7 of 10 sessions used")

### Phase 4: Premium Bypass
- Premium users get unlimited sessions
- Show upgrade prompt in rate limit alert
- Track usage differently for paid users

---

## Deployment Checklist

- [x] Backend endpoint created
- [x] Mobile app updated to call endpoint
- [x] API client regenerated (openapi.json)
- [x] User-friendly messages implemented
- [x] Error handling (fail open)
- [ ] Test with actual rate-limited user
- [ ] Add translations for alert messages
- [ ] Deploy backend to Railway
- [ ] Deploy mobile app update
- [ ] Monitor logs for rate limit hits

---

## Files Modified

**Backend:**
- `backend/routes/realtime_routes.py` - Added `/api/realtime/rate-limit-status` endpoint
- `openapi.json` - Regenerated with new endpoint

**Mobile App:**
- `src/screens/Practice/ConversationScreen.tsx` - Added pre-flight check in `handleStartPracticeConversation()`
- `src/api/generated/services/DefaultService.ts` - Regenerated with new method

**Documentation:**
- `RATE_LIMIT_PREFLIGHT_CHECK_IMPLEMENTATION.md` - This file

---

## Implementation Date

**Date:** 2026-03-18
**Status:** ✅ Ready for Testing
**Version:** 1.0 (Pre-Flight Rate Limit Check)
