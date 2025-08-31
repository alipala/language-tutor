#!/usr/bin/env python3
"""
Comprehensive check of ALL collections in Railway production DB for user conversation data
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

# Production MongoDB connection
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

async def comprehensive_db_check():
    """Check ALL collections for user conversation data"""
    
    print("🔍 COMPREHENSIVE DATABASE CHECK - ALL COLLECTIONS")
    print("=" * 70)
    
    # Connect to production MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    user_id = "688921c268819565ef1ce3dc"
    user_object_id = ObjectId(user_id)
    
    print(f"👤 User ID: {user_id}")
    print(f"📧 Target Email: alipala.ist@gmail.com")
    print()
    
    # Get all collection names
    collection_names = await db.list_collection_names()
    print(f"📊 Found {len(collection_names)} collections:")
    for name in sorted(collection_names):
        print(f"   - {name}")
    print()
    
    total_conversation_minutes = 0.0
    total_sessions = 0
    
    # Check each collection for user data
    for collection_name in sorted(collection_names):
        print(f"🔍 Checking collection: {collection_name}")
        collection = db[collection_name]
        
        # Try different user ID formats
        queries = [
            {"user_id": user_object_id},
            {"user_id": user_id},
            {"userId": user_object_id},
            {"userId": user_id},
            {"_id": user_object_id},
            {"email": "alipala.ist@gmail.com"}
        ]
        
        found_docs = []
        for query in queries:
            try:
                docs = await collection.find(query).to_list(None)
                if docs:
                    found_docs.extend(docs)
                    break  # Found docs with this query, no need to try others
            except Exception as e:
                continue
        
        if found_docs:
            print(f"   ✅ Found {len(found_docs)} documents")
            
            for i, doc in enumerate(found_docs):
                print(f"      Doc {i+1}:")
                
                # Check for various duration/conversation fields
                duration_fields = [
                    'duration', 'conversation_duration', 'practice_minutes_used',
                    'total_duration', 'speaking_duration', 'conversation_time'
                ]
                
                for field in duration_fields:
                    if field in doc and doc[field]:
                        value = doc[field]
                        if isinstance(value, (int, float)) and value > 0:
                            print(f"         {field}: {value}")
                            if field in ['duration', 'conversation_duration', 'speaking_duration', 'conversation_time']:
                                total_conversation_minutes += float(value)
                
                # Check for sessions array
                if 'sessions' in doc and doc['sessions']:
                    sessions = doc['sessions']
                    print(f"         sessions: {len(sessions)} sessions found")
                    
                    for j, session in enumerate(sessions):
                        session_duration = 0.0
                        session_info = []
                        
                        # Check session duration fields
                        for field in ['duration', 'conversation_duration', 'speaking_duration']:
                            if field in session and session[field]:
                                session_duration = float(session[field])
                                session_info.append(f"{field}={session_duration}")
                                break
                        
                        # Check conversation_data
                        if 'conversation_data' in session and session['conversation_data']:
                            conv_data = session['conversation_data']
                            if isinstance(conv_data, dict) and 'duration' in conv_data:
                                session_duration = float(conv_data['duration'])
                                session_info.append(f"conv_data_duration={session_duration}")
                        
                        # Check messages for duration calculation
                        if 'messages' in session and len(session['messages']) >= 2:
                            try:
                                messages = session['messages']
                                first_time = messages[0].get('timestamp')
                                last_time = messages[-1].get('timestamp')
                                if first_time and last_time:
                                    if isinstance(first_time, str):
                                        first_dt = datetime.fromisoformat(first_time.replace('Z', '+00:00'))
                                    else:
                                        first_dt = first_time
                                    
                                    if isinstance(last_time, str):
                                        last_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                                    else:
                                        last_dt = last_time
                                    
                                    calc_duration = (last_dt - first_dt).total_seconds() / 60.0
                                    if calc_duration > 0:
                                        session_duration = calc_duration
                                        session_info.append(f"calculated_from_messages={calc_duration:.2f}")
                            except Exception as e:
                                pass
                        
                        if session_duration > 0:
                            total_conversation_minutes += session_duration
                            total_sessions += 1
                            completed_at = session.get('completed_at', 'Unknown')
                            print(f"            Session {j+1}: {session_duration:.2f} min on {completed_at} ({', '.join(session_info)})")
                
                # Check for messages array (direct conversation)
                if 'messages' in doc and doc['messages']:
                    messages = doc['messages']
                    print(f"         messages: {len(messages)} messages")
                    
                    if len(messages) >= 2:
                        try:
                            first_time = messages[0].get('timestamp')
                            last_time = messages[-1].get('timestamp')
                            if first_time and last_time:
                                if isinstance(first_time, str):
                                    first_dt = datetime.fromisoformat(first_time.replace('Z', '+00:00'))
                                else:
                                    first_dt = first_time
                                
                                if isinstance(last_time, str):
                                    last_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                                else:
                                    last_dt = last_time
                                
                                calc_duration = (last_dt - first_dt).total_seconds() / 60.0
                                if calc_duration > 0:
                                    total_conversation_minutes += calc_duration
                                    total_sessions += 1
                                    print(f"            Conversation duration from messages: {calc_duration:.2f} min")
                        except Exception as e:
                            print(f"            Error calculating message duration: {e}")
                
                # Show creation/completion dates
                date_fields = ['created_at', 'completed_at', 'timestamp', 'date']
                for field in date_fields:
                    if field in doc and doc[field]:
                        print(f"         {field}: {doc[field]}")
                
                print()
        else:
            print(f"   ❌ No documents found")
        
        print()
    
    print("🎯 FINAL COMPREHENSIVE TOTALS:")
    print("=" * 50)
    print(f"🎯 TOTAL CONVERSATION MINUTES FOUND: {total_conversation_minutes:.2f}")
    print(f"📊 TOTAL CONVERSATION SESSIONS FOUND: {total_sessions}")
    print()
    
    # Compare with user record
    user = await db.users.find_one({"_id": user_object_id})
    if user:
        recorded_minutes = user.get('practice_minutes_used', 0.0)
        recorded_sessions = user.get('practice_sessions_used', 0)
        
        print("🔍 COMPARISON WITH USER RECORD:")
        print(f"   User record minutes: {recorded_minutes}")
        print(f"   User record sessions: {recorded_sessions}")
        print(f"   Found actual minutes: {total_conversation_minutes:.2f}")
        print(f"   Found actual sessions: {total_sessions}")
        print(f"   Minutes difference: {abs(recorded_minutes - total_conversation_minutes):.2f}")
        print(f"   Sessions difference: {abs(recorded_sessions - total_sessions)}")
        
        # Show backfill details
        if 'backfill_details' in user:
            backfill = user['backfill_details']
            print(f"\n📋 BACKFILL DETAILS:")
            print(f"   Learning plan sessions: {backfill.get('learning_plan_sessions', 0)}")
            print(f"   Conversation minutes: {backfill.get('conversation_minutes', 0)}")
            print(f"   Total minutes: {backfill.get('total_minutes', 0)}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(comprehensive_db_check())
