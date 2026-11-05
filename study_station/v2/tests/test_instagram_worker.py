import json
import zipfile
import pytest
from app.promo import instagram as ig, instagram_worker as worker


def run(**changes):
    value = dict(id=42, run_number=7, head_repository={'full_name': worker.REPOSITORY},
                 path='.github/workflows/promo-shorts.yml', head_branch=worker.BRANCH,
                 event='schedule', status='completed', conclusion='success', created_at='2026-11-05T10:00:00Z')
    value.update(changes)
    return value


@pytest.mark.parametrize('change', [dict(event='pull_request'), dict(head_branch='untrusted'),
    dict(head_repository={'full_name': 'attacker/web-apps'}), dict(path='untrusted.yml'), dict(conclusion='failure')])
def test_reject_untrusted(change):
    assert worker.trusted(run()) and not worker.trusted(run(**change))


def queue(folder):
    folder.mkdir(parents=True)
    path = folder / '01.mp4'
    path.write_bytes(b'video')
    ig.enqueue('q1', path, 'Original caption', '2026-11-05')


def state(tmp):
    queue(tmp / 'queue' / '42')
    data = {'account': 'studystation', 'since': '2026-11-05T00:00:00+00:00', 'runs': {
        '42': {'status': 'ready', 'at': worker.now(), 'digest': worker.digest(tmp / 'queue' / '42')}}}
    worker.save(tmp, data)
    return data


def test_zip_bounds(tmp_path, monkeypatch):
    archive = tmp_path / 'input.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('../escape.mp4', b'bad')
    with pytest.raises(ig.InstagramError):
        worker.unpack(archive, tmp_path / 'out')
    assert not (tmp_path / 'out').exists()
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('01.mp4', b'0' * 10000)
    monkeypatch.setattr(worker, 'MAX_ARCHIVE', 1000)
    with pytest.raises(ig.InstagramError, match='extraction'):
        worker.unpack(archive, tmp_path / 'out')


def test_history_not_imported(monkeypatch):
    current = worker.now()
    monkeypatch.setattr(worker, 'gh_json', lambda _: {'workflow_runs': [run(created_at='2020-01-01T00:00:00Z'), run(created_at=current)]})
    assert len(worker.discover(current)) == 1


def test_main_scheduler_and_no_output_run_do_not_stall(tmp_path, monkeypatch):
    assert worker.trusted(run(head_branch='main'))
    monkeypatch.setattr(worker, 'gh_json', lambda _: {'artifacts': []})
    assert worker.download(run(), tmp_path / 'unused') is False
    monkeypatch.setattr(worker, 'discover', lambda _: [run()])
    data = {'account': 'studystation', 'since': worker.now(), 'runs': {}}
    worker.sync(tmp_path, data)
    assert data['runs']['42']['status'] == 'no-output'
    worker.cycle(tmp_path, data, lambda *_: pytest.fail('empty publish'))


def test_init_offline_cannot_reset(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, 'gh_json', lambda *_: pytest.fail('network'))
    args = ['--account', 'studystation', '--state-dir', str(tmp_path)]
    assert worker.main(['init', *args]) == 0
    assert worker.main(['init', *args]) == 1
    assert worker.main(['run', *args]) == 1


def test_digest_binds_caption(tmp_path):
    data = state(tmp_path)
    meta = tmp_path / 'queue' / '42' / '01.instagram.json'
    value = json.loads(meta.read_text())
    value['caption'] = 'changed'
    ig.atomic_json(meta, value)
    with pytest.raises(ig.InstagramError, match='changed'):
        worker.cycle(tmp_path, data, lambda *_: pytest.fail('publish'))


@pytest.mark.parametrize('field,value', [('source_ref', 'untrusted'), ('source_sha', 'a' * 40)])
def test_digest_binds_source_provenance(tmp_path, field, value):
    data = state(tmp_path)
    meta = tmp_path / 'queue' / '42' / '01.instagram.json'
    item = json.loads(meta.read_text())
    item[field] = value
    ig.atomic_json(meta, item)
    with pytest.raises(ig.InstagramError, match='changed'):
        worker.cycle(tmp_path, data, lambda *_: pytest.fail('publish'))


@pytest.mark.parametrize('status,valid', [('ahead', True), ('identical', True), ('diverged', False), ('behind', False)])
def test_manifest_revision_must_belong_to_canonical_history(tmp_path, monkeypatch, status, valid):
    queue(tmp_path / 'queue')
    meta = tmp_path / 'queue' / '01.instagram.json'
    item = json.loads(meta.read_text())
    item.update(source_ref=worker.BRANCH, source_sha='a' * 40)
    ig.atomic_json(meta, item)
    calls = []
    def api(endpoint):
        calls.append(endpoint)
        return {'status': status}
    monkeypatch.setattr(worker, 'gh_json', api)
    if valid:
        worker.validate_source(tmp_path / 'queue')
    else:
        with pytest.raises(ig.InstagramError, match='canonical'):
            worker.validate_source(tmp_path / 'queue')
    assert calls == [f'repos/{worker.REPOSITORY}/compare/{"a" * 40}...{worker.BRANCH}']


def test_checkpoint_and_skip_done(tmp_path):
    data = state(tmp_path)
    calls = []
    def publish(folder):
        assert worker.ledger(tmp_path, 'studystation')['runs']['42']['status'] == 'publishing'
        calls.append(folder)
        return 1
    worker.cycle(tmp_path, data, publish)
    worker.cycle(tmp_path, data, publish)
    assert len(calls) == 1


def test_ambiguous_share_requires_reconcile_then_resume(tmp_path):
    data = state(tmp_path)
    def publish(folder):
        def share(item, checkpoint):
            checkpoint()
            raise RuntimeError('lost result')
        return ig.process(folder, tmp_path / 'uploads.json', 'studystation', share)
    with pytest.raises(ig.InstagramError, match='stopped'):
        worker.cycle(tmp_path, data, publish)
    with pytest.raises(ig.InstagramError, match='manual resume'):
        worker.cycle(tmp_path, data, lambda *_: pytest.fail('retry'))
    with pytest.raises(ig.InstagramError, match='reconcile'):
        worker.resume(tmp_path, data, '42')
    ig.reconcile(tmp_path / 'uploads.json', 'studystation', 'q1', 'uploaded', 'https://www.instagram.com/reel/actual123/')
    worker.resume(tmp_path, data, '42')
    worker.cycle(tmp_path, data, lambda folder: ig.process(folder, tmp_path / 'uploads.json', 'studystation',
                                                        lambda *_: pytest.fail('duplicate')))
    assert data['runs']['42']['status'] == 'done'


def test_retention_preserves_unresolved_and_journal(tmp_path):
    data = state(tmp_path)
    data['runs']['42'].update(status='done', at='2020-01-01T00:00:00+00:00')
    queue(tmp_path / 'queue' / '43')
    data['runs']['43'] = {'status': 'blocked', 'at': '2020-01-01T00:00:00+00:00'}
    worker.cleanup(tmp_path, data)
    assert not (tmp_path / 'queue' / '42').exists()
    assert (tmp_path / 'queue' / '43').exists() and (tmp_path / 'batches.json').exists()
