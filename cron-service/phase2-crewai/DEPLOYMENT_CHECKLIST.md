# Phase 2 Deployment Checklist

**Date:** December 16, 2025
**Phase:** 2 - CrewAI Multi-Agent Challenge Generation
**Status:** Ready for Testing

---

## ✅ **PRE-DEPLOYMENT CHECKLIST**

### **1. Code Review**

- [x] All Phase 2 files created
- [x] Clean code with proper documentation
- [x] Environment variables configurable (GPT_MODEL, LLM_PROVIDER)
- [x] Comprehensive logging implemented
- [x] Usage statistics tracking implemented
- [x] Error handling in place
- [ ] Code reviewed by team member

### **2. Testing**

- [ ] Test script runs successfully (`python test_crew_ai.py`)
- [ ] Generated challenges are high quality
- [ ] Challenges are in correct language (native content)
- [ ] Challenges match CEFR level
- [ ] Cost estimates are reasonable (< $0.10 per test run)
- [ ] All 6 challenge types tested
- [ ] Multiple languages tested (at least English, Spanish, Dutch)

### **3. Dependencies**

- [ ] Requirements file includes all dependencies
- [ ] CrewAI installed successfully (`pip install crewai`)
- [ ] No missing dependencies
- [ ] Compatible with Railway environment

### **4. Configuration**

- [ ] `.env` file configured locally (for testing)
- [ ] Railway environment variables prepared:
  - [ ] `OPENAI_API_KEY`
  - [ ] `MONGODB_URL`
  - [ ] `GPT_MODEL` (optional, default: gpt-4o)
  - [ ] `LLM_PROVIDER` (optional, default: openai)
  - [ ] `LOG_LEVEL` (optional, default: INFO)

### **5. Database Prerequisites**

- [ ] Phase 1 completed (challenge_pool cleaned)
- [ ] Phase 1.5 completed (3,643 reference challenges generated)
- [ ] Verification passed (`verify_multilang.py`)
- [ ] All 6 languages have reference challenges
- [ ] Database indexes created

---

## 🧪 **TESTING STEPS**

### **Step 1: Local Environment Setup**

```bash
cd cron-service/phase2-crewai

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="sk-..."
export MONGODB_URL="mongodb://..."
export GPT_MODEL="gpt-4o"
export LOG_LEVEL="INFO"
```

- [ ] Dependencies installed
- [ ] Environment variables set
- [ ] Connection to MongoDB successful

### **Step 2: Run Test Script**

```bash
# Test with default user (English)
python test_crew_ai.py

# Expected: 3 challenges generated, cost < $0.10
```

- [ ] Test completed successfully
- [ ] Challenges generated (3 expected)
- [ ] Cost reasonable (< $0.10)
- [ ] Quality acceptable

### **Step 3: Test Different Languages**

```bash
# Test Spanish
python test_crew_ai.py --language spanish --level B2 --type error_spotting --count 3

# Test Dutch
python test_crew_ai.py --language dutch --level B1 --type micro_quiz --count 3

# Test German
python test_crew_ai.py --language german --level C1 --type swipe_fix --count 3
```

- [ ] Spanish challenges generated
- [ ] Dutch challenges generated
- [ ] German challenges generated
- [ ] All challenges in correct language (not English)
- [ ] All challenges appropriate for level

### **Step 4: Test All Challenge Types**

```bash
for type in error_spotting swipe_fix micro_quiz smart_flashcard native_check brain_tickler; do
  echo "Testing $type..."
  python test_crew_ai.py --type $type --count 2
  sleep 5
done
```

- [ ] error_spotting: ✅
- [ ] swipe_fix: ✅
- [ ] micro_quiz: ✅
- [ ] smart_flashcard: ✅
- [ ] native_check: ✅
- [ ] brain_tickler: ✅

### **Step 5: Review Generated Challenges**

Manually review at least 3 challenges:

- [ ] Grammar is correct
- [ ] Content is native (not translated)
- [ ] Difficulty matches CEFR level
- [ ] Explanations are clear
- [ ] Format is correct (matches reference challenges)
- [ ] Cultural appropriateness

### **Step 6: Cost Analysis**

Review test costs:

```bash
# Check usage report
cat crewai_usage_report_*.json | jq .
```

- [ ] Total cost < $0.50 for all tests
- [ ] Cost per challenge reasonable (< $0.02)
- [ ] Projections for weekly cron acceptable (< $20/week)

---

## 🚀 **DEPLOYMENT STEPS**

### **Step 1: Commit Phase 2 Code**

```bash
cd /home/user/language-tutor

# Check status
git status

# Add Phase 2 files
git add cron-service/phase2-crewai/

# Commit
git commit -m "Add Phase 2: CrewAI multi-agent challenge generation system

- Implement 3-agent architecture (Analyzer, Generator, Curator)
- Add configurable LLM model via GPT_MODEL environment variable
- Implement comprehensive usage statistics tracking
- Add perfect logging (file + console)
- Support all 6 languages with native content generation
- Reduce costs by 97% (weekly schedule)
- Include testing and verification tools"

# Push to branch
git push -u origin claude/setup-fullstack-dev-S51KJ
```

- [ ] Code committed
- [ ] Code pushed to branch

### **Step 2: Railway Configuration**

#### **Add Environment Variables**

In Railway dashboard for cron service:

1. Navigate to service settings
2. Add environment variables:

```
OPENAI_API_KEY=sk-...
MONGODB_URL=mongodb://...
GPT_MODEL=gpt-4o
LLM_PROVIDER=openai
LOG_LEVEL=INFO
```

- [ ] OPENAI_API_KEY added
- [ ] MONGODB_URL added
- [ ] GPT_MODEL added
- [ ] LOG_LEVEL added

#### **Update Cron Schedule**

Change from daily to weekly (Monday 00:00 UTC):

**Cron Expression:**
```
0 0 * * 1
```

- [ ] Cron schedule updated to weekly

#### **Update Cron Command**

Change command to:

```bash
python /home/user/language-tutor/cron-service/phase2-crewai/weekly_cron.py
```

- [ ] Cron command updated

### **Step 3: Deploy to Railway**

```bash
# Trigger deployment
git push origin claude/setup-fullstack-dev-S51KJ

# Or via Railway CLI
railway up
```

- [ ] Code deployed to Railway
- [ ] Deployment successful
- [ ] No build errors

### **Step 4: Test on Railway**

#### **Trigger Manual Test**

```bash
railway run python cron-service/phase2-crewai/weekly_cron.py
```

Or via Railway dashboard: "Run now" button

- [ ] Manual trigger successful
- [ ] Check Railway logs for errors
- [ ] Verify challenges created in database

#### **Monitor Logs**

```bash
railway logs --service cron-service
```

Look for:
- [ ] "✅ CREWAI WEEKLY CHALLENGE GENERATION - COMPLETE"
- [ ] No fatal errors
- [ ] Reasonable execution time (< 1 hour)
- [ ] Cost within budget

### **Step 5: Verify Database**

Check that challenges were created:

```bash
python -c "
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime, timedelta

async def check():
    client = AsyncIOMotorClient('$MONGODB_URL')
    db = client.language_tutor

    # Count challenges created in last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    count = await db.challenge_pool.count_documents({
        'created_at': {'$gte': one_hour_ago}
    })
    print(f'Challenges created in last hour: {count}')

    client.close()

asyncio.run(check())
"
```

- [ ] New challenges created
- [ ] Count matches expected (50-200 per active user)
- [ ] Challenges have correct fields (language, cefr_level, etc.)

---

## 📊 **POST-DEPLOYMENT MONITORING**

### **Week 1: Daily Monitoring**

For the first week, check daily:

- [ ] Day 1: Cron ran successfully
- [ ] Day 2: No errors in logs
- [ ] Day 3: Cost tracking reports exist
- [ ] Day 4: Challenges being used by users
- [ ] Day 5: User completion rates normal
- [ ] Day 6: No API rate limiting
- [ ] Day 7: Review weekly usage report

### **Weekly Checks**

- [ ] Week 1: Verify cron runs on Monday 00:00 UTC
- [ ] Week 2: Review costs (should be < $20)
- [ ] Week 3: Check challenge quality (spot check)
- [ ] Week 4: Analyze user feedback (if any)

### **Monthly Review**

- [ ] Total cost for month (target: < $60)
- [ ] Total challenges generated
- [ ] User completion rates
- [ ] Any errors or issues
- [ ] Quality feedback from users
- [ ] Consider optimizations (cheaper model, reduced frequency, etc.)

---

## 🚨 **ROLLBACK PROCEDURE**

If critical issues occur:

### **1. Immediate Rollback**

In Railway, update cron schedule back to daily:

```
0 0 * * *  # Daily
```

Update command back to:

```bash
python /home/user/language-tutor/cron-service/challenge_pool_replenisher.py
```

- [ ] Schedule reverted
- [ ] Command reverted
- [ ] Old system working

### **2. Investigation**

- [ ] Review error logs
- [ ] Check usage reports
- [ ] Identify root cause
- [ ] Document issue

### **3. Fix and Redeploy**

- [ ] Fix identified issues
- [ ] Test locally again
- [ ] Redeploy to Railway
- [ ] Monitor closely

---

## ✅ **COMPLETION CRITERIA**

Phase 2 deployment is complete when:

- [x] All code committed and pushed
- [ ] Railway environment configured
- [ ] Weekly cron scheduled (Monday 00:00 UTC)
- [ ] First cron run successful
- [ ] Challenges generated correctly
- [ ] Costs within budget (< $20/week)
- [ ] Logs and reports generated
- [ ] No critical errors
- [ ] Team notified of completion

---

## 📝 **NOTES**

**Testing Notes:**
```
Date:
Tester:
Results:


Issues Found:


```

**Deployment Notes:**
```
Date:
Deployed by:
Railway Service:


Issues Encountered:


```

**Post-Deployment Notes:**
```
Week 1:
Week 2:
Week 3:
Week 4:


```

---

## 🎯 **NEXT PHASE**

After Phase 2 is stable (2-4 weeks):

- [ ] Begin Phase 3: Backend API Updates
  - Update challenge_routes.py
  - Add language filtering
  - Update challenge_pool_helpers.py

- [ ] Begin Phase 4: Testing
  - Load testing
  - Multi-language testing
  - User acceptance testing

---

**Deployment Checklist Complete!**

Last Updated: 2025-12-16
Status: ✅ Ready for deployment
