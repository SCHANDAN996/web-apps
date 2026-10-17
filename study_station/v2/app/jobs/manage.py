"""Maintenance actions used by the CLI and by the AI runbook (JOBS_AGENT.md)."""
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models import Job, JobSource, SeenItem, SourceHealth
from ..services import today_ist
from .extract import categorize, dedupe_key, similar
from .http import Fetcher
from .pipeline import process_item, unique_slug
from .sources import Item, host_of, is_official


class Refused(Exception):
    pass


# ------------------------------------------------------------------ add a researched notice
def add_official(db: Session, url, title=None, org=None, category=None, http=None):
    """Add one recruitment found by research. Only official URLs are accepted —
    facts are then read from that document exactly like the scheduled run."""
    if not is_official(url):
        raise Refused(f'not an official domain: {host_of(url)} (use the board\'s own notice/PDF link)')
    http = http or Fetcher()
    if not title:
        r = http.get(url)
        m = re.search(r'<title[^>]*>(.*?)</title>', r.text if not r.is_pdf else '', re.I | re.S)
        title = re.sub(r'\s+', ' ', m.group(1)).strip() if m else Path(url.split('?')[0]).stem.replace('_', ' ')
    item = Item('research', 'official', title[:300], url, org=org, category=category,
                doc_urls=[url])
    outcome = process_item(db, http, item)
    db.add(SeenItem(source='research', url=url[:500], outcome=outcome[:30])) if not db.scalar(
        select(SeenItem.id).where(SeenItem.source == 'research', SeenItem.url == url)) else None
    db.commit()
    return outcome


# ------------------------------------------------------------------ upcoming (exam calendars)
def parse_expected(text):
    """'2027-04-15' or '2027-04' (month → 1st) → date."""
    m = re.fullmatch(r'(\d{4})-(\d{2})(?:-(\d{2}))?', text.strip())
    if not m:
        raise ValueError('expected date must be YYYY-MM or YYYY-MM-DD')
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1))


def add_upcoming(db: Session, title, org, expected, source_url, category=None):
    """An exam the board's official calendar says will be notified soon."""
    if not is_official(source_url):
        raise Refused(f'calendar must come from an official domain, got {host_of(source_url)}')
    when = parse_expected(expected) if isinstance(expected, str) else expected
    key = dedupe_key(host_of(source_url), title, None) + '|upcoming'
    job = db.scalar(select(Job).where(Job.dedupe_key == key))
    created = job is None
    if created:
        job = Job(slug=unique_slug(db, title + ' upcoming'), dedupe_key=key, title=title, job_type='upcoming',
                  source='calendar')
        db.add(job)
    job.org, job.start_date, job.status = org, when, 'verified'
    job.category = category or categorize(f'{title} {org}')
    job.notification_url, job.official_url = source_url, f'https://{host_of(source_url)}/'
    job.verified_at = job.updated_at = datetime.utcnow()
    db.flush()
    if not db.scalar(select(JobSource.id).where(JobSource.job_id == job.id, JobSource.url == source_url)):
        db.add(JobSource(job_id=job.id, source='calendar', kind='official', url=source_url, title=title[:300]))
    db.commit()
    return 'upcoming:new' if created else 'upcoming:updated'


def resolve_upcoming(db: Session):
    """When the real notification arrives, the 'upcoming' entry is no longer needed."""
    removed = 0
    for up in db.scalars(select(Job).where(Job.job_type == 'upcoming')):
        host = host_of(up.notification_url)
        real = db.scalars(select(Job).where(Job.job_type == 'latest', Job.status == 'verified',
                                            Job.created_at >= datetime.utcnow() - timedelta(days=120)))
        if any(host in (host_of(j.notification_url), host_of(j.official_url)) and similar(j.title, up.title, 0.5)
               for j in real):
            db.delete(up)
            removed += 1
    db.commit()
    return removed


# ------------------------------------------------------------------ cleanup
def drop_legacy(db: Session):
    """Delete jobs imported from the old website feed (aggregator-copied titles, no official notice)."""
    n = 0
    for job in db.scalars(select(Job).where(Job.status == 'legacy')):
        db.delete(job)
        n += 1
    db.commit()
    return n


def cleanup(db: Session, keep_closed_days=30, pending_days=30, today=None):
    """Delete what students no longer need: long-closed jobs, stale unconfirmed items,
    passed calendar entries. Returns counts."""
    today = today or today_ist()
    counts = {'closed': 0, 'pending': 0, 'upcoming_passed': 0, 'updates_old': 0,
              'upcoming_resolved': resolve_upcoming(db), 'legacy': drop_legacy(db)}
    stale = datetime.utcnow() - timedelta(days=pending_days)
    rules = [
        ('closed', (Job.job_type == 'latest') & (Job.last_date < today - timedelta(days=keep_closed_days))),
        ('pending', (Job.status == 'pending') & (Job.created_at < stale)),
        ('upcoming_passed', (Job.job_type == 'upcoming') & (Job.start_date < today - timedelta(days=60))),
        ('updates_old', Job.job_type.in_(('admit', 'results', 'answer')) &
         (Job.created_at < datetime.utcnow() - timedelta(days=90))),
    ]
    for name, cond in rules:
        for job in db.scalars(select(Job).where(cond)):
            db.delete(job)
            counts[name] += 1
    db.commit()
    return counts


# ------------------------------------------------------------------ alerts digest
def digest(db: Session, closing_days=3, upcoming_days=60, today=None):
    """What to tell students now. 'New' = verified and never sent before (notified_at is empty)."""
    today = today or today_ist()
    visible = Job.status == 'verified'
    new = list(db.scalars(select(Job).where(visible, Job.job_type == 'latest', Job.notified_at.is_(None),
                                            or_(Job.last_date.is_(None), Job.last_date >= today))
                          .order_by(Job.last_date)))
    closing = list(db.scalars(select(Job).where(visible, Job.job_type == 'latest', Job.last_date >= today,
                                                Job.last_date <= today + timedelta(days=closing_days))
                              .order_by(Job.last_date)))
    upcoming = list(db.scalars(select(Job).where(Job.job_type == 'upcoming', Job.start_date >= today - timedelta(days=7),
                                                 Job.start_date <= today + timedelta(days=upcoming_days))
                               .order_by(Job.start_date)))
    updates = list(db.scalars(select(Job).where(visible, Job.job_type.in_(('admit', 'results', 'answer')),
                                                Job.notified_at.is_(None)).order_by(Job.created_at.desc())))
    broken = list(db.scalars(select(SourceHealth).where(SourceHealth.consecutive_failures > 0)))
    return {'new': new, 'closing': closing, 'upcoming': upcoming, 'updates': updates, 'broken': broken, 'today': today}


def summary(db: Session, today=None):
    """Machine-readable state for an AI agent: counts + what still needs research."""
    today = today or today_ist()
    from sqlalchemy import func
    count = lambda *c: db.scalar(select(func.count(Job.id)).where(*c))
    pending = db.scalars(select(Job).where(Job.status == 'pending').order_by(Job.created_at.desc()).limit(40))
    return {
        'today': today.isoformat(),
        'open': count(Job.status == 'verified', Job.job_type == 'latest', Job.last_date >= today),
        'open_without_last_date': count(Job.status == 'verified', Job.job_type == 'latest', Job.last_date.is_(None)),
        'upcoming': count(Job.job_type == 'upcoming'),
        'updates': count(Job.status == 'verified', Job.job_type.in_(('admit', 'results', 'answer'))),
        'pending_need_official_link': [{'title': j.title, 'seen_at': [s.url for s in j.sources][:2]} for j in pending],
        'broken_sources': [{'source': h.source, 'error': h.last_error, 'failures': h.consecutive_failures}
                           for h in db.scalars(select(SourceHealth).where(SourceHealth.consecutive_failures > 0))],
    }


def _line(j, site):
    bits = [j.title]
    if j.vacancies:
        bits.append(f'{j.vacancies} पद')
    if j.min_qualification:
        bits.append({'10th': '10वीं', '12th': '12वीं', 'graduate': 'स्नातक'}[j.min_qualification])
    if j.last_date:
        bits.append(f'अंतिम तिथि {j.last_date:%d-%m-%Y}')
    link = f'{site}/jobs/{j.slug}' if site else (j.notification_url or '')
    return ' · '.join(bits) + (f'\n  {link}' if link else '')


def digest_markdown(d, site=''):
    out = [f"# नौकरी अपडेट — {d['today']:%d-%m-%Y}", '']
    sections = [
        ('🆕 नई भर्तियाँ (official नोटिस से)', d['new']),
        ('⏳ जल्द बंद हो रही हैं', d['closing']),
        ('📅 आने वाली भर्तियाँ (official exam calendar)', d['upcoming']),
        ('🎫 एडमिट कार्ड / रिज़ल्ट / आंसर की', d['updates']),
    ]
    for head, jobs in sections:
        out.append(f'## {head} ({len(jobs)})')
        if not jobs:
            out.append('- कुछ नहीं')
        for j in jobs:
            if j.job_type == 'upcoming':
                out.append(f'- {j.title} · {j.org or ""} · अपेक्षित {j.start_date:%B %Y}\n  {j.notification_url}')
            else:
                out.append('- ' + _line(j, site))
        out.append('')
    if d['broken']:
        out.append('## ⚠️ जिन sources से data नहीं आया')
        out += [f'- {h.source}: {h.last_error} (लगातार {h.consecutive_failures} बार)' for h in d['broken']]
        out.append('')
    return '\n'.join(out)


def send_telegram(text, token=None, chat_id=None):
    token = token or os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = chat_id or os.environ.get('TELEGRAM_CHANNEL_ID')
    if not token or not chat_id:
        return 'skipped: TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID not set'
    sent = 0
    for chunk in [text[i:i + 3800] for i in range(0, len(text), 3800)]:   # Telegram limit 4096
        try:
            r = httpx.post(f'https://api.telegram.org/bot{token}/sendMessage', timeout=20,
                           data={'chat_id': chat_id, 'text': chunk, 'disable_web_page_preview': 'true'})
        except httpx.HTTPError as e:
            # The URL contains the bot token — report only the error type.
            raise TelegramError(f'network error ({type(e).__name__})') from None
        if r.status_code != 200:
            try:
                desc = r.json().get('description', '')
            except ValueError:
                desc = ''
            raise TelegramError(f'Telegram HTTP {r.status_code}: {desc[:120]}')
        sent += 1
    return f'sent {sent} message(s)'


class TelegramError(Exception):
    pass


def mark_notified(db: Session, d):
    for j in d['new'] + d['updates']:
        j.notified_at = datetime.utcnow()
    db.commit()
