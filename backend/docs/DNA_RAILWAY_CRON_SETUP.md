# Speaking DNA - Railway Cron Job Setup Guide

**Last Updated:** January 28, 2026

## Overview

This guide explains how to set up and test the weekly snapshot background job on Railway for the Speaking DNA feature.

---

## Table of Contents
1. [Understanding the Background Job](#understanding-the-background-job)
2. [Implementation Options](#implementation-options)
3. [Option 1: Railway Cron Job (Recommended)](#option-1-railway-cron-job-recommended)
4. [Option 2: Manual HTTP Endpoint](#option-2-manual-http-endpoint)
5. [Option 3: APScheduler In-Process](#option-3-apscheduler-in-process)
6. [Testing the Background Job](#testing-the-background-job)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)

---

## Understanding the Background Job

**Purpose:** Create weekly snapshots for all active users' DNA profiles every Monday at 00:00 UTC.

**What It Does:**
1. Finds all users with DNA profiles
2. For each user+language combination:
   - Checks if a snapshot exists for the current week
   - Creates new snapshot if needed
   - Updates existing snapshot if it exists

**Why Weekly?**
- Provides evolution timeline for users
- Fills gaps when users don't practice every week
- Enables historical tracking and visualization

---

## Implementation Options

### Option 1: Railway Cron Job (Recommended) ⭐
**Pros:**
- Separate service, doesn't affect main app
- Railway manages scheduling
- Easy to monitor and restart

**Cons:**
- Requires setting up a new Railway service

### Option 2: Manual HTTP Endpoint
**Pros:**
- Simple implementation
- Can be triggered manually or via external cron (GitHub Actions, etc.)

**Cons:**
- Need authentication
- Must set up external scheduler

### Option 3: APScheduler In-Process
**Pros:**
- Runs within main app
- No external dependencies

**Cons:**
- Runs on all instances (need leader election for multiple workers)
- Restarts when app restarts

---

## Option 1: Railway Cron Job (Recommended)

### Step 1: Create the Cron Script

Create `/Users/alipala/CascadeProjects/language-tutor/backend/cron_jobs/weekly_snapshots.py`:

```python
"""
Weekly Snapshots Cron Job
=========================
Creates weekly DNA snapshots for all active users.
Run every Monday at 00:00 UTC.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.speaking_dna_service import speaking_dna_service


async def create_weekly_snapshots_for_all_users():
    """
    Create weekly snapshots for all users with DNA profiles.
    """
    print(f"[CRON] Starting weekly snapshot creation at {datetime.utcnow()}")

    # Connect to MongoDB
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        print("[CRON] ERROR: MONGODB_URL not set")
        return

    client = AsyncIOMotorClient(mongodb_url)
    db = client[os.getenv("DATABASE_NAME", "language_tutor")]

    # Inject database into service
    speaking_dna_service.db = db

    try:
        # Get all unique user+language combinations from DNA profiles
        profiles = await db.speaking_dna_profiles.find({}).to_list(None)

        print(f"[CRON] Found {len(profiles)} DNA profiles to process")

        success_count = 0
        error_count = 0

        for profile in profiles:
            try:
                user_id = profile["user_id"]
                language = profile["language"]
                strands = profile.get("dna_strands", {})

                print(f"[CRON] Processing {user_id} - {language}")

                # Create/update weekly snapshot
                await speaking_dna_service._create_weekly_snapshot(
                    user_id=user_id,
                    language=language,
                    strands=strands,
                    session_duration_minutes=0,  # No new session, just snapshot
                    breakthroughs_count=0
                )

                success_count += 1

            except Exception as e:
                print(f"[CRON] Error processing {user_id}-{language}: {str(e)}")
                error_count += 1

        print(f"[CRON] Completed. Success: {success_count}, Errors: {error_count}")

    except Exception as e:
        print(f"[CRON] Fatal error: {str(e)}")
        raise

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(create_weekly_snapshots_for_all_users())
```

### Step 2: Create Railway Cron Service

**In Railway Dashboard:**

1. **Create New Service:**
   - Click "+ New"
   - Select "Empty Service"
   - Name it: `language-tutor-dna-cron`

2. **Connect to GitHub:**
   - Same repository as main backend
   - Same branch

3. **Configure Build:**
   - Root Directory: `backend`
   - Build Command: (leave empty)
   - Start Command: `python cron_jobs/weekly_snapshots.py`

4. **Set Environment Variables:**
   ```
   MONGODB_URL=your_mongodb_connection_string
   DATABASE_NAME=language_tutor
   ```

5. **Configure Cron Schedule:**
   - Go to Settings → Cron
   - Schedule: `0 0 * * 1`  (Every Monday at 00:00 UTC)
   - Enable Cron

### Step 3: Test the Cron Service

**Manual Test from Railway:**
1. Go to your cron service
2. Click "Deploy" → "Trigger Deploy"
3. Watch logs for output:
   ```
   [CRON] Starting weekly snapshot creation at 2026-01-28 10:00:00
   [CRON] Found 15 DNA profiles to process
   [CRON] Processing user_123 - dutch
   [DNA] Creating/updating weekly snapshot for week starting 2026-01-27
   [DNA] Weekly snapshot created successfully
   ...
   [CRON] Completed. Success: 15, Errors: 0
   ```

---

## Option 2: Manual HTTP Endpoint

### Step 1: Add Admin Route

Add to `/Users/alipala/CascadeProjects/language-tutor/backend/routes/speaking_dna_routes.py`:

```python
@router.post("/admin/create-weekly-snapshots")
async def create_weekly_snapshots_admin(
    admin_key: str = Query(..., description="Admin API key"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    ADMIN ONLY: Manually trigger weekly snapshot creation for all users.

    This endpoint is protected by admin_key and should be called weekly
    via external cron service (GitHub Actions, etc.)
    """
    # Verify admin key
    ADMIN_KEY = os.getenv("ADMIN_API_KEY")
    if not ADMIN_KEY or admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    logger.info("[DNA ADMIN] Starting manual weekly snapshot creation")

    try:
        # Get all DNA profiles
        profiles = await speaking_dna_profiles_collection.find({}).to_list(None)
        logger.info(f"[DNA ADMIN] Found {len(profiles)} profiles")

        results = {"success": [], "errors": []}

        for profile in profiles:
            try:
                user_id = profile["user_id"]
                language = profile["language"]

                await speaking_dna_service._create_weekly_snapshot(
                    user_id=user_id,
                    language=language,
                    strands=profile.get("dna_strands", {}),
                    session_duration_minutes=0,
                    breakthroughs_count=0
                )

                results["success"].append(f"{user_id}-{language}")

            except Exception as e:
                results["errors"].append({
                    "user": f"{user_id}-{language}",
                    "error": str(e)
                })

        logger.info(f"[DNA ADMIN] Completed. Success: {len(results['success'])}, Errors: {len(results['errors'])}")

        return {
            "success": True,
            "processed": len(profiles),
            "succeeded": len(results["success"]),
            "failed": len(results["errors"]),
            "details": results
        }

    except Exception as e:
        logger.error(f"[DNA ADMIN] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 2: Set Environment Variable

In Railway, add:
```
ADMIN_API_KEY=your_secure_random_key_here
```

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 3: Test the Endpoint

```bash
curl -X POST "https://your-backend.railway.app/api/speaking-dna/admin/create-weekly-snapshots?admin_key=YOUR_ADMIN_KEY" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Step 4: Schedule with GitHub Actions (Optional)

Create `.github/workflows/weekly-dna-snapshots.yml`:

```yaml
name: Weekly DNA Snapshots

on:
  schedule:
    - cron: '0 0 * * 1'  # Every Monday at 00:00 UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  create-snapshots:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Weekly Snapshots
        run: |
          curl -X POST "${{ secrets.API_BASE_URL }}/api/speaking-dna/admin/create-weekly-snapshots?admin_key=${{ secrets.ADMIN_API_KEY }}" \
            -H "Authorization: Bearer ${{ secrets.API_AUTH_TOKEN }}"
```

Add secrets to GitHub repository:
- `API_BASE_URL`: Your Railway backend URL
- `ADMIN_API_KEY`: Your admin key
- `API_AUTH_TOKEN`: A valid JWT token (create a service account)

---

## Option 3: APScheduler In-Process

### Step 1: Install Dependencies

Add to `requirements.txt`:
```
APScheduler==3.10.4
```

### Step 2: Create Scheduler Module

Create `/Users/alipala/CascadeProjects/language-tutor/backend/scheduler.py`:

```python
"""
Background task scheduler using APScheduler
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import logging

from services.speaking_dna_service import speaking_dna_service
from database import speaking_dna_profiles_collection

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def create_weekly_snapshots():
    """Background job: Create weekly snapshots for all users"""
    logger.info("[SCHEDULER] Starting weekly snapshot creation")

    try:
        profiles = await speaking_dna_profiles_collection.find({}).to_list(None)
        logger.info(f"[SCHEDULER] Processing {len(profiles)} profiles")

        for profile in profiles:
            await speaking_dna_service._create_weekly_snapshot(
                user_id=profile["user_id"],
                language=profile["language"],
                strands=profile.get("dna_strands", {}),
                session_duration_minutes=0,
                breakthroughs_count=0
            )

        logger.info("[SCHEDULER] Weekly snapshots completed")

    except Exception as e:
        logger.error(f"[SCHEDULER] Error: {str(e)}", exc_info=True)


def start_scheduler():
    """Start the background scheduler"""
    # Run every Monday at 00:00 UTC
    scheduler.add_job(
        create_weekly_snapshots,
        'cron',
        day_of_week='mon',
        hour=0,
        minute=0,
        id='weekly_dna_snapshots',
        replace_existing=True
    )

    scheduler.start()
    logger.info("[SCHEDULER] Started")


def stop_scheduler():
    """Stop the scheduler"""
    scheduler.shutdown()
    logger.info("[SCHEDULER] Stopped")
```

### Step 3: Integrate with FastAPI

In `main.py`:

```python
from scheduler import start_scheduler, stop_scheduler

@app.on_event("startup")
async def startup_event():
    await init_db()
    start_scheduler()  # Start background scheduler
    logger.info("✅ Application started")

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()  # Stop scheduler
    logger.info("👋 Application shutdown")
```

**⚠️ Warning:** This will run on all Railway instances. For production, implement leader election or use Option 1.

---

## Testing the Background Job

### Method 1: Test Locally

```bash
cd /Users/alipala/CascadeProjects/language-tutor/backend

# Run the cron script directly
python cron_jobs/weekly_snapshots.py
```

### Method 2: Test on Railway (Manual Trigger)

**Using Railway CLI:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Trigger the cron job
railway run python cron_jobs/weekly_snapshots.py
```

### Method 3: Force Cron Execution

1. Go to Railway Dashboard
2. Select your cron service
3. Click "Deployments"
4. Click "Trigger Deploy" (this will run the cron job immediately)

---

## Monitoring & Troubleshooting

### Check if Snapshots Were Created

**Query MongoDB:**
```javascript
// Get snapshots from this week
db.speaking_dna_history.find({
  week_start: {
    $gte: ISODate("2026-01-27T00:00:00Z"),
    $lt: ISODate("2026-02-03T00:00:00Z")
  }
}).count()
```

### Monitor Cron Logs in Railway

1. Go to cron service in Railway
2. Click "Deployments" → Select latest deployment
3. Click "View Logs"
4. Look for:
   ```
   [CRON] Starting weekly snapshot creation
   [CRON] Found X DNA profiles
   [CRON] Completed. Success: X, Errors: 0
   ```

### Common Issues

**Issue 1: Cron not running**
- Check cron schedule is configured in Railway
- Verify environment variables are set
- Check service is deployed and running

**Issue 2: MongoDB connection fails**
- Verify `MONGODB_URL` environment variable
- Check MongoDB network access (whitelist Railway IPs)
- Test connection manually

**Issue 3: Snapshots not creating**
- Check if DNA profiles exist in database
- Verify `_create_weekly_snapshot` method is working
- Check for errors in logs

---

## Recommended Setup

For production, we recommend **Option 1 (Railway Cron Job)**:

1. **Week 1:** Implement Option 2 (HTTP endpoint) for immediate testing
2. **Week 2:** Set up Option 1 (Railway Cron) for production

This gives you:
- ✅ Manual trigger capability (for testing)
- ✅ Automated weekly execution (for production)
- ✅ Separate service (better reliability)

---

**Questions or issues? Check the implementation:**
- Cron script: `/Users/alipala/CascadeProjects/language-tutor/backend/cron_jobs/weekly_snapshots.py`
- DNA service: `/Users/alipala/CascadeProjects/language-tutor/backend/services/speaking_dna_service.py`
- Admin routes: `/Users/alipala/CascadeProjects/language-tutor/backend/routes/speaking_dna_routes.py`
