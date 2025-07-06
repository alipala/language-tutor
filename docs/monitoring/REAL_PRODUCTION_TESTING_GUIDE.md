# 🚨 Real Production Incident Testing Guide

## 🎯 **Goal**: Test the monitoring system with actual production errors to verify Slack alerts work correctly.

---

## 📋 **Pre-Merge Testing Checklist**

### ✅ **Before Merging PR #82:**

1. **Verify PR is Ready**: https://github.com/alipala/language-tutor/pull/82
2. **Confirm Railway Environment Variables** are set:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/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
   PERFORMANCE_THRESHOLD=5.0
   ERROR_RATE_THRESHOLD=10.0
   ```
3. **Ensure Railway is deploying from** `feature/application-monitoring` branch

---

## 🧪 **Method 1: Railway Console Testing (Recommended)**

### **Step 1: Access Railway Console**
1. Go to **Railway Dashboard** → Your MyTaco AI project
2. Click on your **backend service**
3. Go to **Console** tab
4. Wait for console to load

### **Step 2: Run Production Test**
```bash
cd backend
python test_production_monitoring.py
```

### **Expected Result:**
- ✅ 6 test alerts sent to your `#mytaco-alerts` Slack channel
- 🚨 Red (Critical), ⚠️ Orange (High), ⚡ Yellow (Medium), ℹ️ Blue (Low) alerts
- Rich context with user info, endpoints, timestamps

---

## 🌐 **Method 2: External API Testing**

### **Test 1: Trigger 404 Error (Should NOT Alert)**
```bash
curl https://mytacoai.com/api/nonexistent-endpoint
```
**Expected**: No Slack alert (4xx errors filtered by design)

### **Test 2: OpenAI Token Without Auth (Should Alert)**
```bash
curl -X POST https://mytacoai.com/api/realtime/token \
  -H "Content-Type: application/json" \
  -d '{"language": "english", "level": "B1"}'
```
**Expected**: 🚨 CRITICAL or ⚠️ HIGH alert depending on response

### **Test 3: Protected Endpoint Without Auth (Should Alert)**
```bash
curl https://mytacoai.com/auth/me
```
**Expected**: ⚠️ HIGH alert for authentication error

### **Test 4: Invalid Session Summary (Should Alert)**
```bash
curl -X POST https://mytacoai.com/api/learning/session-summary \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
```
**Expected**: ⚠️ HIGH alert for server error

---

## 🔥 **Method 3: Simulate Real User Issues**

### **Test 1: Performance Issues**
1. Visit https://mytacoai.com
2. Go through the complete user flow:
   - Language selection
   - Level selection  
   - Topic selection
   - Try to start conversation
3. If any step takes >5 seconds, you'll get a ⚡ MEDIUM performance alert

### **Test 2: Authentication Flow**
1. Try to access protected pages without login
2. Try invalid login credentials
3. Access user dashboard without proper auth

### **Test 3: OpenAI Integration**
1. Try to generate conversation tokens
2. Attempt speaking assessments
3. Use sentence assessment features

---

## 📱 **What to Expect in Slack**

### **Alert Format:**
```
🚨 CRITICAL Alert from MyTaco AI

OpenAI_API_Error: OpenAI API rate limit exceeded

Endpoint: POST /api/realtime/token
User: customer@example.com
Environment: PRODUCTION
Time: 2025-07-06 18:33:00 UTC

Response Time: 2.34s
Is Critical Endpoint: true
Request Id: abc123-def456
```

### **Alert Colors & Meanings:**
- 🚨 **Red (Critical)**: OpenAI failures, Database issues
- ⚠️ **Orange (High)**: Auth errors, Payment issues, 5xx errors
- ⚡ **Yellow (Medium)**: Performance issues, Business logic errors
- ℹ️ **Blue (Low)**: Info alerts, Health checks

---

## 🎯 **Success Criteria**

### **✅ Monitoring is Working If:**
1. **Slack alerts appear** within 10-30 seconds of errors
2. **Correct color coding** based on severity
3. **Rich context** includes user info, endpoints, timestamps
4. **No spam** - duplicate errors don't flood the channel
5. **Performance alerts** trigger for slow responses (>5s)

### **❌ Issues to Investigate:**
1. **No alerts received** - Check webhook URL and Railway environment variables
2. **Wrong severity levels** - Verify error classification logic
3. **Missing context** - Check request middleware integration
4. **Too many alerts** - Adjust deduplication settings

---

## 🔧 **Troubleshooting**

### **No Alerts Received:**
1. **Check Slack webhook URL** in Railway environment variables
2. **Verify Railway deployment** is using the feature branch
3. **Test webhook manually**:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
   --data '{"text":"Test message"}' \
   https://hooks.slack.com/services/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
   ```

### **Wrong Alert Levels:**
1. **Check Railway logs** for error classification
2. **Verify error types** match expected patterns
3. **Review middleware logic** in monitoring system

### **Missing Context:**
1. **Verify user authentication** middleware is working
2. **Check request state** is being set properly
3. **Review middleware order** in main.py

---

## 📊 **Production Monitoring Expectations**

### **Normal Production (Healthy System):**
- **0-2 alerts per day**
- **Mostly performance alerts** during high traffic
- **Occasional business logic alerts** (normal)

### **Problem Indicators:**
- **>10 alerts per hour** (investigate immediately)
- **Multiple critical alerts** (system issues)
- **Repeated same errors** (needs fixing)

### **Real Scenarios You'll Be Alerted For:**
1. **Customer can't log in** → Authentication error alert
2. **OpenAI API is down** → Critical OpenAI error alert
3. **Database connection lost** → Critical database alert
4. **Site is slow** → Performance alert (>5s response)
5. **Payment processing fails** → High priority Stripe alert
6. **Session summaries fail** → Medium business logic alert

---

## 🚀 **After Testing: Merge to Production**

### **When All Tests Pass:**
1. **Merge PR #82** to main branch
2. **Switch Railway** back to main branch deployment
3. **Monitor production** for 24 hours
4. **Adjust thresholds** if needed based on real traffic

### **Environment Variables for Production:**
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/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
PERFORMANCE_THRESHOLD=5.0  # Adjust based on real performance
ERROR_RATE_THRESHOLD=10.0   # Adjust based on error patterns
ENVIRONMENT=production
```

---

## 🎉 **Final Result**

**After successful testing and merging, you'll have:**

✅ **Real-time visibility** into customer issues  
✅ **Immediate alerts** when problems occur  
✅ **Rich context** for faster debugging  
✅ **Performance insights** for optimization  
✅ **Business logic monitoring** for critical operations  
✅ **Zero alert fatigue** with smart deduplication  

**Your MyTaco AI application will now have enterprise-grade monitoring! 🛡️**

---

**Ready to test? Start with Method 1 (Railway Console) for the most reliable results! 🚀**
