import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB connection string from environment variables
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

# Create a MongoDB client
client = AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]

# Collections
users_collection = database.users
sessions_collection = database.sessions
password_reset_collection = database.password_resets

# Initialize TTL index for sessions (expire after 7 days)
async def init_db():
    # Create TTL index for sessions if it doesn't exist
    await sessions_collection.create_index("created_at", expireAfterSeconds=7 * 24 * 60 * 60)
    
    # Create TTL index for password reset tokens (expire after 1 hour)
    await password_reset_collection.create_index("created_at", expireAfterSeconds=60 * 60)
    
    # Create unique index for email in users collection
    await users_collection.create_index("email", unique=True)
    
    print("Database indexes initialized")
