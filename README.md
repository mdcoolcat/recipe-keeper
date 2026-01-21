# Recipe Keeper

Extract recipes from cooking videos on social media platforms using AI.

## Overview

Recipe Keeper is an iOS app with a Python backend that extracts recipes (ingredients and steps) from short-form cooking videos on:
- 🎬 YouTube Shorts
- 🎵 TikTok
- 📸 Instagram Reels

Simply share a cooking video from any of these apps to Recipe Keeper, and AI will extract the recipe for you!

## Features

- **Share Extension**: Share videos directly from YouTube, TikTok, or Instagram
- **AI-Powered**: Uses Google Gemini to extract recipes from video content
- **Multi-language**: Supports English and Chinese content
- **Local Storage**: Recipes saved locally on your device
- **Free**: Uses free Gemini API tier (1,500 extractions/day)

## Project Structure

```
recipe-keeper/
├── backend/              # Python FastAPI backend
│   ├── main.py          # API endpoints
│   ├── recipe_extractor.py  # Gemini AI integration
│   ├── video_processor.py   # yt-dlp video handling
│   ├── platform_detector.py # URL pattern matching
│   └── README.md        # Backend documentation
├── RecipeKeeper/        # iOS app (to be created)
└── test_urls.csv        # Test video URLs
```

## Quick Start

### Backend Setup

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Get Gemini API key** (free):
   - Visit https://ai.google.dev/
   - Sign in and get your API key

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

4. **Run the backend:**
   ```bash
   python main.py
   ```

   Backend will be available at: http://localhost:8000

### iOS App Setup (Coming Next)

The iOS app will be created using Xcode with:
- SwiftUI for the interface
- SwiftData for local storage
- Share Extension for receiving video URLs

## Testing the Backend

Test with the sample URLs in `test_urls.csv`:

```bash
# Test YouTube Short
curl -X POST http://localhost:8000/api/extract-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/shorts/xe6gvF2nYoI"}'

# Test TikTok video
curl -X POST http://localhost:8000/api/extract-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.tiktok.com/@clairehodginss/video/7491817125074904990"}'
```

## How It Works

1. **User shares video** from YouTube/TikTok/Instagram
2. **iOS Share Extension** captures the URL
3. **Backend API** receives URL and detects platform
4. **Video Processing**:
   - YouTube: Direct URL to Gemini (no download)
   - TikTok/Instagram: Download with yt-dlp, then process
5. **AI Extraction**: Gemini analyzes video and extracts recipe
6. **iOS App** saves recipe locally and displays it

## Cost

- **Backend hosting**: $0 (Railway/Render free tier)
- **Gemini API**: $0 (free tier: 1,500 requests/day)
- **Apple Developer**: $99/year (required for iOS app distribution)

**Total**: $0/month for development and personal use

## Development Status

- ✅ Backend API complete
- ✅ Platform detection (YouTube, TikTok, Instagram)
- ✅ Video processing with yt-dlp
- ✅ Gemini AI integration
- ⏳ iOS app (next step)
- ⏳ Share Extension (next step)

## Next Steps

1. Test backend with various video URLs
2. Create iOS Xcode project
3. Implement SwiftUI interface
4. Build Share Extension
5. Test end-to-end flow

## Future Enhancements

- RedNote (小红书) support
- Recipe editing
- Export/share recipes
- Favorites and tags
- OCR + Whisper pipeline for improved accuracy
- Recipe search

## License

MIT

## Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video download
- [Google Gemini](https://ai.google.dev/) - AI recipe extraction
- [SwiftUI](https://developer.apple.com/xcode/swiftui/) - iOS interface
