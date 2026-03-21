# Function Calling Implementation for Grammar Corrections

## Overview

This document describes the **function calling approach** for real-time grammar corrections in voice conversations using OpenAI Realtime API.

## The Problem We Solved

### Original Approach (Failed)
- Used text markers: `{{correction:wrong|correct|tip}}`
- AI generated markers in text
- **Problem:** AI also SPOKE the markers aloud
- Result: "Good correction am like like Use I like Do you like travel?"

### Why Text Markers Failed
- OpenAI Realtime API generates audio and text together
- Whatever text is generated = what gets spoken
- No way to separate "text to display" from "text to speak"

## The Solution: Function Calling

### How It Works

**gpt-realtime-mini DOES support function calling** (confirmed from official docs)

1. **Student makes mistake:** "I am like travel"
2. **AI responds naturally:** "Good! Do you like travel?"
3. **AI calls function silently:**
   ```json
   {
     "name": "report_grammar_mistake",
     "arguments": {
       "wrong": "am like",
       "correct": "like",
       "tip": "Use 'I like' for positive sentences"
     }
   }
   ```
4. **Mobile app receives function call event**
5. **Correction card appears on screen**
6. **Conversation continues naturally** ✅

### Key Benefits

✅ **AI speaks naturally** - No mention of corrections in speech
✅ **Visual feedback only** - Correction card appears silently
✅ **Non-intrusive** - Doesn't interrupt conversation flow
✅ **Accurate** - Function parameters ensure structured data

## Implementation Details

### Backend Changes

**File:** `backend/routes/realtime_routes.py`

Added `tools` parameter to Realtime API payload (A1/A2 only):

```python
tools = [
    {
        "type": "function",
        "name": "report_grammar_mistake",
        "description": "Report a MAJOR grammar mistake...",
        "parameters": {
            "type": "object",
            "properties": {
                "wrong": {"type": "string"},
                "correct": {"type": "string"},
                "tip": {"type": "string"}
            },
            "required": ["wrong", "correct", "tip"]
        }
    }
]

payload = {
    "model": "gpt-realtime-mini",
    "tools": tools,  # Function calling enabled
    ...
}
```

**File:** `backend/prompt_optimization_helpers.py`

Updated instructions to use function calling instead of text markers:

```
When you detect a MAJOR grammar mistake:
1. Respond naturally WITHOUT mentioning the mistake
2. Call report_grammar_mistake() function
3. Continue conversation

Example:
Student: "I am like travel"
Your speech: "Good! Do you like travel?"
Function call: report_grammar_mistake(wrong="am like", correct="like", tip="Use 'I like'")
```

### Mobile App Changes

**File:** `src/screens/Practice/ConversationScreen.tsx`

**1. Listen for function call events:**

```typescript
onEvent: (event) => {
  if (event.type === 'response.function_call_arguments.done') {
    const { call_id, name, arguments: argsString } = event;

    if (name === 'report_grammar_mistake') {
      const args = JSON.parse(argsString);

      // Add correction message
      const correctionMessage = {
        id: `correction-${Date.now()}`,
        role: 'correction',
        correction: {
          wrong: args.wrong,
          correct: args.correct,
          tip: args.tip
        }
      };

      setMessages(prev => [...prev, correctionMessage]);

      // ✅ CRITICAL: Send function call response back to OpenAI
      realtimeServiceRef.current?.sendEvent({
        type: 'conversation.item.create',
        item: {
          type: 'function_call_output',
          call_id: call_id,
          output: JSON.stringify({ status: 'success', message: 'Correction displayed to user' })
        }
      });

      // ✅ CRITICAL: Tell the AI to continue the conversation
      realtimeServiceRef.current?.sendEvent({
        type: 'response.create'
      });
    }
  }
}
```

**2. Render correction messages:**

```typescript
{messages.map((message) => {
  // Show correction card for correction messages
  if (message.role === 'correction' && message.correction) {
    return (
      <GrammarCorrectionCard
        key={message.id}
        wrong={message.correction.wrong}
        correct={message.correction.correct}
        tip={message.correction.tip}
        targetLanguage={language}
      />
    );
  }

  // Show normal message bubble
  return <AnimatedMessage key={message.id} message={message} />;
})}
```

## Event Flow

### Realtime API Events

```
1. User speaks: "I am like travel"
   └─> input_audio_buffer.speech_started

2. AI processes and detects error

3. AI generates response
   ├─> response.audio.started
   ├─> AI speaks: "Good! Do you like travel?"
   └─> response.function_call_arguments.done ⭐
       └─> Function: report_grammar_mistake
           └─> Arguments: {wrong, correct, tip}
           └─> call_id: "call_abc123"

4. Mobile app receives function call
   ├─> Creates correction message
   ├─> Renders GrammarCorrectionCard
   ├─> Sends function_call_output (acknowledges receipt) ✅
   └─> Sends response.create (continues conversation) ✅

5. User sees:
   ├─> AI speech bubble: "Good! Do you like travel?"
   └─> Correction card: "am like" → "like"

6. Conversation continues naturally
```

## When Function Gets Called

**AI calls `report_grammar_mistake` for:**
- ✅ Wrong articles: "a" vs "an" vs "the"
- ✅ Verb conjugation: "I go" vs "I went"
- ✅ Subject-verb agreement: "she don't" → "she doesn't"
- ✅ Plural forms: "two brother" → "two brothers"
- ✅ Word order: major structural errors

**AI does NOT call function for:**
- ❌ Minor pronunciation issues
- ❌ Small vocabulary choices
- ❌ Errors that don't impede understanding
- ❌ Same error repeated within 3 turns

## Testing Guide

### Backend Test

**1. Start backend:**
```bash
python -m uvicorn main:app --reload
```

**2. Check logs for tool registration:**
```
[TOOLS] Added 1 function tools for A1 level
```

**3. Monitor function calls:**
```
[GRAMMAR_CORRECTION] ✨ Function called: {wrong: "am like", correct: "like", ...}
```

### Mobile App Test

**1. Start conversation (A1 or A2 level)**

**2. Make intentional mistakes:**
- "I am like travel" → Should trigger correction
- "She don't like coffee" → Should trigger correction
- "I have two brother" → Should trigger correction

**3. Expected behavior:**
- AI speaks normally: "Good! Do you like travel?"
- Correction card appears with slide animation
- No mention of error in AI's speech

**4. Check console logs:**
```
[GRAMMAR_CORRECTION] ✨ Function called: ...
[CONVERSATION] Event: response.function_call_arguments.done
```

## Comparison: Text Markers vs Function Calling

| Aspect | Text Markers | Function Calling |
|--------|-------------|------------------|
| **AI Speech** | Speaks the marker ❌ | Clean speech ✅ |
| **Parsing** | Regex parsing | Structured JSON |
| **Reliability** | Fragile (regex can fail) | Robust |
| **API Support** | Not designed for this | Designed for this ✅ |
| **Data Structure** | Unstructured text | Typed parameters |

## Critical Implementation Detail: Function Call Response Flow

**IMPORTANT:** When OpenAI calls a function, the conversation **pauses** until the client responds. This is different from regular text-based function calling where you might not need to respond immediately.

### Required Response Flow

When you receive `response.function_call_arguments.done`, you MUST:

1. **Process the function call** (e.g., display correction card)
2. **Send `conversation.item.create` with `function_call_output`:**
   ```typescript
   realtimeServiceRef.current?.sendEvent({
     type: 'conversation.item.create',
     item: {
       type: 'function_call_output',
       call_id: call_id, // From the event
       output: JSON.stringify({ status: 'success' })
     }
   });
   ```

3. **Send `response.create` to continue conversation:**
   ```typescript
   realtimeServiceRef.current?.sendEvent({
     type: 'response.create'
   });
   ```

**What happens if you don't respond?**
- The AI waits indefinitely for your response
- Conversation may hang or behave unexpectedly
- User experience is broken

### Why This Matters

The sample Python code from OpenAI documentation shows this pattern clearly:
```python
# After receiving function call
data_channel.send(json.dumps({
    "type": "conversation.item.create",
    "item": {
        "type": "function_call_output",
        "call_id": call_id,
        "output": json.dumps(result)
    }
}))

# Continue conversation
data_channel.send(json.dumps({"type": "response.create"}))
```

Our initial implementation was missing these two critical steps!

## Known Limitations

### 1. A1/A2 Only
Function calling is only enabled for beginner levels. Advanced learners don't need real-time corrections.

### 2. Function Call Timing
Function call event arrives slightly after the audio starts. This means:
- Correction card appears ~500ms after AI starts speaking
- This is acceptable and feels natural

### 3. No Guarantee AI Will Call
Even with instructions, AI might not call the function for every error. This is intentional - we only want MAJOR errors corrected.

## Future Enhancements

### Phase 2
- **Correction Analytics:** Track which errors are most common
- **Adaptive Frequency:** Reduce corrections as user improves
- **Correction History:** Show all corrections from session

### Phase 3
- **User Feedback:** "Was this helpful?" button on correction cards
- **A/B Testing:** Test different tip phrasing
- **Gamification:** Award points for correcting mistakes

## Troubleshooting

### Issue: Function not being called

**Debug steps:**
1. Check level is A1 or A2 (function only enabled for beginners)
2. Check backend logs for `[TOOLS] Added 1 function tools`
3. Verify error is MAJOR (not minor pronunciation)
4. Check if same error was corrected in last 3 turns

### Issue: Correction card not appearing

**Debug steps:**
1. Check mobile logs for `[GRAMMAR_CORRECTION] ✨ Function called`
2. Verify `event.type === 'response.function_call_arguments.done'` is firing
3. Check message state includes correction message
4. Verify `GrammarCorrectionCard` is rendering

### Issue: AI still speaking corrections

**Possible causes:**
1. Backend not restarted after changes
2. Using cached session (close app and restart)
3. AI ignoring instructions (rare - report to OpenAI)

## Cost Implications

**Function calling adds minimal cost:**
- Function definition: ~100 tokens (one-time per session)
- Function call: ~50 tokens per correction
- For 3-minute session with 2 corrections: ~200 extra tokens
- Cost increase: <2%

**This is acceptable for the UX improvement.**

## Deployment Checklist

- [ ] Backend changes deployed to Railway
- [ ] Mobile app changes deployed to TestFlight/Play Store beta
- [ ] Monitor logs for function call frequency
- [ ] A/B test with small user group
- [ ] Gather user feedback
- [ ] Adjust function call criteria based on data
- [ ] Roll out to all A1/A2 users

## References

- [OpenAI Realtime API Documentation](https://platform.openai.com/docs/guides/realtime)
- [gpt-realtime-mini Model Details](https://developers.openai.com/api/docs/models/gpt-realtime-mini)
- [Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)

---

**Implementation Date:** 2026-03-18
**Version:** 2.0 (Function Calling)
**Status:** ✅ Ready for Testing
