# Environment Variables Configuration Guide

## 🎛️ Complete Configuration for CrewAI Challenge Generation

All challenge generation is now controlled by environment variables. Set these in your Railway Scheduler Service.

---

## 📊 Environment Variables Summary

| Variable | Options | Default | What It Controls |
|----------|---------|---------|------------------|
| `USE_CREWAI` | `true`, `false` | `false` | Enable CrewAI for user challenges |
| `USER_POOL_FREQUENCY` | `daily`, `weekly`, `biweekly`, `monthly` | `daily` | How often to replenish user pools |
| `REFERENCE_GENERATION_FREQUENCY` | `weekly`, `biweekly`, `monthly` | `weekly` | How often to generate reference challenges |
| `REFERENCE_POOL_SIZE` | Any number | `50` | Target pool size per type |

---

## 🎯 System 1: User Challenge Pool Replenishment

**What it does:** Fills each user's personal challenge pool with personalized challenges

**Runs at:** 2:00 AM UTC

**Frequency:** Controlled by `USER_POOL_FREQUENCY`

### Configuration:

```bash
# Enable CrewAI for better quality (optional)
USE_CREWAI=true

# How often to replenish (required)
USER_POOL_FREQUENCY=biweekly
```

### Options for USER_POOL_FREQUENCY:

| Value | Runs Every | Use Case | Cost per Run |
|-------|-----------|----------|--------------|
| `daily` | 1 day | High activity, need fresh challenges daily | High |
| `weekly` | 7 days | Medium activity | Medium |
| `biweekly` | 14 days | Low activity, cost-conscious | Low |
| `monthly` | 30 days | Very low activity, minimal cost | Very low |

### Cost Calculation:

**With USE_CREWAI=false (Simple AI):**
- Cost per challenge: ~$0.01
- Example (100 users, 7 types): 100 × 7 × $0.01 = ~$7 per run

**With USE_CREWAI=true (CrewAI):**
- Cost per challenge: ~$0.05
- Example (100 users, 7 types): 100 × 7 × $0.05 = ~$35 per run

---

## 🎯 System 2: Reference Challenge Generation

**What it does:** Fills the `reference_challenges` collection for freestyle practice

**Runs at:** 3:00 AM UTC

**Frequency:** Controlled by `REFERENCE_GENERATION_FREQUENCY`

### Configuration:

```bash
# How often to generate (required)
REFERENCE_GENERATION_FREQUENCY=biweekly

# Pool size per type (optional)
REFERENCE_POOL_SIZE=50
```

### Options for REFERENCE_GENERATION_FREQUENCY:

| Value | Runs Every | Use Case | Initial Cost |
|-------|-----------|----------|--------------|
| `weekly` | 7 days | High user base, need fresh content | ~$126 initial, ~$10/week |
| `biweekly` | 14 days | Medium user base, balanced | ~$126 initial, ~$5/2 weeks |
| `monthly` | 30 days | Low user base, cost-conscious | ~$126 initial, ~$5/month |

### Cost Calculation:

**Initial Fill (First Run):**
- 6 languages × 6 levels × 7 types × 50 challenges = 12,600 challenges
- Cost: 12,600 × $0.05 = ~$630

**Wait, that's expensive!**

Actually, it only generates what's NEEDED. If you already have 1,000+ challenges per type, it will only top up to 50 per type:
- Needed: ~500-1000 challenges (to balance story_builder)
- Cost: ~$25-50

**Ongoing (After Initial Fill):**
- Only replenishes used challenges
- Cost: ~$5-10 per run

---

## 🚀 Recommended Configurations

### Budget-Conscious (Minimize Costs)

```bash
USE_CREWAI=false
USER_POOL_FREQUENCY=weekly
REFERENCE_GENERATION_FREQUENCY=monthly
REFERENCE_POOL_SIZE=30
```

**Monthly cost:** ~$35-50
- User pool: ~$7/week × 4 = $28
- Reference: ~$5/month = $5

---

### Balanced (Quality + Cost)

```bash
USE_CREWAI=true
USER_POOL_FREQUENCY=biweekly
REFERENCE_GENERATION_FREQUENCY=biweekly
REFERENCE_POOL_SIZE=50
```

**Monthly cost:** ~$75-100
- User pool: ~$35 every 2 weeks × 2 = $70
- Reference: ~$5 every 2 weeks × 2 = $10

---

### Premium (Best Quality)

```bash
USE_CREWAI=true
USER_POOL_FREQUENCY=daily
REFERENCE_GENERATION_FREQUENCY=weekly
REFERENCE_POOL_SIZE=75
```

**Monthly cost:** ~$1,000+
- User pool: ~$35/day × 30 = $1,050
- Reference: ~$10/week × 4 = $40

---

## 📅 How the Scheduler Works

### Daily Check at 2:00 AM UTC (User Pool)

1. Job triggers at 2:00 AM
2. Checks `USER_POOL_FREQUENCY` setting
3. Calculates: "Should I run today?"
   - `daily` → runs every day
   - `weekly` → runs every 7 days
   - `biweekly` → runs every 14 days
   - `monthly` → runs every 30 days
4. If yes, replenishes all users' pools
5. Uses CrewAI if `USE_CREWAI=true`

### Daily Check at 3:00 AM UTC (Reference)

1. Job triggers at 3:00 AM
2. Checks `REFERENCE_GENERATION_FREQUENCY` setting
3. Calculates: "Should I run today?"
   - `weekly` → runs every 7 days
   - `biweekly` → runs every 14 days
   - `monthly` → runs every 30 days
4. If yes, generates reference challenges
5. Always uses CrewAI (high quality)

---

## 🔧 Your Current Settings

Based on your Railway environment variables:

```bash
USE_CREWAI=true
REFERENCE_GENERATION_FREQUENCY=biweekly
REFERENCE_POOL_SIZE=50
```

### What's Missing:

❌ `USER_POOL_FREQUENCY` - **ADD THIS!**

Without it, defaults to `daily` which means:
- User pool replenishes DAILY at 2 AM
- With CrewAI enabled
- Costs ~$35/day = ~$1,050/month 💸

---

## ✅ Recommended Configuration for You

```bash
# Enable CrewAI for quality
USE_CREWAI=true

# Set user pool to biweekly (same as reference)
USER_POOL_FREQUENCY=biweekly

# Reference generation (already set)
REFERENCE_GENERATION_FREQUENCY=biweekly

# Pool size (already set)
REFERENCE_POOL_SIZE=50
```

**This gives you:**
- ✅ High quality with CrewAI
- ✅ Consistent biweekly schedule
- ✅ Reasonable cost (~$75-100/month)
- ✅ Fresh challenges every 2 weeks

---

## 🎯 How to Set in Railway

1. Go to Railway Dashboard
2. Select your **Scheduler Service** (not main API)
3. Click **Variables** tab
4. Add/Update these variables:

```
USE_CREWAI=true
USER_POOL_FREQUENCY=biweekly
REFERENCE_GENERATION_FREQUENCY=biweekly
REFERENCE_POOL_SIZE=50
```

5. Click **Redeploy**

---

## 📊 Monitoring

### Check Logs After Deployment

Look for this startup message:

```
================================================================================
[SCHEDULER] 🚀 Background Job Scheduler Started
[SCHEDULER] 📅 Started at: 2026-01-06 12:00:00
================================================================================
[SCHEDULER] Configuration:
  🔄 User pool replenishment: biweekly at 02:00 AM UTC
  🤖 CrewAI for users: ENABLED
  📖 Reference generation: biweekly at 03:00 AM UTC
  🔔 Heart refill check: Every 30 minutes
  📚 Practice reminders: Every hour
================================================================================
```

### When Jobs Run

Check logs at:
- 2:00-2:30 AM UTC for user pool
- 3:00-5:00 AM UTC for reference generation

Look for:
```
[SCHEDULER] ⏰ User Pool Replenishment Triggered
[SCHEDULER] 🔄 Frequency: biweekly
```

Or if skipping:
```
[SCHEDULER] ⏭️ Skipping user pool replenishment (frequency: biweekly, next run in 12 days)
```

---

## 🚨 Troubleshooting

### Jobs Running Too Often (Daily Instead of Biweekly)

**Problem:** Forgot to set `USER_POOL_FREQUENCY`

**Solution:** Add `USER_POOL_FREQUENCY=biweekly` to Railway

---

### Jobs Not Running At All

**Problem:** Scheduler service might be down

**Solution:**
1. Check Railway logs
2. Ensure scheduler service is running
3. Check for errors at 2 AM and 3 AM UTC

---

### High Costs

**Problem:** Running daily with CrewAI

**Solutions:**
- Set `USER_POOL_FREQUENCY=weekly` or `biweekly`
- OR set `USE_CREWAI=false` (lower quality but cheaper)

---

## 🔄 Migration Guide

### If You Just Merged

**Before (hardcoded daily):**
- User pool: DAILY at 2 AM
- Reference: NOT SCHEDULED

**After (configurable):**
- User pool: Checks `USER_POOL_FREQUENCY` daily
- Reference: Checks `REFERENCE_GENERATION_FREQUENCY` daily

**Action Required:**
Add `USER_POOL_FREQUENCY=biweekly` to prevent daily runs!

---

## 📞 Quick Reference

### Disable Everything:
```bash
USE_CREWAI=false
USER_POOL_FREQUENCY=monthly
REFERENCE_GENERATION_FREQUENCY=monthly
```

### Enable Everything (Expensive):
```bash
USE_CREWAI=true
USER_POOL_FREQUENCY=daily
REFERENCE_GENERATION_FREQUENCY=weekly
```

### Recommended (Balanced):
```bash
USE_CREWAI=true
USER_POOL_FREQUENCY=biweekly
REFERENCE_GENERATION_FREQUENCY=biweekly
REFERENCE_POOL_SIZE=50
```

---

## ✅ Summary

You now have **FULL CONTROL** over:

1. ✅ User challenge quality (CrewAI on/off)
2. ✅ User pool frequency (daily/weekly/biweekly/monthly)
3. ✅ Reference generation frequency (weekly/biweekly/monthly)
4. ✅ Reference pool size (any number)

**All controlled by environment variables in Railway!** 🎉
