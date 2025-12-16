# Phase 3.1: Flexible Language/Level Selection - iOS Integration Guide

## Overview

Phase 3.1 adds **flexible language and level selection** to all challenge endpoints, enabling users to explore any language at any level directly from the Explore tab.

## Three User Scenarios Supported

### 1. 👻 Ghost Users (Not Logged In)
- Can browse predefined challenges from Phase 1.5 (3,643 reference challenges)
- Select language + level directly in Explore tab UI
- NO need to create account or learning plan first
- **Great for onboarding and engagement!**

### 2. ✅ Registered Users WITHOUT Learning Plan
- Browse challenges for ANY language and level
- System automatically copies reference challenges to their pool
- Learning plan is OPTIONAL
- Freedom to explore before committing

### 3. 🎯 Registered Users WITH Learning Plan
- **Default**: See challenges for their active learning plan language/level
- **Manual override**: Can switch to ANY other language in Explore tab
- Example: User has Spanish B1 plan, but wants to try German A1 for fun

---

## API Changes - All Endpoints Now Accept Query Parameters

### 1. GET `/api/challenges/daily`

**NEW: Optional Query Parameters**
- `language` - Target language (english, spanish, dutch, german, french, portuguese)
- `level` - CEFR level (A1, A2, B1, B2, C1, C2)

**Examples:**

```swift
// User manually selects Spanish A1 in Explore tab
GET /api/challenges/daily?language=spanish&level=A1

// User with English B2 plan wants to try French A1
GET /api/challenges/daily?language=french&level=A1

// No parameters - falls back to user's learning plan
GET /api/challenges/daily
```

**Response:** Same as before (6 daily challenges)

---

### 2. GET `/api/challenges/counts`

**NEW: Optional Query Parameters**
- `language` - Target language
- `level` - CEFR level

**Examples:**

```swift
// Check how many German A2 challenges are available
GET /api/challenges/counts?language=german&level=A2

// Ghost user checking Portuguese A1 challenges
GET /api/challenges/counts?language=portuguese&level=A1

// No parameters - uses learning plan
GET /api/challenges/counts
```

**Response:**
```json
{
  "error_spotting": 50,
  "swipe_fix": 50,
  "micro_quiz": 50,
  "smart_flashcard": 50,
  "native_check": 50,
  "brain_tickler": 50
}
```

---

### 3. GET `/api/challenges/by-type/{challenge_type}`

**NEW: Optional Query Parameters**
- `language` - Target language
- `level` - CEFR level
- `limit` - Max challenges to return (default 50)

**Examples:**

```swift
// Get Spanish A1 error_spotting challenges
GET /api/challenges/by-type/error_spotting?language=spanish&level=A1&limit=10

// Get Dutch B1 swipe_fix challenges
GET /api/challenges/by-type/swipe_fix?language=dutch&level=B1

// No parameters - uses learning plan
GET /api/challenges/by-type/micro_quiz
```

---

### 4. GET `/api/challenges/languages`

**NEW: Optional Query Parameters**
- `level` - CEFR level to check counts for (default: user's level)

**Examples:**

```swift
// Check all languages for A1 level
GET /api/challenges/languages?level=A1

// Check all languages for user's current level
GET /api/challenges/languages
```

**Response:**
```json
{
  "success": true,
  "active_language": "spanish",
  "languages": [
    {
      "language": "english",
      "has_learning_plan": false,
      "is_active": false,
      "available_challenges": 0
    },
    {
      "language": "spanish",
      "has_learning_plan": true,
      "is_active": true,
      "available_challenges": 300
    },
    {
      "language": "dutch",
      "has_learning_plan": false,
      "is_active": false,
      "available_challenges": 0
    }
  ]
}
```

---

## Smart Fallback Logic (Backend)

The backend uses **priority-based resolution**:

### Language Resolution:
1. ✅ **Explicit `?language=` parameter** (iOS user selection)
2. ✅ User's active learning plan language
3. ✅ Default: `"english"`

### Level Resolution:
1. ✅ **Explicit `?level=` parameter** (iOS user selection)
2. ✅ User's `preferred_level` from profile
3. ✅ Default: `"B1"`

This means:
- **iOS has full control** when passing parameters
- **Seamless fallback** when parameters are missing
- **No breaking changes** to existing code

---

## iOS Implementation Examples

### Example 1: Language/Level Picker in Explore Tab

```swift
struct ExploreView: View {
    @State private var selectedLanguage = "spanish"
    @State private var selectedLevel = "A1"
    @State private var challenges: [Challenge] = []

    var body: some View {
        VStack {
            // Language & Level Pickers
            HStack {
                Picker("Language", selection: $selectedLanguage) {
                    Text("English").tag("english")
                    Text("Spanish").tag("spanish")
                    Text("Dutch").tag("dutch")
                    Text("German").tag("german")
                    Text("French").tag("french")
                    Text("Portuguese").tag("portuguese")
                }

                Picker("Level", selection: $selectedLevel) {
                    Text("A1").tag("A1")
                    Text("A2").tag("A2")
                    Text("B1").tag("B1")
                    Text("B2").tag("B2")
                    Text("C1").tag("C1")
                    Text("C2").tag("C2")
                }
            }

            // Fetch challenges when selection changes
            .onChange(of: selectedLanguage) { _ in fetchChallenges() }
            .onChange(of: selectedLevel) { _ in fetchChallenges() }

            // Challenge List
            List(challenges) { challenge in
                ChallengeRow(challenge: challenge)
            }
        }
        .onAppear { fetchChallenges() }
    }

    func fetchChallenges() {
        let url = "\(baseURL)/api/challenges/daily?language=\(selectedLanguage)&level=\(selectedLevel)"

        // Make API request...
        APIService.shared.get(url) { (result: Result<DailyChallengesResponse, Error>) in
            switch result {
            case .success(let response):
                self.challenges = response.challenges
            case .failure(let error):
                print("Error: \(error)")
            }
        }
    }
}
```

---

### Example 2: Ghost User Onboarding Flow

```swift
struct OnboardingExploreView: View {
    @State private var selectedLanguage = "english"
    @State private var selectedLevel = "A1"
    @State private var challengeCounts: [String: Int] = [:]

    var body: some View {
        VStack(spacing: 20) {
            Text("Try MyTacoAI!")
                .font(.largeTitle)

            Text("Select a language and level to explore challenges")
                .font(.subheadline)

            // Pickers
            LanguageLevelPicker(
                language: $selectedLanguage,
                level: $selectedLevel
            )

            // Show available challenge counts
            if !challengeCounts.isEmpty {
                VStack {
                    Text("\(challengeCounts.values.reduce(0, +)) challenges available!")
                        .font(.headline)

                    Button("Start Exploring") {
                        // Navigate to challenges
                        showChallenges()
                    }
                    .buttonStyle(.borderedProminent)
                }
            }

            Button("Create Account Later") {
                // Continue as guest
            }
        }
        .onChange(of: selectedLanguage) { _ in fetchCounts() }
        .onChange(of: selectedLevel) { _ in fetchCounts() }
        .onAppear { fetchCounts() }
    }

    func fetchCounts() {
        let url = "\(baseURL)/api/challenges/counts?language=\(selectedLanguage)&level=\(selectedLevel)"

        APIService.shared.get(url) { (result: Result<ChallengeCountsResponse, Error>) in
            switch result {
            case .success(let counts):
                self.challengeCounts = [
                    "error_spotting": counts.error_spotting,
                    "swipe_fix": counts.swipe_fix,
                    "micro_quiz": counts.micro_quiz,
                    // ... etc
                ]
            case .failure(let error):
                print("Error: \(error)")
            }
        }
    }
}
```

---

### Example 3: Exploring Other Languages (User with Learning Plan)

```swift
struct ExploreOtherLanguagesView: View {
    @State private var currentPlanLanguage = "spanish"
    @State private var currentPlanLevel = "B1"
    @State private var exploringLanguage = "german"
    @State private var exploringLevel = "A1"

    var body: some View {
        VStack {
            // Current Learning Plan Banner
            HStack {
                VStack(alignment: .leading) {
                    Text("Your active plan:")
                    Text("\(currentPlanLanguage.capitalized) \(currentPlanLevel)")
                        .font(.headline)
                }

                Spacer()

                Button("Back to My Plan") {
                    // Reset to plan language
                    fetchChallenges(
                        language: currentPlanLanguage,
                        level: currentPlanLevel
                    )
                }
            }
            .padding()
            .background(Color.blue.opacity(0.1))
            .cornerRadius(8)

            Divider()

            // Explore Other Languages
            Text("Try another language")
                .font(.title3)

            LanguageLevelPicker(
                language: $exploringLanguage,
                level: $exploringLevel
            )
            .onChange(of: exploringLanguage) { _ in
                fetchChallenges(
                    language: exploringLanguage,
                    level: exploringLevel
                )
            }
            .onChange(of: exploringLevel) { _ in
                fetchChallenges(
                    language: exploringLanguage,
                    level: exploringLevel
                )
            }

            // Challenge list...
        }
    }

    func fetchChallenges(language: String, level: String) {
        let url = "\(baseURL)/api/challenges/daily?language=\(language)&level=\(level)"
        // Fetch and display...
    }
}
```

---

## Backend Automatic Handling

When a user requests challenges for a language they haven't used before:

1. **Backend checks their challenge pool** for that language/level
2. **If empty**: Automatically copies reference challenges from Phase 1.5 database
3. **If low**: Generates personalized AI challenges
4. **User sees content immediately** - no manual setup needed!

This is handled by `ensure_pool_has_challenges()` in `challenge_pool_helpers.py`.

---

## Validation

Both endpoints validate inputs:

**Valid Languages:**
- `english`, `spanish`, `dutch`, `german`, `french`, `portuguese`

**Valid Levels:**
- `A1`, `A2`, `B1`, `B2`, `C1`, `C2`

Invalid inputs default to:
- Language: `"english"`
- Level: `"B1"`

---

## Migration Notes

### No Breaking Changes
- All query parameters are **optional**
- Existing iOS code continues to work without modification
- Endpoints fall back to learning plan if no parameters provided

### When to Use Parameters
- ✅ When user manually selects language/level in UI
- ✅ For ghost users exploring without account
- ✅ For "try another language" features
- ❌ Don't pass parameters if you want learning plan defaults

---

## Testing Checklist for iOS

- [ ] Ghost user can browse challenges without login
- [ ] User without learning plan can select any language/level
- [ ] User with learning plan sees their plan language by default
- [ ] User with learning plan can manually switch to other languages
- [ ] Language/level pickers update challenges in real-time
- [ ] Invalid language/level inputs are handled gracefully
- [ ] `/counts` endpoint shows correct counts for selected language/level
- [ ] `/languages` endpoint lists all available languages with counts

---

## Next Steps

### Phase 4: Testing & Verification
- Test all endpoints with different languages
- Verify reference challenge copying works
- Check AI generation for new languages

### Phase 5: Railway Deployment
- Deploy updated backend
- Update cron service

### Phase 6: iOS Integration
- Implement language/level pickers in Explore tab
- Update challenge fetching logic
- Add "try another language" feature

---

## Questions?

This implementation gives iOS full control over language/level selection while maintaining backward compatibility. Users can now explore ANY language at ANY level, making the Explore tab a true discovery experience!
