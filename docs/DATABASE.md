# Database Structure

## Overview

The Language Tutor application uses MongoDB, a NoSQL document database, to store and manage user data, learning plans, assessment results, and session information. This document details the database architecture, collections, schema design, and data management strategies.

## Database Architecture

The application connects to MongoDB using the Motor asynchronous driver, which provides non-blocking operations for the FastAPI backend. The database is structured around several core collections, each serving a specific purpose in the application.

![Database Architecture](https://mermaid.ink/img/pako:eNp1k89uwjAMxl8lyglQJ9qyFcEBaRKHcUBCaAeucXCTlkZLkypxQKXquyftYBvbOCXO7_-z4yRnkEYhlCCUbIzuSKJYKaNbNINVajU42gZjlCUldUeG36MeT-i4Ui9krEHaWO7FtG2VtcagHJRswlQdOg6uMpoE_yWT0VnQDTmvWrTcY8WXhBNuyXPvacVBqx4d9ljxJWGPW3LcB1pR0KrHY9_QgPXoLZ_QaFmhYBdvJJvZUY_BDNp5_pLkxTzPi8V8NsuzRVZk0-m0yNJZNl_cZ3meppM0nWVZOkvSdJ6mk0PRQ9iQxsOWBm3Dw71SMtzbJ2tVQ8596G30aPmgB7TcY0uGMdHj4Dqy4ZF2ytfhVRs6Y1VYG6E11mFBG9TYkrNhf_giSeJkkuxl8Si5kyTxThLvJNFOEu8k0U4S7SR7fwD-Ht5P?type=png)

## MongoDB Connection

```python
# From database.py
import os
import motor.motor_asyncio
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# Database connection string from environment variables
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

# Create async client
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]

# Collections
users_collection = database["users"]
sessions_collection = database["sessions"]
password_reset_collection = database["password_reset"]
learning_plans_collection = database["learning_plans"]
assessments_collection = database["assessments"]
```

The database connection is configured with:
- Environment variable-based configuration
- Default local MongoDB instance fallback
- Named collections for different data types
- Asynchronous operations using Motor

## Collection Structure

### Users Collection

Stores user account information and preferences.

```python
# From models.py
class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    preferred_language: Optional[str] = None
    preferred_level: Optional[str] = None
    last_assessment_data: Optional[Dict[str, Any]] = None

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
```

Sample document:
```json
{
  "_id": ObjectId("6079a1b4e147e52b9d7c5e9a"),
  "email": "user@example.com",
  "name": "John Doe",
  "is_active": true,
  "is_verified": true,
  "created_at": ISODate("2023-04-16T12:30:45.123Z"),
  "last_login": ISODate("2023-04-18T09:15:22.456Z"),
  "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
  "preferred_language": "english",
  "preferred_level": "B1",
  "last_assessment_data": {
    "cefr_level": "B1",
    "accuracy": 0.85,
    "fluency": 0.78,
    "timestamp": ISODate("2023-04-17T14:22:33.789Z")
  }
}
```

### Sessions Collection

Manages user authentication sessions with automatic expiration.

```python
# From models.py
class Session(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
```

Sample document:
```json
{
  "_id": ObjectId("6079a2c5f1e8d34a7b9d1e2f"),
  "user_id": ObjectId("6079a1b4e147e52b9d7c5e9a"),
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "created_at": ISODate("2023-04-16T12:35:45.123Z"),
  "expires_at": ISODate("2023-04-16T13:35:45.123Z")
}
```

### Learning Plans Collection

Stores user learning plans with goals, topics, and progress tracking.

```python
# From models.py
class LearningPlan(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: Optional[PyObjectId] = None
    language: str
    level: str
    topic: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_active: bool = True
    goals: List[str] = []
    progress: Dict[str, Any] = {}
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
```

Sample document:
```json
{
  "_id": ObjectId("607a3d9c8b2e7a1c5f4d2e3b"),
  "user_id": ObjectId("6079a1b4e147e52b9d7c5e9a"),
  "language": "english",
  "level": "B1",
  "topic": "travel",
  "created_at": ISODate("2023-04-17T09:20:12.345Z"),
  "updated_at": ISODate("2023-04-18T10:15:30.678Z"),
  "is_active": true,
  "goals": [
    "Improve conversation skills",
    "Learn travel vocabulary",
    "Practice past tense"
  ],
  "progress": {
    "sessions_completed": 3,
    "total_speaking_time": 450,
    "vocabulary_mastered": 42,
    "last_session": ISODate("2023-04-18T10:15:30.678Z")
  }
}
```

### Assessments Collection

Records user speaking and language assessments with detailed feedback.

```python
# From models.py
class SpeakingAssessment(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: Optional[PyObjectId] = None
    language: str
    audio_url: Optional[str] = None
    transcript: str
    duration: float
    cefr_level: str
    feedback: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
```

Sample document:
```json
{
  "_id": ObjectId("607b4e2d9f3a8b2c1d5e6f7a"),
  "user_id": ObjectId("6079a1b4e147e52b9d7c5e9a"),
  "language": "english",
  "transcript": "I think traveling is a great way to learn about different cultures and meet new people. Last year, I visited Spain and it was an amazing experience.",
  "duration": 15.7,
  "cefr_level": "B1",
  "feedback": {
    "pronunciation": {
      "score": 0.82,
      "feedback": "Good pronunciation overall. Work on the 'r' sound in 'traveling'."
    },
    "grammar": {
      "score": 0.88,
      "feedback": "Good use of past tense. Consider using more complex sentence structures."
    },
    "vocabulary": {
      "score": 0.75,
      "feedback": "Good basic vocabulary. Try to incorporate more specific travel-related terms."
    },
    "fluency": {
      "score": 0.79,
      "feedback": "Good flow with minimal pauses. Work on connecting ideas more smoothly."
    },
    "coherence": {
      "score": 0.85,
      "feedback": "Clear and coherent response with logical progression."
    },
    "overall": {
      "score": 0.82,
      "feedback": "Solid B1 level performance. Focus on expanding vocabulary and using more complex structures."
    }
  },
  "created_at": ISODate("2023-04-18T14:25:33.456Z")
}
```

### Password Reset Collection

Manages password reset tokens with automatic expiration.

```python
# From models.py
class PasswordReset(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
```

Sample document:
```json
{
  "_id": ObjectId("607c5f3e0a1b2c3d4e5f6a7b"),
  "email": "user@example.com",
  "token": "a1b2c3d4e5f6g7h8i9j0",
  "created_at": ISODate("2023-04-19T10:45:22.789Z")
}
```

## Database Indexes

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
        await learning_plans_collection.create_index([("user_id", 1), ("is_active", 1)])
        await assessments_collection.create_index([("user_id", 1), ("created_at", -1)])
        
        print("Database indexes initialized successfully")
    except Exception as e:
        print(f"ERROR initializing database indexes: {str(e)}")
```

The application creates several indexes for performance and functionality:
- TTL (Time-To-Live) index on sessions for automatic expiration after 7 days
- TTL index on password reset tokens for expiration after 1 hour
- Unique index on user email to prevent duplicate accounts
- Compound index on learning plans for quick retrieval of active plans
- Compound index on assessments for chronological user history

## Data Models and Validation

The application uses Pydantic models for data validation and serialization:

```python
# From models.py
class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")
```

This custom type enables:
- Proper validation of MongoDB ObjectId values
- Automatic conversion between string and ObjectId
- JSON serialization of ObjectId fields

## CRUD Operations

### Create Operations

```python
# From auth_routes.py
@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    # Check if email already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user document
    user_dict = user_data.dict()
    del user_dict["password"]
    user_dict["hashed_password"] = hashed_password
    user_dict["created_at"] = datetime.utcnow()
    
    # Insert into database
    result = await users_collection.insert_one(user_dict)
    
    # Get created user
    created_user = await users_collection.find_one({"_id": result.inserted_id})
    
    return UserInDB(**created_user)
```

### Read Operations

```python
# From learning_routes.py
@router.get("/plans", response_model=List[LearningPlanResponse])
async def get_learning_plans(current_user: User = Depends(get_current_user)):
    """Get all learning plans for the current user"""
    cursor = learning_plans_collection.find({"user_id": current_user.id})
    plans = await cursor.to_list(length=100)
    
    return [LearningPlanResponse(**plan) for plan in plans]

@router.get("/plans/{plan_id}", response_model=LearningPlanResponse)
async def get_learning_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific learning plan by ID"""
    # Validate ObjectId
    try:
        plan_object_id = ObjectId(plan_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID format"
        )
    
    # Find plan
    plan = await learning_plans_collection.find_one({
        "_id": plan_object_id,
        "user_id": current_user.id
    })
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning plan not found"
        )
    
    return LearningPlanResponse(**plan)
```

### Update Operations

```python
# From learning_routes.py
@router.put("/plans/{plan_id}", response_model=LearningPlanResponse)
async def update_learning_plan(
    plan_id: str,
    plan_data: LearningPlanUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a learning plan"""
    # Validate ObjectId
    try:
        plan_object_id = ObjectId(plan_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID format"
        )
    
    # Check if plan exists and belongs to user
    existing_plan = await learning_plans_collection.find_one({
        "_id": plan_object_id,
        "user_id": current_user.id
    })
    
    if not existing_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning plan not found"
        )
    
    # Prepare update data
    update_data = plan_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    # Update plan
    await learning_plans_collection.update_one(
        {"_id": plan_object_id},
        {"$set": update_data}
    )
    
    # Get updated plan
    updated_plan = await learning_plans_collection.find_one({"_id": plan_object_id})
    
    return LearningPlanResponse(**updated_plan)
```

### Delete Operations

```python
# From learning_routes.py
@router.delete("/plans/{plan_id}", response_model=dict)
async def delete_learning_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a learning plan"""
    # Validate ObjectId
    try:
        plan_object_id = ObjectId(plan_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID format"
        )
    
    # Check if plan exists and belongs to user
    existing_plan = await learning_plans_collection.find_one({
        "_id": plan_object_id,
        "user_id": current_user.id
    })
    
    if not existing_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning plan not found"
        )
    
    # Delete plan
    result = await learning_plans_collection.delete_one({"_id": plan_object_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete learning plan"
        )
    
    return {"message": "Learning plan deleted successfully"}
```

## Guest User Data Management

The application supports guest users with temporary data storage:

```python
# From learning_routes.py
@router.post("/plan", response_model=LearningPlanResponse)
async def create_learning_plan(
    plan_data: LearningPlanCreate,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Create a new learning plan (works for both authenticated and guest users)"""
    # Create plan document
    plan_dict = plan_data.dict()
    plan_dict["created_at"] = datetime.utcnow()
    
    # Add user ID if authenticated
    if current_user:
        plan_dict["user_id"] = current_user.id
    
    # Insert into database
    result = await learning_plans_collection.insert_one(plan_dict)
    
    # Get created plan
    created_plan = await learning_plans_collection.find_one({"_id": result.inserted_id})
    
    return LearningPlanResponse(**created_plan)
```

For guest users:
- Learning plans are created without a user_id
- Assessment data is stored temporarily
- Data can be claimed later by authenticated users

## Data Migration and Cleanup

```python
# From maintenance_tasks.py
async def cleanup_guest_data():
    """Remove old guest data (no user_id) older than 7 days"""
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    
    # Delete old guest learning plans
    result = await learning_plans_collection.delete_many({
        "user_id": None,
        "created_at": {"$lt": cutoff_date}
    })
    
    print(f"Deleted {result.deleted_count} old guest learning plans")
    
    # Delete old guest assessments
    result = await assessments_collection.delete_many({
        "user_id": None,
        "created_at": {"$lt": cutoff_date}
    })
    
    print(f"Deleted {result.deleted_count} old guest assessments")
```

Regular maintenance tasks:
- Remove guest data after 7 days
- Clean up expired sessions and tokens
- Archive old assessment data

## Database Performance

### Connection Pooling

```python
# From database.py
# Configure connection pool
client = motor.motor_asyncio.AsyncIOMotorClient(
    MONGODB_URL,
    maxPoolSize=10,
    minPoolSize=1,
    maxIdleTimeMS=30000,
    connectTimeoutMS=5000,
    serverSelectionTimeoutMS=5000
)
```

The application optimizes database connections with:
- Connection pooling for efficient resource usage
- Minimum and maximum pool size configuration
- Idle connection timeout management
- Connection and server selection timeouts

### Query Optimization

```python
# From learning_routes.py
# Optimized query with projection
@router.get("/user/stats", response_model=UserStats)
async def get_user_stats(current_user: User = Depends(get_current_user)):
    """Get user statistics"""
    # Count learning plans
    plan_count = await learning_plans_collection.count_documents({
        "user_id": current_user.id
    })
    
    # Get latest assessment with projection
    latest_assessment = await assessments_collection.find_one(
        {"user_id": current_user.id},
        sort=[("created_at", -1)],
        projection={"cefr_level": 1, "feedback.overall.score": 1, "created_at": 1}
    )
    
    # Count total assessments
    assessment_count = await assessments_collection.count_documents({
        "user_id": current_user.id
    })
    
    # Return stats
    return {
        "plan_count": plan_count,
        "assessment_count": assessment_count,
        "latest_assessment": latest_assessment
    }
```

Query optimization techniques include:
- Projection to retrieve only necessary fields
- Indexing for frequently queried fields
- Sorting with indexes for efficient ordering
- Count operations for aggregate data

## Error Handling and Resilience

```python
# From database.py
async def get_database_health():
    """Check database connection health"""
    try:
        # Try to ping the database
        await client.admin.command('ping')
        
        # Get database stats
        stats = await database.command('dbStats')
        
        return {
            "status": "connected",
            "collections": stats.get("collections", 0),
            "objects": stats.get("objects", 0),
            "avgObjSize": stats.get("avgObjSize", 0),
            "dataSize": stats.get("dataSize", 0),
            "storageSize": stats.get("storageSize", 0),
            "indexes": stats.get("indexes", 0),
            "indexSize": stats.get("indexSize", 0)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

The application implements robust error handling:
- Database health checks
- Connection retry mechanisms
- Detailed error reporting
- Graceful degradation for database failures

## Backup and Recovery

```python
# From backup_script.py
async def backup_database():
    """Create a backup of the database"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join("backups", timestamp)
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # Get all collections
    collections = await database.list_collection_names()
    
    for collection_name in collections:
        # Get all documents in collection
        cursor = database[collection_name].find({})
        documents = await cursor.to_list(length=None)
        
        # Write to JSON file
        with open(os.path.join(backup_dir, f"{collection_name}.json"), "w") as f:
            json.dump(documents, f, default=json_serializer)
    
    print(f"Backup completed: {backup_dir}")
    return backup_dir
```

Database backup strategies include:
- Regular automated backups
- Collection-level JSON exports
- Timestamp-based backup organization
- Custom serialization for MongoDB types

## Security Considerations

### Data Encryption

```python
# From models.py
class SensitiveData(BaseModel):
    """Model for sensitive user data with encryption"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    data_type: str
    encrypted_data: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# From encryption.py
def encrypt_sensitive_data(data: str, key: bytes) -> str:
    """Encrypt sensitive data using Fernet symmetric encryption"""
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str, key: bytes) -> str:
    """Decrypt sensitive data"""
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()
```

Sensitive data protection includes:
- Fernet symmetric encryption for sensitive fields
- Separate collection for encrypted data
- Key management through environment variables
- Minimal storage of sensitive information

### Access Control

```python
# From database_access.py
class DatabaseAccess:
    """Database access control layer"""
    def __init__(self, user: User):
        self.user = user
    
    async def get_user_data(self, collection_name: str, query: dict = None):
        """Get user data with access control"""
        if query is None:
            query = {}
        
        # Ensure user can only access their own data
        query["user_id"] = self.user.id
        
        # Get collection
        collection = database[collection_name]
        
        # Execute query
        cursor = collection.find(query)
        return await cursor.to_list(length=100)
    
    async def update_user_data(self, collection_name: str, document_id: ObjectId, update_data: dict):
        """Update user data with access control"""
        # Ensure user can only update their own data
        collection = database[collection_name]
        
        # Check document ownership
        document = await collection.find_one({
            "_id": document_id,
            "user_id": self.user.id
        })
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied"
            )
        
        # Perform update
        result = await collection.update_one(
            {"_id": document_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
```

Access control mechanisms include:
- User-based data isolation
- Document ownership verification
- Role-based access control
- Principle of least privilege

## Deployment Considerations

### Environment Variables

```
# MongoDB connection
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/language_tutor?retryWrites=true&w=majority
DATABASE_NAME=language_tutor

# Database encryption
DB_ENCRYPTION_KEY=your-base64-encoded-key
```

Deployment requires:
- Secure MongoDB connection string
- Proper database name configuration
- Encryption key management
- Backup configuration

### Production Configuration

```python
# From database.py
# Production settings
if os.getenv("ENVIRONMENT") == "production":
    # Use MongoDB Atlas connection string
    MONGODB_URL = os.getenv("MONGODB_URL")
    
    # Configure TLS/SSL
    client = motor.motor_asyncio.AsyncIOMotorClient(
        MONGODB_URL,
        tls=True,
        tlsAllowInvalidCertificates=False,
        retryWrites=True,
        w="majority"
    )
else:
    # Development settings
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
```

Production deployment includes:
- MongoDB Atlas configuration
- TLS/SSL security
- Write concern configuration
- Retry logic for write operations

## MongoDB Atlas Integration

```python
# From database.py
# Atlas-specific configuration
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
    
    print("Configured for MongoDB Atlas")
else:
    # Local MongoDB configuration
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
    print("Configured for local MongoDB")
```

MongoDB Atlas features:
- Cloud-hosted database service
- Automatic scaling and backups
- Geographic distribution
- Performance monitoring

## Future Enhancements

1. **Schema Validation**: Implement MongoDB schema validation for collections
2. **Change Streams**: Use change streams for real-time data updates
3. **Aggregation Pipeline**: Implement complex data analytics using aggregation
4. **Sharding**: Prepare for horizontal scaling with sharding
5. **Time Series Collections**: Use time series collections for assessment history
