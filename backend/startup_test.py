#!/usr/bin/env python3
"""
Startup verification script to test backend dependencies and configuration
"""
import sys
import os
import traceback

def test_imports():
    """Test all critical imports"""
    print("🔍 Testing critical imports...")
    
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print(f"✅ Uvicorn: {uvicorn.__version__}")
    except ImportError as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import motor
        print(f"✅ Motor: {motor.version}")
    except ImportError as e:
        print(f"❌ Motor import failed: {e}")
        return False
    
    try:
        import pymongo
        print(f"✅ PyMongo: {pymongo.__version__}")
    except ImportError as e:
        print(f"❌ PyMongo import failed: {e}")
        return False
    
    try:
        import openai
        print(f"✅ OpenAI: {openai.__version__}")
    except ImportError as e:
        print(f"❌ OpenAI import failed: {e}")
        return False
    
    return True

def test_environment():
    """Test environment variables"""
    print("\n🔍 Testing environment variables...")
    
    # Check critical environment variables
    required_vars = []
    optional_vars = ["OPENAI_API_KEY", "MONGODB_URL", "DATABASE_NAME", "PORT"]
    
    for var in required_vars:
        if not os.getenv(var):
            print(f"❌ Missing required environment variable: {var}")
            return False
        else:
            print(f"✅ {var}: configured")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "PASSWORD" in var or "SECRET" in var:
                print(f"✅ {var}: ***")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"⚠️ {var}: not set (using default)")
    
    return True

def test_main_import():
    """Test importing the main application"""
    print("\n🔍 Testing main application import...")
    
    try:
        # Add backend directory to path
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
        from main import app
        print("✅ Main application imported successfully")
        print(f"✅ FastAPI app created: {type(app)}")
        return True
    except Exception as e:
        print(f"❌ Failed to import main application: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

def test_health_endpoint():
    """Test if health endpoint is accessible"""
    print("\n🔍 Testing health endpoint...")
    
    try:
        from main import health_check
        print("✅ Health check function imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import health check: {e}")
        return False

def main():
    """Run all startup tests"""
    print("🚀 Backend Startup Verification")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Environment Tests", test_environment),
        ("Main Application Import", test_main_import),
        ("Health Endpoint Test", test_health_endpoint),
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if not test_func():
                all_passed = False
                print(f"❌ {test_name} FAILED")
            else:
                print(f"✅ {test_name} PASSED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All startup tests PASSED! Backend should start successfully.")
        return 0
    else:
        print("💥 Some startup tests FAILED! Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
