from pathlib import Path
from types import SimpleNamespace
import threading
import json

from tools import book_autopilot as pilot


def test_active_workflow_excludes_disabled_secret_refs():
    workflow = (Path(__file__).resolve().parents[3] / '.github/workflows/book-autopilot.yml').read_text()
    assert 'secrets.NVIDIA_API_KEY }}' not in workflow
    assert 'secrets.NVIDIA_API_KEY_2' not in workflow
    assert 'NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY_3 }},${{ secrets.NVIDIA_API_KEY_4 }}' in workflow
    assert '--workers 4' in workflow
    assert "NVIDIA_ACCOUNT_MIN_INTERVAL_SECONDS: '20'" in workflow
    assert "NVIDIA_MAX_INFLIGHT_PER_KEY: '1'" in workflow
    assert 'BOOKGEN_RATE_POLICY: parallel-v2' in workflow
    assert 'matrix' not in workflow
    assert 'NVIDIA_MIN_INTERVAL_SECONDS' in workflow
    assert "if: github.ref == 'refs/heads/main'" in workflow
    assert 'if [ "$GITHUB_REF_NAME" != main ]; then' in workflow


def test_every_worker_receives_both_active_keys_for_dynamic_request_routing(tmp_path, monkeypatch):
    monkeypatch.setenv('NVIDIA_API_KEY', 'active-three,active-four')
    monkeypatch.setenv('NVIDIA_API_KEY_2', 'disabled-two')
    monkeypatch.setenv('NVIDIA_API_KEY_3', 'active-three')
    monkeypatch.setenv('NVIDIA_API_KEY_4', 'active-four')
    received = []
    class Process:
        returncode = 0
        stdout = ['2026 WARNING NVIDIA rate_limited — retrying in 60s']
        def __init__(self, *args, **kwargs):
            received.append(kwargs['env']['NVIDIA_API_KEY'])
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    monkeypatch.setattr(pilot.subprocess, 'Popen', Process)
    p = pilot.Pilot.__new__(pilot.Pilot)
    p.state_dir = tmp_path
    p.log = lambda *a: None
    for n in (1, 2, 3, 4):
        monkeypatch.setattr(pilot.threading, 'current_thread', lambda n=n: SimpleNamespace(name=f'W{n}'))
        lines, bad = p.bookgen(tmp_path / 'Chapter_01_topic')
        assert 'rate_limited' in lines[0] and not bad
    assert received == ['active-three,active-four'] * 4


def test_failed_chapter_waits_while_other_chapters_continue(tmp_path, monkeypatch):
    args = SimpleNamespace(state_dir=str(tmp_path / 'state'), stop_file=None, retry_delay=30,
                           stop_new_after=0, max_fails=4, dry_run=False, status_file=None)
    p = pilot.Pilot(args)
    chapters = [pilot.bookcheck.BOOKS_ROOT / name for name in ('first', 'second')]
    monkeypatch.setattr(pilot.time, 'time', lambda: 1000)
    monkeypatch.setattr(p, 'chapters', lambda: iter(chapters))
    monkeypatch.setattr(p, 'manual_chapters', lambda: set())
    monkeypatch.setattr(p, 'audit_chapters', lambda: set())
    monkeypatch.setattr(p, 'taken_by_other', lambda ch: False)
    monkeypatch.setattr(pilot.bookcheck, 'chapter_status', lambda ch: ('TODO', ['missing'], []))
    p.record_failure('first')
    assert p.state['failed']['first'] == 1
    assert p.state['retry_after']['first'] == 2800
    assert p.next_job() == (chapters[1], 'second')
    # Persist the cooldown across a process restart, but do not permanently abandon the chapter.
    p = pilot.Pilot(args)
    monkeypatch.setattr(p, 'chapters', lambda: iter(chapters))
    monkeypatch.setattr(p, 'manual_chapters', lambda: set())
    monkeypatch.setattr(p, 'audit_chapters', lambda: set())
    monkeypatch.setattr(p, 'taken_by_other', lambda ch: False)
    monkeypatch.setattr(pilot.time, 'time', lambda: 2801)
    assert p.next_job() == (chapters[0], 'first')


def test_worker_exception_counts_toward_failure_budget(monkeypatch):
    p = pilot.Pilot.__new__(pilot.Pilot)
    p.args = SimpleNamespace(dry_run=False)
    p.stop_file = SimpleNamespace(exists=lambda: False)
    p.lock, p.current, p.claimed = threading.Lock(), {}, {'broken'}
    jobs = iter([(Path('broken'), 'broken'), None])
    monkeypatch.setattr(p, 'next_job', lambda: next(jobs))
    monkeypatch.setattr(p, 'step', lambda *a: None)
    monkeypatch.setattr(p, 'work', lambda *a: (_ for _ in ()).throw(RuntimeError('failed')))
    failures = []
    monkeypatch.setattr(p, 'record_failure', failures.append)
    monkeypatch.setattr(p, 'log', lambda *a: None)
    p.worker(1)
    assert failures == ['broken']
    assert not p.claimed


def test_pool_usage_labels_survive_an_empty_key_without_exposing_keys(tmp_path, monkeypatch):
    monkeypatch.setenv('BOOKGEN_RATE_STATE_DIR', str(tmp_path))
    monkeypatch.setenv('NVIDIA_API_KEY_LABELS', '3,4')
    monkeypatch.setenv('NVIDIA_API_KEY', 'private-three,private-four')
    path = tmp_path / 'pool.json'
    path.write_text(json.dumps({'starts_by_index': [7, 6]}))
    p = pilot.Pilot.__new__(pilot.Pilot)
    assert p.api_pool_usage() == [('3', 7), ('4', 6)]
    monkeypatch.setenv('NVIDIA_API_KEY', ',private-four')
    path.write_text(json.dumps({'starts_by_index': [8]}))
    assert p.api_pool_usage() == [('4', 8)]
    path.write_text('partial write')
    assert p.api_pool_usage() == []
