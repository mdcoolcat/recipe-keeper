# Recipe Keeper - Testing Guide

Complete guide for running all tests manually, including cache tests, extraction tests, thumbnail tests, and more.

## Table of Contents
- [Quick Start](#quick-start)
- [Setup & Installation](#setup--installation)
- [Test Files Overview](#test-files-overview)
- [Running Tests](#running-tests)
- [Test Results Interpretation](#test-results-interpretation)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY and REDIS_URL

# 3. Run cache tests (no API calls, safe)
python3 test/test_cache.py

# 4. Run thumbnail test (uses yt-dlp, no Gemini API)
python3 test/test_thumbnail.py

# 5. Start server for full extraction tests
python3 main.py

# 6. In another terminal, run extraction tests (uses Gemini API)
python3 test/test_extraction.py
```

---

## Setup & Installation

### Prerequisites

- **Python 3.11+** (check with `python3 --version`)
- **pip** (Python package manager)
- **FFmpeg** (for video processing)
- **Internet connection** (for downloading videos)

### Install FFmpeg (if not installed)

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

### Install Python Dependencies

```bash
cd /Users/dmei/Documents/my-project-learning/recipe-keeper/backend

# Install all dependencies
pip install -r requirements.txt

# Or install specific dependencies
pip install fastapi uvicorn python-dotenv yt-dlp google-genai pydantic redis cachetools
```

### Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env file
nano .env  # or use any text editor
```

**Required variables:**
```bash
# Required: Get from https://aistudio.google.com/
GEMINI_API_KEY=your_actual_api_key_here

# Optional: For cache tests with Redis
REDIS_URL=redis://default:your_password@redis-16887.c1.us-west-2-2.ec2.cloud.redislabs.com:16887
```

---

## Test Files Overview

| Test File | Purpose | API Calls | Safe for Quota |
|-----------|---------|-----------|----------------|
| `test_cache.py` | Cache functionality | None | ✅ Yes (no API) |
| `test_thumbnail.py` | Thumbnail extraction (all test URLs) | None | ✅ Yes (no Gemini) |
| `test_extraction.py` | Full recipe extraction (all test URLs) | Gemini API | ⚠️ Uses quota |

### 1. test_cache.py

**Purpose:** Test cache functionality without making any Gemini API calls

**What it tests:**
- ✅ URL normalization for YouTube, TikTok, Instagram
- ✅ Cache key generation (SHA256 hashing)
- ✅ Cache set/get operations
- ✅ Redis connection health
- ✅ Cache statistics
- ✅ Cache invalidation
- ✅ Memory cache fallback

**Safe to run:** ✅ Yes - No API calls, no quota usage

**Location:** `backend/test/test_cache.py`

---

### 2. test_thumbnail.py

**Purpose:** Test thumbnail extraction from video metadata for all URLs in test_urls.csv

**What it tests:**
- ✅ Video metadata extraction (yt-dlp)
- ✅ Thumbnail URL retrieval
- ✅ Video title extraction
- ✅ Tests all URLs from test_urls.csv (5 test cases)

**Safe to run:** ✅ Yes - Uses yt-dlp only, no Gemini API

**Location:** `backend/test/test_thumbnail.py`

---

### 3. test_extraction.py

**Purpose:** Full end-to-end recipe extraction test

**What it tests:**
- ⚠️ Full API endpoint (`/api/extract-recipe`)
- ⚠️ Recipe extraction from multiple test URLs
- ⚠️ Ingredient matching
- ⚠️ Instruction step extraction
- ⚠️ Platform detection

**Safe to run:** ⚠️ Uses Gemini API quota (~1-5 requests per test)

**Requirements:**
- Server must be running (`python3 main.py`)
- Test URLs defined in `test_urls.csv`
- Gemini API quota available

**Location:** `backend/test/test_extraction.py`

---

## Running Tests

### Test 1: Cache Functionality (No API Calls)

**Recommended first test - completely safe!**

```bash
cd /Users/dmei/Documents/my-project-learning/recipe-keeper/backend

# Run cache tests
python3 test/test_cache.py
```

**Expected output:**
```
======================================================================
  RECIPE KEEPER - CACHE FUNCTIONALITY TESTS
  No Gemini API calls will be made
======================================================================

Test started at: 2026-01-21 10:30:45

======================================================================
  Test 1: URL Normalization
======================================================================

YOUTUBE URLs:

  URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
    → Canonical: youtube:dQw4w9WgXcQ
    → Cache Key: 8f3e4d5c6b7a8901

  URL: https://youtu.be/dQw4w9WgXcQ
    → Canonical: youtube:dQw4w9WgXcQ
    → Cache Key: 8f3e4d5c6b7a8901

✓ All youtube URLs map to same cache key!

======================================================================
  Test 2: Cache Operations
======================================================================

→ Test URL: https://youtube.com/watch?v=test123
→ Cache Key: abc123def456

1. Testing cache miss...
✓ Cache miss confirmed (as expected)

2. Storing recipe in cache...
✓ Cached recipe (Redis + Memory): abc123def456 [youtube]
✓ Recipe stored in cache

3. Testing cache hit...
✓ Cache HIT (Redis): abc123def456
✓ Cache hit confirmed!
  Title: Test Recipe
  Ingredients: 3 items
  Steps: 3 steps

4. Testing URL normalization (different format)...
→ Different URL: https://youtu.be/test123
→ Cache Key: abc123def456
✓ Same cache key for different URL format!
✓ Cache hit with different URL format!

======================================================================
  Test 3: Cache Statistics
======================================================================

Cache Configuration:
  Enabled: True
  TTL: 86400 seconds (24 hours)
  Max Items (memory): 1000

Cache Status:
  Redis Available: True
  Redis Size: 2 keys
  Memory Size: 2 items

Cache Performance:
  Redis Hits: 2
  Memory Hits: 0
  Misses: 1
  Hit Rate: 66.67%
  Redis Errors: 0

✓ Redis connection is working!

======================================================================
  Test 4: Redis Connection
======================================================================

→ Redis URL configured: redis://default:RTmWnPNtXP5...

Health Check Results:
  Redis Configured: True
  Redis Package Installed: True
  Redis Available: True
  Memory Cache Size: 2 items

✓ Redis connection healthy!

======================================================================
  Test 5: Cache Invalidation
======================================================================

→ Cache Key: xyz789abc012

1. Storing recipe...
✓ Cached recipe (Redis + Memory): xyz789abc012 [youtube]
✓ Recipe stored

2. Verifying cache...
✓ Cache HIT (Redis): xyz789abc012
✓ Recipe found in cache

3. Deleting from cache...
✓ Deleted cache entry: xyz789abc012
✓ Delete command executed

4. Verifying deletion...
○ Cache MISS: xyz789abc012
✓ Recipe successfully deleted from cache!

======================================================================
  All Tests Completed!
======================================================================
✓ Cache functionality verified without API calls
```

**What success looks like:**
- ✅ All tests show green checkmarks (✓)
- ✅ Redis connection shows "True" if configured
- ✅ No errors or exceptions
- ✅ Cache operations work correctly

**If Redis is not configured:**
- App will show: "Redis not configured, using memory cache only"
- Tests still pass, using in-memory fallback
- This is expected and OK for development

---

### Test 2: Thumbnail Extraction (No Gemini API)

**Tests video metadata extraction using yt-dlp**

```bash
cd /Users/dmei/Documents/my-project-learning/recipe-keeper/backend

# Run thumbnail test
python3 test/test_thumbnail.py
```

**Expected output:**
```
Testing: https://www.youtube.com/shorts/xe6gvF2nYoI

Title: Best Chocolate Chip Cookies | Easy Recipe
Thumbnail URL: https://i.ytimg.com/vi/xe6gvF2nYoI/maxresdefault.jpg

Thumbnail length: 59 chars
```

**What success looks like:**
- ✅ Video title is extracted
- ✅ Thumbnail URL is returned (starts with `https://i.ytimg.com/`)
- ✅ No errors or exceptions

**Common issues:**
- `yt-dlp` not installed: Run `pip install yt-dlp`
- Network error: Check internet connection
- Video unavailable: Try a different URL

---

### Test 3: Full Recipe Extraction (Uses Gemini API)

**⚠️ Warning: This test uses Gemini API quota!**

Each test URL will make 1-5 API calls depending on extraction method:
- Best case: 1 call (recipe in description)
- Worst case: 5 calls (video analysis)

**Prerequisites:**
1. Server must be running
2. Gemini API key configured in `.env`
3. API quota available

**Step 1: Start the server**

```bash
cd /Users/dmei/Documents/my-project-learning/recipe-keeper/backend

# Start server (leave this terminal running)
python3 main.py
```

**Expected output:**
```
✓ Redis connection successful
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Step 2: Run extraction tests (in a new terminal)**

```bash
cd /Users/dmei/Documents/my-project-learning/recipe-keeper/backend

# Run full extraction test suite
python3 test/test_extraction.py
```

**Expected output:**
```
Starting Recipe Extraction Tests
Reading test_urls.csv...
Found 5 test cases

Test 1/5
================================================================================
Testing: Chocolate Chip Cookies Recipe
URL: https://www.youtube.com/watch?v=example123
================================================================================

✅ Extraction succeeded!
Platform: YOUTUBE
Extracted Title: Best Chocolate Chip Cookies
Thumbnail: https://i.ytimg.com/vi/example123/maxresdefault.jpg

📝 Ingredients: 8/8 matched
Expected (8): ['2 cups flour', '1 cup butter', '1 cup sugar']...
Extracted (8): ['2 cups all-purpose flour', '1 cup butter softened', '1 cup sugar']...
✅ All ingredients matched!

👨‍🍳 Instructions: 5 steps extracted (expected 5)
First step: Preheat oven to 350°F
✅ Steps extracted successfully

Waiting 2 seconds before next test...

Test 2/5
...

================================================================================
TEST SUMMARY
================================================================================

Total: 4/5 tests passed (80.0%)

Results:
  ✅ PASS: Chocolate Chip Cookies Recipe
  ✅ PASS: Pasta Carbonara
  ✅ PASS: Fried Rice
  ❌ FAIL: Complex Recipe (quota exceeded)
  ✅ PASS: Simple Pancakes
```

**What success looks like:**
- ✅ Most tests pass (>70% pass rate is good)
- ✅ Recipes are extracted with ingredients and steps
- ✅ Thumbnails are retrieved
- ✅ Platform detection works

**Expected failures:**
- Quota exceeded: Normal if you hit daily limit
- Timeout: Some videos take longer to process
- No recipe found: Some videos don't have recipes

---

### Test 4: Manual API Test (Single Request)

**Test a single URL without running full test suite**

```bash
# Make sure server is running first
cd /Users/dmei/Documents/my-project-learning/recipe-keeper/backend
python3 main.py

# In another terminal, test with curl
curl -X POST http://localhost:8000/api/extract-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "use_cache": true}'
```

**Expected response:**
```json
{
  "success": true,
  "platform": "youtube",
  "recipe": {
    "title": "Chocolate Chip Cookies",
    "ingredients": [
      "2 cups flour",
      "1 cup butter",
      "1 cup sugar"
    ],
    "steps": [
      "Preheat oven to 350°F",
      "Mix dry ingredients",
      "Cream butter and sugar"
    ],
    "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "platform": "youtube",
    "language": "en",
    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
  },
  "from_cache": false,
  "cached_at": null
}
```

**To test cache hit (same URL again):**
```bash
# Run the same curl command again immediately
curl -X POST http://localhost:8000/api/extract-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtu.be/dQw4w9WgXcQ", "use_cache": true}'
```

**Expected response (cached):**
```json
{
  "success": true,
  "platform": "youtube",
  "recipe": { ... },
  "from_cache": true,
  "cached_at": "2026-01-21T10:35:42.123456"
}
```

Note: `from_cache: true` indicates cache hit!

---

### Test 5: Cache Statistics

**Check cache performance without making API calls**

```bash
# Server must be running
curl http://localhost:8000/api/cache/stats
```

**Expected response:**
```json
{
  "enabled": true,
  "redis_available": true,
  "redis_size": 5,
  "memory_size": 5,
  "redis_hits": 12,
  "memory_hits": 3,
  "total_misses": 8,
  "hit_rate": 0.652,
  "redis_errors": 0,
  "ttl_seconds": 86400
}
```

**What the numbers mean:**
- `redis_available: true` - Redis connection working
- `redis_size: 5` - 5 recipes cached in Redis
- `redis_hits: 12` - 12 requests served from Redis
- `hit_rate: 0.652` - 65.2% of requests hit cache
- `ttl_seconds: 86400` - Cache expires after 24 hours

---

### Test 6: Health Check

**Verify server is running**

```bash
curl http://localhost:8000/api/health
```

**Expected response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

**Or use HEAD request (UptimeRobot compatible):**
```bash
curl -I http://localhost:8000/api/health
```

**Expected response:**
```
HTTP/1.1 200 OK
content-type: application/json
...
```

---

## Test Results Interpretation

### Cache Test Results

**All tests pass (✅):**
- Cache is working correctly
- Redis connection healthy
- URL normalization working
- Ready for production

**Some tests fail (❌):**
- Check Redis connection if Test 4 fails
- Check `.env` file for correct `REDIS_URL`
- App will fall back to memory cache (still works)

**Redis unavailable (⚠️):**
- Tests still pass with memory cache
- Expected if `REDIS_URL` not configured
- Production should have Redis for persistence

---

### Thumbnail Test Results

**Success:**
- Thumbnail URL starts with `https://i.ytimg.com/`
- Title is extracted correctly
- No errors

**Failure:**
- Check internet connection
- Try different video URL
- Verify `yt-dlp` is installed: `pip install yt-dlp`
- Update `yt-dlp`: `pip install --upgrade yt-dlp`

---

### Extraction Test Results

**Good pass rate (>70%):**
- Recipe extraction working well
- API integration functional
- Cache should improve this over time

**Low pass rate (<50%):**
- Check Gemini API key in `.env`
- Verify API quota at https://aistudio.google.com/
- Check test URLs in `test_urls.csv`
- Some test URLs may be outdated

**Common errors:**

| Error | Cause | Solution |
|-------|-------|----------|
| `QUOTA_EXCEEDED` | Hit daily API limit | Wait until midnight PT or upgrade |
| `TIMEOUT` | Video too long to process | Increase timeout or use shorter video |
| `No recipe found` | Video doesn't contain recipe | Expected for non-recipe videos |
| `Connection refused` | Server not running | Start server with `python3 main.py` |

---

## Troubleshooting

### Dependencies Not Installed

**Error:**
```
ModuleNotFoundError: No module named 'cachetools'
```

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

---

### Redis Connection Failed

**Error in test output:**
```
✗ Redis connection failed: Connection refused
Falling back to in-memory cache only
```

**Causes:**
1. `REDIS_URL` not configured
2. Wrong password in `REDIS_URL`
3. Redis Cloud endpoint unreachable

**Solution:**
```bash
# Check .env file
cat .env | grep REDIS_URL

# Verify format
REDIS_URL=redis://default:PASSWORD@redis-16887.c1.us-west-2-2.ec2.cloud.redislabs.com:16887

# Test connection manually (requires redis-cli)
redis-cli -u $REDIS_URL ping
# Expected: PONG
```

**Note:** App still works with memory cache if Redis fails

---

### Server Not Running

**Error:**
```
requests.exceptions.ConnectionError: Connection refused
```

**Solution:**
```bash
# Make sure server is running
cd backend
python3 main.py

# Server should show:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### Gemini API Quota Exceeded

**Error:**
```
⚠️ Gemini API quota exceeded. The free tier limit is ~15-20 requests/day.
```

**Solutions:**

**Option 1: Wait for quota reset**
- Quota resets at midnight Pacific Time
- Check current quota: https://aistudio.google.com/apikey

**Option 2: Use cache**
- Re-request previously extracted recipes (cache hit = no API call)
- Check cache stats: `curl http://localhost:8000/api/cache/stats`

**Option 3: Upgrade to paid tier**
- Cost: ~$0.001 per extraction
- Setup: https://aistudio.google.com/
- Free tier: ~15-20 requests/day
- Paid tier: Virtually unlimited

---

### Python Command Not Found

**Error:**
```
python: command not found
```

**Solution:**
Use `python3` instead:
```bash
python3 test_cache.py
python3 main.py
```

**Or create alias:**
```bash
alias python=python3
```

---

### FFmpeg Not Installed

**Error:**
```
ffmpeg: command not found
```

**Solution:**

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Verify:**
```bash
ffmpeg -version
```

---

### Port Already in Use

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**

**Find process using port 8000:**
```bash
lsof -i :8000
```

**Kill the process:**
```bash
kill -9 <PID>
```

**Or use different port:**
```bash
# Edit .env
PORT=8001

# Restart server
python3 main.py
```

---

## Test Cheat Sheet

### Quick Commands

```bash
# Setup (one time)
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# Cache test (safe, no API calls)
python3 test/test_cache.py

# Thumbnail test (safe, no Gemini API)
python3 test/test_thumbnail.py

# Start server
python3 main.py

# Full extraction test (uses API quota)
python3 test/test_extraction.py

# Manual API test
curl -X POST http://localhost:8000/api/extract-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "YOUR_VIDEO_URL"}'

# Cache stats
curl http://localhost:8000/api/cache/stats

# Health check
curl http://localhost:8000/api/health
```

---

## Test Recommendations

### Before Deploying to Production

1. ✅ Run `test_cache.py` - Verify cache works
2. ✅ Run `test_thumbnail.py` - Verify video processing
3. ✅ Test 1-2 URLs manually - Verify end-to-end flow
4. ✅ Check cache stats - Verify Redis connection
5. ✅ Check health endpoint - Verify server starts

### After Deploying to Production

1. ✅ Test production URL with curl
2. ✅ Verify cache works in production
3. ✅ Check logs for errors
4. ✅ Monitor cache hit rate (should improve over time)
5. ✅ Set up UptimeRobot monitoring

### During Development

1. ✅ Use `test_cache.py` frequently (no quota usage)
2. ⚠️ Use `test_extraction.py` sparingly (uses quota)
3. ✅ Test with cached URLs when possible
4. ✅ Monitor API quota: https://aistudio.google.com/

---

## Test Files Summary

| File | Location | API Calls | Quota Safe |
|------|----------|-----------|------------|
| Cache test | `backend/test/test_cache.py` | 0 | ✅ Yes |
| Thumbnail test | `backend/test/test_thumbnail.py` | 0 (yt-dlp only) | ✅ Yes |
| Extraction test | `backend/test/test_extraction.py` | 1-5 per URL | ⚠️ No |
| Test URLs | `test_urls.csv` | N/A | N/A |

---

## Support

- **Gemini API Issues:** https://ai.google.dev/
- **Redis Issues:** https://redis.com/cloud/
- **yt-dlp Issues:** https://github.com/yt-dlp/yt-dlp
- **FastAPI Docs:** https://fastapi.tiangolo.com/

---

*Last updated: 2026-01-21*
