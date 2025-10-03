"""
Tests for feature flag system.
"""
import os
import pytest
from unittest.mock import patch

# Import the feature flags
from app.config import feature_flags, FeatureFlags


class TestFeatureFlags:
    """Test the FeatureFlags class"""

    def test_default_values_are_false(self):
        """Test that all feature flags default to False when env vars are not set"""
        # Ensure environment variables are not set
        with patch.dict(os.environ, {}, clear=True):
            flags = FeatureFlags()

            assert flags.INSTITUTIONAL_FEATURES_ENABLED is False
            assert flags.INSTITUTION_SIGNUP_ENABLED is False
            assert flags.TUTOR_DASHBOARD_ENABLED is False
            assert flags.LEARNER_ENROLLMENT_ENABLED is False

    def test_feature_flags_can_be_enabled(self):
        """Test that feature flags can be enabled via environment variables"""
        env_vars = {
            'INSTITUTIONAL_FEATURES_ENABLED': 'true',
            'INSTITUTION_SIGNUP_ENABLED': 'true',
            'TUTOR_DASHBOARD_ENABLED': 'false',  # Test mixed values
            'LEARNER_ENROLLMENT_ENABLED': 'true'
        }

        with patch.dict(os.environ, env_vars):
            flags = FeatureFlags()

            assert flags.INSTITUTIONAL_FEATURES_ENABLED is True
            assert flags.INSTITUTION_SIGNUP_ENABLED is True
            assert flags.TUTOR_DASHBOARD_ENABLED is False  # Should remain False
            assert flags.LEARNER_ENROLLMENT_ENABLED is True

    def test_case_insensitive_env_values(self):
        """Test that environment variable values are case insensitive"""
        env_vars = {
            'INSTITUTIONAL_FEATURES_ENABLED': 'TRUE',
            'INSTITUTION_SIGNUP_ENABLED': 'True',
            'TUTOR_DASHBOARD_ENABLED': 'FALSE',
            'LEARNER_ENROLLMENT_ENABLED': 'False'
        }

        with patch.dict(os.environ, env_vars):
            flags = FeatureFlags()

            assert flags.INSTITUTIONAL_FEATURES_ENABLED is True
            assert flags.INSTITUTION_SIGNUP_ENABLED is True
            assert flags.TUTOR_DASHBOARD_ENABLED is False
            assert flags.LEARNER_ENROLLMENT_ENABLED is False

    def test_is_enabled_method(self):
        """Test the is_enabled method"""
        with patch.dict(os.environ, {'INSTITUTIONAL_FEATURES_ENABLED': 'true'}):
            flags = FeatureFlags()

            assert flags.is_enabled('INSTITUTIONAL_FEATURES_ENABLED') is True
            assert flags.is_enabled('INSTITUTION_SIGNUP_ENABLED') is False
            assert flags.is_enabled('NON_EXISTENT_FLAG') is False

    def test_get_all_flags(self):
        """Test the get_all_flags method returns all uppercase attributes"""
        with patch.dict(os.environ, {
            'INSTITUTIONAL_FEATURES_ENABLED': 'true',
            'TUTOR_DASHBOARD_ENABLED': 'true'
        }):
            flags = FeatureFlags()
            all_flags = flags.get_all_flags()

            # Should contain all the feature flags
            expected_flags = {
                'INSTITUTIONAL_FEATURES_ENABLED': True,
                'INSTITUTION_SIGNUP_ENABLED': False,
                'TUTOR_DASHBOARD_ENABLED': True,
                'LEARNER_ENROLLMENT_ENABLED': False
            }

            assert all_flags == expected_flags

    def test_global_instance_exists(self):
        """Test that the global feature_flags instance is available"""
        assert hasattr(feature_flags, 'INSTITUTIONAL_FEATURES_ENABLED')
        assert hasattr(feature_flags, 'INSTITUTION_SIGNUP_ENABLED')
        assert hasattr(feature_flags, 'TUTOR_DASHBOARD_ENABLED')
        assert hasattr(feature_flags, 'LEARNER_ENROLLMENT_ENABLED')
        assert hasattr(feature_flags, 'is_enabled')
        assert hasattr(feature_flags, 'get_all_flags')
