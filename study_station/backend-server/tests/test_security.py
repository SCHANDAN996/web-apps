from models import db, Book, BookChapter, StudentProgress, StudyContent, SystemSettings
from security import safe_url


# ---------- admin auth ----------
def test_admin_pages_redirect_to_login(client):
    for path in ['/admin', '/admin/settings', '/admin/study', '/admin/books']:
        res = client.get(path)
        assert res.status_code == 302, path
        assert '/admin/login' in res.headers['Location']


def test_api_writes_need_admin(client):
    assert client.post('/api/books', json={'title': 'x'}).status_code == 401
    assert client.delete('/api/books/1').status_code == 401
    assert client.put('/api/chapters/1', json={}).status_code == 401
    assert client.post('/admin/publish').status_code == 401
    assert client.get('/admin/check_keys').status_code == 302


def test_public_reads_stay_open(client):
    assert client.get('/api/jobs/latest').status_code == 200
    assert client.get('/api/books').status_code == 200


def test_wrong_password_rejected(client):
    res = client.post('/admin/login', data={'password': 'nope'})
    assert res.status_code == 401
    assert client.get('/admin').status_code == 302


def test_login_is_rate_limited(client):
    for _ in range(5):
        client.post('/admin/login', data={'password': 'nope'})
    res = client.post('/admin/login', data={'password': 'correct-horse'})
    assert b'Too many attempts' in res.data


def test_login_logout(admin_client):
    assert admin_client.get('/admin').status_code == 200
    admin_client.post('/admin/logout')
    assert admin_client.get('/admin').status_code == 302


def test_login_next_is_not_open_redirect(client):
    res = client.post('/admin/login?next=//evil.com', data={'password': 'correct-horse'})
    assert res.headers['Location'] == '/admin'


def test_admin_locked_without_config(client, monkeypatch):
    monkeypatch.delenv('ADMIN_PASSWORD')
    res = client.post('/admin/login', data={'password': ''})
    assert res.status_code == 503
    assert client.get('/admin').status_code == 302


def test_check_keys_masks_keys(app, admin_client):
    with app.app_context():
        SystemSettings.query.filter_by(setting_key='gemini_api_keys').delete()
        db.session.add(SystemSettings(setting_key='gemini_api_keys', setting_value='AIzaSECRETSECRETSECRET1234'))
        db.session.commit()
    body = admin_client.get('/admin/check_keys').get_data(as_text=True)
    assert 'SECRETSECRET' not in body


# ---------- CORS / headers ----------
def test_cors_only_for_allowed_origin(client):
    ok = client.get('/api/jobs/latest', headers={'Origin': 'https://studystation.in'})
    assert ok.headers.get('Access-Control-Allow-Origin') == 'https://studystation.in'
    bad = client.get('/api/jobs/latest', headers={'Origin': 'https://evil.com'})
    assert 'Access-Control-Allow-Origin' not in bad.headers


def test_cache_headers(client):
    assert client.get('/api/jobs/latest').headers['Cache-Control'] == 'no-store'
    assert client.get('/css/style.css').headers['Cache-Control'] == 'no-cache'
    assert 'max-age=604800' in client.get('/assets/icon.svg').headers['Cache-Control']


def test_db_path_is_next_to_app():
    import app as app_module
    import os
    assert app_module.basedir == os.path.dirname(os.path.abspath(app_module.__file__))


# ---------- AI chat ----------
def _chapter(app):
    with app.app_context():
        c = StudyContent(title='Ch', class_level=10, subject='Maths', chapter_name='Ch', content_text='notes')
        db.session.add(c)
        SystemSettings.query.filter_by(setting_key='gemini_api_keys').delete()
        db.session.add(SystemSettings(setting_key='gemini_api_keys', setting_value='AIzaTESTKEY0000000000'))
        db.session.commit()
        return c.id


def test_chat_validates_input(app, client):
    cid = _chapter(app)
    assert client.post('/api/chat', json={}).status_code == 400
    assert client.post('/api/chat', json={'chapterId': 'abc', 'message': 'hi'}).status_code == 400
    assert client.post('/api/chat', json={'chapterId': cid, 'message': 'x' * 1001}).status_code == 400
    res = client.post('/api/chat', json={'chapterId': cid, 'message': 'What is a noun?'})
    assert res.status_code == 200 and res.get_json()['success']


def test_chat_rate_limited(app, client):
    cid = _chapter(app)
    codes = [client.post('/api/chat', json={'chapterId': cid, 'message': 'q'}).status_code for _ in range(10)]
    assert codes[:8] == [200] * 8
    assert codes[8] == 429


# ---------- progress ----------
def test_progress_validation_and_new_row(app, client):
    with app.app_context():
        b = Book(title='B', slug='b-test')
        db.session.add(b)
        db.session.flush()
        ch = BookChapter(book_id=b.id, order=1, title_en='C1')
        db.session.add(ch)
        db.session.commit()
        ch_id = ch.id
    assert client.post('/api/progress', json={'chapterId': ch_id, 'quality': 'bad'}).status_code == 400
    assert client.post('/api/progress', json={'chapterId': ch_id, 'quality': 9}).status_code == 400
    assert client.post('/api/progress', json={'chapterId': 999999, 'quality': 4}).status_code == 404
    res = client.post('/api/progress', json={'studentId': 's1', 'chapterId': ch_id, 'quality': 4, 'timeSpent': 30})
    assert res.status_code == 200, res.get_data(as_text=True)
    assert res.get_json()['intervalDays'] == 1


# ---------- URL sanitising ----------
def test_safe_url():
    assert safe_url('https://ssc.gov.in/x') == 'https://ssc.gov.in/x'
    assert safe_url('jobs/job_1.html') == 'jobs/job_1.html'
    assert safe_url('javascript:alert(1)') == ''
    assert safe_url(' JaVa\tScript:alert(1)') == ''
    assert safe_url('data:text/html,hi') == ''
    assert safe_url(None) == ''
