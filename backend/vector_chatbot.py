import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai_client import get_async_openai
from sklearn.metrics.pairwise import cosine_similarity
import pickle

router = APIRouter(prefix="/api/chat", tags=["chat"])

class VectorChatRequest(BaseModel):
    query: str

class VectorChatResponse(BaseModel):
    response: str
    sources: List[str] = []
    similarity_scores: List[float] = []

class VectorChatbot:
    def __init__(self):
        self.documents = []
        self.embeddings = []
        self.document_metadata = []
        
        # Handle file paths for different environments
        if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENVIRONMENT") == "production":
            # In production/Railway, use /tmp for writable files
            self.embeddings_file = "/tmp/chatbot_embeddings.pkl"
            self.documents_file = "/tmp/chatbot_documents.json"
        else:
            # In development, use relative paths
            self.embeddings_file = "chatbot_embeddings.pkl"
            self.documents_file = "chatbot_documents.json"
        
        # Load or create embeddings
        self.load_or_create_embeddings()
    
    def get_user_guides(self) -> List[Dict[str, Any]]:
        """Get all user guide documents"""
        return [
            {
                "id": "getting_started",
                "title": "How to Get Started with My Taco AI",
                "category": "Getting Started",
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
            {
                "id": "detailed_pricing_plans",
                "title": "Complete Pricing Plans & Subscription Details",
                "category": "Pricing & Subscriptions",
                "content": """
💰 COMPLETE PRICING GUIDE FOR MY TACO AI:

🆓 TRY & LEARN PLAN (FREE):
• Price: Completely FREE forever
• 3 practice sessions per month (5 minutes each)
• 1 speaking assessment per month
• 15-second assessment duration
• 1-minute conversation practice
• Basic language level detection
• Access to all 6 languages
• No account required for basic features
• Perfect for trying out the platform

📚 FLUENCY BUILDER PLAN:
• Monthly: $19.99/month
• Annual: $199.99/year (SAVE $39.89 - 17% OFF!)
• 30 practice sessions per month (5 minutes each)
• 2 speaking assessments per month
• 60-second assessment duration (4x longer than free)
• 5-minute conversation practice (5x longer than free)
• 7-DAY FREE TRIAL included
• Save unlimited conversation history
• Track learning progress and streaks
• Earn achievements and badges
• Detailed AI analysis and feedback
• Export learning data as PDF/CSV
• Email support
• Personalized learning plans
• Advanced conversation topics

🚀 TEAM MASTERY PLAN:
• Monthly: $39.99/month per user
• Annual: $399.99/year per user (SAVE $79.89 - 17% OFF!)
• UNLIMITED practice sessions
• UNLIMITED speaking assessments
• 60-second assessment duration
• 5-minute conversation practice
• 7-DAY FREE TRIAL included
• Everything in Fluency Builder PLUS:
• Team management dashboard
• Multiple user accounts (up to 5 users)
• Team progress tracking and analytics
• Bulk user management
• Dedicated account manager
• Custom branding options
• API access for integrations
• Priority customer support
• Advanced pronunciation analysis
• Grammar correction with explanations

💳 PAYMENT & BILLING:
• All major credit cards accepted
• PayPal supported
• Secure payment processing via Stripe
• Automatic billing with email receipts
• Update payment methods anytime
• Cancel anytime - no long-term contracts
• Pause subscription for up to 3 months
• Upgrade or downgrade plans instantly
• Prorated billing for plan changes

🎁 SPECIAL OFFERS:
• 7-day free trial for all paid plans
• Student discounts available (contact support)
• Corporate bulk pricing for 10+ users
• Seasonal promotions and discounts

📞 NEED HELP CHOOSING?
Contact our support team at hello@mytacoai.com or use the chat feature. We'll help you find the perfect plan for your language learning goals!
"""
            },
            {
                "id": "guest_vs_user_experience",
                "title": "Guest vs Registered User Experience Comparison",
                "category": "Account Features",
                "content": """
🔍 GUEST VS REGISTERED USER COMPARISON:

👤 GUEST USER EXPERIENCE (No Account Required):
• Assessment Duration: 15 seconds only
• Conversation Time: 1 minute maximum
• Session Limit: 3 assessments per browser session
• Progress Saving: None - resets when you close browser
• Learning Plans: Temporary only, lost after session
• Achievements: Not available
• Conversation History: Not saved
• Data Export: Not available
• Enhanced Analysis: Not available
• Streak Tracking: Not available
• Support: Community support only

✅ REGISTERED USER EXPERIENCE (Free Account):
• Assessment Duration: 60 seconds (4x longer!)
• Conversation Time: 5 minutes (5x longer!)
• Session Limit: No daily limits
• Progress Saving: Permanent across all devices
• Learning Plans: Saved permanently with progress tracking
• Achievements: 8 different achievements to earn
• Conversation History: Complete history with AI summaries
• Data Export: Full data export in PDF/CSV/ZIP formats
• Enhanced Analysis: 6-tab detailed analysis system
• Streak Tracking: Daily practice streaks with rewards
• Support: Email support included

🎯 WHY CREATE AN ACCOUNT?
• 4x longer assessments for better accuracy
• 5x longer conversations for meaningful practice
• Permanent progress tracking across devices
• AI-generated learning plans that adapt to your progress
• Detailed conversation analysis with insights
• Achievement system to motivate learning
• Complete conversation history with searchable summaries
• Professional data export for sharing with teachers
• Streak tracking to build consistent habits

🔄 GUEST-TO-USER TRANSITION:
• Any learning plans created as guest are automatically saved when you sign up
• Assessment results transfer to your new account
• Seamless transition - no data lost
• Immediate access to all premium features

📱 CROSS-DEVICE SYNC:
• Registered users: Full sync across phone, tablet, computer
• Guest users: Data only available on current browser session

🚀 GETTING STARTED:
• Try as guest first to see if you like the platform
• Sign up for free when ready for full features
• Upgrade to paid plans for unlimited practice and advanced features
"""
            },
            {
                "id": "enhanced_analysis_system",
                "title": "Enhanced AI Analysis System - Complete Guide",
                "category": "Advanced Features",
                "content": """
🧠 ENHANCED AI ANALYSIS SYSTEM - YOUR PERSONAL LANGUAGE COACH:

📊 WHAT IS ENHANCED ANALYSIS?
The Enhanced Analysis System is our advanced AI-powered feature that provides comprehensive insights into your conversation sessions. It goes beyond basic summaries to deliver actionable feedback that helps accelerate your language learning.

🎯 WHEN DO YOU GET ENHANCED ANALYSIS?
• Available for registered users only
• Automatically generated for conversations 5+ minutes long
• Also available for shorter conversations with 15+ messages
• Appears as "Enhanced Analysis Available" badge in your conversation history

📋 THE 6-TAB ANALYSIS INTERFACE:

1️⃣ CONVERSATION TAB:
• Complete conversation transcript
• Chat-style message display with timestamps
• Easy-to-read format for reviewing your practice

2️⃣ OVERVIEW TAB:
• Quick summary of key metrics
• Session highlights and achievements
• Overall performance snapshot
• Time spent and message count

3️⃣ QUALITY METRICS TAB:
• Engagement Score: How actively you participated
• Topic Depth Score: How thoroughly you explored topics
• Word Count Analysis: Measures expression depth
• Question Frequency: Tracks curiosity and interaction
• Elaboration Rate: Evaluates detail quality

4️⃣ PROGRESS TAB:
• Learning advancement indicators
• Complexity growth analysis over time
• Skill development tracking
• Improvement pattern recognition
• Confidence building metrics

5️⃣ AI INSIGHTS TAB:
• Breakthrough Moments: Significant learning achievements
• Struggle Points: Areas needing attention
• Confidence Level Assessment
• Pattern Recognition in your learning
• Personalized observations from AI

6️⃣ RECOMMENDATIONS TAB:
• Immediate Actions: What to practice next session
• Weekly Focus Areas: Medium-term learning goals
• Long-term Objectives: Strategic language development
• Specific exercises and activities
• Conversation topics for improvement

🎯 SAMPLE INSIGHTS YOU'LL RECEIVE:
• "Successfully used complex conditional sentences"
• "Demonstrated improved pronunciation of difficult sounds"
• "Showed increased confidence in expressing opinions"
• "Could benefit from more varied vocabulary in travel topics"
• "Excellent progress in using past perfect tense"

📈 HOW TO ACCESS:
• Complete a 5+ minute conversation
• Go to your Profile page
• Look for "Enhanced Analysis Available" badge
• Click "View Analysis" to open the detailed modal
• Navigate through all 6 tabs for complete insights

🚀 BENEFITS:
• Identify your learning breakthroughs
• Understand exactly what to practice next
• Track your improvement over time
• Get personalized AI coaching
• Accelerate your language learning journey
"""
            },
            {
                "id": "languages_and_levels",
                "title": "Complete Languages & CEFR Levels Guide",
                "category": "Languages & Levels",
                "content": """
🌍 COMPLETE LANGUAGES & LEVELS GUIDE:

🗣️ SUPPORTED LANGUAGES:
• English 🇺🇸 - American English with cultural context
• Dutch 🇳🇱 - Netherlands Dutch with cultural nuances
• Spanish 🇪🇸 - International Spanish with regional variations
• French 🇫🇷 - Standard French with cultural elements
• German 🇩🇪 - High German with cultural context
• Portuguese 🇵🇹 - International Portuguese (Brazilian & European)

📊 CEFR LEVELS EXPLAINED:

🟢 A1 - BEGINNER:
• Can understand and use familiar everyday expressions
• Can introduce themselves and ask basic questions
• Can interact simply if the other person speaks slowly
• Vocabulary: 500-1000 words
• Grammar: Present tense, basic sentence structures
• Topics: Greetings, numbers, colors, family, daily routines

🟡 A2 - ELEMENTARY:
• Can communicate in simple routine tasks
• Can describe background, immediate environment
• Can handle simple exchanges of information
• Vocabulary: 1000-2000 words
• Grammar: Past tense, future with "going to", modal verbs
• Topics: Shopping, work, travel basics, personal history

🔵 B1 - INTERMEDIATE:
• Can deal with most travel situations
• Can describe experiences, events, dreams, hopes
• Can give brief explanations for opinions and plans
• Vocabulary: 2000-3000 words
• Grammar: All tenses, conditional sentences, passive voice
• Topics: Current events, hobbies, work, detailed travel

🟣 B2 - UPPER INTERMEDIATE:
• Can interact with fluency and spontaneity
• Can understand main ideas of complex texts
• Can produce detailed text on wide range of subjects
• Vocabulary: 3000-4000 words
• Grammar: Complex structures, subjunctive, advanced tenses
• Topics: Abstract concepts, professional discussions, culture

🔴 C1 - ADVANCED:
• Can express ideas fluently and spontaneously
• Can use language flexibly for social, academic, professional purposes
• Can produce well-structured, detailed text
• Vocabulary: 4000-8000 words
• Grammar: All structures with precision and style
• Topics: Academic subjects, professional specialization, literature

⚫ C2 - PROFICIENCY:
• Can understand virtually everything heard or read
• Can express themselves with precision in complex situations
• Near-native level fluency and accuracy
• Vocabulary: 8000+ words
• Grammar: Native-like precision and style
• Topics: Any subject with native-like competence

🎯 HOW LEVELS AFFECT YOUR EXPERIENCE:
• Conversation complexity adapts to your level
• Vocabulary and grammar appropriate for your stage
• Cultural context increases with higher levels
• Topics become more sophisticated as you advance
• AI tutor adjusts speaking speed and complexity

📈 LEVEL PROGRESSION:
• Take regular assessments to track improvement
• Conversations automatically adapt as you improve
• Learning plans adjust to your advancing level
• Achievement system recognizes level progression

🌟 CULTURAL ELEMENTS BY LANGUAGE:
• English: American customs, idioms, business culture
• Dutch: Gezelligheid, directness, cycling culture
• Spanish: Family values, festivals, regional variations
• French: Cuisine, art, formal/informal registers
• German: Efficiency, precision, regional dialects
• Portuguese: Music, festivals, Brazilian vs European differences
"""
            },
            {
                "id": "technical_troubleshooting",
                "title": "Technical Requirements & Troubleshooting Guide",
                "category": "Technical Support",
                "content": """
🔧 TECHNICAL REQUIREMENTS & TROUBLESHOOTING:

💻 SYSTEM REQUIREMENTS:

🌐 BROWSER COMPATIBILITY:
• Chrome 55+ (Recommended)
• Safari 11+ (iOS/macOS)
• Firefox 44+ (Limited support)
• Edge 79+ (Good support)
• Mobile browsers supported on iOS 11+ and Android 7+

🎤 MICROPHONE REQUIREMENTS:
• Built-in microphone: Adequate for basic use
• Headset microphone: Recommended for best quality
• USB microphone: Excellent for professional quality
• Bluetooth headphones: Good quality, may have slight delay

📱 DEVICE COMPATIBILITY:
• Desktop/Laptop: Full feature support
• Tablets: Full feature support
• Smartphones: Optimized mobile interface
• Minimum RAM: 2GB recommended
• Stable internet: 1 Mbps minimum for voice features

🚨 COMMON ISSUES & SOLUTIONS:

🎤 MICROPHONE PROBLEMS:
Problem: "Microphone not detected"
Solutions:
• Check browser permissions (click lock icon in address bar)
• Restart browser and try again
• Check system microphone settings
• Try different browser
• Ensure microphone is not used by other apps

Problem: "Poor audio quality"
Solutions:
• Use headphones or external microphone
• Find quieter environment
• Check microphone positioning (6-8 inches from mouth)
• Close other audio applications
• Test microphone in other apps first

🌐 CONNECTION ISSUES:
Problem: "Session keeps disconnecting"
Solutions:
• Check internet connection stability
• Try different WiFi network
• Close bandwidth-heavy applications
• Refresh page and restart session
• Contact support if problem persists

Problem: "Slow loading or lag"
Solutions:
• Clear browser cache and cookies
• Close unnecessary browser tabs
• Restart browser
• Check available device memory
• Try incognito/private browsing mode

📱 MOBILE-SPECIFIC ISSUES:
Problem: "App not working on mobile"
Solutions:
• Update to latest browser version
• Enable JavaScript in browser settings
• Clear mobile browser cache
• Try landscape orientation
• Ensure sufficient battery level

Problem: "Touch controls not responsive"
Solutions:
• Clean screen for better touch sensitivity
• Try different finger/stylus
• Check if screen protector interferes
• Restart device if needed

🔊 AUDIO PLAYBACK ISSUES:
Problem: "Can't hear AI tutor responses"
Solutions:
• Check device volume settings
• Ensure browser has audio permissions
• Try headphones to test audio output
• Check if other apps are using audio
• Restart browser/device

⚡ PERFORMANCE OPTIMIZATION:
• Close unnecessary browser tabs
• Disable browser extensions temporarily
• Use latest browser version
• Ensure adequate device storage
• Use WiFi instead of mobile data when possible

🆘 WHEN TO CONTACT SUPPORT:
• Persistent microphone issues after trying solutions
• Repeated session disconnections
• Payment or subscription problems
• Account access issues
• Feature not working as described

📧 SUPPORT CONTACT:
• Email: hello@mytacoai.com
• Include: Device type, browser version, error description
• Response time: Within 24 hours
• Live chat available during business hours
"""
            },
            {
                "id": "business_policies",
                "title": "Business Policies & Account Management",
                "category": "Policies & Management",
                "content": """
📋 BUSINESS POLICIES & ACCOUNT MANAGEMENT:

💳 SUBSCRIPTION MANAGEMENT:

🔄 BILLING CYCLES:
• Monthly plans: Billed every 30 days from signup date
• Annual plans: Billed every 365 days from signup date
• Free trial: 7 days before first charge
• Prorated billing: Immediate adjustment when changing plans
• Payment date: Same day each month/year as original signup

💰 PRICING CHANGES:
• Current subscribers: 30-day notice for any price increases
• Grandfathered pricing: Existing users keep current rates
• New features: May be added to plans without price increase
• Promotional pricing: Limited time offers clearly marked

🚫 CANCELLATION POLICY:
• Cancel anytime: No cancellation fees
• Immediate effect: Access continues until end of billing period
• Data retention: Account data kept for 90 days after cancellation
• Reactivation: Easy reactivation within 90 days
• Refund policy: Pro-rated refunds for annual plans (see below)

💸 REFUND POLICY:
• Free trial: Cancel during trial for no charge
• Monthly plans: No refunds (cancel to avoid next charge)
• Annual plans: Pro-rated refund for unused months
• Refund processing: 5-10 business days to original payment method
• Dispute resolution: Contact support for billing issues

📊 DATA RETENTION & PRIVACY:

🗄️ ACTIVE ACCOUNTS:
• Conversation history: Stored indefinitely while account active
• Learning plans: Preserved permanently
• Progress data: Maintained for progress tracking
• Assessment results: Kept for level progression analysis

🗑️ CANCELLED ACCOUNTS:
• Grace period: 90 days to reactivate with full data
• Data deletion: Automatic deletion after 90 days
• Export option: Download all data before cancellation
• Anonymization: Personal identifiers removed, learning data may be kept for research

🔒 PRIVACY PROTECTION:
• Conversation encryption: All conversations encrypted in transit and at rest
• No data sharing: Conversations never shared with third parties
• GDPR compliant: Full data portability and deletion rights
• Secure storage: Enterprise-grade security measures

👤 ACCOUNT MANAGEMENT:

🔐 ACCOUNT SECURITY:
• Password requirements: Minimum 8 characters, mixed case recommended
• Two-factor authentication: Available for enhanced security
• Login monitoring: Unusual activity alerts
• Session management: Automatic logout after inactivity

📧 COMMUNICATION PREFERENCES:
• Marketing emails: Opt-in/opt-out available
• Product updates: Important updates sent to all users
• Support communications: Related to your account and usage
• Frequency control: Manage email frequency in settings

🏢 BUSINESS ACCOUNTS:

👥 TEAM PLANS:
• Minimum users: 5 users for team pricing
• Admin controls: Centralized user management
• Billing consolidation: Single invoice for all users
• Usage analytics: Team-wide progress reporting

🏛️ ENTERPRISE SOLUTIONS:
• Custom pricing: Volume discounts for 50+ users
• SSO integration: Single sign-on with corporate systems
• Custom features: Tailored functionality for large organizations
• Dedicated support: Priority support with dedicated account manager

⚖️ TERMS OF SERVICE:

✅ ACCEPTABLE USE:
• Educational purpose: Platform designed for language learning
• Personal use: Individual accounts for personal learning
• Respectful interaction: Appropriate language in all communications
• No abuse: Prohibited to abuse or exploit platform features

🚫 PROHIBITED ACTIVITIES:
• Account sharing: Each account for individual use only
• Automated access: No bots or automated systems
• Reverse engineering: No attempts to copy or replicate technology
• Harassment: No inappropriate or offensive content

📞 SUPPORT & CONTACT:
• Email support: hello@mytacoai.com
• Response time: 24 hours for general inquiries, 4 hours for billing issues
• Live chat: Available during business hours (9 AM - 6 PM EST)
• Knowledge base: Comprehensive self-help resources available
"""
            },
            {
                "id": "assessment_guide",
                "title": "How to Take Your Speaking Assessment",
                "category": "Assessment",
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
            {
                "id": "practice_guide",
                "title": "How to Practice Conversations",
                "category": "Practice",
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
            {
                "id": "save_progress_guide",
                "title": "How to Save Your Progress",
                "category": "Progress Tracking",
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
            {
                "id": "account_help",
                "title": "Account & Login Help",
                "category": "Account Management",
                "content": """
🔐 Complete Account & Login Help Guide:

🆕 CREATING AN ACCOUNT:
• Click "Sign Up" in the top right corner
• Enter your name, email, and password
• Or use "Continue with Google" for quick signup
• Check your email and click the verification link
• Your account is now ready to use!

🔑 SIGNING IN:
• Click "Login" and enter your email and password
• Use Google Sign-In if you registered with Google
• Check "Remember me" to stay logged in longer
• You'll be redirected to your dashboard

🔄 FORGOT YOUR PASSWORD?
• Click "Forgot Password?" on the login page
• Enter your email address
• Check your email for a reset link (check spam folder too)
• Click the link and create a new password
• Use your new password to log in

⭐ ACCOUNT BENEFITS:
• 60-second assessments (vs 15 seconds for guests)
• 5-minute conversations (vs 1 minute for guests)
• Save unlimited conversation history
• Track your learning progress and streaks
• Earn achievements and badges
• Export your learning data as PDF/CSV
• Access to detailed AI analysis

👤 PROFILE MANAGEMENT:
• Update your name and email in account settings
• Change your preferred language and level
• View your learning statistics and achievements
• Download your conversation history
• Manage notification preferences

🚨 TROUBLESHOOTING LOGIN ISSUES:
• Clear your browser cache and cookies
• Make sure cookies are enabled in your browser
• Try logging in using incognito/private mode
• Disable browser extensions temporarily
• Check if your email/password is correct
• Try resetting your password if needed

🔒 ACCOUNT SECURITY:
• Use a strong, unique password
• Enable two-factor authentication if available
• Log out from shared computers
• Keep your email address updated
• Report any suspicious activity immediately

📧 CONTACT SUPPORT:
If you're still having trouble, contact our support team at hello@mytacoai.com with:
• Your email address
• Description of the problem
• Screenshots if helpful
• Browser and device information
"""
            },
            {
                "id": "mobile_tips",
                "title": "Mobile Usage Tips",
                "category": "Mobile Support",
                "content": """
📱 Complete Mobile Usage Guide:

📱 MOBILE SETUP:
• My Taco AI works great on mobile devices!
• Works on iPhone (Safari) and Android (Chrome)
• Allow microphone permission when prompted
• Use headphones or earbuds for better audio quality
• Find a quiet space for recording

🎤 VOICE TIPS FOR MOBILE:
• Speak clearly and at normal volume
• Hold your phone 6-8 inches from your mouth
• Turn off other apps that might use the microphone
• Make sure you have a stable internet connection
• Use WiFi when possible for better quality

💡 MOBILE BEST PRACTICES:
• Landscape mode works best for conversations
• Make sure your battery is charged
• Close unnecessary apps to free up memory
• Turn off notifications during practice sessions
• Keep your phone steady while speaking

🚨 MOBILE TROUBLESHOOTING:
• If microphone doesn't work, refresh the page
• Grant microphone permission in browser settings
• Try closing other apps and restarting your browser
• Check if your microphone is working in other apps
• Restart your phone if problems persist

🌐 BROWSER COMPATIBILITY:
• iOS Safari 11+ (recommended)
• Android Chrome 55+ (recommended)
• Mobile Firefox 44+ (limited support)
• Edge Mobile 79+ (good support)

⚡ PERFORMANCE TIPS:
• Use the latest version of your browser
• Clear browser cache regularly
• Ensure you have enough storage space
• Close background apps to free up RAM
• Use a stable WiFi connection when possible

📐 INTERFACE TIPS:
• Tap and hold to see button descriptions
• Swipe to navigate between sections
• Use pinch-to-zoom if text is too small
• Rotate to landscape for better conversation view
• Enable auto-rotate for optimal experience

🔋 BATTERY OPTIMIZATION:
• Lower screen brightness to save battery
• Close unused browser tabs
• Turn off location services if not needed
• Use airplane mode + WiFi for better battery life
• Keep your device plugged in during long sessions

Having specific mobile issues? Try these steps or contact support!
"""
            },
            {
                "id": "export_data_guide",
                "title": "How to Export Your Learning Data",
                "category": "Data Export",
                "content": """
📊 Complete Data Export Guide:

📥 HOW TO EXPORT YOUR DATA:
• Go to your "Overview" or "Profile" section
• Look for "Export Data" or "Download Report" button
• Choose your preferred format (PDF, CSV, or ZIP)
• Click download and save the file to your device
• Files will download to your default download folder

📄 AVAILABLE EXPORT FORMATS:

🔸 PDF REPORTS:
• Professional conversation history report
• Learning plans and assessment report
• Includes your profile, statistics, and progress charts
• Perfect for sharing with teachers or language schools
• Formatted for printing and professional presentation

🔸 CSV FILES:
• Spreadsheet format for detailed data analysis
• Conversation history with dates, topics, and scores
• Learning plan data with goals and completion rates
• Easy to open in Excel, Google Sheets, or Numbers
• Great for creating your own charts and analysis

🔸 ZIP PACKAGE:
• Complete data export with all formats included
• Includes PDFs, CSVs, and raw JSON data
• Perfect for complete backup of your learning journey
• Contains all your data in multiple formats

📊 WHAT'S INCLUDED IN YOUR EXPORT:

🔸 STUDENT PROFILE:
• Your name, email, and account information
• Report generation date and time
• Total practice sessions and time spent
• Current language levels and achievements

🔸 CONVERSATION HISTORY:
• All your practice sessions with dates and times
• Conversation topics and duration
• Message counts and AI analysis results
• Detailed feedback and corrections received

🔸 ASSESSMENT DATA:
• All your speaking assessment results over time
• Skill scores (pronunciation, grammar, vocabulary, fluency)
• CEFR level progression and improvements
• Detailed feedback for each assessment taken

🔸 LEARNING STATISTICS:
• Total practice time and session frequency
• Learning streaks and achievement progress
• Session patterns and improvement trends
• Progress charts and analytics

💡 WHEN TO EXPORT YOUR DATA:
• Before important meetings with language teachers
• To track your long-term learning progress
• For backup before switching devices
• To share achievements with employers or schools
• For personal motivation and progress review
• Before account changes or deletions

🎯 USING YOUR EXPORTED DATA:
• Share PDF reports with language instructors
• Analyze learning patterns in spreadsheet programs
• Keep permanent backups of your learning journey
• Track improvement over months and years
• Include in language learning portfolios
• Use for job applications requiring language skills

🔒 DATA PRIVACY & SECURITY:
• Only you can export your personal data
• Exports include only your own information
• Data is securely generated and encrypted
• No personal data is shared with third parties
• Downloads are temporary and automatically deleted

📱 MOBILE EXPORT:
• Export feature works on mobile devices
• Files download to your phone or tablet
• Share directly from mobile apps
• View PDFs on any device with a PDF reader
• Upload to cloud storage for easy access

Need help with exports? Contact support at hello@mytacoai.com!
"""
            },
            {
                "id": "pricing_plans",
                "title": "Pricing Plans & Subscription Options",
                "category": "Pricing & Plans",
                "content": """
💰 Complete Pricing Guide for My Taco AI:

🆓 FREE PLAN (Guest Access):
• 15-second speaking assessments
• 1-minute conversation practice sessions
• Basic language level detection
• Access to all 6 languages (English, Dutch, Spanish, French, German, Portuguese)
• No account required - start immediately
• Perfect for trying out the platform

📚 TRY & LEARN PLAN - $9.99/month:
✅ EVERYTHING IN FREE PLUS:
• 60-second speaking assessments (4x longer)
• 5-minute conversation practice sessions (5x longer)
• Save unlimited conversation history
• Track learning progress and streaks
• Earn achievements and badges
• Detailed AI analysis and feedback
• Export learning data as PDF/CSV
• Email support

🚀 FLUENCY BUILDER PLAN - $19.99/month:
✅ EVERYTHING IN TRY & LEARN PLUS:
• Personalized learning plans based on assessment
• Advanced conversation topics and scenarios
• Priority customer support
• Weekly progress reports
• Custom learning goals and milestones
• Advanced pronunciation analysis
• Grammar correction with explanations

👥 TEAM MASTERY PLAN - $39.99/month:
✅ EVERYTHING IN FLUENCY BUILDER PLUS:
• Team management dashboard
• Multiple user accounts (up to 5 users)
• Team progress tracking and analytics
• Bulk user management
• Dedicated account manager
• Custom branding options
• API access for integrations

💡 ANNUAL PRICING (Save 20%):
• Try & Learn: $95.90/year (save $23.98)
• Fluency Builder: $191.90/year (save $47.98)
• Team Mastery: $383.90/year (save $95.98)

🎯 WHICH PLAN IS RIGHT FOR YOU?

🔸 CHOOSE FREE if you want to:
• Try the platform before committing
• Practice occasionally
• Test basic features

🔸 CHOOSE TRY & LEARN if you want to:
• Practice regularly and track progress
• Save your conversation history
• Get detailed feedback and analysis
• Learn at your own pace

🔸 CHOOSE FLUENCY BUILDER if you want to:
• Follow a structured learning plan
• Get advanced feedback and corrections
• Achieve specific language goals
• Access premium features

🔸 CHOOSE TEAM MASTERY if you want to:
• Manage language learning for a team
• Track multiple users' progress
• Get dedicated support
• Integrate with other systems

🔄 SUBSCRIPTION MANAGEMENT:
• Cancel anytime - no long-term contracts
• Pause subscription for up to 3 months
• Upgrade or downgrade plans instantly
• Prorated billing for plan changes
• 7-day free trial for all paid plans

💳 PAYMENT OPTIONS:
• All major credit cards accepted
• PayPal supported
• Secure payment processing via Stripe
• Automatic billing with email receipts
• Update payment methods anytime

🎁 SPECIAL OFFERS:
• 7-day free trial for new subscribers
• Student discounts available (contact support)
• Corporate bulk pricing for 10+ users
• Seasonal promotions and discounts

📞 NEED HELP CHOOSING?
Contact our support team at hello@mytacoai.com or use the chat feature. We'll help you find the perfect plan for your language learning goals!

🚀 READY TO UPGRADE?
Click "Upgrade" in your profile or visit the pricing page to start your free trial today!
"""
            }
        ]
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts using OpenAI's embedding model"""
        if not client:
            print("OpenAI client not available, using dummy embeddings")
            return [[0.0] * 1536 for _ in texts]  # Dummy embeddings
        
        try:
            response = await get_async_openai().embeddings.create(
                model="text-embedding-3-small",  # Cheaper and faster than ada-002
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            print(f"Error creating embeddings: {e}")
            return [[0.0] * 1536 for _ in texts]  # Fallback to dummy embeddings
    
    def load_or_create_embeddings(self):
        """Load existing embeddings or create new ones"""
        # Check if embeddings file exists
        if os.path.exists(self.embeddings_file) and os.path.exists(self.documents_file):
            try:
                # Load existing embeddings
                with open(self.embeddings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.embeddings = data['embeddings']
                    self.document_metadata = data['metadata']
                
                # Load documents
                with open(self.documents_file, 'r') as f:
                    self.documents = json.load(f)
                
                print(f"Loaded {len(self.documents)} documents with embeddings")
                return
            except Exception as e:
                print(f"Error loading embeddings: {e}")
        
        # Create new embeddings
        print("Creating new embeddings...")
        user_guides = self.get_user_guides()
        
        # Prepare documents and metadata
        self.documents = []
        self.document_metadata = []
        
        for guide in user_guides:
            # Create searchable text combining title and content
            searchable_text = f"{guide['title']}\n\n{guide['content']}"
            self.documents.append(searchable_text)
            self.document_metadata.append({
                'id': guide['id'],
                'title': guide['title'],
                'category': guide['category']
            })
        
        # Create embeddings
        self.embeddings = self.create_embeddings(self.documents)
        
        # Save embeddings and documents
        try:
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump({
                    'embeddings': self.embeddings,
                    'metadata': self.document_metadata
                }, f)
            
            with open(self.documents_file, 'w') as f:
                json.dump(self.documents, f, indent=2)
            
            print(f"Created and saved embeddings for {len(self.documents)} documents")
        except Exception as e:
            print(f"Error saving embeddings: {e}")
    
    def search_similar_documents(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        if not self.embeddings:
            return []
        
        # Create embedding for the query
        query_embedding = self.create_embeddings([query])[0]
        
        # Calculate cosine similarity
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        
        # Get top-k most similar documents
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                results.append({
                    'content': self.documents[idx],
                    'metadata': self.document_metadata[idx],
                    'similarity': float(similarities[idx])
                })
        
        return results
    
    def generate_response(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Generate a response using GPT with the retrieved context"""
        if not client:
            return "I'm sorry, I'm having trouble processing your question right now. Please try again later."
        
        if not context_docs:
            return "I'm sorry, I couldn't find specific information about that. Please try asking about getting started, taking assessments, practicing conversations, saving progress, account help, mobile tips, or exporting data."
        
        # Prepare context
        context = "\n\n".join([
            f"## {doc['metadata']['title']}\n{doc['content']}"
            for doc in context_docs
        ])
        
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
        
        try:
            response = await get_async_openai().chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt + context},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm sorry, I'm having trouble processing your question right now. Please try again or ask about our main features."

# Initialize the vector chatbot
vector_chatbot = VectorChatbot()

@router.post("/vector-knowledge", response_model=VectorChatResponse)
async def get_vector_knowledge(request: VectorChatRequest):
    """
    Answer questions using vector similarity search and GPT
    """
    try:
        # 📝 COMPREHENSIVE LOGGING
        print("="*80)
        print(f"🤖 [CHATBOT] User Query Received")
        print(f"📝 Query: '{request.query}'")
        print(f"📝 Query Length: {len(request.query)} characters")
        print(f"📝 Timestamp: {__import__('datetime').datetime.now().isoformat()}")
        print("="*80)
        
        # Search for similar documents
        similar_docs = vector_chatbot.search_similar_documents(request.query, top_k=3)
        
        if not similar_docs:
            print(f"❌ [CHATBOT] No relevant documents found for query: '{request.query}'")
            return VectorChatResponse(
                response="I'm sorry, I couldn't find specific information about that. Please try asking about getting started, taking assessments, practicing conversations, saving progress, account help, mobile tips, or exporting data.",
                sources=[],
                similarity_scores=[]
            )
        
        # Log search results
        print(f"🔍 [CHATBOT] Found {len(similar_docs)} relevant documents:")
        for i, doc in enumerate(similar_docs, 1):
            title = doc['metadata']['title']
            similarity = doc['similarity']
            category = doc['metadata']['category']
            print(f"   {i}. {title} (similarity: {similarity:.3f}, category: {category})")
        
        # Generate response
        response_text = vector_chatbot.generate_response(request.query, similar_docs)
        
        # Extract sources and scores
        sources = [doc['metadata']['title'] for doc in similar_docs]
        scores = [doc['similarity'] for doc in similar_docs]
        
        # Log response generation
        print(f"✅ [CHATBOT] Response generated successfully")
        print(f"📊 Top similarity score: {scores[0]:.3f}")
        print(f"📚 Sources used: {', '.join(sources)}")
        print(f"📝 Response length: {len(response_text)} characters")
        print(f"🎯 Response preview: {response_text[:100]}...")
        print("="*80)
        
        return VectorChatResponse(
            response=response_text,
            sources=sources,
            similarity_scores=scores
        )
        
    except Exception as e:
        print(f"❌ [CHATBOT] Error processing query: '{request.query}'")
        print(f"❌ [CHATBOT] Error details: {str(e)}")
        import traceback
        print(f"❌ [CHATBOT] Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="Sorry, I'm having trouble processing your question right now. Please try again or ask about our main features."
        )
