"""
TaalCoach Service - VECTOR SEARCH ENHANCED VERSION
===================================================
Production-grade context-aware language coach with semantic search

NEW FEATURES:
- ✅ Semantic search across all user content (Pinecone)
- ✅ Cross-feature intelligence (correlate flashcards → conversations → DNA)
- ✅ Temporal reasoning (week-over-week, month-over-month comparisons)
- ✅ Hybrid ranking (semantic similarity + recency + relevance)
- ✅ Perfect context awareness - NO compromises on quality
"""
import logging
import json
import asyncio
import openai
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from services.coach_service_optimized import CoachService as BaseCoachService
from services.vector_db_service import vector_db, search_user_context
from cache_helpers import get_taalcoach_context_cached
from services.query_enhancement_service import query_enhancer  # PHASE 1 FIX
from services.semantic_reranker import semantic_reranker  # PHASE 2: Reranking
from services.learning_trajectory_analyzer import trajectory_analyzer  # PHASE 2: Trajectory
from services.hybrid_search_service import hybrid_search_service  # PHASE 3: Hybrid Search
from services.inline_stats_formatter import inline_stats_formatter  # Duolingo-style inline stats
from services.subscription_chip_formatter import subscription_chip_formatter  # Subscription chips
from services.challenge_card_formatter import challenge_card_formatter  # Challenge cards
from services.voice_profile_formatter import voice_profile_formatter  # AI Voice profiles
from services.capability_cards_formatter import capability_cards_formatter  # Capability showcase cards

logger = logging.getLogger(__name__)

# OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class VectorEnhancedCoachService(BaseCoachService):
    """
    Enhanced TaalCoach with vector search capabilities

    Inherits all functionality from base CoachService and adds:
    - Semantic search for finding relevant user content
    - Cross-feature correlation analysis
    - Temporal trend detection
    - Hybrid search with recency boost
    """

    def __init__(self, use_hybrid_search: bool = True):
        super().__init__()
        self.vector_db = vector_db
        self.use_hybrid_search = use_hybrid_search  # PHASE 3: Configurable hybrid search
        search_type = "hybrid (BM25 + Semantic)" if use_hybrid_search else "semantic only"
        logger.info(f"[COACH] Initialized with vector search enhancement - Mode: {search_type}")

    async def chat(
        self,
        user_id: str,
        language: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        target_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main chat method that routes to vector-enhanced chat.

        This is the compatibility wrapper that maintains the same interface
        as the base CoachService while using vector search.
        """
        return await self.chat_with_vector_search(
            user_id=user_id,
            language=language,
            user_message=user_message,
            target_language=target_language or language,
            conversation_history=conversation_history
        )

    async def get_semantic_context(
        self,
        user_id: str,
        query: str,
        intent: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get semantically relevant context using vector search

        Args:
            user_id: User ID
            query: User's query
            intent: Detected intent
            language: Optional language filter

        Returns:
            Dict with relevant content from vector DB
        """
        try:
            # Build filters based on intent
            filters = {}

            # Language filter
            if language and language != "english":
                filters["language"] = language

            # Intent-specific content type filtering
            if intent == "challenges":
                filters["content_type"] = "challenge"
            elif intent == "learning_plan":
                filters["content_type"] = ["learning_plan", "flashcard_set"]
            elif intent == "progress":
                filters["content_type"] = ["conversation", "challenge", "assessment"]
            elif intent == "dna":
                filters["content_type"] = ["conversation", "assessment"]
            # For "general" and "app_help", search all content types

            # PHASE 1 FIX: Enhance query before searching
            enhanced_query = await query_enhancer.enhance_query(
                query=query,
                user_context={
                    'target_language': language,
                    'current_level': None,  # Will be determined from context
                    'learning_goals': None
                }
            )
            logger.info(f"[COACH] Query enhanced: '{query[:40]}...' → {len(enhanced_query.split())} terms")

            # PHASE 3: Choose between hybrid search (BM25 + Semantic) or pure semantic
            if self.use_hybrid_search:
                logger.info(f"[COACH] Hybrid search (BM25 + Semantic) for user {user_id}")
                logger.debug(f"[COACH] Filters: {filters}")

                # Use hybrid search service
                hybrid_results = await hybrid_search_service.hybrid_search(
                    query=enhanced_query,  # PHASE 1 FIX: Use enhanced query
                    user_id=user_id,
                    top_k=20,  # Get more for reranking
                    semantic_weight=0.6,
                    bm25_weight=0.4,
                    filters=filters if filters else None
                )

                matches = hybrid_results.get('matches', [])
                logger.info(f"[COACH] Hybrid search: {hybrid_results['semantic_count']} semantic + {hybrid_results['bm25_count']} BM25 = {len(matches)} fused results")
            else:
                logger.info(f"[COACH] Semantic-only search for user {user_id}")
                logger.debug(f"[COACH] Filters: {filters}")

                # Use traditional semantic search
                matches = await search_user_context(
                    query=enhanced_query,  # PHASE 1 FIX: Use enhanced query
                    user_id=user_id,
                    filters=filters if filters else None
                )
                logger.info(f"[COACH] Semantic search: {len(matches)} results")

            if not matches:
                logger.warning(f"[COACH] No matches found for query")
                return {"matches": [], "total": 0}

            # PHASE 2: Rerank matches using cross-encoder for better precision
            logger.info(f"[COACH] Reranking {len(matches)} matches with cross-encoder")
            matches = await semantic_reranker.rerank(
                query=query,  # Use original query (not enhanced) for reranking
                matches=matches,
                top_k=10  # Return top 10 most relevant
            )
            logger.info(f"[COACH] After reranking: {len(matches)} results (top final_score: {matches[0].get('final_score', 0):.3f})")

            # Format results for LLM consumption
            semantic_context = {
                "matches": matches,
                "total": len(matches),
                "top_match_score": matches[0].get("final_score", matches[0].get("score", 0)) if matches else 0,
                "content_summary": self._summarize_matches(matches)
            }

            top_score = matches[0].get("final_score", matches[0].get("score", 0)) if matches else 0
            logger.info(f"[COACH] Vector search returned {len(matches)} matches (top score: {top_score:.3f})")

            return semantic_context

        except Exception as e:
            logger.error(f"[COACH] Semantic search failed: {str(e)}")
            return {"matches": [], "total": 0, "error": str(e)}

    def _summarize_matches(self, matches: List[Dict[str, Any]]) -> str:
        """
        Summarize semantic matches for LLM prompt

        Args:
            matches: List of semantic search results

        Returns:
            Human-readable summary string
        """
        if not matches:
            return "No relevant content found."

        # Group by content type
        by_type = {}
        for match in matches:
            content_type = match["metadata"].get("content_type", "unknown")
            if content_type not in by_type:
                by_type[content_type] = []
            by_type[content_type].append(match)

        # Build summary
        summary_parts = []
        for content_type, items in by_type.items():
            summary_parts.append(f"{content_type}: {len(items)} items")

        summary = f"Found {len(matches)} relevant items ({', '.join(summary_parts)})"

        # Add top match details
        top = matches[0]
        top_score = top.get('final_score', top.get('score', 0.0))
        summary += f"\nTop match ({top_score:.2f} similarity): {top['text'][:200]}..."

        return summary

    async def chat_with_vector_search(
        self,
        user_id: str,
        language: str,
        user_message: str,
        target_language: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Enhanced chat with vector search

        This method:
        1. Detects intent (same as base)
        2. Gets regular cached context (same as base)
        3. **NEW**: Gets semantic context from vector DB
        4. Combines both contexts for LLM
        5. Generates response with perfect context awareness

        Args:
            user_id: User ID
            language: UI language
            user_message: User's query
            target_language: Learning language
            conversation_history: Previous messages

        Returns:
            Response dict with message, card, intent, etc.
        """
        try:
            logger.info(f"[COACH] Vector-enhanced chat for user {user_id}: '{user_message[:50]}...'")

            # Step 1: Detect intent (reuse base method)
            intent = await self._detect_user_intent(user_message)
            logger.info(f"[COACH] Detected intent: {intent}")

            # Step 2: Get regular cached context (reuse base method)
            cache_key = f"taalcoach:context:{user_id}:{intent}"
            cached_context = None

            if self.redis_client:
                try:
                    cached = await self.redis_client.get(cache_key)
                    if cached:
                        cached_context = json.loads(cached)
                        logger.info(f"[COACH] Cache HIT for user {user_id}, intent={intent}")
                except Exception as e:
                    logger.warning(f"[COACH] Cache read failed: {e}")

            if not cached_context:
                logger.info(f"[COACH] Cache MISS - Fetching context for user {user_id}, intent={intent}")
                cached_context = await get_taalcoach_context_cached(user_id)

                # Cache it
                if self.redis_client and cached_context:
                    try:
                        await self.redis_client.setex(
                            cache_key,
                            self.cache_ttl_seconds,
                            json.dumps(cached_context, default=str)
                        )
                        logger.info(f"[COACH] Cached context for user {user_id}, intent={intent}")
                    except Exception as e:
                        logger.warning(f"[COACH] Cache write failed: {e}")

            # Step 3: **NEW** Get semantic context from vector DB
            semantic_context = await self.get_semantic_context(
                user_id=user_id,
                query=user_message,
                intent=intent,
                language=target_language
            )

            # PHASE 1 FIX: ALWAYS use MongoDB data to SUPPLEMENT vector search (not replace)
            # This provides complete context even when vector search is strong
            logger.info(f"[COACH] Vector search returned {semantic_context['total']} matches "
                       f"(top score: {semantic_context.get('top_match_score', 0):.3f})")

            # PHASE 1 FIX: Always supplement with MongoDB data for complete context
            if cached_context:
                mongodb_sessions = cached_context.get('practice_sessions_details', [])
                if mongodb_sessions:
                        # 🎯 SMART LANGUAGE FILTERING: Detect if query is cross-language
                        query_lower = user_message.lower()
                        cross_language_keywords = [
                            'other language', 'all language', 'different language', 'multiple language',
                            'english', 'spanish', 'french', 'german', 'italian', 'portuguese', 'dutch',
                            'what language', 'how many language', 'which language', 'compare',
                            'not only', 'also practice', 'besides', 'other than'
                        ]
                        is_cross_language_query = any(keyword in query_lower for keyword in cross_language_keywords)

                        # If user asks about other languages, show ALL sessions
                        if is_cross_language_query:
                            fallback_sessions = mongodb_sessions[:15]  # Show more for cross-language
                            filter_info = f"all languages (cross-language query detected)"
                            logger.info(f"[COACH] 🌐 Cross-language query detected - showing {len(fallback_sessions)} sessions across all languages")
                        # Otherwise, filter by target language if specified
                        elif target_language and target_language != 'all':
                            language_sessions = [s for s in mongodb_sessions if s.get('language', '').lower() == target_language.lower()]
                            # If we have language-specific sessions, prioritize them
                            if language_sessions:
                                fallback_sessions = language_sessions[:10]
                                filter_info = f"{target_language} only"
                            else:
                                # Fall back to all sessions if no language match
                                fallback_sessions = mongodb_sessions[:10]
                                filter_info = f"all languages (no {target_language} sessions found)"
                        else:
                            fallback_sessions = mongodb_sessions[:10]  # Top 10 most recent
                            filter_info = "all languages"

                        semantic_context['mongodb_fallback'] = {
                            'sessions': fallback_sessions,
                            'source': 'mongodb_direct',
                            'target_language': target_language,
                            'filter_applied': filter_info,
                            'message': f'Semantic search found {semantic_context["total"]} matches - supplemented with {len(fallback_sessions)} MongoDB sessions'
                        }
                        logger.info(f"[COACH] Added {len(fallback_sessions)} MongoDB sessions as fallback (from {len(mongodb_sessions)} available, filtered for {filter_info})")

            # Step 3.5: **PHASE 2** Analyze learning trajectory
            trajectory_context = None
            try:
                logger.info(f"[COACH] Analyzing learning trajectory for user {user_id}")
                trajectory_context = await trajectory_analyzer.analyze(
                    user_id=user_id,
                    context=cached_context if cached_context else {}
                )
                if trajectory_context and not trajectory_context.get('insufficient_data'):
                    logger.info(f"[COACH] Trajectory analysis complete: trend={trajectory_context.get('trend')}")
                else:
                    logger.debug(f"[COACH] Insufficient data for trajectory analysis")
            except Exception as e:
                logger.warning(f"[COACH] Trajectory analysis failed: {e}")

            # Step 4: Build enhanced prompt with BOTH contexts
            enhanced_prompt = self._build_enhanced_prompt(
                intent=intent,
                query=user_message,
                cached_context=cached_context,
                semantic_context=semantic_context,
                trajectory_context=trajectory_context,
                language=language,
                target_language=target_language
            )

            # Step 5: Generate response using GPT-5.4-mini
            messages = [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": user_message}
            ]

            # Add conversation history if provided
            if conversation_history:
                # Insert history before user message
                messages = [messages[0]] + conversation_history[-4:] + [messages[1]]

            logger.info(f"[COACH] Calling {self.model} with {len(messages)} messages")

            start_time = datetime.now()

            response = openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_completion_tokens=300,
                response_format={"type": "json_object"}
            )

            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            raw_response = response.choices[0].message.content

            logger.info(f"[COACH] Response generated in {response_time_ms}ms ({len(raw_response)} chars)")

            # Parse response (expects JSON)
            try:
                parsed = json.loads(raw_response)
                ai_response = parsed.get("message", raw_response)
                show_card = parsed.get("show_card", "none")
            except json.JSONDecodeError:
                logger.warning(f"[COACH] Response not valid JSON, using as plain text")
                ai_response = raw_response
                show_card = "none"

            # Parse AI response into rich messages (using base class method)
            base_messages = self._parse_response_with_card(ai_response, show_card, cached_context, user_message)

            # ENHANCEMENT: Add inline stats if appropriate (Duolingo-style visual stats)
            # Only enhance text-only responses (preserve cards like progress_card, dna_card)
            if len(base_messages) == 1 and base_messages[0].get('type') == 'text':
                logger.info("[COACH] Checking if inline stats should be shown")
                parsed_messages = inline_stats_formatter.format_response_with_stats(
                    ai_response=ai_response,
                    context=cached_context,
                    user_message=user_message
                )
            else:
                # Keep existing rich messages (cards, celebrations, etc.)
                logger.info(f"[COACH] Preserving rich messages: {[m.get('type') for m in base_messages]}")
                parsed_messages = base_messages

            # ENHANCEMENT: Add challenge cards if appropriate (challenge queries)
            # Check if we should show challenge cards (BEFORE subscription chips!)
            logger.info("[COACH] Checking if challenge cards should be shown")
            if challenge_card_formatter.should_show_challenge_cards(
                user_message=user_message,
                conversation_history=conversation_history
            ):
                logger.info("[COACH] Showing challenge cards")
                challenge_card_data = challenge_card_formatter.format_challenge_cards(
                    user_language=language
                )
                # Add challenge cards as a rich message
                parsed_messages.append(challenge_card_data)
            else:
                # ENHANCEMENT: Add subscription chips if appropriate (pricing queries)
                # Check if we should show subscription upgrade cards (ONLY if NOT showing challenges)
                logger.info("[COACH] Checking if subscription chips should be shown")
                subscription_messages, subscription_tracking = subscription_chip_formatter.format_response_with_subscription_chips(
                    ai_response=ai_response,
                    user_message=user_message,
                    user_context=cached_context,
                    conversation_history=conversation_history
                )

                # If subscription chips were added, use those messages instead
                if subscription_tracking:
                    logger.info(f"[COACH] Subscription chips shown: {subscription_tracking}")
                    parsed_messages = subscription_messages

            # ENHANCEMENT: Add voice profiles if appropriate (AI voice queries)
            # Check if we should show voice profile cards
            logger.info("[COACH] Checking if voice profiles should be shown")
            voice_messages, voice_tracking = voice_profile_formatter.format_response_with_voice_profile(
                ai_response=ai_response,
                user_message=user_message,
                user_context=cached_context
            )

            # If voice profiles were added, use those messages instead
            if voice_tracking:
                logger.info(f"[COACH] Voice profiles shown: {voice_tracking}")
                parsed_messages = voice_messages

            # ENHANCEMENT: Add capability cards for greeting messages
            # Show TaalCoach's capabilities to guide users
            logger.info("[COACH] Checking if capability cards should be shown")
            capability_messages = capability_cards_formatter.format_greeting_with_capabilities(
                ai_response=ai_response,
                user_message=user_message,
                user_context=cached_context
            )

            # If capability cards were added, use those messages
            if len(capability_messages) > 1:  # More than just text means cards were added
                logger.info(f"[COACH] Capability cards shown for greeting")
                parsed_messages = capability_messages

            # Generate quick replies based on AI's response (using base class method)
            quick_replies = self._generate_quick_replies(cached_context, language, ai_response, conversation_history)

            # Build result (same format as base service)
            result = {
                "messages": parsed_messages,
                "quick_replies": quick_replies,
                "raw_response": ai_response,
                "response_time_ms": response_time_ms,
                "intent": intent,
                "semantic_context": {
                    "matches": len(semantic_context.get("matches", [])),
                    "top_score": semantic_context.get("top_match_score", 0),
                    "total": semantic_context.get("total", 0)
                }
            }

            return result

        except Exception as e:
            logger.error(f"[COACH] Vector-enhanced chat failed: {str(e)}")
            # Fallback to base implementation (call parent class, not self!)
            logger.info(f"[COACH] Falling back to base chat implementation")
            return await super().chat(
                user_id=user_id,
                language=language,
                user_message=user_message,
                target_language=target_language,
                conversation_history=conversation_history
            )

    def _build_enhanced_prompt(
        self,
        intent: str,
        query: str,
        cached_context: Dict[str, Any],
        semantic_context: Dict[str, Any],
        trajectory_context: Optional[Dict[str, Any]],
        language: str,
        target_language: str
    ) -> str:
        """
        Build enhanced system prompt with regular + semantic context

        This creates a comprehensive prompt that includes:
        1. Core instructions (same as base)
        2. Regular cached context (stats, plans, etc.)
        3. **NEW**: Semantically relevant content from vector search
        4. **NEW**: Cross-feature correlation hints
        5. **NEW**: Temporal trend information
        """
        # Start with core system prompt
        prompt = f"""You are TaalCoach, an expert AI language progress coach for the MyTacoAI app.

🎯 YOUR SINGULAR PURPOSE:
Help users IMPROVE from their initial assessment level by guiding them through the app's features with expert teaching strategies.

🎓 YOUR EXPERTISE (Language Teaching & Progress Coaching):
You are a certified language teacher + progress coach with deep knowledge of:
- Second Language Acquisition (SLA) theory and methodology
- CEFR levels (A1-C2) and proficiency assessment
- Personalized learning paths and curriculum design
- Speaking DNA analysis and pronunciation improvement
- Motivation and engagement strategies for language learners
- Error correction techniques and formative feedback
- Spaced repetition and memory retention optimization
- Progress tracking and milestone celebration

🎓 EXPERT TEACHING STRATEGIES YOU MUST USE:

**1. Spaced Repetition (Ebbinghaus Forgetting Curve)**:
   - Vocabulary review schedule: Day+1, Day+3, Day+7, Day+14, Day+30
   - Example: "You learned 'restaurant' vocab 3 days ago - review today to cement long-term memory"
   - Always cite specific timing: "Review in 3 days" not "review soon"

**2. Zone of Proximal Development (Vygotsky's i+1)**:
   - Recommend content at current_level + 1 difficulty
   - Example: "You're A2 - try B1 reading with support. A1 is too easy, C1 too frustrating"
   - Optimal challenge: 90-95% comprehension + 5-10% stretch

**3. Comprehensible Input (Krashen)**:
   - Input slightly above current level aids acquisition
   - Example: "Practice sessions should have 90%+ comprehension with new challenges each time"

**4. Output Hypothesis (Swain)**:
   - Speaking/writing production aids language learning
   - Example: "Pronunciation stuck at 70%? Do 10min shadowing (active production), not passive listening"

**5. Error Pattern Analysis**:
   - Identify SYSTEMATIC errors (not random)
   - Example: "You confuse 'de/het' in 67% of cases - article gender issue. Practice minimal pairs: de man/het kind"

**6. Motivation & Self-Efficacy (Dörnyei)**:
   - Celebrate wins, normalize plateaus
   - Example: "15% pronunciation gain in 2 weeks! A2→B1 transition naturally has slower fluency gains"

**7. CEFR Can-Do Descriptors**:
   - Map current abilities to CEFR benchmarks
   - Example: "A2 listening: understand familiar topics. Next B1 goal: main points in clear standard speech"

📱 MYTACOAI APP FEATURES - ACCURATE DETAILS:

**1. Speaking Assessment** (1 minute, 6 languages):
   - Quick 1-minute speaking test to determine CEFR level
   - Available in: English, Spanish, French, German, Italian, Portuguese, Dutch
   - User can pick from predefined subjects/topics
   - This is the FIRST step for new users

**2. Learning Plan** (Created AFTER speaking assessment):

   **PLAN CREATION WORKFLOW**:
   Step 1: User completes 1-minute speaking assessment → Gets CEFR level (A1-C2)
   Step 2: User creates personalized plan:
     - Duration: 1, 2, 3, 6, or 12 months
     - Goals: Travel, Business, Academic, Daily Conversation, Culture (pick 1-3 goals)
     - Sub-goals: Specific scenarios within goals (e.g., Transportation, Accommodation for Travel)
     - Session duration: 3 min (A1/A2 only) or 5 min (B1+)
   Step 3: AI generates weekly schedule:
     - Total sessions: duration_months × 4 weeks × 4 sessions/week
     - Example: 3-month plan = 3 × 4 × 4 = 48 total sessions
     - Each week has 4 sessions with specific focus areas

   **WEEKLY STRUCTURE**:
   Each week contains:
     - Focus area (e.g., "Foundation Building: Addressing grammar weaknesses")
     - Goals (e.g., "Master basic greetings", "Practice pronunciation")
     - Vocabulary list
     - Grammar focus
     - Activities
     - 2 sessions with completion tracking (pending → in_progress → completed)

   **PLAN GENERATION LOGIC** (60% Goals + 40% Skills):
     - 60% of weeks: Focus on user's selected sub-goals
       Example: User picks 3 travel sub-goals → Each gets 2-3 weeks
     - 40% of weeks: General skill development (vocabulary, grammar, fluency)
     - First 4 weeks: ALWAYS focus on biggest weakness from assessment
       Example: Grammar 60%, Vocabulary 75% → Week 1-4 focus on grammar

   **ADAPTIVE OPTIMIZATION** (AI adjusts plan based on performance):
   • Tier 1 (Every Session): Immediate pattern detection
     - Critical weakness detected (score < 50) → Updates next week's focus
     - Repeated errors (same issue 3+ times) → Adds targeted practice
     - Ready to advance (all skills ≥ 85) → Increases complexity

   • Tier 2 (Every 3+ Sessions): Pattern analysis
     - Recurring grammar issues (appear in 40%+ of sessions)
     - Performance trends (improving, declining, stable)
     - Skill dependencies (e.g., vocabulary blocked by low grammar)

   **FINAL ASSESSMENT** (When plan is complete):
     - Triggered automatically when completed_sessions ≥ total_sessions
     - Dual-criteria evaluation:
       1. Current Level Mastery (must score ≥75%)
       2. Next Level Readiness (must score ≥70%)
     - Both must pass to advance to next CEFR level
     - Unlimited retakes allowed (no penalty)

   **PLAN PROGRESS TRACKING**:
     - Shown as: "5 of 20 sessions complete" or "25% progress"
     - Each session completion updates plan's weekly_schedule
     - TaalCoach should reference plan progress in recommendations

**3. Practice Sessions** (Real-time voice conversations with AI tutor):

   **SESSION TYPES**:

   • **Freestyle Practice** (conversation_type: 'practice'):
     - User-initiated topic conversations
     - Unstructured, flexible topics
     - Counted toward: Lifetime stats, daily streaks
     - Examples: "Let's talk about cooking", "Practice ordering at restaurant"

   • **Learning Plan Sessions** (conversation_type: 'learning_plan'):
     - Part of structured 1-12 month curriculum
     - 4 sessions per week with specific focus areas
     - Tracked in: Plan progress (X/Y sessions completed)
     - Examples: Week 1 Session 1 - "Practice greetings and introductions"

   • **News Practice** (conversation_type: 'news'):
     - Discuss daily news articles at user's CEFR level
     - Current events reading + speaking practice
     - Available in all 6 languages
     - Examples: "Discuss climate change article (B1 level)"

   • **Custom Topic** (conversation_type: 'custom'):
     - User provides custom topic + optional AI research
     - Examples: "Teach me medical terminology for pharmacy"

   **DURATION LOGIC** (CRITICAL for recommendations):
     * A1/A2 users: Choose 3 minutes OR 5 minutes (flexible!)
     * B1+ users: 5 minutes only (need longer exposure for complex topics)

   **SESSION ANALYSIS** (What happens after each session):
   - Immediate summary: AI-generated 2-3 sentence recap
   - Enhanced analysis: Strengths, areas for improvement, key phrases learned
   - Sentence-level analysis: Grammar, vocabulary, fluency scores per sentence
   - Speaking DNA (periodic): Acoustic analysis (pitch, energy, pace)
   - Recommendations: Next topics, challenges to try, specific skills to practice

   **CONVERSATION-TO-CHALLENGE RECOMMENDATIONS**:
   After conversations, TaalCoach should recommend specific challenges based on conversation analysis:
   - Grammar errors detected → <<Error Spotting>> + <<Story Builder>>
   - Vocabulary struggles → <<Smart Flashcard>> + <<Micro Quiz>>
   - Hesitation/slow speech → <<Brain Tickler>> + <<Native Check>>
   - Unnatural phrasing → <<Native Check>> + <<Smart Flashcard>>

   Available in all 6 languages (English, Spanish, French, German, Italian, Portuguese, Dutch), all CEFR levels (A1-C2)

**4. Challenges** (7 types - gamified learning exercises):
   ALL CHALLENGES: <<Micro Quiz>>, <<Error Spotting>>, <<Smart Flashcard>>, <<Native Check>>, <<Brain Tickler>>, <<Story Builder>>, <<Swipe Fix>> (backend only)

   **CHALLENGE DETAILS & PURPOSES**:

   • <<Micro Quiz>> (💡 8-15s):
     - Purpose: Fast decision making, rapid vocabulary/grammar recall
     - Pedagogy: Automaticity development (DeKeyser) - builds automatic retrieval
     - When to recommend: Quick confidence boost, basic grammar practice, warm-up before conversations
     - Example: "I ___ to school" → [go, goes, going]

   • <<Error Spotting>> (🔍 10-18s):
     - Purpose: Find and fix grammar/vocabulary errors in sentences
     - Pedagogy: Noticing Hypothesis (Schmidt) - trains conscious error detection
     - When to recommend: User making systematic grammar errors, needs self-correction ability
     - Example A1: "I go yesterday" → Should be "I went yesterday"

   • <<Smart Flashcard>> (🎴 10-18s):
     - Purpose: Vocabulary from YOUR practice sessions (personalized)
     - Pedagogy: Spaced Repetition (Ebbinghaus) - review at increasing intervals
     - When to recommend: After conversations to reinforce vocabulary, low vocabulary DNA scores
     - Spaced intervals: Review in 1 day, 3 days, 7 days, 14 days

   • <<Native Check>> (🃏 10-15s):
     - Purpose: Assess if sentences sound natural - "Would a native say this?"
     - Pedagogy: Pragmatic/Sociolinguistic Competence (Hymes)
     - When to recommend: Good grammar but sounds "textbook", B1+ learners, preparing for real conversations
     - Swipe RIGHT = Natural, LEFT = Odd

   • <<Brain Tickler>> (⚡ 10s TIMED):
     - Purpose: Beat the clock! Rapid decision making under time pressure
     - Pedagogy: Processing Speed (Skehan) - builds fluency under pressure
     - When to recommend: Good accuracy but slow fluency, exam prep, wants gamified challenge
     - Fixed 10-second time limit per question

   • <<Story Builder>> (📖 Variable):
     - Purpose: Drag words to complete the story - contextual grammar practice
     - Pedagogy: Comprehensible Input + Output Hypothesis - grammar in narrative context
     - When to recommend: Needs grammar practice in context (not isolated rules), writing prep
     - Premium drag & drop interface

   • <<Swipe Fix>> (✋ Backend only - NOT in mobile app yet):
     - Status: Defined in backend but not implemented in frontend
     - Purpose: Swipe to correct word order/grammar

   **CHALLENGE-TO-CONVERSATION CORRELATION** (CRITICAL for smart recommendations):

   After conversation with GRAMMAR ERRORS → Recommend: <<Error Spotting>> + <<Story Builder>>
   After conversation with VOCABULARY STRUGGLES → Recommend: <<Smart Flashcard>> + <<Micro Quiz>>
   After conversation with HESITATION/SLOW SPEECH → Recommend: <<Brain Tickler>> + <<Native Check>>
   After conversation with UNNATURAL PHRASING → Recommend: <<Native Check>> + <<Smart Flashcard>>
   After conversation with LOW COMPLEXITY → Recommend: <<Story Builder>> + <<Error Spotting>>

   Before conversation WARM-UP → Recommend: <<Micro Quiz>> (2-3 min quick activation)
   Before conversation TOPIC PREP → Recommend: <<Smart Flashcard>> (restaurant vocab, then conversation)

   **CEFR DIFFICULTY EXAMPLES**:
   - A1: "I go yesterday" (basic tense) → C2: "Data suggests" vs "suggest" (formal precision)
   - A1: Simple present tense → C2: Subjunctive mood, advanced nuance

   IMPORTANT: When mentioning challenge types to users, use natural Title Case with << >> markers:
   - Use << >> markers: "Try <<Micro Quiz>> on Dutch A1"
   - Make names flow: "Start with <<Error Spotting>>, then <<Micro Quiz>>"
   - NEVER use underscores: "micro_quiz" ❌
   - NEVER use markdown: "**Micro Quiz**" ❌
   - NEVER use all caps: "MICRO QUIZ" ❌ (looks aggressive)

**5. Flashcards** (Review vocabulary from learning plans):
   - Created from practice sessions and challenges
   - Spaced repetition for retention

**6. Speaking DNA** (Deep Acoustic Analysis - Premium):
   - Periodic deep dive analysis of pronunciation, fluency, confidence
   - System adapts learning plan based on DNA insights
   - Tracks improvement over time

**7. Daily News** (Reading practice at user's level):
   - Real news articles adapted to CEFR level
   - All 6 languages available

**8. AI VOICE CHARACTERS** (8 distinct voice personalities):
   Users can select their preferred AI tutor voice from Profile → AI Tutor Voice.

   **AVAILABLE VOICES** (with personality traits):

   • **Alloy** 🎯 - Balanced & Neutral
     - Even-toned, professional, clear enunciation
     - Best for: All levels, professional/business contexts, those who prefer minimal personality
     - Teaching style: Straightforward, factual, objective

   • **Ash** 🌟 - Warm & Encouraging (DEFAULT VOICE)
     - Soft, reassuring, patient, friendly
     - Best for: Beginners (A1-A2), anxious learners, those needing confidence building
     - Teaching style: Supportive, celebrates small wins, patient guidance

   • **Ballad** 🎵 - Melodic & Expressive
     - Lyrical, rhythmic, musical intonation
     - Best for: Creative learners, musicians, pronunciation practice (A2-B2)
     - Teaching style: Uses rhythm and melody to aid memory

   • **Coral** 🌺 - Bright & Friendly
     - Upbeat, cheerful, energetic, enthusiastic
     - Best for: Young learners, morning practice, conversational practice (A2-B2)
     - Teaching style: Energetic, fun, makes learning feel like play

   • **Echo** 🔊 - Clear & Articulate ⭐ PRONUNCIATION SPECIALIST
     - Crystal-clear enunciation, precise pronunciation, deliberate pacing
     - Best for: Pronunciation work (ALL levels), beginners learning sounds, advanced perfecting accent
     - Teaching style: Focus on accuracy, pronunciation, and proper form

   • **Sage** 🧘 - Wise & Patient
     - Calm, measured, thoughtful, mature, contemplative
     - Best for: Advanced learners (B2-C2), deep conversations, mature learners (40+)
     - Teaching style: Reflective, encourages critical thinking, provides cultural context

   • **Shimmer** ✨ - Dynamic & Energetic ⭐ MOTIVATION BOOSTER
     - High energy, enthusiastic, animated, motivational
     - Best for: Maintaining motivation during plateaus, competitive learners, short intense sessions
     - Teaching style: High-energy, motivational, gamified approach

   • **Verse** 📜 - Poetic & Smooth
     - Smooth, flowing, elegant, literary, sophisticated
     - Best for: Literature enthusiasts, advanced learners (B2-C2), reading/storytelling practice
     - Teaching style: Literary, focuses on beauty of language, uses storytelling

   **VOICE RECOMMENDATIONS BY LEVEL**:
   - A1 (Beginner): Ash (warm encouragement), Echo (clear pronunciation), Coral (friendly energy)
   - A2 (Elementary): Ash, Echo, Ballad (musical patterns)
   - B1 (Intermediate): Coral (conversational), Ballad (fluency), Alloy (professional prep)
   - B2 (Upper Intermediate): Sage (nuance), Verse (sophistication), Shimmer (motivation)
   - C1 (Advanced): Sage (deep discussions), Verse (artistry), Echo (accent perfection)
   - C2 (Mastery): Verse (language beauty), Sage (philosophical), Alloy (professional polish)

   **VOICE RECOMMENDATIONS BY GOAL**:
   - Pronunciation improvement → **Echo** (best choice)
   - Conversation fluency → Coral, Ballad, Shimmer
   - Professional/Business → **Alloy** (best choice)
   - Creative expression → **Verse** (best choice)
   - Building confidence → **Ash** (best choice)
   - Overcoming plateau → **Shimmer** (best choice)

   **HOW TO CHANGE VOICE**:
   Navigation: Profile tab (bottom) → AI Tutor Voice → Select voice → Save Preference

   **WHEN USER ASKS ABOUT VOICES**:
   - List all 8 voices with brief personality traits
   - Recommend based on: user's level, learning goals, learning trajectory (plateaus → Shimmer)
   - Provide navigation instructions if they want to change
   - If user asks "what voice do I have?", check user profile for selected_voice field

💳 SUBSCRIPTION PLANS (IMPORTANT - Be accurate!):

**4 PLAN TIERS** (Try & Learn → Fluency Builder → Language Mastery → Team Mastery):

**1. TRY & LEARN** (FREE):
   - 💰 Cost: FREE forever
   - ⏱️ Practice Minutes: Limited (must earn via challenges/watching ads)
   - ❤️ Hearts: 5 hearts per challenge type (separate pools for each challenge)
   - ⏳ Heart Refill: 3 hours per heart (SLOW refill)
   - 🎯 Best for: Beginners, casual learners, trying out the app

**2. FLUENCY BUILDER** (Most Popular):
   - 💰 Monthly: €19.99/month
   - 💰 Annual: €119.00/year (~€9.92/month) - SAVE €120.88 (50% OFF!)
   - ⏱️ Practice Minutes: 150 minutes/month
   - ❤️ Hearts: 10 hearts per challenge type (separate pools)
   - ⏳ Heart Refill: 1 hour per heart (faster than free)
   - 🎁 3-day FREE TRIAL (annual plan only)
   - 🎯 Best for: Regular learners, 2-3 sessions per week, structured practice

**3. LANGUAGE MASTERY** (Top Tier - Unlimited):
   - 💰 Monthly: €39.99/month
   - 💰 Annual: €239.00/year (~€19.92/month) - SAVE €240.88 (50% OFF!)
   - ⏱️ Practice Minutes: UNLIMITED (practice as much as you want!)
   - ❤️ Hearts: UNLIMITED (no heart system restrictions)
   - ⏳ Heart Refill: Instant/unlimited (no waiting!)
   - 🎁 3-day FREE TRIAL (annual plan only)
   - 🎯 Best for: Serious learners, daily practice, preparing for exams/interviews

**4. TEAM MASTERY** (Legacy Plan):
   - Same features as Language Mastery (unlimited minutes, unlimited hearts)
   - No longer available for new subscriptions
   - Existing subscribers keep their legacy pricing

**❤️ HEART SYSTEM EXPLAINED** (Focus Energy for Challenges):

Free users have SEPARATE heart pools for each challenge type:
- <<Micro Quiz>> pool: 5 hearts (3-hour refill)
- <<Error Spotting>> pool: 5 hearts (3-hour refill)
- <<Smart Flashcard>> pool: 5 hearts (3-hour refill)
- <<Native Check>> pool: 5 hearts (3-hour refill)
- <<Brain Tickler>> pool: 5 hearts (3-hour refill)
- <<Story Builder>> pool: 5 hearts (3-hour refill)

Example: If user runs out of hearts in <<Micro Quiz>>, they can still play <<Error Spotting>> with full hearts!

**HEART MECHANICS**:
- ✅ Correct answer: Keep your heart
- ❌ Wrong answer: Lose 1 heart
- 🛡️ Streak Shield: 5 correct in a row = shield (protects from next wrong answer)
- ↩️ Undo Button: 1-second window to undo wrong answer (prevents heart loss)
- 💎 Premium Users: 10 hearts (Fluency Builder) or UNLIMITED (Language Mastery)

**PRICING GUIDANCE** (When users ask about pricing):

When user asks "What are the prices?" or "Tell me about premium plans":
1. Start with annual plans (50% savings!)
2. Highlight 3-day FREE TRIAL for annual plans
3. Compare features side-by-side:
   - Fluency Builder: 150 min/month, 10 hearts, 1-hr refill - €119/year
   - Language Mastery: UNLIMITED min, UNLIMITED hearts - €239/year
4. Recommend based on usage:
   - Casual learner (2-3 sessions/week) → Fluency Builder
   - Daily learner (4+ sessions/week) → Language Mastery
5. Always mention: "Both annual plans have 3-day FREE TRIAL - cancel anytime!"

**UPGRADE PATHS**:
- Free → Fluency Builder: Most common upgrade (150 min usually enough)
- Fluency Builder → Language Mastery: When hitting 150-min limit or running out of hearts
- Monthly → Annual: When user wants 50% savings (annual is ALWAYS cost-effective!)

🎓 YOUR COACHING APPROACH (Based on Their Journey):
STEP 1: Speaking Assessment (1 min) → User discovers initial level (A1-C2)
STEP 2: Learning Plan Creation (1-12 months) → Structured curriculum
   - A1/A2 users choose: 3 min OR 5 min sessions (flexible!)
   - B1+ users: 5 min sessions only
STEP 3: Progress Tracking → Monitor DNA analysis, session completion, challenge accuracy
STEP 4: Adaptive Guidance → System adapts plan based on Speaking DNA insights
STEP 5: Recommend NEXT STEPS based on:
   - Learning plan progress (X of Y sessions completed)
   - DNA analysis trends (pronunciation, fluency, confidence improving?)
   - Challenge performance (accuracy %, struggle areas)
   - Practice consistency (daily streak, speaking minutes used)
   - Weak skills identification (what needs more practice?)

💡 YOUR GUIDANCE PHILOSOPHY:
- **Data-Driven**: Use assessment results, DNA analysis, session data to give specific advice
- **Proactive**: Don't just answer questions - suggest NEXT ACTIONS
- **Feature-Focused**: Guide users to the RIGHT app feature for their current need
- **Progress-Oriented**: Always tie advice back to improving from initial level
- **Encouraging**: Celebrate wins, normalize struggles, maintain growth mindset
- **Theory-Grounded**: ALWAYS cite a teaching strategy when giving advice (Spaced Repetition, ZPD, etc.)
- **Specific Numbers**: Give exact timings ("review in 3 days"), percentages ("73% accuracy"), counts ("5 sessions")

🎨 DUOLINGO-STYLE VISUAL DESIGN (CRITICAL):
The mobile app displays user statistics as VISUAL STAT CHIPS (not text).
These chips appear automatically when you mention numbers/stats in your response.

**PURE STATISTICS QUERIES** (CRITICAL - NEW RULE):
When user asks ONLY for statistics ("show me statistics", "my progress", "my stats"):
- Respond with MINIMAL text or just "✓" (the app will show stat cards automatically)
- DO NOT list the stats in text (they're shown as visual cards)
- Examples:
  User: "Show me statistics" → AI: "✓"
  User: "My progress?" → AI: "Here you go!"
  User: "What are my stats?" → AI: "Looking good!"

**GREETING MESSAGES** (start_greeting_*) - CRITICAL RULE:
🚨 NEVER SUGGEST SPECIFIC ACTIONS IN GREETINGS! 🚨

- Keep it SHORT: Warm greeting + generic help offer (8-12 words MAX)
- ALWAYS use user's name if available (e.g., "Welcome back, Sarah!")
- NEVER mention challenges, quizzes, or any specific activities
- NEVER suggest "Try X" or "Do Y" - the app shows 6 clickable capability cards for that
- DO offer generic help (e.g., "I can help with anything you need!")
- The app automatically shows interactive cards - your job is greeting + help offer!

MANDATORY Greeting Format:
"[Greeting]! [Generic help offer or encouragement]"

GOOD Greeting Examples (COPY THESE):
✅ "Welcome back! I'm here to help with anything you need!"
✅ "Hey there! Ask me anything about your learning journey!"
✅ "Hi! I can help with progress, practice tips, and more!"
✅ "Welcome back! What would you like to know today?"

FORBIDDEN Greeting Examples (NEVER DO THIS):
❌ "Welcome back! Try Micro Quiz on Dutch A1 today." ← WRONG! No activity suggestions!
❌ "Great to see you! Try Error Spotting next." ← WRONG! No recommendations!
❌ "Welcome back! Do a <<Micro Quiz>> today." ← WRONG! No challenge mentions!
❌ "Hi! Start with pronunciation practice." ← WRONG! No specific actions!

Remember: The 6 capability cards are CLICKABLE and will guide the user. Your greeting should offer GENERIC help only.

📝 FORMATTING RULES (CRITICAL):
- NEVER use markdown formatting (**bold**, *italic*, etc.) - the mobile app doesn't support it
- Challenge names: Wrap in << >> markers for bold rendering
  GOOD: "Try <<Micro Quiz>> on Dutch A1 today"
  GOOD: "Start with <<Error Spotting>>, then <<Micro Quiz>>"
  BAD: "Try MICRO QUIZ" (all caps looks aggressive)
  BAD: "Try **Micro Quiz**" (markdown doesn't work)
- Use Title Case for challenge names: Micro Quiz, Error Spotting, Swipe Fix, Brain Tickler, Story Builder, Smart Flashcard, Native Check
- Challenge names to wrap in << >>:
  • <<Micro Quiz>>
  • <<Error Spotting>>
  • <<Swipe Fix>>
  • <<Brain Tickler>>
  • <<Story Builder>>
  • <<Smart Flashcard>>
  • <<Native Check>>
- Make names flow naturally in sentences
- Lists: Use simple "1) item" or "• item", NOT markdown lists

RESPONSE RULES:
- Maximum 1-2 SHORT sentences (25 words ABSOLUTE MAX) - be ultra-concise
- For GREETINGS: 1 sentence MAX (10 words or less) - let visual chips show the stats
- For RECOMMENDATIONS: 1 clear sentence with the action - no explanations
- ANSWER ONLY WHAT'S ASKED: If user asks "list challenges", ONLY list challenges - do NOT add extra suggestions
- DO NOT add unsolicited advice: "then do X" or "plus Y" unless user explicitly asks "what should I do?"
- Use user's REAL data: assessment level, DNA scores, session topics, challenge accuracy
- NO theory explanations unless specifically asked - just the action
- Output JSON: {{"message": "text", "show_card": "..."}}

🎯 WHEN GIVING GUIDANCE, ALWAYS:
1. Reference their INITIAL ASSESSMENT level (from speaking_dna or assessments)
2. Show CURRENT PROGRESS (learning plan completion %, DNA improvements, streak)
3. Identify NEXT STEP (specific session topic, challenge type, or feature to use)
4. Explain WHY (SLA principle: comprehensible input, spaced repetition, etc.)

EXAMPLE RESPONSES (ULTRA-CONCISE DUOLINGO STYLE):

Query: "What challenges should I try?"
❌ BAD: "Try **Micro Quiz** and **Error Spotting** first at A1 level—your 0% challenge accuracy means you need easier, high-success practice (Krashen: 90%+ comprehension). Review the same Dutch items again in **1 day, 3 days, and 7 days** for spaced repetition, then move to **Swipe Fix** once accuracy improves."
❌ BAD: "Start with MICRO QUIZ and ERROR SPOTTING at A1" (all caps looks aggressive)
✅ GOOD: "Try <<Micro Quiz>> and <<Error Spotting>> at A1 for easier practice."
✅ ALSO GOOD: "Start with <<Micro Quiz>>, then <<Error Spotting>>."

Query: "Show me my progress"
❌ BAD: "You've completed 5 of 20 learning plan sessions which is 25% progress following Zone of Proximal Development principles. You should focus on restaurant ordering at B1 level because it stretches your A2 skills appropriately."
✅ GOOD: "5 of 20 sessions complete. Try 'restaurant ordering' next!"

Query: "Welcome back" (greeting)
❌ BAD: "Welcome back! You're A1 (0%) with a 6-day streak and 6 sessions (18 minutes). Your pronunciation is the weakest area (0%), so use a short speaking session for pronunciation—Output Hypothesis: active speaking beats passive review."
❌ BAD: "Welcome back! Try MICRO QUIZ on Dutch A1 today." (all caps)
✅ GOOD: "Welcome back! Ready for a 3-minute pronunciation practice?"
✅ ALSO GOOD: "Welcome back! Try <<Micro Quiz>> on Dutch A1 today."

Query: "List all challenges" (information request)
❌ BAD: "<<Micro Quiz>>, <<Error Spotting>>, <<Swipe Fix>>, <<Brain Tickler>>, <<Story Builder>>, <<Smart Flashcard>>, <<Native Check>>, then try a 3-minute pronunciation practice." (added unsolicited suggestion)
❌ BAD: "Try these: <<Micro Quiz>>, <<Error Spotting>>..." (user asked for list, not recommendation)
✅ GOOD: "<<Micro Quiz>>, <<Error Spotting>>, <<Swipe Fix>>, <<Brain Tickler>>, <<Story Builder>>, <<Smart Flashcard>>, <<Native Check>>."
✅ ALSO GOOD: "All challenges: <<Micro Quiz>>, <<Error Spotting>>, <<Swipe Fix>>, <<Brain Tickler>>, <<Story Builder>>, <<Smart Flashcard>>, <<Native Check>>."

CRITICAL FORMAT RULES:
- NO markdown (**bold**, *italic*) - just plain text
- Challenge names: "Micro Quiz" not "**Micro Quiz**"
- 1-2 sentences MAX (25 words absolute limit)
- Action-focused, not theory-heavy
- Let visual stat chips show the numbers

⚠️ CRITICAL: NEVER MAKE UP NUMBERS OR DATA
- ONLY use numbers from context: assessment scores, DNA metrics, session counts, challenge accuracy
- Use practice_sessions_topics and practice_sessions_details to answer topic questions
- If data is missing, guide to START: "Complete a Speaking Assessment first to unlock your learning plan."

⚠️ NEVER SAY "I don't have data" WHEN DATA EXISTS
- CHECK practice_sessions_details, practice_sessions_topics, speaking_dna, assessments, learning_plans
- CHECK mongodb_fallback sessions if vector search found nothing
- If sessions exist but details limited: "You have X sessions - check [feature] for details on what to practice next."

⚠️ LEARNING PLAN CONTEXT:
- Users create learning plans AFTER speaking assessment
- Learning plans have: total_sessions, completed_sessions, plan_objective, goal, level
- Always tie guidance back to learning plan progress and objective

User is asking in: {language}
Learning language: {target_language}
Query intent: {intent}

"""

        # Add regular cached context (reuse base logic)
        if intent == "progress":
            prompt += self._add_progress_context(cached_context)
        elif intent == "learning_plan":
            prompt += self._add_learning_plan_context(cached_context)
        elif intent == "challenges":
            prompt += self._add_challenges_context(cached_context)
        elif intent == "dna":
            prompt += self._add_dna_context(cached_context)
        elif intent == "app_help":
            prompt += self._add_app_help_context(cached_context)
        else:  # general
            prompt += self._add_general_context(cached_context)

        # **NEW**: Add semantic context from vector search
        matches = semantic_context.get("matches", [])
        if matches:
            prompt += f"\n\n🔍 SEMANTICALLY RELEVANT CONTENT (sorted by relevance):\n"
            prompt += f"Found {len(matches)} items matching user's query.\n\n"

            for i, match in enumerate(matches[:5], 1):  # Top 5 matches
                metadata = match.get("metadata", {})
                text = match.get("text", "")
                score = match.get("score", 0)

                prompt += f"{i}. {metadata.get('content_type', 'unknown').upper()} "
                prompt += f"(relevance: {score:.0%})\n"
                prompt += f"   {text[:300]}...\n"

                # Add metadata hints
                if metadata.get("created_at"):
                    prompt += f"   Date: {metadata['created_at'][:10]}\n"
                if metadata.get("language"):
                    prompt += f"   Language: {metadata['language']}\n"
                if metadata.get("is_correct") is not None:
                    prompt += f"   Result: {'✓ correct' if metadata['is_correct'] else '✗ incorrect'}\n"

                prompt += "\n"

        # **NEW**: Add MongoDB fallback data if vector search was weak
        mongodb_fallback = semantic_context.get("mongodb_fallback")
        if mongodb_fallback:
            sessions = mongodb_fallback.get('sessions', [])
            prompt += f"\n\n📋 PRACTICE SESSIONS FROM DATABASE (Recent sessions - use this data!):\n"
            prompt += f"IMPORTANT: These are REAL user sessions. Use this data to answer topic questions!\n\n"

            for i, session in enumerate(sessions[:8], 1):  # Top 8 most recent
                prompt += f"{i}. {session.get('topic', 'conversation')} - {session.get('language', 'unknown')} ({session.get('level', 'unknown')})\n"
                prompt += f"   Date: {session.get('date', 'unknown')}\n"
                if session.get('highlights'):
                    prompt += f"   Highlights: {', '.join(session['highlights'][:2])}\n"
                if session.get('vocabulary'):
                    prompt += f"   Vocabulary: {', '.join(session['vocabulary'][:3])}\n"
                prompt += f"   Duration: {session.get('duration_minutes', 0)} min\n\n"

            prompt += f"USE THIS SESSION DATA to answer the user's question!\n"

        # **NEW**: Add cross-feature correlation hints
        if matches and len(matches) >= 2:
            content_types = set(m["metadata"].get("content_type") for m in matches)
            if len(content_types) > 1:
                prompt += f"\n💡 CROSS-FEATURE INSIGHT:\n"
                prompt += f"User's query relates to multiple features: {', '.join(content_types)}\n"
                prompt += f"Consider connections between these activities when responding.\n"

        # **NEW**: Add temporal trend information
        if matches and intent in ["progress", "general"]:
            prompt += self._add_temporal_trends(matches)

        # **PHASE 2**: Add learning trajectory analysis
        if trajectory_context and not trajectory_context.get('insufficient_data'):
            prompt += trajectory_analyzer.format_for_prompt(trajectory_context)

        # **CRITICAL**: Add progress coaching summary
        # Pass target_language in context for language-specific level detection
        context_with_lang = {**cached_context, "target_language": target_language} if cached_context else {"target_language": target_language}
        prompt += self._build_progress_coaching_summary(context_with_lang, intent)

        prompt += f"\n\n🎯 NOW ANSWER THE USER'S QUESTION: \"{query}\"\n"
        prompt += f"Remember:\n"
        prompt += f"1. Give SPECIFIC next action (which feature, what to practice)\n"
        prompt += f"2. Reference their REAL data (assessment, DNA, sessions, challenges)\n"
        prompt += f"3. Explain WHY (SLA principle, learning science)\n"
        prompt += f"4. Keep it SHORT (2-3 sentences, 40 words max)\n"

        return prompt

    def _add_temporal_trends(self, matches: List[Dict]) -> str:
        """
        Analyze temporal trends from semantic matches

        Args:
            matches: Semantic search results with timestamps

        Returns:
            Prompt section with trend analysis
        """
        try:
            # Extract dates from matches
            dated_matches = []
            for match in matches:
                created_at = match["metadata"].get("created_at")
                if created_at:
                    try:
                        date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        dated_matches.append((date, match))
                    except:
                        continue

            if len(dated_matches) < 2:
                return ""

            # Sort by date
            dated_matches.sort(key=lambda x: x[0])

            # Calculate trends
            oldest = dated_matches[0][0]
            newest = dated_matches[-1][0]
            span_days = (newest - oldest).days

            if span_days < 7:
                return ""

            # Group by week
            week_counts = {}
            for date, match in dated_matches:
                week = date.strftime("%Y-W%W")
                week_counts[week] = week_counts.get(week, 0) + 1

            if len(week_counts) < 2:
                return ""

            # Calculate week-over-week trend
            weeks = sorted(week_counts.keys())
            recent_week = week_counts[weeks[-1]]
            prev_week = week_counts[weeks[-2]] if len(weeks) > 1 else recent_week

            trend = ""
            if recent_week > prev_week:
                pct_increase = ((recent_week - prev_week) / prev_week) * 100
                trend = f"📈 TREND: Activity increased {pct_increase:.0f}% in last week ({prev_week} → {recent_week} items)\n"
            elif recent_week < prev_week:
                pct_decrease = ((prev_week - recent_week) / prev_week) * 100
                trend = f"📉 TREND: Activity decreased {pct_decrease:.0f}% in last week ({prev_week} → {recent_week} items)\n"
            else:
                trend = f"➡️  TREND: Consistent activity (steady at {recent_week} items/week)\n"

            return f"\n\n{trend}"

        except Exception as e:
            logger.warning(f"[COACH] Failed to calculate trends: {e}")
            return ""

    def _build_progress_coaching_summary(self, context: Dict, intent: str) -> str:
        """
        Build a concise progress coaching summary highlighting:
        - Initial assessment level
        - Current progress (learning plan, DNA, sessions)
        - Recommended next steps

        This helps TaalCoach give actionable, data-driven guidance
        """
        if not context:
            return ""

        summary = "\n\n" + "="*80 + "\n"
        summary += "🎯 PROGRESS COACHING SUMMARY (Use this to guide your response!)\n"
        summary += "="*80 + "\n\n"

        # 1. Initial Assessment & Current Level
        assessments = context.get("assessments", {})
        speaking_dna = context.get("speaking_dna", {})

        # Determine user's current level
        current_level = None
        if assessments.get("total_count", 0) > 0:
            recent = assessments.get("recent_scores", [])
            if recent:
                latest = recent[0]
                current_level = latest.get('level')
                summary += f"📊 INITIAL ASSESSMENT:\n"
                summary += f"   Level: {current_level}\n"
                summary += f"   Score: {latest.get('score', 0)}%\n"
                summary += f"   Date: {latest.get('date', 'unknown')}\n\n"

        # If no assessment, infer from recent sessions for the target language
        if not current_level:
            sessions = context.get("practice_sessions_details", [])
            target_lang = context.get("target_language")

            if sessions:
                # Filter by target language if specified
                language_sessions = sessions
                if target_lang and target_lang != 'all':
                    language_sessions = [s for s in sessions if s.get('language', '').lower() == target_lang.lower()]

                # Get most recent session with a valid level for this language
                for session in (language_sessions if language_sessions else sessions):
                    level = session.get('level')
                    if level and level != 'unknown':
                        current_level = level
                        lang = session.get('language', 'unknown')
                        summary += f"📊 CURRENT LEVEL (from recent {lang} sessions):\n"
                        summary += f"   Level: {current_level}\n"
                        summary += f"   Language: {lang}\n\n"
                        break

        # 2. Learning Plan Progress
        learning_plans = context.get("learning_plans", [])
        if learning_plans:
            for plan in learning_plans[:1]:  # Most recent plan
                completed = plan.get("completed_sessions", 0)
                total = plan.get("total_sessions", 0)
                if total > 0:
                    progress_pct = (completed / total) * 100
                    summary += f"📚 LEARNING PLAN PROGRESS:\n"
                    summary += f"   Objective: {plan.get('plan_objective', 'N/A')}\n"
                    summary += f"   Progress: {completed}/{total} sessions ({progress_pct:.0f}%)\n"
                    summary += f"   Language: {plan.get('language', 'N/A')} - Level: {plan.get('level', 'N/A')}\n"

                    if progress_pct < 25:
                        summary += f"   ⚠️  EARLY STAGE - Guide them to complete more sessions\n"
                    elif progress_pct < 50:
                        summary += f"   ✅ BUILDING MOMENTUM - Encourage consistency\n"
                    elif progress_pct < 75:
                        summary += f"   💪 SOLID PROGRESS - Identify weak areas to focus\n"
                    else:
                        summary += f"   🎉 NEARLY COMPLETE - Prepare for level assessment\n"
                    summary += "\n"

        # 3. Speaking DNA Progress
        if speaking_dna.get("has_profile"):
            latest_profile = speaking_dna.get("latest_profile")
            if latest_profile:
                summary += f"🧬 SPEAKING DNA (Current Scores):\n"
                summary += f"   Pronunciation: {latest_profile.get('pronunciation', 0)}%\n"
                summary += f"   Fluency: {latest_profile.get('fluency', 0)}%\n"
                summary += f"   Confidence: {latest_profile.get('confidence', 0)}%\n"
                summary += f"   Vocabulary: {latest_profile.get('vocabulary', 0)}%\n"
                summary += f"   Grammar: {latest_profile.get('grammar', 0)}%\n"

                # Identify weakest area
                scores = {
                    "pronunciation": latest_profile.get('pronunciation', 0),
                    "fluency": latest_profile.get('fluency', 0),
                    "confidence": latest_profile.get('confidence', 0),
                    "vocabulary": latest_profile.get('vocabulary', 0),
                    "grammar": latest_profile.get('grammar', 0)
                }
                weakest = min(scores, key=scores.get)
                summary += f"   ⚠️  WEAKEST AREA: {weakest.upper()} ({scores[weakest]}%)\n"
                summary += f"   💡 RECOMMEND: Practice sessions focusing on {weakest}\n\n"

        # 4. Practice Session Topics
        topics = context.get("practice_sessions_topics", [])
        if topics:
            unique_topics = list(set([t.get('topic', 'conversation') for t in topics]))
            summary += f"📝 TOPICS PRACTICED ({len(topics)} sessions):\n"
            summary += f"   {', '.join(unique_topics[:5])}\n"
            summary += f"   💡 RECOMMEND: Vary topics for broader vocabulary\n\n"

        # 5. Challenge Performance
        challenges = context.get("challenges", {})
        if challenges.get("total_completed", 0) > 0:
            total = challenges["total_completed"]
            correct = challenges.get("total_correct", 0)
            accuracy = (correct / challenges.get("total_questions", 1)) * 100 if challenges.get("total_questions", 0) > 0 else 0

            summary += f"🎮 CHALLENGE PERFORMANCE:\n"
            summary += f"   Total Completed: {total}\n"
            summary += f"   Accuracy: {accuracy:.0f}%\n"

            if accuracy < 60:
                summary += f"   ⚠️  LOW ACCURACY - Recommend easier challenges or review\n"
            elif accuracy < 75:
                summary += f"   ✅ GOOD - Keep practicing for mastery\n"
            else:
                summary += f"   🎉 EXCELLENT - Ready for harder challenges\n"
            summary += "\n"

        # 6. Engagement & Consistency
        stats = context.get("stats", {})
        streak = stats.get("current_streak", 0)
        total_sessions = stats.get("total_sessions", 0)

        summary += f"📈 ENGAGEMENT:\n"
        summary += f"   Current Streak: {streak} days\n"
        summary += f"   Total Sessions: {total_sessions}\n"

        if streak == 0:
            summary += f"   ⚠️  NO STREAK - Encourage daily practice for spaced repetition\n"
        elif streak < 7:
            summary += f"   💪 BUILDING HABIT - Encourage to reach 7-day streak\n"
        else:
            summary += f"   🔥 STRONG HABIT - Celebrate and maintain momentum\n"

        summary += "\n" + "="*80 + "\n"

        return summary

    def _add_progress_context(self, context: Dict) -> str:
        """Add progress-specific context (reuse from base)"""
        prompt = "\nUSER PROGRESS DATA:\n"
        prompt += f"Total sessions: {context.get('total_sessions', 0)}\n"
        prompt += f"Total minutes: {context.get('total_minutes', 0)}\n"
        prompt += f"Current streak: {context.get('current_streak', 0)} days\n"

        # Add speaking time if available
        speaking_time = context.get("speaking_time", {})
        if speaking_time.get("total_speaking_minutes", 0) > 0:
            prompt += f"Speaking time: {speaking_time['total_speaking_minutes']} minutes\n"

        # Add assessments
        assessments = context.get("assessments", {})
        if assessments.get("total_count", 0) > 0:
            prompt += f"Assessments: {assessments['total_count']} taken, avg score {assessments.get('average_score', 0)}%\n"

        return prompt

    def _add_learning_plan_context(self, context: Dict) -> str:
        """Add learning plan context"""
        prompt = "\nLEARNING PLAN DATA:\n"

        learning_plan = context.get("learning_plan")
        if learning_plan:
            prompt += f"Plan: {learning_plan.get('language')} {learning_plan.get('level')}\n"
            prompt += f"Progress: {learning_plan.get('completed_sessions', 0)}/{learning_plan.get('total_sessions', 0)} sessions\n"

            if learning_plan.get("plan_objective"):
                prompt += f"Plan Goal: {learning_plan['plan_objective']}\n"

        # Add flashcards
        flashcards = context.get("flashcards", {})
        if flashcards.get("total_sets", 0) > 0:
            prompt += f"Flashcard sets: {flashcards['total_sets']}\n"

        # Add personal learning goals
        personal_goals = context.get("learning_goals", {})
        if personal_goals.get("active_goals"):
            prompt += f"Personal Goals (separate from plan): {len(personal_goals['active_goals'])} active\n"

        return prompt

    def _add_challenges_context(self, context: Dict) -> str:
        """Add challenges context"""
        prompt = "\nCHALLENGES DATA:\n"
        prompt += "User has completed various challenge types.\n"

        # Add flashcards (often related to challenges)
        flashcards = context.get("flashcards", {})
        if flashcards.get("total_sets", 0) > 0:
            prompt += f"Flashcard sets: {flashcards['total_sets']}\n"

        return prompt

    def _add_dna_context(self, context: Dict) -> str:
        """Add Speaking DNA context"""
        prompt = "\nSPEAKING DNA DATA:\n"
        prompt += "Speaking analysis tracks pronunciation, fluency, vocabulary, grammar.\n"

        assessments = context.get("assessments", {})
        if assessments.get("total_count", 0) > 0:
            prompt += f"Assessments: {assessments['total_count']} taken, avg {assessments.get('average_score', 0)}%\n"

        return prompt

    def _add_app_help_context(self, context: Dict) -> str:
        """Add app features context"""
        prompt = "\nAVAILABLE FEATURES:\n"
        prompt += "Conversations, Challenges, Learning Plans, Flashcards, Assessments, Speaking DNA\n"

        features = context.get("features_available", [])
        if features:
            prompt += f"Plan features: {', '.join(features)}\n"

        return prompt

    def _add_general_context(self, context: Dict) -> str:
        """Add general context"""
        prompt = "\nUSER OVERVIEW:\n"
        prompt += f"Sessions: {context.get('total_sessions', 0)}\n"
        prompt += f"Minutes: {context.get('total_minutes', 0)}\n"
        prompt += f"Streak: {context.get('current_streak', 0)} days\n"

        # Add most relevant high-level stats
        flashcards = context.get("flashcards", {})
        if flashcards.get("total_sets", 0) > 0:
            prompt += f"Flashcards: {flashcards['total_sets']} sets\n"

        assessments = context.get("assessments", {})
        if assessments.get("total_count", 0) > 0:
            prompt += f"Assessments: {assessments['total_count']} taken\n"

        return prompt


# Global instance
coach_service_vector_enhanced = VectorEnhancedCoachService()
