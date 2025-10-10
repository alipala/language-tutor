"""
Script to create MongoDB indexes for activation_codes collection
Run this script once to set up the required indexes
"""

import asyncio
import os
from dotenv import load_dotenv
from database import init_db, database

# Load environment variables
load_dotenv()

async def create_indexes():
    """Create indexes for activation_codes collection"""
    try:
        # Initialize database connection
        await init_db()
        print("✅ Connected to MongoDB")
        
        # Get the activation_codes collection
        collection = database.activation_codes
        
        print("\n📊 Creating indexes for activation_codes collection...")
        
        # 1. Unique index on activation_code
        await collection.create_index("activation_code", unique=True)
        print("✅ Created unique index on 'activation_code'")
        
        # 2. Index on status for filtering
        await collection.create_index("status")
        print("✅ Created index on 'status'")
        
        # 3. Index on institution_name for searching
        await collection.create_index("institution_name")
        print("✅ Created index on 'institution_name'")
        
        # 4. Index on code_expires_at for expiration checks
        await collection.create_index("code_expires_at")
        print("✅ Created index on 'code_expires_at'")
        
        # 5. Index on is_trial for filtering
        await collection.create_index("is_trial")
        print("✅ Created index on 'is_trial'")
        
        # 6. Index on generated_at for sorting
        await collection.create_index("generated_at")
        print("✅ Created index on 'generated_at'")
        
        # 7. Index on institution_id for lookups
        await collection.create_index("institution_id")
        print("✅ Created index on 'institution_id'")
        
        # 8. Compound index for common queries
        await collection.create_index([("status", 1), ("is_trial", 1)])
        print("✅ Created compound index on 'status' and 'is_trial'")
        
        # List all indexes
        print("\n📋 All indexes on activation_codes collection:")
        indexes = await collection.list_indexes().to_list(length=None)
        for idx in indexes:
            print(f"  - {idx['name']}: {idx.get('key', {})}")
        
        print("\n✅ All indexes created successfully!")
        
    except Exception as e:
        print(f"\n❌ Error creating indexes: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(create_indexes())
