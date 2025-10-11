"""
Cleanup script to remove test activation code and email from database
"""

import asyncio
from database import database

async def cleanup_test_data():
    """Remove test activation code for email: 19890b09-cad0-4924-9ba4-1d79df2ad219@mailslurp.biz"""
    
    test_email = "19890b09-cad0-4924-9ba4-1d79df2ad219@mailslurp.biz"
    
    try:
        collection = database.activation_codes
        
        # Find all codes for this email
        codes = await collection.find({"institution_email": test_email}).to_list(length=100)
        
        if not codes:
            print(f"✅ No activation codes found for {test_email}")
            return
        
        print(f"Found {len(codes)} activation code(s) for {test_email}:")
        for code in codes:
            print(f"  - {code.get('activation_code')} (Status: {code.get('status')})")
        
        # Delete all codes for this email
        result = await collection.delete_many({"institution_email": test_email})
        
        print(f"\n✅ Deleted {result.deleted_count} activation code(s) for {test_email}")
        
    except Exception as e:
        print(f"❌ Error cleaning up test data: {str(e)}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("Cleaning up test activation code data")
    print("=" * 60)
    asyncio.run(cleanup_test_data())
    print("\n✅ Cleanup complete!")
