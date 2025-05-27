# Backend Architecture

## Overview

The Language Tutor backend is built with FastAPI, a modern, high-performance web framework for building APIs with Python. The backend provides a comprehensive set of endpoints for authentication, language assessment, learning plan management, and real-time conversation capabilities.

## Directory Structure

```
backend/
├── auth.py                # Authentication utilities and dependencies
├── auth_routes.py         # Authentication endpoints
├── database.py            # MongoDB connection and configuration
├── learning_routes.py     # Learning plan and goals endpoints
├── main.py                # Main FastAPI application and configuration
├── models/                # Data models and schemas
├── models.py              # Pydantic models for request/response validation
├── requirements.txt       # Python dependencies
├── run.py                 # Entry point for running the server
├── sentence_assessment.py # Sentence assessment functionality
├── speaking_assessment.py # Speaking assessment functionality
├── test_api.py            # API tests
├── tests/                 # Test files
├── tutor_instructions.json # Instructions for the AI tutor
└── utils/                 # Utility functions
```

## Core Components

### FastAPI Application (main.py)

The main application file sets up the FastAPI instance, configures middleware, and registers routes:

```python
app = FastAPI(title="Language Tutor Backend API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(learning_router)
```

Key features:
- Environment-aware CORS configuration
- Middleware for request logging and error handling
- Health check and test endpoints
- Static file serving for production deployment

### Authentication System (auth.py, auth_routes.py)

The authentication system provides:

- User registration and login
- JWT token generation and validation
- Google OAuth integration
- Password reset functionality
- Session management

```python
@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """
    Login with email and password
    """
    user = await authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=60 * 24 * 7)  # 7 days
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    # Create session
    session_token = await create_session(str(user.id))
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "name": user.name,
        "email": user.email
    }
```

### Database Connection (database.py)

The database module handles MongoDB connection with:

- Environment-aware configuration for local and Railway deployment
- Automatic index creation
- Collection initialization
- Connection error handling

```python
# Create a MongoDB client with increased timeout for Railway
try:
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
    database = client[DATABASE_NAME]
    print("MongoDB client initialized successfully")
    
    # Collections - initialize only if database connection was successful
    users_collection = database.users
    sessions_collection = database.sessions
    password_reset_collection = database.password_resets
except Exception as e:
    print(f"Error initializing MongoDB client: {str(e)}")
    # Don't crash the app immediately, let the startup event handle connection issues
    client = None
    database = None
```

### Speaking Assessment (speaking_assessment.py)

The speaking assessment module provides:

- Speech-to-text conversion using OpenAI's Whisper API
- Language proficiency evaluation based on CEFR levels
- Detailed feedback on pronunciation, grammar, vocabulary, fluency, and coherence
- Speaking prompt generation with language adaptation

```python
async def evaluate_language_proficiency(text: str, language: str, duration: int = 60) -> Dict:
    """Comprehensive assessment of language proficiency based on spoken text"""
    
    # CEFR level descriptions and criteria
    cefr_levels = {
        "A1": { /* level criteria */ },
        "A2": { /* level criteria */ },
        "B1": { /* level criteria */ },
        "B2": { /* level criteria */ },
        "C1": { /* level criteria */ },
        "C2": { /* level criteria */ }
    }
    
    # Create OpenAI client
    client = create_openai_client()
    
    try:
        # Prepare the analysis prompt
        system_prompt = f"""
        You are an expert language proficiency assessor for {language}. 
        Analyze the following spoken text and provide a detailed assessment.
        """
        
        # Call OpenAI for analysis
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Text to analyze: {text}\nDuration of speech: {duration} seconds"}
            ],
            temperature=0.1
        )
        
        # Process and return the assessment
        # ...
    except Exception as e:
        # Fallback handling
        # ...
```

### Learning Plans (learning_routes.py)

The learning routes module manages:

- Learning goal retrieval and management
- Custom learning plan creation
- Plan assignment to users
- Assessment data storage

```python
@router.post("/plan", response_model=LearningPlan)
async def create_learning_plan(
    plan_request: LearningPlanRequest,
    current_user: Optional[UserResponse] = None
):
    """
    Create a custom learning plan based on user's proficiency level, goals, and duration.
    Authentication is optional - if authenticated, the plan will be associated with the user.
    """
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key not configured"
        )
    
    # Generate a learning plan using OpenAI
    # ...
    
    # Store the plan in the database
    # ...
    
    return plan
```

## API Endpoints

### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Register a new user |
| `/auth/login` | POST | Login with email and password |
| `/auth/google-login` | POST | Login with Google OAuth token |
| `/auth/me` | GET | Get current user information |
| `/auth/update-profile` | PUT | Update user profile |
| `/auth/logout` | POST | Logout and invalidate session |

### Learning Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/learning/goals` | GET | Get available learning goals |
| `/learning/plan` | POST | Create a learning plan |
| `/learning/plan/{plan_id}` | GET | Get a specific learning plan |
| `/learning/plans` | GET | Get all user learning plans |
| `/learning/save-assessment` | POST | Save assessment data to user profile |

### Assessment Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/assessment/speaking` | POST | Perform speaking assessment |
| `/api/speaking-prompts` | GET | Get speaking prompts |
| `/api/assessment/sentence` | POST | Perform sentence assessment |

### Real-time Conversation Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/token` | POST | Generate ephemeral key for OpenAI Realtime API |
| `/api/mock-token` | POST | Mock token for testing |

### System Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check endpoint |
| `/api/test` | GET | Test connection endpoint |
| `/api/endpoints` | GET | List available API endpoints |

## OpenAI Integration

The backend integrates with several OpenAI APIs:

1. **GPT-4o**: For language assessment, learning plan generation, and sentence analysis
2. **Whisper**: For speech-to-text transcription
3. **Realtime API**: For real-time voice conversation

```python
# Example of OpenAI API usage for token generation
@app.post("/api/token")
async def generate_token(request: TutorSessionRequest):
    try:
        # Create OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Generate ephemeral key with language tutor instructions
        response = client.beta.audio.conversations.ephemeral_keys.create(
            model="gpt-4o",
            voice="alloy",
            instructions=TUTOR_INSTRUCTIONS
        )
        
        return {"ephemeral_key": response.key}
    except Exception as e:
        # Error handling
        # ...
```

## Error Handling

The backend implements comprehensive error handling:

- Global error middleware for catching unhandled exceptions
- Detailed error responses with appropriate status codes
- Extensive logging for debugging
- Graceful fallbacks for API failures

```python
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        # Log the error with traceback
        print(f"Unhandled exception: {str(e)}")
        print(f"Request path: {request.url.path}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Return a JSON response with error details
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        )
```

## Deployment Configuration

The backend is optimized for deployment on Railway:

- Environment variable detection for Railway
- Flexible MongoDB connection string handling
- CORS configuration for production
- Static file serving for the Next.js frontend
- Health check endpoint for monitoring

```python
# Check for Railway-specific environment
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY") == "true":
    print("Running in Railway environment, using permissive CORS settings")
    # The correct frontend URL based on previous memory
    frontend_url = "https://taco.up.railway.app"
    
    # In production Railway environment, we use wildcard origins for maximum compatibility
    origins = ["*"]
```

## Security Considerations

The backend implements several security measures:

- Password hashing with bcrypt
- JWT token authentication with expiration
- HTTPS enforcement in production
- Environment variable protection for sensitive data
- MongoDB connection string obfuscation in logs
- Rate limiting for sensitive endpoints (authentication)

## Performance Optimization

The backend is optimized for performance:

- Asynchronous request handling with FastAPI
- Connection pooling for MongoDB
- Caching of frequently accessed data
- Timeout settings for external API calls
- Efficient error handling to prevent cascading failures
