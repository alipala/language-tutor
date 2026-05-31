"""
Migration: 2026_05_pin_learning_strand.py
S3.2 — Fix Learning Strand Degeneracy (Option A)

For each speaking_dna_profiles document, recompute the Learning strand from
the user's actual challenge history. If a user has zero historical challenges,
sets Learning to a neutral default (challenge_acceptance=0.5, retry_rate=0.5).

Usage:
    python 2026_05_pin_learning_strand.py --dry-run          # default — logs only
    python 2026_05_pin_learning_strand.py --execute          # writes to DB
    python 2026_05_pin_learning_strand.py --user-id <uid>    # single user
    python 2026_05_pin_learning_strand.py --execute --user-id <uid>
"""

import asyncio
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from database import database
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROFILES_COLLECTION = database.speaking_dna_profiles
SESSIONS_COLLECTION = database.conversation_sessions  # adjust if name differs

NEUTRAL_LEARNING = {
    "type": "persistent",
    "retry_rate": 0.5,
    "challenge_acceptance": 0.5,
    "description": "Learns through repetition, prefers mastery before moving on",
}


async def compute_learning_from_history(user_id: str, language: str) -> dict:
    """
    Aggregate challenge counters across all stored sessions for this user+language
    and derive a Learning strand value. Returns NEUTRAL_LEARNING if no challenge
    history exists.
    """
    total_offered  = 0
    total_accepted = 0

    cursor = SESSIONS_COLLECTION.find(
        {"user_id": user_id, "language": language},
        {"challenges_offered": 1, "challenges_accepted": 1},
    )
    async for session in cursor:
        total_offered  += session.get("challenges_offered",  0)
        total_accepted += session.get("challenges_accepted", 0)

    if total_offered == 0:
        return NEUTRAL_LEARNING

    challenge_acceptance = round(total_accepted / total_offered, 2)

    if challenge_acceptance > 0.7:
        learning_type = "explorer"
        description   = "Embraces challenges, learns through exploration"
    elif challenge_acceptance < 0.3:
        learning_type = "cautious"
        description   = "Prefers gradual progression, builds strong foundations"
    else:
        learning_type = "persistent"
        description   = "Learns through repetition, prefers mastery before moving on"

    return {
        "type":                 learning_type,
        "retry_rate":           0.5,  # retry_rate has no historical aggregate — reset to neutral
        "challenge_acceptance": challenge_acceptance,
        "description":          description,
    }


async def migrate(dry_run: bool, user_id_filter: str = None):
    query = {}
    if user_id_filter:
        query["user_id"] = user_id_filter

    profiles = await PROFILES_COLLECTION.find(query).to_list(length=None)
    total   = len(profiles)
    updated = 0
    errors  = 0

    logger.info(f"Found {total} profile(s) to process. dry_run={dry_run}")

    for profile in profiles:
        uid        = profile.get("user_id")
        lang       = profile.get("language", "unknown")
        profile_id = profile.get("_id")
        current    = profile.get("dna_strands", {}).get("learning", {})

        try:
            recomputed = await compute_learning_from_history(uid, lang)

            if dry_run:
                logger.info(
                    f"DRY-RUN user={uid} lang={lang} "
                    f"current_acceptance={current.get('challenge_acceptance')} "
                    f"recomputed_acceptance={recomputed['challenge_acceptance']}"
                )
            else:
                await PROFILES_COLLECTION.update_one(
                    {"_id": profile_id},
                    {"$set": {
                        "dna_strands.learning": recomputed,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }},
                )
                logger.info(
                    f"UPDATED user={uid} lang={lang} "
                    f"challenge_acceptance={recomputed['challenge_acceptance']}"
                )

            updated += 1

        except Exception as e:
            logger.error(f"ERROR user={uid} lang={lang}: {e}")
            errors += 1

    logger.info(f"Done. total={total} updated={updated} errors={errors} dry_run={dry_run}")


def main():
    parser = argparse.ArgumentParser(description="S3.2 learning strand degeneracy migration")
    parser.add_argument("--dry-run",  action="store_true", default=True,  help="Log changes without writing (default)")
    parser.add_argument("--execute",  action="store_true", default=False, help="Actually write changes to DB")
    parser.add_argument("--user-id",  type=str, default=None,             help="Limit to a single user_id")
    args = parser.parse_args()

    dry_run = not args.execute
    asyncio.run(migrate(dry_run=dry_run, user_id_filter=args.user_id))


if __name__ == "__main__":
    main()
