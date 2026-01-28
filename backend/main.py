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
from web_scraper import WebScraper
from datetime import datetime
import os

# Initialize FastAPI app
app = FastAPI(
    title="Recipe Keeper API",
    description="Extract recipes from cooking videos and recipe websites",
    version="1.0.0"
)

# Initialize web scraper
web_scraper = WebScraper()

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


@app.get("/api/config")
async def get_config():
    """Get client-side configuration"""
    return {
        "progress_message_delay": config.PROGRESS_MESSAGE_DELAY_SEC,
        "progress_message_text": config.PROGRESS_MESSAGE_TEXT
    }


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
            error="Unsupported URL. Please provide a valid video or website URL."
        )

    # Check cache
    cache_key = None
    canonical_url = None
    if config.CACHE_ENABLED and use_cache:
        print(f"DEBUG: Cache enabled, checking cache for URL: {url}")
        canonical_url, cache_key = url_normalizer.normalize_and_hash(url, platform)
        print(f"DEBUG: Cache key: {cache_key} for canonical URL: {canonical_url}")

        cached_recipe = await cache_manager.get(cache_key)
        if cached_recipe:
            print(f"DEBUG: ✓ Returning cached recipe: {cached_recipe.title}")
            print(f"DEBUG: Cached recipe author: '{cached_recipe.author}'")
            return ExtractRecipeResponse(
                success=True,
                platform=platform,
                recipe=cached_recipe,
                from_cache=True,
                cached_at=datetime.now().isoformat(),
                extraction_method="cache"
            )
        else:
            print(f"DEBUG: Cache miss, proceeding with extraction")

    # NEW: Website extraction
    if platform == "website":
        try:
            print(f"Extracting recipe from website: {url}")
            recipe = await web_scraper.extract_recipe(url)

            if not recipe:
                return ExtractRecipeResponse(
                    success=False,
                    error="Could not extract recipe from website. The site may not contain a recipe or uses an unsupported format."
                )

            # Cache result
            if config.CACHE_ENABLED and cache_key:
                await cache_manager.set(cache_key, recipe, canonical_url, platform)

            print(f"DEBUG: Returning extracted recipe - Title: '{recipe.title}', Author: '{recipe.author}'")

            return ExtractRecipeResponse(
                success=True,
                platform=platform,
                recipe=recipe,
                from_cache=False
            )

        except Exception as e:
            print(f"Website extraction error: {e}")
            import traceback
            traceback.print_exc()
            return ExtractRecipeResponse(
                success=False,
                error=f"Failed to extract recipe from website: {str(e)}"
            )

    # Video extraction (existing logic)
    recipe = None
    video_path = None
    thumbnail_url = None

    try:
        # Step 1: Get video metadata (title, description, comments, thumbnail)
        print(f"Getting metadata for {platform} video...")
        metadata = video_processor.get_video_info(url)

        if not metadata:
            # Metadata extraction failed - likely bot detection
            print("⚠️  Could not extract video metadata (description/comments)")
            if platform == "youtube":
                return ExtractRecipeResponse(
                    success=False,
                    platform=platform,
                    error=(
                        "Could not access this YouTube video. "
                        "YouTube is blocking automated access. "
                        "Please try a different video or check if the recipe is in the video description."
                    )
                )
            else:
                return ExtractRecipeResponse(
                    success=False,
                    platform=platform,
                    error=f"Could not access video metadata from {platform}"
                )

        if metadata:
            title = metadata.get("title", "")
            description = metadata.get("description", "")
            comments = metadata.get("comments", [])
            thumbnail_url = metadata.get("thumbnail", "")
            author = metadata.get("uploader", "")  # Extract channel/author name

            print(f"Title: {title}")
            print(f"Description length: {len(description)} chars")
            print(f"Comments found: {len(comments)}")
            print(f"Author: {author}")
            print(f"Thumbnail: {thumbnail_url[:100] if thumbnail_url else 'None'}...")

            # Step 2: Try extracting from description first
            if description and len(description) > 50:
                print("Trying to extract from description...")
                recipe = recipe_extractor.extract_from_text(description, title, url, platform, thumbnail_url, author)
                if recipe:
                    # Check if recipe has actual content (ingredients or steps)
                    has_content = (recipe.ingredients and len(recipe.ingredients) > 0) or (recipe.steps and len(recipe.steps) > 0)

                    if has_content:
                        print("Successfully extracted from description!")
                        print(f"DEBUG: Extracted recipe - Title: '{recipe.title}', Author: '{recipe.author}'")

                        # For TikTok, try to find author website and append to ingredients
                        if platform == "tiktok":
                            from tiktok_profile_scraper import tiktok_profile_scraper

                            # Try description first
                            author_website = tiktok_profile_scraper.extract_website_from_description(description)

                            # If not in description, try profile
                            if not author_website:
                                profile_url = metadata.get("uploader_url")
                                if profile_url:
                                    author_website = tiktok_profile_scraper.extract_website_from_profile(profile_url)

                            # Append website to ingredients if found
                            if author_website:
                                recipe.author_website_url = author_website
                                if recipe.ingredients:
                                    recipe.ingredients.append(f"📖 Full recipe available at: {author_website}")
                                    print(f"Added author website to ingredients: {author_website}")

                        # Store in cache
                        if config.CACHE_ENABLED and cache_key:
                            await cache_manager.set(cache_key, recipe, canonical_url, platform)
                        return ExtractRecipeResponse(
                            success=True,
                            platform=platform,
                            recipe=recipe,
                            from_cache=False,
                            extraction_method="description"
                        )
                    else:
                        print("Description extraction found title but no ingredients/steps. Will try video analysis...")
                        # Save the title for later use with video extraction
                        title = recipe.title

            # Step 3: Try extracting from author comments
            for comment in comments:
                if comment.get("author_is_uploader") or len(comment.get("text", "")) > 100:
                    print(f"Trying to extract from comment by {comment.get('author')}...")
                    recipe = recipe_extractor.extract_from_text(
                        comment.get("text", ""), title, url, platform, thumbnail_url, author
                    )
                    if recipe:
                        # Check if recipe has actual content (ingredients or steps)
                        has_content = (recipe.ingredients and len(recipe.ingredients) > 0) or (recipe.steps and len(recipe.steps) > 0)

                        if has_content:
                            print("Successfully extracted from comment!")
                            print(f"DEBUG: Extracted recipe - Title: '{recipe.title}', Author: '{recipe.author}'")

                            # For TikTok, try to find author website and append to ingredients
                            if platform == "tiktok":
                                from tiktok_profile_scraper import tiktok_profile_scraper

                                # Try description first
                                author_website = tiktok_profile_scraper.extract_website_from_description(description)

                                # If not in description, try profile
                                if not author_website:
                                    profile_url = metadata.get("uploader_url")
                                    if profile_url:
                                        author_website = tiktok_profile_scraper.extract_website_from_profile(profile_url)

                                # Append website to ingredients if found
                                if author_website:
                                    recipe.author_website_url = author_website
                                    if recipe.ingredients:
                                        recipe.ingredients.append(f"📖 Full recipe available at: {author_website}")
                                        print(f"Added author website to ingredients: {author_website}")

                            # Store in cache
                            if config.CACHE_ENABLED and cache_key:
                                await cache_manager.set(cache_key, recipe, canonical_url, platform)
                            return ExtractRecipeResponse(
                                success=True,
                                platform=platform,
                                recipe=recipe,
                                from_cache=False,
                                extraction_method="comment"
                            )
                        else:
                            print("Comment extraction found title but no ingredients/steps. Continuing...")

        # Step 4: Fall back to video analysis
        print("No text recipe found, falling back to video analysis...")
        video_path = video_processor.download_video(url, platform)
        if not video_path:
            # Video download failed - provide helpful error message
            if platform == "youtube":
                error_msg = (
                    "Could not extract recipe from this YouTube video. "
                    "The recipe was not found in the description or comments, and video download was blocked. "
                    "Try a different video or check if the recipe is in the description."
                )
            else:
                error_msg = f"Failed to download video from {platform}. Recipe not found in description or comments."

            return ExtractRecipeResponse(
                success=False,
                platform=platform,
                error=error_msg
            )

        # Extract recipe from downloaded video
        recipe = recipe_extractor.extract_from_video_file(video_path, url, platform, thumbnail_url, author if metadata else "")

        # Clean up downloaded video
        if video_path:
            video_processor.cleanup(video_path)

        # Check if extraction was successful
        # Recipe is complete if it has ingredients OR steps
        has_content = recipe and ((recipe.ingredients and len(recipe.ingredients) > 0) or (recipe.steps and len(recipe.steps) > 0))

        if has_content:
            # For TikTok, try to find author website and append to ingredients
            if platform == "tiktok" and metadata:
                from tiktok_profile_scraper import tiktok_profile_scraper

                description = metadata.get("description", "")
                author_website = tiktok_profile_scraper.extract_website_from_description(description)

                # If not in description, try profile
                if not author_website:
                    profile_url = metadata.get("uploader_url")
                    if profile_url:
                        author_website = tiktok_profile_scraper.extract_website_from_profile(profile_url)

                # Append website to ingredients if found
                if author_website:
                    recipe.author_website_url = author_website
                    if recipe.ingredients:
                        recipe.ingredients.append(f"📖 Full recipe available at: {author_website}")
                        print(f"Added author website to ingredients: {author_website}")

            # Store in cache
            if config.CACHE_ENABLED and cache_key:
                await cache_manager.set(cache_key, recipe, canonical_url, platform)

            print(f"DEBUG: Returning extracted recipe - Title: '{recipe.title}', Author: '{recipe.author}'")

            return ExtractRecipeResponse(
                success=True,
                platform=platform,
                recipe=recipe,
                from_cache=False,
                extraction_method="multimedia"
            )
        else:
            # Step 5: Try author's website as final fallback (TikTok only)
            if platform == "tiktok" and metadata:
                print("No recipe in video, trying author's website...")
                from tiktok_profile_scraper import tiktok_profile_scraper

                # Try description first
                description = metadata.get("description", "")
                author_website = tiktok_profile_scraper.extract_website_from_description(description)

                # If not in description, try profile
                if not author_website:
                    profile_url = metadata.get("uploader_url")
                    if profile_url:
                        author_website = tiktok_profile_scraper.extract_website_from_profile(profile_url)

                # If we found a website (from description, username, or profile), try extracting recipe
                if author_website:
                    print(f"Found author website: {author_website}")

                    # Use existing WebScraper to extract recipe
                    recipe = await web_scraper.extract_recipe(author_website)

                    if recipe:
                        print(f"Successfully extracted recipe from author's website!")

                        # Preserve TikTok video metadata (title, thumbnail, URL)
                        # Only ingredients/steps come from the author's website
                        original_title = metadata.get("title", "")
                        original_thumbnail = metadata.get("thumbnail", "")

                        # Clean the title - remove emojis and extra text like "recipe in our website"
                        import re
                        clean_title = original_title
                        if original_title:
                            # Remove emojis and special characters
                            clean_title = re.sub(r'[^\w\s\-\',]', ' ', original_title)
                            # Remove phrases like "recipe in", "recipe on", etc.
                            clean_title = re.split(r'\s+recipe\s+(in|on|at|from)\s+', clean_title, flags=re.IGNORECASE)[0]
                            # Remove website mentions
                            clean_title = re.split(r'\s+https?://|www\.|\.[a-z]{2,3}(?:\s|$)', clean_title)[0]
                            # Clean up extra spaces
                            clean_title = ' '.join(clean_title.split()).strip()

                        recipe.title = clean_title if clean_title else recipe.title
                        recipe.source_url = url  # Keep original TikTok URL
                        recipe.platform = platform  # Keep "tiktok"
                        recipe.thumbnail_url = original_thumbnail  # Keep TikTok thumbnail
                        recipe.author_website_url = author_website  # Add author's website URL

                        # If ingredients/steps are empty, add a helpful message to ingredients
                        if not recipe.ingredients and not recipe.steps:
                            recipe.ingredients = [f"📖 Full recipe available at: {author_website}"]

                        # Cache and return
                        if config.CACHE_ENABLED and cache_key:
                            await cache_manager.set(cache_key, recipe, canonical_url, platform)

                        return ExtractRecipeResponse(
                            success=True,
                            platform=platform,
                            recipe=recipe,
                            from_cache=False,
                            extraction_method="author_website"
                        )
                    else:
                        print("Could not extract recipe from author's website")
                else:
                    print("No external website found in description or profile")

            # Final failure - no recipe found anywhere
            print(f"DEBUG: Recipe extraction failed - no recipe found")
            return ExtractRecipeResponse(
                success=False,
                platform=platform,
                error="Failed to extract recipe. No recipe found in description, comments, video, or author's website."
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
