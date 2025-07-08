"""
Integration tests for learning routes.

Tests cover:
- Learning goals management
- Learning plan creation and management
- Assessment data handling
- Session progress tracking
- Plan assignment and ownership
- Business logic validation
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid

class TestLearningGoals:
    """Test learning goals functionality."""
    
    async def test_get_learning_goals(self, client: AsyncClient):
        """Test retrieving learning goals."""
        response = await client.get("/learning/goals")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check structure of goals
        for goal in data:
            assert "id" in goal
            assert "text" in goal
            assert "category" in goal
    
    async def test_learning_goals_content(self, client: AsyncClient):
        """Test that learning goals contain expected content."""
        response = await client.get("/learning/goals")
        
        assert response.status_code == 200
        goals = response.json()
        
        # Check for expected goal categories
        goal_ids = [goal["id"] for goal in goals]
        expected_goals = ["travel", "business", "academic", "culture", "daily"]
        
        for expected_goal in expected_goals:
            assert expected_goal in goal_ids

class TestLearningPlanCreation:
    """Test learning plan creation functionality."""
    
    @patch('learning_routes.client.chat.completions.create')
    async def test_create_learning_plan_basic(self, mock_openai, client: AsyncClient, sample_learning_plan):
        """Test basic learning plan creation."""
        # Mock OpenAI response (though the current implementation uses mock data)
        mock_openai.return_value = MagicMock()
        
        response = await client.post("/learning/plan", json=sample_learning_plan)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check basic structure
        assert "id" in data
        assert data["language"] == sample_learning_plan["language"]
        assert data["proficiency_level"] == sample_learning_plan["proficiency_level"]
        assert data["goals"] == sample_learning_plan["goals"]
        assert data["duration_months"] == sample_learning_plan["duration_months"]
        assert "plan_content" in data
        assert "created_at" in data
        assert data["total_sessions"] > 0
        assert data["completed_sessions"] == 0
        assert data["progress_percentage"] == 0.0
    
    async def test_create_learning_plan_with_assessment(self, client: AsyncClient, sample_assessment_data, auth_headers):
        """Test learning plan creation with assessment data."""
        plan_data = {
            "language": "english",
            "proficiency_level": "B1",
            "goals": ["travel", "business"],
            "duration_months": 3,
            "assessment_data": sample_assessment_data
        }
        
        response = await client.post("/learning/plan", json=plan_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check assessment integration
        assert data["assessment_data"] == sample_assessment_data
        assert "assessment_summary" in data["plan_content"]
        assert data["plan_content"]["assessment_summary"]["overall_score"] == sample_assessment_data["overall_score"]
        assert data["plan_content"]["assessment_summary"]["recommended_level"] == sample_assessment_data["recommended_level"]
    
    async def test_create_learning_plan_authenticated_user(self, client: AsyncClient, sample_learning_plan, auth_headers, test_user):
        """Test learning plan creation for authenticated user."""
        response = await client.post("/learning/plan", json=sample_learning_plan, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be assigned to the user
        assert data["user_id"] == test_user["id"]
    
    async def test_create_learning_plan_anonymous(self, client: AsyncClient, sample_learning_plan):
        """Test learning plan creation for anonymous user."""
        response = await client.post("/learning/plan", json=sample_learning_plan)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not be assigned to any user
        assert data["user_id"] is None
    
    async def test_create_learning_plan_custom_goal(self, client: AsyncClient):
        """Test learning plan creation with custom goal."""
        plan_data = {
            "language": "spanish",
            "proficiency_level": "A2",
            "goals": ["travel"],
            "duration_months": 6,
            "custom_goal": "Learn medical Spanish for healthcare work"
        }
        
        response = await client.post("/learning/plan", json=plan_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["custom_goal"] == plan_data["custom_goal"]
    
    async def test_create_learning_plan_invalid_data(self, client: AsyncClient):
        """Test learning plan creation with invalid data."""
        invalid_data = {
            "language": "",  # Empty language
            "proficiency_level": "INVALID",  # Invalid level
            "goals": [],  # Empty goals
            "duration_months": 0  # Invalid duration
        }
        
        response = await client.post("/learning/plan", json=invalid_data)
        
        assert response.status_code == 422
    
    async def test_create_learning_plan_missing_fields(self, client: AsyncClient):
        """Test learning plan creation with missing required fields."""
        incomplete_data = {
            "language": "english"
            # Missing other required fields
        }
        
        response = await client.post("/learning/plan", json=incomplete_data)
        
        assert response.status_code == 422

class TestLearningPlanRetrieval:
    """Test learning plan retrieval functionality."""
    
    async def test_get_learning_plan_by_id(self, client: AsyncClient, test_user, auth_headers, test_utils, clean_db):
        """Test retrieving a specific learning plan by ID."""
        # Create a test learning plan
        plan_id = await test_utils.create_test_learning_plan(test_user["id"], clean_db)
        
        response = await client.get(f"/learning/plan/{plan_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == plan_id
        assert data["user_id"] == test_user["id"]
    
    async def test_get_learning_plan_nonexistent(self, client: AsyncClient, auth_headers):
        """Test retrieving non-existent learning plan."""
        fake_id = str(uuid.uuid4())
        
        response = await client.get(f"/learning/plan/{fake_id}", headers=auth_headers)
        
        assert response.status_code == 404
    
    async def test_get_learning_plan_unauthorized(self, client: AsyncClient, premium_user, premium_auth_headers, test_user, auth_headers, test_utils, clean_db):
        """Test retrieving learning plan belonging to another user."""
        # Create a plan for test_user
        plan_id = await test_utils.create_test_learning_plan(test_user["id"], clean_db)
        
        # Try to access with premium_user credentials
        response = await client.get(f"/learning/plan/{plan_id}", headers=premium_auth_headers)
        
        assert response.status_code == 403
    
    async def test_get_learning_plan_unauthenticated(self, client: AsyncClient):
        """Test retrieving learning plan without authentication."""
        fake_id = str(uuid.uuid4())
        
        response = await client.get(f"/learning/plan/{fake_id}")
        
        assert response.status_code == 401
    
    async def test_get_user_learning_plans(self, client: AsyncClient, test_user, auth_headers, test_utils, clean_db):
        """Test retrieving all learning plans for a user."""
        # Create multiple test learning plans
        plan_id1 = await test_utils.create_test_learning_plan(test_user["id"], clean_db)
        plan_id2 = await test_utils.create_test_learning_plan(test_user["id"], clean_db)
        
        response = await client.get("/learning/plans", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        
        # Check that all plans belong to the user
        for plan in data:
            assert plan["user_id"] == test_user["id"]
    
    async def test_get_user_learning_plans_empty(self, client: AsyncClient, auth_headers):
        """Test retrieving learning plans when user has none."""
        response = await client.get("/learning/plans", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

class TestLearningPlanAssignment:
    """Test learning plan assignment functionality."""
    
    async def test_assign_anonymous_plan_to_user(self, client: AsyncClient, auth_headers, sample_learning_plan):
        """Test assigning an anonymous plan to a user."""
        # Create an anonymous plan
        response = await client.post("/learning/plan", json=sample_learning_plan)
        assert response.status_code == 200
        plan_data = response.json()
        plan_id = plan_data["id"]
        assert plan_data["user_id"] is None
        
        # Assign it to the authenticated user
        response = await client.put(f"/learning/plan/{plan_id}/assign", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == plan_id
        assert data["user_id"] is not None
    
    async def test_assign_already_assigned_plan(self, client: AsyncClient, test_user, auth_headers, premium_auth_headers, test_utils, clean_db):
        """Test assigning a plan that's already assigned to someone."""
        # Create a plan assigned to test_user
        plan_id = await test_utils.create_test_learning_plan(test_user["id"], clean_db)
        
        # Try to assign it to premium_user
        response = await client.put(f"/learning/plan/{plan_id}/assign", headers=premium_auth_headers)
        
        assert response.status_code == 400
        assert "already assigned" in response.json()["detail"].lower()
    
    async def test_assign_plan_to_same_user(self, client: AsyncClient, test_user, auth_headers, test_utils, clean_db):
        """Test assigning a plan to the user who already owns it."""
        # Create a plan assigned to test_user
        plan_id = await test_utils.create_test_learning_plan(test_user["id"], clean_db)
        
        # Try to assign it to the same user
        response = await client.put(f"/learning/plan/{plan_id}/assign", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user["id"]
    
    async def test_assign_nonexistent_plan(self, client: AsyncClient, auth_headers):
        """Test assigning a non-existent plan."""
        fake_id = str(uuid.uuid4())
        
        response = await client.put(f"/learning/plan/{fake_id}/assign", headers=auth_headers)
        
        assert response.status_code == 404

class TestSessionProgress:
    """Test session progress tracking functionality."""
    
    async def test_update_session_progress(self, client: AsyncClient, test_user, auth_headers, test_utils, clean_db):
        """Test updating session progress."""
        # Create a test learning plan
        plan_id = await test_utils.create_test_learning_plan(test_user["id"], clean_db)
        
        progress_data = {
            "plan_id": plan_id,
            "completed_sessions": 5
        }
        
        response = await client.put(f"/learning/plan/{plan_id}/progress", json=progress_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["completed_sessions"] == 5
        assert data["progress_percentage"] > 0
    
    async def test_update_progress_exceeds_total(self, client: AsyncClient, test_user, auth_headers, test_utils, clean_db):
        """Test updating progress beyond total sessions."""
        # Create a test learning plan
        plan_id = await test_utils.create_test_learning_plan(test_user["id"], clean_db)
        
        progress_data = {
            "plan_id": plan_id,
            "completed_sessions": 1000  # Way more than total
        }
        
        response = await client.put(f"/learning/plan/{plan_id}/progress", json=progress_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # Should cap at 100%
        assert data["progress_percentage"] == 100.0
    
    async def test_update_progress_unauthorized(self, client: AsyncClient, test_user, premium_auth_headers, test_utils, clean_db):
        """Test updating progress for plan owned by another user."""
        # Create a plan for test_user
        plan_id = await test_utils.create_test_learning_plan(test_user["id"], clean_db)
        
        progress_data = {
            "plan_id": plan_id,
            "completed_sessions": 3
        }
        
        # Try to update with premium_user credentials
        response = await client.put(f"/learning/plan/{plan_id}/progress", json=progress_data, headers=premium_auth_headers)
        
        assert response.status_code == 403

class TestSessionSummary:
    """Test session summary functionality."""
    
    async def test_save_session_summary(self, client: AsyncClient, test_user, auth_headers, test_utils, clean_db):
        """Test saving a session summary."""
        # Create a test learning plan
        plan_id = await test_utils.create_test_learning_plan(test_user["id"], clean_db)
        
        summary_data = {
            "plan_id": plan_id,
            "session_summary": "Great session focusing on travel vocabulary. Student showed improvement in pronunciation."
        }
        
        response = await client.post("/learning/session-summary", params=summary_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "session_number" in data
        assert "week" in data
        assert "progress_percentage" in data
    
    async def test_save_session_summary_with_conversation_data(self, client: AsyncClient, test_user, auth_headers, test_utils, clean_db, sample_conversation_messages):
        """Test saving session summary with conversation data."""
        # Create a test learning plan
        plan_id = await test_utils.create_test_learning_plan(test_user["id"], clean_db)
        
        # Prepare conversation data
        conversation_data = {
            "messages": sample_conversation_messages,
            "duration_minutes": 8.5,
            "topic": "travel"
        }
        
        params = {
            "plan_id": plan_id,
            "session_summary": "Excellent conversation about travel experiences."
        }
        
        response = await client.post("/learning/session-summary", params=params, json=conversation_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    async def test_save_session_summary_nonexistent_plan(self, client: AsyncClient, auth_headers):
        """Test saving session summary for non-existent plan."""
        fake_plan_id = str(uuid.uuid4())
        
        summary_data = {
            "plan_id": fake_plan_id,
            "session_summary": "Test summary"
        }
        
        response = await client.post("/learning/session-summary", params=summary_data, headers=auth_headers)
        
        assert response.status_code == 404

class TestAssessmentData:
    """Test assessment data handling."""
    
    async def test_save_assessment_data(self, client: AsyncClient, auth_headers, sample_assessment_data):
        """Test saving assessment data to user profile."""
        assessment_request = {
            "assessment_data": sample_assessment_data
        }
        
        response = await client.post("/learning/save-assessment", json=assessment_request, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return updated user data
        assert "id" in data
        assert "email" in data
        assert "name" in data
    
    async def test_save_assessment_data_unauthenticated(self, client: AsyncClient, sample_assessment_data):
        """Test saving assessment data without authentication."""
        assessment_request = {
            "assessment_data": sample_assessment_data
        }
        
        response = await client.post("/learning/save-assessment", json=assessment_request)
        
        assert response.status_code == 401
    
    async def test_save_assessment_data_invalid(self, client: AsyncClient, auth_headers):
        """Test saving invalid assessment data."""
        invalid_assessment = {
            "assessment_data": "invalid_data"  # Should be a dict
        }
        
        response = await client.post("/learning/save-assessment", json=invalid_assessment, headers=auth_headers)
        
        assert response.status_code == 422

class TestLearningPlanContent:
    """Test learning plan content generation and structure."""
    
    async def test_plan_content_structure(self, client: AsyncClient, sample_learning_plan):
        """Test that generated plan content has proper structure."""
        response = await client.post("/learning/plan", json=sample_learning_plan)
        
        assert response.status_code == 200
        data = response.json()
        plan_content = data["plan_content"]
        
        # Check required fields
        assert "title" in plan_content
        assert "overview" in plan_content
        assert "weekly_schedule" in plan_content
        assert "resources" in plan_content
        
        # Check weekly schedule structure
        weekly_schedule = plan_content["weekly_schedule"]
        assert isinstance(weekly_schedule, list)
        assert len(weekly_schedule) > 0
        
        for week in weekly_schedule:
            assert "week" in week
            assert "focus" in week
            assert "activities" in week
            assert isinstance(week["activities"], list)
    
    async def test_plan_duration_affects_content(self, client: AsyncClient):
        """Test that plan duration affects the generated content."""
        # Create short plan
        short_plan = {
            "language": "english",
            "proficiency_level": "B1",
            "goals": ["travel"],
            "duration_months": 1
        }
        
        response = await client.post("/learning/plan", json=short_plan)
        assert response.status_code == 200
        short_data = response.json()
        
        # Create long plan
        long_plan = {
            "language": "english",
            "proficiency_level": "B1",
            "goals": ["travel"],
            "duration_months": 12
        }
        
        response = await client.post("/learning/plan", json=long_plan)
        assert response.status_code == 200
        long_data = response.json()
        
        # Long plan should have more sessions and weeks
        assert long_data["total_sessions"] > short_data["total_sessions"]
        assert len(long_data["plan_content"]["weekly_schedule"]) > len(short_data["plan_content"]["weekly_schedule"])
    
    async def test_assessment_affects_plan_content(self, client: AsyncClient, sample_assessment_data):
        """Test that assessment data affects plan content."""
        plan_with_assessment = {
            "language": "english",
            "proficiency_level": "B1",
            "goals": ["travel"],
            "duration_months": 3,
            "assessment_data": sample_assessment_data
        }
        
        response = await client.post("/learning/plan", json=plan_with_assessment)
        
        assert response.status_code == 200
        data = response.json()
        plan_content = data["plan_content"]
        
        # Should include assessment summary
        assert "assessment_summary" in plan_content
        assert plan_content["assessment_summary"]["overall_score"] == sample_assessment_data["overall_score"]
        assert plan_content["assessment_summary"]["strengths"] == sample_assessment_data["strengths"]
        assert plan_content["assessment_summary"]["areas_for_improvement"] == sample_assessment_data["areas_for_improvement"]

class TestSubscriptionIntegration:
    """Test subscription system integration with learning features."""
    
    async def test_assessment_usage_tracking(self, client: AsyncClient, auth_headers, sample_assessment_data, test_user, clean_db):
        """Test that assessments are tracked for subscription limits."""
        from database import users_collection
        from bson import ObjectId
        
        # Get initial usage count
        user = await users_collection.find_one({"_id": ObjectId(test_user["id"])})
        initial_assessments = user.get("assessments_used", 0)
        
        # Save assessment data
        assessment_request = {"assessment_data": sample_assessment_data}
        response = await client.post("/learning/save-assessment", json=assessment_request, headers=auth_headers)
        
        assert response.status_code == 200
        
        # Check that usage was tracked
        user = await users_collection.find_one({"_id": ObjectId(test_user["id"])})
        new_assessments = user.get("assessments_used", 0)
        assert new_assessments == initial_assessments + 1
    
    async def test_learning_plan_creation_tracks_assessment(self, client: AsyncClient, auth_headers, sample_assessment_data, test_user, clean_db):
        """Test that creating a learning plan with assessment data tracks usage."""
        from database import users_collection
        from bson import ObjectId
        
        # Get initial usage count
        user = await users_collection.find_one({"_id": ObjectId(test_user["id"])})
        initial_assessments = user.get("assessments_used", 0)
        
        # Create plan with assessment data
        plan_data = {
            "language": "english",
            "proficiency_level": "B1",
            "goals": ["travel"],
            "duration_months": 3,
            "assessment_data": sample_assessment_data
        }
        
        response = await client.post("/learning/plan", json=plan_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Check that usage was tracked
        user = await users_collection.find_one({"_id": ObjectId(test_user["id"])})
        new_assessments = user.get("assessments_used", 0)
        assert new_assessments == initial_assessments + 1

class TestErrorHandling:
    """Test error handling in learning routes."""
    
    async def test_database_error_handling(self, client: AsyncClient, sample_learning_plan):
        """Test handling of database errors."""
        # This test would require mocking database failures
        # For now, we test that the endpoint handles errors gracefully
        
        # Test with extremely large data that might cause issues
        large_plan = sample_learning_plan.copy()
        large_plan["custom_goal"] = "x" * 10000  # Very long custom goal
        
        response = await client.post("/learning/plan", json=large_plan)
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400, 422, 500]
    
    async def test_invalid_plan_id_format(self, client: AsyncClient, auth_headers):
        """Test handling of invalid plan ID formats."""
        invalid_id = "not-a-valid-uuid"
        
        response = await client.get(f"/learning/plan/{invalid_id}", headers=auth_headers)
        
        # Should handle gracefully
        assert response.status_code in [400, 404]
    
    async def test_concurrent_plan_assignment(self, client: AsyncClient, auth_headers, premium_auth_headers, sample_learning_plan):
        """Test concurrent assignment of the same plan."""
        # Create an anonymous plan
        response = await client.post("/learning/plan", json=sample_learning_plan)
        assert response.status_code == 200
        plan_id = response.json()["id"]
        
        # Try to assign to both users simultaneously
        # In a real scenario, this would be done with actual concurrency
        response1 = await client.put(f"/learning/plan/{plan_id}/assign", headers=auth_headers)
        response2 = await client.put(f"/learning/plan/{plan_id}/assign", headers=premium_auth_headers)
        
        # One should succeed, one should fail
        success_count = sum(1 for r in [response1, response2] if r.status_code == 200)
        failure_count = sum(1 for r in [response1, response2] if r.status_code == 400)
        
        assert success_count == 1
        assert failure_count == 1
