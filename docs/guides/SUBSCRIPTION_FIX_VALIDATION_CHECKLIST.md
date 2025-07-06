# 🔧 Subscription Trial-to-Monthly Transition Fix - Validation Checklist

## 📋 **PRE-DEPLOYMENT CHECKLIST**

### ✅ **1. Dependencies Deployment**
- [ ] Verify `python-dateutil==2.8.2` is installed in Railway environment
- [ ] Check Railway deployment logs for successful dependency installation
- [ ] Test import: `python -c "from dateutil.relativedelta import relativedelta; print('OK')"`

### ✅ **2. Stripe Webhook Configuration**
- [ ] **CRITICAL:** Add `customer.subscription.trial_will_end` to Stripe webhook endpoint
- [ ] Go to: [Stripe Dashboard > Webhooks](https://dashboard.stripe.com/webhooks)
- [ ] Edit your webhook endpoint
- [ ] Add event: `customer.subscription.trial_will_end`
- [ ] Save configuration
- [ ] Verify webhook endpoint URL matches your Railway deployment

### ✅ **3. Environment Variables**
- [ ] Verify `STRIPE_SECRET_KEY` is set in Railway
- [ ] Verify `STRIPE_WEBHOOK_SECRET` is set in Railway
- [ ] Verify `MONGODB_URL` is accessible from Railway

---

## 🧪 **TESTING PLAN**

### **Phase 1: Basic Functionality Testing**

#### Test 1: Webhook Endpoint Verification
```bash
# Test webhook endpoint is accessible
curl -X POST https://your-railway-app.railway.app/api/stripe/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "ping"}'
```
- [ ] Returns 400 (missing signature) - this is expected
- [ ] Does not return 404 or 500

#### Test 2: Database Connection
```bash
# Run the fix script to verify MongoDB connection
python fix_george_subscription.py
```
- [ ] Script connects to MongoDB successfully
- [ ] Shows George's current subscription data
- [ ] No connection errors

### **Phase 2: Webhook Event Testing**

#### Test 3: Simulate trial_will_end Webhook
Use Stripe CLI to simulate the webhook:
```bash
stripe trigger customer.subscription.trial_will_end
```
- [ ] Webhook fires successfully
- [ ] Check Railway logs for `[TRIAL_WILL_END]` messages
- [ ] Verify no errors in webhook processing
- [ ] Check user data is updated correctly

#### Test 4: Simulate subscription.updated Webhook
```bash
stripe trigger customer.subscription.updated
```
- [ ] Webhook fires successfully
- [ ] Check Railway logs for `[SUB_UPDATED]` messages
- [ ] Verify trial-to-active transition logic works

### **Phase 3: Edge Case Testing**

#### Test 5: Trial Cancellation
- [ ] Create test subscription with trial
- [ ] Cancel before trial ends
- [ ] Verify status updates to "canceled"
- [ ] No errors in webhook processing

#### Test 6: Payment Failure at Trial End
- [ ] Create test subscription with invalid payment method
- [ ] Let trial expire
- [ ] Verify status updates to "past_due"
- [ ] Check error handling

#### Test 7: Webhook Retry/Idempotency
- [ ] Send same webhook event multiple times
- [ ] Verify no duplicate processing
- [ ] Database remains consistent

---

## 📊 **MONITORING & ALERTING**

### **Phase 4: Monitoring Setup**

#### Monitor 1: Webhook Processing Logs
```bash
# Check Railway logs for webhook events
railway logs --filter="TRIAL_WILL_END|SUB_UPDATED"
```
- [ ] All webhook events are logged
- [ ] No error messages in logs
- [ ] Processing times are reasonable

#### Monitor 2: Database Consistency Check
```python
# Run this query to check for inconsistent subscriptions
db.users.find({
  "subscription_status": "trialing",
  "subscription_expires_at": {"$lt": new Date()}
})
```
- [ ] No users with expired trials still marked as "trialing"
- [ ] All active subscriptions have future expiry dates

#### Monitor 3: Error Rate Monitoring
- [ ] Set up Railway log monitoring for webhook errors
- [ ] Monitor for failed database updates
- [ ] Track webhook processing success rate

---

## 🎯 **VALIDATION SCENARIOS**

### **Scenario 1: George's Subscription (Real User)**
**User ID:** `6867a7e6e6c0452d1a92a35f`
**Trial Ends:** July 11, 2025

**Expected Behavior:**
- [ ] 3 days before (July 8): `trial_will_end` webhook fires
- [ ] July 11: Status changes from "trialing" to "active"
- [ ] Expiry date updates to August 11, 2025
- [ ] Usage counters reset to 0

**Validation Steps:**
1. [ ] Monitor George's account on July 8-11
2. [ ] Check webhook logs for his subscription
3. [ ] Verify database updates are correct
4. [ ] Confirm he can access paid features after trial

### **Scenario 2: New Trial User**
**Create test subscription with 7-day trial**

**Expected Behavior:**
- [ ] Trial starts correctly
- [ ] `trial_will_end` webhook fires 3 days before end
- [ ] Automatic transition to monthly billing
- [ ] Correct expiry date calculation

---

## 🚨 **ROLLBACK PLAN**

### If Issues Are Found:
1. [ ] **Immediate:** Disable webhook in Stripe dashboard
2. [ ] **Quick Fix:** Revert to previous Railway deployment
3. [ ] **Manual Fix:** Use `fix_george_subscription.py` for affected users
4. [ ] **Investigation:** Check logs and identify root cause

### Rollback Commands:
```bash
# Revert Railway deployment
railway rollback

# Disable webhook processing (emergency)
# Comment out the webhook handler in stripe_routes.py
```

---

## ✅ **SIGN-OFF CHECKLIST**

### Before Merging to Main:
- [ ] All webhook events tested successfully
- [ ] No errors in Railway logs for 24 hours
- [ ] George's subscription transitions correctly (if trial ends)
- [ ] Database consistency verified
- [ ] Monitoring and alerting confirmed working
- [ ] Edge cases handled properly
- [ ] Rollback plan tested

### Final Approval:
- [ ] **Developer:** Code review completed
- [ ] **QA:** All test scenarios passed
- [ ] **DevOps:** Monitoring and alerts configured
- [ ] **Product:** Business logic validated

---

## 📞 **EMERGENCY CONTACTS**

If critical issues arise:
1. **Disable webhook immediately** in Stripe dashboard
2. **Check Railway logs** for error details
3. **Run manual fix script** for affected users
4. **Contact team** for immediate support

---

## 📝 **NOTES**

- Keep this checklist updated as you complete each item
- Document any issues found and their resolutions
- Save all test results for future reference
- Monitor the system for at least 48 hours after deployment
