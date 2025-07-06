# 🔧 Stripe Configuration Guide

## 📋 **Overview**

This guide provides comprehensive documentation for configuring Stripe in live mode for the Language Tutor application, including webhook setup, product configuration, and verification procedures.

## 🎯 **Configuration Requirements**

### **1. Stripe Account Setup**
- ✅ Stripe account activated for live mode
- ✅ Business verification completed
- ✅ Bank account connected for payouts
- ✅ Tax settings configured

### **2. API Keys Configuration**
```bash
# Live Mode Keys (set in Railway environment)
STRIPE_PUBLISHABLE_KEY=pk_live_51Mzx41JcquSiYwWN...
STRIPE_SECRET_KEY=sk_live_51Mzx41JcquSiYwWN...
STRIPE_WEBHOOK_SECRET=whsec_... (from webhook endpoint)
```

### **3. Products & Pricing Structure**

#### **Team Mastery Plan** (`prod_SZ5xUhxcUSrOIo`)
- **Description**: AI language learning for teams
- **Monthly**: €39.99/month (`price_1RdxlGJcquSiYwWNWvyEgmgL`)
- **Yearly**: €399.99/year (`price_1RdxmRJcquSiYwWN7Oc6NnNe`)
- **Statement Descriptor**: MYTACO-TEAM
- **Tax Code**: txcd_10202003

#### **Fluency Builder Plan** (`prod_SZ5YV4PDK1EJvC`)
- **Description**: AI language learning for serious learners
- **Monthly**: €19.99/month (`price_1RdxNjJcquSiYwWN2XQMwwYW`)
- **Yearly**: €199.99/year (`price_1RdxNjJcquSiYwWNIpmYrKSE`)
- **Statement Descriptor**: MYTACO-FLUENCY
- **Tax Code**: txcd_10202003

## 🔔 **Webhook Configuration**

### **Primary Webhook Endpoint**
- **URL**: `https://mytacoai.com/api/stripe/webhook`
- **Status**: Enabled
- **Mode**: Live
- **Events**: 225+ configured

### **Critical Events for Subscription Management**

#### **Core Subscription Events**
```
customer.subscription.created
customer.subscription.updated
customer.subscription.deleted
customer.subscription.trial_will_end  ⭐ CRITICAL FOR TRIAL FIX
```

#### **Payment & Checkout Events**
```
checkout.session.completed
invoice.payment_succeeded
invoice.payment_failed
payment_intent.succeeded
```

#### **Customer Management Events**
```
customer.created
customer.updated
customer.deleted
```

### **Trial-to-Monthly Transition Events**
The following webhook events are essential for proper trial-to-monthly subscription transitions:

1. **`customer.subscription.trial_will_end`** 
   - Fires 3 days before trial ends
   - Prepares system for transition
   - Calculates correct monthly expiry date

2. **`customer.subscription.updated`**
   - Handles status change from "trialing" to "active"
   - Updates expiry dates and usage counters
   - Manages billing period transitions

## 🧪 **Verification Procedures**

### **1. API Keys Verification**
```bash
# Test secret key
stripe balance retrieve --live

# Verify publishable key format
echo $STRIPE_PUBLISHABLE_KEY | grep "pk_live_"
```

### **2. Products Verification**
```bash
# List all active products
stripe products list --live --active=true

# Verify specific products
stripe products retrieve prod_SZ5xUhxcUSrOIo --live
stripe products retrieve prod_SZ5YV4PDK1EJvC --live
```

### **3. Pricing Verification**
```bash
# Team Mastery Plan prices
stripe prices list --live --product=prod_SZ5xUhxcUSrOIo

# Fluency Builder Plan prices
stripe prices list --live --product=prod_SZ5YV4PDK1EJvC
```

### **4. Webhook Verification**
```bash
# List webhook endpoints
stripe webhook_endpoints list --live

# Check specific webhook events
stripe webhook_endpoints retrieve we_1RhppyJcquSiYwWNqrm0MDdd --live
```

### **5. Endpoint Testing**
```bash
# Test webhook endpoint accessibility
curl -X POST https://mytacoai.com/api/stripe/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "verification"}'
# Expected: 400 (missing signature)
```

## 🔍 **Automated Verification Scripts**

### **1. Live Configuration Verification**
```bash
python verify_live_stripe_configuration.py
```
**Purpose**: Comprehensive verification of all Stripe live mode settings
**Checks**: API keys, products, prices, webhooks, endpoint accessibility

### **2. Webhook Configuration Testing**
```bash
python test_webhook_configuration.py
```
**Purpose**: Test webhook endpoint and configuration
**Checks**: Endpoint accessibility, event configuration, date calculations

### **3. Subscription Fix Validation**
```bash
python fix_george_subscription.py
```
**Purpose**: Manual fix script for subscription issues
**Use Case**: Fix existing users with trial-to-monthly transition problems

## 📊 **Configuration Checklist**

### **Pre-Production Checklist**
- [ ] Stripe account verified and activated
- [ ] Live mode API keys generated and secured
- [ ] Products created with correct pricing
- [ ] Webhook endpoint configured with all required events
- [ ] `customer.subscription.trial_will_end` event enabled ⭐
- [ ] Environment variables set in Railway
- [ ] Webhook secret configured
- [ ] Endpoint accessibility verified

### **Post-Deployment Verification**
- [ ] API keys working in production
- [ ] Webhook events firing correctly
- [ ] Subscription creation working
- [ ] Trial-to-monthly transitions functioning
- [ ] Payment processing successful
- [ ] Error monitoring active

## 🚨 **Critical Configuration Notes**

### **Trial-to-Monthly Transition Fix**
The `customer.subscription.trial_will_end` webhook event is **CRITICAL** for proper subscription management:

- **Without this event**: Users remain in "trialing" status after trial ends
- **With this event**: Automatic transition to "active" status with correct expiry dates
- **Implementation**: Added in subscription fix (PR #81)

### **Environment Variables Security**
```bash
# Production Environment (Railway)
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Never commit these keys to version control!
```

### **Webhook Endpoint Security**
- Webhook signature verification enabled
- HTTPS endpoint required
- Proper error handling implemented
- Idempotency protection in place

## 🔄 **Monitoring & Maintenance**

### **Regular Checks**
1. **Weekly**: Verify webhook events are processing
2. **Monthly**: Check subscription transition success rates
3. **Quarterly**: Review pricing and product configurations

### **Error Monitoring**
- Monitor Railway logs for webhook processing errors
- Track failed subscription transitions
- Alert on webhook endpoint downtime

### **Performance Metrics**
- Webhook processing time
- Subscription conversion rates
- Payment success rates
- Trial-to-paid conversion rates

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **Webhook Not Firing**
1. Check webhook endpoint status in Stripe Dashboard
2. Verify endpoint URL is accessible
3. Check webhook secret configuration
4. Review event selection

#### **Trial Transition Issues**
1. Verify `customer.subscription.trial_will_end` event is enabled
2. Check webhook processing logs
3. Run manual fix script if needed
4. Monitor subscription status changes

#### **Payment Failures**
1. Check API key configuration
2. Verify webhook events for payment failures
3. Review customer payment methods
4. Check Stripe Dashboard for declined payments

## 📞 **Support & Resources**

### **Documentation**
- [Stripe API Documentation](https://stripe.com/docs/api)
- [Webhook Events Reference](https://stripe.com/docs/api/events/types)
- [Subscription Lifecycle](https://stripe.com/docs/billing/subscriptions/lifecycle)

### **Tools**
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [Stripe Dashboard](https://dashboard.stripe.com/)
- [Webhook Testing](https://stripe.com/docs/webhooks/test)

### **Emergency Contacts**
- Disable webhook in Stripe Dashboard for immediate issues
- Use manual fix scripts for affected users
- Monitor Railway logs for error details

---

## 📝 **Change Log**

### **2025-07-06**
- ✅ Added `customer.subscription.trial_will_end` webhook event
- ✅ Implemented trial-to-monthly transition fix
- ✅ Created comprehensive verification scripts
- ✅ Documented live mode configuration
- ✅ Verified all webhook events and products

### **Configuration Status**: 🟢 **PRODUCTION READY**

All Stripe configurations have been verified and are ready for production deployment.
