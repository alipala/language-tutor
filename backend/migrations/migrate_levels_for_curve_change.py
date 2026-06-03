#!/usr/bin/env python3
"""
Migration: Recompute `stats.lifetime.level` under the new XP curve.

Context — XP rebalance PR2 (single-source XP + speaking buff + XP-based
daily goal) flips `LEVEL_XP_DIVISOR` in services/progression.py from 100
to 35 so progression feels rewarding under the new per-answer XP. The
levels persisted on each user (`stats.lifetime.level`) were derived under
the old divisor and now under-represent each user by 1–2+ levels.

This script:
  1. Reads every user with a populated `stats.lifetime.total_xp`.
  2. Recomputes their level from existing XP under the NEW curve.
     **XP is left untouched** — only the derived level is re-bucketed.
  3. Prints a before/after table for review.
  4. Writes the new level only when invoked with `--apply` (default is
     a dry-run; nothing is changed and the script exits 0).

Usage:
    # Dry-run (default — prints the table, writes nothing):
    python backend/migrations/migrate_levels_for_curve_change.py

    # Apply the recomputed levels after review:
    python backend/migrations/migrate_levels_for_curve_change.py --apply

    # Scope to one user (works for both dry-run and --apply):
    python backend/migrations/migrate_levels_for_curve_change.py --user-email alice@example.com
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

from bson import ObjectId

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import database
from services.progression import compute_level


async def fetch_targets(user_email: Optional[str]) -> list:
    users_collection = database.users
    query: dict = {"stats.lifetime.total_xp": {"$exists": True}}
    if user_email:
        query["email"] = user_email
    projection = {
        "_id": 1,
        "email": 1,
        "stats.lifetime.total_xp": 1,
        "stats.lifetime.level": 1,
    }
    cursor = users_collection.find(query, projection).sort("stats.lifetime.total_xp", -1)
    return await cursor.to_list(length=None)


def _row(user: dict) -> dict:
    total_xp = int(
        (user.get("stats", {}) or {}).get("lifetime", {}).get("total_xp", 0) or 0
    )
    old_level = (user.get("stats", {}) or {}).get("lifetime", {}).get("level")
    new_level = compute_level(total_xp)
    return {
        "user_id": str(user["_id"]),
        "email": user.get("email", "(no email)"),
        "total_xp": total_xp,
        "old_level": old_level if isinstance(old_level, int) else "—",
        "new_level": new_level,
        "delta": (
            new_level - old_level
            if isinstance(old_level, int)
            else "(new)"
        ),
    }


def _print_table(rows: list) -> None:
    print()
    print(
        f"{'user_id':<26} {'email':<32} {'total_xp':>10} "
        f"{'old':>4} {'new':>4} {'Δ':>4}"
    )
    print("-" * 86)
    for r in rows:
        print(
            f"{r['user_id']:<26} {r['email']:<32} {r['total_xp']:>10} "
            f"{str(r['old_level']):>4} {str(r['new_level']):>4} {str(r['delta']):>4}"
        )
    print("-" * 86)
    bumped = sum(
        1
        for r in rows
        if isinstance(r["delta"], int) and r["delta"] > 0
    )
    unchanged = sum(
        1
        for r in rows
        if isinstance(r["delta"], int) and r["delta"] == 0
    )
    print(f"  {len(rows)} users · {bumped} bumped up · {unchanged} unchanged")
    print()


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recompute users.stats.lifetime.level under the new XP curve."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist the recomputed levels. Default is a dry-run (no writes).",
    )
    parser.add_argument(
        "--user-email",
        type=str,
        default=None,
        help="Scope to a single user (email).",
    )
    args = parser.parse_args()

    users = await fetch_targets(args.user_email)
    if not users:
        print("No users with stats.lifetime.total_xp found.")
        return

    rows = [_row(u) for u in users]
    _print_table(rows)

    if not args.apply:
        print("Dry-run only — no levels were written. Re-run with --apply to persist.")
        return

    users_collection = database.users
    written = 0
    for u, r in zip(users, rows):
        if r["new_level"] == r["old_level"]:
            continue  # no-op
        result = await users_collection.update_one(
            {"_id": ObjectId(r["user_id"])},
            {"$set": {"stats.lifetime.level": r["new_level"]}},
        )
        if result.modified_count > 0:
            written += 1
            print(
                f"  updated {r['email']} ({r['user_id']}): "
                f"level {r['old_level']} → {r['new_level']} "
                f"(total_xp={r['total_xp']})"
            )
    print()
    print(f"Done. {written} user(s) updated.")


if __name__ == "__main__":
    asyncio.run(main())
