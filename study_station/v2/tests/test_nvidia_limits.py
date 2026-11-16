"""Shared-key throttling and bounded server cooldowns, without live API calls."""
import json
import urllib.error
from datetime import datetime, timezone
from email.utils import format_datetime

import pytest

from app import ai, config, nvidia


def clock(monkeypatch):
    now, sleeps = [100.0], []
    monkeypatch.setattr(nvidia.time, 'time', lambda: now[0])
    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds
    monkeypatch.setattr(nvidia.time, 'sleep', sleep)
    return now, sleeps


def test_same_key_calls_share_start_spacing_and_keep_key_private(tmp_path, monkeypatch):
    monkeypatch.setenv('BOOKGEN_RATE_STATE_DIR', str(tmp_path))
    monkeypatch.setenv('NVIDIA_MIN_INTERVAL_SECONDS', '15')
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'private-key-three')
    now, sleeps = clock(monkeypatch)
    monkeypatch.setattr(nvidia, '_call_once', lambda *a: 'ok')
    assert nvidia.call('s', 'u') == 'ok'
    assert nvidia.call('s', 'u') == 'ok'
    assert sleeps == [15]
    assert all('private-key-three' not in p.name + p.read_text() for p in tmp_path.iterdir())
    assert json.loads(next(tmp_path.glob('*.json')).read_text()) == {'next_start': 130}


def test_different_keys_do_not_wait_on_each_others_cooldown(tmp_path, monkeypatch):
    monkeypatch.setenv('BOOKGEN_RATE_STATE_DIR', str(tmp_path))
    now, sleeps = clock(monkeypatch)
    monkeypatch.setattr(nvidia, '_call_once', lambda *a: 'ok')
    for key in ('three', 'four'):
        monkeypatch.setattr(config, 'NVIDIA_API_KEY', key)
        assert nvidia.call('s', 'u') == 'ok'
    assert sleeps == []
    assert len(list(tmp_path.glob('*.json'))) == 2


def test_retry_after_shared_cooldown_does_not_double_sleep(tmp_path, monkeypatch):
    monkeypatch.setenv('BOOKGEN_RATE_STATE_DIR', str(tmp_path))
    monkeypatch.setenv('NVIDIA_MIN_INTERVAL_SECONDS', '15')
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'private-key-four')
    now, sleeps = clock(monkeypatch)
    calls = []
    def attempt(*args):
        calls.append(1)
        if len(calls) == 1:
            error = ai.AIUnavailable('rate_limited')
            error.retry_after = 60
            raise error
        return 'recovered'
    monkeypatch.setattr(nvidia, '_call_once', attempt)
    assert nvidia.call('s', 'u') == 'recovered'
    assert len(calls) == 2
    assert sleeps == [60]


@pytest.mark.parametrize('value, expected', [('120', 120), ('9999', 300), ('-5', 0), ('bad', 0)])
def test_retry_after_is_bounded(value, expected):
    assert nvidia._retry_after({'Retry-After': value}) == expected


def test_retry_after_http_date(monkeypatch):
    monkeypatch.setattr(nvidia.time, 'time', lambda: 100)
    date = format_datetime(datetime.fromtimestamp(160, timezone.utc), usegmt=True)
    assert nvidia._retry_after({'Retry-After': date}) == 60


def test_http_429_carries_server_retry_delay(monkeypatch):
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'secret')
    def busy(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 429, 'busy', {'Retry-After': '90'}, None)
    monkeypatch.setattr(nvidia.urllib.request, 'urlopen', busy)
    with pytest.raises(ai.AIUnavailable, match='rate_limited') as caught:
        nvidia._call_once('s', 'u', 100, 0, None)
    assert caught.value.retry_after == 90


def test_key_slot_is_exclusive_between_processes(tmp_path, monkeypatch):
    import os
    import subprocess
    import sys
    import time
    root = tmp_path / 'rate'
    marker = tmp_path / 'entered'
    started = tmp_path / 'started'
    monkeypatch.setenv('BOOKGEN_RATE_STATE_DIR', str(root))
    monkeypatch.setenv('NVIDIA_MIN_INTERVAL_SECONDS', '0')
    monkeypatch.setenv('NVIDIA_API_KEY', 'shared-key')
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'shared-key')
    program = '''from pathlib import Path
import sys
from app import nvidia
Path(sys.argv[1]).touch()
with nvidia._request_slot():
    Path(sys.argv[2]).touch()
'''
    proc = None
    try:
        with nvidia._request_slot():
            proc = subprocess.Popen([sys.executable, '-c', program, str(started), str(marker)], env=os.environ.copy())
            deadline = time.monotonic() + 10
            while not started.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            assert started.exists()
            assert not marker.exists()
            assert proc.poll() is None
        assert proc.wait(timeout=10) == 0
        assert marker.exists()
    finally:
        if proc and proc.poll() is None:
            proc.kill()
            proc.wait()
