#!/usr/bin/env python3
"""
MIGRATION: Add Final Assessment Fields to Learning Plans
=========================================================

This migration adds the final assessment requirement fields to ALL incomplete learning plans.

IMPORTANT:
- Only affects learning plans where progress_percentage < 100
- Does NOT touch already completed plans (progress_percentage == 100)
- Applies to all future learning plan completions

Fields Added:
- status: "in_progress" | "awaiting_final_assessment" | "completed" | "failed_assessment"
- final_assessment: object with assessment requirements and attempts
- all_sessions_completed_at: timestamp when user finishes last session

Run this migration ONCE before deploying the final assessment feature.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any
from pymongo import UpdateOne
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def calculate_assessment_duration(proficiency_level: str) -> int:
    """
    Calculate required assessment duration based on proficiency level.

    Returns duration in minutes:
    - A1: 2 minutes
    - A2: 3 minutes
    - B1: 4 minutes
    - B2+: 5 minutes
    """
    level_upper = proficiency_level.upper()

    duration_map = {
        'A1': 2,
        'A2': 3,
        'B1': 4,
        'B2': 5,
        'C1': 5,
        'C2': 5
    }

    return duration_map.get(level_upper, 3)  # Default to 3 minutes if unknown


async def get_learning_plan_status(progress_percentage: float, completed_sessions: int, total_sessions: int) -> str:
    """
    Determine the correct status for a learning plan.

    Returns:
    - "in_progress": Plan is active, not all sessions completed
    - "completed": Plan is already at 100% (don't touch these!)
    """
    if progress_percentage >= 100 or completed_sessions >= total_sessions:
        return "completed"  # Already finished, leave as-is
    else:
        return "in_progress"  # Active plan


async def migrate_learning_plans(dry_run: bool = True):
    """
    Migrate incomplete learning plans to include final assessment fields.

    Args:
        dry_run: If True, only logs what would be done without making changes
    """
    try:
        from database import database

        learning_plans_collection = database.learning_plans

        logger.info("=" * 80)
        logger.info("FINAL ASSESSMENT MIGRATION - Starting")
        logger.info("=" * 80)
        logger.info(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (applying changes)'}")
        logger.info("")

        # Count total learning plans
        total_plans = await learning_plans_collection.count_documents({})
        logger.info(f"Total learning plans in database: {total_plans}")

        # Find incomplete learning plans (progress < 100%)
        # Only migrate plans that don't already have final_assessment field
        incomplete_plans = await learning_plans_collection.find({
            "$and": [
                {"progress_percentage": {"$lt": 100}},
                {"final_assessment": {"$exists": False}}
            ]
        }).to_list(length=None)

        logger.info(f"Incomplete plans needing migration: {len(incomplete_plans)}")

        # Find already completed plans (for info only)
        completed_plans_count = await learning_plans_collection.count_documents({
            "progress_percentage": {"$gte": 100}
        })
        logger.info(f"Already completed plans (will NOT touch): {completed_plans_count}")
        logger.info("")

        if len(incomplete_plans) == 0:
            logger.info("✅ No incomplete plans to migrate. All done!")
            return

        # Prepare bulk updates
        bulk_operations = []
        migration_stats = {
            "in_progress": 0,
            "errors": 0
        }

        logger.info("Processing incomplete learning plans...")
        logger.info("")

        for plan in incomplete_plans:
            try:
                plan_id = plan.get("id")
                user_id = plan.get("user_id")
                language = plan.get("language", "unknown")
                level = plan.get("proficiency_level", "A1")
                progress = plan.get("progress_percentage", 0)
                completed = plan.get("completed_sessions", 0)
                total = plan.get("total_sessions", 0)

                # Calculate status
                status = await get_learning_plan_status(progress, completed, total)

                # Calculate assessment duration requirement
                assessment_duration = await calculate_assessment_duration(level)

                # Create final_assessment object
                final_assessment = {
                    "required": True,
                    "completed": False,
                    "attempts": [],
                    "minimum_duration_minutes": assessment_duration,
                    "passed": False,
                    "last_attempt_date": None
                }

                # Prepare update
                update_doc = {
                    "$set": {
                        "status": status,
                        "final_assessment": final_assessment,
                        "all_sessions_completed_at": None,  # Will be set when last session completes
                        "migration_timestamp": datetime.utcnow().isoformat()
                    }
                }

                bulk_operations.append(
                    UpdateOne(
                        {"_id": plan["_id"]},
                        update_doc
                    )
                )

                migration_stats[status] += 1

                logger.info(f"✓ Plan {plan_id[:8]}... | User: {user_id[:8] if user_id else 'None'}... | "
                          f"{language.title()} {level} | Progress: {progress}% ({completed}/{total}) | "
                          f"Status: {status} | Assessment: {assessment_duration}min")

            except Exception as e:
                logger.error(f"✗ Error processing plan {plan.get('id', 'unknown')}: {str(e)}")
                migration_stats["errors"] += 1
                continue

        logger.info("")
        logger.info("=" * 80)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total plans processed: {len(incomplete_plans)}")
        logger.info(f"  - In progress: {migration_stats['in_progress']}")
        logger.info(f"  - Errors: {migration_stats['errors']}")
        logger.info(f"Already completed (not touched): {completed_plans_count}")
        logger.info("")

        # Execute bulk write
        if not dry_run and len(bulk_operations) > 0:
            logger.info("Applying changes to database...")
            result = await learning_plans_collection.bulk_write(bulk_operations, ordered=False)
            logger.info(f"✅ Successfully updated {result.modified_count} learning plans")
        elif dry_run:
            logger.info("🔍 DRY RUN - No changes made to database")
            logger.info("   Run with --live flag to apply changes")
        else:
            logger.info("⚠️  No operations to perform")

        logger.info("")
        logger.info("=" * 80)
        logger.info("MIGRATION COMPLETE")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ MIGRATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def verify_migration():
    """
    Verify the migration was successful by checking a sample of plans.
    """
    try:
        from database import database

        learning_plans_collection = database.learning_plans

        logger.info("")
        logger.info("=" * 80)
        logger.info("VERIFICATION")
        logger.info("=" * 80)

        # Check incomplete plans have final_assessment
        incomplete_with_assessment = await learning_plans_collection.count_documents({
            "$and": [
                {"progress_percentage": {"$lt": 100}},
                {"final_assessment": {"$exists": True}}
            ]
        })

        incomplete_without_assessment = await learning_plans_collection.count_documents({
            "$and": [
                {"progress_percentage": {"$lt": 100}},
                {"final_assessment": {"$exists": False}}
            ]
        })

        # Check completed plans were not touched
        completed_with_assessment = await learning_plans_collection.count_documents({
            "$and": [
                {"progress_percentage": {"$gte": 100}},
                {"final_assessment": {"$exists": True}}
            ]
        })

        completed_without_assessment = await learning_plans_collection.count_documents({
            "$and": [
                {"progress_percentage": {"$gte": 100}},
                {"final_assessment": {"$exists": False}}
            ]
        })

        logger.info(f"Incomplete plans WITH final_assessment: {incomplete_with_assessment} ✓")
        logger.info(f"Incomplete plans WITHOUT final_assessment: {incomplete_without_assessment}")
        logger.info(f"Completed plans WITH final_assessment: {completed_with_assessment}")
        logger.info(f"Completed plans WITHOUT final_assessment: {completed_without_assessment} ✓")
        logger.info("")

        if incomplete_without_assessment == 0 and completed_without_assessment > 0:
            logger.info("✅ Migration verified successfully!")
            logger.info("   - All incomplete plans have final_assessment field")
            logger.info("   - Completed plans were not modified")
        elif incomplete_without_assessment > 0:
            logger.warning(f"⚠️  {incomplete_without_assessment} incomplete plans still missing final_assessment")

        # Show sample plan
        sample = await learning_plans_collection.find_one({
            "$and": [
                {"progress_percentage": {"$lt": 100}},
                {"final_assessment": {"$exists": True}}
            ]
        })

        if sample:
            logger.info("")
            logger.info("Sample migrated plan:")
            logger.info(f"  ID: {sample.get('id')}")
            logger.info(f"  Language: {sample.get('language')}")
            logger.info(f"  Level: {sample.get('proficiency_level')}")
            logger.info(f"  Status: {sample.get('status')}")
            logger.info(f"  Final Assessment: {sample.get('final_assessment')}")

        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Main entry point for migration script."""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate learning plans to include final assessment')
    parser.add_argument('--live', action='store_true', help='Apply changes (default is dry-run)')
    parser.add_argument('--verify', action='store_true', help='Verify migration results')

    args = parser.parse_args()

    if args.verify:
        await verify_migration()
    else:
        dry_run = not args.live
        await migrate_learning_plans(dry_run=dry_run)

        if args.live:
            # Auto-verify after live migration
            await verify_migration()


if __name__ == "__main__":
    asyncio.run(main())
