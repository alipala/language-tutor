# 🚨 CRITICAL BUG: Session Saving Not Working

## Problem Summary
Sessions are NOT being saved and minutes are NOT being deducted when users complete 5-minute practice sessions.

## Root Cause
The `/api/session-heartbeat` endpoint in `backend/session_heartbeat_routes.py` is **ONLY LOGGING** heartbeats but **NOT SAVING** sessions or deducting minutes.

## Evidence from Production Logs
```
[MONITORING] POST /api/session-heartbeat - User: Anonymous - ID: 7dc071a8-9a50-421a-bb9b-7a0e1577b498
INFO:session_heartbeat_routes:[HEARTBEAT] Received heartbeat: 688921c268819565ef1ce3dc_1760552705175 - 0.5min
INFO:     172.71.103.98:0 - "POST /api/session-heartbeat HTTP/1.1" 200 OK
```

The heartbeat is received but nothing happens after logging.

## The Broken Code Location
**File:** `backend/session_heartbeat_routes.py`
**Lines:** 8-42
**Issue:** The endpoint only logs and returns success, but doesn't:
1. Save the session to database
2. Deduct minutes from user subscription
3. Update learning plan progress

## Current Implementation (BROKEN)
```python
@router.post("/api/session-heartbeat")
async def session_heartbeat(request: Request):
    # ... receives heartbeat data ...
    logger.info(f"[HEARTBEAT] Received heartbeat: {heartbeat_data.get('session_id', 'unknown')} - {heartbeat_data.get('duration_minutes', 0):.1f}min")
    
    # ❌ ONLY RETURNS SUCCESS - NO SAVING!
    return {
        "success": True,
        "message": "Heartbeat received",
        "timestamp": datetime.utcnow().isoformat()
    }
```

## What Should Happen
When a heartbeat is received with duration >= 5 minutes:
1. Extract user_id from session_id
2. Call BulletproofTracker.track_speaking_time_atomic() to deduct minutes
3. Save session summary to learning plan if applicable
4. Return success with confirmation

## The Working Implementation (for reference)
The correct implementation exists in `backend/learning_routes.py` (save_session_summary endpoint):

```python
from subscription_service_bulletproof_fix_no_transactions import BulletproofTracker

tracking_request = SpeakingTimeTrackingRequest(
    user_id=str(current_user.id),
    session_id=learning_plan_session_id,
    speaking_minutes=duration_minutes,
    session_completed=duration_minutes >= 2
)

tracking_success = await BulletproofTracker.track_speaking_time_atomic(tracking_request)
```

## Impact
- User completed 3 sessions (15 minutes total)
- Sessions were NOT saved
- Minutes were NOT deducted
- Learning plan progress NOT updated
- User still shows full minutes remaining

## Fix Required
Update `session_heartbeat_routes.py` to:
1. Parse user_id from session_id
2. Call BulletproofTracker when duration >= 5 minutes
3. Save session data to appropriate collection
4. Return proper confirmation

## Test Case
User: alipala.ist@gmail.com (ID: 688921c268819565ef1ce3dc)
- Completed 3 Dutch sessions (15 minutes)
- Expected: 15 minutes deducted, 3 sessions saved
- Actual: 0 minutes deducted, 0 sessions saved
- Status: ❌ BROKEN

## Priority
🔴 **CRITICAL** - This breaks the core functionality of the application
