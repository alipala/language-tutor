# TaalCoach Smart Cards - Suggested Questions Enhancement
**Date:** March 21, 2026
**Purpose:** Add context-aware suggested questions to smart cards to make conversations easier

---

## 🎯 CORRECT UNDERSTANDING

### What User Wants:
When TaalCoach shows a smart card (Progress, DNA, Challenges, etc.), the card should display **suggested questions** that users can TAP to automatically ask TaalCoach.

### NOT This (Navigation CTAs):
```
┌────────────────────────────────┐
│ Progress Card                  │
│ Streak: 15 days               │
│                                │
│ [Start Practice →]             │ ← ❌ NO! This navigates away
└────────────────────────────────┘
```

### YES This (Suggested Questions):
```
┌────────────────────────────────┐
│ Progress Card                  │
│ Streak: 15 days               │
│                                │
│ 💬 "How can I improve my streak?" │ ← ✅ YES! Sends to TaalCoach
│ 💬 "What should I practice today?"│
│ 💬 "Show me my weak areas"     │
└────────────────────────────────┘
```

**When user taps:** Message automatically sent to TaalCoach, coach responds in the chat!

---

## 🔍 CURRENT STATE ANALYSIS

### Quick Replies (Already Implemented)
TaalCoach already has **quick replies** shown BELOW the message:

```typescript
// Current implementation
quick_replies: [
  { label: "Show my progress", value: "show_progress" },
  { label: "Give me tips", value: "give_tips" }
]
```

**Problems:**
1. ❌ Quick replies are GENERIC (same for everyone)
2. ❌ Not context-aware (don't adapt to card content)
3. ❌ Shown BELOW messages, not ON the card
4. ❌ Limited to 2-3 suggestions

### What's Missing:
**Smart cards don't have their OWN suggested questions**

When coach shows Progress Card:
- ✅ Card displays data correctly
- ❌ No card-specific questions like "Why did my streak drop?" or "How do I reach 30 days?"

---

## 💡 ENHANCEMENT PROPOSAL

### Add `suggested_questions` Field to ALL Smart Cards

**Backend sends questions WITH the card:**
```json
{
  "type": "progress_card",
  "data": {
    "streak": 15,
    "total_sessions": 45,
    "total_challenges": 87,
    "last_7_days": [...]
  },
  "suggested_questions": [
    {
      "text": "How can I improve my streak?",
      "icon": "🔥",
      "query": "give_me_tips_to_improve_my_streak"
    },
    {
      "text": "What should I practice today?",
      "icon": "📚",
      "query": "recommend_todays_practice"
    },
    {
      "text": "Show me my weak areas",
      "icon": "💪",
      "query": "show_my_weakest_skills"
    }
  ]
}
```

**Mobile renders questions ON the card:**
```typescript
<View style={styles.card}>
  {/* Card content */}
  <ProgressCardContent data={data} />

  {/* Suggested questions */}
  <View style={styles.suggestedQuestions}>
    {card.suggested_questions.map(q => (
      <TouchableOpacity
        key={q.query}
        style={styles.questionChip}
        onPress={() => sendMessageToCoach(q.text)}
      >
        <Text>{q.icon} {q.text}</Text>
      </TouchableOpacity>
    ))}
  </View>
</View>
```

---

## 📋 CONTEXT-AWARE QUESTION SUGGESTIONS

### 1. Progress Card - Suggested Questions

**Base questions (always show):**
```json
[
  {
    "text": "How can I improve faster?",
    "icon": "🚀",
    "query": "tips_for_faster_improvement"
  },
  {
    "text": "What should I practice today?",
    "icon": "📚",
    "query": "recommend_todays_practice"
  }
]
```

**Context-aware additions:**

**If streak > 7 days:**
```json
{
  "text": "How do I maintain my streak?",
  "icon": "🔥",
  "query": "tips_to_maintain_streak"
}
```

**If streak = 0:**
```json
{
  "text": "How do I build a streak?",
  "icon": "🔥",
  "query": "how_to_start_streak"
}
```

**If sessions < 10:**
```json
{
  "text": "What's the best way to get started?",
  "icon": "🎯",
  "query": "beginner_guidance"
}
```

**If sessions > 50:**
```json
{
  "text": "Am I on track to fluency?",
  "icon": "📈",
  "query": "fluency_progress_check"
}
```

**If last_7_days shows decline:**
```json
{
  "text": "Why did my activity drop?",
  "icon": "📉",
  "query": "explain_activity_decline"
}
```

---

### 2. DNA Card - Suggested Questions

**Base questions:**
```json
[
  {
    "text": "How do I improve my weakest strand?",
    "icon": "💪",
    "query": "improve_weak_strand"
  },
  {
    "text": "What does my DNA mean?",
    "icon": "🧬",
    "query": "explain_my_dna"
  }
]
```

**Context-aware additions:**

**If has weak strand (score < 60):**
```json
{
  "text": "Why is my {strand} low?",
  "icon": "🤔",
  "query": "explain_low_{strand}"
}
// Example: "Why is my fluency low?"
```

**If has strong strand (score > 80):**
```json
{
  "text": "How can I use my {strand} strength?",
  "icon": "⭐",
  "query": "leverage_{strand}_strength"
}
// Example: "How can I use my accuracy strength?"
```

**If confidence < 60:**
```json
{
  "text": "How can I sound more confident?",
  "icon": "🗣️",
  "query": "confidence_building_tips"
}
```

**If fluency < 60:**
```json
{
  "text": "What exercises improve fluency?",
  "icon": "🏃",
  "query": "fluency_exercises"
}
```

**If vocabulary < 70:**
```json
{
  "text": "How do I expand my vocabulary?",
  "icon": "📖",
  "query": "vocabulary_expansion_tips"
}
```

**If recent breakthrough detected:**
```json
{
  "text": "Tell me about my breakthrough!",
  "icon": "🎉",
  "query": "explain_breakthrough"
}
```

---

### 3. Learning Plans Card - Suggested Questions

**Base questions:**
```json
[
  {
    "text": "What's next in my plan?",
    "icon": "📋",
    "query": "next_plan_session"
  },
  {
    "text": "How is my plan going?",
    "icon": "📊",
    "query": "plan_progress_review"
  }
]
```

**Context-aware additions:**

**If plan progress < 30%:**
```json
{
  "text": "How do I stay motivated?",
  "icon": "💪",
  "query": "motivation_tips"
}
```

**If plan progress > 70%:**
```json
{
  "text": "What happens after I finish?",
  "icon": "🎓",
  "query": "post_plan_guidance"
}
```

**If plan progress = 100%:**
```json
{
  "text": "Can you create my next plan?",
  "icon": "🚀",
  "query": "create_next_plan"
}
```

**If multiple plans active:**
```json
{
  "text": "Which plan should I focus on?",
  "icon": "🎯",
  "query": "plan_priority_advice"
}
```

**If no plans:**
```json
{
  "text": "Should I create a learning plan?",
  "icon": "📚",
  "query": "explain_learning_plans"
}
```

---

### 4. Challenge Stats Card - Suggested Questions

**Base questions:**
```json
[
  {
    "text": "Which challenges should I try?",
    "icon": "🎮",
    "query": "recommend_challenges"
  },
  {
    "text": "How can I improve my accuracy?",
    "icon": "🎯",
    "query": "challenge_accuracy_tips"
  }
]
```

**Context-aware additions:**

**If accuracy > 85%:**
```json
{
  "text": "Should I try harder challenges?",
  "icon": "🧠",
  "query": "level_up_challenges"
}
```

**If accuracy < 70%:**
```json
{
  "text": "Why am I getting many wrong?",
  "icon": "🤔",
  "query": "explain_low_accuracy"
}
```

**If specific type has low accuracy:**
```json
{
  "text": "How do I get better at {type}?",
  "icon": "📈",
  "query": "improve_{type}_challenges"
}
// Example: "How do I get better at Error Spotting?"
```

**If close to milestone (95/100):**
```json
{
  "text": "How many until my next badge?",
  "icon": "🏆",
  "query": "milestone_progress"
}
```

**If low XP:**
```json
{
  "text": "How do I earn more XP?",
  "icon": "⭐",
  "query": "xp_earning_tips"
}
```

---

### 5. Celebration Card - Suggested Questions

**When celebrating achievement:**
```json
[
  {
    "text": "What's my next goal?",
    "icon": "🎯",
    "query": "next_goal_suggestion"
  },
  {
    "text": "How do I keep this up?",
    "icon": "🔥",
    "query": "momentum_tips"
  },
  {
    "text": "Can you summarize my progress?",
    "icon": "📊",
    "query": "progress_summary"
  }
]
```

---

## 🚀 IMPLEMENTATION PLAN

### Phase 1: Backend - Add Suggested Questions Logic (1-2 days)

**Step 1:** Create question generator for each card type

```python
# services/coach_service_optimized.py

def _generate_card_questions(
    self,
    card_type: str,
    context: Dict,
    language: str
) -> List[Dict[str, str]]:
    """
    Generate context-aware suggested questions for a card.

    Returns list of questions with:
    - text: Display text for user
    - icon: Emoji icon
    - query: Internal identifier (optional)
    """
    if card_type == "progress":
        return self._generate_progress_questions(context, language)
    elif card_type == "dna":
        return self._generate_dna_questions(context, language)
    elif card_type == "challenges":
        return self._generate_challenge_questions(context, language)
    elif card_type == "learning_plans":
        return self._generate_learning_plan_questions(context, language)
    else:
        return []

def _generate_progress_questions(self, context: Dict, language: str) -> List[Dict]:
    """Generate progress card questions based on user context"""
    questions = []

    # Base questions (always show)
    questions.extend([
        {"text": "How can I improve faster?", "icon": "🚀"},
        {"text": "What should I practice today?", "icon": "📚"}
    ])

    # Context-aware questions
    streak = context['stats']['current_streak']

    if streak > 7:
        questions.append({
            "text": "How do I maintain my streak?",
            "icon": "🔥"
        })
    elif streak == 0:
        questions.append({
            "text": "How do I build a streak?",
            "icon": "🔥"
        })

    sessions = context['stats']['total_sessions']

    if sessions < 10:
        questions.append({
            "text": "What's the best way to get started?",
            "icon": "🎯"
        })
    elif sessions > 50:
        questions.append({
            "text": "Am I on track to fluency?",
            "icon": "📈"
        })

    # Check for activity decline
    if self._has_activity_decline(context['stats']['last_7_days']):
        questions.append({
            "text": "Why did my activity drop?",
            "icon": "📉"
        })

    # Return top 3-4 questions
    return questions[:4]

def _generate_dna_questions(self, context: Dict, language: str) -> List[Dict]:
    """Generate DNA card questions based on speaking profile"""
    questions = []

    # Base questions
    questions.extend([
        {"text": "How do I improve my weakest strand?", "icon": "💪"},
        {"text": "What does my DNA mean?", "icon": "🧬"}
    ])

    if not context.get('has_dna_profile'):
        return questions

    dna = context['speaking_dna']
    weak_strand = dna.get('weakest_strand')
    weak_score = dna.get('weakest_score', 0)

    # Weak strand specific question
    if weak_score < 60:
        strand_name = weak_strand.title()
        questions.append({
            "text": f"Why is my {strand_name} low?",
            "icon": "🤔"
        })

        # Strand-specific improvement tips
        if weak_strand == 'confidence':
            questions.append({
                "text": "How can I sound more confident?",
                "icon": "🗣️"
            })
        elif weak_strand == 'fluency':
            questions.append({
                "text": "What exercises improve fluency?",
                "icon": "🏃"
            })
        elif weak_strand == 'vocabulary':
            questions.append({
                "text": "How do I expand my vocabulary?",
                "icon": "📖"
            })

    # Strong strand question
    strong_strand = dna.get('strongest_strand')
    strong_score = dna.get('strongest_score', 0)

    if strong_score > 80:
        questions.append({
            "text": f"How can I use my {strong_strand.title()} strength?",
            "icon": "⭐"
        })

    # Breakthrough detection
    if context.get('recent_breakthrough'):
        questions.append({
            "text": "Tell me about my breakthrough!",
            "icon": "🎉"
        })

    return questions[:4]

def _generate_challenge_questions(self, context: Dict, language: str) -> List[Dict]:
    """Generate challenge card questions based on stats"""
    questions = []

    # Base questions
    questions.extend([
        {"text": "Which challenges should I try?", "icon": "🎮"},
        {"text": "How can I improve my accuracy?", "icon": "🎯"}
    ])

    challenge_details = context.get('challenge_details', {})
    accuracy = challenge_details.get('accuracy', 0)
    total = challenge_details.get('total', 0)

    # High accuracy
    if accuracy > 85:
        questions.append({
            "text": "Should I try harder challenges?",
            "icon": "🧠"
        })

    # Low accuracy
    if accuracy < 70 and total > 10:
        questions.append({
            "text": "Why am I getting many wrong?",
            "icon": "🤔"
        })

    # Find weakest challenge type
    by_type = challenge_details.get('by_type', {})
    if by_type:
        weakest_type = min(by_type.items(), key=lambda x: x[1].get('accuracy', 100))
        if weakest_type[1].get('accuracy', 0) < 75:
            type_name = weakest_type[0].replace('_', ' ').title()
            questions.append({
                "text": f"How do I improve at {type_name}?",
                "icon": "📈"
            })

    # Milestone check
    if total >= 95 and total < 100:
        questions.append({
            "text": "How many until my next badge?",
            "icon": "🏆"
        })

    return questions[:4]

def _generate_learning_plan_questions(self, context: Dict, language: str) -> List[Dict]:
    """Generate learning plan questions"""
    questions = []

    # Base questions
    questions.extend([
        {"text": "What's next in my plan?", "icon": "📋"},
        {"text": "How is my plan going?", "icon": "📊"}
    ])

    plans = context.get('learning_plans', [])

    if not plans:
        questions.append({
            "text": "Should I create a learning plan?",
            "icon": "📚"
        })
        return questions

    # Get most active plan
    active_plan = plans[0] if plans else None
    if not active_plan:
        return questions

    progress = active_plan.get('progress_percentage', 0)

    # Low progress
    if progress < 30:
        questions.append({
            "text": "How do I stay motivated?",
            "icon": "💪"
        })

    # High progress
    elif progress > 70:
        questions.append({
            "text": "What happens after I finish?",
            "icon": "🎓"
        })

    # Complete
    elif progress >= 100:
        questions.append({
            "text": "Can you create my next plan?",
            "icon": "🚀"
        })

    # Multiple plans
    if len(plans) > 1:
        questions.append({
            "text": "Which plan should I focus on?",
            "icon": "🎯"
        })

    return questions[:4]

def _has_activity_decline(self, last_7_days: List[Dict]) -> bool:
    """Check if user's activity is declining"""
    if len(last_7_days) < 7:
        return False

    # Compare last 3 days to previous 4 days
    recent_avg = sum(day.get('sessions', 0) for day in last_7_days[:3]) / 3
    previous_avg = sum(day.get('sessions', 0) for day in last_7_days[3:7]) / 4

    return recent_avg < previous_avg * 0.5  # 50% decline
```

**Step 2:** Update card generation to include questions

```python
# In _parse_response_with_card()

if show_card == "progress":
    if context["stats"]["total_sessions"] > 0 or context["stats"]["current_streak"] > 0:
        messages.append({
            "type": "progress_card",
            "data": {
                "streak": context["stats"]["current_streak"],
                "total_sessions": context["stats"]["total_sessions"],
                "total_challenges": context["stats"]["total_challenges"],
                "last_7_days": context["stats"]["last_7_days"]
            },
            "suggested_questions": self._generate_card_questions("progress", context, language),  # NEW
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
```

---

### Phase 2: Mobile - Render Suggested Questions (1-2 days)

**Step 1:** Update card components to show questions

```typescript
// src/components/TaalCoach/cards/ProgressCard.tsx

interface SuggestedQuestion {
  text: string;
  icon: string;
  query?: string;
}

interface ProgressCardProps {
  data: {
    streak: number;
    total_sessions: number;
    total_challenges: number;
    last_7_days: any[];
  };
  suggested_questions?: SuggestedQuestion[];
  onQuestionTap: (questionText: string) => void;
}

export function ProgressCard({ data, suggested_questions, onQuestionTap }: ProgressCardProps) {
  return (
    <View style={styles.card}>
      {/* Existing card content */}
      <View style={styles.content}>
        <Text style={styles.title}>📊 Your Progress</Text>
        <Text style={styles.stat}>🔥 {data.streak} day streak</Text>
        <Text style={styles.stat}>📚 {data.total_sessions} sessions</Text>
        <Text style={styles.stat}>🎮 {data.total_challenges} challenges</Text>
      </View>

      {/* NEW: Suggested questions */}
      {suggested_questions && suggested_questions.length > 0 && (
        <View style={styles.suggestedQuestions}>
          <Text style={styles.questionsLabel}>💬 Ask me:</Text>
          {suggested_questions.map((q, idx) => (
            <TouchableOpacity
              key={idx}
              style={styles.questionChip}
              onPress={() => onQuestionTap(q.text)}
              activeOpacity={0.7}
            >
              <Text style={styles.questionText}>
                {q.icon} {q.text}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.cardBackground,
    borderRadius: 16,
    padding: 16,
    marginVertical: 8,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  content: {
    marginBottom: 12,
  },
  suggestedQuestions: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: colors.divider,
  },
  questionsLabel: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 8,
    fontWeight: '600',
  },
  questionChip: {
    backgroundColor: colors.chipBackground,
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: colors.chipBorder,
  },
  questionText: {
    fontSize: 14,
    color: colors.text,
    fontWeight: '500',
  },
});
```

**Step 2:** Update CoachModal to handle question taps

```typescript
// src/components/TaalCoach/CoachModal.tsx

const handleQuestionTap = (questionText: string) => {
  // Send the question to coach
  sendMessage(questionText);

  // Optional: Haptic feedback
  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
};

// In render:
case 'progress_card':
  return (
    <ProgressCard
      key={idx}
      data={richMsg.data}
      suggested_questions={richMsg.suggested_questions}
      onQuestionTap={handleQuestionTap}
    />
  );

case 'dna_card':
  return (
    <DNACard
      key={idx}
      data={richMsg.data}
      suggested_questions={richMsg.suggested_questions}
      onQuestionTap={handleQuestionTap}
    />
  );
```

---

### Phase 3: Multi-Language Support (1 day)

**Translate questions to all supported languages:**

```python
# Question translations
CARD_QUESTIONS = {
    "en": {
        "improve_faster": "How can I improve faster?",
        "practice_today": "What should I practice today?",
        "maintain_streak": "How do I maintain my streak?",
        "build_streak": "How do I build a streak?",
        # ... more
    },
    "tr": {
        "improve_faster": "Nasıl daha hızlı gelişebilirim?",
        "practice_today": "Bugün ne çalışmalıyım?",
        "maintain_streak": "Serimimi nasıl koruyabilirim?",
        "build_streak": "Nasıl seri oluşturabilirim?",
        # ... more
    },
    "es": {
        "improve_faster": "¿Cómo puedo mejorar más rápido?",
        "practice_today": "¿Qué debo practicar hoy?",
        # ... more
    }
}

def _get_question_text(self, key: str, language: str, **kwargs) -> str:
    """Get translated question text"""
    translations = CARD_QUESTIONS.get(language, CARD_QUESTIONS["en"])
    text = translations.get(key, CARD_QUESTIONS["en"].get(key, key))
    return text.format(**kwargs) if kwargs else text
```

---

## 📊 EXPECTED IMPACT

### Before Enhancement:
- Cards show data only
- Users read cards and think "okay... now what?"
- Quick replies below are generic
- User has to TYPE questions
- Engagement: Low

### After Enhancement:
- Cards show data + 3-4 context-aware questions
- Users see: "Oh, I can ask about my weak fluency!"
- Questions are personalized to their situation
- ONE TAP to ask coach
- Engagement: HIGH

### Metrics:
- **Question usage rate:** 40-50% (users tap suggested questions)
- **Conversation depth:** +30% (more back-and-forth with coach)
- **User satisfaction:** "Coach knows exactly what I want to ask!"
- **Feature discovery:** Users learn about features through questions

---

## ✅ SUCCESS CRITERIA

### Phase 1 Complete:
- ✅ Backend generates 3-4 context-aware questions per card
- ✅ Questions adapt to user's situation (streak, accuracy, progress)
- ✅ Questions sent with card data

### Phase 2 Complete:
- ✅ All card components render suggested questions
- ✅ Users can tap questions to send to coach
- ✅ Smooth UX (haptic feedback, visual feedback)

### Phase 3 Complete:
- ✅ Questions translated to all 7 languages
- ✅ Questions maintain context across languages

### Overall Success:
- ✅ 40-50% of users tap suggested questions
- ✅ Conversation length increases 30%
- ✅ Users discover features organically
- ✅ "Coach makes it easy to know what to ask!"

---

## 🎯 NEXT STEPS

### This Week:
1. **Implement Phase 1** (Backend question generation)
   - 4-6 hours effort
   - Add `_generate_card_questions()` methods
   - Update card data to include `suggested_questions`

### Next Week:
2. **Implement Phase 2** (Mobile rendering)
   - 4-6 hours effort
   - Update all card components
   - Add question tap handling

### Following Week:
3. **Implement Phase 3** (Multi-language)
   - 2-3 hours effort
   - Translate questions
   - Test in all languages

**Total Effort:** 10-15 hours
**Expected Impact:** HIGH - Makes coach conversations much easier and more engaging

---

**END OF ENHANCEMENT PLAN**
