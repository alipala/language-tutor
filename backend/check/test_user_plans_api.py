import requests
import json

def test_user_plans_api():
    """Test the API endpoint that fetches user learning plans"""
    
    # API endpoint
    api_url = "https://taco.up.railway.app/learning/plans"
    
    # You would need the user's JWT token to test this
    # For now, let's just check if we can reach the endpoint
    print("Testing user learning plans API...")
    print(f"API URL: {api_url}")
    
    # This would require authentication, so we can't test it directly
    # But we can check the backend logic
    
    print("\n🔍 Based on the database investigation:")
    print("✅ User has 2 learning plans:")
    print("   1. English (12 months, B1 level, 1 session completed)")
    print("   2. Dutch (3 months, 0 sessions completed)")
    
    print("\n🐛 Potential issues:")
    print("   1. Frontend API call might be failing")
    print("   2. Authentication token might be invalid")
    print("   3. Backend might be returning plans in wrong order")
    print("   4. Frontend might be filtering out one of the plans")
    
    print("\n💡 Next steps:")
    print("   1. Check browser network tab when loading dashboard")
    print("   2. Check if both plans are returned in API response")
    print("   3. Check if frontend is properly displaying both plans")

if __name__ == "__main__":
    test_user_plans_api()
