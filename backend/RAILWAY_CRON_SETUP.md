# Railway Cron Job Setup for Challenge Replenishment

## 🚂 Overview

Automatically replenish challenge pools for active users daily at 2 AM UTC.

**How it works:**
- Railway runs `challenge_pool_replenisher.py` on schedule
- Script checks all active users
- Replenishes pools that are running low
- Script exits (no service running 24/7)

---

## ✅ Prerequisites

- [ ] Backend code merged to `main` branch
- [ ] Railway project already exists
- [ ] Environment variables configured in main service

---

## 🎯 Step-by-Step Setup

### Step 1: Create New Railway Service

1. Go to your Railway dashboard: https://railway.app
2. Open your existing project (language-tutor)
3. Click **"+ New"** button
4. Select **"Empty Service"**
5. Name it: **`challenge-replenisher`**

### Step 2: Connect to GitHub Repo

1. In the new service, click **"Settings"**
2. Scroll to **"Source"** section
3. Click **"Connect Repo"**
4. Select your repo: `alipala/language-tutor`
5. Set **Root Directory:** `backend` (important!)
6. Click **"Connect"**

### Step 3: Configure Service

#### 3a. Set Start Command

In **Settings → Deploy:**

**Start Command:**
```bash
python challenge_pool_replenisher.py
```

**Build Command:** (leave default)
```bash
pip install -r requirements.txt
```

#### 3b. Add Environment Variables

In **Settings → Variables**, add these (copy from your main backend service):

**Required:**
- `MONGODB_URL` - Your MongoDB connection string
- `OPENAI_API_KEY` - Your OpenAI API key
- `DATABASE_NAME` - Usually `language_tutor`

**Click "Add Variable" for each one**

### Step 4: Configure Cron Schedule

⚠️ **IMPORTANT:** Railway cron jobs require **Railway Pro plan** ($20/month)

If you have Pro plan:

1. In **Settings**, scroll to **"Cron Schedule"**
2. Enable cron schedule
3. Enter schedule: `0 2 * * *`

**Cron Schedule Options:**
```
0 2 * * *   # Daily at 2 AM UTC
0 6 * * *   # Daily at 6 AM UTC (6 PM PST)
0 */12 * * * # Every 12 hours
0 0 * * 0   # Weekly on Sunday at midnight
```

**Cron Format:**
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-6, Sunday=0)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Step 5: Disable Always-On Service

This service should ONLY run on schedule, not 24/7:

1. In **Settings → Deploy**
2. Find **"Restart Policy"**
3. Set to **"Never"** (service exits after each run)

### Step 6: Deploy

1. Click **"Deploy"** in the top right
2. Wait for build to complete
3. Check **"Deployments"** tab for status

### Step 7: Test the Cron Job

**Manual Test:**
1. Go to **"Deployments"** tab
2. Click **"Redeploy"** button
3. Check logs for output:
   ```
   [REPLENISHER] 🔄 Starting challenge pool replenishment...
   [REPLENISHER] 👥 Found 7 active users to replenish
   [REPLENISHER] ✅ User 1/7: alipala.ist@gmail.com - Generated 30 challenges
   [REPLENISHER] 🎉 Replenishment complete! Processed 7 users
   ```

**Verify Cron Schedule:**
- Wait for scheduled time (2 AM UTC)
- Check **"Deployments"** tab for automatic run
- Review logs to confirm it executed

---

## 🎛️ Alternative: Manual Cron (If No Pro Plan)

If you don't have Railway Pro, run manually from your local machine:

### Option A: Use macOS/Linux Crontab

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM local time)
0 2 * * * cd /Users/alipala/CascadeProjects/language-tutor/backend && /usr/local/bin/python3 challenge_pool_replenisher.py >> /tmp/challenge_replenisher.log 2>&1
```

### Option B: Use GitHub Actions (Free)

Create `.github/workflows/challenge-replenisher.yml`:

```yaml
name: Daily Challenge Replenishment

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  replenish:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        working-directory: ./backend
        run: |
          pip install -r requirements.txt

      - name: Run replenisher
        working-directory: ./backend
        env:
          MONGODB_URL: ${{ secrets.MONGODB_URL }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          DATABASE_NAME: ${{ secrets.DATABASE_NAME }}
        run: |
          python challenge_pool_replenisher.py
```

Add secrets in GitHub repo settings:
- `MONGODB_URL`
- `OPENAI_API_KEY`
- `DATABASE_NAME`

---

## 📊 Monitoring

### Check Replenishment Logs

**Railway Dashboard:**
1. Go to `challenge-replenisher` service
2. Click **"Deployments"**
3. Click latest deployment
4. View logs

**Expected Output:**
```
[REPLENISHER] 🔄 Starting challenge pool replenishment...
[REPLENISHER] 📊 Connected to MongoDB
[REPLENISHER] 👥 Scanning users for replenishment...
[REPLENISHER] 📋 Found 7 active users (subscription OR recent activity)
[REPLENISHER] ✅ User 1/7: alipala.ist@gmail.com - Generated 30 challenges
[REPLENISHER] ✅ User 2/7: test@example.com - Generated 30 challenges
[REPLENISHER] 🎉 Replenishment complete! Processed 7 users in 3.2 minutes
```

### Monitor User Pools

Check challenge pool counts:

```javascript
// MongoDB query
db.challenge_pool.aggregate([
  { $match: { status: "available" } },
  { $group: {
      _id: { user_id: "$user_id", type: "$challenge_type" },
      count: { $sum: 1 }
  }}
])
```

---

## ⚙️ Configuration

### Adjust Replenishment Settings

Edit `challenge_pool_helpers.py`:

```python
MIN_CHALLENGES_PER_TYPE = 10  # Trigger replenishment below this
TARGET_CHALLENGES_PER_TYPE = 10  # Generate up to this amount
```

### Change Cron Schedule

Update in Railway Settings → Cron Schedule:

```
0 2 * * *   # Current: Daily 2 AM UTC
0 6 * * *   # Option: Daily 6 AM UTC
0 */6 * * * # Option: Every 6 hours
```

---

## 🐛 Troubleshooting

### Cron Job Not Running

**Check:**
1. Railway Pro plan active?
2. Cron schedule syntax correct?
3. Service deployment succeeded?
4. Environment variables set?

**View logs:**
- Railway Dashboard → Deployments → Latest → Logs

### Script Errors

**Common Issues:**

**MongoDB Connection Failed:**
```
Error: Could not connect to MongoDB
```
**Fix:** Check `MONGODB_URL` environment variable

**OpenAI API Error:**
```
Error: Invalid API key
```
**Fix:** Check `OPENAI_API_KEY` environment variable

**No Users Found:**
```
Found 0 active users
```
**Fix:** Script filters for active users only (subscription OR recent activity)

### Manual Test Run

SSH into Railway service and run manually:

```bash
# In Railway dashboard
railway run python challenge_pool_replenisher.py
```

---

## 💰 Cost Estimates

### Railway Pro Plan
- **Plan Cost:** $20/month
- **Includes:** Unlimited cron jobs
- **Worth it if:** You need other Pro features

### Replenishment Costs (OpenAI)
- **Per user:** ~$0.10 (30 challenges)
- **7 active users:** ~$0.70/day = ~$21/month
- **50 active users:** ~$5/day = ~$150/month

### Cost Optimization
- Only replenishes users with `subscription OR recent_activity`
- Skips test accounts and inactive users
- Caches AI generation (24h TTL)

---

## ✅ Verification Checklist

After setup:

- [ ] Service created in Railway
- [ ] GitHub repo connected
- [ ] Root directory set to `backend`
- [ ] Start command: `python challenge_pool_replenisher.py`
- [ ] Environment variables added
- [ ] Cron schedule configured (if Pro plan)
- [ ] Manual test run successful
- [ ] Logs show successful replenishment
- [ ] User pools verified in MongoDB

---

## 🎉 Setup Complete!

Your challenge pool system will now automatically replenish daily at 2 AM UTC.

**Next Steps:**
1. Monitor first scheduled run
2. Check logs for any errors
3. Verify user pools are being replenished
4. Adjust schedule/settings as needed

---

**Questions?** Check the logs or run manual test deployment first!
