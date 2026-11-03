import json
from datetime import date
from types import SimpleNamespace

import httpx
import pytest

from app.promo import youtube
from app.promo import __main__ as cli


def configured(monkeypatch, tmp_path, handler):
    for key, value in {'YOUTUBE_CLIENT_ID': 'client-secret-value', 'YOUTUBE_CLIENT_SECRET': 'secret',
                       'YOUTUBE_REFRESH_TOKEN': 'refresh-secret', 'YOUTUBE_CHANNEL_ID': 'UCexpected',
                       'YOUTUBE_MADE_FOR_KIDS': 'false'}.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv('PROMO_YOUTUBE_POSTED', str(tmp_path / 'journal.json'))
    monkeypatch.setattr(youtube, 'client', lambda: httpx.Client(transport=httpx.MockTransport(handler)))
    video = tmp_path / '01.mp4'
    video.write_bytes(b'video')
    return video


def handler(request):
    if request.url.host == 'oauth2.googleapis.com':
        return httpx.Response(200, json={'access_token': 'access-secret'})
    if request.url.path.endswith('/channels'):
        return httpx.Response(200, json={'items': [{'id': 'UCexpected'}]})
    if request.method == 'POST':
        body = json.loads(request.content)
        assert body['status'] == {'privacyStatus': 'private', 'selfDeclaredMadeForKids': False}
        assert body['snippet']['title'] == 'Question #Shorts'
        return httpx.Response(200, headers={'Location': 'https://www.googleapis.com/upload/youtube/v3/videos?upload_id=hidden'})
    assert request.method == 'PUT' and request.content == b'video'
    return httpx.Response(200, json={'id': 'video123'})


def test_upload_journal_success_and_duplicate(monkeypatch, tmp_path):
    video = configured(monkeypatch, tmp_path, handler)
    uploader = youtube.Uploader()
    assert uploader.upload('q1', video, 'Question #Shorts\n\nDescription', date(2026, 10, 24)) == 'video123'
    entry = json.loads((tmp_path / 'journal.json').read_text())['uploads']['UCexpected:q1']
    assert entry['status'] == 'uploaded' and entry['video_id'] == 'video123'
    assert 'secret' not in (tmp_path / 'journal.json').read_text()
    assert uploader.upload('q1', video, 'anything', date(2026, 10, 24)) == 'video123'


def test_channel_mismatch_before_upload(monkeypatch, tmp_path):
    seen = []
    def mismatch(request):
        seen.append(request.url.path)
        if request.url.path.endswith('/channels'):
            return httpx.Response(200, json={'items': [{'id': 'UCwrong'}]})
        return handler(request)
    configured(monkeypatch, tmp_path, mismatch)
    with pytest.raises(youtube.YouTubeError, match='channel'):
        youtube.Uploader()
    assert not any('/upload/' in p for p in seen)


def test_timeout_remains_pending_blocks_next_run_no_secret_leak(monkeypatch, tmp_path):
    def broken(request):
        if request.method == 'PUT':
            raise httpx.ReadTimeout('secret location upload_id=hidden', request=request)
        return handler(request)
    video = configured(monkeypatch, tmp_path, broken)
    uploader = youtube.Uploader()
    with pytest.raises(youtube.YouTubeError) as err:
        uploader.upload('q1', video, 'Question #Shorts\n\nDescription', date(2026, 10, 24))
    assert 'hidden' not in str(err.value)
    assert json.loads((tmp_path / 'journal.json').read_text())['uploads']['UCexpected:q1']['status'] == 'pending'
    with pytest.raises(youtube.YouTubeError, match='pending'):
        youtube.Uploader()


def test_corrupt_journal_fails_closed(monkeypatch, tmp_path):
    configured(monkeypatch, tmp_path, handler)
    (tmp_path / 'journal.json').write_text('{bad')
    with pytest.raises(youtube.YouTubeError, match='journal'):
        youtube.Uploader()


def test_git_checkpoint_failure_stops_before_upload(monkeypatch, tmp_path):
    seen = []
    def track(request):
        seen.append(request.method)
        return handler(request)
    video = configured(monkeypatch, tmp_path, track)
    uploader = youtube.Uploader()
    monkeypatch.setattr(youtube, 'checkpoint', lambda path: (_ for _ in ()).throw(youtube.YouTubeError('checkpoint failed')))
    with pytest.raises(youtube.YouTubeError, match='checkpoint'):
        uploader.upload('q1', video, 'Question', date(2026, 10, 24))
    assert seen == ['POST', 'GET']  # token + channel lookup only


def test_dry_run_no_youtube_network_or_journal(monkeypatch, tmp_path):
    from app.promo import shorts
    monkeypatch.setattr(shorts, 'pick_shorts', lambda *a: [{'id': 'q', 'question': 'Q', 'options': ['A'], 'answer': 0}])
    monkeypatch.setattr(youtube, 'Uploader', lambda: pytest.fail('dry-run authenticated'))
    a = SimpleNamespace(count=1, level=None, dry_run=True, youtube=True, telegram=False, out=str(tmp_path))
    assert cli.run_shorts(a, date(2026, 10, 24), {'shorts': []}) == 0
    assert not list(tmp_path.iterdir())


def test_short_failure_keeps_render_and_successful_item_log(monkeypatch, tmp_path):
    from app.promo import shorts, posted
    q = {'id': 'q1', 'question': 'Q', 'options': ['A'], 'answer': 0}
    monkeypatch.setattr(shorts, 'pick_shorts', lambda *a: [q])
    monkeypatch.setattr(shorts, 'render', lambda q, path, work: path.write_bytes(b'video'))
    monkeypatch.setattr(shorts, 'caption', lambda q: 'Title\n\nDescription')
    class BrokenUploader:
        def upload(self, *a):
            raise youtube.YouTubeError('Upload uncertain')
    monkeypatch.setattr(youtube, 'Uploader', BrokenUploader)
    monkeypatch.setattr(posted, 'POSTED', tmp_path / 'posted.json')
    data = {'shorts': [], 'telegram': [], 'days': {}}
    a = SimpleNamespace(count=1, level=None, dry_run=False, youtube=True, telegram=False, out=str(tmp_path))
    assert cli.run_shorts(a, date(2026, 10, 24), data) == 1
    assert (tmp_path / '01.mp4').exists() and (tmp_path / '01.txt').exists()
    assert json.loads((tmp_path / 'posted.json').read_text())['shorts'] == ['q1']


def test_unexpected_upload_location_never_receives_token(monkeypatch, tmp_path):
    def unsafe(request):
        if request.url.path.startswith('/upload/'):
            return httpx.Response(200, headers={'Location': 'https://attacker.example/upload'})
        return handler(request)
    video = configured(monkeypatch, tmp_path, unsafe)
    with pytest.raises(youtube.YouTubeError, match='unexpected upload endpoint'):
        youtube.Uploader().upload('q1', video, 'Question', date(2026, 10, 24))


def test_maths_comparisons_are_valid_youtube_metadata(monkeypatch, tmp_path):
    def comparison(request):
        if request.url.path.startswith('/upload/') and request.method == 'POST':
            snippet = json.loads(request.content)['snippet']
            assert snippet['title'] == 'a ＜ b #Shorts'
            assert snippet['description'] == 'b ＞ a'
            return httpx.Response(200, headers={'Location': 'https://www.googleapis.com/upload/youtube/v3/videos?upload_id=x'})
        return handler(request)
    video = configured(monkeypatch, tmp_path, comparison)
    assert youtube.Uploader().upload('q1', video, 'a < b #Shorts\n\nb > a', date(2026, 10, 24)) == 'video123'
