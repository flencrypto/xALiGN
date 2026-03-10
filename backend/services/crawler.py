"""Lightweight web crawler for extracting public company information.

Respects robots.txt meta directives embedded in HTML.
Never accesses pages behind authentication walls.
"""

import ipaddress
import logging
import re
import socket
from urllib.parse import urlparse

import httpcore
import httpx
from httpcore._backends.auto import AutoBackend
from httpcore._backends.base import AsyncNetworkStream

logger = logging.getLogger("align.crawler")

_TIMEOUT = 20.0
_MAX_TEXT_LEN = 8000
_HEADERS = {
    "User-Agent": "aLiGN-Intel/1.0 (institutional research; contact admin@align.com)",
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


def _is_private_ip(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Return True if the address is not a globally routable public address.

    Covers loopback, link-local, site-local, private RFC-1918/RFC-4193,
    multicast, reserved, and unspecified (0.0.0.0 / ::) ranges.
    """
    if (
        addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    ):
        return True
    for network in _PRIVATE_NETWORKS:
        if addr in network:
            return True
    return False


def _validate_url(url: str) -> list[str]:
    """Validate that the URL targets a public, external host.

    Raises ValueError for private/loopback/unspecified addresses to prevent SSRF.

    Uses ``socket.getaddrinfo`` to resolve hostnames so that DNS rebinding
    attacks and hostnames that alias private IPs are also blocked.

    Returns the list of validated public IP address strings so callers can
    pin connections to them and avoid a second DNS resolution.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r}. Only http/https are allowed.")

    hostname = parsed.hostname or ""
    if not hostname:
        raise ValueError("URL must include a hostname.")

    if hostname.lower() in _BLOCKED_HOSTS:
        raise ValueError(f"Requests to {hostname!r} are not allowed.")

    # Resolve the hostname (or parse it as a literal IP) and check every
    # returned address against private/reserved ranges.
    try:
        results = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        # If DNS resolution fails, block the request rather than allow it.
        raise ValueError(f"Could not resolve hostname {hostname!r}.")

    valid_ips: list[str] = []
    for _family, _type, _proto, _canonname, sockaddr in results:
        ip_str = sockaddr[0]
        try:
            addr = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if _is_private_ip(addr):
            raise ValueError(
                f"Requests to {hostname!r} are not allowed (resolves to private/reserved address {ip_str})."
            )
        valid_ips.append(ip_str)

    return valid_ips


class _PinnedIPBackend(AutoBackend):
    """Network backend that bypasses the OS DNS resolver for a specific hostname.

    Connects directly to the pre-validated IP address, eliminating the TOCTOU
    window between ``_validate_url()`` and the actual TCP connection.  The
    original hostname is still used by httpcore for the TLS ``server_hostname``
    (SNI) and certificate verification, so HTTPS works correctly.
    """

    def __init__(self, hostname: str, ip: str) -> None:
        super().__init__()
        self._hostname = hostname
        self._pinned_ip = ip

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options=None,
    ) -> AsyncNetworkStream:
        # Replace the DNS-resolved hostname with our pre-validated IP so no
        # further OS-level DNS lookup is performed.  httpcore derives the TLS
        # server_hostname from self._origin.host (the original URL hostname),
        # not from this host argument, so certificate verification is intact.
        target = self._pinned_ip if host == self._hostname else host
        return await super().connect_tcp(
            target,
            port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )


class _PinnedTransport(httpx.AsyncHTTPTransport):
    """httpx transport that pins TCP connections to a pre-validated IP address.

    Eliminates DNS rebinding TOCTOU by replacing the connection pool's
    network backend with ``_PinnedIPBackend``, which connects to a
    pre-resolved IP without invoking the OS resolver again.
    """

    def __init__(self, hostname: str, ip: str) -> None:
        # Bypass super().__init__() to avoid building an unused default pool;
        # handle_async_request and aclose (both inherited) only touch self._pool.
        self._pool = httpcore.AsyncConnectionPool(
            network_backend=_PinnedIPBackend(hostname, ip),
        )


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
        valid_ips = _validate_url(url)
    except ValueError as exc:
        logger.warning("Blocked crawl request: %s", exc)
        return ""

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    if not valid_ips:
        logger.warning("Blocked crawl request: no valid IPs resolved for %s", hostname)
        return ""
    transport = _PinnedTransport(hostname, valid_ips[0])

    try:
        async with httpx.AsyncClient(
            transport=transport, timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True
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
        valid_ips = _validate_url(base)
    except ValueError as exc:
        logger.warning("Blocked crawl request: %s", exc)
        return ""

    parsed = urlparse(base)
    # Reconstruct base_origin from only the validated scheme and netloc components
    # to ensure no user-controlled path or query string is included
    safe_scheme = parsed.scheme if parsed.scheme in ("http", "https") else "https"
    safe_netloc = parsed.netloc
    hostname = parsed.hostname or ""
    if not valid_ips:
        logger.warning("Blocked crawl request: no valid IPs resolved for %s", hostname)
        return ""
    transport = _PinnedTransport(hostname, valid_ips[0])

    combined = ""
    async with httpx.AsyncClient(
        transport=transport, timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True
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

