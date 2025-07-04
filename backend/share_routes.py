import os
import json
import base64
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
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
        progress_data = await get_user_progress_data(current_user.id, request.assessment_id, request.learning_plan_id)
        
        if not progress_data:
            raise HTTPException(
                status_code=404,
                detail="No progress data found for sharing"
            )
        
        # Generate the image prompt
        image_prompt = create_image_prompt(progress_data, request.share_type, request.platform)
        
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
        
        # Download image and convert to base64 for frontend
        image_base64 = None
        try:
            async with httpx.AsyncClient() as http_client:
                img_response = await http_client.get(image_url)
                if img_response.status_code == 200:
                    image_base64 = base64.b64encode(img_response.content).decode('utf-8')
                    print(f"[SHARE] ✅ Image converted to base64")
        except Exception as download_error:
            print(f"[SHARE] ⚠️ Failed to download image for base64: {str(download_error)}")
        
        # Generate share text
        share_text = create_share_text(progress_data, request.platform, request.custom_message)
        
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

async def get_user_progress_data(user_id: str, assessment_id: Optional[str], learning_plan_id: Optional[str]) -> Dict[str, Any]:
    """
    Retrieve user's progress data for sharing
    """
    try:
        progress_data = {
            "user_id": user_id,
            "app_name": "TacoAI",
            "app_logo": "🌮",
            "brand_colors": {
                "turquoise": "#4ECFBF",
                "yellow": "#FFD63A", 
                "coral": "#F75A5A",
                "orange": "#FFA955"
            }
        }
        
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
        
        # Get learning plan data if specified
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
        
        # If no specific data requested, get general progress
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
        
        print(f"[SHARE] Retrieved progress data: {json.dumps(progress_data, indent=2, default=str)}")
        return progress_data
        
    except Exception as e:
        print(f"[SHARE] ❌ Error retrieving progress data: {str(e)}")
        return None

def create_image_prompt(progress_data: Dict[str, Any], share_type: str, platform: str) -> str:
    """
    Create a detailed prompt for DALL-E 3 image generation
    """
    # Brand colors
    turquoise = "#4ECFBF"
    yellow = "#FFD63A"
    coral = "#F75A5A"
    orange = "#FFA955"
    
    # Extract data
    assessment = progress_data.get("assessment", {})
    learning_plan = progress_data.get("learning_plan", {})
    app_name = progress_data.get("app_name", "TacoAI")
    
    # Determine main metrics to highlight
    if learning_plan:
        language = learning_plan.get("language", "English")
        level = learning_plan.get("level", "B1")
        progress_percentage = learning_plan.get("progress_percentage", 0)
        completed_sessions = learning_plan.get("completed_sessions", 0)
        weeks_completed = learning_plan.get("weeks_completed", 0)
    elif assessment:
        language = assessment.get("language", "English")
        level = assessment.get("level", "B1")
        progress_percentage = assessment.get("overall_score", 0)
        completed_sessions = 1
        weeks_completed = 1
    else:
        language = "English"
        level = "B1"
        progress_percentage = 50
        completed_sessions = 5
        weeks_completed = 2
    
    # Create platform-specific prompt
    if platform == "instagram":
        base_prompt = f"""Create a vibrant, Instagram-worthy progress sharing image for a language learning app called '{app_name}'. 

DESIGN REQUIREMENTS:
- Square format (1024x1024) perfect for Instagram posts
- Modern, clean, and visually appealing design
- Use these exact brand colors: turquoise {turquoise}, bright yellow {yellow}, coral {coral}, and orange {orange}
- Include a subtle taco emoji 🌮 as the app logo
- Professional yet fun and engaging aesthetic

CONTENT TO INCLUDE:
- Large, bold text: "Learning {language}!"
- Prominent display: "{level} Level"
- Progress indicator: "{progress_percentage}% Complete" or "{completed_sessions} Sessions Completed"
- App branding: "{app_name}" with taco emoji
- Motivational element: "Keep going!" or "Great progress!"

VISUAL STYLE:
- Gradient backgrounds using the brand colors
- Modern typography with good contrast
- Progress bars or circular progress indicators
- Celebratory elements like stars, checkmarks, or achievement badges
- Clean layout with proper spacing
- Instagram-optimized visual hierarchy

MOOD: Celebratory, motivational, professional, and shareable"""

    elif platform == "whatsapp":
        base_prompt = f"""Create a friendly, personal progress sharing image for WhatsApp sharing for a language learning app called '{app_name}'.

DESIGN REQUIREMENTS:
- Square format optimized for WhatsApp sharing
- Warm, friendly, and personal design
- Use these brand colors: turquoise {turquoise}, yellow {yellow}, coral {coral}, orange {orange}
- Include taco emoji 🌮 as app logo
- Conversational and approachable style

CONTENT TO INCLUDE:
- Friendly text: "I'm learning {language} with {app_name}!"
- Progress: "{progress_percentage}% complete" or "{completed_sessions} sessions done"
- Level: "{level} level"
- Call to action: "Join me!"
- App name with taco emoji

VISUAL STYLE:
- Soft gradients and rounded corners
- Friendly, readable fonts
- Personal achievement feel
- WhatsApp-friendly color scheme
- Encouraging and motivational

MOOD: Personal, encouraging, friendly, and inviting"""

    else:  # general
        base_prompt = f"""Create a versatile progress sharing image for a language learning app called '{app_name}'.

DESIGN REQUIREMENTS:
- Square format suitable for multiple social platforms
- Professional yet engaging design
- Brand colors: turquoise {turquoise}, yellow {yellow}, coral {coral}, orange {orange}
- Taco emoji 🌮 as app logo
- Universal appeal

CONTENT TO INCLUDE:
- Main text: "Learning {language} with {app_name}"
- Progress: "{progress_percentage}% Complete"
- Level: "{level} Level"
- Sessions: "{completed_sessions} Sessions"
- App branding with taco emoji

VISUAL STYLE:
- Clean, modern design
- Good contrast and readability
- Professional color usage
- Achievement-focused layout
- Social media optimized

MOOD: Professional, motivational, and achievement-focused"""

    # Add specific elements based on share type
    if share_type == "milestone":
        base_prompt += f"\n\nSPECIAL MILESTONE ELEMENTS:\n- Add celebration elements like confetti, stars, or trophy icons\n- Emphasize the achievement with 'Milestone Reached!' text\n- Make it extra celebratory and exciting"
    
    elif share_type == "achievement":
        base_prompt += f"\n\nACHIEVEMENT ELEMENTS:\n- Include achievement badge or medal icon\n- Add 'Achievement Unlocked!' text\n- Use gold accents or achievement-style design elements"
    
    # Ensure brand consistency
    base_prompt += f"""

CRITICAL BRAND REQUIREMENTS:
- MUST include '{app_name}' text prominently
- MUST include taco emoji 🌮 
- MUST use the specified brand colors
- MUST be visually appealing and shareable
- MUST look professional and trustworthy
- MUST encourage others to try the app

TECHNICAL REQUIREMENTS:
- High quality, crisp design
- Good contrast for text readability
- Optimized for social media sharing
- Eye-catching and scroll-stopping design"""

    return base_prompt

def create_share_text(progress_data: Dict[str, Any], platform: str, custom_message: Optional[str] = None) -> str:
    """
    Create platform-appropriate share text
    """
    assessment = progress_data.get("assessment", {})
    learning_plan = progress_data.get("learning_plan", {})
    app_name = progress_data.get("app_name", "TacoAI")
    
    # Extract key metrics
    if learning_plan:
        language = learning_plan.get("language", "English")
        level = learning_plan.get("level", "B1")
        progress = learning_plan.get("progress_percentage", 0)
        sessions = learning_plan.get("completed_sessions", 0)
    elif assessment:
        language = assessment.get("language", "English")
        level = assessment.get("level", "B1")
        progress = assessment.get("overall_score", 0)
        sessions = 1
    else:
        language = "English"
        level = "B1"
        progress = 50
        sessions = 5
    
    if custom_message:
        base_text = custom_message
    else:
        if platform == "instagram":
            base_text = f"🌮 Learning {language} with {app_name}! \n\n📈 {level} Level • {progress}% Complete\n💪 {sessions} Sessions Completed\n\n#LanguageLearning #{language}Learning #Progress #TacoAI #LanguageGoals #StudyMotivation"
        
        elif platform == "whatsapp":
            base_text = f"🌮 I'm learning {language} with {app_name}! \n\nJust reached {progress}% completion at {level} level 📈\n\nCompleted {sessions} sessions so far 💪\n\nWant to join me? Check out {app_name}! 🚀"
        
        else:  # general
            base_text = f"🌮 Learning {language} with {app_name}!\n\n📈 Progress: {progress}% complete\n🎯 Level: {level}\n💪 Sessions: {sessions}\n\n#LanguageLearning #{language}"
    
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
