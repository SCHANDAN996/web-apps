from pathlib import Path
import subprocess
import pytest

from tools.book_wip import restore_tracked, save_tracked


def git(repo, *args):
    return subprocess.run(['git', *args], cwd=repo, capture_output=True, text=True, check=True)


def repository(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.email', 'test@example.invalid')
    git(repo, 'config', 'user.name', 'Offline test')
    paths = ['study_station/books/Hindi/Chapter_01/Content_hi.txt',
             'study_station/books/AUTOPILOT_STATUS.md', 'study_station/books/autopilot/lane-2.md',
             'source.py']
    for name in paths:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('original\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'fixture')
    return repo, [repo / name for name in paths]


@pytest.mark.parametrize('staged', [False, True])
def test_tracked_book_corrections_survive_restart_without_status_or_source_edits(tmp_path, staged):
    repo, (book, status, lane, code) = repository(tmp_path)
    book.write_text('corrected Hindi lesson\n')
    status.write_text('transient status\n')
    lane.write_text('transient lane\n')
    code.write_text('unrelated source\n')
    if staged:
        git(repo, 'add', '.')
    patch = tmp_path / 'state' / 'tracked-books.patch'
    save_tracked(repo, patch)
    git(repo, 'restore', '--source=HEAD', '--staged', '--worktree', '.')
    assert restore_tracked(repo, patch) is True
    assert book.read_text() == 'corrected Hindi lesson\n'
    assert status.read_text() == lane.read_text() == code.read_text() == 'original\n'
    assert not git(repo, 'diff', '--cached', '--name-only').stdout


def test_conflicting_newer_source_is_not_overwritten_or_partially_applied(tmp_path):
    repo, (book, *_) = repository(tmp_path)
    book.write_text('private correction\n')
    patch = tmp_path / 'tracked-books.patch'
    save_tracked(repo, patch)
    original_patch = patch.read_bytes()
    git(repo, 'restore', '.')
    book.write_text('newer upstream correction\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'upstream correction')
    assert restore_tracked(repo, patch) is False
    assert book.read_text() == 'newer upstream correction\n'
    assert not git(repo, 'status', '--porcelain').stdout
    save_tracked(repo, patch)     # later packing must not erase the rejected correction bytes
    assert next((tmp_path / 'tracked-conflicts').glob('*.patch')).read_bytes() == original_patch


def test_absent_or_empty_patch_is_a_noop(tmp_path):
    repo, _ = repository(tmp_path)
    patch = tmp_path / 'missing.patch'
    assert restore_tracked(repo, patch) is None
    save_tracked(repo, patch)
    assert restore_tracked(repo, patch) is None


def test_restore_ignores_nonbook_and_status_paths_even_in_a_malformed_cache(tmp_path):
    repo, (book, status, lane, code) = repository(tmp_path)
    for path in (book, status, lane, code):
        path.write_text('cached change\n')
    patch = tmp_path / 'unscoped.patch'
    patch.write_bytes(subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=repo))
    git(repo, 'restore', '.')
    assert restore_tracked(repo, patch) is True
    assert book.read_text() == 'cached change\n'
    assert status.read_text() == lane.read_text() == code.read_text() == 'original\n'


def test_cross_boundary_rename_cannot_delete_source_outside_books(tmp_path):
    repo, (_, _, _, code) = repository(tmp_path)
    moved = repo / 'study_station/books/moved.txt'
    git(repo, 'mv', 'source.py', 'study_station/books/moved.txt')
    patch = tmp_path / 'rename.patch'
    patch.write_bytes(subprocess.check_output(['git', 'diff', '--cached', '--binary', 'HEAD'], cwd=repo))
    assert b'rename from source.py' in patch.read_bytes()
    git(repo, 'restore', '--source=HEAD', '--staged', '--worktree', '.')
    assert restore_tracked(repo, patch) is False
    assert code.read_text() == 'original\n' and not moved.exists()
    assert not git(repo, 'status', '--porcelain').stdout
