"""
The daily decision tally behind the evening Telegram summary.
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.decision_stats import DecisionStats, reason_bucket, stats_path


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def make(tmp_path, day='2026-09-15', clock=None):
    days = {'value': day}
    stats = DecisionStats(stats_dir=str(tmp_path), flush_interval=60,
                          clock=clock or Clock(), today=lambda: days['value'])
    return stats, days


def read(tmp_path, day):
    with open(stats_path(day, str(tmp_path)), encoding='utf-8') as f:
        return json.load(f)


def test_counts_decisions_actions_and_reasons(tmp_path):
    stats, _ = make(tmp_path)
    stats.record('SBIN', 0.41, None, 0.0, 'Neutral signal (0.41) | No direction')
    stats.record('SBIN', 0.48, None, 0.0, 'Neutral signal (0.48) | No direction')
    stats.record('INFY', 0.85, 'BUY', 0.70, 'Technical signal | Macro:NEUTRAL(w0.7)')
    stats.flush()

    data = read(tmp_path, '2026-09-15')
    assert data['decisions'] == 3
    assert data['actions'] == {'NONE': 2, 'BUY': 1}
    assert data['reasons'] == {'No direction': 2, 'Approved': 1}
    assert data['symbols']['SBIN']['decisions'] == 2


def test_strongest_is_the_score_furthest_from_neutral_on_either_side(tmp_path):
    stats, _ = make(tmp_path)
    for score in (0.52, 0.38, 0.60, 0.45):
        stats.record('NIFTY', score, None, 0.0, 'No direction')
    stats.flush()

    sym = read(tmp_path, '2026-09-15')['symbols']['NIFTY']
    assert sym['strongest'] == 0.38   # 0.12 from 0.5 beats 0.60's 0.10
    assert sym['last'] == 0.45


def test_nan_scores_are_counted_but_not_ranked(tmp_path):
    stats, _ = make(tmp_path)
    stats.record('TCS', float('nan'), None, 0.0, 'No direction')
    stats.flush()

    sym = read(tmp_path, '2026-09-15')['symbols']['TCS']
    assert sym['decisions'] == 1
    assert sym['strongest'] is None


def test_writes_are_throttled_but_the_first_record_lands(tmp_path):
    clock = Clock()
    stats, _ = make(tmp_path, clock=clock)

    stats.record('SBIN', 0.40, None, 0.0, 'No direction')
    assert read(tmp_path, '2026-09-15')['decisions'] == 1

    clock.t += 10
    stats.record('SBIN', 0.40, None, 0.0, 'No direction')
    assert read(tmp_path, '2026-09-15')['decisions'] == 1, "wrote again within the interval"

    clock.t += 60
    stats.record('SBIN', 0.40, None, 0.0, 'No direction')
    assert read(tmp_path, '2026-09-15')['decisions'] == 3


def test_a_restart_continues_the_day_instead_of_resetting_it(tmp_path):
    first, _ = make(tmp_path)
    first.record('SBIN', 0.40, None, 0.0, 'No direction')
    first.record('SBIN', 0.40, None, 0.0, 'No direction')
    first.flush()

    second, _ = make(tmp_path)
    second.record('SBIN', 0.40, None, 0.0, 'No direction')
    second.flush()

    assert read(tmp_path, '2026-09-15')['decisions'] == 3


def test_a_new_day_gets_its_own_file_and_closes_out_the_old_one(tmp_path):
    clock = Clock()
    stats, days = make(tmp_path, clock=clock)
    stats.record('SBIN', 0.40, None, 0.0, 'No direction')
    clock.t += 5
    stats.record('SBIN', 0.40, None, 0.0, 'No direction')   # not flushed yet

    days['value'] = '2026-09-16'
    stats.record('SBIN', 0.40, None, 0.0, 'No direction')
    stats.flush()

    assert read(tmp_path, '2026-09-15')['decisions'] == 2
    assert read(tmp_path, '2026-09-16')['decisions'] == 1


def test_reason_buckets_ignore_the_numbers():
    assert reason_bucket(None, 'Neutral signal (0.50) | No direction') == 'No direction'
    assert reason_bucket(None, '⚠️ Quiet market | ❌ Low Confidence VETO (0.12 < 0.6)') \
        == 'Low confidence veto'
    assert reason_bucket('SELL', 'Technical signal | Macro:BEARISH') == 'Approved'
    assert reason_bucket(None, 'Something odd 3.2 | Macro:X') == 'Something odd N'
