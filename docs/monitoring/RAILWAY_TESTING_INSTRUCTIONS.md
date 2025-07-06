# 🚀 How to Test Monitoring in Railway (Web Console & CLI)

## 🌐 **Method 1: Railway Web Console (Easiest)**

### **Step-by-Step Instructions:**

1. **Go to Railway Dashboard**
   - Visit: https://railway.app/dashboard
   - Find your MyTaco AI project
   - Click on your **backend service**

2. **Access the Console**
   - Click on the **"Console"** tab (next to Deployments, Logs, etc.)
   - Wait for the console to load (may take 10-15 seconds)

3. **Navigate to Backend Directory**
   ```bash
   cd backend
   ```

4. **Run the Test Script**
   ```bash
   python test_production_monitoring.py
   ```

5. **Expected Output:**
   ```
   🚀 MyTaco AI Production Monitoring Test
   ============================================================
   Test started at: 2025-07-06T18:39:00.000000

   ⚙️ Monitoring Configuration:
     Slack webhook configured: True
     Environment: production
     Performance threshold: 5.0s

   🧪 Testing different alert scenarios...

   1️⃣ Testing CRITICAL OpenAI API Error...
      Result: ✅ Sent
   2️⃣ Testing HIGH Authentication Error...
      Result: ✅ Sent
   [... and so on for 6 tests]

   🎉 ALL TESTS PASSED!
   ```

6. **Check Your Slack Channel**
   - Go to your `#mytaco-alerts` Slack channel
   - You should see 6 colorful test alerts within 30 seconds

---

## 💻 **Method 2: Railway CLI (Advanced)**

### **Prerequisites:**
- Install Railway CLI: `npm install -g @railway/cli`
- Login: `railway login`

### **Steps:**

1. **Connect to Your Project**
   ```bash
   railway link
   # Select your MyTaco AI project
   ```

2. **Open Railway Shell**
   ```bash
   railway shell
   ```

3. **Navigate and Run Test**
   ```bash
   cd backend
   python test_production_monitoring.py
   ```

---

## 🔧 **Troubleshooting Railway Console**

### **If Console Won't Load:**
1. **Refresh the page** and try again
2. **Try a different browser** (Chrome/Firefox work best)
3. **Clear browser cache** and reload
4. **Wait longer** - Railway console can be slow to initialize

### **If Commands Don't Work:**
1. **Check you're in the right service** (backend, not frontend)
2. **Verify deployment is complete** (check Deployments tab)
3. **Try typing commands slowly** - Railway console can be laggy
4. **Use Railway CLI** as backup method

### **If Python Script Fails:**
1. **Check environment variables** are set in Railway:
   ```
   SLACK_WEBHOOK_URL=your_webhook_url
   PERFORMANCE_THRESHOLD=5.0
   ERROR_RATE_THRESHOLD=10.0
   ```

2. **Verify Railway deployed from main branch** (not feature branch)

3. **Check Railway logs** for any deployment errors

---

## 📱 **Alternative Testing Methods**

### **Method 3: External API Calls (No Railway Access Needed)**

You can test from your local machine or any computer:

```bash
# Test 1: Trigger OpenAI error (should alert)
curl -X POST https://mytacoai.com/api/realtime/token \
  -H "Content-Type: application/json" \
  -d '{"language": "english", "level": "B1"}'

# Test 2: Trigger auth error (should alert)
curl https://mytacoai.com/auth/me

# Test 3: Trigger 404 (should NOT alert - by design)
curl https://mytacoai.com/api/nonexistent-endpoint
```

### **Method 4: Browser Testing**

1. **Visit your production site**: https://mytacoai.com
2. **Try to use features without logging in**
3. **Go through the user flow** (language selection, etc.)
4. **Any errors or slow responses** will trigger alerts

---

## 🎯 **What to Expect in Slack**

### **Successful Test Results:**
- **6 different alerts** with different colors
- **Rich context** including user info, endpoints, timestamps
- **No duplicate alerts** (deduplication working)

### **Alert Examples:**
```
🚨 CRITICAL Alert from MyTaco AI
OpenAI_API_Error: OpenAI API rate limit exceeded
Endpoint: POST /api/realtime/token
Environment: PRODUCTION
Time: 2025-07-06 18:39:00 UTC
```

```
⚠️ HIGH Alert from MyTaco AI
Authentication_Error: Authentication failed
Endpoint: POST /auth/login
Environment: PRODUCTION
Time: 2025-07-06 18:39:05 UTC
```

---

## 🚨 **If Railway Console Doesn't Work**

### **Quick Alternative - Use Method 3:**

Run these commands from your local terminal or any computer:

```bash
# This will trigger real production errors and test your monitoring
curl -X POST https://mytacoai.com/api/realtime/token \
  -H "Content-Type: application/json" \
  -d '{"language": "english", "level": "B1"}'
```

**Expected**: You should get a Slack alert within 30 seconds if the monitoring is working.

---

## 📊 **Success Criteria**

### **✅ Monitoring is Working If:**
1. **Slack alerts appear** within 10-30 seconds
2. **Correct color coding** (red, orange, yellow, blue)
3. **Rich context** in alerts (user info, endpoints)
4. **No spam** - duplicate errors don't flood channel

### **❌ Need to Investigate If:**
1. **No alerts received** - Check webhook URL and environment variables
2. **Wrong colors** - Check error classification
3. **Missing context** - Check middleware integration
4. **Too many alerts** - Adjust deduplication settings

---

## 🎉 **Ready to Test!**

**Start with Railway Web Console (Method 1) - it's the most reliable way to test your production monitoring system!**

**Your monitoring system is live and ready to protect your customers! 🛡️**
