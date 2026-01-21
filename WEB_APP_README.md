# Recipe Keeper Web App

A simple web application that extracts recipes from cooking videos on YouTube, TikTok, and Instagram.

## Features

- Extract recipes from video descriptions and comments (preferred method)
- Fall back to AI video analysis if no text recipe is found
- Support for YouTube (Shorts & Videos), TikTok, and Instagram Reels
- Beautiful, responsive UI with loading states and error handling
- Display ingredients and step-by-step instructions
- Link back to original video

## How to Use

### 1. Start the Backend Server

```bash
cd /Users/dmei/Documents/my-project-learning/recipe-keeper/backend
source ../path/to/venv/bin/activate
python main.py
```

The server will start on `http://localhost:8000`

### 2. Open the Web App

Open your browser and go to: `http://localhost:8000`

### 3. Extract a Recipe

1. Copy a video URL from:
   - YouTube (e.g., `https://www.youtube.com/shorts/xe6gvF2nYoI`)
   - TikTok (e.g., `https://www.tiktok.com/t/ZP8fufJvN/`)
   - Instagram (e.g., `https://www.instagram.com/reels/DKqwfMmNyIv/`)

2. Paste the URL into the input field

3. Click "Extract Recipe" or press Enter

4. Wait for the extraction to complete (usually 5-30 seconds)

5. View the extracted recipe with ingredients and instructions

## How It Works

The app uses a smart extraction strategy:

1. **First:** Tries to extract from video description
2. **Second:** Tries to extract from author comments
3. **Third:** Falls back to AI video analysis using Google Gemini

This approach ensures the highest accuracy since recipe authors often post full recipes in descriptions or comments.

## API Endpoints

### GET `/`
Serves the web application interface

### GET `/api/health`
Health check endpoint
```json
{"status": "ok", "version": "1.0.0"}
```

### POST `/api/extract-recipe`
Extract recipe from a video URL

**Request:**
```json
{
  "url": "https://www.youtube.com/shorts/xe6gvF2nYoI"
}
```

**Response (Success):**
```json
{
  "success": true,
  "platform": "youtube",
  "recipe": {
    "title": "Gut Brownies",
    "ingredients": [
      "1 medium Sweet potato",
      "2 medium eggs",
      "70-80mL Honey",
      ...
    ],
    "steps": [
      "Mix Dry Ingredients",
      "Add in Wet Ingredients",
      ...
    ],
    "source_url": "https://www.youtube.com/shorts/xe6gvF2nYoI",
    "platform": "youtube",
    "language": "en"
  },
  "error": null
}
```

**Response (Error):**
```json
{
  "success": false,
  "platform": "youtube",
  "error": "Failed to extract recipe. No recipe found in description, comments, or video."
}
```

## Project Structure

```
backend/
├── main.py                 # FastAPI app with endpoints
├── recipe_extractor.py     # Gemini AI integration
├── video_processor.py      # yt-dlp video/metadata handling
├── platform_detector.py    # URL pattern matching
├── models.py              # Pydantic data models
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (GEMINI_API_KEY)
└── static/
    └── index.html        # Web app interface
```

## Troubleshooting

### Server won't start
- Make sure port 8000 is not already in use
- Kill existing process: `lsof -ti:8000 | xargs kill -9`

### "Network error" in web app
- Make sure the backend server is running on port 8000
- Check browser console for CORS errors

### Extraction fails
- Verify the URL is from a supported platform (YouTube, TikTok, Instagram)
- Some videos may be private or region-locked
- TikTok may require cookies for some videos

### YouTube downloads fail
- Make sure `deno` is installed: `brew install deno`
- Update yt-dlp: `pip install -U yt-dlp`

## Next Steps

- Deploy backend to Railway or Render for public access
- Add recipe saving/export functionality
- Build iOS app with Share Extension
- Add support for more platforms
- Implement recipe editing and tagging
