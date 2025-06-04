import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from openai import OpenAI

from auth import get_current_user
from models import (
    UserResponse, ConversationSession, ConversationMessage, 
    SaveConversationRequest, ConversationStats, ConversationHistoryResponse
)
from database import conversation_sessions_collection, users_collection

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        print(f"[PROGRESS] Getting conversation history for user {current_user.id}")
        print(f"[PROGRESS] Limit: {limit}, Offset: {offset}")
        
        # Get total count
        total_count = await conversation_sessions_collection.count_documents({"user_id": current_user.id})
        
        # Get sessions with pagination, sorted by creation date (newest first)
        sessions_cursor = conversation_sessions_collection.find(
            {"user_id": current_user.id}
        ).sort("created_at", -1).skip(offset).limit(limit)
        
        sessions_data = await sessions_cursor.to_list(length=limit)
        
        # Convert to ConversationSession objects
        sessions = []
        for session_data in sessions_data:
            # Convert messages
            messages = []
            for msg_data in session_data.get('messages', []):
                # Handle timestamp conversion for ConversationMessage
                if 'timestamp' in msg_data and isinstance(msg_data['timestamp'], str):
                    try:
                        msg_data['timestamp'] = datetime.fromisoformat(msg_data['timestamp'].replace('Z', '+00:00'))
                    except ValueError:
                        msg_data['timestamp'] = datetime.utcnow()
                elif 'timestamp' not in msg_data:
                    msg_data['timestamp'] = datetime.utcnow()
                
                # Convert to simple dict instead of Pydantic model
                messages.append({
                    'role': msg_data.get('role', 'user'),
                    'content': msg_data.get('content', ''),
                    'timestamp': msg_data['timestamp']
                })
            
            # Handle session timestamps
            if 'created_at' in session_data and isinstance(session_data['created_at'], str):
                try:
                    session_data['created_at'] = datetime.fromisoformat(session_data['created_at'].replace('Z', '+00:00'))
                except ValueError:
                    session_data['created_at'] = datetime.utcnow()
            
            if 'updated_at' in session_data and isinstance(session_data['updated_at'], str):
                try:
                    session_data['updated_at'] = datetime.fromisoformat(session_data['updated_at'].replace('Z', '+00:00'))
                except ValueError:
                    session_data['updated_at'] = datetime.utcnow()
            
            # Set the converted messages
            session_data['messages'] = messages
            
            # Convert ObjectId to string for the session
            if '_id' in session_data:
                session_data['id'] = str(session_data['_id'])
            
            # Create ConversationSession with proper field mapping
            session = ConversationSession(
                id=session_data.get('id'),
                user_id=session_data['user_id'],
                language=session_data['language'],
                level=session_data['level'],
                topic=session_data.get('topic'),
                messages=messages,
                duration_minutes=session_data.get('duration_minutes', 0.0),
                message_count=session_data.get('message_count', 0),
                summary=session_data.get('summary'),
                is_streak_eligible=session_data.get('is_streak_eligible', False),
                created_at=session_data.get('created_at', datetime.utcnow()),
                updated_at=session_data.get('updated_at', datetime.utcnow())
            )
            sessions.append(session)
        
        # Get stats
        stats = await get_progress_stats(current_user)
        
        response = ConversationHistoryResponse(
            sessions=sessions,
            total_count=total_count,
            stats=stats
        )
        
        print(f"[PROGRESS] ✅ Retrieved {len(sessions)} conversations")
        return response
        
    except Exception as e:
        print(f"[PROGRESS] ❌ Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation history: {str(e)}")

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
