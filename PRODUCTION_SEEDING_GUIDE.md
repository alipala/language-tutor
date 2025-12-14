# 🚀 Production Challenge Pool Seeding Guide

## Quick Answer to Your Questions

### Q1: "How do scripts identify users to generate perfect challenges?"

**Answer:** The AI analyzes EACH user's actual learning data:

```python
# For EACH user, the AI analyzes:
1. Practice sessions (last 10) → Grammar mistakes, error patterns
2. Weak flashcards (mastery < 50%) → Vocabulary struggles
3. Learning plans → Current focus topics
4. CEFR level → User's preferred level (A1-C2)

# Then GPT-4 generates personalized challenges based on this data
```

**For new users with no data:**
- AI generates level-appropriate generic challenges
- As they practice, future challenges become more personalized

---

### Q2: "Some users are not active. What do we need to do?"

**Answer:** I created a SMART script that only seeds active users!

**Active user criteria:**
- ✅ Has active subscription (status: `active` or `trialing`)
- ✅ OR has practice sessions in last 30 days
- ❌ Excludes test/demo accounts

---

### Q3: "What do we need to do to generate challenges at midnight?"

**Answer:** Daily replenishment job (already created and updated!)

The replenisher:
- Runs at 2 AM daily (via scheduler or cron)
- Only replenishes ACTIVE users
- Only generates what's needed (efficient)
- Keeps pools at target level (50 per type)

---

## 📋 Step-by-Step: Seed Production NOW

### Step 1: Preview Which Users Will Be Seeded

```bash
cd /Users/alipala/CascadeProjects/language-tutor/backend

# See which users would be seeded (no generation, just preview)
python seed_production_smart.py list
```

**Output:**
```
USERS THAT WOULD BE SEEDED:
======================================================================

1. user1@example.com
   Level: B1 | Reason: subscription

2. user2@example.com
   Level: A2 | Reason: 5 sessions in 30d

3. user3@example.com
   Level: C1 | Reason: subscription

======================================================================
Total: 15 active users
======================================================================
```

---

### Step 2: Seed Active Users

```bash
# Start small (10 per type = 60 total) - FASTEST
python seed_production_smart.py active 10

# Or medium (25 per type = 150 total) - RECOMMENDED
python seed_production_smart.py active 25

# Or full (50 per type = 300 total)
python seed_production_smart.py active 50
```

**What happens:**
1. ✅ Connects to production MongoDB
2. ✅ Asks for confirmation
3. ✅ Filters to active users only
4. ✅ Shows progress for each user
5. ✅ Generates personalized challenges using AI
6. ✅ Saves to production database

---

### Step 3: Verify It Worked

Check one user's challenges in production:

```bash
# In MongoDB shell or Compass
use language_tutor

# Count challenges for a user
db.challenge_pool.aggregate([
  { $match: { user_id: "USER_ID_HERE", status: "available" } },
  { $group: { _id: "$challenge_type", count: { $sum: 1 } } }
])

# Expected output:
# { "_id": "error_spotting", "count": 10 }
# { "_id": "swipe_fix", "count": 10 }
# ... etc
```

---

## ⏰ Set Up Automatic Midnight Replenishment

### Option 1: Run Scheduler as Service (Recommended)

The scheduler runs continuously and triggers replenishment at 2 AM daily.

```bash
# Install schedule package
pip install schedule

# Run scheduler (keeps running in background)
python run_scheduler.py
```

**For Production (systemd):**

Create `/etc/systemd/system/challenge-replenisher.service`:

```ini
[Unit]
Description=Challenge Pool Replenisher
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/backend
Environment="MONGODB_URL=your_production_url"
Environment="OPENAI_API_KEY=your_openai_key"
ExecStart=/path/to/python run_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable challenge-replenisher
sudo systemctl start challenge-replenisher

# Check status
sudo systemctl status challenge-replenisher

# View logs
sudo journalctl -u challenge-replenisher -f
```

---

### Option 2: Cron Job (Simple)

```bash
# Edit crontab
crontab -e

# Add this line (runs at 2 AM daily)
0 2 * * * cd /path/to/backend && /path/to/python challenge_pool_replenisher.py >> /var/log/challenge-replenish.log 2>&1
```

---

## 🎯 How Personalization Works (Detailed)

### Example: User with Activity

**User:** john@example.com (Level: B1)

**AI analyzes:**
```
Practice Sessions (last 10):
- Struggled with: past perfect tense
- Common mistake: "I have went" → "I have gone"
- Vocabulary gaps: business English terms

Weak Flashcards:
- "negotiate" (mastery: 30%)
- "deadline" (mastery: 25%)

Learning Plan:
- Current focus: "Business Communication"
- Week 3 goal: "Emails and meetings"
```

**AI generates:**
```json
{
  "id": "ai_es_123",
  "type": "error_spotting",
  "sentence": "Yesterday I have went to the meeting.",
  "explanation": "Use 'went' (past simple), not 'have gone' with 'yesterday'",
  "tags": ["past_perfect", "time_expressions"],
  "cefrLevel": "B1"
}

{
  "id": "ai_sf_456",
  "type": "smart_flashcard",
  "word": "negotiate",
  "context": "business communication",
  "explanation": "To reach an agreement through discussion",
  "exampleSentence": "We need to negotiate the contract terms."
}
```

### Example: New User (No Activity)

**User:** jane@example.com (Level: A2)

**AI generates:**
- Level-appropriate generic challenges
- Common A2 grammar topics (present simple, past simple, articles)
- Essential A2 vocabulary
- As she practices, challenges become personalized

---

## 📊 Performance & Costs

### Initial Seeding (One-Time)

| Users | Challenges/Type | Time per User | Total Time | OpenAI Cost |
|-------|-----------------|---------------|------------|-------------|
| 10 | 10 | 5 min | 50 min | ~$1 |
| 10 | 25 | 12 min | 2 hours | ~$2.50 |
| 10 | 50 | 25 min | 4 hours | ~$5 |

**OpenAI Cost:** ~$0.10 per user for 50 challenges (300 total)

### Daily Replenishment

**Example:** User completes 6 challenges per day

| Day | Completed | Available | Need to Generate |
|-----|-----------|-----------|------------------|
| Day 1 | 6 | 294 (50-6=44 per type) | 6 |
| Day 2 | 6 | 294 | 6 |
| Day 7 | 42 | 258 | 42 |

**Cost:** Only generate what's used
- Active user (6/day): ~$0.012/day
- Inactive user: $0 (nothing to replenish)

---

## 🚨 Important Notes

### DO NOT Seed:
- ❌ Test accounts (email contains "test" or "demo")
- ❌ Inactive users (no subscription, no recent activity)
- ❌ Users who already have full pools

### DO Seed:
- ✅ Users with active subscriptions
- ✅ Users with recent practice sessions
- ✅ Real production users

### The Smart Script Handles This Automatically!

```bash
# This script automatically filters to active users only
python seed_production_smart.py active 25
```

---

## 🔍 Monitoring & Verification

### Check Pool Status

```bash
# In MongoDB
db.challenge_pool.aggregate([
  { $match: { status: "available" } },
  { $group: {
      _id: { user_id: "$user_id", type: "$challenge_type" },
      count: { $sum: 1 }
  }}
])
```

### Check Replenishment Logs

```bash
# If using systemd
sudo journalctl -u challenge-replenisher -f

# If using cron
tail -f /var/log/challenge-replenish.log
```

### Test API Endpoints

```bash
# Get counts
curl -H "Authorization: Bearer TOKEN" \
  https://your-api.com/api/challenges/counts

# Get challenges
curl -H "Authorization: Bearer TOKEN" \
  https://your-api.com/api/challenges/by-type/error_spotting?limit=10
```

---

## 📖 Complete Command Reference

### Seed Production (Smart)

```bash
# Preview active users (no generation)
python seed_production_smart.py list

# Seed active users only
python seed_production_smart.py active 10   # Fast (5 min/user)
python seed_production_smart.py active 25   # Recommended (12 min/user)
python seed_production_smart.py active 50   # Full (25 min/user)

# Seed specific user
python seed_production_smart.py user email@example.com 25
```

### Daily Replenishment

```bash
# Run once manually
python challenge_pool_replenisher.py

# Run scheduler (continuous)
python run_scheduler.py
```

### Test Locally

```bash
# Test with local user
python test_challenge_pool.py
```

---

## ✅ Recommended Workflow

### Initial Setup (Today)

1. **Preview users:**
   ```bash
   python seed_production_smart.py list
   ```

2. **Start small:**
   ```bash
   python seed_production_smart.py active 10
   ```

3. **Verify in production:**
   - Check MongoDB: challenges exist
   - Test API: `/api/challenges/counts`
   - Test iOS app: challenges display

4. **Scale up:**
   ```bash
   python seed_production_smart.py active 25
   ```

### Ongoing (Daily)

1. **Set up scheduler:**
   ```bash
   # Option 1: systemd service (production)
   sudo systemctl start challenge-replenisher

   # Option 2: cron (simple)
   # Add to crontab: 0 2 * * * ...
   ```

2. **Monitor logs:**
   - Check replenishment runs successfully
   - Verify only active users are processed

3. **User experience:**
   - Users always have 50 challenges per type
   - Challenges refresh as they complete them
   - New challenges generated at 2 AM daily

---

## 🆘 Troubleshooting

### "No users found"
- Check `.env` has correct `MONGODB_URL`
- Verify users exist in production: `db.users.count()`

### "AI generation failed"
- Check `OPENAI_API_KEY` in `.env`
- Verify OpenAI API has credits

### "Challenges not showing in iOS"
- Verify user authentication token is valid
- Check backend logs for API calls
- Verify challenges exist: `db.challenge_pool.find({user_id: "..."})`

### "Replenishment not running"
- Check scheduler process is running
- View logs: `journalctl -u challenge-replenisher`
- Test manually: `python challenge_pool_replenisher.py`

---

## 📞 Support

**Questions?**
- Check `/CHALLENGE_POOL_SYSTEM.md` for detailed API docs
- Run `python seed_production_smart.py` for help
- Check backend logs with `[CHALLENGE_POOL]` prefix

**Ready to seed production! 🎉**
