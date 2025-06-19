# Helper Scripts

This directory contains utility scripts for database maintenance and administration tasks.

## Scripts

### `clean_user_data.py`
**Purpose**: Clean users' speaking assessment and practice mode conversation data from MongoDB

**Features**:
- Lists all users with their basic information and assessment data status
- Lists all conversation sessions (practice mode conversations)
- Lists all learning plans
- Provides detailed overview of database collections
- Safely removes:
  - Speaking assessment data from user profiles (`last_assessment_data` field)
  - All conversation sessions (practice mode conversations)
  - All learning plans
- Includes confirmation prompt before deletion
- Provides detailed cleanup summary

**Usage**:
```bash
cd backend/helper_scripts
python clean_user_data.py
```

**Safety Features**:
- Requires explicit confirmation before deletion
- Provides detailed preview of what will be deleted
- Maintains database connection safety with proper error handling
- Preserves user accounts and other essential data

### `verify_cleanup.py`
**Purpose**: Verify that the cleanup process was successful

**Features**:
- Connects to MongoDB and verifies cleanup results
- Counts remaining assessment data, conversation sessions, and learning plans
- Provides clear success/failure status

**Usage**:
```bash
cd backend/helper_scripts
python verify_cleanup.py
```

## Requirements

Both scripts require:
- Python 3.7+
- `motor` (async MongoDB driver)
- `python-dotenv` for environment variables
- Access to MongoDB database (configured via environment variables)

## Environment Variables

The scripts use the following environment variables:
- `MONGODB_URL`: MongoDB connection string (defaults to `mongodb://localhost:27017`)
- `DATABASE_NAME`: Database name (defaults to `language_tutor`)

## Safety Notes

⚠️ **Important**: The cleanup script permanently deletes data. Always:
1. Backup your database before running cleanup scripts
2. Test on a development/staging environment first
3. Review the preview output carefully before confirming deletion
4. Run the verification script after cleanup to confirm success

## Example Output

### Cleanup Script
```
🚀 Starting MongoDB User Data Cleanup
================================================================================
✅ Connected to MongoDB at: mongodb://localhost:27017
📁 Using database: language_tutor

📋 STEP 1: Examining database structure
📁 All collections in database:
   📂 users: 35 documents
   📂 conversation_sessions: 5 documents
   📂 learning_plans: 19 documents
   ...

✅ CLEANUP COMPLETED
   📊 Users with assessment data cleaned: 6
   💬 Conversation sessions deleted: 5
   📚 Learning plans deleted: 19
```

### Verification Script
```
✅ Connected to MongoDB at: mongodb://localhost:27017
🔍 VERIFICATION RESULTS
   👥 Users with assessment data remaining: 0
   💬 Conversation sessions remaining: 0
   📚 Learning plans remaining: 0

✅ CLEANUP VERIFICATION: SUCCESS
All speaking assessment data and practice mode conversations have been cleaned!
