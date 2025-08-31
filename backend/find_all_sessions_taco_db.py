#!/usr/bin/env python3
"""
Find ALL conversation sessions in Taco DB Railway production service
Based on screenshot showing: 10 Dutch sessions + 1 English B2 session = 11 total
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

async def find_all_sessions_taco_db():
    """Find all conversation sessions in Taco DB production"""
    
    print("🔍 SEARCHING TACO DB RAILWAY PRODUCTION FOR ALL SESSIONS")
    print("=" * 70)
    print("📊 Expected from screenshot: 10 Dutch sessions + 1 English B2 session")
    print("=" * 70)
    
    # Railway production MongoDB URL for Taco DB
    MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
    DATABASE_NAME = "language_tutor"
    
    print(f"🔗 Connecting to Taco DB: {MONGODB_URL[:50]}...")
    print(f"🗄️  Database: {DATABASE_NAME}")
    print()
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    user_id = "688921c268819565ef1ce3dc"
    user_object_id = ObjectId(user_id)
    
    print(f"👤 User ID: {user_id}")
    print(f"📧 Email: alipala.ist@gmail.com")
    print()
    
    # Get all collections
    collections = await db.list_collection_names()
    print(f"📊 Found {len(collections)} collections in Taco DB:")
    for col in sorted(collections):
        print(f"   - {col}")
    print()
    
    total_minutes = 0.0
    total_sessions = 0
    dutch_sessions = 0
    english_sessions = 0
    
    print("🔍 SEARCHING ALL COLLECTIONS FOR SESSION DATA:")
    print("=" * 60)
    
    # Check each collection thoroughly
    for collection_name in sorted(collections):
        print(f"\n📁 Collection: {collection_name}")
        collection = db[collection_name]
        
        # Try all possible user ID variations
        user_queries = [
            {"user_id": user_id},           # String format
            {"user_id": user_object_id},    # ObjectId format
            {"userId": user_id},
            {"userId": user_object_id},
            {"_id": user_object_id},
            {"email": "alipala.ist@gmail.com"}
        ]
        
        found_any = False
        
        for query in user_queries:
            try:
                docs = await collection.find(query).to_list(None)
                if docs:
                    found_any = True
                    print(f"   ✅ Found {len(docs)} documents with query: {query}")
                    
                    for i, doc in enumerate(docs):
                        print(f"      📄 Document {i+1}:")
                        
                        # Look for sessions array (learning plans)
                        if 'sessions' in doc and doc['sessions']:
                            sessions = doc['sessions']
                            print(f"         📚 Sessions array: {len(sessions)} sessions")
                            
                            # Check plan language/level
                            plan_name = doc.get('name', 'Unknown')
                            language = doc.get('language', 'Unknown')
                            level = doc.get('level', 'Unknown')
                            print(f"         🏷️  Plan: {plan_name} | Language: {language} | Level: {level}")
                            
                            for j, session in enumerate(sessions):
                                if session.get('completed_at'):
                                    # Calculate session duration
                                    duration = 0.0
                                    duration_source = ""
                                    
                                    # Check various duration fields
                                    if 'conversation_duration' in session:
                                        duration = float(session['conversation_duration'])
                                        duration_source = "conversation_duration"
                                    elif 'duration' in session:
                                        duration = float(session['duration'])
                                        duration_source = "duration"
                                    elif 'conversation_data' in session and session['conversation_data']:
                                        conv_data = session['conversation_data']
                                        if isinstance(conv_data, dict) and 'duration' in conv_data:
                                            duration = float(conv_data['duration'])
                                            duration_source = "conversation_data.duration"
                                    
                                    # Calculate from messages if no duration
                                    if duration == 0 and 'messages' in session and len(session['messages']) >= 2:
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
                                                
                                                duration = (last_dt - first_dt).total_seconds() / 60.0
                                                duration_source = "calculated_from_messages"
                                        except Exception as e:
                                            pass
                                    
                                    if duration > 0:
                                        total_minutes += duration
                                        total_sessions += 1
                                        
                                        # Count by language
                                        if 'dutch' in language.lower() or 'dutch' in plan_name.lower():
                                            dutch_sessions += 1
                                        elif 'english' in language.lower() or 'english' in plan_name.lower():
                                            english_sessions += 1
                                        
                                        completed_at = session.get('completed_at')
                                        print(f"            ✅ Session {j+1}: {duration:.2f} min on {completed_at}")
                                        print(f"               Source: {duration_source}")
                                        print(f"               Language: {language}")
                        
                        # Check for direct duration fields
                        duration_fields = ['duration', 'conversation_duration', 'speaking_duration', 'practice_minutes_used']
                        for field in duration_fields:
                            if field in doc and isinstance(doc[field], (int, float)) and doc[field] > 0:
                                value = float(doc[field])
                                print(f"         💬 {field}: {value} minutes")
                                if field != 'practice_minutes_used':  # Avoid double counting
                                    total_minutes += value
                                    total_sessions += 1
                        
                        # Show document metadata
                        meta_fields = ['created_at', 'completed_at', 'name', 'language', 'level']
                        for field in meta_fields:
                            if field in doc and doc[field]:
                                print(f"         📅 {field}: {doc[field]}")
                    
                    break  # Found docs with this query, no need to try others
                    
            except Exception as e:
                continue
        
        if not found_any:
            print(f"   ❌ No documents found")
    
    print("\n" + "=" * 70)
    print("🎯 FINAL RESULTS FROM TACO DB:")
    print("=" * 70)
    print(f"🎯 TOTAL CONVERSATION MINUTES: {total_minutes:.2f}")
    print(f"📊 TOTAL CONVERSATION SESSIONS: {total_sessions}")
    print(f"🇳🇱 Dutch sessions: {dutch_sessions}")
    print(f"🇬🇧 English sessions: {english_sessions}")
    print()
    
    # Compare with expected
    expected_sessions = 11  # 10 Dutch + 1 English B2
    print("🔍 COMPARISON WITH SCREENSHOT:")
    print(f"   Expected sessions: {expected_sessions} (10 Dutch + 1 English B2)")
    print(f"   Found sessions: {total_sessions}")
    print(f"   Found Dutch: {dutch_sessions} (expected: 10)")
    print(f"   Found English: {english_sessions} (expected: 1)")
    
    if total_sessions == expected_sessions:
        print("   ✅ SESSION COUNT MATCHES!")
    else:
        print("   ❌ SESSION COUNT MISMATCH!")
        print(f"   Missing sessions: {expected_sessions - total_sessions}")
    
    # Show user record for comparison
    user = await db.users.find_one({"_id": user_object_id})
    if user:
        recorded_minutes = user.get('practice_minutes_used', 0.0)
        recorded_sessions = user.get('practice_sessions_used', 0)
        print(f"\n📋 USER RECORD:")
        print(f"   Recorded minutes: {recorded_minutes}")
        print(f"   Recorded sessions: {recorded_sessions}")
        print(f"   Actual found minutes: {total_minutes:.2f}")
        print(f"   Actual found sessions: {total_sessions}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(find_all_sessions_taco_db())
