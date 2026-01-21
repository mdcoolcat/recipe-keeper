# Recipe Keeper Backend

FastAPI backend for extracting recipes from cooking videos on YouTube, TikTok, and Instagram.

## Features

- 🎥 Extract recipes from YouTube Shorts, TikTok, and Instagram Reels
- 🤖 AI-powered extraction using Google Gemini
- 🌐 Support for English and Chinese content
- 🆓 Free to run (uses Gemini free tier)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Gemini API Key

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Sign in with your Google account
3. Click "Get API Key"
4. Copy your API key

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### 4. Run the Server

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

## API Endpoints

### Health Check

```bash
GET /api/health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### Extract Recipe

```bash
POST /api/extract-recipe
Content-Type: application/json

{
  "url": "https://youtube.com/shorts/xe6gvF2nYoI"
}
```

Response:
```json
{
  "success": true,
  "platform": "youtube",
  "recipe": {
    "title": "Gut Brownies",
    "ingredients": [
      "1 medium Sweet potato",
      "2 medium eggs",
      ...
    ],
    "steps": [
      "Mix Dry Ingredients",
      "Add in Wet Ingredients",
      ...
    ],
    "source_url": "https://youtube.com/shorts/xe6gvF2nYoI",
    "platform": "youtube",
    "language": "en"
  }
}
```

## Testing

Test with curl:

```bash
# Health check
curl http://localhost:8000/api/health

# Extract recipe from YouTube
curl -X POST http://localhost:8000/api/extract-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/shorts/xe6gvF2nYoI"}'

# Extract recipe from TikTok
curl -X POST http://localhost:8000/api/extract-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.tiktok.com/@clairehodginss/video/7491817125074904990"}'
```

## Supported Platforms

- ✅ YouTube (Shorts and regular videos)
- ✅ TikTok
- ✅ Instagram Reels
- ❌ RedNote (not yet implemented)

## How It Works

1. **Platform Detection**: Identifies platform from URL pattern
2. **Video Processing**:
   - YouTube: Tries direct URL processing with Gemini (no download)
   - TikTok/Instagram: Downloads video temporarily with yt-dlp
3. **Recipe Extraction**: Sends video to Gemini AI for analysis
4. **Cleanup**: Removes temporary files
5. **Response**: Returns structured recipe data

## Deployment

### Railway

1. Create account at [Railway](https://railway.app)
2. Create new project
3. Connect GitHub repository
4. Set environment variable: `GEMINI_API_KEY`
5. Deploy

### Render

1. Create account at [Render](https://render.com)
2. Create new Web Service
3. Connect GitHub repository
4. Set environment variable: `GEMINI_API_KEY`
5. Deploy

## Cost

- **Gemini API**: Free tier (1,500 requests/day)
- **Hosting**: $0 on Railway/Render free tier
- **Total**: $0/month for POC

## Troubleshooting

### "GEMINI_API_KEY is required"
- Make sure you created `.env` file from `.env.example`
- Add your actual API key to `.env`

### "Unsupported platform"
- Check that the URL is from YouTube, TikTok, or Instagram
- Make sure the URL format is correct

### "Failed to download video"
- Check your internet connection
- Some videos may be private or region-locked
- TikTok/Instagram may block automated downloads

### "Failed to extract recipe"
- Video might not be a cooking video
- Content might be unclear or too short
- Try a different video

## Development

Run in development mode with auto-reload:
```bash
uvicorn main:app --reload
```

View API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
