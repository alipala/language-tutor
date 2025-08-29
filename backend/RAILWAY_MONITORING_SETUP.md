# Railway Monitoring Setup Guide

## 🚂 Why Railway Doesn't Support Traditional Cron Jobs

Railway is a **Platform-as-a-Service (PaaS)** that runs containerized applications, not traditional servers. Unlike VPS or dedicated servers, Railway containers:

- Are **stateless** and can be restarted/moved at any time
- Don't have persistent **cron daemon** processes
- Are designed for **web applications**, not background services
- **Scale automatically** based on traffic, not scheduled tasks

## 🛡️ Duration Monitoring Solutions for Railway

We've created **3 flexible options** for running daily monitoring:

### **Option 1: HTTP Endpoint (Recommended)**
✅ **Best for Railway** - Works with any external cron service

**Setup:**
1. The monitoring endpoint is already deployed: `backend/monitoring_endpoint.py`
2. Add environment variable: `MONITORING_TOKEN=your-secure-token`
3. Use external cron service to call your Railway app daily

**External Cron Services (Free):**
- **cron-job.org** (recommended)
- **EasyCron.com**
- **cron-job.de**

**Example Setup on cron-job.org:**
```bash
URL: https://mytacoai.com/health-check
Method: POST
Headers: Authorization: Bearer your-secure-token
Schedule: 0 2 * * * (daily at 2 AM)
```

### **Option 2: GitHub Actions (Automated)**
✅ **Fully automated** - No external services needed

The GitHub workflow is already created: `.github/workflows/duration-monitoring.yml`

**Setup:**
1. Add GitHub repository secrets:
   - `RAILWAY_API_TOKEN`
   - `RAILWAY_PROJECT_ID` 
   - `RAILWAY_SERVICE_ID`
2. The workflow runs automatically daily at 2 AM UTC

### **Option 3: Manual Execution**
✅ **For testing** and immediate checks

**Run directly on Railway:**
```bash
python3 backend/scheduled_monitoring.py
```

**Or via HTTP endpoint:**
```bash
curl -X POST https://mytacoai.com/health-check \
  -H "Authorization: Bearer your-token"
```

## 🔧 Recommended Setup Steps

### **Step 1: Choose Your Monitoring Method**
We recommend **Option 1 (HTTP Endpoint)** for simplicity and reliability.

### **Step 2: Set Environment Variables**
Add to your Railway environment:
```bash
MONITORING_TOKEN=your-very-secure-random-token-here
```

### **Step 3: Set Up External Cron (Option 1)**
1. Go to **cron-job.org** (free account)
2. Create new cron job:
   - **URL:** `https://mytacoai.com/health-check`
   - **Method:** POST
   - **Headers:** `Authorization: Bearer your-very-secure-random-token-here`
   - **Schedule:** `0 2 * * *` (daily at 2 AM)
   - **Timezone:** UTC

### **Step 4: Test the Setup**
```bash
# Test the monitoring endpoint
curl -X POST https://mytacoai.com/health-check \
  -H "Authorization: Bearer your-token"

# Check monitoring status
curl https://mytacoai.com/monitoring-status
```

## 📊 What the Monitoring Does

**Daily Health Check:**
- ✅ Scans all users for data anomalies
- ✅ Detects suspicious duration changes
- ✅ Validates data integrity
- ✅ Sends Slack alerts for critical issues
- ✅ Generates usage statistics
- ✅ Creates audit trails

**Slack Alerts:**
- 🚨 **Critical:** Data corruption detected
- ⚠️ **Warning:** Suspicious patterns found
- ✅ **Success:** All systems healthy

## 🎯 Benefits Over Traditional Cron

**Railway-Native Approach:**
- ✅ **Scalable** - Works with Railway's auto-scaling
- ✅ **Reliable** - External services ensure execution
- ✅ **Monitored** - HTTP responses confirm execution
- ✅ **Flexible** - Can be triggered manually anytime
- ✅ **Logged** - All execution is logged and tracked

**Traditional Cron Problems:**
- ❌ Container restarts kill cron processes
- ❌ No execution confirmation
- ❌ Difficult to debug failures
- ❌ Not compatible with PaaS architecture

## 🔍 Monitoring the Monitoring

**Check if monitoring is working:**
1. **Slack notifications** - You'll get daily alerts if issues are found
2. **HTTP endpoint status** - `GET /monitoring-status` shows system health
3. **Database logs** - Check `duration_health_reports` collection
4. **Railway logs** - Monitor application logs for execution

**Troubleshooting:**
- If no Slack alerts for several days → Check external cron service
- If HTTP endpoint fails → Check Railway deployment and logs
- If monitoring reports errors → Check database connectivity

This approach gives you **enterprise-grade monitoring** that's fully compatible with Railway's modern PaaS architecture! 🚀
