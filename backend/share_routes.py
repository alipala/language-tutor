import os
import json
import base64
import httpx
import requests
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

def create_epic_achievement_prompt(progress_data: Dict[str, Any], share_type: str, platform: str, week_number: Optional[int] = None) -> str:
    """
    Create EPIC, engaging achievement prompts that users will be proud to share and wear on t-shirts
    """
    # Extract data
    learning_plan = progress_data.get("learning_plan", {})
    plan_content = progress_data.get("plan_content", {})
    language = learning_plan.get("language", "English").title()
    level = learning_plan.get("level", "B1").upper()
    app_name = progress_data.get("app_name", "MyTacoAI")
    
    # Brand colors for epic design
    turquoise = "#4ECFBF"
    yellow = "#FFD63A"
    coral = "#F75A5A"
    orange = "#FFA955"
    
    # Epic achievement types based on week number and progress
    if week_number:
        if week_number == 1:
            achievement_type = "FIRST VICTORY"
            epic_element = "golden crown with radiating light beams"
            background_effect = "explosive celebration with confetti and fireworks"
        elif week_number <= 4:
            achievement_type = "CHAMPION RISING"
            epic_element = "blazing phoenix wings spreading wide"
            background_effect = "dynamic energy waves and lightning bolts"
        elif week_number <= 8:
            achievement_type = "WARRIOR ELITE"
            epic_element = "majestic sword crossed with laurel branches"
            background_effect = "cosmic nebula with swirling galaxies"
        elif week_number <= 12:
            achievement_type = "LEGEND MASTER"
            epic_element = "mythical dragon coiled around a crystal"
            background_effect = "divine rays of light piercing storm clouds"
        else:
            achievement_type = "ULTIMATE CHAMPION"
            epic_element = "celestial crown with floating gems"
            background_effect = "otherworldly aurora with magical particles"
    else:
        achievement_type = "LANGUAGE WARRIOR"
        epic_element = "heroic shield with glowing runes"
        background_effect = "epic battlefield with victory banners"
    
    # Create platform-optimized prompt
    if platform == "instagram":
        # Square format, Instagram-optimized
        prompt = f"""Create an EPIC achievement badge design that screams SUCCESS and VICTORY! 

🎯 DESIGN CONCEPT: "{achievement_type} - WEEK {week_number} CONQUERED!"

VISUAL ELEMENTS:
- Center: Massive, bold text "WEEK {week_number}" in heroic golden font with chrome effects
- Below: "COMPLETE!" in explosive letters with fire trails
- Around: {epic_element} as the main heroic symbol
- Background: {background_effect} in cinematic style

COLOR SCHEME: 
- Primary: Brilliant gold ({yellow}) and electric turquoise ({turquoise})
- Accents: Victory coral ({coral}) and champion orange ({orange})
- Effects: Metallic chrome, glowing auras, light explosions

STYLE: 
- Epic fantasy art meets superhero comic book
- Cinematic lighting with dramatic shadows
- Perfect for t-shirt printing - bold, high contrast
- Social media ready - eye-catching and shareable

TEXT PLACEMENT:
- Top arc: "{level} {language} MASTERY"
- Bottom banner: "{app_name} CHAMPION"
- Side elements: Victory stars and achievement flames

MOOD: Triumphant, powerful, legendary achievement unlocked!
Format: Square 1024x1024 for perfect Instagram sharing"""

    elif platform == "whatsapp":
        # More personal, friendly but still epic
        prompt = f"""Design a CELEBRATION EXPLOSION achievement that friends will be amazed by!

🏆 ACHIEVEMENT: "LANGUAGE CHAMPION - WEEK {week_number} MASTERED!"

DESIGN ELEMENTS:
- Bold central text: "WEEK {week_number} DONE!" with celebration effects
- {epic_element} surrounding the text majestically
- {background_effect} creating an awesome backdrop
- Victory ribbons flowing with "{level} {language}" text

COLORS:
- Vibrant celebration palette: {turquoise}, {yellow}, {coral}
- Metallic gold accents for premium feel
- Glowing effects that pop on phone screens

STYLE:
- Modern achievement badge meets party celebration
- Clean enough for WhatsApp but epic enough for bragging
- T-shirt ready design with bold graphics

ELEMENTS:
- Confetti and celebration particles
- Achievement stars bursting outward
- "{app_name}" banner at bottom
- Success crown or victory laurels

Perfect for sharing progress with friends and family!
Square format 1024x1024"""

    else:  # General/universal
        # Most epic version for maximum impact
        prompt = f"""Create an ABSOLUTELY LEGENDARY achievement design that commands respect!

🔥 ULTIMATE ACHIEVEMENT: "{achievement_type} UNLOCKED!"

EPIC ELEMENTS:
- Dominant text: "WEEK {week_number} CONQUERED" in god-tier typography
- Subtitle: "{level} {language} WARRIOR" in heroic font
- Central symbol: {epic_element} rendered in mythical glory
- Background: {background_effect} with cinematic grandeur

LEGENDARY DESIGN:
- Style: Epic fantasy meets modern superhero aesthetic
- Lighting: Dramatic cinematic lighting with divine rays
- Effects: Particle explosions, energy auras, metallic gleams
- Colors: Champion gold, warrior turquoise, victory coral, flame orange

POWER ELEMENTS:
- Lightning bolts crackling around edges
- Victory wreaths and champion laurels
- Mystical runes spelling "{app_name}"
- Achievement gems floating in corners

IMPACT GOALS:
- Museum-quality poster worthy
- T-shirt design that starts conversations
- Social media post that gets engagement
- Badge of honor users wear with pride

Format: Perfect square for maximum platform compatibility
Mood: "I am a LEGEND and this proves it!"
1024x1024 resolution for crisp printing and sharing"""

    return prompt

def create_weekly_milestone_prompt(progress_data: Dict[str, Any], week_number: int, platform: str) -> str:
    """
    Special prompts for specific weekly milestones with unique themes
    """
    learning_plan = progress_data.get("learning_plan", {})
    language = learning_plan.get("language", "English").title()
    level = learning_plan.get("level", "B1").upper()
    app_name = progress_data.get("app_name", "MyTacoAI")
    
    # Special milestone themes
    milestone_themes = {
        1: {
            "title": "FIRST BLOOD",
            "theme": "Medieval knight achieving first victory",
            "elements": "golden sword piercing through darkness",
            "background": "dawn breaking over mountain peaks",
            "mood": "triumphant beginning of an epic journey"
        },
        4: {
            "title": "MONTH WARRIOR", 
            "theme": "Ancient gladiator in the arena",
            "elements": "colosseum with roaring crowds",
            "background": "golden sunset with victory banners",
            "mood": "earned respect through persistent battle"
        },
        8: {
            "title": "CHAMPION RISE",
            "theme": "Dragon rider soaring above clouds",
            "elements": "majestic dragon with glowing eyes",
            "background": "stormy skies with lightning",
            "mood": "power and mastery over the elements"
        },
        12: {
            "title": "LANGUAGE GOD",
            "theme": "Mythical deity on mountain throne",
            "elements": "crown of stars and cosmic energy",
            "background": "divine realm with floating islands",
            "mood": "transcendent mastery beyond mortal limits"
        }
    }
    
    # Get milestone or default
    milestone = milestone_themes.get(week_number, milestone_themes[1])
    
    prompt = f"""Design an ABSOLUTELY LEGENDARY {milestone['title']} achievement!

🌟 MILESTONE: "{milestone['title']} - {level} {language} LEGEND"

EPIC THEME: {milestone['theme']}
- Central element: {milestone['elements']}
- Background scene: {milestone['background']}
- Artistic mood: {milestone['mood']}

HEROIC TEXT:
- Main: "WEEK {week_number}" in massive godlike letters
- Subtitle: "{milestone['title']}" in epic carved stone font
- Banner: "{level} {language} MASTERY ACHIEVED"
- Signature: "{app_name} CHAMPION" in victory scroll

LEGENDARY DESIGN:
- Style: Cinematic concept art meets ancient mythology
- Lighting: Divine rays, magical auras, epic backlighting
- Colors: Mythical gold, eternal turquoise, victory crimson
- Effects: Particle magic, energy waves, heroic glow

POWER SYMBOLS:
- Achievement runes glowing with power
- Victory wreaths made of linguistic symbols
- Magical elements representing language mastery
- Epic flourishes worthy of a movie poster

IMPACT: Users will frame this and show it off proudly!
Perfect for t-shirts, posters, social media dominance!
Square 1024x1024 for maximum awesome!"""
    
    return prompt

def create_achievement_tier_prompt(progress_data: Dict[str, Any], achievement_level: str, platform: str) -> str:
    """
    Create tier-based achievement prompts (Bronze, Silver, Gold, Platinum, Diamond)
    """
    learning_plan = progress_data.get("learning_plan", {})
    language = learning_plan.get("language", "English").title()
    level = learning_plan.get("level", "B1").upper()
    completed_sessions = learning_plan.get("completed_sessions", 0)
    app_name = progress_data.get("app_name", "MyTacoAI")
    
    # Achievement tiers with epic themes
    tiers = {
        "bronze": {
            "title": "BRONZE WARRIOR",
            "color_scheme": "Bronze metallic with copper highlights",
            "elements": "Ancient bronze shield with warrior engravings",
            "background": "Forge fires with sparks flying",
            "subtitle": "THE JOURNEY BEGINS"
        },
        "silver": {
            "title": "SILVER CHAMPION", 
            "color_scheme": "Brilliant silver with platinum accents",
            "elements": "Gleaming silver armor with victory wreaths",
            "background": "Moonlit battlefield with silver light rays",
            "subtitle": "RISING TO GLORY"
        },
        "gold": {
            "title": "GOLD LEGEND",
            "color_scheme": "Pure gold with radiant yellow highlights", 
            "elements": "Majestic golden crown with floating gems",
            "background": "Sunburst explosion with golden particles",
            "subtitle": "LEGENDARY STATUS ACHIEVED"
        },
        "platinum": {
            "title": "PLATINUM MASTER",
            "color_scheme": "Platinum white with prismatic rainbow effects",
            "elements": "Crystalline scepter with energy orbs",
            "background": "Cosmic nebula with swirling galaxies",
            "subtitle": "BEYOND MORTAL LIMITS"
        },
        "diamond": {
            "title": "DIAMOND GOD",
            "color_scheme": "Diamond clarity with rainbow prismatic effects",
            "elements": "Transcendent crystal formation with divine light",
            "background": "Otherworldly dimension with floating crystals",
            "subtitle": "ULTIMATE PERFECTION"
        }
    }
    
    tier = tiers.get(achievement_level.lower(), tiers["bronze"])
    
    prompt = f"""Create an ABSOLUTELY MAGNIFICENT {tier['title']} achievement badge!

💎 TIER ACHIEVEMENT: "{tier['title']} - {level} {language}"

EPIC DESIGN ELEMENTS:
- Primary text: "{tier['title']}" in legendary typography
- Secondary: "{tier['subtitle']}" in heroic script
- Central symbol: {tier['elements']} 
- Background: {tier['background']}
- Color palette: {tier['color_scheme']}

ACHIEVEMENT DETAILS:
- Sessions completed: {completed_sessions} VICTORIES
- Language level: {level} {language} MASTERY
- Platform: {app_name} CHAMPION
- Tier status: {tier['title']} RANK ACHIEVED

ARTISTIC STYLE:
- Premium gaming achievement aesthetic
- Hollywood movie poster quality
- Museum-worthy artistic composition
- Perfect for luxury merchandise

VISUAL EFFECTS:
- Metallic textures with realistic reflections
- Particle systems with magical sparkles
- Dynamic lighting with dramatic shadows
- Cinematic depth and epic proportions

USER PRIDE FACTOR: 
This is something they'll want to print on everything!
T-shirts, mugs, posters, business cards!
Pure visual flex that commands respect!

Square format 1024x1024 for perfect sharing and printing"""
    
    return prompt

def create_image_prompt(progress_data: Dict[str, Any], share_type: str, platform: str, week_number: Optional[int] = None) -> str:
    """
    Master function that routes to the appropriate epic prompt creator
    """
    learning_plan = progress_data.get("learning_plan", {})
    completed_sessions = learning_plan.get("completed_sessions", 0)
    
    # Determine achievement tier based on progress
    if completed_sessions >= 48:
        achievement_level = "diamond"
    elif completed_sessions >= 36:
        achievement_level = "platinum"
    elif completed_sessions >= 24:
        achievement_level = "gold"
    elif completed_sessions >= 12:
        achievement_level = "silver"
    else:
        achievement_level = "bronze"
    
    # Choose prompt type based on share_type and data
    if share_type == "milestone" and week_number and week_number in [1, 4, 8, 12]:
        return create_weekly_milestone_prompt(progress_data, week_number, platform)
    elif share_type == "tier" or completed_sessions >= 12:
        return create_achievement_tier_prompt(progress_data, achievement_level, platform)
    else:
        return create_epic_achievement_prompt(progress_data, share_type, platform, week_number)

def create_share_text(progress_data: Dict[str, Any], platform: str, custom_message: Optional[str] = None, week_number: Optional[int] = None) -> str:
    """
    Create epic, engaging share text that matches the powerful imagery
    """
    learning_plan = progress_data.get("learning_plan", {})
    language = learning_plan.get("language", "English").title()
    level = learning_plan.get("level", "B1").upper()
    completed_sessions = learning_plan.get("completed_sessions", 0)
    app_name = progress_data.get("app_name", "MyTacoAI")
    
    # Epic achievement phrases
    victory_phrases = [
        "🔥 CONQUERED ANOTHER WEEK",
        "⚡ DOMINATING MY LANGUAGE GOALS", 
        "🏆 CRUSHING EVERY MILESTONE",
        "💪 UNSTOPPABLE LEARNING MACHINE",
        "🎯 PRECISION STRIKING MY TARGETS"
    ]
    
    power_phrases = [
        f"I don't just learn languages - I MASTER them! 💎",
        f"Another week, another victory in my linguistic conquest! ⚔️", 
        f"My {language} skills are reaching legendary status! 🌟",
        f"Building my language empire one week at a time! 🏛️",
        f"Transforming from student to {language} CHAMPION! 👑"
    ]
    
    if custom_message:
        base_text = custom_message
    else:
        if platform == "instagram":
            victory = victory_phrases[week_number % len(victory_phrases) if week_number else 0]
            power = power_phrases[completed_sessions % len(power_phrases)]
            
            base_text = f"""{victory}

Week {week_number} ✅ COMPLETE!
{level} {language} progression: DOMINANT 📈

{power}

This isn't just language learning - this is LANGUAGE MASTERY! 

Every session brings me closer to fluency perfection. Every week proves I'm unstoppable! 

Who else is ready to join the {language} champions? 💪

#{language}Learning #{language}Champion #{app_name}Warrior #LanguageMastery #UnstoppableLearning #WeeklyWins #LanguageGoals #LearningJourney #FluentLife #StudyMotivation #LanguageSkills #MasteryMode"""

        elif platform == "whatsapp":
            base_text = f"""🎉 WEEK {week_number} CRUSHED! 🎉

Just dominated another week of {language} learning! 

Current status: {level} level CHAMPION 👑
Sessions completed: {completed_sessions} VICTORIES ⚡
Confidence level: MAXIMUM 💪

I'm not just learning {language} - I'm CONQUERING it! 

Every week I get stronger, smarter, and more fluent. This journey with {app_name} is turning me into a language LEGEND! 

Want to join my conquest? Let's dominate languages together! 🚀"""

        else:  # General platform
            base_text = f"""🏆 LANGUAGE MASTERY UPDATE 🏆

Week {week_number}: CONQUERED ✅
Level: {level} {language} CHAMPION 👑  
Progress: {completed_sessions} sessions of pure DOMINATION 💪

I'm not just learning - I'm building a LEGEND! 

Every week with {app_name} transforms me into a more powerful, confident {language} speaker. 

This is what REAL progress looks like! 🔥

#LanguageChampion #{language}Mastery #UnstoppableLearning"""
    
    return base_text

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
        
        print(f"[SHARE] Generated epic prompt: {image_prompt[:200]}...")
        
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
            print(f"[SHARE] ✅ Epic image generated successfully: {image_url}")
            
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
                sessions_per_week = 4
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
async def get_user_weeks(
    current_user: UserResponse = Depends(get_current_user),
    learning_plan_id: Optional[str] = None
):
    """
    Get user's completed weeks for sharing
    - If learning_plan_id is provided: return weeks for THAT specific plan only
    - If no learning_plan_id: return aggregated weeks across ALL plans (global achievements)
    """
    try:
        learning_plans_collection = database.learning_plans
        
        if learning_plan_id:
            # SPECIFIC PLAN MODE: Only show achievements for the specified learning plan
            print(f"[SHARE] Getting weeks for specific learning plan: {learning_plan_id}")
            
            specific_plan = await learning_plans_collection.find_one({
                "id": learning_plan_id,
                "user_id": current_user.id
            })
            
            if not specific_plan:
                print(f"[SHARE] Learning plan {learning_plan_id} not found for user {current_user.id}")
                return {"completed_weeks": [], "total_weeks": 0, "completed_sessions": 0}
            
            completed_sessions = specific_plan.get("completed_sessions", 0)
            sessions_per_week = 4
            plan_completed_weeks = completed_sessions // sessions_per_week
            plan_total_weeks = specific_plan.get("duration_months", 6) * 4
            plan_language = specific_plan.get("language", "unknown")
            
            print(f"[SHARE] Specific plan: {plan_language}, {completed_sessions} sessions, {plan_completed_weeks} weeks completed")
            
            # Create weeks array for this specific plan only
            completed_weeks_list = []
            for week_num in range(1, plan_completed_weeks + 1):
                completed_weeks_list.append({
                    "week_number": week_num,
                    "sessions_completed": sessions_per_week,
                    "total_sessions": sessions_per_week,
                    "is_completed": True,
                    "plan_language": plan_language,
                    "plan_id": learning_plan_id
                })
            
            print(f"[SHARE] ✅ Returning {len(completed_weeks_list)} weeks for specific plan {learning_plan_id}")
            
            return {
                "completed_weeks": completed_weeks_list,
                "total_weeks": plan_total_weeks,
                "completed_sessions": completed_sessions,
                "plan_specific": True,
                "plan_language": plan_language
            }
        
        else:
            # GLOBAL MODE: Aggregate achievements across ALL plans
            print(f"[SHARE] Getting aggregated weeks across all learning plans")
            
            all_plans = await learning_plans_collection.find(
                {"user_id": current_user.id}
            ).to_list(100)
            
            if not all_plans:
                return {"completed_weeks": [], "total_weeks": 0, "completed_sessions": 0}
            
            print(f"[SHARE] Found {len(all_plans)} learning plans for user {current_user.id}")
            
            # Aggregate completed weeks across ALL plans
            all_completed_weeks = {}
            max_total_weeks = 0
            total_completed_sessions = 0
            
            for plan in all_plans:
                completed_sessions = plan.get("completed_sessions", 0)
                sessions_per_week = 4
                plan_completed_weeks = completed_sessions // sessions_per_week
                plan_total_weeks = plan.get("duration_months", 6) * 4
                plan_language = plan.get("language", "unknown")
                
                print(f"[SHARE] Plan {plan.get('id', 'unknown')}: {plan_language}, {completed_sessions} sessions, {plan_completed_weeks} weeks completed")
                
                # Track the highest week completed across all plans
                for week_num in range(1, plan_completed_weeks + 1):
                    if week_num not in all_completed_weeks:
                        all_completed_weeks[week_num] = {
                            "week_number": week_num,
                            "sessions_completed": sessions_per_week,
                            "total_sessions": sessions_per_week,
                            "is_completed": True,
                            "plan_language": plan_language,
                            "plan_id": plan.get("id", "unknown")
                        }
                        print(f"[SHARE] Added week {week_num} from {plan_language} plan")
                
                max_total_weeks = max(max_total_weeks, plan_total_weeks)
                total_completed_sessions += completed_sessions
            
            # Convert to sorted list
            completed_weeks_list = [
                all_completed_weeks[week_num] 
                for week_num in sorted(all_completed_weeks.keys())
            ]
            
            print(f"[SHARE] ✅ Aggregated {len(completed_weeks_list)} completed weeks across all plans")
            print(f"[SHARE] Completed weeks: {[w['week_number'] for w in completed_weeks_list]}")
            
            return {
                "completed_weeks": completed_weeks_list,
                "total_weeks": max_total_weeks,
                "completed_sessions": total_completed_sessions,
                "plan_specific": False
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
