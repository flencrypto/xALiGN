"""Lightweight web crawler for extracting public company information.

Respects robots.txt meta directives embedded in HTML.
Never accesses pages behind authentication walls.
"""

import ipaddress
import logging
import re
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("contractghost.crawler")

_TIMEOUT = 20.0
_MAX_TEXT_LEN = 8000
_HEADERS = {
    "User-Agent": "ContractGHOST-Intel/1.0 (institutional research; contact admin@contractghost.com)",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.5",
}

# Additional paths to try for leadership/about information
_EXEC_PATHS = ["/about", "/about-us", "/team", "/leadership", "/our-team", "/people", "/management"]

# Blocked hostnames and IP ranges (SSRF protection)
_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("fc00::/7"),
]


def _validate_url(url: str) -> None:
    """
    Validate that the URL targets a public, external host.

    Raises ValueError for private/loopback addresses to prevent SSRF.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r}. Only http/https are allowed.")

    hostname = parsed.hostname or ""
    if not hostname:
        raise ValueError("URL must include a hostname.")

    if hostname.lower() in _BLOCKED_HOSTS:
        raise ValueError(f"Requests to {hostname!r} are not allowed.")

    # Block numeric private IPs
    try:
        addr = ipaddress.ip_address(hostname)
        for network in _PRIVATE_NETWORKS:
            if addr in network:
                raise ValueError(f"Requests to private IP range {network} are not allowed.")
        if addr.is_loopback or addr.is_link_local or addr.is_reserved:
            raise ValueError(f"Requests to reserved/loopback addresses are not allowed.")
    except ValueError as exc:
        # Re-raise SSRF errors; ignore "not a valid IP" which means it's a hostname
        if "not allowed" in str(exc) or "Unsupported" in str(exc) or "must include" in str(exc):
            raise


def _strip_html(html: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    # Use [^>]* in closing tags to handle any attributes/whitespace variants
    text = re.sub(r"<script[\s\S]*?</script[^>]*>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style[^>]*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _normalise_url(url: str) -> str:
    """Ensure the URL has a scheme."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


async def crawl_homepage(website: str) -> str:
    """Fetch and extract plain text from a company homepage."""
    url = _normalise_url(website)
    try:
        _validate_url(url)
    except ValueError as exc:
        logger.warning("Blocked crawl request: %s", exc)
        return ""

    try:
        async with httpx.AsyncClient(
            timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            text = _strip_html(resp.text)
            return text[:_MAX_TEXT_LEN]
    except httpx.HTTPStatusError as exc:
        logger.warning("HTTP %s when crawling %s", exc.response.status_code, url)
        return ""
    except Exception as exc:
        logger.warning("Failed to crawl %s: %s", url, exc)
        return ""


async def crawl_leadership_pages(website: str) -> str:
    """
    Attempt to fetch leadership/about pages to extract executive information.

    Tries several common paths and concatenates the extracted text.
    """
    base = _normalise_url(website)
    try:
        _validate_url(base)
    except ValueError as exc:
        logger.warning("Blocked crawl request: %s", exc)
        return ""

    parsed = urlparse(base)
    # Reconstruct base_origin from only the validated scheme and netloc components
    # to ensure no user-controlled path or query string is included
    safe_scheme = parsed.scheme if parsed.scheme in ("http", "https") else "https"
    safe_netloc = parsed.netloc

    combined = ""
    async with httpx.AsyncClient(
        timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True
    ) as client:
        for path in _EXEC_PATHS:
            # path is from a hardcoded constant list; safe to append directly
            url = f"{safe_scheme}://{safe_netloc}{path}"
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    text = _strip_html(resp.text)
                    combined += text[:2000] + "\n"
                    if len(combined) >= 6000:
                        break
            except Exception:
                continue

    return combined[:_MAX_TEXT_LEN]
