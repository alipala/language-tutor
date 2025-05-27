# Guest User Experience

## Overview

The Language Tutor application provides a thoughtfully designed guest experience that allows users to try core features without requiring authentication. This document details the guest user journey, limitations, implementation details, and the transition path to becoming a registered user.

## Guest User Journey

The guest experience is designed to showcase the application's value while encouraging users to create an account for full functionality:

1. **Initial Assessment**: Guests can complete a 15-second speaking assessment to determine their language proficiency
2. **Language Selection**: Guests can choose from multiple supported languages
3. **Conversation Practice**: Guests receive 1 minute of AI conversation practice after assessment
4. **Results and Feedback**: Guests receive detailed feedback on their speaking performance
5. **Conversion Opportunity**: Clear calls-to-action encourage account creation for expanded features

## Implementation Details

### Time-Limited Assessments

```typescript
// From speaking-assessment.tsx
const SpeakingAssessment: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [assessmentDuration, setAssessmentDuration] = useState(
    isAuthenticated ? 60 : 15
  );
  
  // Component implementation
  // ...
  
  return (
    <div className="speaking-assessment">
      {/* Timer display */}
      <div className="timer-container">
        <CircularProgressTimer 
          duration={assessmentDuration}
          isActive={isTimerActive}
          onComplete={handleTimerComplete}
        />
        <div className="timer-label">
          {isAuthenticated ? '60s' : '15s'}
        </div>
      </div>
      
      {/* Guest notice */}
      {!isAuthenticated && (
        <div className="guest-notice">
          <p>
            You are using the guest mode with limited features.
            <a href="/login">Sign in</a> for the full experience.
          </p>
        </div>
      )}
    </div>
  );
};
```

The speaking assessment component:
- Automatically detects guest vs. authenticated users
- Sets a shorter assessment duration for guests (15 seconds vs. 60 seconds)
- Displays a clear notice about guest limitations
- Provides a direct link to sign in

### Time-Limited Conversations

```typescript
// From speech-client.tsx
export default function SpeechClient() {
  const { isAuthenticated } = useAuth();
  const [conversationTimeLimit, setConversationTimeLimit] = useState(
    isAuthenticated ? 300 : 60
  ); // 5 minutes for auth users, 1 minute for guests
  
  // Component implementation
  // ...
  
  useEffect(() => {
    let timer: NodeJS.Timeout;
    
    if (isConversationActive && !isAuthenticated) {
      // Start countdown for guest users
      timer = setTimeout(() => {
        setShowTimeUpModal(true);
        stopConversation();
      }, conversationTimeLimit * 1000);
    }
    
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [isConversationActive, isAuthenticated]);
  
  // Render time-up modal for guests
  return (
    <div className="speech-client">
      {/* Conversation UI */}
      
      {/* Time-up modal */}
      {showTimeUpModal && (
        <TimeUpModal 
          isAuthenticated={isAuthenticated}
          onClose={handleTimeUpModalClose}
          onSignUp={() => router.push('/signup')}
        />
      )}
    </div>
  );
}
```

The speech client component:
- Limits conversation time for guests to 1 minute (vs. 5 minutes for authenticated users)
- Shows a modal when time expires
- Provides clear next steps for conversion

### Guest Session Management

```typescript
// From guest-utils.ts
export const getGuestAssessmentCount = (): number => {
  try {
    const count = sessionStorage.getItem('guestAssessmentCount');
    return count ? parseInt(count, 10) : 0;
  } catch (error) {
    console.error('Error getting guest assessment count:', error);
    return 0;
  }
};

export const incrementGuestAssessmentCount = (): void => {
  try {
    const currentCount = getGuestAssessmentCount();
    sessionStorage.setItem('guestAssessmentCount', (currentCount + 1).toString());
  } catch (error) {
    console.error('Error incrementing guest assessment count:', error);
  }
};

export const hasReachedGuestAssessmentLimit = (): boolean => {
  return getGuestAssessmentCount() >= MAX_GUEST_ASSESSMENTS;
};

export const markPlanAsExpired = (planId: string): void => {
  try {
    sessionStorage.setItem(`plan_${planId}_expired`, 'true');
  } catch (error) {
    console.error('Error marking plan as expired:', error);
  }
};

export const isPlanExpired = (planId: string): boolean => {
  try {
    return sessionStorage.getItem(`plan_${planId}_expired`) === 'true';
  } catch (error) {
    console.error('Error checking if plan is expired:', error);
    return false;
  }
};
```

The guest utilities:
- Track the number of assessments completed by a guest user
- Enforce a maximum limit on guest assessments (3 per session)
- Mark conversation plans as expired after use
- Prevent access to expired conversations

### Learning Plan Creation for Guests

```typescript
// From learning-routes.py
@router.post("/plan", response_model=LearningPlanResponse)
async def create_learning_plan(
    plan_data: LearningPlanCreate,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Create a new learning plan (works for both authenticated and guest users)"""
    # Create plan document
    plan_dict = plan_data.dict()
    plan_dict["created_at"] = datetime.utcnow()
    
    # Add user ID if authenticated
    if current_user:
        plan_dict["user_id"] = current_user.id
    
    # Insert into database
    result = await learning_plans_collection.insert_one(plan_dict)
    
    # Get created plan
    created_plan = await learning_plans_collection.find_one({"_id": result.inserted_id})
    
    return LearningPlanResponse(**created_plan)
```

The backend supports:
- Creating learning plans for both guests and authenticated users
- Storing guest plans without a user ID
- Allowing plans to be claimed later by authenticated users

### Guest-to-User Conversion

```typescript
// From PendingLearningPlanHandler.tsx
export const PendingLearningPlanHandler: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const [isProcessing, setIsProcessing] = useState(false);
  
  useEffect(() => {
    // Check for pending learning plan after login
    const pendingPlanId = sessionStorage.getItem('pendingLearningPlanId');
    
    if (isAuthenticated && user && pendingPlanId) {
      assignPendingPlanToUser(pendingPlanId, user.id);
    }
  }, [isAuthenticated, user]);
  
  const assignPendingPlanToUser = async (planId: string, userId: string) => {
    try {
      setIsProcessing(true);
      
      // Call API to assign plan to user
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/learning/assign-plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          plan_id: planId,
          user_id: userId
        })
      });
      
      if (response.ok) {
        // Clear pending plan ID
        sessionStorage.removeItem('pendingLearningPlanId');
      }
    } catch (error) {
      console.error('Error assigning pending plan:', error);
    } finally {
      setIsProcessing(false);
    }
  };
  
  return null; // This component doesn't render anything
};
```

The conversion process:
- Detects pending learning plans created as a guest
- Automatically assigns plans to the user after authentication
- Preserves the user's progress and preferences
- Provides a seamless transition experience

## User Interface Elements

### Guest Notice Banner

```typescript
// From GuestNoticeBanner.tsx
export const GuestNoticeBanner: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [isDismissed, setIsDismissed] = useState(false);
  
  if (isAuthenticated || isDismissed) {
    return null;
  }
  
  return (
    <div className="guest-notice-banner">
      <div className="banner-content">
        <InfoIcon className="info-icon" />
        <p>
          You're using <strong>Language Tutor</strong> as a guest.
          <span className="highlight">Sign up for free</span> to unlock:
        </p>
        <ul>
          <li>60-second assessments (vs. 15 seconds)</li>
          <li>5-minute conversations (vs. 1 minute)</li>
          <li>Unlimited practice sessions</li>
          <li>Progress tracking</li>
        </ul>
        <div className="banner-actions">
          <Button 
            variant="contained" 
            color="primary"
            href="/signup"
          >
            Sign Up Free
          </Button>
          <Button 
            variant="text"
            onClick={() => setIsDismissed(true)}
          >
            Continue as Guest
          </Button>
        </div>
      </div>
      <button 
        className="dismiss-button"
        onClick={() => setIsDismissed(true)}
        aria-label="Dismiss notice"
      >
        <CloseIcon />
      </button>
    </div>
  );
};
```

The guest notice banner:
- Appears only for guest users
- Clearly communicates the benefits of signing up
- Provides direct access to the sign-up page
- Can be dismissed for the current session

### Time-Up Modal

```typescript
// From TimeUpModal.tsx
export const TimeUpModal: React.FC<TimeUpModalProps> = ({
  isAuthenticated,
  onClose,
  onSignUp
}) => {
  return (
    <Modal
      isOpen={true}
      onRequestClose={onClose}
      className="time-up-modal"
      overlayClassName="modal-overlay"
    >
      <div className="modal-content">
        <h2>Time's Up!</h2>
        
        {isAuthenticated ? (
          <>
            <p>Your conversation time has ended.</p>
            <p>Would you like to start a new assessment?</p>
            <div className="modal-actions">
              <Button 
                variant="contained" 
                color="primary"
                onClick={onClose}
              >
                Start New Assessment
              </Button>
            </div>
          </>
        ) : (
          <>
            <p>Your guest conversation time has ended.</p>
            <p>
              <strong>Sign up for free</strong> to get longer conversation times
              and unlimited practice sessions!
            </p>
            <div className="modal-actions">
              <Button 
                variant="contained" 
                color="primary"
                onClick={onSignUp}
              >
                Sign Up Free
              </Button>
              <Button 
                variant="outlined"
                onClick={onClose}
              >
                Start New Assessment
              </Button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};
```

The time-up modal:
- Displays different content for guests vs. authenticated users
- Emphasizes the benefits of signing up
- Provides clear next steps
- Maintains a positive user experience

## Limitations and Restrictions

### Assessment Limits

```typescript
// From speaking-assessment.tsx
useEffect(() => {
  // Check if guest has reached assessment limit
  if (!isAuthenticated && hasReachedGuestAssessmentLimit()) {
    setShowLimitModal(true);
  }
}, [isAuthenticated]);

// Render limit modal
{showLimitModal && (
  <LimitModal
    onClose={() => setShowLimitModal(false)}
    onSignUp={() => router.push('/signup')}
  />
)}
```

Guest users face the following limitations:
- Maximum of 3 assessments per session
- 15-second assessment duration (vs. 60 seconds)
- 1-minute conversation time (vs. 5 minutes)
- No progress tracking across sessions

### Back Button Protection

```typescript
// From speech-client.tsx
useEffect(() => {
  // Check if plan is expired when component mounts
  const checkPlanExpiration = () => {
    const planId = sessionStorage.getItem('currentPlanId');
    if (planId && isPlanExpired(planId)) {
      // Redirect to home if plan is expired
      router.replace('/');
      return true;
    }
    return false;
  };
  
  // Check immediately
  const isExpired = checkPlanExpiration();
  if (isExpired) return;
  
  // Set up periodic checks
  const intervalId = setInterval(checkPlanExpiration, 5000);
  
  return () => {
    clearInterval(intervalId);
  };
}, [router]);
```

The application prevents:
- Accessing expired conversations via browser back button
- Extending conversation time by refreshing the page
- Bypassing the time limits through navigation tricks

## Data Management

```python
# From maintenance_tasks.py
async def cleanup_guest_data():
    """Remove old guest data (no user_id) older than 7 days"""
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    
    # Delete old guest learning plans
    result = await learning_plans_collection.delete_many({
        "user_id": None,
        "created_at": {"$lt": cutoff_date}
    })
    
    print(f"Deleted {result.deleted_count} old guest learning plans")
    
    # Delete old guest assessments
    result = await assessments_collection.delete_many({
        "user_id": None,
        "created_at": {"$lt": cutoff_date}
    })
    
    print(f"Deleted {result.deleted_count} old guest assessments")
```

Guest data management includes:
- Temporary storage of guest learning plans and assessments
- Automatic cleanup of guest data after 7 days
- Session storage for tracking guest usage
- No persistent data across browser sessions

## Testing and Debugging

```typescript
// From guest-utils.ts
export const resetGuestData = (): void => {
  try {
    // Clear all guest-related session storage items
    sessionStorage.removeItem('guestAssessmentCount');
    sessionStorage.removeItem('pendingLearningPlanId');
    sessionStorage.removeItem('selectedLanguage');
    sessionStorage.removeItem('selectedLevel');
    
    // Clear expired plan markers
    const keys = Object.keys(sessionStorage);
    keys.forEach(key => {
      if (key.startsWith('plan_') && key.endsWith('_expired')) {
        sessionStorage.removeItem(key);
      }
    });
    
    console.log('Guest data reset successfully');
  } catch (error) {
    console.error('Error resetting guest data:', error);
  }
};
```

Testing tools include:
- Functions to reset guest data for testing
- Clear logging of guest actions
- Debugging utilities for session storage
- Easy simulation of guest limits

## Future Enhancements

1. **Device Fingerprinting**: Implement device fingerprinting to track guest usage across browser sessions
2. **Progressive Disclosure**: Gradually reveal more features as guests engage with the application
3. **Personalized Conversion Messaging**: Tailor sign-up messaging based on guest usage patterns
4. **Guest Preferences**: Allow guests to set and save preferences without authentication
5. **Email Capture**: Provide option for guests to save progress by entering email without full registration
