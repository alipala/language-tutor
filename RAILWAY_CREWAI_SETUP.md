# Railway CrewAI Cron Service Setup Guide

## 🎯 Purpose

Set up the **Phase 2 CrewAI multi-agent system** as a Railway cron service to automatically generate challenges for users with learning plans on a weekly schedule.

---

## 📋 Current Problem

After PR #170, we have:
- ✅ CrewAI code built (Phase 2)
- ✅ Database with 3,643 reference challenges
- ✅ Language-aware backend (Phase 3)
- ❌ **NO cron job running** (old one was deleted)
- ❌ Users get slow on-demand AI generation (10-20s wait)
- ❌ Expensive real-time GPT-4 calls during HTTP requests

---

## 🚀 Solution: Deploy CrewAI as Railway Cron Service

### **What This Will Fix:**

1. **Proactive Challenge Generation** - Runs weekly, keeps pools full
2. **Fast Explore Tab** - Challenges pre-generated, instant loading
3. **Cost Optimization** - Weekly batch vs on-demand real-time
4. **Completed Learning Plans** - Generates for 100% complete plans

---

## 📦 Step 1: Create New Railway Service

### **Option A: Railway Dashboard (Recommended)**

1. Go to your Railway project
2. Click **"+ New"** → **"Empty Service"**
3. Name it: `crewai-challenge-generator`
4. Click **"Create"**

### **Option B: Railway CLI**

```bash
railway service create crewai-challenge-generator
```

---

## ⚙️ Step 2: Configure Service Settings

### **2.1 Set Root Directory**

In Railway dashboard:
1. Go to service settings
2. Set **Root Directory**: `cron-service`
3. This tells Railway to use `cron-service/` as the working directory

### **2.2 Configure Build**

Railway will automatically detect:
- `nixpacks.toml` in `cron-service/`
- `requirements.txt` in `cron-service/`
- Python 3.11 (from `backend/nixpacks.toml` or Railway default)

### **2.3 Set Start Command**

The start command is already configured in `cron-service/nixpacks.toml`:
```toml
[start]
cmd = "python phase2-crewai/weekly_cron.py"
```

---

## 🔐 Step 3: Set Environment Variables

Add these environment variables to the new service:

### **Required Variables:**

```bash
# OpenAI API Key (required for CrewAI)
OPENAI_API_KEY=sk-proj-...

# MongoDB Connection (copy from main backend service)
MONGODB_URL=mongodb+srv://...

# LLM Model Configuration (optional, defaults shown)
GPT_MODEL=gpt-4o
LLM_PROVIDER=openai

# Logging (optional)
LOG_LEVEL=INFO
```

### **How to Set Variables in Railway:**

1. Click on the `crewai-challenge-generator` service
2. Go to **"Variables"** tab
3. Click **"+ Add Variable"**
4. Add each variable above
5. Save

**💡 Tip:** Copy `MONGODB_URL` from your main backend service to ensure same database connection.

---

## 🕒 Step 4: Configure Cron Schedule

### **Set Cron Trigger:**

1. In Railway dashboard, go to service settings
2. Enable **"Cron"** trigger
3. Set schedule: `0 0 * * 1`
   - **Meaning:** Every Monday at 00:00 UTC (midnight)
   - **Frequency:** Weekly (4 times/month)

### **Alternative Schedules:**

```bash
# Twice weekly (Monday & Thursday)
0 0 * * 1,4

# Daily (if you have high traffic)
0 0 * * *

# Every 3 days
0 0 */3 * *
```

**Recommendation:** Start with **weekly** (cost-effective), increase if pools run low.

---

## 🔗 Step 5: Deploy Service

### **Option A: Automatic Deploy (Recommended)**

1. Ensure branch is pushed to GitHub
2. In Railway, link service to your GitHub repo
3. Set branch: `main` (or your working branch)
4. Railway will auto-deploy on push

### **Option B: Manual Deploy**

```bash
cd /home/user/language-tutor

# Link Railway project
railway link

# Deploy cron-service
railway up --service crewai-challenge-generator
```

---

## ✅ Step 6: Verify Deployment

### **6.1 Check Build Logs:**

1. Go to Railway dashboard
2. Click on `crewai-challenge-generator` service
3. Go to **"Deployments"** tab
4. Check latest deployment logs

**Look for:**
```
✅ Successfully installed crewai-1.7.1 crewai-tools-1.7.1
✅ Build completed
```

### **6.2 Test Manual Run:**

Trigger the cron manually to verify it works:

1. In Railway dashboard, go to service
2. Click **"Run Now"** (if available) or wait for next scheduled run
3. Monitor logs in real-time

**Expected Output:**
```
================================================================================
🗓️  WEEKLY CHALLENGE GENERATION CRON
================================================================================
Started at: 2025-12-17 14:00:00 UTC
================================================================================

🔍 Finding active users...
📊 Found 45 users with active learning plans

👤 Processing user 1/45 (alipala.ist@gmail.com)
   Language: english, Level: B1
   Current pool: 60 challenges ✅ (No replenishment needed)

👤 Processing user 2/45 (user2@example.com)
   Language: dutch, Level: A2
   Current pool: 25 challenges 🔄 (Need 25 more)
   🤖 Generating with CrewAI...
   ✅ Generated 25 challenges in 42 seconds

...

================================================================================
📊 WEEKLY GENERATION SUMMARY
================================================================================
✅ Users processed: 45
✅ Challenges generated: 150
💰 Total cost: $3.50
⏱️ Total time: 18 minutes
================================================================================
✅ Weekly cron completed successfully!
================================================================================
```

---

## 📊 Step 7: Monitor & Optimize

### **Week 1: Daily Monitoring**

Check daily to ensure:
- ✅ Cron runs successfully
- ✅ No errors in logs
- ✅ Challenge pools are replenished
- ✅ Users can access challenges quickly

### **Week 2+: Weekly Monitoring**

Check weekly:
- 💰 **OpenAI costs** (should be ~$3-10/week)
- ⏱️ **Execution time** (should be < 30 minutes)
- 📊 **Challenge counts** per user/language
- 🐛 **Error rate** (should be < 5%)

### **Cost Tracking:**

Expected costs:
```
Weekly cron (4 runs/month):
- Active users: ~45
- Challenges per run: ~150 (only for low pools)
- Cost per run: $3-10
- Monthly cost: $12-40

Compared to old daily cron:
- Old: $367/month ❌
- New: $12-40/month ✅
- Savings: $327-355/month (87-92% reduction)
```

---

## 🎯 Step 8: Handle Completed Learning Plans

The CrewAI cron currently generates for **active learning plans**. To handle **completed (100%) plans**:

### **Logic Update Needed:**

File: `cron-service/phase2-crewai/challenge_crew_ai.py`

Current logic:
```python
# Gets active learning plans (not completed)
learning_plans = await database.learning_plans.find({
    "user_id": user_id,
    "status": "active"
}).to_list(None)
```

**Proposed logic:**
```python
# Gets active OR completed plans
learning_plans = await database.learning_plans.find({
    "user_id": user_id,
    "status": {"$in": ["active", "completed"]}
}).to_list(None)
```

**Why this matters:**
- Users who complete a learning plan may still want challenges
- Keeps them engaged after completion
- Allows exploration of same language at higher levels

**Should I update this logic now?** Let me know and I can make this change.

---

## 🚨 Common Issues & Solutions

### **Issue 1: Service fails to start**

**Error:** `ModuleNotFoundError: No module named 'crewai'`

**Solution:**
```bash
# Check requirements.txt includes:
crewai==1.7.1
crewai-tools==1.7.1

# Redeploy service
```

---

### **Issue 2: MongoDB connection fails**

**Error:** `pymongo.errors.ServerSelectionTimeoutError`

**Solutions:**
1. Check `MONGODB_URL` is set correctly
2. Verify Railway IP is whitelisted in MongoDB Atlas
3. Test connection string locally

---

### **Issue 3: OpenAI API errors**

**Error:** `openai.error.AuthenticationError: Incorrect API key`

**Solutions:**
1. Verify `OPENAI_API_KEY` is set correctly
2. Check API key hasn't expired
3. Ensure OpenAI account has credits

---

### **Issue 4: Cron doesn't run at scheduled time**

**Solutions:**
1. Check cron schedule syntax: `0 0 * * 1` (weekly Monday)
2. Verify cron is enabled in Railway settings
3. Check Railway service status (must be running)

---

## 📝 Step 9: Update Documentation

After deployment, update these files:

1. **README.md** - Document the new cron service
2. **DEPLOYMENT_PLAN_PHASE3.md** - Mark cron as deployed
3. **iOS Integration Guide** - Update with faster response times

---

## ✅ Deployment Checklist

- [ ] Created `crewai-challenge-generator` service in Railway
- [ ] Set root directory to `cron-service`
- [ ] Added all required environment variables
- [ ] Configured cron schedule (weekly: `0 0 * * 1`)
- [ ] Deployed service successfully
- [ ] Verified build logs (CrewAI installed)
- [ ] Triggered manual test run
- [ ] Checked challenge generation logs
- [ ] Monitored OpenAI costs
- [ ] Updated documentation
- [ ] Notified iOS team of faster response times

---

## 🎉 Expected Results After Deployment

### **Before (Current State):**
```
User visits Explore tab → Portuguese A1
❌ No challenges in pool
❌ On-demand AI generation starts
❌ User waits 10-20 seconds
❌ Multiple GPT-4 API calls ($0.50)
❌ Slow, expensive, poor UX
```

### **After (With CrewAI Cron):**
```
Monday 00:00 UTC - Cron runs:
✅ Checks all users with learning plans
✅ Generates challenges for low pools
✅ Pre-populates Portuguese A1 if user has plan

User visits Explore tab → Portuguese A1
✅ 60 challenges already in pool
✅ Instant response (< 1 second)
✅ No AI calls needed
✅ Fast, cheap, great UX
```

---

## 📞 Support

**Need help?**
- Check Railway logs for errors
- Review `PHASE2_COMPLETE.md` for CrewAI details
- Test locally with `python test_crew_ai.py`
- Contact backend team if issues persist

---

**Status:** Ready to deploy! 🚀
**Estimated Setup Time:** 15-20 minutes
**Estimated Cost Savings:** $327-355/month

---
