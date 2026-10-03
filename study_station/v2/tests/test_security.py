"""Regression tests for the security review findings."""
import httpx
import pytest

from app import ai, config
from app.jobs import http as jhttp, manage, pipeline
from app.jobs.http import FetchError, Fetcher, Response
from app.jobs.sources import Item, is_official, official_links_from_page, safe_http_url
from app.models import Job


@pytest.mark.parametrize('url', [
    'http://ssc.nic.in:@evil.com/advt.pdf', 'http://user:pw@ssc.gov.in/a', 'javascript://ssc.gov.in/%0aalert(1)',
    'JavaScript:alert(1)', 'data:text/html,x', 'ftp://ssc.gov.in/x', 'https://ssc.gov.in\n.evil.com/', '//ssc.gov.in/x',
])
def test_lookalike_and_script_urls_are_never_official(url):
    assert safe_http_url(url) is None and not is_official(url)


def test_real_official_urls_still_pass():
    assert is_official('https://ssc.gov.in/api/attachment/x.pdf') and is_official('https://WWW.IBPS.IN/notice')


def test_aggregator_page_with_lookalike_link_finds_nothing():
    html = ('<a href="http://ssc.nic.in:@evil.com/advt.pdf">Notification</a>'
            '<a href="javascript://ssc.gov.in/%0aalert(1)">Official site</a>')
    assert official_links_from_page(html, 'https://www.freejobalert.com/a') == ([], [])


class Fake:
    def __init__(self, pages):
        self.pages = pages

    def get(self, url, params=None, headers=None):
        if url in self.pages:
            final, body = self.pages[url]
            return Response(final, 200, body.encode(), 'text/html')
        raise FetchError('no route ' + url)


def test_discovery_cannot_send_us_off_site(db):
    item = Item('fja', 'discovery', 'X Recruitment 2026', 'http://127.0.0.1:8001/admin', origin_host='freejobalert.com')
    with pytest.raises(FetchError):
        pipeline.resolve_discovery(Fake({}), item)


def test_official_doc_that_redirects_away_is_not_trusted(db):
    pdf = 'https://ssc.gov.in/advt.pdf'
    text, url = pipeline.read_official(Fake({pdf: ('https://evil.example/advt.pdf', 'Last date 01.01.2099')}), [pdf])
    assert text is None and url is None


def test_fetcher_blocks_private_hosts_and_redirects_to_them(monkeypatch):
    monkeypatch.setattr(jhttp, 'public_host', lambda h: h == 'good.gov.in')

    def handler(request):
        if request.url.path == '/robots.txt':
            return httpx.Response(404)
        return httpx.Response(302, headers={'location': 'http://169.254.169.254/latest/meta-data'})
    f = Fetcher(client=httpx.Client(transport=httpx.MockTransport(handler)), host_gap=0)
    with pytest.raises(FetchError, match='refusing private'):
        f.get('http://127.0.0.1:8001/x', retries=0)
    with pytest.raises(FetchError, match='refusing private'):
        f.get('https://good.gov.in/notice', retries=0)


def test_job_page_never_renders_script_links(client, db):
    db.add(Job(slug='xss-job', title='T', status='verified', job_type='latest',
               official_url='javascript://ssc.gov.in/%0aalert(1)', notification_url='http://ssc.nic.in:@evil.com/a.pdf'))
    db.commit()
    page = client.get('/jobs/xss-job')
    assert 'javascript:' not in page.text and 'evil.com' not in page.text
    csp = page.headers['content-security-policy']
    assert "script-src 'self'" in csp and "frame-ancestors 'none'" in csp
    assert '<script>' not in client.get('/').text            # no inline JS anywhere (CSP)


def test_json_only_check_parses_media_type(client):
    r = client.post('/api/v1/sync/code', content=b'{}', headers={'content-type': 'text/plain; x=application/json'})
    assert r.status_code == 415


def test_recovery_code_is_single_use(client):
    client.post('/api/v1/me', json={'level': '10th'})
    code = client.post('/api/v1/sync/code', json={}).json()['code']
    client.cookies.clear()
    assert client.post('/api/v1/sync/restore', json={'code': code}).status_code == 200
    client.cookies.clear()
    assert client.post('/api/v1/sync/restore', json={'code': code}).status_code == 404


def test_admin_sessions_end_when_password_changes(client, monkeypatch):
    from app import admin
    admin._attempts.clear()
    monkeypatch.setattr(config, 'SECRET_KEY', 's')
    monkeypatch.setattr(config, 'ADMIN_PASSWORD', 'old-pass')
    client.post('/admin/login', data={'password': 'old-pass'}, headers={'origin': 'http://testserver'})
    assert client.get('/admin', follow_redirects=False).status_code == 200
    monkeypatch.setattr(config, 'ADMIN_PASSWORD', 'new-pass')
    assert client.get('/admin', follow_redirects=False).status_code == 303


def test_telegram_errors_never_contain_the_token(monkeypatch):
    def fake_post(url, **kw):
        return httpx.Response(401, json={'ok': False, 'description': 'Unauthorized'},
                              request=httpx.Request('POST', url))
    monkeypatch.setattr(manage.httpx, 'post', fake_post)
    with pytest.raises(manage.TelegramError) as e:
        manage.send_telegram('hi', token='123456:SECRET-TOKEN', chat_id='@c')
    assert 'SECRET-TOKEN' not in str(e.value) and '401' in str(e.value)


def test_ai_budget_is_refunded_when_the_call_fails(client, db, monkeypatch):
    from app.models import AiUsage, Question
    from conftest import topic_id
    monkeypatch.setattr(config, 'ANTHROPIC_API_KEY', 'k')

    def boom(*a, **k):
        raise ai.AIUnavailable('network')
    monkeypatch.setattr(ai, 'call', boom)
    client.post('/api/v1/me', json={'level': '10th'})
    att = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'analogy'), 'count': 1}).json()
    qid = att['questions'][0]['id']
    client.post(f"/api/v1/attempts/{att['id']}/answer", json={'question_id': qid, 'chosen_index': 0})
    from app.models import QuestionExplanation
    db.query(QuestionExplanation).filter_by(question_id=qid).delete()
    db.commit()
    before = sum(u.count for u in db.query(AiUsage).all())
    assert client.post(f'/api/v1/questions/{qid}/explain', json={'lang': 'hi'}).status_code == 503
    db.expire_all()
    assert sum(u.count for u in db.query(AiUsage).all()) == before


def test_assets_are_versioned_and_sw_is_stamped(client):
    from app.main import ASSET_V
    page = client.get('/').text
    assert f'/static/css/app.css?v={ASSET_V}' in page and f'/static/js/app.js?v={ASSET_V}' in page
    sw = client.get('/sw.js')
    assert sw.status_code == 200 and '__ASSET_V__' not in sw.text and ASSET_V in sw.text
    assert sw.headers['cache-control'] == 'no-cache'


# ---- book files: symlinks, ReDoS, atomic writes (security review of the books feature)
def test_book_sections_never_follow_symlinks(tmp_path, monkeypatch):
    from app import books, config
    from app.bookcheck import check_chapter, section_files
    secret = tmp_path / 'secret.env'
    secret.write_text('ANTHROPIC_API_KEY=sk-FAKE ' * 40)
    ch = tmp_path / 'books' / '10th_Level' / 'GK' / 'Foundation_10th_GK_WorldClass' / 'Chapter_01_Polity'
    ch.mkdir(parents=True)
    (ch / 'Content_hi.txt').write_text('राजव्यवस्था का पाठ। ' * 40, encoding='utf-8')
    (ch / 'Key_Facts_hi.txt').symlink_to(secret)
    (ch / 'chapter.json').symlink_to(secret)
    assert 'Key_Facts_hi.txt' not in section_files(ch)
    assert any('symlinks are not allowed' in p for p in check_chapter(ch)[1])
    monkeypatch.setattr(config, 'BOOKS_DIR', tmp_path / 'books')
    monkeypatch.setattr(config, 'BOOKS_RECHECK_SECONDS', 0)
    chapter = books.index(force=True)[0].chapters[0]
    assert 'Key_Facts' not in chapter.sections and books.load_meta(ch) == {}


def test_book_regexes_stay_fast_on_hostile_lines():
    import time
    from app import books
    from app.importers import TRAP_HINT
    cases = [lambda: books.parse_mermaid('```mermaid\ngraph TD\nA -- ' + ' ' * 8000 + 'B\n```'),
             lambda: books.EDGE.split('A -- ' + ' ' * 400 + 'B'),
             lambda: books.render_text('**a ' * 8000),
             lambda: books.render_text('# a' + ' ' * 8000 + 'b'),
             lambda: TRAP_HINT.sub('', '(परीक्षक का जाल' * 8000)]
    for f in cases:
        t = time.perf_counter(); f()
        assert time.perf_counter() - t < 0.5


def test_atomic_write_does_not_follow_a_planted_temp_link(tmp_path):
    from app.books import atomic_write
    victim = tmp_path / 'victim.txt'
    victim.write_text('keep me')
    (tmp_path / 'Content_hi.tmp').symlink_to(victim)          # the old predictable temp name
    atomic_write(tmp_path / 'Content_hi.txt', 'नया पाठ')
    assert victim.read_text() == 'keep me' and (tmp_path / 'Content_hi.txt').read_text() == 'नया पाठ'
    assert not [p for p in tmp_path.iterdir() if p.name.startswith('.Content_hi')]


def test_ai_reserve_is_atomic_and_obeys_global_kill_switch(db, monkeypatch):
    from sqlalchemy import func, select
    from app import ai, config
    from app.models import AiUsage
    used = db.scalar(select(func.coalesce(func.sum(AiUsage.count), 0)).where(AiUsage.day == ai._today()))
    mine = db.scalar(select(AiUsage.count).where(AiUsage.day == ai._today(), AiUsage.device_id == -7)) or 0
    monkeypatch.setattr(config, 'AI_DAILY_LIMIT_TOTAL', used + 3)
    assert [ai.reserve(db, -7, own_limit=mine + 10) for _ in range(5)] == [True, True, True, False, False]
    monkeypatch.setattr(config, 'AI_DAILY_LIMIT_TOTAL', 0)
    assert ai.reserve(db, 42, own_limit=10) is False


def test_unexpected_service_errors_do_not_leak_details(client, monkeypatch):
    from app import services
    from fastapi.testclient import TestClient
    from app.main import app
    def boom(*a, **k):
        raise RuntimeError('SELECT secret FROM device')
    monkeypatch.setattr(services, 'start_mock', boom)
    c = TestClient(app, raise_server_exceptions=False)
    c.post('/api/v1/me', json={'level': '10th', 'lang': 'hi'})
    r = c.post('/api/v1/mock', json={'exam': 'ssc-gd'})
    assert r.status_code == 500 and 'SELECT' not in r.text
