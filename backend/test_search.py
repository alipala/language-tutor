#!/usr/bin/env python3
"""
Test script to verify admin search functionality
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from admin_routes import get_users_admin
from database import users_collection
from datetime import datetime

async def test_search():
    """Test the search functionality"""
    print("Testing admin search functionality...")
    
    # Test 1: Basic search without filters
    print("\n1. Testing basic user fetch (no filters):")
    try:
        # Mock admin user
        class MockAdmin:
            id = "test"
            email = "test@test.com"
            name = "Test Admin"
            role = "admin"
            permissions = ["read:users"]
        
        # Test basic fetch
        result = await get_users_admin(
            page=1,
            per_page=5,
            sort_field="created_at",
            sort_order="desc",
            q=None,
            is_active=None,
            is_verified=None,
            preferred_language=None,
            current_admin=MockAdmin()
        )
        
        print(f"✅ Basic fetch successful: {len(result.data)} users found, total: {result.total}")
        
        # Test 2: Search with query
        print("\n2. Testing search with query:")
        if result.data:
            # Use the first user's name for search
            first_user = result.data[0]
            search_term = first_user['name'][:3] if first_user.get('name') else 'test'
            
            search_result = await get_users_admin(
                page=1,
                per_page=5,
                sort_field="created_at",
                sort_order="desc",
                q=search_term,
                is_active=None,
                is_verified=None,
                preferred_language=None,
                current_admin=MockAdmin()
            )
            
            print(f"✅ Search for '{search_term}' successful: {len(search_result.data)} users found")
            
        # Test 3: Filter by active status
        print("\n3. Testing filter by active status:")
        active_result = await get_users_admin(
            page=1,
            per_page=5,
            sort_field="created_at",
            sort_order="desc",
            q=None,
            is_active=True,
            is_verified=None,
            preferred_language=None,
            current_admin=MockAdmin()
        )
        
        print(f"✅ Active users filter successful: {len(active_result.data)} users found")
        
        print("\n🎉 All search tests passed!")
        
    except Exception as e:
        print(f"❌ Search test failed: {str(e)}")
        import traceback
        traceback.print_exc()

async def check_database_connection():
    """Check if we can connect to the database"""
    try:
        count = await users_collection.count_documents({})
        print(f"✅ Database connection successful. Total users: {count}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

async def main():
    """Main test function"""
    print("🔍 Admin Search Functionality Test")
    print("=" * 40)
    
    # Check database connection first
    if not await check_database_connection():
        print("Cannot proceed without database connection.")
        return
    
    # Run search tests
    await test_search()

if __name__ == "__main__":
    asyncio.run(main())
