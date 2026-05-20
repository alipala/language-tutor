import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from openai_client import get_async_openai
from bson import ObjectId
import statistics
from collections import defaultdict, Counter

from database import (
    users_collection, 
    conversation_sessions_collection, 
    learning_plans_collection
)

class AIReportGenerator:
    """Advanced AI-powered report generation service"""
    
    @staticmethod
    async def generate_comprehensive_user_data(user_id: str) -> Dict[str, Any]:
        """Collect and analyze comprehensive user data for report generation"""
        
        print(f"[AI_REPORT] 🔍 Collecting comprehensive data for user {user_id}")
        
        # Convert user_id to ObjectId for MongoDB queries
        try:
            if ObjectId.is_valid(user_id):
                user_object_id = ObjectId(user_id)
                user = await users_collection.find_one({"_id": user_object_id})
            else:
                # Try as string first, then as ObjectId
                user = await users_collection.find_one({"_id": user_id})
                if not user:
                    user_object_id = ObjectId(user_id)
                    user = await users_collection.find_one({"_id": user_object_id})
        except Exception as e:
            print(f"[AI_REPORT] ❌ Error finding user: {str(e)}")
            raise ValueError(f"User {user_id} not found")
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        print(f"[AI_REPORT] ✅ Found user: {user.get('name', 'Unknown')}")
        
        # Get learning plans with detailed analysis (user_id is stored as string in learning_plans)
        learning_plans = await learning_plans_collection.find(
            {"user_id": user_id}
        ).to_list(length=None)
        
        print(f"[AI_REPORT] ✅ Found {len(learning_plans)} learning plans")
        
        # Get conversation sessions with enhanced analysis (user_id is stored as string in conversations)
        conversations = await conversation_sessions_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).to_list(length=None)
        
        print(f"[AI_REPORT] ✅ Found {len(conversations)} conversations")
        
        # Perform advanced analytics
        try:
            print(f"[AI_REPORT] 🔄 Starting analytics generation...")
            analytics = await AIReportGenerator._perform_advanced_analytics(
                user, learning_plans, conversations
            )
            print(f"[AI_REPORT] ✅ Analytics completed successfully")
        except Exception as e:
            print(f"[AI_REPORT] ❌ Analytics error: {str(e)}")
            print(f"[AI_REPORT] ❌ Error type: {type(e)}")
            import traceback
            print(f"[AI_REPORT] ❌ Traceback: {traceback.format_exc()}")
            raise
        
        # Generate AI insights
        try:
            print(f"[AI_REPORT] 🔄 Starting AI insights generation...")
            ai_insights = await AIReportGenerator._generate_ai_insights(
                user, learning_plans, conversations, analytics
            )
            print(f"[AI_REPORT] ✅ AI insights completed successfully")
        except Exception as e:
            print(f"[AI_REPORT] ❌ AI insights error: {str(e)}")
            print(f"[AI_REPORT] ❌ Error type: {type(e)}")
            import traceback
            print(f"[AI_REPORT] ❌ Traceback: {traceback.format_exc()}")
            raise
        
        return {
            'user_profile': user,
            'learning_plans': learning_plans,
            'conversations': conversations,
            'analytics': analytics,
            'ai_insights': ai_insights,
            'export_date': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def _perform_advanced_analytics(
        user: Dict[str, Any], 
        learning_plans: List[Dict[str, Any]], 
        conversations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform comprehensive analytics on user data"""
        
        print(f"[AI_REPORT] 📊 Performing advanced analytics")
        
        # Time-based analytics
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        
        # Conversation analytics
        total_conversations = len(conversations)
        recent_conversations = []
        
        for c in conversations:
            if c.get('created_at'):
                try:
                    # Handle different date formats
                    created_at = c['created_at']
                    if isinstance(created_at, str):
                        # String format - parse as ISO format
                        date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    elif isinstance(created_at, (int, float)):
                        # Timestamp format - convert from timestamp
                        date = datetime.fromtimestamp(created_at)
                    else:
                        # Assume it's already a datetime object
                        date = created_at
                    
                    if date >= thirty_days_ago:
                        recent_conversations.append(c)
                except Exception as e:
                    print(f"[AI_REPORT] ⚠️ Error parsing date for conversation: {str(e)}")
                    continue
        
        # Learning progress analytics
        try:
            print(f"[AI_REPORT] 🔄 Analyzing learning progress...")
            progress_analytics = AIReportGenerator._analyze_learning_progress(
                learning_plans, conversations
            )
            print(f"[AI_REPORT] ✅ Learning progress analysis completed")
        except Exception as e:
            print(f"[AI_REPORT] ❌ Learning progress error: {str(e)}")
            raise
        
        # Skill development analytics
        try:
            print(f"[AI_REPORT] 🔄 Analyzing skill development...")
            skill_analytics = AIReportGenerator._analyze_skill_development(conversations)
            print(f"[AI_REPORT] ✅ Skill development analysis completed")
        except Exception as e:
            print(f"[AI_REPORT] ❌ Skill development error: {str(e)}")
            raise
        
        # Engagement analytics
        try:
            print(f"[AI_REPORT] 🔄 Analyzing engagement patterns...")
            engagement_analytics = AIReportGenerator._analyze_engagement_patterns(
                conversations
            )
            print(f"[AI_REPORT] ✅ Engagement analysis completed")
        except Exception as e:
            print(f"[AI_REPORT] ❌ Engagement analysis error: {str(e)}")
            raise
        
        # Language proficiency analytics
        try:
            print(f"[AI_REPORT] 🔄 Analyzing proficiency trends...")
            proficiency_analytics = AIReportGenerator._analyze_proficiency_trends(
                learning_plans, conversations
            )
            print(f"[AI_REPORT] ✅ Proficiency analysis completed")
        except Exception as e:
            print(f"[AI_REPORT] ❌ Proficiency analysis error: {str(e)}")
            raise
        
        # Goal achievement analytics
        try:
            print(f"[AI_REPORT] 🔄 Analyzing goal achievement...")
            goal_analytics = AIReportGenerator._analyze_goal_achievement(learning_plans)
            print(f"[AI_REPORT] ✅ Goal achievement analysis completed")
        except Exception as e:
            print(f"[AI_REPORT] ❌ Goal achievement error: {str(e)}")
            raise
        
        return {
            'overview': {
                'total_conversations': total_conversations,
                'recent_conversations_30d': len(recent_conversations),
                'total_learning_plans': len(learning_plans),
                'account_age_days': AIReportGenerator._calculate_account_age(user, now),
                'total_practice_minutes': sum(
                    c.get('duration_minutes', 0) for c in conversations
                ),
                'languages_studied': len(set(
                    lp.get('language', 'Unknown') for lp in learning_plans
                ))
            },
            'progress': progress_analytics,
            'skills': skill_analytics,
            'engagement': engagement_analytics,
            'proficiency': proficiency_analytics,
            'goals': goal_analytics
        }
    
    @staticmethod
    def _analyze_learning_progress(
        learning_plans: List[Dict[str, Any]], 
        conversations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze learning progress patterns"""
        
        if not learning_plans:
            return {'status': 'no_plans', 'message': 'No learning plans found'}
        
        # Calculate overall progress
        total_sessions_planned = sum(lp.get('total_sessions', 0) for lp in learning_plans)
        total_sessions_completed = sum(lp.get('completed_sessions', 0) for lp in learning_plans)
        
        overall_progress = (
            (total_sessions_completed / total_sessions_planned * 100) 
            if total_sessions_planned > 0 else 0
        )
        
        # Analyze progress by language
        progress_by_language = {}
        for plan in learning_plans:
            lang = plan.get('language', 'Unknown')
            if lang not in progress_by_language:
                progress_by_language[lang] = {
                    'total_sessions': 0,
                    'completed_sessions': 0,
                    'plans_count': 0
                }
            
            progress_by_language[lang]['total_sessions'] += plan.get('total_sessions', 0)
            progress_by_language[lang]['completed_sessions'] += plan.get('completed_sessions', 0)
            progress_by_language[lang]['plans_count'] += 1
        
        # Calculate progress percentages
        for lang_data in progress_by_language.values():
            lang_data['progress_percentage'] = (
                (lang_data['completed_sessions'] / lang_data['total_sessions'] * 100)
                if lang_data['total_sessions'] > 0 else 0
            )
        
        # Analyze weekly progress trends
        weekly_progress = AIReportGenerator._analyze_weekly_progress(conversations)
        
        return {
            'overall_progress_percentage': round(overall_progress, 1),
            'total_sessions_planned': total_sessions_planned,
            'total_sessions_completed': total_sessions_completed,
            'progress_by_language': progress_by_language,
            'weekly_trends': weekly_progress,
            'consistency_score': AIReportGenerator._calculate_consistency_score(conversations)
        }
    
    @staticmethod
    def _analyze_weekly_progress(conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze weekly progress patterns"""
        
        if not conversations:
            return {'weeks_analyzed': 0, 'trend': 'no_data'}
        
        # Group conversations by week
        weekly_data = defaultdict(lambda: {'sessions': 0, 'minutes': 0, 'messages': 0})
        
        for conv in conversations:
            if conv.get('created_at'):
                try:
                    # Handle different date formats
                    created_at = conv['created_at']
                    if isinstance(created_at, str):
                        date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    elif isinstance(created_at, (int, float)):
                        date = datetime.fromtimestamp(created_at)
                    else:
                        date = created_at
                    
                    week_key = date.strftime('%Y-W%U')  # Year-Week format
                    
                    weekly_data[week_key]['sessions'] += 1
                    weekly_data[week_key]['minutes'] += conv.get('duration_minutes', 0)
                    weekly_data[week_key]['messages'] += conv.get('message_count', 0)
                except Exception as e:
                    print(f"[AI_REPORT] ⚠️ Error parsing date in weekly progress: {str(e)}")
                    continue
        
        # Calculate trends
        weeks = sorted(weekly_data.keys())[-8:]  # Last 8 weeks
        if len(weeks) < 2:
            return {'weeks_analyzed': len(weeks), 'trend': 'insufficient_data'}
        
        # Calculate trend
        recent_avg = statistics.mean([
            weekly_data[week]['sessions'] for week in weeks[-4:]
        ]) if len(weeks) >= 4 else 0
        
        earlier_avg = statistics.mean([
            weekly_data[week]['sessions'] for week in weeks[:4]
        ]) if len(weeks) >= 4 else 0
        
        trend = 'improving' if recent_avg > earlier_avg else 'declining' if recent_avg < earlier_avg else 'stable'
        
        return {
            'weeks_analyzed': len(weeks),
            'trend': trend,
            'recent_weekly_average': round(recent_avg, 1),
            'weekly_data': dict(weekly_data)
        }
    
    @staticmethod
    def _calculate_consistency_score(conversations: List[Dict[str, Any]]) -> float:
        """Calculate learning consistency score (0-100)"""
        
        if not conversations:
            return 0
        
        # Get last 30 days of conversations
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        recent_conversations = []
        for conv in conversations:
            if conv.get('created_at'):
                try:
                    # Handle different date formats
                    created_at = conv['created_at']
                    if isinstance(created_at, str):
                        date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    elif isinstance(created_at, (int, float)):
                        date = datetime.fromtimestamp(created_at)
                    else:
                        date = created_at
                    
                    if date >= thirty_days_ago:
                        recent_conversations.append(date)
                except Exception as e:
                    print(f"[AI_REPORT] ⚠️ Error parsing date in consistency score: {str(e)}")
                    continue
        
        if not recent_conversations:
            return 0
        
        # Calculate days with practice
        practice_days = set(date.date() for date in recent_conversations)
        consistency_score = (len(practice_days) / 30) * 100
        
        return round(consistency_score, 1)
    
    @staticmethod
    def _analyze_skill_development(conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze skill development patterns"""
        
        enhanced_sessions = [
            c for c in conversations 
            if c.get('enhanced_analysis')
        ]
        
        if not enhanced_sessions:
            return {'status': 'no_enhanced_data', 'message': 'No enhanced analysis data available'}
        
        # Analyze skill trends over time
        skill_trends = {
            'engagement': [],
            'topic_depth': [],
            'complexity': [],
            'confidence': []
        }
        
        for session in enhanced_sessions:
            analysis = session.get('enhanced_analysis', {})
            
            # Extract skill metrics
            conv_quality = analysis.get('conversation_quality', {})
            if conv_quality.get('engagement', {}).get('score'):
                skill_trends['engagement'].append(conv_quality['engagement']['score'])
            
            if conv_quality.get('topic_depth', {}).get('score'):
                skill_trends['topic_depth'].append(conv_quality['topic_depth']['score'])
            
            # Extract AI insights
            ai_insights = analysis.get('ai_insights', {})
            if ai_insights.get('confidence_level'):
                skill_trends['confidence'].append(ai_insights['confidence_level'])
        
        # Calculate skill averages and trends
        skill_analysis = {}
        for skill, scores in skill_trends.items():
            if scores:
                skill_analysis[skill] = {
                    'average_score': round(statistics.mean(scores), 1),
                    'latest_score': scores[-1] if scores else 0,
                    'trend': AIReportGenerator._calculate_trend(scores),
                    'improvement': round(scores[-1] - scores[0], 1) if len(scores) > 1 else 0
                }
        
        return {
            'skills_analyzed': len(skill_analysis),
            'skill_breakdown': skill_analysis,
            'overall_skill_trend': AIReportGenerator._calculate_overall_trend(skill_analysis)
        }
    
    @staticmethod
    def _calculate_trend(scores: List[float]) -> str:
        """Calculate trend from a list of scores"""
        if len(scores) < 2:
            return 'insufficient_data'
        
        # Simple linear trend calculation
        recent_half = scores[len(scores)//2:]
        earlier_half = scores[:len(scores)//2]
        
        recent_avg = statistics.mean(recent_half)
        earlier_avg = statistics.mean(earlier_half)
        
        if recent_avg > earlier_avg + 2:
            return 'improving'
        elif recent_avg < earlier_avg - 2:
            return 'declining'
        else:
            return 'stable'
    
    @staticmethod
    def _calculate_overall_trend(skill_analysis: Dict[str, Any]) -> str:
        """Calculate overall skill development trend"""
        trends = [data.get('trend', 'stable') for data in skill_analysis.values()]
        
        improving_count = trends.count('improving')
        declining_count = trends.count('declining')
        
        if improving_count > declining_count:
            return 'improving'
        elif declining_count > improving_count:
            return 'declining'
        else:
            return 'stable'
    
    @staticmethod
    def _analyze_engagement_patterns(conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user engagement patterns"""
        
        if not conversations:
            return {'status': 'no_data'}
        
        # Analyze session duration patterns
        durations = [c.get('duration_minutes', 0) for c in conversations if c.get('duration_minutes', 0) > 0]
        
        # Analyze message count patterns
        message_counts = [c.get('message_count', 0) for c in conversations if c.get('message_count', 0) > 0]
        
        # Analyze topic preferences
        topics = [c.get('topic', 'general') for c in conversations if c.get('topic')]
        topic_preferences = Counter(topics)
        
        # Calculate engagement metrics
        engagement_metrics = {
            'average_session_duration': round(statistics.mean(durations), 1) if durations else 0,
            'average_messages_per_session': round(statistics.mean(message_counts), 1) if message_counts else 0,
            'preferred_topics': dict(topic_preferences.most_common(5)),
            'session_completion_rate': AIReportGenerator._calculate_completion_rate(conversations),
            'peak_engagement_periods': AIReportGenerator._analyze_peak_periods(conversations)
        }
        
        return engagement_metrics
    
    @staticmethod
    def _calculate_completion_rate(conversations: List[Dict[str, Any]]) -> float:
        """Calculate session completion rate based on duration"""
        if not conversations:
            return 0
        
        # Consider sessions > 3 minutes as "completed"
        completed_sessions = sum(1 for c in conversations if c.get('duration_minutes', 0) >= 3)
        completion_rate = (completed_sessions / len(conversations)) * 100
        
        return round(completion_rate, 1)
    
    @staticmethod
    def _analyze_peak_periods(conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze when user is most active"""
        
        if not conversations:
            return {'status': 'no_data'}
        
        hour_counts = defaultdict(int)
        day_counts = defaultdict(int)
        
        for conv in conversations:
            if conv.get('created_at'):
                try:
                    date = datetime.fromisoformat(conv['created_at'].replace('Z', '+00:00'))
                    hour_counts[date.hour] += 1
                    day_counts[date.strftime('%A')] += 1
                except:
                    continue
        
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else 12
        peak_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else 'Monday'
        
        return {
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'hourly_distribution': dict(hour_counts),
            'daily_distribution': dict(day_counts)
        }
    
    @staticmethod
    def _analyze_proficiency_trends(
        learning_plans: List[Dict[str, Any]], 
        conversations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze language proficiency development trends"""
        
        # Analyze proficiency levels from learning plans
        proficiency_progression = {}
        
        for plan in learning_plans:
            lang = plan.get('language', 'Unknown')
            level = plan.get('proficiency_level', 'Unknown')
            created_at = plan.get('created_at')
            
            if lang not in proficiency_progression:
                proficiency_progression[lang] = []
            
            proficiency_progression[lang].append({
                'level': level,
                'date': created_at,
                'assessment_score': plan.get('assessment_data', {}).get('overall_score', 0)
            })
        
        # Sort by date for each language
        for lang in proficiency_progression:
            proficiency_progression[lang].sort(
                key=lambda x: x['date'] if x['date'] else '1970-01-01'
            )
        
        # Analyze assessment score trends
        assessment_trends = AIReportGenerator._analyze_assessment_trends(learning_plans)
        
        return {
            'proficiency_progression': proficiency_progression,
            'assessment_trends': assessment_trends,
            'current_levels': {
                lang: progression[-1]['level'] if progression else 'Unknown'
                for lang, progression in proficiency_progression.items()
            }
        }
    
    @staticmethod
    def _analyze_assessment_trends(learning_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze assessment score trends"""
        
        assessments_with_scores = [
            plan for plan in learning_plans 
            if plan.get('assessment_data', {}).get('overall_score')
        ]
        
        if not assessments_with_scores:
            return {'status': 'no_assessment_data'}
        
        # Sort by creation date
        assessments_with_scores.sort(
            key=lambda x: x.get('created_at', '1970-01-01')
        )
        
        scores = [
            plan['assessment_data']['overall_score'] 
            for plan in assessments_with_scores
        ]
        
        # Calculate skill-specific trends
        skill_trends = {}
        skills = ['pronunciation', 'grammar', 'vocabulary', 'fluency', 'coherence']
        
        for skill in skills:
            skill_scores = [
                plan['assessment_data'].get(skill, {}).get('score', 0)
                for plan in assessments_with_scores
                if plan['assessment_data'].get(skill, {}).get('score')
            ]
            
            if skill_scores:
                skill_trends[skill] = {
                    'average': round(statistics.mean(skill_scores), 1),
                    'latest': skill_scores[-1],
                    'improvement': round(skill_scores[-1] - skill_scores[0], 1) if len(skill_scores) > 1 else 0,
                    'trend': AIReportGenerator._calculate_trend(skill_scores)
                }
        
        return {
            'overall_score_trend': AIReportGenerator._calculate_trend(scores),
            'average_score': round(statistics.mean(scores), 1),
            'latest_score': scores[-1],
            'score_improvement': round(scores[-1] - scores[0], 1) if len(scores) > 1 else 0,
            'skill_trends': skill_trends,
            'assessments_count': len(assessments_with_scores)
        }
    
    @staticmethod
    def _analyze_goal_achievement(learning_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze learning goal achievement patterns"""
        
        if not learning_plans:
            return {'status': 'no_plans'}
        
        # Analyze goal frequency
        all_goals = []
        for plan in learning_plans:
            all_goals.extend(plan.get('goals', []))
        
        goal_frequency = Counter(all_goals)
        
        # Analyze goal completion rates
        goal_completion = {}
        for plan in learning_plans:
            progress = plan.get('progress_percentage', 0)
            for goal in plan.get('goals', []):
                if goal not in goal_completion:
                    goal_completion[goal] = {'total_progress': 0, 'plan_count': 0}
                
                goal_completion[goal]['total_progress'] += progress
                goal_completion[goal]['plan_count'] += 1
        
        # Calculate average completion for each goal
        for goal, data in goal_completion.items():
            data['average_completion'] = round(
                data['total_progress'] / data['plan_count'], 1
            )
        
        return {
            'most_common_goals': dict(goal_frequency.most_common(5)),
            'goal_completion_rates': goal_completion,
            'total_unique_goals': len(goal_frequency),
            'goal_achievement_summary': AIReportGenerator._summarize_goal_achievement(goal_completion)
        }
    
    @staticmethod
    def _summarize_goal_achievement(goal_completion: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize overall goal achievement"""
        
        if not goal_completion:
            return {'status': 'no_goals'}
        
        completion_rates = [
            data['average_completion'] 
            for data in goal_completion.values()
        ]
        
        overall_completion = statistics.mean(completion_rates)
        
        # Categorize goals by completion rate
        high_achievement = [
            goal for goal, data in goal_completion.items()
            if data['average_completion'] >= 75
        ]
        
        moderate_achievement = [
            goal for goal, data in goal_completion.items()
            if 25 <= data['average_completion'] < 75
        ]
        
        low_achievement = [
            goal for goal, data in goal_completion.items()
            if data['average_completion'] < 25
        ]
        
        return {
            'overall_completion_rate': round(overall_completion, 1),
            'high_achievement_goals': high_achievement,
            'moderate_achievement_goals': moderate_achievement,
            'low_achievement_goals': low_achievement,
            'achievement_distribution': {
                'high': len(high_achievement),
                'moderate': len(moderate_achievement),
                'low': len(low_achievement)
            }
        }
    
    @staticmethod
    def _calculate_account_age(user: Dict[str, Any], now: datetime) -> int:
        """Calculate account age in days, handling different date formats"""
        try:
            created_at = user.get('created_at')
            if not created_at:
                return 0
            
            if isinstance(created_at, str):
                # String format - parse as ISO format
                user_created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            elif isinstance(created_at, (int, float)):
                # Timestamp format - convert from timestamp
                user_created = datetime.fromtimestamp(created_at)
            else:
                # Assume it's already a datetime object
                user_created = created_at
            
            return (now - user_created).days
        except Exception as e:
            print(f"[AI_REPORT] ⚠️ Error calculating account age: {str(e)}")
            return 0
    
    @staticmethod
    async def _generate_ai_insights(
        user: Dict[str, Any],
        learning_plans: List[Dict[str, Any]],
        conversations: List[Dict[str, Any]],
        analytics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive AI insights for the report"""
        
        print(f"[AI_REPORT] 🤖 Generating AI insights")
        
        try:
            # Prepare data summary for AI analysis
            data_summary = {
                'user_profile': {
                    'account_age_days': analytics['overview']['account_age_days'],
                    'languages_studied': analytics['overview']['languages_studied'],
                    'total_conversations': analytics['overview']['total_conversations'],
                    'total_practice_minutes': analytics['overview']['total_practice_minutes']
                },
                'learning_progress': analytics['progress'],
                'skill_development': analytics['skills'],
                'engagement_patterns': analytics['engagement'],
                'goal_achievement': analytics['goals']
            }
            
            # Create comprehensive analysis prompt
            prompt = f"""
            As an expert language learning analyst, analyze this comprehensive student data and provide professional insights for a detailed learning report.
            
            Student Data Summary:
            {json.dumps(data_summary, indent=2)}
            
            Provide a comprehensive analysis in JSON format with these sections:
            
            1. executive_summary: A professional 2-3 sentence overview of the student's learning journey and current status
            
            2. key_achievements: Array of 3-5 specific achievements and milestones reached
            
            3. learning_strengths: Array of 3-4 identified strengths in the student's learning approach
            
            4. improvement_opportunities: Array of 3-4 specific areas for improvement with actionable suggestions
            
            5. personalized_recommendations: Object with:
               - immediate_actions: Array of 2-3 actions to take in the next week
               - monthly_focus: Array of 2-3 areas to focus on this month
               - long_term_strategy: Array of 2-3 strategic recommendations for continued growth
            
            6. learning_insights: Object with:
               - learning_style_assessment: Analysis of the student's preferred learning patterns
               - motivation_indicators: Assessment of engagement and motivation levels
               - progress_trajectory: Prediction of future progress based on current patterns
            
            7. professional_assessment: A formal assessment paragraph suitable for academic or professional contexts
            
            Make the analysis professional, specific, and actionable. Focus on data-driven insights and concrete recommendations.
            """
            
            response = await get_async_openai().chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional language learning analyst creating comprehensive reports for educational institutions and language learning platforms. Provide detailed, actionable insights based on learning data."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            ai_insights = json.loads(response.choices[0].message.content)
            print(f"[AI_REPORT] ✅ AI insights generated successfully")
            
            return ai_insights
            
        except Exception as e:
            print(f"[AI_REPORT] ❌ Error generating AI insights: {str(e)}")
            
            # Return fallback insights
            return {
                "executive_summary": "Comprehensive learning analysis completed based on available data.",
                "key_achievements": [
                    f"Completed {analytics['overview']['total_conversations']} practice sessions",
                    f"Accumulated {analytics['overview']['total_practice_minutes']:.1f} minutes of practice time",
                    f"Studied {analytics['overview']['languages_studied']} language(s)"
                ],
                "learning_strengths": [
                    "Consistent practice engagement",
                    "Active participation in conversations",
                    "Goal-oriented learning approach"
                ],
                "improvement_opportunities": [
                    "Increase session frequency for better retention",
                    "Explore diverse conversation topics",
                    "Focus on identified weak skill areas"
                ],
                "personalized_recommendations": {
                    "immediate_actions": [
                        "Schedule regular practice sessions",
                        "Review previous session feedback"
                    ],
                    "monthly_focus": [
                        "Expand vocabulary in target areas",
                        "Practice complex sentence structures"
                    ],
                    "long_term_strategy": [
                        "Set progressive proficiency goals",
                        "Integrate real-world language use"
                    ]
                },
                "learning_insights": {
                    "learning_style_assessment": "Data-driven learning approach with consistent engagement patterns",
                    "motivation_indicators": "Positive engagement with structured learning activities",
                    "progress_trajectory": "Steady improvement expected with continued practice"
                },
                "professional_assessment": "The student demonstrates commitment to language learning through consistent practice and engagement with structured learning activities. Continued focus on identified improvement areas will support ongoing proficiency development."
            }

# Export the main function for use in enhanced_export_routes
async def generate_ai_insights(user_data: Dict[str, Any], report_type: str = "comprehensive") -> Dict[str, Any]:
    """
    Main function to generate AI insights for enhanced reports
    This is the function called by enhanced_export_routes.py
    """
    try:
        print(f"[AI_REPORT] 🚀 Starting AI insights generation for report type: {report_type}")
        
        # Extract user ID from user_data
        user_id = None
        if 'user_profile' in user_data and '_id' in user_data['user_profile']:
            user_id = str(user_data['user_profile']['_id'])
        elif 'id' in user_data:
            user_id = str(user_data['id'])
        else:
            raise ValueError("User ID not found in user_data")
        
        print(f"[AI_REPORT] 📊 Generating comprehensive data for user: {user_id}")
        
        # Use the existing comprehensive data generation
        comprehensive_data = await AIReportGenerator.generate_comprehensive_user_data(user_id)
        
        print(f"[AI_REPORT] ✅ AI insights generation completed successfully")
        
        return comprehensive_data['ai_insights']
        
    except Exception as e:
        print(f"[AI_REPORT] ❌ Error in generate_ai_insights: {str(e)}")
        import traceback
        print(f"[AI_REPORT] ❌ Traceback: {traceback.format_exc()}")
        
        # Return fallback insights
        return {
            "executive_summary": "AI-powered analysis completed based on available learning data.",
            "key_achievements": [
                "Active engagement with language learning platform",
                "Consistent practice sessions completed",
                "Progress tracking and goal setting"
            ],
            "learning_strengths": [
                "Commitment to structured learning",
                "Regular practice engagement",
                "Goal-oriented approach"
            ],
            "improvement_opportunities": [
                "Increase practice frequency",
                "Explore diverse learning activities",
                "Focus on skill development areas"
            ],
            "personalized_recommendations": {
                "immediate_actions": [
                    "Schedule regular practice sessions",
                    "Review learning objectives"
                ],
                "monthly_focus": [
                    "Expand vocabulary knowledge",
                    "Practice conversation skills"
                ],
                "long_term_strategy": [
                    "Set progressive learning goals",
                    "Integrate real-world practice"
                ]
            },
            "learning_insights": {
                "learning_style_assessment": "Structured learning approach with consistent engagement",
                "motivation_indicators": "Positive engagement with learning activities",
                "progress_trajectory": "Steady improvement expected with continued practice"
            },
            "professional_assessment": "The learner demonstrates commitment to language acquisition through consistent engagement with structured learning activities and goal-oriented practice sessions."
        }
