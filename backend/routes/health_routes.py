"""
Health Check Routes
Simple health check and test endpoints for monitoring
"""

import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/test")
async def test_endpoint():
    """Simple test endpoint to verify API is running"""
    return {"message": "Language Tutor API is running"}

@router.get("/health")
@router.get("/api/health")
async def health_check():
    """
    Minimal health check - only returns status and environment (no logging)
    Supports both /health and /api/health for compatibility
    """
    # Determine environment correctly
    is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY") == "true")
    environment = "production" if is_railway or os.getenv("ENVIRONMENT") == "production" else "development"

    return {
        "status": "ok",
        "environment": environment
    }
