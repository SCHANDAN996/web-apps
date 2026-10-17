"""Polite, safe HTTP fetching: robots.txt, per-host spacing, retries, size limits,
and no requests to private/internal addresses (checked on every redirect hop)."""
import ipaddress
import socket
import threading
import time
import urllib.robotparser
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx

from ..config import SITE_URL

USER_AGENT = f"StudyStationBot/1.0 (+{SITE_URL or 'https://studystation.in'}/bot; exam-job alerts)"
HOST_GAP_SEC = 2.0
MAX_BYTES = 12 * 1024 * 1024
MAX_REDIRECTS = 4


class FetchError(Exception):
    pass


@dataclass
class Response:
    url: str
    status: int
    content: bytes
    content_type: str

    @property
    def text(self):
        return self.content.decode('utf-8', errors='replace')

    @property
    def is_pdf(self):
        return 'pdf' in self.content_type or self.content[:5] == b'%PDF-'


def public_ip(ip):
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast
                or ip.is_unspecified)


def public_host(host):
    """True only if every address the name resolves to is a public internet address."""
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError):
        return False
    return bool(infos) and all(public_ip(ipaddress.ip_address(sa[0].split('%')[0])) for *_, sa in infos)


class Fetcher:
    def __init__(self, client=None, respect_robots=True, host_gap=HOST_GAP_SEC, allow_private=False):
        self.client = client or httpx.Client(timeout=30, follow_redirects=False,
                                             headers={'User-Agent': USER_AGENT})
        self.respect_robots = respect_robots
        self.host_gap = host_gap
        self.allow_private = allow_private
        self._robots = {}
        self._last_hit = {}
        self._lock = threading.Lock()

    def _check_url(self, url):
        from .sources import safe_http_url
        if not safe_http_url(url):
            raise FetchError(f'refusing non-http(s) or malformed URL: {url[:120]}')
        host = urlsplit(url).hostname
        if not self.allow_private and not public_host(host):
            raise FetchError(f'refusing private/unresolvable host: {host}')
        if not self._allowed(url):
            raise FetchError(f'robots.txt disallows {url}')

    def _allowed(self, url):
        if not self.respect_robots:
            return True
        parts = urlsplit(url)
        base = f'{parts.scheme}://{parts.netloc}'
        rp = self._robots.get(base)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.client.get(base + '/robots.txt', timeout=10, follow_redirects=True)
                # Missing/forbidden robots.txt → treat as allowed (RFC 9309 §2.3.1.3)
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except httpx.HTTPError:
                rp.parse([])
            self._robots[base] = rp
        return rp.can_fetch(USER_AGENT, url)

    def _wait_turn(self, host):
        with self._lock:
            now = time.monotonic()
            go = max(now, self._last_hit.get(host, 0) + self.host_gap)
            self._last_hit[host] = go
        if go > now:
            time.sleep(go - now)

    def _fetch_once(self, url, params, headers):
        """One request, no redirects followed. Returns (status, location, body, content_type)."""
        with self.client.stream('GET', url, params=params, headers=headers) as r:
            if 300 <= r.status_code < 400 and r.headers.get('location'):
                return r.status_code, r.headers['location'], b'', ''
            if r.status_code >= 400:
                return r.status_code, None, b'', ''
            chunks, size = [], 0
            for chunk in r.iter_bytes():
                size += len(chunk)
                if size > MAX_BYTES:
                    raise FetchError(f'too large: {url}')
                chunks.append(chunk)
            return r.status_code, None, b''.join(chunks), r.headers.get('content-type', '')

    def get(self, url, params=None, headers=None, retries=2):
        last = None
        for attempt in range(retries + 1):
            current, hop_params = url, params
            try:
                for _hop in range(MAX_REDIRECTS + 1):
                    self._check_url(current)
                    self._wait_turn(urlsplit(current).netloc)
                    status, location, body, ctype = self._fetch_once(current, hop_params, headers)
                    if location:
                        current, hop_params = urljoin(current, location), None
                        continue
                    if status in (429, 500, 502, 503, 504):
                        raise FetchError(f'HTTP {status}')
                    if status >= 400:
                        raise _Final(f'HTTP {status} for {url}')
                    return Response(current, status, body, ctype)
                raise _Final(f'too many redirects: {url}')
            except _Final as e:
                raise FetchError(str(e))
            except FetchError as e:
                if 'refusing' in str(e) or 'robots.txt' in str(e) or 'too large' in str(e):
                    raise
                last = e
            except httpx.HTTPError as e:
                last = FetchError(f'{type(e).__name__}: {e}'[:200])
            if attempt < retries:
                time.sleep(2 ** attempt * 3)
        raise last


class _Final(Exception):
    """Non-retryable outcome inside the redirect loop."""
