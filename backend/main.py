import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv

# Import production-safe logging
from logging_config import logger

# Import MongoDB and authentication modules
from database import init_db
from auth_routes import router as auth_router

# Load environment variables
load_dotenv()


# Check if OpenAI API key is configured
if not os.getenv("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY is not configured in environment")
    logger.error("Please configure OPENAI_API_KEY in environment variables")

app = FastAPI(title="Language Tutor Backend API")

# 🚀 PERFORMANCE: Enable GZip compression for all responses
# This reduces payload sizes by 60-80% (e.g., 15KB → 3KB)
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses larger than 1KB
    compresslevel=6     # Balance between speed and compression ratio (1-9)
)

# CORS configuration
# For Railway deployment, we need to ensure proper CORS settings
origins = ["*"]  # Start with permissive setting

# Check for Railway-specific environment
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY") == "true":
    print("Running in Railway environment, using permissive CORS settings")
    # Support both domains
    frontend_url = "https://mytacoai.com"  # Primary domain
    
    # In production Railway environment, include both domains
    origins = [
        "https://mytacoai.com",
        "https://taco.up.railway.app",
        "*"  # Keep wildcard for maximum compatibility
    ]
elif os.getenv("ENVIRONMENT") == "production":
    # For other production environments
    frontend_url = os.getenv("FRONTEND_URL", "https://mytacoai.com")
    origins = [
        "https://mytacoai.com",
        "https://taco.up.railway.app",
        frontend_url,
    ]
else:
    # For local development localhost:3000
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]
    frontend_url = "http://localhost:3000"

print(f"Configured CORS with origins: {origins}")

# CORS middleware must be added before any other middleware or route registration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Set to True to allow credentials
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)

# Include learning routes
from learning_routes import router as learning_router
app.include_router(learning_router)

# Include progress routes
from progress_routes import router as progress_router
app.include_router(progress_router)

# Include export routes
from export_routes import router as export_router
# from enhanced_export_routes import router as enhanced_export_router  # Temporarily disabled due to plotly dependency
app.include_router(export_router)
# app.include_router(enhanced_export_router)  # Temporarily disabled due to plotly dependency

# Include chat routes
from chat_routes import router as chat_router
from vector_chatbot import router as vector_chat_router
from contextual_chatbot import router as contextual_chat_router
app.include_router(chat_router)
app.include_router(vector_chat_router)
app.include_router(contextual_chat_router)

# Include admin routes
from admin_routes import router as admin_router
app.include_router(admin_router)

# Include stripe routes
from stripe_routes import router as stripe_router
app.include_router(stripe_router)

# Include upgrade routes
from routers.upgrade_routes import router as upgrade_router
app.include_router(upgrade_router)

# Include notification routes
from notification_routes import router as notification_router
app.include_router(notification_router, prefix="/api")

# Include WebSocket routes for real-time notifications
from websocket_routes import router as websocket_router
app.include_router(websocket_router, prefix="/api")

# Include low minutes alert routes
from low_minutes_alert import router as low_minutes_router
app.include_router(low_minutes_router)

# Include health ping routes
from health_ping_routes import router as health_ping_router
app.include_router(health_ping_router)

# Include share routes
from share_routes import router as share_router
app.include_router(share_router)

# Include URL redirect routes
from url_redirect_routes import router as url_redirect_router
app.include_router(url_redirect_router)

# Include voice sample routes
from voice_sample_routes import router as voice_sample_router
app.include_router(voice_sample_router)

# Include conversation help routes
from conversation_help_routes import router as conversation_help_router
app.include_router(conversation_help_router)

# Include session heartbeat routes
from session_heartbeat_routes import router as session_heartbeat_router
app.include_router(session_heartbeat_router)

# Include consent routes
from app.consent.routes import router as consent_router
app.include_router(consent_router)

# Include institution routes
from app.institution.routes import router as institution_router
from app.institution.dashboard_routes import router as dashboard_router
app.include_router(institution_router)
app.include_router(dashboard_router)

# Include tutor routes
from app.tutor.routes import router as tutor_router
app.include_router(tutor_router)

# Include tutor dashboard routes (NEW: Authentication & Dashboard endpoints)
from app.tutor.tutor_routes import router as tutor_dashboard_router
app.include_router(tutor_dashboard_router)

# Include learner routes
from app.learner.routes import router as learner_router
app.include_router(learner_router)

# Include activation codes routes
from activation_codes_routes import router as activation_codes_router
app.include_router(activation_codes_router)

# Include flashcard routes
from flashcard_routes import router as flashcard_router
app.include_router(flashcard_router)

# Include challenge routes (Explore Tab)
from challenge_routes import router as challenge_router
app.include_router(challenge_router)

# Include achievement routes (Gamification)
from routes.achievement_routes import router as achievement_router
app.include_router(achievement_router)

# Include progress stats routes
from routes.progress_stats_routes import router as progress_stats_router
app.include_router(progress_stats_router)

# Include gamification stats routes (NEW)
from routes.stats_routes import router as stats_router
app.include_router(stats_router)

# Include heart system routes (Focus Energy)
from routes.heart_routes import router as heart_router
app.include_router(heart_router, prefix="/api/hearts")

# Include modular routes (refactored from main.py)
from routes import health_router, mock_router
from routes.image_routes import router as image_router
from routes.realtime_routes import router as realtime_router
from routes.content_routes import router as content_router
from routes.subscription_routes import router as subscription_router
from routes.feedback_routes import router as feedback_router
from routes.session_summary_routes import router as session_summary_router
from routes.assessment_routes import router as assessment_router
from routes.transcription_routes import router as transcription_router
from routes.guest_analysis_routes import router as guest_analysis_router
from routes.final_assessment_routes import router as final_assessment_router

app.include_router(health_router)
app.include_router(mock_router)
app.include_router(image_router)
app.include_router(realtime_router)
app.include_router(content_router)
app.include_router(subscription_router)
app.include_router(feedback_router)
app.include_router(session_summary_router)
app.include_router(assessment_router)
app.include_router(transcription_router)
app.include_router(guest_analysis_router)
app.include_router(final_assessment_router)


# Initialize MongoDB on startup
@app.on_event("startup")
async def startup_db_client():
    try:
        # Check if we're in Railway environment
        if os.getenv("RAILWAY_ENVIRONMENT"):
            print(f"Starting in Railway environment")
            # Print available environment variables for MongoDB (with sensitive info masked)
            mongo_vars = {
                k: ("*****" if "PASSWORD" in k else v) 
                for k, v in os.environ.items() 
                if "MONGO" in k
            }
            print(f"Available MongoDB environment variables: {mongo_vars}")
        
        # Initialize database
        await init_db()
        print("MongoDB initialized successfully")
        
        # Email verification migration (DISABLED - run manually if needed)
        # This was automatically marking all users as verified on every startup
        # To run migration manually, use: POST /auth/mark-existing-users-verified
        print("📧 Email verification migration: DISABLED (run manually if needed)")
        
        # Log available collections and their document counts
        from database import database
        if database is not None:
            collections = await database.list_collection_names()
            print(f"Available database collections: {collections}")
            
            # Log document counts for each collection
            collection_stats = {}
            for collection_name in collections:
                count = await database[collection_name].count_documents({})
                collection_stats[collection_name] = count
            
            print(f"Collection document counts: {collection_stats}")
    except Exception as e:
        print(f"ERROR initializing MongoDB: {str(e)}")
        print("The application will continue, but database functionality may be limited")

# Enhanced monitoring middleware with Slack integration
from monitoring import MonitoringMiddleware, RequestLoggingMiddleware

# Add monitoring middleware (replaces basic error handling)
app.add_middleware(MonitoringMiddleware, performance_threshold=5.0)

# Add request logging middleware for development
if os.getenv("ENVIRONMENT") == "development":
    app.add_middleware(RequestLoggingMiddleware)

# Frontend is served by Next.js server (npm start), not by FastAPI
# Backend only handles API routes
print("="*80)
print("🔧 FRONTEND SERVING MODE")
print("="*80)
print("✅ Using Next.js server mode (not static export)")
print("✅ Frontend will be served by Next.js on port 3001")
print("✅ Backend API only handles /api/* routes")
print("="*80)

# Note: Static file serving disabled - Next.js server handles all frontend routes
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
