"""
Tests for consent service
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from app.consent.service import ConsentService


class TestConsentService:
    """Test ConsentService class"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database"""
        db = MagicMock()
        db.consent_records = MagicMock()
        db.institutional_learners = MagicMock()
        db.institutions = MagicMock()
        db.tutors = MagicMock()
        return db

    @pytest.fixture
    def consent_service(self, mock_db):
        """Create ConsentService instance with mock db"""
        return ConsentService(mock_db)

    @pytest.mark.asyncio
    async def test_check_consent_true(self, consent_service, mock_db):
        """Test check_consent returns True when consent exists"""
        mock_db.institutional_learners.find_one = AsyncMock(return_value={
            "user_id": "user123",
            "institution_id": "inst456",
            "consent_given": True,
            "consent_revoked": False,
            "is_active": True
        })

        result = await consent_service.check_consent("user123", "inst456")

        assert result is True
        mock_db.institutional_learners.find_one.assert_called_once_with({
            "user_id": "user123",
            "institution_id": "inst456",
            "consent_given": True,
            "consent_revoked": False,
            "is_active": True
        })

    @pytest.mark.asyncio
    async def test_check_consent_false(self, consent_service, mock_db):
        """Test check_consent returns False when no consent"""
        mock_db.institutional_learners.find_one = AsyncMock(return_value=None)

        result = await consent_service.check_consent("user123", "inst456")

        assert result is False

    @pytest.mark.asyncio
    async def test_grant_consent_success(self, consent_service, mock_db):
        """Test successful consent granting"""
        # Mock the update operation
        mock_db.institutional_learners.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

        # Mock the insert operation
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = "consent_record_id"
        mock_db.consent_records.insert_one = AsyncMock(return_value=mock_insert_result)

        result = await consent_service.grant_consent(
            learner_id="user123",
            institution_id="inst456",
            tutor_id="tutor789",
            data_to_share=["assessment_results", "learning_plans"],
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )

        assert result["success"] is True
        assert result["consent_record_id"] == "consent_record_id"
        assert result["message"] == "Consent granted successfully"

        # Verify institutional_learners was updated
        mock_db.institutional_learners.update_one.assert_called_once()
        update_call = mock_db.institutional_learners.update_one.call_args
        assert update_call[0][0] == {"user_id": "user123", "institution_id": "inst456"}
        assert "consent_given" in update_call[0][1]["$set"]
        assert update_call[0][1]["$set"]["consent_given"] is True

        # Verify consent record was created
        mock_db.consent_records.insert_one.assert_called_once()
        insert_call = mock_db.consent_records.insert_one.call_args[0][0]
        assert insert_call["learner_id"] == "user123"
        assert insert_call["institution_id"] == "inst456"
        assert insert_call["tutor_id"] == "tutor789"
        assert insert_call["action"] == "granted"
        assert insert_call["ip_address"] == "192.168.1.1"
        assert insert_call["user_agent"] == "Mozilla/5.0"

    @pytest.mark.asyncio
    async def test_grant_consent_enrollment_not_found(self, consent_service, mock_db):
        """Test grant_consent fails when enrollment not found"""
        mock_db.institutional_learners.update_one = AsyncMock(return_value=MagicMock(modified_count=0))

        with pytest.raises(ValueError, match="Learner enrollment not found"):
            await consent_service.grant_consent(
                learner_id="user123",
                institution_id="inst456",
                tutor_id="tutor789",
                data_to_share=["assessment_results"]
            )

    @pytest.mark.asyncio
    async def test_revoke_consent_success(self, consent_service, mock_db):
        """Test successful consent revocation"""
        # Mock finding the enrollment
        mock_db.institutional_learners.find_one = AsyncMock(return_value={
            "_id": "enrollment_id",
            "user_id": "user123",
            "institution_id": "inst456",
            "tutor_id": "tutor789"
        })

        # Mock the update operation
        mock_db.institutional_learners.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

        # Mock the insert operation
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = "revoke_record_id"
        mock_db.consent_records.insert_one = AsyncMock(return_value=mock_insert_result)

        result = await consent_service.revoke_consent("user123", "inst456")

        assert result["success"] is True
        assert result["consent_record_id"] == "revoke_record_id"
        assert result["message"] == "Consent revoked successfully"

        # Verify enrollment was updated
        mock_db.institutional_learners.update_one.assert_called_once()
        update_call = mock_db.institutional_learners.update_one.call_args
        assert update_call[0][1]["$set"]["consent_revoked"] is True

        # Verify revocation record was created
        mock_db.consent_records.insert_one.assert_called_once()
        insert_call = mock_db.consent_records.insert_one.call_args[0][0]
        assert insert_call["action"] == "revoked"

    @pytest.mark.asyncio
    async def test_revoke_consent_enrollment_not_found(self, consent_service, mock_db):
        """Test revoke_consent fails when enrollment not found"""
        mock_db.institutional_learners.find_one = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Enrollment not found"):
            await consent_service.revoke_consent("user123", "inst456")

    @pytest.mark.asyncio
    async def test_get_consent_status_success(self, consent_service, mock_db):
        """Test successful consent status retrieval"""
        # Mock enrollment
        mock_db.institutional_learners.find_one = AsyncMock(return_value={
            "user_id": "user123",
            "institution_id": "inst456",
            "tutor_id": "tutor789",
            "consent_given": True,
            "consent_date": datetime.utcnow(),
            "consent_revoked": False
        })

        # Mock institution
        mock_db.institutions.find_one = AsyncMock(return_value={
            "_id": "inst456",
            "name": "Test Academy"
        })

        # Mock tutor
        mock_db.tutors.find_one = AsyncMock(return_value={
            "_id": "tutor789",
            "name": "John Doe"
        })

        # Mock latest consent record
        mock_db.consent_records.find_one = AsyncMock(return_value={
            "data_shared": ["assessment_results", "learning_plans"]
        })

        result = await consent_service.get_consent_status("user123", "inst456")

        assert result is not None
        assert result["has_consent"] is True
        assert result["consent_revoked"] is False
        assert result["institution_name"] == "Test Academy"
        assert result["tutor_name"] == "John Doe"
        assert result["data_shared"] == ["assessment_results", "learning_plans"]

    @pytest.mark.asyncio
    async def test_get_consent_status_no_enrollment(self, consent_service, mock_db):
        """Test get_consent_status returns None when no enrollment"""
        mock_db.institutional_learners.find_one = AsyncMock(return_value=None)

        result = await consent_service.get_consent_status("user123", "inst456")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_consent_status_unknown_institution_tutor(self, consent_service, mock_db):
        """Test get_consent_status handles missing institution/tutor gracefully"""
        # Mock enrollment
        mock_db.institutional_learners.find_one = AsyncMock(return_value={
            "user_id": "user123",
            "institution_id": "inst456",
            "tutor_id": "tutor789",
            "consent_given": False
        })

        # Mock missing institution
        mock_db.institutions.find_one = AsyncMock(return_value=None)

        # Mock missing tutor
        mock_db.tutors.find_one = AsyncMock(return_value=None)

        # Mock no consent record
        mock_db.consent_records.find_one = AsyncMock(return_value=None)

        result = await consent_service.get_consent_status("user123", "inst456")

        assert result is not None
        assert result["has_consent"] is False
        assert result["institution_name"] == "Unknown"
        assert result["tutor_name"] == "Unknown"
        assert result["data_shared"] == []
