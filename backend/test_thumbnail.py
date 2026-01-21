"""Quick test to verify thumbnail extraction"""
from video_processor import video_processor

# Test YouTube URL
url = "https://www.youtube.com/shorts/xe6gvF2nYoI"
print(f"Testing: {url}")
metadata = video_processor.get_video_info(url)

if metadata:
    print(f"\nTitle: {metadata.get('title')}")
    print(f"Thumbnail URL: {metadata.get('thumbnail')}")
    print(f"\nThumbnail length: {len(metadata.get('thumbnail', ''))} chars")
else:
    print("Failed to get metadata")
