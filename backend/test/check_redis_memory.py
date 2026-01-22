"""
Check Redis memory usage and analyze overhead
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    print("Error: redis package not installed")
    print("Run: pip install redis")
    sys.exit(1)


async def check_redis_memory():
    """Check Redis memory usage and breakdown"""

    if not config.REDIS_URL:
        print("Error: REDIS_URL not configured in .env")
        sys.exit(1)

    print("Connecting to Redis...")
    print(f"URL: {config.REDIS_URL[:30]}...")
    print()

    try:
        # Connect to Redis
        client = redis.from_url(
            config.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )

        # Test connection
        await client.ping()
        print("✓ Connected to Redis")
        print()

        # Get memory info
        info = await client.info('memory')

        print("="*70)
        print("REDIS MEMORY USAGE")
        print("="*70)

        # Key metrics
        used_memory = info.get('used_memory', 0)
        used_memory_human = info.get('used_memory_human', 'N/A')
        used_memory_rss = info.get('used_memory_rss', 0)
        used_memory_peak = info.get('used_memory_peak', 0)
        used_memory_peak_human = info.get('used_memory_peak_human', 'N/A')
        mem_fragmentation_ratio = info.get('mem_fragmentation_ratio', 0)

        print(f"\nActual Memory Used:")
        print(f"  Used Memory:           {used_memory_human} ({used_memory:,} bytes)")
        print(f"  RSS (OS view):         {used_memory_rss:,} bytes")
        print(f"  Peak Memory:           {used_memory_peak_human} ({used_memory_peak:,} bytes)")
        print(f"  Fragmentation Ratio:   {mem_fragmentation_ratio:.2f}")

        # Get dataset size
        used_memory_dataset = info.get('used_memory_dataset', 0)
        used_memory_overhead = info.get('used_memory_overhead', 0)

        print(f"\nMemory Breakdown:")
        print(f"  Dataset (your data):   {used_memory_dataset:,} bytes")
        print(f"  Overhead (Redis):      {used_memory_overhead:,} bytes")

        overhead_percent = (used_memory_overhead / used_memory * 100) if used_memory > 0 else 0
        data_percent = (used_memory_dataset / used_memory * 100) if used_memory > 0 else 0

        print(f"\n  Data:                  {data_percent:.1f}% of total")
        print(f"  Overhead:              {overhead_percent:.1f}% of total")

        # Get key count and stats
        print()
        print("="*70)
        print("KEY STATISTICS")
        print("="*70)

        db_info = await client.info('keyspace')
        total_keys = 0

        if db_info:
            for db_key, db_stats in db_info.items():
                if db_key.startswith('db'):
                    keys = db_stats.get('keys', 0)
                    total_keys += keys
                    print(f"\n{db_key}: {keys} keys")
        else:
            print("\nNo keys in database")

        # List all recipe keys
        print()
        print("="*70)
        print("CACHED RECIPES")
        print("="*70)

        cursor = 0
        recipe_keys = []

        while True:
            cursor, keys = await client.scan(cursor, match="recipe:*", count=100)
            recipe_keys.extend(keys)
            if cursor == 0:
                break

        if recipe_keys:
            print(f"\nFound {len(recipe_keys)} cached recipe(s):")

            for i, key in enumerate(recipe_keys, 1):
                # Get key size
                value = await client.get(key)
                value_size = len(value.encode('utf-8')) if value else 0
                key_size = len(key.encode('utf-8'))
                ttl = await client.ttl(key)

                print(f"\n{i}. {key}")
                print(f"   Key size:    {key_size} bytes")
                print(f"   Value size:  {value_size:,} bytes")
                print(f"   TTL:         {ttl} seconds ({ttl/3600:.1f} hours)")

                # Show overhead
                redis_overhead = 96 + 64  # Object header + hash table entry
                total_with_overhead = key_size + value_size + redis_overhead
                print(f"   + Overhead:  ~{redis_overhead} bytes (Redis internal)")
                print(f"   Total:       ~{total_with_overhead:,} bytes")
        else:
            print("\nNo recipe keys found")

        # Memory efficiency
        print()
        print("="*70)
        print("MEMORY EFFICIENCY")
        print("="*70)

        if total_keys > 0 and used_memory_dataset > 0:
            avg_per_key = used_memory_dataset / total_keys
            print(f"\nAverage per key (data only): {avg_per_key:,.0f} bytes")

            if used_memory > 0:
                avg_total_per_key = used_memory / total_keys
                print(f"Average per key (with overhead): {avg_total_per_key:,.0f} bytes")
                print(f"Overhead multiplier: {avg_total_per_key/avg_per_key:.2f}x")

        print()
        print("="*70)
        print("EXPLANATION")
        print("="*70)
        print("""
Redis memory usage includes:
1. Your data (JSON strings)        - Small %
2. Keys and internal structures    - ~160 bytes/key
3. Base Redis instance             - 1-2 MB
4. Memory allocator overhead       - 2-3x actual size
5. Monitoring and stats            - Varies
6. Connection buffers              - Varies

For a single 336-byte entry, expect:
- Data: 336 bytes
- Key + overhead: ~160 bytes
- Base Redis: 1-2 MB
- Allocator fragmentation: 2-3 MB
- Total: 4-6 MB is normal!

As you add more entries, the overhead per entry decreases.
With 100 entries, you might use 8-10 MB (much better ratio).
""")

        await client.close()

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_redis_memory())
