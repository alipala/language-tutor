import os
import re
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ProjectKnowledgeRequest(BaseModel):
    query: str

class ProjectKnowledgeResponse(BaseModel):
    response: str
    sources: List[str] = []

# Knowledge base from documentation - chunked by topic
KNOWLEDGE_BASE = {
    "speech_recognition": {
        "title": "Speech Recognition System",
        "keywords": ["speech", "recognition", "audio", "recording", "microphone", "webrtc", "whisper", "transcription", "voice"],
        "content": """
The Language Tutor application implements a sophisticated speech recognition and real-time conversation system using a combination of browser-based APIs and OpenAI's advanced language models.

Architecture:
- Frontend WebRTC Client: Handles audio capture and streaming
- Backend Token Service: Generates secure ephemeral tokens
- OpenAI Realtime API: Processes audio and generates responses

Key Features:
- Audio capture using MediaRecorder API
- WebRTC implementation for real-time communication
- Multi-language support with appropriate language codes
- Secure token management with ephemeral keys
- Error handling and reliability features

The system uses the browser's MediaRecorder API to capture audio from the user's microphone, creates a stream of audio data that's collected in chunks and later combined into a single audio blob. For real-time conversation, the application establishes a WebRTC connection with peer connection to OpenAI's servers, data channel for control messages and text responses, and audio track handling for the AI's voice responses.

Browser Compatibility:
- Chrome 55+
- Firefox 44+
- Safari 11+
- Edge 79+

For older browsers, the application implements a fallback to a text-only interface.
"""
    },
    "authentication": {
        "title": "Authentication System",
        "keywords": ["auth", "login", "signup", "register", "jwt", "google", "oauth", "password", "security", "token"],
        "content": """
The Language Tutor application implements a comprehensive authentication system that supports multiple authentication methods, secure session management, and role-based access control.

Authentication Methods:
- JWT-based Authentication: Primary authentication method using JSON Web Tokens
- Google OAuth Integration: Social login option for streamlined user experience
- Password Reset Flow: Secure password recovery mechanism
- Guest Access System: Limited functionality for unauthenticated users

Security Features:
- Password hashing with bcrypt
- JWT token authentication with expiration
- HTTPS enforcement in production
- Environment variable protection for sensitive data
- Rate limiting for sensitive endpoints

The login process validates user credentials, generates a JWT token, updates the last login timestamp, and returns the token with basic user information. Google OAuth flow verifies the token with Google's authentication service, creates a new user or updates an existing one, automatically marks Google-authenticated users as verified, and issues a JWT token for the authenticated session.

Password reset includes secure token generation, 1-hour token expiration, email delivery of reset links, and secure password update process.
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
    "learning_features": {
        "title": "Learning Features and Assessment",
        "keywords": ["learning", "assessment", "cefr", "levels", "pronunciation", "grammar", "vocabulary", "fluency", "feedback"],
        "content": """
Language Tutor provides comprehensive language learning features with AI-powered assessment and personalized feedback.

Assessment System:
- CEFR Level Evaluation: Determines user level from A1 (beginner) to C2 (native-like)
- Speaking Assessment: 15-60 second recordings analyzed for multiple skills
- Real-time Feedback: Immediate corrections and suggestions during conversations
- Pronunciation Analysis: Detailed feedback on pronunciation accuracy
- Grammar Evaluation: Assessment of grammatical structures and usage
- Vocabulary Assessment: Analysis of vocabulary range and appropriateness
- Fluency Measurement: Evaluation of speaking pace and hesitation patterns
- Coherence Analysis: Assessment of logical flow and organization

Skill Scoring:
Each skill is scored on a 0-100 scale with detailed feedback:
- Pronunciation: Accuracy of sounds, stress, and intonation
- Grammar: Correct use of tenses, structures, and syntax
- Vocabulary: Range, accuracy, and appropriateness of word choice
- Fluency: Natural pace, minimal hesitation, smooth delivery
- Coherence: Logical organization and clear communication

Learning Levels:
- A1 (Beginner): Basic phrases and simple interactions
- A2 (Elementary): Simple conversations on familiar topics
- B1 (Intermediate): Clear communication on familiar subjects
- B2 (Upper-Intermediate): Complex topics and abstract concepts
- C1 (Advanced): Fluent and spontaneous expression
- C2 (Proficiency): Native-like fluency and precision

Personalized Learning:
- Custom learning plans based on assessment results
- Adaptive difficulty based on user performance
- Targeted practice for specific skill areas
- Progress tracking with detailed analytics
- Achievement system to motivate continued learning

Conversation Topics:
- Travel & Tourism
- Food & Cooking
- Hobbies & Interests
- Culture & Traditions
- Movies & TV Shows
- Music and Entertainment
- Technology and Innovation
- Environment & Nature
- Custom topics based on user interests

The system provides immediate feedback during conversations, helping users improve in real-time while maintaining natural conversation flow.
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
        
        # Add specific topic scoring
        if any(topic in query_lower for topic in ["speech", "voice", "audio", "recording"]):
            if chunk_id == "speech_recognition":
                score += 15
        
        if any(topic in query_lower for topic in ["auth", "login", "signup", "password"]):
            if chunk_id == "authentication":
                score += 15
        
        if any(topic in query_lower for topic in ["guest", "trial", "free", "limitation"]):
            if chunk_id == "guest_experience":
                score += 15
        
        if any(topic in query_lower for topic in ["progress", "tracking", "history", "achievement"]):
            if chunk_id == "progress_tracking":
                score += 15
        
        if any(topic in query_lower for topic in ["mobile", "ios", "android", "phone"]):
            if chunk_id == "mobile_support":
                score += 15
        
        if any(topic in query_lower for topic in ["assessment", "cefr", "level", "pronunciation", "grammar"]):
            if chunk_id == "learning_features":
                score += 15
        
        if any(topic in query_lower for topic in ["frontend", "react", "nextjs", "component"]):
            if chunk_id == "frontend_architecture":
                score += 15
        
        if any(topic in query_lower for topic in ["backend", "api", "fastapi", "python", "mongodb"]):
            if chunk_id == "backend_architecture":
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
        
        # Create system prompt for GPT-4o-mini
        system_prompt = """You are a helpful assistant for the Language Tutor application. Answer user questions based on the provided documentation context. 

Guidelines:
- Use the provided context to answer questions accurately
- Be conversational and helpful
- If the context doesn't contain enough information, say so politely
- Focus on practical, actionable information
- Use emojis sparingly but appropriately
- Keep responses concise but informative
- Mention specific features, benefits, and technical details when relevant

Context from Language Tutor documentation:
"""

        # Generate response using GPT-4o-mini
        response = client.chat.completions.create(
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
