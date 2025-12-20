# MongoDB Query Reference Guide

This guide provides **reusable MongoDB queries** to analyze documents by language and CEFR level in the `reference_challenges` and `challenge_pool` collections.

## Database Connection

```bash
# Connect to MongoDB using mongosh
mongosh "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@66.33.22.252:44437/language_tutor?authSource=admin"

# Or if already connected
use language_tutor
```

---

## 📚 REFERENCE CHALLENGES QUERIES

### 1. Count Documents by Language and Level

**Template:**
```javascript
db.reference_challenges.countDocuments({
  language: "LANGUAGE_HERE",
  cefr_level: "LEVEL_HERE"
})
```

**Examples:**
```javascript
// French A1
db.reference_challenges.countDocuments({
  language: "french",
  cefr_level: "A1"
})

// Dutch B2
db.reference_challenges.countDocuments({
  language: "dutch",
  cefr_level: "B2"
})

// Spanish A2
db.reference_challenges.countDocuments({
  language: "spanish",
  cefr_level: "A2"
})

// English B1
db.reference_challenges.countDocuments({
  language: "english",
  cefr_level: "B1"
})
```

### 2. Count All Documents for a Language (All Levels)

**Template:**
```javascript
db.reference_challenges.countDocuments({
  language: "LANGUAGE_HERE"
})
```

**Examples:**
```javascript
// All French challenges
db.reference_challenges.countDocuments({ language: "french" })

// All Dutch challenges
db.reference_challenges.countDocuments({ language: "dutch" })
```

### 3. Count All Documents for a Level (All Languages)

**Template:**
```javascript
db.reference_challenges.countDocuments({
  cefr_level: "LEVEL_HERE"
})
```

**Examples:**
```javascript
// All A1 challenges
db.reference_challenges.countDocuments({ cefr_level: "A1" })

// All B2 challenges
db.reference_challenges.countDocuments({ cefr_level: "B2" })
```

### 4. Count by Language, Level, AND Challenge Type

**Template:**
```javascript
db.reference_challenges.countDocuments({
  language: "LANGUAGE_HERE",
  cefr_level: "LEVEL_HERE",
  challenge_type: "TYPE_HERE"
})
```

**Examples:**
```javascript
// French A1 error spotting challenges
db.reference_challenges.countDocuments({
  language: "french",
  cefr_level: "A1",
  challenge_type: "error_spotting"
})

// Dutch B2 multiple choice challenges
db.reference_challenges.countDocuments({
  language: "dutch",
  cefr_level: "B2",
  challenge_type: "multiple_choice"
})
```

### 5. Get Complete Breakdown by Language and Level

```javascript
db.reference_challenges.aggregate([
  {
    $group: {
      _id: {
        language: "$language",
        level: "$cefr_level"
      },
      count: { $sum: 1 }
    }
  },
  {
    $sort: {
      "_id.language": 1,
      "_id.level": 1
    }
  }
])
```

### 6. Get Breakdown by Challenge Type for a Specific Language/Level

**Template:**
```javascript
db.reference_challenges.aggregate([
  {
    $match: {
      language: "LANGUAGE_HERE",
      cefr_level: "LEVEL_HERE"
    }
  },
  {
    $group: {
      _id: "$challenge_type",
      count: { $sum: 1 }
    }
  },
  {
    $sort: { count: -1 }
  }
])
```

**Example:**
```javascript
// Breakdown of French A1 challenges by type
db.reference_challenges.aggregate([
  {
    $match: {
      language: "french",
      cefr_level: "A1"
    }
  },
  {
    $group: {
      _id: "$challenge_type",
      count: { $sum: 1 }
    }
  },
  {
    $sort: { count: -1 }
  }
])
```

### 7. Find Sample Documents

**Template:**
```javascript
db.reference_challenges.find({
  language: "LANGUAGE_HERE",
  cefr_level: "LEVEL_HERE"
}).limit(5).pretty()
```

**Example:**
```javascript
// Get 5 sample French A1 challenges
db.reference_challenges.find({
  language: "french",
  cefr_level: "A1"
}).limit(5).pretty()
```

---

## 🎯 CHALLENGE POOL QUERIES

### 1. Count Documents by Language and Level

**Template:**
```javascript
db.challenge_pool.countDocuments({
  language: "LANGUAGE_HERE",
  cefr_level: "LEVEL_HERE"
})
```

**Examples:**
```javascript
// French A1 in challenge pool
db.challenge_pool.countDocuments({
  language: "french",
  cefr_level: "A1"
})

// Dutch B2 in challenge pool
db.challenge_pool.countDocuments({
  language: "dutch",
  cefr_level: "B2"
})
```

### 2. Count by Language, Level, AND Status

**Template:**
```javascript
db.challenge_pool.countDocuments({
  language: "LANGUAGE_HERE",
  cefr_level: "LEVEL_HERE",
  status: "STATUS_HERE"  // available, completed, expired
})
```

**Examples:**
```javascript
// Available French A1 challenges
db.challenge_pool.countDocuments({
  language: "french",
  cefr_level: "A1",
  status: "available"
})

// Completed Dutch B2 challenges
db.challenge_pool.countDocuments({
  language: "dutch",
  cefr_level: "B2",
  status: "completed"
})
```

### 3. Count for a Specific User

**Template:**
```javascript
db.challenge_pool.countDocuments({
  user_id: "USER_ID_HERE",
  language: "LANGUAGE_HERE",
  cefr_level: "LEVEL_HERE"
})
```

**Example:**
```javascript
// User's French A1 challenges
db.challenge_pool.countDocuments({
  user_id: "693f32dfbdb6ea2037d17895",
  language: "french",
  cefr_level: "A1"
})
```

### 4. Get Breakdown by Language, Level, and Status

```javascript
db.challenge_pool.aggregate([
  {
    $group: {
      _id: {
        language: "$language",
        level: "$cefr_level",
        status: "$status"
      },
      count: { $sum: 1 }
    }
  },
  {
    $sort: {
      "_id.language": 1,
      "_id.level": 1,
      "_id.status": 1
    }
  }
])
```

### 5. Get Status Breakdown for Specific Language/Level

**Template:**
```javascript
db.challenge_pool.aggregate([
  {
    $match: {
      language: "LANGUAGE_HERE",
      cefr_level: "LEVEL_HERE"
    }
  },
  {
    $group: {
      _id: "$status",
      count: { $sum: 1 }
    }
  }
])
```

**Example:**
```javascript
// Status breakdown for French A1
db.challenge_pool.aggregate([
  {
    $match: {
      language: "french",
      cefr_level: "A1"
    }
  },
  {
    $group: {
      _id: "$status",
      count: { $sum: 1 }
    }
  }
])
```

### 6. Count by User and Status

**Template:**
```javascript
db.challenge_pool.countDocuments({
  user_id: "USER_ID_HERE",
  status: "STATUS_HERE"
})
```

**Example:**
```javascript
// User's available challenges
db.challenge_pool.countDocuments({
  user_id: "693f32dfbdb6ea2037d17895",
  status: "available"
})
```

---

## 📊 COMBINED STATISTICS QUERIES

### 1. Compare Reference vs Pool for a Language/Level

**Template (run these two queries):**
```javascript
// Reference challenges count
var refCount = db.reference_challenges.countDocuments({
  language: "LANGUAGE_HERE",
  cefr_level: "LEVEL_HERE"
})

// Challenge pool count
var poolCount = db.challenge_pool.countDocuments({
  language: "LANGUAGE_HERE",
  cefr_level: "LEVEL_HERE"
})

// Display results
print("Reference: " + refCount)
print("Pool: " + poolCount)
```

**Example:**
```javascript
// French A1 comparison
var refCount = db.reference_challenges.countDocuments({
  language: "french",
  cefr_level: "A1"
})

var poolCount = db.challenge_pool.countDocuments({
  language: "french",
  cefr_level: "A1"
})

print("French A1 - Reference: " + refCount)
print("French A1 - Pool: " + poolCount)
```

### 2. Get All Available Languages

```javascript
// From reference_challenges
db.reference_challenges.distinct("language")

// From challenge_pool
db.challenge_pool.distinct("language")
```

### 3. Get All Available CEFR Levels

```javascript
// From reference_challenges
db.reference_challenges.distinct("cefr_level")

// From challenge_pool
db.challenge_pool.distinct("cefr_level")
```

### 4. Get All Challenge Types

```javascript
db.reference_challenges.distinct("challenge_type")
```

---

## 🔍 ADVANCED QUERIES

### 1. Find Empty Combinations (No Documents)

```javascript
// Check if a specific combination exists
db.reference_challenges.countDocuments({
  language: "french",
  cefr_level: "C2"
}) === 0 ? "No documents found" : "Documents exist"
```

### 2. Get Most Common Challenge Types by Language

**Template:**
```javascript
db.reference_challenges.aggregate([
  {
    $match: { language: "LANGUAGE_HERE" }
  },
  {
    $group: {
      _id: "$challenge_type",
      count: { $sum: 1 }
    }
  },
  {
    $sort: { count: -1 }
  }
])
```

### 3. Get Total Challenges Per Language (All Collections)

```javascript
// Use a function to combine counts
function getTotalByLanguage(lang) {
  var ref = db.reference_challenges.countDocuments({ language: lang })
  var pool = db.challenge_pool.countDocuments({ language: lang })
  print(lang + " - Reference: " + ref + ", Pool: " + pool + ", Total: " + (ref + pool))
}

// Usage
getTotalByLanguage("french")
getTotalByLanguage("dutch")
getTotalByLanguage("spanish")
```

---

## 📝 QUICK REFERENCE TABLE

| Collection | Field | Values |
|------------|-------|--------|
| `reference_challenges` | `language` | "french", "dutch", "spanish", "english", etc. |
| `reference_challenges` | `cefr_level` | "A1", "A2", "B1", "B2", "C1", "C2" |
| `reference_challenges` | `challenge_type` | "error_spotting", "fill_blank", "multiple_choice", etc. |
| `challenge_pool` | `language` | "french", "dutch", "spanish", "english", etc. |
| `challenge_pool` | `cefr_level` | "A1", "A2", "B1", "B2", "C1", "C2" |
| `challenge_pool` | `status` | "available", "completed", "expired" |

---

## 💡 Tips for Reusable Queries

1. **Case Sensitivity**:
   - `language` field is lowercase: `"french"`, `"dutch"`
   - `cefr_level` field is uppercase: `"A1"`, `"B2"`

2. **Save Frequently Used Queries**: Create shell functions
   ```javascript
   // Add to ~/.mongoshrc.js
   function countRL(lang, level) {
     return db.reference_challenges.countDocuments({
       language: lang,
       cefr_level: level
     })
   }

   // Usage: countRL("french", "A1")
   ```

3. **Export Results to File**:
   ```bash
   mongosh "YOUR_CONNECTION_STRING" --eval 'db.reference_challenges.countDocuments({language: "french", cefr_level: "A1"})' > results.txt
   ```

---

## 🚀 Python Script Usage

For programmatic access, use the `query_helpers.py` script:

```bash
cd backend
python query_helpers.py
```

Or import in your Python code:
```python
from query_helpers import count_reference_challenges_by_language_and_level

count = await count_reference_challenges_by_language_and_level("french", "A1")
print(f"French A1 challenges: {count}")
```

---

**Last Updated**: 2025-12-20
