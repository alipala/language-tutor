#!/usr/bin/env python3
"""
Scheduled Monitoring for Railway Deployment
Alternative to cron jobs - can be triggered via Railway's scheduled tasks or external services
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
import logging

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from duration_monitoring import run_daily_monitoring

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """
    Main entry point for scheduled monitoring
    Can be called by:
    1. Railway Cron (if available in your plan)
    2. External cron service (like cron-job.org)
    3. GitHub Actions scheduled workflow
    4. Manual execution for testing
    """
    try:
        logger.info("🔍 Starting scheduled duration monitoring...")
        
        # Run the daily monitoring
        health_report = await run_daily_monitoring()
        
        # Log completion
        status = health_report.get('overall_status', 'unknown')
        issues_count = len(health_report.get('issues_found', []))
        warnings_count = len(health_report.get('warnings', []))
        
        logger.info(f"✅ Monitoring completed - Status: {status}, Issues: {issues_count}, Warnings: {warnings_count}")
        
        # Exit with appropriate code
        if status == 'critical':
            sys.exit(1)  # Non-zero exit for critical issues
        elif status == 'warning':
            sys.exit(0)  # Success but with warnings
        else:
            sys.exit(0)  # All good
            
    except Exception as e:
        logger.error(f"❌ Scheduled monitoring failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
