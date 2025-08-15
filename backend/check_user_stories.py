import asyncio
from database import init_db, database

async def check_user_stories():
    await init_db()
    
    # Check user first
    users_collection = database.users
    user = await users_collection.find_one({'email': '6c9cc30e-ba82-4012-a02a-7f18dff3c526@mailslurp.biz'})
    
    if not user:
        print('❌ User not found with that email')
        
        # Let's check what users exist
        all_users = await users_collection.find({}).to_list(5)
        print(f'Total users in DB: {await users_collection.count_documents({})}')
        print('Sample users:')
        for u in all_users:
            print(f'- {u.get("email", "No email")} (ID: {str(u["_id"])})')
        return
    
    user_id = str(user['_id'])
    print(f'✅ Found user: {user.get("name", "Unknown")} (ID: {user_id})')
    
    # Check stories
    story_worlds_collection = database.story_worlds
    user_stories = await story_worlds_collection.find({'creator_id': user_id}).to_list(100)
    
    print(f'\n📚 Stories created by this user: {len(user_stories)}')
    
    if user_stories:
        for i, story in enumerate(user_stories, 1):
            print(f'\n{i}. {story.get("title", "Untitled")}')
            print(f'   ID: {story.get("id", "No ID")}')
            print(f'   Language: {story.get("language", "Unknown")}')
            print(f'   Level: {story.get("target_level", "Unknown")}')
            print(f'   Status: {story.get("status", "Unknown")}')
            print(f'   Privacy: {story.get("privacy_setting", "Unknown")}')
    else:
        print('\n📝 No stories found for this user')
        
        # Check total stories in database
        total_stories = await story_worlds_collection.count_documents({})
        print(f'\n🔍 Total stories in database: {total_stories}')
        
        if total_stories > 0:
            # Show sample stories
            sample_stories = await story_worlds_collection.find({}).to_list(3)
            print('\nSample stories in database:')
            for story in sample_stories:
                print(f'- "{story.get("title", "Untitled")}" by creator: {story.get("creator_id", "Unknown")}')

if __name__ == "__main__":
    asyncio.run(check_user_stories())
