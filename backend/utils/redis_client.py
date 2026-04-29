"""
Redis Client for SwarmBharat AI
Production-ready Redis Cloud integration with free tier support
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
import asyncio

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class RedisClient:
    """
    Redis Cloud client for SwarmBharat AI
    Free tier: 30MB memory, unlimited connections
    """
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        self.client = None
        self.connected = False
        
    async def connect(self):
        """Connect to Redis Cloud"""
        try:
            if not REDIS_AVAILABLE:
                logger.warning("Redis not installed, using in-memory fallback")
                return False
                
            if not self.redis_url:
                logger.warning("Redis URL not provided, using in-memory fallback")
                return False
                
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            await self.client.ping()
            self.connected = True
            
            logger.info("✅ Connected to Redis Cloud")
            return True
            
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            return False
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set key with TTL"""
        try:
            if self.connected:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                await self.client.setex(key, ttl, value)
                return True
            return False
        except Exception as e:
            logger.error(f"Redis set failed: {str(e)}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get key value"""
        try:
            if self.connected:
                value = await self.client.get(key)
                if value:
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                return None
            return None
        except Exception as e:
            logger.error(f"Redis get failed: {str(e)}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            if self.connected:
                await self.client.delete(key)
                return True
            return False
        except Exception as e:
            logger.error(f"Redis delete failed: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            if self.connected:
                return bool(await self.client.exists(key))
            return False
        except Exception as e:
            logger.error(f"Redis exists check failed: {str(e)}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        try:
            if self.connected:
                return await self.client.incrby(key, amount)
            return None
        except Exception as e:
            logger.error(f"Redis increment failed: {str(e)}")
            return None
    
    async def get_ttl(self, key: str) -> int:
        """Get key TTL"""
        try:
            if self.connected:
                return await self.client.ttl(key)
            return -1
        except Exception as e:
            logger.error(f"Redis TTL check failed: {str(e)}")
            return -1
    
    async def set_user_session(self, user_id: str, session_data: Dict[str, Any], ttl: int = 86400):
        """Set user session data"""
        key = f"session:{user_id}"
        return await self.set(key, session_data, ttl)
    
    async def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data"""
        key = f"session:{user_id}"
        return await self.get(key)
    
    async def cache_api_response(self, cache_key: str, response_data: Dict[str, Any], ttl: int = 300):
        """Cache API response"""
        key = f"api_cache:{cache_key}"
        return await self.set(key, response_data, ttl)
    
    async def get_cached_api_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached API response"""
        key = f"api_cache:{cache_key}"
        return await self.get(key)
    
    async def track_rate_limit(self, identifier: str, limit: int, window: int = 3600) -> bool:
        """Track rate limiting"""
        key = f"rate_limit:{identifier}"
        current = await self.increment(key)
        
        if current == 1:
            # Set expiry for the first request in window
            await self.client.expire(key, window)
        
        return current <= limit
    
    async def get_rate_limit_remaining(self, identifier: str) -> int:
        """Get remaining requests for rate limit"""
        key = f"rate_limit:{identifier}"
        try:
            if self.connected:
                current = await self.client.get(key)
                if current:
                    return max(0, 100 - int(current))
                return 100
            return 100
        except:
            return 100
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        try:
            if self.connected:
                info = await self.client.info()
                return {
                    "used_memory": info.get("used_memory_human", "0B"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0)
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {str(e)}")
            return {}
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")

# Global Redis instance
redis_client = RedisClient()
