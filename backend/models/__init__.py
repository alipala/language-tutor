"""
Models package for the Language Tutor application
"""

# Import world building models first (they don't depend on main models)
from .world_building_models import *

# Create aliases for commonly used world building models
StoryWorld = StoryWorldInDB  # Alias for backward compatibility
StoryContribution = StoryContributionInDB  # Alias for backward compatibility

# Import main models directly to avoid circular imports
# We'll import them directly from the parent models.py file
import sys
import os

# Add parent directory to path to import main models
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import all models from the main models.py file
try:
    # Import the main models module directly
    import importlib.util
    spec = importlib.util.spec_from_file_location("main_models", os.path.join(parent_dir, "models.py"))
    main_models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_models)
    
    # Export all the main models
    UserResponse = main_models.UserResponse
    UserInDB = main_models.UserInDB
    UserBase = main_models.UserBase
    UserCreate = main_models.UserCreate
    UserUpdate = main_models.UserUpdate
    Token = main_models.Token
    TokenData = main_models.TokenData
    LoginRequest = main_models.LoginRequest
    GoogleLoginRequest = main_models.GoogleLoginRequest
    PasswordResetRequest = main_models.PasswordResetRequest
    PasswordResetConfirm = main_models.PasswordResetConfirm
    EmailVerificationRequest = main_models.EmailVerificationRequest
    EmailVerificationConfirm = main_models.EmailVerificationConfirm
    ResendVerificationRequest = main_models.ResendVerificationRequest
    ConversationSession = main_models.ConversationSession
    SaveConversationRequest = main_models.SaveConversationRequest
    SubscriptionStatus = main_models.SubscriptionStatus
    SubscriptionLimits = main_models.SubscriptionLimits
    NotificationResponse = main_models.NotificationResponse
    PasswordReset = main_models.PasswordReset
    EmailVerification = main_models.EmailVerification
    VoiceSelectionRequest = main_models.VoiceSelectionRequest
    VoiceSelectionResponse = main_models.VoiceSelectionResponse
    UsageTrackingRequest = main_models.UsageTrackingRequest
    SpeakingTimeTrackingRequest = main_models.SpeakingTimeTrackingRequest
    
    # Additional models that might be needed
    Session = main_models.Session
    ConversationMessage = main_models.ConversationMessage
    ConversationStats = main_models.ConversationStats
    ConversationHistoryResponse = main_models.ConversationHistoryResponse
    SubscriptionPlan = main_models.SubscriptionPlan
    LearningPlanPreservation = main_models.LearningPlanPreservation
    NotificationBase = main_models.NotificationBase
    NotificationCreate = main_models.NotificationCreate
    NotificationInDB = main_models.NotificationInDB
    UserNotificationBase = main_models.UserNotificationBase
    UserNotificationInDB = main_models.UserNotificationInDB
    UserNotificationResponse = main_models.UserNotificationResponse
    NotificationMarkReadRequest = main_models.NotificationMarkReadRequest
    NotificationListResponse = main_models.NotificationListResponse
    NotificationType = main_models.NotificationType
    
    print("✅ Successfully imported all main models")
    
except Exception as e:
    print(f"❌ Error importing main models: {e}")
    # Create placeholder classes to prevent import errors
    class UserResponse: pass
    class UserInDB: pass
    class UserBase: pass
    class UserCreate: pass
    class UserUpdate: pass
    class Token: pass
    class TokenData: pass
    class LoginRequest: pass
    class GoogleLoginRequest: pass
    class PasswordResetRequest: pass
    class PasswordResetConfirm: pass
    class EmailVerificationRequest: pass
    class EmailVerificationConfirm: pass
    class ResendVerificationRequest: pass
    class ConversationSession: pass
    class SaveConversationRequest: pass
    class SubscriptionStatus: pass
    class SubscriptionLimits: pass
    class NotificationResponse: pass
    class PasswordReset: pass
    class EmailVerification: pass
    class VoiceSelectionRequest: pass
    class VoiceSelectionResponse: pass
    class UsageTrackingRequest: pass
    class SpeakingTimeTrackingRequest: pass
    class Session: pass
    class ConversationMessage: pass
    class ConversationStats: pass
    class ConversationHistoryResponse: pass
    class SubscriptionPlan: pass
    class LearningPlanPreservation: pass
    class NotificationBase: pass
    class NotificationCreate: pass
    class NotificationInDB: pass
    class UserNotificationBase: pass
    class UserNotificationInDB: pass
    class UserNotificationResponse: pass
    class NotificationMarkReadRequest: pass
    class NotificationListResponse: pass
    class NotificationType: pass
