"""
Low Minutes Alert System
Provides API endpoint and utilities for checking if users have critically low remaining minutes
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime
from database import database
from auth import get_current_user
from models import UserResponse
from subscription_service import SubscriptionService
from logging_config import logger
from bson import ObjectId
from performance_cache import perf_cache

router = APIRouter()

# Threshold for low minutes warning (in minutes)
LOW_MINUTES_THRESHOLD = 10.0

def get_user_query(user_id: str):
    """Helper function to handle both UUID and ObjectId formats"""
    try:
        return {"_id": ObjectId(user_id)}
    except:
        return {"_id": user_id}

async def check_low_minutes_status(user_id: str) -> Dict[str, Any]:
    """
    Check if user has critically low remaining minutes
    Returns detailed status information for UI display
    """
    try:
        # Get subscription status
        status = await SubscriptionService.get_user_subscription_status(user_id)
        
        if not status.limits:
            return {
                "has_low_minutes": False,
                "minutes_remaining": None,
                "is_unlimited": False,
                "message": None
            }
        
        # Check if unlimited plan
        if status.limits.minutes_limit == -1:
            return {
                "has_low_minutes": False,
                "minutes_remaining": -1,
                "is_unlimited": True,
                "message": None
            }
        
        minutes_remaining = status.limits.minutes_remaining or 0
        
        # Check if critically low
        has_low_minutes = 0 < minutes_remaining <= LOW_MINUTES_THRESHOLD
        
        # Generate appropriate message
        message = None
        severity = "info"
        
        if minutes_remaining <= 0:
            message = "⚠️ You've used all your speaking time for this period. Upgrade to continue learning!"
            severity = "critical"
        elif has_low_minutes:
            if minutes_remaining <= 1:
                message = f"⏰ Only {minutes_remaining:.0f} minute remaining! Consider upgrading to avoid interruption."
                severity = "critical"
            elif minutes_remaining <= 3:
                message = f"⏰ Only {minutes_remaining:.0f} minutes remaining! Upgrade soon to keep learning."
                severity = "warning"
            else:
                message = f"⏰ You have {minutes_remaining:.0f} minutes left this {status.period}. Upgrade for unlimited access!"
                severity = "warning"
        
        return {
            "has_low_minutes": has_low_minutes,
            "minutes_remaining": minutes_remaining,
            "minutes_used": status.limits.minutes_used,
            "minutes_limit": status.limits.minutes_limit,
            "is_unlimited": False,
            "message": message,
            "severity": severity,
            "period": status.period,
            "plan": status.plan
        }
        
    except Exception as e:
        logger.error(f"Error checking low minutes status for user {user_id}: {str(e)}")
        return {
            "has_low_minutes": False,
            "minutes_remaining": None,
            "is_unlimited": False,
            "message": None,
            "error": str(e)
        }

@router.get("/api/subscription/low-minutes-check")
async def get_low_minutes_status(current_user: UserResponse = Depends(get_current_user)):
    """
    🚀 OPTIMIZED: API endpoint to check if current user has low remaining minutes with server-side caching
    Returns status and appropriate warning message
    """
    try:
        user_id = str(current_user.id)
        cache_key = f"low_minutes_check:{user_id}"
        
        async def fetch_low_minutes_data():
            """Inner function to fetch low minutes data (cached by perf_cache)"""
            status = await check_low_minutes_status(user_id)
            return {
                "success": True,
                "data": status
            }
        
        # Use server-side cache with 30-second TTL and request deduplication
        response = await perf_cache.fetch_with_cache_and_dedup(
            cache_key,
            fetch_low_minutes_data,
            ttl_seconds=30
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in low minutes check endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/subscription/can-start-session")
async def check_can_start_session(current_user: dict = Depends(get_current_user)):
    """
    Check if user can start a new session based on remaining minutes
    """
    try:
        user_id = str(current_user["_id"])
        can_start, message = await SubscriptionService.can_start_session(user_id)
        
        # Also get low minutes status for additional context
        low_minutes_status = await check_low_minutes_status(user_id)
        
        return {
            "success": True,
            "can_start": can_start,
            "message": message,
            "low_minutes_status": low_minutes_status
        }
        
    except Exception as e:
        logger.error(f"Error checking session start permission: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
