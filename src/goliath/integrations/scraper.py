"""
Web Scraper Integration — extract text, links, and structured data from web pages.

SETUP INSTRUCTIONS
==================

No API keys needed. Just install the dependencies (already in requirements.txt):
    pip install requests beautifulsoup4

Usage:
    from goliath.integrations.scraper import WebScraper

    ws = WebScraper()

    # Get all text from a page
    text = ws.get_text("https://example.com")

    # Get all links
    links = ws.get_links("https://example.com")

    # Get the full parsed page for custom extraction
    page = ws.fetch("https://example.com")
    titles = page.select("h1")

    # Extract structured data (text from CSS selectors)
    data = ws.extract("https://news.ycombinator.com", {
        "titles": ".titleline > a",
        "scores": ".score",
    })
    # Returns: {"titles": ["Story 1", "Story 2", ...], "scores": ["100 points", ...]}

    # Download a file
    ws.download("https://example.com/report.pdf", "report.pdf")
"""

from pathlib import Path

import requests
from bs4 import BeautifulSoup

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
}


def _validate_url(url: str) -> None:
    """Reject non-HTTP(S) URLs to prevent SSRF and local file access."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are allowed."
        )


class WebScraper:
    """Web scraper for extracting content from web pages."""

    def __init__(self, headers: dict | None = None, timeout: int = 30):
        """
        Args:
            headers: Custom HTTP headers. Defaults to a standard browser User-Agent.
            timeout: Request timeout in seconds.
        """
        self.session = requests.Session()
        self.session.headers.update(headers or _DEFAULT_HEADERS)
        self.timeout = timeout

    # -- public API --------------------------------------------------------

    def fetch(self, url: str) -> BeautifulSoup:
        """Fetch a URL and return a parsed BeautifulSoup object.

        Args:
            url: The web page URL to fetch.

        Returns:
            BeautifulSoup object for custom querying.
        """
        _validate_url(url)
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

    def get_text(self, url: str) -> str:
        """Extract all visible text from a web page.

        Args:
            url: The web page URL.

        Returns:
            Cleaned text content of the page.
        """
        soup = self.fetch(url)

        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Collapse multiple blank lines
        lines = [line for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def get_links(self, url: str, absolute: bool = True) -> list[dict]:
        """Extract all links from a web page.

        Args:
            url:      The web page URL.
            absolute: Convert relative URLs to absolute. Default True.

        Returns:
            List of dicts: [{"text": "link text", "href": "url"}, ...]
        """
        from urllib.parse import urljoin

        soup = self.fetch(url)
        links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if absolute and not href.startswith(("http://", "https://")):
                href = urljoin(url, href)
            links.append(
                {
                    "text": a.get_text(strip=True),
                    "href": href,
                }
            )

        return links

    def extract(self, url: str, selectors: dict[str, str]) -> dict[str, list[str]]:
        """Extract text from multiple CSS selectors.

        Args:
            url:       The web page URL.
            selectors: Dict mapping names to CSS selectors.
                       e.g. {"titles": "h2.title", "prices": ".price"}

        Returns:
            Dict mapping each name to a list of matched text strings.
        """
        soup = self.fetch(url)
        results = {}

        for name, selector in selectors.items():
            elements = soup.select(selector)
            results[name] = [el.get_text(strip=True) for el in elements]

        return results

    def download(self, url: str, save_path: str) -> Path:
        """Download a file from a URL.

        Args:
            url:       The file URL.
            save_path: Local path to save the file.

        Returns:
            Path object of the saved file.
        """
        _validate_url(url)
        resp = self.session.get(url, timeout=self.timeout, stream=True)
        resp.raise_for_status()

        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        return path
