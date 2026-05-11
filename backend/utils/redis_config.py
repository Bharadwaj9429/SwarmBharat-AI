"""
Redis Cloud Configuration for SwarmBharat AI
Handles caching, sessions, and rate limiting
"""

import redis.asyncio as redis
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pickle

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis Cloud manager for production caching"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = None
        self.key_prefix = "swarmbharat:"
    
    async def connect(self) -> bool:
        """Connect to Redis Cloud"""
        try:
            self.client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.client.ping()
            logger.info("✅ Connected to Redis Cloud")
            return True
            
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
    
    def _make_key(self, key: str) -> str:
        """Create namespaced key"""
        return f"{self.key_prefix}{key}"
    
    # User Session Management
    async def set_user_session(self, user_id: str, session_data: Dict[str, Any], ttl_hours: int = 24) -> bool:
        """Store user session"""
        try:
            key = self._make_key(f"session:{user_id}")
            await self.client.setex(
                key,
                ttl_hours * 3600,
                json.dumps(session_data, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set user session: {str(e)}")
            return False
    
    async def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user session"""
        try:
            key = self._make_key(f"session:{user_id}")
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get user session: {str(e)}")
            return None
    
    async def delete_user_session(self, user_id: str) -> bool:
        """Delete user session"""
        try:
            key = self._make_key(f"session:{user_id}")
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete user session: {str(e)}")
            return False
    
    # API Response Caching
    async def cache_api_response(self, cache_key: str, response_data: Any, ttl_minutes: int = 15) -> bool:
        """Cache API response"""
        try:
            key = self._make_key(f"api:{cache_key}")
            await self.client.setex(
                key,
                ttl_minutes * 60,
                json.dumps(response_data, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cache API response: {str(e)}")
            return False
    
    async def get_cached_api_response(self, cache_key: str) -> Optional[Any]:
        """Get cached API response"""
        try:
            key = self._make_key(f"api:{cache_key}")
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached API response: {str(e)}")
            return None
    
    # Government API Caching
    async def cache_government_data(self, service: str, identifier: str, data: Any, ttl_hours: int = 24) -> bool:
        """Cache government API data"""
        try:
            key = self._make_key(f"gov:{service}:{identifier}")
            await self.client.setex(
                key,
                ttl_hours * 3600,
                json.dumps(data, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cache government data: {str(e)}")
            return False
    
    async def get_cached_government_data(self, service: str, identifier: str) -> Optional[Any]:
        """Get cached government data"""
        try:
            key = self._make_key(f"gov:{service}:{identifier}")
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached government data: {str(e)}")
            return None
    
    # Rate Limiting
    async def check_rate_limit(self, identifier: str, limit: int, window_seconds: int) -> Dict[str, Any]:
        """Check rate limit for user/IP"""
        try:
            key = self._make_key(f"rate:{identifier}")
            current = await self.client.incr(key)
            
            if current == 1:
                await self.client.expire(key, window_seconds)
            
            ttl = await self.client.ttl(key)
            
            return {
                "allowed": current <= limit,
                "remaining": max(0, limit - current),
                "reset_time": datetime.now() + timedelta(seconds=ttl),
                "current_requests": current
            }
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            return {"allowed": True, "remaining": limit, "current_requests": 0}
    
    # User Preferences Caching
    async def cache_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Cache user preferences"""
        try:
            key = self._make_key(f"prefs:{user_id}")
            await self.client.set(
                key,
                json.dumps(preferences, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cache user preferences: {str(e)}")
            return False
    
    async def get_cached_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user preferences"""
        try:
            key = self._make_key(f"prefs:{user_id}")
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached user preferences: {str(e)}")
            return None
    
    # Real-time Debate Caching
    async def cache_debate_result(self, debate_id: str, result: Dict[str, Any], ttl_hours: int = 48) -> bool:
        """Cache debate result"""
        try:
            key = self._make_key(f"debate:{debate_id}")
            await self.client.setex(
                key,
                ttl_hours * 3600,
                json.dumps(result, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cache debate result: {str(e)}")
            return False
    
    async def get_cached_debate_result(self, debate_id: str) -> Optional[Dict[str, Any]]:
        """Get cached debate result"""
        try:
            key = self._make_key(f"debate:{debate_id}")
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached debate result: {str(e)}")
            return None
    
    # Analytics Caching
    async def increment_analytics_counter(self, metric: str, tags: Dict[str, str] = None) -> bool:
        """Increment analytics counter"""
        try:
            key_parts = [f"analytics:{metric}"]
            if tags:
                for k, v in sorted(tags.items()):
                    key_parts.append(f"{k}:{v}")
            
            key = self._make_key(":".join(key_parts))
            await self.client.incr(key)
            await self.client.expire(key, 86400)  # 24 hours
            return True
        except Exception as e:
            logger.error(f"Failed to increment analytics counter: {str(e)}")
            return False
    
    async def get_analytics_counters(self, metric: str, tags: Dict[str, str] = None) -> Dict[str, int]:
        """Get analytics counters"""
        try:
            key_parts = [f"analytics:{metric}"]
            if tags:
                for k, v in sorted(tags.items()):
                    key_parts.append(f"{k}:{v}")
            
            key = self._make_key(":".join(key_parts))
            value = await self.client.get(key)
            return {metric: int(value) if value else 0}
        except Exception as e:
            logger.error(f"Failed to get analytics counters: {str(e)}")
            return {metric: 0}
    
    # Cache Management
    async def clear_cache_pattern(self, pattern: str) -> int:
        """Clear cache keys matching pattern"""
        try:
            search_pattern = self._make_key(pattern)
            keys = await self.client.keys(search_pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear cache pattern: {str(e)}")
            return 0
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """Get Redis cache information"""
        try:
            info = await self.client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get cache info: {str(e)}")
            return {}
    
    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

# Global Redis manager instance
redis_manager = None

async def init_redis(redis_url: str) -> RedisManager:
    """Initialize Redis manager"""
    global redis_manager
    redis_manager = RedisManager(redis_url)
    await redis_manager.connect()
    return redis_manager

async def get_redis() -> RedisManager:
    """Get Redis manager instance"""
    return redis_manager
