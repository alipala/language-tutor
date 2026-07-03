"""
Standalone test harness for the smart reminder system.

Runs WITHOUT a live MongoDB: we stub the `database` module with in-memory fake
async collections and a stub notification_service, then import the triggers and
drive them through happy / negative / edge scenarios.

Focus = RISK MITIGATION:
  - spam control (weekly cap, per-kind daily dedup, quiet hours, precedence)
  - correct timezone / time-window gating
  - opt-out respected
  - no-crash on malformed / missing data
  - budget bookkeeping integrity (record only on success, week rollover)

Run: python test_reminders_harness.py
Exit code 0 = all passed.
"""

import sys
import types
import asyncio
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# Fake async Mongo collections
# ─────────────────────────────────────────────────────────────────────────────

class FakeCursor:
    def __init__(self, docs, sort_key=None):
        self._docs = list(docs)
        if sort_key:
            field, direction = sort_key
            self._docs.sort(key=lambda d: d.get(field) or datetime.min.replace(tzinfo=timezone.utc),
                            reverse=(direction < 0))

    def sort(self, field, direction):
        self._docs.sort(
            key=lambda d: d.get(field) or datetime.min,
            reverse=(direction < 0),
        )
        return self

    def __aiter__(self):
        async def gen():
            for d in self._docs:
                yield d
        return gen()


def _matches(doc, query):
    for k, v in query.items():
        if isinstance(v, dict) and "$gte" in v:
            if doc.get(k) is None or doc.get(k) < v["$gte"]:
                return False
        else:
            if doc.get(k) != v:
                return False
    return True


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = docs or []
        self.updates = []  # record update_one calls for assertions

    def find(self, query=None, projection=None):
        query = query or {}
        matched = [d for d in self.docs if _matches(d, query)]
        return FakeCursor(matched)

    async def find_one(self, query, projection=None, sort=None):
        matched = [d for d in self.docs if _matches(d, query)]
        if sort:
            field, direction = sort[0]
            matched.sort(key=lambda d: d.get(field) or datetime.min.replace(tzinfo=timezone.utc),
                         reverse=(direction < 0))
        return matched[0] if matched else None

    async def update_one(self, query, update):
        self.updates.append((query, update))
        # apply $set so record_send round-trips (weekly counter etc.)
        for d in self.docs:
            if _matches(d, query):
                if "$set" in update:
                    for k, val in update["$set"].items():
                        if "." in k:
                            parts = k.split(".")
                            cur = d
                            for p in parts[:-1]:
                                cur = cur.setdefault(p, {})
                            cur[parts[-1]] = val
                        else:
                            d[k] = val
                break
        class R:  # noqa
            modified_count = 1
            matched_count = 1
        return R()


# ─────────────────────────────────────────────────────────────────────────────
# Install stubs BEFORE importing triggers
# ─────────────────────────────────────────────────────────────────────────────

users = FakeCollection()
prefs = FakeCollection()
story_progress = FakeCollection()
news_batches = FakeCollection()
learning_plans = FakeCollection()
daily_stats = FakeCollection()

db_stub = types.ModuleType("database")
db_stub.users_collection = users
db_stub.notification_preferences_collection = prefs
db_stub.story_progress_collection = story_progress
db_stub.news_batches_collection = news_batches
db_stub.learning_plans_collection = learning_plans
db_stub.daily_stats_collection = daily_stats
sys.modules["database"] = db_stub

# Stub notification_service so no real push is attempted.
SENT = []  # list of dicts pushed


class StubNotificationService:
    def send_expo_push_notification(self, push_tokens, title, body, data=None,
                                    priority="high", sound="default", badge=None):
        SENT.append({"tokens": push_tokens, "title": title, "body": body,
                     "data": data or {}})
        return {"success": True, "sent": len(push_tokens)}


ns_stub = types.ModuleType("notification_service")
ns_stub.NotificationService = StubNotificationService
sys.modules["notification_service"] = ns_stub

import reminder_common as rc  # noqa: E402
import story_reminder_trigger as srt  # noqa: E402
import news_reminder_trigger as nrt  # noqa: E402
import learning_plan_reminder_trigger as prt  # noqa: E402

# Point the trigger singletons at the stub service instance.
srt.story_reminder_trigger.notification_service = StubNotificationService()
nrt.news_reminder_trigger.notification_service = StubNotificationService()
prt.learning_plan_reminder_trigger.notification_service = StubNotificationService()

# Make triggers use a controllable "now" by monkeypatching datetime.utcnow.
# Instead, each trigger calls datetime.utcnow() internally; we set the machine
# nowhere-near midnight scenarios by choosing UTC times that map to the target
# local hour for a chosen timezone. We drive via a fixed UTC by patching.

import builtins  # noqa

FAKE_UTC = {"value": datetime(2026, 7, 3, 12, 0, 0)}  # default noon UTC


class _PatchedDatetime(datetime):
    @classmethod
    def utcnow(cls):
        return FAKE_UTC["value"]

    @classmethod
    def now(cls, tz=None):
        base = FAKE_UTC["value"].replace(tzinfo=timezone.utc)
        return base.astimezone(tz) if tz else FAKE_UTC["value"]


# Patch datetime in each trigger + reminder_common module namespace.
for mod in (srt, nrt, prt, rc):
    mod.datetime = _PatchedDatetime


# ─────────────────────────────────────────────────────────────────────────────
# Test helpers
# ─────────────────────────────────────────────────────────────────────────────

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    mark = "✅" if cond else "❌"
    print(f"{mark} {name}" + (f"  [{detail}]" if detail and not cond else ""))


def reset():
    users.docs.clear(); prefs.docs.clear(); story_progress.docs.clear()
    news_batches.docs.clear(); learning_plans.docs.clear(); daily_stats.docs.clear()
    users.updates.clear(); prefs.updates.clear()
    SENT.clear()
    nrt.news_reminder_trigger._fresh_cache = {}


def set_utc(y, mo, d, h, mi=0):
    FAKE_UTC["value"] = datetime(y, mo, d, h, mi, 0)


def mk_user(uid="u1", tz="America/New_York", token="ExponentPushToken[abc]",
            story_completed=0, news_by_category=None, last_news=None):
    stats_life = {"story_episodes_completed": story_completed}
    if news_by_category is not None:
        stats_life["news_by_category"] = news_by_category
    if last_news is not None:
        stats_life["last_news_session_at"] = last_news
    return {"_id": uid, "push_token": token, "timezone": tz,
            "stats": {"lifetime": stats_life}}


# ObjectId(user_id) is called inside triggers; stub bson.ObjectId to identity.
import bson  # noqa
_orig_objectid = bson.ObjectId
class _IdentityObjectId(str):
    def __new__(cls, v=""):
        return str.__new__(cls, v)
bson.ObjectId = _IdentityObjectId
srt.ObjectId = _IdentityObjectId
nrt.ObjectId = _IdentityObjectId
prt.ObjectId = _IdentityObjectId


def mk_prefs(uid="u1", tz="America/New_York", story=True, news=True, plan=True,
             preferred_hour=18, quiet=False, q_start=22, q_end=8,
             week_count=0, week_start=None, max_week=3, last_by_kind=None):
    return {
        "user_id": uid, "timezone": tz,
        "story_reminders_enabled": story,
        "news_reminders_enabled": news,
        "learning_plan_updates_enabled": plan,
        "preferred_notification_time": preferred_hour,
        "quiet_hours_enabled": quiet, "quiet_hours_start": q_start,
        "quiet_hours_end": q_end,
        "notification_count_this_week": week_count,
        "week_start_date": week_start or FAKE_UTC["value"],
        "max_notifications_per_week": max_week,
        "last_sent_by_kind": last_by_kind or {},
    }


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIOS
# ─────────────────────────────────────────────────────────────────────────────

def scenario_story_unlock_happy():
    reset()
    # NY morning: 09:00 local => 13:00 UTC (EDT = UTC-4 in July)
    set_utc(2026, 7, 3, 13, 0)
    prefs.docs.append(mk_prefs())
    users.docs.append(mk_user())
    unlocked = datetime(2026, 7, 3, 4, 0, tzinfo=timezone.utc)  # already passed
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 2, "scene_index": 0, "unlocked_at": unlocked},
        "last_played_at": datetime(2026, 7, 2, 20, 0, tzinfo=timezone.utc),  # before unlock
    })
    run(srt.run_story_reminder_check())
    check("STORY unlock: happy path sends", len(SENT) == 1)
    check("STORY unlock: correct tier", SENT and SENT[0]["data"].get("tier") == "unlock")
    check("STORY unlock: deep-link screen", SENT and SENT[0]["data"].get("screen") == "StoryWorlds")
    check("STORY unlock: budget recorded", len(prefs.updates) == 1)


def scenario_story_unlock_already_played():
    reset()
    set_utc(2026, 7, 3, 13, 0)
    prefs.docs.append(mk_prefs())
    users.docs.append(mk_user())
    unlocked = datetime(2026, 7, 3, 4, 0, tzinfo=timezone.utc)
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 2, "unlocked_at": unlocked},
        "last_played_at": datetime(2026, 7, 3, 9, 0, tzinfo=timezone.utc),  # AFTER unlock
    })
    run(srt.run_story_reminder_check())
    check("STORY unlock: suppressed if already played since unlock", len(SENT) == 0)


def scenario_story_still_locked():
    reset()
    set_utc(2026, 7, 3, 13, 0)  # 09:00 NY
    prefs.docs.append(mk_prefs())
    users.docs.append(mk_user())
    unlocked = datetime(2026, 7, 4, 4, 0, tzinfo=timezone.utc)  # future
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 2, "unlocked_at": unlocked},
        "last_played_at": datetime(2026, 7, 2, 20, 0, tzinfo=timezone.utc),
    })
    run(srt.run_story_reminder_check())
    check("STORY unlock: not sent while still time-locked", len(SENT) == 0)


def scenario_story_resume_evening():
    reset()
    # preferred hour 18 local NY => 22:00 UTC
    set_utc(2026, 7, 3, 22, 0)
    prefs.docs.append(mk_prefs(preferred_hour=18))
    users.docs.append(mk_user())
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 1},  # no unlocked_at -> not an unlock case
        "last_played_at": datetime(2026, 6, 29, 20, 0, tzinfo=timezone.utc),  # 4 days stale
    })
    run(srt.run_story_reminder_check())
    check("STORY resume: stale in_progress sends in evening", len(SENT) == 1)
    check("STORY resume: correct tier", SENT and SENT[0]["data"].get("tier") == "resume")


def scenario_story_resume_not_stale():
    reset()
    set_utc(2026, 7, 3, 22, 0)
    prefs.docs.append(mk_prefs(preferred_hour=18))
    users.docs.append(mk_user())
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 1},
        "last_played_at": datetime(2026, 7, 3, 2, 0, tzinfo=timezone.utc),  # today, fresh
    })
    run(srt.run_story_reminder_check())
    check("STORY resume: fresh play not nudged", len(SENT) == 0)


def scenario_story_discover_weekly():
    reset()
    # Saturday 2026-07-04 is weekday 5; preferred hour 18 NY => 22 UTC.
    # 2026-07-04 22:00 UTC == 18:00 EDT Saturday.
    set_utc(2026, 7, 4, 22, 0)
    prefs.docs.append(mk_prefs(preferred_hour=18))
    users.docs.append(mk_user(story_completed=0))  # never completed
    # no story_progress docs => never tried
    run(srt.run_story_reminder_check())
    check("STORY discover: engaged-never-played sends on discover weekday", len(SENT) == 1)
    check("STORY discover: correct tier", SENT and SENT[0]["data"].get("tier") == "discover")


def scenario_story_discover_wrong_day():
    reset()
    set_utc(2026, 7, 3, 22, 0)  # Friday weekday 4, not discover day
    prefs.docs.append(mk_prefs(preferred_hour=18))
    users.docs.append(mk_user(story_completed=0))
    run(srt.run_story_reminder_check())
    check("STORY discover: not sent on non-discover weekday", len(SENT) == 0)


def scenario_story_optout():
    reset()
    set_utc(2026, 7, 3, 13, 0)
    prefs.docs.append(mk_prefs(story=False))
    users.docs.append(mk_user())
    unlocked = datetime(2026, 7, 3, 4, 0, tzinfo=timezone.utc)
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 2, "unlocked_at": unlocked},
        "last_played_at": datetime(2026, 7, 2, 20, 0, tzinfo=timezone.utc),
    })
    run(srt.run_story_reminder_check())
    check("STORY: opted-out user never receives push", len(SENT) == 0)


def scenario_quiet_hours():
    reset()
    # 23:00 NY local within quiet 22->8. 23 NY == 03:00 UTC next day.
    set_utc(2026, 7, 4, 3, 0)
    prefs.docs.append(mk_prefs(preferred_hour=23, quiet=True, q_start=22, q_end=8))
    users.docs.append(mk_user())
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 1},
        "last_played_at": datetime(2026, 6, 29, 20, 0, tzinfo=timezone.utc),
    })
    run(srt.run_story_reminder_check())
    check("QUIET HOURS: suppressed inside quiet window", len(SENT) == 0)


def scenario_weekly_cap():
    reset()
    set_utc(2026, 7, 3, 22, 0)
    prefs.docs.append(mk_prefs(preferred_hour=18, week_count=3, max_week=3))  # at cap
    users.docs.append(mk_user())
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 1},
        "last_played_at": datetime(2026, 6, 29, 20, 0, tzinfo=timezone.utc),
    })
    run(srt.run_story_reminder_check())
    check("WEEKLY CAP: at cap -> no send", len(SENT) == 0)


def scenario_perkind_daily_dedup():
    reset()
    set_utc(2026, 7, 3, 22, 0)  # 18:00 NY
    # already sent a story_resume today (local)
    today_local_stamp = datetime(2026, 7, 3, 15, 0, tzinfo=timezone.utc)  # 11:00 NY today
    prefs.docs.append(mk_prefs(preferred_hour=18,
                               last_by_kind={"story_resume": today_local_stamp}))
    users.docs.append(mk_user())
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 1},
        "last_played_at": datetime(2026, 6, 29, 20, 0, tzinfo=timezone.utc),
    })
    run(srt.run_story_reminder_check())
    check("DAILY DEDUP: same-kind already sent today -> suppressed", len(SENT) == 0)


def scenario_missing_token():
    reset()
    set_utc(2026, 7, 3, 22, 0)
    prefs.docs.append(mk_prefs(preferred_hour=18))
    users.docs.append(mk_user(token=None))  # no push token
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 1},
        "last_played_at": datetime(2026, 6, 29, 20, 0, tzinfo=timezone.utc),
    })
    run(srt.run_story_reminder_check())
    check("EDGE: missing push token -> no crash, no send", len(SENT) == 0)


def scenario_bad_timezone():
    reset()
    set_utc(2026, 7, 3, 22, 0)
    prefs.docs.append(mk_prefs(tz="Not/A_Zone", preferred_hour=22))  # falls back to UTC
    u = mk_user(tz="Not/A_Zone"); users.docs.append(u)
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 1},
        "last_played_at": datetime(2026, 6, 29, 20, 0, tzinfo=timezone.utc),
    })
    run(srt.run_story_reminder_check())
    # UTC 22:00 == preferred 22 -> resume should fire (proves no crash + UTC fallback)
    check("EDGE: invalid timezone falls back to UTC (no crash)", len(SENT) == 1)


def scenario_malformed_timestamps():
    reset()
    set_utc(2026, 7, 3, 13, 0)
    prefs.docs.append(mk_prefs())
    users.docs.append(mk_user())
    # unlocked_at as ISO STRING, last_played as string too
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 2, "unlocked_at": "2026-07-03T04:00:00+00:00"},
        "last_played_at": "2026-07-02T20:00:00Z",
    })
    run(srt.run_story_reminder_check())
    check("EDGE: string timestamps parsed (unlock fires)", len(SENT) == 1)


def scenario_missing_current_object():
    reset()
    set_utc(2026, 7, 3, 13, 0)
    prefs.docs.append(mk_prefs())
    users.docs.append(mk_user())
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": None,  # null cursor
        "last_played_at": datetime(2026, 7, 2, 20, 0, tzinfo=timezone.utc),
    })
    run(srt.run_story_reminder_check())
    check("EDGE: null current cursor -> no crash", True)  # reaching here = no exception


# ── NEWS ─────────────────────────────────────────────────────────────────────

def scenario_news_personalized():
    reset()
    set_utc(2026, 7, 3, 13, 0)  # 09:00 NY within [7,11)
    prefs.docs.append(mk_prefs())
    users.docs.append(mk_user(news_by_category={"technology": 4, "sports": 1}))
    news_batches.docs.append({"date": datetime(2026, 7, 3, 0, 0), "status": "completed"})
    run(nrt.run_news_reminder_check())
    check("NEWS personalized: sends with category", len(SENT) == 1)
    check("NEWS personalized: category=technology",
          SENT and SENT[0]["data"].get("category") == "technology")
    check("NEWS personalized: names Technology in body",
          SENT and "Technology" in SENT[0]["body"])


def scenario_news_generic():
    reset()
    set_utc(2026, 7, 3, 13, 0)
    prefs.docs.append(mk_prefs())
    users.docs.append(mk_user(news_by_category=None))  # no interest
    news_batches.docs.append({"date": datetime(2026, 7, 3, 0, 0), "status": "completed"})
    run(nrt.run_news_reminder_check())
    check("NEWS generic: sends without category", len(SENT) == 1)
    check("NEWS generic: no category key", SENT and not SENT[0]["data"].get("category"))


def scenario_news_below_threshold():
    reset()
    set_utc(2026, 7, 3, 13, 0)
    prefs.docs.append(mk_prefs())
    users.docs.append(mk_user(news_by_category={"sports": 1}))  # below MIN(2)
    news_batches.docs.append({"date": datetime(2026, 7, 3, 0, 0), "status": "completed"})
    run(nrt.run_news_reminder_check())
    check("NEWS: single-tap category not named (generic)", len(SENT) == 1 and not SENT[0]["data"].get("category"))


def scenario_news_no_fresh():
    reset()
    set_utc(2026, 7, 3, 13, 0)
    prefs.docs.append(mk_prefs())
    users.docs.append(mk_user(news_by_category={"technology": 4}))
    # no news batch for today
    run(nrt.run_news_reminder_check())
    check("NEWS: no fresh news -> no send", len(SENT) == 0)


def scenario_news_already_read_today():
    reset()
    set_utc(2026, 7, 3, 13, 0)  # 09:00 NY
    prefs.docs.append(mk_prefs())
    # read news today at 08:00 NY == 12:00 UTC
    users.docs.append(mk_user(news_by_category={"technology": 4},
                              last_news=datetime(2026, 7, 3, 12, 0, tzinfo=timezone.utc)))
    news_batches.docs.append({"date": datetime(2026, 7, 3, 0, 0), "status": "completed"})
    run(nrt.run_news_reminder_check())
    check("NEWS: already read today -> suppressed", len(SENT) == 0)


def scenario_news_outside_morning():
    reset()
    set_utc(2026, 7, 3, 22, 0)  # 18:00 NY, outside [7,11)
    prefs.docs.append(mk_prefs())
    users.docs.append(mk_user(news_by_category={"technology": 4}))
    news_batches.docs.append({"date": datetime(2026, 7, 3, 0, 0), "status": "completed"})
    run(nrt.run_news_reminder_check())
    check("NEWS: outside morning window -> no send", len(SENT) == 0)


def scenario_news_optout():
    reset()
    set_utc(2026, 7, 3, 13, 0)
    prefs.docs.append(mk_prefs(news=False))
    users.docs.append(mk_user(news_by_category={"technology": 4}))
    news_batches.docs.append({"date": datetime(2026, 7, 3, 0, 0), "status": "completed"})
    run(nrt.run_news_reminder_check())
    check("NEWS: opted-out -> no send", len(SENT) == 0)


def scenario_news_batch_inprogress_zero():
    reset()
    set_utc(2026, 7, 3, 13, 0)
    prefs.docs.append(mk_prefs())
    users.docs.append(mk_user())
    news_batches.docs.append({"date": datetime(2026, 7, 3, 0, 0),
                              "status": "in_progress", "article_count": 0})
    run(nrt.run_news_reminder_check())
    check("NEWS: in_progress batch with 0 articles -> no send", len(SENT) == 0)


# ── LEARNING PLAN ────────────────────────────────────────────────────────────

def scenario_plan_stale_active():
    reset()
    set_utc(2026, 7, 3, 22, 0)  # 18:00 NY preferred
    prefs.docs.append(mk_prefs(preferred_hour=18))
    users.docs.append(mk_user())
    learning_plans.docs.append({
        "_id": "p1", "user_id": "u1", "language": "spanish",
        "total_sessions": 20, "completed_sessions": 8, "status": "active",
        "updated_at": datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc),  # 3 days stale
    })
    run(prt.run_plan_reminder_check())
    check("PLAN: stale active plan sends", len(SENT) == 1)
    check("PLAN: body has percent", SENT and "40%" in SENT[0]["body"])
    check("PLAN: deep-link screen", SENT and SENT[0]["data"].get("screen") == "LearningPlan")


def scenario_plan_fresh():
    reset()
    set_utc(2026, 7, 3, 22, 0)
    prefs.docs.append(mk_prefs(preferred_hour=18))
    users.docs.append(mk_user())
    learning_plans.docs.append({
        "_id": "p1", "user_id": "u1", "language": "spanish",
        "total_sessions": 20, "completed_sessions": 8, "status": "active",
        "updated_at": datetime(2026, 7, 3, 2, 0, tzinfo=timezone.utc),  # today, fresh
    })
    run(prt.run_plan_reminder_check())
    check("PLAN: fresh plan not nudged", len(SENT) == 0)


def scenario_plan_completed():
    reset()
    set_utc(2026, 7, 3, 22, 0)
    prefs.docs.append(mk_prefs(preferred_hour=18))
    users.docs.append(mk_user())
    learning_plans.docs.append({
        "_id": "p1", "user_id": "u1", "language": "spanish",
        "total_sessions": 20, "completed_sessions": 20, "status": "active",
        "updated_at": datetime(2026, 6, 25, 2, 0, tzinfo=timezone.utc),
    })
    run(prt.run_plan_reminder_check())
    check("PLAN: completed plan not nudged", len(SENT) == 0)


def scenario_plan_archived():
    reset()
    set_utc(2026, 7, 3, 22, 0)
    prefs.docs.append(mk_prefs(preferred_hour=18))
    users.docs.append(mk_user())
    learning_plans.docs.append({
        "_id": "p1", "user_id": "u1", "language": "spanish",
        "total_sessions": 20, "completed_sessions": 5, "status": "archived",
        "updated_at": datetime(2026, 6, 25, 2, 0, tzinfo=timezone.utc),
    })
    run(prt.run_plan_reminder_check())
    check("PLAN: archived plan not nudged", len(SENT) == 0)


def scenario_plan_optout():
    reset()
    set_utc(2026, 7, 3, 22, 0)
    prefs.docs.append(mk_prefs(preferred_hour=18, plan=False))
    users.docs.append(mk_user())
    learning_plans.docs.append({
        "_id": "p1", "user_id": "u1", "language": "spanish",
        "total_sessions": 20, "completed_sessions": 8, "status": "active",
        "updated_at": datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc),
    })
    run(prt.run_plan_reminder_check())
    check("PLAN: opted-out -> no send", len(SENT) == 0)


# ── SHARED BUDGET INTEGRITY ──────────────────────────────────────────────────

def scenario_budget_week_rollover():
    reset()
    # week started 8 days ago -> counter should reset, and post-send count=1
    old_week = datetime(2026, 6, 25, 12, 0)
    set_utc(2026, 7, 3, 22, 0)
    prefs.docs.append(mk_prefs(preferred_hour=18, week_count=3, max_week=3,
                               week_start=old_week))
    users.docs.append(mk_user())
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 1},
        "last_played_at": datetime(2026, 6, 29, 20, 0, tzinfo=timezone.utc),
    })
    run(srt.run_story_reminder_check())
    check("BUDGET: expired week resets, send allowed", len(SENT) == 1)
    # after record_send, counter should be 1 and week_start updated
    p = prefs.docs[0]
    check("BUDGET: counter reset to 1 after rollover",
          p.get("notification_count_this_week") == 1,
          str(p.get("notification_count_this_week")))


def scenario_budget_increments():
    reset()
    set_utc(2026, 7, 3, 22, 0)
    prefs.docs.append(mk_prefs(preferred_hour=18, week_count=1, max_week=3))
    users.docs.append(mk_user())
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 1},
        "last_played_at": datetime(2026, 6, 29, 20, 0, tzinfo=timezone.utc),
    })
    run(srt.run_story_reminder_check())
    p = prefs.docs[0]
    check("BUDGET: counter increments 1->2 on send",
          p.get("notification_count_this_week") == 2,
          str(p.get("notification_count_this_week")))
    check("BUDGET: per-kind stamp written",
          "story_resume" in (p.get("last_sent_by_kind") or {}))


def scenario_precedence_one_push():
    reset()
    # Morning AND stale AND at preferred? Force overlap: preferred=9, morning window.
    set_utc(2026, 7, 3, 13, 0)  # 09:00 NY (in morning window AND preferred=9)
    prefs.docs.append(mk_prefs(preferred_hour=9))
    users.docs.append(mk_user())
    unlocked = datetime(2026, 7, 3, 4, 0, tzinfo=timezone.utc)
    story_progress.docs.append({
        "_id": "u1:s1", "user_id": "u1", "series_id": "s1", "status": "in_progress",
        "current": {"episode_number": 2, "unlocked_at": unlocked},
        "last_played_at": datetime(2026, 6, 28, 20, 0, tzinfo=timezone.utc),  # stale too
    })
    run(srt.run_story_reminder_check())
    check("PRECEDENCE: exactly one push when unlock+resume both apply", len(SENT) == 1)
    check("PRECEDENCE: unlock wins over resume",
          SENT and SENT[0]["data"].get("tier") == "unlock")


def scenario_multiuser_resilience():
    reset()
    set_utc(2026, 7, 3, 22, 0)  # 18:00 NY preferred
    # A: valid stale -> send
    prefs.docs.append(mk_prefs(uid="A", preferred_hour=18))
    users.docs.append(mk_user(uid="A"))
    story_progress.docs.append({"_id": "A:s1", "user_id": "A", "series_id": "s1",
        "status": "in_progress", "current": {"episode_number": 1},
        "last_played_at": datetime(2026, 6, 28, 20, 0, tzinfo=timezone.utc)})
    # B: prefs but NO user doc -> clean skip (not error)
    prefs.docs.append(mk_prefs(uid="B", preferred_hour=18))
    # C: valid stale -> send
    prefs.docs.append(mk_prefs(uid="C", preferred_hour=18))
    users.docs.append(mk_user(uid="C"))
    story_progress.docs.append({"_id": "C:s1", "user_id": "C", "series_id": "s1",
        "status": "in_progress", "current": {"episode_number": 1},
        "last_played_at": datetime(2026, 6, 28, 20, 0, tzinfo=timezone.utc)})
    res = run(srt.run_story_reminder_check())
    check("RESILIENCE: 2 valid users sent, 1 missing-user skipped", len(SENT) == 2)
    check("RESILIENCE: missing user doc is a skip not an error", res["errors"] == 0)


def scenario_failed_push_no_budget_burn():
    reset()
    set_utc(2026, 7, 3, 22, 0)

    class FailingNS:
        def send_expo_push_notification(self, **kw):
            return {"success": False, "message": "simulated failure"}

    prev = srt.story_reminder_trigger.notification_service
    srt.story_reminder_trigger.notification_service = FailingNS()
    try:
        prefs.docs.append(mk_prefs(preferred_hour=18, week_count=1))
        users.docs.append(mk_user())
        story_progress.docs.append({"_id": "u1:s1", "user_id": "u1", "series_id": "s1",
            "status": "in_progress", "current": {"episode_number": 1},
            "last_played_at": datetime(2026, 6, 28, 20, 0, tzinfo=timezone.utc)})
        run(srt.run_story_reminder_check())
        p = prefs.docs[0]
        check("FAIL-SAFE: failed push does not burn weekly budget",
              p.get("notification_count_this_week") == 1,
              str(p.get("notification_count_this_week")))
        check("FAIL-SAFE: failed push does not set dedup stamp",
              "story_resume" not in (p.get("last_sent_by_kind") or {}))
    finally:
        srt.story_reminder_trigger.notification_service = prev


def main():
    scenarios = [
        scenario_multiuser_resilience,
        scenario_failed_push_no_budget_burn,
        scenario_story_unlock_happy,
        scenario_story_unlock_already_played,
        scenario_story_still_locked,
        scenario_story_resume_evening,
        scenario_story_resume_not_stale,
        scenario_story_discover_weekly,
        scenario_story_discover_wrong_day,
        scenario_story_optout,
        scenario_quiet_hours,
        scenario_weekly_cap,
        scenario_perkind_daily_dedup,
        scenario_missing_token,
        scenario_bad_timezone,
        scenario_malformed_timestamps,
        scenario_missing_current_object,
        scenario_news_personalized,
        scenario_news_generic,
        scenario_news_below_threshold,
        scenario_news_no_fresh,
        scenario_news_already_read_today,
        scenario_news_outside_morning,
        scenario_news_optout,
        scenario_news_batch_inprogress_zero,
        scenario_plan_stale_active,
        scenario_plan_fresh,
        scenario_plan_completed,
        scenario_plan_archived,
        scenario_plan_optout,
        scenario_budget_week_rollover,
        scenario_budget_increments,
        scenario_precedence_one_push,
    ]
    for s in scenarios:
        try:
            s()
        except Exception as e:
            import traceback
            check(f"{s.__name__} (EXCEPTION)", False, str(e))
            traceback.print_exc()

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print("\n" + "=" * 60)
    print(f"RESULT: {passed}/{total} assertions passed")
    print("=" * 60)
    if passed != total:
        print("\nFAILURES:")
        for name, ok, detail in RESULTS:
            if not ok:
                print(f"  ❌ {name}  {detail}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
