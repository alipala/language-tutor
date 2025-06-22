import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def test_search():
    # Connect to MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.language_tutor
    users_collection = db.users
    
    print("Testing direct MongoDB search...")
    
    # Test 1: Get all users
    all_users = await users_collection.find({}).to_list(length=None)
    print(f"Total users in database: {len(all_users)}")
    
    # Print first few user names for reference
    for i, user in enumerate(all_users[:5]):
        print(f"User {i+1}: {user.get('name', 'No name')} - {user.get('email', 'No email')}")
    
    # Test 2: Search for "ali"
    search_term = "ali"
    search_query = {
        "$or": [
            {"name": {"$regex": search_term, "$options": "i"}},
            {"email": {"$regex": search_term, "$options": "i"}}
        ]
    }
    
    print(f"\nTesting search for '{search_term}'...")
    print(f"Search query: {search_query}")
    
    search_results = await users_collection.find(search_query).to_list(length=None)
    print(f"Found {len(search_results)} users matching '{search_term}':")
    
    for user in search_results:
        print(f"  - {user.get('name', 'No name')} ({user.get('email', 'No email')})")
    
    # Test 3: Count documents with search
    count = await users_collection.count_documents(search_query)
    print(f"\nCount documents result: {count}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_search())
