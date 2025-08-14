#!/usr/bin/env python3
"""
Script to enable world building feature and initialize the database foundation
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def enable_world_building():
    """Enable world building feature and initialize database"""
    print("🌍 [WORLD_BUILDING] Enabling Collaborative World Building Feature")
    print("=" * 70)
    
    try:
        # Set the feature flag
        os.environ["WORLD_BUILDING_ENABLED"] = "true"
        print("✅ Feature flag WORLD_BUILDING_ENABLED set to true")
        
        # Import required modules
        from utils.feature_flags import feature_flags
        from utils.world_building_helpers import world_building_helpers
        from database import init_db
        
        # Verify feature is enabled
        if feature_flags.is_world_building_enabled():
            print("✅ World building feature is now enabled")
        else:
            print("❌ Failed to enable world building feature")
            return False
        
        # Initialize database
        print("\n🗄️ Initializing database...")
        await init_db()
        
        # Initialize world building system
        print("\n🚀 Initializing world building system...")
        success = await world_building_helpers.initialize_world_building_system()
        
        if success:
            print("\n✅ World building system initialized successfully!")
            
            # Get system stats
            print("\n📊 Getting system statistics...")
            stats = await world_building_helpers.get_world_building_stats()
            
            if "error" not in stats:
                print(f"   Total worlds: {stats['overview']['total_worlds']}")
                print(f"   Active worlds: {stats['overview']['active_worlds']}")
                print(f"   Total contributions: {stats['overview']['total_contributions']}")
                print(f"   Languages available: {len(stats['distributions']['languages'])}")
                
                # Show sample worlds
                if stats['overview']['total_worlds'] > 0:
                    print("\n🌟 Sample worlds created:")
                    for lang_stat in stats['distributions']['languages'][:3]:
                        print(f"   • {lang_stat['language'].upper()}: {lang_stat['count']} worlds")
            
            # Perform health check
            print("\n🏥 Performing health check...")
            health = await world_building_helpers.check_world_building_health()
            print(f"   Overall status: {health['overall_status']}")
            
            if health['warnings']:
                print("   Warnings:")
                for warning in health['warnings']:
                    print(f"     ⚠️ {warning}")
            
            if health['errors']:
                print("   Errors:")
                for error in health['errors']:
                    print(f"     ❌ {error}")
            
            return True
        else:
            print("❌ Failed to initialize world building system")
            return False
            
    except Exception as e:
        print(f"❌ Error enabling world building: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

async def main():
    """Main function"""
    print(f"🚀 Starting World Building Enablement")
    print(f"📅 Started at: {datetime.now()}")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    print()
    
    try:
        success = await enable_world_building()
        
        if success:
            print("\n🎉 World Building feature is now ready!")
            print("\nNext steps:")
            print("1. The feature flag WORLD_BUILDING_ENABLED is now set to true")
            print("2. Database collections and indexes have been created")
            print("3. Sample worlds have been seeded")
            print("4. The system is ready for use")
            print("\nTo use in production, set WORLD_BUILDING_ENABLED=true in your environment variables")
        else:
            print("\n❌ Failed to enable World Building feature")
            print("Please check the errors above and try again")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
