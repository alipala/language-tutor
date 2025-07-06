# 🚨 Fix Slack Webhook Issue - Invalid Token Error

## ❌ **Problem Identified**
The Slack webhook is returning `403 invalid_token` error, which means:
- The webhook URL has expired
- The webhook URL is incorrect
- The Slack app/integration was removed or regenerated

## 🔧 **Solution: Generate New Slack Webhook URL**

### **Step 1: Create New Slack Webhook**

#### **Option A: Quick Fix - Incoming Webhooks App**
1. **Go to Slack** → Your workspace
2. **Click workspace name** (top left) → **Settings & administration** → **Manage apps**
3. **Search for "Incoming Webhooks"** → Click **Add to Slack**
4. **Choose #mytaco-alerts channel** (or create new channel)
5. **Click "Add Incoming Webhooks integration"**
6. **Copy the NEW webhook URL** (will look like):
   ```
   https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
   ```

#### **Option B: Create Slack App (More Reliable)**
1. **Go to** https://api.slack.com/apps
2. **Click "Create New App"** → **From scratch**
3. **App Name**: "MyTaco AI Monitoring"
4. **Pick your workspace**
5. **Go to "Incoming Webhooks"** → Toggle **ON**
6. **Click "Add New Webhook to Workspace"**
7. **Select #mytaco-alerts channel**
8. **Copy the webhook URL**

### **Step 2: Update Railway Environment Variables**

1. **Go to Railway Dashboard** → Your backend service
2. **Click "Variables" tab**
3. **Update SLACK_WEBHOOK_URL** with the NEW webhook URL:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/NEW/WEBHOOK/URL
   ```
4. **Save changes** → Railway will redeploy automatically

### **Step 3: Test the New Webhook**

#### **Quick Test (Manual)**
```bash
# Replace with your NEW webhook URL
curl -X POST -H 'Content-type: application/json' \
--data '{"text":"🚀 Test message from MyTaco AI monitoring!"}' \
https://hooks.slack.com/services/YOUR/NEW/WEBHOOK/URL
```

**Expected**: You should see a test message in your Slack channel.

#### **Full Test (After Railway Redeploys)**
```bash
# In Railway console or CLI
cd backend
python test_production_monitoring.py
```

## 🔍 **Why This Happened**

### **Common Causes:**
1. **Webhook URL expired** - Slack webhooks can expire if not used
2. **App was removed** - Someone removed the Slack app/integration
3. **Workspace changes** - Slack workspace settings changed
4. **Copy/paste error** - URL was truncated or modified

### **Prevention:**
- Use Slack Apps instead of simple webhooks (more reliable)
- Test webhooks regularly
- Document webhook creation process for team

## 🚀 **Alternative Testing While Fixing**

### **Test Without Slack (Verify Monitoring Logic)**
You can test the monitoring system logic without Slack:

1. **Temporarily disable Slack** in Railway:
   ```
   # Remove or comment out SLACK_WEBHOOK_URL
   # SLACK_WEBHOOK_URL=
   ```

2. **Check Railway logs** for monitoring activity:
   - Go to Railway → Backend service → Logs tab
   - Look for monitoring middleware messages

3. **Test error detection** by triggering real errors:
   ```bash
   curl -X POST https://mytacoai.com/api/realtime/token \
     -H "Content-Type: application/json" \
     -d '{"language": "english", "level": "B1"}'
   ```

## 📋 **Step-by-Step Fix Checklist**

### **✅ Immediate Actions:**
1. [ ] Create new Slack webhook URL
2. [ ] Update Railway environment variable
3. [ ] Wait for Railway to redeploy (2-3 minutes)
4. [ ] Test new webhook with curl command
5. [ ] Run full monitoring test

### **✅ Verification:**
1. [ ] Webhook test message appears in Slack
2. [ ] All 6 monitoring tests pass
3. [ ] Colorful alerts appear in #mytaco-alerts
4. [ ] No more "invalid_token" errors

## 🎯 **Expected Result After Fix**

```bash
🚀 MyTaco AI Production Monitoring Test
============================================================

1️⃣ Testing CRITICAL OpenAI API Error...
[SLACK_NOTIFIER] ✅ Alert sent successfully
   Result: ✅ Sent

2️⃣ Testing HIGH Authentication Error...
[SLACK_NOTIFIER] ✅ Alert sent successfully
   Result: ✅ Sent

[... all 6 tests pass ...]

🎉 ALL TESTS PASSED!
```

## 🚨 **Need Help?**

If you're still having issues:

1. **Share the new webhook URL** you created
2. **Check Railway logs** for any other errors
3. **Try the manual curl test** first to isolate the issue
4. **Verify the Slack channel** exists and webhook has access

---

**The monitoring system logic is working perfectly - we just need to fix the Slack webhook URL! 🔧**
