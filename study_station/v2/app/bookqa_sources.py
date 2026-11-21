"""Bounded retrieval of explicitly cited public official HTML/text sources; never an AI verdict."""
import hashlib
import io
import ipaddress
import json
import re
import socket
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.robotparser import RobotFileParser

AGENT = 'StudyStationBookQA/1.0 (+https://github.com/SCHANDAN996/web-apps)'
MAX_BYTES = 250_000
OFFICIAL_HOSTS = {'nios.ac.in', 'ignou.ac.in', 'rbi.org.in', 'sbi.co.in', 'ibps.in'}


def official_url(url):
    try:
        u = urlsplit(url)
        h = (u.hostname or '').lower().rstrip('.')
        return (u.scheme == 'https' and not u.username and not u.password and u.port in (None, 443)
                and (h.endswith('.gov.in') or h.endswith('.nic.in') or h in OFFICIAL_HOSTS))
    except ValueError:
        return False


def public_url(url):
    if not official_url(url):
        raise ValueError('not an allowed official HTTPS source')
    host = urlsplit(url).hostname
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
        raise ValueError('non-public source address')


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []; self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self.hidden += 1
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript'):
            self.hidden = max(0, self.hidden - 1)
    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def _read(url):
    public_url(url)
    with build_opener(SafeRedirect()).open(Request(url, headers={'User-Agent': AGENT}), timeout=12) as r:
        public_url(r.geturl())
        kind = r.headers.get_content_type()
        if kind not in ('text/plain', 'text/html', 'application/xhtml+xml', 'application/pdf'):
            raise ValueError('unsupported source format')
        limit = 2_000_000 if kind == 'application/pdf' else MAX_BYTES
        data = r.read(limit + 1)
        if len(data) > limit:
            raise ValueError('source exceeds retrieval limit')
        if kind == 'application/pdf':
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise ValueError('encrypted source PDF')
            return '\n'.join(reader.pages[n].extract_text() or '' for n in range(min(10, len(reader.pages))))[:40000]
        return data.decode(r.headers.get_content_charset() or 'utf-8', errors='strict')


def fetch_excerpt(url):
    public_url(url)
    robots_url = urljoin(url, '/robots.txt')
    # Fail closed when robots cannot be read; no silent bypass of site policy.
    robots = RobotFileParser(); robots.set_url(robots_url)
    robots.parse(_read(robots_url).splitlines())
    if not robots.can_fetch(AGENT, url):
        raise ValueError('robots disallows source retrieval')
    delay = robots.crawl_delay(AGENT) or robots.crawl_delay('*')
    if delay:
        raise ValueError('site requires crawl delay; defer to reference lane')
    parser = PlainText(); parser.feed(_read(url))
    text = re.sub(r'\s+', ' ', ' '.join(parser.parts)).strip()
    if len(text) < 80:
        raise ValueError('source text too short')
    # Bounded evidence, never claim the unseen remainder was reviewed.
    return text[:16000]


def refresh(chapter, max_urls=2, out=print):
    """Fetch explicit URLs only. Absence/failure remains a reference blocker downstream."""
    from .bookcheck import section_files, is_prompt
    chapter = Path(chapter)
    target = chapter / 'QA.references.json'
    if target.is_symlink():
        raise ValueError('reference evidence must not be a symlink')
    try:
        data = json.loads(target.read_text(encoding='utf-8'))
        entries = data['sources']
        if not isinstance(entries, list):
            entries = []
        attempts = data.get('attempts', {})
        if not isinstance(attempts, dict):
            attempts = {}
    except (OSError, ValueError, KeyError, TypeError):
        entries = []
        attempts = {}
    count = 0; cache = {}; changed = False
    for name, path in sorted(section_files(chapter).items()):
        raw = path.read_bytes()
        content = raw.decode('utf-8')
        if is_prompt(content):
            continue
        sha = hashlib.sha256(raw).hexdigest()
        claims = re.findall(r'^\s*(?:Source|स्रोत)\s*[:：]\s*(.+)$', content, re.M | re.I)
        for claim in dict.fromkeys(c.strip() for c in claims):
            for url in re.findall(r'https://[^\s<>\]\)]+', claim):
                url = url.rstrip('.,;।')
                if not official_url(url):
                    continue
                if any(isinstance(e, dict) and e.get('file') == name and e.get('content_sha') == sha
                       and e.get('claim') == claim and e.get('url') == url and e.get('verified_by') == 'official-fetch'
                       and e.get('verified') is True and isinstance(e.get('excerpt'), str)
                       and e.get('sha256') == hashlib.sha256(e['excerpt'].encode()).hexdigest()
                       for e in entries):
                    continue
                if url not in cache:
                    if count >= max_urls:
                        continue
                    previous = attempts.get(url, {})
                    if isinstance(previous, dict) and isinstance(previous.get('at'), (int, float)) and time.time() - previous['at'] < 86400:
                        continue
                    count += 1
                    attempts[url] = {'at': time.time()}
                    changed = True
                    try:
                        cache[url] = fetch_excerpt(url)
                    except Exception as exc:
                        cache[url] = None
                        out(f'reference deferred: {type(exc).__name__}')
                excerpt = cache[url]
                if not excerpt:
                    continue
                entries.append({'file': name, 'content_sha': sha, 'claim': claim, 'url': url,
                                'excerpt': excerpt, 'sha256': hashlib.sha256(excerpt.encode()).hexdigest(),
                                'fetched_at': datetime.now(timezone.utc).isoformat(), 'verified': True,
                                'verified_by': 'official-fetch'})
                changed = True
    if changed:
        from .books import atomic_write
        atomic_write(target, json.dumps({'version': 1, 'sources': entries, 'attempts': attempts}, ensure_ascii=False, indent=2))
    return count
