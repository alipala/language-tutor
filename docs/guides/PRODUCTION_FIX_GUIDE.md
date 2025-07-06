# Production Fix Guide: Existing User Subscription Usage

## Problem
The existing user in production has:
- Learning plan progress: 1/8 sessions completed ✅
- Subscription usage: 30/30 (should be 29/30) ❌

## Solution
Run the `fix_existing_user_subscription_usage.py` script to synchronize the subscription usage counter with the actual learning plan progress.

## How to Run in Production

### Step 1: Get Railway MongoDB Connection String

1. Go to your Railway dashboard
2. Navigate to your project
3. Click on the MongoDB service
4. Go to the "Variables" tab
5. Copy the `MONGODB_URL` value (it should look like: `mongodb://mongo:password@host:port/database`)

### Step 2: Set Environment Variable Locally

```bash
# Replace with your actual Railway MongoDB URL
export MONGODB_URL="mongodb://mongo:password@host:port/database"
```

### Step 3: Install Required Dependencies

```bash
# Make sure you have the required Python packages
pip install motor pymongo
```

### Step 4: Run the Fix Script

```bash
# Navigate to the project directory
cd /path/to/language-tutor

# Run the fix script
python fix_existing_user_subscription_usage.py
```

## What the Script Does

1. **Connects** to the production MongoDB database
2. **Finds** the specific user (ID: 68643c98596dc75f6c38c443)
3. **Checks** their current subscription usage vs learning plan progress
4. **Calculates** the correct subscription usage based on completed sessions
5. **Asks for confirmation** before making any changes
6. **Updates** the `practice_sessions_used` field to match actual usage
7. **Verifies** the update was successful

## Expected Output

```
🔧 Fixing Existing User Subscription Usage
==================================================
🔍 Looking for user: 68643c98596dc75f6c38c443
✅ Found user: User Name (user@email.com)
📊 Current Status:
   - Plan: fluency_builder
   - Status: active
   - Practice Sessions Used: 0
   - Assessments Used: 0
📈 Learning Plan Progress:
   - Language: Spanish
   - Level: B1
   - Completed Sessions: 1/8

🧮 Calculating Correct Usage:
   - Learning plan shows: 1 sessions completed
   - Subscription counter shows: 0 sessions used
   - Correct value should be: 1

⚠️  PROPOSED CHANGE:
   - Update practice_sessions_used: 0 → 1

Do you want to proceed with this update? (yes/no): yes

🔄 Updating subscription usage...
✅ Successfully updated subscription usage!
📊 Updated Status:
   - Practice Sessions Used: 0 → 1
   - Frontend will now show: 29/30
   - Learning plan shows: 1/8
✅ SUCCESS: Both metrics are now synchronized!
```

## After Running the Script

The user's profile page will now show:
- **Learning Plan Progress:** 1/8 sessions completed
- **Subscription Usage:** 29/30 Practice Sessions remaining

Both metrics will be properly synchronized!

## Safety Features

- ✅ **Read-only checks first** - Shows current state before making changes
- ✅ **Confirmation required** - Asks for explicit "yes" before updating
- ✅ **Verification** - Confirms the update was successful
- ✅ **Error handling** - Graceful error handling with detailed messages
- ✅ **Specific user targeting** - Only affects the identified user

## Alternative: Railway CLI Method

If you prefer to run the script directly on Railway:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Run the script on Railway
railway run python fix_existing_user_subscription_usage.py
```

## Troubleshooting

### "MONGODB_URL environment variable not set"
- Make sure you exported the MONGODB_URL correctly
- Check that the URL is valid and accessible

### "User not found"
- Verify the user ID is correct
- Check that you're connected to the right database

### "No learning plan found"
- The user might not have a learning plan yet
- Check the learning_plans collection manually

### Connection errors
- Verify the MongoDB URL is correct
- Check network connectivity
- Ensure MongoDB service is running on Railway

---

**Important:** This script only needs to be run once to fix the existing user's data. Future sessions will be tracked correctly thanks to the code fix that was already deployed.
