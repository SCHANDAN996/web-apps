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
    if request.url.path.endswith('/videos') and request.method == 'GET':
        return httpx.Response(200, json={'items': [{'processingDetails': {'processingStatus': 'succeeded'}}]})
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
    monkeypatch.setattr(shorts, 'metadata', lambda q: {'title': 'Title', 'description': 'Description', 'tags': []})
    class BrokenUploader:
        def upload(self, *a, **kw):
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


def test_upload_sends_tags_and_sets_thumbnail(monkeypatch, tmp_path):
    seen = {}
    def track(request):
        if request.method == 'POST' and request.url.path.endswith('/thumbnails/set'):
            seen['thumb'] = (request.url.params['videoId'], request.headers['Content-Type'], request.content)
            return httpx.Response(200, json={})
        if request.method == 'POST' and '/videos' in request.url.path:
            seen['tags'] = json.loads(request.content)['snippet']['tags']
        return handler(request)
    video = configured(monkeypatch, tmp_path, track)
    thumb = tmp_path / '01.jpg'
    thumb.write_bytes(b'jpeg')
    assert youtube.Uploader().upload('q1', video, 'Question #Shorts\n\nD', date(2026, 10, 24),
                                     tags=['GK', 'SSC'], thumbnail=thumb) == 'video123'
    assert seen['tags'] == ['GK', 'SSC'] and seen['thumb'] == ('video123', 'image/jpeg', b'jpeg')


def test_thumbnail_failure_keeps_upload(monkeypatch, tmp_path, capsys):
    def deny(request):
        if request.url.path.endswith('/thumbnails/set'):
            return httpx.Response(403, json={'error': 'secret body'})
        return handler(request)
    video = configured(monkeypatch, tmp_path, deny)
    thumb = tmp_path / '01.jpg'
    thumb.write_bytes(b'jpeg')
    assert youtube.Uploader().upload('q1', video, 'Question #Shorts\n\nD', date(2026, 10, 24),
                                     thumbnail=thumb) == 'video123'
    out = capsys.readouterr().out
    assert 'thumbnail not set 403' in out and 'secret body' not in out
    assert json.loads((tmp_path / 'journal.json').read_text())['uploads']['UCexpected:q1']['status'] == 'uploaded'


def test_publish_time_slots(monkeypatch):
    from datetime import datetime, timezone
    monkeypatch.delenv('YOUTUBE_PUBLISH_TIMES', raising=False)
    day = date(2026, 11, 4)
    early = datetime(2026, 11, 3, 19, 31, tzinfo=timezone.utc)          # 01:01 IST
    got = [youtube.publish_time(day, i, early) for i in range(4)]
    assert [g.strftime('%H:%M') for g in got[:3]] == ['00:30', '08:30', '13:30'] and got[3] is None
    late = datetime(2026, 11, 4, 8, 20, tzinfo=timezone.utc)            # 13:50 IST: 14:00 too close
    assert youtube.publish_time(day, 0, late) is None and youtube.publish_time(day, 1, late) is None  # 06:00 gone, 14:00 too close
    assert youtube.publish_time(day, 2, late).strftime('%H:%M') == '13:30'
    monkeypatch.setenv('YOUTUBE_PUBLISH_TIMES', 'nine')
    with pytest.raises(youtube.YouTubeError, match='PUBLISH_TIMES'):
        youtube.publish_time(day, 0, early)


def test_public_upload_is_scheduled(monkeypatch, tmp_path):
    from datetime import datetime, timezone
    seen = {}
    def track(request):
        if request.method == 'POST' and '/videos' in request.url.path:
            seen['status'] = json.loads(request.content)['status']
            return httpx.Response(200, headers={'Location': 'https://www.googleapis.com/upload/youtube/v3/videos?upload_id=x'})
        return handler(request)
    video = configured(monkeypatch, tmp_path, track)
    monkeypatch.setenv('YOUTUBE_PRIVACY_STATUS', 'public')
    at = datetime(2026, 11, 4, 3, 30, tzinfo=timezone.utc)
    youtube.Uploader().upload('q1', video, 'Question #Shorts\n\nD', date(2026, 11, 4), publish_at=at)
    assert seen['status'] == {'privacyStatus': 'private', 'publishAt': '2026-11-04T03:30:00Z',
                              'selfDeclaredMadeForKids': False}
    entry = json.loads((tmp_path / 'journal.json').read_text())['uploads']['UCexpected:q1']
    assert entry['publish_at'] == '2026-11-04T03:30:00Z'


def test_once_skips_when_today_is_done(monkeypatch, tmp_path):
    from app.promo import shorts
    monkeypatch.setattr(shorts, 'pick_shorts', lambda *a: pytest.fail('picked again'))
    data = {'shorts': ['q1'], 'telegram': [], 'days': {'2026-11-04': {'shorts': [[{'id': 'q1'}]]}}}
    a = SimpleNamespace(count=3, level=None, dry_run=False, youtube=True, telegram=False, out=str(tmp_path), once=True)
    assert cli.run_shorts(a, date(2026, 11, 4), data) == 0


def test_thumbnail_waits_for_processing_before_setting(monkeypatch, tmp_path):
    events = []
    states = iter(['processing', 'succeeded'])
    def track(request):
        if request.method == 'GET' and request.url.path.endswith('/videos'):
            events.append('processing')
            return httpx.Response(200, json={'items': [{'processingDetails': {'processingStatus': next(states)}}]})
        if request.url.path.endswith('/thumbnails/set'):
            events.append('thumbnail')
            return httpx.Response(200, json={})
        return handler(request)
    video = configured(monkeypatch, tmp_path, track)
    monkeypatch.setattr(youtube.clock, 'sleep', lambda seconds: events.append('wait'))
    thumb = tmp_path / 'cover.jpg'
    thumb.write_bytes(b'jpeg')
    youtube.Uploader().upload('q1', video, 'Question #Shorts\n\nD', date(2026, 11, 5), thumbnail=thumb)
    assert events == ['processing', 'wait', 'processing', 'thumbnail']
    entry = json.loads((tmp_path / 'journal.json').read_text())['uploads']['UCexpected:q1']
    assert entry['thumbnail_status'] == 'accepted' and entry['status'] == 'uploaded'


@pytest.mark.parametrize('state', ['processing', 'failed', None])
def test_thumbnail_processing_failure_is_bounded_and_keeps_video(monkeypatch, tmp_path, state):
    seen = []
    def track(request):
        if request.method == 'GET' and request.url.path.endswith('/videos'):
            seen.append('processing')
            return httpx.Response(200, json={'items': [{'processingDetails': {'processingStatus': state}}]})
        if request.url.path.endswith('/thumbnails/set'):
            pytest.fail('thumbnail attempted before processing succeeded')
        return handler(request)
    video = configured(monkeypatch, tmp_path, track)
    monkeypatch.setattr(youtube.clock, 'sleep', lambda seconds: None)
    thumb = tmp_path / 'cover.jpg'
    thumb.write_bytes(b'jpeg')
    assert youtube.Uploader().upload('q1', video, 'Question #Shorts\n\nD', date(2026, 11, 5), thumbnail=thumb) == 'video123'
    assert len(seen) == (12 if state == 'processing' else 1)
    entry = json.loads((tmp_path / 'journal.json').read_text())['uploads']['UCexpected:q1']
    assert entry['thumbnail_status'] == 'not_set' and entry['status'] == 'uploaded'


@pytest.mark.parametrize('payload', [[], {'items': [None]}, {'items': [{'processingDetails': None}]}])
def test_malformed_processing_response_is_nonfatal(monkeypatch, tmp_path, payload):
    def track(request):
        if request.method == 'GET' and request.url.path.endswith('/videos'):
            return httpx.Response(200, json=payload)
        return handler(request)
    configured(monkeypatch, tmp_path, track)
    thumb = tmp_path / 'cover.jpg'
    thumb.write_bytes(b'jpeg')
    assert youtube.Uploader().set_thumbnail('video123', thumb) is False


def test_cli_exports_and_uploads_same_metadata_even_if_cover_fails(monkeypatch, tmp_path):
    from app.promo import shorts, posted
    q = {'id': 'test#q1', 'question': '20 का 10 प्रतिशत कितना है?', 'subject': 'Maths',
         'level': '10th_Level', 'chapter': '10th_Level/Maths/Test/Chapter_01_Percentage',
         'options': ['1', '2', '3', '4'], 'answer': 1, 'explanation': 'SECRET_SOLUTION'}
    monkeypatch.setattr(shorts, 'pick_shorts', lambda *a: [q])
    monkeypatch.setattr(shorts, 'render', lambda q, path, work: path.write_bytes(b'video'))
    def no_cover(*args):
        raise shorts.DoesNotFit('cover failed')
    monkeypatch.setattr(shorts, 'thumbnail', no_cover)
    monkeypatch.setattr(posted, 'POSTED', tmp_path / 'posted.json')
    captured = {}
    class FakeUploader:
        privacy = 'private'
        def upload(self, qid, path, caption, day, **extra):
            captured.update(caption=caption, tags=extra['tags'])
            assert 'thumbnail' not in extra
            return 'video123'
    monkeypatch.setattr(youtube, 'Uploader', FakeUploader)
    a = SimpleNamespace(count=1, level=None, dry_run=False, youtube=True, telegram=False, out=str(tmp_path))
    assert cli.run_shorts(a, date(2026, 11, 5), {'shorts': [], 'telegram': [], 'days': {}}) == 0
    meta = json.loads((tmp_path / '01.metadata.json').read_text())
    assert captured['caption'] == (tmp_path / '01.txt').read_text()
    assert captured['caption'].startswith(meta['title'] + '\n\n') and captured['tags'] == meta['tags']
    assert 'SECRET_SOLUTION' not in captured['caption']
