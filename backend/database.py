import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debug Railway environment
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY") == "true":
    print("Detected Railway environment")
    # Print all environment variables with MONGO in them (masking passwords)
    mongo_env_vars = {k: ("***" if "PASSWORD" in k or "password" in k else v) 
                     for k, v in os.environ.items() 
                     if "MONGO" in k.upper()}
    print(f"Available MongoDB environment variables: {mongo_env_vars}")

# Get MongoDB connection string from environment variables
# Check for Railway-specific MongoDB environment variables first
MONGODB_URL = None

# Check for MongoDB URL in various environment variable formats
for var_name in ["MONGODB_URL", "MONGO_URL", "MONGO_PUBLIC_URL"]:
    if os.getenv(var_name):
        MONGODB_URL = os.getenv(var_name)
        print(f"Using MongoDB URL from {var_name}")
        break

# If we're in Railway but no MongoDB URL is found, try to construct it from individual variables
if not MONGODB_URL and (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY") == "true"):
    mongo_host = os.getenv("MONGOHOST")
    mongo_port = os.getenv("MONGOPORT")
    mongo_user = os.getenv("MONGOUSER")
    mongo_password = os.getenv("MONGOPASSWORD")
    
    if mongo_host and mongo_user and mongo_password:
        # Construct MongoDB URL with authentication
        port_str = f":{mongo_port}" if mongo_port else ""
        MONGODB_URL = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}{port_str}"
        print(f"Constructed MongoDB URL for Railway: mongodb://{mongo_user}:***@{mongo_host}{port_str}")

# Fall back to localhost if no MongoDB URL is found
if not MONGODB_URL:
    MONGODB_URL = "mongodb://localhost:27017"
    print("Warning: Using localhost MongoDB. This won't work in Railway unless properly configured.")

DATABASE_NAME = os.getenv("DATABASE_NAME") or os.getenv("MONGO_DATABASE") or "language_tutor"

print(f"Connecting to MongoDB at: {MONGODB_URL.replace(MONGODB_URL.split('@')[0] if '@' in MONGODB_URL else MONGODB_URL, 'mongodb://***:***')}")
print(f"Using database: {DATABASE_NAME}")

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
    users_collection = None
    sessions_collection = None
    password_reset_collection = None

# Initialize TTL index for sessions (expire after 7 days)
async def init_db():
    # Check if database connection is available
    if database is None or client is None:
        print("WARNING: Cannot initialize database indexes - no database connection")
        return
    
    try:
        # Test the connection by pinging the server
        await client.admin.command('ping')
        print("MongoDB connection verified with ping")
        
        # Check if collections are available
        if (users_collection is None or 
            sessions_collection is None or 
            password_reset_collection is None):
            print("WARNING: Cannot initialize database indexes - collections not available")
            return
            
        # Create TTL index for sessions if it doesn't exist
        await sessions_collection.create_index("created_at", expireAfterSeconds=7 * 24 * 60 * 60)
        
        # Create TTL index for password reset tokens (expire after 1 hour)
        await password_reset_collection.create_index("created_at", expireAfterSeconds=60 * 60)
        
        # Create unique index for email in users collection
        await users_collection.create_index("email", unique=True)
        
        print("Database indexes initialized successfully")
    except Exception as e:
        print(f"ERROR initializing database indexes: {str(e)}")
        print("The application may not function correctly without database access")
