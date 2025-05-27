# Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Language Tutor application to production environments. The application is designed to be deployed on Railway.app, a modern platform-as-a-service (PaaS) provider, but can be adapted for other cloud platforms as needed.

## Architecture Overview

The Language Tutor application consists of two main components:

1. **Frontend**: Next.js application
2. **Backend**: FastAPI application

These components are deployed as separate services but work together to provide a seamless user experience.

![Deployment Architecture](https://mermaid.ink/img/pako:eNp1kk9rwzAMxb9K8CmFNaRL_kAPg0F32GGwwXbYNQ6OrdZgJ8GxYS3pd5_SZGvXjZMsv_f0JNk5g9QKoQShZGN0RxLFShndog6sUqvB0TYYoyxJqTsy_B71eELHlXohYw3SxnIvpm2rrDUG5aBkE6bq0HFwldEk-C-ZjM6Cbsh51aLlHiu-JJxwS557TysOWvXosMeKLwl73JLjPtCKglY9HvuGBqxHb_mERssKBbt4I9nMjnoMZtDO85ckL-Z5XizmszxbZEU2nU6LLJ1l88V9ludpOknTWZals2SazpN0cih6CBvSeNjSoG14uFdKhnv7ZK1qyLkPvY0eLR_0gJZ7bMkwJnocXEc2PNJO-Tq8akNnrAprI7TGOixogxpbcjbsD18kSZxMkr0sHiV3kiTeSZKdJtpJ4p0m2mminWbvDwDU3lA?type=png)

## Prerequisites

Before deploying the Language Tutor application, ensure you have:

1. **Railway.app Account**: Sign up at [Railway.app](https://railway.app/)
2. **GitHub Repository**: The application code should be in a GitHub repository
3. **Environment Variables**: Prepare all required environment variables (detailed below)
4. **MongoDB Atlas Account**: For the production database (or another MongoDB provider)
5. **OpenAI API Key**: For the language model and speech recognition features

## Environment Variables

### Backend Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | API key for OpenAI services | `sk-...` |
| `MONGODB_URL` | Connection string for MongoDB | `mongodb+srv://user:password@cluster.mongodb.net/language_tutor` |
| `DATABASE_NAME` | Name of the MongoDB database | `language_tutor` |
| `SECRET_KEY` | Secret key for JWT token generation | `your-secret-key-at-least-32-chars-long` |
| `ALGORITHM` | Algorithm for JWT token generation | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time in minutes | `30` |
| `GOOGLE_CLIENT_ID` | Client ID for Google OAuth | `41687548204-0go9lqlnve4llpv3vdl48jujddlt2kp5.apps.googleusercontent.com` |
| `FRONTEND_URL` | URL of the frontend application | `https://taco.up.railway.app` |
| `ENVIRONMENT` | Deployment environment | `production` |

### Frontend Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | URL of the backend API | `https://taco-backend.up.railway.app` |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Client ID for Google OAuth | `41687548204-0go9lqlnve4llpv3vdl48jujddlt2kp5.apps.googleusercontent.com` |

## Deployment Steps

### 1. Prepare the Repository

Ensure your repository has the following files:

- `railway.json` in the root directory
- `Procfile` in both frontend and backend directories
- `.env.example` files with required environment variables

```json
// railway.json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "echo 'Building Language Tutor'"
  },
  "deploy": {
    "startCommand": "echo 'Starting Language Tutor'",
    "healthcheckPath": "/",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 2. Deploy the Backend

1. **Create a new project in Railway.app**:
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project" > "Deploy from GitHub repo"
   - Select your GitHub repository
   - Choose the main branch (or your deployment branch)

2. **Configure the backend service**:
   - Set the root directory to `/backend`
   - Add all required environment variables
   - Set the start command to `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Deploy the backend**:
   - Click "Deploy" to start the deployment process
   - Wait for the build and deployment to complete
   - Note the generated URL for your backend service

### 3. Deploy the Frontend

1. **Add a new service to your Railway project**:
   - Click "New Service" > "GitHub Repo"
   - Select the same repository
   - Choose the main branch (or your deployment branch)

2. **Configure the frontend service**:
   - Set the root directory to `/frontend`
   - Add all required environment variables
   - Set `NEXT_PUBLIC_API_URL` to the backend URL from step 2
   - Set the start command to `npm run start`

3. **Deploy the frontend**:
   - Click "Deploy" to start the deployment process
   - Wait for the build and deployment to complete
   - Note the generated URL for your frontend service

### 4. Configure Domain and HTTPS

1. **Set up custom domains** (optional):
   - In the Railway dashboard, go to your frontend service
   - Click on the "Settings" tab
   - Scroll to "Domains" and click "Generate Domain"
   - You can use a Railway subdomain or configure your own custom domain

2. **HTTPS is automatically configured** by Railway for all domains

### 5. Verify Deployment

1. **Check the frontend**:
   - Visit your frontend URL
   - Verify that the application loads correctly
   - Test basic functionality like language selection

2. **Check the backend**:
   - Visit `{backend-url}/docs` to access the Swagger documentation
   - Verify that the API endpoints are accessible
   - Test the health check endpoint at `{backend-url}/api/health`

## Deployment Configuration

### Backend Configuration

The backend is configured for production deployment with the following settings:

```python
# From main.py
# Production settings
if os.getenv("ENVIRONMENT") == "production":
    # Use secure cookies
    app.add_middleware(
        SessionMiddleware,
        secret_key=SECRET_KEY,
        max_age=1800,  # 30 minutes
        https_only=True
    )
    
    # CORS configuration for production
    origins = ["*"]  # Allow all origins in production for maximum compatibility
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

### Frontend Configuration

The frontend is configured for production deployment with the following settings:

```javascript
// next.config.js
module.exports = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ];
  },
};
```

## API URL Configuration

The frontend uses a dynamic API URL configuration to handle different environments:

```typescript
// From api-utils.ts
export function getApiUrl(): string {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname.includes('railway.app')) {
      return '';
    }
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return window.location.origin;
    }
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}
```

This function:
- Returns an empty string for Railway deployments (same-origin requests)
- Uses the environment variable for local development
- Handles other deployment scenarios gracefully

## MongoDB Configuration

The MongoDB connection is configured for production with:

```python
# From database.py
# MongoDB connection string from environment variables
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

# Create async client with production settings
if "mongodb+srv" in MONGODB_URL:
    # Configure connection pooling for Atlas
    client = motor.motor_asyncio.AsyncIOMotorClient(
        MONGODB_URL,
        maxPoolSize=10,
        minPoolSize=1,
        maxIdleTimeMS=30000,
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000,
        retryWrites=True,
        w="majority"
    )
else:
    # Local MongoDB configuration
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
```

## Health Checks

The application includes health check endpoints for monitoring:

```python
# From main.py
@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db_health = await get_database_health()
        
        # Check OpenAI API
        openai_health = await check_openai_health()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": VERSION,
            "database": db_health,
            "openai": openai_health
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "version": VERSION
        }
```

The frontend also includes a health check utility:

```typescript
// From healthCheck.ts
export async function checkBackendHealth(baseUrl?: string): Promise<HealthCheckResponse> {
  // Determine the API URL based on the environment
  let apiUrl = baseUrl || '';
  if (typeof window !== 'undefined') {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      apiUrl = 'http://localhost:8000';
    }
  }
  
  // Retry logic for better reliability
  let retries = 0;
  const maxRetries = 3;
  
  while (retries < maxRetries) {
    try {
      const response = await fetch(`${apiUrl}/api/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        return {
          isHealthy: data.status === 'healthy',
          details: data,
          error: null
        };
      } else {
        const errorData = await response.json();
        retries++;
        
        if (retries >= maxRetries) {
          return {
            isHealthy: false,
            details: null,
            error: `Backend health check failed: ${errorData.error || response.statusText}`
          };
        }
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, 1000 * retries));
      }
    } catch (error) {
      retries++;
      
      if (retries >= maxRetries) {
        return {
          isHealthy: false,
          details: null,
          error: `Backend health check failed: ${error.message}`
        };
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, 1000 * retries));
    }
  }
  
  // This should never be reached due to the return statements in the loop
  return {
    isHealthy: false,
    details: null,
    error: 'Backend health check failed after multiple retries'
  };
}
```

## Continuous Deployment

Railway.app supports continuous deployment from GitHub:

1. **Automatic Deployments**:
   - Every push to the configured branch triggers a new deployment
   - Railway builds and deploys the application automatically

2. **Deployment Settings**:
   - In the Railway dashboard, go to your service
   - Click on the "Settings" tab
   - Under "Deployments", you can configure:
     - Automatic deployments
     - Branch to deploy from
     - Build and start commands

3. **Rollbacks**:
   - Railway keeps a history of deployments
   - You can roll back to a previous deployment if needed
   - In the Railway dashboard, go to the "Deployments" tab
   - Select a previous deployment and click "Redeploy"

## Monitoring and Logging

Railway.app provides built-in monitoring and logging:

1. **Logs**:
   - In the Railway dashboard, go to your service
   - Click on the "Logs" tab to view application logs
   - You can filter logs by severity and search for specific terms

2. **Metrics**:
   - In the Railway dashboard, go to your service
   - Click on the "Metrics" tab to view:
     - CPU usage
     - Memory usage
     - Network traffic
     - Disk usage

3. **Custom Logging**:
   - The application includes custom logging for important events
   - Logs are structured for easy filtering and analysis

```python
# From main.py
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("language-tutor")

# Log important events
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log request details
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.4f}s"
    )
    
    return response
```

## Scaling

Railway.app provides automatic scaling capabilities:

1. **Vertical Scaling**:
   - In the Railway dashboard, go to your service
   - Click on the "Settings" tab
   - Under "Resources", you can adjust:
     - CPU allocation
     - Memory allocation
     - Disk space

2. **Horizontal Scaling**:
   - The application is designed to be stateless
   - Multiple instances can run in parallel
   - Railway handles load balancing automatically

3. **Database Scaling**:
   - MongoDB Atlas provides its own scaling capabilities
   - You can adjust your MongoDB Atlas tier as needed

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Ensure the `FRONTEND_URL` environment variable is set correctly
   - Check the CORS configuration in `main.py`
   - Verify that the frontend is using the correct API URL

2. **Database Connection Issues**:
   - Verify the `MONGODB_URL` environment variable
   - Check network access rules in MongoDB Atlas
   - Ensure the IP address of your Railway service is whitelisted

3. **Authentication Problems**:
   - Verify the `SECRET_KEY` and `ALGORITHM` environment variables
   - Check the `GOOGLE_CLIENT_ID` for Google OAuth
   - Ensure the frontend and backend are using the same Google Client ID

4. **Deployment Failures**:
   - Check the build logs for errors
   - Verify that all required environment variables are set
   - Ensure the start commands are correct

### Debugging Techniques

1. **Enable Debug Logging**:
   - Set the `LOG_LEVEL` environment variable to `DEBUG`
   - Check the logs for detailed information

2. **Test API Endpoints**:
   - Use the Swagger documentation at `{backend-url}/docs`
   - Test individual endpoints to isolate issues

3. **Check Frontend Network Requests**:
   - Use browser developer tools to inspect network requests
   - Look for failed requests and error responses

## Backup and Recovery

1. **Database Backups**:
   - MongoDB Atlas provides automated backups
   - Configure backup frequency in the MongoDB Atlas dashboard
   - Test backup restoration periodically

2. **Application State**:
   - The application stores all state in the database
   - No critical data is stored in the application itself
   - Recovery involves redeploying the application and restoring the database

## Security Considerations

1. **Environment Variables**:
   - Store sensitive information in environment variables
   - Never commit secrets to the repository
   - Use Railway's environment variable management

2. **HTTPS**:
   - Railway automatically provides HTTPS for all domains
   - The application enforces HTTPS in production

3. **Authentication**:
   - JWT tokens with appropriate expiration
   - Secure password hashing with bcrypt
   - Google OAuth for social login

4. **API Security**:
   - Rate limiting for authentication endpoints
   - Input validation with Pydantic models
   - Proper error handling to prevent information leakage

## Conclusion

The Language Tutor application is designed for easy deployment on Railway.app. By following this guide, you can deploy both the frontend and backend components and configure them to work together seamlessly. The application includes health checks, monitoring, and security features to ensure reliable operation in production.

For any issues or questions, please refer to the troubleshooting section or contact the development team.
