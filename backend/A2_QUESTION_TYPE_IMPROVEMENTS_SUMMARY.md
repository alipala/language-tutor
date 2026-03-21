# A2 Question Type Improvements - Implementation Summary

## 🎯 **PROBLEM SOLVED**

**Original Issue:** The AI tutor was treating A2 learners too similarly to A1, asking 50% YES/NO questions ("Coffee? Yes or no?", "Is it good?") which doesn't make sense for A2 level learners who can handle more complex language production.

**Solution:** Implemented context-aware question distributions that reduce YES/NO reliance and increase WH questions, CHOICE questions, and introduce scaffolded OPEN-ENDED questions for A2 learners.

---

## ✅ **ALL CHANGES IMPLEMENTED** (8/8 Tasks Complete)

### **Phase 1: Question Type Distribution (High Priority)**

#### 1. ✅ Context-Aware Question Types for A2
**File:** `prompt_optimization_helpers.py` - `build_beginner_question_types()`

**Changes:**
- Added `context_type` parameter to distinguish between learning_plan, freestyle, news, and general contexts
- Replaced single A2 distribution with **4 context-specific distributions:**

**A2 Learning Plan (Structured Practice):**
- 30% SIMPLE WH questions (↑ from 20%)
- 30% YES/NO questions (↓ from 50%)
- 25% CHOICE questions
- 15% OPEN-ENDED questions (NEW)

**A2 Freestyle (Exploration):**
- 35% SIMPLE WH questions (↑ from 20%)
- 25% YES/NO questions (↓ from 50%)
- 20% CHOICE questions
- 20% OPEN-ENDED questions (NEW)

**A2 News (Comprehension):**
- 30% SIMPLE WH questions (↑ from 20%)
- 35% YES/NO questions (↓ from 50%)
- 25% CHOICE questions
- 10% SIMPLE OPINION questions (NEW)

**A1 Unchanged:**
- 70% YES/NO, 20% CHOICE, 10% SIMPLE WH (kept as-is)

**Impact:** A2 learners now get 30-35% WH questions instead of just 20%, encouraging language production rather than single-word responses.

---

#### 2. ✅ Differentiated Scaffolding Strategies
**File:** `prompt_optimization_helpers.py` - `build_beginner_scaffolding()`

**Changes:**
- Split function into A1 and A2 sections with completely different strategies
- **A1:** Heavy scaffolding with quick simplification to YES/NO
- **A2:** "Build UP, not DOWN" philosophy with 5 strategies:

**A2 Scaffolding Principles:**
1. **WH Questions with Vocabulary Support**
   - "What did you eat? Bread? Eggs? Coffee?"
   - Keeps WH question, adds vocabulary hints

2. **Past Tense Scaffolding**
   - Encourages past tense: "What did you do yesterday?"
   - Provides past tense options if struggling

3. **Opinion Questions with "Why"**
   - "Do you like coffee? Why?"
   - Builds simple justifications

4. **Build on Responses**
   - Student: "I eat breakfast" → "You ATE breakfast. What did you eat?"
   - Follow with WH question, not simplify to YES/NO

5. **Response Quality Triggers**
   - 3+ word answers → maintain WH questions
   - 1-2 word answers → add more vocabulary
   - Only simplify to YES/NO as last resort

**Impact:** A2 students get more opportunities to produce language before simplification.

---

#### 3. ✅ A2 Open-Ended Question Scaffolding
**File:** `prompt_optimization_helpers.py` - `build_a2_open_ended_scaffolding()` (NEW FUNCTION)

**Changes:**
- Created dedicated function for A2 open-ended question guidance (180+ lines)
- Provides when/how to use open-ended questions effectively

**Key Guidelines:**
- **When to use:** After 2-3 successful WH answers, student gives 3+ word responses
- **When NOT to use:** Start of conversation, student struggles with WH questions
- **How to scaffold:** Question + WH follow-up + vocabulary support
  - "Tell me about your weekend. What did you do?"
  - If struggling: "Did you work? Relax? See friends?"

**Examples:**
- "Describe your home. What is it like?" → "Is it big or small? How many rooms?"
- "Talk about your job." → "Where do you work? What are your hours?"

**Success Criteria:**
- 2-3 sentences = SUCCESS
- 1 sentence = PARTIAL SUCCESS (ask follow-up WH)
- 1 word/silence = NOT READY (return to WH questions)

**Impact:** A2 gets practice with narrative skills (bridge to B1) while maintaining appropriate support.

---

### **Phase 2: Context-Specific Templates (Medium Priority)**

#### 4. ✅ Learning Plan Context Updates
**File:** `prompt_optimization_helpers.py` - `build_beginner_instructions()` learning_plan_context

**Changes:**
- Added level-specific question guidance for learning plans
- **A1:** "Ask ONLY simple yes/no or choice questions"
- **A2:**
  ```
  - 30% SIMPLE WH: "What did you...?", "Where do you...?"
  - 30% YES/NO: "Do you like...?"
  - 25% CHOICE: "Coffee or tea?"
  - 15% OPEN-ENDED: "Tell me about...", "Describe your..."
  - Use past tense questions
  - Follow YES/NO with "Why?" occasionally
  - Encourage complete sentences
  ```

**Impact:** Learning plan sessions for A2 now focus on WH questions and past tense practice.

---

#### 5. ✅ Topic/Freestyle Context Updates
**File:** `prompt_optimization_helpers.py` - topic_context (user_prompt and predefined topics)

**Changes:**
- Updated both custom topics (user_prompt) and predefined topics (work, food, etc.)
- **A1:** "Ask simple questions: 'Is it good or bad?', 'Yes or no?'"
- **A2:**
  ```
  FREESTYLE distribution:
  - 35% SIMPLE WH: "What do you think?", "What did you hear?"
  - 25% YES/NO: "Do you like it?", "Is this interesting?"
  - 20% CHOICE: "Good or bad?", "Interesting or boring?"
  - 20% OPEN-ENDED: "Tell me about...", "Describe what you know."
  - Use past tense, ask for opinions with "Why?"
  - Encourage complete sentences
  ```

**Conversation Flow A2:**
- Message 1: Simple WH or YES/NO
- Message 2-4: WH questions ("What do you think?")
- Message 5-7: Mix WH, CHOICE, opinion ("Do you like it? Why?")
- Message 8-10: Try 1-2 open-ended if confident
- Message 10+: Continue with variety

**Impact:** Freestyle practice now provides maximum variety and language production opportunities.

---

#### 6. ✅ News Context Updates
**File:** `prompt_optimization_helpers.py` - news_article_context

**Changes:**
- **A1:** "Ask ONLY yes/no or choice questions"
- **A2:**
  ```
  NEWS distribution:
  - 30% SIMPLE WH: "What is this about?", "Where did this happen?", "When?", "Who?"
  - 35% YES/NO: "Do you understand?", "Is this about politics?"
  - 25% CHOICE: "Good news or bad news?", "Health or economy?"
  - 10% SIMPLE OPINION: "What do you think?", "Good or bad? Why?"
  - Use past tense for recent events
  - Simplify complex ideas (politics → "people and government")
  - Keep opinions simple, scaffold with "because..."
  ```

**Impact:** News practice focuses on comprehension WH questions while maintaining A2 simplicity.

---

### **Phase 3: Examples & Integration (Enhancement)**

#### 7. ✅ A2 Conversation Flow Examples
**File:** `prompt_optimization_helpers.py` - `build_beginner_conversation_flow()`

**Changes:**
- Updated A2 Phase 2 structure percentages
- Rewrote example exchange to show WH question progression:

**NEW Example:**
```
You: "What did you eat for breakfast today?"
Student: "I eat bread"
You: "You ATE bread. Good! What did you drink?"
[WH question instead of YES/NO]
Student: "Coffee"
You: "Coffee! Why do you like coffee?"
[Opinion question]
Student: "It's good"
You: "Yes, coffee is good! When do you usually drink it? Morning or evening?"
[CHOICE question]
```

**Updated scaffolding strategy:**
- First: Provide vocabulary with WH question ("What did you eat? Bread? Eggs?")
- Second: Offer choices ("Bread or rice?")
- Last resort: Make it YES/NO ("Did you eat bread?")

**Impact:** Examples now demonstrate the "build UP" philosophy with varied question types.

---

#### 8. ✅ Main Integration
**File:** `prompt_optimization_helpers.py` - `build_beginner_instructions()`

**Changes:**
- Added context type detection logic:
  ```python
  context_type = "general"
  if learning_plan_data: context_type = "learning_plan"
  elif news_context: context_type = "news"
  elif user_prompt or topic: context_type = "freestyle"
  ```
- Pass context_type to `build_beginner_question_types(level, context_type)`
- Added A2-only open-ended scaffolding section:
  ```python
  if level.upper() == 'A2':
      open_ended_scaffolding = build_a2_open_ended_scaffolding()
  ```
- Integrated into final instructions template

**Impact:** All components work together seamlessly with proper context awareness.

---

## 📊 **COMPARISON: BEFORE vs AFTER**

### **A2 Learning Plan Session - BEFORE**
```
Tutor: "Do you like coffee?"
Student: "Yes"
Tutor: "Coffee? Yes or no?"  ← PROBLEM: Simplifying unnecessarily
Student: "Yes"
Tutor: "Good or bad?"
Student: "Good"
```
- 50% YES/NO questions
- Student produces minimal language (single words)
- No past tense practice
- No justifications

### **A2 Learning Plan Session - AFTER**
```
Tutor: "What did you eat for breakfast?"  ← WH question
Student: "I eat bread"
Tutor: "You ATE bread. What did you drink?"  ← Corrects + WH follow-up
Student: "Coffee"
Tutor: "Coffee! Why do you like coffee?"  ← Opinion question
Student: "It's good"
Tutor: "Yes! When do you drink it? Morning or evening?"  ← CHOICE
Student: "Morning"
Tutor: "Tell me about your morning routine."  ← OPEN-ENDED
```
- 30% WH, 30% YES/NO, 25% CHOICE, 15% OPEN
- Student produces more language
- Past tense practice
- Simple justifications

---

### **A2 Freestyle Practice - BEFORE**
```
Tutor: "Do you like your job?"
Student: "Yes"
Tutor: "Is it good?"  ← PROBLEM: Repetitive YES/NO
Student: "Yes"
Tutor: "Happy? Yes or no?"
Student: "Yes"
```
- 50% YES/NO
- Boring, repetitive
- No exploration

### **A2 Freestyle Practice - AFTER**
```
Tutor: "What do you like about your job?"  ← WH question (35%)
Student: "The people"
Tutor: "The people are nice! Where do you work?"  ← WH follow-up
Student: "Office"
Tutor: "In an office! Tell me about a typical day."  ← OPEN-ENDED (20%)
Student: "I start 9. I work computer."
Tutor: "You start at 9 and work on a computer. What projects do you work on?"
```
- 35% WH, 25% YES/NO, 20% CHOICE, 20% OPEN
- Varied, engaging
- Natural conversation flow

---

### **A2 News Practice - BEFORE**
```
Tutor: "This article is about politics. Good or bad?"
Student: "Bad"
Tutor: "Bad? Yes or no?"  ← PROBLEM: Pointless simplification
Student: "Bad"
Tutor: "You like? Yes or no?"
Student: "No"
```
- 50% YES/NO
- Doesn't test comprehension
- No content engagement

### **A2 News Practice - AFTER**
```
Tutor: "What is this article about?"  ← WH comprehension (30%)
Student: "Politics"
Tutor: "Yes, politics! Where did this happen?"  ← WH follow-up
Student: "England"
Tutor: "In England! What do you think about this? Good or bad?"  ← Opinion (10%)
Student: "Bad"
Tutor: "You think it's bad. Why?"  ← Follow-up for justification
Student: "People angry"
Tutor: "Yes, people are angry. Do you think this will change?"
```
- 30% WH, 35% YES/NO, 25% CHOICE, 10% OPINION
- Tests comprehension
- Engages with content
- Encourages simple opinions

---

## 🎯 **KEY IMPROVEMENTS BY THE NUMBERS**

| Metric | A1 (Unchanged) | A2 Before | A2 After (Learning Plan) | A2 After (Freestyle) | A2 After (News) |
|--------|----------------|-----------|-------------------------|---------------------|-----------------|
| **YES/NO %** | 70% | 50% | **30%** ↓ | **25%** ↓ | **35%** |
| **WH %** | 10% | 20% | **30%** ↑ | **35%** ↑ | **30%** ↑ |
| **CHOICE %** | 20% | 30% | **25%** | **20%** | **25%** |
| **OPEN-ENDED %** | 0% | 0% | **15%** NEW | **20%** NEW | **10%** NEW |
| **Expected Response Length** | 1 word | 1-2 words | 3-5 words | 3-7 words | 2-5 words |
| **Past Tense Practice** | Minimal | Low | High | High | Medium |
| **Opinion Questions** | None | None | Some | Frequent | Some |

---

## 🚀 **TESTING INSTRUCTIONS**

### **How to Test:**

1. **Start Backend:**
   ```bash
   cd /Users/alipala/CascadeProjects/language-tutor/backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Test Scenarios:**

#### **Scenario 1: A2 Learning Plan**
- Create/use A2 learning plan session
- **Expected behavior:**
  - AI asks mix of WH questions ("What did you...?", "Where do you...?")
  - Reduces YES/NO questions
  - Follows up with "Why?" occasionally
  - Tries 1-2 open-ended questions if student is confident

#### **Scenario 2: A2 Freestyle Practice**
- Start freestyle conversation (no specific topic or custom topic)
- **Expected behavior:**
  - AI leads with WH questions most of the time
  - Variety in question types
  - Asks for simple opinions
  - Attempts open-ended questions ("Tell me about...")

#### **Scenario 3: A2 News Article**
- Practice with a news article
- **Expected behavior:**
  - AI asks comprehension WH questions ("What is this about?", "Where?", "When?")
  - Tests understanding with YES/NO checks
  - Asks for simple opinions ("Good or bad? Why?")

#### **Scenario 4: A1 (Control - Should NOT Change)**
- Test A1 learning plan or freestyle
- **Expected behavior:**
  - Still 70% YES/NO questions
  - Still 20% CHOICE questions
  - Still 10% WH questions
  - No open-ended questions
  - Heavy emoji usage

### **What to Monitor:**

✅ **Question Distribution:**
- Count questions in a 5-minute session (typically 8-12 questions)
- A2 should have more WH than YES/NO in freestyle/learning plan
- A2 should attempt 1-2 open-ended questions

✅ **Scaffolding Behavior:**
- When A2 student gives 1-word answer, does AI:
  1. First: Add vocabulary to WH question?
  2. Second: Offer choices?
  3. Last: Simplify to YES/NO?
- Does it build UP instead of DOWN?

✅ **Past Tense Usage:**
- Does A2 AI ask past tense questions? ("What did you...?")
- Does it encourage past tense responses?

✅ **Open-Ended Questions:**
- Does A2 AI attempt "Tell me about..." style questions?
- Does it scaffold properly if student struggles?
- Does it return to WH questions if open-ended doesn't work?

❌ **A1 Should NOT Change:**
- Still very simple YES/NO heavy
- Still uses emojis extensively
- No open-ended questions

---

## 📝 **FILES MODIFIED**

| File | Lines Changed | Summary |
|------|---------------|---------|
| `prompt_optimization_helpers.py` | ~500 lines | All 8 improvements implemented |

**Key Functions Modified:**
- `build_beginner_question_types()` - Added context parameter, context-aware distributions
- `build_beginner_scaffolding()` - Split A1/A2 with distinct strategies
- `build_beginner_instructions()` - Integration and context detection

**New Functions Added:**
- `build_a2_open_ended_scaffolding()` - 180+ lines of open-ended question guidance

---

## ⚠️ **POTENTIAL ISSUES TO WATCH FOR**

### **Issue 1: GPT Realtime Mini May Not Follow Exact Percentages**
**Expected:** Model will approximate (±10-15% variance)
**Mitigation:** Percentages are weights, not hard targets. Over 10 questions, distribution will average out.

### **Issue 2: Open-Ended Questions May Be Too Challenging**
**Symptom:** A2 students consistently give 1-word answers or go silent
**Solution:** Reduce open-ended % from 15-20% to 10% if needed

### **Issue 3: Context Detection May Fail**
**Symptom:** Wrong distribution applied (news gets freestyle distribution)
**Solution:** Check context_type logic in `build_beginner_instructions()`

### **Issue 4: A1 Students Accidentally Get A2 Instructions**
**Symptom:** A1 gets WH questions and open-ended
**Solution:** Verify level.upper() == 'A1' vs 'A2' conditionals

---

## 🎉 **EXPECTED OUTCOMES**

### **User Experience:**
- **A2 learners:** More engaging conversations, more language production, less boring
- **A1 learners:** No change (still heavily scaffolded, as appropriate)

### **Metrics to Track:**
- **Average response length (A2):** Should increase 30-50% (from 1-2 words to 3-5 words)
- **WH question success rate (A2):** Should be >70% (students answer WH questions successfully)
- **User satisfaction (A2):** Monitor ratings - should maintain or improve
- **Completion rate:** Should remain stable (not too difficult)

### **Success Indicators:**
✅ A2 students produce more complete sentences
✅ A2 students practice past tense naturally
✅ A2 students give simple opinions/justifications
✅ Conversations feel more natural and varied
✅ A1 students still get appropriate scaffolding (no regression)

---

## 🔧 **ROLLBACK PLAN**

If issues arise, you can revert by:

1. **Partial Rollback (Keep Context Awareness, Remove Open-Ended):**
   - Comment out `open_ended_scaffolding` section
   - Reduce open_ended_percent to 0% in distributions
   - Keep WH question increases

2. **Full Rollback:**
   - `git revert` to commit before this implementation
   - Restore original A2 question distribution (50% YES/NO, 30% CHOICE, 20% WH)

---

## 📚 **DOCUMENTATION REFERENCES**

- **CEFR A2 Level Definition:** Can describe experiences, give brief reasons, participate in short exchanges
- **Question Type Theory:** WH questions require production, YES/NO requires comprehension only
- **Scaffolding Research:** "Build UP not DOWN" - provide support without removing challenge

---

## ✅ **IMPLEMENTATION STATUS: COMPLETE**

All 8 tasks implemented successfully:
1. ✅ Context-aware question type distributions
2. ✅ Differentiated scaffolding (A1 vs A2)
3. ✅ A2 open-ended scaffolding function
4. ✅ Learning plan context updates
5. ✅ Topic/freestyle context updates
6. ✅ News context updates
7. ✅ A2 conversation flow examples
8. ✅ Main integration with context detection

**Ready for testing!** 🚀
