import os
import tempfile
from typing import Optional, Dict, Any
import yt_dlp
from config import config


class VideoProcessor:
    """Process videos using yt-dlp"""

    def __init__(self):
        self.temp_dir = config.TEMP_DIR
        os.makedirs(self.temp_dir, exist_ok=True)

    def download_video(self, url: str, platform: str) -> Optional[str]:
        """
        Download video from URL using yt-dlp

        Args:
            url: Video URL
            platform: Platform name (youtube, tiktok, instagram)

        Returns:
            Path to downloaded video file, or None if download failed
        """
        try:
            # Create unique output path
            import time
            timestamp = str(int(time.time() * 1000))
            output_path = os.path.join(self.temp_dir, f"video_{timestamp}.mp4")

            ydl_opts = {
                "format": "worst[ext=mp4]/worst",  # Use worst quality to speed up
                "outtmpl": output_path,
                "quiet": False,  # Show output for debugging
                "no_warnings": False,
                "extract_flat": False,
                # Anti-bot measures
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"],  # Use Android client to bypass bot detection
                        "skip": ["dash", "hls"],  # Skip DASH/HLS formats that might require more validation
                    }
                },
            }

            # Add cookies if available from environment variable
            cookies_path = os.getenv("YOUTUBE_COOKIES_PATH")
            if cookies_path and os.path.exists(cookies_path):
                ydl_opts["cookiefile"] = cookies_path
                print(f"Using cookies from: {cookies_path}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            # Check if file exists and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"Downloaded video: {output_path}, size: {os.path.getsize(output_path)} bytes")
                return output_path

            print(f"Video download failed or file is empty")
            return None

        except Exception as e:
            error_msg = str(e)
            print(f"Error downloading video: {error_msg}")

            # Check if it's a bot detection error
            if "Sign in to confirm" in error_msg or "not a bot" in error_msg:
                print("⚠️  YouTube bot detection triggered. Video analysis unavailable.")
                print("💡 Tip: Recipe may still be extracted from description/comments.")

            return None

    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get video metadata including description and comments

        Args:
            url: Video URL

        Returns:
            Dictionary with video info, or None if extraction failed
        """
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
                "getcomments": True,  # Extract comments
                # Anti-bot measures
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"],  # Use Android client to bypass bot detection
                        "comment_sort": ["top"],
                        "skip": ["dash", "hls"],
                    }
                },
            }

            # Add cookies if available from environment variable
            cookies_path = os.getenv("YOUTUBE_COOKIES_PATH")
            if cookies_path and os.path.exists(cookies_path):
                ydl_opts["cookiefile"] = cookies_path

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Get top comments (first 5)
                comments = info.get("comments", [])
                top_comments = []
                for comment in comments[:5]:
                    top_comments.append({
                        "author": comment.get("author"),
                        "text": comment.get("text"),
                        "author_is_uploader": comment.get("author_is_uploader", False)
                    })

                return {
                    "title": info.get("title"),
                    "description": info.get("description"),
                    "duration": info.get("duration"),
                    "uploader": info.get("uploader"),
                    "thumbnail": info.get("thumbnail"),
                    "comments": top_comments,
                }

        except Exception as e:
            error_msg = str(e)
            print(f"Error extracting video info: {error_msg}")

            # Check if it's a bot detection error
            if "Sign in to confirm" in error_msg or "not a bot" in error_msg:
                print("⚠️  YouTube bot detection triggered for metadata extraction.")
                print("💡 Attempting to continue with limited info...")

            return None

    def cleanup(self, file_path: str):
        """Delete temporary video file"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up file {file_path}: {str(e)}")


# Singleton instance
video_processor = VideoProcessor()
