#!/usr/bin/env python3
"""
Test script for contextual chatbot with user authentication
"""

import requests
import json
import sys

# Configuration
BASE_URL = "https://taco.up.railway.app"  # Update this to your Railway URL
TEST_EMAIL = "bc0e874a-64c4-4419-8f48-d0c4bae5cc23@mailslurp.biz"
TEST_PASSWORD = "040050803"

def authenticate_user():
    """Authenticate user and get access token"""
    print(f"🔐 Authenticating user: {TEST_EMAIL}")
    
    # Login endpoint
    login_url = f"{BASE_URL}/auth/token"
    
    # Prepare login data (form data for OAuth2)
    login_data = {
        "username": TEST_EMAIL,  # OAuth2 uses 'username' field for email
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(
            login_url,
            data=login_data,  # Use data for form encoding
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"✅ Authentication successful!")
            print(f"Token type: {token_data.get('token_type')}")
            return access_token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during authentication: {str(e)}")
        return None

def test_contextual_chatbot(access_token, query):
    """Test the contextual chatbot with user authentication"""
    print(f"\n🤖 Testing contextual chatbot with query: '{query}'")
    
    # Contextual chatbot endpoint
    chatbot_url = f"{BASE_URL}/api/chat/contextual-knowledge"
    
    # Prepare headers with authentication
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Prepare request data
    request_data = {
        "query": query
    }
    
    try:
        response = requests.post(
            chatbot_url,
            json=request_data,
            headers=headers
        )
        
        print(f"Chatbot response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            print(f"✅ Chatbot response received!")
            print(f"📝 Response: {response_data.get('response', 'No response')}")
            print(f"📚 Sources: {response_data.get('sources', [])}")
            print(f"📊 Similarity scores: {response_data.get('similarity_scores', [])}")
            print(f"👤 User context used: {response_data.get('user_context_used', False)}")
            print(f"💡 Personalized suggestions: {response_data.get('personalized_suggestions', [])}")
            
            return response_data
        else:
            print(f"❌ Chatbot request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during chatbot request: {str(e)}")
        return None

def test_regular_chatbot(query):
    """Test the regular chatbot without authentication"""
    print(f"\n🤖 Testing regular chatbot with query: '{query}'")
    
    # Regular chatbot endpoint
    chatbot_url = f"{BASE_URL}/api/chat/vector-knowledge"
    
    # Prepare request data
    request_data = {
        "query": query
    }
    
    try:
        response = requests.post(
            chatbot_url,
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Regular chatbot response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            print(f"✅ Regular chatbot response received!")
            print(f"📝 Response: {response_data.get('response', 'No response')}")
            print(f"📚 Sources: {response_data.get('sources', [])}")
            print(f"📊 Similarity scores: {response_data.get('similarity_scores', [])}")
            
            return response_data
        else:
            print(f"❌ Regular chatbot request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during regular chatbot request: {str(e)}")
        return None

def main():
    """Main test function"""
    print("🧪 CONTEXTUAL CHATBOT TESTING")
    print("=" * 50)
    
    # Test questions for registered users with learning plans
    test_questions = [
        "How am I doing with my learning plan?",
        "What should I focus on this week?",
        "What should I practice in my next session?",
        "How many sessions have I completed?",
        "What's my current week's objective?"
    ]
    
    # Step 1: Authenticate user
    access_token = authenticate_user()
    
    if not access_token:
        print("❌ Cannot proceed without authentication")
        sys.exit(1)
    
    # Step 2: Test contextual chatbot with each question
    print("\n" + "=" * 50)
    print("🎯 TESTING CONTEXTUAL CHATBOT (WITH USER CONTEXT)")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- TEST {i}/5 ---")
        contextual_response = test_contextual_chatbot(access_token, question)
        
        if contextual_response:
            print(f"✅ Test {i} completed successfully")
        else:
            print(f"❌ Test {i} failed")
    
    # Step 3: Compare with regular chatbot
    print("\n" + "=" * 50)
    print("🔍 TESTING REGULAR CHATBOT (NO USER CONTEXT)")
    print("=" * 50)
    
    # Test one question with regular chatbot for comparison
    comparison_question = test_questions[0]  # "How am I doing with my learning plan?"
    print(f"\n--- COMPARISON TEST ---")
    regular_response = test_regular_chatbot(comparison_question)
    
    if regular_response:
        print(f"✅ Regular chatbot test completed")
    else:
        print(f"❌ Regular chatbot test failed")
    
    print("\n" + "=" * 50)
    print("🏁 TESTING COMPLETED")
    print("=" * 50)
    
    # Summary
    print("\n📋 SUMMARY:")
    print("- Tested contextual chatbot with user authentication")
    print("- Tested 5 learning plan specific questions")
    print("- Compared with regular chatbot response")
    print("- Check responses above to verify user context awareness")

if __name__ == "__main__":
    main()
