"""
Data exploration script for admin panel development
"""
import asyncio
from database import init_db, database, users_collection, conversation_sessions_collection, learning_plans_collection

async def explore_database():
    """Explore database structure and content for admin panel development"""
    try:
        await init_db()
        print("✅ Database connected successfully")
        
        # List all collections
        collections = await database.list_collection_names()
        print(f"\n📁 Available collections: {collections}")
        
        # Explore users collection
        print("\n" + "="*50)
        print("👥 USERS COLLECTION")
        print("="*50)
        
        user_count = await users_collection.count_documents({})
        print(f"Total users: {user_count}")
        
        # Get a sample user to see structure
        sample_user = await users_collection.find_one()
        if sample_user:
            print(f"User fields: {list(sample_user.keys())}")
            print("Sample user data:")
            for key, value in sample_user.items():
                if key != '_id':
                    print(f"  {key}: {value}")
        
        # Check for users with learning data
        users_with_language = await users_collection.count_documents({"preferred_language": {"$ne": None}})
        users_with_level = await users_collection.count_documents({"preferred_level": {"$ne": None}})
        print(f"Users with preferred language: {users_with_language}")
        print(f"Users with preferred level: {users_with_level}")
        
        # Explore conversation sessions
        print("\n" + "="*50)
        print("💬 CONVERSATION SESSIONS")
        print("="*50)
        
        conv_count = await conversation_sessions_collection.count_documents({})
        print(f"Total conversation sessions: {conv_count}")
        
        if conv_count > 0:
            sample_conv = await conversation_sessions_collection.find_one()
            if sample_conv:
                print(f"Conversation fields: {list(sample_conv.keys())}")
                print("Sample conversation data:")
                for key, value in sample_conv.items():
                    if key not in ['_id', 'conversation_data']:
                        print(f"  {key}: {value}")
                    elif key == 'conversation_data':
                        print(f"  {key}: [Large data - {len(str(value))} chars]")
        
        # Explore learning plans
        print("\n" + "="*50)
        print("📚 LEARNING PLANS")
        print("="*50)
        
        plan_count = await learning_plans_collection.count_documents({})
        print(f"Total learning plans: {plan_count}")
        
        if plan_count > 0:
            sample_plan = await learning_plans_collection.find_one()
            if sample_plan:
                print(f"Learning plan fields: {list(sample_plan.keys())}")
                print("Sample learning plan data:")
                for key, value in sample_plan.items():
                    if key not in ['_id', 'plan_content']:
                        print(f"  {key}: {value}")
                    elif key == 'plan_content':
                        print(f"  {key}: [Large data - {len(str(value))} chars]")
        
        # Check for other collections that might contain user activity data
        print("\n" + "="*50)
        print("🔍 OTHER COLLECTIONS")
        print("="*50)
        
        for collection_name in collections:
            if collection_name not in ['users', 'conversation_sessions', 'learning_plans']:
                collection = database[collection_name]
                count = await collection.count_documents({})
                print(f"{collection_name}: {count} documents")
                
                if count > 0:
                    sample = await collection.find_one()
                    if sample:
                        print(f"  Fields: {list(sample.keys())}")
        
        # Analyze user activity patterns
        print("\n" + "="*50)
        print("📊 USER ACTIVITY ANALYSIS")
        print("="*50)
        
        # Users with recent activity
        recent_users = await users_collection.count_documents({"last_login": {"$ne": None}})
        print(f"Users with login history: {recent_users}")
        
        # Get some sample user IDs to check for related data
        sample_users = await users_collection.find({}, {"_id": 1, "email": 1}).limit(3).to_list(length=3)
        print(f"Sample user IDs for cross-reference:")
        for user in sample_users:
            user_id = str(user["_id"])
            email = user.get("email", "No email")
            
            # Check conversations for this user
            user_convs = await conversation_sessions_collection.count_documents({"user_id": user_id})
            user_plans = await learning_plans_collection.count_documents({"user_id": user_id})
            
            print(f"  {email} ({user_id}): {user_convs} conversations, {user_plans} plans")
        
        print("\n✅ Database exploration complete!")
        
    except Exception as e:
        print(f"❌ Error exploring database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(explore_database())
