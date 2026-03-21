# 🔧 MongoDB Connection Pool Optimization

## Problem: Connection Limit Bottleneck

**Current Situation:**
- Railway MongoDB: ~500 concurrent connections max
- Each active user: ~2 connections
- **Current limit: 250 concurrent users**

**Goal:** Increase connection pool to support more users

---

## ✅ Solution 1: Optimize Motor Connection Pool (QUICK FIX)

### Current Configuration (database.py line 60):

```python
client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
```

**Problem:** Using Motor defaults, no connection pool optimization

### ✅ Recommended Configuration:

Update `backend/database.py` line 60 to:

```python
client = AsyncIOMotorClient(
    MONGODB_URL,
    serverSelectionTimeoutMS=30000,
    maxPoolSize=100,           # Max connections per replica (default: 100)
    minPoolSize=10,            # Min connections to maintain (default: 0)
    maxIdleTimeMS=45000,       # Close idle connections after 45s (default: None)
    waitQueueTimeoutMS=5000,   # Wait 5s for connection from pool (default: None)
    connectTimeoutMS=10000,    # Timeout for initial connection (default: 20000)
    socketTimeoutMS=45000,     # Timeout for socket operations (default: None)
)
```

### Explanation:

| **Parameter** | **Current** | **Recommended** | **Why** |
|--------------|-------------|----------------|---------|
| `maxPoolSize` | 100 (default) | **100-200** | Max connections per client |
| `minPoolSize` | 0 (default) | **10** | Keeps pool warm, faster responses |
| `maxIdleTimeMS` | None (never close) | **45000** (45s) | Free up idle connections |
| `waitQueueTimeoutMS` | None (wait forever) | **5000** (5s) | Fail fast if pool exhausted |
| `connectTimeoutMS` | 20000 (20s) | **10000** (10s) | Faster failure detection |
| `socketTimeoutMS` | None (no timeout) | **45000** (45s) | Prevent hanging connections |

### Impact:

**Before:**
- Default pool size: 100 connections
- Idle connections: Never close (wasted)
- Wait time: Forever (can hang)

**After:**
- Pool size: 100-200 connections (configurable)
- Idle connections: Close after 45s (efficient)
- Wait time: 5s timeout (fast failure)
- Min pool: 10 connections (always ready)

**Result:** Better connection management, but still limited by Railway MongoDB (~500 total)

---

## ⚠️ Railway MongoDB Limitations

### Problem: Railway MongoDB has Hard Limits

Railway's managed MongoDB has server-side connection limits:
- **~500 concurrent connections total** (estimated, not documented)
- Cannot be configured from client side
- Shared resource across all clients

### Verification:

You can check actual connection limit by:

```bash
# Connect to Railway MongoDB
railway run mongosh $MONGODB_URL

# In mongo shell
db.serverStatus().connections

# Output will show:
# {
#   current: 45,
#   available: 455,   <-- This is your limit
#   totalCreated: 1234
# }
```

**If `available` shows ~500, you're hitting Railway's hard limit.**

---

## 🚀 Solution 2: Multiple Backend Replicas (BETTER)

### How It Works:

When you deploy 2 Railway replicas:
- Each replica has its own Motor client
- Each client has its own connection pool
- **Total connections: 2 × maxPoolSize**

### Example:

**1 Replica:**
- maxPoolSize: 100
- Total connections: 100
- Concurrent users: ~50 (at 2 connections/user)

**2 Replicas:**
- maxPoolSize: 100 each
- Total connections: 200
- Concurrent users: ~100

**3 Replicas:**
- maxPoolSize: 100 each
- Total connections: 300
- Concurrent users: ~150

### Calculation:

```
Concurrent Users = (Replicas × maxPoolSize) ÷ Connections per User
                 = (2 × 100) ÷ 2
                 = 100 users
```

### Limitations:

**Railway MongoDB total limit: ~500 connections**

So with 2 replicas:
- 2 × 100 = 200 connections used
- Leaves 300 available
- **Still within Railway limit** ✅

With 5 replicas:
- 5 × 100 = 500 connections
- **At Railway limit** ⚠️

---

## 🎯 Solution 3: Increase maxPoolSize (RISKY)

### Configuration:

```python
client = AsyncIOMotorClient(
    MONGODB_URL,
    maxPoolSize=250,  # Increased from 100 (RISKY)
    # ... other settings
)
```

### With 2 Replicas:

- 2 replicas × 250 connections = **500 connections**
- Uses 100% of Railway MongoDB limit
- **No room for spikes** ⚠️

### Risks:

1. **Connection exhaustion**
   - Any spike above 2 replicas × 250 = failure
   - No safety margin

2. **Other services starved**
   - If you have other services using same MongoDB
   - They won't get connections

3. **Hard to debug**
   - Errors like "connection pool exhausted"
   - Intermittent failures under load

### Recommendation:

**DO NOT increase beyond 200 per replica** unless you're certain of Railway's exact limit.

---

## ✅ RECOMMENDED: Optimized Configuration

### Step 1: Update database.py

Edit `/Users/alipala/CascadeProjects/language-tutor/backend/database.py` line 58-60:

**Replace:**
```python
try:
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
    database = client[DATABASE_NAME]
```

**With:**
```python
try:
    # Optimized connection pool for Railway MongoDB
    client = AsyncIOMotorClient(
        MONGODB_URL,
        serverSelectionTimeoutMS=30000,

        # Connection pool optimization
        maxPoolSize=100,           # Conservative limit (safe for Railway)
        minPoolSize=10,            # Keep pool warm
        maxIdleTimeMS=45000,       # Close idle connections after 45s
        waitQueueTimeoutMS=5000,   # Fail fast if pool exhausted

        # Timeout optimization
        connectTimeoutMS=10000,    # Faster connection timeout
        socketTimeoutMS=45000,     # Prevent hanging sockets

        # Connection optimization
        retryWrites=True,          # Retry failed writes once
        retryReads=True,           # Retry failed reads once

        # Logging (optional, for debugging)
        # event_listeners=[ConnectionPoolListener()],  # Uncomment to debug
    )
    database = client[DATABASE_NAME]
```

### Step 2: Add Monitoring (Optional)

Add connection pool monitoring to see actual usage:

```python
# At top of database.py
from pymongo.monitoring import ConnectionPoolListener
import logging

class MongoConnectionPoolListener(ConnectionPoolListener):
    """Monitor connection pool events"""

    def pool_created(self, event):
        logging.info(f"[MONGO] Connection pool created: {event.address}")

    def pool_closed(self, event):
        logging.info(f"[MONGO] Connection pool closed: {event.address}")

    def connection_created(self, event):
        logging.debug(f"[MONGO] Connection created: {event.connection_id}")

    def connection_closed(self, event):
        logging.debug(f"[MONGO] Connection closed: {event.connection_id}")

    def connection_check_out_started(self, event):
        logging.debug(f"[MONGO] Connection checkout started")

    def connection_checked_out(self, event):
        logging.debug(f"[MONGO] Connection checked out: {event.connection_id}")

# Then use it in AsyncIOMotorClient:
client = AsyncIOMotorClient(
    MONGODB_URL,
    # ... other settings
    event_listeners=[MongoConnectionPoolListener()],
)
```

**With monitoring, you can see in Railway logs:**
```
[MONGO] Connection pool created: mongodb://...
[MONGO] Connection created: 12345
[MONGO] Connection checked out: 12345
```

---

## 📊 Expected Results

### Before Optimization:

```
maxPoolSize: 100 (default)
minPoolSize: 0 (default)
Idle connections: Never closed
Timeouts: No limits

With 1 replica:
- Max connections: 100
- Concurrent users: ~50
- Problem: Idle connections waste resources
```

### After Optimization:

```
maxPoolSize: 100
minPoolSize: 10
maxIdleTimeMS: 45000
waitQueueTimeoutMS: 5000

With 1 replica:
- Max connections: 100
- Active connections: 10-50 (based on load)
- Concurrent users: ~50
- Benefit: Efficient connection usage, fast failures
```

### With 2 Replicas + Optimization:

```
Each replica:
- maxPoolSize: 100
- minPoolSize: 10

Total:
- Max connections: 200
- Active connections: 20-100 (based on load)
- Concurrent users: ~100
- Railway usage: 200/500 (40%, safe margin)
```

---

## 🚨 What If You Still Need More Connections?

### Option A: Increase maxPoolSize to 150-200 (RISKY)

**With 2 replicas:**
- 2 × 200 = 400 connections
- Railway limit: 500
- Margin: 100 (20% buffer)

**Risk:** Low margin for spikes

**When to use:** Temporary measure while planning MongoDB Atlas migration

---

### Option B: Migrate to MongoDB Atlas (RECOMMENDED)

**MongoDB Atlas M10 Tier:**
- **Connection limit: 1,500+** (vs Railway's ~500)
- Replica set (3 nodes for HA)
- Automated backups
- Better monitoring
- Managed service

**Capacity:**
- With 2 replicas × 100 maxPoolSize = 200 connections
- Atlas limit: 1,500
- **Usage: 13% (huge margin!)**

**Cost:** $57/month (vs Railway MongoDB ~$10/month)

**ROI:** 3x connection capacity + HA + backups for $47/month

---

## 📋 Implementation Steps

### Step 1: Deploy Connection Pool Optimization (5 minutes)

```bash
cd /Users/alipala/CascadeProjects/language-tutor/backend

# Edit database.py (update client initialization)
# Add optimized parameters shown above

# Commit changes
git add database.py
git commit -m "Optimize MongoDB connection pool

- Increase minPoolSize to 10 (keep pool warm)
- Add maxIdleTimeMS=45000 (close idle connections)
- Add waitQueueTimeoutMS=5000 (fail fast)
- Add socket and connection timeouts
- Enable retry reads/writes"

# Push to Railway
git push origin main

# Watch deployment
railway logs -f
```

**Expected log output:**
```
MongoDB client initialized successfully
MongoDB connection verified with ping
[MONGO] Connection pool created: mongodb://...
```

### Step 2: Monitor Connection Usage

**Check Railway MongoDB connections:**

```bash
# Connect to Railway MongoDB
railway run mongosh $MONGODB_URL

# Check connection stats
db.serverStatus().connections

# Output:
{
  current: 45,       # Current active connections
  available: 455,    # Available connections
  totalCreated: 234  # Total created since restart
}
```

**Monitor in application logs:**

```bash
railway logs | grep "MONGO"

# You'll see:
[MONGO] Connection pool created
[MONGO] Connection created: 12345
[MONGO] Using 45/100 connections
```

### Step 3: Test Under Load

**Simulate concurrent users:**

```bash
# Test script (create test_concurrent_users.sh)
#!/bin/bash

for i in {1..100}; do
  curl -X POST https://mytacoai.com/api/realtime/token \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"language":"dutch","level":"B1"}' &
done

wait
```

**Monitor connections during test:**

```bash
# In separate terminal
watch -n 1 'railway run mongosh $MONGODB_URL --eval "db.serverStatus().connections"'

# Should see:
{
  current: 85,      # Spikes during test
  available: 415,   # Decreases during test
  totalCreated: 456
}
```

---

## 🎯 Recommendations

### Immediate (This Week):

1. ✅ **Deploy connection pool optimization** (5 min, FREE)
   - Update `database.py` with optimized settings
   - Better connection management
   - Fast failure detection

### Short-Term (Next 2 Weeks):

2. ✅ **Deploy 2 Railway replicas** (5 min, +$60/mo)
   - Double connection capacity (100 → 200)
   - High availability bonus
   - Still within Railway MongoDB limit

**Result:** 200 connections, supports ~100 concurrent users

### Medium-Term (Next 30 Days):

3. ✅ **Migrate to MongoDB Atlas M10** (1-2 days, +$47/mo)
   - 1,500+ connection limit (3x Railway)
   - Replica set (HA)
   - Automated backups
   - Removes bottleneck

**Result:** 1,500 connections, supports 750+ concurrent users

---

## 💰 Cost Comparison

| **Option** | **Connections** | **Concurrent Users** | **Cost** | **Time** |
|-----------|----------------|---------------------|---------|---------|
| **Current** (1 replica, default) | 100 | ~50 | $0 | - |
| **Optimized** (1 replica, tuned) | 100 | ~50 | $0 | 5 min |
| **2 Replicas + Optimized** | 200 | ~100 | +$60/mo | 10 min |
| **MongoDB Atlas M10** | 1,500 | ~750 | +$47/mo | 1-2 days |

**Best Value:** MongoDB Atlas M10 (3x capacity for same cost as replicas)

---

## 🆘 Troubleshooting

### Issue: "Connection pool exhausted" errors

**Diagnosis:**
```bash
railway logs | grep "pool exhausted"
```

**Solution:**
1. Check Railway MongoDB connection limit
2. Reduce `maxPoolSize` to be safer
3. Add more replicas (if within Railway limit)
4. Migrate to MongoDB Atlas

---

### Issue: Slow queries causing connection hogging

**Diagnosis:**
```bash
# Check slow queries
railway run mongosh $MONGODB_URL --eval "db.currentOp({secs_running: {$gt: 5}})"
```

**Solution:**
1. Add database indexes (see `INFRASTRUCTURE_IMPROVEMENTS_SUMMARY.md`)
2. Optimize queries
3. Lower `socketTimeoutMS` to kill slow queries faster

---

### Issue: Connections never released

**Diagnosis:**
```bash
railway run mongosh $MONGODB_URL --eval "db.serverStatus().connections"

# If 'current' stays high even with no traffic:
{
  current: 95,  # Should drop when idle
  available: 405
}
```

**Solution:**
- Add `maxIdleTimeMS=45000` (closes idle connections)
- Restart backend to clear stuck connections

---

## ✅ Summary

**Quick Win (5 min, FREE):**
```python
# Update database.py
client = AsyncIOMotorClient(
    MONGODB_URL,
    maxPoolSize=100,
    minPoolSize=10,
    maxIdleTimeMS=45000,
    waitQueueTimeoutMS=5000,
)
```

**Better Win (10 min, +$60/mo):**
- Connection pool optimization (above)
- 2 Railway replicas
- Result: 200 connections, ~100 concurrent users

**Best Win (1-2 days, +$47/mo):**
- Migrate to MongoDB Atlas M10
- Result: 1,500+ connections, 750+ concurrent users
- Removes bottleneck permanently

**My Recommendation:**
1. Deploy connection pool optimization NOW (5 min, FREE)
2. Plan MongoDB Atlas migration for next month (better than replicas)
3. Skip 2 replicas UNLESS you need HA urgently

**Why:** MongoDB Atlas gives 3x capacity for same cost as replicas, plus HA and backups.
