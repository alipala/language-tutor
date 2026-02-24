#!/usr/bin/env python3
"""
Migration: Add selected_duration field to existing sessions
Date: 2026-02-23
Purpose: Support 3-minute sessions for A1/A2 learners

This migration adds selected_duration field with default value of 5
for backward compatibility with existing sessions.
"""

import asyncio
from datetime import datetime
from database import database

async def migrate_up():
    """
    Add selected_duration field to existing sessions
    """
    print("[MIGRATION] Starting migration: 002_add_selected_duration")
    print("[MIGRATION] This will add selected_duration=5 to all existing sessions")

    # 1. Update conversation_sessions collection
    print("\n[MIGRATION] Updating conversation_sessions...")
    conversation_sessions = database.conversation_sessions

    # Count documents without selected_duration
    count_without = await conversation_sessions.count_documents({
        "selected_duration": {"$exists": False}
    })

    print(f"[MIGRATION] Found {count_without} conversation sessions without selected_duration")

    if count_without > 0:
        result = await conversation_sessions.update_many(
            {"selected_duration": {"$exists": False}},
            {"$set": {"selected_duration": 5}}
        )
        print(f"[MIGRATION] ✅ Updated {result.modified_count} conversation sessions")
    else:
        print("[MIGRATION] ✅ No conversation sessions to update")

    # 2. Update learning_plans collection (session_history)
    print("\n[MIGRATION] Updating learning_plans session_history...")
    learning_plans = database.learning_plans

    # Find all learning plans with session_history
    plans_cursor = learning_plans.find({"session_history": {"$exists": True, "$ne": []}})
    plans = await plans_cursor.to_list(None)

    print(f"[MIGRATION] Found {len(plans)} learning plans with session history")

    updated_plans = 0
    for plan in plans:
        session_history = plan.get("session_history", [])
        modified = False

        for session in session_history:
            if "selected_duration" not in session:
                session["selected_duration"] = 5
                modified = True

        if modified:
            await learning_plans.update_one(
                {"_id": plan["_id"]},
                {"$set": {"session_history": session_history}}
            )
            updated_plans += 1

    print(f"[MIGRATION] ✅ Updated {updated_plans} learning plans")

    # 3. Update learning_plans collection (weekly_schedule.session_details)
    print("\n[MIGRATION] Updating learning_plans weekly_schedule...")

    plans_cursor = learning_plans.find({
        "plan_content.weekly_schedule": {"$exists": True}
    })
    plans = await plans_cursor.to_list(None)

    print(f"[MIGRATION] Found {len(plans)} learning plans with weekly schedules")

    updated_schedules = 0
    for plan in plans:
        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
        modified = False

        for week in weekly_schedule:
            session_details = week.get("session_details", [])
            for session in session_details:
                if "selected_duration" not in session:
                    session["selected_duration"] = 5
                    modified = True

        if modified:
            await learning_plans.update_one(
                {"_id": plan["_id"]},
                {"$set": {"plan_content.weekly_schedule": weekly_schedule}}
            )
            updated_schedules += 1

    print(f"[MIGRATION] ✅ Updated {updated_schedules} learning plans with weekly schedules")

    # 4. Summary
    print("\n[MIGRATION] Migration complete!")
    print(f"[MIGRATION] Summary:")
    print(f"  - Conversation sessions: {count_without} updated")
    print(f"  - Learning plans (history): {updated_plans} updated")
    print(f"  - Learning plans (schedules): {updated_schedules} updated")
    print(f"\n[MIGRATION] All existing sessions now have selected_duration=5 (backward compatible)")

async def migrate_down():
    """
    Remove selected_duration field (rollback)
    """
    print("[MIGRATION] Rolling back migration: 002_add_selected_duration")

    # 1. Remove from conversation_sessions
    conversation_sessions = database.conversation_sessions
    result = await conversation_sessions.update_many(
        {},
        {"$unset": {"selected_duration": ""}}
    )
    print(f"[MIGRATION] Removed selected_duration from {result.modified_count} conversation sessions")

    # 2. Remove from learning_plans (session_history)
    learning_plans = database.learning_plans
    plans_cursor = learning_plans.find({"session_history": {"$exists": True}})
    plans = await plans_cursor.to_list(None)

    for plan in plans:
        session_history = plan.get("session_history", [])
        for session in session_history:
            session.pop("selected_duration", None)

        await learning_plans.update_one(
            {"_id": plan["_id"]},
            {"$set": {"session_history": session_history}}
        )

    # 3. Remove from learning_plans (weekly_schedule)
    plans_cursor = learning_plans.find({"plan_content.weekly_schedule": {"$exists": True}})
    plans = await plans_cursor.to_list(None)

    for plan in plans:
        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
        for week in weekly_schedule:
            session_details = week.get("session_details", [])
            for session in session_details:
                session.pop("selected_duration", None)

        await learning_plans.update_one(
            {"_id": plan["_id"]},
            {"$set": {"plan_content.weekly_schedule": weekly_schedule}}
        )

    print("[MIGRATION] Rollback complete!")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "down":
        asyncio.run(migrate_down())
    else:
        asyncio.run(migrate_up())
