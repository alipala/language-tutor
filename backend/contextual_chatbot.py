import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from openai_client import get_async_openai
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from auth import get_optional_current_user
from models import UserResponse
from database import database
from bson import ObjectId

# Import Redis caching helpers
from cache_helpers import get_taalcoach_context_cached, invalidate_taalcoach_context

router = APIRouter(prefix="/api/chat", tags=["contextual-chat"])


class ContextualChatRequest(BaseModel):
    query: str
    user_context: Optional[Dict[str, Any]] = None

class ContextualChatResponse(BaseModel):
    response: str
    sources: List[str] = []
    similarity_scores: List[float] = []
    user_context_used: bool = False
    personalized_suggestions: List[str] = []

class ContextualVectorChatbot:
    def __init__(self):
        self.documents = []
        self.embeddings = []
        self.document_metadata = []
        
        # Handle file paths for different environments
        if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENVIRONMENT") == "production":
            # In production/Railway, use /tmp for writable files
            self.embeddings_file = "/tmp/contextual_chatbot_embeddings.pkl"
            self.documents_file = "/tmp/contextual_chatbot_documents.json"
        else:
            # In development, use relative paths
            self.embeddings_file = "contextual_chatbot_embeddings.pkl"
            self.documents_file = "contextual_chatbot_documents.json"
        
        # Load embeddings from disk (sync). If file missing, stays empty until
        # async load_or_create_embeddings() is called explicitly.
        self._load_embeddings_from_disk()
    
    def get_user_guides(self) -> List[Dict[str, Any]]:
        """Get all user guide documents with enhanced contextual information"""
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
• Speak clearly for 30 seconds (guests) or 60 seconds (registered users)
• Talk about anything - describe your day, hobbies, or goals
• Our AI will tell you your level: A1 (beginner) to C2 (advanced)

💬 STEP 3: Start Your First Conversation
• After assessment, click "Start Conversation"
• Talk naturally with our AI tutor
• Discuss interesting topics like travel, food, or culture
• Get instant feedback and corrections
• Practice for 2 minutes (guests) or 5 minutes (registered users)

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
• 30-second assessment duration
• 2-minute conversation practice
• Basic language level detection
• Access to all 6 languages
• No account required for basic features
• Perfect for trying out the platform

📚 FLUENCY BUILDER PLAN:
• Monthly: $19.99/month
• Annual: $199.99/year (SAVE $39.89 - 17% OFF!)
• 30 practice sessions per month (5 minutes each)
• 2 speaking assessments per month
• 60-second assessment duration (2x longer than free)
• 5-minute conversation practice (2.5x longer than free)
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
• Assessment Duration: 30 seconds only
• Conversation Time: 2 minutes maximum
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
• Assessment Duration: 60 seconds (2x longer!)
• Conversation Time: 5 minutes (2.5x longer!)
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
• 2x longer assessments for better accuracy
• 2.5x longer conversations for meaningful practice
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
            }
        ]
    
    async def get_user_context(self, user: Optional[UserResponse]) -> Dict[str, Any]:
        """
        Get comprehensive user context for personalized responses

        NOW WITH REDIS CACHING! 🚀
        - Guest users: No caching (context is simple)
        - Registered users: 5-minute cache (reduces MongoDB load by 90%)
        """
        if not user:
            return {
                "user_type": "guest",
                "subscription_plan": "guest",
                "features_available": ["30s assessments", "2min conversations", "basic features"],
                "limitations": ["No progress saving", "Limited session time", "No advanced features"]
            }

        try:
            # 🚀 REDIS CACHING: Try to get context from cache first
            cached_context = await get_taalcoach_context_cached(user.id)
            if cached_context:
                print(f"✅ [TAALCOACH] Using cached user context for {user.id}")
                return cached_context

            # Cache miss - build context from MongoDB (fallback)
            print(f"❌ [TAALCOACH] Cache miss, building context from MongoDB for {user.id}")

            # Get user's subscription status
            user_doc = await database["users"].find_one({"_id": ObjectId(user.id)})
            if not user_doc:
                return {"user_type": "registered", "subscription_plan": "try_learn"}

            # Get learning plans
            learning_plans = await database["learning_plans"].find({"user_id": user.id}).to_list(length=10)

            # Get conversation history
            conversations = await database["conversation_sessions"].find({"user_id": user.id}).to_list(length=5)

            # Get progress stats
            total_sessions = len(conversations)
            total_minutes = sum(session.get('duration_minutes', 0) for session in conversations)

            # Calculate current streak (simplified)
            current_streak = 0  # Would implement proper streak calculation

            context = {
                "user_type": "registered",
                "subscription_plan": user_doc.get("subscription_plan", "try_learn"),
                "subscription_status": user_doc.get("subscription_status", "active"),
                "is_in_trial": user_doc.get("is_in_trial", False),
                "learning_plans_count": len(learning_plans),
                "total_sessions": total_sessions,
                "total_minutes": total_minutes,
                "current_streak": current_streak,
                "preferred_language": user_doc.get("preferred_language"),
                "preferred_level": user_doc.get("preferred_level"),
                "recent_languages": list(set([conv.get('language') for conv in conversations if conv.get('language')])),
                "usage_this_month": {
                    "sessions_used": user_doc.get("practice_sessions_used", 0),
                    "assessments_used": user_doc.get("assessments_used", 0)
                }
            }

            # Note: This context is NOT automatically cached here
            # It will be cached in get_taalcoach_context_cached() helper
            # which is called at the start of this function

            return context

        except Exception as e:
            print(f"Error getting user context: {e}")
            return {"user_type": "registered", "subscription_plan": "try_learn"}
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts using OpenAI's embedding model"""
        try:
            response = await get_async_openai().embeddings.create(
                model="text-embedding-3-small",  # Cheaper and faster than ada-002
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            print(f"Error creating embeddings: {e}")
            return [[0.0] * 1536 for _ in texts]  # Fallback to dummy embeddings
    
    def _load_embeddings_from_disk(self):
        """Sync: load embeddings from disk only. Called from __init__."""
        if os.path.exists(self.embeddings_file) and os.path.exists(self.documents_file):
            try:
                with open(self.embeddings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.embeddings = data['embeddings']
                    self.document_metadata = data['metadata']
                with open(self.documents_file, 'r') as f:
                    self.documents = json.load(f)
                print(f"Loaded {len(self.documents)} contextual documents with embeddings")
            except Exception as e:
                print(f"Error loading contextual embeddings from disk: {e}")

    async def load_or_create_embeddings(self):
        """Async: load from disk or create via OpenAI if file missing."""
        if os.path.exists(self.embeddings_file) and os.path.exists(self.documents_file):
            try:
                with open(self.embeddings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.embeddings = data['embeddings']
                    self.document_metadata = data['metadata']
                with open(self.documents_file, 'r') as f:
                    self.documents = json.load(f)
                print(f"Loaded {len(self.documents)} contextual documents with embeddings")
                return
            except Exception as e:
                print(f"Error loading contextual embeddings: {e}")
        
        # Create new embeddings
        print("Creating new contextual embeddings...")
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
        self.embeddings = await self.create_embeddings(self.documents)
        
        # Save embeddings and documents
        try:
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump({
                    'embeddings': self.embeddings,
                    'metadata': self.document_metadata
                }, f)
            
            with open(self.documents_file, 'w') as f:
                json.dump(self.documents, f, indent=2)
            
            print(f"Created and saved contextual embeddings for {len(self.documents)} documents")
        except Exception as e:
            print(f"Error saving contextual embeddings: {e}")
    
    async def search_similar_documents(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        if not self.embeddings:
            return []
        
        # Create embedding for the query
        query_embedding = (await self.create_embeddings([query]))[0]
        
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
    
    def generate_personalized_suggestions(self, user_context: Dict[str, Any], query: str) -> List[str]:
        """Generate personalized suggestions based on user context"""
        suggestions = []
        
        print(f"🎯 [SUGGESTIONS] Generating suggestions for user context: {user_context}")
        
        if user_context.get("user_type") == "guest":
            suggestions.extend([
                "🎯 Sign up for free to get 2x longer assessments and 2.5x longer conversations!",
                "📊 Create an account to save your progress and track improvement",
                "🏆 Register to unlock achievements and learning streaks"
            ])
        else:
            # For registered users
            plan = user_context.get("subscription_plan", "try_learn")
            total_sessions = user_context.get("total_sessions", 0)
            current_streak = user_context.get("current_streak", 0)
            sessions_used = user_context.get("usage_this_month", {}).get("sessions_used", 0)
            
            print(f"🎯 [SUGGESTIONS] Plan: {plan}, Sessions: {total_sessions}, Streak: {current_streak}, Used: {sessions_used}")
            
            # Plan-specific suggestions
            if plan == "try_learn":
                if total_sessions < 5:
                    suggestions.append("💬 Try practicing different conversation topics to expand your vocabulary")
                
                if current_streak == 0:
                    suggestions.append("🔥 Start a learning streak by practicing daily for just 5 minutes")
                
                if sessions_used >= 2:
                    suggestions.append("🚀 Consider upgrading to Fluency Builder for unlimited practice sessions")
            
            elif plan == "fluency_builder":
                if total_sessions < 10:
                    suggestions.append("📈 You're on Fluency Builder! Try to reach 10 total sessions for better progress tracking")
                
                if current_streak == 0:
                    suggestions.append("🔥 Start a daily practice streak to maximize your Fluency Builder benefits")
                
                if sessions_used < 10:
                    suggestions.append("💪 You have 30 sessions per month - practice more to get the most value from your plan")
                
                # Enhanced Analysis suggestion
                suggestions.append("🧠 Practice for 5+ minutes to unlock Enhanced Analysis with detailed feedback")
            
            elif plan == "team_mastery":
                suggestions.append("🚀 You have unlimited sessions! Practice as much as you want")
                suggestions.append("📊 Check your team dashboard for progress insights")
                suggestions.append("🎯 Use advanced features like custom branding and API access")
            
            # General suggestions for all registered users
            if total_sessions == 0:
                suggestions.append("🎤 Take your first speaking assessment to get started")
            
            if total_sessions > 0 and current_streak == 0:
                suggestions.append("📅 Practice daily to build a learning streak")
        
        # Language-specific suggestions
        if user_context.get("preferred_language"):
            lang = user_context["preferred_language"]
            suggestions.append(f"🌍 Continue practicing {lang.title()} to build consistency")
        
        # Level-specific suggestions
        if user_context.get("preferred_level"):
            level = user_context["preferred_level"]
            if level in ["A1", "A2"]:
                suggestions.append("📚 Focus on basic vocabulary and everyday conversations")
            elif level in ["B1", "B2"]:
                suggestions.append("🎯 Challenge yourself with more complex topics and grammar")
            elif level in ["C1", "C2"]:
                suggestions.append("⭐ Practice advanced topics and cultural nuances")
        
        # Learning plans suggestions
        learning_plans_count = user_context.get("learning_plans_count", 0)
        if learning_plans_count == 0:
            suggestions.append("📋 Create a personalized learning plan to track your progress")
        elif learning_plans_count > 0:
            suggestions.append("📚 Follow your learning plan objectives for structured progress")
        
        print(f"🎯 [SUGGESTIONS] Generated {len(suggestions)} suggestions: {suggestions}")
        return suggestions[:3]  # Return top 3 suggestions
    
    async def generate_contextual_response(self, query: str, context_docs: List[Dict[str, Any]], user_context: Dict[str, Any]) -> str:
        """Generate a contextual response using GPT with user context"""
        if not context_docs:
            return "I'm sorry, I couldn't find specific information about that. Please try asking about getting started, pricing, features, or technical support."
        
        # Prepare context
        context = "\n\n".join([
            f"## {doc['metadata']['title']}\n{doc['content']}"
            for doc in context_docs
        ])
        
        # Prepare user context for the prompt
        user_info = ""
        if user_context.get("user_type") == "guest":
            user_info = "User is a GUEST (not logged in) with limited features: 30s assessments, 2min conversations, no progress saving."
        else:
            plan = user_context.get("subscription_plan", "try_learn")
            sessions = user_context.get("total_sessions", 0)
            minutes = user_context.get("total_minutes", 0)
            streak = user_context.get("current_streak", 0)
            
            user_info = f"""User is REGISTERED with {plan} plan. 
            Progress: {sessions} sessions, {minutes:.1f} minutes practiced, {streak}-day streak.
            Usage this month: {user_context.get('usage_this_month', {}).get('sessions_used', 0)} sessions used.
            Preferred language: {user_context.get('preferred_language', 'not set')}.
            Preferred level: {user_context.get('preferred_level', 'not set')}."""
        
        system_prompt = f"""You are a friendly and helpful assistant for My Taco AI language learning app. Your goal is to help users who feel stuck, confused, or need guidance on how to use the app effectively.

IMPORTANT: Personalize your response based on the user's context below.

User Context: {user_info}

Guidelines:
- Be warm, encouraging, and supportive
- Personalize responses based on user's subscription plan, progress, and preferences
- For guests: Encourage account creation and highlight benefits
- For registered users: Reference their progress and suggest next steps
- For free plan users: Mention upgrade benefits when relevant
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
                max_tokens=600
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating contextual response: {e}")
            return "I'm sorry, I'm having trouble processing your question right now. Please try again or ask about our main features."

# Initialize the contextual vector chatbot
contextual_vector_chatbot = ContextualVectorChatbot()

@router.post("/contextual-knowledge", response_model=ContextualChatResponse)
async def get_contextual_knowledge(
    request: ContextualChatRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user)
):
    """
    Answer questions using vector similarity search and GPT with user context awareness
    """
    try:
        # 📝 COMPREHENSIVE LOGGING
        print("="*80)
        print(f"🤖 [CONTEXTUAL-CHATBOT] User Query Received")
        print(f"📝 Query: '{request.query}'")
        print(f"👤 User: {current_user.email if current_user else 'Guest'}")
        print(f"📝 Query Length: {len(request.query)} characters")
        print(f"📝 Timestamp: {__import__('datetime').datetime.now().isoformat()}")
        print("="*80)
        
        # Get user context
        user_context = await contextual_vector_chatbot.get_user_context(current_user)
        print(f"👤 [CONTEXTUAL-CHATBOT] User Context: {user_context}")
        
        # Search for similar documents
        similar_docs = await contextual_vector_chatbot.search_similar_documents(request.query, top_k=3)
        
        if not similar_docs:
            print(f"❌ [CONTEXTUAL-CHATBOT] No relevant documents found for query: '{request.query}'")
            return ContextualChatResponse(
                response="I'm sorry, I couldn't find specific information about that. Please try asking about getting started, pricing, features, or technical support.",
                sources=[],
                similarity_scores=[],
                user_context_used=False,
                personalized_suggestions=[]
            )
        
        # Log search results
        print(f"🔍 [CONTEXTUAL-CHATBOT] Found {len(similar_docs)} relevant documents:")
        for i, doc in enumerate(similar_docs, 1):
            title = doc['metadata']['title']
            similarity = doc['similarity']
            category = doc['metadata']['category']
            print(f"   {i}. {title} (similarity: {similarity:.3f}, category: {category})")
        
        # Generate contextual response
        response_text = await contextual_vector_chatbot.generate_contextual_response(
            request.query, similar_docs, user_context
        )
        
        # Generate personalized suggestions
        suggestions = contextual_vector_chatbot.generate_personalized_suggestions(
            user_context, request.query
        )
        
        # Extract sources and scores
        sources = [doc['metadata']['title'] for doc in similar_docs]
        scores = [doc['similarity'] for doc in similar_docs]
        
        # Log response generation
        print(f"✅ [CONTEXTUAL-CHATBOT] Response generated successfully")
        print(f"📊 Top similarity score: {scores[0]:.3f}")
        print(f"📚 Sources used: {', '.join(sources)}")
        print(f"📝 Response length: {len(response_text)} characters")
        print(f"🎯 Suggestions generated: {len(suggestions)}")
        print(f"🎯 Suggestions content: {suggestions}")
        print(f"🎯 Response preview: {response_text[:100]}...")
        print("="*80)
        
        return ContextualChatResponse(
            response=response_text,
            sources=sources,
            similarity_scores=scores,
            user_context_used=True,
            personalized_suggestions=suggestions
        )
        
    except Exception as e:
        print(f"❌ [CONTEXTUAL-CHATBOT] Error processing query: '{request.query}'")
        print(f"❌ [CONTEXTUAL-CHATBOT] Error details: {str(e)}")
        import traceback
        print(f"❌ [CONTEXTUAL-CHATBOT] Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="Sorry, I'm having trouble processing your question right now. Please try again or ask about our main features."
        )
