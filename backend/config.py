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

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        return True


config = Config()
