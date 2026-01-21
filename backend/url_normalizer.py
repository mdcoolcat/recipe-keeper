"""
URL Normalizer for Recipe Keeper
Normalizes video URLs to canonical form for cache key generation
"""

import re
import hashlib
from typing import Optional, Tuple


class URLNormalizer:
    """Normalize video URLs to canonical form for cache key generation"""

    def extract_youtube_id(self, url: str) -> Optional[str]:
        """
        Extract YouTube video ID from various URL formats

        Supports:
        - youtube.com/watch?v=VIDEO_ID
        - youtu.be/VIDEO_ID
        - youtube.com/embed/VIDEO_ID
        - youtube.com/shorts/VIDEO_ID
        - m.youtube.com/watch?v=VIDEO_ID

        Args:
            url: YouTube URL in any supported format

        Returns:
            11-character video ID or None if not found
        """
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
            r'm\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def extract_tiktok_id(self, url: str) -> Optional[str]:
        """
        Extract TikTok video ID from various URL formats

        Supports:
        - tiktok.com/@username/video/VIDEO_ID
        - vm.tiktok.com/SHORTCODE
        - tiktok.com/t/SHORTCODE

        Args:
            url: TikTok URL in any supported format

        Returns:
            Video ID or shortcode, or None if not found
        """
        # Try full video URL first
        match = re.search(r'tiktok\.com/@[\w\d_.-]+/video/(\d+)', url)
        if match:
            return match.group(1)

        # Try short URL formats
        match = re.search(r'(?:vm\.tiktok\.com|tiktok\.com/t)/([\w\d]+)', url)
        if match:
            return f"short:{match.group(1)}"

        return None

    def extract_instagram_id(self, url: str) -> Optional[str]:
        """
        Extract Instagram post ID from various URL formats

        Supports:
        - instagram.com/reel/POST_ID
        - instagram.com/reels/POST_ID
        - instagram.com/p/POST_ID
        - instagram.com/tv/POST_ID

        Args:
            url: Instagram URL in any supported format

        Returns:
            Post ID or None if not found
        """
        match = re.search(r'instagram\.com/(?:reel|reels|p|tv)/([\w\d_-]+)', url)
        if match:
            return match.group(1)

        return None

    def normalize_url(self, url: str, platform: str) -> str:
        """
        Convert URL to canonical form: {platform}:{video_id}

        Args:
            url: Original video URL
            platform: Platform name (youtube, tiktok, instagram)

        Returns:
            Canonical URL string in format "platform:video_id"
        """
        extractors = {
            "youtube": self.extract_youtube_id,
            "tiktok": self.extract_tiktok_id,
            "instagram": self.extract_instagram_id,
        }

        if platform not in extractors:
            # Unknown platform - use full URL
            return f"{platform}:{url}"

        video_id = extractors[platform](url)
        if not video_id:
            # Could not extract ID - use full URL
            return f"{platform}:{url}"

        return f"{platform}:{video_id}"

    def generate_cache_key(self, canonical_url: str) -> str:
        """
        Generate SHA256 hash as cache key (first 16 chars)

        Args:
            canonical_url: Normalized URL in format "platform:video_id"

        Returns:
            First 16 characters of SHA256 hash
        """
        hash_obj = hashlib.sha256(canonical_url.encode('utf-8'))
        return hash_obj.hexdigest()[:16]

    def normalize_and_hash(self, url: str, platform: str) -> Tuple[str, str]:
        """
        Convenience method: normalize URL and generate cache key

        Args:
            url: Original video URL
            platform: Platform name (youtube, tiktok, instagram)

        Returns:
            Tuple of (canonical_url, cache_key)
        """
        canonical_url = self.normalize_url(url, platform)
        cache_key = self.generate_cache_key(canonical_url)
        return canonical_url, cache_key


# Singleton instance
url_normalizer = URLNormalizer()
