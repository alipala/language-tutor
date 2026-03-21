# TaalCoach Smart Quick Replies - Fix & Enhancement
**Date:** March 21, 2026
**Purpose:** Make quick replies context-aware based on coach's response, not just user's message

---

## 🔍 PROBLEM IDENTIFIED

### Current System (WRONG):
```python
def _generate_quick_replies(context, language, user_message):
    # Only looks at USER's message
    if "progress" in user_message:
        return ["Show my progress", "Give me tips"]

    # Generic fallback
    return ["Show my progress", "What's my learning plan?"]
```

**Issues:**
1. ❌ Analyzes USER's message, not COACH's response
2. ❌ Returns only 2-3 suggestions (limit at line 1179)
3. ❌ Generic suggestions that don't match conversation context
4. ❌ Doesn't extract actionable items from coach's response

### Example of Broken Behavior:

**Conversation:**
- User: "What should I do next?"
- Coach: "Great — when you're ready, I can help you **start the next Dutch session** or **set up a quick speaking practice**."

**Current quick replies:**
- "Show my progress" ← ❌ Generic, doesn't match context
- "What's my learning plan?" ← ❌ Generic, doesn't match context

**Should be:**
- "Start my next session" ← ✅ Extracted from coach's offer
- "Set up speaking practice" ← ✅ Extracted from coach's offer
- "What's my progress?" ← ✅ Relevant follow-up
- "How is my learning plan going?" ← ✅ Contextual

---

## 💡 SOLUTION: AI-Powered Context-Aware Quick Replies

### New Approach:
1. **Analyze COACH's response** (not user's message)
2. **Extract actionable suggestions** from what coach said
3. **Use GPT to generate** 4-5 context-aware questions
4. **Fallback to smart defaults** if extraction fails

---

## 🚀 IMPLEMENTATION

### Option 1: AI-Powered Quick Reply Generation (RECOMMENDED)

**Use GPT to analyze coach's response and generate perfect quick replies:**

```python
def _generate_smart_quick_replies(
    self,
    ai_response: str,
    context: Dict,
    language: str,
    conversation_history: List[Dict] = None
) -> List[Dict[str, str]]:
    """
    Generate context-aware quick replies by analyzing coach's response.

    Uses GPT to extract actionable items and suggest natural next questions.
    """

    # Build prompt for quick reply generation
    prompt = f"""You are analyzing a conversation between a language learning coach and a student.

COACH'S LAST RESPONSE:
"{ai_response}"

USER CONTEXT:
- Learning: {context['user_profile']['target_language'].title()}
- Level: {context['user_profile']['cefr_level']}
- Has learning plan: {context['has_learning_plan']}
- Streak: {context['stats']['current_streak']} days

Generate 4-5 PERFECT quick reply suggestions that:
1. Extract actionable items from the coach's response
2. Suggest logical follow-up questions
3. Are SHORT (max 5 words)
4. Are in {language} language
5. Feel NATURAL and conversational

RULES:
- If coach offers actions ("I can help you start..."), suggest those as questions
- If coach mentions features, suggest asking about them
- If coach shares stats, suggest asking about improvement
- Always include at least one general option ("What's my progress?")

Output format (JSON):
{{
  "suggestions": [
    {{"text": "Start my next session", "reason": "coach offered to help start it"}},
    {{"text": "Set up speaking practice", "reason": "coach offered this"}},
    {{"text": "What's my progress?", "reason": "general option"}},
    {{"text": "How is my plan going?", "reason": "contextual to learning plan"}}
  ]
}}
"""

    try:
        # Call GPT to generate quick replies
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates perfect quick reply suggestions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        # Parse response
        result = json.loads(response.choices[0].message.content)
        suggestions = result.get("suggestions", [])

        # Format for quick replies
        quick_replies = [
            {"label": s["text"], "value": s["text"].lower().replace(" ", "_")}
            for s in suggestions[:5]  # Top 5
        ]

        logger.info(f"[COACH] Generated {len(quick_replies)} smart quick replies")
        return quick_replies

    except Exception as e:
        logger.warning(f"[COACH] Failed to generate smart quick replies: {e}")
        # Fallback to rule-based system
        return self._generate_fallback_quick_replies(ai_response, context, language)

def _generate_fallback_quick_replies(
    self,
    ai_response: str,
    context: Dict,
    language: str
) -> List[Dict[str, str]]:
    """
    Fallback rule-based quick reply generation.
    Analyzes coach's response using keyword extraction.
    """
    suggestions = []
    response_lower = ai_response.lower()

    # Extract action offers from coach's response
    action_patterns = {
        "start": ["start", "begin", "launch", "try"],
        "continue": ["continue", "resume", "keep going"],
        "practice": ["practice", "speaking", "conversation"],
        "challenge": ["challenge", "quiz", "game"],
        "plan": ["plan", "session", "curriculum"],
    }

    # Check what coach is offering
    if any(word in response_lower for word in action_patterns["start"]):
        if "session" in response_lower or "practice" in response_lower:
            suggestions.append({"label": "Start my next session", "value": "start_session"})

        if "speaking" in response_lower:
            suggestions.append({"label": "Set up speaking practice", "value": "setup_speaking"})

    if any(word in response_lower for word in action_patterns["continue"]):
        suggestions.append({"label": "Continue my plan", "value": "continue_plan"})

    if "challenge" in response_lower:
        suggestions.append({"label": "Try a challenge", "value": "try_challenge"})

    # Always add general follow-ups
    suggestions.append({"label": "What's my progress?", "value": "show_progress"})

    if context["has_learning_plan"]:
        suggestions.append({"label": "How is my learning plan?", "value": "check_plan"})

    if context["has_dna_profile"]:
        suggestions.append({"label": "Show my Speaking DNA", "value": "show_dna"})

    suggestions.append({"label": "What should I do next?", "value": "next_steps"})

    # Return top 5, prioritize extracted actions first
    return suggestions[:5]
```

**Update chat() method to use new system:**

```python
async def chat(
    self,
    user_id: str,
    language: str,
    user_message: str,
    conversation_history: List[Dict] = None,
    target_language: str = None
) -> Dict[str, Any]:
    # ... existing code ...

    # OLD: Generate quick replies based on user message
    # quick_replies = self._generate_quick_replies(context, language, user_message, history)

    # NEW: Generate smart quick replies based on AI response
    quick_replies = self._generate_smart_quick_replies(
        ai_response=ai_message,
        context=context,
        language=language,
        conversation_history=history
    )

    # ... rest of code ...
```

---

### Option 2: Enhanced Rule-Based System (FASTER, NO EXTRA API CALL)

**Analyze coach's response using smart pattern matching:**

```python
def _generate_smart_quick_replies_v2(
    self,
    ai_response: str,
    context: Dict,
    language: str
) -> List[Dict[str, str]]:
    """
    Generate quick replies by analyzing coach's response (rule-based).
    No extra API call, instant response.
    """
    suggestions = []
    response_lower = ai_response.lower()

    # PATTERN 1: Extract action offers
    # "I can help you start..." → "Start my next session"
    # "try a quick..." → "Try it now"

    action_mapping = {
        # Session starters
        ("start", "session"): "Start my next session",
        ("start", "dutch"): "Start Dutch practice",
        ("start", "practice"): "Start practicing",
        ("begin", "session"): "Begin my session",

        # Practice types
        ("speaking", "practice"): "Set up speaking practice",
        ("quick", "conversation"): "Quick conversation",
        ("voice", "practice"): "Voice practice now",

        # Learning plan
        ("continue", "plan"): "Continue my plan",
        ("next", "session"): "What's the next session?",
        ("learning", "plan"): "Tell me about my plan",

        # Challenges
        ("try", "challenge"): "Try a challenge",
        ("brain", "tickler"): "Try Brain Ticklers",
        ("error", "spotting"): "Try Error Spotting",

        # Progress
        ("progress", ""): "Show my progress",
        ("streak", ""): "How's my streak?",
        ("improvement", ""): "How can I improve?",
    }

    # Extract suggested actions from coach's response
    for (keyword1, keyword2), suggestion_text in action_mapping.items():
        if keyword1 in response_lower and (not keyword2 or keyword2 in response_lower):
            suggestions.append({
                "label": suggestion_text,
                "value": suggestion_text.lower().replace(" ", "_")
            })
            if len(suggestions) >= 3:
                break  # Got enough action-based suggestions

    # PATTERN 2: Add contextual follow-ups based on what coach mentioned

    # If coach mentioned user's weak area
    if context.get("has_dna_profile"):
        weak_strand = context.get("speaking_dna", {}).get("weakest_strand")
        if weak_strand and weak_strand in response_lower:
            suggestions.append({
                "label": f"How do I improve {weak_strand}?",
                "value": f"improve_{weak_strand}"
            })

    # If coach mentioned learning plan
    if "plan" in response_lower or "session" in response_lower:
        if context["has_learning_plan"]:
            suggestions.append({
                "label": "How is my plan going?",
                "value": "plan_progress"
            })

    # If coach mentioned challenges
    if "challenge" in response_lower:
        suggestions.append({
            "label": "Which challenges should I try?",
            "value": "recommend_challenges"
        })

    # PATTERN 3: Always add general helpful options
    general_options = []

    if "What's my progress?" not in [s["label"] for s in suggestions]:
        general_options.append({"label": "What's my progress?", "value": "show_progress"})

    if "What should I do next?" not in [s["label"] for s in suggestions]:
        general_options.append({"label": "What should I do next?", "value": "next_steps"})

    if context["has_dna_profile"] and len(suggestions) < 4:
        general_options.append({"label": "Show my Speaking DNA", "value": "show_dna"})

    general_options.append({"label": "Give me tips", "value": "give_tips"})

    # Combine: Extracted actions first, then contextual, then general
    all_suggestions = suggestions + general_options

    # Return top 5, ensuring variety
    return all_suggestions[:5]
```

---

## 📊 COMPARISON

### Option 1: AI-Powered (GPT-4o-mini)
**Pros:**
- ✅ Perfect context understanding
- ✅ Natural language extraction
- ✅ Handles complex responses
- ✅ Learns from conversation flow

**Cons:**
- ❌ Extra API call (adds ~200-300ms latency)
- ❌ Small cost (~$0.0001 per call)
- ❌ Dependency on GPT availability

**When to use:**
- Premium users (can afford extra latency)
- Complex responses with multiple suggestions
- When perfection matters

---

### Option 2: Enhanced Rule-Based
**Pros:**
- ✅ NO extra API call (instant)
- ✅ NO additional cost
- ✅ Reliable, predictable
- ✅ Fast (0ms overhead)

**Cons:**
- ❌ Limited pattern matching
- ❌ May miss subtle context
- ❌ Requires manual pattern updates

**When to use:**
- All users (default)
- Fast response needed
- Budget-conscious

---

## 🎯 RECOMMENDED APPROACH

### **Hybrid System** (Best of Both)

```python
async def chat(self, user_id, language, user_message, conversation_history, target_language):
    # ... generate AI response ...

    # Check subscription status
    is_premium = context['user_profile'].get('subscription_status') in ['active', 'trialing']

    if is_premium and self.use_ai_quick_replies:
        # Premium users get AI-powered quick replies
        quick_replies = self._generate_smart_quick_replies(
            ai_response=ai_message,
            context=context,
            language=language
        )
    else:
        # Free users get enhanced rule-based
        quick_replies = self._generate_smart_quick_replies_v2(
            ai_response=ai_message,
            context=context,
            language=language
        )

    # ... rest of code ...
```

**Benefits:**
- Premium users get perfect AI-powered suggestions
- Free users get fast rule-based suggestions
- No extra cost for majority of users
- Premium value differentiation

---

## 🚀 IMPLEMENTATION STEPS

### Phase 1: Implement Enhanced Rule-Based (1-2 hours)
1. Replace `_generate_quick_replies()` with `_generate_smart_quick_replies_v2()`
2. Change from analyzing user message to analyzing AI response
3. Increase limit from 3 to 5 suggestions
4. Test with real conversations

### Phase 2: Add AI-Powered Option (2-3 hours)
1. Implement `_generate_smart_quick_replies()` with GPT
2. Add hybrid system (premium vs free)
3. Add fallback to rule-based if AI fails
4. Monitor performance and costs

### Phase 3: Multi-Language Support (1-2 hours)
1. Translate action patterns to all languages
2. Ensure GPT generates replies in correct language
3. Test in all 7 supported languages

---

## 📋 TESTING SCENARIOS

### Test Case 1: Coach Offers Actions
**Coach says:**
> "Great — when you're ready, I can help you start the next Dutch session or set up a quick speaking practice."

**Expected quick replies:**
1. "Start my next session" ← Extracted from coach's offer
2. "Set up speaking practice" ← Extracted from coach's offer
3. "What's my progress?" ← General option
4. "How is my learning plan?" ← Contextual
5. "What should I do next?" ← General

---

### Test Case 2: Coach Discusses Weak Strand
**Coach says:**
> "Your fluency is at 58, which needs work. Try 5-minute daily conversations to build speaking rhythm."

**Expected quick replies:**
1. "How do I improve fluency?" ← Extracted from weak strand
2. "What exercises help fluency?" ← Contextual
3. "Start 5-minute practice" ← Extracted from suggestion
4. "What's my progress?" ← General
5. "Show my Speaking DNA" ← Contextual

---

### Test Case 3: Coach Celebrates Milestone
**Coach says:**
> "Congratulations on your 15-day streak! You're building a strong learning habit. Keep it up!"

**Expected quick replies:**
1. "How do I maintain my streak?" ← Contextual to streak
2. "What's my next goal?" ← Forward-looking
3. "What should I practice today?" ← Actionable
4. "Show my progress" ← General
5. "How can I improve?" ← General

---

## 💡 ADVANCED ENHANCEMENTS (Future)

### Conversation Flow Awareness
Track conversation state and suggest natural continuations:

```python
# If user just saw progress card
if last_card_shown == "progress":
    suggestions.append("What's my weakest area?")
    suggestions.append("How can I improve faster?")

# If user just asked about challenges
if "challenge" in last_user_message:
    suggestions.append("Which type should I try?")
    suggestions.append("What's my accuracy?")
```

### Learning from User Behavior
Track which quick replies users tap most:

```python
# Analytics
quick_reply_usage = {
    "What's my progress?": 1245,  # Most used
    "Show my DNA": 432,
    "Give me tips": 891,
}

# Prioritize popular suggestions
suggestions.sort(key=lambda s: quick_reply_usage.get(s["label"], 0), reverse=True)
```

---

## 📊 EXPECTED IMPACT

### Before Fix:
- Quick replies: 2-3 generic options
- Relevance: Low (doesn't match context)
- Usage rate: ~15% (users ignore them)
- User thinks: "These don't help me"

### After Fix:
- Quick replies: 4-5 context-aware options
- Relevance: High (extracted from coach's response)
- Usage rate: 45-55% (users rely on them)
- User thinks: "Perfect! These are exactly what I want to ask!"

### Metrics:
- **Quick reply usage:** 15% → 45-55%
- **Conversation length:** +40% (more engagement)
- **User satisfaction:** "Coach knows what I want to ask next!"
- **Typing reduction:** Users type 40% less (tap instead)

---

## ✅ SUCCESS CRITERIA

### Phase 1 Complete:
- ✅ Quick replies analyze AI response (not user message)
- ✅ 4-5 suggestions shown (up from 2-3)
- ✅ Suggestions extracted from coach's offers
- ✅ Context-aware based on conversation

### Phase 2 Complete:
- ✅ AI-powered option for premium users
- ✅ Fallback to rule-based works reliably
- ✅ Hybrid system deployed

### Overall Success:
- ✅ 45-55% quick reply usage rate
- ✅ Users say "suggestions are perfect"
- ✅ Reduced typing, more engagement
- ✅ Natural conversation flow

---

**RECOMMENDATION: Start with Phase 1 (Enhanced Rule-Based)**
- Fast to implement (1-2 hours)
- No extra costs
- Immediate impact
- Can add AI-powered later if needed

**END OF DOCUMENT**
