# Phase 1: Database Migration Scripts

**Purpose:** Safely delete challenge_pool, add language fields, and normalize casing
**Safety:** All operations are safe, tested, and reversible
**Timeline:** 15-20 minutes to run all scripts

---

## 📋 **EXECUTION ORDER**

Run these scripts in order from your local machine:

### **Prerequisites**

1. **Install Python dependencies:**
   ```bash
   pip install motor pymongo python-dotenv
   ```

2. **Set MongoDB connection:**
   ```bash
   export MONGODB_URL="mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
   ```

   Or create a `.env` file:
   ```
   MONGODB_URL=mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin
   ```

---

## 🚀 **STEP-BY-STEP EXECUTION**

### **Step 1: Backup Collections** ✅ SAFE
```bash
cd database-migrations/phase1
python 1_backup_collections.py
```

**What it does:**
- Backs up `challenge_pool` (2,363 documents)
- Backs up `reference_challenges` (600 documents)
- Creates timestamped backup directory
- Generates metadata file

**Safety:** Read-only, completely safe

**Output:**
- `backups_YYYYMMDD_HHMMSS/` directory
- JSON files with all data

**Time:** ~30 seconds

---

### **Step 2: Delete Challenge Pool** ⚠️ DESTRUCTIVE (but safe)
```bash
python 2_delete_challenge_pool.py
```

**What it does:**
- Deletes all 2,363 documents from `challenge_pool`
- Optionally cleans up user challengeStats
- System regenerates challenges automatically

**Safety:**
- ✅ Isolated collection (no foreign keys)
- ✅ Reversible from backup
- ✅ App continues working

**Confirmation required:**
- Type `DELETE 2363` to confirm

**Time:** ~10 seconds

---

### **Step 3: Add Language to Reference Challenges** ✅ SAFE
```bash
python 3_add_language_to_references.py
```

**What it does:**
- Adds `language: "english"` to all reference challenges
- Creates index for performance
- Non-destructive (only adds field)

**Safety:**
- ✅ Additive only
- ✅ Doesn't change existing data
- ✅ Reversible

**Time:** ~5 seconds

---

### **Step 4: Normalize Language Casing** ✅ SAFE
```bash
python 4_normalize_language_casing.py
```

**What it does:**
- Converts all language fields to lowercase
- Affects 5 collections:
  - `learning_plans` (58 docs)
  - `users` (41 docs)
  - `conversation_sessions` (137 docs)
  - `reference_challenges` (600 docs)
  - `flashcards` (300 docs)

**Changes:**
- `"English"` → `"english"`
- `"Dutch"` → `"dutch"`
- `"Spanish"` → `"spanish"`

**Safety:**
- ✅ Only changes string values
- ✅ Doesn't affect structure
- ✅ Reversible from backup

**Time:** ~10 seconds

---

### **Step 5: Verify Migration** ✅ SAFE
```bash
python 5_verify_migration.py
```

**What it does:**
- Checks all Phase 1 changes
- Verifies:
  - Challenge pool is empty
  - Reference challenges have language field
  - All languages are lowercase
  - Indexes exist

**Safety:** Read-only, completely safe

**Time:** ~5 seconds

---

## 📊 **EXPECTED RESULTS**

After running all 5 scripts:

### ✅ Challenge Pool
```
challenge_pool: 0 documents (deleted)
```

### ✅ Reference Challenges
```
reference_challenges: 600 documents
  - All have language: "english"
  - Index created: language + cefr_level + challenge_type
```

### ✅ Language Casing
```
learning_plans:
  - english: 46 plans ✅
  - dutch: 7 plans ✅
  - spanish: 4 plans ✅
  (No more "English", "Dutch", "Spanish")

users:
  - english: 6 users ✅
  - dutch: 4 users ✅
  (No more "English", "Dutch")

conversation_sessions:
  - english: 132 sessions ✅
  - dutch: 2 sessions ✅
  (All lowercase)
```

---

## ⚠️ **TROUBLESHOOTING**

### Problem: Connection timeout
```
Error: ServerSelectionTimeoutError
```

**Solution:**
1. Check MongoDB URL is correct
2. Verify network access to Railway
3. Try increasing timeout in script

### Problem: Script hangs on confirmation
```
Continue? (yes/no):
```

**Solution:**
- Type `yes` and press Enter
- For Step 2, type `DELETE 2363` exactly

### Problem: "Module not found"
```
ModuleNotFoundError: No module named 'motor'
```

**Solution:**
```bash
pip install motor pymongo python-dotenv
```

---

## 🔄 **ROLLBACK PROCEDURE**

If you need to undo changes:

### Restore Challenge Pool
```bash
cd backups_YYYYMMDD_HHMMSS/
mongoimport --uri="$MONGODB_URL" \
  --collection=challenge_pool \
  --file=challenge_pool_backup.json
```

### Restore Reference Challenges
```bash
mongoimport --uri="$MONGODB_URL" \
  --collection=reference_challenges \
  --file=reference_challenges_backup.json
```

### Restore Other Collections
Same process for each collection backup.

---

## 💰 **IMPACT SUMMARY**

### Data Changes:
- ✅ Challenge pool: 2,363 documents deleted
- ✅ Reference challenges: 600 documents updated (language added)
- ✅ Learning plans: 58 documents updated (casing normalized)
- ✅ Users: 41 documents updated (casing normalized)
- ✅ Sessions: 137 documents updated (casing normalized)

### App Impact:
- ✅ App continues working normally
- ✅ Users get fresh challenges automatically
- ✅ No downtime required
- ✅ All other features unaffected

### Cost Impact:
- ✅ No immediate cost
- ✅ Weekly cron (Phase 5) saves $358/month

---

## ✅ **VERIFICATION CHECKLIST**

After running all scripts, verify:

- [ ] Challenge pool is empty (0 documents)
- [ ] Reference challenges all have `language: "english"`
- [ ] No uppercase languages in `learning_plans`
- [ ] No uppercase languages in `users.preferred_language`
- [ ] No uppercase languages in `conversation_sessions`
- [ ] Index exists on `reference_challenges` (language field)
- [ ] Backups created and saved
- [ ] Verification script shows "ALL CHECKS PASSED"

---

## 🎯 **NEXT STEPS**

Once Phase 1 is complete:

1. ✅ **Phase 2:** Implement CrewAI multi-agent system
2. ✅ **Phase 3:** Update backend code with language filtering
3. ✅ **Phase 4:** Test English/Dutch separation
4. ✅ **Phase 5:** Deploy weekly cron
5. ✅ **Phase 6:** Create iOS integration guide

---

## 📞 **SUPPORT**

If you encounter issues:

1. Check the backup files exist
2. Run verification script to see what failed
3. Review error messages in script output
4. Can rollback anytime from backups

---

## 🎉 **SUCCESS CRITERIA**

You'll know Phase 1 succeeded when:

1. ✅ Verification script shows "ALL CHECKS PASSED"
2. ✅ Challenge pool is empty
3. ✅ All languages are lowercase
4. ✅ Reference challenges have language field
5. ✅ No errors in any script output

**Ready to proceed to Phase 2!** 🚀
