"""
No-DB harness for daily-digest DELIVERY (cron_jobs/run_daily_digest.py).

Delivery was silently dead in production: digest docs store user_id as a STRING
while users._id is an ObjectId, so every lookup missed, every digest hit the
"user not found" path, and — because that path didn't mark the doc — the pending
queue grew forever (47 stuck docs, 0 ever sent).

These assertions pin the three properties that keep it fixed:

  1. The string user_id resolves to the ObjectId user (the original bug).
  2. EVERY terminal path marks the digest sent, so nothing re-piles.
  3. A backlog drains QUIETLY — digests past DIGEST_MAX_AGE_HOURS are retired
     unsent instead of arriving as a burst of stale pushes.

Run:  python3 test_digest_delivery_harness.py
"""

import asyncio
import importlib.util
import os
import sys
import types
from datetime import datetime, timedelta

from bson import ObjectId

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)


# ── Stubs: installed BEFORE importing the digest module ──────────────────────
# Same approach as test_reminders_harness.py. Extra reason here: importing the
# module for real pulls in services/ (Python 3.10+ syntax) and opens a Motor
# client against the production URL from .env — neither belongs in a unit test.

def _install_import_stubs():
    motor = types.ModuleType("motor")
    motor_asyncio = types.ModuleType("motor.motor_asyncio")

    class _FakeDB:
        def __getattr__(self, _name):
            return None

    class AsyncIOMotorClient:
        def __init__(self, *_a, **_kw):
            pass

        def __getitem__(self, _name):
            return _FakeDB()

        def close(self):
            pass

    motor_asyncio.AsyncIOMotorClient = AsyncIOMotorClient
    motor.motor_asyncio = motor_asyncio
    sys.modules["motor"] = motor
    sys.modules["motor.motor_asyncio"] = motor_asyncio

    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *_a, **_kw: None
    sys.modules["dotenv"] = dotenv

    services = types.ModuleType("services")
    services.__path__ = []
    generator = types.ModuleType("services.daily_digest_generator")
    generator.daily_digest_generator = object()
    services.daily_digest_generator = generator
    sys.modules["services"] = services
    sys.modules["services.daily_digest_generator"] = generator

    ns = types.ModuleType("notification_service")

    async def _unused_send(**_kw):
        raise AssertionError("install() must replace send_push_notification")

    ns.send_push_notification = _unused_send
    sys.modules["notification_service"] = ns


_install_import_stubs()

# cron_jobs has no __init__.py, so load the module straight from its path.
_spec = importlib.util.spec_from_file_location(
    "run_daily_digest", os.path.join(BACKEND_DIR, "cron_jobs", "run_daily_digest.py")
)
dd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dd)

PASS = FAIL = 0


def check(cond, label):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"✅ {label}")
    else:
        FAIL += 1
        print(f"❌ {label}")


# ── Fakes ────────────────────────────────────────────────────────────────────

class FakeDigests:
    def __init__(self, docs):
        self.docs = docs
        self.updates = {}  # _id -> update $set

    def find(self, query):
        outer = self

        class _Cursor:
            async def to_list(self, _n):
                now = query["scheduled_for"]["$lte"]
                return [d for d in outer.docs
                        if d["scheduled_for"] <= now and d["sent"] is False]

        return _Cursor()

    async def update_one(self, flt, update):
        self.updates[flt["_id"]] = update["$set"]


class FakeUsers:
    def __init__(self, docs):
        self.docs = docs
        self.queried_with = []

    async def find_one(self, query):
        self.queried_with.append(query.get("_id"))
        for d in self.docs:
            if d["_id"] == query.get("_id"):
                return d
        return None


class FakePrefs:
    def __init__(self, docs):
        self.docs = docs

    async def find_one(self, query):
        for d in self.docs:
            if d["user_id"] == query.get("user_id"):
                return d
        return None


class Pushes:
    def __init__(self):
        self.sent = []
        self.succeed = True

    async def __call__(self, push_token=None, title=None, body=None,
                       data=None, user_id=None):
        self.sent.append({"token": push_token, "title": title, "user": user_id})
        return self.succeed


def digest(_id, user_id, hours_ago, sent=False):
    return {
        "_id": _id,
        "user_id": user_id,
        "scheduled_for": datetime.utcnow() - timedelta(hours=hours_ago),
        "sent": sent,
        "message_type": "celebration",
        "subject": "Nice work!",
        "message": "You hit a 3-day streak.",
        "quick_actions": [],
    }


def install(digests, users, prefs):
    pushes = Pushes()
    dd.daily_digest_messages_collection = FakeDigests(digests)
    dd.users_collection = FakeUsers(users)
    dd.notification_preferences_collection = FakePrefs(prefs)
    dd.send_push_notification = pushes
    return pushes


# ── Cases ────────────────────────────────────────────────────────────────────

OID = ObjectId("6a537dff29636cf39c18f69b")
UID = str(OID)


def case_string_user_id_resolves():
    """The original bug: string user_id must find the ObjectId user."""
    pushes = install(
        [digest("d1", UID, hours_ago=2)],
        [{"_id": OID, "name": "Sipahi", "push_token": "ExponentPushToken[x]"}],
        [],  # no prefs doc at all -> default ON
    )
    asyncio.get_event_loop().run_until_complete(dd.send_pending_digest_messages())

    check(dd.users_collection.queried_with == [OID],
          "LOOKUP: string user_id coerced to ObjectId before querying users")
    check(len(pushes.sent) == 1, "LOOKUP: push actually delivered")
    update = dd.daily_digest_messages_collection.updates.get("d1", {})
    check(update.get("sent") is True and "skipped_reason" not in update,
          "LOOKUP: digest closed as DELIVERED, not retired with a skip reason")


def case_missing_prefs_defaults_on():
    """#3 — absence of a prefs doc means 'never chose', not 'opted out'."""
    pushes = install(
        [digest("d1", UID, hours_ago=1)],
        [{"_id": OID, "push_token": "ExponentPushToken[x]"}],
        [],
    )
    asyncio.get_event_loop().run_until_complete(dd.send_pending_digest_messages())
    check(len(pushes.sent) == 1, "DEFAULT-ON: no prefs doc still receives digest")


def case_explicit_false_still_opts_out():
    """An explicit False is a real user choice and must be honoured."""
    pushes = install(
        [digest("d1", UID, hours_ago=1)],
        [{"_id": OID, "push_token": "ExponentPushToken[x]"}],
        [{"user_id": UID, "practice_reminders_enabled": False}],
    )
    asyncio.get_event_loop().run_until_complete(dd.send_pending_digest_messages())
    check(len(pushes.sent) == 0, "OPT-OUT: explicit False suppresses the push")
    check(dd.daily_digest_messages_collection.updates["d1"]["skipped_reason"]
          == "practice_reminders_disabled",
          "OPT-OUT: retired with the opt-out reason")


def case_backlog_drains_quietly():
    """A 14-deep backlog must NOT fire as 14 pushes when delivery is restored."""
    docs = [digest(f"old{i}", UID, hours_ago=48 + i * 24) for i in range(14)]
    docs.append(digest("fresh", UID, hours_ago=2))
    pushes = install(
        docs,
        [{"_id": OID, "push_token": "ExponentPushToken[x]"}],
        [{"user_id": UID, "practice_reminders_enabled": True}],
    )
    asyncio.get_event_loop().run_until_complete(dd.send_pending_digest_messages())

    check(len(pushes.sent) == 1, "BACKLOG: only the fresh digest is pushed (1 of 15)")
    updates = dd.daily_digest_messages_collection.updates
    check(all(updates.get(f"old{i}", {}).get("skipped_reason") == "stale"
              for i in range(14)),
          "BACKLOG: all 14 stale digests retired with reason 'stale'")
    check(len(updates) == 15, "BACKLOG: every digest closed out, none left pending")


def case_terminal_paths_always_mark_sent():
    """No user / no token must still close the doc, or it re-piles forever."""
    ghost = ObjectId("6a3e6bbe89aa02261defc82b")
    pushes = install(
        [digest("gone", "6999cdfd3a60245dffe449c8", hours_ago=1),
         digest("notok", str(ghost), hours_ago=1)],
        [{"_id": ghost, "push_token": None}],
        [],
    )
    asyncio.get_event_loop().run_until_complete(dd.send_pending_digest_messages())

    updates = dd.daily_digest_messages_collection.updates
    check(len(pushes.sent) == 0, "TERMINAL: nothing pushed")
    check(updates.get("gone", {}).get("skipped_reason") == "user_not_found",
          "TERMINAL: deleted user retired (was the leak that piled 47 docs)")
    check(updates.get("notok", {}).get("skipped_reason") == "no_push_token",
          "TERMINAL: token-less user retired")


def case_send_failure_stays_pending():
    """A transient Expo failure should retry next hour, not be swallowed."""
    pushes = install(
        [digest("d1", UID, hours_ago=1)],
        [{"_id": OID, "push_token": "ExponentPushToken[x]"}],
        [{"user_id": UID, "practice_reminders_enabled": True}],
    )
    pushes.succeed = False
    asyncio.get_event_loop().run_until_complete(dd.send_pending_digest_messages())
    check("d1" not in dd.daily_digest_messages_collection.updates,
          "RETRY: failed send leaves the digest pending for the next run")


if __name__ == "__main__":
    asyncio.set_event_loop(asyncio.new_event_loop())
    for fn in (case_string_user_id_resolves,
               case_missing_prefs_defaults_on,
               case_explicit_false_still_opts_out,
               case_backlog_drains_quietly,
               case_terminal_paths_always_mark_sent,
               case_send_failure_stays_pending):
        print(f"\n--- {fn.__name__} ---")
        fn()

    print("\n" + "=" * 60)
    print(f"RESULT: {PASS}/{PASS + FAIL} assertions passed")
    print("=" * 60)
    sys.exit(1 if FAIL else 0)
