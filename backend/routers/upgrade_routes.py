"""
Upgrade Routes - API endpoints for subscription upgrades
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from auth import get_current_user
from models import UserResponse
from services.upgrade_service import UpgradeService
from logging_config import logger
from pydantic import BaseModel

router = APIRouter(prefix="/api/upgrade", tags=["upgrade"])


class UpgradeProcessRequest(BaseModel):
    """Request model for processing an upgrade"""
    price_id: str
    upgrade_type: str


@router.get("/options")
async def get_upgrade_options(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get personalized upgrade options for the current user
    
    Returns:
        Dictionary with current_plan and upgrade_options
    """
    try:
        logger.info(f"[UPGRADE] Getting upgrade options for user {current_user.id}")
        options = await UpgradeService.get_upgrade_options(current_user.id)
        return options
    except ValueError as e:
        logger.error(f"[UPGRADE] ValueError getting options for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[UPGRADE] Error getting options for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get upgrade options")


@router.post("/process")
async def process_upgrade(
    request: UpgradeProcessRequest,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process a subscription upgrade
    
    Args:
        request: UpgradeProcessRequest with price_id and upgrade_type
        
    Returns:
        Dictionary with success status and details
    """
    try:
        logger.info(f"[UPGRADE] Processing upgrade for user {current_user.id}: {request.upgrade_type}")
        logger.info(f"[UPGRADE] New price ID: {request.price_id}")
        
        result = await UpgradeService.process_upgrade(
            user_id=current_user.id,
            upgrade_type=request.upgrade_type,
            new_price_id=request.price_id
        )
        
        if result.get("success"):
            logger.info(f"[UPGRADE] Successfully upgraded user {current_user.id}")
            return result
        else:
            logger.error(f"[UPGRADE] Failed to upgrade user {current_user.id}: {result.get('error')}")
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Upgrade failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[UPGRADE] Error processing upgrade for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process upgrade")
