import json
from google import genai
from google.genai import types
from typing import Optional, Dict, Any
from config import config
from models import Recipe


class RecipeExtractor:
    """Extract recipes from videos using Gemini API"""

    def __init__(self):
        """Initialize Gemini API client"""
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")

        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model_id = 'models/gemini-2.0-flash'  # Stable model with better free tier than 2.5

    def extract_from_text(self, text: str, title: str, url: str, platform: str, thumbnail_url: Optional[str] = None) -> Optional[Recipe]:
        """
        Extract recipe from text (description or comment)

        Args:
            text: Recipe text from description or comment
            title: Video title
            url: Original video URL
            platform: Platform name
            thumbnail_url: Video thumbnail URL

        Returns:
            Recipe object or None if extraction failed
        """
        try:
            prompt = f"""You are a recipe extraction AI. Extract the recipe from this text.

Video Title: {title}

Recipe Text:
{text}

Extract the following information:
1. Recipe title (use the video title if no specific recipe title in text)
2. Ingredients list (with exact quantities as stated)
3. Cooking steps/instructions (in order, if available)
4. Language of the content (en for English, zh for Chinese, etc.)

Return the information in the following JSON format:
{{
  "title": "Recipe Name",
  "ingredients": ["ingredient 1 with quantity", "ingredient 2 with quantity", ...],
  "steps": ["step 1", "step 2", ...],
  "language": "en"
}}

Important guidelines:
- Keep all quantities EXACTLY as stated
- If no steps are provided, return an empty steps array []
- Be concise but complete
- If video is in Chinese, keep content in Chinese but set language to "zh"
- If this is not a recipe, return: {{"error": "Not a recipe"}}

Return ONLY the JSON object, no other text.
"""

            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            return self._parse_response(response.text, url, platform, thumbnail_url)

        except Exception as e:
            error_msg = str(e)
            print(f"Error extracting recipe from text: {error_msg}")

            # Check for quota exceeded error
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                raise Exception("QUOTA_EXCEEDED: Gemini API daily quota exceeded. Please wait until midnight PT for reset or upgrade to pay-as-you-go.")

            return None

    def extract_from_video_file(self, video_path: str, url: str, platform: str, thumbnail_url: Optional[str] = None) -> Optional[Recipe]:
        """
        Extract recipe from downloaded video file

        Args:
            video_path: Path to video file
            url: Original video URL
            platform: Platform name
            thumbnail_url: Video thumbnail URL

        Returns:
            Recipe object or None if extraction failed
        """
        try:
            prompt = self._build_prompt()

            # Upload video file to Gemini
            with open(video_path, 'rb') as f:
                video_file = self.client.files.upload(file=f, config={"mime_type": "video/mp4"})

            # Wait for file processing
            import time
            while video_file.state == types.FileState.PROCESSING:
                time.sleep(1)
                video_file = self.client.files.get(name=video_file.name)

            if video_file.state == types.FileState.FAILED:
                print(f"File upload failed: {video_file}")
                return None

            # Generate content from video
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[prompt, video_file]
            )

            return self._parse_response(response.text, url, platform, thumbnail_url)

        except Exception as e:
            error_msg = str(e)
            print(f"Error extracting recipe from video file: {error_msg}")
            import traceback
            traceback.print_exc()

            # Check for quota exceeded error
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                raise Exception("QUOTA_EXCEEDED: Gemini API daily quota exceeded. Please wait until midnight PT for reset or upgrade to pay-as-you-go.")

            return None

    def _build_prompt(self) -> str:
        """Build the extraction prompt for Gemini"""
        return """You are a recipe extraction AI. Analyze this cooking video and extract the recipe information.

Extract the following information:
1. Recipe title (create a descriptive name if not explicitly stated)
2. Ingredients list (with quantities if mentioned)
3. Cooking steps/instructions (in order)
4. Language of the content (en for English, zh for Chinese, etc.)

Return the information in the following JSON format:
{
  "title": "Recipe Name",
  "ingredients": ["ingredient 1 with quantity", "ingredient 2 with quantity", ...],
  "steps": ["step 1", "step 2", ...],
  "language": "en"
}

Important guidelines:
- If ingredients appear as text overlays in the video, extract them
- If ingredients are spoken, transcribe them
- Keep ingredient quantities and units
- Number steps in order
- Be concise but complete
- If video is in Chinese, keep content in Chinese but set language to "zh"
- If this is not a cooking/recipe video, return: {"error": "Not a recipe video"}

Return ONLY the JSON object, no other text.
"""

    def _parse_response(self, response_text: str, source_url: str, platform: str, thumbnail_url: Optional[str] = None) -> Optional[Recipe]:
        """
        Parse Gemini response into Recipe object

        Args:
            response_text: Raw response from Gemini
            source_url: Original video URL
            platform: Platform name
            thumbnail_url: Video thumbnail URL

        Returns:
            Recipe object or None if parsing failed
        """
        try:
            # Clean up response text (remove markdown code blocks if present)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            # Parse JSON
            data = json.loads(cleaned_text)

            # Check for error
            if "error" in data:
                print(f"Gemini detected non-recipe video: {data['error']}")
                return None

            # Create Recipe object
            recipe = Recipe(
                title=data.get("title", "Untitled Recipe"),
                ingredients=data.get("ingredients", []),
                steps=data.get("steps", []),
                source_url=source_url,
                platform=platform,
                language=data.get("language", "en"),
                thumbnail_url=thumbnail_url
            )

            return recipe

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {str(e)}")
            print(f"Raw response: {response_text}")
            return None
        except Exception as e:
            print(f"Error creating Recipe object: {str(e)}")
            return None


# Singleton instance
recipe_extractor = RecipeExtractor()
