"""
WordPress Recipe Plugin Detector
Detects and extracts recipes from WordPress recipe plugins
Supports: WPRM, Tasty Recipes, WP Recipe Maker, and more
"""

from typing import Optional, List, Dict
from bs4 import BeautifulSoup, Tag
from models import Recipe
import re
import html


class WordPressPluginDetector:
    """Detect and extract recipes from WordPress recipe plugins"""

    def _decode_html_entities(self, text: str) -> str:
        """
        Decode HTML entities like &#039; &quot; &amp; etc.

        Args:
            text: Text with HTML entities

        Returns:
            Decoded text
        """
        if not text:
            return text
        return html.unescape(text)

    # Plugin detection patterns (CSS classes/IDs)
    PLUGIN_PATTERNS = {
        'wprm': ['.wprm-recipe', '#wprm-recipe-container', '[class*="wprm-recipe"]'],
        'tasty': ['.tasty-recipes', '.tasty-recipe', '[class*="tasty-recipe"]'],
        'wp_recipe_maker': ['.wp-recipe-maker', '[class*="wp-recipe-maker"]'],
        'mv_create': ['.mv-create-card', '[class*="mv-create"]'],
        'ziplist': ['.ziplist-recipe', '.zlrecipe-container'],
    }

    def extract_from_html(self, html: str, source_url: str) -> Optional[Recipe]:
        """
        Extract recipe from WordPress plugin markup in HTML

        Args:
            html: HTML content of the webpage
            source_url: URL of the source webpage

        Returns:
            Recipe object or None if not found
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Try each plugin type
        for plugin_name, patterns in self.PLUGIN_PATTERNS.items():
            for pattern in patterns:
                recipe_container = soup.select_one(pattern)
                if recipe_container:
                    print(f"Detected WordPress plugin: {plugin_name}")
                    recipe = self._extract_from_plugin(recipe_container, plugin_name, source_url)
                    if recipe:
                        return recipe

        return None

    def _extract_from_plugin(self, container: Tag, plugin_name: str, source_url: str) -> Optional[Recipe]:
        """
        Extract recipe from plugin-specific container

        Args:
            container: BeautifulSoup Tag containing recipe
            plugin_name: Plugin name (wprm, tasty, etc.)
            source_url: Source URL

        Returns:
            Recipe object or None
        """
        extractors = {
            'wprm': self._extract_wprm,
            'tasty': self._extract_tasty,
            'wp_recipe_maker': self._extract_wp_recipe_maker,
            'mv_create': self._extract_mv_create,
            'ziplist': self._extract_ziplist,
        }

        if plugin_name in extractors:
            return extractors[plugin_name](container, source_url)

        return None

    def _extract_wprm(self, container: Tag, source_url: str) -> Optional[Recipe]:
        """
        Extract from WP Recipe Maker (WPRM) plugin

        Common classes:
        - .wprm-recipe-name (title)
        - .wprm-recipe-ingredient (ingredients)
        - .wprm-recipe-instruction-text (steps)
        - .wprm-recipe-image (thumbnail)

        Args:
            container: WPRM recipe container
            source_url: Source URL

        Returns:
            Recipe object or None
        """
        try:
            # Extract title
            title_elem = container.select_one('.wprm-recipe-name, h2.wprm-recipe-name, [class*="recipe-name"]')
            if not title_elem:
                return None
            title = self._decode_html_entities(title_elem.get_text(strip=True))

            # Extract ingredients
            ingredients = []
            ingredient_elems = container.select('.wprm-recipe-ingredient, .wprm-recipe-ingredient-name, [class*="recipe-ingredient"]')
            for elem in ingredient_elems:
                text = self._decode_html_entities(elem.get_text(strip=True))
                if text and len(text) > 1:
                    ingredients.append(text)

            # If no ingredients found with specific class, try list items in ingredient container
            if not ingredients:
                ingredient_container = container.select_one('.wprm-recipe-ingredients-container, .wprm-recipe-ingredients')
                if ingredient_container:
                    list_items = ingredient_container.select('li')
                    for item in list_items:
                        text = self._decode_html_entities(item.get_text(strip=True))
                        if text:
                            ingredients.append(text)

            if not ingredients or len(ingredients) < 2:
                return None

            # Extract steps
            steps = []
            step_elems = container.select('.wprm-recipe-instruction-text, .wprm-recipe-instruction, [class*="recipe-instruction-text"]')
            for elem in step_elems:
                text = self._decode_html_entities(elem.get_text(strip=True))
                if text and len(text) > 5:
                    steps.append(text)

            # If no steps found with specific class, try list items in instructions container
            if not steps:
                instructions_container = container.select_one('.wprm-recipe-instructions-container, .wprm-recipe-instructions')
                if instructions_container:
                    list_items = instructions_container.select('li')
                    for item in list_items:
                        text = self._decode_html_entities(item.get_text(strip=True))
                        if text and len(text) > 5:
                            steps.append(text)

            if not steps or len(steps) < 2:
                return None

            # Extract thumbnail
            thumbnail_url = ''
            img_elem = container.select_one('.wprm-recipe-image img, .wprm-recipe-image-container img, img[class*="recipe-image"]')
            if img_elem:
                thumbnail_url = img_elem.get('src', img_elem.get('data-src', ''))

            print(f"DEBUG: WPRM extraction - Title: {title}")
            print(f"DEBUG: WPRM extraction - Ingredients count: {len(ingredients)}")
            print(f"DEBUG: WPRM extraction - Steps count: {len(steps)}")

            return Recipe(
                title=title,
                ingredients=ingredients,
                steps=steps,
                source_url=source_url,
                platform="website",
                language="en",
                thumbnail_url=thumbnail_url,
                author=None
            )

        except (AttributeError, TypeError) as e:
            return None

    def _extract_tasty(self, container: Tag, source_url: str) -> Optional[Recipe]:
        """
        Extract from Tasty Recipes plugin

        Common classes:
        - .tasty-recipes-title (title)
        - .tasty-recipes-ingredients li (ingredients)
        - .tasty-recipes-instructions li (steps)

        Args:
            container: Tasty Recipes container
            source_url: Source URL

        Returns:
            Recipe object or None
        """
        try:
            # Extract title
            title_elem = container.select_one('.tasty-recipes-title, h2.tasty-recipes-title, [class*="tasty-recipes-title"]')
            if not title_elem:
                return None
            title = self._decode_html_entities(title_elem.get_text(strip=True))

            # Extract ingredients
            ingredients = []
            ingredient_elems = container.select('.tasty-recipes-ingredients li, .tasty-recipes-ingredients-body li')
            for elem in ingredient_elems:
                text = self._decode_html_entities(elem.get_text(strip=True))
                if text:
                    ingredients.append(text)

            if not ingredients or len(ingredients) < 2:
                return None

            # Extract steps
            steps = []
            step_elems = container.select('.tasty-recipes-instructions li, .tasty-recipes-instructions-body li')
            for elem in step_elems:
                text = self._decode_html_entities(elem.get_text(strip=True))
                if text and len(text) > 5:
                    steps.append(text)

            if not steps or len(steps) < 2:
                return None

            # Extract thumbnail
            thumbnail_url = ''
            img_elem = container.select_one('.tasty-recipes-image img, img[class*="tasty-recipes-image"]')
            if img_elem:
                thumbnail_url = img_elem.get('src', img_elem.get('data-src', ''))

            print(f"DEBUG: Tasty Recipes extraction - Title: {title}")
            print(f"DEBUG: Tasty Recipes extraction - Ingredients count: {len(ingredients)}")
            print(f"DEBUG: Tasty Recipes extraction - Steps count: {len(steps)}")

            return Recipe(
                title=title,
                ingredients=ingredients,
                steps=steps,
                source_url=source_url,
                platform="website",
                language="en",
                thumbnail_url=thumbnail_url,
                author=None
            )

        except (AttributeError, TypeError) as e:
            return None

    def _extract_wp_recipe_maker(self, container: Tag, source_url: str) -> Optional[Recipe]:
        """
        Extract from WP Recipe Maker plugin (different from WPRM)

        Args:
            container: WP Recipe Maker container
            source_url: Source URL

        Returns:
            Recipe object or None
        """
        try:
            # Extract title
            title_elem = container.select_one('h2, h3, .recipe-title, [class*="recipe-name"]')
            if not title_elem:
                return None
            title = self._decode_html_entities(title_elem.get_text(strip=True))

            # Extract ingredients
            ingredients = []
            ingredient_container = container.select_one('[class*="ingredients"], .ingredients-list')
            if ingredient_container:
                list_items = ingredient_container.select('li, .ingredient')
                for item in list_items:
                    text = self._decode_html_entities(item.get_text(strip=True))
                    if text:
                        ingredients.append(text)

            if not ingredients or len(ingredients) < 2:
                return None

            # Extract steps
            steps = []
            instructions_container = container.select_one('[class*="instructions"], .instructions-list')
            if instructions_container:
                list_items = instructions_container.select('li, .instruction')
                for item in list_items:
                    text = self._decode_html_entities(item.get_text(strip=True))
                    if text and len(text) > 5:
                        steps.append(text)

            if not steps or len(steps) < 2:
                return None

            # Extract thumbnail
            thumbnail_url = ''
            img_elem = container.select_one('img')
            if img_elem:
                thumbnail_url = img_elem.get('src', img_elem.get('data-src', ''))

            print(f"DEBUG: WP Recipe Maker extraction - Title: {title}")
            print(f"DEBUG: WP Recipe Maker extraction - Ingredients count: {len(ingredients)}")
            print(f"DEBUG: WP Recipe Maker extraction - Steps count: {len(steps)}")

            return Recipe(
                title=title,
                ingredients=ingredients,
                steps=steps,
                source_url=source_url,
                platform="website",
                language="en",
                thumbnail_url=thumbnail_url,
                author=None
            )

        except (AttributeError, TypeError) as e:
            return None

    def _extract_mv_create(self, container: Tag, source_url: str) -> Optional[Recipe]:
        """
        Extract from MV Create (Mediavine Create) plugin

        Args:
            container: MV Create container
            source_url: Source URL

        Returns:
            Recipe object or None
        """
        # Similar structure to other plugins
        return self._extract_wp_recipe_maker(container, source_url)

    def _extract_ziplist(self, container: Tag, source_url: str) -> Optional[Recipe]:
        """
        Extract from ZipList Recipe plugin

        Args:
            container: ZipList container
            source_url: Source URL

        Returns:
            Recipe object or None
        """
        # Similar structure to other plugins
        return self._extract_wp_recipe_maker(container, source_url)


# Singleton instance
wordpress_plugin_detector = WordPressPluginDetector()
