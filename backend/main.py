from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models import (
    ExtractRecipeRequest,
    ExtractRecipeResponse,
    HealthResponse,
    Recipe,
    CacheStatsResponse
)
from platform_detector import detect_platform
from video_processor import video_processor
from recipe_extractor import recipe_extractor
from config import config
from cache_manager import cache_manager
from url_normalizer import url_normalizer
from datetime import datetime
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


@app.api_route("/api/health", methods=["GET", "HEAD"], response_model=HealthResponse)
async def health_check():
    """Health check endpoint - supports both GET and HEAD for monitoring"""
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/api/extract-recipe", response_model=ExtractRecipeResponse)
async def extract_recipe(request: ExtractRecipeRequest):
    """
    Extract recipe from a video URL

    Supports YouTube, TikTok, and Instagram videos.
    """
    url = request.url
    use_cache = request.use_cache

    # Detect platform
    platform = detect_platform(url)
    if not platform:
        return ExtractRecipeResponse(
            success=False,
            error="Unsupported platform. Please provide a YouTube, TikTok, or Instagram URL."
        )

    # Check cache
    cache_key = None
    canonical_url = None
    if config.CACHE_ENABLED and use_cache:
        canonical_url, cache_key = url_normalizer.normalize_and_hash(url, platform)
        print(f"Cache key: {cache_key} for {canonical_url}")

        cached_recipe = await cache_manager.get(cache_key)
        if cached_recipe:
            return ExtractRecipeResponse(
                success=True,
                platform=platform,
                recipe=cached_recipe,
                from_cache=True,
                cached_at=datetime.now().isoformat()
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
                    # Store in cache
                    if config.CACHE_ENABLED and cache_key:
                        await cache_manager.set(cache_key, recipe, canonical_url, platform)
                    return ExtractRecipeResponse(
                        success=True,
                        platform=platform,
                        recipe=recipe,
                        from_cache=False
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
                        # Store in cache
                        if config.CACHE_ENABLED and cache_key:
                            await cache_manager.set(cache_key, recipe, canonical_url, platform)
                        return ExtractRecipeResponse(
                            success=True,
                            platform=platform,
                            recipe=recipe,
                            from_cache=False
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
            # Store in cache
            if config.CACHE_ENABLED and cache_key:
                await cache_manager.set(cache_key, recipe, canonical_url, platform)
            return ExtractRecipeResponse(
                success=True,
                platform=platform,
                recipe=recipe,
                from_cache=False
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

        error_msg = str(e)
        print(f"Error processing request: {error_msg}")
        import traceback
        traceback.print_exc()

        # Check for quota exceeded error
        if "QUOTA_EXCEEDED" in error_msg:
            return ExtractRecipeResponse(
                success=False,
                platform=platform,
                error="⚠️ Gemini API quota exceeded. The free tier limit is ~15-20 requests/day. Please try again after midnight PT, or upgrade to pay-as-you-go at https://aistudio.google.com/ (costs ~$0.001 per extraction)."
            )

        return ExtractRecipeResponse(
            success=False,
            platform=platform,
            error=f"Internal server error: {error_msg}"
        )


@app.get("/api/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Get cache statistics"""
    if not config.CACHE_ENABLED:
        return CacheStatsResponse(
            enabled=False,
            redis_available=False,
            redis_size=0,
            memory_size=0,
            redis_hits=0,
            memory_hits=0,
            total_misses=0,
            hit_rate=0.0,
            redis_errors=0,
            ttl_seconds=0
        )

    stats = await cache_manager.get_stats()
    return CacheStatsResponse(
        enabled=True,
        redis_available=stats["redis_available"],
        redis_size=stats["redis_size"],
        memory_size=stats["memory_size"],
        redis_hits=stats["redis_hits"],
        memory_hits=stats["memory_hits"],
        total_misses=stats["misses"],
        hit_rate=stats["hit_rate"],
        redis_errors=stats["redis_errors"],
        ttl_seconds=config.CACHE_TTL_SECONDS
    )


@app.delete("/api/cache/{cache_key}")
async def invalidate_cache_entry(cache_key: str):
    """Invalidate a specific cache entry"""
    if not config.CACHE_ENABLED:
        raise HTTPException(status_code=400, detail="Cache is disabled")

    await cache_manager.delete(cache_key)
    return {"message": f"Cache entry {cache_key} invalidated"}


@app.delete("/api/cache")
async def clear_cache():
    """Clear entire cache (admin operation)"""
    if not config.CACHE_ENABLED:
        raise HTTPException(status_code=400, detail="Cache is disabled")

    await cache_manager.clear()
    return {"message": "Cache cleared successfully"}


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
