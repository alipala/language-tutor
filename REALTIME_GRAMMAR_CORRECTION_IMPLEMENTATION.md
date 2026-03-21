# Real-Time Grammar Correction Implementation Guide

## Overview

This document describes the implementation of real-time grammar correction feedback for A1/A2 learners during voice conversations. The feature provides immediate, visual feedback when learners make grammar mistakes, without interrupting the conversation flow.

## Feature Summary

**Goal:** Help A1/A2 learners spot and understand their grammar mistakes during real-time voice conversations, in an engaging and motivating way.

**Key Principles:**
- ✅ Non-intrusive: Corrections appear visually but don't stop the conversation
- ✅ Motivating: Encouraging language and positive visual design
- ✅ Educational: Shows wrong vs. right with brief explanations
- ✅ Balanced: Only corrects MAJOR errors (max 1 per turn)
- ✅ Separate from end-session analysis: Post-session sentence analysis remains unchanged

## Architecture

### Backend (Python/FastAPI)

**File Modified:** `backend/prompt_optimization_helpers.py`
- **Function:** `build_beginner_correction_style()`
- **Location:** Lines 1258-1331
- **Branch:** `feature/realtime-grammar-correction`
- **Commit:** `6aecefb05`

**Changes:**
1. Added correction marker format instructions to AI system prompt
2. Marker format: `{{correction:wrong_part|correct_part|brief_tip}}`
3. Rules for when to use markers (MAJOR errors only)
4. Examples in multiple languages (Dutch, English)

**How It Works:**
- The AI (gpt-realtime-mini) receives updated instructions
- When user makes a MAJOR grammar mistake (articles, verb forms, word order)
- AI responds naturally AND includes hidden correction marker
- Example: `"Goed geprobeerd! {{correction:één|een|Use 'een' for 'a/an', not 'één' (one)}} Heb je een broer of zus?"`

### Mobile App (React Native/TypeScript)

**Files Changed:**
1. **New Component:** `src/components/GrammarCorrectionCard.tsx` (273 lines)
2. **Modified:** `src/screens/Practice/ConversationScreen.tsx`

**Branch:** `feature/realtime-grammar-correction`
**Commit:** `2299f83`

#### GrammarCorrectionCard Component

**Features:**
- Warm orange/cream color scheme (#FFF7ED background, #F97316 accent)
- Slide-in animation from bottom
- Haptic feedback on appearance
- Auto-dismiss after 8 seconds
- Three sections:
  1. **Header:** "Quick Fix!" with bulb icon 💡
  2. **Comparison:** Wrong (red, strikethrough) vs Correct (green, bold)
  3. **Tip:** Educational explanation
  4. **Action Button:** "Tap to hear correct version" (TTS placeholder)

**Visual Design:**
```
┌─────────────────────────────────────┐
│ 💡 Quick Fix!                    ✨ │
├─────────────────────────────────────┤
│ ┌───────────────────────────────┐  │
│ │ You said:                     │  │
│ │ ❌ één                        │  │
│ │                               │  │
│ │ Better way:                   │  │
│ │ ✅ een                        │  │
│ └───────────────────────────────┘  │
├─────────────────────────────────────┤
│ ℹ️ Use 'een' for 'a/an', not 'één' │
├─────────────────────────────────────┤
│   🔊 Tap to hear correct version   │
└─────────────────────────────────────┘
```

#### ConversationScreen Integration

**Changes:**
1. Import GrammarCorrectionCard component
2. Parse correction markers from AI messages
3. Extract correction data: wrong, correct, tip
4. Remove marker from displayed message text
5. Render GrammarCorrectionCard after AI message bubble

**Parsing Logic:**
```typescript
const correctionRegex = /\{\{correction:(.*?)\|(.*?)\|(.*?)\}\}/;
const match = message.content.match(correctionRegex);

if (match) {
  correctionData = {
    wrong: match[1],
    correct: match[2],
    tip: match[3],
  };
}
```

## User Experience Flow

### Example Conversation (Dutch A1)

**User speaks:** "Ik heb één model" (incorrect: should use "een" not "één")

**AI responds:** "Goed geprobeerd! {{correction:één|een|Use 'een' for 'a/an', not 'één' (one)}} Heb je een broer of zus?"

**What user sees:**

1. **AI speech bubble (purple):**
   ```
   "Goed geprobeerd! Heb je een broer of zus?"
   ```
   (Marker removed from display)

2. **Correction card (orange) appears below with slide animation:**
   ```
   ┌─────────────────────────────────────┐
   │ 💡 Quick Fix!                    ✨ │
   ├─────────────────────────────────────┤
   │ You said:                           │
   │ ❌ één                              │
   │                                     │
   │ Better way:                         │
   │ ✅ een                              │
   ├─────────────────────────────────────┤
   │ ℹ️ Use 'een' for 'a/an', not 'één' │
   │    (one)                            │
   ├─────────────────────────────────────┤
   │   🔊 Tap to hear correct version   │
   └─────────────────────────────────────┘
   ```

3. **User feels:** ✅ Encouraged ("Goed geprobeerd!") + ✅ Learned (visual correction) + ✅ Motivated (continues conversation)

## Important: End-Session Analysis Unchanged

**This feature does NOT change:**
- Post-session sentence analysis
- Background sentence analysis
- Sentence scoring (grammar, vocabulary, complexity)
- Session summary modal
- Speaking DNA analysis

**These features remain exactly as they were.** The real-time correction is ONLY for immediate visual feedback during the conversation.

## Testing Guide

### Backend Testing

**1. Check System Instructions:**
```bash
# In backend repo
git checkout feature/realtime-grammar-correction

# Verify changes
grep -A 30 "CORRECTION MARKER FORMAT" backend/prompt_optimization_helpers.py
```

**2. Test with A1 Conversation:**
- Start a Dutch A1 conversation
- Make a grammar mistake (e.g., "Ik heb één model")
- Check backend logs for AI response containing `{{correction:...}}`

**Expected AI response format:**
```
Goed geprobeerd! {{correction:één|een|Use 'een' for 'a/an', not 'één' (one)}} Heb je een broer of zus?
```

### Mobile App Testing

**1. Visual Component Test:**
```bash
# In mobile app repo
cd /Users/alipala/github/MyTacoAIMobile
git checkout feature/realtime-grammar-correction

# Run app
npm run ios  # or npm run android
```

**2. Manual Test Cases:**

**Test Case 1: Article Error (Dutch A1)**
- User says: "Ik heb één model"
- Expected: Correction card shows "één" → "een"

**Test Case 2: Verb Conjugation (English A1)**
- User says: "She don't like coffee"
- Expected: Correction card shows "don't" → "doesn't"

**Test Case 3: Plural Form (English A1)**
- User says: "I have two brother"
- Expected: Correction card shows "brother" → "brothers"

**Test Case 4: No Error**
- User says: "Ik heb een broer"
- Expected: NO correction card (correct sentence)

**Test Case 5: Minor Error (should NOT trigger)**
- User says: "I like very much pizza" (awkward but understandable)
- Expected: NO correction card (only MAJOR errors get markers)

**3. Animation Test:**
- Correction card should slide in from bottom
- Should have haptic feedback (vibration)
- Should auto-dismiss after 8 seconds
- Should have sparkle emoji (✨) in top-right corner

**4. Styling Test:**
- Background: Warm orange/cream (#FFF7ED)
- Border: Left orange accent (#F97316)
- Wrong text: Red with strikethrough
- Correct text: Green and bold
- Play button: Purple (#8B5CF6) matching AI tutor theme

## Configuration

### Backend Environment Variables

No new environment variables required. Feature is automatically enabled for A1/A2 learners.

### Mobile App Configuration

No configuration needed. Component is self-contained.

### Internationalization

**Translation Keys Added (with fallbacks):**
```json
{
  "practice.correction.quick_fix": "Quick Fix!",
  "practice.correction.you_said": "You said:",
  "practice.correction.better_way": "Better way:",
  "practice.correction.playing": "Playing...",
  "practice.correction.hear_correct": "Tap to hear correct version"
}
```

If translations are missing, English fallbacks are used.

## Known Limitations & TODOs

### Current Limitations

1. **TTS Not Implemented:** "Tap to hear" button shows visual feedback but doesn't play audio yet
   - TODO: Add TTS endpoint in backend
   - TODO: Connect mobile app to TTS endpoint

2. **A1/A2 Only:** Feature only works for beginner levels
   - By design - advanced learners don't need this level of guidance

3. **Single Correction Per Turn:** AI will only mark ONE correction even if multiple errors exist
   - By design - prevents overwhelming the learner

### Future Enhancements

**Phase 2 Ideas:**
1. **Correction Counter:** Show "3 tips learned today!" badge
2. **Correction History:** Review all corrections from session
3. **Favorite Corrections:** Save corrections for later review
4. **Progress Tracking:** Track which error types are improving
5. **Gamification:** Award points/badges for correcting mistakes

**Phase 3 Ideas:**
1. **A/B Testing:** Test different visual designs
2. **Adaptive Frequency:** Reduce corrections as user improves
3. **Voice Recording:** Record user's original mistake for playback
4. **Contextual Examples:** Show more example sentences

## Deployment Checklist

### Backend Deployment

- [ ] Merge `feature/realtime-grammar-correction` to `main`
- [ ] Deploy to Railway (auto-deploys from main)
- [ ] Monitor logs for correction marker usage
- [ ] Check that markers are being sent correctly

### Mobile App Deployment

- [ ] Merge `feature/realtime-grammar-correction` to `main`
- [ ] Test on iOS and Android devices
- [ ] Add translation keys to all language files
- [ ] Build and submit to App Store / Play Store
- [ ] Monitor crash reports (Sentry/Firebase)

### Post-Deployment Monitoring

**Week 1:**
- Monitor correction card appearance rate
- Track user engagement (do they read tips?)
- Check for parsing errors in logs
- Gather user feedback

**Week 2-4:**
- Analyze correction types (articles, verbs, etc.)
- Measure learning impact (are users making same mistakes?)
- A/B test auto-dismiss timing (8s vs 10s vs 12s)

## Analytics Events to Track

**Recommended Events:**
1. `correction_card_shown` - When card appears
   - Properties: `language`, `level`, `error_type`, `wrong_text`, `correct_text`

2. `correction_card_dismissed` - When card auto-dismisses or manually closed
   - Properties: `method` (auto/manual), `time_visible`

3. `correction_card_audio_played` - When user taps "hear correct"
   - Properties: `correction_id`

4. `correction_repeated` - Same error made again after correction
   - Properties: `error_type`, `times_repeated`

## Support & Troubleshooting

### Issue: Correction Card Not Appearing

**Possible Causes:**
1. User is not A1/A2 level
2. AI didn't detect error as MAJOR
3. Regex parsing failed
4. Marker format incorrect

**Debug Steps:**
```typescript
// Add console logs in ConversationScreen.tsx
console.log('[CORRECTION] Message content:', message.content);
console.log('[CORRECTION] Regex match:', match);
console.log('[CORRECTION] Correction data:', correctionData);
```

### Issue: Card Appears for Minor Errors

**Solution:** Update backend instructions to be more strict about what constitutes a MAJOR error.

### Issue: Card Doesn't Auto-Dismiss

**Solution:** Check that `onDismiss` prop is being passed to GrammarCorrectionCard.

### Issue: Animations Not Smooth

**Solution:** Ensure `useNativeDriver: true` is set for all animations.

## Code Review Checklist

Before merging:
- [ ] Backend instructions are clear and unambiguous
- [ ] Mobile component follows app design patterns
- [ ] Regex parsing is robust (handles edge cases)
- [ ] Animations are smooth on both iOS and Android
- [ ] Colors match app theme
- [ ] Internationalization is complete
- [ ] No console errors or warnings
- [ ] Haptic feedback works on supported devices
- [ ] Auto-dismiss timing feels right
- [ ] Component is accessible (font sizes, contrast)

## References

**Research Sources:**
- [ELSA Speak - Real-time Grammar Correction](https://elsaspeak.com/en/product/)
- [How AI Is Transforming Language Learning in 2026](https://testprepinsight.com/resources/how-ai-is-transforming-language-learning-in-2026/)
- [Best Practices for Error Correction in Language Learning](https://www.enverson.com/ai-english-learning-app-that-corrects-mistakes)

**Related Files:**
- Backend: `backend/prompt_optimization_helpers.py`
- Mobile: `src/components/GrammarCorrectionCard.tsx`
- Mobile: `src/screens/Practice/ConversationScreen.tsx`
- Session Analysis: `backend/background_sentence_analysis.py` (UNCHANGED)

## Contact

For questions or issues:
- Backend: Check `backend/routes/realtime_routes.py` for session creation
- Mobile: Check `src/screens/Practice/ConversationScreen.tsx` for rendering
- Feature flag (if needed): Add to `backend/.env` as `ENABLE_REALTIME_CORRECTION=true`

---

**Implementation Date:** 2026-03-18
**Version:** 1.0
**Status:** ✅ Complete (TTS pending)
