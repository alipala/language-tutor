# Phase 3 & 3.1 Deployment Plan - Production Railway

## 📋 Overview

Deploy language-aware challenge system with flexible language/level selection to Railway production.

---

## ✅ Pre-Deployment Checklist

### **1. Code Changes Summary**

**Modified Files:**
- ✅ `backend/challenge_generator_ai.py` - Added language parameter to AI generation
- ✅ `backend/challenge_pool_helpers.py` - Added language parameter to all helper functions
- ✅ `backend/challenge_routes.py` - Added query parameters and smart resolution logic

**New Files:**
- ✅ `backend/populate_user_challenges.py` - One-time population script
- ✅ `cron-service/challenge_pool_replenisher_v2.py` - Updated cron service (optional)
- ✅ `PHASE3_REACT_NATIVE_INTEGRATION.md` - iOS integration guide

**Testing:**
- ✅ All endpoints tested locally
- ✅ Auto-population tested (60 challenges per language/level)
- ✅ Language switching tested
- ✅ Smart fallback tested
- ✅ iOS integration tested

**Database:**
- ✅ `reference_challenges` collection: 3,643 challenges available
- ✅ `challenge_pool` collection: Tested auto-population
- ✅ No schema changes required

**Railway Services:**
- ✅ Old `challenge-replenisher` cron service DELETED ✅

---

## 🚀 Deployment Steps

### **Step 1: Verify Production Database**

Before deploying, ensure production has reference challenges:

```bash
# Connect to production MongoDB via Railway
railway connect mongodb

# In MongoDB shell:
use language_tutor
db.reference_challenges.countDocuments()
# Should return: 3643
```

**If count is 0 or low:**
- Reference challenges are missing!
- Need to run Phase 1.5 seed script first
- Contact backend team or check `seed_reference_challenges.py`

**If count is 3643:** ✅ Good to proceed!

---

### **Step 2: Merge Branch to Main**

```bash
# Ensure all changes are committed and pushed
git status
# Should show: "nothing to commit, working tree clean"

# Switch to main branch
git checkout main

# Pull latest
git pull origin main

# Merge Phase 3.1 branch
git merge claude/setup-fullstack-dev-S51KJ

# Push to main
git push origin main
```

---

### **Step 3: Deploy Backend to Railway**

**Option A: Auto-Deploy (if enabled)**
- Push to main triggers automatic deployment
- Monitor Railway dashboard for deployment status

**Option B: Manual Deploy**
```bash
# Using Railway CLI
railway up

# Or trigger deployment in Railway dashboard
# Go to backend service → "Deployments" → "Deploy"
```

**Monitor Deployment:**
1. Go to Railway dashboard
2. Select backend service
3. Watch deployment logs
4. Wait for "✅ Deployment successful"

**Verify Deployment:**
```bash
# Test production endpoints
curl https://your-backend.up.railway.app/api/health

# Test challenge counts (should auto-populate)
curl -X POST https://your-backend.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.access_token'

# Use token to test counts
curl https://your-backend.up.railway.app/api/challenges/counts?language=spanish&level=A1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### **Step 4: Populate Challenges for Existing Users**

**This is CRITICAL!** Existing users with learning plans need challenges.

**Option A: Run Locally Against Production DB**

```bash
# Update backend/.env to use production MongoDB
MONGODB_URL=<production-mongodb-url-from-railway>

# Run population script
cd backend
python populate_user_challenges.py

# Choose option 1: Current level only (faster)
# OR option 2: All levels A1-C2 (full flexibility)
```

**Option B: Run on Railway (Recommended)**

```bash
# Using Railway CLI
railway run python backend/populate_user_challenges.py

# Or create a one-time job in Railway dashboard
```

**Expected Output:**
```
================================================================================
POPULATING CHALLENGES FOR USERS WITH LEARNING PLANS
================================================================================

📊 Found 45 active learning plans

👤 User: user1@example.com
   Language: spanish
   Level: B1
   🔄 Populating challenges...
   ✅ Populated 60 challenges!

👤 User: user2@example.com
   Language: german
   Level: A2
   🔄 Populating challenges...
   ✅ Populated 60 challenges!

...

================================================================================
SUMMARY
================================================================================
✅ Successfully populated: 45 users
❌ Errors: 0 users
📊 Total learning plans: 45
================================================================================
```

---

### **Step 5: Verify Production Functionality**

**Test All 3 User Scenarios:**

#### **1. User WITH Learning Plan:**
```bash
# Login with existing user (has Spanish B1 learning plan)
TOKEN=$(curl -s -X POST "https://your-backend.up.railway.app/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

# Get counts (should use learning plan language - Spanish B1)
curl "https://your-backend.up.railway.app/api/challenges/counts" \
  -H "Authorization: Bearer $TOKEN" | jq

# Should return: 60+ challenges for Spanish B1

# Override to try German A1
curl "https://your-backend.up.railway.app/api/challenges/counts?language=german&level=A1" \
  -H "Authorization: Bearer $TOKEN" | jq

# Should auto-populate 60 German A1 challenges
```

#### **2. User WITHOUT Learning Plan:**
```bash
# Login with user who has NO learning plan
TOKEN=$(curl -s -X POST "https://your-backend.up.railway.app/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"noplan@example.com","password":"password"}' \
  | jq -r '.access_token')

# Request Spanish A1
curl "https://your-backend.up.railway.app/api/challenges/counts?language=spanish&level=A1" \
  -H "Authorization: Bearer $TOKEN" | jq

# Should auto-populate 60 Spanish A1 challenges
```

#### **3. Guest User (No Auth):**
```bash
# No token needed
curl "https://your-backend.up.railway.app/api/challenges/counts?language=french&level=A2" | jq

# Should return error (auth required for counts)
# But /languages endpoint should work without auth (if public)
```

---

### **Step 6: Monitor Production**

**Check Logs:**
```bash
# Railway CLI
railway logs --tail

# Look for:
# - [RESOLVE] logs showing language/level resolution
# - [POOL_HELPER] logs showing auto-population
# - [AI_CHALLENGE] logs showing AI generation
# - Any errors
```

**Check Slack Alerts:**
- Monitor Slack for slow response alerts
- Daily challenges may trigger alerts (10-20s AI generation)
- This is expected - consider increasing threshold to 20s

**Monitor Database:**
```bash
# Connect to production MongoDB
railway connect mongodb

# Check challenge_pool growth
db.challenge_pool.countDocuments()

# Check by language
db.challenge_pool.aggregate([
  { $group: { _id: "$language", count: { $sum: 1 } } }
])

# Check daily_challenges_cache
db.daily_challenges_cache.countDocuments()
```

---

### **Step 7: Deploy iOS App (After Backend Verified)**

**iOS app should already have:**
- ✅ Language/Level picker component
- ✅ Updated API calls with query parameters
- ✅ Timeout handling (30s for /daily endpoint)
- ✅ Loading states

**iOS Deployment:**
1. Update iOS app to point to production backend URL
2. Test on TestFlight with real users
3. Monitor for any errors
4. Submit to App Store

---

## 🔧 Optional: Setup New Cron Service

**If you want proactive pool replenishment:**

1. **Create new Railway service:**
   - Service name: `challenge-replenisher-v2`
   - Start command: `python challenge_pool_replenisher_v2.py`
   - Cron schedule: `0 2 * * *` (2 AM daily)

2. **Add environment variables:**
   - Copy all env vars from main backend service
   - Ensure MONGODB_URL is set

3. **Deploy cron service:**
   ```bash
   # In Railway dashboard
   # Deploy cron-service/ directory
   ```

**OR just skip it** - on-demand auto-population works great!

---

## 🚨 Rollback Plan

**If deployment fails:**

### **Backend Rollback:**
```bash
# Railway dashboard → Backend service → Deployments
# Click on previous successful deployment
# Click "Redeploy"
```

### **Code Rollback:**
```bash
# Revert merge
git revert -m 1 <merge-commit-hash>
git push origin main
```

### **Database Rollback:**
```bash
# Clear challenge_pool if needed
db.challenge_pool.deleteMany({ created_at: { $gte: new Date('2025-12-17') } })
```

---

## 📊 Success Metrics

**After deployment, verify:**

- ✅ All 3 user scenarios working (with plan, without plan, override)
- ✅ Auto-population from reference challenges working (3-4 seconds)
- ✅ AI daily challenges generating successfully (10-20 seconds)
- ✅ Language switching working in iOS app
- ✅ No errors in production logs
- ✅ Challenge pool growing for active users
- ✅ Existing users have challenges populated

**Database Metrics:**
- `reference_challenges`: 3,643 documents (unchanged)
- `challenge_pool`: Growing as users request challenges
- `daily_challenges_cache`: Growing as users get daily challenges

**Performance Metrics:**
- `/api/challenges/counts`: 3-4 seconds (auto-population)
- `/api/challenges/daily`: 10-20 seconds (AI generation)
- `/api/challenges/by-type`: 0.3-0.7 seconds (pool query)
- `/api/challenges/languages`: 1-2 seconds

---

## 🎯 Post-Deployment Tasks

### **Day 1:**
- ✅ Monitor logs for errors
- ✅ Check Slack alerts
- ✅ Verify auto-population working
- ✅ Test iOS app with real users

### **Day 7:**
- ✅ Check challenge_pool growth
- ✅ Monitor OpenAI costs (daily AI generation)
- ✅ Review user feedback
- ✅ Check if any languages/levels have low reference challenges

### **Day 30:**
- ✅ Analyze usage by language
- ✅ Identify popular language/level combinations
- ✅ Consider adding more reference challenges for popular combos
- ✅ Review AI generation quality

---

## 📝 Notes

**Breaking Changes:**
- ❌ None - All query parameters are optional
- ✅ Backward compatible with existing iOS app

**Database Changes:**
- ❌ No schema migrations required
- ✅ Only new documents added to challenge_pool

**API Changes:**
- ✅ New optional query parameters: `?language=` and `?level=`
- ✅ New endpoint: `/api/challenges/languages`
- ✅ All existing endpoints still work without parameters

**Cost Impact:**
- ✅ **Reduced costs** - Uses free reference challenges vs expensive AI generation
- ✅ Old cron service deleted (saved ~$20-50/day in GPT-4 costs)
- ✅ AI generation only for daily challenges (~$0.05 per user per day)

---

## ✅ Deployment Checklist

**Pre-Deployment:**
- [ ] All changes committed and pushed to branch
- [ ] Local testing complete
- [ ] iOS app tested against local backend
- [ ] Production database has 3,643 reference challenges
- [ ] Old challenge-replenisher service deleted from Railway

**Deployment:**
- [ ] Merge branch to main
- [ ] Deploy backend to Railway
- [ ] Verify deployment successful
- [ ] Test endpoints in production

**Post-Deployment:**
- [ ] Run population script for existing users
- [ ] Verify all 3 user scenarios working
- [ ] Test iOS app against production
- [ ] Monitor logs for 24 hours
- [ ] Update iOS app to production URL
- [ ] Submit iOS app to App Store

**Optional:**
- [ ] Setup new cron service v2 (or skip)
- [ ] Update Slack alert threshold for /daily endpoint (5s → 20s)

---

**Ready to deploy!** 🚀
