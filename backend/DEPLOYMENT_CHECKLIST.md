# 🚀 Challenge Pool System - Deployment Checklist

## ✅ Step-by-Step Deployment Guide

### Phase 1: Code Deployment (Now)

- [x] **Create PR** ✅ [PR #169](https://github.com/alipala/language-tutor/pull/169)
- [ ] **Review PR** - Check `PR_DESCRIPTION.md` for details
- [ ] **Merge PR to main**
  ```bash
  # Review PR on GitHub first, then:
  gh pr merge 169 --squash
  ```
- [ ] **Wait for Railway Auto-Deploy** (2-3 minutes)
- [ ] **Verify deployment** - Check Railway logs for successful start

---

### Phase 2: Test Critical Fixes (After Deployment)

#### Test 1: Profile Update Fix (CRITICAL)
This was a production-breaking bug affecting ALL profile updates!

**Test Steps:**
1. Open iOS app
2. Go to **Profile → App Settings → Account Preferences**
3. Change proficiency level from B1 to C2
4. Check Railway logs - Should see:
   ```
   [UPDATE_PROFILE] 👤 User xyz@email.com updating profile
   [UPDATE_PROFILE] 📊 LEVEL CHANGE: B1 → C2
   [UPDATE_PROFILE] 💾 Database update result: matched=1, modified=1 ✅
   [UPDATE_PROFILE] ✅ Verified preferred_level in DB: C2
   ```
5. Go back to settings - Verify level shows C2 (not B1!)

**Expected:** ✅ Level saves correctly (matched=1, modified=1)
**Before Fix:** ❌ matched=0, modified=0 (silently failed)

---

#### Test 2: CEFR Level Filtering
Verify different levels show different challenges.

**Test Steps:**
1. User with B1 level opens Explore tab
2. Check logs - Should see:
   ```
   [POOL_HELPER] 📊 Counting challenges for user xxx, level: B1
   [POOL_HELPER] ✅ Final counts for level B1: {error_spotting: 10, ...}
   ```
3. Change level to C2 in settings
4. Return to Explore tab
5. Check logs - Should see:
   ```
   [POOL_HELPER] 📊 Counting challenges for user xxx, level: C2
   [POOL_HELPER] ✅ Final counts for level C2: {error_spotting: 10, ...}
   ```

**Expected:** ✅ Logs show correct level after change
**Before Fix:** ❌ Always showed B1 regardless of user setting

---

### Phase 3: Generate Reference Challenges (Required!)

⚠️ **CRITICAL:** Without reference challenges, new users will have NO challenges at all!

**Current Status:**
- ✅ B1: 300 challenges (already generated)
- ✅ C2: 300 challenges (already generated)
- ⏳ A1: Not generated - **REQUIRED!**
- ⏳ A2: Not generated - **REQUIRED!**
- ⏳ B2: Not generated - **REQUIRED!**
- ⏳ C1: Not generated - **REQUIRED!**

**Run These Commands:**

```bash
cd /Users/alipala/CascadeProjects/language-tutor/backend

# Generate all remaining levels (takes ~1.5 hours total)
python seed_reference_challenges.py level A1 50  # ~25 min
python seed_reference_challenges.py level A2 50  # ~25 min
python seed_reference_challenges.py level B2 50  # ~25 min
python seed_reference_challenges.py level C1 50  # ~25 min
```

**Or all at once:**
```bash
python seed_reference_challenges.py level A1 50 && \
python seed_reference_challenges.py level A2 50 && \
python seed_reference_challenges.py level B2 50 && \
python seed_reference_challenges.py level C1 50
```

**Verify in MongoDB:**
```javascript
db.reference_challenges.aggregate([
  { $group: { _id: "$cefr_level", count: { $sum: 1 } } }
])

// Expected output:
// { "_id": "A1", "count": 300 }
// { "_id": "A2", "count": 300 }
// { "_id": "B1", "count": 300 }
// { "_id": "B2", "count": 300 }
// { "_id": "C1", "count": 300 }
// { "_id": "C2", "count": 300 }
```

**Cost:** ~$2-3 total (one-time)

---

### Phase 4: iOS Level Selection (REQUIRED!)

**What iOS Needs to Do:**

Add CEFR level selector in: **Profile → App Settings → Account Preferences**

**Implementation:**
- Picker/Selector with 6 options: A1, A2, B1, B2, C1, C2
- Call existing endpoint: `PUT /api/auth/update-profile`
- Request body: `{ "preferred_level": "C2" }`
- Default: B1 if not set

**Backend is ready!** Endpoint already exists and is now working correctly.

---

### Phase 5: Railway Cron Job Setup (Optional)

⚠️ **Requires Railway Pro Plan** ($20/month)

**Purpose:** Automatically replenish challenge pools daily at 2 AM UTC

**Setup Instructions:** See `RAILWAY_CRON_SETUP.md`

**Quick Steps:**
1. Create new Railway service: "challenge-replenisher"
2. Connect to GitHub repo
3. Set start command: `python challenge_pool_replenisher.py`
4. Add environment variables (MONGODB_URL, OPENAI_API_KEY, DATABASE_NAME)
5. Set cron schedule: `0 2 * * *`
6. Test manual run

**Alternative (Free):** Use GitHub Actions - see `RAILWAY_CRON_SETUP.md` for setup

---

## 🧪 Full System Test

After completing all phases:

### Test New User Flow
1. Create brand new test account
2. Don't do any activity (no practice, no learning plan)
3. Open Explore tab
4. **Expected:** See 10 challenges per type instantly (<5 seconds)
5. **Check logs:** Should say "New user - copying from reference"

### Test Active User Flow
1. Use existing user with practice sessions
2. Complete most challenges (leave <10 per type)
3. Open Explore tab
4. **Expected:** Auto-generates new personalized challenges
5. **Check logs:** Should say "Pool running low - replenishing"

### Test Level Change Flow
1. User with B1 level opens Explore tab
2. Note the challenge titles/content
3. Change level to C2 in settings
4. Return to Explore tab
5. **Expected:** Different challenges appear (C2 difficulty)
6. **Check logs:** Should show "level: C2"

---

## 🐛 Troubleshooting

### Issue: Profile updates still not saving

**Check:**
1. Railway redeployed after merge?
2. Check logs for `[UPDATE_PROFILE]` messages
3. Verify `matched=1, modified=1` in logs

### Issue: Still showing B1 challenges after changing to C2

**Possible Causes:**
1. iOS caching old level (frontend issue)
2. Backend not redeployed yet
3. User's level didn't save (check logs)

**Fix:**
1. Force restart Railway service
2. Clear iOS app cache
3. Test with new user account

### Issue: New users have no challenges

**Cause:** Reference challenges not generated for that level

**Fix:**
1. Check which level user selected
2. Run: `python seed_reference_challenges.py level [LEVEL] 50`
3. User should refresh Explore tab

---

## ✅ Success Criteria

All tests pass:
- [x] PR merged to main
- [ ] Railway deployed successfully
- [ ] Profile updates save correctly (matched=1, modified=1)
- [ ] Level filtering works (different counts for different levels)
- [ ] Reference challenges generated for all levels (A1-C2)
- [ ] New users see challenges instantly (<5 seconds)
- [ ] Level changes reflect in Explore tab
- [ ] iOS level selection implemented (by iOS team)
- [ ] Railway cron job setup (optional)

---

## 📞 Need Help?

**Check logs first:**
- Railway Dashboard → Deployments → Latest → Logs
- Look for `[UPDATE_PROFILE]`, `[POOL_HELPER]`, `[CHALLENGE_POOL]` tags

**Common log patterns:**

✅ **Success:**
```
[UPDATE_PROFILE] 💾 Database update result: matched=1, modified=1
[POOL_HELPER] 📊 Counting challenges for user xxx, level: C2
```

❌ **Error:**
```
[UPDATE_PROFILE] 💾 Database update result: matched=0, modified=0
[POOL_HELPER] ❌ Error ensuring pool: ...
```

---

## 🎉 You're All Set!

Once all checkboxes are complete, the Challenge Pool System is fully deployed and production-ready! 🚀
