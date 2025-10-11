# 🧪 MyTaco AI Institutional Features - Production Test Scenarios

**Environment:** Railway Staging/Production  
**Database:** Production MongoDB  
**Testing Method:** Manual Frontend Testing  
**Date:** March 10, 2025

---

## 📋 TEST PREPARATION

### Prerequisites
1. ✅ Railway deployment is live
2. ✅ Production MongoDB is accessible
3. ✅ Feature flags are enabled:
   ```
   INSTITUTIONAL_FEATURES_ENABLED=true
   INSTITUTION_SIGNUP_ENABLED=true
   TUTOR_DASHBOARD_ENABLED=true
   LEARNER_ENROLLMENT_ENABLED=true
   ```
4. ✅ You have access to MongoDB to verify data
5. ✅ You have 2-3 email addresses for testing

### Test Data Requirements
- **Admin Email:** `test-admin-{timestamp}@yourdomain.com`
- **Tutor Emails:** `tutor1@test.com`, `tutor2@test.com`
- **Learner Emails:** `learner1@test.com`, `learner2@test.com`, etc.

---

## 🎯 TEST SUITE OVERVIEW

| Flow | Tests | Status | Priority |
|------|-------|--------|----------|
| FLOW 3 - Institution Setup | 15 tests | ✅ Ready | HIGH |
| FLOW 2 - New Learner Enrollment | 12 tests | ✅ Ready | HIGH |
| FLOW 1 - Existing User | 0 tests | ❌ Not Implemented | N/A |

---

# 🏢 FLOW 3: INSTITUTION SETUP - TEST SCENARIOS

## TEST 3.1: Institution Admin Signup (Happy Path)

### Objective
Verify that an institution admin can successfully create an account and set up an institution.

### Steps
1. Navigate to institution signup page
   - URL: `https://your-app.railway.app/institution/signup`

2. Fill out the signup form:
   ```
   Institution Name: "Test Academy [TIMESTAMP]"
   Domain: "test-academy.edu" (optional)
   Admin Name: "John Admin"
   Admin Email: "admin-[timestamp]@test-academy.edu"
   Password: "SecurePass123!"
   Subscription Plan: Select "Professional"
   ```

3. Click "Sign Up" button

### Expected Results
✅ **Success Response:**
- Success message displayed: "Institution created successfully"
- Institution code generated (e.g., "TBR4332") and displayed
- User redirected to admin dashboard or login page
- HTTP Status: 200

✅ **Database Verification (MongoDB):**
```javascript
// Check institutions collection
db.institutions.findOne({admin_email: "admin-[timestamp]@test-academy.edu"})

// Should contain:
{
  name: "Test Academy [TIMESTAMP]",
  institution_code: "[6+ chars]",
  admin_email: "admin-[timestamp]@test-academy.edu",
  subscription_plan: "professional",
  max_tutors: 10,
  max_learners: 200,
  is_active: true,
  created_at: "[timestamp]"
}
```

### Error Scenarios to Test
❌ **Test 3.1a: Duplicate Email**
- Try signing up again with same admin email
- Expected: 400 error "Email already exists"

❌ **Test 3.1b: Invalid Email Format**
- Use email: "notanemail"
- Expected: 422 Validation error

❌ **Test 3.1c: Empty Required Fields**
- Leave institution name blank
- Expected: Form validation error

---

## TEST 3.2: Institution Admin Login

### Objective
Verify admin can log in after signup.

### Steps
1. Navigate to institution login page
   - URL: `https://your-app.railway.app/institution/login`

2. Enter credentials:
   ```
   Email: "admin-[timestamp]@test-academy.edu"
   Password: "SecurePass123!"
   ```

3. Click "Login"

### Expected Results
✅ **Success:**
- JWT token returned
- User redirected to admin dashboard
- Session maintained
- HTTP Status: 200

❌ **Test 3.2a: Wrong Password**
- Enter wrong password
- Expected: 401 Unauthorized

---

## TEST 3.3: View Institution Statistics

### Objective
Verify admin can view institution stats.

### Steps
1. Log in as admin (from Test 3.2)

2. Navigate to institution dashboard
   - Should auto-load after login

3. View statistics panel

### Expected Results
✅ **Statistics Displayed:**
```
Total Tutors: 0
Total Learners: 0
Max Tutors: 10 (Professional plan)
Max Learners: 200 (Professional plan)
Active Status: Active
Institution Code: [displayed]
```

---

## TEST 3.4: Invite First Tutor

### Objective
Verify admin can invite tutors.

### Steps
1. From admin dashboard, click "Invite Tutor" button

2. Fill out invitation form:
   ```
   Tutor Name: "Jane Tutor"
   Tutor Email: "tutor1-[timestamp]@test.com"
   ```

3. Click "Send Invitation"

### Expected Results
✅ **Success:**
- Success message: "Tutor invitation sent"
- Invitation code generated and displayed (e.g., "a8f7d9e6c5b4...")
- Tutor appears in "Pending Invitations" list

✅ **Database Verification:**
```javascript
db.invitations.findOne({email: "tutor1-[timestamp]@test.com"})

// Should contain:
{
  email: "tutor1-[timestamp]@test.com",
  name: "Jane Tutor",
  invitation_type: "tutor",
  code: "[unique_code]",
  is_accepted: false,
  expires_at: "[now + 7 days]",
  institution_id: "[institution_id]"
}
```

---

## TEST 3.5: Tutor Accepts Invitation

### Objective
Verify tutor can create account using invitation code.

### Steps
1. **Get invitation code** from Test 3.4 or from database

2. Navigate to tutor invitation acceptance page
   - URL: `https://your-app.railway.app/tutor/accept-invite`

3. Enter invitation code:
   ```
   Invitation Code: "[code from step 1]"
   ```

4. Fill out tutor profile:
   ```
   Bio: "Experienced Spanish teacher with 10 years of experience"
   Qualifications: "MA in Linguistics, DELE Certification"
   ```

5. Click "Accept Invitation"

### Expected Results
✅ **Success:**
- Success message: "Welcome! Your tutor account is now active"
- Tutor account created
- User redirected to tutor dashboard
- HTTP Status: 200

✅ **Database Verification:**
```javascript
db.tutors.findOne({email: "tutor1-[timestamp]@test.com"})

// Should contain:
{
  email: "tutor1-[timestamp]@test.com",
  name: "Jane Tutor",
  institution_id: "[institution_id]",
  is_active: true,
  invitation_accepted: true,
  bio: "[bio text]",
  qualifications: "[qualifications text]"
}

// Invitation should be marked accepted:
db.invitations.findOne({email: "tutor1-[timestamp]@test.com"})
// is_accepted: true
```

---

## TEST 3.6: Invite Multiple Tutors (Test Limits)

### Objective
Verify subscription limits are enforced for tutors.

### Steps
1. From admin dashboard, invite tutors up to the limit:
   - Professional plan: 10 tutors max
   - Invite tutors 2-10

2. Try to invite 11th tutor

### Expected Results
✅ **For tutors 2-10:**
- All invitations created successfully

❌ **For 11th tutor:**
- Error message: "Maximum tutor limit reached (10)"
- HTTP Status: 400
- No invitation created

---

## TEST 3.7: Add Learner Manually (Admin)

### Objective
Verify admin can manually enroll a learner.

### Steps
1. Log in as admin

2. Navigate to "Learner Management" page

3. Click "Add Learner" button

4. Fill out the form:
   ```
   Learner Name: "Maria Student"
   Learner Email: "learner1-[timestamp]@test.com"
   Assign to Tutor: Select "Jane Tutor"
   ```

5. Click "Enroll Learner"

### Expected Results
✅ **Success:**
- Success message: "Learner invitation sent"
- Invitation code generated
- Learner appears in "Pending Enrollments" list

✅ **Database Verification:**
```javascript
db.invitations.findOne({email: "learner1-[timestamp]@test.com"})

// Should contain:
{
  email: "learner1-[timestamp]@test.com",
  name: "Maria Student",
  invitation_type: "learner",
  institution_id: "[institution_id]",
  assigned_tutor_id: "[tutor_id]",
  is_accepted: false
}
```

---

## TEST 3.8: Bulk Import Learners (CSV)

### Objective
Verify admin can bulk import learners via CSV.

### Steps
1. Create a CSV file: `test_learners.csv`
   ```csv
   name,email
   "John Smith","john@test.com"
   "Sarah Johnson","sarah@test.com"
   "Mike Wilson","mike@test.com"
   "Emily Brown","emily@test.com"
   "David Lee","david@test.com"
   ```

2. From admin dashboard, click "Bulk Import"

3. Upload the CSV file

4. Review preview of learners

5. Click "Import All"

### Expected Results
✅ **Success:**
- Progress indicator shows: "Importing 5 learners..."
- Success message: "Successfully imported 5 learners"
- All learners appear in pending enrollments
- Auto-assigned to tutors (round-robin)

✅ **Database Verification:**
```javascript
// Count invitations created
db.invitations.countDocuments({
  email: {$in: ["john@test.com", "sarah@test.com", "mike@test.com", "emily@test.com", "david@test.com"]}
})
// Should return: 5
```

---

## TEST 3.9: View Tutor Dashboard

### Objective
Verify tutor can access their dashboard.

### Steps
1. Log in as tutor (from Test 3.5)
   - Email: "tutor1-[timestamp]@test.com"

2. View tutor dashboard

### Expected Results
✅ **Dashboard Shows:**
- Assigned learners list (initially empty)
- "Waiting for learners to accept consent"
- Statistics: 0 active learners
- Institution name displayed
- Profile information displayed

---

## TEST 3.10: Check Institution Stats Update

### Objective
Verify institution stats are updated correctly.

### Steps
1. Log in as admin

2. View institution statistics

### Expected Results
✅ **Updated Statistics:**
```
Total Tutors: 1 (or more if you invited more)
Total Learners: 5 (from bulk import)
Pending Invitations: 5 learners + any pending tutors
Max Tutors: 10
Max Learners: 200
```

---

# 🎓 FLOW 2: NEW LEARNER ENROLLMENT - TEST SCENARIOS

## TEST 2.1: Learner Self-Signup with Institution Code

### Objective
Verify a new learner can sign up using institution code.

### Steps
1. **Get institution code** from admin dashboard or database
   - Should be displayed during institution signup (e.g., "TBR4332")

2. Navigate to learner signup page
   - URL: `https://your-app.railway.app/learner/signup`

3. Fill out the form:
   ```
   Full Name: "Carlos Student"
   Email: "carlos-[timestamp]@test.com"
   Password: "LearnerPass123!"
   Institution Code: "[code from step 1]"
   ```

4. Click "Sign Up"

### Expected Results
✅ **Success:**
- Account created successfully
- User redirected to consent screen
- HTTP Status: 200
- Response indicates: `requires_consent: true`

✅ **Database Verification:**
```javascript
// User created
db.users.findOne({email: "carlos-[timestamp]@test.com"})

// Enrollment record created
db.institutional_learners.findOne({email: "carlos-[timestamp]@test.com"})

// Should contain:
{
  user_id: "[user_id]",
  email: "carlos-[timestamp]@test.com",
  institution_id: "[institution_id]",
  tutor_id: "[assigned_tutor_id]",
  consent_given: false,  // Not yet consented
  enrollment_method: "self_signup",
  is_active: true
}
```

---

## TEST 2.2: View Consent Screen

### Objective
Verify consent screen is shown and displays correct information.

### Steps
1. After Test 2.1 signup, user should be on consent screen

2. Review consent information

### Expected Results
✅ **Consent Screen Shows:**
- Institution name: "Test Academy"
- Tutor name: "Jane Tutor"
- Clear explanation of data sharing
- List of data to be shared:
  - Progress tracking
  - Assessment results
  - Conversation history
  - Learning statistics
- Two buttons: "Accept" and "Decline"
- Privacy explanation text

---

## TEST 2.3: Accept Consent

### Objective
Verify learner can grant consent and access becomes active.

### Steps
1. From consent screen (Test 2.2), click "Accept" button

2. Confirm consent if prompted

### Expected Results
✅ **Success:**
- Success message: "Consent granted. You may now start learning!"
- User redirected to learner dashboard
- HTTP Status: 200

✅ **Database Verification:**
```javascript
// Enrollment updated
db.institutional_learners.findOne({email: "carlos-[timestamp]@test.com"})

// Should now have:
{
  consent_given: true,
  consent_date: "[timestamp]",
  consent_revoked: false
}

// Consent audit record created
db.consent_records.find({learner_id: "[user_id]"})

// Should contain entry:
{
  learner_id: "[user_id]",
  institution_id: "[institution_id]",
  action: "granted",
  action_date: "[timestamp]",
  data_shared: ["progress", "assessments", "conversation_history"]
}
```

---

## TEST 2.4: Verify Learner Appears in Tutor Dashboard

### Objective
Verify tutor can now see the learner after consent is granted.

### Steps
1. Log in as tutor
   - Email: "tutor1-[timestamp]@test.com"

2. View assigned learners

### Expected Results
✅ **Learner Visible:**
- Carlos Student appears in learner list
- Shows "Consent Granted" status
- Shows enrollment date
- Can click to view learner profile

---

## TEST 2.5: Decline Consent

### Objective
Verify what happens when learner declines consent.

### Steps
1. Create another learner using Test 2.1 steps:
   ```
   Name: "Test Declined"
   Email: "declined-[timestamp]@test.com"
   ```

2. On consent screen, click "Decline" button

### Expected Results
✅ **Expected Behavior:**
- User account still created
- But institutional access is not granted
- Message: "You can still use MyTaco as an individual learner"

⚠️ **Note:** Current implementation keeps user linked with `consent_given: false`. 
Ideally, should convert to independent account.

✅ **Database Verification:**
```javascript
db.institutional_learners.findOne({email: "declined-[timestamp]@test.com"})

// Should have:
{
  consent_given: false,
  // User exists but tutor can't see them
}
```

---

## TEST 2.6: Learner Accepts Invitation from Admin

### Objective
Verify admin-invited learner can complete enrollment.

### Steps
1. **Get invitation code** from Test 3.7 or database:
   ```javascript
   db.invitations.findOne({email: "learner1-[timestamp]@test.com"})
   ```

2. Navigate to invitation acceptance page
   - URL: `https://your-app.railway.app/learner/accept-invite`

3. Enter invitation code and create account:
   ```
   Invitation Code: "[code]"
   Password: "NewPassword123!"
   ```

4. Click "Create Account"

5. View consent screen and click "Accept"

### Expected Results
✅ **Success:**
- Account created
- Consent granted
- User redirected to dashboard
- Appears in tutor's learner list

---

## TEST 2.7: Test Invalid Institution Code

### Objective
Verify error handling for invalid codes.

### Steps
1. Navigate to learner signup

2. Enter:
   ```
   Name: "Test Invalid"
   Email: "test@test.com"
   Password: "Pass123!"
   Institution Code: "INVALID_CODE_123"
   ```

3. Click "Sign Up"

### Expected Results
❌ **Error:**
- Error message: "Invalid institution code"
- HTTP Status: 400
- No account created

---

## TEST 2.8: Test Duplicate Email (Learner Already Exists)

### Objective
Verify duplicate email handling.

### Steps
1. Try to sign up again with Carlos's email:
   ```
   Email: "carlos-[timestamp]@test.com"  # Already used
   Institution Code: "[valid code]"
   ```

### Expected Results
⚠️ **Expected Behavior:**
- Should detect existing user
- Should link existing user to institution
- Should prompt for consent
- **Note:** Currently only works during signup flow

---

## TEST 2.9: Test Learner Limit

### Objective
Verify subscription learner limits are enforced.

### Steps
1. Note current learner count

2. **For Professional Plan (200 learners):**
   - This test requires 200+ signups
   - Use bulk import to approach limit
   - Try to enroll 201st learner

### Expected Results (at limit)
❌ **Error:**
- Error message: "Maximum learner limit reached (200)"
- HTTP Status: 400
- No enrollment created

---

## TEST 2.10: Check Consent Status API

### Objective
Verify consent status can be queried.

### Steps
1. **Using API client (Postman or curl):**
   ```bash
   GET https://your-app.railway.app/api/v1/consent/status/{learner_id}/{institution_id}
   ```

2. Replace `{learner_id}` and `{institution_id}` with actual IDs

### Expected Results
✅ **Response:**
```json
{
  "has_consent": true,
  "consent_given_date": "2025-03-10T...",
  "consent_revoked": false,
  "institution_name": "Test Academy",
  "tutor_name": "Jane Tutor",
  "data_shared": ["progress", "assessments", "conversation_history"]
}
```

---

## TEST 2.11: Revoke Consent

### Objective
Verify learner can revoke consent.

### Steps
1. **Using API client (or future settings UI):**
   ```bash
   POST https://your-app.railway.app/api/v1/consent/revoke
   Content-Type: application/json
   
   {
     "learner_id": "[learner_id]",
     "institution_id": "[institution_id]"
   }
   ```

### Expected Results
✅ **Success:**
- HTTP Status: 200
- Message: "Consent revoked successfully"

✅ **Database Verification:**
```javascript
db.institutional_learners.findOne({user_id: "[learner_id]"})

// Should show:
{
  consent_given: true,  // Still true
  consent_revoked: true,  // But revoked
  consent_revoked_date: "[timestamp]"
}

// Audit record created
db.consent_records.find({learner_id: "[learner_id]", action: "revoked"})
// Should exist
```

✅ **Tutor View:**
- Learner should disappear from tutor's dashboard
- Or show as "Access Revoked"

---

## TEST 2.12: Verify Data Isolation

### Objective
Verify tutors can only see learners with consent.

### Steps
1. Create 3 learners:
   - Learner A: Consent granted
   - Learner B: Consent not granted (declined)
   - Learner C: Consent granted

2. Log in as tutor

3. View learner list

### Expected Results
✅ **Tutor Sees:**
- Learner A ✅
- Learner B ❌ (not visible)
- Learner C ✅

✅ **Database Query Verification:**
```javascript
// This is what tutor dashboard should query
db.institutional_learners.find({
  tutor_id: "[tutor_id]",
  consent_given: true,
  consent_revoked: false,
  is_active: true
})

// Should only return A and C
```

---

# 🚫 FLOW 1: EXISTING USER - NOT TESTABLE

## ❌ Cannot Test - Not Implemented

**FLOW 1 (Existing User Joins Institution)** cannot be tested because critical components are missing:

- ❌ No API endpoint to link existing users
- ❌ No Settings page for users
- ❌ No invitation system for existing users
- ❌ No UI to enter institution code as logged-in user

**Estimated Implementation:** 18-28 hours

**Workaround for Testing:**
- Existing users can sign up as "new learners" if they create a new account
- Not ideal, but functional for testing FLOW 2

---

# 📊 TEST EXECUTION CHECKLIST

## Before Testing
- [ ] Railway app is deployed and accessible
- [ ] MongoDB connection is working
- [ ] Feature flags are enabled
- [ ] You have email addresses ready
- [ ] You have MongoDB access (for verification)
- [ ] You have API client (Postman/curl) for API tests

## During Testing - Track Results

### FLOW 3 Tests (Institution Setup)
- [ ] 3.1: Institution signup ✅ / ❌
- [ ] 3.2: Admin login ✅ / ❌
- [ ] 3.3: View stats ✅ / ❌
- [ ] 3.4: Invite tutor ✅ / ❌
- [ ] 3.5: Tutor accepts invite ✅ / ❌
- [ ] 3.6: Test tutor limits ✅ / ❌
- [ ] 3.7: Add learner manually ✅ / ❌
- [ ] 3.8: Bulk import learners ✅ / ❌
- [ ] 3.9: Tutor dashboard ✅ / ❌
- [ ] 3.10: Stats update ✅ / ❌

### FLOW 2 Tests (Learner Enrollment)
- [ ] 2.1: Learner self-signup ✅ / ❌
- [ ] 2.2: Consent screen displayed ✅ / ❌
- [ ] 2.3: Accept consent ✅ / ❌
- [ ] 2.4: Appears in tutor dashboard ✅ / ❌
- [ ] 2.5: Decline consent ✅ / ❌
- [ ] 2.6: Accept admin invitation ✅ / ❌
- [ ] 2.7: Invalid code error ✅ / ❌
- [ ] 2.8: Duplicate email ✅ / ❌
- [ ] 2.9: Learner limit ✅ / ❌
- [ ] 2.10: Check consent status ✅ / ❌
- [ ] 2.11: Revoke consent ✅ / ❌
- [ ] 2.12: Data isolation ✅ / ❌

## After Testing
- [ ] Document all failures
- [ ] Take screenshots of errors
- [ ] Save MongoDB queries used
- [ ] Note any unexpected behaviors
- [ ] Clean up test data (if needed)

---

# 🔍 DATABASE VERIFICATION QUERIES

## Quick Check Queries

### Check Institution
```javascript
// Find your test institution
db.institutions.findOne({name: /Test Academy/i})

// Count tutors in institution
db.tutors.countDocuments({institution_id: "[institution_id]"})

// Count learners in institution
db.institutional_learners.countDocuments({institution_id: "[institution_id]"})
```

### Check Invitations
```javascript
// Pending invitations
db.invitations.find({is_accepted: false, institution_id: "[institution_id]"})

// Accepted invitations
db.invitations.find({is_accepted: true, institution_id: "[institution_id]"})

// Expired invitations (older than 7 days)
db.invitations.find({
  expires_at: {$lt: new Date()},
  is_accepted: false
})
```

### Check Consent
```javascript
// Learners with consent
db.institutional_learners.find({
  institution_id: "[institution_id]",
  consent_given: true,
  consent_revoked: false
})

// Consent audit trail
db.consent_records.find({institution_id: "[institution_id]"}).sort({action_date: -1})
```

### Check Users
```javascript
// Institutional learners
db.users.find({account_type: "institutional_learner"})

// Recently created users
db.users.find({created_at: {$gte: new Date(Date.now() - 24*60*60*1000)}})
```

---

# 🐛 COMMON ISSUES & DEBUGGING

## Issue 1: Feature Flags Not Working
**Symptom:** 403 error "Institutional features not enabled"

**Solution:**
- Check Railway environment variables
- Ensure `INSTITUTIONAL_FEATURES_ENABLED=true`
- Restart application after changing

## Issue 2: Institution Code Not Generated
**Symptom:** Signup succeeds but no code shown

**Solution:**
- Check database directly:
  ```javascript
  db.institutions.findOne({admin_email: "[your_email]"}).institution_code
  ```
- Code should be 6+ characters

## Issue 3: Tutor Can't See Learners
**Symptom:** Tutor dashboard is empty

**Solution:**
- Verify learner granted consent
- Check query:
  ```javascript
  db.institutional_learners.find({
    tutor_id: "[tutor_id]",
    consent_given: true
  })
  ```

## Issue 4: Invitation Code Invalid
**Symptom:** "Invalid invitation code" error

**Solution:**
- Check invitation exists and not expired:
  ```javascript
  db.invitations.findOne({code: "[code]"})
  ```
- Check `expires_at` date
- Check `is_accepted` is false

## Issue 5: CSV Import Fails
**Symptom:** Bulk import shows errors

**Solution:**
- Verify CSV format (comma-separated, headers: name,email)
- Check for duplicate emails
- Verify learner limit not exceeded
- Ensure at least one active tutor exists

---

# 📈 SUCCESS CRITERIA

## Test Pass Criteria

✅ **FLOW 3 (Institution Setup):**
- All 10 tests pass
- Institution created successfully
- Tutors can be invited and accept
- Learners can be enrolled
- Statistics are accurate
- Subscription limits enforced

✅ **FLOW 2 (New Learner Enrollment):**
- All 12 tests pass
- Learners can self-signup
- Learners can accept admin invitations
- Consent screen works
- Data isolation maintained
- Tutors only see consented learners

---

# 📞 SUPPORT

**If tests fail:**
1. Check validation reports in `backend/validation/`
2. Review MongoDB data for inconsistencies
3. Check Railway logs for errors
4. Verify feature flags are enabled
5. Ensure database indexes are created

**MongoDB Commands to Run:**
```bash
# Connect to production MongoDB
mongosh "[your_mongodb_uri]"

# Switch to database
use language_tutor

# Run verification queries from above
```

---

**Test Report Template:**

```markdown
## Test Execution Report

**Date:** [Date]
**Environment:** [Staging/Production]
**Tester:** [Name]

### Summary
- Total Tests: 22
- Passed: [X]
- Failed: [Y]
- Pass Rate: [X/22 * 100]%

### Failed Tests
1. Test X.X: [Description]
   - Error: [Error message]
   - Expected: [Expected result]
   - Actual: [Actual result]
   - Screenshots: [Link]

### Notes
[Any additional observations]

### Recommendation
[ ] Ready for production
[ ] Needs fixes before production
```

---

**END OF TEST SCENARIOS**

*These scenarios validate FLOW 2 (New Learner Enrollment) and FLOW 3 (Institution Setup). FLOW 1 (Existing User) cannot be tested as it's only 30% implemented.*
