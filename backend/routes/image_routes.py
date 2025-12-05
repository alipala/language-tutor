"""
Image URL shortener routes
Handles downloading, caching, and serving shortened OpenAI image URLs
"""

import os
import hashlib
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import requests

router = APIRouter()

# Create images directory for URL shortener
os.makedirs("static/images", exist_ok=True)


@router.post("/api/shorten-image")
async def shorten_openai_image(request: dict):
    """Download OpenAI image and return short URL"""
    try:
        openai_url = request.get('url')
        if not openai_url:
            raise HTTPException(status_code=400, detail="URL is required")

        # For testing, allow any image URL, but prioritize OpenAI URLs
        if 'oaidalleapiprodscus.blob.core.windows.net' not in openai_url:
            print(f"[IMAGE_SHORTENER] ⚠️ Non-OpenAI URL detected: {openai_url}")

        # Generate unique ID from URL
        url_hash = hashlib.md5(openai_url.encode()).hexdigest()
        image_id = url_hash[:12]  # Use first 12 characters
        image_path = f"static/images/{image_id}.png"

        print(f"[IMAGE_SHORTENER] Processing URL: {openai_url}")
        print(f"[IMAGE_SHORTENER] Generated image_id: {image_id}")
        print(f"[IMAGE_SHORTENER] Image path: {image_path}")

        # Check if image already exists
        if not os.path.exists(image_path):
            print(f"[IMAGE_SHORTENER] Image not cached, downloading...")

            # Download image from OpenAI using requests (same as share_routes.py)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/png,image/jpeg,image/*;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            response = requests.get(openai_url, headers=headers, timeout=30, allow_redirects=True)
            print(f"[IMAGE_SHORTENER] Download response status: {response.status_code}")

            if response.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(response.content)
                print(f"[IMAGE_SHORTENER] ✅ Image saved successfully: {len(response.content)} bytes")
            else:
                print(f"[IMAGE_SHORTENER] ❌ Failed to download image: HTTP {response.status_code}")
                raise HTTPException(status_code=400, detail="Failed to download image")
        else:
            print(f"[IMAGE_SHORTENER] ✅ Image already cached")

        # Return short URL
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        short_url = f"{base_url}/api/img/{image_id}"

        print(f"[IMAGE_SHORTENER] ✅ Short URL created: {short_url}")

        return {
            "short_url": short_url,
            "image_id": image_id,
            "original_url": openai_url
        }

    except Exception as e:
        print(f"[IMAGE_SHORTENER] ❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error shortening image URL: {str(e)}")


@router.get("/api/img/{image_id}")
async def serve_image(image_id: str):
    """Serve shortened image"""
    try:
        # Validate image_id (alphanumeric only)
        if not image_id.isalnum() or len(image_id) != 12:
            raise HTTPException(status_code=400, detail="Invalid image ID")

        image_path = f"static/images/{image_id}.png"

        print(f"[IMAGE_SHORTENER] Serving image: {image_id}")
        print(f"[IMAGE_SHORTENER] Image path: {image_path}")
        print(f"[IMAGE_SHORTENER] File exists: {os.path.exists(image_path)}")

        if os.path.exists(image_path):
            return FileResponse(
                image_path,
                media_type="image/png",
                headers={"Cache-Control": "public, max-age=86400"}  # Cache for 24 hours
            )
        else:
            print(f"[IMAGE_SHORTENER] ❌ Image not found: {image_path}")
            raise HTTPException(status_code=404, detail="Image not found")

    except HTTPException:
        raise
    except Exception as e:
        print(f"[IMAGE_SHORTENER] ❌ Error serving image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


@router.post("/api/cleanup-images")
async def cleanup_old_images():
    """Remove images older than 24 hours"""
    try:
        if not os.path.exists("static/images"):
            return {"message": "No images directory"}

        now = datetime.now()
        deleted_count = 0

        for filename in os.listdir("static/images"):
            file_path = os.path.join("static/images", filename)
            if os.path.isfile(file_path):
                # Check file age
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if (now - file_time).days > 1:  # Older than 1 day
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"[IMAGE_SHORTENER] Deleted old image: {filename}")

        print(f"[IMAGE_SHORTENER] Cleanup completed: {deleted_count} files deleted")
        return {"message": f"Deleted {deleted_count} old images"}

    except Exception as e:
        print(f"[IMAGE_SHORTENER] ❌ Cleanup error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")
