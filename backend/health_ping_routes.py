"""
Lightweight health check endpoint for connectivity monitoring
"""

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
import time

router = APIRouter()

@router.head("/api/health/ping")
@router.get("/api/health/ping")
async def health_ping():
    """
    Ultra-lightweight health check endpoint
    Returns minimal response for connectivity verification
    """
    return Response(
        status_code=200,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Health-Check": "ok",
            "X-Timestamp": str(int(time.time()))
        }
    )

@router.get("/api/health/status")
async def health_status():
    """
    Detailed health status for debugging
    """
    return JSONResponse({
        "status": "healthy",
        "timestamp": int(time.time()),
        "service": "language-tutor-backend"
    })
