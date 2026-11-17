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


def test_account_gate_spaces_starts_across_different_keys(tmp_path, monkeypatch):
    monkeypatch.setenv('BOOKGEN_RATE_STATE_DIR', str(tmp_path))
    monkeypatch.setenv('NVIDIA_ACCOUNT_MIN_INTERVAL_SECONDS', '10')
    monkeypatch.setenv('NVIDIA_MIN_INTERVAL_SECONDS', '15')
    monkeypatch.setenv('NVIDIA_MAX_INFLIGHT_PER_KEY', '2')
    now, sleeps = clock(monkeypatch)
    starts = []
    monkeypatch.setattr(nvidia, '_call_once', lambda *a: starts.append(now[0]) or 'ok')
    for key in ('three', 'four', 'three'):
        monkeypatch.setattr(config, 'NVIDIA_API_KEY', key)
        assert nvidia.call('s', 'u') == 'ok'
    assert starts == [100, 110, 120]
    assert sleeps == [10, 10]


def test_pool_rotates_ready_keys_and_counts_starts_without_mutating_config(tmp_path, monkeypatch):
    monkeypatch.setenv('BOOKGEN_RATE_STATE_DIR', str(tmp_path))
    monkeypatch.setenv('NVIDIA_ACCOUNT_MIN_INTERVAL_SECONDS', '10')
    monkeypatch.setenv('NVIDIA_MIN_INTERVAL_SECONDS', '15')
    monkeypatch.setenv('NVIDIA_MAX_INFLIGHT_PER_KEY', '2')
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'private-three, private-four, private-three')
    now, sleeps = clock(monkeypatch)
    selected = []
    monkeypatch.setattr(nvidia, '_call_once', lambda *args: selected.append((args[-1], now[0])) or 'ok')
    for _ in range(4):
        assert nvidia.call('s', 'u') == 'ok'
    assert selected == [('private-three', 100), ('private-four', 110), ('private-three', 120), ('private-four', 130)]
    assert config.NVIDIA_API_KEY == 'private-three, private-four, private-three'
    assert json.loads((tmp_path / 'pool.json').read_text()) == {'last_index': 1, 'starts_by_index': [2, 2]}
    assert all('private-three' not in p.name + p.read_text() and 'private-four' not in p.name + p.read_text()
               for p in tmp_path.iterdir())


def test_pool_429_cooldown_is_respected_before_using_other_key(tmp_path, monkeypatch):
    monkeypatch.setenv('BOOKGEN_RATE_STATE_DIR', str(tmp_path))
    monkeypatch.setenv('NVIDIA_ACCOUNT_MIN_INTERVAL_SECONDS', '10')
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'three,four')
    now, sleeps = clock(monkeypatch)
    with pytest.raises(ai.AIUnavailable, match='rate_limited'):
        with nvidia._request_slot() as key:
            assert key == 'three'
            raise ai.AIUnavailable('rate_limited')
    with nvidia._request_slot() as key:
        assert key == 'four' and now[0] == 160
    assert sleeps == [60]


def test_explicit_pool_key_alone_is_sent_as_authorization(monkeypatch):
    from test_bookgen import FakeStream, sse
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'private-three,private-four')
    seen = []
    def respond(req, timeout):
        seen.append(req.get_header('Authorization'))
        return FakeStream(sse('ठीक'))
    monkeypatch.setattr(nvidia.urllib.request, 'urlopen', respond)
    assert nvidia._call_once('s', 'u', 100, 0, None, 'private-four') == 'ठीक'
    assert seen == ['Bearer private-four']


@pytest.mark.parametrize('retry_after, expected', [(0, 60), (90, 90)])
def test_429_pauses_other_keys_on_shared_account(tmp_path, monkeypatch, retry_after, expected):
    monkeypatch.setenv('BOOKGEN_RATE_STATE_DIR', str(tmp_path))
    monkeypatch.setenv('NVIDIA_ACCOUNT_MIN_INTERVAL_SECONDS', '10')
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'three')
    now, sleeps = clock(monkeypatch)
    with pytest.raises(ai.AIUnavailable, match='rate_limited'):
        with nvidia._request_slot():
            error = ai.AIUnavailable('rate_limited')
            error.retry_after = retry_after
            raise error
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'four')
    with nvidia._request_slot():
        assert now[0] == 100 + expected
    assert sum(sleeps) == expected


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


def test_two_inflight_requests_allowed_but_third_waits_across_processes(tmp_path, monkeypatch):
    import os
    import subprocess
    import sys
    import time
    monkeypatch.setenv('BOOKGEN_RATE_STATE_DIR', str(tmp_path / 'rate'))
    monkeypatch.setenv('NVIDIA_MIN_INTERVAL_SECONDS', '0')
    monkeypatch.setenv('NVIDIA_ACCOUNT_MIN_INTERVAL_SECONDS', '0')
    monkeypatch.setenv('NVIDIA_MAX_INFLIGHT_PER_KEY', '2')
    monkeypatch.setenv('NVIDIA_API_KEY', 'same-private-key')
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'same-private-key')
    started, entered, release = [tmp_path / name for name in ('started', 'entered', 'release')]
    third_started, third_entered = [tmp_path / name for name in ('third-started', 'third-entered')]
    program = '''from pathlib import Path
import sys, time
from app import nvidia
Path(sys.argv[1]).touch()
with nvidia._request_slot():
    Path(sys.argv[2]).touch()
    if len(sys.argv) > 3:
        while not Path(sys.argv[3]).exists():
            time.sleep(0.01)
'''
    def wait_for(path):
        deadline = time.monotonic() + 10
        while not path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert path.exists()
    children = []
    try:
        with nvidia._request_slot():
            children.append(subprocess.Popen([sys.executable, '-c', program, str(started), str(entered), str(release)], env=os.environ.copy()))
            wait_for(entered)                   # second request enters while the first is still in flight
            children.append(subprocess.Popen([sys.executable, '-c', program, str(third_started), str(third_entered)], env=os.environ.copy()))
            wait_for(third_started)
            time.sleep(0.1)
            assert not third_entered.exists() and children[1].poll() is None
        assert children[1].wait(timeout=10) == 0  # a freed slot admits the third, without ending the second
        assert third_entered.exists() and children[0].poll() is None
        release.touch()
        assert children[0].wait(timeout=10) == 0
    finally:
        for proc in children:
            if proc.poll() is None:
                proc.kill()
                proc.wait()


def test_pool_uses_free_other_key_and_caps_both_keys_across_processes(tmp_path, monkeypatch):
    import os
    import subprocess
    import sys
    import time
    monkeypatch.setenv('BOOKGEN_RATE_STATE_DIR', str(tmp_path / 'rate'))
    monkeypatch.setenv('NVIDIA_MIN_INTERVAL_SECONDS', '0')
    monkeypatch.setenv('NVIDIA_ACCOUNT_MIN_INTERVAL_SECONDS', '0')
    monkeypatch.setenv('NVIDIA_MAX_INFLIGHT_PER_KEY', '2')
    monkeypatch.setenv('NVIDIA_API_KEY', 'private-three,private-four')
    # Occupy both slots of key three; child workers receive the full shared pool.
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'private-three')
    release = tmp_path / 'release'
    program = '''from pathlib import Path
import sys, time
from app import nvidia
Path(sys.argv[1]).touch()
with nvidia._request_slot() as key:
    Path(sys.argv[2]).write_text(str(nvidia._configured_keys().index(key)))
    if len(sys.argv) > 3:
        while not Path(sys.argv[3]).exists():
            time.sleep(0.01)
'''
    def wait_for(path):
        deadline = time.monotonic() + 10
        while not path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert path.exists()
    children, markers = [], []
    def start_child(number, hold=True):
        started, entered = [tmp_path / f'{prefix}{number}' for prefix in ('started', 'entered')]
        args = [sys.executable, '-c', program, str(started), str(entered)]
        if hold:
            args.append(str(release))
        proc = subprocess.Popen(args, env=os.environ.copy())
        children.append(proc)
        markers.append(entered)
        wait_for(started)
        return proc, entered
    try:
        with nvidia._request_slot():
            with nvidia._request_slot():
                _, first = start_child(1)
                wait_for(first)
                assert first.read_text() == '1'   # busy key three does not strand the worker
                _, second = start_child(2)
                wait_for(second)
                assert second.read_text() == '1'
                third, entered = start_child(3, hold=False)
                time.sleep(0.1)
                assert not entered.exists() and third.poll() is None  # four total in flight: two per key
            assert third.wait(timeout=10) == 0
            assert entered.read_text() == '0'    # uses the newly freed key-three slot, while key four stays busy
            assert all(proc.poll() is None for proc in children[:2])
        release.touch()
        assert all(proc.wait(timeout=10) == 0 for proc in children)
    finally:
        for proc in children:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
