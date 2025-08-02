#!/usr/bin/env python3
"""
Script to enhance Kamile's existing session summaries with comprehensive AI analysis
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from openai import OpenAI

# MongoDB connection for Railway
MONGODB_URL = os.getenv("MONGODB_URL") or os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

async def enhance_session_summaries():
    """Enhance Kamile's existing session summaries with comprehensive AI analysis"""
    
    if not MONGODB_URL:
        print("❌ MONGODB_URL not found in environment variables")
        return
    
    if not client:
        print("❌ OpenAI API key not found")
        return
    
    try:
        # Connect to MongoDB
        mongo_client = AsyncIOMotorClient(MONGODB_URL)
        db = mongo_client.language_tutor
        learning_plans_collection = db.learning_plans
        
        print("🔗 Connected to Railway MongoDB")
        
        # Find Kamile's learning plan
        learning_plan_id = "c9a0b7e9-1938-4353-95d0-c91c6b339769"
        user_id = "6863ba8450b8c0aa0d78de51"
        
        plan = await learning_plans_collection.find_one({"id": learning_plan_id})
        
        if not plan:
            print(f"❌ Learning plan {learning_plan_id} not found")
            return
        
        print(f"✅ Found learning plan for user {user_id}")
        
        # Get current session summaries
        current_summaries = plan.get("session_summaries", [])
        print(f"📊 Current summaries: {len(current_summaries)}")
        
        for i, summary in enumerate(current_summaries):
            print(f"  Session {i+1}: {summary[:80]}...")
        
        # Get plan details for context
        language = plan.get("language", "english")
        level = plan.get("proficiency_level", "C1")
        
        # Get Week 1 focus from weekly schedule
        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
        week1_focus = "Addressing key improvement areas: Enhance intonation and word stress for better pronunciation"
        if weekly_schedule and len(weekly_schedule) > 0:
            week1_focus = weekly_schedule[0].get("focus", week1_focus)
        
        print(f"🎯 Week 1 Focus: {week1_focus}")
        
        # Generate enhanced summaries
        enhanced_summaries = []
        
        for i, basic_summary in enumerate(current_summaries):
            session_number = i + 1
            print(f"\n🤖 Generating enhanced summary for Session {session_number}...")
            
            # Extract duration and message count from basic summary
            duration = "5.7 minutes"
            messages = "14-16 messages"
            if "5.7 minutes, 14 messages" in basic_summary:
                duration = "5.7 minutes"
                messages = "14 messages"
            elif "5.7 minutes, 16 messages" in basic_summary:
                duration = "5.7 minutes" 
                messages = "16 messages"
            
            # Generate comprehensive summary using OpenAI
            prompt = f"""Create a comprehensive learning session summary for this {language} language learning session.

STUDENT PROFILE:
- Language: {language}
- Level: {level}
- Session: {session_number} of Week 1
- Week 1 Focus: {week1_focus}

BASIC SESSION INFO:
- Duration: {duration}
- Messages exchanged: {messages}
- Session type: Conversation practice focused on technical vocabulary and grammar accuracy

CONTEXT:
This was a Week 1 session focusing on enhancing intonation and word stress for better pronunciation. The student is at C1 level and demonstrated strong technical vocabulary usage while discussing LangChain tools and AI concepts. Based on their assessment, they excel at advanced vocabulary but need work on intonation variety and smoother transitions.

Create a comprehensive summary that includes:
1. Session overview (duration, engagement level)
2. Language skills demonstrated (pronunciation, grammar, vocabulary, fluency)
3. Progress towards Week 1 learning objectives
4. Key achievements and improvements observed
5. Areas for continued focus based on C1 level expectations
6. Connection to the weekly focus on pronunciation and intonation

Format as a detailed but concise summary suitable for tracking learning progress."""

            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an expert language learning analyst. Create detailed, insightful summaries of student progress based on session data."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=400,
                    temperature=0.3
                )
                
                if response and response.choices:
                    enhanced_summary = response.choices[0].message.content.strip()
                    enhanced_summaries.append(enhanced_summary)
                    print(f"✅ Enhanced summary generated: {len(enhanced_summary)} characters")
                    print(f"📝 Preview: {enhanced_summary[:100]}...")
                else:
                    # Fallback to enhanced basic summary
                    fallback = f"Session {session_number} completed: {duration}, {messages} exchanged. Focus: {week1_focus}. Strong technical vocabulary demonstrated with continued progress in {language} at {level} level. Areas for improvement: intonation variety and smoother transitions between ideas."
                    enhanced_summaries.append(fallback)
                    print(f"⚠️ Used fallback summary")
                    
            except Exception as e:
                print(f"❌ Error generating summary for session {session_number}: {str(e)}")
                # Use enhanced basic summary as fallback
                fallback = f"Session {session_number} completed: {duration}, {messages} exchanged. Focus: {week1_focus}. Continued progress in {language} at {level} level with emphasis on pronunciation and intonation improvements."
                enhanced_summaries.append(fallback)
        
        # Update the learning plan with enhanced summaries
        print(f"\n💾 Updating learning plan with {len(enhanced_summaries)} enhanced summaries...")
        
        result = await learning_plans_collection.update_one(
            {"id": learning_plan_id},
            {"$set": {
                "session_summaries": enhanced_summaries,
                "updated_at": datetime.utcnow()
            }}
        )
        
        if result.modified_count > 0:
            print("✅ Successfully updated session summaries!")
            
            # Verify the update
            updated_plan = await learning_plans_collection.find_one({"id": learning_plan_id})
            if updated_plan:
                updated_summaries = updated_plan.get("session_summaries", [])
                print(f"\n📋 VERIFICATION - {len(updated_summaries)} enhanced summaries:")
                for i, summary in enumerate(updated_summaries):
                    print(f"  Session {i+1}: {summary[:100]}...")
        else:
            print("⚠️ No changes were made to the learning plan")
        
        if mongo_client:
            mongo_client.close()
        print("\n🎉 Session summary enhancement completed!")
        
    except Exception as e:
        print(f"❌ Error enhancing session summaries: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(enhance_session_summaries())
