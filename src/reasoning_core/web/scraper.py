"""Website scraping utilities."""

import ipaddress
import socket
from typing import Dict, Optional
from urllib.parse import urljoin, urlparse

from reasoning_core.web.config import ALLOW_PRIVATE_IPS, ALLOWED_URL_DOMAINS, URL_SCRAPE_TIMEOUT
from reasoning_core.web.validation import URL_PATTERN

# Maximum number of redirects followed while scraping a page.
MAX_REDIRECTS = 5

# HTTP status codes treated as redirect responses.
_REDIRECT_STATUSES = (301, 302, 303, 307, 308)


class ScrapingError(Exception):
    """Exception raised when website scraping fails."""

    pass


def _parse_literal_ip(hostname):
    """Parse a hostname as a canonical IP address literal.

    Only canonical forms accepted by ``ipaddress`` are recognized. Legacy
    numeric spellings (decimal integer, hex, octal/leading-zero, and
    shortened forms such as ``127.1``) are deliberately *not* interpreted
    here: the platform resolver that performs the actual connection may read
    them differently, so ``_is_ambiguous_numeric_host`` rejects them outright
    instead.

    Args:
        hostname: Hostname to parse

    Returns:
        An ``ipaddress`` address object, or None when the hostname is not a
        canonical IP literal.
    """
    try:
        return ipaddress.ip_address(hostname)
    except ValueError:
        return None


def _is_ambiguous_numeric_host(hostname: str) -> bool:
    """Return True for non-canonical numeric host spellings.

    Examples: ``010.0.0.1``, ``0x7f000001``, ``2130706433``, ``127.1``.
    These are rejected outright by ``is_safe_url`` (issue #6: alternate
    encodings are "normalized or rejected"): the platform resolver used for
    the connection may interpret them differently from any local parsing, so
    approving one based on a local reading could send the request to a
    private address.
    """
    parts = hostname.split(".")
    if not 1 <= len(parts) <= 4:
        return False

    def _is_numeric_part(part: str) -> bool:
        if not part or not part.isascii():
            return False
        if part.isdigit():
            return True
        if part[:2].lower() == "0x" and len(part) > 2:
            return all(char in "0123456789abcdefABCDEF" for char in part[2:])
        return False

    return all(_is_numeric_part(part) for part in parts)


def _resolve_host_ips(hostname):
    """Resolve a hostname to the IP addresses it refers to.

    Canonical IP literals bypass DNS; everything else is resolved with the
    system resolver — the same one the connection will use. All returned
    addresses are checked by the caller, because a name can map to both
    public and private addresses.

    Args:
        hostname: Hostname to resolve

    Returns:
        List of ``ipaddress`` address objects (IPv4-mapped IPv6 addresses are
        normalized to their IPv4 form).
    """
    literal = _parse_literal_ip(hostname)
    if literal is not None:
        if isinstance(literal, ipaddress.IPv6Address) and literal.ipv4_mapped is not None:
            return [literal.ipv4_mapped]
        return [literal]

    addresses = []
    for family, _type, _proto, _canonname, sockaddr in socket.getaddrinfo(hostname, None):
        if family not in (socket.AF_INET, socket.AF_INET6):
            continue
        address = ipaddress.ip_address(sockaddr[0].split("%", 1)[0])
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
            address = address.ipv4_mapped
        addresses.append(address)
    return addresses


def _is_blocked_ip(ip) -> bool:
    """Return True when an address must never be fetched.

    Multicast and the unspecified address are always blocked. Private,
    loopback, link-local, and reserved ranges are blocked unless
    ``REASONING_CORE_ALLOW_PRIVATE_IPS`` explicitly opts in.
    """
    if ip.is_multicast or ip.is_unspecified:
        return True
    if ALLOW_PRIVATE_IPS:
        return False
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        return True
    return not ip.is_global


def is_safe_url(url: str) -> bool:  # noqa: C901
    """Check if URL is safe to fetch (prevent SSRF attacks).

    Validates the scheme and an optional domain allowlist, then *resolves the
    hostname* and rejects the URL when any resolved address is private or
    reserved. Legacy numeric host spellings (decimal integer, hex,
    octal/leading-zero, shortened forms) are rejected outright, because the
    platform resolver may read them differently from any local parsing.

    Args:
        url: URL to check

    Returns:
        True if URL is safe, False otherwise
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    # Block file:// and other dangerous schemes
    if parsed.scheme not in ("http", "https"):
        return False

    hostname = (parsed.hostname or "").strip().rstrip(".").lower()
    if not hostname:
        return False

    # Reject legacy numeric spellings (decimal integer, hex,
    # octal/leading-zero, shortened) outright: the platform resolver may read
    # them differently from any local parsing, which could otherwise route
    # the request to a private address (issue #6: alternate IP encodings are
    # "normalized or rejected").
    if _parse_literal_ip(hostname) is None and _is_ambiguous_numeric_host(hostname):
        return False

    # Block localhost hostnames unless explicitly allowed (resolving the name
    # below would also catch these, but the explicit check is clearer)
    if not ALLOW_PRIVATE_IPS and hostname == "localhost":
        return False

    # Check domain whitelist if configured
    if ALLOWED_URL_DOMAINS:
        allowed_domains = [domain.strip().lower() for domain in ALLOWED_URL_DOMAINS if domain.strip()]
        if not any(hostname == domain or hostname.endswith(f".{domain}") for domain in allowed_domains):
            return False

    # Resolve the hostname and validate every address it can reach. A name
    # that cannot be resolved is rejected: it cannot be verified as safe.
    try:
        addresses = _resolve_host_ips(hostname)
    except Exception:
        return False

    if not addresses:
        return False

    return all(not _is_blocked_ip(address) for address in addresses)


def _fetch_page(url: str, timeout: int):
    """Fetch a URL, validating every redirect hop before following it.

    ``requests`` follows redirects invisibly by default, which would skip the
    SSRF check for redirect targets; redirects are therefore followed manually
    for at most ``MAX_REDIRECTS`` hops, and each hop is validated first.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        The final response object

    Raises:
        ScrapingError: If a hop is not allowed or there are too many redirects
    """
    import requests

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    current_url = url

    for _ in range(MAX_REDIRECTS + 1):
        if not is_safe_url(current_url):
            raise ScrapingError(f"URL not allowed: {current_url}. Private/internal URLs are blocked for security.")

        response = requests.get(current_url, headers=headers, timeout=timeout, allow_redirects=False)

        if response.status_code in _REDIRECT_STATUSES:
            location = response.headers.get("location")
            if not location:
                raise ScrapingError("Redirect response without a Location header")
            current_url = urljoin(current_url, location)
            continue

        return response

    raise ScrapingError(f"Too many redirects (maximum {MAX_REDIRECTS})")


def scrape_website(url: str, timeout: Optional[int] = None) -> Dict[str, str]:  # noqa: C901
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
    if not URL_PATTERN.match(url):
        raise ValueError(f"Invalid URL format: {url}")

    try:
        from bs4 import BeautifulSoup

        # Make request (SSRF protection is applied to the URL and to every
        # redirect hop inside _fetch_page)
        response = _fetch_page(url, timeout)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()

        # Get main content (prefer article, main, or body)
        main_content = soup.find("article") or soup.find("main") or soup.find("body") or soup

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

    except ScrapingError:
        raise
    except ImportError as e:
        missing = []
        try:
            import requests  # noqa: F401  # imported only to test availability
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
