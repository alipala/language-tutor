# Mobile App Timer Integration Guide

## ✅ Backend Now Controls Session Duration

The backend now returns session configuration in the `/api/realtime/token` response, including the correct duration for guest vs authenticated users.

---

## 📡 API Response Format

### **Endpoint:** `POST /api/realtime/token`

**Previous Response:**
```json
{
  "id": "sess_abc123",
  "client_secret": { "value": "..." },
  "model": "gpt-realtime-mini",
  "expires_at": 1234567890
}
```

**NEW Response (includes session_config):**
```json
{
  "id": "sess_abc123",
  "client_secret": { "value": "..." },
  "model": "gpt-realtime-mini",
  "expires_at": 1234567890,
  "session_config": {
    "max_duration_seconds": 120,
    "is_guest": true,
    "duration_minutes": 2,
    "assessment_duration_seconds": 30
  }
}
```

---

## 🔧 Mobile Implementation

### **BEFORE (Hardcoded - ❌ Wrong):**

```typescript
// ❌ Don't do this anymore
const MAX_DURATION = 300; // Always 5 minutes

function PracticeScreen() {
  const [timeRemaining, setTimeRemaining] = useState(MAX_DURATION);
  // ...
}
```

### **AFTER (Backend-Controlled - ✅ Correct):**

```typescript
// ✅ Use the duration from backend
async function startPracticeSession() {
  // 1. Get token from backend
  const response = await fetch('/api/realtime/token', {
    method: 'POST',
    headers: authHeaders, // Include token if authenticated, omit if guest
    body: JSON.stringify({
      language: 'english',
      level: 'A1',
      topic: 'travel'
    })
  });

  const data = await response.json();

  // 2. Extract session config
  const { session_config } = data;
  const maxDuration = session_config.max_duration_seconds; // 120 or 300
  const isGuest = session_config.is_guest;

  console.log(`Session duration: ${maxDuration}s (${session_config.duration_minutes} min)`);
  console.log(`User type: ${isGuest ? 'guest' : 'authenticated'}`);

  // 3. Initialize timer with backend-provided duration
  setMaxDuration(maxDuration);
  setTimeRemaining(maxDuration);

  // 4. Connect to OpenAI with the token
  connectToRealtime(data.client_secret.value);
}
```

---

## 📱 Complete React Native Example

```typescript
import React, { useState, useEffect } from 'react';
import { View, Text } from 'react-native';

interface SessionConfig {
  max_duration_seconds: number;
  is_guest: boolean;
  duration_minutes: number;
  assessment_duration_seconds: number;
}

export default function PracticeScreen() {
  const [sessionConfig, setSessionConfig] = useState<SessionConfig | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [isActive, setIsActive] = useState(false);

  // Fetch token and config when screen loads
  useEffect(() => {
    async function initSession() {
      try {
        const response = await fetch(`${API_URL}/api/realtime/token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            // Include Authorization header only if user is logged in
            ...(authToken && { 'Authorization': `Bearer ${authToken}` })
          },
          body: JSON.stringify({
            language: selectedLanguage,
            level: selectedLevel,
            topic: selectedTopic
          })
        });

        const data = await response.json();

        // Store session config from backend
        setSessionConfig(data.session_config);
        setTimeRemaining(data.session_config.max_duration_seconds);

        console.log(`✅ Session initialized: ${data.session_config.duration_minutes} minutes`);
        console.log(`   User type: ${data.session_config.is_guest ? 'Guest' : 'Authenticated'}`);

        // Start session with OpenAI token
        await startRealtimeSession(data.client_secret.value);
        setIsActive(true);

      } catch (error) {
        console.error('Failed to initialize session:', error);
      }
    }

    initSession();
  }, []);

  // Countdown timer
  useEffect(() => {
    if (!isActive || timeRemaining <= 0) return;

    const interval = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          handleTimeUp();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, timeRemaining]);

  // Format time as MM:SS
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTimeUp = () => {
    setIsActive(false);
    // Show time-up modal
    navigation.navigate('TimeUp', {
      isGuest: sessionConfig?.is_guest
    });
  };

  return (
    <View>
      {/* Timer Display */}
      <Text style={styles.timer}>
        {formatTime(timeRemaining)} / {formatTime(sessionConfig?.max_duration_seconds || 0)}
      </Text>

      {/* Show guest indicator */}
      {sessionConfig?.is_guest && (
        <Text style={styles.guestBadge}>
          Guest Mode: {sessionConfig.duration_minutes} min limit
        </Text>
      )}

      {/* Rest of your UI */}
    </View>
  );
}
```

---

## 🎯 Key Benefits of Backend Control

### ✅ **Single Source of Truth**
- Duration defined once in backend
- All platforms (iOS, Android, Web) get same value
- No inconsistencies

### ✅ **No App Updates Required**
- Want to test 3 minutes? Change backend, done
- A/B testing different durations
- Instant rollout to all users

### ✅ **Dynamic Configuration**
- Different durations per region
- Promotional periods (e.g., 4 min for holidays)
- Personalized limits per user

### ✅ **Accurate Display**
- Timer shows exactly what backend enforces
- No confusion about limits
- Backend and frontend always in sync

---

## 🔍 What Changed in Backend

**File:** `backend/routes/realtime_routes.py` (lines 1013-1031)

```python
# Determine duration based on authentication
is_guest = current_user is None
max_duration_seconds = 120 if is_guest else 300  # 2 min : 5 min

# Return session config along with OpenAI token
return {
    **result,  # OpenAI session data
    "session_config": {
        "max_duration_seconds": max_duration_seconds,
        "is_guest": is_guest,
        "duration_minutes": max_duration_seconds / 60,
        "assessment_duration_seconds": 30 if is_guest else 60
    }
}
```

---

## 🧪 Testing

### **Test as Guest:**
```bash
curl -X POST http://localhost:8000/api/realtime/token \
  -H "Content-Type: application/json" \
  -d '{"language": "english", "level": "A1", "topic": "travel"}'
```

**Expected Response:**
```json
{
  "session_config": {
    "max_duration_seconds": 120,
    "is_guest": true,
    "duration_minutes": 2.0,
    "assessment_duration_seconds": 30
  }
}
```

### **Test as Authenticated User:**
```bash
curl -X POST http://localhost:8000/api/realtime/token \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"language": "english", "level": "A1", "topic": "travel"}'
```

**Expected Response:**
```json
{
  "session_config": {
    "max_duration_seconds": 300,
    "is_guest": false,
    "duration_minutes": 5.0,
    "assessment_duration_seconds": 60
  }
}
```

---

## 📝 Migration Checklist

For your mobile app:

- [ ] Remove hardcoded `MAX_DURATION = 300` constant
- [ ] Extract `session_config` from token response
- [ ] Use `session_config.max_duration_seconds` for timer
- [ ] Display `session_config.duration_minutes` in UI
- [ ] Check `session_config.is_guest` for conditional features
- [ ] Test as guest user (should see 2:00)
- [ ] Test as authenticated user (should see 5:00)
- [ ] Remove old guest duration constants from app

---

## 🎨 UI Recommendations

### **Timer Display:**
```
┌─────────────────────┐
│  English Practice   │
│                     │
│   ⏱️ 0:45 / 2:00   │  ← Guest user
│                     │
│   Guest Mode        │
└─────────────────────┘

┌─────────────────────┐
│  English Practice   │
│                     │
│   ⏱️ 2:30 / 5:00   │  ← Authenticated
│                     │
└─────────────────────┘
```

### **Guest Badge:**
```typescript
{sessionConfig?.is_guest && (
  <View style={styles.guestBadge}>
    <Text>🎁 Guest Mode: {sessionConfig.duration_minutes} min trial</Text>
    <Text>Sign up for {300/60} min sessions!</Text>
  </View>
)}
```

---

## 🚀 Deployment

**Backend:** Already deployed (commit `27c631d`)

**Mobile App:** Update your code to use `session_config.max_duration_seconds`

**Web App:** Already uses `frontend/lib/guest-utils.ts` which will be updated to fetch from backend in future

---

## 💡 Future Enhancements

With backend control, you can easily add:

1. **Premium tiers:** 10-minute sessions for paid users
2. **Regional limits:** Different durations per country
3. **A/B testing:** Test 2 vs 3 vs 4 minutes
4. **Dynamic pricing:** "Upgrade to 10 min for $X"
5. **Promotional campaigns:** Holiday bonus time

All without app updates! 🎉

---

## ❓ Questions?

- Backend changes: `backend/routes/realtime_routes.py:1013-1031`
- Example implementation: See "Complete React Native Example" above
- Testing: See "Testing" section above
