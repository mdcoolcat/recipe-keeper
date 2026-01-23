"""
Web Scraper for Recipe Websites
Orchestrates multi-layer recipe extraction from recipe websites
"""

import requests
from typing import Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from models import Recipe
from schema_extractor import schema_extractor
from wordpress_plugin_detector import wordpress_plugin_detector
from heuristic_parser import heuristic_parser


class WebScraper:
    """Fetch and extract recipes from recipe websites"""

    def __init__(self):
        """Initialize web scraper with default settings"""
        self.timeout = 10  # seconds
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            # Note: requests library only auto-decompresses gzip and deflate, not br (brotli)
            # Omitting Accept-Encoding lets requests handle it automatically
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def extract_author_from_url(self, url: str) -> str:
        """
        Extract author/site name from URL domain

        Examples:
            https://jaroflemons.com/recipe -> jaroflemons
            https://www.natashaskitchen.com/meatballs -> natashaskitchen

        Args:
            url: Website URL

        Returns:
            Author name extracted from domain
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path

            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            # Extract main domain name (before first dot)
            # e.g., "natashaskitchen.com" -> "natashaskitchen"
            author = domain.split('.')[0]

            return author

        except Exception as e:
            return ""

    def fetch_html(self, url: str) -> Tuple[str, str]:
        """
        Fetch HTML content from URL

        Args:
            url: Website URL

        Returns:
            Tuple of (html_content, final_url)

        Raises:
            requests.RequestException: If request fails
        """
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()

            # Return HTML and final URL (after redirects)
            return response.text, response.url

        except requests.Timeout:
            raise Exception(f"Request timed out after {self.timeout} seconds")
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch webpage: {str(e)}")

    async def extract_recipe(self, url: str) -> Optional[Recipe]:
        """
        Extract recipe from website URL using multi-layer approach

        Extraction layers (in order):
        1. Schema.org JSON-LD (Phase 1)
        2. WordPress plugins (Phase 2)
        3. recipe-scrapers library (Phase 5)
        4. Heuristic HTML parsing (Phase 4)
        5. Gemini AI fallback (Phase 6)

        Args:
            url: Recipe website URL

        Returns:
            Recipe object or None if extraction failed
        """
        try:
            # Fetch HTML
            html, final_url = self.fetch_html(url)

            # Use final URL (after redirects) as source
            source_url = final_url

            # Extract author from domain
            author = self.extract_author_from_url(source_url)
            print(f"DEBUG: Extracted author from URL: '{author}'")

            # Layer 1: Schema.org JSON-LD extraction
            print("Trying Schema.org JSON-LD extraction...")
            recipe = schema_extractor.extract_from_html(html, source_url)
            if recipe:
                print("Successfully extracted from Schema.org JSON-LD!")
                print(f"DEBUG: Recipe author from Schema.org: '{recipe.author}'")
                # Add author if not already set
                if not recipe.author:
                    recipe.author = author
                    print(f"DEBUG: Set author from URL: '{author}'")
                else:
                    print(f"DEBUG: Keeping author from Schema.org: '{recipe.author}'")
                return recipe

            # Layer 2: WordPress plugin detection
            print("Trying WordPress plugin extraction...")
            recipe = await self.extract_from_wordpress_plugins(html, source_url)
            if recipe:
                print("Successfully extracted from WordPress plugin!")
                print(f"DEBUG: Recipe author from WordPress: '{recipe.author}'")
                # Add author if not already set
                if not recipe.author:
                    recipe.author = author
                    print(f"DEBUG: Set author from URL: '{author}'")
                print(f"DEBUG: Final author: '{recipe.author}'")
                return recipe

            # Layer 3: recipe-scrapers library
            print("Trying recipe-scrapers library...")
            recipe = await self.extract_from_recipe_scrapers(source_url, author)
            if recipe:
                print("Successfully extracted from recipe-scrapers!")
                print(f"DEBUG: Final author: '{recipe.author}'")
                return recipe

            # Layer 4: Heuristic HTML parsing
            print("Trying heuristic HTML parsing...")
            recipe = await self.extract_from_heuristics(html, source_url)
            if recipe:
                print("Successfully extracted from heuristic parsing!")
                print(f"DEBUG: Recipe author from heuristic: '{recipe.author}'")
                # Add author if not already set
                if not recipe.author:
                    recipe.author = author
                    print(f"DEBUG: Set author from URL: '{author}'")
                print(f"DEBUG: Final author: '{recipe.author}'")
                return recipe

            # Layer 5: Gemini AI fallback
            print("Trying Gemini AI fallback...")
            recipe = await self.extract_from_gemini(html, source_url)
            if recipe:
                print("Successfully extracted from Gemini AI!")
                print(f"DEBUG: Recipe author from Gemini: '{recipe.author}'")
                # Add author if not already set
                if not recipe.author:
                    recipe.author = author
                    print(f"DEBUG: Set author from URL: '{author}'")
                print(f"DEBUG: Final author: '{recipe.author}'")
                return recipe

            print("All extraction methods failed")
            return None

        except Exception as e:
            print(f"Error extracting recipe from website: {e}")
            raise

    # Placeholder methods for future phases

    async def extract_from_wordpress_plugins(self, html: str, source_url: str) -> Optional[Recipe]:
        """
        Extract from WordPress recipe plugins (Phase 2)

        Args:
            html: HTML content
            source_url: Source URL

        Returns:
            Recipe object or None
        """
        return wordpress_plugin_detector.extract_from_html(html, source_url)

    async def extract_from_recipe_scrapers(self, url: str, author: str = "") -> Optional[Recipe]:
        """
        Extract using recipe-scrapers library (Phase 5)

        Supports 200+ popular recipe sites including:
        - AllRecipes, Food Network, Bon Appetit, Serious Eats
        - NYTimes Cooking, Epicurious, Delish, and more

        Args:
            url: Recipe URL
            author: Author name extracted from domain

        Returns:
            Recipe object or None
        """
        try:
            from recipe_scrapers import scrape_me

            # Use wild_mode=True to attempt scraping on unsupported sites
            scraper = scrape_me(url, wild_mode=True)

            # Extract recipe data
            title = scraper.title()
            ingredients = scraper.ingredients()
            instructions = scraper.instructions()

            # Parse instructions (may be single string or list)
            if isinstance(instructions, str):
                # Split by newlines or numbered steps
                steps = [s.strip() for s in instructions.split('\n') if s.strip()]
            else:
                steps = instructions

            # Get image
            try:
                thumbnail_url = scraper.image() or ''
            except:
                thumbnail_url = ''

            # Validate extracted data
            if not title or not ingredients or not steps:
                return None

            if len(ingredients) < 2 or len(steps) < 2:
                return None

            return Recipe(
                title=title,
                ingredients=ingredients,
                steps=steps,
                source_url=url,
                platform="website",
                language="en",
                thumbnail_url=thumbnail_url,
                author=author
            )

        except Exception as e:
            # recipe-scrapers will raise exceptions for unsupported sites
            # or when extraction fails - this is expected
            return None

    async def extract_from_heuristics(self, html: str, source_url: str) -> Optional[Recipe]:
        """
        Extract using heuristic HTML parsing (Phase 4)

        Args:
            html: HTML content
            source_url: Source URL

        Returns:
            Recipe object or None
        """
        return heuristic_parser.extract_from_html(html, source_url)

    async def extract_from_gemini(self, html: str, source_url: str) -> Optional[Recipe]:
        """
        Extract using Gemini AI as fallback (Phase 6)

        This is the last resort when all structured extraction methods fail.
        Uses the Gemini API to analyze the page text and extract recipe information.

        Args:
            html: HTML content
            source_url: Source URL

        Returns:
            Recipe object or None
        """
        try:
            from recipe_extractor import recipe_extractor

            # Parse HTML and extract text
            soup = BeautifulSoup(html, 'html.parser')

            # Remove script, style, and other non-content tags
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()

            # Get text content
            text = soup.get_text(separator='\n', strip=True)

            # Truncate to avoid token limits (Gemini has ~1M token limit, but be conservative)
            # Most recipes should fit in 50k characters
            if len(text) > 50000:
                text = text[:50000]

            # Extract page title
            title_elem = soup.find('title')
            page_title = title_elem.get_text(strip=True) if title_elem else "Recipe"

            # Use recipe_extractor with custom prompt
            recipe = recipe_extractor.extract_from_text(
                text=text,
                title=page_title,
                url=source_url,
                platform="website",
                thumbnail_url=None
            )

            return recipe

        except Exception as e:
            error_msg = str(e)
            print(f"Gemini AI fallback error: {error_msg}")

            # Propagate quota exceeded errors
            if "QUOTA_EXCEEDED" in error_msg:
                raise

            return None


# Singleton instance (will be used in Phase 3)
# web_scraper = WebScraper()
