"""Today's Telegram quiz inside the app.

The posted log is written by the GitHub workflow, so the server's copy is only as new as the last deployment.
The app therefore reads the log from the public GitHub branch (cached for 10 minutes) and falls back to the
local copy when GitHub cannot be reached. Posted ids name book questions ("<chapter>#Set03#Q71"); they are
matched to question rows through the import key the seeder gives every book question.
"""
import re
import threading
import time
from datetime import date, timedelta

from sqlalchemy import select

from .. import config
from ..importers import SUBJECT_DIRS
from . import posted as plog

CACHE_SECONDS = 600
_cache = {'at': 0.0, 'data': None}
_lock = threading.Lock()
LEVEL_DIRS = {'10th_Level': '10th', '12th_Level': '12th', 'Graduation_Level': 'graduate'}
POST_ID = re.compile(r'^(?P<level>\w+_Level)/(?P<subject>\w+)/(?:.*/)?Chapter_\d+_(?P<name>[A-Za-z_]+)#Set(?P<set>\d+)#Q(?P<num>\d+)$')


def fetch_log():
    """The workflow-owned posted log: GitHub copy when reachable, else this server's copy. Never written."""
    with _lock:
        if _cache['data'] is not None and time.monotonic() - _cache['at'] < CACHE_SECONDS:
            return _cache['data']
    data = None
    if config.PROMO_POSTED_URL:
        import httpx
        try:
            r = httpx.get(config.PROMO_POSTED_URL, timeout=5, follow_redirects=True,
                          headers={'User-Agent': 'StudyStation/1.0 (+telegram quiz)'})
            if r.status_code == 200:
                body = r.json()
                if isinstance(body, dict) and isinstance(body.get('days'), dict):
                    data = body
        except (httpx.HTTPError, ValueError):
            data = None
    if data is None:
        data = plog.load()
    with _lock:
        _cache.update(at=time.monotonic(), data=data)
    return data


def import_keys(post_id):
    """Possible Question.import_key values for a posted book-question id (see app.seed.seed_questions)."""
    m = POST_ID.match(post_id or '')
    if not m or m['level'] not in LEVEL_DIRS or m['subject'] not in SUBJECT_DIRS:
        return []
    key = (f"{LEVEL_DIRS[m['level']]}/{SUBJECT_DIRS[m['subject']]}/{m['name'].lower().replace('_', '-')}"
           f"/s{int(m['set'])}/q{int(m['num'])}")
    return [key, key + '/hi', key + '/en']


def quiz_for(db, today: date, days_back=2):
    """(day, [question ids]) of the latest day (today, else up to `days_back` days before) that had Telegram
    polls, in posting order; only questions that are live in the app. (None, []) when there is nothing."""
    from ..models import Question
    from ..services import USABLE
    log = fetch_log()
    for back in range(days_back + 1):
        day = today - timedelta(days=back)
        posted = [it.get('id') for batch in log.get('days', {}).get(day.isoformat(), {}).get('quiz', []) for it in batch]
        wanted = {k: pid for pid in posted for k in import_keys(pid)}
        if not wanted:
            continue
        rows = dict(db.execute(select(Question.import_key, Question.id)
                               .where(Question.import_key.in_(list(wanted)), USABLE)).all())
        ids, seen = [], set()
        for pid in posted:
            qid = next((rows[k] for k in import_keys(pid) if k in rows), None)
            if qid and qid not in seen:
                seen.add(qid)
                ids.append(qid)
        if ids:
            return day, ids
    return None, []
