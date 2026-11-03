"""First-run introduction: public counts, honest scope, and repeat access."""
from bs4 import BeautifulSoup

from app import services
from app.models import Question


def test_intro_has_three_bilingual_slides_and_settings_replay(client):
    for language in ['hi', 'en']:
        client.cookies.set('ss_lang', language)
        doc = BeautifulSoup(client.get('/').text, 'html.parser')
        assert doc.select_one('[data-intro-auto]')
        assert len(doc.select('#studyIntro [data-intro-slide]')) == 3
        assert len(doc.select('#studyIntro [data-intro-dot]')) == 3
        assert doc.select_one('#studyIntro [data-intro-close]')
        assert not doc.select_one('#studyIntro [data-intro-count]').text.strip()
        settings = BeautifulSoup(client.get('/settings').text, 'html.parser')
        assert settings.select_one('[data-intro-open]')
        assert not settings.select_one('[data-intro-auto]')
    client.post('/api/v1/me', json={'level': '10th'})
    assert not BeautifulSoup(client.get('/').text, 'html.parser').select_one('[data-intro-auto]')


def test_intro_summary_counts_rows_once_without_login_or_trial(client, db, monkeypatch):
    monkeypatch.setenv('MEMBERSHIP_ENABLED', '1')
    services.invalidate_question_counts()
    expected = db.query(Question).filter(services.USABLE).count()
    response = client.get('/api/v1/intro-summary')
    assert response.status_code == 200
    assert response.json() == {'questions': expected, 'scope': 'online_bank'}
    # Hindi and English are fields on each row, not two question banks to add up.
    assert expected < db.query(Question).count()
