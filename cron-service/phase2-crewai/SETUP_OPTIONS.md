# Phase 2 Setup - Two Options

You have an existing virtual environment at the **project root** that you use for the backend.

You have **two options** for setting up Phase 2:

---

## ✅ **Option A: Use Your Existing Root Venv** (Recommended)

**Pros:**
- ✅ Simpler - one environment for everything
- ✅ Uses your existing setup
- ✅ Fewer commands to remember

**Cons:**
- ⚠️ Phase 2 dependencies mixed with backend dependencies
- ⚠️ Potential for dependency conflicts (unlikely)

### **Setup:**

```bash
# From project root
cd /path/to/language-tutor

# Activate your existing venv
source venv/bin/activate

# Install Phase 2 dependencies
pip install -r cron-service/phase2-crewai/requirements.txt

# Test Phase 2
cd cron-service/phase2-crewai
python test_crew_ai.py
```

That's it! ✅

---

## ✅ **Option B: Use Separate Venv for Phase 2** (Better Isolation)

**Pros:**
- ✅ Complete isolation between backend and Phase 2
- ✅ No dependency conflicts
- ✅ Cleaner separation of concerns

**Cons:**
- ⚠️ Need to activate different venvs for different tasks
- ⚠️ Two separate environments to maintain

### **Setup:**

```bash
cd cron-service/phase2-crewai

# Run automated setup
./setup_venv.sh

# Activate Phase 2 venv
source venv/bin/activate

# Test
python test_crew_ai.py
```

---

## 📊 **Comparison**

| Aspect | Option A (Root Venv) | Option B (Separate Venv) |
|--------|---------------------|-------------------------|
| **Complexity** | Simpler | Slightly more complex |
| **Dependencies** | Shared | Isolated |
| **Disk Space** | ~200MB | ~400MB (2 venvs) |
| **Activation** | `source venv/bin/activate` (root) | `source cron-service/phase2-crewai/venv/bin/activate` |
| **Use Case** | Backend + Phase 2 testing | Just Phase 2 testing |

---

## 🎯 **My Recommendation: Option A**

Since you already have a working venv setup with `run_with_venv.py`, I recommend **Option A**:

1. It's simpler
2. You're already familiar with the workflow
3. CrewAI dependencies won't conflict with your backend
4. You can test Phase 2 without switching environments

---

## 🚀 **Quick Start - Option A**

```bash
# 1. Go to project root
cd /path/to/language-tutor

# 2. Activate your existing venv
source venv/bin/activate

# 3. Install Phase 2 dependencies
pip install crewai==0.80.0 crewai-tools==0.12.1

# 4. Test Phase 2
cd cron-service/phase2-crewai
python test_crew_ai.py
```

**Note:** Your backend already has most dependencies (openai, motor, pymongo, python-dotenv). You only need to add CrewAI!

---

## 🔍 **Checking What's Already Installed**

Check if your root venv already has the dependencies:

```bash
# Activate root venv
source venv/bin/activate

# Check installed packages
pip list | grep -E 'crewai|openai|motor|pymongo'
```

**Expected:**
```
openai           1.109.1  ✅ Already installed (from backend)
motor            3.3.2    ✅ Already installed (from backend)
pymongo          4.6.1    ✅ Already installed (from backend)
crewai           (none)   ❌ Need to install
crewai-tools     (none)   ❌ Need to install
```

---

## 💡 **If You Choose Option A**

You'll have this structure:

```
language-tutor/
├── venv/                          ← Your existing root venv
│   ├── bin/
│   │   └── python
│   └── lib/
│       └── python3.11/
│           └── site-packages/
│               ├── fastapi/       ← Backend dependencies
│               ├── openai/        ← Shared
│               ├── motor/         ← Shared
│               ├── crewai/        ← NEW for Phase 2
│               └── ...
│
├── backend/
│   ├── run_with_venv.py           ← Your existing runner
│   ├── main.py
│   └── requirements.txt
│
└── cron-service/
    └── phase2-crewai/
        ├── test_crew_ai.py        ← Run with root venv
        ├── challenge_crew_ai.py
        └── requirements.txt
```

**To run backend:**
```bash
cd backend
python run_with_venv.py
```

**To test Phase 2:**
```bash
source venv/bin/activate
cd cron-service/phase2-crewai
python test_crew_ai.py
```

---

## 💡 **If You Choose Option B**

You'll have this structure:

```
language-tutor/
├── venv/                          ← Backend venv
│   └── ...backend dependencies
│
├── backend/
│   ├── run_with_venv.py
│   └── ...
│
└── cron-service/
    └── phase2-crewai/
        ├── venv/                  ← Separate Phase 2 venv
        │   └── ...Phase 2 dependencies
        ├── test_crew_ai.py
        └── ...
```

**To run backend:**
```bash
cd backend
python run_with_venv.py
```

**To test Phase 2:**
```bash
cd cron-service/phase2-crewai
source venv/bin/activate
python test_crew_ai.py
```

---

## 🎯 **What I Recommend You Do Right Now**

### **Step 1: Check your existing venv**

```bash
cd /path/to/language-tutor

# Does your venv exist?
ls -la venv/bin/python
```

If yes, proceed with Option A:

```bash
# Activate it
source venv/bin/activate

# Install only what's missing (just CrewAI)
pip install crewai==0.80.0 crewai-tools==0.12.1

# Test Phase 2
cd cron-service/phase2-crewai
python test_crew_ai.py
```

### **Step 2: If venv doesn't exist**

Create it first:

```bash
cd /path/to/language-tutor

# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Install Phase 2 dependencies
pip install -r cron-service/phase2-crewai/requirements.txt

# Test backend
cd backend
python run_with_venv.py

# Test Phase 2 (in another terminal)
source venv/bin/activate
cd cron-service/phase2-crewai
python test_crew_ai.py
```

---

## 📝 **Summary**

| If you have... | Then do... |
|----------------|-----------|
| ✅ Root venv exists | **Option A** - Just install CrewAI dependencies |
| ❌ No root venv yet | **Option A** - Create root venv, install all deps |
| 🎯 Want isolation | **Option B** - Use separate venv for Phase 2 |

**My recommendation: Option A** - Use your existing root venv and add CrewAI to it. Simpler and matches your current workflow!

---

## 🚀 **One-Liner Setup (Option A)**

If your root venv exists:

```bash
source venv/bin/activate && pip install crewai==0.80.0 crewai-tools==0.12.1 && cd cron-service/phase2-crewai && python test_crew_ai.py
```

Done! ✅
