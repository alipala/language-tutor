"""
LT-1 Setup: Create 50 load-test users in production MongoDB.

Each user gets:
  - Light synthetic data: 5 conversation_sessions, 10 flashcards, 1 learning_plan
  - All documents tagged __load_test_user: true
  - 30-day JWT minted using the same signing path as auth.py

Idempotent: existing users by email get their JWTs refreshed, not recreated.

Output: /test_credentials/load_test_users.json

Run from project root:
    python load_tests/setup/create_load_test_users.py
"""
import asyncio
import hashlib
import json
import os
import secrets
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Resolve backend on path so auth.py signing logic is importable
BACKEND_DIR = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

env_file = BACKEND_DIR / ".env.local" if (BACKEND_DIR / ".env.local").exists() else BACKEND_DIR / ".env"
load_dotenv(env_file)

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from jose import jwt

# ── Config ────────────────────────────────────────────────────────────────────

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30

NUM_USERS = 50
EMAIL_TEMPLATE = "load-test-{:02d}@mytacoai.com"
LANGUAGES = ["nl", "en", "de", "fr", "es"]
LEVELS = ["A1", "A2", "B1", "B2"]

OUTPUT_PATH = Path(__file__).parent.parent.parent / "test_credentials" / "load_test_users.json"

# ── Helpers ───────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    h = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"${salt}${h}"


def mint_jwt(user_id: str, email: str) -> str:
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": user_id, "email": email, "exp": expire, "jti": str(uuid.uuid4())},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def make_user_doc(user_id: str, email: str, password_hash: str) -> dict:
    now = datetime.utcnow()
    return {
        "_id": ObjectId(user_id),
        "email": email,
        "name": f"Load Test {email.split('@')[0].split('-')[-1].lstrip('0') or '0'}",
        "hashed_password": password_hash,
        "is_active": True,
        "is_verified": True,
        "created_at": now,
        "last_login": now,
        "preferred_language": "nl",
        "preferred_level": "B1",
        "preferred_voice": "alloy",
        "subscription_plan": "try_learn",
        "subscription_period": "monthly",
        "subscription_status": None,
        "practice_minutes_used": 0.0,
        "practice_sessions_used": 0,
        "assessments_used": 0,
        "current_period_start": now,
        "current_period_end": now + timedelta(days=30),
        "timezone": "Europe/Amsterdam",
        "__load_test_user": True,
    }


def make_sessions(user_id: str, count: int = 5) -> list:
    docs = []
    for i in range(count):
        lang = LANGUAGES[i % len(LANGUAGES)]
        level = LEVELS[i % len(LEVELS)]
        created_at = datetime.utcnow() - timedelta(days=i * 7)
        docs.append({
            "_id": ObjectId(),
            "user_id": user_id,
            "language": lang,
            "level": level,
            "duration_minutes": 5,
            "created_at": created_at,
            "session_date": created_at.strftime("%Y-%m-%d"),
            "transcript": f"Load test session {i}.",
            "messages": [],
            "status": "completed",
            "__load_test_user": True,
        })
    return docs


def make_flashcard_set(user_id: str) -> dict:
    return {
        "_id": ObjectId(),
        "user_id": user_id,
        "name": "Load Test Set",
        "language": "nl",
        "created_at": datetime.utcnow(),
        "__load_test_user": True,
    }


def make_flashcards(user_id: str, set_id: str, count: int = 10) -> list:
    return [
        {
            "_id": ObjectId(),
            "user_id": user_id,
            "set_id": set_id,
            "front": f"word_{i}",
            "back": f"translation_{i}",
            "due_date": datetime.utcnow() + timedelta(days=i),
            "created_at": datetime.utcnow(),
            "__load_test_user": True,
        }
        for i in range(count)
    ]


def make_learning_plan(user_id: str) -> dict:
    plan_id = str(ObjectId())
    return {
        "_id": ObjectId(),
        "id": plan_id,
        "user_id": user_id,
        "language": "nl",
        "proficiency_level": "B1",
        "goals": ["general"],
        "duration_months": 3,
        "plan_content": {"weeks": []},
        "status": "in_progress",
        "created_at": datetime.utcnow().isoformat(),
        "completed_sessions": 0,
        "progress_percentage": 0.0,
        "weekly_progress": [
            {"week": w, "sessions_completed": 0, "minutes": 0} for w in range(4)
        ],
        "__load_test_user": True,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    if not JWT_SECRET_KEY:
        print("ERROR: JWT_SECRET_KEY not set. Cannot mint JWTs.")
        sys.exit(1)

    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
    db = client[DATABASE_NAME]

    try:
        await client.admin.command("ping")
        print(f"✓ Connected to MongoDB: {DATABASE_NAME}")
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        sys.exit(1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    users_output = []
    created = refreshed = 0

    for idx in range(1, NUM_USERS + 1):
        email = EMAIL_TEMPLATE.format(idx)
        existing = await db.users.find_one({"email": email})

        if existing:
            user_id = str(existing["_id"])
            token = mint_jwt(user_id, email)
            password = "(existing — password unchanged)"
            refreshed += 1
            print(f"  ↩  {email} exists — JWT refreshed")
        else:
            password = secrets.token_urlsafe(16)
            user_id = str(ObjectId())
            user_doc = make_user_doc(user_id, email, hash_password(password))
            await db.users.insert_one(user_doc)

            sessions = make_sessions(user_id)
            await db.conversation_sessions.insert_many(sessions)

            set_doc = make_flashcard_set(user_id)
            await db.flashcard_sets.insert_one(set_doc)
            cards = make_flashcards(user_id, str(set_doc["_id"]))
            await db.flashcards.insert_many(cards)

            plan_doc = make_learning_plan(user_id)
            await db.learning_plans.insert_one(plan_doc)

            token = mint_jwt(user_id, email)
            created += 1
            print(f"  ✓  Created {email} (id={user_id})")

        users_output.append({
            "index": idx,
            "user_id": user_id,
            "email": email,
            "password": password,
            "jwt": token,
        })

    result = {
        "created_at": datetime.utcnow().isoformat(),
        "users": users_output,
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n✓ Credentials written to {OUTPUT_PATH}")
    print(f"  Created: {created}  Refreshed: {refreshed}")
    print("\n── Verification counts ─────────────────────────────")
    print(f"  users:                 {await db.users.count_documents({'__load_test_user': True})}")
    print(f"  conversation_sessions: {await db.conversation_sessions.count_documents({'__load_test_user': True})}")
    print(f"  flashcards:            {await db.flashcards.count_documents({'__load_test_user': True})}")
    print(f"  learning_plans:        {await db.learning_plans.count_documents({'__load_test_user': True})}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
