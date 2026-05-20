"""
LT Cleanup: Delete all load-test data from production MongoDB and Redis.

Tags targeted:
  MongoDB: __load_test_user: true  (top-level boolean on every created doc)
  Redis:   "test:*", "ratelimit:*load-test-*"

Usage:
    python load_tests/setup/cleanup_load_test_data.py            # interactive y/N prompt
    python load_tests/setup/cleanup_load_test_data.py --dry-run  # show counts, delete nothing

Run from project root.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

env_file = BACKEND_DIR / ".env.local" if (BACKEND_DIR / ".env.local").exists() else BACKEND_DIR / ".env"
load_dotenv(env_file)

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import redis.asyncio as aioredis

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")
REDIS_URL = os.getenv("REDIS_URL")

CREDENTIALS_PATH = Path(__file__).parent.parent.parent / "test_credentials" / "load_test_users.json"

MONGO_COLLECTIONS = [
    "users", "conversation_sessions", "flashcards", "flashcard_sets",
    "learning_plans", "daily_stats", "challenge_sessions", "realtime_usage_logs",
    "assessments", "sentence_analysis_jobs", "session_feedback",
    "speaking_dna_profiles", "speaking_dna_history", "speaking_breakthroughs",
    "heart_events", "speaking_time_tracking", "recent_performance",
    "journey_checkpoints", "recommended_actions", "daily_digest_messages",
]

REDIS_PATTERNS = ["test:*", "ratelimit:*load-test-*"]


async def main():
    dry_run = "--dry-run" in sys.argv
    mode = "DRY RUN" if dry_run else "LIVE DELETE"
    print(f"=== Load Test Cleanup [{mode}] ===\n")

    # Load user IDs for targeted cleanup
    load_test_user_ids = []
    if CREDENTIALS_PATH.exists():
        with open(CREDENTIALS_PATH) as f:
            creds = json.load(f)
        load_test_user_ids = [u["user_id"] for u in creds["users"]]
        print(f"Loaded {len(load_test_user_ids)} load-test user IDs from credentials file.")
    else:
        print("Warning: credentials file not found — relying on __load_test_user flag only.")

    if not dry_run:
        answer = input("\n⚠️  This will permanently delete all load-test data. Type 'DELETE LOAD TEST DATA' to confirm: ").strip()
        if answer != "DELETE LOAD TEST DATA":
            print("Aborted.")
            sys.exit(0)

    # ── MongoDB cleanup ───────────────────────────────────────────────────────
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
    db = client[DATABASE_NAME]

    try:
        await client.admin.command("ping")
        print(f"\n✓ Connected to MongoDB: {DATABASE_NAME}")
    except Exception as e:
        print(f"✗ MongoDB failed: {e}")
        sys.exit(1)

    total_mongo = 0
    for col_name in MONGO_COLLECTIONS:
        col = db[col_name]
        if col_name == "users" and load_test_user_ids:
            obj_ids = []
            for uid in load_test_user_ids:
                try:
                    obj_ids.append(ObjectId(uid))
                except Exception:
                    pass
            filt = {"$or": [{"__load_test_user": True}, {"_id": {"$in": obj_ids}}]}
        else:
            filt = {"$or": [{"__load_test_user": True}, {"user_id": {"$in": load_test_user_ids}}]} \
                   if load_test_user_ids else {"__load_test_user": True}

        count = await col.count_documents(filt)
        if count:
            if dry_run:
                print(f"  [DRY RUN] {col_name}: would delete {count}")
            else:
                result = await col.delete_many(filt)
                print(f"  {col_name}: deleted {result.deleted_count}")
                total_mongo += result.deleted_count

    if not dry_run:
        print(f"\nTotal MongoDB documents deleted: {total_mongo}")

    client.close()

    # ── Redis cleanup ─────────────────────────────────────────────────────────
    if not REDIS_URL:
        print("\nRedis URL not set — skipping Redis cleanup.")
        return

    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        await r.ping()
        print("\n✓ Connected to Redis")
    except Exception as e:
        print(f"\n✗ Redis connection failed: {e}")
        await r.aclose()
        return

    total_redis = 0
    for pattern in REDIS_PATTERNS:
        cursor = 0
        keys_found = []
        while True:
            cursor, keys = await r.scan(cursor=cursor, match=pattern, count=200)
            keys_found.extend(keys)
            if cursor == 0:
                break
        if keys_found:
            if dry_run:
                print(f"  [DRY RUN] Redis pattern '{pattern}': would delete {len(keys_found)} keys")
            else:
                await r.delete(*keys_found)
                print(f"  Redis pattern '{pattern}': deleted {len(keys_found)} keys")
                total_redis += len(keys_found)

    if not dry_run:
        print(f"Total Redis keys deleted: {total_redis}")

    await r.aclose()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
