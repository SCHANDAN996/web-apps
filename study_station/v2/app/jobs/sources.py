"""
Where jobs come from.

  official   — the recruiting body's own website/API. Facts can be published.
  discovery  — aggregators' public RSS feeds. Used only to *find* new
               recruitments quickly; we then open the official notice they link
               to and read the facts from there. Nothing is copied from them.

Adding a new board = one entry in SOURCES (most government sites work with the
generic HtmlListingSource). A source that breaks never stops the others.
"""
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

# Domains whose documents count as "official".
OFFICIAL_SUFFIXES = ('.gov.in', '.nic.in', '.ac.in', '.edu.in', '.res.in', '.gov')
OFFICIAL_HOSTS = {
    'ibps.in', 'sbi.co.in', 'bank.sbi', 'rbi.org.in', 'licindia.in', 'nabard.org', 'sidbi.in', 'ntpc.co.in',
    'ongcindia.com', 'bhel.com', 'iocl.com', 'gailonline.com', 'aai.aero', 'bel-india.in', 'hal-india.co.in',
    'powergrid.in', 'coalindia.in', 'nhpcindia.com', 'sail.co.in', 'bsnl.co.in', 'indiapost.gov.in',
    'aiimsexams.ac.in', 'nta.ac.in', 'cdac.in', 'barc.gov.in', 'isro.gov.in', 'drdo.gov.in', 'nhai.gov.in',
    'bankofbaroda.in', 'pnbindia.in', 'canarabank.com', 'unionbankofindia.co.in', 'bankofindia.co.in',
    'centralbankofindia.co.in', 'indianbank.in', 'iob.in', 'ucobank.com', 'bankofmaharashtra.in', 'idbibank.in',
    'nationalinsurance.nic.co.in', 'newindia.co.in', 'uiic.co.in', 'orientalinsurance.org.in', 'epfindia.gov.in',
}
AGGREGATOR_HOSTS = ('freejobalert', 'sarkariresult', 'indgovtjobs', 'sarkari', 'rojgar', 'naukri', 'jagran',
                    'adda247', 'testbook', 'jobriya', 'careerpower', 'govtjobguru', 'fresherslive')


def safe_http_url(url):
    """The URL if it is plain http(s) with a hostname and no user:pass@ part, else None.
    Blocks javascript:/data: links and 'http://ssc.nic.in:@evil.com/' look-alikes."""
    url = (url or '').strip()
    if re.search(r'[\x00-\x20]', url):
        return None
    try:
        p = urlsplit(url)
        p.port                       # raises on garbage ports
    except ValueError:
        return None
    if p.scheme.lower() not in ('http', 'https') or not p.hostname or p.username is not None or p.password is not None:
        return None
    return url


def host_of(url):
    if not safe_http_url(url):
        return ''
    h = urlsplit(url).hostname.lower().rstrip('.')
    return h[4:] if h.startswith('www.') else h


def is_official(url):
    h = host_of(url)
    if not h or any(a in h for a in AGGREGATOR_HOSTS):
        return False
    return h.endswith(OFFICIAL_SUFFIXES) or h in OFFICIAL_HOSTS or any(h.endswith('.' + o) for o in OFFICIAL_HOSTS)


@dataclass
class Item:
    source: str
    kind: str                      # official / discovery
    title: str
    url: str
    org: str | None = None
    category: str | None = None
    published: date | None = None
    doc_urls: list = field(default_factory=list)   # official notice files
    hint_text: str = ''
    origin_host: str = ''                           # discovery: the aggregator's own host


def clean(s):
    return re.sub(r'\s+', ' ', s or '').strip()


# ------------------------------------------------------------------ SSC (official JSON API)
class SSCSource:
    """ssc.gov.in's own notice-board API (the same one its website uses)."""
    kind = 'official'
    API = 'https://ssc.gov.in/api/general-website/portal/records'
    FILES = 'https://ssc.gov.in/api/attachment/'

    def __init__(self, name='ssc', content_types=('notice-boards',), limit=10, pages=4, window_days=120):
        # The API serves 10 records per page regardless of `limit` (or everything at once).
        self.name, self.content_types, self.limit, self.pages = name, content_types, limit, pages
        self.window_days = window_days

    def fetch(self, http):
        items = []
        for ct in self.content_types:
          for page in range(1, self.pages + 1):
            r = http.get(self.API, params={
                'page': page, 'limit': self.limit, 'contentType': ct, 'key': 'createdAt', 'order': 'DESC',
                'isPaginationRequired': 'true', 'isAttachment': 'true', 'language': 'english',
                'attributes': 'id,headline,examId,contentType,startDate,endDate,language,createdAt'},
                headers={'Accept': 'application/json', 'Referer': 'https://ssc.gov.in/'})
            batch = self.parse(r.text)
            items += batch
            if not batch or len(batch) > self.limit:   # API ignored paging and sent everything
                break
        # Keep everything from the last ~4 months — an open recruitment can be weeks old.
        cutoff = date.today() - timedelta(days=self.window_days)
        items = [i for i in items if i.published is None or i.published >= cutoff]
        items.sort(key=lambda i: i.published or date.min, reverse=True)
        return items[:300]

    def parse(self, body):
        import json
        data = json.loads(body).get('data') or []
        out = []
        for rec in data:
            docs = [self.FILES + a['path'].replace('\\', '/') for a in rec.get('attachments') or [] if a.get('path')]
            created = (rec.get('createdAt') or '')[:10]
            out.append(Item(self.name, self.kind, clean(rec.get('headline')),
                            f"https://ssc.gov.in/#notice-{rec.get('id')}",   # stable per notice; files can repeat
                            org='Staff Selection Commission (SSC)', category='ssc',
                            published=date.fromisoformat(created) if created else None, doc_urls=docs))
        return out


# ------------------------------------------------------------------ generic official listing page
LISTING_KW = re.compile(r'recruit|advertis|advt|notification|vacanc|apply|engagement|walk.?in|post of|posts|'
                        r'admit|result|answer key|भर्ती|विज्ञापन|आवेदन|परिणाम', re.I)


class HtmlListingSource:
    """Most board websites list notices as table rows or links. Heuristics, no per-site code."""
    kind = 'official'

    def __init__(self, name, url, org, category=None, max_items=60):
        self.name, self.url, self.org, self.category, self.max_items = name, url, org, category, max_items

    def fetch(self, http):
        r = http.get(self.url)
        return self.parse(r.text, r.url)

    def parse(self, html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        out, seen = [], set()

        def add(title, href, hint=''):
            title = re.sub(r'(\s*(read\s+more|click\s+here|new|अधिक\s+पढ़ें))+$', '', clean(title), flags=re.I)
            if not href or '{{' in title:
                return
            url = safe_http_url(urljoin(base_url, href.strip()))
            if not url:
                return
            if len(title) < 12 or url in seen or not LISTING_KW.search(title + ' ' + hint):
                return
            seen.add(url)
            is_doc = url.lower().split('?')[0].endswith('.pdf') or 'advertisement' in url.lower()
            out.append(Item(self.name, self.kind, title[:300], url, org=self.org, category=self.category,
                            doc_urls=[url] if is_doc else [], hint_text=clean(hint)[:1000]))

        for table in soup.find_all('table'):
            headers = [clean(th.get_text(' ')) for th in table.find_all('th')]
            for tr in table.find_all('tr'):
                links = tr.find_all('a', href=True)
                cells = [clean(td.get_text(' ')) for td in tr.find_all('td')]
                text = clean(tr.get_text(' '))
                if not links or not cells or not LISTING_KW.search(text):
                    continue
                best = max(links, key=lambda a: (a['href'].lower().endswith('.pdf'),
                                                 'advert' in (a.get_text() + a['href']).lower()))
                # "Header: value" pairs let the date extractor see "Last Date ...: 21/10/2026".
                if len(headers) >= len(cells):
                    hint = ' | '.join(f'{h}: {c}' for h, c in zip(headers, cells) if c)
                    named = [c for h, c in zip(headers, cells) if re.search(r'name|post|exam|title|subject|detail|description', h, re.I) and c]
                else:
                    hint, named = text, []
                informative = [c for c in cells if not re.fullmatch(r'[\d/.\-\s,]+', c) and len(c) > 3]
                title = named[0] if named else (max(informative, key=len) if informative else text)
                if len(title) < 25:   # e.g. just an advt number → add the row's other words
                    words = ' '.join(c for c in informative if not re.search(r'apply|view|instruction|click', c, re.I))
                    words = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4}', '', words)
                    title = clean(' '.join(dict.fromkeys(words.replace(',', ' ').split())))
                add(f'{self.org}: {title}' if self.org and self.org.lower() not in title.lower() else title, best['href'], hint)
        for a in soup.find_all('a', href=True):
            if a.find_parent('tr') is None:
                add(a.get_text(' '), a['href'])
        return out[: self.max_items]


# ------------------------------------------------------------------ aggregator RSS (discovery only)
class RSSDiscoverySource:
    kind = 'discovery'

    def __init__(self, name, url, max_items=60):
        self.name, self.url, self.max_items = name, url, max_items

    def fetch(self, http):
        return self.parse(http.get(self.url).content)

    def parse(self, xml_bytes):
        root = ET.fromstring(xml_bytes)
        out = []
        for it in root.iter('item'):
            title, link = clean(it.findtext('title')), safe_http_url(clean(it.findtext('link')))
            pub = None
            try:
                pub = parsedate_to_datetime(it.findtext('pubDate')).date()
            except (TypeError, ValueError):
                pass
            if title and link:
                out.append(Item(self.name, self.kind, title, link, published=pub, origin_host=host_of(self.url)))
        atom = '{http://www.w3.org/2005/Atom}'
        for e in root.iter(atom + 'entry'):
            link = safe_http_url(next((l.get('href') for l in e.findall(atom + 'link') if l.get('rel') in (None, 'alternate')), None))
            title = clean(e.findtext(atom + 'title'))
            if title and link:
                out.append(Item(self.name, self.kind, title, link, origin_host=host_of(self.url)))
        return out[: self.max_items]


def official_links_from_page(html, base_url):
    """On an aggregator article, find links to the official notice / website."""
    soup = BeautifulSoup(html, 'html.parser')
    docs, sites = [], []
    for a in soup.find_all('a', href=True):
        url = safe_http_url(urljoin(base_url, a['href'].strip()))
        if not url or not is_official(url):
            continue
        text = a.get_text(' ').lower()
        if url.lower().split('?')[0].endswith('.pdf') or re.search(r'notification|advertisement|notice|विज्ञापन', text):
            docs.append(url)
        else:
            sites.append(url)
    uniq = lambda xs: list(dict.fromkeys(xs))
    return uniq(docs), uniq(sites)


# ------------------------------------------------------------------ registry
# "checked" = parser verified against the live site while building this.
# Unchecked sources use the generic parser and report health after each run.
SOURCES = [
    SSCSource(),                                                                                         # checked
    HtmlListingSource('isro', 'https://www.isro.gov.in/Careers.html', 'ISRO', 'psu'),                    # checked
    HtmlListingSource('uppsc', 'https://uppsc.up.nic.in/CandidatePages/Notifications.aspx', 'UPPSC', 'psc'),  # checked
    HtmlListingSource('lic', 'https://www.licindia.in/careers', 'LIC', 'psu'),                           # checked
    HtmlListingSource('upsc', 'https://upsc.gov.in/recruitment/recruitment-advertisement', 'UPSC', 'psc'),
    HtmlListingSource('upsc-exams', 'https://upsc.gov.in/examinations/active-examinations', 'UPSC', 'psc'),
    HtmlListingSource('ibps', 'https://www.ibps.in/', 'IBPS', 'banking'),
    HtmlListingSource('rrb-cdg', 'https://www.rrbcdg.gov.in/', 'Railway Recruitment Board', 'railway'),
    HtmlListingSource('bpsc', 'https://bpsc.bihar.gov.in/', 'BPSC', 'psc'),
    HtmlListingSource('rpsc', 'https://rpsc.rajasthan.gov.in/', 'RPSC', 'psc'),
    HtmlListingSource('mppsc', 'https://mppsc.mp.gov.in/', 'MPPSC', 'psc'),
    HtmlListingSource('dsssb', 'https://dsssb.delhi.gov.in/', 'DSSSB', 'govt'),
    RSSDiscoverySource('freejobalert', 'https://www.freejobalert.com/feed/'),                           # checked
    RSSDiscoverySource('indgovtjobs', 'https://www.indgovtjobs.in/feeds/posts/default?alt=rss'),         # checked
]


def enabled_sources(only=None, disabled=()):
    return [s for s in SOURCES if (not only or s.name in only) and s.name not in disabled]
