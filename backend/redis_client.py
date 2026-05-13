"""
Redis Client for Caching
Provides async connection to Redis Cloud and helper functions for caching

IMPORTANT: Redis URL Format
---------------------------
Your Redis Cloud URL should be in this format:
redis://username:password@hostname:port

Example from your .env:
REDIS_URL=redis://default:YOUR_PASSWORD@redis-11736.c12.us-east-1-4.ec2.cloud.redislabs.com:11736

If you see connection errors, check:
1. URL starts with "redis://" (not just hostname)
2. Includes username (usually "default")
3. Includes password from Redis Cloud dashboard
4. Hostname and port are correct
"""

import os
import redis.asyncio as aioredis
import json
from typing import Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    logger.warning("⚠️  REDIS_URL not found in environment variables. Caching will be disabled.")
    logger.warning("⚠️  Please add REDIS_URL to your .env file or Railway environment variables")
    redis_client = None
elif not REDIS_URL.startswith("redis://"):
    logger.error(f"❌ REDIS_URL format is incorrect: {REDIS_URL}")
    logger.error("❌ Expected format: redis://username:password@hostname:port")
    logger.error("❌ Example: redis://default:password@redis-11736.c12.us-east-1-4.ec2.cloud.redislabs.com:11736")
    redis_client = None
else:
    # Mask password in logs for security
    masked_url = REDIS_URL.split('@')[1] if '@' in REDIS_URL else 'localhost'
    logger.info(f"🔗 Connecting to Redis at {masked_url}")

# Initialize async Redis client
redis_client: Optional[aioredis.Redis] = None

async def init_redis():
    """Initialize Redis connection on startup"""
    global redis_client

    if not REDIS_URL:
        logger.warning("⚠️  Redis disabled - no REDIS_URL configured")
        return

    if not REDIS_URL.startswith("redis://"):
        logger.error("❌ Redis disabled - REDIS_URL format is incorrect")
        logger.error("❌ Expected format: redis://username:password@hostname:port")
        return

    try:
        logger.info("🔄 Initializing Redis connection...")

        redis_client = await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,  # Auto-decode bytes to strings
            socket_timeout=5,       # 5s timeout for operations
            socket_connect_timeout=10,  # 10s timeout for initial connection
            retry_on_timeout=True,  # Retry once on timeout
            health_check_interval=30,  # Health check every 30s
        )

        # Test connection
        await redis_client.ping()
        logger.info("✅ Redis connected successfully!")

        # Log Redis info
        try:
            info = await redis_client.info("memory")
            used_memory_mb = info.get("used_memory", 0) / 1024 / 1024
            max_memory_mb = info.get("maxmemory", 0) / 1024 / 1024
            logger.info(f"📊 Redis memory: {used_memory_mb:.2f} MB used" + (f" / {max_memory_mb:.0f} MB max" if max_memory_mb > 0 else ""))

            # Log database info
            db_info = await redis_client.info("keyspace")
            if db_info:
                logger.info(f"📊 Redis keyspace: {db_info}")
        except Exception as e:
            logger.warning(f"⚠️  Could not fetch Redis info: {str(e)}")

    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {str(e)}")
        logger.warning("⚠️  Continuing without cache - all queries will hit MongoDB")
        logger.warning("⚠️  Check your REDIS_URL format and network connection")
        redis_client = None

async def close_redis():
    """Close Redis connection on shutdown"""
    global redis_client

    if redis_client:
        try:
            await redis_client.close()
            logger.info("✅ Redis connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing Redis: {str(e)}")

# ============================================================================
# CACHE HELPER FUNCTIONS
# ============================================================================

async def get_cached(key: str) -> Optional[Any]:
    """
    Get value from Redis cache

    Args:
        key: Cache key (e.g., "user:123abc")

    Returns:
        Cached value (parsed from JSON) or None if not found
    """
    if not redis_client:
        return None

    try:
        value = await redis_client.get(key)
        if value:
            logger.debug(f"✅ Cache HIT: {key}")
            return json.loads(value)
        else:
            logger.debug(f"❌ Cache MISS: {key}")
            return None
    except Exception as e:
        logger.error(f"❌ Redis GET error for key {key}: {str(e)}")
        return None

async def set_cached(key: str, value: Any, ttl_seconds: int = 300):
    """
    Set value in Redis cache with expiration

    Args:
        key: Cache key (e.g., "user:123abc")
        value: Value to cache (will be JSON-serialized)
        ttl_seconds: Time-to-live in seconds (default: 5 minutes)
    """
    if not redis_client:
        return

    try:
        serialized = json.dumps(value, default=str)  # default=str handles ObjectId, datetime
        await redis_client.setex(key, ttl_seconds, serialized)
        logger.debug(f"✅ Cache SET: {key} (TTL: {ttl_seconds}s)")
    except Exception as e:
        logger.error(f"❌ Redis SET error for key {key}: {str(e)}")

async def delete_cached(key: str):
    """
    Delete value from Redis cache

    Args:
        key: Cache key to delete
    """
    if not redis_client:
        return

    try:
        await redis_client.delete(key)
        logger.debug(f"✅ Cache DELETE: {key}")
    except Exception as e:
        logger.error(f"❌ Redis DELETE error for key {key}: {str(e)}")

async def delete_pattern(pattern: str):
    """
    Delete all keys matching a pattern

    Args:
        pattern: Redis key pattern (e.g., "user:*" deletes all user keys)
    """
    if not redis_client:
        return

    try:
        # Use scan_iter for memory efficiency (doesn't load all keys at once)
        deleted_count = 0
        async for key in redis_client.scan_iter(match=pattern, count=100):
            await redis_client.delete(key)
            deleted_count += 1

        if deleted_count > 0:
            logger.info(f"✅ Cache DELETE pattern: {pattern} ({deleted_count} keys)")
    except Exception as e:
        logger.error(f"❌ Redis DELETE pattern error for {pattern}: {str(e)}")

async def get_cache_stats():
    """
    Get Redis cache statistics

    Returns:
        Dict with memory usage, key count, hit rate, etc.
    """
    if not redis_client:
        return {"enabled": False, "message": "Redis not configured"}

    try:
        info = await redis_client.info("stats")
        memory_info = await redis_client.info("memory")
        server_info = await redis_client.info("server")

        # Calculate hit rate
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0

        return {
            "enabled": True,
            "keys": await redis_client.dbsize(),
            "memory_used_mb": round(memory_info.get("used_memory", 0) / 1024 / 1024, 2),
            "memory_peak_mb": round(memory_info.get("used_memory_peak", 0) / 1024 / 1024, 2),
            "memory_max_mb": round(memory_info.get("maxmemory", 0) / 1024 / 1024, 2) if memory_info.get("maxmemory", 0) > 0 else "unlimited",
            "hit_rate": round(hit_rate, 2),
            "keyspace_hits": hits,
            "keyspace_misses": misses,
            "total_connections": info.get("total_connections_received", 0),
            "ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
            "redis_version": server_info.get("redis_version", "unknown"),
            "uptime_days": round(server_info.get("uptime_in_seconds", 0) / 86400, 1)
        }
    except Exception as e:
        logger.error(f"❌ Error getting cache stats: {str(e)}")
        return {"enabled": False, "error": str(e)}

# ============================================================================
# TOKEN BLOCKLIST (logout / session invalidation)
# ============================================================================

async def blocklist_token(jti: str, ttl_seconds: int) -> bool:
    """
    Add a token JTI to the blocklist so it cannot be reused after logout.
    ttl_seconds should equal the token's remaining lifetime so Redis auto-expires the entry.
    Returns True on success, False if Redis is unavailable (fail open — do not block auth).
    """
    if not redis_client:
        logger.warning("⚠️  Redis unavailable — token blocklist skipped for JTI: %s", jti)
        return False
    try:
        key = f"blocklist:{jti}"
        await redis_client.setex(key, ttl_seconds, "1")
        logger.info("🔒 Token blocklisted: %s (TTL %ds)", jti, ttl_seconds)
        return True
    except Exception as e:
        logger.error("❌ Redis blocklist SET error for JTI %s: %s", jti, str(e))
        return False


async def is_token_blocklisted(jti: str) -> bool:
    """
    Returns True if the token JTI has been blocklisted (i.e. logged out).
    Returns False if Redis is unavailable (fail open — never block valid users on cache outage).
    """
    if not redis_client:
        return False
    try:
        key = f"blocklist:{jti}"
        result = await redis_client.exists(key)
        return bool(result)
    except Exception as e:
        logger.error("❌ Redis blocklist GET error for JTI %s: %s", jti, str(e))
        return False


# Export for use in other modules
__all__ = [
    "redis_client",
    "init_redis",
    "close_redis",
    "get_cached",
    "set_cached",
    "delete_cached",
    "delete_pattern",
    "get_cache_stats",
    "blocklist_token",
    "is_token_blocklisted",
]
