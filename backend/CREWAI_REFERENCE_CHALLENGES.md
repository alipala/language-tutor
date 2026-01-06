# CrewAI Reference Challenge System

## Overview

This system generates high-quality, AI-powered reference challenges for freestyle practice mode using CrewAI's multi-agent framework.

## Configuration

### Environment Variables

```bash
# Generation frequency
REFERENCE_GENERATION_FREQUENCY=weekly   # Options: weekly, biweekly, monthly

# Target pool size per language/level/type combination
REFERENCE_POOL_SIZE=50                  # Default: 50 challenges per type
```

### Supported Combinations

- **Languages**: 6 (english, spanish, french, german, italian, portuguese)
- **CEFR Levels**: 6 (A1, A2, B1, B2, C1, C2)
- **Challenge Types**: 7 (error_spotting, swipe_fix, micro_quiz, smart_flashcard, native_check, brain_tickler)
- **Total Combinations**: 6 × 6 × 7 = **252 combinations**

With `REFERENCE_POOL_SIZE=50`, the system maintains a pool of **12,600 unique challenges** across all combinations.

## Preventing Duplicate Challenges

### Problem
Users were seeing the same challenges repeatedly in freestyle mode.

### Solution
The system uses a **large pool strategy** with user tracking:

1. **Large Pool Size**: Default 50 challenges per type ensures variety
2. **Smart Selection**: API endpoint should track completed challenges per user
3. **Random Selection**: Pick from pool excluding user's completed challenges

### API Implementation

When fetching freestyle challenges, use this strategy:

```python
async def get_freestyle_challenge(user_id: str, language: str, level: str, challenge_type: str):
    """
    Get a freestyle challenge that user hasn't completed
    """
    # Get user's completed challenge IDs
    completed_ids = await get_user_completed_reference_challenges(user_id, language, level, challenge_type)

    # Query for active challenges NOT in completed list
    challenge = await database.reference_challenges.find_one({
        "language": language,
        "cefr_level": level,
        "challenge_type": challenge_type,
        "is_active": True,
        "_id": {"$nin": completed_ids}  # Exclude completed
    })

    # If all completed, reset and pick any
    if not challenge:
        challenge = await database.reference_challenges.find_one({
            "language": language,
            "cefr_level": level,
            "challenge_type": challenge_type,
            "is_active": True
        })

    return challenge
```

### User Tracking Collection

```javascript
// collection: user_reference_progress
{
  user_id: "688921c268819565ef1ce3dc",
  language: "english",
  cefr_level: "A2",
  challenge_type: "brain_tickler",
  completed_challenge_ids: [
    ObjectId("..."),
    ObjectId("..."),
    // ... up to 50 IDs
  ],
  last_reset: ISODate("2026-01-05T23:00:00Z"),  // When pool was refreshed
  updated_at: ISODate("2026-01-05T23:30:00Z")
}
```

When user completes a challenge, add its `_id` to this array. When array reaches pool size, reset it.

## Generation Schedule

### Weekly (7 days)
- **Best for**: Active user base, frequent new content
- **Cost**: ~$15-20/week (252 combinations × 10 challenges/batch)
- **Pool refresh**: Every 7 days

### Biweekly (14 days)
- **Best for**: Moderate user base, balanced cost
- **Cost**: ~$15-20/2 weeks
- **Pool refresh**: Every 14 days

### Monthly (30 days)
- **Best for**: Budget-conscious, stable pool
- **Cost**: ~$15-20/month
- **Pool refresh**: Every 30 days

## Cost Calculation

- **Per challenge**: ~$0.05 (3 agents)
- **Per batch** (10 challenges): ~$0.50
- **Per combination**: ~$0.50
- **Full generation** (252 combinations): ~$126

However, with TARGET_POOL_SIZE=50 and incremental replenishment:
- Only generates when below target
- After initial fill, weekly cost is much lower (~$5-10)

## Testing

### Test Single Combination
```bash
python generate_reference_challenges_crew.py test english A2 brain_tickler 3
```

### Full Generation (All Combinations)
```bash
# Set environment variables first
export REFERENCE_GENERATION_FREQUENCY=weekly
export REFERENCE_POOL_SIZE=50

# Run full generation
python generate_reference_challenges_crew.py
```

⚠️ **Warning**: Full generation takes several hours and costs ~$126 initially.

## Railway Deployment

### 1. Set Environment Variables in Railway

```bash
REFERENCE_GENERATION_FREQUENCY=biweekly
REFERENCE_POOL_SIZE=50
```

### 2. Schedule Cron Job

Add to Railway scheduler service:

```bash
# Biweekly: Every 2 weeks on Monday at 2 AM UTC
0 2 * * 1 cd /app && python generate_reference_challenges_crew.py

# Weekly: Every Monday at 2 AM UTC
0 2 * * 1 cd /app && python generate_reference_challenges_crew.py

# Monthly: First Monday of month at 2 AM UTC
0 2 1-7 * 1 cd /app && python generate_reference_challenges_crew.py
```

## Monitoring

After each generation, check logs for:

```
✅ BIWEEKLY REFERENCE GENERATION COMPLETE
Total generated: 450 challenges
Completed at: 2026-01-06 02:35:42 UTC
Next run: 2026-01-20 02:35:42 UTC (14 days)
```

## Database Collections

### reference_challenges
```javascript
{
  _id: ObjectId("..."),
  language: "english",
  cefr_level: "A2",
  challenge_type: "brain_tickler",
  challenge_data: {
    id: "challenge_1_76ebbcfa",
    type: "brain_tickler",
    title: "Past Tense Puzzle",
    // ... full challenge data
  },
  created_at: ISODate("2026-01-05T23:32:01Z"),
  source: "crewai_reference_generator",
  is_active: true
}
```

### Indexes Needed

```javascript
// For fast challenge lookup
db.reference_challenges.createIndex({
  "language": 1,
  "cefr_level": 1,
  "challenge_type": 1,
  "is_active": 1
})

// For user progress tracking
db.user_reference_progress.createIndex({
  "user_id": 1,
  "language": 1,
  "cefr_level": 1,
  "challenge_type": 1
})
```

## FAQ

### Q: Will users see duplicate challenges?
**A**: No, if:
1. Pool size is adequate (50+ per type)
2. API tracks completed challenges per user
3. Random selection excludes completed

### Q: How often should I generate?
**A**:
- High activity (1000+ daily users): Weekly
- Medium activity (100-1000 users): Biweekly
- Low activity (<100 users): Monthly

### Q: Can I generate for specific languages only?
**A**: Yes, modify `LANGUAGES` list in the script before running.

### Q: Does CrewAI support all languages and levels?
**A**: Yes! CrewAI agents are language-agnostic. They generate native content for all 6 languages at all 6 CEFR levels.

## Next Steps

1. ✅ Set environment variables
2. ⏳ Run initial test generation
3. ⏳ Set up Railway cron job
4. ⏳ Implement API endpoint with duplicate prevention
5. ⏳ Add user progress tracking collection
6. ⏳ Monitor costs and adjust frequency
