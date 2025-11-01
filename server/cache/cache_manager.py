"""
Redis Cache Manager
===================
Caching layer for theories, quizzes, embeddings, and computed results.
Improves performance by reducing redundant LLM calls and database queries.
"""

import json
import pickle
from typing import Any, Optional, Dict, List
from datetime import timedelta
import redis.asyncio as aioredis
import redis

from config.settings import settings


class CacheManager:
    """
    Redis-based cache manager with async support
    """
    
    def __init__(self, redis_url: str = None):
        """
        Initialize cache manager
        
        Args:
            redis_url: Redis connection URL (uses settings if not provided)
        """
        # Build Redis URL from settings
        if redis_url is None:
            password_part = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
            redis_url = f"redis://{password_part}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        
        self.redis_url = redis_url
        self.default_ttl = settings.REDIS_TTL
        
        # Async client
        self.async_client: Optional[aioredis.Redis] = None
        
        # Sync client (for scripts)
        self.sync_client: Optional[redis.Redis] = None
        
        # Key prefixes for different data types
        self.THEORY_PREFIX = "theory:"
        self.QUIZ_PREFIX = "quiz:"
        self.EMBEDDING_PREFIX = "embedding:"
        self.PROFILE_PREFIX = "profile:"
        self.METRICS_PREFIX = "metrics:"
        self.CURRICULUM_PREFIX = "curriculum:"
    
    async def connect(self):
        """Establish async connection to Redis"""
        if self.async_client is None:
            self.async_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False  # We'll handle encoding manually
            )
            print("✅ Connected to Redis (async)")
    
    async def disconnect(self):
        """Close async connection"""
        if self.async_client:
            await self.async_client.close()
            self.async_client = None
            print("🔌 Disconnected from Redis (async)")
    
    def connect_sync(self):
        """Establish sync connection"""
        if self.sync_client is None:
            self.sync_client = redis.from_url(
                self.redis_url,
                decode_responses=False
            )
            print("✅ Connected to Redis (sync)")
    
    def disconnect_sync(self):
        """Close sync connection"""
        if self.sync_client:
            self.sync_client.close()
            self.sync_client = None
            print("🔌 Disconnected from Redis (sync)")
    
    # ==================== THEORY CACHING ====================
    
    async def cache_theory(
        self,
        module_name: str,
        topic_name: str,
        theory_content: str,
        ttl: int = None
    ) -> bool:
        """
        Cache generated theory content
        
        Args:
            module_name: Module name
            topic_name: Topic name
            theory_content: Theory markdown content
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            Success status
        """
        if not self.async_client:
            await self.connect()
        
        key = f"{self.THEORY_PREFIX}{module_name}:{topic_name}"
        ttl = ttl or self.default_ttl
        
        try:
            await self.async_client.setex(
                key,
                ttl,
                theory_content.encode('utf-8')
            )
            return True
        except Exception as e:
            print(f"❌ Error caching theory: {e}")
            return False
    
    async def get_theory(
        self,
        module_name: str,
        topic_name: str
    ) -> Optional[str]:
        """Get cached theory content"""
        if not self.async_client:
            await self.connect()
        
        key = f"{self.THEORY_PREFIX}{module_name}:{topic_name}"
        
        try:
            content = await self.async_client.get(key)
            if content:
                return content.decode('utf-8')
            return None
        except Exception as e:
            print(f"❌ Error getting theory: {e}")
            return None
    
    # ==================== QUIZ CACHING ====================
    
    async def cache_quiz(
        self,
        quiz_id: str,
        quiz_data: Dict[str, Any],
        ttl: int = None
    ) -> bool:
        """
        Cache generated quiz
        
        Args:
            quiz_id: Unique quiz identifier
            quiz_data: Quiz data dictionary
            ttl: Time-to-live in seconds
            
        Returns:
            Success status
        """
        if not self.async_client:
            await self.connect()
        
        key = f"{self.QUIZ_PREFIX}{quiz_id}"
        ttl = ttl or self.default_ttl
        
        try:
            # Serialize quiz data
            serialized = json.dumps(quiz_data).encode('utf-8')
            await self.async_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"❌ Error caching quiz: {e}")
            return False
    
    async def get_quiz(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """Get cached quiz"""
        if not self.async_client:
            await self.connect()
        
        key = f"{self.QUIZ_PREFIX}{quiz_id}"
        
        try:
            data = await self.async_client.get(key)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
        except Exception as e:
            print(f"❌ Error getting quiz: {e}")
            return None
    
    async def invalidate_quiz(self, quiz_id: str) -> bool:
        """Invalidate cached quiz"""
        if not self.async_client:
            await self.connect()
        
        key = f"{self.QUIZ_PREFIX}{quiz_id}"
        
        try:
            await self.async_client.delete(key)
            return True
        except Exception as e:
            print(f"❌ Error invalidating quiz: {e}")
            return False
    
    # ==================== EMBEDDING CACHING ====================
    
    async def cache_embedding(
        self,
        text: str,
        embedding: List[float],
        ttl: int = None
    ) -> bool:
        """
        Cache text embedding
        
        Args:
            text: Source text
            embedding: Embedding vector
            ttl: Time-to-live (default: 7 days for embeddings)
            
        Returns:
            Success status
        """
        if not self.async_client:
            await self.connect()
        
        # Use hash of text as key
        import hashlib
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        key = f"{self.EMBEDDING_PREFIX}{text_hash}"
        
        # Embeddings can be cached longer
        ttl = ttl or (7 * 24 * 60 * 60)  # 7 days
        
        try:
            # Use pickle for efficient float array storage
            serialized = pickle.dumps(embedding)
            await self.async_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"❌ Error caching embedding: {e}")
            return False
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding"""
        if not self.async_client:
            await self.connect()
        
        import hashlib
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        key = f"{self.EMBEDDING_PREFIX}{text_hash}"
        
        try:
            data = await self.async_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            print(f"❌ Error getting embedding: {e}")
            return None
    
    # ==================== STUDENT METRICS CACHING ====================
    
    async def cache_student_metrics(
        self,
        student_id: str,
        metrics: Dict[str, Any],
        ttl: int = 300  # 5 minutes for metrics
    ) -> bool:
        """Cache computed student performance metrics"""
        if not self.async_client:
            await self.connect()
        
        key = f"{self.METRICS_PREFIX}{student_id}"
        
        try:
            serialized = json.dumps(metrics).encode('utf-8')
            await self.async_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"❌ Error caching metrics: {e}")
            return False
    
    async def get_student_metrics(
        self,
        student_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached student metrics"""
        if not self.async_client:
            await self.connect()
        
        key = f"{self.METRICS_PREFIX}{student_id}"
        
        try:
            data = await self.async_client.get(key)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
        except Exception as e:
            print(f"❌ Error getting metrics: {e}")
            return None
    
    async def invalidate_student_metrics(self, student_id: str) -> bool:
        """Invalidate student metrics cache (after quiz submission)"""
        if not self.async_client:
            await self.connect()
        
        key = f"{self.METRICS_PREFIX}{student_id}"
        
        try:
            await self.async_client.delete(key)
            return True
        except Exception as e:
            print(f"❌ Error invalidating metrics: {e}")
            return False
    
    # ==================== CURRICULUM CACHING ====================
    
    async def cache_curriculum(
        self,
        curriculum_id: str,
        curriculum_data: Dict[str, Any],
        ttl: int = None
    ) -> bool:
        """Cache generated curriculum"""
        if not self.async_client:
            await self.connect()
        
        key = f"{self.CURRICULUM_PREFIX}{curriculum_id}"
        ttl = ttl or (24 * 60 * 60)  # 24 hours for curricula
        
        try:
            serialized = json.dumps(curriculum_data).encode('utf-8')
            await self.async_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"❌ Error caching curriculum: {e}")
            return False
    
    async def get_curriculum(
        self,
        curriculum_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached curriculum"""
        if not self.async_client:
            await self.connect()
        
        key = f"{self.CURRICULUM_PREFIX}{curriculum_id}"
        
        try:
            data = await self.async_client.get(key)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
        except Exception as e:
            print(f"❌ Error getting curriculum: {e}")
            return None
    
    # ==================== UTILITY METHODS ====================
    
    async def set_with_ttl(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> bool:
        """Generic set with TTL"""
        if not self.async_client:
            await self.connect()
        
        ttl = ttl or self.default_ttl
        
        try:
            # Auto-serialize based on type
            if isinstance(value, (dict, list)):
                value = json.dumps(value).encode('utf-8')
            elif isinstance(value, str):
                value = value.encode('utf-8')
            elif not isinstance(value, bytes):
                value = pickle.dumps(value)
            
            await self.async_client.setex(key, ttl, value)
            return True
        except Exception as e:
            print(f"❌ Error setting cache: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Generic get"""
        if not self.async_client:
            await self.connect()
        
        try:
            data = await self.async_client.get(key)
            if data:
                # Try JSON first, then pickle
                try:
                    return json.loads(data.decode('utf-8'))
                except:
                    try:
                        return pickle.loads(data)
                    except:
                        return data.decode('utf-8')
            return None
        except Exception as e:
            print(f"❌ Error getting cache: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        if not self.async_client:
            await self.connect()
        
        try:
            await self.async_client.delete(key)
            return True
        except Exception as e:
            print(f"❌ Error deleting cache: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        if not self.async_client:
            await self.connect()
        
        try:
            keys = await self.async_client.keys(pattern)
            if keys:
                return await self.async_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"❌ Error deleting pattern: {e}")
            return 0
    
    async def health_check(self) -> bool:
        """Check Redis connectivity"""
        try:
            if not self.async_client:
                await self.connect()
            await self.async_client.ping()
            return True
        except:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.async_client:
            await self.connect()
        
        try:
            info = await self.async_client.info()
            
            return {
                'connected': True,
                'used_memory': info.get('used_memory_human', 'N/A'),
                'total_keys': await self.async_client.dbsize(),
                'hit_rate': info.get('keyspace_hits', 0) / max(
                    info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1), 1
                ),
                'uptime_seconds': info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            return {'connected': False, 'error': str(e)}
    
    async def clear_all(self) -> bool:
        """Clear all cached data (use with caution!)"""
        if not self.async_client:
            await self.connect()
        
        try:
            await self.async_client.flushdb()
            print("🗑️ Cleared all cache data")
            return True
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
            return False


# Global cache instance
_cache_manager: Optional[CacheManager] = None


async def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
        await _cache_manager.connect()
    return _cache_manager


async def close_cache_manager():
    """Close global cache manager"""
    global _cache_manager
    if _cache_manager:
        await _cache_manager.disconnect()
        _cache_manager = None


if __name__ == "__main__":
    import asyncio
    
    async def test_cache():
        """Test cache manager"""
        print("🧪 Testing Cache Manager...")
        
        cache = CacheManager()
        await cache.connect()
        
        # Test health check
        is_healthy = await cache.health_check()
        print(f"Health check: {'✅ Passed' if is_healthy else '❌ Failed'}")
        
        if not is_healthy:
            print("⚠️  Redis not available. Please start Redis server.")
            return
        
        # Test theory caching
        print("\n📝 Testing theory cache...")
        await cache.cache_theory(
            "Module1",
            "Topic1",
            "# Theory Content\n\nThis is test theory content.",
            ttl=60
        )
        
        theory = await cache.get_theory("Module1", "Topic1")
        print(f"Retrieved theory: {theory[:50] if theory else 'None'}...")
        
        # Test quiz caching
        print("\n📊 Testing quiz cache...")
        quiz_data = {
            'quiz_id': 'test_quiz_001',
            'questions': [
                {'id': 'q1', 'question': 'Test question?'}
            ]
        }
        await cache.cache_quiz('test_quiz_001', quiz_data, ttl=60)
        
        cached_quiz = await cache.get_quiz('test_quiz_001')
        print(f"Retrieved quiz: {cached_quiz['quiz_id'] if cached_quiz else 'None'}")
        
        # Test embedding cache
        print("\n🧮 Testing embedding cache...")
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        await cache.cache_embedding("test text", test_embedding, ttl=60)
        
        cached_embedding = await cache.get_embedding("test text")
        print(f"Retrieved embedding: {cached_embedding}")
        
        # Get stats
        print("\n📈 Cache Statistics:")
        stats = await cache.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        await cache.disconnect()
        
        print("\n✅ Cache manager test complete!")
    
    asyncio.run(test_cache())
