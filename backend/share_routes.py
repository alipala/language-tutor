import os
import json
import base64
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from openai import OpenAI

from auth import get_current_user
from models import UserResponse
from database import database

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables")

try:
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized successfully in share_routes")
except TypeError as e:
    if "proxies" in str(e):
        print("Detected 'proxies' error in OpenAI initialization. Using alternative initialization...")
        client = OpenAI(api_key=api_key, http_client=httpx.Client())
        print("OpenAI client initialized with alternative method in share_routes")
    else:
        print(f"Error initializing OpenAI client in share_routes: {str(e)}")
        raise

router = APIRouter(prefix="/api/share", tags=["share"])

class ShareProgressRequest(BaseModel):
    assessment_id: Optional[str] = None
    learning_plan_id: Optional[str] = None
    share_type: str = "progress"  # "progress", "achievement", "milestone"
    platform: str = "instagram"  # "instagram", "whatsapp", "general"
    week_number: Optional[int] = None
    custom_message: Optional[str] = None

class ShareProgressResponse(BaseModel):
    success: bool
    image_url: str
    image_base64: Optional[str] = None
    share_text: str
    download_url: Optional[str] = None
    qr_code: Optional[str] = None

@router.post("/generate-progress-image", response_model=ShareProgressResponse)
async def generate_progress_image(
    request: ShareProgressRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate a shareable progress image using OpenAI DALL-E 3
    """
    try:
        print(f"[SHARE] Generating progress image for user {current_user.id}")
        print(f"[SHARE] Request: {request.dict()}")
        
        # Get user's progress data
        progress_data = await get_user_progress_data(current_user.id, request.assessment_id, request.learning_plan_id, request.week_number)
        
        if not progress_data:
            raise HTTPException(
                status_code=404,
                detail="No progress data found for sharing"
            )
        
        # Generate the image prompt
        image_prompt = create_image_prompt(progress_data, request.share_type, request.platform, request.week_number)
        
        print(f"[SHARE] Generated prompt: {image_prompt[:200]}...")
        
        # Generate image using DALL-E 3
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            if not response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate image"
                )
            
            image_url = response.data[0].url
            print(f"[SHARE] ✅ Image generated successfully: {image_url}")
            
        except Exception as openai_error:
            print(f"[SHARE] ❌ OpenAI error: {str(openai_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate image: {str(openai_error)}"
            )
        
        # Download image IMMEDIATELY and convert to base64 (OpenAI URLs expire quickly!)
        image_base64 = None
        try:
            print(f"[SHARE] 🔄 Downloading image immediately from: {image_url}")
            
            # CRITICAL FIX: Use requests instead of httpx to avoid URL encoding issues
            import requests
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/png,image/jpeg,image/*;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            print(f"[SHARE] 🔄 Making request to: {image_url}")
            
            # Use requests which handles URLs properly
            img_response = requests.get(image_url, headers=headers, timeout=30, allow_redirects=True)
            print(f"[SHARE] Download response status: {img_response.status_code}")
            
            if img_response.status_code == 200:
                image_base64 = base64.b64encode(img_response.content).decode('utf-8')
                print(f"[SHARE] ✅ Image converted to base64 ({len(image_base64)} chars)")
            else:
                print(f"[SHARE] ❌ Failed to download image: HTTP {img_response.status_code}")
                print(f"[SHARE] Response headers: {img_response.headers}")
                # Try to get error details
                try:
                    error_text = img_response.text
                    print(f"[SHARE] Error response: {error_text}")
                except:
                    pass
        except Exception as download_error:
            print(f"[SHARE] ❌ Exception downloading image: {str(download_error)}")
            import traceback
            print(f"[SHARE] Traceback: {traceback.format_exc()}")
        
        # Generate share text
        share_text = create_share_text(progress_data, request.platform, request.custom_message, request.week_number)
        
        # Store sharing activity
        await track_sharing_activity(current_user.id, request.share_type, request.platform, progress_data)
        
        return ShareProgressResponse(
            success=True,
            image_url=image_url,
            image_base64=image_base64,
            share_text=share_text,
            download_url=image_url,  # Same as image_url for now
            qr_code=None  # Could implement QR code generation later
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[SHARE] ❌ Error generating progress image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate progress image: {str(e)}"
        )

async def get_user_progress_data(user_id: str, assessment_id: Optional[str], learning_plan_id: Optional[str], week_number: Optional[int] = None) -> Dict[str, Any]:
    """
    Retrieve user's progress data with enhanced assessment information for sharing
    """
    try:
        progress_data = {
            "user_id": user_id,
            "app_name": "MyTacoAI",
            "brand_colors": {
                "turquoise": "#4ECFBF",
                "yellow": "#FFD63A", 
                "coral": "#F75A5A",
                "orange": "#FFA955"
            }
        }
        
        # Get learning plan data if specified (includes plan_content with assessment_summary)
        if learning_plan_id:
            learning_plans_collection = database.learning_plans
            learning_plan = await learning_plans_collection.find_one({"id": learning_plan_id, "user_id": user_id})
            if learning_plan:
                completed_sessions = learning_plan.get("completed_sessions", 0)
                total_sessions = learning_plan.get("total_sessions", 48)
                progress_percentage = learning_plan.get("progress_percentage", 0)
                
                # Calculate weeks completed
                sessions_per_week = 2
                weeks_completed = completed_sessions // sessions_per_week
                total_weeks = learning_plan.get("duration_months", 6) * 4
                
                progress_data["learning_plan"] = {
                    "language": learning_plan.get("language", "English"),
                    "level": learning_plan.get("proficiency_level", "B1"),
                    "completed_sessions": completed_sessions,
                    "total_sessions": total_sessions,
                    "progress_percentage": progress_percentage,
                    "weeks_completed": weeks_completed,
                    "total_weeks": total_weeks,
                    "duration_months": learning_plan.get("duration_months", 6),
                    "goals": learning_plan.get("goals", [])
                }
                
                # Include the rich plan_content data
                plan_content = learning_plan.get("plan_content", {})
                if plan_content:
                    progress_data["plan_content"] = plan_content
        
        # Get assessment data if specified
        if assessment_id:
            assessments_collection = database.assessments
            assessment = await assessments_collection.find_one({"_id": assessment_id, "user_id": user_id})
            if assessment:
                progress_data["assessment"] = {
                    "overall_score": assessment.get("overall_score", 0),
                    "language": assessment.get("language", "English"),
                    "level": assessment.get("recommended_level", "B1"),
                    "confidence": assessment.get("confidence", 0),
                    "strengths": assessment.get("strengths", []),
                    "date": assessment.get("date", datetime.now().isoformat())
                }
        
        # If no specific data requested, get latest
        if not assessment_id and not learning_plan_id:
            # Get latest assessment
            assessments_collection = database.assessments
            latest_assessment = await assessments_collection.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            
            if latest_assessment:
                progress_data["assessment"] = {
                    "overall_score": latest_assessment.get("overall_score", 0),
                    "language": latest_assessment.get("language", "English"),
                    "level": latest_assessment.get("recommended_level", "B1"),
                    "confidence": latest_assessment.get("confidence", 0),
                    "date": latest_assessment.get("date", datetime.now().isoformat())
                }
            
            # Get latest learning plan
            learning_plans_collection = database.learning_plans
            latest_plan = await learning_plans_collection.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            
            if latest_plan:
                completed_sessions = latest_plan.get("completed_sessions", 0)
                total_sessions = latest_plan.get("total_sessions", 48)
                progress_percentage = latest_plan.get("progress_percentage", 0)
                
                progress_data["learning_plan"] = {
                    "language": latest_plan.get("language", "English"),
                    "level": latest_plan.get("proficiency_level", "B1"),
                    "completed_sessions": completed_sessions,
                    "total_sessions": total_sessions,
                    "progress_percentage": progress_percentage,
                    "duration_months": latest_plan.get("duration_months", 6)
                }
                
                # Include plan_content if available
                plan_content = latest_plan.get("plan_content", {})
                if plan_content:
                    progress_data["plan_content"] = plan_content
        
        print(f"[SHARE] Retrieved enhanced progress data: {json.dumps(progress_data, indent=2, default=str)}")
        return progress_data
        
    except Exception as e:
        print(f"[SHARE] ❌ Error retrieving enhanced progress data: {str(e)}")
        return None

def create_image_prompt(progress_data: Dict[str, Any], share_type: str, platform: str, week_number: Optional[int] = None) -> str:
    """
    Create a SIMPLE, clean badge prompt that avoids complexity and gibberish text
    """
    # Brand colors
    turquoise = "#4ECFBF"
    yellow = "#FFD63A"
    
    # Extract basic data
    learning_plan = progress_data.get("learning_plan", {})
    language = learning_plan.get("language", "English").title()
    level = learning_plan.get("level", "B1").upper()
    app_name = progress_data.get("app_name", "MyTacoAI")
    
    prompt = f"""Create a SIMPLE circular achievement badge with minimal text.

EXACT TEXT ONLY:
- Center: "WEEK {week_number} COMPLETE!"
- Top: "{level} {language}"  
- Bottom: "{app_name}"

DESIGN:
- Clean circle, 1024x1024
- Turquoise {turquoise} to yellow {yellow} gradient
- White bold text
- 2-3 small stars for decoration
- NO other text or letters anywhere

Keep it SIMPLE and CLEAN. Focus on the achievement."""

    return prompt

def create_share_text(progress_data: Dict[str, Any], platform: str, custom_message: Optional[str] = None, week_number: Optional[int] = None) -> str:
    """
    Create platform-appropriate share text (no percentages)
    """
    assessment = progress_data.get("assessment", {})
    learning_plan = progress_data.get("learning_plan", {})
    app_name = progress_data.get("app_name", "TacoAI")
    
    # Extract key metrics
    if learning_plan:
        language = learning_plan.get("language", "English")
        level = learning_plan.get("level", "B1")
        sessions = learning_plan.get("completed_sessions", 0)
    elif assessment:
        language = assessment.get("language", "English")
        level = assessment.get("level", "B1")
        sessions = 1
    else:
        language = "English"
        level = "B1"
        sessions = 5
    
    # Add week-specific content
    week_text = f"Week {week_number} completed! 🎉" if week_number else ""
    
    if custom_message:
        base_text = custom_message
    else:
        if platform == "instagram":
            base_text = f"🎓 Learning {language} with {app_name}! \n\n{week_text}\n📚 {level} Level\n💪 {sessions} Sessions Completed\n\n#LanguageLearning #{language}Learning #Progress #MyTacoAI #LanguageGoals #StudyMotivation"
        
        elif platform == "whatsapp":
            base_text = f"🎓 I'm learning {language} with {app_name}! \n\n{week_text}\nCurrently at {level} level 📚\n\nCompleted {sessions} sessions so far 💪\n\nWant to join me? Check out {app_name}! 🚀"
        
        else:  # general
            base_text = f"🎓 Learning {language} with {app_name}!\n\n{week_text}\n🎯 Level: {level}\n💪 Sessions: {sessions}\n\n#LanguageLearning #{language}"
    
    return base_text

async def track_sharing_activity(user_id: str, share_type: str, platform: str, progress_data: Dict[str, Any]):
    """
    Track sharing activity for analytics
    """
    try:
        sharing_collection = database.sharing_activity
        
        activity_doc = {
            "user_id": user_id,
            "share_type": share_type,
            "platform": platform,
            "progress_data": progress_data,
            "created_at": datetime.utcnow(),
            "success": True
        }
        
        await sharing_collection.insert_one(activity_doc)
        print(f"[SHARE] ✅ Tracked sharing activity for user {user_id}")
        
    except Exception as e:
        print(f"[SHARE] ⚠️ Failed to track sharing activity: {str(e)}")
        # Don't raise exception - this is non-critical

class DownloadImageRequest(BaseModel):
    image_url: str

@router.get("/proxy-image/{image_url:path}")
async def proxy_image(image_url: str):
    """
    Proxy route to download images from external URLs (like OpenAI)
    This avoids CORS issues and authentication problems
    """
    try:
        # Decode the URL
        from urllib.parse import unquote
        decoded_url = unquote(image_url)
        
        print(f"[SHARE] Proxying image from: {decoded_url}")
        
        # Create headers that work with OpenAI URLs
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        async with httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True) as http_client:
            # CRITICAL FIX: Use raw string to prevent any URL encoding by httpx
            response = await http_client.get(decoded_url, follow_redirects=True)
            
            print(f"[SHARE] Proxy response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[SHARE] Proxy failed with status: {response.status_code}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to fetch image: HTTP {response.status_code}"
                )
            
            print(f"[SHARE] Successfully proxied {len(response.content)} bytes")
            
            # Return the image with proper headers
            return Response(
                content=response.content,
                media_type="image/png",
                headers={
                    "Content-Disposition": "attachment; filename=tacoai-progress.png",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
            
    except Exception as e:
        print(f"[SHARE] ❌ Error proxying image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to proxy image: {str(e)}"
        )

@router.post("/download-image")
async def download_image(
    request: DownloadImageRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Download image from OpenAI URL to avoid CORS issues
    DEPRECATED: Use proxy-image route instead
    """
    try:
        print(f"[SHARE] Downloading image from: {request.image_url}")
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.get(request.image_url)
            
            print(f"[SHARE] Download response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[SHARE] Download failed with status: {response.status_code}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to download image: HTTP {response.status_code}"
                )
            
            print(f"[SHARE] Successfully downloaded {len(response.content)} bytes")
            
            return Response(
                content=response.content,
                media_type="image/png",
                headers={
                    "Content-Disposition": "attachment; filename=tacoai-progress.png"
                }
            )
            
    except httpx.HTTPError as e:
        print(f"[SHARE] ❌ HTTP Error downloading image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Network error downloading image: {str(e)}"
        )
    except Exception as e:
        print(f"[SHARE] ❌ Error downloading image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download image: {str(e)}"
        )

@router.get("/user-weeks")
async def get_user_weeks(current_user: UserResponse = Depends(get_current_user)):
    """
    Get user's completed weeks for sharing
    """
    try:
        # Get latest learning plan
        learning_plans_collection = database.learning_plans
        latest_plan = await learning_plans_collection.find_one(
            {"user_id": current_user.id},
            sort=[("created_at", -1)]
        )
        
        if not latest_plan:
            return {"completed_weeks": [], "total_weeks": 0}
        
        completed_sessions = latest_plan.get("completed_sessions", 0)
        sessions_per_week = 2
        completed_weeks_count = completed_sessions // sessions_per_week
        total_weeks = latest_plan.get("duration_months", 6) * 4
        
        # Create weeks array
        weeks = []
        for i in range(1, completed_weeks_count + 1):
            weeks.append({
                "week_number": i,
                "sessions_completed": sessions_per_week,
                "total_sessions": sessions_per_week,
                "is_completed": True
            })
        
        return {
            "completed_weeks": weeks,
            "total_weeks": total_weeks,
            "completed_sessions": completed_sessions
        }
        
    except Exception as e:
        print(f"[SHARE] ❌ Error getting user weeks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user weeks: {str(e)}"
        )

@router.post("/shorten-url")
async def shorten_url(
    request: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a shortened URL for sharing (simple implementation)
    """
    try:
        original_url = request.get("url")
        if not original_url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        # Simple URL shortener using a hash of the URL
        import hashlib
        url_hash = hashlib.md5(original_url.encode()).hexdigest()[:8]
        
        # Store in database for tracking
        url_collection = database.shortened_urls
        
        # Check if already exists
        existing = await url_collection.find_one({"hash": url_hash})
        if existing:
            short_url = f"https://mytacoai.com/s/{url_hash}"
            return {"short_url": short_url, "original_url": original_url}
        
        # Create new shortened URL
        url_doc = {
            "hash": url_hash,
            "original_url": original_url,
            "user_id": current_user.id,
            "created_at": datetime.utcnow(),
            "clicks": 0
        }
        
        await url_collection.insert_one(url_doc)
        
        short_url = f"https://mytacoai.com/s/{url_hash}"
        return {"short_url": short_url, "original_url": original_url}
        
    except Exception as e:
        print(f"[SHARE] ❌ Error shortening URL: {str(e)}")
        # Return original URL if shortening fails
        return {"short_url": request.get("url", ""), "original_url": request.get("url", "")}

@router.get("/sharing-stats")
async def get_sharing_stats(current_user: UserResponse = Depends(get_current_user)):
    """
    Get user's sharing statistics
    """
    try:
        sharing_collection = database.sharing_activity
        
        # Get user's sharing history
        shares = await sharing_collection.find({"user_id": current_user.id}).to_list(length=None)
        
        # Calculate stats
        total_shares = len(shares)
        platform_breakdown = {}
        share_type_breakdown = {}
        
        for share in shares:
            platform = share.get("platform", "unknown")
            share_type = share.get("share_type", "unknown")
            
            platform_breakdown[platform] = platform_breakdown.get(platform, 0) + 1
            share_type_breakdown[share_type] = share_type_breakdown.get(share_type, 0) + 1
        
        return {
            "total_shares": total_shares,
            "platform_breakdown": platform_breakdown,
            "share_type_breakdown": share_type_breakdown,
            "recent_shares": shares[-5:] if shares else []  # Last 5 shares
        }
        
    except Exception as e:
        print(f"[SHARE] ❌ Error getting sharing stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sharing stats: {str(e)}"
        )
