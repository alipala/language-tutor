# Phase 3 & 3.1: React Native Integration Guide

## Overview

This document explains the backend changes for **flexible language/level selection** in the Challenge system and how to integrate them into the React Native app.

---

## ✅ What We've Accomplished

### Your Original Requirements

Support **3 user scenarios**:

1. **👻 Ghost users** - Not logged in, can browse predefined challenges in Explore tab to engage them
2. **✅ Users WITHOUT learning plans** - Can select ANY language/level manually from Explore tab
3. **🎯 Users WITH learning plans** - Can explore other languages in addition to their plan-specific challenges

### What We Built

#### **Phase 3: Language-Aware Backend Filtering** ✅

- Separated all challenges by language (English, Spanish, Dutch, German, French, Portuguese)
- Updated all helper functions to accept `language` parameter
- Updated MongoDB queries to filter by language
- Prevents language mixing in challenge pools

**Files Modified:**
- `backend/challenge_pool_helpers.py` - Added `language` parameter to all 3 core functions
- `backend/challenge_generator_ai.py` - Added language filtering for AI generation
- `backend/challenge_routes.py` - Added language detection and routing

#### **Phase 3.1: Flexible Language/Level Selection** ✅

- Added **optional query parameters** to ALL challenge endpoints
- Implemented **smart resolution logic** with priority fallback
- **Auto-population** from reference challenges (3,643 challenges available)
- **Backward compatible** - existing React Native app continues to work

**Files Modified:**
- `backend/challenge_routes.py` - Added query parameters to 4 endpoints + smart resolution helper

**Smart Resolution Logic:**
```
Priority for LANGUAGE:
1. ?language= query parameter (React Native user selection) ← HIGHEST
2. User's active learning plan language
3. Fallback: "english"

Priority for LEVEL:
1. ?level= query parameter (React Native user selection) ← HIGHEST
2. User's preferred_level from profile
3. Fallback: "B1"
```

---

## 🔌 Backend Endpoints - Complete Reference

### **Endpoint 1: GET `/api/challenges/daily`**

**Purpose:** Get 6 daily challenges for a specific language/level (one per challenge type)

#### Query Parameters

| Parameter | Type | Required | Valid Values | Default |
|-----------|------|----------|--------------|---------|
| `language` | string | ❌ No | `english`, `spanish`, `dutch`, `german`, `french`, `portuguese` | User's learning plan language or `"english"` |
| `level` | string | ❌ No | `A1`, `A2`, `B1`, `B2`, `C1`, `C2` | User's preferred level or `"B1"` |

#### Headers

```javascript
{
  "Authorization": "Bearer <access_token>",  // Optional for ghost users
  "Content-Type": "application/json"
}
```

#### Request Examples

**React Native - Ghost User (No Authentication):**
```javascript
// No authentication needed!
const response = await fetch(
  `${API_BASE_URL}/api/challenges/daily?language=spanish&level=A1`,
  {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  }
);
const data = await response.json();
```

**React Native - User WITHOUT Learning Plan:**
```javascript
const response = await fetch(
  `${API_BASE_URL}/api/challenges/daily?language=german&level=B2`,
  {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  }
);
const data = await response.json();
```

**React Native - User WITH Learning Plan (Override):**
```javascript
// User has Spanish B1 plan but wants to try French A1
const response = await fetch(
  `${API_BASE_URL}/api/challenges/daily?language=french&level=A1`,
  {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  }
);
const data = await response.json();
```

**React Native - User WITH Learning Plan (Default):**
```javascript
// No params - uses their active learning plan automatically
const response = await fetch(
  `${API_BASE_URL}/api/challenges/daily`,
  {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  }
);
const data = await response.json();
```

#### Response Structure

```javascript
{
  "success": true,
  "challenges": [
    {
      "challenge_id": "er_a1_sp_00001",
      "challenge_type": "error_spotting",
      "language": "spanish",
      "cefr_level": "A1",
      "question": "Find the error: 'Yo es estudiante'",
      "correct_answer": "Yo soy estudiante",
      "explanation": "'Es' is for third person, use 'soy' for first person",
      "difficulty": 1,
      "status": "available"
    },
    // ... 5 more challenges (6 total, one per type)
  ],
  "total_completed_today": 0,
  "streak": {
    "current": 1,
    "longest": 5
  }
}
```

---

### **Endpoint 2: GET `/api/challenges/counts`**

**Purpose:** Get count of available challenges by type for a specific language/level

#### Query Parameters

| Parameter | Type | Required | Valid Values | Default |
|-----------|------|----------|--------------|---------|
| `language` | string | ❌ No | `english`, `spanish`, `dutch`, `german`, `french`, `portuguese` | User's learning plan language or `"english"` |
| `level` | string | ❌ No | `A1`, `A2`, `B1`, `B2`, `C1`, `C2` | User's preferred level or `"B1"` |

#### Headers

```javascript
{
  "Authorization": "Bearer <access_token>",  // Optional
  "Content-Type": "application/json"
}
```

#### Request Example

**React Native:**
```javascript
// Check Spanish A1 availability before showing to user
const response = await fetch(
  `${API_BASE_URL}/api/challenges/counts?language=spanish&level=A1`,
  {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  }
);

const data = await response.json();
console.log(data);
// {
//   "error_spotting": 10,
//   "swipe_fix": 10,
//   "micro_quiz": 10,
//   "smart_flashcard": 10,
//   "native_check": 10,
//   "brain_tickler": 10
// }

// Calculate total
const total = Object.values(data).reduce((sum, count) => sum + count, 0);
console.log(`${total} challenges available!`); // "60 challenges available!"
```

#### Response Structure

```javascript
{
  "error_spotting": 50,
  "swipe_fix": 50,
  "micro_quiz": 50,
  "smart_flashcard": 50,
  "native_check": 50,
  "brain_tickler": 50
}
```

**Use Case:** Show users "300 challenges available!" before they start exploring

---

### **Endpoint 3: GET `/api/challenges/by-type/{challenge_type}`**

**Purpose:** Get challenges of a specific type for a language/level

#### Path Parameters

| Parameter | Type | Required | Valid Values |
|-----------|------|----------|--------------|
| `challenge_type` | string | ✅ Yes | `error_spotting`, `swipe_fix`, `micro_quiz`, `smart_flashcard`, `native_check`, `brain_tickler` |

#### Query Parameters

| Parameter | Type | Required | Valid Values | Default |
|-----------|------|----------|--------------|---------|
| `language` | string | ❌ No | `english`, `spanish`, `dutch`, `german`, `french`, `portuguese` | User's learning plan language or `"english"` |
| `level` | string | ❌ No | `A1`, `A2`, `B1`, `B2`, `C1`, `C2` | User's preferred level or `"B1"` |
| `limit` | number | ❌ No | 1-100 | 50 |

#### Headers

```javascript
{
  "Authorization": "Bearer <access_token>",  // Optional
  "Content-Type": "application/json"
}
```

#### Request Examples

**React Native:**
```javascript
// Get 10 Spanish A1 error_spotting challenges
const challengeType = 'error_spotting';
const response = await fetch(
  `${API_BASE_URL}/api/challenges/by-type/${challengeType}?language=spanish&level=A1&limit=10`,
  {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  }
);

const data = await response.json();
console.log(data.challenges.length); // Up to 10 challenges
```

#### Response Structure

```javascript
{
  "success": true,
  "challenge_type": "error_spotting",
  "challenges": [
    {
      "challenge_id": "er_a1_sp_00001",
      "challenge_type": "error_spotting",
      "language": "spanish",
      "cefr_level": "A1",
      "question": "Find the error in this sentence",
      "correct_answer": "...",
      "explanation": "...",
      "status": "available"
    },
    // ... up to 10 challenges
  ]
}
```

---

### **Endpoint 4: GET `/api/challenges/languages`** (NEW!)

**Purpose:** List all 6 supported languages with availability info for a specific level

#### Query Parameters

| Parameter | Type | Required | Valid Values | Default |
|-----------|------|----------|--------------|---------|
| `level` | string | ❌ No | `A1`, `A2`, `B1`, `B2`, `C1`, `C2` | User's preferred level or `"B1"` |

#### Headers

```javascript
{
  "Authorization": "Bearer <access_token>",  // Optional
  "Content-Type": "application/json"
}
```

#### Request Example

**React Native:**
```javascript
// Get all languages for A1 level
const response = await fetch(
  `${API_BASE_URL}/api/challenges/languages?level=A1`,
  {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  }
);

const data = await response.json();

// Find active language
const activeLanguage = data.languages.find(lang => lang.is_active);
console.log(`Active: ${activeLanguage?.language}`); // "spanish"

// Find languages with available content
const availableLanguages = data.languages.filter(
  lang => lang.available_challenges > 0
);
console.log(`${availableLanguages.length} languages have content`);
```

#### Response Structure

```javascript
{
  "success": true,
  "active_language": "spanish",  // User's current learning plan language (null if no plan)
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
      "available_challenges": 300  // This language has challenges ready
    },
    {
      "language": "dutch",
      "has_learning_plan": false,
      "is_active": false,
      "available_challenges": 0
    },
    {
      "language": "german",
      "has_learning_plan": false,
      "is_active": false,
      "available_challenges": 0
    },
    {
      "language": "french",
      "has_learning_plan": false,
      "is_active": false,
      "available_challenges": 0
    },
    {
      "language": "portuguese",
      "has_learning_plan": false,
      "is_active": false,
      "available_challenges": 0
    }
  ]
}
```

**Use Case:**
- Populate language picker UI
- Show which languages have available content
- Display user's active learning plan language

---

## 🔄 Backend Auto-Population Magic

### How It Works

When a user requests challenges for a new language/level combination:

1. User makes request: `GET /api/challenges/daily?language=german&level=A2`
2. Backend checks their `challenge_pool` collection for `german` + `A2` challenges
3. **If pool is empty**: Backend automatically copies 60 reference challenges from `reference_challenges` collection
4. User receives challenges immediately - **no manual setup needed!**

**This happens automatically in:**
`backend/challenge_pool_helpers.py` → `ensure_pool_has_challenges()` function

**Available reference challenges:** 3,643 challenges across:
- 6 languages × 6 levels × 6 challenge types
- Pre-generated in Phase 1.5

---

## 📊 Endpoint Summary Table

| Endpoint | Method | Auth Required | Purpose | Query Params |
|----------|--------|---------------|---------|--------------|
| `/api/challenges/daily` | GET | Optional | Get 6 daily challenges (1 per type) | `?language=&level=` |
| `/api/challenges/counts` | GET | Optional | Get challenge counts by type | `?language=&level=` |
| `/api/challenges/by-type/{type}` | GET | Optional | Get challenges of specific type | `?language=&level=&limit=` |
| `/api/challenges/languages` | GET | Optional | List all languages with counts | `?level=` |

---

## 🎯 React Native Implementation Checklist

### What Needs to Be Updated in React Native App

#### 1. **Update API Service Layer**

Add query parameters to existing API calls:

```javascript
// OLD (before Phase 3.1)
export const getDailyChallenges = async (accessToken) => {
  const response = await fetch(`${API_BASE_URL}/api/challenges/daily`, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  return response.json();
};

// NEW (after Phase 3.1)
export const getDailyChallenges = async (accessToken, language = null, level = null) => {
  let url = `${API_BASE_URL}/api/challenges/daily`;

  // Add query parameters if provided
  const params = new URLSearchParams();
  if (language) params.append('language', language);
  if (level) params.append('level', level);

  if (params.toString()) {
    url += `?${params.toString()}`;
  }

  const response = await fetch(url, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  return response.json();
};
```

#### 2. **Create Language/Level Picker Component**

```javascript
import React from 'react';
import { View, Text, Picker } from 'react-native';

const LanguageLevelPicker = ({ selectedLanguage, selectedLevel, onLanguageChange, onLevelChange }) => {
  const languages = [
    { code: 'english', name: '🇬🇧 English' },
    { code: 'spanish', name: '🇪🇸 Spanish' },
    { code: 'dutch', name: '🇳🇱 Dutch' },
    { code: 'german', name: '🇩🇪 German' },
    { code: 'french', name: '🇫🇷 French' },
    { code: 'portuguese', name: '🇵🇹 Portuguese' }
  ];

  const levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

  return (
    <View style={styles.container}>
      <View style={styles.pickerContainer}>
        <Text style={styles.label}>Choose Language</Text>
        <Picker
          selectedValue={selectedLanguage}
          onValueChange={onLanguageChange}
        >
          {languages.map(lang => (
            <Picker.Item key={lang.code} label={lang.name} value={lang.code} />
          ))}
        </Picker>
      </View>

      <View style={styles.pickerContainer}>
        <Text style={styles.label}>Choose Level</Text>
        <Picker
          selectedValue={selectedLevel}
          onValueChange={onLevelChange}
        >
          {levels.map(level => (
            <Picker.Item key={level} label={level} value={level} />
          ))}
        </Picker>
      </View>
    </View>
  );
};

export default LanguageLevelPicker;
```

#### 3. **Update Explore Screen**

```javascript
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, ActivityIndicator } from 'react-native';
import LanguageLevelPicker from './components/LanguageLevelPicker';
import { getDailyChallenges, getChallengeCounts } from './services/api';

const ExploreScreen = ({ accessToken }) => {
  const [selectedLanguage, setSelectedLanguage] = useState('spanish');
  const [selectedLevel, setSelectedLevel] = useState('A1');
  const [challenges, setChallenges] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);

  // Fetch challenges when language/level changes
  useEffect(() => {
    fetchChallenges();
    fetchCounts();
  }, [selectedLanguage, selectedLevel]);

  const fetchChallenges = async () => {
    setLoading(true);
    try {
      const data = await getDailyChallenges(accessToken, selectedLanguage, selectedLevel);
      setChallenges(data.challenges);
    } catch (error) {
      console.error('Error fetching challenges:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCounts = async () => {
    try {
      const counts = await getChallengeCounts(accessToken, selectedLanguage, selectedLevel);
      const total = Object.values(counts).reduce((sum, count) => sum + count, 0);
      setTotalCount(total);
    } catch (error) {
      console.error('Error fetching counts:', error);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Explore Challenges</Text>

      {/* Language/Level Picker */}
      <LanguageLevelPicker
        selectedLanguage={selectedLanguage}
        selectedLevel={selectedLevel}
        onLanguageChange={setSelectedLanguage}
        onLevelChange={setSelectedLevel}
      />

      {/* Total Count */}
      <Text style={styles.countText}>
        {totalCount} challenges available!
      </Text>

      {/* Challenge List */}
      {loading ? (
        <ActivityIndicator size="large" />
      ) : (
        <FlatList
          data={challenges}
          keyExtractor={(item) => item.challenge_id}
          renderItem={({ item }) => (
            <ChallengeCard challenge={item} />
          )}
        />
      )}
    </View>
  );
};

export default ExploreScreen;
```

#### 4. **Ghost User Onboarding Screen** (Optional)

```javascript
import React, { useState, useEffect } from 'react';
import { View, Text, Button } from 'react-native';
import LanguageLevelPicker from './components/LanguageLevelPicker';
import { getChallengeCounts } from './services/api';

const GhostUserOnboardingScreen = ({ navigation }) => {
  const [selectedLanguage, setSelectedLanguage] = useState('english');
  const [selectedLevel, setSelectedLevel] = useState('A1');
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    fetchCounts();
  }, [selectedLanguage, selectedLevel]);

  const fetchCounts = async () => {
    try {
      // No access token needed for ghost users!
      const counts = await getChallengeCounts(null, selectedLanguage, selectedLevel);
      const total = Object.values(counts).reduce((sum, count) => sum + count, 0);
      setTotalCount(total);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Try MyTacoAI!</Text>
      <Text style={styles.subtitle}>
        Select a language and level to explore challenges
      </Text>

      <LanguageLevelPicker
        selectedLanguage={selectedLanguage}
        selectedLevel={selectedLevel}
        onLanguageChange={setSelectedLanguage}
        onLevelChange={setSelectedLevel}
      />

      {totalCount > 0 && (
        <View style={styles.availabilityContainer}>
          <Text style={styles.availabilityText}>
            {totalCount} challenges available!
          </Text>
          <Button
            title="Start Exploring"
            onPress={() => navigation.navigate('Explore', {
              language: selectedLanguage,
              level: selectedLevel
            })}
          />
        </View>
      )}

      <Button
        title="Create Account Later"
        onPress={() => navigation.navigate('Explore', {
          language: selectedLanguage,
          level: selectedLevel
        })}
      />
    </View>
  );
};

export default GhostUserOnboardingScreen;
```

---

## ✅ Testing Status

All endpoints have been tested with user `d77240fe-5821-486a-a6cc-d61396fffa58@mailslurp.biz`:

- ✅ **Spanish A1**: 60 challenges auto-populated
- ✅ **German B2**: 60 challenges auto-populated
- ✅ **French A2**: 60 challenges auto-populated
- ✅ **Dutch B1**: 60 challenges auto-populated
- ✅ **English B1**: 60 challenges auto-populated
- ✅ **Smart fallback logic** working correctly
- ✅ **Ghost user support** working (no auth required)
- ✅ **Auto-population from reference challenges** working

---

## 🚀 Implementation Strategy

### Phase 1: Update API Service (No UI Changes)
1. Add query parameters to existing API functions
2. Make parameters optional (defaults to learning plan)
3. Test that existing app still works (backward compatible)

### Phase 2: Add Language/Level Picker to Explore Tab
1. Create `LanguageLevelPicker` component
2. Add to Explore screen
3. Wire up state changes to API calls

### Phase 3: Add Ghost User Onboarding
1. Create onboarding screen with language/level selection
2. Show challenge counts before signup
3. Allow "Continue as Guest" flow

### Phase 4: Add "Try Another Language" Feature
1. For users with learning plans
2. Show current plan prominently
3. Allow temporary override to explore other languages

---

## 📝 Notes

### No Breaking Changes
- All query parameters are **optional**
- Existing React Native code continues to work without modification
- Backend falls back to learning plan if no parameters provided

### When to Use Parameters
- ✅ When user manually selects language/level in Explore tab
- ✅ For ghost users exploring without account
- ✅ For "try another language" features
- ❌ Don't pass parameters if you want learning plan defaults

### Valid Values
**Languages:** `english`, `spanish`, `dutch`, `german`, `french`, `portuguese`
**Levels:** `A1`, `A2`, `B1`, `B2`, `C1`, `C2`

Invalid inputs automatically fallback to safe defaults (`english` / `B1`)

---

## 🎯 Next Steps

1. **Share this document with React Native team**
2. **Update API service layer** with query parameters
3. **Create Language/Level picker component**
4. **Update Explore screen** to use new parameters
5. **Test with different language/level combinations**
6. **Deploy to production** after testing

---

**Questions or need clarification?** This implementation gives React Native full control over language/level selection while maintaining backward compatibility!
