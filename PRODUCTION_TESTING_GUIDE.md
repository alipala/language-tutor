# 🚀 Production Monitoring Testing Guide

## ✅ Local Testing Complete!
Your monitoring system is working perfectly locally. Now let's test it in production on Railway.

## 🧪 Production Testing Methods

### Method 1: Trigger Real Errors (Recommended)

#### Test 1: 404 Error (Should NOT alert - by design)
```bash
curl https://your-app.railway.app/api/nonexistent-endpoint
```

#### Test 2: OpenAI Token Error (Should alert - CRITICAL)
```bash
# Try to get OpenAI token without proper authentication
curl -X POST https://your-app.railway.app/api/realtime/token \
  -H "Content-Type: application/json" \
  -d '{"language": "english", "level": "B1"}'
```

#### Test 3: Authentication Error (Should alert - HIGH)
```bash
# Try to access protected endpoint without auth
curl https://your-app.railway.app/auth/me
```

### Method 2: Performance Testing
Visit your production site and use it normally:
- Go through the language selection flow
- Try the speaking assessment
- Use the conversation features

If any endpoint takes >5 seconds, you'll get a performance alert.

### Method 3: Railway Console Testing
1. Go to Railway Dashboard → Your backend service → Console
2. Run the production test:
```bash
cd backend
python test_production_monitoring.py
```

## 📱 What to Expect in Slack

### Alert Format Example:
```
🚨 CRITICAL Alert from MyTaco AI

OpenAI_API_Error: OpenAI API rate limit exceeded

Endpoint: POST /api/realtime/token
User: customer@example.com
Environment: PRODUCTION
Time: 2025-07-06 18:25:00 UTC

Api Endpoint: realtime/sessions
Rate Limit: exceeded
Retry After: 60 seconds
```

### Alert Colors:
- 🚨 **Red**: Critical errors (OpenAI, Database)
- ⚠️ **Orange**: High priority (Auth, Payments, Health)
- ⚡ **Yellow**: Medium priority (Performance, Business logic)
- ℹ️ **Blue**: Low priority (Info, Tests)

## 🔍 Monitoring What's Working

### ✅ Currently Monitored:
- **All 5xx server errors**
- **OpenAI API failures** (Critical)
- **Database connection issues** (Critical)
- **Authentication failures** (High)
- **Payment processing errors** (High)
- **Performance issues** (>5s response time)
- **Business logic failures** (Session summaries, learning plans)

### ❌ NOT Monitored (by design):
- 4xx client errors (unless suspicious patterns)
- Health check endpoints (to avoid spam)
- Static file requests
- Development environment noise

## 🚨 Real Production Scenarios

### When You'll Get Alerts:

1. **Customer can't log in** → Authentication error alert
2. **OpenAI API is down** → Critical OpenAI error alert
3. **Database connection lost** → Critical database alert
4. **Site is slow** → Performance alert (>5s response)
5. **Payment processing fails** → High priority Stripe alert
6. **Session summaries fail** → Medium business logic alert

## 📊 Alert Volume Expectations

### Normal Production:
- **0-2 alerts per day** (healthy system)
- **Mostly performance alerts** during high traffic
- **Occasional business logic alerts** (normal)

### Problem Indicators:
- **>10 alerts per hour** (investigate immediately)
- **Multiple critical alerts** (system issues)
- **Repeated same errors** (needs fixing)

## 🔧 Adjusting Thresholds

If you get too many/few alerts, adjust in Railway:

```bash
# Make performance alerts less sensitive (10s instead of 5s)
PERFORMANCE_THRESHOLD=10.0

# Make performance alerts more sensitive (3s instead of 5s)
PERFORMANCE_THRESHOLD=3.0
```

## 🎯 Success Criteria

After production testing, you should have:
- ✅ Received test alerts in Slack
- ✅ Verified alert formatting and colors
- ✅ Confirmed real errors trigger alerts
- ✅ Validated performance monitoring works
- ✅ No spam or false positives

## 📞 Next Steps

1. **Test in production** using methods above
2. **Monitor alert volume** for first 24 hours
3. **Adjust thresholds** if needed
4. **Document incident response** procedures
5. **Train team** on alert meanings

---

**Your monitoring system is now production-ready! 🚀**
