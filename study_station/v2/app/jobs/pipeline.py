"""
fetch every source → skip already-seen items → classify → (discovery: find the
official notice) → read facts from the official document → merge into one Job
→ record source health.  Run every few hours from cron (see README).
"""
import logging
import re
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Job, JobSource, SeenItem, SourceHealth
from ..seed import slugify
from .extract import (categorize, classify, dedupe_key, extract_facts, html_text, is_academic,
                      is_roundup, pdf_text, qualification, similar, tokens)
from .http import FetchError, Fetcher
from .sources import Item, enabled_sources, host_of, is_official, official_links_from_page

log = logging.getLogger('jobs')
FACT_FIELDS = ('start_date', 'last_date', 'vacancies', 'age_min', 'age_max', 'min_qualification', 'advt_no')
KEEP_TYPES = {'latest', 'admit', 'results', 'answer'}


def resolve_discovery(http: Fetcher, item: Item):
    """Open the aggregator's article only to find the official notice link."""
    r = http.get(item.url)
    docs, sites = official_links_from_page(r.text, r.url)
    item.doc_urls = docs[:3]
    return sites[0] if sites else None


def find_existing(db: Session, key, title, notification_url, org_host, kind='discovery'):
    if notification_url:
        j = db.scalar(select(Job).where(Job.notification_url == notification_url))
        if j:
            return j
    j = db.scalar(select(Job).where(Job.dedupe_key == key))
    if j:
        return j
    if kind == 'official':
        # Each official notice is its own record ("Typing Test result" ≠ "Stenography Test result");
        # only an identical document or advt no. above merges official items.
        return None
    # An aggregator headline: same organisation, similar title, seen recently → same recruitment.
    since = datetime.utcnow() - timedelta(days=120)
    for cand in db.scalars(select(Job).where(Job.created_at >= since, Job.status != 'legacy')):
        same_org = org_host and org_host in (host_of(cand.notification_url), host_of(cand.official_url))
        if (same_org or not org_host) and similar(cand.title, title):
            return cand
    return None


def unique_slug(db, title):
    base = slugify(title)
    slug, n = base, 2
    while db.scalar(select(Job.id).where(Job.slug == slug)):
        slug, n = f'{base}-{n}', n + 1
    return slug


def upsert(db: Session, item: Item, job_type, facts, notification_url, official_url, verified):
    org_host = host_of(notification_url or official_url) or None
    key = dedupe_key(org_host or item.source, item.title, facts.get('advt_no'))
    job = find_existing(db, key, item.title, notification_url, org_host, item.kind)
    created = job is None
    if created:
        job = Job(slug=unique_slug(db, item.title), title=item.title, dedupe_key=key, status='pending',
                  job_type=job_type, source=item.source)
        db.add(job)
    # Official wording wins over an aggregator's headline.
    if item.kind == 'official' and job.source != item.source and job.status != 'verified':
        job.title, job.source = item.title, item.source
    job.org = job.org or item.org
    job.category = item.category or (job.category if not created else None) or categorize(f'{item.title} {item.org or ""} {org_host or ""}')
    if verified:
        for f in FACT_FIELDS:                     # official facts overwrite
            if facts.get(f) is not None:
                setattr(job, f, facts[f])
        job.status, job.verified_at = 'verified', datetime.utcnow()
        job.notification_url = notification_url or job.notification_url
    else:
        for f in FACT_FIELDS:                     # never overwrite with unverified data
            if getattr(job, f) is None and facts.get(f) is not None and job.status != 'verified':
                setattr(job, f, facts[f])
    if job.last_date:
        job.last_date_text = job.last_date.strftime('%d-%m-%Y')
    job.official_url = job.official_url or official_url
    job.updated_at = datetime.utcnow()
    db.flush()
    if not db.scalar(select(JobSource.id).where(JobSource.job_id == job.id, JobSource.url == item.url)):
        db.add(JobSource(job_id=job.id, source=item.source, kind=item.kind, url=item.url, title=item.title[:300]))
    return job, created


def _official_pdf_links(html, base_url):
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    soup = BeautifulSoup(html, 'html.parser')
    out = []
    for a in soup.find_all('a', href=True):
        url = urljoin(base_url, a['href'])
        if url.lower().split('?')[0].endswith('.pdf') and is_official(url):
            text = (a.get_text(' ') + ' ' + a['href']).lower()
            score = 2 if re.search(r'advert|notification|detailed|bilingual|विज्ञापन', text) else 1
            out.append((score, url))
    return [u for _, u in sorted(out, key=lambda x: -x[0])]


def relevant(text, title, advt=None):
    """Is this page really about the item (not a generic home page)?"""
    low = text.lower()
    if advt and advt.lower() in low:
        return True
    words = tokens(title)
    return bool(words) and sum(w in low for w in words) / len(words) >= 0.5


def read_official(http: Fetcher, urls, title='', advt=None):
    """Read the first official document that yields text; follow one HTML → PDF hop."""
    for url in urls:
        if not is_official(url):
            continue
        try:
            r = http.get(url)
        except FetchError as e:
            log.info('doc failed %s: %s', url, e)
            continue
        if r.is_pdf:
            text = pdf_text(r.content)
            if text.strip():
                return text, url
            continue
        text = html_text(r.text)
        if not relevant(text, title, advt):
            log.info('page not about this item, ignoring %s', url)
            continue
        facts = extract_facts(text)
        if not facts['last_date']:
            for pdf in _official_pdf_links(r.text, r.url)[:1]:
                try:
                    pr = http.get(pdf)
                    if pr.is_pdf and (pt := pdf_text(pr.content)).strip():
                        return text + '\n' + pt, pdf
                except FetchError as e:
                    log.info('pdf failed %s: %s', pdf, e)
        if text.strip():
            return text, url
    return None, None


def process_item(db: Session, http: Fetcher, item: Item):
    job_type = classify(item.title)
    if job_type not in KEEP_TYPES:
        return f'skipped:{job_type or "unrelated"}'
    if is_academic(item.title):
        return 'skipped:academic'
    if item.kind == 'discovery' and is_roundup(item.title):
        return 'skipped:roundup'
    official_url = None
    if item.kind == 'discovery':
        official_url = resolve_discovery(http, item)
        candidates = item.doc_urls
    else:
        candidates = item.doc_urls or [item.url]

    row_facts = extract_facts(item.hint_text) if item.hint_text else {}
    text, notification_url = read_official(http, candidates, item.title, row_facts.get('advt_no'))
    verified = text is not None
    if not verified and item.kind == 'official' and is_official(item.url):
        # Listing row from the official site itself: the title is official,
        # facts can only come from the row text.
        notification_url, verified = item.url, True
    facts = extract_facts(text or '')
    # The notice title often states the level outright: "Combined Higher Secondary (10+2) Level".
    facts['min_qualification'] = qualification(item.title) or facts['min_qualification']
    for k, v in row_facts.items():            # the row on the official listing is the most specific
        if v is not None:
            facts[k] = v
    if job_type != 'latest':
        # Results / admit cards / answer keys: application facts don't apply.
        facts = {'advt_no': facts.get('advt_no')}
    if item.kind == 'official':
        official_url = official_url or f'https://{host_of(item.url)}/'
    job, created = upsert(db, item, job_type, facts, notification_url, official_url, verified)
    return 'job:new' if created else 'job:merged'


def run(db: Session, sources=None, http: Fetcher | None = None, max_new_per_source=40, dry_run=False):
    http = http or Fetcher()
    report = {}
    for src in sources if sources is not None else enabled_sources():
        health = db.get(SourceHealth, src.name) or SourceHealth(source=src.name, consecutive_failures=0, last_items=0)
        health.last_run = datetime.utcnow()
        stats = {'items': 0, 'new': 0, 'merged': 0, 'skipped': 0, 'errors': 0}
        try:
            items = src.fetch(http)
        except Exception as e:                       # one broken site never stops the run
            health.consecutive_failures = (health.consecutive_failures or 0) + 1
            health.last_error = f'{type(e).__name__}: {e}'[:300]
            db.add(health)
            db.commit()
            report[src.name] = {'error': health.last_error}
            continue
        stats['items'] = len(items)
        seen = set(db.scalars(select(SeenItem.url).where(SeenItem.source == src.name)))
        todo = []
        for i in items:                       # skip seen, and duplicates within this batch
            if i.url not in seen:
                seen.add(i.url)
                todo.append(i)
        todo = todo[:max_new_per_source]
        for item in todo:
            try:
                outcome = process_item(db, http, item)
            except Exception as e:
                log.warning('item failed %s: %s', item.url, e)
                outcome = 'error'
                db.rollback()
            key = outcome.split(':')[-1] if outcome.startswith('job') else ('errors' if outcome == 'error' else 'skipped')
            stats[key] = stats.get(key, 0) + 1
            if outcome != 'error':           # errors are retried next run
                db.add(SeenItem(source=src.name, url=item.url[:500], outcome=outcome[:30]))
            if dry_run:
                db.rollback()
            else:
                db.commit()
        health.last_ok, health.last_error = datetime.utcnow(), None
        health.consecutive_failures, health.last_items = 0, len(items)
        db.add(health)
        db.commit()
        report[src.name] = stats
    return report

