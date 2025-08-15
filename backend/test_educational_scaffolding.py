#!/usr/bin/env python3
"""
Test script for Phase 6: Educational Scaffolding
Tests all learning gates, progress updates, achievements, and analytics integration
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, database
from services.educational_scaffolding_service import EducationalScaffoldingService
from models.educational_scaffolding_models import StoryProgressUpdate

class EducationalScaffoldingTester:
    """Comprehensive test suite for Educational Scaffolding Phase 6"""
    
    def __init__(self):
        self.test_user_id = "test_user_educational_scaffolding"
        self.test_world_id = "world_medieval_adventure"
        self.test_language = "english"
        self.test_level = "B1"
        
    async def run_all_tests(self):
        """Run all educational scaffolding tests"""
        print("🧪 " + "="*80)
        print("🧪 PHASE 6: EDUCATIONAL SCAFFOLDING - COMPREHENSIVE TEST SUITE")
        print("🧪 " + "="*80)
        
        try:
            # Initialize database
            await init_db()
            print("✅ Database initialized")
            
            # Setup test data
            await self.setup_test_data()
            
            # Run all test categories
            await self.test_learning_gates()
            await self.test_progress_updates()
            await self.test_achievements()
            await self.test_analytics()
            await self.test_integration()
            
            print("\n🎉 " + "="*80)
            print("🎉 ALL EDUCATIONAL SCAFFOLDING TESTS COMPLETED SUCCESSFULLY!")
            print("🎉 Phase 6 is ready for production use")
            print("🎉 " + "="*80)
            
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in educational scaffolding tests: {str(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return False
        
        return True
    
    async def setup_test_data(self):
        """Setup test data for educational scaffolding tests"""
        print("\n📋 Setting up test data...")
        
        # Create test user with assessment data
        test_user = {
            "_id": self.test_user_id,
            "email": "test@educational-scaffolding.com",
            "name": "Educational Test User",
            "last_assessment_data": {
                "language": self.test_language,
                "level": self.test_level,
                "overall_score": 75,
                "pronunciation": {"score": 80},
                "grammar": {"score": 70},
                "vocabulary": {"score": 75},
                "fluency": {"score": 72},
                "coherence": {"score": 78}
            },
            "practice_sessions_used": 5,
            "practice_minutes_used": 25.0,
            "subscription_status": "active",
            "subscription_plan": "fluency_builder",
            "vocabulary_learned": [],
            "grammar_improvements": []
        }
        
        # Insert or update test user
        await database.users.replace_one(
            {"_id": self.test_user_id},
            test_user,
            upsert=True
        )
        
        # Create test world
        test_world = {
            "id": self.test_world_id,
            "title": "Medieval Adventure",
            "description": "A collaborative medieval fantasy story",
            "language": self.test_language,
            "target_level": self.test_level,
            "status": "active",
            "creator_id": "system",
            "contributors": [],
            "created_at": datetime.utcnow()
        }
        
        await database.story_worlds.replace_one(
            {"id": self.test_world_id},
            test_world,
            upsert=True
        )
        
        # Create recent conversation session (for recent practice gate)
        recent_session = {
            "user_id": self.test_user_id,
            "language": self.test_language,
            "level": self.test_level,
            "duration_minutes": 5.0,
            "created_at": datetime.utcnow() - timedelta(days=1)  # 1 day ago
        }
        
        await database.conversation_sessions.insert_one(recent_session)
        
        print("✅ Test data setup completed")
    
    async def test_learning_gates(self):
        """Test all learning gate checks"""
        print("\n🚪 Testing Learning Gates...")
        
        # Test 1: All gates should pass for properly setup user
        print("  🔍 Test 1: All gates passing...")
        result = await EducationalScaffoldingService.check_learning_gates(
            user_id=self.test_user_id,
            world_id=self.test_world_id,
            language=self.test_language
        )
        
        assert result.can_contribute == True, f"Expected can_contribute=True, got {result.can_contribute}"
        assert result.gate_checks["assessment_completed"] == True, "Assessment gate should pass"
        assert result.gate_checks["level_match"] == True, "Level match gate should pass"
        assert result.gate_checks["recent_practice"] == True, "Recent practice gate should pass"
        assert result.gate_checks["sessions_remaining"] == True, "Sessions remaining gate should pass"
        print("    ✅ All gates passing correctly")
        
        # Test 2: Level mismatch (user B1, world C2)
        print("  🔍 Test 2: Level mismatch...")
        await database.story_worlds.update_one(
            {"id": self.test_world_id},
            {"$set": {"target_level": "C2"}}
        )
        
        result = await EducationalScaffoldingService.check_learning_gates(
            user_id=self.test_user_id,
            world_id=self.test_world_id,
            language=self.test_language
        )
        
        assert result.can_contribute == False, "Should not be able to contribute with level mismatch"
        assert result.gate_checks["level_match"] == False, "Level match gate should fail"
        assert "level doesn't match" in " ".join(result.blocking_reasons).lower(), "Should mention level mismatch"
        print("    ✅ Level mismatch correctly blocked")
        
        # Reset world level
        await database.story_worlds.update_one(
            {"id": self.test_world_id},
            {"$set": {"target_level": self.test_level}}
        )
        
        # Test 3: No recent practice (old session)
        print("  🔍 Test 3: No recent practice...")
        await database.conversation_sessions.update_many(
            {"user_id": self.test_user_id},
            {"$set": {"created_at": datetime.utcnow() - timedelta(days=10)}}  # 10 days ago
        )
        
        result = await EducationalScaffoldingService.check_learning_gates(
            user_id=self.test_user_id,
            world_id=self.test_world_id,
            language=self.test_language
        )
        
        assert result.can_contribute == False, "Should not be able to contribute without recent practice"
        assert result.gate_checks["recent_practice"] == False, "Recent practice gate should fail"
        assert result.days_since_practice >= 7, "Should show days since practice"
        print("    ✅ No recent practice correctly blocked")
        
        # Reset recent session
        await database.conversation_sessions.update_many(
            {"user_id": self.test_user_id},
            {"$set": {"created_at": datetime.utcnow() - timedelta(days=1)}}
        )
        
        # Test 4: No assessment data
        print("  🔍 Test 4: No assessment data...")
        await database.users.update_one(
            {"_id": self.test_user_id},
            {"$unset": {"last_assessment_data": ""}}
        )
        
        result = await EducationalScaffoldingService.check_learning_gates(
            user_id=self.test_user_id,
            world_id=self.test_world_id,
            language=self.test_language
        )
        
        assert result.can_contribute == False, "Should not be able to contribute without assessment"
        assert result.gate_checks["assessment_completed"] == False, "Assessment gate should fail"
        assert "assessment" in " ".join(result.blocking_reasons).lower(), "Should mention assessment requirement"
        print("    ✅ No assessment correctly blocked")
        
        # Reset assessment data
        await database.users.update_one(
            {"_id": self.test_user_id},
            {"$set": {
                "last_assessment_data": {
                    "language": self.test_language,
                    "level": self.test_level,
                    "overall_score": 75
                }
            }}
        )
        
        print("✅ Learning Gates tests completed")
    
    async def test_progress_updates(self):
        """Test story progress updates and integration"""
        print("\n📈 Testing Progress Updates...")
        
        # Test progress update
        progress_update = StoryProgressUpdate(
            user_id=self.test_user_id,
            world_id=self.test_world_id,
            session_duration_minutes=8.5,
            vocabulary_learned=[
                {"word": "castle", "context": "medieval story", "learned_at": datetime.utcnow()},
                {"word": "knight", "context": "brave warrior", "learned_at": datetime.utcnow()}
            ],
            grammar_improvements=[
                {"area": "past_tense", "improvement": "Better use of past perfect", "score_improvement": 0.2}
            ],
            pronunciation_improvements=[
                {"phoneme": "/θ/", "word": "think", "improvement": 0.15}
            ],
            cultural_insights=[
                {"insight": "Medieval castle architecture", "context": "story setting"}
            ],
            engagement_score=0.85,
            contribution_quality=0.78,
            collaboration_score=0.82
        )
        
        print("  🔍 Test 1: Story progress update...")
        success = await EducationalScaffoldingService.update_story_progress(progress_update)
        assert success == True, "Progress update should succeed"
        print("    ✅ Progress update successful")
        
        # Verify story learning metrics were created
        print("  🔍 Test 2: Story learning metrics creation...")
        metrics = await database.story_learning_metrics.find_one({
            "user_id": self.test_user_id,
            "world_id": self.test_world_id
        })
        
        assert metrics is not None, "Story learning metrics should be created"
        assert len(metrics["vocabulary_acquired"]) == 2, "Should have 2 vocabulary items"
        assert len(metrics["grammar_improvements"]) == 1, "Should have 1 grammar improvement"
        assert metrics["story_engagement_score"] == 0.85, "Should have correct engagement score"
        print("    ✅ Story learning metrics created correctly")
        
        # Verify main progress integration
        print("  🔍 Test 3: Main progress integration...")
        user = await database.users.find_one({"_id": self.test_user_id})
        
        # Check subscription usage was updated
        assert user["practice_sessions_used"] > 5, "Session count should be incremented"
        assert user["practice_minutes_used"] > 25.0, "Minutes should be incremented"
        
        # Check vocabulary integration
        vocab_learned = user.get("vocabulary_learned", [])
        story_vocab = [v for v in vocab_learned if v.get("source") == "story_world"]
        assert len(story_vocab) == 2, "Should have 2 story vocabulary items in main progress"
        print("    ✅ Main progress integration working")
        
        print("✅ Progress Updates tests completed")
    
    async def test_achievements(self):
        """Test story achievement system"""
        print("\n🏆 Testing Achievements...")
        
        # Create a story contribution to trigger "Story Pioneer" achievement
        print("  🔍 Test 1: Story Pioneer achievement...")
        await database.story_contributions.insert_one({
            "user_id": self.test_user_id,
            "world_id": self.test_world_id,
            "content": "Test contribution",
            "created_at": datetime.utcnow()
        })
        
        # Trigger achievement check
        await EducationalScaffoldingService._check_story_achievements(self.test_user_id)
        
        # Verify achievement was awarded
        achievement = await database.user_story_achievements.find_one({
            "user_id": self.test_user_id,
            "achievement_id": "story_pioneer"
        })
        
        assert achievement is not None, "Story Pioneer achievement should be awarded"
        print("    ✅ Story Pioneer achievement awarded")
        
        # Test achievement retrieval
        print("  🔍 Test 2: Achievement retrieval...")
        achievements = await EducationalScaffoldingService.get_user_story_achievements(self.test_user_id)
        
        assert len(achievements) >= 1, "Should have at least 1 achievement"
        pioneer_achievement = next((a for a in achievements if a["id"] == "story_pioneer"), None)
        assert pioneer_achievement is not None, "Should include Story Pioneer achievement"
        assert pioneer_achievement["earned"] == True, "Achievement should be marked as earned"
        print("    ✅ Achievement retrieval working")
        
        print("✅ Achievements tests completed")
    
    async def test_analytics(self):
        """Test story learning analytics"""
        print("\n📊 Testing Analytics...")
        
        # Test analytics generation
        print("  🔍 Test 1: Story learning analytics...")
        analytics = await EducationalScaffoldingService.get_story_learning_analytics(
            user_id=self.test_user_id,
            language=self.test_language
        )
        
        assert analytics is not None, "Analytics should be generated"
        assert analytics.total_story_sessions >= 1, "Should have at least 1 story session"
        assert analytics.total_contributions >= 1, "Should have at least 1 contribution"
        assert analytics.total_worlds_participated >= 1, "Should have participated in at least 1 world"
        assert analytics.current_effective_level == self.test_level, "Should have correct effective level"
        print("    ✅ Story learning analytics generated")
        
        # Test user statistics
        print("  🔍 Test 2: User story statistics...")
        stats = await EducationalScaffoldingService._get_user_story_statistics(self.test_user_id)
        
        assert stats["contributions"] >= 1, "Should have at least 1 contribution"
        assert stats["vocabulary_learned"] >= 2, "Should have learned vocabulary"
        print("    ✅ User story statistics calculated")
        
        print("✅ Analytics tests completed")
    
    async def test_integration(self):
        """Test integration with existing systems"""
        print("\n🔗 Testing System Integration...")
        
        # Test level compatibility checking
        print("  🔍 Test 1: Level compatibility...")
        compatible = EducationalScaffoldingService._check_level_compatibility("B1", "B2")
        assert compatible == True, "B1 should be compatible with B2 (±1 level)"
        
        compatible = EducationalScaffoldingService._check_level_compatibility("A1", "C1")
        assert compatible == False, "A1 should not be compatible with C1 (>1 level difference)"
        print("    ✅ Level compatibility working")
        
        # Test level advancement recommendation
        print("  🔍 Test 2: Level advancement...")
        await EducationalScaffoldingService._check_level_advancement(self.test_user_id, self.test_world_id)
        
        # Check if recommendation was created (high performance scores should trigger it)
        user = await database.users.find_one({"_id": self.test_user_id})
        # Note: Recommendation only triggers with high performance (>0.8) and multiple contributions
        print("    ✅ Level advancement check completed")
        
        # Test subscription integration
        print("  🔍 Test 3: Subscription integration...")
        user_before = await database.users.find_one({"_id": self.test_user_id})
        sessions_before = user_before["practice_sessions_used"]
        minutes_before = user_before["practice_minutes_used"]
        
        # Simulate another progress update
        await EducationalScaffoldingService._update_subscription_usage(self.test_user_id, 5.0)
        
        user_after = await database.users.find_one({"_id": self.test_user_id})
        assert user_after["practice_sessions_used"] > sessions_before, "Sessions should be incremented"
        assert user_after["practice_minutes_used"] > minutes_before, "Minutes should be incremented"
        print("    ✅ Subscription integration working")
        
        print("✅ System Integration tests completed")
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Remove test collections data
        await database.users.delete_many({"_id": self.test_user_id})
        await database.story_worlds.delete_many({"id": self.test_world_id})
        await database.conversation_sessions.delete_many({"user_id": self.test_user_id})
        await database.story_contributions.delete_many({"user_id": self.test_user_id})
        await database.story_learning_metrics.delete_many({"user_id": self.test_user_id})
        await database.user_story_achievements.delete_many({"user_id": self.test_user_id})
        
        print("✅ Test data cleaned up")

async def main():
    """Main test function"""
    tester = EducationalScaffoldingTester()
    
    try:
        success = await tester.run_all_tests()
        if success:
            print("\n🎉 All tests passed! Educational Scaffolding Phase 6 is ready!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return 1
    finally:
        # Always cleanup
        try:
            await tester.cleanup_test_data()
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup error: {str(cleanup_error)}")

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
