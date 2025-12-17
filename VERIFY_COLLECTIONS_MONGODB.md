# MongoDB Collections Verification Guide

## 📊 Quick Verification Commands

Run these commands in **Railway MongoDB shell** or **MongoDB Compass** or **mongosh**:

---

## 1️⃣ **REFERENCE_CHALLENGES Collection**

```javascript
// Switch to database
use language_tutor

// ========================================
// REFERENCE_CHALLENGES VERIFICATION
// ========================================

// Total count
db.reference_challenges.countDocuments()
// Expected: ~3,643 (or 4K as you mentioned)

// Sample document
db.reference_challenges.findOne()
// Check for: language, cefr_level, challenge_type
// Should NOT have: user_id, status

// Language distribution
db.reference_challenges.aggregate([
  { $group: { _id: "$language", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
// Expected: english, spanish, dutch, german, french, portuguese

// Challenge type distribution
db.reference_challenges.aggregate([
  { $group: { _id: "$challenge_type", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
// Expected: 6 types (error_spotting, swipe_fix, micro_quiz, etc.)

// CEFR level distribution
db.reference_challenges.aggregate([
  { $group: { _id: "$cefr_level", count: { $sum: 1 } } },
  { $sort: { _id: 1 } }
])
// Expected: A1, A2, B1, B2, C1, C2

// ✅ Verification: Should have NO user_id
db.reference_challenges.countDocuments({ user_id: { $exists: true } })
// Expected: 0

// ✅ Verification: Should have language field
db.reference_challenges.countDocuments({ language: { $exists: false } })
// Expected: 0
```

**✅ PURPOSE:**
- Template/seed challenges
- High-quality, curated content
- Used for COPYING to user pools (not direct use)
- Generated once in Phase 1.5

---

## 2️⃣ **CHALLENGE_POOL Collection**

```javascript
// ========================================
// CHALLENGE_POOL VERIFICATION
// ========================================

// Total count
db.challenge_pool.countDocuments()
// Expected: ~1K (your number)

// Sample document
db.challenge_pool.findOne()
// Check for: user_id, language, cefr_level, status, created_at
// Should HAVE: user_id, status

// User distribution
db.challenge_pool.aggregate([
  { $group: { _id: "$user_id", count: { $sum: 1 } } },
  { $sort: { count: -1 } },
  { $limit: 10 }
])
// Shows how many challenges each user has

// Status distribution
db.challenge_pool.aggregate([
  { $group: { _id: "$status", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
// Expected: available, completed, expired

// Language distribution
db.challenge_pool.aggregate([
  { $group: { _id: "$language", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])

// Challenge type distribution
db.challenge_pool.aggregate([
  { $group: { _id: "$challenge_type", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])

// ✅ Verification: Should have user_id
db.challenge_pool.countDocuments({ user_id: { $exists: false } })
// Expected: 0

// ✅ Verification: Should have status
db.challenge_pool.countDocuments({ status: { $exists: false } })
// Expected: 0

// ✅ Verification: Should have language field
db.challenge_pool.countDocuments({ language: { $exists: false } })
// Expected: 0
```

**✅ PURPOSE:**
- User-specific challenges
- Ready to be used in Explore tab
- Copied from reference OR AI-generated
- Has status tracking (available → completed)

---

## 3️⃣ **KEY DIFFERENCES Table**

| Feature | reference_challenges | challenge_pool |
|---------|---------------------|----------------|
| **Total Count** | ~4,000 | ~1,000 |
| **Has user_id?** | ❌ NO | ✅ YES |
| **Has status?** | ❌ NO | ✅ YES (available/completed/expired) |
| **Purpose** | Template library | User inventory |
| **Direct usage?** | ❌ NO (copy first) | ✅ YES (Explore tab) |
| **Generated when?** | Phase 1.5 (once) | Weekly cron + on-demand |
| **Expires?** | ❌ NO | ✅ YES (30 days) |

---

## 4️⃣ **HOW THEY WORK TOGETHER**

```
┌──────────────────────────────────────────────────────────────┐
│              reference_challenges (4K)                       │
│  [Template Library - No user_id, No status]                 │
│                                                              │
│  english-A1-error_spotting-001                              │
│  spanish-B2-micro_quiz-042                                  │
│  dutch-A2-swipe_fix-017                                     │
│  ...                                                         │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ COPY (fast, free)
                            │ OR
                            │ AI GENERATE (slow, $$$)
                            ↓
┌──────────────────────────────────────────────────────────────┐
│              challenge_pool (1K)                             │
│  [User Inventory - Has user_id, Has status]                 │
│                                                              │
│  user_123 → english-B1-error_spotting (available)           │
│  user_123 → spanish-A1-micro_quiz (completed)               │
│  user_456 → dutch-A2-swipe_fix (available)                  │
│  ...                                                         │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ USER REQUESTS
                            ↓
                    ┌──────────────┐
                    │  Explore Tab │
                    └──────────────┘
```

---

## 5️⃣ **WORKFLOW EXAMPLE**

**Scenario: User visits Explore tab (English B1)**

```javascript
// Step 1: Check challenge_pool for this user
db.challenge_pool.find({
  user_id: "688921c268819565ef1ce3dc",
  language: "english",
  cefr_level: "B1",
  status: "available"
}).count()

// Case A: Pool has 60 challenges
//   → Return immediately (< 1s)
//   → No API calls needed
//   → Fast UX ✅

// Case B: Pool has 0 challenges
//   → Copy 60 from reference_challenges (3-4s)
//   → Insert to challenge_pool with user_id
//   → Return challenges
//   → Fast, free ✅

// Case C: Pool has 10 challenges (< 50 threshold)
//   → Weekly cron will replenish next Monday
//   → OR trigger AI generation if urgent
```

---

## 6️⃣ **VERIFICATION CHECKLIST**

Run these checks to verify everything is correct:

```javascript
// ✅ Check 1: Reference challenges have NO user_id
db.reference_challenges.countDocuments({ user_id: { $exists: true } })
// Expected: 0

// ✅ Check 2: Challenge pool has user_id
db.challenge_pool.countDocuments({ user_id: { $exists: false } })
// Expected: 0

// ✅ Check 3: Reference challenges have language
db.reference_challenges.countDocuments({ language: { $exists: false } })
// Expected: 0

// ✅ Check 4: Challenge pool has language
db.challenge_pool.countDocuments({ language: { $exists: false } })
// Expected: 0

// ✅ Check 5: Challenge pool has status
db.challenge_pool.countDocuments({ status: { $exists: false } })
// Expected: 0

// ✅ Check 6: Check language distribution in reference
db.reference_challenges.aggregate([
  { $group: { _id: "$language", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
// Expected: 6 languages with roughly equal distribution

// ✅ Check 7: Sample challenge pool item for your user
db.challenge_pool.findOne({ user_id: "688921c268819565ef1ce3dc" })
// Should show: user_id, language, cefr_level, status, created_at
```

---

## 7️⃣ **COMMON QUERIES**

### **Find challenges for specific user:**
```javascript
db.challenge_pool.find({
  user_id: "688921c268819565ef1ce3dc",
  language: "english",
  cefr_level: "B1",
  status: "available"
}).limit(10).pretty()
```

### **Count available vs completed:**
```javascript
db.challenge_pool.aggregate([
  { $match: { user_id: "688921c268819565ef1ce3dc" } },
  { $group: { _id: "$status", count: { $sum: 1 } } }
])
```

### **Find reference challenges for specific language/level:**
```javascript
db.reference_challenges.find({
  language: "english",
  cefr_level: "B1",
  challenge_type: "error_spotting"
}).limit(5).pretty()
```

### **Check when challenge pool items were created:**
```javascript
db.challenge_pool.aggregate([
  {
    $project: {
      date: { $dateToString: { format: "%Y-%m-%d", date: "$created_at" } }
    }
  },
  { $group: { _id: "$date", count: { $sum: 1 } } },
  { $sort: { _id: -1 } },
  { $limit: 10 }
])
```

---

## 8️⃣ **EXPECTED OUTPUT**

### **Reference Challenges (4K):**
```javascript
{
  "_id": ObjectId("..."),
  "language": "english",
  "cefr_level": "B1",
  "challenge_type": "error_spotting",
  "content": { ... },
  "correct_answer": "...",
  "created_at": ISODate("2025-12-16T...")
  // ❌ NO user_id
  // ❌ NO status
}
```

### **Challenge Pool (1K):**
```javascript
{
  "_id": ObjectId("..."),
  "user_id": "688921c268819565ef1ce3dc",  // ✅ Has user_id
  "language": "english",
  "cefr_level": "B1",
  "challenge_type": "error_spotting",
  "status": "available",  // ✅ Has status
  "content": { ... },
  "correct_answer": "...",
  "created_at": ISODate("2025-12-17T..."),
  "expires_at": ISODate("2026-01-16T...")
}
```

---

## 🚀 **HOW TO RUN THESE COMMANDS**

### **Option 1: Railway Dashboard (Easiest)**
1. Go to Railway dashboard
2. Click on MongoDB service
3. Click "Connect" → "MongoDB Shell"
4. Paste commands above

### **Option 2: MongoDB Compass**
1. Connect with your MONGODB_URL
2. Select `language_tutor` database
3. Use "Aggregations" tab or "Shell" tab
4. Paste commands

### **Option 3: mongosh CLI**
```bash
mongosh "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@66.33.22.252:44437/language_tutor?authSource=admin"

# Then paste verification commands
```

---

## ✅ **SUMMARY**

**Two separate collections serving different purposes:**

1. **`reference_challenges` (4K)** = Library/Templates
   - No user_id, no status
   - Used for copying, not direct use
   - Generated once in Phase 1.5

2. **`challenge_pool` (1K)** = User Inventory
   - Has user_id and status
   - Used in Explore tab
   - Generated weekly OR on-demand

**They work together:** reference → copy/generate → challenge_pool → user

---

**Questions?** Run the verification commands above and share the output!
