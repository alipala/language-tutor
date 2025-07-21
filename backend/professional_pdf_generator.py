import os
import json
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics import renderPDF
from reportlab.graphics.widgetbase import Widget
from reportlab.graphics.charts.legends import Legend
from io import BytesIO
import statistics

class ProfessionalPDFGenerator:
    """Generate professional, AI-enhanced PDF reports"""
    
    # Professional color scheme
    COLORS = {
        'primary': colors.HexColor('#2563EB'),      # Professional blue
        'secondary': colors.HexColor('#10B981'),    # Success green
        'accent': colors.HexColor('#F59E0B'),       # Warning amber
        'danger': colors.HexColor('#EF4444'),       # Error red
        'dark': colors.HexColor('#1F2937'),         # Dark gray
        'medium': colors.HexColor('#6B7280'),       # Medium gray
        'light': colors.HexColor('#F3F4F6'),        # Light gray
        'white': colors.white,
        'teal': colors.HexColor('#14B8A6'),         # Teal
        'purple': colors.HexColor('#8B5CF6'),       # Purple
        'indigo': colors.HexColor('#6366F1'),       # Indigo
    }
    
    @staticmethod
    def generate_comprehensive_report(user_data: Dict[str, Any], report_type: str = "comprehensive") -> BytesIO:
        """Generate a professional report based on type"""
        
        if report_type == "learning_plans":
            return ProfessionalPDFGenerator.generate_learning_plans_report(user_data)
        elif report_type == "conversations":
            return ProfessionalPDFGenerator.generate_conversations_report(user_data)
        else:
            return ProfessionalPDFGenerator.generate_full_comprehensive_report(user_data)
    
    @staticmethod
    def generate_full_comprehensive_report(user_data: Dict[str, Any]) -> BytesIO:
        """Generate a comprehensive professional report"""
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            rightMargin=40, 
            leftMargin=40, 
            topMargin=60, 
            bottomMargin=60,
            title="Language Learning Progress Report"
        )
        
        # Create custom styles
        styles = ProfessionalPDFGenerator._create_custom_styles()
        
        # Build document content
        story = []
        
        # 1. Cover Page
        story.extend(ProfessionalPDFGenerator._create_cover_page(user_data, styles, "Comprehensive"))
        story.append(PageBreak())
        
        # 2. Executive Summary
        story.extend(ProfessionalPDFGenerator._create_executive_summary(user_data, styles))
        story.append(PageBreak())
        
        # 3. Learning Analytics Dashboard
        story.extend(ProfessionalPDFGenerator._create_analytics_dashboard(user_data, styles))
        story.append(PageBreak())
        
        # 4. Skill Development Analysis
        story.extend(ProfessionalPDFGenerator._create_skill_analysis(user_data, styles))
        story.append(PageBreak())
        
        # 5. Progress Tracking & Milestones
        story.extend(ProfessionalPDFGenerator._create_progress_tracking(user_data, styles))
        story.append(PageBreak())
        
        # 6. AI-Powered Insights & Recommendations
        story.extend(ProfessionalPDFGenerator._create_ai_insights_section(user_data, styles))
        story.append(PageBreak())
        
        # 7. Detailed Session Analysis
        story.extend(ProfessionalPDFGenerator._create_session_analysis(user_data, styles))
        story.append(PageBreak())
        
        # 8. Learning Plan Performance
        story.extend(ProfessionalPDFGenerator._create_learning_plan_performance(user_data, styles))
        story.append(PageBreak())
        
        # 9. Recommendations & Next Steps
        story.extend(ProfessionalPDFGenerator._create_recommendations_section(user_data, styles))
        
        # 10. Footer
        story.extend(ProfessionalPDFGenerator._create_footer(user_data, styles))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_learning_plans_report(user_data: Dict[str, Any]) -> BytesIO:
        """Generate a focused learning plans and assessments report"""
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            rightMargin=40, 
            leftMargin=40, 
            topMargin=60, 
            bottomMargin=60,
            title="Learning Plans & Assessment Report"
        )
        
        # Create custom styles
        styles = ProfessionalPDFGenerator._create_custom_styles()
        
        # Build document content
        story = []
        
        # 1. Cover Page
        story.extend(ProfessionalPDFGenerator._create_cover_page(user_data, styles, "Learning Plans & Assessments"))
        story.append(PageBreak())
        
        # 2. Learning Plan Performance (removed Assessment Summary section)
        story.extend(ProfessionalPDFGenerator._create_learning_plan_performance(user_data, styles))
        story.append(PageBreak())
        
        # 4. Progress Tracking & Milestones
        story.extend(ProfessionalPDFGenerator._create_progress_tracking(user_data, styles))
        story.append(PageBreak())
        
        # 5. Skill Development Analysis
        story.extend(ProfessionalPDFGenerator._create_skill_analysis(user_data, styles))
        story.append(PageBreak())
        
        # 6. AI-Powered Learning Insights
        story.extend(ProfessionalPDFGenerator._create_ai_insights_section(user_data, styles))
        story.append(PageBreak())
        
        # 7. Recommendations for Learning Plans
        story.extend(ProfessionalPDFGenerator._create_learning_recommendations(user_data, styles))
        
        # 8. Footer
        story.extend(ProfessionalPDFGenerator._create_footer(user_data, styles))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_conversations_report(user_data: Dict[str, Any]) -> BytesIO:
        """Generate a focused conversation analysis report"""
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            rightMargin=40, 
            leftMargin=40, 
            topMargin=60, 
            bottomMargin=60,
            title="Conversation Analysis Report"
        )
        
        # Create custom styles
        styles = ProfessionalPDFGenerator._create_custom_styles()
        
        # Build document content
        story = []
        
        # 1. Cover Page
        story.extend(ProfessionalPDFGenerator._create_cover_page(user_data, styles, "Conversation Analysis"))
        story.append(PageBreak())
        
        # 2. Conversation Overview
        story.extend(ProfessionalPDFGenerator._create_conversation_overview(user_data, styles))
        story.append(PageBreak())
        
        # 3. Detailed Session Analysis
        story.extend(ProfessionalPDFGenerator._create_session_analysis(user_data, styles))
        story.append(PageBreak())
        
        # 4. Engagement Patterns
        story.extend(ProfessionalPDFGenerator._create_engagement_analysis(user_data, styles))
        story.append(PageBreak())
        
        # 5. AI Conversation Insights
        story.extend(ProfessionalPDFGenerator._create_conversation_ai_insights(user_data, styles))
        story.append(PageBreak())
        
        # 6. Speaking & Communication Recommendations
        story.extend(ProfessionalPDFGenerator._create_conversation_recommendations(user_data, styles))
        
        # 7. Footer
        story.extend(ProfessionalPDFGenerator._create_footer(user_data, styles))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def _create_custom_styles():
        """Create custom paragraph styles for professional formatting"""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=ProfessionalPDFGenerator.COLORS['primary'],
            alignment=TA_CENTER,
            fontName='Times-Bold'
        ))
        
        # Section header style
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=8,
            spaceBefore=15,
            textColor=ProfessionalPDFGenerator.COLORS['dark'],
            fontName='Times-Bold',
            borderWidth=0,
            borderColor=ProfessionalPDFGenerator.COLORS['primary'],
            borderPadding=10
        ))
        
        # Subsection header style
        styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=4,
            spaceBefore=8,
            textColor=ProfessionalPDFGenerator.COLORS['primary'],
            fontName='Times-Bold'
        ))
        
        # Professional body text
        styles.add(ParagraphStyle(
            name='ProfessionalBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=2,
            textColor=ProfessionalPDFGenerator.COLORS['dark'],
            fontName='Times-Roman',
            alignment=TA_JUSTIFY
        ))
        
        # Highlight text
        styles.add(ParagraphStyle(
            name='Highlight',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=2,
            textColor=ProfessionalPDFGenerator.COLORS['primary'],
            fontName='Times-Bold'
        ))
        
        # Metric value style
        styles.add(ParagraphStyle(
            name='MetricValue',
            parent=styles['Normal'],
            fontSize=20,
            textColor=ProfessionalPDFGenerator.COLORS['primary'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        
        # Metric label style
        styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=styles['Normal'],
            fontSize=10,
            textColor=ProfessionalPDFGenerator.COLORS['medium'],
            fontName='Helvetica',
            alignment=TA_CENTER
        ))
        
        return styles
    
    @staticmethod
    def _create_cover_page(user_data: Dict[str, Any], styles, report_type: str = "Comprehensive") -> List:
        """Create professional cover page"""
        story = []
        user_profile = user_data.get('user_profile', {})
        analytics = user_data.get('analytics', {})
        
        # Spacer for top margin
        story.append(Spacer(1, 80))
        
        # Main title
        title_map = {
            "Comprehensive": "Language Learning Progress Report",
            "Learning Plans & Assessments": "Learning Plans & Assessment Report", 
            "Conversation Analysis": "Conversation Analysis Report"
        }
        
        story.append(Paragraph(
            title_map.get(report_type, "Language Learning Progress Report"),
            styles['CustomTitle']
        ))
        
        story.append(Spacer(1, 20))
        
        # Remove the subtitle - we don't want "Comprehensive for Milan Mateo"
        # story.append(Paragraph(
        #     f"{report_type} for {user_profile.get('name', 'Student')}",
        #     styles['Heading2']
        # ))
        
        story.append(Spacer(1, 40))
        
        # Key metrics overview table
        overview = analytics.get('overview', {})
        # Create meaningful achievement indicators based on actual values
        total_sessions = overview.get('total_conversations', 0)
        practice_minutes = overview.get('total_practice_minutes', 0)
        languages = overview.get('languages_studied', 0)
        account_days = overview.get('account_age_days', 0)
        learning_plans = overview.get('total_learning_plans', 0)
        
        metrics_data = [
            ['Metric', 'Value', 'Achievement Level'],
            ['Total Practice Sessions', str(total_sessions), 
             'Excellent' if total_sessions >= 20 else 'Good' if total_sessions >= 10 else 'Getting Started'],
            ['Practice Time', f"{practice_minutes:.1f} minutes", 
             'Strong' if practice_minutes >= 120 else 'Moderate' if practice_minutes >= 60 else 'Building'],
            ['Languages Studied', str(languages), 
             'Multilingual' if languages >= 3 else 'Bilingual' if languages >= 2 else 'Focused'],
            ['Account Age', f"{account_days} days", 
             'Experienced' if account_days >= 90 else 'Developing' if account_days >= 30 else 'New Learner'],
            ['Learning Plans', str(learning_plans), 
             'Comprehensive' if learning_plans >= 3 else 'Structured' if learning_plans >= 1 else 'Planning Phase']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ProfessionalPDFGenerator.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), ProfessionalPDFGenerator.COLORS['dark']),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, ProfessionalPDFGenerator.COLORS['light']),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ProfessionalPDFGenerator.COLORS['light']])
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 60))
        
        # Remove metadata table as requested
        # story.append(metadata_table)
        
        return story
    
    @staticmethod
    def _create_executive_summary(user_data: Dict[str, Any], styles) -> List:
        """Create executive summary section"""
        story = []
        ai_insights = user_data.get('ai_insights', {})
        analytics = user_data.get('analytics', {})
        
        # Section header
        story.append(Paragraph("Executive Summary", styles['SectionHeader']))
        
        # AI-generated executive summary
        executive_summary = ai_insights.get('executive_summary', 
            'This report provides a comprehensive analysis of the student\'s language learning progress and achievements.')
        
        story.append(Paragraph(executive_summary, styles['ProfessionalBody']))
        story.append(Spacer(1, 20))
        
        # Key achievements section
        story.append(Paragraph("Key Achievements", styles['SubsectionHeader']))
        
        achievements = ai_insights.get('key_achievements', [])
        for achievement in achievements:
            story.append(Paragraph(f"• {achievement}", styles['ProfessionalBody']))
        
        story.append(Spacer(1, 20))
        
        # Learning strengths
        story.append(Paragraph("Learning Strengths", styles['SubsectionHeader']))
        
        strengths = ai_insights.get('learning_strengths', [])
        for strength in strengths:
            story.append(Paragraph(f"• {strength}", styles['ProfessionalBody']))
        
        story.append(Spacer(1, 20))
        
        # Quick stats table
        progress = analytics.get('progress', {})
        engagement = analytics.get('engagement', {})
        
        quick_stats_data = [
            ['Key Metric', 'Current Status', 'Assessment'],
            ['Overall Progress', f"{progress.get('overall_progress_percentage', 0):.1f}%", 
             ProfessionalPDFGenerator._get_progress_assessment(progress.get('overall_progress_percentage', 0))],
            ['Consistency Score', f"{progress.get('consistency_score', 0):.1f}%",
             ProfessionalPDFGenerator._get_consistency_assessment(progress.get('consistency_score', 0))],
            ['Session Completion', f"{engagement.get('session_completion_rate', 0):.1f}%",
             ProfessionalPDFGenerator._get_completion_assessment(engagement.get('session_completion_rate', 0))],
            ['Avg Session Duration', f"{engagement.get('average_session_duration', 0):.1f} min",
             ProfessionalPDFGenerator._get_duration_assessment(engagement.get('average_session_duration', 0))]
        ]
        
        quick_stats_table = Table(quick_stats_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        quick_stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ProfessionalPDFGenerator.COLORS['secondary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), ProfessionalPDFGenerator.COLORS['dark']),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, ProfessionalPDFGenerator.COLORS['light']),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(quick_stats_table)
        
        return story
    
    @staticmethod
    def _create_analytics_dashboard(user_data: Dict[str, Any], styles) -> List:
        """Create analytics dashboard with visual elements"""
        story = []
        analytics = user_data.get('analytics', {})
        
        story.append(Paragraph("Learning Analytics Dashboard", styles['SectionHeader']))
        
        # Overview metrics
        overview = analytics.get('overview', {})
        progress = analytics.get('progress', {})
        engagement = analytics.get('engagement', {})
        
        # Create metrics grid
        metrics_grid_data = [
            ['Total Sessions', 'Practice Time', 'Languages', 'Consistency'],
            [str(overview.get('total_conversations', 0)), 
             f"{overview.get('total_practice_minutes', 0):.0f} min",
             str(overview.get('languages_studied', 0)),
             f"{progress.get('consistency_score', 0):.1f}%"],
            ['Avg Duration', 'Completion Rate', 'Weekly Trend', 'Recent Activity'],
            [f"{engagement.get('average_session_duration', 0):.1f} min",
             f"{engagement.get('session_completion_rate', 0):.1f}%",
             progress.get('weekly_trends', {}).get('trend', 'stable').title(),
             f"{overview.get('recent_conversations_30d', 0)} sessions"]
        ]
        
        metrics_grid = Table(metrics_grid_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        metrics_grid.setStyle(TableStyle([
            # Header rows
            ('BACKGROUND', (0, 0), (-1, 0), ProfessionalPDFGenerator.COLORS['primary']),
            ('BACKGROUND', (0, 2), (-1, 2), ProfessionalPDFGenerator.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 2), (-1, 2), 10),
            # Value rows
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('BACKGROUND', (0, 3), (-1, 3), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, 1), ProfessionalPDFGenerator.COLORS['primary']),
            ('TEXTCOLOR', (0, 3), (-1, 3), ProfessionalPDFGenerator.COLORS['primary']),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('FONTSIZE', (0, 3), (-1, 3), 14),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, ProfessionalPDFGenerator.COLORS['light']),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(metrics_grid)
        story.append(Spacer(1, 30))
        
        # Progress by language (if multiple languages)
        progress_by_lang = progress.get('progress_by_language', {})
        if len(progress_by_lang) > 1:
            story.append(Paragraph("Progress by Language", styles['SubsectionHeader']))
            
            lang_progress_data = [['Language', 'Sessions Completed', 'Total Sessions', 'Progress %']]
            for lang, data in progress_by_lang.items():
                lang_progress_data.append([
                    lang.title(),
                    str(data.get('completed_sessions', 0)),
                    str(data.get('total_sessions', 0)),
                    f"{data.get('progress_percentage', 0):.1f}%"
                ])
            
            lang_progress_table = Table(lang_progress_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            lang_progress_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), ProfessionalPDFGenerator.COLORS['teal']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), ProfessionalPDFGenerator.COLORS['dark']),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, ProfessionalPDFGenerator.COLORS['light']),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ProfessionalPDFGenerator.COLORS['light']])
            ]))
            
            story.append(lang_progress_table)
            story.append(Spacer(1, 20))
        
        # Engagement patterns
        story.append(Paragraph("📈 Engagement Patterns", styles['SubsectionHeader']))
        
        peak_periods = engagement.get('peak_engagement_periods', {})
        preferred_topics = engagement.get('preferred_topics', {})
        
        engagement_info = [
            f"• Most active time: {peak_periods.get('peak_hour', 12)}:00",
            f"• Preferred day: {peak_periods.get('peak_day', 'Monday')}",
            f"• Average messages per session: {engagement.get('average_messages_per_session', 0):.1f}",
        ]
        
        if preferred_topics:
            top_topic = max(preferred_topics.items(), key=lambda x: x[1])
            engagement_info.append(f"• Most discussed topic: {top_topic[0]} ({top_topic[1]} sessions)")
        
        for info in engagement_info:
            story.append(Paragraph(info, styles['ProfessionalBody']))
        
        return story
    
    @staticmethod
    def _create_skill_analysis(user_data: Dict[str, Any], styles) -> List:
        """Create detailed skill development analysis"""
        story = []
        analytics = user_data.get('analytics', {})
        skills = analytics.get('skills', {})
        
        story.append(Paragraph("Skill Development Analysis", styles['SectionHeader']))
        
        if skills.get('status') == 'no_enhanced_data':
            story.append(Paragraph(
                "Enhanced skill analysis is available after completing sessions with detailed feedback. "
                "Continue practicing to unlock comprehensive skill tracking.",
                styles['ProfessionalBody']
            ))
            return story
        
        skill_breakdown = skills.get('skill_breakdown', {})
        overall_trend = skills.get('overall_skill_trend', 'stable')
        
        # Overall skill trend
        story.append(Paragraph("📊 Overall Skill Development Trend", styles['SubsectionHeader']))
        trend_text = {
            'improving': "🔥 Your skills are showing consistent improvement across multiple areas!",
            'stable': "📊 Your skills are maintaining steady performance levels.",
            'declining': "⚠️ Some skills may need additional focus and practice."
        }.get(overall_trend, "📊 Skill development analysis in progress.")
        
        story.append(Paragraph(trend_text, styles['ProfessionalBody']))
        story.append(Spacer(1, 15))
        
        # Detailed skill breakdown
        if skill_breakdown:
            story.append(Paragraph("🔍 Detailed Skill Breakdown", styles['SubsectionHeader']))
            
            skill_data = [['Skill Area', 'Average Score', 'Latest Score', 'Trend', 'Improvement']]
            
            for skill, data in skill_breakdown.items():
                trend_text = {
                    'improving': 'UP Improving',
                    'stable': '-> Stable',
                    'declining': 'DOWN Declining'
                }.get(data.get('trend', 'stable'), '-> Stable')
                
                improvement = data.get('improvement', 0)
                improvement_text = f"+{improvement:.1f}" if improvement > 0 else f"{improvement:.1f}"
                
                skill_data.append([
                    skill.replace('_', ' ').title(),
                    f"{data.get('average_score', 0):.1f}",
                    f"{data.get('latest_score', 0):.1f}",
                    trend_text,
                    improvement_text
                ])
            
            skill_table = Table(skill_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.5*inch, 1*inch])
            skill_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), ProfessionalPDFGenerator.COLORS['purple']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), ProfessionalPDFGenerator.COLORS['dark']),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, ProfessionalPDFGenerator.COLORS['light']),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ProfessionalPDFGenerator.COLORS['light']])
            ]))
            
            story.append(skill_table)
        
        return story
    
    @staticmethod
    def _create_progress_tracking(user_data: Dict[str, Any], styles) -> List:
        """Create progress tracking and milestones section"""
        story = []
        analytics = user_data.get('analytics', {})
        progress = analytics.get('progress', {})
        
        story.append(Paragraph("Progress Tracking & Milestones", styles['SectionHeader']))
        
        # Overall progress summary
        overall_progress = progress.get('overall_progress_percentage', 0)
        total_planned = progress.get('total_sessions_planned', 0)
        total_completed = progress.get('total_sessions_completed', 0)
        
        story.append(Paragraph("🎯 Overall Learning Progress", styles['SubsectionHeader']))
        
        progress_summary = f"""
        You have completed {total_completed} out of {total_planned} planned learning sessions, 
        achieving {overall_progress:.1f}% of your overall learning goals. This represents 
        {ProfessionalPDFGenerator._get_progress_description(overall_progress)} progress in your language learning journey.
        """
        
        story.append(Paragraph(progress_summary.strip(), styles['ProfessionalBody']))
        story.append(Spacer(1, 15))
        
        # Weekly trends
        weekly_trends = progress.get('weekly_trends', {})
        if weekly_trends.get('weeks_analyzed', 0) > 0:
            story.append(Paragraph("📅 Weekly Learning Patterns", styles['SubsectionHeader']))
            
            trend = weekly_trends.get('trend', 'stable')
            weeks_analyzed = weekly_trends.get('weeks_analyzed', 0)
            recent_avg = weekly_trends.get('recent_weekly_average', 0)
            
            trend_descriptions = {
                'improving': f"📈 Your learning activity is increasing! Recent weeks show an average of {recent_avg:.1f} sessions per week.",
                'stable': f"📊 You maintain consistent learning habits with {recent_avg:.1f} sessions per week on average.",
                'declining': f"📉 Your recent activity has decreased to {recent_avg:.1f} sessions per week. Consider setting a regular practice schedule."
            }
            
            story.append(Paragraph(
                trend_descriptions.get(trend, f"Analysis based on {weeks_analyzed} weeks of data."),
                styles['ProfessionalBody']
            ))
            story.append(Spacer(1, 15))
        
        # Consistency analysis
        consistency_score = progress.get('consistency_score', 0)
        story.append(Paragraph("🔄 Learning Consistency", styles['SubsectionHeader']))
        
        consistency_text = f"""
        Your consistency score is {consistency_score:.1f}%, indicating 
        {ProfessionalPDFGenerator._get_consistency_description(consistency_score)} learning habits. 
        {ProfessionalPDFGenerator._get_consistency_recommendation(consistency_score)}
        """
        
        story.append(Paragraph(consistency_text.strip(), styles['ProfessionalBody']))
        
        return story
    
    @staticmethod
    def _create_ai_insights_section(user_data: Dict[str, Any], styles) -> List:
        """Create AI-powered insights and recommendations section"""
        story = []
        ai_insights = user_data.get('ai_insights', {})
        
        story.append(Paragraph("AI-Powered Learning Insights", styles['SectionHeader']))
        
        # Professional assessment
        professional_assessment = ai_insights.get('professional_assessment', 
            'The student demonstrates commitment to language learning through consistent practice and engagement.')
        
        story.append(Paragraph("📝 Professional Assessment", styles['SubsectionHeader']))
        story.append(Paragraph(professional_assessment, styles['ProfessionalBody']))
        story.append(Spacer(1, 20))
        
        # Learning insights
        learning_insights = ai_insights.get('learning_insights', {})
        if learning_insights:
            story.append(Paragraph("🧠 Learning Style Analysis", styles['SubsectionHeader']))
            
            insights_data = []
            if learning_insights.get('learning_style_assessment'):
                insights_data.append(['Learning Style', learning_insights['learning_style_assessment']])
            if learning_insights.get('motivation_indicators'):
                insights_data.append(['Motivation Level', learning_insights['motivation_indicators']])
            if learning_insights.get('progress_trajectory'):
                insights_data.append(['Progress Trajectory', learning_insights['progress_trajectory']])
            
            if insights_data:
                # Convert text to Paragraph objects for proper wrapping
                wrapped_insights_data = []
                for row in insights_data:
                    wrapped_row = [
                        Paragraph(row[0], styles['Highlight']),
                        Paragraph(row[1], styles['ProfessionalBody'])
                    ]
                    wrapped_insights_data.append(wrapped_row)
                
                insights_table = Table(wrapped_insights_data, colWidths=[2*inch, 4*inch])
                insights_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('TEXTCOLOR', (0, 0), (0, -1), ProfessionalPDFGenerator.COLORS['primary']),
                    ('TEXTCOLOR', (1, 0), (1, -1), ProfessionalPDFGenerator.COLORS['dark']),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, ProfessionalPDFGenerator.COLORS['light']),
                ]))
                story.append(insights_table)
        
        # Improvement opportunities
        story.append(Spacer(1, 20))
        story.append(Paragraph("🎯 Areas for Improvement", styles['SubsectionHeader']))
        
        improvements = ai_insights.get('improvement_opportunities', [])
        for improvement in improvements:
            # Handle both string and dict formats
            if isinstance(improvement, dict):
                area = improvement.get('area', 'General')
                suggestion = improvement.get('suggestion', str(improvement))
                story.append(Paragraph(f"• {area}: {suggestion}", styles['ProfessionalBody']))
            else:
                story.append(Paragraph(f"• {improvement}", styles['ProfessionalBody']))
        
        return story
    
    @staticmethod
    def _create_session_analysis(user_data: Dict[str, Any], styles) -> List:
        """Create detailed session analysis"""
        story = []
        conversations = user_data.get('conversations', [])
        analytics = user_data.get('analytics', {})
        
        story.append(Paragraph("💬 Detailed Session Analysis", styles['SectionHeader']))
        
        if not conversations:
            story.append(Paragraph("No conversation sessions found.", styles['ProfessionalBody']))
            return story
        
        # Recent sessions overview
        recent_sessions = conversations[:10]  # Last 10 sessions
        
        story.append(Paragraph("📊 Recent Sessions Overview", styles['SubsectionHeader']))
        
        session_data = [['Date', 'Language', 'Topic', 'Duration', 'Messages', 'Enhanced Analysis']]
        
        for session in recent_sessions:
            created_at = 'N/A'
            if session.get('created_at'):
                try:
                    date = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
                    created_at = date.strftime('%m/%d/%Y')
                except:
                    pass
            
            has_analysis = '✓' if session.get('enhanced_analysis') else '✗'
            
            session_data.append([
                created_at,
                session.get('language', 'Unknown').title(),
                session.get('topic', 'General')[:15] + ('...' if len(session.get('topic', '')) > 15 else ''),
                f"{session.get('duration_minutes', 0):.1f}m",
                str(session.get('message_count', 0)),
                has_analysis
            ])
        
        session_table = Table(session_data, colWidths=[1*inch, 1*inch, 1.2*inch, 0.8*inch, 0.8*inch, 1.2*inch])
        session_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ProfessionalPDFGenerator.COLORS['indigo']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), ProfessionalPDFGenerator.COLORS['dark']),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, ProfessionalPDFGenerator.COLORS['light']),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ProfessionalPDFGenerator.COLORS['light']])
        ]))
        
        story.append(session_table)
        story.append(Spacer(1, 20))
        
        # Enhanced analysis sessions
        enhanced_sessions = [s for s in conversations if s.get('enhanced_analysis')]
        if enhanced_sessions:
            story.append(Paragraph("🔍 Enhanced Analysis Highlights", styles['SubsectionHeader']))
            
            for i, session in enumerate(enhanced_sessions[:3]):  # Show top 3
                analysis = session.get('enhanced_analysis', {})
                ai_insights = analysis.get('ai_insights', {})
                
                session_title = f"Session {i+1}: {session.get('topic', 'General')} ({session.get('language', 'Unknown')})"
                story.append(Paragraph(session_title, styles['Highlight']))
                
                # Key insights
                if ai_insights.get('breakthrough_moments'):
                    story.append(Paragraph(
                        f"Breakthrough: {ai_insights['breakthrough_moments'][0][:100]}...",
                        styles['ProfessionalBody']
                    ))
                
                if ai_insights.get('confidence_level'):
                    story.append(Paragraph(
                        f"Confidence Level: {ai_insights['confidence_level']}/100",
                        styles['ProfessionalBody']
                    ))
                
                story.append(Spacer(1, 10))
        
        return story
    
    @staticmethod
    def _create_learning_plan_performance(user_data: Dict[str, Any], styles) -> List:
        """Create learning plan performance analysis"""
        story = []
        learning_plans = user_data.get('learning_plans', [])
        analytics = user_data.get('analytics', {})
        
        story.append(Paragraph("📚 Learning Plan Performance", styles['SectionHeader']))
        
        if not learning_plans:
            story.append(Paragraph("No learning plans found.", styles['ProfessionalBody']))
            return story
        
        # Plans overview
        story.append(Paragraph("📋 Plans Overview", styles['SubsectionHeader']))
        
        plan_data = [['Plan', 'Language', 'Level', 'Progress', 'Sessions', 'Created']]
        
        for i, plan in enumerate(learning_plans, 1):
            created_at = 'N/A'
            if plan.get('created_at'):
                try:
                    date = datetime.fromisoformat(plan['created_at'].replace('Z', '+00:00'))
                    created_at = date.strftime('%m/%d/%Y')
                except:
                    pass
            
            progress = plan.get('progress_percentage', 0)
            completed = plan.get('completed_sessions', 0)
            total = plan.get('total_sessions', 0)
            
            plan_data.append([
                f"Plan {i}",
                plan.get('language', 'Unknown').title(),
                plan.get('proficiency_level', 'Unknown'),
                f"{progress:.1f}%",
                f"{completed}/{total}",
                created_at
            ])
        
        plan_table = Table(plan_data, colWidths=[0.8*inch, 1*inch, 0.8*inch, 1*inch, 1*inch, 1.4*inch])
        plan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ProfessionalPDFGenerator.COLORS['accent']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), ProfessionalPDFGenerator.COLORS['dark']),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, ProfessionalPDFGenerator.COLORS['light']),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ProfessionalPDFGenerator.COLORS['light']])
        ]))
        
        story.append(plan_table)
        story.append(Spacer(1, 20))
        
        # Goal achievement analysis
        goals = analytics.get('goals', {})
        if goals.get('status') != 'no_plans':
            story.append(Paragraph("🎯 Goal Achievement Analysis", styles['SubsectionHeader']))
            
            goal_summary = goals.get('goal_achievement_summary', {})
            if goal_summary.get('status') != 'no_goals':
                overall_completion = goal_summary.get('overall_completion_rate', 0)
                story.append(Paragraph(
                    f"Overall goal completion rate: {overall_completion:.1f}%",
                    styles['ProfessionalBody']
                ))
                
                # High achievement goals
                high_goals = goal_summary.get('high_achievement_goals', [])
                if high_goals:
                    story.append(Paragraph("High Achievement Goals:", styles['Highlight']))
                    for goal in high_goals[:3]:
                        story.append(Paragraph(f"• {goal}", styles['ProfessionalBody']))
        
        return story
    
    @staticmethod
    def _create_recommendations_section(user_data: Dict[str, Any], styles) -> List:
        """Create recommendations and next steps section"""
        story = []
        ai_insights = user_data.get('ai_insights', {})
        
        story.append(Paragraph("🚀 Recommendations & Next Steps", styles['SectionHeader']))
        
        recommendations = ai_insights.get('personalized_recommendations', {})
        
        # Immediate actions
        immediate_actions = recommendations.get('immediate_actions', [])
        if immediate_actions:
            story.append(Paragraph("⚡ Immediate Actions (This Week)", styles['SubsectionHeader']))
            for action in immediate_actions:
                story.append(Paragraph(f"• {action}", styles['ProfessionalBody']))
            story.append(Spacer(1, 15))
        
        # Monthly focus
        monthly_focus = recommendations.get('monthly_focus', [])
        if monthly_focus:
            story.append(Paragraph("📅 Monthly Focus Areas", styles['SubsectionHeader']))
            for focus in monthly_focus:
                story.append(Paragraph(f"• {focus}", styles['ProfessionalBody']))
            story.append(Spacer(1, 15))
        
        # Long-term strategy
        long_term = recommendations.get('long_term_strategy', [])
        if long_term:
            story.append(Paragraph("🎯 Long-term Strategy", styles['SubsectionHeader']))
            for strategy in long_term:
                story.append(Paragraph(f"• {strategy}", styles['ProfessionalBody']))
        
        return story
    
    @staticmethod
    def _create_footer(user_data: Dict[str, Any], styles) -> List:
        """Create report footer"""
        story = []
        
        story.append(Spacer(1, 40))
        story.append(HRFlowable(width="100%", thickness=1, color=ProfessionalPDFGenerator.COLORS['light']))
        story.append(Spacer(1, 20))
        
        footer_data = [
            ['Generated by My Taco AI Learning Platform'],
            ['Professional Language Learning Analytics & Insights'],
            ['For support: hello@mytacoai.com | www.mytacoai.com']
        ]
        
        footer_table = Table(footer_data, colWidths=[6*inch])
        footer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, 1), 10),
            ('FONTSIZE', (0, 2), (-1, 2), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), ProfessionalPDFGenerator.COLORS['primary']),
            ('TEXTCOLOR', (0, 1), (-1, -1), ProfessionalPDFGenerator.COLORS['medium']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(footer_table)
        
        return story
    
    # Helper methods for assessments
    @staticmethod
    def _get_progress_assessment(progress: float) -> str:
        if progress >= 80:
            return "Excellent Progress"
        elif progress >= 60:
            return "Good Progress"
        elif progress >= 40:
            return "Moderate Progress"
        elif progress >= 20:
            return "Early Progress"
        else:
            return "Getting Started"
    
    @staticmethod
    def _get_consistency_assessment(consistency: float) -> str:
        if consistency >= 80:
            return "Highly Consistent"
        elif consistency >= 60:
            return "Good Consistency"
        elif consistency >= 40:
            return "Moderate Consistency"
        elif consistency >= 20:
            return "Developing Consistency"
        else:
            return "Needs Improvement"
    
    @staticmethod
    def _get_completion_assessment(completion: float) -> str:
        if completion >= 90:
            return "Excellent Completion"
        elif completion >= 75:
            return "Good Completion"
        elif completion >= 60:
            return "Fair Completion"
        else:
            return "Needs Improvement"
    
    @staticmethod
    def _get_duration_assessment(duration: float) -> str:
        if duration >= 8:
            return "Optimal Duration"
        elif duration >= 5:
            return "Good Duration"
        elif duration >= 3:
            return "Adequate Duration"
        else:
            return "Short Sessions"
    
    @staticmethod
    def _get_progress_description(progress: float) -> str:
        if progress >= 80:
            return "exceptional"
        elif progress >= 60:
            return "strong"
        elif progress >= 40:
            return "steady"
        elif progress >= 20:
            return "developing"
        else:
            return "initial"
    
    @staticmethod
    def _get_consistency_description(consistency: float) -> str:
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
    
    @staticmethod
    def _get_consistency_recommendation(consistency: float) -> str:
        if consistency >= 80:
            return "Keep up the excellent work!"
        elif consistency >= 60:
            return "Try to practice a bit more regularly for optimal results."
        elif consistency >= 40:
            return "Consider setting a regular practice schedule to improve consistency."
        else:
            return "Focus on establishing a regular practice routine for better learning outcomes."
    
    # Additional methods for specialized reports
    @staticmethod
    def _create_assessment_summary(user_data: Dict[str, Any], styles) -> List:
        """Create assessment summary for learning plans report"""
        story = []
        analytics = user_data.get('analytics', {})
        proficiency = analytics.get('proficiency', {})
        
        story.append(Paragraph("📊 Assessment Summary", styles['SectionHeader']))
        
        assessment_trends = proficiency.get('assessment_trends', {})
        if assessment_trends.get('status') != 'no_assessment_data':
            latest_score = assessment_trends.get('latest_score', 0)
            average_score = assessment_trends.get('average_score', 0)
            improvement = assessment_trends.get('score_improvement', 0)
            
            story.append(Paragraph(f"Latest Assessment Score: {latest_score:.1f}/100", styles['Highlight']))
            story.append(Paragraph(f"Average Score: {average_score:.1f}/100", styles['ProfessionalBody']))
            story.append(Paragraph(f"Overall Improvement: {improvement:+.1f} points", styles['ProfessionalBody']))
        else:
            story.append(Paragraph("Complete your first assessment to see detailed analysis here.", styles['ProfessionalBody']))
        
        return story
    
    @staticmethod
    def _create_learning_recommendations(user_data: Dict[str, Any], styles) -> List:
        """Create learning-focused recommendations"""
        story = []
        ai_insights = user_data.get('ai_insights', {})
        
        story.append(Paragraph("🎯 Learning Plan Recommendations", styles['SectionHeader']))
        
        recommendations = ai_insights.get('personalized_recommendations', {})
        monthly_focus = recommendations.get('monthly_focus', [])
        
        for focus in monthly_focus:
            story.append(Paragraph(f"• {focus}", styles['ProfessionalBody']))
        
        return story
    
    @staticmethod
    def _create_conversation_overview(user_data: Dict[str, Any], styles) -> List:
        """Create conversation overview for conversation report"""
        story = []
        analytics = user_data.get('analytics', {})
        engagement = analytics.get('engagement', {})
        
        story.append(Paragraph("💬 Conversation Overview", styles['SectionHeader']))
        
        total_sessions = analytics.get('overview', {}).get('total_conversations', 0)
        avg_duration = engagement.get('average_session_duration', 0)
        avg_messages = engagement.get('average_messages_per_session', 0)
        
        story.append(Paragraph(f"Total Conversation Sessions: {total_sessions}", styles['Highlight']))
        story.append(Paragraph(f"Average Session Duration: {avg_duration:.1f} minutes", styles['ProfessionalBody']))
        story.append(Paragraph(f"Average Messages per Session: {avg_messages:.1f}", styles['ProfessionalBody']))
        
        return story
    
    @staticmethod
    def _create_engagement_analysis(user_data: Dict[str, Any], styles) -> List:
        """Create detailed engagement analysis"""
        story = []
        analytics = user_data.get('analytics', {})
        engagement = analytics.get('engagement', {})
        
        story.append(Paragraph("📈 Engagement Analysis", styles['SectionHeader']))
        
        completion_rate = engagement.get('session_completion_rate', 0)
        preferred_topics = engagement.get('preferred_topics', {})
        
        story.append(Paragraph(f"Session Completion Rate: {completion_rate:.1f}%", styles['Highlight']))
        
        if preferred_topics:
            story.append(Paragraph("Most Discussed Topics:", styles['SubsectionHeader']))
            for topic, count in list(preferred_topics.items())[:5]:
                story.append(Paragraph(f"• {topic}: {count} sessions", styles['ProfessionalBody']))
        
        return story
    
    @staticmethod
    def _create_conversation_ai_insights(user_data: Dict[str, Any], styles) -> List:
        """Create AI insights focused on conversations"""
        story = []
        ai_insights = user_data.get('ai_insights', {})
        
        story.append(Paragraph("🤖 AI Conversation Insights", styles['SectionHeader']))
        
        learning_insights = ai_insights.get('learning_insights', {})
        if learning_insights.get('learning_style_assessment'):
            story.append(Paragraph("Communication Style:", styles['Highlight']))
            story.append(Paragraph(learning_insights['learning_style_assessment'], styles['ProfessionalBody']))
        
        return story
    
    @staticmethod
    def _create_conversation_recommendations(user_data: Dict[str, Any], styles) -> List:
        """Create conversation-focused recommendations"""
        story = []
        ai_insights = user_data.get('ai_insights', {})
        
        story.append(Paragraph("🗣️ Speaking & Communication Recommendations", styles['SectionHeader']))
        
        recommendations = ai_insights.get('personalized_recommendations', {})
        immediate_actions = recommendations.get('immediate_actions', [])
        
        for action in immediate_actions:
            if 'speak' in action.lower() or 'conversation' in action.lower() or 'practice' in action.lower():
                story.append(Paragraph(f"• {action}", styles['ProfessionalBody']))
        
        return story
