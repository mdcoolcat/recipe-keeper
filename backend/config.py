import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for the Recipe Keeper backend"""

    # Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # Server settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # CORS settings (allow iOS app to connect)
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # Temporary file storage
    TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/recipe-keeper")

    # Video processing settings
    MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", 100))
    VIDEO_DOWNLOAD_TIMEOUT = int(os.getenv("VIDEO_DOWNLOAD_TIMEOUT", 60))

    # Cache settings
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "86400"))  # 24 hours
    CACHE_MAX_ITEMS = int(os.getenv("CACHE_MAX_ITEMS", "1000"))

    # Redis connection
    REDIS_URL = os.getenv("REDIS_URL", None)

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        return True


config = Config()
