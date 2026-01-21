from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models import (
    ExtractRecipeRequest,
    ExtractRecipeResponse,
    HealthResponse,
    Recipe
)
from platform_detector import detect_platform
from video_processor import video_processor
from recipe_extractor import recipe_extractor
from config import config
import os

# Initialize FastAPI app
app = FastAPI(
    title="Recipe Keeper API",
    description="Extract recipes from cooking videos on YouTube, TikTok, and Instagram",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """Serve the web app"""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/api/extract-recipe", response_model=ExtractRecipeResponse)
async def extract_recipe(request: ExtractRecipeRequest):
    """
    Extract recipe from a video URL

    Supports YouTube, TikTok, and Instagram videos.
    """
    url = request.url

    # Detect platform
    platform = detect_platform(url)
    if not platform:
        return ExtractRecipeResponse(
            success=False,
            error="Unsupported platform. Please provide a YouTube, TikTok, or Instagram URL."
        )

    recipe = None
    video_path = None
    thumbnail_url = None

    try:
        # Step 1: Get video metadata (title, description, comments, thumbnail)
        print(f"Getting metadata for {platform} video...")
        metadata = video_processor.get_video_info(url)

        if metadata:
            title = metadata.get("title", "")
            description = metadata.get("description", "")
            comments = metadata.get("comments", [])
            thumbnail_url = metadata.get("thumbnail", "")

            print(f"Title: {title}")
            print(f"Description length: {len(description)} chars")
            print(f"Comments found: {len(comments)}")
            print(f"Thumbnail: {thumbnail_url[:100] if thumbnail_url else 'None'}...")

            # Step 2: Try extracting from description first
            if description and len(description) > 50:
                print("Trying to extract from description...")
                recipe = recipe_extractor.extract_from_text(description, title, url, platform, thumbnail_url)
                if recipe:
                    print("Successfully extracted from description!")
                    return ExtractRecipeResponse(
                        success=True,
                        platform=platform,
                        recipe=recipe
                    )

            # Step 3: Try extracting from author comments
            for comment in comments:
                if comment.get("author_is_uploader") or len(comment.get("text", "")) > 100:
                    print(f"Trying to extract from comment by {comment.get('author')}...")
                    recipe = recipe_extractor.extract_from_text(
                        comment.get("text", ""), title, url, platform, thumbnail_url
                    )
                    if recipe:
                        print("Successfully extracted from comment!")
                        return ExtractRecipeResponse(
                            success=True,
                            platform=platform,
                            recipe=recipe
                        )

        # Step 4: Fall back to video analysis
        print("No text recipe found, falling back to video analysis...")
        video_path = video_processor.download_video(url, platform)
        if not video_path:
            return ExtractRecipeResponse(
                success=False,
                platform=platform,
                error=f"Failed to download video from {platform}"
            )

        # Extract recipe from downloaded video
        recipe = recipe_extractor.extract_from_video_file(video_path, url, platform, thumbnail_url)

        # Clean up downloaded video
        if video_path:
            video_processor.cleanup(video_path)

        # Check if extraction was successful
        if recipe:
            return ExtractRecipeResponse(
                success=True,
                platform=platform,
                recipe=recipe
            )
        else:
            return ExtractRecipeResponse(
                success=False,
                platform=platform,
                error="Failed to extract recipe. No recipe found in description, comments, or video."
            )

    except Exception as e:
        # Clean up on error
        if video_path:
            video_processor.cleanup(video_path)

        print(f"Error processing request: {str(e)}")
        import traceback
        traceback.print_exc()
        return ExtractRecipeResponse(
            success=False,
            platform=platform,
            error=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set GEMINI_API_KEY environment variable")
        exit(1)

    # Run server
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level="info"
    )
