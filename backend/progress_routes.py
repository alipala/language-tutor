import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from openai import OpenAI
import httpx

from auth import get_current_user
from models import (
    UserResponse, ConversationSession, ConversationMessage, 
    SaveConversationRequest, ConversationStats, ConversationHistoryResponse
)
from database import conversation_sessions_collection, users_collection
from enhanced_analysis import generate_enhanced_analysis

# Initialize OpenAI client with error handling
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables")

# Initialize OpenAI client with error handling for Railway deployment
try:
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized successfully in progress_routes")
except TypeError as e:
    if "proxies" in str(e):
        print("Detected 'proxies' error in OpenAI initialization. Using alternative initialization...")
        # Alternative initialization without proxies
        client = OpenAI(api_key=api_key, http_client=httpx.Client())
        print("OpenAI client initialized with alternative method in progress_routes")
    else:
        print(f"Error initializing OpenAI client in progress_routes: {str(e)}")
        raise

router = APIRouter(prefix="/api/progress", tags=["progress"])

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
        
        # Check if this is a learning plan conversation
        learning_plan_id = getattr(request, 'learning_plan_id', None)
        conversation_type = getattr(request, 'conversation_type', 'practice')
        
        print(f"[PROGRESS] Learning Plan ID: {learning_plan_id}")
        print(f"[PROGRESS] Conversation Type: {conversation_type}")
        
        # If this has a learning plan ID or is not explicitly marked as practice, handle learning plan progress
        if learning_plan_id is not None or conversation_type != 'practice':
            print(f"[PROGRESS] 📚 This is a learning plan session - updating learning plan progress")
            print(f"[PROGRESS] Learning plan conversations should not appear in conversation history")
            
            # Update learning plan progress for learning plan sessions
            await update_learning_plan_progress(current_user.id, request.language, request.level, request.topic)
            
            return {
                "success": True,
                "session_id": "learning_plan_session",
                "message": "Learning plan progress updated successfully",
                "is_streak_eligible": False,
                "summary": "Learning plan session progress updated",
                "action": "learning_plan_updated"
            }
        
        # Convert messages to ConversationMessage objects
        conversation_messages = []
        for msg in request.messages:
            # Handle timestamp parsing - convert 'Z' suffix to proper timezone format
            timestamp_str = msg.get('timestamp', datetime.utcnow().isoformat())
            if timestamp_str.endswith('Z'):
                # Replace 'Z' with '+00:00' for proper ISO format parsing
                timestamp_str = timestamp_str[:-1] + '+00:00'
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                # Convert to UTC if timezone-aware
                if timestamp.tzinfo is not None:
                    timestamp = timestamp.replace(tzinfo=None)
            except ValueError:
                # Fallback to current time if parsing fails
                timestamp = datetime.utcnow()
            
            conversation_messages.append(ConversationMessage(
                role=msg.get('role', 'user'),
                content=msg.get('content', ''),
                timestamp=timestamp
            ))
        
        # Generate conversation summary using OpenAI
        summary = await generate_conversation_summary(conversation_messages, request.language, request.level)
        
        # Determine analysis level based on session quality
        analysis_level = determine_analysis_level(request.duration_minutes, len(conversation_messages))
        print(f"[PROGRESS] Analysis level determined: {analysis_level} (duration: {request.duration_minutes}min, messages: {len(conversation_messages)})")
        
        # Generate enhanced analysis only for qualifying sessions
        enhanced_analysis = None
        if analysis_level == "enhanced":
            print(f"[PROGRESS] Generating enhanced analysis for qualifying session")
            enhanced_analysis = await generate_enhanced_analysis(
                conversation_messages,
                current_user.id,
                request.language,
                request.level,
                request.topic or "general",
                request.duration_minutes
            )
        else:
            print(f"[PROGRESS] Skipping enhanced analysis - session doesn't meet criteria")
        
        # Determine if session is streak eligible (5+ minutes)
        is_streak_eligible = request.duration_minutes >= 5.0
        
        # Check if there's an existing session for this user today with the same language/level/topic
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
                "enhanced_analysis": enhanced_analysis,
                "is_streak_eligible": is_streak_eligible,
                "updated_at": datetime.utcnow()
            }
            
            result = await conversation_sessions_collection.update_one(
                {"_id": existing_session["_id"]},
                {"$set": update_data}
            )
            
            print(f"[PROGRESS] ✅ Conversation updated with ID: {existing_session['_id']}")
            
            # Update learning plan progress if this is a learning plan session
            await update_learning_plan_progress(current_user.id, request.language, request.level, request.topic)
            
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
                "enhanced_analysis": enhanced_analysis,
                "is_streak_eligible": is_streak_eligible,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await conversation_sessions_collection.insert_one(session_dict)
            
            print(f"[PROGRESS] ✅ New conversation saved with ID: {result.inserted_id}")
            
            # Update learning plan progress if this is a learning plan session
            await update_learning_plan_progress(current_user.id, request.language, request.level, request.topic)
            
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

@router.get("/conversations")
async def get_conversation_history(
    limit: int = 10,
    offset: int = 0,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's conversation history"""
    try:
        print(f"[PROGRESS] ===== CONVERSATION HISTORY DEBUG START =====")
        print(f"[PROGRESS] Getting conversation history for user {current_user.id}")
        print(f"[PROGRESS] Limit: {limit}, Offset: {offset}")
        
        # Get total count
        total_count = await conversation_sessions_collection.count_documents({"user_id": current_user.id})
        print(f"[PROGRESS] Total count: {total_count}")
        
        # Get sessions with pagination, sorted by creation date (newest first)
        sessions_cursor = conversation_sessions_collection.find(
            {"user_id": current_user.id}
        ).sort("created_at", -1).skip(offset).limit(limit)
        
        sessions_data = await sessions_cursor.to_list(length=limit)
        print(f"[PROGRESS] Raw sessions data count: {len(sessions_data)}")
        
        # Debug: Print first session structure
        if sessions_data:
            print(f"[PROGRESS] First session structure: {list(sessions_data[0].keys())}")
            print(f"[PROGRESS] First session messages type: {type(sessions_data[0].get('messages', []))}")
            if sessions_data[0].get('messages'):
                print(f"[PROGRESS] First message structure: {list(sessions_data[0]['messages'][0].keys()) if sessions_data[0]['messages'] else 'No messages'}")
        
        # Convert to simple dictionaries - NO PYDANTIC MODELS AT ALL
        sessions = []
        for i, session_data in enumerate(sessions_data):
            try:
                # Convert messages to simple dictionaries
                messages = []
                for j, msg_data in enumerate(session_data.get('messages', [])):
                    # Handle timestamp - keep it simple
                    timestamp = msg_data.get('timestamp', datetime.utcnow())
                    if isinstance(timestamp, str):
                        try:
                            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        except ValueError:
                            timestamp = datetime.utcnow()
                    
                    # Create simple message dict
                    message_dict = {
                        'role': msg_data.get('role', 'user'),
                        'content': msg_data.get('content', ''),
                        'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp)
                    }
                    messages.append(message_dict)
                
                # Handle session timestamps
                created_at = session_data.get('created_at', datetime.utcnow())
                updated_at = session_data.get('updated_at', datetime.utcnow())
                
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except ValueError:
                        created_at = datetime.utcnow()
                
                if isinstance(updated_at, str):
                    try:
                        updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    except ValueError:
                        updated_at = datetime.utcnow()
                
                # Create simple session dictionary - NO PYDANTIC
                session_dict = {
                    'id': str(session_data.get('_id', '')),
                    'user_id': session_data.get('user_id', ''),
                    'language': session_data.get('language', ''),
                    'level': session_data.get('level', ''),
                    'topic': session_data.get('topic'),
                    'messages': messages,
                    'duration_minutes': float(session_data.get('duration_minutes', 0.0)),
                    'message_count': int(session_data.get('message_count', 0)),
                    'summary': session_data.get('summary'),
                    'enhanced_analysis': session_data.get('enhanced_analysis'),
                    'is_streak_eligible': bool(session_data.get('is_streak_eligible', False)),
                    'created_at': created_at.isoformat() if isinstance(created_at, datetime) else str(created_at),
                    'updated_at': updated_at.isoformat() if isinstance(updated_at, datetime) else str(updated_at)
                }
                sessions.append(session_dict)
                print(f"[PROGRESS] Session {i+1} processed successfully")
                
            except Exception as session_error:
                print(f"[PROGRESS] ❌ Error processing session {i+1}: {str(session_error)}")
                print(f"[PROGRESS] Session data keys: {list(session_data.keys())}")
                # Skip this session and continue
                continue
        
        # Get stats
        print(f"[PROGRESS] Getting stats...")
        stats = await get_progress_stats(current_user)
        print(f"[PROGRESS] Stats retrieved successfully")
        
        # Return simple dictionary - NO PYDANTIC
        response = {
            'sessions': sessions,
            'total_count': total_count,
            'stats': stats.dict()
        }
        
        print(f"[PROGRESS] ✅ Retrieved {len(sessions)} conversations successfully")
        print(f"[PROGRESS] ===== CONVERSATION HISTORY DEBUG END =====")
        return response
        
    except Exception as e:
        print(f"[PROGRESS] ❌ CRITICAL ERROR in conversation history: {str(e)}")
        print(f"[PROGRESS] Error type: {type(e)}")
        import traceback
        print(f"[PROGRESS] Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation history: {str(e)}")

@router.get("/conversation/{session_id}/analysis")
async def get_conversation_analysis(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get enhanced analysis for a specific conversation session"""
    try:
        print(f"[PROGRESS] Getting enhanced analysis for session {session_id}")
        
        # Validate ObjectId format
        from bson import ObjectId
        try:
            session_object_id = ObjectId(session_id)
        except:
            raise HTTPException(
                status_code=400,
                detail="Invalid session ID format"
            )
        
        # Find the session
        session = await conversation_sessions_collection.find_one({
            "_id": session_object_id,
            "user_id": current_user.id
        })
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Conversation session not found"
            )
        
        # Get enhanced analysis
        enhanced_analysis = session.get('enhanced_analysis')
        
        if not enhanced_analysis:
            # If no enhanced analysis exists, generate it
            print(f"[PROGRESS] No enhanced analysis found, generating...")
            
            # Convert messages to ConversationMessage objects
            conversation_messages = []
            for msg in session.get('messages', []):
                conversation_messages.append(ConversationMessage(
                    role=msg.get('role', 'user'),
                    content=msg.get('content', ''),
                    timestamp=msg.get('timestamp', datetime.utcnow())
                ))
            
            # Generate enhanced analysis
            enhanced_analysis = await generate_enhanced_analysis(
                conversation_messages,
                current_user.id,
                session.get('language', 'english'),
                session.get('level', 'B1'),
                session.get('topic', 'general'),
                session.get('duration_minutes', 0)
            )
            
            # Save the generated analysis
            await conversation_sessions_collection.update_one(
                {"_id": session_object_id},
                {"$set": {"enhanced_analysis": enhanced_analysis}}
            )
        
        return {
            "session_id": session_id,
            "enhanced_analysis": enhanced_analysis,
            "session_info": {
                "language": session.get('language'),
                "level": session.get('level'),
                "topic": session.get('topic'),
                "duration_minutes": session.get('duration_minutes'),
                "message_count": session.get('message_count'),
                "created_at": session.get('created_at')
            },
            "conversation_messages": session.get('messages', [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PROGRESS] ❌ Error getting conversation analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation analysis: {str(e)}")

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

async def generate_conversation_summary(messages: List[ConversationMessage], language: str, level: str) -> str:
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

def determine_analysis_level(duration_minutes: float, message_count: int) -> str:
    """
    Determine the level of analysis to perform based on session quality
    
    Returns:
    - "enhanced": Full enhanced analysis for quality sessions
    - "basic": Basic summary only for short/low-quality sessions
    """
    # Enhanced analysis criteria:
    # - Duration >= 5 minutes AND message_count >= 10
    # - OR Duration >= 3 minutes AND message_count >= 15 (very active short session)
    
    if duration_minutes >= 5.0 and message_count >= 10:
        return "enhanced"
    elif duration_minutes >= 3.0 and message_count >= 15:
        return "enhanced"
    else:
        return "basic"

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

async def update_learning_plan_progress(user_id: str, language: str, level: str, topic: Optional[str] = None):
    """Update learning plan progress when a conversation is completed"""
    try:
        from database import database
        learning_plans_collection = database.learning_plans
        
        print(f"[LEARNING_PLAN] Checking for learning plan updates for user {user_id}")
        print(f"[LEARNING_PLAN] Session details: {language}, {level}, topic: {topic}")
        
        # Find learning plans for this user that match the conversation parameters
        query = {
            "user_id": str(user_id),
            "language": language,
            "proficiency_level": level
        }
        
        plans_cursor = learning_plans_collection.find(query)
        plans = await plans_cursor.to_list(length=None)
        
        if not plans:
            print(f"[LEARNING_PLAN] No matching learning plans found for user {user_id}")
            return
        
        print(f"[LEARNING_PLAN] Found {len(plans)} matching learning plan(s)")
        
        # If there are multiple plans, only update the most recently created plan
        if len(plans) > 1:
            print(f"[LEARNING_PLAN] Multiple plans found - updating only the most recent one")
            plans_sorted = sorted(plans, key=lambda x: x.get('created_at', ''), reverse=True)
            plans = [plans_sorted[0]]
            print(f"[LEARNING_PLAN] Selected most recent plan: {plans[0].get('id')}")
        
        # Update the selected plan(s) with proper week-based logic
        for plan in plans:
            plan_id = plan.get("id")
            current_completed = plan.get("completed_sessions", 0)
            total_sessions = plan.get("total_sessions", 24)  # Default 6 months * 4 weeks * 1 week = 24 sessions
            
            # Get today's sessions count for this plan
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            # Count sessions for this plan today
            today_sessions = await conversation_sessions_collection.count_documents({
                "user_id": user_id,
                "language": language,
                "level": level,
                "created_at": {
                    "$gte": today_start,
                    "$lte": today_end
                }
            })
            
            print(f"[LEARNING_PLAN] User has {today_sessions} session(s) today")
            
            # Calculate sessions per week (2 sessions per week)
            sessions_per_week = 2
            
            # Calculate current week based on completed sessions
            current_week = (current_completed // sessions_per_week) + 1
            sessions_in_current_week = current_completed % sessions_per_week
            
            print(f"[LEARNING_PLAN] Current progress: Week {current_week}, {sessions_in_current_week}/{sessions_per_week} sessions in week")
            
            # Only increment if this is the first or second session of the day
            # and the week is not already completed
            should_increment = False
            
            if sessions_in_current_week < sessions_per_week:
                # Week is not completed yet
                if today_sessions == 1:
                    # This is the first session today, increment
                    should_increment = True
                    print(f"[LEARNING_PLAN] First session today - incrementing progress")
                elif today_sessions == 2 and sessions_in_current_week == 0:
                    # This is the second session today and we haven't incremented for the first one yet
                    should_increment = True
                    print(f"[LEARNING_PLAN] Second session today, first increment - incrementing progress")
                else:
                    print(f"[LEARNING_PLAN] Not incrementing - either multiple sessions today or week already progressed")
            else:
                print(f"[LEARNING_PLAN] Week {current_week} already completed - not incrementing")
            
            if should_increment:
                # Increment completed sessions
                new_completed = current_completed + 1
                
                # Don't exceed total sessions
                if new_completed > total_sessions:
                    new_completed = total_sessions
                
                # Calculate new progress percentage
                progress_percentage = (new_completed / total_sessions) * 100 if total_sessions > 0 else 0.0
                
                # Update the plan
                result = await learning_plans_collection.update_one(
                    {"id": plan_id},
                    {"$set": {
                        "completed_sessions": new_completed,
                        "progress_percentage": progress_percentage
                    }}
                )
                
                if result.modified_count > 0:
                    new_week = (new_completed // sessions_per_week) + 1
                    new_sessions_in_week = new_completed % sessions_per_week
                    print(f"[LEARNING_PLAN] ✅ Updated plan {plan_id}: {new_completed}/{total_sessions} sessions ({progress_percentage:.1f}%)")
                    print(f"[LEARNING_PLAN] ✅ Now in Week {new_week}, {new_sessions_in_week}/{sessions_per_week} sessions completed")
                else:
                    print(f"[LEARNING_PLAN] ⚠️ No changes made to plan {plan_id}")
            else:
                print(f"[LEARNING_PLAN] ℹ️ No increment needed for plan {plan_id}")
                
    except Exception as e:
        print(f"[LEARNING_PLAN] ❌ Error updating learning plan progress: {str(e)}")
        # Don't raise the exception - this is a non-critical operation
