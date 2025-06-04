import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
import httpx
from collections import Counter
import re
import statistics

from models import ConversationMessage
from database import conversation_sessions_collection

# Initialize OpenAI client with error handling
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables")

try:
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized successfully in enhanced_analysis")
except TypeError as e:
    if "proxies" in str(e):
        print("Detected 'proxies' error in OpenAI initialization. Using alternative initialization...")
        client = OpenAI(api_key=api_key, http_client=httpx.Client())
        print("OpenAI client initialized with alternative method in enhanced_analysis")
    else:
        print(f"Error initializing OpenAI client in enhanced_analysis: {str(e)}")
        raise

class ConversationQualityMetrics:
    """Analyze conversation quality and engagement"""
    
    @staticmethod
    def calculate_engagement_score(messages: List[ConversationMessage]) -> Dict[str, Any]:
        """Calculate how engaged the user was in the conversation"""
        user_messages = [msg for msg in messages if msg.role == "user"]
        
        if not user_messages:
            return {"score": 0, "feedback": "No user messages found", "details": {}}
        
        # Calculate metrics
        total_words = sum(len(msg.content.split()) for msg in user_messages)
        avg_words_per_message = total_words / len(user_messages)
        
        # Count questions asked by user
        questions_asked = sum(1 for msg in user_messages if '?' in msg.content)
        
        # Count elaborative responses (more than 5 words)
        elaborative_responses = sum(1 for msg in user_messages if len(msg.content.split()) > 5)
        elaboration_rate = elaborative_responses / len(user_messages)
        
        # Calculate engagement score (0-100)
        word_score = min(avg_words_per_message * 5, 40)  # Max 40 points for word count
        question_score = min(questions_asked * 10, 30)   # Max 30 points for questions
        elaboration_score = elaboration_rate * 30        # Max 30 points for elaboration
        
        engagement_score = word_score + question_score + elaboration_score
        
        return {
            "score": round(engagement_score, 1),
            "feedback": ConversationQualityMetrics._get_engagement_feedback(engagement_score),
            "details": {
                "avg_words_per_message": round(avg_words_per_message, 1),
                "questions_asked": questions_asked,
                "elaboration_rate": round(elaboration_rate * 100, 1),
                "total_user_messages": len(user_messages)
            }
        }
    
    @staticmethod
    def _get_engagement_feedback(score: float) -> str:
        """Get feedback based on engagement score"""
        if score >= 80:
            return "Excellent engagement! You actively participated with detailed responses and questions."
        elif score >= 60:
            return "Good engagement! Try asking more questions to deepen the conversation."
        elif score >= 40:
            return "Moderate engagement. Consider giving more detailed responses."
        else:
            return "Low engagement. Try to elaborate more on your answers and ask follow-up questions."
    
    @staticmethod
    def analyze_topic_depth(messages: List[ConversationMessage], topic: str) -> Dict[str, Any]:
        """Analyze how deeply the conversation explored the topic"""
        user_messages = [msg for msg in messages if msg.role == "user"]
        conversation_text = " ".join([msg.content for msg in user_messages])
        
        # Count topic-related keywords (this would be enhanced with NLP)
        topic_keywords = {
            "travel": ["trip", "journey", "vacation", "country", "city", "culture", "experience", "visit"],
            "food": ["eat", "taste", "cook", "recipe", "restaurant", "meal", "flavor", "dish"],
            "work": ["job", "career", "office", "colleague", "project", "meeting", "business"],
            "hobbies": ["enjoy", "fun", "interest", "passion", "activity", "leisure", "free time"],
            "family": ["parent", "sibling", "relative", "child", "mother", "father", "family"],
            "education": ["school", "study", "learn", "teacher", "student", "university", "course"]
        }
        
        keywords = topic_keywords.get(topic.lower(), [])
        keyword_count = sum(1 for word in conversation_text.lower().split() if word in keywords)
        
        # Calculate depth score
        depth_score = min(keyword_count * 10, 100)
        
        return {
            "score": depth_score,
            "feedback": ConversationQualityMetrics._get_depth_feedback(depth_score, topic),
            "details": {
                "topic_keywords_used": keyword_count,
                "keywords_found": [word for word in conversation_text.lower().split() if word in keywords]
            }
        }
    
    @staticmethod
    def _get_depth_feedback(score: float, topic: str) -> str:
        """Get feedback based on topic depth score"""
        if score >= 70:
            return f"Great topic exploration! You discussed {topic} in detail with relevant vocabulary."
        elif score >= 40:
            return f"Good coverage of {topic}. Try to use more specific vocabulary related to this topic."
        else:
            return f"Limited exploration of {topic}. Consider sharing more specific details and experiences."

class LearningProgressIndicators:
    """Analyze learning progress and improvement patterns"""
    
    @staticmethod
    async def analyze_complexity_growth(user_id: str, current_messages: List[ConversationMessage]) -> Dict[str, Any]:
        """Compare sentence complexity with previous sessions"""
        # Get previous sessions for comparison
        previous_sessions = await conversation_sessions_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(5).to_list(length=5)
        
        current_complexity = LearningProgressIndicators._calculate_complexity(current_messages)
        
        if len(previous_sessions) < 2:
            return {
                "score": current_complexity,
                "trend": "baseline",
                "feedback": "This is your baseline complexity score. Keep practicing to see improvement!",
                "details": {"current_complexity": current_complexity, "sessions_compared": 0}
            }
        
        # Calculate average complexity from previous sessions
        prev_complexities = []
        for session in previous_sessions[1:]:  # Skip current session
            session_messages = [ConversationMessage(**msg) for msg in session.get('messages', [])]
            prev_complexities.append(LearningProgressIndicators._calculate_complexity(session_messages))
        
        avg_prev_complexity = statistics.mean(prev_complexities) if prev_complexities else current_complexity
        improvement = current_complexity - avg_prev_complexity
        
        trend = "improving" if improvement > 2 else "stable" if improvement > -2 else "declining"
        
        return {
            "score": round(current_complexity, 1),
            "trend": trend,
            "improvement": round(improvement, 1),
            "feedback": LearningProgressIndicators._get_complexity_feedback(trend, improvement),
            "details": {
                "current_complexity": round(current_complexity, 1),
                "previous_average": round(avg_prev_complexity, 1),
                "sessions_compared": len(prev_complexities)
            }
        }
    
    @staticmethod
    def _calculate_complexity(messages: List[ConversationMessage]) -> float:
        """Calculate sentence complexity score"""
        user_messages = [msg for msg in messages if msg.role == "user"]
        
        if not user_messages:
            return 0
        
        total_score = 0
        total_sentences = 0
        
        for msg in user_messages:
            sentences = re.split(r'[.!?]+', msg.content)
            for sentence in sentences:
                if len(sentence.strip()) > 3:  # Ignore very short fragments
                    words = sentence.strip().split()
                    # Simple complexity: word count + subordinate clauses + complex structures
                    word_score = min(len(words) * 0.5, 10)  # Max 10 points for length
                    clause_score = sentence.count(',') * 2  # Commas indicate complexity
                    complex_score = sum(2 for word in ['because', 'although', 'however', 'therefore', 'while'] if word in sentence.lower())
                    
                    total_score += word_score + clause_score + complex_score
                    total_sentences += 1
        
        return total_score / total_sentences if total_sentences > 0 else 0
    
    @staticmethod
    def _get_complexity_feedback(trend: str, improvement: float) -> str:
        """Get feedback based on complexity trend"""
        if trend == "improving":
            return f"Excellent! Your sentence complexity has improved by {improvement:.1f} points. You're using more sophisticated language structures."
        elif trend == "stable":
            return "Your complexity level is consistent. Try incorporating more complex sentence structures and connecting words."
        else:
            return "Your sentences have become simpler. Challenge yourself with more complex ideas and longer explanations."

class PersonalizedInsights:
    """Generate personalized learning insights"""
    
    @staticmethod
    async def detect_learning_patterns(user_id: str, current_session: Dict[str, Any]) -> Dict[str, Any]:
        """Detect user's learning patterns and preferences"""
        # Get user's session history
        sessions = await conversation_sessions_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(10).to_list(length=10)
        
        if len(sessions) < 3:
            return {
                "patterns": "insufficient_data",
                "feedback": "Complete a few more sessions to unlock personalized insights!",
                "details": {"sessions_analyzed": len(sessions)}
            }
        
        # Analyze patterns
        patterns = {
            "preferred_topics": PersonalizedInsights._analyze_topic_preferences(sessions),
            "optimal_duration": PersonalizedInsights._analyze_duration_patterns(sessions),
            "engagement_patterns": PersonalizedInsights._analyze_engagement_patterns(sessions),
            "improvement_areas": PersonalizedInsights._identify_improvement_areas(sessions)
        }
        
        return {
            "patterns": patterns,
            "feedback": PersonalizedInsights._generate_pattern_feedback(patterns),
            "details": {"sessions_analyzed": len(sessions)}
        }
    
    @staticmethod
    def _analyze_topic_preferences(sessions: List[Dict]) -> Dict[str, Any]:
        """Analyze which topics the user engages with most"""
        topic_engagement = {}
        
        for session in sessions:
            topic = session.get('topic', 'general')
            duration = session.get('duration_minutes', 0)
            message_count = session.get('message_count', 0)
            
            if topic not in topic_engagement:
                topic_engagement[topic] = {"total_duration": 0, "total_messages": 0, "sessions": 0}
            
            topic_engagement[topic]["total_duration"] += duration
            topic_engagement[topic]["total_messages"] += message_count
            topic_engagement[topic]["sessions"] += 1
        
        # Calculate engagement scores
        for topic, data in topic_engagement.items():
            avg_duration = data["total_duration"] / data["sessions"]
            avg_messages = data["total_messages"] / data["sessions"]
            data["engagement_score"] = avg_duration * 0.6 + avg_messages * 0.4
        
        # Find most engaging topic
        best_topic = max(topic_engagement.items(), key=lambda x: x[1]["engagement_score"])
        
        return {
            "most_engaging": best_topic[0],
            "engagement_score": round(best_topic[1]["engagement_score"], 1),
            "all_topics": topic_engagement
        }
    
    @staticmethod
    def _analyze_duration_patterns(sessions: List[Dict]) -> Dict[str, Any]:
        """Analyze optimal session duration patterns"""
        durations = [session.get('duration_minutes', 0) for session in sessions]
        message_counts = [session.get('message_count', 0) for session in sessions]
        
        # Calculate efficiency (messages per minute)
        efficiencies = [msg/dur if dur > 0 else 0 for msg, dur in zip(message_counts, durations)]
        
        if efficiencies:
            avg_efficiency = statistics.mean(efficiencies)
            optimal_duration = statistics.mean(durations)
            
            return {
                "optimal_duration": round(optimal_duration, 1),
                "efficiency_score": round(avg_efficiency, 1),
                "recommendation": PersonalizedInsights._get_duration_recommendation(optimal_duration)
            }
        
        return {"optimal_duration": 5.0, "efficiency_score": 0, "recommendation": "Aim for 5-10 minute sessions"}
    
    @staticmethod
    def _get_duration_recommendation(duration: float) -> str:
        """Get duration recommendation based on patterns"""
        if duration < 3:
            return "Try extending your sessions to 5-7 minutes for better learning outcomes"
        elif duration > 10:
            return "Consider shorter, more focused sessions of 7-10 minutes"
        else:
            return f"Your {duration:.1f}-minute sessions are well-paced. Keep it up!"
    
    @staticmethod
    def _analyze_engagement_patterns(sessions: List[Dict]) -> Dict[str, Any]:
        """Analyze when user is most engaged"""
        # This is a simplified version - in reality, you'd analyze time of day, day of week, etc.
        recent_sessions = sessions[:5]
        engagement_scores = []
        
        for session in recent_sessions:
            messages = session.get('messages', [])
            user_messages = [msg for msg in messages if msg.get('role') == 'user']
            
            if user_messages:
                avg_length = statistics.mean([len(msg.get('content', '').split()) for msg in user_messages])
                engagement_scores.append(avg_length)
        
        if engagement_scores:
            trend = "increasing" if len(engagement_scores) > 1 and engagement_scores[0] > engagement_scores[-1] else "stable"
            avg_engagement = statistics.mean(engagement_scores)
            
            return {
                "trend": trend,
                "average_engagement": round(avg_engagement, 1),
                "recent_scores": [round(score, 1) for score in engagement_scores]
            }
        
        return {"trend": "unknown", "average_engagement": 0, "recent_scores": []}
    
    @staticmethod
    def _identify_improvement_areas(sessions: List[Dict]) -> List[str]:
        """Identify areas where user could improve"""
        areas = []
        
        # Analyze session lengths
        durations = [session.get('duration_minutes', 0) for session in sessions]
        avg_duration = statistics.mean(durations) if durations else 0
        
        if avg_duration < 3:
            areas.append("session_length")
        
        # Analyze message counts
        message_counts = [session.get('message_count', 0) for session in sessions]
        avg_messages = statistics.mean(message_counts) if message_counts else 0
        
        if avg_messages < 10:
            areas.append("conversation_participation")
        
        # Analyze topic variety
        topics = set(session.get('topic', 'general') for session in sessions)
        if len(topics) < 3:
            areas.append("topic_variety")
        
        return areas
    
    @staticmethod
    def _generate_pattern_feedback(patterns: Dict[str, Any]) -> str:
        """Generate feedback based on detected patterns"""
        feedback_parts = []
        
        # Topic preference feedback
        if "preferred_topics" in patterns:
            best_topic = patterns["preferred_topics"]["most_engaging"]
            feedback_parts.append(f"You're most engaged when discussing {best_topic}")
        
        # Duration feedback
        if "optimal_duration" in patterns:
            duration_rec = patterns["optimal_duration"]["recommendation"]
            feedback_parts.append(duration_rec)
        
        # Engagement feedback
        if "engagement_patterns" in patterns:
            trend = patterns["engagement_patterns"]["trend"]
            if trend == "increasing":
                feedback_parts.append("Your engagement is improving over time!")
        
        return ". ".join(feedback_parts) if feedback_parts else "Keep practicing to unlock more insights!"

async def generate_enhanced_analysis(
    messages: List[ConversationMessage],
    user_id: str,
    language: str,
    level: str,
    topic: str,
    duration_minutes: float
) -> Dict[str, Any]:
    """Generate comprehensive enhanced analysis for a conversation session"""
    
    try:
        print(f"[ENHANCED_ANALYSIS] Starting analysis for user {user_id}")
        
        # 1. Conversation Quality Metrics
        engagement = ConversationQualityMetrics.calculate_engagement_score(messages)
        topic_depth = ConversationQualityMetrics.analyze_topic_depth(messages, topic)
        
        # 2. Learning Progress Indicators
        complexity_analysis = await LearningProgressIndicators.analyze_complexity_growth(user_id, messages)
        
        # 3. Personalized Insights
        learning_patterns = await PersonalizedInsights.detect_learning_patterns(user_id, {
            "language": language,
            "level": level,
            "topic": topic,
            "duration_minutes": duration_minutes,
            "messages": [msg.dict() for msg in messages]
        })
        
        # 4. Generate AI-powered insights using OpenAI
        ai_insights = await _generate_ai_insights(messages, language, level, topic, duration_minutes)
        
        # 5. Compile comprehensive analysis
        enhanced_analysis = {
            "conversation_quality": {
                "engagement": engagement,
                "topic_depth": topic_depth,
                "overall_score": round((engagement["score"] + topic_depth["score"]) / 2, 1)
            },
            "learning_progress": {
                "complexity_growth": complexity_analysis,
                "improvement_indicators": _calculate_improvement_indicators(messages)
            },
            "personalized_insights": learning_patterns,
            "ai_insights": ai_insights,
            "recommendations": _generate_recommendations(engagement, topic_depth, complexity_analysis, learning_patterns),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        print(f"[ENHANCED_ANALYSIS] ✅ Analysis completed successfully")
        return enhanced_analysis
        
    except Exception as e:
        print(f"[ENHANCED_ANALYSIS] ❌ Error generating analysis: {str(e)}")
        return {
            "error": "Failed to generate enhanced analysis",
            "basic_metrics": {
                "message_count": len(messages),
                "duration_minutes": duration_minutes,
                "user_messages": len([msg for msg in messages if msg.role == "user"])
            },
            "generated_at": datetime.utcnow().isoformat()
        }

async def _generate_ai_insights(
    messages: List[ConversationMessage],
    language: str,
    level: str,
    topic: str,
    duration_minutes: float
) -> Dict[str, Any]:
    """Generate AI-powered insights about the conversation"""
    
    try:
        # Prepare conversation text
        conversation_text = ""
        for msg in messages:
            role = "Student" if msg.role == "user" else "Tutor"
            conversation_text += f"{role}: {msg.content}\n"
        
        # Create analysis prompt
        prompt = f"""
        Analyze this {language} language learning conversation at {level} level about {topic}.
        Duration: {duration_minutes} minutes.
        
        Provide insights in JSON format with these keys:
        - confidence_level: How confident the student seemed (0-100)
        - breakthrough_moments: Array of specific moments where student excelled
        - struggle_points: Array of specific areas where student struggled
        - vocabulary_highlights: New or advanced words the student used successfully
        - grammar_patterns: Grammar structures the student attempted (successful and unsuccessful)
        - cultural_awareness: Evidence of cultural understanding in responses
        - motivation_indicators: Signs of high or low motivation
        - next_session_focus: Specific recommendations for the next practice session
        
        Conversation:
        {conversation_text}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are an expert language learning analyst. Provide detailed, actionable insights about student performance."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        ai_insights = json.loads(response.choices[0].message.content)
        print(f"[ENHANCED_ANALYSIS] AI insights generated successfully")
        return ai_insights
        
    except Exception as e:
        print(f"[ENHANCED_ANALYSIS] ❌ Error generating AI insights: {str(e)}")
        return {
            "confidence_level": 50,
            "breakthrough_moments": ["Unable to analyze specific moments"],
            "struggle_points": ["Analysis unavailable"],
            "vocabulary_highlights": [],
            "grammar_patterns": [],
            "cultural_awareness": "Unable to assess",
            "motivation_indicators": "Analysis unavailable",
            "next_session_focus": ["Continue practicing conversation skills"]
        }

def _calculate_improvement_indicators(messages: List[ConversationMessage]) -> Dict[str, Any]:
    """Calculate various improvement indicators from the current session"""
    user_messages = [msg for msg in messages if msg.role == "user"]
    
    if not user_messages:
        return {"error": "No user messages to analyze"}
    
    # Calculate various metrics
    total_words = sum(len(msg.content.split()) for msg in user_messages)
    unique_words = len(set(word.lower() for msg in user_messages for word in msg.content.split()))
    
    # Vocabulary diversity
    vocabulary_diversity = unique_words / total_words if total_words > 0 else 0
    
    # Response length progression
    response_lengths = [len(msg.content.split()) for msg in user_messages]
    length_trend = "increasing" if len(response_lengths) > 1 and response_lengths[-1] > response_lengths[0] else "stable"
    
    # Question asking behavior
    questions_asked = sum(1 for msg in user_messages if '?' in msg.content)
    
    return {
        "vocabulary_diversity": round(vocabulary_diversity, 3),
        "total_unique_words": unique_words,
        "response_length_trend": length_trend,
        "questions_asked": questions_asked,
        "average_response_length": round(statistics.mean(response_lengths), 1) if response_lengths else 0
    }

def _generate_recommendations(
    engagement: Dict[str, Any],
    topic_depth: Dict[str, Any],
    complexity_analysis: Dict[str, Any],
    learning_patterns: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate actionable recommendations based on all analyses"""
    
    recommendations = {
        "immediate_actions": [],
        "weekly_focus": [],
        "long_term_goals": []
    }
    
    # Engagement-based recommendations
    if engagement["score"] < 60:
        recommendations["immediate_actions"].append("Try to give longer, more detailed responses in your next session")
        recommendations["immediate_actions"].append("Ask follow-up questions to keep the conversation flowing")
    
    # Topic depth recommendations
    if topic_depth["score"] < 50:
        recommendations["weekly_focus"].append(f"Study vocabulary related to {topic_depth.get('topic', 'your chosen topics')}")
        recommendations["weekly_focus"].append("Practice describing experiences in more detail")
    
    # Complexity recommendations
    if complexity_analysis.get("trend") == "declining":
        recommendations["immediate_actions"].append("Challenge yourself with more complex sentence structures")
        recommendations["weekly_focus"].append("Practice using connecting words like 'because', 'although', 'however'")
    
    # Pattern-based recommendations
    if learning_patterns.get("patterns") != "insufficient_data":
        patterns = learning_patterns.get("patterns", {})
        if "improvement_areas" in patterns:
            for area in patterns["improvement_areas"]:
                if area == "session_length":
                    recommendations["immediate_actions"].append("Try to extend your next session to 5-7 minutes")
                elif area == "topic_variety":
                    recommendations["weekly_focus"].append("Explore different conversation topics this week")
    
    # Default recommendations if none generated
    if not any(recommendations.values()):
        recommendations["immediate_actions"] = ["Keep practicing regularly to maintain your progress"]
        recommendations["weekly_focus"] = ["Focus on areas you find most challenging"]
        recommendations["long_term_goals"] = ["Set a goal to practice 3-4 times per week"]
    
    return recommendations
