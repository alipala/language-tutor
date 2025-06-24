import os
import json
import io
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import zipfile
from io import BytesIO

from auth import get_current_user
from models import UserResponse
from database import conversation_sessions_collection, learning_plans_collection, users_collection

router = APIRouter(prefix="/api/export", tags=["export"])

class ExportService:
    """Service for generating export documents"""
    
    @staticmethod
    async def get_user_data(user_id: str) -> Dict[str, Any]:
        """Collect all user data for export"""
        
        # Get user profile - handle both ObjectId and string formats
        from bson import ObjectId
        
        # Try to find user with string ID first
        user = await users_collection.find_one({"_id": user_id})
        
        # If not found and user_id looks like ObjectId, try ObjectId format
        if not user and ObjectId.is_valid(user_id):
            try:
                user = await users_collection.find_one({"_id": ObjectId(user_id)})
            except:
                pass
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get learning plans
        learning_plans = await learning_plans_collection.find({"user_id": user_id}).to_list(length=None)
        
        # Get conversation sessions
        conversations = await conversation_sessions_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).to_list(length=None)
        
        # Calculate statistics
        total_sessions = len(conversations)
        total_minutes = sum(session.get('duration_minutes', 0) for session in conversations)
        total_messages = sum(session.get('message_count', 0) for session in conversations)
        
        # Get sessions with enhanced analysis
        enhanced_sessions = [s for s in conversations if s.get('enhanced_analysis')]
        
        # Organize data by language
        languages_data = {}
        for plan in learning_plans:
            lang = plan.get('language', 'Unknown')
            if lang not in languages_data:
                languages_data[lang] = {
                    'learning_plans': [],
                    'conversations': [],
                    'assessments': []
                }
            languages_data[lang]['learning_plans'].append(plan)
        
        for conversation in conversations:
            lang = conversation.get('language', 'Unknown')
            if lang not in languages_data:
                languages_data[lang] = {
                    'learning_plans': [],
                    'conversations': [],
                    'assessments': []
                }
            languages_data[lang]['conversations'].append(conversation)
        
        return {
            'user_profile': {
                'name': user.get('name', ''),
                'email': user.get('email', ''),
                'preferred_language': user.get('preferred_language', ''),
                'preferred_level': user.get('preferred_level', ''),
                'created_at': user.get('created_at', ''),
                'last_assessment_data': user.get('last_assessment_data')
            },
            'statistics': {
                'total_sessions': total_sessions,
                'total_minutes': round(total_minutes, 2),
                'total_messages': total_messages,
                'enhanced_analyses': len(enhanced_sessions),
                'languages_studied': len(languages_data)
            },
            'learning_plans': learning_plans,
            'conversations': conversations,
            'enhanced_sessions': enhanced_sessions,
            'languages_data': languages_data,
            'export_date': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def generate_learning_plans_pdf(user_data: Dict[str, Any]) -> BytesIO:
        """Generate comprehensive table-based PDF report for learning plans with statistics"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        
        # App-inspired color scheme
        primary_color = colors.HexColor('#4ECFBF')  # Teal (app primary)
        secondary_color = colors.HexColor('#2563EB')  # Blue
        accent_color = colors.HexColor('#F59E0B')  # Amber
        success_color = colors.HexColor('#10B981')  # Green
        text_color = colors.HexColor('#1F2937')  # Dark gray
        light_bg = colors.HexColor('#F0FDFA')  # Very light teal
        
        # Build document content
        story = []
        user_profile = user_data['user_profile']
        learning_plans = user_data['learning_plans']
        
        # Header
        header_data = [['🎓 Assessment & Learning Plans Report']]
        header_table = Table(header_data, colWidths=[7*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), primary_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 20),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # Student Profile Table
        profile_header = [['👤 Student Profile']]
        profile_header_table = Table(profile_header, colWidths=[7*inch])
        profile_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), secondary_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(profile_header_table)
        
        profile_data = [
            ['Student Name', user_profile['name']],
            ['Email Address', user_profile['email']],
            ['Report Generated', datetime.fromisoformat(user_data['export_date']).strftime('%B %d, %Y at %I:%M %p')],
            ['Total Learning Plans', str(len(learning_plans))]
        ]
        
        profile_table = Table(profile_data, colWidths=[2.5*inch, 4.5*inch])
        profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (0, -1), secondary_color),
            ('TEXTCOLOR', (1, 0), (1, -1), text_color),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
        ]))
        story.append(profile_table)
        story.append(Spacer(1, 25))
        
        # Learning Statistics Overview Table
        stats_header = [['📊 Learning Statistics Overview']]
        stats_header_table = Table(stats_header, colWidths=[7*inch])
        stats_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), success_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(stats_header_table)
        
        # Calculate comprehensive statistics
        total_assessments = len([p for p in learning_plans if p.get('assessment_data')])
        avg_score = 0
        level_distribution = {}
        goal_frequency = {}
        
        if total_assessments > 0:
            scores = [p['assessment_data']['overall_score'] for p in learning_plans if p.get('assessment_data', {}).get('overall_score')]
            avg_score = sum(scores) / len(scores) if scores else 0
        
        for plan in learning_plans:
            level = plan.get('proficiency_level', 'Unknown')
            level_distribution[level] = level_distribution.get(level, 0) + 1
            
            for goal in plan.get('goals', []):
                goal_frequency[goal] = goal_frequency.get(goal, 0) + 1
        
        # Safe handling for empty data
        most_common_level = 'N/A'
        most_common_level_count = 0
        if level_distribution:
            most_common_level, most_common_level_count = max(level_distribution.items(), key=lambda x: x[1])
        
        top_goal = 'N/A'
        top_goal_count = 0
        if goal_frequency:
            top_goal, top_goal_count = max(goal_frequency.items(), key=lambda x: x[1])
        
        level_dist_text = 'No data available'
        if level_distribution:
            level_dist_text = ', '.join([f'{k}: {v}' for k, v in sorted(level_distribution.items())])
        
        stats_data = [
            ['Metric', 'Value', 'Details'],
            ['Total Learning Plans', str(len(learning_plans)), f'{total_assessments} with assessments'],
            ['Average Assessment Score', f'{avg_score:.1f}/100' if avg_score > 0 else 'N/A', 'Across all assessments'],
            ['Most Common Level', most_common_level, f'{most_common_level_count} plans'],
            ['Top Learning Goal', top_goal, f'{top_goal_count} times selected'],
            ['Level Distribution', f'{len(level_distribution)} different levels', level_dist_text]
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, 1.5*inch, 3.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), success_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 25))
        
        # Detailed Learning Plans Table
        plans_header = [['📚 Detailed Learning Plans']]
        plans_header_table = Table(plans_header, colWidths=[7*inch])
        plans_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), primary_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(plans_header_table)
        
        if learning_plans:
            # Create comprehensive plans table
            plans_table_data = [['#', 'Language', 'Level', 'Score', 'Goals', 'Duration', 'Created']]
            
            for i, plan in enumerate(learning_plans, 1):
                assessment = plan.get('assessment_data', {})
                score = f"{assessment.get('overall_score', 'N/A')}/100" if assessment.get('overall_score') else 'No Assessment'
                goals = ', '.join(plan.get('goals', [])[:3])  # Limit to first 3 goals
                if len(plan.get('goals', [])) > 3:
                    goals += f' (+{len(plan.get("goals", [])) - 3} more)'
                
                duration = f"{plan.get('duration_months', 'N/A')} months" if plan.get('duration_months') else 'N/A'
                
                created = 'N/A'
                if plan.get('created_at'):
                    try:
                        created = datetime.fromisoformat(plan['created_at'].replace('Z', '+00:00')).strftime('%m/%d/%Y')
                    except:
                        created = 'N/A'
                
                plans_table_data.append([
                    str(i),
                    plan.get('language', 'Unknown').title(),
                    plan.get('proficiency_level', 'Unknown'),
                    score,
                    goals or 'No goals specified',
                    duration,
                    created
                ])
            
            plans_table = Table(plans_table_data, colWidths=[0.4*inch, 0.8*inch, 0.6*inch, 0.8*inch, 2.2*inch, 0.8*inch, 0.8*inch])
            # Create table style with dynamic alternate row colors
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (4, 0), (4, -1), 'LEFT'),  # Goals column left-aligned
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ]
            
            # Add alternate row colors only for existing rows
            for row_idx in range(2, len(plans_table_data), 2):  # Start from row 2, every other row
                table_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), light_bg))
            
            plans_table.setStyle(TableStyle(table_style))
            story.append(plans_table)
        else:
            # No learning plans message
            no_plans_data = [['📭 No Learning Plans Available']]
            no_plans_table = Table(no_plans_data, colWidths=[7*inch])
            no_plans_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3F4F6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), text_color),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 20),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ]))
            story.append(no_plans_table)
        
        story.append(Spacer(1, 25))
        
        # Assessment Details Table (for plans with assessments)
        assessed_plans = [p for p in learning_plans if p.get('assessment_data')]
        if assessed_plans:
            assessment_header = [['🎯 Assessment Skill Breakdown']]
            assessment_header_table = Table(assessment_header, colWidths=[7*inch])
            assessment_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), accent_color),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 14),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(assessment_header_table)
            
            assessment_data = [['Plan', 'Overall', 'Pronunciation', 'Grammar', 'Vocabulary', 'Fluency', 'Coherence']]
            
            for i, plan in enumerate(assessed_plans, 1):
                assessment = plan['assessment_data']
                row = [
                    f"Plan {learning_plans.index(plan) + 1}",
                    f"{assessment.get('overall_score', 'N/A')}/100",
                    f"{assessment.get('pronunciation', {}).get('score', 'N/A')}/100",
                    f"{assessment.get('grammar', {}).get('score', 'N/A')}/100",
                    f"{assessment.get('vocabulary', {}).get('score', 'N/A')}/100",
                    f"{assessment.get('fluency', {}).get('score', 'N/A')}/100",
                    f"{assessment.get('coherence', {}).get('score', 'N/A')}/100"
                ]
                assessment_data.append(row)
            
            assessment_table = Table(assessment_data, colWidths=[1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
            assessment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), accent_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ]))
            story.append(assessment_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_data = [['Generated by My Taco AI | hello@mytacoai.com | www.mytacoai.com']]
        footer_table = Table(footer_data, colWidths=[7*inch])
        footer_table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#6B7280')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(footer_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_conversations_pdf(user_data: Dict[str, Any]) -> BytesIO:
        """Generate modern, professional PDF report focused on conversation history and analysis"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        
        # App-inspired color scheme
        primary_color = colors.HexColor('#4ECFBF')  # Teal (app primary)
        secondary_color = colors.HexColor('#2563EB')  # Blue
        success_color = colors.HexColor('#10B981')  # Green
        text_color = colors.HexColor('#1F2937')  # Dark gray
        
        # Build document content
        story = []
        user_profile = user_data['user_profile']
        conversations = user_data['conversations']
        stats = user_data['statistics']
        
        # Header
        header_data = [['💬 Conversation History & Analysis Report']]
        header_table = Table(header_data, colWidths=[7*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), primary_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 20),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # Student Profile Section
        profile_header = [['👤 Student Profile']]
        profile_header_table = Table(profile_header, colWidths=[7*inch])
        profile_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), secondary_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(profile_header_table)
        
        profile_data = [
            ['Student Name', user_profile['name']],
            ['Email Address', user_profile['email']],
            ['Report Generated', datetime.fromisoformat(user_data['export_date']).strftime('%B %d, %Y at %I:%M %p UTC')],
            ['Total Practice Sessions', str(stats['total_sessions'])]
        ]
        
        profile_table = Table(profile_data, colWidths=[2.5*inch, 4.5*inch])
        profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (0, -1), secondary_color),
            ('TEXTCOLOR', (1, 0), (1, -1), text_color),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
        ]))
        story.append(profile_table)
        story.append(Spacer(1, 25))
        
        # Statistics Overview Table
        stats_header = [['📊 Practice Statistics Overview']]
        stats_header_table = Table(stats_header, colWidths=[7*inch])
        stats_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), secondary_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(stats_header_table)
        
        stats_data = [
            ['Total Practice Sessions', str(stats['total_sessions'])],
            ['Total Practice Time', f"{stats['total_minutes']} minutes"],
            ['Total Messages Exchanged', str(stats['total_messages'])],
            ['Enhanced Analyses Available', str(stats['enhanced_analyses'])]
        ]
        
        stats_table = Table(stats_data, colWidths=[3.5*inch, 3.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (0, -1), secondary_color),
            ('TEXTCOLOR', (1, 0), (1, -1), text_color),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 25))
        
        # Conversation Sessions Table
        if conversations:
            sessions_header = [['🗣️ Conversation Sessions Overview']]
            sessions_header_table = Table(sessions_header, colWidths=[7*inch])
            sessions_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), success_color),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 14),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(sessions_header_table)
            
            # Sessions table
            sessions_data = [['#', 'Date', 'Language', 'Level', 'Topic', 'Duration', 'Messages', 'Analysis']]
            
            for i, conversation in enumerate(conversations, 1):
                created_at = 'N/A'
                if conversation.get('created_at'):
                    try:
                        created_at = datetime.fromisoformat(conversation['created_at'].replace('Z', '+00:00')).strftime('%m/%d/%Y')
                    except:
                        created_at = 'N/A'
                
                # Use text instead of emoji for better PDF compatibility
                has_analysis = 'Yes' if conversation.get('enhanced_analysis') else 'No'
                
                # Wrap topic text properly
                topic = conversation.get('topic', 'General')
                if len(topic) > 12:
                    topic = topic[:12] + '...'
                
                sessions_data.append([
                    str(i),
                    created_at,
                    conversation.get('language', 'Unknown').title(),
                    conversation.get('level', 'N/A'),
                    topic,
                    f"{conversation.get('duration_minutes', 0):.1f}m",
                    str(conversation.get('message_count', 0)),
                    has_analysis
                ])
            
            sessions_table = Table(sessions_data, colWidths=[0.4*inch, 0.8*inch, 0.8*inch, 0.6*inch, 1.2*inch, 0.6*inch, 0.6*inch, 0.6*inch])
            sessions_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), success_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
                ('WORDWRAP', (0, 0), (-1, -1), True),  # Enable word wrapping
            ]))
            story.append(sessions_table)
            story.append(Spacer(1, 25))
            
            # Detailed Analysis Section for sessions with enhanced analysis
            enhanced_conversations = [c for c in conversations if c.get('enhanced_analysis')]
            if enhanced_conversations:
                analysis_header = [['🧠 Detailed AI Analysis']]
                analysis_header_table = Table(analysis_header, colWidths=[7*inch])
                analysis_header_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#8B5CF6')),  # Purple
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 14),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(analysis_header_table)
                
                for i, conversation in enumerate(enhanced_conversations, 1):
                    session_num = conversations.index(conversation) + 1
                    analysis = conversation['enhanced_analysis']
                    
                    # Session header
                    session_title = f"Session {session_num} Analysis - {conversation.get('language', 'Unknown')} ({conversation.get('level', 'N/A')})"
                    session_header_data = [[session_title]]
                    session_header_table = Table(session_header_data, colWidths=[7*inch])
                    session_header_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3F4F6')),
                        ('TEXTCOLOR', (0, 0), (-1, -1), text_color),
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 12),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 15),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ]))
                    story.append(session_header_table)
                    
                    # Conversation Quality Metrics
                    if 'conversation_quality' in analysis:
                        quality = analysis['conversation_quality']
                        quality_data = [['Quality Metric', 'Score', 'Assessment']]
                        
                        if 'engagement' in quality:
                            engagement_score = quality['engagement'].get('score', 0)
                            engagement_assessment = "Excellent" if engagement_score >= 80 else "Good" if engagement_score >= 60 else "Needs Improvement"
                            quality_data.append(['Engagement', f"{engagement_score}/100", engagement_assessment])
                        
                        if 'topic_depth' in quality:
                            depth_score = quality['topic_depth'].get('score', 0)
                            depth_assessment = "Excellent" if depth_score >= 80 else "Good" if depth_score >= 60 else "Needs Improvement"
                            quality_data.append(['Topic Depth', f"{depth_score}/100", depth_assessment])
                        
                        if 'language_complexity' in quality:
                            complexity_score = quality['language_complexity'].get('score', 0)
                            complexity_assessment = "Excellent" if complexity_score >= 80 else "Good" if complexity_score >= 60 else "Needs Improvement"
                            quality_data.append(['Language Complexity', f"{complexity_score}/100", complexity_assessment])
                        
                        quality_table = Table(quality_data, colWidths=[2.5*inch, 1.5*inch, 3*inch])
                        quality_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5CF6')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 9),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                            ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 8),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                            ('TOPPADDING', (0, 0), (-1, -1), 6),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
                        ]))
                        story.append(quality_table)
                        story.append(Spacer(1, 10))
                    
                    # AI Insights
                    if 'ai_insights' in analysis:
                        ai_insights = analysis['ai_insights']
                        insights_data = []
                        
                        if ai_insights.get('confidence_level'):
                            insights_data.append(['Confidence Level', f"{ai_insights['confidence_level']}/100"])
                        
                        if ai_insights.get('breakthrough_moments'):
                            breakthrough_text = '; '.join(ai_insights['breakthrough_moments'][:2])  # Limit to first 2
                            if len(ai_insights['breakthrough_moments']) > 2:
                                breakthrough_text += f" (+{len(ai_insights['breakthrough_moments']) - 2} more)"
                            # Wrap long text in Paragraph for proper text wrapping
                            breakthrough_para = Paragraph(breakthrough_text, ParagraphStyle(
                                'Normal', fontName='Helvetica', fontSize=8, leading=10, wordWrap='LTR'
                            ))
                            insights_data.append(['Breakthrough Moments', breakthrough_para])
                        
                        if ai_insights.get('struggle_points'):
                            struggle_text = '; '.join(ai_insights['struggle_points'][:2])  # Limit to first 2
                            if len(ai_insights['struggle_points']) > 2:
                                struggle_text += f" (+{len(ai_insights['struggle_points']) - 2} more)"
                            # Wrap long text in Paragraph for proper text wrapping
                            struggle_para = Paragraph(struggle_text, ParagraphStyle(
                                'Normal', fontName='Helvetica', fontSize=8, leading=10, wordWrap='LTR'
                            ))
                            insights_data.append(['Areas of Struggle', struggle_para])
                        
                        if ai_insights.get('vocabulary_highlights'):
                            vocab_text = '; '.join(ai_insights['vocabulary_highlights'][:3])  # Limit to first 3
                            if len(ai_insights['vocabulary_highlights']) > 3:
                                vocab_text += f" (+{len(ai_insights['vocabulary_highlights']) - 3} more)"
                            # Wrap long text in Paragraph for proper text wrapping
                            vocab_para = Paragraph(vocab_text, ParagraphStyle(
                                'Normal', fontName='Helvetica', fontSize=8, leading=10, wordWrap='LTR'
                            ))
                            insights_data.append(['Vocabulary Highlights', vocab_para])
                        
                        if insights_data:
                            insights_table = Table(insights_data, colWidths=[2*inch, 5*inch])
                            insights_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF3C7')),
                                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#92400E')),
                                ('TEXTCOLOR', (1, 0), (1, -1), text_color),
                                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                                ('FONTSIZE', (0, 0), (-1, -1), 8),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                                ('TOPPADDING', (0, 0), (-1, -1), 6),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
                            ]))
                            story.append(insights_table)
                            story.append(Spacer(1, 10))
                    
                    # Recommendations
                    if 'recommendations' in analysis:
                        recommendations = analysis['recommendations']
                        if recommendations.get('next_session_focus'):
                            rec_data = [['Next Session Recommendations']]
                            for rec in recommendations['next_session_focus'][:3]:  # Limit to first 3
                                rec_data.append([f"• {rec}"])
                            
                            rec_table = Table(rec_data, colWidths=[7*inch])
                            rec_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 9),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F0FDF4')),
                                ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
                                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                                ('FONTSIZE', (0, 1), (-1, -1), 8),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                                ('TOPPADDING', (0, 0), (-1, -1), 6),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
                            ]))
                            story.append(rec_table)
                    
                    # Add separator between sessions
                    if i < len(enhanced_conversations):
                        story.append(Spacer(1, 15))
        else:
            # No conversations message
            no_conv_data = [['📭 No Conversation History Available']]
            no_conv_table = Table(no_conv_data, colWidths=[7*inch])
            no_conv_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3F4F6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), text_color),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 20),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ]))
            story.append(no_conv_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_data = [['Generated by My Taco AI | hello@mytacoai.com | www.mytacoai.com']]
        footer_table = Table(footer_data, colWidths=[7*inch])
        footer_table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#6B7280')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(footer_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_csv_data(user_data: Dict[str, Any]) -> Dict[str, BytesIO]:
        """Generate CSV files for different data types"""
        csv_files = {}
        
        # Learning Plans CSV
        if user_data['learning_plans']:
            learning_plans_buffer = BytesIO()
            learning_plans_buffer.write('\ufeff'.encode('utf-8'))  # BOM for Excel compatibility
            
            fieldnames = ['plan_id', 'language', 'proficiency_level', 'goals', 'duration_months', 
                         'created_at', 'overall_score', 'pronunciation_score', 'grammar_score', 
                         'vocabulary_score', 'fluency_score', 'coherence_score']
            
            # Create a text wrapper for the BytesIO buffer
            text_buffer = io.TextIOWrapper(learning_plans_buffer, encoding='utf-8', newline='')
            writer = csv.DictWriter(text_buffer, fieldnames=fieldnames, 
                                  extrasaction='ignore', lineterminator='\n')
            writer.writeheader()
            
            for plan in user_data['learning_plans']:
                assessment = plan.get('assessment_data', {})
                row = {
                    'plan_id': str(plan.get('_id', '')),
                    'language': plan.get('language', ''),
                    'proficiency_level': plan.get('proficiency_level', ''),
                    'goals': ', '.join(plan.get('goals', [])) if plan.get('goals') else '',
                    'duration_months': str(plan.get('duration_months', '')) if plan.get('duration_months') else '',
                    'created_at': plan.get('created_at', ''),
                    'overall_score': str(assessment.get('overall_score', '')) if assessment.get('overall_score') else '',
                    'pronunciation_score': str(assessment.get('pronunciation', {}).get('score', '')) if assessment.get('pronunciation', {}).get('score') else '',
                    'grammar_score': str(assessment.get('grammar', {}).get('score', '')) if assessment.get('grammar', {}).get('score') else '',
                    'vocabulary_score': str(assessment.get('vocabulary', {}).get('score', '')) if assessment.get('vocabulary', {}).get('score') else '',
                    'fluency_score': str(assessment.get('fluency', {}).get('score', '')) if assessment.get('fluency', {}).get('score') else '',
                    'coherence_score': str(assessment.get('coherence', {}).get('score', '')) if assessment.get('coherence', {}).get('score') else ''
                }
                writer.writerow(row)
            
            text_buffer.flush()
            text_buffer.detach()
            learning_plans_buffer.seek(0)
            csv_files['learning_plans.csv'] = learning_plans_buffer
        
        # Conversation History CSV
        if user_data['conversations']:
            conversations_buffer = BytesIO()
            conversations_buffer.write('\ufeff'.encode('utf-8'))  # BOM for Excel compatibility
            
            fieldnames = ['session_id', 'language', 'level', 'topic', 'created_at', 
                         'duration_minutes', 'message_count', 'has_enhanced_analysis', 'summary']
            
            # Create a text wrapper for the BytesIO buffer
            text_buffer = io.TextIOWrapper(conversations_buffer, encoding='utf-8', newline='')
            writer = csv.DictWriter(text_buffer, fieldnames=fieldnames, 
                                  extrasaction='ignore', lineterminator='\n')
            writer.writeheader()
            
            for conversation in user_data['conversations']:
                row = {
                    'session_id': str(conversation.get('_id', '')),
                    'language': conversation.get('language', ''),
                    'level': conversation.get('level', ''),
                    'topic': conversation.get('topic', ''),
                    'created_at': conversation.get('created_at', ''),
                    'duration_minutes': str(conversation.get('duration_minutes', '')) if conversation.get('duration_minutes') else '',
                    'message_count': str(conversation.get('message_count', '')) if conversation.get('message_count') else '',
                    'has_enhanced_analysis': 'Yes' if conversation.get('enhanced_analysis') else 'No',
                    'summary': conversation.get('summary', '').replace('\n', ' ').replace('\r', ' ') if conversation.get('summary') else ''
                }
                writer.writerow(row)
            
            text_buffer.flush()
            text_buffer.detach()
            conversations_buffer.seek(0)
            csv_files['conversation_history.csv'] = conversations_buffer
        
        return csv_files

@router.get("/learning-plans")
async def export_learning_plans(
    format: str = "json",
    current_user: UserResponse = Depends(get_current_user)
):
    """Export learning plans and assessments"""
    try:
        user_data = await ExportService.get_user_data(current_user.id)
        
        if format == "json":
            # Return JSON data focused on learning plans
            export_data = {
                'user_profile': user_data['user_profile'],
                'learning_plans': user_data['learning_plans'],
                'statistics': user_data['statistics'],
                'export_date': user_data['export_date']
            }
            
            return StreamingResponse(
                io.BytesIO(json.dumps(export_data, indent=2, default=str).encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=learning_plans_{current_user.name.replace(' ', '_')}.json"
                }
            )
        
        elif format == "pdf":
            # Generate PDF report focused on learning plans
            pdf_buffer = ExportService.generate_learning_plans_pdf(user_data)
            
            return StreamingResponse(
                io.BytesIO(pdf_buffer.read()),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=learning_plans_{current_user.name.replace(' ', '_')}.pdf"
                }
            )
        
        elif format == "csv":
            csv_files = ExportService.generate_csv_data(user_data)
            if 'learning_plans.csv' in csv_files:
                return StreamingResponse(
                    csv_files['learning_plans.csv'],
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f"attachment; filename=learning_plans_{current_user.name.replace(' ', '_')}.csv"
                    }
                )
            else:
                raise HTTPException(status_code=404, detail="No learning plans data available")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use: json, pdf, or csv")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/conversations")
async def export_conversations(
    format: str = "json",
    current_user: UserResponse = Depends(get_current_user)
):
    """Export conversation history and analysis"""
    try:
        user_data = await ExportService.get_user_data(current_user.id)
        
        if format == "json":
            # Return JSON data focused on conversations
            export_data = {
                'user_profile': user_data['user_profile'],
                'conversations': user_data['conversations'],
                'statistics': user_data['statistics'],
                'export_date': user_data['export_date']
            }
            
            return StreamingResponse(
                io.BytesIO(json.dumps(export_data, indent=2, default=str).encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=conversation_history_{current_user.name.replace(' ', '_')}.json"
                }
            )
        
        elif format == "pdf":
            # Generate PDF report focused on conversations
            pdf_buffer = ExportService.generate_conversations_pdf(user_data)
            
            return StreamingResponse(
                io.BytesIO(pdf_buffer.read()),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=conversation_history_{current_user.name.replace(' ', '_')}.pdf"
                }
            )
        
        elif format == "csv":
            csv_files = ExportService.generate_csv_data(user_data)
            if 'conversation_history.csv' in csv_files:
                return StreamingResponse(
                    csv_files['conversation_history.csv'],
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f"attachment; filename=conversation_history_{current_user.name.replace(' ', '_')}.csv"
                    }
                )
            else:
                raise HTTPException(status_code=404, detail="No conversation data available")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use: json, pdf, or csv")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/data")
async def export_all_data(
    format: str = "json",
    current_user: UserResponse = Depends(get_current_user)
):
    """Export all user data"""
    try:
        user_data = await ExportService.get_user_data(current_user.id)
        
        if format == "json":
            return StreamingResponse(
                io.BytesIO(json.dumps(user_data, indent=2, default=str).encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=complete_data_{current_user.name.replace(' ', '_')}.json"
                }
            )
        
        elif format == "zip":
            # Create ZIP file with all formats
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add JSON
                zip_file.writestr(
                    f"complete_data_{current_user.name.replace(' ', '_')}.json",
                    json.dumps(user_data, indent=2, default=str)
                )
                
                # Add PDFs
                learning_plans_pdf = ExportService.generate_learning_plans_pdf(user_data)
                zip_file.writestr(
                    f"learning_plans_{current_user.name.replace(' ', '_')}.pdf",
                    learning_plans_pdf.read()
                )
                
                conversations_pdf = ExportService.generate_conversations_pdf(user_data)
                zip_file.writestr(
                    f"conversation_history_{current_user.name.replace(' ', '_')}.pdf",
                    conversations_pdf.read()
                )
                
                # Add CSVs
                csv_files = ExportService.generate_csv_data(user_data)
                for filename, buffer in csv_files.items():
                    zip_file.writestr(
                        f"{current_user.name.replace(' ', '_')}_{filename}",
                        buffer.read()
                    )
            
            zip_buffer.seek(0)
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename=complete_learning_data_{current_user.name.replace(' ', '_')}.zip"
                }
            )
        
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use: json or zip")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
