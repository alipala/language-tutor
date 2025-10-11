"""
Tests for institutional models
"""
import pytest
from datetime import datetime, timedelta
from app.models.institution import Institution, InstitutionBase
from app.models.tutor import Tutor, TutorBase
from app.models.institutional_learner import InstitutionalLearner, InstitutionalLearnerBase
from app.models.invitation import Invitation, InvitationBase
from app.models.consent import ConsentRecord, ConsentRecordBase


class TestInstitutionModel:
    """Test Institution model"""

    def test_institution_base_creation(self):
        """Test creating an InstitutionBase instance"""
        institution_data = {
            "name": "Lincoln Academy",
            "domain": "lincoln-academy.edu",
            "admin_email": "admin@lincoln-academy.edu",
            "institution_code": "LINCOLN2024",
            "subscription_plan": "professional",
            "max_tutors": 5,
            "max_learners": 100
        }

        institution = InstitutionBase(**institution_data)

        assert institution.name == "Lincoln Academy"
        assert institution.domain == "lincoln-academy.edu"
        assert institution.admin_email == "admin@lincoln-academy.edu"
        assert institution.institution_code == "LINCOLN2024"
        assert institution.subscription_plan == "professional"
        assert institution.max_tutors == 5
        assert institution.max_learners == 100
        assert institution.is_active is True
        assert isinstance(institution.created_at, datetime)
        assert isinstance(institution.updated_at, datetime)

    def test_institution_creation(self):
        """Test creating a full Institution instance"""
        institution_data = {
            "name": "Test Academy",
            "admin_email": "admin@test.edu",
            "institution_code": "TEST123"
        }

        institution = Institution(**institution_data)

        assert institution.name == "Test Academy"
        assert institution.admin_email == "admin@test.edu"
        assert institution.institution_code == "TEST123"
        assert hasattr(institution, 'id')
        assert institution.id is not None


class TestTutorModel:
    """Test Tutor model"""

    def test_tutor_base_creation(self):
        """Test creating a TutorBase instance"""
        tutor_data = {
            "email": "john.doe@school.edu",
            "name": "John Doe",
            "institution_id": "507f1f77bcf86cd799439011",
            "bio": "Experienced language instructor",
            "qualifications": "MA in Linguistics",
            "assigned_learners": ["user1", "user2"]
        }

        tutor = TutorBase(**tutor_data)

        assert tutor.email == "john.doe@school.edu"
        assert tutor.name == "John Doe"
        assert tutor.institution_id == "507f1f77bcf86cd799439011"
        assert tutor.bio == "Experienced language instructor"
        assert tutor.qualifications == "MA in Linguistics"
        assert tutor.assigned_learners == ["user1", "user2"]
        assert tutor.is_active is True
        assert tutor.invitation_accepted is False

    def test_tutor_creation(self):
        """Test creating a full Tutor instance"""
        tutor_data = {
            "email": "jane.smith@school.edu",
            "name": "Jane Smith",
            "institution_id": "507f1f77bcf86cd799439011"
        }

        tutor = Tutor(**tutor_data)

        assert tutor.email == "jane.smith@school.edu"
        assert tutor.name == "Jane Smith"
        assert tutor.institution_id == "507f1f77bcf86cd799439011"
        assert hasattr(tutor, 'id')
        assert tutor.id is not None


class TestInstitutionalLearnerModel:
    """Test InstitutionalLearner model"""

    def test_institutional_learner_base_creation(self):
        """Test creating an InstitutionalLearnerBase instance"""
        learner_data = {
            "user_id": "user123",
            "institution_id": "inst456",
            "tutor_id": "tutor789",
            "enrollment_method": "admin_invite",
            "consent_given": True,
            "consent_date": datetime.utcnow()
        }

        learner = InstitutionalLearnerBase(**learner_data)

        assert learner.user_id == "user123"
        assert learner.institution_id == "inst456"
        assert learner.tutor_id == "tutor789"
        assert learner.enrollment_method == "admin_invite"
        assert learner.consent_given is True
        assert learner.consent_revoked is False
        assert learner.is_active is True
        assert isinstance(learner.enrolled_at, datetime)

    def test_institutional_learner_creation(self):
        """Test creating a full InstitutionalLearner instance"""
        learner_data = {
            "user_id": "user123",
            "institution_id": "inst456",
            "tutor_id": "tutor789"
        }

        learner = InstitutionalLearner(**learner_data)

        assert learner.user_id == "user123"
        assert learner.institution_id == "inst456"
        assert learner.tutor_id == "tutor789"
        assert hasattr(learner, 'id')
        assert learner.id is not None


class TestInvitationModel:
    """Test Invitation model"""

    def test_invitation_base_creation(self):
        """Test creating an InvitationBase instance"""
        invitation_data = {
            "email": "student@school.edu",
            "invitation_type": "learner",
            "institution_id": "inst456",
            "invited_by": "admin123"
        }

        invitation = InvitationBase(**invitation_data)

        assert invitation.email == "student@school.edu"
        assert invitation.invitation_type == "learner"
        assert invitation.institution_id == "inst456"
        assert invitation.invited_by == "admin123"
        assert invitation.is_accepted is False
        assert len(invitation.code) > 0  # Should generate a code
        assert isinstance(invitation.expires_at, datetime)
        assert invitation.expires_at > datetime.utcnow()  # Should be in the future

    def test_invitation_creation(self):
        """Test creating a full Invitation instance"""
        invitation_data = {
            "email": "tutor@school.edu",
            "invitation_type": "tutor",
            "institution_id": "inst456",
            "invited_by": "admin123"
        }

        invitation = Invitation(**invitation_data)

        assert invitation.email == "tutor@school.edu"
        assert invitation.invitation_type == "tutor"
        assert invitation.institution_id == "inst456"
        assert invitation.invited_by == "admin123"
        assert hasattr(invitation, 'id')
        assert invitation.id is not None


class TestConsentRecordModel:
    """Test ConsentRecord model"""

    def test_consent_record_base_creation(self):
        """Test creating a ConsentRecordBase instance"""
        consent_data = {
            "learner_id": "user123",
            "institution_id": "inst456",
            "tutor_id": "tutor789",
            "action": "granted",
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0..."
        }

        consent = ConsentRecordBase(**consent_data)

        assert consent.learner_id == "user123"
        assert consent.institution_id == "inst456"
        assert consent.tutor_id == "tutor789"
        assert consent.action == "granted"
        assert consent.data_shared == [
            "assessment_results",
            "learning_plans",
            "practice_sessions",
            "progress_metrics"
        ]
        assert isinstance(consent.action_date, datetime)
        assert consent.ip_address == "192.168.1.1"
        assert consent.user_agent == "Mozilla/5.0..."

    def test_consent_record_creation(self):
        """Test creating a full ConsentRecord instance"""
        consent_data = {
            "learner_id": "user123",
            "institution_id": "inst456",
            "tutor_id": "tutor789",
            "action": "revoked"
        }

        consent = ConsentRecord(**consent_data)

        assert consent.learner_id == "user123"
        assert consent.institution_id == "inst456"
        assert consent.tutor_id == "tutor789"
        assert consent.action == "revoked"
        assert hasattr(consent, 'id')
        assert consent.id is not None


class TestModelValidation:
    """Test model validation"""

    def test_institution_code_validation(self):
        """Test institution code length validation"""
        # Should fail - too short
        with pytest.raises(ValueError):
            InstitutionBase(
                name="Test",
                admin_email="admin@test.com",
                institution_code="ABC"  # Too short
            )

        # Should fail - too long
        with pytest.raises(ValueError):
            InstitutionBase(
                name="Test",
                admin_email="admin@test.com",
                institution_code="A" * 21  # Too long
            )

        # Should pass
        institution = InstitutionBase(
            name="Test",
            admin_email="admin@test.com",
            institution_code="VALIDCODE123"
        )
        assert institution.institution_code == "VALIDCODE123"

    def test_email_validation(self):
        """Test email field validation"""
        # Should pass
        institution = InstitutionBase(
            name="Test",
            admin_email="admin@test.com",
            institution_code="VALID123"
        )
        assert institution.admin_email == "admin@test.com"

        # Should fail - invalid email
        with pytest.raises(ValueError):
            InstitutionBase(
                name="Test",
                admin_email="invalid-email",
                institution_code="VALID123"
            )
