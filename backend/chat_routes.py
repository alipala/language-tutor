import os
import re
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai_client import get_async_openai

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ProjectKnowledgeRequest(BaseModel):
    query: str

class ProjectKnowledgeResponse(BaseModel):
    response: str
    sources: List[str] = []

# User Experience Knowledge Base - focused on helping users navigate and use the app
KNOWLEDGE_BASE = {
    "getting_started": {
        "title": "How to Get Started with My Taco AI",
        "keywords": ["start", "begin", "first", "new", "how", "setup", "tutorial", "guide", "onboarding", "get started"],
        "content": """
🌮 Welcome to My Taco AI! Here's your complete getting started guide:

🎯 STEP 1: Choose Your Language
• Look for the colorful language flags on the homepage
• Click any flag: English 🇺🇸, Dutch 🇳🇱, Spanish 🇪🇸, French 🇫🇷, German 🇩🇪, Portuguese 🇵🇹
• Don't worry - you can change this anytime later!

🎤 STEP 2: Take Your Speaking Assessment
• Click the big "Take Assessment" button
• Allow microphone permission when asked
• Speak clearly for 15 seconds (guests) or 60 seconds (registered users)
• Talk about anything - describe your day, hobbies, or goals
• Our AI will tell you your level: A1 (beginner) to C2 (advanced)

💬 STEP 3: Start Your First Conversation
• After assessment, click "Start Conversation"
• Talk naturally with our AI tutor
• Discuss interesting topics like travel, food, or culture
• Get instant feedback and corrections
• Practice for 1 minute (guests) or 5 minutes (registered users)

📊 STEP 4: Save Your Progress (Optional but Recommended!)
• Click "Sign Up" to create a free account
• Save all your conversations and track improvement
• View your progress in the "Overview" tab
• Earn achievements and maintain learning streaks

✨ Pro Tips for Success:
• Use headphones or earbuds for better audio quality
• Find a quiet room without background noise
• Speak at normal volume - don't whisper or shout
• Don't worry about making mistakes - that's how you learn!
• Practice a little bit every day for best results

🚀 Ready to start? Just click any language flag on the homepage!
"""
    },
    "account_help": {
        "title": "Account & Login Help",
        "keywords": ["auth", "login", "signup", "register", "account", "password", "google", "forgot", "reset", "profile"],
        "content": """
Need help with your account? Here's everything you need to know:

Creating an Account:
- Click "Sign Up" in the top right corner
- Enter your name, email, and password
- Or use "Continue with Google" for quick signup
- Verify your email to unlock all features

Signing In:
- Click "Login" and enter your credentials
- Use Google Sign-In if you registered with Google
- Check "Remember me" to stay logged in

Forgot Your Password?
- Click "Forgot Password?" on the login page
- Enter your email address
- Check your email for a reset link
- Create a new password when prompted

Account Benefits:
- 60-second assessments (vs 15 seconds for guests)
- 5-minute conversations (vs 1 minute for guests)
- Save your conversation history
- Track your learning progress
- Earn achievements and maintain streaks
- Export your learning data

Profile Management:
- Update your name and email in settings
- Change your preferred language and level
- View your learning statistics
- Download your conversation history

Troubleshooting:
- Clear your browser cache if login issues persist
- Make sure cookies are enabled
- Try incognito/private mode
- Contact support if problems continue
"""
    },
    "guest_experience": {
        "title": "Guest User Experience",
        "keywords": ["guest", "trial", "free", "limitations", "conversion", "signup", "unregistered"],
        "content": """
The Language Tutor application provides a thoughtfully designed guest experience that allows users to try core features without requiring authentication.

Guest Limitations:
- Maximum of 3 assessments per session
- 15-second assessment duration (vs. 60 seconds for registered users)
- 1-minute conversation time (vs. 5 minutes for registered users)
- No progress tracking across sessions
- Limited conversation history

Guest Features:
- Initial Assessment: Complete a 15-second speaking assessment to determine language proficiency
- Language Selection: Choose from multiple supported languages
- Conversation Practice: Receive 1 minute of AI conversation practice after assessment
- Results and Feedback: Receive detailed feedback on speaking performance
- Conversion Opportunity: Clear calls-to-action encourage account creation for expanded features

The system tracks guest usage through session storage, enforces limits to encourage conversion, and provides clear upgrade messaging at key moments. Guest data is automatically cleaned up after 7 days, and there's no persistent data across browser sessions.

Conversion benefits clearly communicated:
- 60-second assessments vs 15 seconds
- 5-minute conversations vs 1 minute
- Unlimited practice sessions
- Progress tracking and achievements
"""
    },
    "enhanced_analysis": {
        "title": "Enhanced Tutor Analysis System",
        "keywords": ["analysis", "feedback", "assessment", "ai insights", "progress", "recommendations", "quality", "metrics"],
        "content": """
The Enhanced Tutor Analysis System provides comprehensive AI-powered analysis of conversation sessions, offering detailed insights into user engagement, learning progress, and personalized recommendations.

Core Features:
- Conversation Quality Analysis: Evaluates engagement levels and topic depth
- Progress Tracking: Monitors learning advancement and complexity growth
- Insight Generation: Identifies breakthrough moments and struggle points
- Recommendation Engine: Provides personalized next steps and learning goals
- Interactive Modal: Presents analysis in an intuitive tabbed interface

Quality Assessment includes:
- Overall Engagement Score: Comprehensive assessment of user participation
- Word Count Analysis: Measures verbosity and expression depth
- Question Frequency: Tracks curiosity and interactive learning
- Elaboration Rate: Evaluates detail and explanation quality
- Topic Depth Score: Measures how thoroughly topics are explored

AI Insights provide:
- Breakthrough Moment Detection: Highlights significant learning achievements
- Struggle Point Analysis: Identifies areas needing improvement
- Confidence Level Assessment: Measures growing language confidence
- Skill Progression Tracking: Development in grammar, vocabulary, fluency

Personalized Recommendations include:
- Immediate Actions: Specific areas to work on immediately
- Weekly Learning Goals: Medium-term objectives for language growth
- Long-term Objectives: CEFR level advancement targets

Session Eligibility: Enhanced analysis is generated for sessions with duration >= 5 minutes AND message_count >= 10, or duration >= 3 minutes AND message_count >= 15 for very active short sessions.
"""
    },
    "progress_tracking": {
        "title": "Progress Tracking System",
        "keywords": ["progress", "tracking", "history", "sessions", "achievements", "streaks", "statistics", "save"],
        "content": """
The Language Tutor application features a comprehensive progress tracking system that allows registered users to save their conversation sessions, view detailed conversation history, track learning statistics, and earn achievements.

Key Components:
- Save Progress Button: Allows users to manually save conversation progress during practice sessions
- Conversation History Storage: Automatically stores conversation transcripts with AI-generated summaries
- Progress Statistics: Tracks total sessions, practice time, streaks, and other metrics
- Achievement System: Dynamic achievements based on actual user progress
- Profile Integration: Displays all progress data in a comprehensive user profile

Save Progress Features:
- 1-minute cooldown to encourage meaningful conversations
- Dynamic visual states (saving, saved, error, cooldown)
- Smart visibility for authenticated users only
- Session extension instead of creating duplicates

Statistics Tracked:
- Total conversation sessions
- Total practice time in minutes
- Current learning streak (consecutive days)
- Longest streak achieved
- Sessions this week/month
- Streak eligibility (sessions ≥5 minutes)

Achievement Types:
- First Steps 🎯: Complete your first conversation
- Chatterbox 💬: Complete 5 conversations
- Dedicated Learner 📚: Practice for 30 minutes total
- Consistency King 👑: Maintain a 3-day streak
- Week Warrior 🔥: Maintain a 7-day streak
- Marathon Master 🏃: Practice for 60 minutes total
- Conversation Pro ⭐: Complete 10 conversations
- Monthly Master 🏆: Maintain a 30-day streak

The system implements proper resource cleanup, secure data storage, and comprehensive error handling for a reliable user experience.
"""
    },
    "frontend_architecture": {
        "title": "Frontend Architecture",
        "keywords": ["frontend", "nextjs", "react", "typescript", "components", "architecture", "ui", "interface"],
        "content": """
The Language Tutor frontend is built with Next.js 14, using the App Router pattern for modern, efficient page routing and server components. The application features a component-based architecture with a focus on reusability, maintainability, and performance.

Technology Stack:
- Next.js 14 with App Router
- TypeScript for type safety
- Tailwind CSS for styling
- React ChatBotify for chatbot functionality
- Framer Motion for animations

Key Components:
- Speaking Assessment: Handles audio recording using MediaRecorder API, processing and sending recordings to backend, displaying assessment results with detailed feedback
- Speech Client: Manages conversation interface with real-time communication with AI tutor, WebRTC audio streaming, message display and history
- Authentication Components: auth-form.tsx for login/registration, google-auth-button.tsx for Google Sign-In, auth.tsx for authentication context

State Management:
- React Context for global state like authentication and error handling
- Local Component State using useState and useReducer
- Session Storage for persisting state across page navigation
- Custom Hooks for encapsulating complex logic like real-time communication

Navigation System:
- Client-side routing with Next.js router
- Fallback navigation with window.location for reliability
- Session storage flags to track navigation state
- Stuck-state detection and automatic recovery

API Communication:
- api-utils.ts determines correct API URL based on environment
- Service-specific API clients
- healthCheck.ts verifies backend connectivity with retry logic

The application uses Tailwind CSS for responsive design, ensuring good user experience on both desktop and mobile devices with flexible layouts using Flexbox and Grid, mobile-first approach with responsive breakpoints, and custom components optimized for touch interaction.
"""
    },
    "backend_architecture": {
        "title": "Backend Architecture",
        "keywords": ["backend", "fastapi", "python", "api", "mongodb", "openai", "endpoints", "server"],
        "content": """
The Language Tutor backend is built with FastAPI, a modern, high-performance web framework for building APIs with Python. The backend provides a comprehensive set of endpoints for authentication, language assessment, learning plan management, and real-time conversation capabilities.

Technology Stack:
- FastAPI for high-performance API development
- MongoDB for data storage with AsyncIOMotorClient
- OpenAI GPT-4o for conversations and analysis
- Whisper API for speech-to-text transcription
- JWT for authentication
- bcrypt for password hashing

Core Components:
- Authentication System: User registration/login, JWT token generation/validation, Google OAuth integration, password reset functionality
- Speaking Assessment: Speech-to-text conversion using Whisper API, language proficiency evaluation based on CEFR levels, detailed feedback on pronunciation, grammar, vocabulary, fluency, and coherence
- Learning Plans: Learning goal retrieval and management, custom learning plan creation, plan assignment to users, assessment data storage
- Real-time Conversation: Ephemeral key generation for OpenAI Realtime API, WebRTC token management, conversation session handling

API Endpoints:
- Authentication: /auth/register, /auth/login, /auth/google-login, /auth/me
- Learning: /learning/goals, /learning/plan, /learning/plans
- Assessment: /api/assessment/speaking, /api/speaking-prompts, /api/assessment/sentence
- Real-time: /api/token, /api/mock-token
- System: /api/health, /api/test, /api/endpoints

OpenAI Integration:
- GPT-4o for language assessment, learning plan generation, and sentence analysis
- Whisper for speech-to-text transcription
- Realtime API for real-time voice conversation

Security Features:
- Password hashing with bcrypt
- JWT token authentication with expiration
- HTTPS enforcement in production
- Environment variable protection
- Rate limiting for authentication endpoints
- CORS configuration for cross-origin requests

The backend is optimized for deployment on Railway with environment variable detection, flexible MongoDB connection handling, and comprehensive error handling with detailed logging.
"""
    },
    "mobile_support": {
        "title": "Mobile Compatibility",
        "keywords": ["mobile", "responsive", "ios", "android", "safari", "chrome", "touch", "microphone", "pwa"],
        "content": """
Language Tutor is designed to work seamlessly across all devices, with special attention to mobile user experience and voice functionality.

Mobile Features:
- Responsive design that adapts to all screen sizes
- Touch-optimized interface with larger buttons and touch targets
- Mobile microphone access with proper permission handling
- Offline-capable PWA features for better performance
- Optimized layouts for portrait and landscape orientations

Voice on Mobile:
- WebRTC works reliably on iOS Safari and Android Chrome
- Automatic microphone permission handling with user-friendly prompts
- Optimized for mobile networks with adaptive quality
- Real-time audio streaming with low latency
- Fallback mechanisms for older mobile browsers

Browser Compatibility:
- iOS Safari 11+ (full WebRTC support)
- Android Chrome 55+ (full WebRTC support)
- Mobile Firefox 44+ (limited WebRTC support)
- Edge Mobile 79+ (full support)

Mobile Optimization Tips:
- Use headphones for better audio quality and reduced echo
- Ensure stable internet connection for real-time features
- Allow microphone permissions when prompted
- Works best in landscape mode for conversation interface
- Close other apps to ensure optimal performance

Technical Implementation:
- Responsive breakpoints using Tailwind CSS
- Touch event handling for better mobile interaction
- Viewport meta tag for proper mobile scaling
- Service worker for PWA functionality
- Optimized bundle size for faster mobile loading

The application automatically detects mobile devices and adjusts the interface accordingly, providing larger touch targets, simplified navigation, and optimized layouts for smaller screens.
"""
    },
    "assessment_guide": {
        "title": "How to Take Your Speaking Assessment",
        "keywords": ["assessment", "test", "level", "speaking", "cefr", "pronunciation", "grammar", "vocabulary", "fluency", "evaluate"],
        "content": """
🎯 Complete Guide to Taking Your Speaking Assessment:

🎤 HOW TO START YOUR ASSESSMENT:
• Click the "Take Assessment" button on any language page
• Allow microphone permission when your browser asks
• You'll see a timer: 15 seconds (guests) or 60 seconds (registered users)
• Click "Start Recording" when you're ready

🗣️ WHAT TO TALK ABOUT:
• Describe your daily routine or hobbies
• Talk about your goals for learning this language
• Describe your hometown or favorite place to visit
• Share what you enjoy doing in your free time
• Discuss your work or studies
• Talk about your family or friends

💡 TIPS FOR A GREAT ASSESSMENT:
• Speak naturally - don't try to be perfect!
• Use complete sentences when possible
• If you make a mistake, just keep going
• Try to speak for the full time available
• Use headphones for better audio quality
• Find a quiet room without background noise

📊 WHAT YOU'LL GET:
After your assessment, you'll receive:
• Your CEFR level (A1-C2)
• Pronunciation score and feedback
• Grammar assessment and tips
• Vocabulary evaluation
• Fluency analysis
• Overall speaking score

🎯 UNDERSTANDING YOUR LEVEL:
• A1 (Beginner): Just starting to learn
• A2 (Elementary): Can handle basic conversations
• B1 (Intermediate): Comfortable with familiar topics
• B2 (Upper-Intermediate): Can discuss complex ideas
• C1 (Advanced): Very fluent and natural
• C2 (Proficiency): Near-native level

🚀 AFTER YOUR ASSESSMENT:
• Click "Start Conversation" to practice with our AI tutor
• Your conversation topics will match your level
• You'll get real-time feedback as you speak
• Sign up to save your results and track improvement!
"""
    },
    "practice_guide": {
        "title": "How to Practice Conversations",
        "keywords": ["practice", "conversation", "talk", "speak", "chat", "tutor", "ai", "feedback", "topics"],
        "content": """
💬 Complete Guide to Practicing Conversations:

🚀 HOW TO START PRACTICING:
• After your assessment, click "Start Conversation"
• Or go to any language page and click "Start Conversation"
• Allow microphone permission if asked
• You'll see a timer: 1 minute (guests) or 5 minutes (registered users)

🎯 WHAT HAPPENS DURING PRACTICE:
• Our AI tutor will greet you and suggest a topic
• Talk naturally about the suggested topic
• The AI will respond and ask follow-up questions
• You'll see your conversation appear as text on screen
• Get instant corrections and suggestions

🗣️ GREAT CONVERSATION TOPICS:
• Travel: Describe places you've visited or want to visit
• Food: Talk about your favorite dishes or cooking
• Hobbies: Share what you enjoy doing in free time
• Culture: Discuss traditions from your country
• Movies/TV: Talk about shows you like
• Work/Study: Describe your job or education
• Future Plans: Share your goals and dreams

💡 TIPS FOR BETTER CONVERSATIONS:
• Speak clearly and at normal speed
• Don't worry about making mistakes - that's how you learn!
• Ask questions back to the AI tutor
• Try to give detailed answers, not just yes/no
• Use the vocabulary you know
• If you don't understand, ask the AI to repeat or explain

🎤 TECHNICAL TIPS:
• Use headphones or earbuds for best audio quality
• Speak 6-8 inches from your microphone
• Find a quiet room without background noise
• Make sure your internet connection is stable
• If audio cuts out, refresh the page and try again

📈 GETTING FEEDBACK:
• Real-time corrections appear during conversation
• After 5+ minutes, you can get detailed AI analysis
• See your pronunciation, grammar, and fluency scores
• Get personalized recommendations for improvement

🏆 MAKING PROGRESS:
• Practice regularly - even 5 minutes daily helps!
• Try different topics to expand vocabulary
• Challenge yourself with slightly harder topics
• Sign up to track your improvement over time
"""
    },
    "save_progress_guide": {
        "title": "How to Save Your Progress",
        "keywords": ["save", "progress", "history", "track", "account", "sessions", "improvement", "data"],
        "content": """
💾 Complete Guide to Saving Your Progress:

🔐 CREATE AN ACCOUNT FIRST:
• Click "Sign Up" in the top right corner
• Enter your name, email, and password
• Or use "Continue with Google" for quick signup
• Verify your email to unlock all features

💾 SAVING DURING CONVERSATIONS:
• Look for the "Save Progress" button during practice
• Click it anytime during your conversation
• You'll see a confirmation when it's saved
• The button has a 1-minute cooldown to encourage longer practice

📊 WHAT GETS SAVED:
• Complete conversation transcripts
• Your speaking assessment results
• Practice session duration and date
• AI feedback and corrections
• Your CEFR level progression
• Achievement progress

📈 VIEWING YOUR PROGRESS:
• Click "Overview" tab to see all your data
• View conversation history with dates
• See total practice time and session count
• Track your learning streaks
• Monitor your level improvements

🏆 ACHIEVEMENTS YOU CAN EARN:
• First Steps 🎯: Complete your first conversation
• Chatterbox 💬: Complete 5 conversations
• Dedicated Learner 📚: Practice for 30 minutes total
• Consistency King 👑: Maintain a 3-day streak
• Week Warrior 🔥: Maintain a 7-day streak
• Marathon Master 🏃: Practice for 60 minutes total
• Conversation Pro ⭐: Complete 10 conversations
• Monthly Master 🏆: Maintain a 30-day streak

📊 TRACKING YOUR STREAKS:
• Practice at least 5 minutes daily to maintain streaks
• Streaks reset if you miss a day
• Your longest streak is saved forever
• Streaks motivate consistent practice

💡 PROGRESS TIPS:
• Save every conversation to track improvement
• Review your conversation history regularly
• Notice patterns in your mistakes
• Celebrate your achievements!
• Set daily practice goals

🔄 AUTOMATIC SAVING:
• Conversations over 5 minutes are automatically saved
• Assessment results are always saved
• Your account syncs across all devices
• Data is securely stored and backed up
"""
    },
    "learning_plans_guide": {
        "title": "Understanding Learning Plans",
        "keywords": ["learning", "plan", "goals", "personalized", "curriculum", "study", "improvement", "recommendations"],
        "content": """
📚 Complete Guide to Learning Plans:

🎯 WHAT ARE LEARNING PLANS:
• Personalized study programs based on your assessment
• Custom goals tailored to your level and interests
• Step-by-step recommendations for improvement
• Adaptive plans that evolve with your progress

📋 HOW TO GET YOUR LEARNING PLAN:
• Take your speaking assessment first
• Your plan is automatically generated based on results
• View it in the "Learning Plan" section
• Plans update as you practice and improve

🎯 WHAT'S IN YOUR LEARNING PLAN:
• Your current CEFR level and target level
• Specific skills to focus on (pronunciation, grammar, etc.)
• Recommended practice topics
• Weekly and monthly goals
• Estimated time to reach next level

📈 TYPES OF GOALS IN YOUR PLAN:
• Pronunciation Goals: Specific sounds to practice
• Grammar Goals: Tenses and structures to master
• Vocabulary Goals: Word categories to expand
• Fluency Goals: Speaking pace and confidence targets
• Conversation Goals: Topics and situations to practice

🎯 FOLLOWING YOUR LEARNING PLAN:
• Practice the recommended topics during conversations
• Focus on your weak areas identified in assessments
• Try to meet your weekly practice time goals
• Take regular assessments to track progress

📊 TRACKING PLAN PROGRESS:
• See completion percentage for each goal
• Monitor time spent on recommended topics
• Track skill improvements over time
• Get updated recommendations based on progress

💡 TIPS FOR SUCCESS:
• Follow your plan consistently for best results
• Don't skip the areas you find difficult
• Practice a little bit every day rather than long sessions
• Ask the AI tutor to focus on your plan topics
• Celebrate when you complete goals!

🔄 PLAN UPDATES:
• Plans automatically update based on new assessments
• Goals adjust as you improve
• New recommendations appear as you progress
• Plans become more challenging as you advance

🎯 CUSTOMIZING YOUR PLAN:
• Focus on specific skills you want to improve
• Choose topics that interest you most
• Set your own practice time goals
• Adjust difficulty based on your schedule
"""
    },
    "export_data_guide": {
        "title": "How to Export Your Learning Data",
        "keywords": ["export", "download", "data", "progress", "report", "pdf", "csv", "history", "backup"],
        "content": """
📊 Complete Guide to Exporting Your Learning Data:

📥 HOW TO EXPORT YOUR DATA:
• Go to your "Overview" or "Profile" section
• Look for "Export Data" or "Download Report" button
• Choose your preferred format (PDF, CSV, or ZIP)
• Click download and save the file to your device

📄 AVAILABLE EXPORT FORMATS:

🔸 PDF REPORTS:
• Professional conversation history report
• Learning plans and assessment report
• Includes your profile, statistics, and progress
• Perfect for sharing with teachers or institutions

🔸 CSV FILES:
• Spreadsheet format for detailed analysis
• Conversation history with dates and topics
• Learning plan data with scores and goals
• Easy to open in Excel or Google Sheets

🔸 ZIP PACKAGE:
• Complete data export with all formats
• Includes PDFs, CSVs, and JSON data
• Perfect for complete backup of your progress

📊 WHAT'S INCLUDED IN YOUR EXPORT:

🔸 STUDENT PROFILE:
• Your name and email
• Report generation date
• Total practice sessions
• Current language levels

🔸 CONVERSATION HISTORY:
• All your practice sessions with dates
• Conversation topics and duration
• Message counts and AI analysis
• Detailed feedback and corrections

🔸 ASSESSMENT DATA:
• All your speaking assessment results
• Skill scores (pronunciation, grammar, etc.)
• CEFR level progression over time
• Detailed feedback for each assessment

🔸 LEARNING STATISTICS:
• Total practice time
• Learning streaks and achievements
• Session frequency and patterns
• Progress trends and improvements

💡 WHEN TO EXPORT YOUR DATA:
• Before important meetings with teachers
• To track long-term progress
• For backup before changing devices
• To share achievements with others
• For personal motivation and review

🎯 USING YOUR EXPORTED DATA:
• Share PDF reports with language teachers
• Analyze patterns in CSV files
• Keep backups of your learning journey
• Track improvement over months/years
• Include in language learning portfolios

🔒 DATA PRIVACY:
• Only you can export your data
• Exports include only your personal information
• Data is securely generated and downloaded
• No data is shared with third parties

📱 MOBILE EXPORT:
• Export works on mobile devices too
• Files download to your phone/tablet
• Share directly from mobile apps
• View PDFs on any device
"""
    }
}

def search_knowledge_base(query: str) -> List[Dict[str, Any]]:
    """
    Search the knowledge base using keyword matching and return relevant chunks
    """
    query_lower = query.lower()
    query_words = re.findall(r'\b\w+\b', query_lower)
    
    results = []
    
    for chunk_id, chunk in KNOWLEDGE_BASE.items():
        score = 0
        
        # Check title match
        if any(word in chunk["title"].lower() for word in query_words):
            score += 10
        
        # Check keyword matches
        keyword_matches = sum(1 for keyword in chunk["keywords"] if keyword in query_lower)
        score += keyword_matches * 5
        
        # Check content matches
        content_lower = chunk["content"].lower()
        content_matches = sum(1 for word in query_words if word in content_lower)
        score += content_matches
        
        # Add specific topic scoring for user guides
        if any(topic in query_lower for topic in ["start", "begin", "getting started", "how to start", "first time", "new user"]):
            if chunk_id == "getting_started":
                score += 20
        
        if any(topic in query_lower for topic in ["assessment", "test", "level", "speaking test", "evaluate", "take assessment"]):
            if chunk_id == "assessment_guide":
                score += 20
        
        if any(topic in query_lower for topic in ["practice", "conversation", "talk", "speak", "chat", "tutor"]):
            if chunk_id == "practice_guide":
                score += 20
        
        if any(topic in query_lower for topic in ["save", "progress", "track", "history", "improvement", "save progress"]):
            if chunk_id == "save_progress_guide":
                score += 20
        
        if any(topic in query_lower for topic in ["learning plan", "goals", "curriculum", "study plan", "personalized"]):
            if chunk_id == "learning_plans_guide":
                score += 20
        
        if any(topic in query_lower for topic in ["export", "download", "data", "report", "pdf", "csv", "backup"]):
            if chunk_id == "export_data_guide":
                score += 20
        
        if any(topic in query_lower for topic in ["auth", "login", "signup", "password", "account", "register"]):
            if chunk_id == "account_help":
                score += 20
        
        if any(topic in query_lower for topic in ["mobile", "ios", "android", "phone", "tablet", "mobile tips"]):
            if chunk_id == "mobile_support":
                score += 20
        
        # Legacy scoring for backward compatibility
        if any(topic in query_lower for topic in ["guest", "trial", "free", "limitation"]):
            if chunk_id == "guest_experience":
                score += 15
        
        if any(topic in query_lower for topic in ["analysis", "feedback", "ai insights", "enhanced"]):
            if chunk_id == "enhanced_analysis":
                score += 15
        
        if score > 0:
            results.append({
                "chunk_id": chunk_id,
                "title": chunk["title"],
                "content": chunk["content"],
                "score": score
            })
    
    # Sort by score and return top results
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:3]  # Return top 3 most relevant chunks

@router.post("/project-knowledge", response_model=ProjectKnowledgeResponse)
async def get_project_knowledge(request: ProjectKnowledgeRequest):
    """
    Answer questions about the Language Tutor project using RAG
    """
    try:
        print(f"[CHAT] Received query: {request.query}")
        
        # Search knowledge base
        relevant_chunks = search_knowledge_base(request.query)
        
        if not relevant_chunks:
            return ProjectKnowledgeResponse(
                response="I'm sorry, I couldn't find specific information about that. Please try asking about our features like speaking assessment, real-time conversations, progress tracking, authentication, mobile support, or technical architecture.",
                sources=[]
            )
        
        # Prepare context from relevant chunks
        context = "\n\n".join([
            f"## {chunk['title']}\n{chunk['content']}"
            for chunk in relevant_chunks
        ])
        
        # Create system prompt for GPT-4o-mini focused on user experience
        system_prompt = """You are a friendly and helpful assistant for My Taco AI language learning app. Your goal is to help users who feel stuck, confused, or need guidance on how to use the app effectively.

Guidelines:
- Be warm, encouraging, and supportive
- Focus on practical step-by-step guidance rather than technical details
- Use simple, clear language that anyone can understand
- Include helpful emojis to make responses friendly
- Provide specific actionable steps users can take right now
- If users seem frustrated, acknowledge their feelings and offer solutions
- Always end with an offer to help further or ask follow-up questions
- Avoid technical jargon - focus on what users need to DO, not how it works

Your role: Help users navigate the app, solve problems, and have a great learning experience.

Context from My Taco AI user guides:
"""

        # Generate response using GPT-4o-mini
        response = await get_async_openai().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt + context},
                {"role": "user", "content": request.query}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        sources = [chunk["title"] for chunk in relevant_chunks]
        
        print(f"[CHAT] Generated response with {len(relevant_chunks)} sources")
        
        return ProjectKnowledgeResponse(
            response=answer,
            sources=sources
        )
        
    except Exception as e:
        print(f"[CHAT] Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Sorry, I'm having trouble processing your question right now. Please try again or ask about our main features."
        )
