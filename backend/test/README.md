# Recipe Keeper Test Suite

This directory contains all test files for the Recipe Keeper backend.

## Test Files

### test_cache.py
**Purpose:** Test cache functionality without making any Gemini API calls

**Safe to run:** ✅ Yes - No API calls, no quota usage

**What it tests:**
- URL normalization for YouTube, TikTok, Instagram
- Cache key generation (SHA256 hashing)
- Cache set/get operations
- Redis connection health
- Cache statistics
- Cache invalidation
- Memory cache fallback

**Run:**
```bash
cd /Users/dmei/Documents/my-project-learning/recipe-keeper/backend
python3 test/test_cache.py
```

---

### test_thumbnail.py
**Purpose:** Test thumbnail extraction from video metadata for all URLs in test_urls.csv

**Safe to run:** ✅ Yes - Uses yt-dlp only, no Gemini API

**What it tests:**
- Video metadata extraction (yt-dlp)
- Thumbnail URL retrieval
- Video title extraction
- Tests all 5 URLs from test_urls.csv

**Run:**
```bash
cd /Users/dmei/Documents/my-project-learning/recipe-keeper/backend
python3 test/test_thumbnail.py
```

---

### test_extraction.py
**Purpose:** Full end-to-end recipe extraction test for all URLs in test_urls.csv

**Safe to run:** ⚠️ Uses Gemini API quota (~1-5 requests per test URL)

**What it tests:**
- Full API endpoint (`/api/extract-recipe`)
- Recipe extraction from all 5 test URLs
- Ingredient matching
- Instruction step extraction
- Platform detection

**Requirements:**
- Server must be running (`python3 main.py`)
- Test URLs defined in `test_urls.csv` (5 test cases)
- Gemini API quota available

**Run:**
```bash
# Terminal 1: Start server
cd /Users/dmei/Documents/my-project-learning/recipe-keeper/backend
python3 main.py

# Terminal 2: Run tests
cd /Users/dmei/Documents/my-project-learning/recipe-keeper/backend
python3 test/test_extraction.py
```

---

## Quick Start

```bash
# Navigate to backend directory
cd /Users/dmei/Documents/my-project-learning/recipe-keeper/backend

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY and REDIS_URL

# Run safe tests first (no API quota)
python3 test/test_cache.py
python3 test/test_thumbnail.py

# Then run extraction tests (uses API quota)
python3 test/test_extraction.py
```

---

## Documentation

For complete testing documentation, see:
- **[TESTING.md](../../TESTING.md)** - Full testing guide with detailed instructions
- **[CONFIGURATION.md](../../CONFIGURATION.md)** - Configuration reference

---

## Test Results

### Expected Output Indicators

**Success:**
- ✅ Green checkmarks
- All tests pass
- No errors or exceptions

**Partial Success:**
- ⚠️ Some tests pass, some fail
- Check error messages for details

**Failure:**
- ❌ Red X marks
- Check error messages
- See troubleshooting in TESTING.md

---

## Important Notes

1. **Cache tests are always safe** - They never use Gemini API quota
2. **Thumbnail tests are safe** - They only use yt-dlp, not Gemini API
3. **Extraction tests use quota** - Be mindful of the free tier limit (15-20 requests/day)
4. **Use cache to save quota** - Re-requesting the same URL hits cache (no API call)

---

*For troubleshooting and detailed usage, see [TESTING.md](../../TESTING.md)*
