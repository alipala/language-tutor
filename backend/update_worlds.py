import asyncio
from datetime import datetime, timedelta
from database import database

async def update_existing_worlds():
    try:
        print("🔄 Updating existing worlds...")
        
        # Update first 4 worlds to be featured and have recent activity
        worlds = await database.story_worlds.find({}).limit(5).to_list(5)
        
        for i, world in enumerate(worlds):
            update_data = {}
            
            # Mark first 4 as featured
            if i < 4:
                update_data['featured'] = True
                # Add recent activity for trending (first 2 worlds)
                if i < 2:
                    update_data['last_contribution_at'] = datetime.utcnow() - timedelta(hours=2)
            else:
                update_data['featured'] = False
            
            # Update the world
            result = await database.story_worlds.update_one(
                {'_id': world['_id']},
                {'$set': update_data}
            )
            
            print(f"Updated '{world['title']}' - Featured: {update_data.get('featured', False)} - Modified: {result.modified_count}")
        
        print('✅ Successfully updated existing worlds')
        
    except Exception as e:
        print(f'❌ Error updating worlds: {e}')

if __name__ == "__main__":
    asyncio.run(update_existing_worlds())
