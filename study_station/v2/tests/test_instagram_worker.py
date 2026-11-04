import io
import json
import zipfile

import pytest

from app.promo import instagram as ig
from app.promo import instagram_worker as worker


def run(**changes):
    value = dict(id=42, run_number=7, head_repository={'full_name': worker.REPOSITORY},
                 path='.github/workflows/promo-shorts.yml', head_branch=worker.BRANCH,
                 event='schedule', status='completed', conclusion='success')
    value.update(changes)
    return value


@pytest.mark.parametrize('change', [dict(event='pull_request'), dict(head_branch='main'),
                                  dict(head_repository={'full_name': 'attacker/web-apps'}),
                                  dict(path='.github/workflows/untrusted.yml'), dict(conclusion='failure')])
def test_discovery_rejects_untrusted_run(change):
    assert worker.trusted(run())
    assert not worker.trusted(run(**change))


def callback(**changes):
    value = {'from': {'id': 99}, 'message': {'message_id': 5, 'chat': {'type': 'private', 'id': 99}},
             'data': 'ig:42:randomnonce:yes'}
    value.update(changes)
    return {'update_id': 1, 'callback_query': value}


def record():
    return {'42': {'status': 'waiting', 'nonce': 'randomnonce', 'message_id': 5}}


@pytest.mark.parametrize('change', [{'from': {'id': 88}}, {'data': 'ig:42:wrongnonce:yes'},
                                  {'message': {'message_id': 6, 'chat': {'type': 'private', 'id': 99}}},
                                  {'message': {'message_id': 5, 'chat': {'type': 'group', 'id': 99}}}])
def test_callback_cannot_be_spoofed(change):
    records = record()
    assert not worker.apply_callback(callback(**change), records, '99')
    assert records['42']['status'] == 'waiting'


def test_approval_reject_and_replay():
    records = record()
    assert worker.apply_callback(callback(), records, '99')
    assert records['42']['status'] == 'approved'
    assert not worker.apply_callback(callback(data='ig:42:randomnonce:no'), records, '99')
    rejected = record()
    assert worker.apply_callback(callback(data='ig:42:randomnonce:no'), rejected, '99')
    assert rejected['42']['status'] == 'rejected'


def test_zip_traversal_and_expansion_limit(tmp_path):
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, 'w') as archive:
        archive.writestr('../escape.mp4', b'bad')
    with pytest.raises(ig.InstagramError):
        worker.unpack(raw.getvalue(), tmp_path / 'queue')
    assert not (tmp_path / 'escape.mp4').exists()


def make_queue(folder):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / '01.mp4'
    path.write_bytes(b'video')
    ig.enqueue('question1', path, 'Original caption', '2026-11-05')


class Bot:
    chat_id = '99'

    def __init__(self, updates=()):
        self.updates = updates

    def call(self, method, **kwargs):
        return self.updates if method == 'getUpdates' else {}


def test_first_start_baselines_history_without_publish(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, 'discover', lambda: [run()])
    monkeypatch.setattr(worker, 'download', lambda *args: pytest.fail('historical download'))
    worker.cycle(tmp_path, Bot(), 'studystationhindi', lambda folder: pytest.fail('historical publish'))
    data = json.loads((tmp_path / 'batches.json').read_text())
    assert data['runs']['42']['status'] == 'baseline'


def prepare_approved(tmp_path):
    folder = tmp_path / 'queue' / '42'
    make_queue(folder)
    data = {'account': 'studystationhindi', 'initialized': True, 'offset': 0,
            'runs': {'42': {'status': 'approved', 'digest': worker.queue_digest(folder)}}}
    ig.atomic_json(tmp_path / 'batches.json', data)
    return folder


def test_approval_binds_content_and_blocks_modified_batch(tmp_path, monkeypatch):
    folder = prepare_approved(tmp_path)
    path = folder / '01.instagram.json'
    changed = json.loads(path.read_text())
    changed['caption'] = 'Substituted caption'
    ig.atomic_json(path, changed)
    monkeypatch.setattr(worker, 'discover', lambda: [])
    with pytest.raises(ig.InstagramError, match='blocked'):
        worker.cycle(tmp_path, Bot(), 'studystationhindi', lambda folder: pytest.fail('tampered publish'))
    assert json.loads((tmp_path / 'batches.json').read_text())['runs']['42']['status'] == 'blocked'


def test_publish_checkpoint_done_and_no_duplicate(tmp_path, monkeypatch):
    prepare_approved(tmp_path)
    monkeypatch.setattr(worker, 'discover', lambda: [])
    calls = []

    def publish(folder):
        data = json.loads((tmp_path / 'batches.json').read_text())
        assert data['runs']['42']['status'] == 'publishing'
        calls.append(folder)
        return 1

    worker.cycle(tmp_path, Bot(), 'studystationhindi', publish)
    worker.cycle(tmp_path, Bot(), 'studystationhindi', publish)
    assert len(calls) == 1


def test_crash_checkpoint_never_retries_automatically(tmp_path, monkeypatch):
    prepare_approved(tmp_path)
    data = json.loads((tmp_path / 'batches.json').read_text())
    data['runs']['42']['status'] = 'publishing'
    ig.atomic_json(tmp_path / 'batches.json', data)
    monkeypatch.setattr(worker, 'discover', lambda: [])
    worker.cycle(tmp_path, Bot(), 'studystationhindi', lambda folder: pytest.fail('ambiguous retry'))


def test_worker_off_by_default():
    assert worker.main(['--state-dir', '/unused', '--account', 'studystationhindi', '--once']) == 1
