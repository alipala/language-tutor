# Progress Tracking System

## Overview

The Language Tutor application features a comprehensive progress tracking system that allows registered users to save their conversation sessions, view detailed conversation history, track learning statistics, and earn achievements based on their practice activities. This document details the implementation, features, and user experience of the progress tracking system.

## Architecture Overview

The progress tracking system consists of several integrated components:

1. **Save Progress Button**: Allows users to manually save conversation progress during practice sessions
2. **Conversation History Storage**: Automatically stores conversation transcripts with AI-generated summaries
3. **Progress Statistics**: Tracks total sessions, practice time, streaks, and other metrics
4. **Achievement System**: Dynamic achievements based on actual user progress
5. **Profile Integration**: Displays all progress data in a comprehensive user profile

![Progress Tracking Architecture](https://mermaid.ink/img/pako:eNp1kk1PwzAMhv9KlBOgTdCWD8EBaRKHcUBCaAeucXCTlkZLkypxQKXqf8dpt7EB4hTHz-vYsXMBZTVCCdLo1tqeNMqRsrpDOzpnVhvHfbDWOFLK9mT5HvV4Qs-VeqNgLdLGcS-mXWc6Zy2qwegmWNWh5-Aqo0nxXzIZnQXdUPCqQ8cDVnxJOOGWPPeBVhSsGvDYNzRgPXrHJzRWV6jYxRvNZnbUYzCDdp6_JHkxz_NiMZ_N8myRFdl0Oi2ydJbNF_dZnqfpJE1nWZbOkjSdp-nkUPQQNqTxsKVBu_Bwb7QO9-7JOdNQcB_-Nnr0_KAHdDxgS5Yx0ePgOvLhkXbG1-FVGzpjVVgbpTXWYUEb1NhSsGF_-CJJ4mSS7GXxKLmTJPFOEu8k0U4S7yTRThLtJHt_ACVl3Vc?type=png)

## Core Features

### 1. Save Progress Button

The save progress button allows users to manually save their conversation progress during practice sessions.

#### Implementation

```typescript
// From save-progress-button.tsx
export default function SaveProgressButton({ 
  conversationHistory, 
  language, 
  level, 
  topic, 
  duration 
}: SaveProgressButtonProps) {
  const { user } = useAuth();
  const [saveState, setSaveState] = useState<SaveState>('idle');
  const [cooldownTime, setCooldownTime] = useState(0);
  
  // 1-minute cooldown to encourage meaningful conversations
  const COOLDOWN_DURATION = 60; // seconds
  
  const handleSave = async () => {
    if (!user || saveState === 'saving' || cooldownTime > 0) return;
    
    setSaveState('saving');
    
    try {
      const response = await fetch(`${getApiUrl()}/api/progress/save-conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          language,
          level,
          topic,
          messages: conversationHistory,
          duration_minutes: duration / 60
        })
      });
      
      if (response.ok) {
        setSaveState('saved');
        startCooldown();
        setTimeout(() => setSaveState('idle'), 2000);
      } else {
        setSaveState('error');
        setTimeout(() => setSaveState('idle'), 3000);
      }
    } catch (error) {
      console.error('Error saving progress:', error);
      setSaveState('error');
      setTimeout(() => setSaveState('idle'), 3000);
    }
  };
  
  // Visual feedback with dynamic states
  const getButtonContent = () => {
    switch (saveState) {
      case 'saving':
        return (
          <>
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
            Saving...
          </>
        );
      case 'saved':
        return (
          <>
            <Check className="h-4 w-4 mr-2" />
            Saved ✓
          </>
        );
      case 'error':
        return (
          <>
            <AlertCircle className="h-4 w-4 mr-2" />
            Retry Save
          </>
        );
      default:
        return cooldownTime > 0 ? (
          <>
            <Clock className="h-4 w-4 mr-2" />
            Wait {cooldownTime}s
          </>
        ) : (
          <>
            <Save className="h-4 w-4 mr-2" />
            💾 Save Progress
          </>
        );
    }
  };
  
  return (
    <button
      onClick={handleSave}
      disabled={!user || saveState === 'saving' || cooldownTime > 0}
      className={`save-progress-button ${saveState} ${cooldownTime > 0 ? 'cooldown' : ''}`}
    >
      {getButtonContent()}
    </button>
  );
}
```

#### Key Features

- **1-Minute Cooldown**: Prevents spam clicking and encourages meaningful conversations
- **Dynamic Visual States**: 
  - `💾 Save Progress` (default)
  - `Saving...` (with spinner)
  - `Saved ✓` (success with checkmark)
  - `Wait 60s` (cooldown countdown)
  - `Retry Save` (error state)
- **Smart Visibility**: Only appears for authenticated users with active sessions
- **Session Extension**: Updates existing conversations instead of creating duplicates

### 2. Conversation History Storage

The system automatically stores conversation transcripts with AI-generated summaries.

#### Backend Implementation

```python
# From progress_routes.py
@router.post("/save-conversation")
async def save_conversation(
    request: SaveConversationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Save a conversation session for a registered user"""
    try:
        print(f"[PROGRESS] Saving conversation for user {current_user.id}")
        print(f"[PROGRESS] Language: {request.language}, Level: {request.level}")
        print(f"[PROGRESS] Duration: {request.duration_minutes} minutes")
        print(f"[PROGRESS] Messages count: {len(request.messages)}")
        
        # Convert messages to ConversationMessage objects
        conversation_messages = []
        for msg in request.messages:
            # Handle timestamp parsing
            timestamp_str = msg.get('timestamp', datetime.utcnow().isoformat())
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                if timestamp.tzinfo is not None:
                    timestamp = timestamp.replace(tzinfo=None)
            except ValueError:
                timestamp = datetime.utcnow()
            
            conversation_messages.append(ConversationMessage(
                role=msg.get('role', 'user'),
                content=msg.get('content', ''),
                timestamp=timestamp
            ))
        
        # Generate conversation summary using OpenAI
        summary = await generate_conversation_summary(
            conversation_messages, 
            request.language, 
            request.level
        )
        
        # Determine if session is streak eligible (5+ minutes)
        is_streak_eligible = request.duration_minutes >= 5.0
        
        # Check for existing session today with same language/level/topic
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        existing_session = await conversation_sessions_collection.find_one({
            "user_id": current_user.id,
            "language": request.language,
            "level": request.level,
            "topic": request.topic,
            "created_at": {
                "$gte": today_start,
                "$lte": today_end
            }
        })
        
        if existing_session:
            # Update existing session
            print(f"[PROGRESS] Updating existing session: {existing_session['_id']}")
            
            update_data = {
                "messages": [msg.dict() for msg in conversation_messages],
                "duration_minutes": request.duration_minutes,
                "message_count": len(conversation_messages),
                "summary": summary,
                "is_streak_eligible": is_streak_eligible,
                "updated_at": datetime.utcnow()
            }
            
            result = await conversation_sessions_collection.update_one(
                {"_id": existing_session["_id"]},
                {"$set": update_data}
            )
            
            print(f"[PROGRESS] ✅ Conversation updated with ID: {existing_session['_id']}")
            
            return {
                "success": True,
                "session_id": str(existing_session["_id"]),
                "message": "Conversation updated successfully",
                "is_streak_eligible": is_streak_eligible,
                "summary": summary,
                "action": "updated"
            }
        else:
            # Create new session
            print(f"[PROGRESS] Creating new conversation session")
            
            session_dict = {
                "user_id": current_user.id,
                "language": request.language,
                "level": request.level,
                "topic": request.topic,
                "messages": [msg.dict() for msg in conversation_messages],
                "duration_minutes": request.duration_minutes,
                "message_count": len(conversation_messages),
                "summary": summary,
                "is_streak_eligible": is_streak_eligible,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await conversation_sessions_collection.insert_one(session_dict)
            
            print(f"[PROGRESS] ✅ New conversation saved with ID: {result.inserted_id}")
            
            return {
                "success": True,
                "session_id": str(result.inserted_id),
                "message": "Conversation saved successfully",
                "is_streak_eligible": is_streak_eligible,
                "summary": summary,
                "action": "created"
            }
        
    except Exception as e:
        print(f"[PROGRESS] ❌ Error saving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save conversation: {str(e)}")
```

#### AI-Generated Summaries

```python
# From progress_routes.py
async def generate_conversation_summary(
    messages: List[ConversationMessage], 
    language: str, 
    level: str
) -> str:
    """Generate a summary of the conversation using OpenAI"""
    try:
        if not messages:
            return "Empty conversation"
        
        # Create conversation text
        conversation_text = ""
        for msg in messages:
            role = "Student" if msg.role == "user" else "Tutor"
            conversation_text += f"{role}: {msg.content}\n"
        
        # Generate summary
        prompt = f"""Summarize this {language} language learning conversation at {level} level in 1-2 sentences. Focus on the main topics discussed and learning progress shown.

Conversation:
{conversation_text}

Summary:"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a language learning assistant. Create brief, helpful summaries of student conversations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        print(f"[PROGRESS] Generated summary: {summary}")
        return summary
        
    except Exception as e:
        print(f"[PROGRESS] ❌ Error generating summary: {str(e)}")
        return f"Conversation in {language} ({level} level) - {len(messages)} messages"
```

#### Session Management Strategy

- **One Session Per Day**: Per language/level/topic combination
- **Session Extension**: Updates existing conversations instead of creating duplicates
- **Comprehensive Summaries**: AI-generated summaries that update as conversation grows
- **Streak Tracking**: Sessions ≥5 minutes count toward learning streaks

### 3. Database Schema

```python
# From models.py
class ConversationMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationSession(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    language: str
    level: str
    topic: Optional[str] = None
    messages: List[ConversationMessage] = []
    duration_minutes: float = 0.0
    message_count: int = 0
    summary: Optional[str] = None
    is_streak_eligible: bool = False  # True if session >= 5 minutes
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
```

Sample conversation session document:
```json
{
  "_id": ObjectId("68408bce9dc9ec64c1cbcf6c"),
  "user_id": "683decf8103a7bbacfa3a88b",
  "language": "english",
  "level": "B2",
  "topic": "movies",
  "messages": [
    {
      "role": "user",
      "content": "I think traveling is a great way to learn about different cultures.",
      "timestamp": "2025-06-04T20:07:42.154Z"
    },
    {
      "role": "assistant", 
      "content": "That's a wonderful perspective! What's the most interesting culture you've encountered?",
      "timestamp": "2025-06-04T20:07:45.234Z"
    }
  ],
  "duration_minutes": 3.47,
  "message_count": 34,
  "summary": "The student and tutor discussed the student's interest in improving their English language skills, particularly focusing on grammar. The tutor suggested working on conversational skills, and they practiced discussing the student's favorite hobby of playing chess.",
  "is_streak_eligible": false,
  "created_at": "2025-06-04T20:07:42.154Z",
  "updated_at": "2025-06-04T20:09:15.678Z"
}
```

### 4. Progress Statistics

The system tracks comprehensive learning statistics for each user.

#### Backend Implementation

```python
# From progress_routes.py
@router.get("/stats")
async def get_progress_stats(current_user: UserResponse = Depends(get_current_user)):
    """Get user's conversation statistics"""
    try:
        print(f"[PROGRESS] Getting stats for user {current_user.id}")
        
        # Get all user's sessions
        sessions_cursor = conversation_sessions_collection.find({"user_id": current_user.id})
        sessions = await sessions_cursor.to_list(length=None)
        
        # Calculate basic stats
        total_sessions = len(sessions)
        total_minutes = sum(session.get('duration_minutes', 0) for session in sessions)
        
        # Calculate streak
        current_streak, longest_streak = await calculate_streaks(current_user.id)
        
        # Calculate sessions this week/month
        now = datetime.utcnow()
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        
        sessions_this_week = len([s for s in sessions if s.get('created_at', datetime.min) >= week_start])
        sessions_this_month = len([s for s in sessions if s.get('created_at', datetime.min) >= month_start])
        
        stats = ConversationStats(
            total_sessions=total_sessions,
            total_minutes=total_minutes,
            current_streak=current_streak,
            longest_streak=longest_streak,
            sessions_this_week=sessions_this_week,
            sessions_this_month=sessions_this_month
        )
        
        print(f"[PROGRESS] ✅ Stats calculated: {stats.dict()}")
        return stats
        
    except Exception as e:
        print(f"[PROGRESS] ❌ Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
```

#### Streak Calculation

```python
# From progress_routes.py
async def calculate_streaks(user_id: str) -> tuple[int, int]:
    """Calculate current and longest streak for a user"""
    try:
        # Get all streak-eligible sessions, sorted by date
        sessions_cursor = conversation_sessions_collection.find(
            {"user_id": user_id, "is_streak_eligible": True}
        ).sort("created_at", 1)
        
        sessions = await sessions_cursor.to_list(length=None)
        
        if not sessions:
            return 0, 0
        
        # Group sessions by date
        session_dates = set()
        for session in sessions:
            date = session.get('created_at', datetime.min).date()
            session_dates.add(date)
        
        sorted_dates = sorted(session_dates)
        
        # Calculate current streak
        current_streak = 0
        today = datetime.utcnow().date()
        
        # Check if user practiced today or yesterday
        if today in sorted_dates:
            current_date = today
        elif (today - timedelta(days=1)) in sorted_dates:
            current_date = today - timedelta(days=1)
        else:
            current_streak = 0
            current_date = None
        
        if current_date:
            for date in reversed(sorted_dates):
                if date == current_date:
                    current_streak += 1
                    current_date -= timedelta(days=1)
                elif date == current_date:
                    continue
                else:
                    break
        
        # Calculate longest streak
        longest_streak = 0
        temp_streak = 0
        prev_date = None
        
        for date in sorted_dates:
            if prev_date is None or date == prev_date + timedelta(days=1):
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1
            prev_date = date
        
        print(f"[PROGRESS] Calculated streaks - Current: {current_streak}, Longest: {longest_streak}")
        return current_streak, longest_streak
        
    except Exception as e:
        print(f"[PROGRESS] ❌ Error calculating streaks: {str(e)}")
        return 0, 0
```

### 5. Achievement System

The achievement system provides dynamic achievements based on actual user progress.

#### Backend Implementation

```python
# From progress_routes.py
@router.get("/achievements")
async def get_user_achievements(current_user: UserResponse = Depends(get_current_user)):
    """Get user's achievements based on their progress"""
    try:
        print(f"[PROGRESS] Getting achievements for user {current_user.id}")
        
        # Get user stats
        stats = await get_progress_stats(current_user)
        
        # Define achievements
        achievements = []
        
        # First Steps (1 conversation)
        if stats.total_sessions >= 1:
            achievements.append({
                "name": "First Steps",
                "icon": "🎯",
                "description": "Complete your first conversation",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Chatterbox (5 conversations)
        if stats.total_sessions >= 5:
            achievements.append({
                "name": "Chatterbox",
                "icon": "💬",
                "description": "Complete 5 conversations",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Dedicated Learner (30 minutes total)
        if stats.total_minutes >= 30:
            achievements.append({
                "name": "Dedicated Learner",
                "icon": "📚",
                "description": "Practice for 30 minutes total",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Consistency King (3-day streak)
        if stats.current_streak >= 3:
            achievements.append({
                "name": "Consistency King",
                "icon": "👑",
                "description": "Maintain a 3-day streak",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Week Warrior (7-day streak)
        if stats.current_streak >= 7:
            achievements.append({
                "name": "Week Warrior",
                "icon": "🔥",
                "description": "Maintain a 7-day streak",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Marathon Master (60 minutes total)
        if stats.total_minutes >= 60:
            achievements.append({
                "name": "Marathon Master",
                "icon": "🏃",
                "description": "Practice for 60 minutes total",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Conversation Pro (10 conversations)
        if stats.total_sessions >= 10:
            achievements.append({
                "name": "Conversation Pro",
                "icon": "⭐",
                "description": "Complete 10 conversations",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        # Monthly Master (30-day streak)
        if stats.current_streak >= 30:
            achievements.append({
                "name": "Monthly Master",
                "icon": "🏆",
                "description": "Maintain a 30-day streak",
                "earned": True,
                "date": datetime.utcnow().strftime("%b %d, %Y")
            })
        
        print(f"[PROGRESS] ✅ User has {len(achievements)} achievements")
        return {"achievements": achievements}
        
    except Exception as e:
        print(f"[PROGRESS] ❌ Error getting achievements: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get achievements: {str(e)}")
```

#### Achievement Types

- **First Steps** 🎯: Complete your first conversation
- **Chatterbox** 💬: Complete 5 conversations  
- **Dedicated Learner** 📚: Practice for 30 minutes total
- **Consistency King** 👑: Maintain a 3-day streak
- **Week Warrior** 🔥: Maintain a 7-day streak
- **Marathon Master** 🏃: Practice for 60 minutes total
- **Conversation Pro** ⭐: Complete 10 conversations
- **Monthly Master** 🏆: Maintain a 30-day streak

### 6. Profile Page Integration

The profile page displays comprehensive progress information in an intuitive interface.

#### Frontend Implementation

```typescript
// From profile/page.tsx
{/* Conversation History */}
<div className="bg-white rounded-2xl shadow-lg p-6">
  <div className="flex items-center justify-between mb-6">
    <h3 className="text-xl font-bold text-gray-800 flex items-center">
      <Mic className="h-6 w-6 mr-2" style={{ color: '#4ECFBF' }} />
      Conversation History
      <span className="ml-2 bg-teal-100 text-teal-700 text-xs px-2 py-0.5 rounded-full">
        {progressStats?.total_sessions || 0} sessions
      </span>
    </h3>
    <div className="text-sm text-gray-500">
      {progressStats?.total_minutes ? `${Math.round(progressStats.total_minutes)} minutes practiced` : ''}
    </div>
  </div>
  
  {statsLoading ? (
    <div className="flex justify-center items-center py-8">
      <div className="animate-spin h-6 w-6 border-2 border-teal-500 border-t-transparent rounded-full"></div>
    </div>
  ) : conversationHistory.length === 0 ? (
    <div className="text-center py-8">
      <div className="w-16 h-16 mx-auto mb-4 bg-teal-100 rounded-full flex items-center justify-center">
        <Mic className="h-8 w-8 text-teal-500" />
      </div>
      <h4 className="text-lg font-medium text-gray-800 mb-2">No Conversations Yet</h4>
      <p className="text-gray-600 mb-4">Start practicing to see your conversation history here.</p>
      <Button 
        onClick={() => router.push('/speech')}
        className="text-white py-2 px-6 rounded-lg shadow-md hover:shadow-lg transition-all"
        style={{ backgroundColor: '#4ECFBF' }}
      >
        Start Practicing
      </Button>
    </div>
  ) : (
    <div className="space-y-4">
      {conversationHistory.slice(0, 5).map((session, index) => (
        <div key={session.id || index} className="border rounded-xl p-4" style={{ backgroundColor: '#F0FDFA', borderColor: 'rgba(78, 207, 191, 0.2)' }}>
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold" style={{ backgroundColor: '#4ECFBF' }}>
                {session.language?.charAt(0)?.toUpperCase() || 'L'}
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 capitalize">
                  {session.language} - {session.level}
                </h4>
                <p className="text-sm text-gray-600">
                  {session.topic && `Topic: ${session.topic} • `}
                  {Math.round(session.duration_minutes || 0)} min • {session.message_count || 0} messages
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-gray-500">
                {session.created_at ? new Date(session.created_at).toLocaleDateString('en-US', { 
                  month: 'short', 
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                }) : 'Recent'}
              </div>
              {session.is_streak_eligible && (
                <div className="flex items-center text-xs text-green-600 mt-1">
                  <Flame className="h-3 w-3 mr-1" />
                  Streak eligible
                </div>
              )}
            </div>
          </div>
          
          {session.summary && (
            <div className="bg-white rounded-lg p-3 text-sm text-gray-700">
              <strong>Summary:</strong> {session.summary}
            </div>
          )}
        </div>
      ))}
      
      {conversationHistory.length > 5 && (
        <div className="text-center pt-4">
          <button 
            className="text-sm font-medium hover:opacity-80 transition-opacity"
            style={{ color: '#4ECFBF' }}
          >
            View all {conversationHistory.length} conversations
          </button>
        </div>
      )}
    </div>
  )}
</div>
```

#### Profile Features

- **Hero Section**: User stats with total XP, current level, streak, and achievements
- **Conversation History**: Recent sessions with summaries and details
- **Progress Statistics**: Total sessions, minutes practiced, streaks
- **Achievement Display**: Earned achievements with dates and descriptions
- **Learning Plans**: Integration with existing learning plan system

### 7. Browser Navigation Protection

The system includes a leave conversation modal to protect against accidental navigation.

#### Implementation

```typescript
// From leave-conversation-modal.tsx
export default function LeaveConversationModal({
  isOpen,
  onClose,
  onSaveAndLeave,
  onStayAndContinue,
  practiceTime,
  hasUnsavedProgress
}: LeaveConversationModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center text-lg font-semibold">
            <AlertTriangle className="h-5 w-5 mr-2 text-amber-500" />
            Leave Conversation?
          </DialogTitle>
        </DialogHeader>
        
        <div className="py-4">
          <p className="text-gray-600 mb-4">
            You've been practicing for <strong>{Math.floor(practiceTime / 60)}:{(practiceTime % 60).toString().padStart(2, '0')}</strong>.
          </p>
          
          {hasUnsavedProgress && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
              <p className="text-amber-800 text-sm">
                💡 <strong>Tip:</strong> Save your progress to track your learning journey and earn achievements!
              </p>
            </div>
          )}
          
          <p className="text-gray-600">
            What would you like to do?
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            variant="outline"
            onClick={onStayAndContinue}
            className="flex-1"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Stay & Continue
          </Button>
          
          <Button
            onClick={onSaveAndLeave}
            className="flex-1 bg-teal-600 hover:bg-teal-700 text-white"
          >
            <Save className="h-4 w-4 mr-2" />
            Save & Leave
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

#### Navigation Protection Features

- **Browser Back Button**: Intercepts navigation attempts
- **Page Refresh Protection**: Warns before losing unsaved progress
- **Tab Close Protection**: Prevents accidental tab closure
- **Auto-Save Integration**: "Save & Leave" button triggers progress saving
- **Practice Time Display**: Shows elapsed conversation time
- **User-Friendly Options**: "Stay & Continue" and "Save & Leave" choices

## API Endpoints

### Progress Tracking Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/progress/save-conversation` | POST | Save conversation session with messages and metadata |
| `/api/progress/stats` | GET | Get user's progress statistics (sessions, minutes, streaks) |
| `/api/progress/conversations` | GET | Get user's conversation history with pagination |
| `/api/progress/achievements` | GET | Get user's earned achievements based on progress |

### Request/Response Examples

#### Save Conversation Request
```json
{
  "language": "english",
  "level": "B2", 
  "topic": "movies",
  "messages": [
    {
      "role": "user",
      "content": "I love watching movies in my free time.",
      "timestamp": "2025-06-04T20:07:42.154Z"
    },
    {
      "role": "assistant",
      "content": "That's great! What's your favorite genre?",
      "timestamp": "2025-06-04T20:07:45.234Z"
    }
  ],
  "duration_minutes": 3.47
}
```

#### Progress Stats Response
```json
{
  "total_sessions": 5,
  "total_minutes": 12.44,
  "current_streak": 0,
  "longest_streak": 0,
  "sessions_this_week": 5,
  "sessions_this_month": 5
}
```

## User Experience Flow

### 1. Starting a Practice Session
1. User navigates to speech practice page
2. Selects language, level, and topic
3. Begins conversation with AI tutor
4. Save Progress button appears after meaningful conversation

### 2. During Practice
1. User engages in conversation with AI tutor
2. Save Progress button shows with 1-minute cooldown
3. Button provides visual feedback during save process
4. Conversation continues with updated progress

### 3. Ending Practice
1. User attempts to navigate away
2. Leave Conversation modal appears if unsaved progress exists
3. User can choose to save progress or continue practicing
4. Progress is saved with AI-generated summary

### 4. Viewing Progress
1. User navigates to profile page
2. Conversation history displays with summaries
3. Progress statistics show total practice time and streaks
4. Achievements are displayed based on actual progress

## Technical Implementation Details

### Database Collections

#### conversation_sessions
```javascript
{
  _id: ObjectId,
  user_id: String,
  language: String,
  level: String, 
  topic: String,
  messages: [ConversationMessage],
  duration_minutes: Number,
  message_count: Number,
  summary: String,
  is_streak_eligible: Boolean,
  created_at: Date,
  updated_at: Date
}
```

#### Database Indexes
- `user_id` + `created_at` (compound index for user history queries)
- `user_id` + `language` + `level` + `topic` + `created_at` (session lookup)
- `created_at` (TTL index for data retention)

### Frontend State Management

#### Save Progress Button States
- `idle`: Default state, ready to save
- `saving`: API request in progress
- `saved`: Successfully saved with checkmark
- `error`: Save failed, retry available
- `cooldown`: 1-minute cooldown active

#### Conversation History State
- `loading`: Fetching conversation data
- `loaded`: Data successfully retrieved
- `error`: Failed to load data
- `empty`: No conversations found

### Error Handling

#### Backend Error Scenarios
- Invalid user authentication
- Database connection failures
- OpenAI API failures for summaries
- Malformed request data
- Duplicate session conflicts

#### Frontend Error Scenarios
- Network connectivity issues
- Authentication token expiration
- Save operation timeouts
- Navigation protection failures

### Performance Considerations

#### Backend Optimizations
- Efficient MongoDB queries with proper indexing
- Asynchronous processing for AI summary generation
- Session extension instead of duplicate creation
- Comprehensive error logging for debugging

#### Frontend Optimizations
- Debounced save operations with cooldown
- Lazy loading of conversation history
- Optimistic UI updates for better UX
- Efficient state management with React hooks

## Security Considerations

### Data Protection
- User conversations are encrypted in transit
- Authentication required for all progress operations
- User data isolation in database queries
- Secure token validation for API access

### Privacy Features
- Conversation summaries generated server-side
- No client-side storage of sensitive conversation data
- User control over progress saving
- Clear data retention policies

## Testing Strategy

### Backend Testing
- Unit tests for progress calculation logic
- Integration tests for API endpoints
- Database operation testing
- Error handling validation

### Frontend Testing
- Component testing for save progress button
- Integration testing for conversation flow
- Navigation protection testing
- User interaction testing

## Deployment Considerations

### Environment Variables
```
OPENAI_API_KEY=your-openai-api-key
MONGODB_URL=your-mongodb-connection-string
DATABASE_NAME=language_tutor
```

### Database Setup
- Create conversation_sessions collection
- Set up appropriate indexes
- Configure TTL for data retention
- Set up backup procedures

### Monitoring
- Track save operation success rates
- Monitor conversation summary generation
- Alert on database performance issues
- Log user engagement metrics

## Future Enhancements

### Planned Features
1. **Detailed Analytics**: More granular progress tracking
2. **Goal Setting**: User-defined learning objectives
3. **Social Features**: Share achievements with friends
4. **Export Options**: Download conversation history
5. **Advanced Achievements**: More complex achievement criteria

### Technical Improvements
1. **Real-time Sync**: Live progress updates across devices
2. **Offline Support**: Save progress when offline
3. **Performance Optimization**: Faster conversation loading
4. **Enhanced Summaries**: More detailed AI analysis
5. **Data Visualization**: Charts and graphs for progress

## Conclusion

The Progress Tracking System provides a comprehensive solution for monitoring and encouraging user engagement in language learning. By combining manual save controls, automatic conversation storage, AI-generated summaries, and dynamic achievements, the system creates a motivating and informative experience for language learners.

The implementation balances user control with automation, ensuring that progress is captured meaningfully while providing clear feedback and motivation through achievements and statistics. The system is designed to scale with user growth and can be extended with additional features as needed.
