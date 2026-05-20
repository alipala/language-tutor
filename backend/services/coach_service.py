"""
Taal Coach Service
==================
AI-powered language learning coach that provides personalized guidance,
progress insights, and encouragement.

Features:
- Full user context aggregation (learning plans, DNA, sessions, stats)
- Multilingual responses (in user's target language)
- New user onboarding and guidance
- Rich message types (text, cards, quick replies)
- NO redirections - all guidance within chat
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import os
from openai_client import get_async_openai

from database import (
    users_collection,
    learning_plans_collection,
    speaking_dna_profiles_collection,
    speaking_dna_history_collection,
    speaking_breakthroughs_collection,
    daily_stats_collection,
    conversation_sessions_collection,
    challenge_sessions_collection,
    user_achievements_collection,
    heart_events_collection,
    flashcard_sets_collection,
    speaking_time_tracking_collection,
)

logger = logging.getLogger(__name__)



class CoachService:
    """Service for Taal Coach AI interactions"""

    def __init__(self):
        self.model = "gpt-5-mini"  # Upgraded from gpt-4o-mini to latest GPT-5 mini
        self.cache_ttl_seconds = 300  # 5 minute cache

    async def get_user_context(
        self,
        user_id: str,
        language: str = None
    ) -> Dict[str, Any]:
        """
        Aggregate ALL user context for coach AI - NO language filtering!

        This is a FAST endpoint that returns cached/aggregated data
        so the coach can respond instantly with FULL context across ALL languages.

        The coach should be able to answer questions about ANY language the user
        has practiced in, not just the current learning language.

        Args:
            user_id: User's ID
            language: Optional - if provided, used as primary language for backwards compat

        Returns:
            Dict with ALL user context:
            - user_profile: Basic user info, subscription, level
            - ALL learning plans (across all languages)
            - ALL speaking DNA profiles (grouped by language)
            - ALL breakthroughs (across all languages)
            - ALL stats, sessions, challenges
            - Additional data: achievements, hearts, flashcards, etc.
            - is_new_user: Whether user is new (no sessions completed)
        """
        try:
            logger.info(f"[COACH] Aggregating FULL context for user {user_id} (ALL LANGUAGES)")

            # Parallel data fetching
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise ValueError(f"User {user_id} not found")

            # =========================================================================
            # FIXED: Fetch ALL learning plans - query BOTH string and ObjectId user_id!
            # =========================================================================
            learning_plans = await learning_plans_collection.find({
                "$or": [
                    {"user_id": user_id},
                    {"user_id": ObjectId(user_id)}
                ]
            }).to_list(None)

            logger.info(f"[COACH] Found {len(learning_plans)} learning plans (ALL LANGUAGES)")

            # Use first plan for detailed info, but track all
            learning_plan = learning_plans[0] if learning_plans else None

            # NOTE: Don't determine languages yet - we need to fetch all data first
            # Will determine all languages after fetching conversation_sessions, challenges, DNA profiles

            # =========================================================================
            # FIXED: Fetch ALL DNA profiles - NO language filter!
            # =========================================================================
            all_dna_profiles = await speaking_dna_profiles_collection.find({
                "user_id": user_id
            }).to_list(None)

            # Get primary DNA (first one or by the passed language)
            dna_profile = None
            if language and all_dna_profiles:
                # Try to get DNA for the specified language first
                for profile in all_dna_profiles:
                    if profile.get("language") == language:
                        dna_profile = profile
                        break
            
            # Fallback to first available
            if not dna_profile and all_dna_profiles:
                dna_profile = all_dna_profiles[0]

            # Format all DNA profiles by language
            all_dna_by_language = {}
            for profile in all_dna_profiles:
                lang = profile.get("language", "unknown")
                all_dna_by_language[lang] = self._format_dna_profile(profile, [])

            logger.info(f"[COACH] Found {len(all_dna_profiles)} DNA profiles: {list(all_dna_by_language.keys())}")

            # Get recent DNA evolution for primary profile
            dna_evolution = []
            if dna_profile:
                dna_evolution = await speaking_dna_history_collection.find({
                    "user_id": user_id,
                    "language": dna_profile.get("language")
                }).sort("week_start", -1).limit(4).to_list(4)

            # =========================================================================
            # FIXED: Fetch ALL breakthroughs - NO language filter!
            # =========================================================================
            breakthroughs = await speaking_breakthroughs_collection.find({
                "user_id": user_id
            }).sort("detected_at", -1).limit(10).to_list(10)

            logger.info(f"[COACH] Found {len(breakthroughs)} breakthroughs (ALL LANGUAGES)")

            # Get daily stats (last 7 days) - already language-agnostic
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            daily_stats = await daily_stats_collection.find({
                "user_id": user_id,
                "date": {"$gte": seven_days_ago.strftime("%Y-%m-%d")}
            }).sort("date", -1).to_list(7)

            # =========================================================================
            # FIXED: Get ALL conversation sessions - query BOTH string and ObjectId user_id!
            # =========================================================================
            
            # Query with string user_id OR ObjectId user_id
            recent_sessions = await conversation_sessions_collection.find({
                "$or": [
                    {"user_id": user_id},
                    {"user_id": ObjectId(user_id)}
                ]
            }).sort("created_at", -1).limit(10).to_list(10)

            # Count ALL conversation sessions
            total_conversation_sessions = await conversation_sessions_collection.count_documents({
                "$or": [
                    {"user_id": user_id},
                    {"user_id": ObjectId(user_id)}
                ]
            })
            logger.info(f"[COACH] Found {total_conversation_sessions} conversation sessions (ALL LANGUAGES)")

            # =========================================================================
            # FIXED: Get ALL learning plan sessions - across ALL plans
            # =========================================================================
            learning_plan_sessions = 0
            if learning_plans:
                for plan in learning_plans:
                    plan_sessions = plan.get("completed_sessions", 0)
                    learning_plan_sessions += plan_sessions
                    logger.info(f"[COACH] Learning plan {plan.get('language', 'unknown')}: {plan_sessions} completed sessions")

            # =========================================================================
            # FIXED: Get ALL challenge sessions - NO language filter!
            # =========================================================================
            challenge_sessions = await challenge_sessions_collection.find({
                "user_id": user_id,
                "is_active": False
            }).to_list(None)

            challenge_stats = len(challenge_sessions)
            logger.info(f"[COACH] Found {challenge_stats} completed challenges (ALL LANGUAGES)")

            # Breakdown by challenge type AND by language
            challenge_breakdown = {}
            challenge_by_language = {}
            total_correct = 0
            total_wrong = 0
            total_xp = 0
            for session in challenge_sessions:
                ctype = session.get("challenge_type", "unknown")
                clang = session.get("language", "unknown")
                
                # By type
                if ctype not in challenge_breakdown:
                    challenge_breakdown[ctype] = {
                        "count": 0,
                        "correct": 0,
                        "wrong": 0,
                        "xp": 0
                    }
                challenge_breakdown[ctype]["count"] += 1
                challenge_breakdown[ctype]["correct"] += session.get("correct_answers", 0)
                challenge_breakdown[ctype]["wrong"] += session.get("wrong_answers", 0)
                challenge_breakdown[ctype]["xp"] += session.get("total_xp", 0)
                
                # By language
                if clang not in challenge_by_language:
                    challenge_by_language[clang] = {
                        "count": 0,
                        "correct": 0,
                        "wrong": 0,
                        "xp": 0
                    }
                challenge_by_language[clang]["count"] += 1
                challenge_by_language[clang]["correct"] += session.get("correct_answers", 0)
                challenge_by_language[clang]["wrong"] += session.get("wrong_answers", 0)
                challenge_by_language[clang]["xp"] += session.get("total_xp", 0)
                
                total_correct += session.get("correct_answers", 0)
                total_wrong += session.get("wrong_answers", 0)
                total_xp += session.get("total_xp", 0)

            logger.info(f"[COACH] Challenge types: {list(challenge_breakdown.keys())}")
            logger.info(f"[COACH] Challenge by language: {list(challenge_by_language.keys())}")

            # =========================================================================
            # NEW: Fetch additional collections for full context
            # =========================================================================
            
            # User achievements
            user_achievements = await user_achievements_collection.find({
                "user_id": user_id
            }).sort("earned_at", -1).limit(10).to_list(10)
            logger.info(f"[COACH] Found {len(user_achievements)} achievements")

            # Heart events
            heart_events = await heart_events_collection.find({
                "user_id": user_id
            }).sort("created_at", -1).limit(20).to_list(20)
            logger.info(f"[COACH] Found {len(heart_events)} heart events")

            # Flashcard sets
            flashcard_sets = await flashcard_sets_collection.find({
                "user_id": user_id
            }).to_list(None)
            logger.info(f"[COACH] Found {len(flashcard_sets)} flashcard sets")

            # Speaking time tracking
            speaking_time = await speaking_time_tracking_collection.find({
                "user_id": user_id
            }).sort("date", -1).limit(30).to_list(30)
            logger.info(f"[COACH] Found {len(speaking_time)} speaking time entries")

            # =========================================================================
            # CRITICAL FIX: Gather ALL languages user has practiced in from ALL sources
            # =========================================================================
            all_learning_languages = set()

            # 1. From learning plans
            for plan in learning_plans:
                plan_lang = plan.get("language")
                if plan_lang:
                    all_learning_languages.add(plan_lang.lower())

            # 2. From conversation sessions
            for session in recent_sessions:
                session_lang = session.get("language")
                if session_lang:
                    all_learning_languages.add(session_lang.lower())

            # 3. From challenge sessions
            for challenge in challenge_sessions:
                challenge_lang = challenge.get("language")
                if challenge_lang:
                    all_learning_languages.add(challenge_lang.lower())

            # 4. From DNA profiles
            for profile in all_dna_profiles:
                profile_lang = profile.get("language")
                if profile_lang:
                    all_learning_languages.add(profile_lang.lower())

            # Convert to sorted list for consistent ordering
            learning_languages = sorted(list(all_learning_languages))

            logger.info(f"[COACH] ALL languages user has practiced: {learning_languages}")
            logger.info(f"[COACH] Sources - Plans: {[p.get('language') for p in learning_plans]}, "
                       f"Conversations: {list(set([s.get('language') for s in recent_sessions if s.get('language')]))}, "
                       f"Challenges: {list(challenge_by_language.keys())}, "
                       f"DNA: {list(all_dna_by_language.keys())}")

            # Calculate derived insights
            total_sessions = total_conversation_sessions + learning_plan_sessions
            logger.info(f"[COACH] Session totals: {total_conversation_sessions} conversation + {learning_plan_sessions} learning plan = {total_sessions} total")
            has_dna = dna_profile is not None
            has_learning_plan = learning_plan is not None

            # User is truly new if they have no sessions, no challenges, no plans, and no DNA
            is_new_user = (
                total_sessions == 0 and
                challenge_stats == 0 and
                not has_learning_plan and
                not has_dna
            )

            # Calculate current streak
            current_streak = 0
            if daily_stats:
                for stat in daily_stats:
                    if stat.get("sessions_completed", 0) > 0:
                        current_streak += 1
                    else:
                        break

            # Build context object - now includes ALL data!
            context = {
                "user_profile": {
                    "user_id": user_id,
                    "email": user.get("email"),
                    "target_language": learning_languages[0] if learning_languages else language,
                    "cefr_level": user.get("cefr_level", "A1"),
                    "subscription_status": user.get("subscription_status"),
                    "created_at": user.get("created_at"),
                    "all_learning_languages": learning_languages,
                },
                "is_new_user": is_new_user,
                "has_learning_plan": has_learning_plan,
                "has_dna_profile": has_dna,
                "learning_plans": [self._format_learning_plan(plan) for plan in learning_plans] if learning_plans else [],
                "learning_plan": self._format_learning_plan(learning_plan) if learning_plan else None,
                "speaking_dna": self._format_dna_profile(dna_profile, dna_evolution) if dna_profile else None,
                "all_dna_profiles": all_dna_by_language,
                "breakthroughs": self._format_breakthroughs(breakthroughs),
                "stats": {
                    "current_streak": current_streak,
                    "total_sessions": total_sessions,
                    "conversation_sessions": total_conversation_sessions,
                    "learning_plan_sessions": learning_plan_sessions,
                    "total_challenges": challenge_stats,
                    "last_7_days": self._format_daily_stats(daily_stats),
                },
                "challenge_details": {
                    "total": challenge_stats,
                    "total_correct": total_correct,
                    "total_wrong": total_wrong,
                    "total_xp": total_xp,
                    "accuracy": round((total_correct / (total_correct + total_wrong) * 100), 1) if (total_correct + total_wrong) > 0 else 0,
                    "by_type": challenge_breakdown,
                    "by_language": challenge_by_language
                },
                "recent_sessions": self._format_recent_sessions(recent_sessions),
                # NEW: Additional user data
                "achievements": self._format_achievements(user_achievements),
                "hearts": {
                    "total": len(heart_events),
                    "recent": heart_events[:5] if heart_events else []
                },
                "flashcards": {
                    "total_sets": len(flashcard_sets),
                    "sets": [{"name": fs.get("name"), "cards": fs.get("card_count", 0)} for fs in flashcard_sets]
                },
                "speaking_time": {
                    "total_entries": len(speaking_time),
                    "recent": speaking_time[:7] if speaking_time else []
                }
            }

            # Log detailed context for debugging
            logger.info(f"[COACH] Context aggregated: new_user={is_new_user}, has_dna={has_dna}, total_sessions={total_sessions}, streak={current_streak}")
            logger.info(f"[COACH] Languages: {learning_languages}")
            if context["speaking_dna"]:
                logger.info(f"[COACH] Primary DNA scores: confidence={context['speaking_dna']['confidence']}, fluency={context['speaking_dna']['fluency']}, vocabulary={context['speaking_dna']['vocabulary']}, accuracy={context['speaking_dna']['accuracy']}")
            return context

        except Exception as e:
            logger.error(f"[COACH] Error aggregating context: {str(e)}", exc_info=True)
            raise

    async def chat(
        self,
        user_id: str,
        language: str,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        target_language: str = None
    ) -> Dict[str, Any]:
        """
        Generate AI coach response.

        Args:
            user_id: User's ID
            language: Interface language for coach responses (English, Turkish, etc.)
            user_message: User's message text
            conversation_history: Previous messages in conversation
            target_language: User's target learning language (for context, optional)

        Returns:
            Dict with:
            - messages: List of rich message objects
            - quick_replies: Suggested quick reply options
        """
        try:
            logger.info(f"[COACH] Generating response for user {user_id}: '{user_message}'")

            # Content moderation check (skip for system messages like greetings)
            if not user_message.startswith("start_greeting"):
                try:
                    moderation = await get_async_openai().moderations.create(input=user_message)
                    if moderation.results[0].flagged:
                        logger.warning(f"[COACH] Message flagged by moderation: {user_message[:50]}...")
                        # Return polite refusal in user's language
                        refusal_messages = {
                            "en": "I'm here to help with your language learning journey. Let's keep our conversation focused on learning!",
                            "english": "I'm here to help with your language learning journey. Let's keep our conversation focused on learning!",
                            "tr": "Dil öğrenme yolculuğunuzda size yardımcı olmak için buradayım. Konuşmamızı öğrenmeye odaklı tutalım!",
                            "turkish": "Dil öğrenme yolculuğunuzda size yardımcı olmak için buradayım. Konuşmamızı öğrenmeye odaklı tutalım!",
                            "es": "Estoy aquí para ayudarte en tu viaje de aprendizaje de idiomas. ¡Mantengamos nuestra conversación enfocada en el aprendizaje!",
                            "spanish": "Estoy aquí para ayudarte en tu viaje de aprendizaje de idiomas. ¡Mantengamos nuestra conversación enfocada en el aprendizaje!",
                        }
                        refusal_text = refusal_messages.get(language.lower(), refusal_messages["en"])
                        return {
                            "messages": [{
                                "type": "text",
                                "content": refusal_text,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }],
                            "quick_replies": [],
                            "raw_response": refusal_text,
                        }
                except Exception as mod_error:
                    logger.warning(f"[COACH] Moderation check failed: {str(mod_error)}")
                    # Continue without moderation if check fails

            # Get full user context using target language if provided, otherwise use interface language
            context_lang = target_language if target_language else language
            context = await self.get_user_context(user_id, context_lang)

            # Build system prompt with interface language for responses
            system_prompt = self._build_system_prompt(context, language)

            # Build conversation messages in GPT-5 format
            # GPT-5 uses structured content (array of objects) and no system role
            messages = []

            # Add system instructions as first user message (GPT-5 doesn't have system role)
            # Can send multiple user messages in a row without requiring assistant responses
            messages.append({
                "role": "user",
                "content": [{"type": "text", "text": system_prompt}]
            })

            # Add conversation history in GPT-5 format (limited to last 5 messages for speed)
            if conversation_history:
                for msg in conversation_history[-5:]:  # Last 5 messages (reduced from 10)
                    messages.append({
                        "role": msg["role"],
                        "content": [{"type": "text", "text": msg["content"]}]
                    })

            # Add current user message in GPT-5 format
            messages.append({
                "role": "user",
                "content": [{"type": "text", "text": user_message}]
            })

            # Debug: Log the request we're sending
            logger.info(f"[COACH] Calling GPT-5-mini with {len(messages)} messages")
            logger.info(f"[COACH] First message role: {messages[0]['role']}, content type: {type(messages[0]['content'])}")
            logger.info(f"[COACH] Last message role: {messages[-1]['role']}")

            # Call OpenAI with GPT-5-mini specific parameters
            # GPT-5 models use:
            # - max_completion_tokens (not max_tokens) - increased to 4096 to prevent cutoff
            # - temperature=1 only (default)
            # - reasoning_effort="low" for faster responses (was "medium")
            # - response_format for structured output
            response = await get_async_openai().chat.completions.create(
                model=self.model,
                messages=messages
            )

            # Debug: Log full response structure for GPT-5-mini
            logger.info(f"[COACH] Full API response: finish_reason={response.choices[0].finish_reason}, model={response.model}")

            # GPT-5 models can have a "refusal" field - check for it first
            message_obj = response.choices[0].message

            # Check if model refused to respond
            if hasattr(message_obj, 'refusal') and message_obj.refusal:
                logger.warning(f"[COACH] Model refused to respond: {message_obj.refusal}")
                # Return a friendly fallback message
                refusal_messages = {
                    "en": "I'm here to help with your language learning. Let's focus on your progress!",
                    "english": "I'm here to help with your language learning. Let's focus on your progress!",
                }
                ai_response = refusal_messages.get(language.lower(), refusal_messages["en"])
            else:
                # GPT-5 response: content can be string or array of content parts
                content = message_obj.content

                if isinstance(content, list):
                    # Structured content format: [{"type": "text", "text": "..."}]
                    ai_response = ""
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            ai_response += part.get("text", "")
                        elif hasattr(part, 'type') and part.type == "text":
                            ai_response += getattr(part, 'text', '')
                    logger.info(f"[COACH] Extracted text from structured content ({len(ai_response)} chars)")
                elif isinstance(content, str):
                    # Simple string format (fallback)
                    ai_response = content
                else:
                    logger.error(f"[COACH] Unknown content format: {type(content)}")
                    logger.error(f"[COACH] Content: {content}")
                    ai_response = ""

            # Check if response is empty or None
            if not ai_response or ai_response.strip() == "":
                logger.error(f"[COACH] Empty response from GPT-5-mini!")
                logger.error(f"[COACH] Message object: {message_obj}")
                logger.error(f"[COACH] Content type: {type(message_obj.content)}")
                logger.error(f"[COACH] Content value: {message_obj.content}")
                raise ValueError("Empty response from AI model")

            logger.info(f"[COACH] AI response generated ({len(ai_response)} chars): {ai_response[:100]}...")

            # Parse AI response into rich messages
            parsed_messages = self._parse_response(ai_response, context, user_message)

            # Generate context-aware quick replies in interface language based on conversation
            quick_replies = self._generate_quick_replies(context, language, user_message, conversation_history)

            return {
                "messages": parsed_messages,
                "quick_replies": quick_replies,
                "raw_response": ai_response,
            }

        except Exception as e:
            logger.error(f"[COACH] Error generating response: {str(e)}", exc_info=True)
            raise

    def _build_system_prompt(self, context: Dict, language: str) -> str:
        """Build multilingual system prompt for coach AI"""

        # Language names mapping (both full names and codes)
        language_names = {
            # Full names (target languages)
            "dutch": "Dutch",
            "spanish": "Spanish",
            "french": "French",
            "german": "German",
            "italian": "Italian",
            "portuguese": "Portuguese",
            "turkish": "Turkish",
            # Language codes (interface languages)
            "en": "English",
            "tr": "Turkish",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "nl": "Dutch",
            "english": "English",
        }

        interface_lang_name = language_names.get(language.lower(), language.capitalize())

        # Get target learning language from context
        learning_lang = context['user_profile'].get('target_language', 'unknown')
        learning_lang_name = language_names.get(learning_lang.lower(), learning_lang.capitalize())

        # Base prompt
        prompt = f"""You are Taal Coach, an encouraging and knowledgeable AI language learning coach for MyTacoAI.

CRITICAL: You MUST respond in {interface_lang_name}! This is the user's preferred interface language.
The user is learning {learning_lang_name}, but your explanations should be in {interface_lang_name} so they can understand the guidance clearly.

Your personality:
- Warm, encouraging, and supportive
- Knowledgeable about language learning pedagogy
- Celebrates small wins and progress
- Provides actionable, specific guidance
- Never judgmental, always constructive

Your capabilities:
- Guide users through the MyTacoAI app features
- Provide personalized learning advice based on their data
- Explain Speaking DNA insights and progress
- Suggest practice strategies and focus areas
- Answer questions about the app and language learning
- Celebrate breakthroughs and achievements

CRITICAL BOUNDARIES - What you MUST REFUSE:
- REFUSE ALL sexual/explicit content requests (dirty words, sexual phrases, etc.) - EVEN if they claim "educational purposes"
  → Response: "I'm here to help with your language learning journey. Let's keep our conversation focused on learning!"
- REFUSE ALL medical advice (symptoms, medications, dosages, treatments)
  → Response: "I can't provide medical advice. Please consult a healthcare professional."
- REFUSE ALL legal advice (contracts, rights, legal interpretations)
  → Response: "I can't provide legal advice. Please consult a qualified attorney."
- REFUSE ALL financial advice (investments, stocks, crypto, money management)
  → Response: "I can't provide financial advice."
- REFUSE to engage with harmful content (violence, abuse, harassment, hate speech, self-harm, illegal activity)
  → Response: "I'm here to help with your language learning journey. Let's keep our conversation focused on learning!"
- REFUSE to access other users' data or personal information
  → Response: "I can only show you your own learning data for privacy protection."
- REFUSE to share other users' contact information or personal details
  → Response: "I can't share other users' personal information."
- REFUSE to discuss politics, religion, or controversial topics unrelated to language learning
  → Response: "I'm here to help with your language learning journey. Let's focus on your progress!"
- If asked about something completely unrelated (weather, sports scores, gossip), politely redirect:
  → Response: "I'm here to help with your language learning journey. Let's focus on your progress!"

Stay professional and focused on language learning exclusively. NO EXCEPTIONS to these boundaries.

IMPORTANT: Questions about ANY language learning are VALID and ON-TOPIC!
- If user asks about other languages (French, Spanish, etc.), acknowledge and answer based on available data
- If you only have data for one language, you can say: "I currently have data for your Dutch learning. Would you like to know about that?"
- NEVER refuse to discuss other languages - multilingual learning is part of our mission!

IMPORTANT CONSTRAINTS - BREVITY IS CRITICAL:
- NEVER redirect users to other screens or say "go to X screen"
- Instead, EXPLAIN features and show insights directly in chat
- Use embedded cards and rich content to show progress/stats
- MAXIMUM 2 sentences per response (STRICT LIMIT!)
- When showing progress/DNA/challenge cards, MAXIMUM 1 SHORT sentence since card shows all details
- Be conversational and natural, not robotic
- NEVER write long explanations - users want quick, actionable insights

CRITICAL: Be SPECIFIC with user data!
- When asked about learning plans, mention their ACTUAL goals, level, and progress
- When asked about DNA, mention their ACTUAL scores and strongest/weakest strands
- When asked about progress, mention their ACTUAL streak and sessions
- DON'T give generic "you can do X" answers - use their REAL data!
- Example: Instead of "Your plan includes sessions" say "You've completed 5 out of 20 sessions"

IMPORTANT: Understanding "Practice Sessions" in MyTacoAI
In our app, there are THREE types of practice sessions:
1. **Conversation Sessions**: Real-time speaking practice with AI tutor (voice conversations)
2. **Learning Plan Sessions**: Guided practice sessions as part of structured learning plans
3. **Challenge Sessions**: Gamified practice challenges (micro quizzes, brain ticklers, etc.)

When a user asks about "practice sessions" or "sessions", they mean ALL of these types combined.
- "Total Sessions" = Conversation Sessions + Learning Plan Sessions
- "Challenges" are tracked separately but are also a form of practice

NEVER say "you haven't completed practice sessions" if they have conversation or learning plan sessions!
Example CORRECT responses:
- "You've completed 5 practice sessions: 1 conversation and 4 learning plan sessions."
- "Yes, you've done 1 conversation practice and 4 guided learning sessions."

User Context:
"""

        # Add user-specific context
        if context["is_new_user"]:
            prompt += f"""
NEW USER - This is their first interaction!
- Welcome them warmly
- Explain what you can help with
- Guide them to start their first session or challenge
- Keep it simple and encouraging
"""
        else:
            # Get all learning languages
            all_languages = context['user_profile'].get('all_learning_languages', [learning_lang])
            
            prompt += f"""
Returning User:
- All Languages Learning: {', '.join([lang.title() for lang in all_languages])}
- CEFR Level: {context['user_profile']['cefr_level']}
- Subscription Status: {context['user_profile'].get('subscription_status', 'free')} {'(FREE - 10 min/month)' if context['user_profile'].get('subscription_status') in [None, 'free', 'expired', 'canceled'] else '(PREMIUM)'}
- Current Streak: {context['stats']['current_streak']} days
- Total Practice Sessions: {context['stats']['total_sessions']} ({context['stats']['conversation_sessions']} conversation + {context['stats']['learning_plan_sessions']} learning plan)
- Total Challenges: {context['stats']['total_challenges']}

Session Breakdown (ALL LANGUAGES):
- Conversation Sessions: {context['stats']['conversation_sessions']} (real-time speaking practice)
- Learning Plan Sessions: {context['stats']['learning_plan_sessions']} (guided learning practice)
- Challenge Sessions: {context['stats']['total_challenges']} (gamified practice)

IMPORTANT: You now have data for ALL languages the user is learning: {', '.join([lang.title() for lang in all_languages])}
When user asks about progress, mention data from ALL their languages!
"""

            # Add challenge breakdown if available (now includes ALL languages!)
            if context.get("challenge_details") and context["challenge_details"]["total"] > 0:
                chal = context["challenge_details"]
                prompt += f"""
Challenge Performance (ALL LANGUAGES):
- Total Completed: {chal['total']} challenges
- Overall Accuracy: {chal['accuracy']}%
- Correct Answers: {chal['total_correct']} | Wrong: {chal['total_wrong']}
- Total XP Earned: {chal['total_xp']}

Challenge Types Completed:
"""
                for ctype, stats in chal['by_type'].items():
                    type_name = ctype.replace('_', ' ').title()
                    type_accuracy = round((stats['correct'] / (stats['correct'] + stats['wrong']) * 100), 1) if (stats['correct'] + stats['wrong']) > 0 else 0
                    prompt += f"  - {type_name}: {stats['count']} completed, {type_accuracy}% accuracy, {stats['xp']} XP\n"
                
                # Add breakdown by language
                if 'by_language' in chal and len(chal['by_language']) > 1:
                    prompt += "\nBy Language:\n"
                    for lang, stats in chal['by_language'].items():
                        prompt += f"  - {lang.title()}: {stats['count']} challenges\n"

            if context["has_dna_profile"]:
                dna = context["speaking_dna"]
                prompt += f"""
Speaking DNA Profile (Scores 0-100):
- Confidence: {dna['confidence']} ({dna['strongest_strand'] if dna['confidence'] == dna['strongest_score'] else ''})
- Fluency (Rhythm): {dna['fluency']} ({dna['strongest_strand'] if dna['fluency'] == dna['strongest_score'] else ''})
- Vocabulary: {dna['vocabulary']} ({dna['strongest_strand'] if dna['vocabulary'] == dna['strongest_score'] else ''})
- Accuracy: {dna['accuracy']} ({dna['strongest_strand'] if dna['accuracy'] == dna['strongest_score'] else ''})
- Strongest Area: {dna['strongest_strand'].capitalize()} (Score: {dna['strongest_score']})
- Growth Area: {dna['weakest_strand'].capitalize()} (Score: {dna['weakest_score']})
"""

            if context["breakthroughs"]:
                recent_bt = context["breakthroughs"][0]
                prompt += f"\nRecent Breakthrough: {recent_bt['title']} - {recent_bt['description']}\n"

            if context["has_learning_plan"] and context.get("learning_plans"):
                plans = context["learning_plans"]
                total_completed = sum(p['completed_sessions'] for p in plans)

                prompt += f"""
Learning Plans ({len(plans)} active):
"""
                for i, plan in enumerate(plans, 1):
                    goals_str = ", ".join(plan['goals']) if plan.get('goals') else "General"
                    prompt += f"""  Plan {i}: {plan.get('level', 'Unknown')} - {goals_str}
    - Progress: {plan['completed_sessions']} out of {plan['total_sessions']} sessions completed
"""
                prompt += f"\nIMPORTANT: User has {len(plans)} SEPARATE learning plans. When discussing progress, mention INDIVIDUAL plan progress, NOT combined totals!\n"
                prompt += f"Example: Say '3 out of 8 in Travel & Tourism, 1 out of 16 in Academic Studies' instead of '4 out of 24 overall'\n"

        # Add comprehensive app features guide for onboarding
        prompt += f"""

==========================================================================
📱 APP FEATURES GUIDE - Answer user questions about the app!
==========================================================================

**1. LEARNING PLANS**
Purpose: Structured learning paths with guided practice sessions
- Help users reach specific goals (travel, work, academic, social, culture)
- Progress through CEFR levels (A1 → A2 → B1 → B2 → C1 → C2)
- Sessions organized by weeks with topics, vocabulary, grammar

How to create:
- Go to Dashboard → Tap "+" button → Select language, level, goals, duration
- Choose from: Travel & Tourism, Work & Business, Academic Studies, Social & Friends, Culture & Entertainment

Difference from Practice Sessions:
- Learning Plan = Structured curriculum with specific topics
- Practice Sessions = Free conversation practice (any topic)

**2. PRACTICE SESSIONS (3 Types)**
a) Conversation Sessions: Real-time voice conversations with AI tutor
   - Tap "Practice" button → Select language → Start speaking
   - AI responds naturally, corrects mistakes, provides feedback

b) Learning Plan Sessions: Guided practice from your learning plan
   - Follow structured curriculum with topics, vocab, grammar
   - Complete sessions to progress through your plan

c) Challenge Sessions: Gamified practice challenges
   - Brain Ticklers, Micro Quizzes, Error Spotting, Swipe Fix, etc.
   - Earn XP, hearts, and track accuracy

**3. CHALLENGES & GAMES**
Access: Dashboard → "Challenges" card OR Practice tab
Types:
- Brain Tickler: Quick thinking language puzzles
- Micro Quiz: Fast-paced vocabulary/grammar quizzes
- Error Spotting: Find mistakes in sentences
- Swipe Fix: Swipe to correct errors
- Story Builder: Build stories with correct grammar
- Native Check: Match native speaker patterns

**4. ACCOUNT INFORMATION**
Access: Settings (gear icon at top right) → Account section
View: Email, subscription status, learning languages, CEFR level

**5. FREE VS PREMIUM PLANS**
FREE Account (Try & Learn):
- 10 minutes of conversation practice per month
- Access to challenges (with heart system limits)
- Basic progress tracking
- Limited assessments

Fluency Builder (Premium - €19.99/month or €119/year):
- 150 minutes speaking per month
- 2 assessments per month
- 10 hearts for challenges
- Refills every 1 hour
- Advanced tracking
- All conversation topics
- 7-day free trial

Language Mastery (Premium - €39.99/month or €239/year):
- UNLIMITED speaking time
- UNLIMITED assessments
- UNLIMITED hearts with instant refills
- Premium learning plans
- Advanced analytics
- All conversation topics
- 7-day free trial

**6. FLASHCARDS**
Location: Dashboard → "Flashcards" section
How they work:
- Automatically generated from your conversation sessions
- Key vocabulary and phrases you practiced
- Swipe to study, mark as learned

**7. DNA ANALYSIS & VOICE METRICS**
What is it:
- Speaking DNA = Your unique speaking profile across 4 strands:
  • Confidence: Speaking boldness and self-assurance
  • Fluency (Rhythm): Speaking pace, pauses, natural flow
  • Vocabulary: Word variety and usage
  • Accuracy: Grammar and pronunciation correctness

Importance:
- Identifies your strengths and growth areas
- Tracks improvement over time (weekly snapshots)
- Detects breakthroughs (significant improvements)
- Provides personalized feedback

How to access:
- Premium feature (Fluency Builder or Language Mastery)
- Dashboard → Speaking DNA card
- View detailed scores, evolution, and breakthroughs

**8. AI TUTOR VOICE**
How to change:
- Settings → AI Tutor Voice section
- Choose from: Alloy, Echo, Fable, Onyx, Nova, Shimmer
- Each voice has unique tone and personality

**9. APP LANGUAGE**
How to change interface language:
- Settings → App Language
- Available: English, Turkish, Spanish, French, German, Italian, Portuguese, Dutch
- Note: This changes UI language, NOT your learning language

**10. SUBSCRIPTIONS**
How to check/manage:
- Settings → Subscription & Billing section
- View current plan, renewal date, usage minutes
- Upgrade, downgrade, or cancel subscription
- Manage billing information

**11. USER SETTINGS**
Access: Settings (gear icon at top right)
Options:
- Profile: Name, email, password
- Learning Languages: Add/remove languages, set CEFR level
- Notifications: Push notification preferences
- AI Tutor: Voice selection, speaking speed
- Privacy: Data preferences, account deletion
- Support: Help center, contact support

**12. HEART SYSTEM (Free Users)**
How it works:
- Free users use hearts for challenges
- Lose hearts for wrong answers, gain for correct streaks
- Hearts refill over time (1 heart per 30 minutes)
- Streak shield: 5 correct answers → shield (protects from 1 wrong answer)

Premium users: Unlimited hearts, no waiting

**13. STATISTICS & PROGRESS TRACKING**
📊 WHERE TO FIND ALL YOUR STATISTICS:
Location: Profile tab (bottom navigation) → Statistics tab

What's available in Statistics tab:
1. **Minutes Practiced** - Total speaking time across all sessions
   - Tap card to see: Daily breakdown, this week's total, practice patterns

2. **Challenges Completed** - All gamified challenges finished
   - Tap card to see: Total count, today's count, breakdown by type with accuracy
   - Shows: Brain Ticklers, Micro Quizzes, Error Spotting, Swipe Fix, etc.

3. **Day Streak** - Current consecutive days of practice
   - Tap card to see: Current streak, longest streak, streak history

4. **Flashcards** - Generated vocabulary sets from conversations
   - Tap card to see: List of all flashcard sets with study buttons

5. **Achievements** - Earned badges and milestones
   - Tap card to see: All achievements with unlock requirements

6. **Average Daily Practice** - Average practice time per day
   - Tap card to see: Weekly practice pattern visualization with chart

7. **Practice Sessions** - Total conversation + learning plan sessions
   - Shows total count (conversations + guided learning combined)

8. **Learning Plans** - Active structured learning plans
   - Tap card to see: All plans with progress indicators

9. **Total XP** - Experience points earned
   - Tap card to see: XP breakdown by source (challenges, conversations, achievements)

📈 OTHER STATISTICS LOCATIONS:
- **Speaking DNA Analysis**: Profile tab → DNA Analytics tab
  - 6 DNA strands with progress rings and evolution tracking
  - Shows: Confidence, Vocabulary, Accuracy, Rhythm, Learning, Emotional scores

- **Recent Performance**: Dashboard → Recent Performance card
  - 7-day accuracy trend graph
  - Daily breakdown with sparkline visualization

CRITICAL: When users ask "where can I see my [statistic]", tell them:
- Go to Profile tab → Statistics tab → Tap the [Statistic Name] card
- Example: "Go to Profile tab → Statistics tab → Tap 'Challenges Completed' card to see your full breakdown by type and accuracy"

Statistics available in YOUR context (what you can see):
- Current streak: {context['stats']['current_streak']} days
- Total sessions: {context['stats']['total_sessions']}
- Total challenges: {context['stats']['total_challenges']}
- Challenge accuracy: {context.get('challenge_details', {}).get('accuracy', 0)}%
- XP earned: {context.get('challenge_details', {}).get('total_xp', 0)}
- Speaking DNA scores (if premium): Confidence, Fluency, Vocabulary, Accuracy
- Learning plan progress: Sessions completed per plan

==========================================================================
IMPORTANT: When users ask app questions, answer DIRECTLY with specifics!
- Don't say "you can check settings" - tell them EXACTLY where and how
- Don't say "there are different features" - list them with details
- Be a helpful onboarding coach, not a generic assistant
- Guide free users on how to use the app effectively
- When asked about statistics: Tell them Profile tab → Statistics tab → Tap specific card
==========================================================================

Response Format (STRICT RULES):
- Language: MUST be in {interface_lang_name} (NOT {learning_lang_name}!)
- Length: MAXIMUM 2 sentences (HARD LIMIT!)
- When showing cards: MAXIMUM 1 SHORT sentence (card has all details)
- Tone: Conversational, warm, encouraging
- Style: Direct, actionable, specific (no fluff!)

CRITICAL LENGTH EXAMPLES:
✅ GOOD: "You've completed 4 challenges with 75% accuracy! Keep practicing to improve your rhythm."
❌ BAD: "You've completed 4 challenges so far! That's a great start and shows you're actively engaging with the material. Your accuracy is 75%, which is good, but there's room for improvement. Keep practicing to get better results."

Remember: RESPOND IN {interface_lang_name}! User learns {learning_lang_name}, but needs SHORT guidance in {interface_lang_name}.
"""

        return prompt

    def _parse_response(self, ai_response: str, context: Dict, user_message: str = "") -> List[Dict[str, Any]]:
        """
        Parse AI text response into rich message objects.

        Message types:
        - text: Simple text message
        - progress_card: Shows progress stats
        - dna_card: Shows DNA insights
        - learning_plans_table: Shows all learning plans with progress
        - challenge_stats_table: Shows challenge statistics breakdown
        - celebration: Animated celebration for breakthroughs
        """
        messages = []

        # For now, return simple text message
        # In future, can parse special markers like [SHOW_PROGRESS] or [CELEBRATE]
        messages.append({
            "type": "text",
            "content": ai_response,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Check user's message (not AI response) for intent to show cards
        user_msg_lower = user_message.lower()

        # Add learning plans table if user asked about plans
        if any(keyword in user_msg_lower for keyword in ["learning plan", "plan", "my plans", "learning path"]):
            if context.get("learning_plans") and len(context["learning_plans"]) > 0:
                messages.append({
                    "type": "learning_plans_table",
                    "data": {
                        "plans": context["learning_plans"],
                        "total_plans": len(context["learning_plans"]),
                        "total_completed": sum(p.get("completed_sessions", 0) for p in context["learning_plans"]),
                        "total_sessions": sum(p.get("total_sessions", 0) for p in context["learning_plans"])
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        # Add progress card if user asked about progress
        if any(keyword in user_msg_lower for keyword in ["progress", "streak", "sessions", "stats"]):
            if context["stats"]["total_sessions"] > 0 or context["stats"]["current_streak"] > 0:
                messages.append({
                    "type": "progress_card",
                    "data": {
                        "streak": context["stats"]["current_streak"],
                        "total_sessions": context["stats"]["total_sessions"],
                        "total_challenges": context["stats"]["total_challenges"],
                        "last_7_days": context["stats"]["last_7_days"]
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        # Add challenge stats table if user asked about challenges
        if any(keyword in user_msg_lower for keyword in ["challenge", "challenges", "quiz", "game"]):
            if context.get("challenge_details") and context["challenge_details"]["total"] > 0:
                chal = context["challenge_details"]
                messages.append({
                    "type": "challenge_stats_table",
                    "data": {
                        "total": chal["total"],
                        "accuracy": chal["accuracy"],
                        "total_correct": chal["total_correct"],
                        "total_wrong": chal["total_wrong"],
                        "total_xp": chal["total_xp"],
                        "by_type": chal["by_type"]
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        # Add DNA card if user asked about DNA specifically
        # Be more restrictive - only show if explicitly asking about DNA
        if any(keyword in user_msg_lower for keyword in ["dna", "speaking dna", "voice dna", "strands", "confidence score", "fluency score"]):
            if context["has_dna_profile"]:
                messages.append({
                    "type": "dna_card",
                    "data": context["speaking_dna"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        return messages

    def _generate_quick_replies(
        self,
        context: Dict,
        language: str,
        user_message: str = "",
        conversation_history: List[Dict] = None
    ) -> List[Dict[str, str]]:
        """Generate context-aware quick reply suggestions based on conversation flow"""

        # Quick replies mapping (interface languages)
        quick_replies_map = {
            # English
            "english": {
                "progress": "Show my progress",
                "dna": "Tell me about my DNA",
                "tips": "Give me tips",
                "plan": "What's my learning plan?",
                "challenges": "What challenges I completed?",
                "start": "Let's start!",
                "how_improve": "How can I improve?",
                "next_steps": "What should I do next?",
                "streak": "How's my streak?",
            },
            "en": {
                "progress": "Show my progress",
                "dna": "Tell me about my DNA",
                "tips": "Give me tips",
                "plan": "What's my learning plan?",
                "challenges": "What challenges I completed?",
                "start": "Let's start!",
                "how_improve": "How can I improve?",
                "next_steps": "What should I do next?",
                "streak": "How's my streak?",
            },
            # Turkish
            "turkish": {
                "progress": "İlerlememi göster",
                "dna": "DNA'm hakkında bilgi ver",
                "tips": "Bana ipuçları ver",
                "plan": "Öğrenme planım nedir?",
                "challenges": "Hangi zorlukları tamamladım?",
                "start": "Hadi başlayalım!",
                "how_improve": "Nasıl gelişebilirim?",
                "next_steps": "Ne yapmalıyım?",
                "streak": "Serilerim nasıl?",
            },
            "tr": {
                "progress": "İlerlememi göster",
                "dna": "DNA'm hakkında bilgi ver",
                "tips": "Bana ipuçları ver",
                "plan": "Öğrenme planım nedir?",
                "challenges": "Hangi zorlukları tamamladım?",
                "start": "Hadi başlayalım!",
                "how_improve": "Nasıl gelişebilirim?",
                "next_steps": "Ne yapmalıyım?",
                "streak": "Serilerim nasıl?",
            },
            # Spanish
            "spanish": {
                "progress": "Muestra mi progreso",
                "dna": "Cuéntame sobre mi DNA",
                "tips": "Dame consejos",
                "plan": "¿Cuál es mi plan?",
                "challenges": "¿Qué desafíos completé?",
                "start": "¡Empecemos!",
                "how_improve": "¿Cómo puedo mejorar?",
                "next_steps": "¿Qué debo hacer?",
                "streak": "¿Cómo va mi racha?",
            },
            "es": {
                "progress": "Muestra mi progreso",
                "dna": "Cuéntame sobre mi DNA",
                "tips": "Dame consejos",
                "plan": "¿Cuál es mi plan?",
                "challenges": "¿Qué desafíos completé?",
                "start": "¡Empecemos!",
                "how_improve": "¿Cómo puedo mejorar?",
                "next_steps": "¿Qué debo hacer?",
                "streak": "¿Cómo va mi racha?",
            },
        }

        # Default to English
        replies = quick_replies_map.get(language.lower(), quick_replies_map["en"])

        # Generate contextual follow-up questions based on current conversation
        suggestions = []
        user_msg_lower = user_message.lower()

        # New user flow
        if context["is_new_user"]:
            suggestions.append({"label": replies["start"], "value": "start_first_session"})
            suggestions.append({"label": replies["plan"], "value": "explain_learning_plan"})
            return suggestions[:3]

        # Context-aware suggestions based on what user just asked

        # If they asked about progress, suggest DNA or challenges next
        if any(keyword in user_msg_lower for keyword in ["progress", "streak", "sessions", "stats"]):
            if context["has_dna_profile"]:
                suggestions.append({"label": replies["dna"], "value": "show_dna"})
            if context["stats"]["total_challenges"] > 0:
                suggestions.append({"label": replies["challenges"], "value": "show_challenges"})
            suggestions.append({"label": replies["tips"], "value": "give_tips"})

        # If they asked about DNA, suggest progress or improvement tips
        elif any(keyword in user_msg_lower for keyword in ["dna", "speaking dna", "strands"]):
            suggestions.append({"label": replies["how_improve"], "value": "improvement_tips"})
            suggestions.append({"label": replies["progress"], "value": "show_progress"})
            suggestions.append({"label": replies["next_steps"], "value": "next_steps"})

        # If they asked about learning plan, suggest progress or specific plan details
        elif any(keyword in user_msg_lower for keyword in ["learning plan", "plan", "path"]):
            suggestions.append({"label": replies["progress"], "value": "show_progress"})
            if context["stats"]["total_challenges"] > 0:
                suggestions.append({"label": replies["challenges"], "value": "show_challenges"})
            suggestions.append({"label": replies["next_steps"], "value": "next_steps"})

        # If they asked about challenges, suggest tips or DNA
        elif any(keyword in user_msg_lower for keyword in ["challenge", "challenges", "quiz"]):
            suggestions.append({"label": replies["tips"], "value": "give_tips"})
            if context["has_dna_profile"]:
                suggestions.append({"label": replies["dna"], "value": "show_dna"})
            suggestions.append({"label": replies["progress"], "value": "show_progress"})

        # Default suggestions (greeting or general query)
        else:
            suggestions.append({"label": replies["progress"], "value": "show_progress"})
            if context["has_learning_plan"]:
                suggestions.append({"label": replies["plan"], "value": "show_plan"})
            if context["has_dna_profile"]:
                suggestions.append({"label": replies["dna"], "value": "show_dna"})

        return suggestions[:3]  # Max 3 quick replies

    def _format_learning_plan(self, plan: Dict) -> Dict:
        """Format learning plan for context"""
        if not plan:
            return None

        # Get goals
        goals = plan.get("goals", [])
        goal_names = {
            "travel": "Travel & Tourism",
            "work": "Work & Business",
            "academic": "Academic Studies",
            "social": "Social & Friends",
            "culture": "Culture & Entertainment",
            "general": "General Communication"
        }
        formatted_goals = [goal_names.get(g, g) for g in goals] if goals else []

        # Use completed_sessions field (integer) instead of counting sessions array
        # Also properly extract total_sessions
        return {
            "level": plan.get("proficiency_level") or plan.get("level") or plan.get("cefr_level", "A1"),
            "language": plan.get("language"),
            "goals": formatted_goals,
            "total_sessions": plan.get("total_sessions", 0),  # Use total_sessions field
            "completed_sessions": plan.get("completed_sessions", 0),  # Use completed_sessions field
            "current_week": plan.get("current_week", 1),
        }

    def _format_dna_profile(self, profile: Dict, evolution: List[Dict]) -> Dict:
        """Format DNA profile for context"""
        if not profile:
            return None

        strands = profile.get("dna_strands", {})

        # Extract scores from correct fields and convert to percentages (0-100)
        # Each strand type has different field names
        confidence_score = strands.get("confidence", {}).get("score", 0)
        rhythm_score = strands.get("rhythm", {}).get("consistency_score", 0)  # Note: consistency_score, not score
        vocabulary_score = strands.get("vocabulary", {}).get("new_word_attempt_rate", 0)  # Note: new_word_attempt_rate
        accuracy_score = strands.get("accuracy", {}).get("grammar_accuracy", 0)  # Note: grammar_accuracy
        learning_score = strands.get("learning_agility", {}).get("score", 0) if strands.get("learning_agility") else 0
        emotional_score = strands.get("emotional_expression", {}).get("score", 0) if strands.get("emotional_expression") else 0

        # Convert decimals to percentages (0.66 → 66)
        strand_scores = {
            "confidence": int(confidence_score * 100),
            "rhythm": int(rhythm_score * 100),
            "vocabulary": int(vocabulary_score * 100),
            "accuracy": int(accuracy_score * 100),
            "learning": int(learning_score * 100),
            "emotional": int(emotional_score * 100),
        }

        # Find strongest and weakest (excluding zeros)
        non_zero_scores = {k: v for k, v in strand_scores.items() if v > 0}
        if non_zero_scores:
            strongest = max(non_zero_scores.items(), key=lambda x: x[1])
            weakest = min(non_zero_scores.items(), key=lambda x: x[1])
        else:
            strongest = ("confidence", 0)
            weakest = ("rhythm", 0)

        return {
            "confidence": strand_scores["confidence"],
            "fluency": strand_scores["rhythm"],
            "vocabulary": strand_scores["vocabulary"],
            "accuracy": strand_scores["accuracy"],
            "strongest_strand": strongest[0],
            "weakest_strand": weakest[0],
            "strongest_score": strongest[1],
            "weakest_score": weakest[1],
            "has_evolution": len(evolution) > 1,
        }

    def _format_breakthroughs(self, breakthroughs: List[Dict]) -> List[Dict]:
        """Format breakthroughs for context"""
        return [
            {
                "title": bt.get("title"),
                "description": bt.get("description"),
                "type": bt.get("breakthrough_type"),
                "detected_at": bt.get("detected_at"),
            }
            for bt in breakthroughs
        ]

    def _format_daily_stats(self, stats: List[Dict]) -> List[Dict]:
        """Format daily stats for context"""
        return [
            {
                "date": stat.get("date"),
                "sessions": stat.get("sessions_completed", 0),
                "challenges": stat.get("challenges_completed", 0),
                "xp_earned": stat.get("xp_earned", 0),
            }
            for stat in stats
        ]

    def _format_recent_sessions(self, sessions: List[Dict]) -> List[Dict]:
        """Format recent sessions for context"""
        return [
            {
                "type": session.get("session_type"),
                "duration_minutes": session.get("duration_minutes", 0),
                "created_at": session.get("created_at"),
            }
            for session in sessions[:5]  # Last 5 sessions
        ]

    def _format_achievements(self, achievements: List[Dict]) -> List[Dict]:
        """Format achievements for context"""
        return [
            {
                "title": ach.get("title"),
                "description": ach.get("description"),
                "type": ach.get("achievement_type"),
                "earned_at": ach.get("earned_at"),
            }
            for ach in achievements
        ]


# Singleton instance
coach_service = CoachService()
