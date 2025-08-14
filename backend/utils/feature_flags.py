import os
from typing import Dict, Any, Optional

class FeatureFlags:
    """Centralized feature flag management for the application"""
    
    # Default feature flag values
    DEFAULT_FLAGS = {
        "WORLD_BUILDING_ENABLED": True,
        "ENHANCED_ANALYTICS": True,
        "ADVANCED_ASSESSMENTS": True,
        "COLLABORATIVE_FEATURES": False,
        "BETA_FEATURES": False,
        "EXPERIMENTAL_UI": False,
        "PREMIUM_CONTENT": True,
        "SOCIAL_FEATURES": False,
        "GAMIFICATION": True,
        "MOBILE_OPTIMIZATIONS": True
    }
    
    @staticmethod
    def get_flag(flag_name: str, default: Optional[bool] = None) -> bool:
        """
        Get a feature flag value from environment variables or defaults
        
        Args:
            flag_name: Name of the feature flag
            default: Default value if not found (overrides DEFAULT_FLAGS)
            
        Returns:
            Boolean value of the feature flag
        """
        # Check environment variable first
        env_value = os.getenv(flag_name)
        if env_value is not None:
            return env_value.lower() in ('true', '1', 'yes', 'on', 'enabled')
        
        # Use provided default or fall back to DEFAULT_FLAGS
        if default is not None:
            return default
        
        return FeatureFlags.DEFAULT_FLAGS.get(flag_name, False)
    
    @staticmethod
    def is_world_building_enabled() -> bool:
        """Check if collaborative world building feature is enabled"""
        return FeatureFlags.get_flag("WORLD_BUILDING_ENABLED")
    
    @staticmethod
    def is_enhanced_analytics_enabled() -> bool:
        """Check if enhanced analytics features are enabled"""
        return FeatureFlags.get_flag("ENHANCED_ANALYTICS")
    
    @staticmethod
    def is_collaborative_features_enabled() -> bool:
        """Check if collaborative features are enabled"""
        return FeatureFlags.get_flag("COLLABORATIVE_FEATURES")
    
    @staticmethod
    def is_beta_features_enabled() -> bool:
        """Check if beta features are enabled"""
        return FeatureFlags.get_flag("BETA_FEATURES")
    
    @staticmethod
    def is_social_features_enabled() -> bool:
        """Check if social features are enabled"""
        return FeatureFlags.get_flag("SOCIAL_FEATURES")
    
    @staticmethod
    def get_all_flags() -> Dict[str, bool]:
        """Get all feature flags with their current values"""
        flags = {}
        for flag_name in FeatureFlags.DEFAULT_FLAGS.keys():
            flags[flag_name] = FeatureFlags.get_flag(flag_name)
        return flags
    
    @staticmethod
    def get_flags_for_user(user_id: Optional[str] = None, subscription_plan: Optional[str] = None) -> Dict[str, bool]:
        """
        Get feature flags customized for a specific user
        
        Args:
            user_id: User's ID for personalized flags
            subscription_plan: User's subscription plan for plan-specific features
            
        Returns:
            Dictionary of feature flags for the user
        """
        flags = FeatureFlags.get_all_flags()
        
        # Customize flags based on subscription plan
        if subscription_plan:
            if subscription_plan in ["fluency_builder", "team_mastery"]:
                # Premium features for paid plans
                flags["PREMIUM_CONTENT"] = True
                flags["ENHANCED_ANALYTICS"] = True
                flags["COLLABORATIVE_FEATURES"] = True
            
            if subscription_plan == "team_mastery":
                # Advanced features for highest tier
                flags["WORLD_BUILDING_ENABLED"] = True
                flags["SOCIAL_FEATURES"] = True
                flags["BETA_FEATURES"] = True
        
        # User-specific customizations could be added here
        # For example, beta testers, admin users, etc.
        
        return flags
    
    @staticmethod
    def set_flag_for_environment(flag_name: str, value: bool):
        """
        Set a feature flag for the current environment (for testing)
        
        Args:
            flag_name: Name of the feature flag
            value: Boolean value to set
        """
        os.environ[flag_name] = str(value).lower()
    
    @staticmethod
    def get_feature_config() -> Dict[str, Any]:
        """
        Get comprehensive feature configuration for the application
        
        Returns:
            Dictionary with feature configuration details
        """
        return {
            "feature_flags": FeatureFlags.get_all_flags(),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "version": os.getenv("VERSION", "development"),
            "world_building": {
                "enabled": FeatureFlags.is_world_building_enabled(),
                "max_worlds_per_user": int(os.getenv("MAX_WORLDS_PER_USER", "5")),
                "max_contributors_per_world": int(os.getenv("MAX_CONTRIBUTORS_PER_WORLD", "10")),
                "session_duration_limits": {
                    "min_minutes": int(os.getenv("MIN_SESSION_DURATION", "5")),
                    "max_minutes": int(os.getenv("MAX_SESSION_DURATION", "30"))
                }
            },
            "collaboration": {
                "enabled": FeatureFlags.is_collaborative_features_enabled(),
                "invitation_expiry_hours": int(os.getenv("INVITATION_EXPIRY_HOURS", "168")),  # 7 days
                "max_invitations_per_day": int(os.getenv("MAX_INVITATIONS_PER_DAY", "10"))
            },
            "analytics": {
                "enhanced_enabled": FeatureFlags.is_enhanced_analytics_enabled(),
                "retention_days": int(os.getenv("ANALYTICS_RETENTION_DAYS", "90"))
            }
        }

# Global feature flags instance
feature_flags = FeatureFlags()
