# Grammar Correction Toggle Implementation

## Overview

Added a **toggle switch** in the "Important Information" modal to allow users to enable/disable real-time grammar corrections during conversation. This gives users control over their learning experience.

## Feature Details

### Toggle Behavior

- **Enabled by default** for A1/A2 learners (beginners benefit most from corrections)
- **Only visible for A1/A2 levels** (advanced learners don't get real-time corrections)
- **Persists for the session** - toggle state is passed to backend
- **Placed perfectly** next to Conversation Help toggle for consistency

### User Experience

**When Enabled (Default for A1/A2):**
- Grammar correction cards appear during conversation
- Function calling is active on backend
- User gets instant feedback on major errors

**When Disabled:**
- No grammar correction cards shown
- Function calling tools NOT registered with OpenAI
- Cleaner conversation flow, no interruptions

---

## Implementation Details

### Mobile App Changes

#### 1. Added State for Toggle

**File:** `src/screens/Practice/ConversationScreen.tsx` (line ~327)

```typescript
// Grammar correction toggle state (enabled by default for A1/A2 only)
const [grammarCorrectionsEnabled, setGrammarCorrectionsEnabled] = useState(() => {
  return level === 'A1' || level === 'A2';
});
```

**Default behavior:**
- A1/A2 levels: `true` (enabled)
- B1+ levels: `true` but toggle won't show (function calling not supported)

#### 2. Added Toggle UI in Modal

**File:** `src/screens/Practice/ConversationScreen.tsx` (line ~2473)

```typescript
{/* Grammar Corrections Toggle - Only for A1/A2 users */}
{((level === 'A1' || level === 'A2') || (learningPlan?.proficiency_level === 'A1' || learningPlan?.proficiency_level === 'A2')) && (
  <View style={[styles.infoCardCompact, styles.helpToggleCard, { backgroundColor: 'rgba(255, 255, 255, 0.15)', borderColor: 'rgba(255, 255, 255, 0.25)' }]}>
    <Ionicons name="bulb-outline" size={22} color="#FFFFFF" />
    <View style={styles.infoContent}>
      <Text style={styles.infoTitle}>{t('practice.conversation.modal_info_corrections_title', { defaultValue: 'Grammar Corrections' })}</Text>
      <Text style={styles.infoTextCompact}>Get instant feedback on grammar mistakes during conversation</Text>
    </View>
    <Switch
      value={grammarCorrectionsEnabled}
      onValueChange={(value) => {
        if (Platform.OS === 'ios') {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
        }
        setGrammarCorrectionsEnabled(value);
        console.log('[GRAMMAR_CORRECTIONS] Toggle changed:', value);
      }}
      trackColor={{ false: 'rgba(255, 255, 255, 0.3)', true: 'rgba(255, 255, 255, 0.5)' }}
      thumbColor={grammarCorrectionsEnabled ? '#FFFFFF' : 'rgba(255, 255, 255, 0.8)'}
      ios_backgroundColor="rgba(255, 255, 255, 0.3)"
    />
  </View>
)}
```

**Design features:**
- ✅ Uses lightbulb icon (`bulb-outline`) to represent learning/tips
- ✅ Matches Conversation Help toggle styling perfectly
- ✅ Same card style, colors, and layout
- ✅ Haptic feedback on iOS
- ✅ Console logging for debugging

#### 3. Pass Value to RealtimeService

**File:** `src/screens/Practice/ConversationScreen.tsx` (line ~968)

```typescript
realtimeServiceRef.current = new RealtimeService({
  // ... other config
  disableCorrections: !grammarCorrectionsEnabled, // Pass grammar corrections preference
  // ... rest of config
});
```

**Logic:**
- `grammarCorrectionsEnabled = true` → `disableCorrections = false` → Corrections ON
- `grammarCorrectionsEnabled = false` → `disableCorrections = true` → Corrections OFF

#### 4. Updated Type Definition

**File:** `src/services/types.ts`

```typescript
export interface RealtimeServiceConfig {
  // ... other fields
  disableCorrections?: boolean; // Disable real-time grammar corrections (A1/A2 only)
  // ... rest of fields
}
```

#### 5. Pass to Backend API

**File:** `src/services/RealtimeService.ts` (line ~107)

```typescript
const response = await DefaultService.generateTokenApiRealtimeTokenPost({
  // ... other fields
  disable_corrections: this.config.disableCorrections || false, // Disable grammar corrections if requested
});
```

### Backend Changes

#### 1. Added Field to Request Model

**File:** `backend/routes/realtime_routes.py` (line ~52)

```python
class TutorSessionRequest(BaseModel):
    # ... existing fields
    disable_corrections: Optional[bool] = False  # Disable real-time grammar corrections (A1/A2 only)
```

**Default:** `False` (corrections enabled by default)

#### 2. Updated Function Tool Registration Logic

**File:** `backend/routes/realtime_routes.py` (line ~1475)

```python
# Define function tools for grammar correction (A1/A2 only, and only if not disabled)
tools = []
if request.level.upper() in ['A1', 'A2'] and not request.disable_corrections:
    tools = [
        {
            "type": "function",
            "name": "report_grammar_mistake",
            # ... function definition
        }
    ]
```

**Logic:**
- Level is A1 or A2 **AND** `disable_corrections` is `False` → Tools registered ✅
- Level is A1 or A2 **BUT** `disable_corrections` is `True` → No tools ❌
- Level is B1+ → No tools regardless of flag ❌

---

## UI/UX Design

### Modal Layout (Top to Bottom)

```
┌─────────────────────────────────────────┐
│  Important Information                   │
├─────────────────────────────────────────┤
│                                          │
│  [Icon] How it Works                     │
│  Engage in natural conversation...      │
│                                          │
│  [Icon] Conversation Help     [Toggle]   │
│  Toggle AI suggestions...                │
│                                          │
│  [Icon] Grammar Corrections  [Toggle]   │  ← NEW!
│  Get instant feedback...                 │
│                                          │
│  [3 min] [5 min]  (A1/A2 only)          │
│                                          │
│  [Cancel]  [Got it! Let's start]         │
└─────────────────────────────────────────┘
```

**Visual consistency:**
- Same card background color: `rgba(255, 255, 255, 0.15)`
- Same border color: `rgba(255, 255, 255, 0.25)`
- Same toggle colors and style
- Same spacing and padding

---

## Testing Guide

### Test 1: A1/A2 User - Toggle Visible

1. **Go to Conversation screen as A1 or A2 user**
2. **Check "Important Information" modal**
3. **Expected:**
   - "Grammar Corrections" toggle IS visible
   - Default: ON (enabled)
   - Positioned below "Conversation Help" toggle

### Test 2: Enable/Disable During Session Start

**Test 2a: With Corrections Enabled**
1. **Keep toggle ON**
2. **Click "Got it! Let's start"**
3. **Make a grammar mistake:** "I am like travel"
4. **Expected:**
   - Grammar correction card appears ✅
   - Shows: "am like" → "like"

**Test 2b: With Corrections Disabled**
1. **Turn toggle OFF**
2. **Click "Got it! Let's start"**
3. **Make a grammar mistake:** "I am like travel"
4. **Expected:**
   - NO grammar correction card ❌
   - Conversation continues normally

### Test 3: B1+ User - Toggle Hidden

1. **Go to Conversation screen as B1, B2, C1, or C2 user**
2. **Check "Important Information" modal**
3. **Expected:**
   - "Grammar Corrections" toggle NOT visible
   - Only "Conversation Help" toggle shows

### Test 4: Backend Logs

**With corrections enabled:**
```
[TOOLS] Added 1 function tools for A1 level
```

**With corrections disabled:**
```
(No tools message - tools array is empty)
```

### Test 5: API Request

Check the request payload sent to `/api/realtime/token`:

**With toggle ON:**
```json
{
  "language": "english",
  "level": "A1",
  "disable_corrections": false
}
```

**With toggle OFF:**
```json
{
  "language": "english",
  "level": "A1",
  "disable_corrections": true
}
```

---

## Benefits

### User Control
✅ Users choose their learning style
✅ Some prefer uninterrupted flow
✅ Others want immediate feedback

### Reduced Distractions
✅ Advanced flow for confident learners
✅ Focus on conversation, not corrections
✅ Cleaner UI when disabled

### Better UX
✅ Clear, discoverable toggle
✅ Matches existing design patterns
✅ Obvious what it does

---

## Future Enhancements

### Phase 2: Persistence
- Save preference to user profile
- Remember across sessions
- Different preference per language

### Phase 3: Smart Defaults
- Disable after user reaches certain accuracy
- Auto-suggest disabling for advanced A2 learners
- Re-enable if accuracy drops

### Phase 4: Analytics
- Track how many users disable corrections
- Measure impact on engagement
- A/B test different default values

---

## Files Modified

**Mobile App:**
- `src/screens/Practice/ConversationScreen.tsx` - Added state, UI, and config passing
- `src/services/types.ts` - Added `disableCorrections` field to config
- `src/services/RealtimeService.ts` - Pass `disable_corrections` to API
- `src/api/generated/` - Regenerated TypeScript client

**Backend:**
- `backend/routes/realtime_routes.py` - Added `disable_corrections` field and logic
- `openapi.json` - Regenerated with new field

**Documentation:**
- `GRAMMAR_CORRECTION_TOGGLE_IMPLEMENTATION.md` - This file

---

## Implementation Date

**Date:** 2026-03-18
**Status:** ✅ Ready for Testing
**Version:** 1.0 (Grammar Correction Toggle)
