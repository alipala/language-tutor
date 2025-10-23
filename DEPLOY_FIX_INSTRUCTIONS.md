# 🚀 Deployment Instructions for API URL Fix

## ⚠️ IMPORTANT: The Fix is in Source Code, Not Yet Deployed!

The changes we made are in the **source code** but the production server is still running the **old compiled JavaScript** that has `localhost:8000` hardcoded.

---

## 📋 What Needs to Happen

You need to **rebuild and redeploy** the application so the new code gets compiled and deployed to production.

---

## 🔧 Deployment Steps

### Option 1: Deploy via Git Push (Recommended)

If your production server auto-deploys from Git:

```bash
# 1. Commit the changes (if not already done)
git add -A
git commit -m "Fix: API URLs now resolve at runtime instead of build time"

# 2. Push to your production branch (usually 'main' or 'master')
git push origin main

# 3. Wait for automatic deployment to complete
# Check your Railway/Vercel/hosting dashboard for deployment status
```

### Option 2: Manual Rebuild

If you need to manually rebuild:

```bash
# 1. Clean previous builds
rm -rf .next
rm -rf frontend/.next
rm -rf frontend/out

# 2. Install dependencies (if needed)
npm install

# 3. Build the frontend
cd frontend
npm run build

# 4. Deploy the built files to your hosting service
# (This depends on your hosting provider)
```

### Option 3: Railway Specific

If using Railway:

```bash
# Trigger a new deployment
railway up

# Or use the Railway dashboard to trigger a redeploy
```

---

## ✅ How to Verify the Fix

After deployment, check the browser console:

### Before Fix (Current State):
```
GET https://localhost:8000/api/ net::ERR_SSL_PROTOCOL_ERROR
```

### After Fix (Expected):
```
GET https://mytacoai.com/api/unread-count 200 OK
```

---

## 🎯 Files That Were Changed

These files contain the fix and need to be deployed:

1. ✅ `frontend/lib/api-service.ts` - All API calls now use `getApiUrl()` at runtime
2. ✅ `frontend/hooks/useLowMinutesAlert.ts` - Uses cached API service

---

## 🔍 Why This Happened

**The Problem:**
- The old code called `getApiUrl()` at **build time** (during compilation)
- This hardcoded `localhost:8000` into the compiled JavaScript
- When deployed, the compiled code still had `localhost:8000`

**The Fix:**
- Now `getApiUrl()` is called at **runtime** (in the user's browser)
- The browser detects the correct hostname and uses the right API URL
- But this fix only works after **rebuilding and redeploying**

---

## 📝 Next Steps

1. **Commit and push** the changes to your Git repository
2. **Wait for deployment** to complete (check your hosting dashboard)
3. **Clear browser cache** and test the notifications
4. **Verify** that API calls now go to the correct domain

---

## 🆘 If Still Not Working

If after deployment you still see `localhost:8000` errors:

1. **Hard refresh** the browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
2. **Clear browser cache** completely
3. **Check deployment logs** to ensure the new code was deployed
4. **Verify the build** included the latest changes

---

## 💡 Pro Tip

To avoid this in the future, always remember:
- **Environment-dependent code** should run at runtime, not build time
- **Never call environment functions** at module level
- **Always test** in production-like environment before deploying
