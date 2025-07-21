import os
import io
import base64
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from io import BytesIO
import tempfile

# Chart generation libraries
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
from matplotlib.patches import Rectangle

# HTML/PDF generation
import weasyprint
from jinja2 import Environment, FileSystemLoader, select_autoescape
import logging

# Configure matplotlib for better rendering
plt.style.use('default')
sns.set_palette("husl")

class ModernPDFGenerator:
    """Modern PDF generator using WeasyPrint + HTML/CSS with beautiful charts"""
    
    # Color scheme matching the design
    COLORS = {
        'primary': '#4ECFBF',
        'secondary': '#FFD63A', 
        'accent': '#F75A5A',
        'dark': '#1F2937',
        'success': '#10B981',
        'warning': '#F59E0B',
        'purple': '#8B5CF6',
        'indigo': '#6366F1',
        'light_gray': '#F3F4F6',
        'medium_gray': '#6B7280'
    }
    
    def __init__(self):
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'pdf')
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Configure logging
        logging.getLogger('weasyprint').setLevel(logging.ERROR)
    
    @staticmethod
    def generate_comprehensive_report(user_data: Dict[str, Any], report_type: str = "comprehensive") -> BytesIO:
        """Generate a professional report based on type - maintains API compatibility"""
        
        generator = ModernPDFGenerator()
        
        if report_type == "learning_plans":
            return generator._generate_learning_plans_report(user_data)
        elif report_type == "conversations":
            return generator._generate_conversations_report(user_data)
        else:
            return generator._generate_comprehensive_report(user_data)
    
    def _generate_learning_plans_report(self, user_data: Dict[str, Any]) -> BytesIO:
        """Generate focused learning plans report"""
        
        try:
            print("[MODERN_PDF] 🎨 Generating learning plans report...")
            
            # Generate charts
            charts = self._generate_charts(user_data, report_type="learning_plans")
            
            # Prepare template data
            template_data = self._prepare_learning_plans_data(user_data, charts)
            
            # Render HTML template
            html_content = self._render_template('learning_plans_template.html', template_data)
            
            # Convert to PDF
            pdf_buffer = self._html_to_pdf(html_content)
            
            print("[MODERN_PDF] ✅ Learning plans report generated successfully")
            return pdf_buffer
            
        except Exception as e:
            print(f"[MODERN_PDF] ❌ Error generating learning plans report: {str(e)}")
            # Fallback to basic report
            return self._generate_fallback_report(user_data, "Learning Plans Report")
    
    def _generate_conversations_report(self, user_data: Dict[str, Any]) -> BytesIO:
        """Generate focused conversations report"""
        
        try:
            print("[MODERN_PDF] 🎨 Generating conversations report...")
            
            # Generate charts
            charts = self._generate_charts(user_data, report_type="conversations")
            
            # Prepare template data
            template_data = self._prepare_conversations_data(user_data, charts)
            
            # Render HTML template using conversation history template
            html_content = self._render_template('conversation_history_template.html', template_data)
            
            # Convert to PDF
            pdf_buffer = self._html_to_pdf(html_content)
            
            print("[MODERN_PDF] ✅ Conversations report generated successfully")
            return pdf_buffer
            
        except Exception as e:
            print(f"[MODERN_PDF] ❌ Error generating conversations report: {str(e)}")
            # Fallback to basic report
            return self._generate_fallback_report(user_data, "Conversation Analysis Report")
    
    def _generate_comprehensive_report(self, user_data: Dict[str, Any]) -> BytesIO:
        """Generate comprehensive report with all sections"""
        
        try:
            print("[MODERN_PDF] 🎨 Generating comprehensive report...")
            
            # Generate charts
            charts = self._generate_charts(user_data, report_type="comprehensive")
            
            # Prepare template data
            template_data = self._prepare_comprehensive_data(user_data, charts)
            
            # Render HTML template (using learning plans template for now)
            html_content = self._render_template('learning_plans_template.html', template_data)
            
            # Convert to PDF
            pdf_buffer = self._html_to_pdf(html_content)
            
            print("[MODERN_PDF] ✅ Comprehensive report generated successfully")
            return pdf_buffer
            
        except Exception as e:
            print(f"[MODERN_PDF] ❌ Error generating comprehensive report: {str(e)}")
            # Fallback to basic report
            return self._generate_fallback_report(user_data, "Comprehensive Learning Report")
    
    def _generate_charts(self, user_data: Dict[str, Any], report_type: str = "comprehensive") -> Dict[str, str]:
        """Generate all charts as base64 encoded images"""
        
        charts = {}
        
        try:
            # Progress Overview Chart (Plotly Bar Chart)
            charts['progress_overview'] = self._create_progress_overview_chart(user_data)
            
            # Skills Radar Chart (if skills data available)
            charts['skills_radar'] = self._create_skills_radar_chart(user_data)
            
            # Weekly Activity Chart (Matplotlib)
            charts['weekly_activity'] = self._create_weekly_activity_chart(user_data)
            
            print(f"[MODERN_PDF] 📊 Generated {len([c for c in charts.values() if c])} charts")
            
        except Exception as e:
            print(f"[MODERN_PDF] ⚠️ Error generating charts: {str(e)}")
        
        return charts
    
    def _create_progress_overview_chart(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create progress overview bar chart using Plotly"""
        
        try:
            analytics = user_data.get('analytics', {})
            overview = analytics.get('overview', {})
            
            # Prepare data
            metrics = ['Sessions', 'Practice Time', 'Languages', 'Plans']
            values = [
                overview.get('total_conversations', 0),
                overview.get('total_practice_minutes', 0),
                overview.get('languages_studied', 0),
                overview.get('total_learning_plans', 0)
            ]
            
            colors = [self.COLORS['primary'], self.COLORS['secondary'], self.COLORS['accent'], self.COLORS['purple']]
            
            # Create bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=metrics,
                    y=values,
                    marker_color=colors,
                    text=values,
                    textposition='auto',
                    textfont=dict(size=14, color='white', family='Inter')
                )
            ])
            
            fig.update_layout(
                title=dict(
                    text='Learning Progress Overview',
                    font=dict(size=20, family='Inter', color=self.COLORS['dark']),
                    x=0.5
                ),
                xaxis=dict(
                    title='Metrics',
                    titlefont=dict(size=14, family='Inter'),
                    tickfont=dict(size=12, family='Inter')
                ),
                yaxis=dict(
                    title='Values',
                    titlefont=dict(size=14, family='Inter'),
                    tickfont=dict(size=12, family='Inter')
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter'),
                margin=dict(l=50, r=50, t=80, b=50),
                height=400,
                width=800
            )
            
            # Convert to base64
            img_bytes = fig.to_image(format="png", engine="kaleido")
            return base64.b64encode(img_bytes).decode()
            
        except Exception as e:
            print(f"[MODERN_PDF] ⚠️ Error creating progress overview chart: {str(e)}")
            return None
    
    def _create_skills_radar_chart(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create skills radar chart using Plotly"""
        
        try:
            analytics = user_data.get('analytics', {})
            skills = analytics.get('skills', {})
            skill_breakdown = skills.get('skill_breakdown', {})
            
            if not skill_breakdown:
                return None
            
            # Prepare data
            skills_names = list(skill_breakdown.keys())
            skills_values = [skill_breakdown[skill].get('latest_score', 0) for skill in skills_names]
            
            # Create radar chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=skills_values,
                theta=[skill.replace('_', ' ').title() for skill in skills_names],
                fill='toself',
                fillcolor=f'rgba(78, 207, 191, 0.3)',
                line=dict(color=self.COLORS['primary'], width=3),
                marker=dict(color=self.COLORS['primary'], size=8),
                name='Current Skills'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        tickfont=dict(size=10, family='Inter'),
                        gridcolor='rgba(0,0,0,0.1)'
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=12, family='Inter', color=self.COLORS['dark'])
                    )
                ),
                title=dict(
                    text='Skills Analysis Radar',
                    font=dict(size=20, family='Inter', color=self.COLORS['dark']),
                    x=0.5
                ),
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter'),
                margin=dict(l=50, r=50, t=80, b=50),
                height=400,
                width=400
            )
            
            # Convert to base64
            img_bytes = fig.to_image(format="png", engine="kaleido")
            return base64.b64encode(img_bytes).decode()
            
        except Exception as e:
            print(f"[MODERN_PDF] ⚠️ Error creating skills radar chart: {str(e)}")
            return None
    
    def _create_weekly_activity_chart(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create weekly activity chart using Matplotlib"""
        
        try:
            # Create sample weekly data (in real implementation, extract from user_data)
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            activities = [3, 2, 4, 1, 5, 2, 3]  # Sample data
            
            # Create figure with modern styling
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create gradient bars
            bars = ax.bar(days, activities, color=self.COLORS['primary'], alpha=0.8, edgecolor='white', linewidth=2)
            
            # Add value labels on bars
            for bar, value in zip(bars, activities):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{value}', ha='center', va='bottom', fontsize=12, fontweight='bold')
            
            # Styling
            ax.set_title('Weekly Learning Activity', fontsize=18, fontweight='bold', color=self.COLORS['dark'], pad=20)
            ax.set_xlabel('Day of Week', fontsize=14, color=self.COLORS['dark'])
            ax.set_ylabel('Sessions', fontsize=14, color=self.COLORS['dark'])
            
            # Remove top and right spines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color(self.COLORS['medium_gray'])
            ax.spines['bottom'].set_color(self.COLORS['medium_gray'])
            
            # Grid styling
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_axisbelow(True)
            
            # Set background
            fig.patch.set_facecolor('white')
            ax.set_facecolor('white')
            
            # Tight layout
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)
            
            return img_base64
            
        except Exception as e:
            print(f"[MODERN_PDF] ⚠️ Error creating weekly activity chart: {str(e)}")
            return None
    
    def _prepare_learning_plans_data(self, user_data: Dict[str, Any], charts: Dict[str, str]) -> Dict[str, Any]:
        """Prepare data for learning plans template"""
        
        analytics = user_data.get('analytics', {})
        user_profile = user_data.get('user_profile', {})
        learning_plans = user_data.get('learning_plans', [])
        ai_insights = user_data.get('ai_insights', {})
        
        # Overview metrics
        overview = analytics.get('overview', {})
        overview_data = {
            'total_conversations': overview.get('total_conversations', 0),
            'total_practice_minutes': overview.get('total_practice_minutes', 0),
            'languages_studied': overview.get('languages_studied', 0),
            'total_learning_plans': overview.get('total_learning_plans', 0),
            'sessions_achievement': self._get_achievement_level(overview.get('total_conversations', 0), 'sessions'),
            'time_achievement': self._get_achievement_level(overview.get('total_practice_minutes', 0), 'time'),
            'language_achievement': self._get_achievement_level(overview.get('languages_studied', 0), 'languages'),
            'plans_achievement': self._get_achievement_level(overview.get('total_learning_plans', 0), 'plans')
        }
        
        # Progress data
        progress = analytics.get('progress', {})
        progress_data = {
            'total_sessions_completed': progress.get('total_sessions_completed', 0),
            'total_sessions_planned': progress.get('total_sessions_planned', 0),
            'overall_progress_percentage': progress.get('overall_progress_percentage', 0),
            'consistency_score': progress.get('consistency_score', 0),
            'consistency_description': self._get_consistency_description(progress.get('consistency_score', 0)),
            'consistency_recommendation': self._get_consistency_recommendation(progress.get('consistency_score', 0))
        }
        
        # Skills data
        skills = analytics.get('skills', {})
        skills_data = {
            'skill_breakdown': skills.get('skill_breakdown', {}),
            'trend_description': self._get_trend_description(skills.get('overall_skill_trend', 'stable'))
        }
        
        # Learning plans data
        plans_data = []
        for i, plan in enumerate(learning_plans, 1):
            created_date = 'N/A'
            if plan.get('created_at'):
                try:
                    date = datetime.fromisoformat(plan['created_at'].replace('Z', '+00:00'))
                    created_date = date.strftime('%m/%d/%Y')
                except:
                    pass
            
            plans_data.append({
                'language': plan.get('language', 'Unknown'),
                'proficiency_level': plan.get('proficiency_level', 'Unknown'),
                'progress_percentage': plan.get('progress_percentage', 0),
                'completed_sessions': plan.get('completed_sessions', 0),
                'total_sessions': plan.get('total_sessions', 0),
                'created_date': created_date
            })
        
        return {
            'report_title': 'Learning Plans & Assessment Report',
            'user_name': user_profile.get('name', 'Student'),
            'generation_date': datetime.now().strftime('%B %d, %Y'),
            'overview': overview_data,
            'progress': progress_data,
            'skills': skills_data,
            'learning_plans': plans_data,
            'ai_insights': ai_insights,
            'charts': charts
        }
    
    def _prepare_conversations_data(self, user_data: Dict[str, Any], charts: Dict[str, str]) -> Dict[str, Any]:
        """Prepare data for conversations template"""
        
        analytics = user_data.get('analytics', {})
        user_profile = user_data.get('user_profile', {})
        conversations = user_data.get('conversations', [])
        ai_insights = user_data.get('ai_insights', {})
        
        # Overview metrics for conversations
        overview = analytics.get('overview', {})
        overview_data = {
            'total_conversations': overview.get('total_conversations', 0),
            'total_practice_minutes': overview.get('total_practice_minutes', 0),
            'total_messages': overview.get('total_messages', 0),
            'enhanced_analyses': len([c for c in conversations if c.get('enhanced_analysis')]),
            'sessions_achievement': self._get_achievement_level(overview.get('total_conversations', 0), 'sessions'),
            'time_achievement': self._get_achievement_level(overview.get('total_practice_minutes', 0), 'time'),
            'messages_achievement': self._get_achievement_level(overview.get('total_messages', 0), 'messages'),
            'analysis_achievement': self._get_achievement_level(len([c for c in conversations if c.get('enhanced_analysis')]), 'analyses')
        }
        
        # Prepare conversations data for table
        conversations_data = []
        for i, conv in enumerate(conversations, 1):
            # Format date
            conv_date = 'N/A'
            if conv.get('created_at'):
                try:
                    date = datetime.fromisoformat(conv['created_at'].replace('Z', '+00:00'))
                    conv_date = date.strftime('%m/%d/%Y')
                except:
                    pass
            
            # Format duration
            duration = f"{conv.get('duration_minutes', 0):.1f}m"
            
            conversations_data.append({
                'date': conv_date,
                'language': conv.get('language', 'Unknown'),
                'level': conv.get('proficiency_level', 'Unknown'),
                'topic': conv.get('topic', 'General'),
                'duration': duration,
                'messages': conv.get('message_count', 0),
                'has_analysis': bool(conv.get('enhanced_analysis'))
            })
        
        # Prepare detailed analyses
        detailed_analyses = []
        for i, conv in enumerate(conversations, 1):
            if conv.get('enhanced_analysis'):
                analysis = conv['enhanced_analysis']
                
                # Parse quality metrics
                quality_metrics = {}
                if analysis.get('engagement_level') is not None:
                    quality_metrics['engagement'] = {
                        'score': analysis.get('engagement_level', 0),
                        'assessment': self._get_score_assessment(analysis.get('engagement_level', 0))
                    }
                if analysis.get('topic_depth') is not None:
                    quality_metrics['topic_depth'] = {
                        'score': analysis.get('topic_depth', 0),
                        'assessment': self._get_score_assessment(analysis.get('topic_depth', 0))
                    }
                if analysis.get('confidence_level') is not None:
                    quality_metrics['confidence_level'] = {
                        'score': analysis.get('confidence_level', 0),
                        'assessment': self._get_score_assessment(analysis.get('confidence_level', 0))
                    }
                
                detailed_analyses.append({
                    'session_number': i,
                    'language': conv.get('language', 'Unknown'),
                    'level': conv.get('proficiency_level', 'Unknown'),
                    'quality_metrics': quality_metrics,
                    'breakthrough_moments': analysis.get('breakthrough_moments', ''),
                    'areas_of_struggle': analysis.get('areas_of_struggle', ''),
                    'vocabulary_highlights': analysis.get('vocabulary_highlights', '')
                })
        
        return {
            'report_title': 'Conversation History & Analysis Report',
            'user_name': user_profile.get('name', 'Student'),
            'generation_date': datetime.now().strftime('%B %d, %Y'),
            'overview': overview_data,
            'conversations': conversations_data,
            'detailed_analyses': detailed_analyses,
            'ai_insights': ai_insights,
            'charts': charts
        }
    
    def _prepare_comprehensive_data(self, user_data: Dict[str, Any], charts: Dict[str, str]) -> Dict[str, Any]:
        """Prepare data for comprehensive template"""
        # For now, use the same structure as learning plans
        return self._prepare_learning_plans_data(user_data, charts)
    
    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render HTML template with data"""
        
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**data)
        except Exception as e:
            print(f"[MODERN_PDF] ❌ Error rendering template {template_name}: {str(e)}")
            raise
    
    def _html_to_pdf(self, html_content: str) -> BytesIO:
        """Convert HTML to PDF using WeasyPrint"""
        
        try:
            # Create PDF
            pdf_buffer = BytesIO()
            
            # Configure WeasyPrint
            html_doc = weasyprint.HTML(string=html_content)
            css_string = """
                @page {
                    size: A4;
                    margin: 1cm;
                }
            """
            css = weasyprint.CSS(string=css_string)
            
            # Generate PDF
            html_doc.write_pdf(pdf_buffer, stylesheets=[css])
            pdf_buffer.seek(0)
            
            return pdf_buffer
            
        except Exception as e:
            print(f"[MODERN_PDF] ❌ Error converting HTML to PDF: {str(e)}")
            raise
    
    def _generate_fallback_report(self, user_data: Dict[str, Any], title: str) -> BytesIO:
        """Generate a simple fallback report if main generation fails"""
        
        try:
            user_profile = user_data.get('user_profile', {})
            
            simple_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .header {{ background: #4ECFBF; color: white; padding: 20px; border-radius: 10px; }}
                    .content {{ margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{title}</h1>
                    <p>Generated for {user_profile.get('name', 'Student')} on {datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                <div class="content">
                    <p>Your learning report is being generated. Please try again in a moment.</p>
                    <p>If this issue persists, please contact support at hello@mytacoai.com</p>
                </div>
            </body>
            </html>
            """
            
            return self._html_to_pdf(simple_html)
            
        except Exception as e:
            print(f"[MODERN_PDF] ❌ Error generating fallback report: {str(e)}")
            # Return empty buffer as last resort
            return BytesIO()
    
    # Helper methods
    
    def _get_consistency_description(self, consistency: float) -> str:
        """Get consistency description"""
        if consistency >= 80:
            return "highly consistent"
        elif consistency >= 60:
            return "good"
        elif consistency >= 40:
            return "moderate"
        elif consistency >= 20:
            return "developing"
        else:
            return "inconsistent"
    
    def _get_consistency_recommendation(self, consistency: float) -> str:
        """Get consistency recommendation"""
        if consistency >= 80:
            return "Keep up the excellent work!"
        elif consistency >= 60:
            return "Try to practice a bit more regularly for optimal results."
        elif consistency >= 40:
            return "Consider setting a regular practice schedule to improve consistency."
        else:
            return "Focus on establishing a regular practice routine for better learning outcomes."
    
    def _get_trend_description(self, trend: str) -> str:
        """Get trend description"""
        descriptions = {
            'improving': "Your skills are showing consistent improvement across multiple areas!",
            'stable': "Your skills are maintaining steady performance levels.",
            'declining': "Some skills may need additional focus and practice."
        }
        return descriptions.get(trend, "Skill development analysis in progress.")
    
    def _get_score_assessment(self, score: float) -> str:
        """Get assessment description for a score"""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Needs Improvement"
        else:
            return "Needs Improvement"
    
    def _get_achievement_level(self, value: float, metric_type: str) -> str:
        """Get achievement level for metrics - updated with new metric types"""
        
        thresholds = {
            'sessions': [(20, 'Excellent'), (10, 'Good'), (0, 'Getting Started')],
            'time': [(120, 'Strong'), (60, 'Moderate'), (0, 'Building')],
            'languages': [(3, 'Multilingual'), (2, 'Bilingual'), (0, 'Focused')],
            'plans': [(3, 'Comprehensive'), (1, 'Structured'), (0, 'Planning Phase')],
            'messages': [(100, 'Very Active'), (50, 'Active'), (0, 'Getting Started')],
            'analyses': [(5, 'Comprehensive'), (2, 'Good'), (0, 'Basic')]
        }
        
        for threshold, level in thresholds.get(metric_type, [(0, 'Good')]):
            if value >= threshold:
                return level
        return 'Good'

# Maintain backward compatibility by providing the same interface as the old generator
class ProfessionalPDFGenerator:
    """Backward compatibility wrapper for the modern PDF generator"""
    
    @staticmethod
    def generate_comprehensive_report(user_data: Dict[str, Any], report_type: str = "comprehensive") -> BytesIO:
        """Generate a professional report - maintains exact API compatibility"""
        return ModernPDFGenerator.generate_comprehensive_report(user_data, report_type)
