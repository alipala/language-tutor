#!/usr/bin/env python3
"""
Health check fix for Railway deployment
This script creates a simple health endpoint that doesn't depend on database connectivity
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import os
import time
import asyncio

async def simple_health_check():
    """
    Simple health check that doesn't require database connectivity
    """
    try:
        current_time = time.time()
        
        # Basic health status
        health_status = {
            "status": "ok",
            "timestamp": current_time,
            "environment": os.getenv("ENVIRONMENT", "production"),
            "railway": os.getenv("RAILWAY_ENVIRONMENT") is not None or os.getenv("RAILWAY") == "true",
            "port": os.getenv("PORT", "3001"),
            "python_version": "3.11",
            "service": "language-tutor-backend"
        }
        
        # Check if OpenAI API key is configured
        health_status["openai_configured"] = os.getenv("OPENAI_API_KEY") is not None
        
        # Check if MongoDB URL is configured (don't test connection for speed)
        mongodb_configured = False
        for var_name in ["MONGODB_URL", "MONGO_URL", "MONGO_PUBLIC_URL"]:
            if os.getenv(var_name):
                mongodb_configured = True
                break
        
        health_status["mongodb_configured"] = mongodb_configured
        
        return health_status
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

if __name__ == "__main__":
    # Test the health check
    import asyncio
    result = asyncio.run(simple_health_check())
    print("Health check result:", result)
