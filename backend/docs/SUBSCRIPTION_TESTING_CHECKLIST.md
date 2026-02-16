# Subscription System Testing Checklist

## Code Review Summary - Bugs Found & Fixed

### Bug #1: Apple IAP Routes - Incomplete `$unset` Data
**Location:** `routes/apple_iap_routes.py:162-170`
**Issue:** Wrong Google Play field names and missing fields in `$unset`
- ❌ Used `google_purchase_token` instead of `google_play_purchase_token`
- ❌ Used `google_order_id` instead of `google_play_order_id`
- ❌ Missing `google_play_is_trial`
- ❌ Missing `google_play_auto_renewing`

**Fix Applied:** Updated `unset_data` with correct field names and added missing fields

### Bug #2: Google Play Routes - Missing Apple Fields
**Location:** `routes/google_play_routes.py:162-170`
**Issue:** Missing Apple-specific fields in `$unset`
- ❌ Missing `apple_original_transaction_id`
- ❌ Missing `apple_is_trial`

**Fix Applied:** Added missing Apple fields to `unset_data`

### Bug #3: Stripe Webhook - Incomplete `$unset` Data
**Location:** `stripe_routes.py:1224-1236`
**Issue:** Same issues as Bug #1 - wrong Google Play field names and missing fields

**Fix Applied:** Updated `unset_data` with complete correct field list

### Bug #4: Stripe Webhook - Usage Not Reset on First Subscription
**Location:** `stripe_routes.py:1203-1211`
**Issue:** Stripe only reset usage on renewal (`if is_renewal`), not first subscription
- Apple/Google always reset usage on new subscription
- Inconsistent behavior across providers
- User subscribing via Stripe web wouldn't get fresh usage allocation

**Fix Applied:** Changed condition to `if is_renewal or old_period_end is None` to reset on both renewal AND first subscription

### Bug #5: Stripe Webhook - Wrong Field Name (CRITICAL)
**Location:** `stripe_routes.py:1196`
**Issue:** Used `subscription_id` instead of `stripe_subscription_id`
- Inconsistent with Apple (`apple_transaction_id`) and Google Play (`google_play_purchase_token`)
- Not following standardized naming convention (provider prefix)

**Fix Applied:**
- Changed line 1196: `"subscription_id"` → `"stripe_subscription_id"`
- Added `"subscription_id": 1` to `unset_data` to remove old field name

**Discovered:** During first production test (2026-02-16)

### Bug #6: Timezone-Naive vs Timezone-Aware Datetime Comparison (CRITICAL)
**Location:** `stripe_routes.py:1189`
**Issue:** Comparing timezone-naive datetime from MongoDB with timezone-aware datetime from Stripe
```python
old_period_end = user.get("current_period_end")  # MongoDB - might be naive
new_period_start = datetime.fromtimestamp(..., tz=timezone.utc)  # Aware

if old_period_end and new_period_start > old_period_end:  # ❌ CRASHES!
    # Error: "can't compare offset-naive and offset-aware datetimes"
```

**Fix Applied:**
```python
# Make old_period_end timezone-aware before comparison
if old_period_end and old_period_end.tzinfo is None:
    old_period_end = old_period_end.replace(tzinfo=timezone.utc)
```

**Impact:**
- `invoice.payment_succeeded` webhook crashed
- Bug fixes #1-5 never applied to production subscriptions
- Fallback webhook (`customer.subscription.created`) used old logic without fixes

**Discovered:** During first production test (2026-02-16) - error in Railway logs

---

## Testing Checklist

### Phase 1: Database Cleanup (Already Completed)
- [x] MongoDB: Reset 1 user's subscription data to standardized format
- [x] Stripe: Deleted 200 orphaned test customers
- [x] All fields now use top-level format (no nested `subscription` object)

### Phase 2: Backend API Testing

#### 2.1 Apple IAP Verification
**Endpoint:** `POST /api/apple-iap/verify-receipt`

**Test Cases:**
- [ ] **T1.1** Valid receipt verification
  - Send valid Apple receipt + product_id
  - Verify subscription created with correct fields
  - Check all Google Play fields removed via `$unset`
  - Verify usage counters reset to 0

- [ ] **T1.2** Provider conflict protection
  - Create user with active Stripe subscription
  - Attempt Apple IAP verification
  - Expect HTTP 409 error with message about active Stripe subscription

- [ ] **T1.3** Provider switch from Google Play
  - Create user with Google Play subscription
  - Verify Apple receipt
  - Check all Google Play fields removed
  - Verify Apple fields set correctly

- [ ] **T1.4** Invalid receipt handling
  - Send invalid receipt data
  - Expect HTTP 400 error

- [ ] **T1.5** Invalid product ID
  - Send valid receipt with invalid product_id
  - Expect HTTP 400 error

**Expected Database State After T1.1:**
```json
{
  "subscription_plan": "fluency_builder",
  "subscription_status": "active",
  "subscription_period": "monthly",
  "subscription_provider": "apple",
  "subscription_expires_at": "<future_date>",
  "apple_product_id": "com.bigdavinci.mytaco.fluency_builder_monthly",
  "apple_transaction_id": "...",
  "apple_original_transaction_id": "...",
  "apple_is_trial": false,
  "current_period_start": "<now>",
  "current_period_end": "<future_date>",
  "practice_minutes_used": 0.0,
  "practice_sessions_used": 0,
  "assessments_used": 0,
  // All Google Play fields should be absent
  // All Stripe fields should be absent
  // No nested "subscription" object
}
```

#### 2.2 Google Play Verification
**Endpoint:** `POST /api/google-play/verify-purchase`

**Test Cases:**
- [ ] **T2.1** Valid purchase verification
  - Send valid purchase token + product_id
  - Verify subscription created with correct fields
  - Check all Apple fields removed via `$unset`
  - Verify usage counters reset to 0

- [ ] **T2.2** Provider conflict protection
  - Create user with active Stripe subscription
  - Attempt Google Play verification
  - Expect HTTP 409 error

- [ ] **T2.3** Provider switch from Apple
  - Create user with Apple subscription
  - Verify Google Play purchase
  - Check all Apple fields removed (including `apple_original_transaction_id`, `apple_is_trial`)
  - Verify Google Play fields set correctly

- [ ] **T2.4** Invalid purchase token
  - Send invalid purchase token
  - Expect HTTP 400 error

**Expected Database State After T2.1:**
```json
{
  "subscription_plan": "fluency_builder",
  "subscription_status": "active",
  "subscription_period": "monthly",
  "subscription_provider": "google_play",
  "subscription_expires_at": "<future_date>",
  "google_play_product_id": "fluency_builder_monthly",
  "google_play_purchase_token": "...",
  "google_play_order_id": "...",
  "google_play_is_trial": false,
  "google_play_auto_renewing": true,
  "current_period_start": "<now>",
  "current_period_end": "<future_date>",
  "practice_minutes_used": 0.0,
  "practice_sessions_used": 0,
  "assessments_used": 0,
  // All Apple fields should be absent
  // All Stripe fields should be absent
}
```

#### 2.3 Stripe Webhook Testing
**Endpoint:** `POST /stripe-webhook`

**Test Cases:**
- [ ] **T3.1** First subscription (invoice.payment_succeeded)
  - Create Stripe customer + subscription
  - Send webhook for first invoice payment
  - Verify usage counters reset to 0 (Bug #4 fix)
  - Check all Apple/Google fields removed

- [ ] **T3.2** Subscription renewal
  - Create user with existing Stripe subscription (set usage to 50 minutes)
  - Send webhook for renewal invoice with new `current_period_start`
  - Verify usage counters reset to 0
  - Verify period dates updated

- [ ] **T3.3** Subscription update (no renewal)
  - Create user with existing subscription
  - Send invoice webhook with same `current_period_end`
  - Verify usage NOT reset (only reset on renewal or first subscription)

- [ ] **T3.4** Provider switch from Apple
  - Create user with Apple subscription
  - Send Stripe webhook
  - Check all Apple fields removed (including `apple_original_transaction_id`, `apple_is_trial`)

- [ ] **T3.5** Provider switch from Google Play
  - Create user with Google Play subscription
  - Send Stripe webhook
  - Check all Google Play fields removed with CORRECT field names:
    - `google_play_product_id` (not `google_purchase_token`)
    - `google_play_purchase_token` (not `google_order_id`)
    - `google_play_order_id`
    - `google_play_is_trial`
    - `google_play_auto_renewing`

**Database Validation for T3.1 (First Subscription):**
```python
# Before webhook
user = {
  "subscription_plan": "try_learn",
  "practice_minutes_used": 10.0,
  "practice_sessions_used": 2,
}

# After webhook (Bug #4 fix - should reset even on first subscription)
user = {
  "subscription_plan": "fluency_builder",
  "subscription_status": "active",
  "subscription_provider": "stripe",
  "practice_minutes_used": 0.0,  # ✅ RESET on first subscription
  "practice_sessions_used": 0,   # ✅ RESET on first subscription
  "assessments_used": 0,          # ✅ RESET on first subscription
}
```

**Database Validation for T3.2 (Renewal):**
```python
# Before webhook
user = {
  "current_period_end": datetime(2026, 1, 15),
  "practice_minutes_used": 50.0,
  "practice_sessions_used": 10,
}

# After webhook
user = {
  "current_period_start": datetime(2026, 2, 15),  # New period
  "current_period_end": datetime(2026, 3, 15),
  "practice_minutes_used": 0.0,  # ✅ RESET on renewal
  "practice_sessions_used": 0,
  "assessments_used": 0,
}
```

#### 2.4 Free User Reset Cron Job
**Script:** `cron_jobs/reset_free_user_usage.py`

**Test Cases:**
- [ ] **T4.1** Reset expired free user
  - Create free user with `subscription_plan: "try_learn"`
  - Set `current_period_end` to past date
  - Set usage to non-zero values
  - Run cron job
  - Verify usage reset to 0
  - Verify period dates updated to new month

- [ ] **T4.2** Skip free users with future period end
  - Create free user with future `current_period_end`
  - Set usage to non-zero values
  - Run cron job
  - Verify usage NOT reset

- [ ] **T4.3** Skip paid users
  - Create paid user with expired period
  - Run cron job
  - Verify user NOT processed

- [ ] **T4.4** Audit trail creation
  - Run reset on free user
  - Verify `SubscriptionService.reset_monthly_usage()` called
  - Check audit trail created correctly

### Phase 3: Mobile App Testing

#### 3.1 Apple IAP Service
**File:** `src/services/AppleIAPService.ts`

**Test Cases:**
- [ ] **T5.1** Restore purchases with no conflict
  - User has no active subscription
  - Tap "Restore Purchases"
  - Verify no warning shown
  - Verify restore proceeds normally

- [ ] **T5.2** Restore purchases with Stripe conflict
  - User has active Stripe subscription
  - Tap "Restore Purchases"
  - Verify alert shown: "You have an active STRIPE subscription..."
  - Tap "Cancel"
  - Verify restore cancelled

- [ ] **T5.3** Restore purchases - user confirms despite conflict
  - User has active Google Play subscription
  - Tap "Restore Purchases"
  - Verify alert shown with warning
  - Tap "Continue Anyway"
  - Verify restore proceeds

- [ ] **T5.4** Restore purchases - status check fails
  - Mock API failure for `/api/stripe/subscription-status`
  - Tap "Restore Purchases"
  - Verify restore proceeds anyway (graceful degradation)

#### 3.2 Google Play Billing Service
**File:** `src/services/GooglePlayBillingService.ts`

**Test Cases:**
- [ ] **T6.1** Restore purchases with no conflict
  - User has no active subscription
  - Tap "Restore Purchases"
  - Verify no warning shown
  - Verify restore proceeds normally

- [ ] **T6.2** Restore purchases with Apple conflict
  - User has active Apple subscription
  - Tap "Restore Purchases"
  - Verify alert shown: "You have an active APPLE subscription..."
  - Tap "Cancel"
  - Verify restore cancelled

- [ ] **T6.3** Restore purchases - user confirms despite conflict
  - User has active Stripe subscription
  - Tap "Restore Purchases"
  - Verify alert shown with warning
  - Tap "Continue Anyway"
  - Verify restore proceeds

### Phase 4: Cross-Provider Integration Testing

#### 4.1 Provider Switching Scenarios

**Test Cases:**
- [ ] **T7.1** Stripe → Apple → Google Play
  - Subscribe via Stripe web
  - Verify subscription active, usage reset
  - Cancel Stripe, wait for expiration
  - Subscribe via Apple IAP
  - Verify all Stripe fields removed
  - Cancel Apple, wait for expiration
  - Subscribe via Google Play
  - Verify all Apple fields removed
  - Verify all Stripe fields removed

- [ ] **T7.2** Google Play → Apple
  - Subscribe via Google Play
  - Cancel and wait for expiration
  - Subscribe via Apple
  - Verify `$unset` removed:
    - `google_play_product_id`
    - `google_play_purchase_token`
    - `google_play_order_id`
    - `google_play_is_trial`
    - `google_play_auto_renewing`

- [ ] **T7.3** Apple → Stripe
  - Subscribe via Apple
  - Cancel and wait for expiration
  - Subscribe via Stripe
  - Verify `$unset` removed:
    - `apple_product_id`
    - `apple_transaction_id`
    - `apple_original_transaction_id`
    - `apple_is_trial`

#### 4.2 Conflict Prevention

**Test Cases:**
- [ ] **T8.1** Active Stripe blocks Apple
  - Subscribe via Stripe (active until March 1)
  - Attempt Apple IAP verification
  - Expect HTTP 409 with expiry date in message

- [ ] **T8.2** Active Apple blocks Google Play
  - Subscribe via Apple (active until March 1)
  - Attempt Google Play verification
  - Expect HTTP 409

- [ ] **T8.3** Active Google Play blocks Stripe
  - Subscribe via Google Play
  - Attempt Stripe subscription via webhook
  - Should succeed (Stripe webhooks don't have conflict check)
  - Note: This is expected - Stripe is authoritative

### Phase 5: Data Integrity Validation

#### 5.1 Field Completeness Checks

**Manual Database Queries:**
```javascript
// Check for orphaned Stripe fields on non-Stripe users
db.users.find({
  subscription_provider: { $ne: "stripe" },
  $or: [
    { stripe_customer_id: { $exists: true } },
    { stripe_subscription_id: { $exists: true } }
  ]
})

// Check for orphaned Apple fields on non-Apple users
db.users.find({
  subscription_provider: { $ne: "apple" },
  $or: [
    { apple_product_id: { $exists: true } },
    { apple_transaction_id: { $exists: true } },
    { apple_original_transaction_id: { $exists: true } },
    { apple_is_trial: { $exists: true } }
  ]
})

// Check for orphaned Google Play fields on non-Google users
db.users.find({
  subscription_provider: { $ne: "google_play" },
  $or: [
    { google_play_product_id: { $exists: true } },
    { google_play_purchase_token: { $exists: true } },
    { google_play_order_id: { $exists: true } },
    { google_play_is_trial: { $exists: true } },
    { google_play_auto_renewing: { $exists: true } }
  ]
})

// Check for nested subscription object (old format)
db.users.find({
  subscription: { $exists: true }
})
```

**Expected Results:** All queries should return 0 documents after fixes applied

#### 5.2 Usage Reset Validation

**Queries:**
```javascript
// Find any Stripe users with first subscription but non-zero usage (Bug #4)
// Note: This requires checking audit trail or logs, can't query directly

// Find any users with usage > limits
db.users.aggregate([
  {
    $match: {
      subscription_plan: "try_learn",
      $or: [
        { practice_minutes_used: { $gt: 15 } },
        { practice_sessions_used: { $gt: 3 } },
        { assessments_used: { $gt: 1 } }
      ]
    }
  }
])
```

### Phase 6: Edge Cases

**Test Cases:**
- [ ] **T9.1** Concurrent provider switches
  - Simulate rapid provider switches
  - Verify final state is consistent
  - Check for race conditions

- [ ] **T9.2** Expired subscription restoration
  - User's subscription expired 30 days ago
  - User restores purchase
  - Verify usage reset
  - Verify dates set correctly

- [ ] **T9.3** Trial to paid conversion
  - User on trial via Stripe
  - Trial ends, converts to paid
  - Verify usage reset at conversion

---

## Testing Tools

### Manual Testing Script
```python
# scripts/test_subscription_system.py
import asyncio
from database import database
from datetime import datetime, timedelta

async def verify_field_cleanup(user_id: str, expected_provider: str):
    """Verify all non-provider fields are removed"""
    user = await database["users"].find_one({"_id": user_id})

    # Check Stripe fields
    if expected_provider != "stripe":
        assert "stripe_customer_id" not in user, "Stripe fields not cleaned up"
        assert "stripe_subscription_id" not in user

    # Check Apple fields
    if expected_provider != "apple":
        assert "apple_product_id" not in user, "Apple fields not cleaned up"
        assert "apple_transaction_id" not in user
        assert "apple_original_transaction_id" not in user, "apple_original_transaction_id not removed"
        assert "apple_is_trial" not in user, "apple_is_trial not removed"

    # Check Google Play fields
    if expected_provider != "google_play":
        assert "google_play_product_id" not in user, "Google Play product_id not removed"
        assert "google_play_purchase_token" not in user, "Google Play purchase_token not removed"
        assert "google_play_order_id" not in user, "Google Play order_id not removed"
        assert "google_play_is_trial" not in user, "Google Play is_trial not removed"
        assert "google_play_auto_renewing" not in user, "Google Play auto_renewing not removed"

    # Check no nested subscription object
    assert "subscription" not in user, "Nested subscription object still exists"

    print(f"✅ Field cleanup verified for provider: {expected_provider}")

async def verify_usage_reset(user_id: str):
    """Verify usage counters are reset to 0"""
    user = await database["users"].find_one({"_id": user_id})

    assert user["practice_minutes_used"] == 0.0, f"Minutes not reset: {user['practice_minutes_used']}"
    assert user["practice_sessions_used"] == 0, f"Sessions not reset: {user['practice_sessions_used']}"
    assert user["assessments_used"] == 0, f"Assessments not reset: {user['assessments_used']}"

    print(f"✅ Usage counters reset verified")
```

### Stripe CLI Testing
```bash
# Listen to webhooks locally
stripe listen --forward-to localhost:8000/stripe-webhook

# Trigger test events
stripe trigger invoice.payment_succeeded
stripe trigger customer.subscription.updated
stripe trigger customer.subscription.deleted
```

### MongoDB Validation Queries
See Section 5.1 above

---

## Success Criteria

### Code Review Phase (Completed)
- [x] All backend routes reviewed
- [x] All mobile app services reviewed
- [x] 4 bugs identified and fixed
- [x] All `$unset` operations use correct field names
- [x] Usage reset consistent across all providers

### Testing Phase (Pending)
- [ ] All Phase 2 API tests pass (17 test cases)
- [ ] All Phase 3 mobile tests pass (8 test cases)
- [ ] All Phase 4 integration tests pass (6 test cases)
- [ ] All Phase 5 data integrity queries return 0 results
- [ ] All Phase 6 edge cases handled correctly

### Production Readiness
- [ ] No orphaned provider fields in database
- [ ] No nested `subscription` objects remain
- [ ] Usage reset works on first subscription (Bug #4 fix validated)
- [ ] Provider conflict protection working (HTTP 409 errors)
- [ ] Mobile app restore warnings functional
- [ ] Audit trails created for all usage resets
- [ ] Logging comprehensive and consistent

---

## Next Steps

1. **Commit bug fixes** to feature branch
2. **Run automated tests** (if available)
3. **Manual testing** following this checklist
4. **Database validation** queries
5. **User acceptance testing** with test accounts
6. **Merge to main** after all tests pass
7. **Monitor production** for first 24 hours after deployment

---

## Notes

- All 4 bugs found during code review have been fixed
- Mobile app changes are correct - no bugs found
- Free user reset cron job is correct - no bugs found
- Testing should focus on provider switching and field cleanup
- Pay special attention to Bug #4 fix - ensure first Stripe subscriptions reset usage
