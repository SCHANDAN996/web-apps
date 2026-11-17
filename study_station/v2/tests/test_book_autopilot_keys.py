from pathlib import Path
from types import SimpleNamespace
import threading

from tools import book_autopilot as pilot


def test_active_workflow_excludes_disabled_secret_refs():
    workflow = (Path(__file__).resolve().parents[3] / '.github/workflows/book-autopilot.yml').read_text()
    assert 'secrets.NVIDIA_API_KEY }}' not in workflow
    assert 'secrets.NVIDIA_API_KEY_2' not in workflow
    assert 'NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY_3 }},${{ secrets.NVIDIA_API_KEY_4 }}' in workflow
    assert '--workers 3' in workflow
    assert 'matrix' not in workflow
    assert 'NVIDIA_MIN_INTERVAL_SECONDS' in workflow
    assert "if: github.ref == 'refs/heads/main'" in workflow
    assert 'if [ "$GITHUB_REF_NAME" != main ]; then' in workflow


def test_worker_pool_uses_only_supplied_active_keys(monkeypatch):
    monkeypatch.setenv('NVIDIA_API_KEY', 'active-three,active-four')
    monkeypatch.setenv('NVIDIA_API_KEY_2', 'disabled-two')
    monkeypatch.setenv('NVIDIA_API_KEY_3', 'active-three')
    monkeypatch.setenv('NVIDIA_API_KEY_4', 'active-four')
    selected = []
    for n in (1, 2, 3):
        monkeypatch.setattr(pilot.threading, 'current_thread', lambda n=n: SimpleNamespace(name=f'W{n}'))
        selected.append(pilot.Pilot.__new__(pilot.Pilot).key_for_worker())
    assert selected == ['active-three', 'active-four', 'active-three']


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
