from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Dict, Any, Optional
import os
import json
import zipfile
import tempfile
from datetime import datetime
from io import BytesIO
import asyncio

from auth import get_current_user
from models import UserResponse
from ai_report_generator import AIReportGenerator
from modern_pdf_generator import ProfessionalPDFGenerator

# Initialize router
router = APIRouter(prefix="/export", tags=["enhanced_export"])

@router.get("/comprehensive-report/current")
async def export_current_user_report(
    format: str = "pdf",  # pdf, json, zip
    report_type: str = "comprehensive",  # comprehensive, learning_plans, conversations
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Export AI-enhanced learning report for current authenticated user
    
    Report Types:
    - comprehensive: Complete analysis with all sections
    - learning_plans: Focus on assessments, progress, and learning plans
    - conversations: Focus on conversation analysis and speaking practice
    
    Formats:
    - pdf: Professional PDF report with AI insights
    - json: Raw data in JSON format for developers
    - zip: Complete package with PDF + JSON + assets
    """
    
    actual_user_id = str(current_user.id)
    
    try:
        print(f"[ENHANCED_EXPORT] 🚀 Starting {report_type} report generation for user {actual_user_id}")
        
        # Generate comprehensive user data with AI insights
        user_data = await AIReportGenerator.generate_comprehensive_user_data(actual_user_id)
        
        user_name = user_data.get('user_profile', {}).get('name', 'Student')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        if format.lower() == "json":
            # Return raw JSON data
            json_content = json.dumps(user_data, indent=2, default=str)
            
            # Update filename based on report type
            filename_prefix = {
                "learning_plans": "Learning_Plan",
                "conversations": "Conversation_History", 
                "comprehensive": "Comprehensive_Report"
            }.get(report_type, "Comprehensive_Report")
            
            return StreamingResponse(
                BytesIO(json_content.encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_prefix}_{timestamp}_{user_name}.json"
                }
            )
        
        elif format.lower() == "pdf":
            # Generate professional PDF report with specified type
            pdf_buffer = ProfessionalPDFGenerator.generate_comprehensive_report(user_data, report_type)
            
            # Update filename based on report type
            filename_prefix = {
                "learning_plans": "Learning_Plan",
                "conversations": "Conversation_History", 
                "comprehensive": "Comprehensive_Report"
            }.get(report_type, "Comprehensive_Report")
            
            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_prefix}_{timestamp}_{user_name}.pdf"
                }
            )
        
        elif format.lower() == "zip":
            # Generate complete package
            return await _generate_complete_package(user_data, user_name, timestamp)
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Supported formats: pdf, json, zip"
            )
    
    except Exception as e:
        print(f"[ENHANCED_EXPORT] ❌ Error generating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate {report_type} report: {str(e)}"
        )

@router.get("/comprehensive-report/{user_id}")
async def export_comprehensive_report(
    user_id: str,
    format: str = "pdf",  # pdf, json, zip
    report_type: str = "comprehensive",  # comprehensive, learning_plans, conversations
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Export AI-enhanced learning report
    
    Report Types:
    - comprehensive: Complete analysis with all sections
    - learning_plans: Focus on assessments, progress, and learning plans
    - conversations: Focus on conversation analysis and speaking practice
    
    Formats:
    - pdf: Professional PDF report with AI insights
    - json: Raw data in JSON format for developers
    - zip: Complete package with PDF + JSON + assets
    """
    
    # Use authenticated user's ID (ignore the path parameter for security)
    actual_user_id = str(current_user.id)
    
    try:
        print(f"[ENHANCED_EXPORT] 🚀 Starting comprehensive report generation for user {actual_user_id}")
        
        # Generate comprehensive user data with AI insights
        user_data = await AIReportGenerator.generate_comprehensive_user_data(actual_user_id)
        
        user_name = user_data.get('user_profile', {}).get('name', 'Student')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        if format.lower() == "json":
            # Return raw JSON data
            json_content = json.dumps(user_data, indent=2, default=str)
            
            return StreamingResponse(
                BytesIO(json_content.encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=comprehensive_report_{user_name}_{timestamp}.json"
                }
            )
        
        elif format.lower() == "pdf":
            # Generate professional PDF report with specified type
            pdf_buffer = ProfessionalPDFGenerator.generate_comprehensive_report(user_data, report_type)
            
            # Update filename based on report type
            filename_prefix = {
                "learning_plans": "Learning_Plan",
                "conversations": "Conversation_History", 
                "comprehensive": "Comprehensive_Report"
            }.get(report_type, "Comprehensive_Report")
            
            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_prefix}_{timestamp}_{user_name}.pdf"
                }
            )
        
        elif format.lower() == "zip":
            # Generate complete package
            return await _generate_complete_package(user_data, user_name, timestamp)
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Supported formats: pdf, json, zip"
            )
    
    except Exception as e:
        print(f"[ENHANCED_EXPORT] ❌ Error generating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate comprehensive report: {str(e)}"
        )

@router.get("/learning-analytics/{user_id}")
async def export_learning_analytics(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Export detailed learning analytics in JSON format
    """
    
    # Use authenticated user's ID
    actual_user_id = str(current_user.id)
    
    try:
        print(f"[ENHANCED_EXPORT] 📊 Generating learning analytics for user {actual_user_id}")
        
        # Generate comprehensive analytics
        user_data = await AIReportGenerator.generate_comprehensive_user_data(actual_user_id)
        
        # Extract just the analytics portion
        analytics_data = {
            'user_id': user_id,
            'export_date': user_data.get('export_date'),
            'analytics': user_data.get('analytics', {}),
            'ai_insights': user_data.get('ai_insights', {}),
            'summary': {
                'total_conversations': len(user_data.get('conversations', [])),
                'total_learning_plans': len(user_data.get('learning_plans', [])),
                'data_completeness': _calculate_data_completeness(user_data)
            }
        }
        
        user_name = user_data.get('user_profile', {}).get('name', 'Student')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        json_content = json.dumps(analytics_data, indent=2, default=str)
        
        return StreamingResponse(
            BytesIO(json_content.encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=learning_analytics_{user_name}_{timestamp}.json"
            }
        )
    
    except Exception as e:
        print(f"[ENHANCED_EXPORT] ❌ Error generating analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning analytics: {str(e)}"
        )

@router.get("/conversation-insights/{user_id}")
async def export_conversation_insights(
    user_id: str,
    enhanced_only: bool = False,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Export conversation insights with AI analysis
    """
    
    # Use authenticated user's ID
    actual_user_id = str(current_user.id)
    
    try:
        print(f"[ENHANCED_EXPORT] 💬 Generating conversation insights for user {actual_user_id}")
        
        # Generate comprehensive data
        user_data = await AIReportGenerator.generate_comprehensive_user_data(actual_user_id)
        conversations = user_data.get('conversations', [])
        
        # Filter for enhanced analysis if requested
        if enhanced_only:
            conversations = [c for c in conversations if c.get('enhanced_analysis')]
        
        # Create insights report
        insights_data = {
            'user_id': user_id,
            'export_date': user_data.get('export_date'),
            'conversation_summary': {
                'total_conversations': len(user_data.get('conversations', [])),
                'enhanced_conversations': len([c for c in user_data.get('conversations', []) if c.get('enhanced_analysis')]),
                'filtered_conversations': len(conversations),
                'enhanced_only_filter': enhanced_only
            },
            'conversations': conversations,
            'analytics': user_data.get('analytics', {}).get('engagement', {}),
            'ai_insights': user_data.get('ai_insights', {})
        }
        
        user_name = user_data.get('user_profile', {}).get('name', 'Student')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filter_suffix = "_enhanced" if enhanced_only else "_all"
        
        json_content = json.dumps(insights_data, indent=2, default=str)
        
        return StreamingResponse(
            BytesIO(json_content.encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=conversation_insights_{user_name}{filter_suffix}_{timestamp}.json"
            }
        )
    
    except Exception as e:
        print(f"[ENHANCED_EXPORT] ❌ Error generating conversation insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate conversation insights: {str(e)}"
        )

@router.get("/learning-plans-detailed/{user_id}")
async def export_learning_plans_detailed(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Export detailed learning plans with progress analysis
    """
    
    # Use authenticated user's ID
    actual_user_id = str(current_user.id)
    
    try:
        print(f"[ENHANCED_EXPORT] 📚 Generating detailed learning plans for user {actual_user_id}")
        
        # Generate comprehensive data
        user_data = await AIReportGenerator.generate_comprehensive_user_data(actual_user_id)
        
        # Create detailed learning plans report
        plans_data = {
            'user_id': user_id,
            'export_date': user_data.get('export_date'),
            'learning_plans': user_data.get('learning_plans', []),
            'progress_analytics': user_data.get('analytics', {}).get('progress', {}),
            'goal_analytics': user_data.get('analytics', {}).get('goals', {}),
            'ai_recommendations': user_data.get('ai_insights', {}).get('personalized_recommendations', {}),
            'summary': {
                'total_plans': len(user_data.get('learning_plans', [])),
                'languages_covered': len(set(
                    plan.get('language', 'Unknown') 
                    for plan in user_data.get('learning_plans', [])
                )),
                'overall_progress': user_data.get('analytics', {}).get('progress', {}).get('overall_progress_percentage', 0)
            }
        }
        
        user_name = user_data.get('user_profile', {}).get('name', 'Student')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        json_content = json.dumps(plans_data, indent=2, default=str)
        
        return StreamingResponse(
            BytesIO(json_content.encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=learning_plans_detailed_{user_name}_{timestamp}.json"
            }
        )
    
    except Exception as e:
        print(f"[ENHANCED_EXPORT] ❌ Error generating learning plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate detailed learning plans: {str(e)}"
        )

@router.post("/generate-custom-report/{user_id}")
async def generate_custom_report(
    user_id: str,
    report_config: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate custom report based on user specifications
    
    report_config example:
    {
        "sections": ["executive_summary", "skill_analysis", "recommendations"],
        "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
        "languages": ["english", "spanish"],
        "format": "pdf",
        "include_raw_data": false
    }
    """
    
    if str(current_user.id) != user_id and not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only generate reports for your own data"
        )
    
    try:
        print(f"[ENHANCED_EXPORT] 🎨 Generating custom report for user {user_id}")
        print(f"[ENHANCED_EXPORT] Config: {report_config}")
        
        # Generate comprehensive data
        user_data = await AIReportGenerator.generate_comprehensive_user_data(user_id)
        
        # Apply filters based on config
        filtered_data = await _apply_report_filters(user_data, report_config)
        
        # Generate report based on format
        format_type = report_config.get('format', 'pdf').lower()
        user_name = user_data.get('user_profile', {}).get('name', 'Student')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        if format_type == 'pdf':
            # Generate custom PDF (simplified version for now)
            pdf_buffer = ProfessionalPDFGenerator.generate_comprehensive_report(filtered_data)
            
            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=custom_report_{user_name}_{timestamp}.pdf"
                }
            )
        
        else:  # JSON format
            json_content = json.dumps(filtered_data, indent=2, default=str)
            
            return StreamingResponse(
                BytesIO(json_content.encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=custom_report_{user_name}_{timestamp}.json"
                }
            )
    
    except Exception as e:
        print(f"[ENHANCED_EXPORT] ❌ Error generating custom report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate custom report: {str(e)}"
        )

# Helper functions

async def _generate_complete_package(user_data: Dict[str, Any], user_name: str, timestamp: str) -> StreamingResponse:
    """Generate complete ZIP package with PDF, JSON, and additional assets"""
    
    print(f"[ENHANCED_EXPORT] 📦 Creating complete package for {user_name}")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, f"complete_report_{user_name}_{timestamp}.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            
            # 1. Add comprehensive PDF report
            pdf_buffer = ProfessionalPDFGenerator.generate_comprehensive_report(user_data)
            zipf.writestr(f"comprehensive_report_{user_name}_{timestamp}.pdf", pdf_buffer.getvalue())
            
            # 2. Add raw data JSON
            json_content = json.dumps(user_data, indent=2, default=str)
            zipf.writestr(f"raw_data_{user_name}_{timestamp}.json", json_content)
            
            # 3. Add analytics summary
            analytics_summary = {
                'overview': user_data.get('analytics', {}).get('overview', {}),
                'key_metrics': {
                    'total_conversations': len(user_data.get('conversations', [])),
                    'total_learning_plans': len(user_data.get('learning_plans', [])),
                    'enhanced_sessions': len([
                        c for c in user_data.get('conversations', []) 
                        if c.get('enhanced_analysis')
                    ])
                },
                'ai_insights_summary': user_data.get('ai_insights', {}).get('executive_summary', ''),
                'export_info': {
                    'generated_at': user_data.get('export_date'),
                    'user_name': user_name,
                    'report_version': '2.0'
                }
            }
            
            zipf.writestr(
                f"analytics_summary_{user_name}_{timestamp}.json", 
                json.dumps(analytics_summary, indent=2, default=str)
            )
            
            # 4. Add README file
            readme_content = f"""
# Language Learning Report Package

Generated for: {user_name}
Date: {timestamp}
Report Version: 2.0 (AI-Enhanced)

## Contents:

1. **comprehensive_report_{user_name}_{timestamp}.pdf**
   - Professional PDF report with AI insights
   - Executive summary, analytics, recommendations
   - Suitable for sharing with instructors or employers

2. **raw_data_{user_name}_{timestamp}.json**
   - Complete raw data export
   - All conversations, learning plans, and analytics
   - For developers or detailed analysis

3. **analytics_summary_{user_name}_{timestamp}.json**
   - Key metrics and insights summary
   - Quick overview of learning progress
   - AI-generated executive summary

4. **README.txt** (this file)
   - Package contents and description

## AI-Enhanced Features:

- Comprehensive learning analytics
- Personalized insights and recommendations
- Professional assessment suitable for academic/professional contexts
- Skill development tracking and trends
- Goal achievement analysis

## Support:

For questions about this report, contact:
- Email: hello@mytacoai.com
- Website: www.mytacoai.com

Generated by My Taco AI Learning Platform
"""
            
            zipf.writestr("README.txt", readme_content)
        
        # Read the ZIP file and return as streaming response
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        return StreamingResponse(
            BytesIO(zip_content),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=complete_report_{user_name}_{timestamp}.zip"
            }
        )

def _calculate_data_completeness(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate data completeness metrics"""
    
    conversations = user_data.get('conversations', [])
    learning_plans = user_data.get('learning_plans', [])
    
    enhanced_sessions = len([c for c in conversations if c.get('enhanced_analysis')])
    total_sessions = len(conversations)
    
    plans_with_progress = len([p for p in learning_plans if p.get('progress_percentage', 0) > 0])
    total_plans = len(learning_plans)
    
    return {
        'conversations': {
            'total': total_sessions,
            'with_enhanced_analysis': enhanced_sessions,
            'enhancement_rate': (enhanced_sessions / total_sessions * 100) if total_sessions > 0 else 0
        },
        'learning_plans': {
            'total': total_plans,
            'with_progress': plans_with_progress,
            'progress_tracking_rate': (plans_with_progress / total_plans * 100) if total_plans > 0 else 0
        },
        'overall_completeness': {
            'has_conversations': total_sessions > 0,
            'has_learning_plans': total_plans > 0,
            'has_enhanced_data': enhanced_sessions > 0,
            'data_richness_score': _calculate_richness_score(user_data)
        }
    }

def _calculate_richness_score(user_data: Dict[str, Any]) -> float:
    """Calculate overall data richness score (0-100)"""
    
    score = 0
    max_score = 100
    
    # Base data (20 points)
    if user_data.get('conversations'):
        score += 10
    if user_data.get('learning_plans'):
        score += 10
    
    # Enhanced analysis (30 points)
    enhanced_sessions = len([
        c for c in user_data.get('conversations', []) 
        if c.get('enhanced_analysis')
    ])
    if enhanced_sessions > 0:
        score += min(enhanced_sessions * 3, 30)
    
    # Progress tracking (20 points)
    plans_with_progress = len([
        p for p in user_data.get('learning_plans', []) 
        if p.get('progress_percentage', 0) > 0
    ])
    if plans_with_progress > 0:
        score += min(plans_with_progress * 10, 20)
    
    # AI insights (20 points)
    ai_insights = user_data.get('ai_insights', {})
    if ai_insights.get('executive_summary'):
        score += 5
    if ai_insights.get('key_achievements'):
        score += 5
    if ai_insights.get('personalized_recommendations'):
        score += 5
    if ai_insights.get('learning_insights'):
        score += 5
    
    # Analytics depth (10 points)
    analytics = user_data.get('analytics', {})
    if analytics.get('skills', {}).get('skill_breakdown'):
        score += 5
    if analytics.get('engagement', {}).get('peak_engagement_periods'):
        score += 5
    
    return min(score, max_score)

async def _apply_report_filters(user_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply filters to user data based on report configuration"""
    
    filtered_data = user_data.copy()
    
    # Date range filter
    if config.get('date_range'):
        start_date = config['date_range'].get('start')
        end_date = config['date_range'].get('end')
        
        if start_date or end_date:
            filtered_conversations = []
            for conv in user_data.get('conversations', []):
                conv_date = conv.get('created_at')
                if conv_date:
                    try:
                        conv_datetime = datetime.fromisoformat(conv_date.replace('Z', '+00:00'))
                        
                        if start_date and conv_datetime < datetime.fromisoformat(start_date):
                            continue
                        if end_date and conv_datetime > datetime.fromisoformat(end_date):
                            continue
                        
                        filtered_conversations.append(conv)
                    except:
                        # Include conversations with invalid dates
                        filtered_conversations.append(conv)
            
            filtered_data['conversations'] = filtered_conversations
    
    # Language filter
    if config.get('languages'):
        target_languages = [lang.lower() for lang in config['languages']]
        
        filtered_conversations = [
            conv for conv in filtered_data.get('conversations', [])
            if conv.get('language', '').lower() in target_languages
        ]
        
        filtered_plans = [
            plan for plan in filtered_data.get('learning_plans', [])
            if plan.get('language', '').lower() in target_languages
        ]
        
        filtered_data['conversations'] = filtered_conversations
        filtered_data['learning_plans'] = filtered_plans
    
    # Remove raw data if not requested
    if not config.get('include_raw_data', True):
        # Keep only summary information
        filtered_data = {
            'user_profile': {
                'name': user_data.get('user_profile', {}).get('name', 'Student'),
                'export_date': user_data.get('export_date')
            },
            'analytics': filtered_data.get('analytics', {}),
            'ai_insights': filtered_data.get('ai_insights', {}),
            'summary': {
                'conversations_count': len(filtered_data.get('conversations', [])),
                'learning_plans_count': len(filtered_data.get('learning_plans', []))
            }
        }
    
    return filtered_data
