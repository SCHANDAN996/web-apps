from pathlib import Path
from types import SimpleNamespace

from tools import book_autopilot as pilot


def test_active_workflow_excludes_disabled_secret_refs():
    workflow = (Path(__file__).resolve().parents[3] / '.github/workflows/book-autopilot.yml').read_text()
    assert 'secrets.NVIDIA_API_KEY }}' not in workflow
    assert 'secrets.NVIDIA_API_KEY_2' not in workflow
    assert 'NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY_3 }},${{ secrets.NVIDIA_API_KEY_4 }}' in workflow
    assert '--workers 2' in workflow
    assert 'matrix' not in workflow
    assert 'NVIDIA_MIN_INTERVAL_SECONDS' in workflow


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
