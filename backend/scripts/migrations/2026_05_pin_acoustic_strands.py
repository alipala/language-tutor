"""
Migration: 2026_05_pin_acoustic_strands.py
S3.1 — Fix Acoustic Strand Drift

For each speaking_dna_profiles document, find the most recent acoustic source
(latest voice_check session or baseline assessment) and recompute Rhythm,
Confidence, and Emotional from that source. Leaves Vocabulary, Accuracy,
Learning untouched.

Usage:
    python 2026_05_pin_acoustic_strands.py --dry-run          # default — logs only
    python 2026_05_pin_acoustic_strands.py --execute          # writes to DB
    python 2026_05_pin_acoustic_strands.py --user-id <uid>    # single user
    python 2026_05_pin_acoustic_strands.py --execute --user-id <uid>
"""

import asyncio
import argparse
import logging
import sys
import os

# Allow running from the scripts/migrations directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from database import database
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROFILES_COLLECTION   = database.speaking_dna_profiles
SESSIONS_COLLECTION   = database.conversation_sessions  # adjust if name differs


async def get_acoustic_source(user_id: str, language: str):
    """
    Find the most recent voice-check session that has acoustic data,
    or fall back to the baseline assessment scores.

    Returns a dict with keys: rhythm, confidence, emotional — each the
    strand sub-dict from that session's recorded strand_snapshots, or None.
    """
    # Look for voice-check sessions with strand_snapshots stored
    cursor = SESSIONS_COLLECTION.find(
        {
            "user_id": user_id,
            "language": language,
            "session_type": "voice_check",
            "strand_snapshots": {"$exists": True},
        },
        sort=[("created_at", -1)],
        limit=1,
    )
    async for session in cursor:
        snaps = session.get("strand_snapshots", {})
        if snaps.get("rhythm") or snaps.get("confidence") or snaps.get("emotional"):
            return snaps

    # Fall back: baseline assessment stored on the profile itself
    profile = await PROFILES_COLLECTION.find_one(
        {"user_id": user_id, "language": language},
        {"baseline_assessment": 1, "dna_strands": 1},
    )
    if profile and profile.get("baseline_assessment"):
        # Baseline sets all strands; return dna_strands from that era
        # (best proxy without a separate snapshot)
        return profile.get("dna_strands", {})

    return None


async def migrate(dry_run: bool, user_id_filter: str = None):
    query = {}
    if user_id_filter:
        query["user_id"] = user_id_filter

    profiles = await PROFILES_COLLECTION.find(query).to_list(length=None)
    total = len(profiles)
    updated = 0
    skipped = 0
    errors = 0

    logger.info(f"Found {total} profile(s) to process. dry_run={dry_run}")

    for profile in profiles:
        uid = profile.get("user_id")
        lang = profile.get("language", "unknown")
        profile_id = profile.get("_id")

        try:
            source = await get_acoustic_source(uid, lang)

            if not source:
                logger.info(f"SKIP user={uid} lang={lang} — no acoustic source found")
                skipped += 1
                continue

            # Build the $set payload for acoustic strands only
            set_payload = {}
            for strand in ("rhythm", "confidence", "emotional"):
                strand_data = source.get(strand)
                if strand_data:
                    set_payload[f"dna_strands.{strand}"] = strand_data

            if not set_payload:
                logger.info(f"SKIP user={uid} lang={lang} — acoustic source has no strand data")
                skipped += 1
                continue

            if dry_run:
                logger.info(f"DRY-RUN would update user={uid} lang={lang} strands={list(set_payload.keys())}")
            else:
                set_payload["updated_at"] = datetime.now(timezone.utc).isoformat()
                await PROFILES_COLLECTION.update_one(
                    {"_id": profile_id},
                    {"$set": set_payload},
                )
                logger.info(f"UPDATED user={uid} lang={lang} strands={list(set_payload.keys())}")

            updated += 1

        except Exception as e:
            logger.error(f"ERROR user={uid} lang={lang}: {e}")
            errors += 1

    logger.info(
        f"Done. total={total} updated={updated} skipped={skipped} errors={errors} dry_run={dry_run}"
    )


def main():
    parser = argparse.ArgumentParser(description="S3.1 acoustic strand drift migration")
    parser.add_argument("--dry-run",  action="store_true", default=True,  help="Log changes without writing (default)")
    parser.add_argument("--execute",  action="store_true", default=False, help="Actually write changes to DB")
    parser.add_argument("--user-id",  type=str, default=None,             help="Limit to a single user_id")
    args = parser.parse_args()

    dry_run = not args.execute
    asyncio.run(migrate(dry_run=dry_run, user_id_filter=args.user_id))


if __name__ == "__main__":
    main()
