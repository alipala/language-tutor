"""
Feature flag system for gradual rollout of new features.
"""
import os
from typing import Dict, Any

class FeatureFlags:
    """Centralized feature flag management"""

    def __init__(self):
        # Institutional Features - Default FALSE
        self.INSTITUTIONAL_FEATURES_ENABLED = os.getenv(
            'INSTITUTIONAL_FEATURES_ENABLED',
            'false'
        ).lower() == 'true'

        # Individual feature sub-flags (for granular control)
        self.INSTITUTION_SIGNUP_ENABLED = os.getenv(
            'INSTITUTION_SIGNUP_ENABLED',
            'false'
        ).lower() == 'true'

        self.TUTOR_DASHBOARD_ENABLED = os.getenv(
            'TUTOR_DASHBOARD_ENABLED',
            'false'
        ).lower() == 'true'

        self.LEARNER_ENROLLMENT_ENABLED = os.getenv(
            'LEARNER_ENROLLMENT_ENABLED',
            'false'
        ).lower() == 'true'

    def is_enabled(self, feature_name: str) -> bool:
        """Check if a specific feature is enabled"""
        return getattr(self, feature_name, False)

    def get_all_flags(self) -> Dict[str, bool]:
        """Return all feature flags for debugging"""
        return {
            key: value for key, value in self.__dict__.items()
            if key.isupper()
        }

# Global instance
feature_flags = FeatureFlags()

# Export for easy import
__all__ = ['feature_flags', 'FeatureFlags']
