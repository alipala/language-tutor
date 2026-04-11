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
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from services.coach_service_optimized import CoachService as BaseCoachService
from services.vector_db_service import vector_db, search_user_context

logger = logging.getLogger(__name__)


class VectorEnhancedCoachService(BaseCoachService):
    """
    Enhanced TaalCoach with vector search capabilities

    Inherits all functionality from base CoachService and adds:
    - Semantic search for finding relevant user content
    - Cross-feature correlation analysis
    - Temporal trend detection
    - Hybrid search with recency boost
    """

    def __init__(self):
        super().__init__()
        self.vector_db = vector_db
        logger.info("[COACH] Initialized with vector search enhancement")

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

            # Perform hybrid semantic search
            logger.info(f"[COACH] Semantic search for user {user_id}: '{query[:50]}...'")
            logger.debug(f"[COACH] Filters: {filters}")

            matches = await search_user_context(
                query=query,
                user_id=user_id,
                filters=filters if filters else None
            )

            if not matches:
                logger.warning(f"[COACH] No semantic matches found for query")
                return {"matches": [], "total": 0}

            # Format results for LLM consumption
            semantic_context = {
                "matches": matches,
                "total": len(matches),
                "top_match_score": matches[0]["score"] if matches else 0,
                "content_summary": self._summarize_matches(matches)
            }

            logger.info(f"[COACH] Found {len(matches)} semantic matches (top score: {matches[0]['score']:.3f})")

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
        summary += f"\nTop match ({top['score']:.2f} similarity): {top['text'][:200]}..."

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
            intent = await self._detect_intent_ai(user_message, language, target_language)
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

            # Step 4: Build enhanced prompt with BOTH contexts
            enhanced_prompt = self._build_enhanced_prompt(
                intent=intent,
                query=user_message,
                cached_context=cached_context,
                semantic_context=semantic_context,
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
                max_tokens=300
            )

            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            raw_response = response.choices[0].message.content

            logger.info(f"[COACH] Response generated in {response_time_ms}ms ({len(raw_response)} chars)")

            # Parse response (expects JSON)
            try:
                parsed = json.loads(raw_response)
                message = parsed.get("message", raw_response)
                show_card = parsed.get("show_card")
            except json.JSONDecodeError:
                logger.warning(f"[COACH] Response not valid JSON, using as plain text")
                message = raw_response
                show_card = None

            # Build result
            result = {
                "message": message,
                "show_card": show_card,
                "intent": intent,
                "response_time_ms": response_time_ms,
                "raw_response": raw_response,
                "messages": messages,
                "semantic_matches": len(semantic_context.get("matches", [])),
                "semantic_top_score": semantic_context.get("top_match_score", 0),
                "model": self.model
            }

            return result

        except Exception as e:
            logger.error(f"[COACH] Vector-enhanced chat failed: {str(e)}")
            # Fallback to base implementation
            logger.info(f"[COACH] Falling back to base chat implementation")
            return await self.chat(
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
        prompt = f"""You are TaalCoach, an AI language learning assistant for the MyTacoAI app.

RESPONSE RULES:
- Maximum 2 SHORT sentences (25 words total)
- Be specific, use user's REAL data from context below
- When suggesting features, recommend SPECIFIC actions
- Output JSON: {{"message": "text", "show_card": "..."}}

⚠️ CRITICAL: NEVER MAKE UP NUMBERS OR DATA
- ONLY use numbers that appear EXACTLY in the context data below
- If data is missing or zero, say so honestly: "You haven't done any X yet"
- DO NOT estimate, guess, or invent session counts, minutes, scores, or any metrics
- If unsure about a number, DO NOT mention it

⚠️ IMPORTANT: Distinguish between concepts:
- "Learning Plan Goal/Objective" = The goal OF the learning plan itself (e.g., "Master Dutch A1")
- "Personal Goals" = User's personal learning goals set separately (e.g., "Have a 10-minute conversation")
- When user asks about "learning plan goal", respond about the PLAN's objective, NOT personal goals

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

        prompt += f"\n\nNow answer the user's question: \"{query}\""

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
