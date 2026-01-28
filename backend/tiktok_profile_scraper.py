import requests
from bs4 import BeautifulSoup
from typing import Optional
from urllib.parse import urlparse
import time


class TikTokProfileScraper:
    """Scrape TikTok profile pages to extract external website links from bio"""

    def __init__(self):
        # Common social media domains to filter out
        self.social_media_domains = {
            'tiktok.com', 'instagram.com', 'twitter.com', 'x.com',
            'facebook.com', 'youtube.com', 'snapchat.com', 'linkedin.com',
            'pinterest.com', 'twitch.tv', 'reddit.com', 'discord.com',
            'telegram.org', 't.me'
        }

        # Realistic browser headers to avoid bot detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }

    def _is_recipe_related_domain(self, url: str) -> bool:
        """
        Check if URL is likely a recipe/blog site (not social media)

        Args:
            url: URL to check

        Returns:
            True if URL appears to be a recipe/blog site
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            # Filter out social media
            if domain in self.social_media_domains:
                return False

            # Filter out common URL shorteners (they might redirect to social media)
            shorteners = {'bit.ly', 'tinyurl.com', 'ow.ly', 't.co', 'goo.gl'}
            if domain in shorteners:
                return False

            return True

        except Exception:
            return False

    def extract_website_from_description(self, description: str) -> Optional[str]:
        """
        Extract website URL from video description text

        Args:
            description: Video description text

        Returns:
            External website URL or None if not found
        """
        if not description:
            return None

        import re
        # Look for domain patterns in the description
        # Match patterns like: archersfood.com, www.archersfood.com, https://archersfood.com
        url_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?)'
        matches = re.findall(url_pattern, description)

        for match in matches:
            # Construct full URL
            url = f'https://{match}' if not match.startswith('http') else match
            if self._is_recipe_related_domain(url):
                print(f"Found website in description: {url}")
                return url

        return None

    def extract_website_from_profile(self, profile_url: str) -> Optional[str]:
        """
        Extract external website link from TikTok creator profile bio

        Args:
            profile_url: TikTok profile URL (e.g., https://www.tiktok.com/@username)

        Returns:
            External website URL or None if not found
        """
        try:
            print(f"Fetching TikTok profile: {profile_url}")

            # Add delay to be respectful
            time.sleep(1)

            # Fetch profile page
            response = requests.get(profile_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            html_content = response.text

            # TikTok profile pages contain structured data in script tags
            # Look for bio links in various possible locations
            external_links = []

            # Method 1: Extract from embedded JSON data (most reliable)
            # TikTok embeds user data in the HTML
            import json
            import re

            # Look for embedded JSON with user info
            # Pattern: "nickname":"www.archersfood.com" or bio/signature fields
            try:
                # Search for userInfo JSON structure
                print(f"DEBUG: Starting JSON extraction...")
                print(f"DEBUG: HTML length: {len(html_content)}")
                print(f"DEBUG: 'archersfood.com' in HTML: {'archersfood.com' in html_content}")
                print(f"DEBUG: 'userInfo' in HTML: {'userInfo' in html_content}")
                json_match = re.search(r'"userInfo":\s*({[^}]+?"nickname"[^}]+?})', html_content)
                print(f"DEBUG: json_match found: {json_match is not None}")
                if json_match:
                    user_info_str = json_match.group(1)
                    # Extract nickname which might be a website
                    nickname_match = re.search(r'"nickname":\s*"([^"]+)"', user_info_str)
                    if nickname_match:
                        nickname = nickname_match.group(1)
                        # Check if nickname looks like a website
                        if ('.' in nickname and
                            not nickname.startswith('@') and
                            (nickname.startswith('www.') or nickname.startswith('http'))):
                            # Add https if missing
                            if not nickname.startswith('http'):
                                nickname = 'https://' + nickname
                            print(f"DEBUG: Checking domain: {nickname}")
                            is_valid = self._is_recipe_related_domain(nickname)
                            print(f"DEBUG: Domain valid: {is_valid}")
                            if is_valid:
                                external_links.append(nickname)
                                print(f"Found website in nickname: {nickname}")

                # Also search for signature/bio field
                signature_match = re.search(r'"signature":\s*"([^"]*(?:https?://|www\.)[^"]+)"', html_content)
                if signature_match:
                    bio_text = signature_match.group(1)
                    # Extract URLs from bio
                    url_pattern = r'(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
                    urls_in_bio = re.findall(url_pattern, bio_text)
                    for url in urls_in_bio:
                        if not url.startswith('http'):
                            url = 'https://' + url
                        if self._is_recipe_related_domain(url):
                            external_links.append(url)
                            print(f"Found website in bio: {url}")
            except Exception as e:
                print(f"Error parsing JSON data: {e}")
                import traceback
                traceback.print_exc()

            # Method 2: Look for links in anchor tags (bio section)
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')

                # Skip TikTok internal links
                if 'tiktok.com' in href:
                    continue

                # Check if it's an external link
                if href.startswith('http://') or href.startswith('https://'):
                    if self._is_recipe_related_domain(href):
                        external_links.append(href)

            # Method 2: Look for bio text that might contain URLs
            # TikTok often wraps bio content in specific divs/spans
            bio_selectors = [
                'h2[data-e2e="user-bio"]',  # Common TikTok bio selector
                'div[data-e2e="user-bio"]',
                'div[class*="bio"]',
                'div[class*="description"]',
            ]

            for selector in bio_selectors:
                bio_element = soup.select_one(selector)
                if bio_element:
                    bio_text = bio_element.get_text()
                    # Look for URLs in the text
                    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
                    urls_in_text = re.findall(url_pattern, bio_text)

                    for url in urls_in_text:
                        if self._is_recipe_related_domain(url):
                            external_links.append(url)

            # Return the first valid external link found
            if external_links:
                website_url = external_links[0]
                print(f"Found external website in profile: {website_url}")
                return website_url

            print("No external website link found in profile")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching TikTok profile: {e}")
            return None
        except Exception as e:
            print(f"Error parsing TikTok profile: {e}")
            return None


# Singleton instance
tiktok_profile_scraper = TikTokProfileScraper()
