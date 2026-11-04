import json
from pathlib import Path

import pytest

from app.promo import instagram as ig


def bundle(tmp_path):
    queue = tmp_path / 'queue'
    queue.mkdir()
    video = queue / '01.mp4'
    video.write_bytes(b'video')
    ig.enqueue('q1', video, 'एक सवाल #StudyStation', '2026-11-05')
    return queue


def test_queue_integrity_and_path_escape(tmp_path):
    queue = bundle(tmp_path)
    assert ig.load_queue(queue)[0]['caption'].startswith('एक सवाल')
    (queue / '01.mp4').write_bytes(b'tampered')
    with pytest.raises(ig.InstagramError, match='checksum'):
        ig.load_queue(queue)
    meta = queue / '01.instagram.json'
    data = json.loads(meta.read_text())
    data['video'] = '../outside.mp4'
    meta.write_text(json.dumps(data))
    with pytest.raises(ig.InstagramError, match='filename'):
        ig.load_queue(queue)


def test_publish_checkpoints_before_share_and_skips_duplicate(tmp_path):
    queue = bundle(tmp_path)
    journal = tmp_path / 'state.json'
    seen = []

    def share(item, checkpoint):
        checkpoint()
        seen.append(json.loads(journal.read_text())['uploads']['studystation:q1']['status'])
        return 'confirmed'

    assert ig.process(queue, journal, 'studystation', share) == 1
    assert seen == ['pending']
    assert ig.process(queue, journal, 'studystation', share) == 0
    assert seen == ['pending']


def test_ambiguous_share_never_retries(tmp_path):
    queue = bundle(tmp_path)
    journal = tmp_path / 'state.json'

    def fail(item, checkpoint):
        checkpoint()
        raise RuntimeError('network lost after Share')

    with pytest.raises(RuntimeError):
        ig.process(queue, journal, 'studystation', fail)
    with pytest.raises(ig.InstagramError, match='reconcile'):
        ig.process(queue, journal, 'studystation', fail)
    ig.reconcile(journal, 'studystation', 'q1', 'retry', None)
    assert json.loads(journal.read_text())['uploads']['studystation:q1']['status'] == 'ready'


def test_failure_before_share_is_retryable_and_lock_is_exclusive(tmp_path):
    queue = bundle(tmp_path)
    journal = tmp_path / 'state.json'
    with ig.locked(journal):
        with pytest.raises(ig.InstagramError, match='locked'):
            with ig.locked(journal):
                pass
    def fail(item, checkpoint):
        raise RuntimeError('login missing')
    with pytest.raises(RuntimeError):
        ig.process(queue, journal, 'studystation', fail)
    assert not journal.exists()


def test_state_must_stay_outside_repository(tmp_path):
    with pytest.raises(ig.InstagramError, match='outside'):
        ig.private_state(Path(ig.__file__).parent / 'profile')
    assert ig.private_state(tmp_path / 'private').is_dir()


def test_corrupt_journal_and_invalid_account_fail_closed(tmp_path):
    queue = bundle(tmp_path)
    journal = tmp_path / 'state.json'
    journal.write_text('broken')
    with pytest.raises(ig.InstagramError, match='journal'):
        ig.process(queue, journal, 'studystation', lambda *_: None)
    with pytest.raises(ig.InstagramError, match='account'):
        ig.account_name('../another')


def test_publish_is_explicitly_disabled_and_check_never_opens_browser(tmp_path, capsys):
    queue = bundle(tmp_path)
    args = ['--account', 'studystation', '--state-dir', str(tmp_path / 'state'), '--queue', str(queue)]
    assert ig.main(['publish', *args]) == 1
    assert 'publishing disabled' in capsys.readouterr().out
    assert ig.main(['check', *args]) == 0
    assert 'nothing published' in capsys.readouterr().out


def test_browser_rejects_wrong_account():
    class Link:
        def wait_for(self, **kw):
            pass
        def get_attribute(self, key):
            return '/another_account/'
    class Page:
        url = 'https://www.instagram.com/'
        def get_by_role(self, *args, **kw):
            return Link()
    class Context:
        pages = [Page()]
    publisher = ig.BrowserPublisher(Context(), 'studystation')
    with pytest.raises(ig.InstagramError, match='does not match'):
        publisher.verify_account()


def test_shorts_render_exports_instagram_queue(monkeypatch, tmp_path):
    from datetime import date
    from types import SimpleNamespace
    from app.promo import __main__ as cli, shorts
    monkeypatch.setattr(shorts, 'pick_shorts', lambda *_: [{'id': 'question1'}])
    monkeypatch.setattr(shorts, 'render', lambda q, path, frames: path.write_bytes(b'rendered'))
    monkeypatch.setattr(shorts, 'caption', lambda q: 'Ready caption')
    monkeypatch.setattr(cli.plog, 'save', lambda data: None)
    args = SimpleNamespace(count=1, level=None, dry_run=False, out=str(tmp_path), telegram=False)
    data = {'shorts': [], 'days': {}, 'telegram': []}
    assert cli.run_shorts(args, date(2026, 11, 5), data) == 0
    item = ig.load_queue(tmp_path)[0]
    assert item['id'] == 'question1' and item['caption'] == 'Ready caption'


def test_state_rejects_another_git_checkout_and_worktree(tmp_path):
    for name, worktree in [('checkout', False), ('worktree', True)]:
        repo = tmp_path / name
        repo.mkdir()
        if worktree:
            (repo / '.git').write_text('gitdir: /elsewhere/worktrees/id')
        else:
            (repo / '.git').mkdir()
        with pytest.raises(ig.InstagramError, match='outside all Git'):
            ig.private_state(repo / 'runtime' / 'instagram')
