# Recipe Keeper - Configuration & Tools Documentation

## Table of Contents
- [System Architecture](#system-architecture)
- [Tools & Frameworks](#tools--frameworks)
- [Configuration Reference](#configuration-reference)
- [LLM Model Configuration](#llm-model-configuration)
- [Cache Configuration](#cache-configuration)
- [Video Processing Configuration](#video-processing-configuration)
- [Deployment Configuration](#deployment-configuration)
- [Where to Change Configs](#where-to-change-configs)

---

## System Architecture

```
┌─────────────────┐
│   User (iOS)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Server │ ◄──── UptimeRobot (monitoring)
│  (Render.com)   │
└────────┬────────┘
         │
         ├──► Redis Cloud (cache)
         │
         ├──► yt-dlp (video download)
         │
         └──► Gemini 2.0 Flash (AI extraction)
```

---

## Tools & Frameworks

### Backend Framework
| Tool | Version | Purpose | Configuration Location |
|------|---------|---------|----------------------|
| **FastAPI** | 0.115+ | Modern async Python web framework | `backend/main.py` |
| **Uvicorn** | 0.32+ | ASGI server for FastAPI | `backend/main.py:183-188` |
| **Python** | 3.11+ | Programming language | `backend/Dockerfile:1` |
| **Pydantic** | 2.10+ | Data validation & serialization | `backend/models.py` |

**Where to configure:**
- Server host/port: `backend/.env` → `HOST`, `PORT`
- CORS origins: `backend/.env` → `CORS_ORIGINS`
- API docs: Auto-generated at `/docs` and `/redoc`

---

### LLM / AI Model
| Component | Value | Purpose |
|-----------|-------|---------|
| **Model** | `gemini-2.0-flash` | Multimodal AI for recipe extraction |
| **Provider** | Google AI Studio | LLM API provider |
| **Library** | `google-genai` 1.0+ | Python SDK for Gemini API |
| **API Key** | Environment variable | Authentication |
| **Free Tier** | ~15-20 requests/day | Quota limit |
| **Paid Cost** | ~$0.075 per 1M tokens | ~$0.001 per extraction |

**Where configured:**
- Model ID: `backend/recipe_extractor.py:18`
  ```python
  model = genai.GenerativeModel("gemini-2.0-flash")
  ```
- API Key: `backend/.env` → `GEMINI_API_KEY`
- Get API Key: https://aistudio.google.com/

**Usage:**
1. Text extraction from video descriptions/comments
2. Video frame analysis (multimodal capability)
3. Recipe parsing and structuring

**To change model:**
```python
# backend/recipe_extractor.py line 18
model = genai.GenerativeModel("gemini-2.0-flash")  # Current
model = genai.GenerativeModel("gemini-1.5-pro")     # Alternative (more capable, slower)
model = genai.GenerativeModel("gemini-1.5-flash")   # Alternative (older version)
```

---

### Video Processing
| Tool | Version | Purpose | Configuration |
|------|---------|---------|--------------|
| **yt-dlp** | 2024.3.10+ | Download & extract video metadata | `backend/video_processor.py` |
| **FFmpeg** | Latest | Video/audio processing | Installed in Dockerfile |
| **Deno** | Latest | JavaScript runtime (for YouTube) | Installed in Dockerfile |

**Supported Platforms:**
- YouTube (including Shorts)
- TikTok
- Instagram (Reels)

**Where configured:**
- Download settings: `backend/.env`
  - `MAX_VIDEO_SIZE_MB` (default: 100)
  - `VIDEO_DOWNLOAD_TIMEOUT` (default: 60 seconds)
  - `TEMP_DIR` (default: `/tmp/recipe-keeper`)

**Platform Detection:**
- Logic: `backend/platform_detector.py`
- URL patterns for each platform

**To change video settings:**
```bash
# .env file
MAX_VIDEO_SIZE_MB=200           # Allow larger videos
VIDEO_DOWNLOAD_TIMEOUT=120      # Longer timeout
TEMP_DIR=/custom/temp/path      # Custom temp directory
```

---

### Caching Layer
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Primary Cache** | Redis Cloud | Persistent cache across restarts |
| **Fallback Cache** | cachetools (TTLCache) | In-memory cache if Redis fails |
| **Library** | `redis` 5.0+ | Async Redis client |
| **Cache Library** | `cachetools` 5.3+ | In-memory TTL cache |

**Architecture:**
```
Request → URL Normalizer → SHA256 Cache Key
                              ↓
                        Check Redis
                        ├─ Hit → Return cached recipe
                        ├─ Miss → Check Memory
                        │         ├─ Hit → Return cached
                        │         └─ Miss → Extract recipe
                        └─ Error → Fallback to Memory
```

**Where configured:**
- Cache Manager: `backend/cache_manager.py`
- URL Normalizer: `backend/url_normalizer.py`
- Config: `backend/.env`
  - `CACHE_ENABLED` (default: true)
  - `CACHE_TTL_SECONDS` (default: 86400 = 24 hours)
  - `CACHE_MAX_ITEMS` (default: 1000)
  - `REDIS_URL` (Redis Cloud connection string)

**Redis Cloud Setup:**
- Provider: Redis Cloud (managed service)
- Endpoint: `redis-16887.c1.us-west-2-2.ec2.cloud.redislabs.com:16887`
- Free tier: 30MB (~30,000 cached recipes)

---

### Deployment Platform
| Component | Value | Purpose |
|-----------|-------|---------|
| **Platform** | Render.com | Cloud hosting |
| **Plan** | Free tier | 512MB RAM, 0.1 CPU |
| **Container** | Docker | Containerization |
| **Base Image** | `python:3.11-slim` | Lightweight Python image |
| **URL** | recipe-keeper-api-8cxl.onrender.com | Production endpoint |

**Render Configuration:**
- Config file: `backend/render.yaml`
- Dockerfile: `backend/Dockerfile`
- Auto-deploy: Triggered by git push to `main` branch

**Free Tier Limitations:**
- Spins down after 15 min inactivity
- Cold start: ~1 minute
- Ephemeral disk (lost on restart, but Redis persists)
- 750 hours/month compute time

**Where configured:**
- Service settings: `backend/render.yaml`
- Environment variables: Render dashboard → Environment tab
- Build settings: `backend/Dockerfile`

---

### Monitoring
| Tool | Purpose | Configuration |
|------|---------|--------------|
| **UptimeRobot** | Uptime monitoring | External service |
| **Health Check** | `/api/health` endpoint | `backend/main.py:45-48` |

**UptimeRobot Setup:**
- URL: https://uptimerobot.com/
- Monitor: `https://recipe-keeper-api-8cxl.onrender.com/api/health`
- Interval: 5 minutes
- Method: HEAD (free tier compatible)
- Benefits:
  - Email alerts on downtime
  - Keeps Render service awake (< 15 min timeout)

**Health Endpoints:**
- `GET /api/health` - Basic health check
- `HEAD /api/health` - UptimeRobot compatible
- `GET /api/cache/stats` - Cache health & statistics

---

### iOS App (Planned)
| Component | Technology | Status |
|-----------|-----------|--------|
| **UI Framework** | SwiftUI | Planned |
| **Language** | Swift | Planned |
| **HTTP Client** | URLSession | Planned |
| **Share Extension** | iOS Share Sheet | Planned |
| **Local Storage** | Core Data | Planned |

**Not yet implemented**

---

## Configuration Reference

### Environment Variables

All configurations are managed through environment variables:

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `GEMINI_API_KEY` | string | - | Gemini API key | ✓ Yes |
| `REDIS_URL` | string | None | Redis connection URL | Optional |
| `HOST` | string | `0.0.0.0` | Server host | No |
| `PORT` | integer | `8000` | Server port | No |
| `CORS_ORIGINS` | string | `*` | Allowed CORS origins (comma-separated) | No |
| `TEMP_DIR` | string | `/tmp/recipe-keeper` | Temporary file storage | No |
| `MAX_VIDEO_SIZE_MB` | integer | `100` | Max video download size | No |
| `VIDEO_DOWNLOAD_TIMEOUT` | integer | `60` | Video download timeout (seconds) | No |
| `CACHE_ENABLED` | boolean | `true` | Enable/disable caching | No |
| `CACHE_TTL_SECONDS` | integer | `86400` | Cache TTL (24 hours) | No |
| `CACHE_MAX_ITEMS` | integer | `1000` | In-memory cache max items | No |

---

## LLM Model Configuration

### Current Model: Gemini 2.0 Flash

**Location:** `backend/recipe_extractor.py:18`

```python
model = genai.GenerativeModel("gemini-2.0-flash")
```

**Capabilities:**
- Text analysis (descriptions, comments)
- Video frame analysis (multimodal)
- Recipe extraction and structuring
- JSON output formatting

**API Key Configuration:**
1. Get API key from: https://aistudio.google.com/
2. Add to `.env` file:
   ```bash
   GEMINI_API_KEY=your_api_key_here
   ```
3. For production (Render): Add to Environment tab in dashboard

**Quota Management:**
- Free tier: ~15-20 requests/day
- Resets: Midnight Pacific Time
- Monitor: https://aistudio.google.com/apikey
- Upgrade: Pay-as-you-go (~$0.001 per extraction)

**To Change Model:**
```python
# More capable but slower
model = genai.GenerativeModel("gemini-1.5-pro")

# Older flash version
model = genai.GenerativeModel("gemini-1.5-flash")

# Custom configuration
model = genai.GenerativeModel(
    "gemini-2.0-flash",
    generation_config={
        "temperature": 0.7,
        "top_p": 0.95,
        "max_output_tokens": 8192,
    }
)
```

---

## Cache Configuration

### TTL (Time To Live)

**Current:** 24 hours (86400 seconds)

**Location:** `backend/.env` line 20
```bash
CACHE_TTL_SECONDS=86400
```

**Why 24 hours?**
- Matches Gemini quota reset cycle
- Balances freshness vs API savings
- Handles recipe updates gracefully

**To change:**
```bash
# 12 hours (fresher data, more API calls)
CACHE_TTL_SECONDS=43200

# 48 hours (less API calls, staler data)
CACHE_TTL_SECONDS=172800

# 7 days (maximum savings)
CACHE_TTL_SECONDS=604800
```

### Cache Size

**In-memory cache:** 1000 items max

**Location:** `backend/.env` line 21
```bash
CACHE_MAX_ITEMS=1000
```

**Redis cache:** No hard limit (depends on Redis Cloud plan)
- Free tier: 30MB storage
- Estimated: ~30,000 recipes at ~1KB each

**To change:**
```bash
# Smaller (less memory, more evictions)
CACHE_MAX_ITEMS=500

# Larger (more memory, fewer evictions)
CACHE_MAX_ITEMS=5000
```

### Cache Strategy

**URL Normalization:**
- Extract platform-specific video ID
- Generate SHA256 hash (first 16 chars)
- Different URL formats → same cache key

**Examples:**
```
https://youtube.com/watch?v=abc123    → youtube:abc123 → cache_key: f3e4d5c6b7a89012
https://youtu.be/abc123               → youtube:abc123 → cache_key: f3e4d5c6b7a89012
https://youtube.com/shorts/abc123     → youtube:abc123 → cache_key: f3e4d5c6b7a89012
```

**Cache Invalidation:**
- Automatic: TTL expiration (24h)
- Manual: `DELETE /api/cache/{cache_key}`
- Full clear: `DELETE /api/cache`
- Bypass: `POST /api/extract-recipe` with `use_cache: false`

### Redis Connection

**Format:**
```bash
REDIS_URL=redis://[username]:[password]@host:port
```

**Current setup:**
```bash
REDIS_URL=redis://default:RTmWnPNtXP5kAwnjNPElFeX314wL3LRM@redis-16887.c1.us-west-2-2.ec2.cloud.redislabs.com:16887
```

**Components:**
- Protocol: `redis://`
- Username: `default` (Redis Cloud default)
- Password: Your Redis Cloud password
- Host: `redis-16887.c1.us-west-2-2.ec2.cloud.redislabs.com`
- Port: `16887`

**Connection Handling:**
- Timeout: 5 seconds for connect and operations
- Retry: Attempts reconnection on failure
- Fallback: Uses in-memory cache if Redis unavailable

---

## Video Processing Configuration

### Download Limits

**Location:** `backend/.env`

```bash
MAX_VIDEO_SIZE_MB=100        # Max download size
VIDEO_DOWNLOAD_TIMEOUT=60    # Timeout in seconds
TEMP_DIR=/tmp/recipe-keeper  # Temporary storage
```

**To change:**
```bash
# Allow larger videos (may hit Render limits)
MAX_VIDEO_SIZE_MB=200

# Longer timeout for slow connections
VIDEO_DOWNLOAD_TIMEOUT=120

# Custom temp directory (must exist and be writable)
TEMP_DIR=/custom/path
```

### yt-dlp Configuration

**Location:** `backend/video_processor.py`

**Current options:**
```python
ydl_opts = {
    'format': 'best[ext=mp4]/best',
    'outtmpl': f'{temp_dir}/%(id)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'max_filesize': config.MAX_VIDEO_SIZE_MB * 1024 * 1024,
}
```

**To customize (edit `video_processor.py`):**
```python
# Download audio only
'format': 'bestaudio/best'

# Limit resolution
'format': 'best[height<=720]'

# Add cookies for authentication
'cookiefile': '/path/to/cookies.txt'

# Use proxy
'proxy': 'http://proxy-server:port'
```

### Platform Support

**Configured in:** `backend/platform_detector.py`

**URL Patterns:**
- YouTube: `youtube.com`, `youtu.be`, `m.youtube.com`
- TikTok: `tiktok.com`, `vm.tiktok.com`
- Instagram: `instagram.com`

**To add new platform:**
1. Add detection pattern in `platform_detector.py`
2. Add URL normalizer in `url_normalizer.py`
3. Test with platform URLs

---

## Deployment Configuration

### Local Development

**Start server:**
```bash
cd backend
python main.py
```

**Configuration:**
- Uses `.env` file in backend directory
- Runs on `http://localhost:8000`
- Hot reload: Not enabled (restart required)

### Production (Render)

**Deployment trigger:**
```bash
git add .
git commit -m "Your changes"
git push origin main
```

**Configuration files:**
1. `backend/render.yaml` - Service definition
2. `backend/Dockerfile` - Container build
3. Render Dashboard - Environment variables

**Environment variables (Render Dashboard):**
1. Go to: https://dashboard.render.com
2. Select: recipe-keeper-api
3. Tab: Environment
4. Add/Edit variables
5. Save Changes → Triggers auto-deploy

**Required in Render:**
- `GEMINI_API_KEY` (mark as secret)
- `REDIS_URL` (mark as secret)

**Auto-configured by Render:**
- `PORT` (set by Render, do not override)

### Docker Build

**Location:** `backend/Dockerfile`

**Base image:**
```dockerfile
FROM python:3.11-slim
```

**System dependencies:**
- `ffmpeg` - Video processing
- `curl` - Downloads
- `git` - Version control
- `unzip` - Archives
- `deno` - JavaScript runtime

**To modify Dockerfile:**
```dockerfile
# Add system package
RUN apt-get install -y new-package

# Change Python version
FROM python:3.12-slim

# Add build step
RUN some-build-command
```

---

## Where to Change Configs

### Quick Reference Table

| What to Change | Location | Restart Required |
|----------------|----------|------------------|
| **LLM Model** | `backend/recipe_extractor.py:18` | Yes |
| **API Keys** | `backend/.env` (local) or Render Dashboard (prod) | Yes |
| **Cache TTL** | `backend/.env` → `CACHE_TTL_SECONDS` | Yes |
| **Cache Size** | `backend/.env` → `CACHE_MAX_ITEMS` | Yes |
| **Redis URL** | `backend/.env` → `REDIS_URL` | Yes |
| **Video Limits** | `backend/.env` → `MAX_VIDEO_SIZE_MB`, `VIDEO_DOWNLOAD_TIMEOUT` | Yes |
| **Server Port** | `backend/.env` → `PORT` | Yes |
| **CORS Origins** | `backend/.env` → `CORS_ORIGINS` | Yes |
| **Add Platform** | `backend/platform_detector.py` + `backend/url_normalizer.py` | Yes |
| **yt-dlp Options** | `backend/video_processor.py` | Yes |
| **Dockerfile** | `backend/Dockerfile` | Yes (rebuild) |
| **Render Config** | `backend/render.yaml` | Yes (redeploy) |

### Configuration Priority

1. **Environment Variables** (highest priority)
   - Local: `.env` file
   - Production: Render Dashboard

2. **Config Class Defaults** (`backend/config.py`)
   - Used if env var not set

3. **Hardcoded Values** (lowest priority)
   - In Python files
   - Should be avoided for configurable values

### Environment-Specific Configs

**Development (.env file):**
```bash
# Local development
GEMINI_API_KEY=your_key
REDIS_URL=redis://localhost:6379  # Local Redis
CACHE_TTL_SECONDS=3600             # Shorter TTL for testing
```

**Production (Render Dashboard):**
```bash
# Production
GEMINI_API_KEY=your_key            # Mark as secret
REDIS_URL=redis://cloud-url        # Redis Cloud, mark as secret
CACHE_TTL_SECONDS=86400            # Full 24h TTL
```

---

## API Endpoints Reference

### Recipe Extraction
- `POST /api/extract-recipe` - Extract recipe from video URL
  - Request: `{"url": "video_url", "use_cache": true}`
  - Response: Recipe + cache info

### Cache Management
- `GET /api/cache/stats` - Get cache statistics
- `DELETE /api/cache/{cache_key}` - Invalidate specific entry
- `DELETE /api/cache` - Clear entire cache

### Health & Monitoring
- `GET /api/health` - Health check
- `HEAD /api/health` - UptimeRobot compatible

### Documentation
- `GET /docs` - Swagger UI (interactive API docs)
- `GET /redoc` - ReDoc (alternative API docs)

---

## Troubleshooting

### Cache Issues

**Redis connection fails:**
1. Check `REDIS_URL` format
2. Verify Redis Cloud dashboard (check endpoint)
3. Test connection: `redis-cli -u $REDIS_URL ping`
4. App falls back to memory cache automatically

**Cache not working:**
1. Check `CACHE_ENABLED=true` in `.env`
2. Verify logs for "✓ Redis connection successful"
3. Check `/api/cache/stats` for hit rate

### LLM Issues

**Quota exceeded:**
1. Wait until midnight PT (quota resets)
2. Check quota: https://aistudio.google.com/apikey
3. Upgrade to pay-as-you-go
4. Use cache to reduce API calls

**Model errors:**
1. Verify `GEMINI_API_KEY` is correct
2. Check model name in `recipe_extractor.py:18`
3. Check Gemini API status

### Deployment Issues

**Render build fails:**
1. Check `Dockerfile` syntax
2. Verify `requirements.txt` dependencies
3. Check Render build logs

**Render service down:**
1. Check UptimeRobot for alerts
2. Verify environment variables in Render
3. Check Render logs for errors
4. May need to restart service manually

---

## Version History

- **v1.0.0** (Initial) - Basic recipe extraction
- **v1.1.0** (Current) - Added Redis caching layer
  - URL normalization
  - Dual cache (Redis + memory)
  - Cache management endpoints
  - Statistics tracking

---

## Support & Resources

- **Gemini API:** https://ai.google.dev/
- **Redis Cloud:** https://redis.com/cloud/
- **Render.com:** https://render.com/docs
- **FastAPI:** https://fastapi.tiangolo.com/
- **yt-dlp:** https://github.com/yt-dlp/yt-dlp
- **UptimeRobot:** https://uptimerobot.com/

---

*Last updated: 2026-01-21*
