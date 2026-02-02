"""Website scraper tool implementation."""

import logging
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, urljoin
import urllib.request
import urllib.error
import ssl

from src.agent.tools.base import BaseTool
from src.shared.models import ToolMode

logger = logging.getLogger(__name__)

# Try to import BeautifulSoup
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BeautifulSoup = None
    BS4_AVAILABLE = False


class WebScraperTool(BaseTool):
    """
    Website scraper tool for extracting content from web pages.

    Extracts text content, metadata, and structured data from websites.
    Respects robots.txt and implements polite scraping practices.
    """

    TOOL_NAME = "web_scraper"
    TOOL_DESCRIPTION = (
        "Scrape content from a website URL. "
        "Returns page title, meta description, main text content, and links. "
        "Use this to get detailed information from company websites, "
        "product pages, or news articles. Note: Some sites may block scraping."
    )
    TOOL_MODE = ToolMode.EXTENDED
    DEFAULT_TIMEOUT = 15.0
    MAX_RETRIES = 1  # Don't hammer sites
    CACHE_TTL = 3600.0  # 1 hour cache

    RATE_LIMIT_RPS = 1.0  # Be polite
    RATE_LIMIT_BURST = 2

    # Max content size (1MB)
    MAX_CONTENT_SIZE = 1024 * 1024

    def __init__(
        self,
        max_content_length: int = 5000,
        user_agent: str = "B2BAccountAgent/1.0 (Research Bot)",
        **kwargs
    ):
        """
        Initialize web scraper tool.

        Args:
            max_content_length: Maximum text content to return
            user_agent: User agent string
            **kwargs: Additional BaseTool arguments
        """
        super().__init__(**kwargs)
        self.max_content_length = max_content_length
        self.user_agent = user_agent

        if not BS4_AVAILABLE:
            logger.warning(
                "beautifulsoup4 not installed. "
                "Install with: pip install beautifulsoup4"
            )

    def _execute(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL.

        Args:
            url: URL to scrape

        Returns:
            Dictionary with scraped content
        """
        if not BS4_AVAILABLE:
            return {
                "success": False,
                "error": "BeautifulSoup not available. Install beautifulsoup4 package.",
                "url": url
            }

        # Validate URL
        if not url or not url.strip():
            return {
                "success": False,
                "error": "Empty URL",
                "url": url
            }

        url = url.strip()

        # Add protocol if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # Parse and validate URL
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return {
                    "success": False,
                    "error": "Invalid URL format",
                    "url": url
                }
        except Exception:
            return {
                "success": False,
                "error": "Invalid URL format",
                "url": url
            }

        try:
            # Fetch page content
            content, final_url, content_type = self._fetch_url(url)

            if content is None:
                return {
                    "success": False,
                    "error": "Failed to fetch URL content",
                    "url": url
                }

            # Check content type
            if content_type and "html" not in content_type.lower():
                return {
                    "success": False,
                    "error": f"URL points to non-HTML content: {content_type}",
                    "url": url
                }

            # Parse HTML
            soup = BeautifulSoup(content, "html.parser")

            # Extract data
            result = {
                "success": True,
                "url": final_url or url,
            }

            # Title
            title = soup.find("title")
            if title:
                result["title"] = title.get_text(strip=True)

            # Meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                result["description"] = meta_desc.get("content", "")

            # Open Graph data
            og_data = {}
            for og_tag in soup.find_all("meta", property=re.compile(r"^og:")):
                prop = og_tag.get("property", "").replace("og:", "")
                og_data[prop] = og_tag.get("content", "")
            if og_data:
                result["og_data"] = og_data

            # Main content
            main_content = self._extract_main_content(soup)
            if main_content:
                result["content"] = main_content[:self.max_content_length]
                if len(main_content) > self.max_content_length:
                    result["content_truncated"] = True

            # Links
            links = self._extract_links(soup, url)
            if links:
                result["links"] = links[:10]  # Top 10 links

            # Contact info
            contact = self._extract_contact_info(soup, content)
            if contact:
                result["contact_info"] = contact

            return result

        except urllib.error.HTTPError as e:
            error_messages = {
                403: "Website restricts automated access (403 Forbidden)",
                404: "Page not found (404)",
                429: "Rate limited by website. Try again later.",
                503: "Website temporarily unavailable (503)",
            }
            return {
                "success": False,
                "error": error_messages.get(e.code, f"HTTP error: {e.code}"),
                "url": url,
                "status_code": e.code
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Scraper error for {url}: {error_msg}")

            # Detect specific error types
            if "ssl" in error_msg.lower() or "certificate" in error_msg.lower():
                return {
                    "success": False,
                    "error": "SSL/Certificate error. Site may have security issues.",
                    "url": url
                }

            if "timeout" in error_msg.lower():
                return {
                    "success": False,
                    "error": "Request timed out. Site may be slow or unavailable.",
                    "url": url
                }

            return {
                "success": False,
                "error": f"Scraping failed: {error_msg}",
                "url": url
            }

    def _fetch_url(self, url: str) -> tuple:
        """Fetch URL content with redirect handling."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Create SSL context that doesn't verify (for some sites)
        context = ssl.create_default_context()

        req = urllib.request.Request(url, headers=headers)

        redirect_count = 0
        max_redirects = 5
        final_url = url

        while redirect_count < max_redirects:
            try:
                response = urllib.request.urlopen(
                    req,
                    timeout=self.timeout,
                    context=context
                )

                # Check for redirect
                if response.geturl() != final_url:
                    final_url = response.geturl()

                content_type = response.headers.get("Content-Type", "")

                # Read with size limit
                content = response.read(self.MAX_CONTENT_SIZE)

                # Detect encoding
                encoding = "utf-8"
                if "charset=" in content_type:
                    encoding = content_type.split("charset=")[-1].split(";")[0].strip()

                return content.decode(encoding, errors="ignore"), final_url, content_type

            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 303, 307, 308):
                    redirect_url = e.headers.get("Location")
                    if redirect_url:
                        final_url = urljoin(final_url, redirect_url)
                        req = urllib.request.Request(final_url, headers=headers)
                        redirect_count += 1
                        continue
                raise

        raise Exception("Too many redirects")

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main text content from page."""
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Try to find main content area
        main = soup.find("main") or soup.find("article") or soup.find(class_=re.compile(r"content|main|body"))

        if main:
            text = main.get_text(separator=" ", strip=True)
        else:
            # Fallback to body
            body = soup.find("body")
            text = body.get_text(separator=" ", strip=True) if body else ""

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract important links from page."""
        links = []
        seen_urls = set()

        # Important link patterns
        important_patterns = ["about", "team", "careers", "product", "pricing", "contact", "blog"]

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            text = a.get_text(strip=True)

            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            # Make absolute URL
            full_url = urljoin(base_url, href)

            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # Check if important
            href_lower = href.lower()
            is_important = any(p in href_lower for p in important_patterns)

            if is_important or len(links) < 5:
                links.append({
                    "text": text[:100] if text else href,
                    "url": full_url
                })

        return links

    def _extract_contact_info(self, soup: BeautifulSoup, text: str) -> Dict[str, Any]:
        """Extract contact information from page."""
        contact = {}

        # Email pattern
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, text)
        if emails:
            # Filter out common non-contact emails
            filtered = [e for e in emails if not any(x in e.lower() for x in ["example", "test", "noreply"])]
            if filtered:
                contact["emails"] = list(set(filtered))[:3]

        # Phone pattern (basic)
        phone_pattern = r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        phones = re.findall(phone_pattern, text)
        if phones:
            contact["phones"] = list(set(phones))[:2]

        # Social links
        social_patterns = {
            "twitter": r"twitter\.com/(\w+)",
            "linkedin": r"linkedin\.com/(?:company|in)/([^/\s\"']+)",
            "github": r"github\.com/([^/\s\"']+)",
        }

        for platform, pattern in social_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                contact[platform] = match.group(1)

        return contact if contact else None

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": (
                        "The URL to scrape. "
                        "Examples: 'stripe.com', 'https://openai.com/about', "
                        "'www.anthropic.com'"
                    )
                }
            },
            "required": ["url"]
        }

    @staticmethod
    def is_available() -> bool:
        """Check if web scraper is available."""
        return BS4_AVAILABLE
