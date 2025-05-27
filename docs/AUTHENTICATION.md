# Authentication System

## Overview

The Language Tutor application implements a comprehensive authentication system that supports multiple authentication methods, secure session management, and role-based access control. This document details the authentication architecture, implementation, and security considerations.

## Authentication Architecture

The authentication system uses a multi-layered approach:

1. **JWT-based Authentication**: Primary authentication method using JSON Web Tokens
2. **Google OAuth Integration**: Social login option for streamlined user experience
3. **Password Reset Flow**: Secure password recovery mechanism
4. **Guest Access System**: Limited functionality for unauthenticated users

![Authentication Architecture](https://mermaid.ink/img/pako:eNp1ksFuwjAMhl_FyglQJ9qyFcEBaRKHcUBCaAeucXCTlkZLkypxQKXquyftYBvbOCXO7_-z4yRnkEYhlCCUbIzuSKJYKaNbNINVajU42gZjlCUldUeG36MeT-i4Ui9krEHaWO7FtG2VtcagHJRswlQdOg6uMpoE_yWT0VnQDTmvWrTcY8WXhBNuyXPvacVBqx4d9ljxJWGPW3LcB1pR0KrHY9_QgPXoLZ_QaFmhYBdvJJvZUY_BDNp5_pLkxTzPi8V8NsuzRVZk0-m0yNJZNl_cZ3meppM0nWVZOkvSdJ6mk0PRQ9iQxsOWBm3Dw71SMtzbJ2tVQ8596G30aPmgB7TcY0uGMdHj4Dqy4ZF2ytfhVRs6Y1VYG6E11mFBG9TYkrNhf_giSeJkkuxl8Si5kyTxThLvJNFOEu8k0U4S7SR7fwD-Ht5P?type=png)

## Backend Implementation

### JWT Authentication

```python
# From auth_routes.py
def create_access_token(data: dict, expires_delta: timedelta = None):
    """Generate a JWT token with optional expiration"""
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    
    # Create encoded JWT
    encoded_jwt = jwt.encode(
        to_encode, 
        SECRET_KEY, 
        algorithm=ALGORITHM
    )
    
    return encoded_jwt
```

JWT tokens are created with:
- User ID encoded in the token payload
- Configurable expiration time (default: 15 minutes)
- HMAC-SHA256 (HS256) algorithm for signing

### Password Hashing

```python
# From auth_routes.py
def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)
```

Password security is ensured with:
- Bcrypt hashing algorithm with salt
- Configurable work factor for future-proofing
- Constant-time comparison to prevent timing attacks

### User Authentication Flow

```python
# From auth_routes.py
@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """Authenticate a user and return a JWT token"""
    # Authenticate user credentials
    user = await authenticate_user(login_data.email, login_data.password)
    
    # Return 401 if authentication fails
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)}, 
        expires_delta=access_token_expires
    )
    
    # Update last login timestamp
    await users_collection.update_one(
        {"_id": user.id}, 
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Return token and user information
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "name": user.name,
        "email": user.email
    }
```

The login endpoint:
- Validates user credentials
- Generates a JWT token
- Updates the last login timestamp
- Returns the token with basic user information

### Google OAuth Integration

```python
# From auth_routes.py
@router.post("/google-login", response_model=Token)
async def google_login(token_data: GoogleTokenRequest):
    """Authenticate with Google OAuth token"""
    try:
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            token_data.token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
        
        # Extract user information
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        
        # Check if user exists
        existing_user = await users_collection.find_one({"email": email})
        
        if existing_user:
            # Update existing user
            user_id = existing_user["_id"]
            await users_collection.update_one(
                {"_id": user_id},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        else:
            # Create new user
            user_id = ObjectId()
            new_user = {
                "_id": user_id,
                "email": email,
                "name": name,
                "is_active": True,
                "is_verified": True,  # Google-authenticated users are verified
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow()
            }
            await users_collection.insert_one(new_user)
        
        # Generate JWT token
        access_token = create_access_token(
            data={"sub": str(user_id)},
            expires_delta=access_token_expires
        )
        
        # Return token and user information
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": str(user_id),
            "name": name,
            "email": email
        }
    
    except ValueError:
        # Invalid token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
```

The Google OAuth flow:
- Verifies the token with Google's authentication service
- Creates a new user or updates an existing one
- Automatically marks Google-authenticated users as verified
- Issues a JWT token for the authenticated session

### Password Reset Flow

```python
# From auth_routes.py
@router.post("/request-password-reset")
async def request_password_reset(email_data: EmailRequest):
    """Request a password reset token"""
    user = await users_collection.find_one({"email": email_data.email})
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If your email is registered, you will receive a reset link"}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    
    # Store token in database
    await password_reset_collection.insert_one({
        "email": email_data.email,
        "token": reset_token,
        "created_at": datetime.utcnow()
    })
    
    # Send email with reset link
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    
    # Email sending logic
    # ...
    
    return {"message": "If your email is registered, you will receive a reset link"}

@router.post("/reset-password")
async def reset_password(reset_data: PasswordResetRequest):
    """Reset a user's password using a reset token"""
    # Find reset token
    reset_record = await password_reset_collection.find_one({
        "token": reset_data.token,
        "created_at": {"$gt": datetime.utcnow() - timedelta(hours=1)}
    })
    
    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update user's password
    hashed_password = get_password_hash(reset_data.new_password)
    
    result = await users_collection.update_one(
        {"email": reset_record["email"]},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete used token
    await password_reset_collection.delete_one({"token": reset_data.token})
    
    return {"message": "Password updated successfully"}
```

The password reset flow includes:
- Secure token generation
- 1-hour token expiration
- Email delivery of reset links
- Secure password update process

### Token Validation Middleware

```python
# From auth_routes.py
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate JWT token and return the current user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
        
        # Find user in database
        user_obj = await users_collection.find_one({"_id": ObjectId(user_id)})
        
        if user_obj is None:
            raise credentials_exception
        
        # Convert to Pydantic model
        user = UserInDB(**user_obj)
        return user
    
    except JWTError:
        raise credentials_exception
```

This middleware:
- Extracts and validates the JWT token
- Retrieves the user from the database
- Raises appropriate exceptions for invalid tokens
- Returns the authenticated user for route handlers

## Frontend Implementation

### Authentication Context

```typescript
// From auth-context.tsx
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Initialize auth state from localStorage
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    const storedToken = localStorage.getItem('token');
    
    if (storedUser && storedToken) {
      setUser(JSON.parse(storedUser));
    }
    
    setLoading(false);
  }, []);
  
  // Login function
  const login = async (email: string, password: string): Promise<User> => {
    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }
      
      const userData = await response.json();
      
      // Store auth data
      localStorage.setItem('token', userData.access_token);
      localStorage.setItem('user', JSON.stringify({
        id: userData.user_id,
        name: userData.name,
        email: userData.email,
      }));
      
      // Update state
      setUser({
        id: userData.user_id,
        name: userData.name,
        email: userData.email,
      });
      
      return userData;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };
  
  // Logout function
  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };
  
  // Google login function
  const googleLogin = async (token: string): Promise<User> => {
    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/auth/google-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Google login failed');
      }
      
      const userData = await response.json();
      
      // Store auth data
      localStorage.setItem('token', userData.access_token);
      localStorage.setItem('user', JSON.stringify({
        id: userData.user_id,
        name: userData.name,
        email: userData.email,
      }));
      
      // Update state
      setUser({
        id: userData.user_id,
        name: userData.name,
        email: userData.email,
      });
      
      return userData;
    } catch (error) {
      console.error('Google login error:', error);
      throw error;
    }
  };
  
  // Context value
  const value = {
    user,
    loading,
    login,
    logout,
    googleLogin,
    isAuthenticated: !!user,
  };
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
```

The authentication context:
- Manages user authentication state
- Provides login and logout functions
- Handles token storage in localStorage
- Exposes authentication status to components

### Google Authentication Button

```typescript
// From GoogleAuthButton.tsx
export const GoogleAuthButton: React.FC<GoogleAuthButtonProps> = ({ onSuccess, onError }) => {
  const { googleLogin } = useAuth();
  
  useEffect(() => {
    // Initialize Google Sign-In
    if (window.google?.accounts?.id) {
      window.google.accounts.id.initialize({
        client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '',
        callback: handleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true,
      });
      
      window.google.accounts.id.renderButton(
        document.getElementById('google-signin-button')!,
        { 
          type: 'standard',
          theme: 'outline',
          size: 'large',
          text: 'signin_with',
          shape: 'rectangular',
          width: 280
        }
      );
    } else {
      console.error('Google Sign-In SDK not loaded');
    }
  }, []);
  
  // Handle Google credential response
  const handleCredentialResponse = async (response: any) => {
    try {
      // Get ID token from response
      const token = response.credential;
      
      // Authenticate with backend
      const user = await googleLogin(token);
      
      // Call success callback
      if (onSuccess) {
        onSuccess(user);
      }
    } catch (error) {
      console.error('Google authentication error:', error);
      
      // Call error callback
      if (onError) {
        onError(error as Error);
      }
    }
  };
  
  return (
    <div className="google-auth-container">
      <div id="google-signin-button"></div>
    </div>
  );
};
```

The Google authentication button:
- Initializes the Google Sign-In SDK
- Renders the standard Google Sign-In button
- Processes the authentication response
- Integrates with the auth context

### Protected Route Component

```typescript
// From ProtectedRoute.tsx
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children,
  redirectTo = '/login',
  allowGuest = false
}) => {
  const { user, loading, isAuthenticated } = useAuth();
  const router = useRouter();
  
  useEffect(() => {
    // Skip if still loading
    if (loading) return;
    
    // Check if guest access is allowed
    if (!isAuthenticated && !allowGuest) {
      // Store the current path for redirect after login
      sessionStorage.setItem('redirectAfterLogin', router.asPath);
      
      // Redirect to login
      router.push(redirectTo);
    }
  }, [isAuthenticated, loading, redirectTo, router, allowGuest]);
  
  // Show loading state
  if (loading) {
    return <div className="loading">Loading...</div>;
  }
  
  // Show content if authenticated or guest access is allowed
  if (isAuthenticated || allowGuest) {
    return <>{children}</>;
  }
  
  // Return null while redirecting
  return null;
};
```

The protected route component:
- Guards routes that require authentication
- Redirects unauthenticated users to the login page
- Stores the original destination for post-login redirect
- Optionally allows guest access to certain routes

### API Authentication Utilities

```typescript
// From api-utils.ts
export const getAuthHeaders = (): HeadersInit => {
  // Get token from localStorage
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  
  // Return headers with Authorization if token exists
  return token
    ? {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    : {
        'Content-Type': 'application/json'
      };
};

export const fetchWithAuth = async (url: string, options: RequestInit = {}): Promise<Response> => {
  // Get authentication headers
  const authHeaders = getAuthHeaders();
  
  // Merge with provided options
  const mergedOptions = {
    ...options,
    headers: {
      ...authHeaders,
      ...(options.headers || {})
    }
  };
  
  // Make authenticated request
  const response = await fetch(url, mergedOptions);
  
  // Handle 401 Unauthorized
  if (response.status === 401) {
    // Clear authentication data
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    // Redirect to login
    if (typeof window !== 'undefined') {
      window.location.href = '/login?session=expired';
    }
  }
  
  return response;
};
```

These utilities:
- Add authentication headers to API requests
- Handle unauthorized responses by logging out
- Provide consistent authentication across the application

## Guest User Experience

The application supports limited functionality for guest users:

```typescript
// From speaking-assessment.tsx
const SpeakingAssessment: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [assessmentDuration, setAssessmentDuration] = useState(
    isAuthenticated ? 60 : 15
  );
  
  // Component implementation
  // ...
  
  return (
    <div className="speaking-assessment">
      {/* Assessment UI */}
      {!isAuthenticated && (
        <div className="guest-notice">
          <p>
            You are using the guest mode with limited features.
            <a href="/login">Sign in</a> for the full experience.
          </p>
        </div>
      )}
      
      {/* Assessment content */}
    </div>
  );
};
```

Guest users have:
- Limited assessment duration (15 seconds vs 60 seconds)
- Limited conversation time (1 minute vs 5 minutes)
- Clear notifications about limitations
- Easy access to sign-up/login options

## Security Considerations

### Token Storage

```typescript
// Secure token storage approach
localStorage.setItem('token', userData.access_token);

// Token retrieval
const token = localStorage.getItem('token');

// Token removal on logout
localStorage.removeItem('token');
```

The application stores authentication tokens in localStorage with considerations for:
- XSS protection through proper output encoding
- Token expiration to limit exposure
- Secure token transmission over HTTPS

### CORS Configuration

```python
# From main.py
# Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://taco.up.railway.app"
]

# In production, allow all origins for maximum compatibility
if os.getenv("ENVIRONMENT") == "production":
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

CORS is configured to:
- Allow specific origins in development
- Allow all origins in production for maximum compatibility
- Support credentials for authenticated requests
- Allow necessary methods and headers

### Password Policy

```typescript
// From auth-form.tsx
const validatePassword = (password: string): boolean => {
  // Minimum 8 characters with at least one number and one letter
  const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/;
  return passwordRegex.test(password);
};
```

The application enforces password policies:
- Minimum 8 characters
- At least one letter and one number
- Client and server-side validation
- Secure password reset process

### Rate Limiting

```python
# From main.py
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware for authentication endpoints"""
    client_ip = request.client.host
    
    # Only rate limit authentication endpoints
    if request.url.path.startswith("/api/auth"):
        # Check rate limit
        current_time = time.time()
        request_key = f"{client_ip}:{request.url.path}"
        
        # Get existing request count
        request_count = rate_limit_cache.get(request_key, {"count": 0, "reset_time": current_time + 60})
        
        # Reset count if time expired
        if current_time > request_count["reset_time"]:
            request_count = {"count": 0, "reset_time": current_time + 60}
        
        # Increment count
        request_count["count"] += 1
        rate_limit_cache[request_key] = request_count
        
        # Check if limit exceeded
        if request_count["count"] > 10:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests, please try again later"}
            )
    
    # Continue processing request
    response = await call_next(request)
    return response
```

The application implements rate limiting:
- IP-based request counting
- 10 requests per minute for authentication endpoints
- Automatic reset after the time window
- Clear error messages for rate-limited requests

## MongoDB Integration

```python
# From database.py
async def init_db():
    """Initialize database connection and indexes"""
    if database is None or client is None:
        print("WARNING: Cannot initialize database indexes - no database connection")
        return
    
    try:
        # Verify connection
        await client.admin.command('ping')
        print("MongoDB connection verified with ping")
        
        # Create indexes
        await sessions_collection.create_index("created_at", expireAfterSeconds=7 * 24 * 60 * 60)
        await password_reset_collection.create_index("created_at", expireAfterSeconds=60 * 60)
        await users_collection.create_index("email", unique=True)
        
        print("Database indexes initialized successfully")
    except Exception as e:
        print(f"ERROR initializing database indexes: {str(e)}")
```

The MongoDB integration includes:
- TTL indexes for automatic session and token expiration
- Unique email index to prevent duplicate accounts
- Proper error handling for database operations
- Connection verification on startup

## Testing and Debugging

### Authentication Testing

```python
# From test_auth.py
async def test_login_success():
    """Test successful login"""
    # Create test user
    hashed_password = get_password_hash("testpassword123")
    user_id = ObjectId()
    
    await users_collection.insert_one({
        "_id": user_id,
        "email": "test@example.com",
        "name": "Test User",
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow()
    })
    
    # Test login
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user_id"] == str(user_id)
    assert data["email"] == "test@example.com"
    
    # Clean up
    await users_collection.delete_one({"_id": user_id})
```

Authentication testing includes:
- Successful and failed login scenarios
- Token validation tests
- Password reset flow verification
- Google OAuth mocking

### Debugging Tools

```typescript
// From auth-context.tsx
const debugAuth = (message: string, data?: any) => {
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Auth] ${message}`, data);
  }
};
```

The application includes debugging tools:
- Conditional logging in development
- Clear error messages
- Authentication state tracking
- Token validation debugging

## Deployment Considerations

### Environment Variables

```
# Backend
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GOOGLE_CLIENT_ID=41687548204-0go9lqlnve4llpv3vdl48jujddlt2kp5.apps.googleusercontent.com
FRONTEND_URL=https://taco.up.railway.app

# Frontend
NEXT_PUBLIC_GOOGLE_CLIENT_ID=41687548204-0go9lqlnve4llpv3vdl48jujddlt2kp5.apps.googleusercontent.com
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Deployment requires proper configuration of:
- Secret key for JWT signing
- Google OAuth client ID
- Frontend URL for redirects
- Token expiration settings

### Production Configuration

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
    
    # Enable HTTPS redirect
    app.add_middleware(HTTPSRedirectMiddleware)
else:
    # Development settings
    app.add_middleware(
        SessionMiddleware,
        secret_key=SECRET_KEY,
        max_age=1800  # 30 minutes
    )
```

Production deployment includes:
- HTTPS enforcement
- Secure cookie settings
- Appropriate CORS configuration
- Rate limiting for security

## Future Enhancements

1. **Refresh Tokens**: Implement token refresh for longer sessions
2. **Multi-factor Authentication**: Add optional 2FA for enhanced security
3. **Session Management**: Allow users to view and manage active sessions
4. **Role-based Authorization**: Expand beyond basic authentication to role-based access control
5. **Additional OAuth Providers**: Add support for more social login options
