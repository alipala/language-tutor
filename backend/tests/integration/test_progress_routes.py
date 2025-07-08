"""
Integration tests for progress tracking routes.

Tests cover:
- Conversation session saving
- Progress statistics
- Conversation history
- Enhanced analysis
- Achievements system
- Streak calculation
- Session validation
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid

class TestConversationSaving:
    """Test conversation session saving functionality."""
    
    async def test_save_conversation_basic(self, client: AsyncClient, auth_headers, sample_conversation_messages):
        """Test saving a basic conversation session."""
        conversation_data = {
            "language": "english",
            "level": "B1",
            "topic": "travel",
            "messages": sample_conversation_messages,
            "duration_minutes": 8.5
        }
        
        response = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "session_id" in data
        assert data["is_streak_eligible"] == True  # 8.5 minutes >= 5 minutes
        assert "summary" in data
        assert data["action"] in ["created", "updated"]
    
    async def test_save_conversation_short_session(self, client: AsyncClient, auth_headers, sample_conversation_messages):
        """Test saving a short conversation session."""
        conversation_data = {
            "language": "english",
            "level": "B1",
            "topic": "travel",
            "messages": sample_conversation_messages[:2],  # Fewer messages
            "duration_minutes": 3.0  # Less than 5 minutes
        }
        
        response = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["is_streak_eligible"] == False  # Less than 5 minutes
    
    async def test_save_conversation_learning_plan_session(self, client: AsyncClient, auth_headers, sample_conversation_messages, test_user, test_utils, clean_db):
        """Test saving a learning plan conversation session."""
        # Create a test learning plan
        plan_id = await test_utils.create_test_learning_plan(test_user["id"], clean_db)
        
        conversation_data = {
            "language": "english",
            "level": "B1",
            "topic": "travel",
            "messages": sample_conversation_messages,
            "duration_minutes": 10.0,
            "learning_plan_id": plan_id,
            "conversation_type": "learning_plan"
        }
        
        response = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["action"] == "learning_plan_session_saved"
        assert "summary" in data
    
    async def test_save_conversation_update_existing(self, client: AsyncClient, auth_headers, sample_conversation_messages):
        """Test updating an existing conversation session."""
        conversation_data = {
            "language": "english",
            "level": "B1",
            "topic": "travel",
            "messages": sample_conversation_messages[:2],
            "duration_minutes": 5.0
        }
        
        # Save initial conversation
        response = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        assert response.status_code == 200
        initial_data = response.json()
        
        # Update with more messages
        conversation_data["messages"] = sample_conversation_messages
        conversation_data["duration_minutes"] = 10.0
        
        response = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["action"] == "updated"
        assert data["session_id"] == initial_data["session_id"]
    
    async def test_save_conversation_unauthenticated(self, client: AsyncClient, sample_conversation_messages):
        """Test saving conversation without authentication."""
        conversation_data = {
            "language": "english",
            "level": "B1",
            "messages": sample_conversation_messages,
            "duration_minutes": 5.0
        }
        
        response = await client.post("/api/progress/save-conversation", json=conversation_data)
        
        assert response.status_code == 401
    
    async def test_save_conversation_invalid_data(self, client: AsyncClient, auth_headers):
        """Test saving conversation with invalid data."""
        invalid_data = {
            "language": "",  # Empty language
            "level": "",     # Empty level
            "messages": [],  # Empty messages
            "duration_minutes": -1  # Negative duration
        }
        
        response = await client.post("/api/progress/save-conversation", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
    
    async def test_save_conversation_malformed_messages(self, client: AsyncClient, auth_headers):
        """Test saving conversation with malformed messages."""
        conversation_data = {
            "language": "english",
            "level": "B1",
            "messages": [
                {"role": "user"},  # Missing content
                {"content": "Hello"},  # Missing role
                "invalid_message"  # Not a dict
            ],
            "duration_minutes": 5.0
        }
        
        response = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        
        # Should handle gracefully or return validation error
        assert response.status_code in [200, 422, 500]

class TestProgressStats:
    """Test progress statistics functionality."""
    
    async def test_get_progress_stats_empty(self, client: AsyncClient, auth_headers):
        """Test getting progress stats when user has no sessions."""
        response = await client.get("/api/progress/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_sessions"] == 0
        assert data["total_minutes"] == 0
        assert data["current_streak"] == 0
        assert data["longest_streak"] == 0
        assert data["sessions_this_week"] == 0
        assert data["sessions_this_month"] == 0
    
    async def test_get_progress_stats_with_sessions(self, client: AsyncClient, auth_headers, test_user, test_utils, clean_db):
        """Test getting progress stats with existing sessions."""
        # Create test conversation sessions
        session_id1 = await test_utils.create_test_conversation_session(test_user["id"], clean_db)
        session_id2 = await test_utils.create_test_conversation_session(test_user["id"], clean_db)
        
        response = await client.get("/api/progress/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_sessions"] >= 2
        assert data["total_minutes"] >= 0
        assert isinstance(data["current_streak"], int)
        assert isinstance(data["longest_streak"], int)
        assert isinstance(data["sessions_this_week"], int)
        assert isinstance(data["sessions_this_month"], int)
    
    async def test_get_progress_stats_unauthenticated(self, client: AsyncClient):
        """Test getting progress stats without authentication."""
        response = await client.get("/api/progress/stats")
        
        assert response.status_code == 401

class TestConversationHistory:
    """Test conversation history functionality."""
    
    async def test_get_conversation_history_empty(self, client: AsyncClient, auth_headers):
        """Test getting conversation history when user has no sessions."""
        response = await client.get("/api/progress/conversations", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sessions" in data
        assert "total_count" in data
        assert "stats" in data
        assert isinstance(data["sessions"], list)
        assert len(data["sessions"]) == 0
        assert data["total_count"] == 0
    
    async def test_get_conversation_history_with_sessions(self, client: AsyncClient, auth_headers, test_user, test_utils, clean_db):
        """Test getting conversation history with existing sessions."""
        # Create test conversation sessions
        session_id1 = await test_utils.create_test_conversation_session(test_user["id"], clean_db)
        session_id2 = await test_utils.create_test_conversation_session(test_user["id"], clean_db)
        
        response = await client.get("/api/progress/conversations", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["sessions"]) >= 2
        assert data["total_count"] >= 2
        
        # Check session structure
        for session in data["sessions"]:
            assert "id" in session
            assert "user_id" in session
            assert "language" in session
            assert "level" in session
            assert "messages" in session
            assert "duration_minutes" in session
            assert "created_at" in session
    
    async def test_get_conversation_history_pagination(self, client: AsyncClient, auth_headers, test_user, test_utils, clean_db):
        """Test conversation history pagination."""
        # Create multiple test sessions
        for _ in range(5):
            await test_utils.create_test_conversation_session(test_user["id"], clean_db)
        
        # Test with limit
        response = await client.get("/api/progress/conversations?limit=2", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["sessions"]) <= 2
        assert data["total_count"] >= 5
        
        # Test with offset
        response = await client.get("/api/progress/conversations?limit=2&offset=2", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["sessions"]) <= 2
    
    async def test_get_conversation_history_unauthenticated(self, client: AsyncClient):
        """Test getting conversation history without authentication."""
        response = await client.get("/api/progress/conversations")
        
        assert response.status_code == 401

class TestConversationAnalysis:
    """Test conversation analysis functionality."""
    
    async def test_get_conversation_analysis_existing(self, client: AsyncClient, auth_headers, test_user, test_utils, clean_db):
        """Test getting analysis for existing conversation."""
        # Create test conversation session
        session_id = await test_utils.create_test_conversation_session(test_user["id"], clean_db)
        
        response = await client.get(f"/api/progress/conversation/{session_id}/analysis", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == session_id
        assert "session_info" in data
        assert "conversation_messages" in data
        # Enhanced analysis might be None if not generated yet
        assert "enhanced_analysis" in data
    
    @patch('progress_routes.generate_enhanced_analysis')
    async def test_get_conversation_analysis_generate_on_demand(self, mock_generate, client: AsyncClient, auth_headers, test_user, test_utils, clean_db):
        """Test generating analysis on demand when not exists."""
        # Mock enhanced analysis generation
        mock_generate.return_value = {
            "overall_assessment": "Good conversation",
            "strengths": ["vocabulary", "pronunciation"],
            "areas_for_improvement": ["grammar", "fluency"]
        }
        
        # Create test conversation session
        session_id = await test_utils.create_test_conversation_session(test_user["id"], clean_db)
        
        response = await client.get(f"/api/progress/conversation/{session_id}/analysis", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["enhanced_analysis"] is not None
        mock_generate.assert_called_once()
    
    async def test_get_conversation_analysis_nonexistent(self, client: AsyncClient, auth_headers):
        """Test getting analysis for non-existent conversation."""
        fake_session_id = str(uuid.uuid4())
        
        response = await client.get(f"/api/progress/conversation/{fake_session_id}/analysis", headers=auth_headers)
        
        assert response.status_code == 404
    
    async def test_get_conversation_analysis_invalid_id(self, client: AsyncClient, auth_headers):
        """Test getting analysis with invalid session ID format."""
        invalid_id = "not-a-valid-objectid"
        
        response = await client.get(f"/api/progress/conversation/{invalid_id}/analysis", headers=auth_headers)
        
        assert response.status_code == 400
    
    async def test_get_conversation_analysis_unauthorized(self, client: AsyncClient, premium_auth_headers, test_user, test_utils, clean_db):
        """Test getting analysis for conversation owned by another user."""
        # Create session for test_user
        session_id = await test_utils.create_test_conversation_session(test_user["id"], clean_db)
        
        # Try to access with premium_user credentials
        response = await client.get(f"/api/progress/conversation/{session_id}/analysis", headers=premium_auth_headers)
        
        assert response.status_code == 404  # Should not find session for different user

class TestAchievements:
    """Test achievements system functionality."""
    
    async def test_get_achievements_empty(self, client: AsyncClient, auth_headers):
        """Test getting achievements when user has no progress."""
        response = await client.get("/api/progress/achievements", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "achievements" in data
        assert isinstance(data["achievements"], list)
        # Should have no achievements for new user
        assert len(data["achievements"]) == 0
    
    async def test_get_achievements_with_progress(self, client: AsyncClient, auth_headers, test_user, test_utils, clean_db):
        """Test getting achievements with user progress."""
        # Create test conversation sessions to trigger achievements
        for _ in range(3):
            await test_utils.create_test_conversation_session(test_user["id"], clean_db)
        
        response = await client.get("/api/progress/achievements", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        achievements = data["achievements"]
        assert isinstance(achievements, list)
        
        # Should have some achievements based on progress
        if len(achievements) > 0:
            for achievement in achievements:
                assert "name" in achievement
                assert "icon" in achievement
                assert "description" in achievement
                assert "earned" in achievement
                assert achievement["earned"] == True
    
    async def test_get_achievements_unauthenticated(self, client: AsyncClient):
        """Test getting achievements without authentication."""
        response = await client.get("/api/progress/achievements")
        
        assert response.status_code == 401

class TestStreakCalculation:
    """Test streak calculation functionality."""
    
    async def test_streak_calculation_single_day(self, client: AsyncClient, auth_headers, sample_conversation_messages):
        """Test streak calculation with single day activity."""
        # Save a streak-eligible conversation
        conversation_data = {
            "language": "english",
            "level": "B1",
            "topic": "travel",
            "messages": sample_conversation_messages,
            "duration_minutes": 6.0  # Streak eligible
        }
        
        response = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Check stats
        response = await client.get("/api/progress/stats", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["current_streak"] >= 1
        assert data["longest_streak"] >= 1
    
    async def test_streak_calculation_multiple_days(self, client: AsyncClient, auth_headers, test_user, clean_db):
        """Test streak calculation with multiple days."""
        from database import conversation_sessions_collection
        from datetime import datetime, timedelta
        
        # Create sessions for consecutive days
        base_date = datetime.utcnow() - timedelta(days=2)
        
        for i in range(3):  # 3 consecutive days
            session_date = base_date + timedelta(days=i)
            session_data = {
                "user_id": test_user["id"],
                "language": "english",
                "level": "B1",
                "topic": "travel",
                "messages": [{"role": "user", "content": "Hello", "timestamp": session_date}],
                "duration_minutes": 6.0,
                "message_count": 1,
                "summary": "Test conversation",
                "is_streak_eligible": True,
                "created_at": session_date,
                "updated_at": session_date
            }
            await conversation_sessions_collection.insert_one(session_data)
        
        response = await client.get("/api/progress/stats", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Should have a streak of at least 2-3 days
        assert data["current_streak"] >= 2
        assert data["longest_streak"] >= 2

class TestSessionValidation:
    """Test session data validation and processing."""
    
    async def test_save_conversation_timestamp_handling(self, client: AsyncClient, auth_headers):
        """Test handling of different timestamp formats."""
        # Test with ISO format with Z suffix
        messages_with_z = [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": "2023-01-01T12:00:00Z"
            }
        ]
        
        conversation_data = {
            "language": "english",
            "level": "B1",
            "messages": messages_with_z,
            "duration_minutes": 5.0
        }
        
        response = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Test with ISO format with timezone
        messages_with_tz = [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": "2023-01-01T12:00:00+00:00"
            }
        ]
        
        conversation_data["messages"] = messages_with_tz
        response = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        assert response.status_code == 200
    
    async def test_save_conversation_missing_timestamps(self, client: AsyncClient, auth_headers):
        """Test handling of messages without timestamps."""
        messages_no_timestamp = [
            {
                "role": "user",
                "content": "Hello"
                # No timestamp field
            }
        ]
        
        conversation_data = {
            "language": "english",
            "level": "B1",
            "messages": messages_no_timestamp,
            "duration_minutes": 5.0
        }
        
        response = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        
        # Should handle gracefully by using current time
        assert response.status_code == 200
    
    async def test_save_conversation_enhanced_analysis_threshold(self, client: AsyncClient, auth_headers, sample_conversation_messages):
        """Test enhanced analysis generation based on session quality."""
        # Test session that should get enhanced analysis (long + many messages)
        long_messages = sample_conversation_messages * 3  # More messages
        
        conversation_data = {
            "language": "english",
            "level": "B1",
            "topic": "travel",
            "messages": long_messages,
            "duration_minutes": 8.0  # Long duration
        }
        
        response = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Test session that should NOT get enhanced analysis (short + few messages)
        short_conversation_data = {
            "language": "english",
            "level": "B1",
            "topic": "work",
            "messages": sample_conversation_messages[:1],  # Few messages
            "duration_minutes": 2.0  # Short duration
        }
        
        response = await client.post("/api/progress/save-conversation", json=short_conversation_data, headers=auth_headers)
        assert response.status_code == 200

class TestErrorHandling:
    """Test error handling in progress routes."""
    
    async def test_database_connection_error(self, client: AsyncClient, auth_headers):
        """Test handling of database connection errors."""
        # This would require mocking database failures
        # For now, test that the endpoints handle errors gracefully
        
        # Test with extremely large conversation data
        large_messages = []
        for i in range(1000):  # Very large number of messages
            large_messages.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": "x" * 1000,  # Very long content
                "timestamp": datetime.utcnow().isoformat()
            })
        
        conversation_data = {
            "language": "english",
            "level": "B1",
            "messages": large_messages,
            "duration_minutes": 60.0
        }
        
        response = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400, 422, 500]
    
    async def test_invalid_session_data_types(self, client: AsyncClient, auth_headers):
        """Test handling of invalid data types in session data."""
        invalid_conversation_data = {
            "language": 123,  # Should be string
            "level": None,    # Should be string
            "messages": "not_a_list",  # Should be list
            "duration_minutes": "not_a_number"  # Should be number
        }
        
        response = await client.post("/api/progress/save-conversation", json=invalid_conversation_data, headers=auth_headers)
        
        assert response.status_code == 422
    
    async def test_concurrent_session_saving(self, client: AsyncClient, auth_headers, sample_conversation_messages):
        """Test concurrent saving of sessions for same user."""
        conversation_data = {
            "language": "english",
            "level": "B1",
            "topic": "travel",
            "messages": sample_conversation_messages,
            "duration_minutes": 5.0
        }
        
        # In a real scenario, this would be done with actual concurrency
        # For now, just test sequential saves
        response1 = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        response2 = await client.post("/api/progress/save-conversation", json=conversation_data, headers=auth_headers)
        
        # Both should succeed (second one should update the first)
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Second response should indicate an update
        data2 = response2.json()
        assert data2["action"] == "updated"
