# Slack Webhook Setup & Railway Deployment Guide

## 🎯 Goal
Set up Slack webhook integration and deploy the monitoring system to Railway for production testing on the `feature/application-monitoring` branch.

## 📋 Step-by-Step Instructions

### 1. 🔧 Create Slack Webhook URL

#### Option A: Using Slack Workflow Builder (Recommended)
1. **Open Slack** and go to your workspace
2. **Click on your workspace name** (top left) → **Settings & administration** → **Manage apps**
3. **Search for "Incoming Webhooks"** and click **Add to Slack**
4. **Choose a channel** where you want to receive alerts (e.g., `#alerts`, `#monitoring`, `#mytaco-alerts`)
5. **Click "Add Incoming Webhooks integration"**
6. **Copy the Webhook URL** - it will look like:
   ```
   https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
   ```
7. **Customize the integration** (optional):
   - **Descriptive Label**: "MyTaco AI Monitoring"
   - **Customize Name**: "MyTaco Monitor"
   - **Customize Icon**: Upload a custom icon or emoji

#### Option B: Using Slack App (Advanced)
1. **Go to** https://api.slack.com/apps
2. **Click "Create New App"** → **From scratch**
3. **App Name**: "MyTaco AI Monitoring"
4. **Pick a workspace** where you want to install the app
5. **Go to "Incoming Webhooks"** in the left sidebar
6. **Toggle "Activate Incoming Webhooks"** to On
7. **Click "Add New Webhook to Workspace"**
8. **Select the channel** for alerts
9. **Copy the Webhook URL**

### 2. 🚀 Deploy to Railway for Production Testing

#### Step 1: Push Feature Branch to GitHub
```bash
# Make sure you're on the feature branch
git branch
# Should show: * feature/application-monitoring

# Push the feature branch to GitHub
git push origin feature/application-monitoring
```

#### Step 2: Deploy Feature Branch on Railway
1. **Go to Railway Dashboard**: https://railway.app/dashboard
2. **Find your MyTaco AI project**
3. **Click on your backend service**
4. **Go to "Settings" tab**
5. **In "Source" section**, click **"Configure GitHub Repo"**
6. **Change the branch** from `main` to `feature/application-monitoring`
7. **Click "Update"** - Railway will automatically redeploy from the feature branch

#### Step 3: Add Environment Variables in Railway
1. **In your Railway backend service**, go to **"Variables" tab**
2. **Add the following environment variables**:

```bash
# Monitoring Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
PERFORMANCE_THRESHOLD=5.0
ERROR_RATE_THRESHOLD=10.0

# Make sure these existing variables are still set:
ENVIRONMENT=production
OPENAI_API_KEY=your_openai_key
MONGODB_URL=your_mongodb_url
STRIPE_SECRET_KEY=your_stripe_key
# ... (all your existing variables)
```

#### Step 4: Verify Deployment
1. **Wait for deployment to complete** (usually 2-3 minutes)
2. **Check the deployment logs** for any errors
3. **Look for these log messages**:
   ```
   [SLACK_NOTIFIER] Initialized for production environment
   [SLACK_NOTIFIER] Webhook configured: True
   [MONITORING_MIDDLEWARE] Initialized with enhanced error handling and alerting
   ```

### 3. 🧪 Test the Monitoring System

#### Option A: Run Test Script Locally (Recommended)
```bash
# In your local backend directory
cd backend

# Set the Slack webhook URL in your local .env file
echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL" >> .env

# Run the test suite
python test_monitoring.py
```

#### Option B: Test in Production
1. **Visit your production site** and try to trigger some errors:
   - Try accessing a non-existent endpoint: `https://your-app.railway.app/api/nonexistent`
   - Try the OpenAI token endpoint without proper auth
   - Try accessing protected routes

2. **Check your Slack channel** for alerts

#### Option C: Manual Test via Railway Console
1. **In Railway**, go to your backend service
2. **Click "Console" tab**
3. **Run the test script**:
   ```bash
   cd backend
   python test_monitoring.py
   ```

### 4. 📊 What to Expect

#### Successful Setup Indicators:
- ✅ **Slack Test Alert**: You should receive a test alert in your Slack channel
- ✅ **Error Alerts**: Different colored alerts based on severity
- ✅ **Performance Alerts**: Alerts for slow responses
- ✅ **Rich Context**: User info, endpoint details, timestamps

#### Sample Alert Format:
```
🚨 CRITICAL Alert from MyTaco AI

OpenAI_API_Error: OpenAI API rate limit exceeded

Endpoint: POST /api/realtime/token
User: user@example.com
Environment: PRODUCTION
Time: 2025-06-07 17:58:00 UTC

Stack Trace:
```
Error details...
```
```

### 5. 🔧 Monitoring Configuration

#### Recommended Slack Channel Setup:
- **Channel Name**: `#mytaco-alerts` or `#monitoring`
- **Channel Purpose**: "Real-time alerts from MyTaco AI production"
- **Notification Settings**: Enable notifications for all messages

#### Alert Severity Levels:
- 🚨 **CRITICAL** (Red): OpenAI failures, Database issues
- ⚠️ **HIGH** (Orange): Payment errors, Auth failures
- ⚡ **MEDIUM** (Yellow): Performance issues, Business logic errors
- ℹ️ **LOW** (Blue): Info and test alerts

#### Performance Thresholds:
- **Default**: 5 seconds response time threshold
- **Adjustable**: Set `PERFORMANCE_THRESHOLD=X.X` in Railway variables

### 6. 🚨 Troubleshooting

#### No Alerts Received:
1. **Check Slack webhook URL** is correct in Railway variables
2. **Verify channel permissions** - webhook should have access
3. **Check Railway logs** for error messages
4. **Test webhook manually**:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
   --data '{"text":"Test message"}' \
   YOUR_WEBHOOK_URL
   ```

#### Too Many Alerts:
1. **Increase deduplication window** (currently 5 minutes)
2. **Adjust performance threshold** to higher value
3. **Check for infinite loops** in error handling

#### Missing Context in Alerts:
1. **Verify user authentication** is working
2. **Check middleware order** in main.py
3. **Ensure request state** is being set properly

### 7. 📈 Monitoring Best Practices

#### During Testing:
- **Monitor alert volume** - should not be spammy
- **Verify alert accuracy** - alerts should correspond to real issues
- **Test different error types** - OpenAI, Database, Stripe, Auth
- **Check performance alerts** - test with slow endpoints

#### For Production:
- **Set up dedicated Slack channel** for alerts
- **Configure notification preferences** for team members
- **Document alert response procedures**
- **Regular monitoring system health checks**

### 8. 🔄 Switching Back to Main Branch

#### When Testing is Complete:
```bash
# In Railway Dashboard:
# 1. Go to backend service Settings
# 2. Change branch back to "main"
# 3. Remove test environment variables if needed

# Locally, switch back to main:
git checkout main
```

## 🎉 Success Criteria

After setup, you should have:
- ✅ Real-time Slack alerts for production errors
- ✅ Performance monitoring for slow responses
- ✅ Rich context in all alerts (user, endpoint, stack trace)
- ✅ Smart deduplication preventing spam
- ✅ Color-coded severity levels
- ✅ Production-ready monitoring system

## 📞 Support

If you encounter issues:
1. **Check Railway deployment logs** for errors
2. **Verify Slack webhook URL** is accessible
3. **Run local test suite** to isolate issues
4. **Check environment variables** are set correctly

---

**Ready to monitor MyTaco AI in production! 🚀**
