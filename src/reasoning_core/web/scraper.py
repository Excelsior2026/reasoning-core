"""Website scraping utilities."""

from typing import Dict, Optional
import re
import ipaddress
from urllib.parse import urlparse
from reasoning_core.web.config import ALLOW_PRIVATE_IPS, ALLOWED_URL_DOMAINS, URL_SCRAPE_TIMEOUT


class ScrapingError(Exception):
    """Exception raised when website scraping fails."""

    pass


def is_safe_url(url: str) -> bool:
    """Check if URL is safe to fetch (prevent SSRF attacks).

    Args:
        url: URL to check

    Returns:
        True if URL is safe, False otherwise
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return False

        # Check if hostname is an IP address
        try:
            ip = ipaddress.ip_address(hostname)
            # Block private/localhost IPs unless explicitly allowed
            if not ALLOW_PRIVATE_IPS:
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    return False
            # Block multicast and broadcast
            if ip.is_multicast or (hasattr(ip, 'is_global') and not ip.is_global):
                return False
        except ValueError:
            # Hostname, not an IP - check domain whitelist if configured
            if ALLOWED_URL_DOMAINS:
                # Check if hostname matches any allowed domain
                if hostname not in ALLOWED_URL_DOMAINS:
                    # Also check subdomains
                    for allowed_domain in ALLOWED_URL_DOMAINS:
                        if hostname.endswith(f".{allowed_domain}"):
                            return True
                    return False

        # Block localhost hostnames unless explicitly allowed
        if not ALLOW_PRIVATE_IPS:
            localhost_names = ["localhost", "127.0.0.1", "0.0.0.0", "::1"]
            if hostname.lower() in localhost_names:
                return False

        # Block file:// and other dangerous schemes
        if parsed.scheme not in ("http", "https"):
            return False

        return True

    except Exception:
        return False


def scrape_website(url: str, timeout: Optional[int] = None) -> Dict[str, str]:
    """Scrape text content from a website.

    Args:
        url: Website URL to scrape
        timeout: Request timeout in seconds

    Returns:
        Dictionary with 'text' (extracted content) and 'metadata' (page info)

    Raises:
        ScrapingError: If scraping fails
        ValueError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    # Use timeout from config if not provided
    if timeout is None:
        timeout = URL_SCRAPE_TIMEOUT

    # Validate URL format
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if not url_pattern.match(url):
        raise ValueError(f"Invalid URL format: {url}")

    # Check for SSRF vulnerabilities
    if not is_safe_url(url):
        raise ScrapingError(
            f"URL not allowed: {url}. Private/internal URLs are blocked for security."
        )

    try:
        import requests
        from bs4 import BeautifulSoup

        # Make request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()

        # Get main content (prefer article, main, or body)
        main_content = (
            soup.find("article")
            or soup.find("main")
            or soup.find("body")
            or soup
        )

        # Extract text
        text = main_content.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)

        # Extract metadata
        title = soup.find("title")
        title_text = title.string.strip() if title and title.string else ""

        # Try to get description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        description = ""
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"]

        return {
            "text": text,
            "metadata": {
                "url": url,
                "title": title_text,
                "description": description,
                "status_code": response.status_code,
                "content_length": len(text),
            },
        }

    except ImportError as e:
        missing = []
        try:
            import requests
        except ImportError:
            missing.append("requests")

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            missing.append("beautifulsoup4")

        if missing:
            raise ScrapingError(
                f"Required packages not installed: {', '.join(missing)}. "
                f"Install with: pip install {' '.join(missing)}"
            ) from e
        raise
    except Exception as e:
        raise ScrapingError(f"Failed to scrape website: {e}") from e
