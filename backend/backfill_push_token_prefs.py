"""
Backfill notification_preferences for users who already hold a push token.

WHY
---
Every reminder trigger (practice / news / story / learning-plan) opens its loop
with `notification_preferences_collection.find(...)`. A user with no document is
never iterated, so the code-level "default ON" never applies to them. The doc
used to be created only by GET /api/preferences/notifications — i.e. only if the
user opened the Notification Settings screen.

auth_routes._ensure_notification_preferences now creates the doc when a push
token is registered, which self-heals anyone who opens the app. But the users we
most want to re-engage are precisely the ones who DON'T open the app, so they
need a one-off backfill. This is that script.

SAFETY
------
  * Dry-run by default. Pass --apply to write.
  * Only ever INSERTS. An existing document is left completely untouched, so a
    choice made on the settings screen can never be overwritten.
  * Seeds the real timezone from users.timezone when known; otherwise leaves it
    unset so the triggers' UTC fallback applies and a later fix can still tell
    "unknown" apart from "explicitly UTC".

Run:
    python backfill_push_token_prefs.py            # dry run, prints the plan
    python backfill_push_token_prefs.py --apply    # actually insert
"""

import argparse
import asyncio
import os
import sys

import pytz
from bson import ObjectId
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from models import NotificationPreferencesInDB  # noqa: E402

# Must match auth_routes._ensure_notification_preferences. 18:00 is 19:00-21:00
# across the EU/TR user base when the timezone is unknown and the hour is read
# as UTC; 10:00 would land at 02:00-05:00 in the US.
DEFAULT_HOUR = 18


def _resolve_timezone(user):
    tz = user.get("timezone")
    if not tz:
        return None
    try:
        pytz.timezone(tz)
        return tz
    except Exception:
        return None


async def main(apply_changes: bool):
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("DATABASE_NAME", "language_tutor")]

    users_collection = db.users
    prefs_collection = db.notification_preferences

    token_users = await users_collection.find(
        {"push_token": {"$exists": True, "$ne": None}}
    ).to_list(None)

    existing_ids = {
        d["user_id"]
        for d in await prefs_collection.find({}, {"user_id": 1}).to_list(None)
    }

    missing = [u for u in token_users if str(u["_id"]) not in existing_ids]

    mode = "APPLY" if apply_changes else "DRY RUN"
    print(f"\n=== Backfill notification_preferences [{mode}] ===")
    print(f"users with a push token      : {len(token_users)}")
    print(f"already have a prefs doc     : {len(token_users) - len(missing)}")
    print(f"to create                    : {len(missing)}\n")

    if not missing:
        print("Nothing to do.")
        client.close()
        return

    created = 0
    for user in missing:
        user_id = str(user["_id"])
        tz = _resolve_timezone(user)
        email = user.get("email", "?")
        print(f"  {'CREATE' if apply_changes else 'would create'}  "
              f"{email[:34]:36} timezone={tz or 'unset (UTC fallback)'}")

        if not apply_changes:
            continue

        defaults = NotificationPreferencesInDB(
            user_id=user_id,
            timezone=tz,
            preferred_notification_time=DEFAULT_HOUR,
        )
        # $setOnInsert + upsert: a doc created between the read above and this
        # write (e.g. the user just opened the app) wins and is not clobbered.
        result = await prefs_collection.update_one(
            {"user_id": user_id},
            {"$setOnInsert": defaults.model_dump(by_alias=True)},
            upsert=True,
        )
        if result.upserted_id is not None:
            created += 1

    print(f"\n{'Created' if apply_changes else 'Would create'}: "
          f"{created if apply_changes else len(missing)} document(s)")
    if not apply_changes:
        print("Re-run with --apply to write.")

    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="actually write (default is a dry run)")
    args = parser.parse_args()
    asyncio.run(main(args.apply))
