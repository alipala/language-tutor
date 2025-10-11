# Institutional Data Management Scripts

This directory contains scripts for managing institutional data during development and testing.

## Scripts Overview

### 1. `setup_institutional_db.py`
**Purpose**: Initialize institutional collections and indexes in MongoDB
**Usage**: Run once to set up the database schema
```bash
python scripts/setup_institutional_db.py
```

### 2. `seed_institutional_data.py`
**Purpose**: Populate MongoDB with realistic test data for development
**Usage**: Run in development environments to create mock data
```bash
python scripts/seed_institutional_data.py
```

**Creates**:
- 3 Institutions (Lincoln Academy, Global Language Institute, StartUp Language School)
- 3 Tutors with different qualifications and bios
- 3 Invitations (2 active, 1 expired)
- 2 Institutional learners (1 with consent, 1 without)
- 2 Consent records (grant and revoke actions)

### 3. `clear_institutional_data.py`
**Purpose**: Remove all institutional data for clean testing
**Usage**: Run before re-seeding or for clean test environments
```bash
python scripts/clear_institutional_data.py
```

### 4. `verify_seed_data.py`
**Purpose**: Verify that seed data was created correctly
**Usage**: Run after seeding to confirm data integrity
```bash
python scripts/verify_seed_data.py
```

## Test Data Summary

### Institution Codes
- **Lincoln Academy**: `LINCOLN2025` (Professional plan)
- **Global Language Institute**: `GLI2025` (Enterprise plan)
- **StartUp Language School**: `STARTUP2025` (Starter plan)

### Test Emails
- `sarah.johnson@lincoln-academy.edu` (Tutor)
- `michael.chen@lincoln-academy.edu` (Tutor)
- `maria.lopez@gli.org` (Tutor)
- `new.learner@example.com` (Pending learner invitation)
- `pending.tutor@lincoln-academy.edu` (Pending tutor invitation)

## Development Workflow

### Initial Setup
```bash
# 1. Set up collections and indexes
python scripts/setup_institutional_db.py

# 2. Seed with test data
python scripts/seed_institutional_data.py

# 3. Verify data was created
python scripts/verify_seed_data.py
```

### Reset for Testing
```bash
# Clear existing data
python scripts/clear_institutional_data.py

# Re-seed fresh data
python scripts/seed_institutional_data.py
```

## Safety Notes

- ✅ **Safe for development**: Scripts only affect institutional collections
- ✅ **Isolated data**: No interference with existing user/learning data
- ✅ **Environment-aware**: Uses `.env` file for database configuration
- ⚠️ **Development only**: Never run seed/clear scripts in production
- ⚠️ **Backup first**: Consider backing up data before clearing in development

## Environment Variables

Scripts automatically load from `.env` file:
- `MONGODB_URL`: Database connection string
- `DATABASE_NAME`: Database name (defaults to "language_tutor")

## Troubleshooting

### Connection Issues
- Verify MongoDB is running and accessible
- Check `MONGODB_URL` in `.env` file
- Ensure network connectivity to database

### Permission Issues
- Scripts need read access to `.env` file
- Database user must have read/write permissions on institutional collections

### Data Verification
- Use `verify_seed_data.py` to check data integrity
- Check MongoDB directly if scripts report issues
