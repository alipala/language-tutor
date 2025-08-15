import pymongo
from bson import ObjectId

# Direct MongoDB connection using production credentials
client = pymongo.MongoClient('mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin')
db = client['language_tutor']

print('✅ Connected to Production MongoDB')

# The specific user we need to fix
target_user_id = "689e243a0b308d5557da1656"
target_email = "6c9cc30e-ba82-4012-a02a-7f18dff3c526@mailslurp.biz"

# Check the user exists
users = db.users
user = users.find_one({'_id': target_user_id})

if not user:
    print(f'❌ User not found with _id: {target_user_id}')
    exit(1)

print(f'✅ Found user: {user["name"]} ({user["email"]})')

# Check stories collection
stories = db.story_worlds

# First, let's see what's actually in the database
print('\n🔍 Checking current stories in database...')
total_stories = stories.count_documents({})
print(f'Total stories in database: {total_stories}')

# Check sample stories to see creator_id format
sample_stories = list(stories.find({}).limit(5))
print('\n📚 Sample stories:')
for i, story in enumerate(sample_stories, 1):
    creator_id = story.get('creator_id', 'NO_CREATOR_ID')
    print(f'{i}. "{story.get("title", "Untitled")}"')
    print(f'   creator_id: "{creator_id}" (type: {type(creator_id)})')
    print(f'   Match with target user: {creator_id == target_user_id}')
    print()

# Count stories by this user in different formats
count_string = stories.count_documents({'creator_id': target_user_id})
print(f'Stories with string creator_id matching user: {count_string}')

try:
    count_objectid = stories.count_documents({'creator_id': ObjectId(target_user_id)})
    print(f'Stories with ObjectId creator_id matching user: {count_objectid}')
except Exception as e:
    print(f'ObjectId query failed: {e}')

# If no stories found, let's create a test story for this user
if count_string == 0 and count_objectid == 0:
    print('\n🔧 No stories found for this user. Creating a test story...')
    
    from datetime import datetime
    import uuid
    
    test_story = {
        'id': str(uuid.uuid4()),
        'title': 'Test Story for My Stories Filter - PRODUCTION',
        'description': 'This story was created to test the My Stories filter in production.',
        'language': 'en',
        'target_level': 'B1',
        'genre': 'adventure',
        'privacy_setting': 'public',
        'status': 'active',
        'creator_id': target_user_id,  # Use string format
        'contributors': [target_user_id],
        'tags': ['test', 'production', 'my-stories'],
        'featured': False,
        'trending': False,
        'world_state': {
            'current_plot_point': 'Testing the My Stories filter in production environment.',
            'active_characters': [
                {
                    'name': 'Production Tester',
                    'role': 'QA Engineer',
                    'description': 'A character created to test production functionality.'
                }
            ],
            'locations': [
                {
                    'name': 'Production Environment',
                    'description': 'The live system where real users interact.'
                }
            ],
            'important_items': [
                {
                    'name': 'My Stories Filter',
                    'significance': 'Critical for user experience and story management.'
                }
            ]
        },
        'learning_objectives': {
            'primary_focus': 'vocabulary',
            'target_structures': ['present tense', 'questions'],
            'vocabulary_themes': ['testing', 'production', 'quality-assurance']
        },
        'collaboration_settings': {
            'max_contributors': 5,
            'session_duration_minutes': 15,
            'requires_approval': False
        },
        'statistics': {
            'total_sessions': 0,
            'total_contributors': 1,
            'average_session_rating': 0.0
        },
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    # Insert the test story
    result = stories.insert_one(test_story)
    
    if result.inserted_id:
        print(f'✅ Test story created successfully!')
        print(f'Story ID: {test_story["id"]}')
        print(f'Title: {test_story["title"]}')
        print(f'Creator ID: {test_story["creator_id"]} (type: {type(test_story["creator_id"])})')
        
        # Verify it was created
        verification = stories.find_one({'_id': result.inserted_id})
        if verification:
            print(f'✅ Verification: Story exists with creator_id: {verification["creator_id"]}')
        else:
            print('❌ Verification failed: Story not found after creation')
    else:
        print('❌ Failed to create test story')

else:
    print(f'\n✅ Found {count_string + count_objectid} stories for this user')
    
    # Show the user's stories
    user_stories = list(stories.find({
        '$or': [
            {'creator_id': target_user_id},
            {'creator_id': ObjectId(target_user_id)}
        ]
    }).limit(3))
    
    print('\n📖 User\'s stories:')
    for story in user_stories:
        print(f'- "{story.get("title", "Untitled")}"')
        print(f'  creator_id: {story.get("creator_id")} (type: {type(story.get("creator_id"))})')

print('\n🎯 Summary:')
print(f'User ID: {target_user_id}')
print(f'User Email: {target_email}')
print(f'Stories with string creator_id: {stories.count_documents({"creator_id": target_user_id})}')
print(f'Stories with ObjectId creator_id: {stories.count_documents({"creator_id": ObjectId(target_user_id)})}')

client.close()
print('\n✅ Done!')
