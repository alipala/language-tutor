"""
Pytest configuration and fixtures for Language Tutor API tests.

This module provides shared fixtures, test database setup, and common utilities
for all integration tests.
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator, Dict, Any
from httpx import AsyncClient
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import uuid

# Import the FastAPI app
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import init_db, client as db_client, database as db
from auth import create_access_token, get_password_hash
from models import UserInDB

# Test database configuration
TEST_DATABASE_NAME = "language_tutor_test"
TEST_MONGODB_URL = os.getenv("TEST_MONGODB_URL", "mongodb://localhost:27017")

@pytest.fixture(scope="function")
async def test_db():
    """Set up test database connection."""
    # Create unique database name for each test
    import uuid
    unique_db_name = f"{TEST_DATABASE_NAME}_{uuid.uuid4().hex[:8]}"
    
    # Connect to test database
    test_client = AsyncIOMotorClient(TEST_MONGODB_URL)
    test_database = test_client[unique_db_name]
    
    # Override the global database connection for tests
    import database
    original_client = database.client
    original_database = database.database
    original_db_name = database.DATABASE_NAME
    
    database.client = test_client
    database.database = test_database
    database.DATABASE_NAME = unique_db_name
    
    # Initialize collections
    try:
        await init_db()
    except Exception as e:
        print(f"Database initialization warning: {e}")
    
    yield test_database
    
    # Cleanup: Drop test database after test
    try:
        await test_client.drop_database(unique_db_name)
        test_client.close()
    except Exception as e:
        print(f"Cleanup warning: {e}")
    
    # Restore original database connection
    database.client = original_client
    database.database = original_database
    database.DATABASE_NAME = original_db_name

@pytest.fixture
async def clean_db(test_db):
    """Alias for test_db for backward compatibility."""
    yield test_db

@pytest.fixture
async def client(clean_db) -> AsyncGenerator[AsyncClient, None]:
    """Create test client for API requests."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sync_client(clean_db) -> TestClient:
    """Create synchronous test client for simple requests."""
    return TestClient(app)

@pytest.fixture
async def test_user(clean_db) -> Dict[str, Any]:
    """Create a test user in the database."""
    from database import users_collection
    from bson import ObjectId
    
    user_id = ObjectId()
    user_data = {
        "_id": user_id,
        "email": "test@example.com",
        "name": "Test User",
        "hashed_password": get_password_hash("testpassword123"),
        "is_active": True,
        "is_verified": True,
        "created_at": datetime.utcnow(),
        "preferred_language": "english",
        "preferred_level": "B1",
        "preferred_voice": "alloy",
        "subscription_status": "active",
        "subscription_plan": "fluency_builder",
        "subscription_period": "monthly",
        "practice_sessions_used": 0,
        "assessments_used": 0,
        "current_period_start": datetime.utcnow(),
        "current_period_end": datetime.utcnow() + timedelta(days=30)
    }
    
    await users_collection.insert_one(user_data)
    
    return {
        "id": str(user_id),
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpassword123",
        "is_verified": True,
        "subscription_status": "active",
        "subscription_plan": "fluency_builder"
    }

@pytest.fixture
async def unverified_user(clean_db) -> Dict[str, Any]:
    """Create an unverified test user."""
    from database import users_collection
    from bson import ObjectId
    
    user_id = ObjectId()
    user_data = {
        "_id": user_id,
        "email": "unverified@example.com",
        "name": "Unverified User",
        "hashed_password": get_password_hash("testpassword123"),
        "is_active": True,
        "is_verified": False,
        "created_at": datetime.utcnow(),
        "subscription_status": "try_learn"
    }
    
    await users_collection.insert_one(user_data)
    
    return {
        "id": str(user_id),
        "email": "unverified@example.com",
        "name": "Unverified User",
        "password": "testpassword123",
        "is_verified": False
    }

@pytest.fixture
async def premium_user(clean_db) -> Dict[str, Any]:
    """Create a premium test user with unlimited access."""
    from database import users_collection
    from bson import ObjectId
    
    user_id = ObjectId()
    user_data = {
        "_id": user_id,
        "email": "premium@example.com",
        "name": "Premium User",
        "hashed_password": get_password_hash("testpassword123"),
        "is_active": True,
        "is_verified": True,
        "created_at": datetime.utcnow(),
        "subscription_status": "active",
        "subscription_plan": "team_mastery",
        "subscription_period": "annual",
        "practice_sessions_used": 0,
        "assessments_used": 0,
        "current_period_start": datetime.utcnow(),
        "current_period_end": datetime.utcnow() + timedelta(days=365)
    }
    
    await users_collection.insert_one(user_data)
    
    return {
        "id": str(user_id),
        "email": "premium@example.com",
        "name": "Premium User",
        "password": "testpassword123",
        "subscription_plan": "team_mastery"
    }

@pytest.fixture
async def auth_headers(test_user) -> Dict[str, str]:
    """Create authentication headers for test user."""
    access_token = create_access_token(data={"sub": test_user["id"]})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
async def premium_auth_headers(premium_user) -> Dict[str, str]:
    """Create authentication headers for premium user."""
    access_token = create_access_token(data={"sub": premium_user["id"]})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def sample_learning_plan() -> Dict[str, Any]:
    """Sample learning plan data for testing."""
    return {
        "language": "english",
        "proficiency_level": "B1",
        "goals": ["travel", "business"],
        "duration_months": 3,
        "custom_goal": "Improve presentation skills"
    }

@pytest.fixture
def sample_assessment_data() -> Dict[str, Any]:
    """Sample assessment data for testing."""
    return {
        "recognized_text": "Hello, my name is John and I like to travel.",
        "overall_score": 75,
        "recommended_level": "B1",
        "strengths": ["vocabulary", "pronunciation"],
        "areas_for_improvement": ["grammar", "fluency"],
        "pronunciation": {"score": 80, "feedback": "Good pronunciation"},
        "grammar": {"score": 70, "feedback": "Some grammar issues"},
        "vocabulary": {"score": 85, "feedback": "Rich vocabulary"},
        "fluency": {"score": 65, "feedback": "Could be more fluent"},
        "coherence": {"score": 75, "feedback": "Well structured"}
    }

@pytest.fixture
def sample_conversation_messages() -> list:
    """Sample conversation messages for testing."""
    return [
        {
            "role": "assistant",
            "content": "Hello! Let's practice English. How are you today?",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "role": "user",
            "content": "I am good, thank you. I want to practice speaking about travel.",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "role": "assistant",
            "content": "Great! Tell me about your favorite travel destination.",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "role": "user",
            "content": "I love Paris because it has beautiful architecture and great food.",
            "timestamp": datetime.utcnow().isoformat()
        }
    ]

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for testing."""
    class MockChoice:
        def __init__(self, content):
            self.message = type('obj', (object,), {'content': content})
    
    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]
    
    return MockResponse

@pytest.fixture
def mock_stripe_customer():
    """Mock Stripe customer data."""
    return {
        "id": "cus_test123",
        "email": "test@example.com",
        "name": "Test User",
        "metadata": {"user_id": "test_user_id"}
    }

@pytest.fixture
def mock_stripe_subscription():
    """Mock Stripe subscription data."""
    return {
        "id": "sub_test123",
        "customer": "cus_test123",
        "status": "active",
        "current_period_start": 1640995200,  # 2022-01-01
        "current_period_end": 1643673600,    # 2022-02-01
        "items": {
            "data": [{
                "price": {
                    "id": "price_test123",
                    "product": "prod_test123",
                    "recurring": {"interval": "month"}
                }
            }]
        }
    }

# Test utilities
class TestUtils:
    """Utility functions for tests."""
    
    @staticmethod
    def generate_test_email() -> str:
        """Generate a unique test email."""
        return f"test_{uuid.uuid4().hex[:8]}@example.com"
    
    @staticmethod
    def generate_test_user_data() -> Dict[str, Any]:
        """Generate test user registration data."""
        return {
            "email": TestUtils.generate_test_email(),
            "name": "Test User",
            "password": "testpassword123"
        }
    
    @staticmethod
    async def create_test_conversation_session(user_id: str, db) -> str:
        """Create a test conversation session."""
        from database import conversation_sessions_collection
        from bson import ObjectId
        
        session_data = {
            "user_id": user_id,
            "language": "english",
            "level": "B1",
            "topic": "travel",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": datetime.utcnow()
                }
            ],
            "duration_minutes": 5.0,
            "message_count": 1,
            "summary": "Test conversation",
            "is_streak_eligible": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await conversation_sessions_collection.insert_one(session_data)
        return str(result.inserted_id)
    
    @staticmethod
    async def create_test_learning_plan(user_id: str, db) -> str:
        """Create a test learning plan."""
        from database import database
        
        plan_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "language": "english",
            "proficiency_level": "B1",
            "goals": ["travel"],
            "duration_months": 3,
            "plan_content": {
                "title": "Test Learning Plan",
                "overview": "Test plan overview",
                "weekly_schedule": [
                    {
                        "week": 1,
                        "focus": "Basic vocabulary",
                        "activities": ["Learn 20 words", "Practice pronunciation"],
                        "sessions_completed": 0,
                        "total_sessions": 2
                    }
                ]
            },
            "created_at": datetime.utcnow().isoformat(),
            "total_sessions": 24,
            "completed_sessions": 0,
            "progress_percentage": 0.0
        }
        
        await database.learning_plans.insert_one(plan_data)
        return plan_data["id"]

@pytest.fixture
def test_utils():
    """Provide test utilities."""
    return TestUtils

# Environment setup for tests
def pytest_configure(config):
    """Configure pytest environment."""
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_NAME"] = TEST_DATABASE_NAME
    
    # Mock external services for tests
    os.environ["OPENAI_API_KEY"] = "test_openai_key"
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_123"
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_123"

def pytest_unconfigure(config):
    """Cleanup after tests."""
    # Reset environment variables
    if "ENVIRONMENT" in os.environ:
        del os.environ["ENVIRONMENT"]
