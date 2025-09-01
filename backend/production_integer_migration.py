#!/usr/bin/env python3
"""
PRODUCTION INTEGER MIGRATION
Safe migration of all production data from decimal to integer calculations
"""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId
import json
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ProductionIntegerMigration:
    """Safe migration of production data to integer calculations"""
    
    def __init__(self, db):
        self.db = db
    
    @staticmethod
    def minutes_to_hundredths(minutes_float: float) -> int:
        """Convert decimal minutes to integer hundredths"""
        return int(round(minutes_float * 100))
    
    @staticmethod
    def hundredths_to_minutes(hundredths_int: int) -> float:
        """Convert integer hundredths to decimal minutes"""
        return hundredths_int / 100
    
    async def get_all_users_for_migration(self) -> list:
        """Get all users that need migration"""
        try:
            # Get all users with subscription data
            users = await self.db.users.find({
                "$or": [
                    {"practice_minutes_used": {"$exists": True}},
                    {"practice_sessions_used": {"$exists": True}},
                    {"assessments_used": {"$exists": True}}
                ]
            }).to_list(length=None)
            
            return users
            
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    
    async def migrate_user_records(self) -> Dict[str, Any]:
        """Migrate all user records to integer fields"""
        try:
            print("👥 MIGRATING USER RECORDS")
            print("-" * 30)
            
            users = await self.get_all_users_for_migration()
            print(f"Found {len(users)} users to migrate")
            
            migration_results = []
            
            for user in users:
                user_id = str(user["_id"])
                email = user.get("email", "unknown")
                
                # Get current decimal values
                decimal_minutes = user.get('practice_minutes_used', 0.0)
                decimal_sessions = user.get('practice_sessions_used', 0)
                decimal_assessments = user.get('assessments_used', 0)
                
                # Convert to integers
                integer_minutes_hundredths = self.minutes_to_hundredths(decimal_minutes)
                
                # Update user with integer fields (keeping decimal for safety)
                update_result = await self.db.users.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            # New integer fields
                            "practice_minutes_used_hundredths": integer_minutes_hundredths,
                            "practice_sessions_used_int": decimal_sessions,
                            "assessments_used_int": decimal_assessments,
                            
                            # Migration metadata
                            "integer_migration_date": datetime.utcnow().isoformat(),
                            "integer_migration_version": "1.0",
                            "integer_migration_source": {
                                "decimal_minutes": decimal_minutes,
                                "decimal_sessions": decimal_sessions,
                                "decimal_assessments": decimal_assessments
                            }
                        }
                    }
                )
                
                migration_result = {
                    "user_id": user_id,
                    "email": email,
                    "success": update_result.modified_count > 0,
                    "decimal_values": {
                        "minutes": decimal_minutes,
                        "sessions": decimal_sessions,
                        "assessments": decimal_assessments
                    },
                    "integer_values": {
                        "minutes_hundredths": integer_minutes_hundredths,
                        "sessions": decimal_sessions,
                        "assessments": decimal_assessments
                    }
                }
                
                migration_results.append(migration_result)
                
                if migration_result["success"]:
                    print(f"✅ {email}: {decimal_minutes:.2f} min → {integer_minutes_hundredths} hundredths")
                else:
                    print(f"❌ {email}: Migration failed")
            
            successful_migrations = sum(1 for r in migration_results if r["success"])
            print(f"\n📊 Migration Summary: {successful_migrations}/{len(users)} users migrated")
            
            return {
                "total_users": len(users),
                "successful_migrations": successful_migrations,
                "migration_results": migration_results
            }
            
        except Exception as e:
            print(f"Error migrating user records: {e}")
            return {"error": str(e)}
    
    async def migrate_learning_plan_sessions(self) -> Dict[str, Any]:
        """Migrate learning plan session durations to integer hundredths"""
        try:
            print("\n🎓 MIGRATING LEARNING PLAN SESSIONS")
            print("-" * 38)
            
            # Get all learning plans
            learning_plans = await self.db.learning_plans.find({}).to_list(length=None)
            print(f"Found {len(learning_plans)} learning plans to check")
            
            migration_results = []
            
            for plan in learning_plans:
                plan_id = str(plan["_id"])
                user_id = plan.get("user_id", "unknown")
                plan_name = plan.get("name", "Unknown Plan")
                
                sessions = plan.get("sessions", [])
                if not sessions:
                    continue
                
                # Check if any sessions have decimal durations
                sessions_updated = 0
                updated_sessions = []
                
                for session in sessions:
                    duration_minutes = session.get("duration_minutes", 0.0)
                    
                    if duration_minutes > 0:
                        # Add integer hundredths field
                        session["duration_minutes_hundredths"] = self.minutes_to_hundredths(duration_minutes)
                        updated_sessions.append(session)
                        sessions_updated += 1
                
                if sessions_updated > 0:
                    # Update the learning plan with integer fields
                    update_result = await self.db.learning_plans.update_one(
                        {"_id": plan["_id"]},
                        {
                            "$set": {
                                "sessions": updated_sessions,
                                "integer_migration_date": datetime.utcnow().isoformat(),
                                "sessions_migrated": sessions_updated
                            }
                        }
                    )
                    
                    migration_result = {
                        "plan_id": plan_id,
                        "user_id": user_id,
                        "plan_name": plan_name,
                        "sessions_updated": sessions_updated,
                        "success": update_result.modified_count > 0
                    }
                    
                    migration_results.append(migration_result)
                    
                    if migration_result["success"]:
                        print(f"✅ {plan_name} (User: {user_id}): {sessions_updated} sessions migrated")
                    else:
                        print(f"❌ {plan_name}: Migration failed")
            
            successful_plans = sum(1 for r in migration_results if r["success"])
            total_sessions = sum(r["sessions_updated"] for r in migration_results)
            
            print(f"\n📊 Learning Plan Migration Summary:")
            print(f"   - Plans migrated: {successful_plans}/{len(migration_results)}")
            print(f"   - Sessions migrated: {total_sessions}")
            
            return {
                "total_plans": len(learning_plans),
                "plans_with_sessions": len(migration_results),
                "successful_migrations": successful_plans,
                "total_sessions_migrated": total_sessions,
                "migration_results": migration_results
            }
            
        except Exception as e:
            print(f"Error migrating learning plans: {e}")
            return {"error": str(e)}
    
    async def migrate_conversation_sessions(self) -> Dict[str, Any]:
        """Migrate conversation session durations to integer hundredths"""
        try:
            print("\n💬 MIGRATING CONVERSATION SESSIONS")
            print("-" * 36)
            
            # Get all conversation sessions with durations
            conversations = await self.db.conversation_sessions.find({
                "duration_minutes": {"$exists": True, "$gt": 0}
            }).to_list(length=None)
            
            print(f"Found {len(conversations)} conversation sessions to migrate")
            
            migration_results = []
            
            for conversation in conversations:
                session_id = str(conversation["_id"])
                user_id = conversation.get("user_id", "unknown")
                duration_minutes = conversation.get("duration_minutes", 0.0)
                created_at = conversation.get("created_at", "unknown")
                
                # Convert to integer hundredths
                duration_hundredths = self.minutes_to_hundredths(duration_minutes)
                
                # Update conversation with integer field
                update_result = await self.db.conversation_sessions.update_one(
                    {"_id": conversation["_id"]},
                    {
                        "$set": {
                            "duration_minutes_hundredths": duration_hundredths,
                            "integer_migration_date": datetime.utcnow().isoformat()
                        }
                    }
                )
                
                migration_result = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "created_at": str(created_at),
                    "decimal_minutes": duration_minutes,
                    "integer_hundredths": duration_hundredths,
                    "success": update_result.modified_count > 0
                }
                
                migration_results.append(migration_result)
            
            successful_conversations = sum(1 for r in migration_results if r["success"])
            print(f"\n📊 Conversation Migration Summary: {successful_conversations}/{len(conversations)} sessions migrated")
            
            return {
                "total_conversations": len(conversations),
                "successful_migrations": successful_conversations,
                "migration_results": migration_results
            }
            
        except Exception as e:
            print(f"Error migrating conversations: {e}")
            return {"error": str(e)}
    
    async def verify_migration_integrity(self) -> Dict[str, Any]:
        """Verify that migration preserved data integrity"""
        try:
            print("\n🔍 VERIFYING MIGRATION INTEGRITY")
            print("-" * 35)
            
            # Check user records
            users = await self.db.users.find({
                "integer_migration_date": {"$exists": True}
            }).to_list(length=None)
            
            user_integrity_issues = []
            
            for user in users:
                user_id = str(user["_id"])
                email = user.get("email", "unknown")
                
                # Compare decimal vs integer values
                decimal_minutes = user.get("practice_minutes_used", 0.0)
                integer_hundredths = user.get("practice_minutes_used_hundredths", 0)
                integer_minutes = self.hundredths_to_minutes(integer_hundredths)
                
                difference = abs(decimal_minutes - integer_minutes)
                
                if difference > 0.01:  # More than 0.01 minute difference
                    user_integrity_issues.append({
                        "user_id": user_id,
                        "email": email,
                        "decimal_minutes": decimal_minutes,
                        "integer_minutes": integer_minutes,
                        "difference": difference
                    })
                    print(f"⚠️ {email}: Difference {difference:.4f} minutes")
                else:
                    print(f"✅ {email}: Perfect match")
            
            print(f"\n📊 User Integrity Check: {len(user_integrity_issues)} issues found")
            
            # Check learning plan sessions
            learning_plans = await self.db.learning_plans.find({
                "integer_migration_date": {"$exists": True}
            }).to_list(length=None)
            
            plan_integrity_issues = []
            
            for plan in learning_plans:
                sessions = plan.get("sessions", [])
                for session in sessions:
                    if "duration_minutes_hundredths" in session:
                        decimal_minutes = session.get("duration_minutes", 0.0)
                        integer_hundredths = session.get("duration_minutes_hundredths", 0)
                        integer_minutes = self.hundredths_to_minutes(integer_hundredths)
                        
                        difference = abs(decimal_minutes - integer_minutes)
                        
                        if difference > 0.01:
                            plan_integrity_issues.append({
                                "plan_id": str(plan["_id"]),
                                "user_id": plan.get("user_id"),
                                "decimal_minutes": decimal_minutes,
                                "integer_minutes": integer_minutes,
                                "difference": difference
                            })
            
            print(f"📊 Learning Plan Integrity Check: {len(plan_integrity_issues)} issues found")
            
            return {
                "user_integrity_issues": user_integrity_issues,
                "plan_integrity_issues": plan_integrity_issues,
                "total_issues": len(user_integrity_issues) + len(plan_integrity_issues),
                "migration_integrity": len(user_integrity_issues) + len(plan_integrity_issues) == 0
            }
            
        except Exception as e:
            print(f"Error verifying migration integrity: {e}")
            return {"error": str(e)}

async def run_production_migration():
    """Run the complete production migration"""
    
    # Get MongoDB URL
    mongodb_url = os.getenv('MONGODB_URL')
    if not mongodb_url:
        raise ValueError("MONGODB_URL environment variable is required")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongodb_url)
    db = client.language_tutor
    
    print("🚀 PRODUCTION INTEGER MIGRATION")
    print("=" * 40)
    print(f"📅 Migration Time: {datetime.utcnow().isoformat()}")
    print(f"🎯 Target: Railway Production MongoDB")
    print()
    
    # Initialize migration service
    migration = ProductionIntegerMigration(db)
    
    # Step 1: Migrate user records
    user_migration = await migration.migrate_user_records()
    
    # Step 2: Migrate learning plan sessions
    plan_migration = await migration.migrate_learning_plan_sessions()
    
    # Step 3: Migrate conversation sessions
    conversation_migration = await migration.migrate_conversation_sessions()
    
    # Step 4: Verify integrity
    integrity_check = await migration.verify_migration_integrity()
    
    # Create comprehensive migration report
    migration_report = {
        "migration_timestamp": datetime.utcnow().isoformat(),
        "migration_version": "1.0",
        "user_migration": user_migration,
        "learning_plan_migration": plan_migration,
        "conversation_migration": conversation_migration,
        "integrity_verification": integrity_check,
        "overall_success": (
            user_migration.get("successful_migrations", 0) > 0 and
            "error" not in plan_migration and
            "error" not in conversation_migration and
            integrity_check.get("migration_integrity", False)
        )
    }
    
    # Save migration report
    report_filename = f"production_integer_migration_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(migration_report, f, indent=2, default=str)
    
    print(f"\n📄 Migration report saved: {report_filename}")
    
    # Final summary
    print("\n🎯 MIGRATION SUMMARY")
    print("-" * 20)
    
    if migration_report["overall_success"]:
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print(f"   - Users migrated: {user_migration.get('successful_migrations', 0)}")
        print(f"   - Learning plans migrated: {plan_migration.get('successful_migrations', 0)}")
        print(f"   - Conversations migrated: {conversation_migration.get('successful_migrations', 0)}")
        print(f"   - Data integrity: {'✅ PERFECT' if integrity_check.get('migration_integrity', False) else '❌ ISSUES FOUND'}")
        print()
        print("🚀 READY FOR INTEGER-BASED CALCULATIONS!")
    else:
        print("❌ MIGRATION HAD ISSUES - REVIEW REPORT")
    
    await client.close()
    
    return migration_report

if __name__ == "__main__":
    asyncio.run(run_production_migration())
