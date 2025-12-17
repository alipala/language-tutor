# Phase 2 CrewAI - Quick Start Guide

**For macOS Users** 🍎

This guide helps you set up and test Phase 2 locally on your Mac.

---

## ⚠️ **The "externally-managed-environment" Error**

If you saw this error:

```
error: externally-managed-environment
× This environment is externally managed
```

**This is NORMAL on modern macOS!**

Apple's Python and Homebrew Python are "externally managed" to prevent conflicts.

**Solution:** Use a Python virtual environment (venv) ✅

---

## 🚀 **Quick Setup - TWO OPTIONS**

### **Option 1: Use Your Existing Root Venv** ⭐ RECOMMENDED

If you already run the backend with `python run_with_venv.py`, you have a venv at the project root. Let's use it!

```bash
cd cron-service/phase2-crewai

# Add Phase 2 dependencies to your root venv
./setup_root_venv.sh

# Then activate and test
cd ../..  # Go to project root
source venv/bin/activate
cd cron-service/phase2-crewai
python test_crew_ai.py
```

**Pros:** ✅ Simpler, uses your existing setup, one environment for everything

---

### **Option 2: Create Separate Venv for Phase 2**

If you want complete isolation:

```bash
cd cron-service/phase2-crewai

# Create separate venv
./setup_venv.sh

# Activate it
source venv/bin/activate

# Run test
python test_crew_ai.py
```

**Pros:** ✅ Complete isolation, no dependency conflicts

---

**Not sure which to choose?** See `SETUP_OPTIONS.md` for detailed comparison.

**Most users:** Use Option 1 (root venv) - it's simpler!

---

## 📋 **Manual Setup (Alternative)**

If you prefer to set up manually instead of using the scripts:

```bash
cd cron-service/phase2-crewai

# 1. Create virtual environment
python3 -m venv venv

# 2. Activate it
source venv/bin/activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run test
python test_crew_ai.py
```

---

## 📋 **Environment Variables**

The test script automatically loads from `backend/.env`. Make sure you have:

```bash
# backend/.env should contain:
OPENAI_API_KEY=sk-...
MONGODB_URL=mongodb://...
```

If these are missing, the script will tell you.

---

## 🧪 **Testing Commands**

### **Basic Test** (Default - English, B1, 3 challenges)

```bash
python test_crew_ai.py
```

### **Test Spanish**

```bash
python test_crew_ai.py --language spanish --level B2 --type micro_quiz --count 3
```

### **Test All Challenge Types**

```bash
for type in error_spotting swipe_fix micro_quiz smart_flashcard native_check brain_tickler; do
  echo "Testing $type..."
  python test_crew_ai.py --type $type --count 2
  sleep 5
done
```

### **Test Multiple Languages**

```bash
# Spanish
python test_crew_ai.py --language spanish --level B2 --count 3

# Dutch
python test_crew_ai.py --language dutch --level B1 --count 3

# German
python test_crew_ai.py --language german --level C1 --count 3

# French
python test_crew_ai.py --language french --level A2 --count 3

# Portuguese
python test_crew_ai.py --language portuguese --level B1 --count 3
```

---

## 💡 **Common Issues**

### **1. "command not found: pip"**

Use `pip3` or activate the virtual environment first:

```bash
source venv/bin/activate
# Now you can use "pip" and "python" instead of "pip3" and "python3"
```

### **2. "OPENAI_API_KEY not found"**

Check that `backend/.env` exists and contains your API key:

```bash
cat backend/.env | grep OPENAI_API_KEY
```

If missing, add it:

```bash
echo "OPENAI_API_KEY=sk-..." >> backend/.env
```

### **3. "MongoDB connection timeout"**

Check that `MONGODB_URL` is correct:

```bash
cat backend/.env | grep MONGODB_URL
```

Test connection:

```bash
python -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; asyncio.run(AsyncIOMotorClient('YOUR_URL').admin.command('ping'))"
```

### **4. "No module named 'crewai'"**

You forgot to activate the virtual environment:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### **5. Virtual environment not activating**

Make sure you're in the right directory:

```bash
cd /path/to/language-tutor/cron-service/phase2-crewai
source venv/bin/activate
```

You should see `(venv)` in your prompt:

```bash
(venv) alipala@Ali-MacBook-Pro phase2-crewai %
```

---

## 🎯 **What to Expect**

When you run `python test_crew_ai.py`, you should see:

```
🧪 CREWAI CHALLENGE GENERATION - TEST MODE
================================================================================
Timestamp: 2025-12-16 20:30:00 UTC
LLM Model: gpt-4o
LLM Provider: openai
================================================================================

📡 Connecting to MongoDB...
✅ Connected to MongoDB

👤 Test User: 6758a1f5809a0e9c7d83217e
📧 Email: user@example.com

📚 User has 2 learning plan(s):
   1. spanish - B2 ✅ ACTIVE
   2. french - A2 ⏸️  INACTIVE

🤖 Initializing CrewAI system...
✅ CrewAI system initialized

[CrewAI agents will run here - takes 30-60 seconds]

================================================================================
📊 GENERATION RESULTS
================================================================================
✅ Generated: 3 challenge(s)
⏱️  Time: 45.32 seconds
🤖 API Calls: 6 (estimated)
🪙 Input Tokens: 9,000
🪙 Output Tokens: 3,000
💰 Cost: $0.0525

📝 SAMPLE CHALLENGE (First Generated)
[Challenge details displayed here]

💾 Save Challenges to Database?
   Type 'yes' to save:
```

**Expected cost per test:** $0.05-0.10

---

## ✅ **Verifying Everything Works**

After running a test, verify:

1. **✅ No errors in output**
2. **✅ Challenges generated (should be 3)**
3. **✅ Cost is reasonable (< $0.10)**
4. **✅ Challenge is in correct language** (not English if testing Spanish/Dutch/etc.)
5. **✅ Grammar looks correct**
6. **✅ Difficulty matches level** (B2 should be harder than A1)

---

## 🔄 **Deactivating Virtual Environment**

When you're done testing:

```bash
deactivate
```

This exits the virtual environment and returns to your normal shell.

---

## 📁 **Directory Structure**

After setup, you'll have:

```
cron-service/phase2-crewai/
├── venv/                          # Virtual environment (excluded from git)
├── challenge_crew_ai.py           # Main CrewAI system
├── weekly_cron.py                 # Railway entry point
├── test_crew_ai.py                # Testing script
├── requirements.txt               # Dependencies
├── setup_venv.sh                  # Setup script
├── QUICKSTART.md                  # This file
├── README.md                      # Full documentation
└── DEPLOYMENT_CHECKLIST.md        # Deployment guide
```

After running tests, you may also see:

```
├── crewai_challenges_20251216.log         # Execution logs (excluded from git)
└── crewai_usage_report_*.json             # Usage stats (excluded from git)
```

---

## 🎓 **Understanding the Output**

### **API Calls**

Each test generates ~6 API calls because CrewAI uses 3 agents:

1. **Analyzer** - Makes 2 calls (analyze, summarize)
2. **Generator** - Makes 2 calls (generate, format)
3. **Curator** - Makes 2 calls (review, finalize)

### **Cost Breakdown**

For GPT-4o:
- **Input tokens:** ~1,500 per call × 6 calls = 9,000 tokens
- **Output tokens:** ~500 per call × 6 calls = 3,000 tokens
- **Cost:** (9,000/1M × $2.50) + (3,000/1M × $10.00) = **$0.0525**

### **Quality vs Cost**

| Model | Cost/Test | Quality | Speed |
|-------|-----------|---------|-------|
| `gpt-4o` | $0.05 | ⭐⭐⭐⭐⭐ | Fast |
| `gpt-4o-mini` | $0.003 | ⭐⭐⭐⭐ | Very Fast |
| `gpt-4` | $0.63 | ⭐⭐⭐⭐⭐ | Slower |

To change model, set environment variable:

```bash
export GPT_MODEL="gpt-4o-mini"
python test_crew_ai.py
```

---

## 🚀 **Next Steps**

Once testing is successful:

1. **Review challenge quality** - Check at least 5-10 challenges
2. **Test all 6 languages** - Ensure native content generation works
3. **Check costs** - Verify estimates are acceptable
4. **Read deployment guide** - See `DEPLOYMENT_CHECKLIST.md`
5. **Deploy to Railway** - Follow deployment steps

---

## 💡 **Pro Tips**

### **Tip 1: Save Test Challenges**

When prompted "Save Challenges to Database?", type `yes` to save them. Then you can:

```bash
# View in MongoDB
python -c "
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv('../../backend/.env')

async def view():
    client = AsyncIOMotorClient(os.getenv('MONGODB_URL'))
    db = client.language_tutor

    # Get last 3 challenges
    challenges = await db.challenge_pool.find().sort('created_at', -1).limit(3).to_list(3)

    for c in challenges:
        print(f\"Language: {c['language']}, Level: {c['cefr_level']}, Type: {c['challenge_type']}\")
        print(json.dumps(c['challenge_data'], indent=2, ensure_ascii=False))
        print('---')

    client.close()

asyncio.run(view())
"
```

### **Tip 2: Watch Logs in Real-Time**

Open a second terminal and watch the log file:

```bash
cd cron-service/phase2-crewai
tail -f crewai_challenges_*.log
```

### **Tip 3: Test Cheaply First**

Use `gpt-4o-mini` for initial testing (98% cheaper):

```bash
export GPT_MODEL="gpt-4o-mini"
python test_crew_ai.py --count 10  # Only $0.03 for 10 challenges!
```

Then switch to `gpt-4o` for quality validation.

### **Tip 4: Batch Testing**

Test all challenge types at once:

```bash
# Create a test script
cat > test_all.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
for type in error_spotting swipe_fix micro_quiz smart_flashcard native_check brain_tickler; do
  echo "=== Testing $type ==="
  python test_crew_ai.py --type $type --count 2 --language spanish --level B2
  sleep 3
done
EOF

chmod +x test_all.sh
./test_all.sh
```

---

## 📞 **Need Help?**

1. **Check logs:** `cat crewai_challenges_*.log`
2. **Check usage report:** `cat crewai_usage_report_*.json | jq .`
3. **Verify environment:** `python -c "import crewai, openai, motor; print('All imports OK!')"`
4. **Test MongoDB:** `python -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio, os; from dotenv import load_dotenv; load_dotenv('../../backend/.env'); asyncio.run(AsyncIOMotorClient(os.getenv('MONGODB_URL')).admin.command('ping')); print('MongoDB OK!')"`

---

## 🎉 **You're Ready!**

Virtual environments are standard Python best practice. Once you get used to them, they make development much easier!

**Remember:**
1. Always `source venv/bin/activate` before running Python commands
2. Use `deactivate` when done
3. The virtual environment is excluded from git (already in `.gitignore`)

**Happy testing!** 🚀
