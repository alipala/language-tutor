# iOS UI for Users with Learning Plans

## 🎯 User Experience Design

### **The Challenge:**
Users with learning plans should:
1. ✅ See their learning plan challenges **by default**
2. ✅ Have the **option to explore other languages** manually
3. ✅ Know which language is their "main" learning plan

---

## 📱 iOS App UI Components

### **1. Explore Tab - Default View (User WITH Learning Plan)**

```
┌─────────────────────────────────────┐
│  Explore Challenges                 │
├─────────────────────────────────────┤
│                                     │
│  📚 Your Learning Plan              │
│  🇪🇸 Spanish - B1                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                     │
│  60 challenges available!           │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  Daily Challenges (6)       │  │
│  │  ─────────────────────────  │  │
│  │  🎯 Error Spotting          │  │
│  │  🔄 Swipe Fix               │  │
│  │  ❓ Micro Quiz              │  │
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  Explore by Type            │  │
│  │  ─────────────────────────  │  │
│  │  📝 Error Spotting (10)     │  │
│  │  🔄 Swipe Fix (10)          │  │
│  │  ❓ Micro Quiz (10)         │  │
│  │  📚 Smart Flashcard (10)    │  │
│  │  ✓ Native Check (10)        │  │
│  │  🧠 Brain Tickler (10)      │  │
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  Try Another Language?      │  │ ← NEW!
│  │  🌍 Explore Other Languages │  │
│  └─────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

**Key Features:**
- ✅ Shows user's active learning plan language/level prominently
- ✅ Displays challenges for their learning plan by default
- ✅ "Try Another Language" button at bottom for exploration

---

### **2. Explore Tab - Manual Override (User Clicks "Try Another Language")**

```
┌─────────────────────────────────────┐
│  ← Back to My Plan                  │
├─────────────────────────────────────┤
│                                     │
│  🌍 Explore Other Languages         │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  Choose Language            │  │
│  │                             │  │
│  │  🇬🇧 English  🇪🇸 Spanish  │  │ ← Language picker
│  │  🇳🇱 Dutch    🇩🇪 German   │  │
│  │  🇫🇷 French   🇵🇹 Portuguese│  │
│  │                             │  │
│  │  Selected: 🇩🇪 German       │  │
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  Choose Level               │  │
│  │                             │  │
│  │  A1  A2  B1  B2  C1  C2     │  │ ← Level picker
│  │  ●                          │  │
│  │                             │  │
│  │  Selected: A1 - Beginner    │  │
│  └─────────────────────────────┘  │
│                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                     │
│  60 challenges available!           │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  German A1 Challenges       │  │
│  │  ─────────────────────────  │  │
│  │  📝 Error Spotting (10)     │  │
│  │  🔄 Swipe Fix (10)          │  │
│  │  ❓ Micro Quiz (10)         │  │
│  └─────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

**Key Features:**
- ✅ "Back to My Plan" button to return to learning plan
- ✅ Language picker with flags
- ✅ Level picker with descriptions
- ✅ Shows challenges for selected language/level
- ✅ User's learning plan is still active in background

---

### **3. Explore Tab - User WITHOUT Learning Plan**

```
┌─────────────────────────────────────┐
│  Explore Challenges                 │
├─────────────────────────────────────┤
│                                     │
│  🌍 Choose Your Language & Level    │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  Language                   │  │
│  │                             │  │
│  │  🇬🇧 English  🇪🇸 Spanish  │  │
│  │  🇳🇱 Dutch    🇩🇪 German   │  │
│  │  🇫🇷 French   🇵🇹 Portuguese│  │
│  │                             │  │
│  │  Selected: 🇪🇸 Spanish      │  │
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  Level                      │  │
│  │                             │  │
│  │  A1  A2  B1  B2  C1  C2     │  │
│  │       ●                     │  │
│  │                             │  │
│  │  Selected: A2 - Elementary  │  │
│  └─────────────────────────────┘  │
│                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                     │
│  60 challenges available!           │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  Spanish A2 Challenges      │  │
│  │  ─────────────────────────  │  │
│  │  📝 Error Spotting (10)     │  │
│  │  🔄 Swipe Fix (10)          │  │
│  └─────────────────────────────┘  │
│                                     │
│  💡 Want to create a learning plan? │
│  [Create Learning Plan Button]     │
│                                     │
└─────────────────────────────────────┘
```

**Key Features:**
- ✅ Language/Level picker shown by default (no learning plan)
- ✅ Full freedom to choose any language/level
- ✅ Prompt to create learning plan (optional)

---

## 💻 React Native Implementation

### **Component Structure:**

```typescript
// ExploreScreen.tsx

const ExploreScreen = () => {
  const { user, learningPlan } = useAuth();

  // State
  const [viewMode, setViewMode] = useState<'plan' | 'explore'>('plan');
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [challenges, setChallenges] = useState([]);

  // Initialize based on learning plan
  useEffect(() => {
    if (learningPlan) {
      // User has learning plan - show their plan by default
      setSelectedLanguage(learningPlan.language);
      setSelectedLevel(learningPlan.level || user.preferred_level);
      setViewMode('plan');
    } else {
      // No learning plan - show language/level picker
      setSelectedLanguage('english');
      setSelectedLevel(user.preferred_level || 'B1');
      setViewMode('explore');
    }
  }, [learningPlan]);

  // Fetch challenges when language/level changes
  useEffect(() => {
    if (selectedLanguage && selectedLevel) {
      fetchChallenges();
    }
  }, [selectedLanguage, selectedLevel]);

  const fetchChallenges = async () => {
    try {
      // Call API with language/level
      const counts = await getChallengesCounts(
        accessToken,
        selectedLanguage,
        selectedLevel
      );

      setChallenges(counts);
    } catch (error) {
      console.error('Error fetching challenges:', error);
    }
  };

  const handleTryOtherLanguage = () => {
    setViewMode('explore');
  };

  const handleBackToMyPlan = () => {
    if (learningPlan) {
      setSelectedLanguage(learningPlan.language);
      setSelectedLevel(learningPlan.level || user.preferred_level);
      setViewMode('plan');
    }
  };

  return (
    <View>
      {/* Header */}
      {viewMode === 'plan' && learningPlan && (
        <LearningPlanBanner
          language={learningPlan.language}
          level={learningPlan.level}
          onExploreOther={handleTryOtherLanguage}
        />
      )}

      {viewMode === 'explore' && learningPlan && (
        <BackButton onPress={handleBackToMyPlan} />
      )}

      {/* Language/Level Picker */}
      {(viewMode === 'explore' || !learningPlan) && (
        <LanguageLevelPicker
          selectedLanguage={selectedLanguage}
          selectedLevel={selectedLevel}
          onLanguageChange={setSelectedLanguage}
          onLevelChange={setSelectedLevel}
        />
      )}

      {/* Challenge Count Banner */}
      <ChallengeBanner totalChallenges={challenges.total} />

      {/* Challenge List */}
      <ChallengeList
        language={selectedLanguage}
        level={selectedLevel}
        challenges={challenges}
      />
    </View>
  );
};
```

---

## 🎨 UI Components Breakdown

### **1. LearningPlanBanner Component**

```typescript
const LearningPlanBanner = ({ language, level, onExploreOther }) => {
  const languageFlags = {
    english: '🇬🇧',
    spanish: '🇪🇸',
    dutch: '🇳🇱',
    german: '🇩🇪',
    french: '🇫🇷',
    portuguese: '🇵🇹'
  };

  return (
    <View style={styles.banner}>
      <Text style={styles.label}>📚 Your Learning Plan</Text>
      <Text style={styles.language}>
        {languageFlags[language]} {language.charAt(0).toUpperCase() + language.slice(1)} - {level}
      </Text>

      <TouchableOpacity onPress={onExploreOther} style={styles.exploreButton}>
        <Text style={styles.exploreButtonText}>🌍 Try Another Language?</Text>
      </TouchableOpacity>
    </View>
  );
};
```

### **2. LanguageLevelPicker Component** (Already Created!)

Already implemented by iOS agent - just use it!

### **3. BackButton Component**

```typescript
const BackButton = ({ onPress }) => {
  return (
    <TouchableOpacity onPress={onPress} style={styles.backButton}>
      <Text style={styles.backButtonText}>← Back to My Plan</Text>
    </TouchableOpacity>
  );
};
```

### **4. ChallengeBanner Component**

```typescript
const ChallengeBanner = ({ totalChallenges }) => {
  return (
    <View style={styles.banner}>
      <Text style={styles.count}>{totalChallenges} challenges available!</Text>
    </View>
  );
};
```

---

## 🔄 User Flow

### **Flow 1: User WITH Learning Plan (Default)**

```
User opens Explore tab
  ↓
Show learning plan banner (Spanish B1)
  ↓
API Call: GET /api/challenges/counts
  (no params - uses learning plan)
  ↓
Backend returns: Spanish B1 challenges
  ↓
Display: "60 challenges available!"
  ↓
User sees challenge types for Spanish B1
```

### **Flow 2: User WITH Learning Plan (Override)**

```
User opens Explore tab
  ↓
Show learning plan banner (Spanish B1)
  ↓
User clicks "Try Another Language?"
  ↓
Show language/level picker
  ↓
User selects German A1
  ↓
API Call: GET /api/challenges/counts?language=german&level=A1
  ↓
Backend auto-populates 60 German A1 challenges
  ↓
Display: "60 challenges available!"
  ↓
User sees challenge types for German A1
  ↓
User can click "Back to My Plan" to return to Spanish B1
```

### **Flow 3: User WITHOUT Learning Plan**

```
User opens Explore tab
  ↓
Show language/level picker (default: English B1)
  ↓
API Call: GET /api/challenges/counts?language=english&level=B1
  ↓
Backend auto-populates 60 English B1 challenges
  ↓
Display: "60 challenges available!"
  ↓
User can change language/level anytime
```

---

## 🎯 Key Design Principles

### **1. Learning Plan is Primary**
- Users with learning plans see their plan challenges by default
- Learning plan language/level is prominent (banner, flag, level)
- No manual selection needed - just works!

### **2. Exploration is Optional**
- "Try Another Language?" button for exploration
- Doesn't affect their learning plan
- Can always return to their plan

### **3. Flexibility for All**
- Users without plans have full freedom
- Ghost users can explore without account
- Everyone can switch languages/levels easily

### **4. Clear Context**
- Always show which language/level is selected
- Show if it's their learning plan or manual selection
- Display challenge counts prominently

---

## ✅ Summary

**For Users WITH Learning Plans:**
```
Default View: Show their learning plan challenges
Override View: Show language/level picker + "Back to My Plan"
```

**For Users WITHOUT Learning Plans:**
```
Default View: Show language/level picker
No learning plan banner
```

**Backend Handles:**
```
No params → Use learning plan (if exists) or default to English B1
With params → Use specified language/level (override)
```

**iOS App Needs:**
1. ✅ LearningPlanBanner component (NEW - needs to be created)
2. ✅ LanguageLevelPicker component (DONE - iOS agent created it)
3. ✅ BackButton component (NEW - simple to create)
4. ✅ ChallengeBanner component (NEW - simple to create)
5. ✅ View mode state management (plan vs explore)

---

**The iOS agent already did most of the work! Just need to add:**
- Learning plan banner
- "Try Another Language" button
- "Back to My Plan" functionality
- View mode toggle (plan vs explore)

🚀 **Ready to deploy!**
