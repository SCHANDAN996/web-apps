"""Polite HTTP fetching: robots.txt, per-host spacing, retries, size limits."""
import threading
import time
import urllib.robotparser
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx

from ..config import SITE_URL

USER_AGENT = f"StudyStationBot/1.0 (+{SITE_URL or 'https://studystation.in'}/bot; exam-job alerts)"
HOST_GAP_SEC = 2.0
MAX_BYTES = 12 * 1024 * 1024


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


class Fetcher:
    def __init__(self, client=None, respect_robots=True, host_gap=HOST_GAP_SEC):
        self.client = client or httpx.Client(timeout=30, follow_redirects=True,
                                             headers={'User-Agent': USER_AGENT})
        self.respect_robots = respect_robots
        self.host_gap = host_gap
        self._robots = {}
        self._last_hit = {}
        self._lock = threading.Lock()

    def _allowed(self, url):
        if not self.respect_robots:
            return True
        parts = urlsplit(url)
        base = f'{parts.scheme}://{parts.netloc}'
        rp = self._robots.get(base)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.client.get(base + '/robots.txt', timeout=10)
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

    def get(self, url, params=None, headers=None, retries=2):
        if not self._allowed(url):
            raise FetchError(f'robots.txt disallows {url}')
        host = urlsplit(url).netloc
        last = None
        for attempt in range(retries + 1):
            self._wait_turn(host)
            try:
                with self.client.stream('GET', url, params=params, headers=headers) as r:
                    if r.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                        last = FetchError(f'HTTP {r.status_code}')
                        time.sleep(2 ** attempt * 3)
                        continue
                    if r.status_code >= 400:
                        raise FetchError(f'HTTP {r.status_code} for {url}')
                    chunks, size = [], 0
                    for chunk in r.iter_bytes():
                        size += len(chunk)
                        if size > MAX_BYTES:
                            raise FetchError(f'too large: {url}')
                        chunks.append(chunk)
                    return Response(str(r.url), r.status_code, b''.join(chunks), r.headers.get('content-type', ''))
            except httpx.HTTPError as e:
                last = FetchError(f'{type(e).__name__}: {e}'[:200])
                if attempt < retries:
                    time.sleep(2 ** attempt * 3)
        raise last
