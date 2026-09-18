"""
Per-day tally of what the trading loop decided, for the evening summary.

main.py calls record() once per council decision -- thousands a day, from one
thread per symbol. Counts live in memory under a lock and are written to
logs/decisions_<IST date>.json at most once a minute, atomically, so
daily_summary.py always reads a whole file. A restart reloads the day's file
and carries on counting instead of starting again from zero.
"""
import json
import os
import re
import threading
import time
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
STATS_DIR = 'logs'
FLUSH_INTERVAL_SEC = 60


def ist_today():
    return datetime.now(IST).strftime('%Y-%m-%d')


def stats_path(day, stats_dir=STATS_DIR):
    return os.path.join(stats_dir, f'decisions_{day}.json')


def reason_bucket(action, reason):
    """Group council reasons that differ only in their numbers."""
    reason = reason or ''
    if action:
        return 'Approved'
    if 'No direction' in reason:
        return 'No direction'
    if 'VETO' in reason:
        return 'Low confidence veto'
    first = reason.split(' | ')[0]
    return re.sub(r'-?\d+(?:\.\d+)?', 'N', first).strip()[:80] or 'Unknown'


class DecisionStats:
    def __init__(self, stats_dir=STATS_DIR, flush_interval=FLUSH_INTERVAL_SEC,
                 clock=time.monotonic, today=ist_today):
        self.stats_dir = stats_dir
        self.flush_interval = flush_interval
        self._clock = clock
        self._today = today
        self._lock = threading.Lock()
        self._day = None
        self._data = None
        self._last_flush = None

    @staticmethod
    def _empty(day):
        return {'date': day, 'decisions': 0, 'actions': {}, 'reasons': {},
                'symbols': {}, 'updated': None}

    def _load(self, day):
        try:
            with open(stats_path(day, self.stats_dir), encoding='utf-8') as f:
                data = json.load(f)
            if data.get('date') == day:
                return data
        except (OSError, ValueError):
            pass
        return self._empty(day)

    def record(self, symbol, score, action, confidence, reason):
        day = self._today()
        with self._lock:
            if day != self._day:
                if self._data is not None:
                    self._write()  # close out the previous day before switching
                self._day, self._data = day, self._load(day)

            d = self._data
            d['decisions'] += 1

            key = action or 'NONE'
            d['actions'][key] = d['actions'].get(key, 0) + 1

            bucket = reason_bucket(action, reason)
            d['reasons'][bucket] = d['reasons'].get(bucket, 0) + 1

            s = d['symbols'].setdefault(
                symbol, {'decisions': 0, 'strongest': None, 'last': None})
            s['decisions'] += 1
            if score is not None:
                score = float(score)
                if score == score:  # skip NaN
                    s['last'] = round(score, 4)
                    if s['strongest'] is None or \
                            abs(score - 0.5) > abs(s['strongest'] - 0.5):
                        s['strongest'] = round(score, 4)

            now = self._clock()
            if self._last_flush is None or now - self._last_flush >= self.flush_interval:
                self._write()
                self._last_flush = now

    def flush(self):
        with self._lock:
            if self._data is not None:
                self._write()

    def _write(self):
        self._data['updated'] = datetime.now(IST).isoformat(timespec='seconds')
        os.makedirs(self.stats_dir, exist_ok=True)
        path = stats_path(self._data['date'], self.stats_dir)
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)


_default = DecisionStats()


def record(symbol, score, action, confidence, reason):
    _default.record(symbol, score, action, confidence, reason)


def flush():
    _default.flush()
