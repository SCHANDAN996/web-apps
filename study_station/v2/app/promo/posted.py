"""The posted-log (study_station/promo/posted.json): which items went out, so nothing is posted twice.

{"telegram": [ids…], "shorts": [ids…], "days": {"2026-10-23": {"quiz": [[{"id", "msg", …}, …], …]}}}
"""
import json
import os
import tempfile
from pathlib import Path

POSTED = Path(os.environ.get('PROMO_POSTED', Path(__file__).resolve().parents[3] / 'promo' / 'posted.json'))
KEEP_IDS = 20000
KEEP_DAYS = 14


def load(path=None):
    p = Path(path or POSTED)
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        data = {}
    data.setdefault('telegram', [])
    data.setdefault('shorts', [])
    data.setdefault('days', {})
    return data


def save(data, path=None):
    """Atomic write: a crash never leaves half a file behind."""
    p = Path(path or POSTED)
    p.parent.mkdir(parents=True, exist_ok=True)
    for key in ('telegram', 'shorts'):
        data[key] = data[key][-KEEP_IDS:]
    data['days'] = {d: v for d, v in sorted(data['days'].items())[-KEEP_DAYS:]}
    fd, tmp = tempfile.mkstemp(dir=p.parent, suffix='.tmp')
    with os.fdopen(fd, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    os.replace(tmp, p)


def batches(data, day, slot):
    """What was posted on `day` in `slot`: a list of batches (one per run), each a list of item dicts."""
    return data['days'].get(day, {}).get(slot, [])


def record(data, day, slot, items, key='telegram'):
    data['days'].setdefault(day, {}).setdefault(slot, []).append(items)
    data[key] += [it['id'] for it in items if it.get('id')]
