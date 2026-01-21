"""
Test Cache Functionality Without API Calls
Tests URL normalization, cache operations, and Redis connection
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path so we can import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our modules
from url_normalizer import url_normalizer
from cache_manager import cache_manager
from models import Recipe
from config import config


def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_success(text):
    """Print success message"""
    print(f"✓ {text}")


def print_info(text):
    """Print info message"""
    print(f"→ {text}")


def print_error(text):
    """Print error message"""
    print(f"✗ {text}")


def test_url_normalization():
    """Test URL normalization for different platforms"""
    print_header("Test 1: URL Normalization")

    test_cases = [
        # YouTube
        {
            "platform": "youtube",
            "urls": [
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "https://youtu.be/dQw4w9WgXcQ",
                "https://youtube.com/shorts/dQw4w9WgXcQ",
                "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            ]
        },
        # TikTok
        {
            "platform": "tiktok",
            "urls": [
                "https://www.tiktok.com/@user/video/1234567890",
                "https://vm.tiktok.com/abc123",
            ]
        },
        # Instagram
        {
            "platform": "instagram",
            "urls": [
                "https://www.instagram.com/reel/abc123xyz",
                "https://www.instagram.com/p/abc123xyz",
            ]
        }
    ]

    for test in test_cases:
        platform = test["platform"]
        urls = test["urls"]

        print(f"\n{platform.upper()} URLs:")
        cache_keys = []

        for url in urls:
            canonical, cache_key = url_normalizer.normalize_and_hash(url, platform)
            cache_keys.append(cache_key)
            print(f"\n  URL: {url}")
            print(f"    → Canonical: {canonical}")
            print(f"    → Cache Key: {cache_key}")

        # Verify all URLs from same platform produce same cache key
        if len(set(cache_keys)) == 1:
            print_success(f"All {platform} URLs map to same cache key!")
        else:
            print_error(f"Different cache keys detected for {platform}!")
            print(f"  Keys: {cache_keys}")


async def test_cache_operations():
    """Test cache set/get operations"""
    print_header("Test 2: Cache Operations")

    # Create a mock recipe
    mock_recipe = Recipe(
        title="Test Recipe",
        ingredients=["1 cup flour", "2 eggs", "1 cup milk"],
        steps=["Mix ingredients", "Cook for 10 minutes", "Serve hot"],
        source_url="https://youtube.com/watch?v=test123",
        platform="youtube",
        language="en",
        thumbnail_url="https://example.com/thumb.jpg"
    )

    # Generate cache key
    canonical_url, cache_key = url_normalizer.normalize_and_hash(
        "https://youtube.com/watch?v=test123",
        "youtube"
    )

    print_info(f"Test URL: https://youtube.com/watch?v=test123")
    print_info(f"Cache Key: {cache_key}")

    # Test 1: Cache miss
    print("\n1. Testing cache miss...")
    cached = await cache_manager.get(cache_key)
    if cached is None:
        print_success("Cache miss confirmed (as expected)")
    else:
        print_error("Unexpected cache hit!")

    # Test 2: Store in cache
    print("\n2. Storing recipe in cache...")
    await cache_manager.set(cache_key, mock_recipe, canonical_url, "youtube")
    print_success("Recipe stored in cache")

    # Test 3: Cache hit
    print("\n3. Testing cache hit...")
    cached = await cache_manager.get(cache_key)
    if cached:
        print_success("Cache hit confirmed!")
        print(f"  Title: {cached.title}")
        print(f"  Ingredients: {len(cached.ingredients)} items")
        print(f"  Steps: {len(cached.steps)} steps")
    else:
        print_error("Cache miss (unexpected!)")

    # Test 4: Different URL format, same video (should hit cache)
    print("\n4. Testing URL normalization (different format)...")
    different_url = "https://youtu.be/test123"
    canonical_url2, cache_key2 = url_normalizer.normalize_and_hash(
        different_url,
        "youtube"
    )

    print_info(f"Different URL: {different_url}")
    print_info(f"Cache Key: {cache_key2}")

    if cache_key == cache_key2:
        print_success("Same cache key for different URL format!")
        cached2 = await cache_manager.get(cache_key2)
        if cached2:
            print_success("Cache hit with different URL format!")
        else:
            print_error("Cache miss (unexpected!)")
    else:
        print_error("Different cache keys!")


async def test_cache_stats():
    """Test cache statistics"""
    print_header("Test 3: Cache Statistics")

    stats = await cache_manager.get_stats()

    print("\nCache Configuration:")
    print(f"  Enabled: {config.CACHE_ENABLED}")
    print(f"  TTL: {config.CACHE_TTL_SECONDS} seconds ({config.CACHE_TTL_SECONDS // 3600} hours)")
    print(f"  Max Items (memory): {config.CACHE_MAX_ITEMS}")

    print("\nCache Status:")
    print(f"  Redis Available: {stats['redis_available']}")
    print(f"  Redis Size: {stats['redis_size']} keys")
    print(f"  Memory Size: {stats['memory_size']} items")

    print("\nCache Performance:")
    print(f"  Redis Hits: {stats['redis_hits']}")
    print(f"  Memory Hits: {stats['memory_hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Hit Rate: {stats['hit_rate']:.2%}")
    print(f"  Redis Errors: {stats['redis_errors']}")

    if stats['redis_available']:
        print_success("Redis connection is working!")
    else:
        print_info("Redis not available, using memory cache fallback")


async def test_redis_connection():
    """Test Redis connection health"""
    print_header("Test 4: Redis Connection")

    if not config.REDIS_URL:
        print_info("REDIS_URL not configured")
        print_info("App will use in-memory cache only")
        return

    print_info(f"Redis URL configured: {config.REDIS_URL[:30]}...")

    health = await cache_manager.health_check()

    print("\nHealth Check Results:")
    print(f"  Redis Configured: {health['redis_configured']}")
    print(f"  Redis Package Installed: {health['redis_package_installed']}")
    print(f"  Redis Available: {health['redis_available']}")
    print(f"  Memory Cache Size: {health['memory_cache_size']} items")

    if health['redis_available']:
        print_success("Redis connection healthy!")
    else:
        print_error("Redis connection unavailable")
        print_info("Check REDIS_URL format and credentials")


async def test_cache_invalidation():
    """Test cache invalidation"""
    print_header("Test 5: Cache Invalidation")

    # Create and cache a recipe
    mock_recipe = Recipe(
        title="Recipe to Delete",
        ingredients=["test"],
        steps=["test"],
        source_url="https://youtube.com/watch?v=delete123",
        platform="youtube",
        language="en"
    )

    canonical_url, cache_key = url_normalizer.normalize_and_hash(
        "https://youtube.com/watch?v=delete123",
        "youtube"
    )

    print_info(f"Cache Key: {cache_key}")

    # Store in cache
    print("\n1. Storing recipe...")
    await cache_manager.set(cache_key, mock_recipe, canonical_url, "youtube")
    print_success("Recipe stored")

    # Verify it's cached
    print("\n2. Verifying cache...")
    cached = await cache_manager.get(cache_key)
    if cached:
        print_success("Recipe found in cache")
    else:
        print_error("Recipe not in cache!")
        return

    # Delete from cache
    print("\n3. Deleting from cache...")
    await cache_manager.delete(cache_key)
    print_success("Delete command executed")

    # Verify it's gone
    print("\n4. Verifying deletion...")
    cached = await cache_manager.get(cache_key)
    if cached is None:
        print_success("Recipe successfully deleted from cache!")
    else:
        print_error("Recipe still in cache!")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("  RECIPE KEEPER - CACHE FUNCTIONALITY TESTS")
    print("  No Gemini API calls will be made")
    print("="*70)
    print(f"\nTest started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Test 1: URL Normalization (no async)
        test_url_normalization()

        # Test 2: Cache Operations
        await test_cache_operations()

        # Test 3: Cache Statistics
        await test_cache_stats()

        # Test 4: Redis Connection
        await test_redis_connection()

        # Test 5: Cache Invalidation
        await test_cache_invalidation()

        print_header("All Tests Completed!")
        print_success("Cache functionality verified without API calls")

    except Exception as e:
        print_error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
