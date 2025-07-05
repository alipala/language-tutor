#!/usr/bin/env python3
"""
Test script to verify all Instagram sharing fixes are working correctly
"""

import asyncio
import httpx
import json
import base64
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_TOKEN = "your_test_token_here"  # Replace with actual test token

async def test_image_generation():
    """Test image generation with simplified prompt"""
    print("🧪 Testing image generation...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/share/generate-progress-image",
            headers={
                "Authorization": f"Bearer {TEST_USER_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "share_type": "progress",
                "platform": "instagram",
                "week_number": 1
            },
            timeout=60.0
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Image generated successfully")
            print(f"✅ Image URL: {data.get('image_url', 'N/A')[:100]}...")
            print(f"✅ Base64 available: {bool(data.get('image_base64'))}")
            print(f"✅ Share text: {data.get('share_text', 'N/A')[:100]}...")
            return data
        else:
            print(f"❌ Failed: {response.text}")
            return None

async def test_url_shortening():
    """Test URL shortening functionality"""
    print("\n🧪 Testing URL shortening...")
    
    test_url = "https://oaidalleapiprodscus.blob.core.windows.net/private/org-6vZH6u1IW74cQYD4sjlhJHrB/user-uha0FCGecDAsSQqnb1mmgXJS/img-dAm1t8usevirnwszI48uDJMV.png?st=2025-07-04T19%3A26%3A49Z&se=2025-07-04T21%3A26%3A49Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/share/shorten-url",
            headers={
                "Authorization": f"Bearer {TEST_USER_TOKEN}",
                "Content-Type": "application/json"
            },
            json={"url": test_url},
            timeout=30.0
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            short_url = data.get('short_url')
            print(f"✅ URL shortened successfully")
            print(f"✅ Original: {test_url[:50]}...")
            print(f"✅ Shortened: {short_url}")
            return short_url
        else:
            print(f"❌ Failed: {response.text}")
            return None

async def test_url_redirect(short_url):
    """Test URL redirect functionality"""
    if not short_url:
        print("\n⏭️ Skipping redirect test (no short URL)")
        return
    
    print(f"\n🧪 Testing URL redirect for: {short_url}")
    
    # Extract hash from short URL
    url_hash = short_url.split('/')[-1]
    redirect_url = f"{BASE_URL}/s/{url_hash}"
    
    async with httpx.AsyncClient(follow_redirects=False) as client:
        response = await client.get(redirect_url, timeout=30.0)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 302:
            location = response.headers.get('location')
            print(f"✅ Redirect working correctly")
            print(f"✅ Redirects to: {location[:50]}...")
        else:
            print(f"❌ Expected 302 redirect, got {response.status_code}")
            print(f"Response: {response.text}")

async def test_user_weeks():
    """Test user weeks endpoint"""
    print("\n🧪 Testing user weeks endpoint...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/share/user-weeks",
            headers={"Authorization": f"Bearer {TEST_USER_TOKEN}"},
            timeout=30.0
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            weeks = data.get('completed_weeks', [])
            print(f"✅ User weeks retrieved successfully")
            print(f"✅ Completed weeks: {len(weeks)}")
            print(f"✅ Total weeks: {data.get('total_weeks', 0)}")
            for week in weeks[:3]:  # Show first 3 weeks
                print(f"   Week {week['week_number']}: {week['sessions_completed']}/{week['total_sessions']} sessions")
        else:
            print(f"❌ Failed: {response.text}")

async def test_image_download_fix():
    """Test that image download works with the URL encoding fix"""
    print("\n🧪 Testing image download fix...")
    
    # Generate an image first
    share_data = await test_image_generation()
    if not share_data:
        print("⏭️ Skipping download test (no image generated)")
        return
    
    image_url = share_data.get('image_url')
    if not image_url:
        print("⏭️ Skipping download test (no image URL)")
        return
    
    print(f"Testing download from: {image_url[:50]}...")
    
    # Test direct download (this should work with our fix)
    async with httpx.AsyncClient() as client:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/png,image/jpeg,image/*;q=0.9,*/*;q=0.8',
        }
        
        try:
            response = await client.get(image_url, headers=headers, timeout=30.0)
            print(f"Direct download status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Direct download successful ({len(response.content)} bytes)")
            else:
                print(f"❌ Direct download failed: {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")
        except Exception as e:
            print(f"❌ Direct download error: {str(e)}")

def print_summary():
    """Print test summary and fixes implemented"""
    print("\n" + "="*80)
    print("🎯 INSTAGRAM SHARING FIXES SUMMARY")
    print("="*80)
    print("✅ FIXED: Image download 403 error (URL double-encoding)")
    print("✅ FIXED: Simplified DALL-E prompt (removed taco symbols)")
    print("✅ FIXED: URL shortening with redirect functionality")
    print("✅ FIXED: Removed 'Share with System' button")
    print("✅ FIXED: Removed 'Download Image' button")
    print("✅ FIXED: Added download to 'Share with Instagram' button")
    print("✅ FIXED: Removed percentage display (floating numbers)")
    print("✅ FIXED: Moved buttons from Image Preview to Share Text section")
    print("✅ ADDED: URL redirect handler for shortened URLs")
    print("="*80)
    print("🚀 All fixes implemented and ready for testing!")
    print("="*80)

async def main():
    """Run all tests"""
    print("🧪 TESTING INSTAGRAM SHARING FIXES")
    print("="*50)
    
    # Note: These tests require a valid user token
    if TEST_USER_TOKEN == "your_test_token_here":
        print("⚠️  Please set a valid TEST_USER_TOKEN in the script")
        print("   You can get a token by logging in and checking localStorage")
        print("\n🔧 Testing what we can without authentication...")
        
        # Test URL shortening endpoint (might work without auth for testing)
        print("\n🧪 Testing URL shortening (no auth)...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{BASE_URL}/api/share/shorten-url",
                    json={"url": "https://example.com/test"},
                    timeout=30.0
                )
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")
            except Exception as e:
                print(f"Error: {str(e)}")
        
        print_summary()
        return
    
    try:
        # Test image generation and download fix
        await test_image_download_fix()
        
        # Test URL shortening
        short_url = await test_url_shortening()
        
        # Test URL redirect
        await test_url_redirect(short_url)
        
        # Test user weeks
        await test_user_weeks()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
    
    print_summary()

if __name__ == "__main__":
    asyncio.run(main())
