# Fix for macOS Localhost MongoDB Connection Issue

## Problem

When running the backend locally on **macOS**, you may encounter this error during login:

```
[Errno 8] nodename nor servname provided, or not known
503 Service Unavailable
```

Even though:
- ✅ Backend connects successfully at startup
- ✅ MongoDB ping works
- ✅ Same code works fine in production (Railway)

## Root Cause

This is a **known issue** with Motor (async MongoDB driver) on macOS:

1. **Motor uses asyncio's DNS resolution** on macOS, not the system resolver
2. **Railway's proxy hostname** (`crossover.proxy.rlwy.net`) sometimes fails to resolve in async context
3. **Production works fine** because Railway backend uses internal networking (`mongodb.railway.internal`)
4. **Standard Python works fine** (sync DNS), but async requests fail

This affects:
- macOS only (Linux/Railway works fine)
- Motor 2.5.0+ with newer async DNS behavior
- Railway proxy URLs (external access)

## Quick Fix (Recommended)

Run the automated fix script:

```bash
cd /Users/alipala/CascadeProjects/language-tutor/backend

# Run the fix script
./fix_local_mongodb.sh
```

This script will:
1. Backup your `.env` file
2. Resolve Railway proxy hostname to IP address
3. Replace hostname with IP in your `.env`
4. Verify the change worked

**Then restart your backend:**
```bash
python ./run_with_venv.py
```

## Manual Fix

If you prefer to do it manually:

**Step 1: Find the Railway proxy IP**
```bash
nslookup crossover.proxy.rlwy.net
# Returns: 66.33.22.252 (may change)
```

**Step 2: Edit your `.env` file**
```bash
cd /Users/alipala/CascadeProjects/language-tutor/backend
nano .env
```

**Step 3: Replace hostname with IP**

Change this line:
```env
MONGODB_URL=mongodb://mongo:PASSWORD@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin&...
```

To this (using the IP you found):
```env
MONGODB_URL=mongodb://mongo:PASSWORD@66.33.22.252:44437/language_tutor?authSource=admin&...
```

**Step 4: Save and restart backend**
```bash
python ./run_with_venv.py
```

**Step 5: Test login**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"d77240fe-5821-486a-a6cc-d61396fffa58@mailslurp.biz","password":"040050803"}'
```

Should return `200 OK` with token, not `503 Service Unavailable`.

## Alternative: Use Railway CLI

If you don't want to modify `.env`, run backend with Railway environment injection:

```bash
cd /Users/alipala/CascadeProjects/language-tutor/backend

# This automatically uses Railway's environment variables
railway run python ./run_with_venv.py
```

## Alternative: Use Local MongoDB

For faster local development:

```bash
# Start local MongoDB
docker run -d -p 27017:27017 --name mongodb-dev mongo:latest

# Update .env
MONGODB_URL=mongodb://localhost:27017/language_tutor_dev
```

## Why This Happened

This issue appeared after:
1. **Virtual environment recreation** - Newer Motor version installed
2. **Connection pool changes** - Phase 3.1 added `maxPoolSize=50` which creates more connections
3. **DNS cache cleared** - macOS DNS cache was flushed or network changed

## Production is Unaffected

**Railway production uses internal networking:**
```env
# Production backend .env (on Railway)
MONGODB_URL=mongodb://mongo:PASSWORD@mongodb.railway.internal:27017/language_tutor
```

Not the public proxy! So this issue only affects local development on macOS.

## Verify the Fix

After applying the fix, you should see:

**Backend startup:**
```
Connecting to MongoDB at: mongodb://***:***@66.33.22.252:44437
MongoDB connection verified with ping ✅
```

**Login request:**
```bash
curl -X POST "http://localhost:8000/api/auth/login" ...
# Returns 200 OK with token ✅
```

## If Railway Changes Proxy IP

Railway sometimes rotates proxy IPs. If the fix stops working:

1. Re-run the fix script: `./fix_local_mongodb.sh`
2. Or check Railway dashboard for new URL
3. Or use `railway variables get MONGODB_URL`

## Long-term Solution

For permanent local development setup, consider:

1. **Use Railway CLI** - Always fresh credentials
2. **Use local MongoDB** - No network dependency
3. **Use Docker Compose** - Full stack locally

## Related Links

- Motor macOS DNS issue: https://github.com/mongodb/motor/issues/493
- Railway proxy docs: https://docs.railway.app/guides/public-networking
- Phase 3.1 implementation: `/PHASE3.1_IOS_INTEGRATION.md`

## Support

If the fix doesn't work:
1. Check Railway dashboard for current MongoDB URL
2. Verify Railway proxy is accessible: `nc -zv crossover.proxy.rlwy.net 44437`
3. Try Railway CLI: `railway run python ./run_with_venv.py`
4. Check backend logs for specific error messages
