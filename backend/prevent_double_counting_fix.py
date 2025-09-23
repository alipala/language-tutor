#!/usr/bin/env python3
"""
PERMANENT FIX TO PREVENT DOUBLE COUNTING

Root Cause Analysis:
1. stripe_routes.py has /track-speaking-time endpoint
2. conversation_help.py calls track_speaking_time when session completes
3. learning_routes.py calls track_speaking_time when saving session summary

Solution: Add idempotency to prevent the same session from being counted multiple times
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# The files that need to be fixed
FILES_TO_FIX = [
    'conversation_help.py',
    'learning_routes.py',
    'stripe_routes.py'
]

def analyze_double_counting_sources():
    """Analyze where double counting is happening"""
    
    logger.info("=" * 80)
    logger.info("🔍 ANALYZING DOUBLE COUNTING SOURCES")
    logger.info("=" * 80)
    
    issues = []
    
    # 1. conversation_help.py
    logger.info("\n1️⃣ conversation_help.py:")
    logger.info("   - track_help_usage() calls track_speaking_time")
    logger.info("   - Called when help_type='session_completed'")
    logger.info("   ⚠️ ISSUE: This tracks the session")
    issues.append("conversation_help.py: track_help_usage with session_completed")
    
    # 2. learning_routes.py  
    logger.info("\n2️⃣ learning_routes.py:")
    logger.info("   - save_session_summary() calls track_speaking_time")
    logger.info("   - Called when saving learning plan sessions")
    logger.info("   ⚠️ ISSUE: This ALSO tracks the session")
    issues.append("learning_routes.py: save_session_summary")
    
    # 3. stripe_routes.py
    logger.info("\n3️⃣ stripe_routes.py:")
    logger.info("   - /track-speaking-time endpoint")
    logger.info("   - Called directly from frontend")
    logger.info("   ⚠️ ISSUE: This ALSO tracks the session")
    issues.append("stripe_routes.py: /track-speaking-time endpoint")
    
    logger.info("\n" + "=" * 80)
    logger.info("❌ PROBLEM: Same session tracked from MULTIPLE places!")
    logger.info("=" * 80)
    
    return issues

def propose_solution():
    """Propose the solution to fix double counting"""
    
    logger.info("\n" + "=" * 80)
    logger.info("💡 PROPOSED SOLUTION")
    logger.info("=" * 80)
    
    logger.info("""
SOLUTION: Implement Session Tracking Idempotency

1. Add a 'tracking_id' to each session
2. Store tracked session IDs in user record or separate collection
3. Before tracking, check if session was already tracked
4. Only track if not already tracked

IMPLEMENTATION PLAN:

1. IMMEDIATE FIX (for now):
   - Disable tracking in conversation_help.py (it's redundant)
   - Keep tracking only in ONE place (stripe_routes.py)
   
2. LONG-TERM FIX:
   - Add session_tracking collection
   - Store: {user_id, session_id, tracked_at, minutes, source}
   - Check before tracking to prevent duplicates

WHICH TRACKING TO KEEP:
- Keep: stripe_routes.py /track-speaking-time (primary endpoint)
- Disable: conversation_help.py track_help_usage for sessions
- Disable: learning_routes.py duplicate tracking
""")

def generate_fix_code():
    """Generate the code to fix the issue"""
    
    logger.info("\n" + "=" * 80)
    logger.info("🔧 FIX TO APPLY")
    logger.info("=" * 80)
    
    fix_code = """
# FIX 1: conversation_help.py
# Comment out the subscription tracking in track_help_usage
# Line ~280-300 in track_help_usage function

# BEFORE:
if duration_minutes > 0 and help_type in ["session_completed", "conversation_ended"]:
    tracking_success = await SubscriptionService.track_speaking_time(speaking_time_request)

# AFTER:
# DISABLED TO PREVENT DOUBLE COUNTING - Tracking happens in stripe_routes.py
# if duration_minutes > 0 and help_type in ["session_completed", "conversation_ended"]:
#     # tracking_success = await SubscriptionService.track_speaking_time(speaking_time_request)
#     tracking_success = True  # Assume success without actually tracking

# FIX 2: learning_routes.py  
# In save_session_summary function, disable the duplicate tracking
# Line ~1000-1020

# BEFORE:
tracking_success = await SubscriptionService.track_speaking_time(speaking_time_request)

# AFTER:
# DISABLED TO PREVENT DOUBLE COUNTING - Tracking happens via main endpoint
# tracking_success = await SubscriptionService.track_speaking_time(speaking_time_request)
tracking_success = True  # Assume success without duplicate tracking

# FIX 3: Keep stripe_routes.py /track-speaking-time as the SINGLE source of truth
# This is the primary endpoint that should handle ALL tracking
"""
    
    logger.info(fix_code)
    
    return fix_code

async def main():
    """Main function"""
    
    # Analyze the problem
    issues = analyze_double_counting_sources()
    
    # Propose solution
    propose_solution()
    
    # Generate fix
    generate_fix_code()
    
    logger.info("\n" + "=" * 80)
    logger.info("📋 SUMMARY")
    logger.info("=" * 80)
    logger.info("""
PROBLEM: Multiple endpoints tracking the same session
CAUSE: No idempotency check before tracking
SOLUTION: Disable redundant tracking, keep single source of truth

IMMEDIATE ACTION:
1. Disable tracking in conversation_help.py
2. Disable duplicate tracking in learning_routes.py  
3. Keep only stripe_routes.py /track-speaking-time

RESULT: Each session tracked ONCE only
""")

if __name__ == "__main__":
    asyncio.run(main())
