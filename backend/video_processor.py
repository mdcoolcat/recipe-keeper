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
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            # Check if file exists and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"Downloaded video: {output_path}, size: {os.path.getsize(output_path)} bytes")
                return output_path

            print(f"Video download failed or file is empty")
            return None

        except Exception as e:
            print(f"Error downloading video: {str(e)}")
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
                "extractor_args": {"youtube": {"comment_sort": ["top"]}},
            }

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
            print(f"Error extracting video info: {str(e)}")
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
