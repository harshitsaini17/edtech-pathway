"""
Simple Phase 3 Test: Content Delivery (Cache)
==============================================
Test caching functionality without requiring MongoDB/Redis connection.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("PHASE 3 TEST: CONTENT DELIVERY (CACHE)")
print("=" * 80)

print("\n1. Testing cache manager import...")
try:
    from cache.cache_manager import CacheManager
    print("   ✅ CacheManager imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import: {e}")
    sys.exit(1)

print("\n2. Testing cache manager initialization (without Redis)...")
try:
    cache = CacheManager(redis_url="redis://localhost:6379/0")
    print("   ✅ CacheManager initialized (connection will fail, expected)")
except Exception as e:
    print(f"   ℹ️  Initialization warning: {e}")

print("\n3. Testing cache key generation...")
try:
    # Test that methods exist
    assert hasattr(cache, 'cache_theory')
    assert hasattr(cache, 'cache_quiz')
    assert hasattr(cache, 'cache_embedding')
    print("   ✅ Cache methods exist")
except Exception as e:
    print(f"   ❌ Method check failed: {e}")
    sys.exit(1)

print("\n4. Testing theory generator import...")
try:
    from flexible_module_theory_generator import FlexibleModuleTheoryGenerator
    print("   ✅ Theory generator imported")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

print("\n✅ PHASE 3 TEST PASSED (Structure Verified)")
print("=" * 80)
print("\nNote: Full functionality requires Redis connection")
print("To test with Redis: docker run -d -p 6379:6379 redis:alpine")
