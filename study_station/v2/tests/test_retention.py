"""Retention boundaries and filesystem isolation (uses only tmp_path)."""
import importlib.util
from pathlib import Path
import os
import pytest

spec = importlib.util.spec_from_file_location('ss_retention', Path(__file__).parents[1] / 'deploy' / 'retention.py')
retention = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retention)


def setup_roots(monkeypatch, tmp_path):
    backup, snapshots, logs, nginx = [tmp_path / name for name in ('backup', 'snapshots', 'logs', 'nginx')]
    for root in (backup, snapshots, logs, nginx):
        root.mkdir()
    monkeypatch.setattr(retention, 'BACKUP_ROOTS', (backup, snapshots))
    monkeypatch.setattr(retention, 'LOG_ROOT', logs)
    monkeypatch.setattr(retention, 'LOG_FILES', (nginx / 'study.log',))
    monkeypatch.setattr(retention, 'LEGACY_LOG_FILES', (nginx / 'legacy-error.log',))
    return backup, snapshots, logs, nginx


def aged(path, stamp):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('isolated fixture')
    os.utime(path, (stamp, stamp))
    return path


def test_expires_backup_snapshots_at_conservative_boundary(monkeypatch, tmp_path):
    backup, snapshots, logs, nginx = setup_roots(monkeypatch, tmp_path)
    now = 2_000_000_000
    cutoff = now - retention.EXPIRE_SECONDS
    old = aged(backup / 'studystation.db.gz', cutoff)
    env = aged(snapshots / 'phase' / 'env-before', cutoff - 1)
    fresh = aged(backup / 'fresh.db.gz', cutoff + 1)
    live = aged(logs / 'jobs.log', cutoff - 1)
    unrelated = aged(tmp_path / 'other-app.db', cutoff - 1)
    archive = aged(logs / 'jobs.log.1', cutoff - 1)
    legacy = aged(nginx / 'legacy-error.log', cutoff - 1)
    assert retention.candidates(now) == sorted([old, env, archive, legacy])
    assert all(p.exists() for p in (old, env, fresh, live, unrelated, archive))


def test_never_follows_symlinks_or_expired_archive_links(monkeypatch, tmp_path):
    backup, snapshots, logs, nginx = setup_roots(monkeypatch, tmp_path)
    outside = aged(tmp_path / 'outside' / 'private.db', 1)
    # Model symlink metadata without requiring Windows administrator privileges.
    escape = backup / 'escape'
    escape.mkdir()
    archive_link = aged(logs / 'jobs.log.1', 1)
    original_lstat = Path.lstat
    def symlink_metadata(path, *args, **kwargs):
        data = original_lstat(path, *args, **kwargs)
        if path in (escape, archive_link):
            values = list(data)
            values[0] = 0o120777
            return os.stat_result(values)
        return data
    monkeypatch.setattr(Path, 'lstat', symlink_metadata)
    assert retention.candidates(2_000_000_000) == []
    monkeypatch.setattr(retention, 'BACKUP_ROOTS', (backup / 'escape',))
    with pytest.raises(ValueError, match='Symlink'):
        retention.candidates(2_000_000_000)


def test_apply_only_vacuums_app_namespace(monkeypatch, tmp_path, capsys):
    backup, _, _, _ = setup_roots(monkeypatch, tmp_path)
    old = aged(backup / 'old.db', 1)
    commands = []
    # Real dir_fd/O_NOFOLLOW operation is Linux-specific; the CLI behavior is
    # isolated here, and its descriptor traversal has a separate unit check.
    monkeypatch.setattr(retention, 'unlink_expired', lambda path, cutoff: path.unlink())
    monkeypatch.setattr(retention.subprocess, 'run', lambda cmd, **kw: commands.append(cmd))
    monkeypatch.setattr('sys.argv', ['retention.py'])
    retention.main()
    assert old.exists() and commands == []
    monkeypatch.setattr('sys.argv', ['retention.py', '--apply'])
    retention.main()
    assert not old.exists()
    assert len(commands) == 2
    assert all('--namespace=studystation' in cmd for cmd in commands)


def test_unlink_resolves_each_parent_with_nofollow(monkeypatch):
    from types import SimpleNamespace
    opens, deletes, closes = [], [], []
    monkeypatch.setattr(retention.os, 'O_DIRECTORY', 0x10000, raising=False)
    monkeypatch.setattr(retention.os, 'O_NOFOLLOW', 0x20000, raising=False)
    def open_descriptor(path, flags, **kwargs):
        opens.append((path, flags, kwargs))
        return 20 + len(opens)
    monkeypatch.setattr(retention.os, 'open', open_descriptor)
    monkeypatch.setattr(retention.os, 'close', closes.append)
    monkeypatch.setattr(retention.os, 'stat', lambda *args, **kwargs: SimpleNamespace(st_mode=0o100600, st_mtime=1))
    monkeypatch.setattr(retention.os, 'unlink', lambda *args, **kwargs: deletes.append((args, kwargs)))
    # PurePosixPath keeps the Linux path layout when the test host is Windows.
    from pathlib import PurePosixPath
    retention.unlink_expired(PurePosixPath('/var/backups/studystation/old.db'), 2)
    assert [entry[0] for entry in opens] == ['/', 'var', 'backups', 'studystation']
    assert all(flags & retention.os.O_NOFOLLOW for _, flags, _ in opens)
    assert deletes == [(('old.db',), {'dir_fd': 24})]
    assert len(closes) == len(opens)
