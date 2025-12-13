# Guest User Practice Session API Documentation

## Overview
This API allows guest (non-authenticated) users to receive comprehensive session analysis without requiring signup or database persistence. Perfect for mobile apps to show value before conversion.

---

## Endpoints

### 1. Analyze Guest Session (Full Analysis)

**Endpoint:** `POST /api/guest/analyze-session`

**Authentication:** None required

**Purpose:** Complete session analysis including sentence corrections, AI summary, insights, and flashcards

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "I go to the store yesterday",
      "timestamp": "2024-01-01T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Oh, you went to the store yesterday? What did you buy?",
      "timestamp": "2024-01-01T12:00:05Z"
    }
  ],
  "duration_minutes": 2.0,
  "sentences_for_analysis": [
    {
      "text": "I go to the store yesterday",
      "timestamp": "2024-01-01T12:00:00Z",
      "messageIndex": 0
    }
  ],
  "language": "spanish",
  "level": "B1",
  "topic": "travel"
}
```

**Response:**
```json
{
  "success": true,
  "is_guest": true,
  "session_stats": {
    "total_words": 245,
    "user_words": 120,
    "tutor_words": 125,
    "user_message_count": 8,
    "tutor_message_count": 7,
    "total_messages": 15,
    "average_user_message_length": 15.0,
    "average_tutor_message_length": 17.9,
    "conversation_turns": 15,
    "speaking_speed_wpm": 60,
    "duration_minutes": 2.0
  },
  "session_summary": "Great job completing your first spanish practice session! You spoke 120 words in 2 minutes at B1 level...",
  "background_analyses": [
    {
      "sentence": "I go to the store yesterday",
      "is_worth_analyzing": true,
      "grammar_issues": [
        "Incorrect verb tense: 'go' should be 'went'"
      ],
      "vocabulary_suggestions": [
        "Consider using 'supermarket' for more specific vocabulary"
      ],
      "alternative_phrasings": [
        "I went to the store yesterday",
        "I went to the supermarket yesterday"
      ],
      "difficulty_level": "A2",
      "quality_score": 65,
      "explanation": "The sentence uses present tense 'go' with the past time marker 'yesterday', which is grammatically incorrect."
    }
  ],
  "insights": {
    "breakthrough_moments": [
      "Successfully used past tense in most sentences",
      "Good vocabulary range for B1 level"
    ],
    "struggle_points": [
      "Inconsistent verb tense usage",
      "Preposition placement needs practice"
    ],
    "confidence_level": "Medium",
    "immediate_actions": [
      "Practice irregular past tense verbs for 5 minutes daily",
      "Review common preposition patterns"
    ]
  },
  "flashcards": [
    {
      "id": "guest_flash_0",
      "front": "How can you improve this sentence?\n\n\"I go to the store yesterday\"",
      "back": "I went to the store yesterday",
      "category": "grammar",
      "difficulty": "A2",
      "hint": "Incorrect verb tense: 'go' should be 'went'"
    }
  ],
  "message": "Session analyzed successfully. Sign up to save your progress!"
}
```

---

### 2. Quick Stats (Lightweight)

**Endpoint:** `POST /api/guest/quick-stats`

**Authentication:** None required

**Purpose:** Get just session statistics without full analysis (faster, cheaper)

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    },
    {
      "role": "assistant",
      "content": "I'm well, thank you! And you?"
    }
  ],
  "duration_minutes": 2.0
}
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_words": 245,
    "user_words": 120,
    "tutor_words": 125,
    "user_message_count": 8,
    "tutor_message_count": 7,
    "total_messages": 15,
    "average_user_message_length": 15.0,
    "average_tutor_message_length": 17.9,
    "conversation_turns": 15,
    "speaking_speed_wpm": 60,
    "duration_minutes": 2.0
  }
}
```

---

## Mobile Implementation Guide

### Step 1: Collect Session Data

During the 2-minute conversation, collect:

```typescript
const sessionData = {
  messages: conversationMessages,  // All messages with role, content, timestamp
  duration_minutes: 2.0,
  sentences_for_analysis: userSentences,  // Extract user sentences only
  language: 'spanish',
  level: 'B1',
  topic: 'travel'
}
```

### Step 2: Call Analysis API

After session ends:

```typescript
const response = await fetch('https://api.mytacoai.com/api/guest/analyze-session', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(sessionData)
})

const analysis = await response.json()
```

### Step 3: Display Results

Show a tabbed results screen:

**Tab 1: Summary**
- Display `session_stats` (words, messages, speed)
- Show `session_summary` text

**Tab 2: Sentence Analysis**
- List `background_analyses` items
- Show grammar issues, suggestions, alternatives
- Display difficulty badges

**Tab 3: Flashcards**
- Swipeable flashcard UI
- Use `flashcards` array
- Front/back flip animation

**Tab 4: Insights**
- Show `insights.breakthrough_moments` (positive)
- Show `insights.struggle_points` (areas to improve)
- Display `insights.immediate_actions` (next steps)

### Step 4: Conversion CTA

Bottom button: **"Sign Up Free to Save Your Progress"**

---

## Data Flow

```
Mobile App (2-min session ends)
    ↓
Extract messages + user sentences
    ↓
POST /api/guest/analyze-session
    ↓
Backend analyzes (NO database save)
    ↓
Returns full analysis
    ↓
Mobile displays results
    ↓
User sees value → Signs up
```

---

## Performance Notes

- **Analysis Time:** ~3-5 seconds for full analysis
- **API Costs:** ~$0.02 per session (GPT-4o-mini)
- **Max Sentences:** Recommends analyzing 5-10 user sentences max
- **Response Size:** ~5-10KB typical

---

## Error Handling

If sentence analysis fails, the API will still return stats and summary:

```json
{
  "success": true,
  "is_guest": true,
  "session_stats": { ... },
  "session_summary": "...",
  "background_analyses": [],  // Empty if failed
  "insights": { ... },
  "flashcards": [],  // Empty if no analyses
  "message": "Session analyzed successfully. Sign up to save your progress!"
}
```

---

## Cost Optimization

To minimize API costs for guest users:

1. **Limit sentences:** Only send 5-10 most important user sentences
2. **Use quick-stats:** For interim feedback during session
3. **Batch calls:** Don't call per message, only at end
4. **Cache results:** Store in memory for session duration

---

## Differences from Authenticated Users

| Feature | Guest | Authenticated |
|---------|-------|---------------|
| Session Duration | 2 min | 5 min |
| Database Save | ❌ No | ✅ Yes |
| Sentence Analysis | ✅ Yes | ✅ Yes |
| AI Summary | ✅ Yes (short) | ✅ Yes (detailed) |
| Flashcards | ✅ Yes (5 max) | ✅ Yes (unlimited) |
| Progress Tracking | ❌ No | ✅ Yes |
| History | ❌ No | ✅ Yes |
| Enhanced Analysis | ❌ No | ✅ Yes |

---

## Example: Complete Mobile Flow

```typescript
// After 2-minute timer ends
async function handleSessionEnd() {
  // 1. Show loading
  setLoading(true)

  // 2. Prepare data
  const data = {
    messages: conversationHistory,
    duration_minutes: 2.0,
    sentences_for_analysis: extractUserSentences(conversationHistory),
    language: selectedLanguage,
    level: selectedLevel,
    topic: selectedTopic
  }

  // 3. Call API
  try {
    const response = await fetch(`${API_URL}/api/guest/analyze-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })

    const analysis = await response.json()

    // 4. Show results screen
    navigation.navigate('SessionResults', { analysis })

  } catch (error) {
    // Show error, but still allow signup
    showError('Analysis failed, but you can still sign up!')
  } finally {
    setLoading(false)
  }
}

function extractUserSentences(messages) {
  return messages
    .filter(m => m.role === 'user')
    .slice(-10)  // Last 10 messages
    .map((m, idx) => ({
      text: m.content,
      timestamp: m.timestamp,
      messageIndex: idx
    }))
}
```

---

## Testing

### Test Request (cURL)

```bash
curl -X POST https://api.mytacoai.com/api/guest/analyze-session \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I go to the store yesterday"},
      {"role": "assistant", "content": "Oh, you went to the store yesterday?"}
    ],
    "duration_minutes": 2.0,
    "sentences_for_analysis": [
      {"text": "I go to the store yesterday", "messageIndex": 0}
    ],
    "language": "spanish",
    "level": "B1",
    "topic": "travel"
  }'
```

### Test Response

Should return JSON with:
- ✅ `success: true`
- ✅ `is_guest: true`
- ✅ `session_stats` object
- ✅ `session_summary` string
- ✅ `background_analyses` array
- ✅ `insights` object
- ✅ `flashcards` array

---

## Support

For issues or questions:
- Backend Repo: `/home/user/language-tutor/backend`
- Route File: `/backend/routes/guest_analysis_routes.py`
- Main App: `/backend/main.py` (line 191, 203)
