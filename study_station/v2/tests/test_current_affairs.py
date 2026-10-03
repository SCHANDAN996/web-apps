from datetime import date
from pathlib import Path

import pytest

from app import ai, config, current_affairs as ca
from app.jobs.http import Response
from app.models import CAItem, Question

FX = Path(__file__).parent / 'fixtures'
FEED = (FX / 'pib_feed.xml').read_bytes()
AIR = (FX / 'air_national_feed.xml').read_bytes()
RELEASE = (FX / 'pib_release.html').read_text(encoding='utf-8')


class Fake:
    """PIB feed + release pages; AIR national feed; other AIR feeds empty; optionally PIB blocked."""
    def __init__(self, pib_blocked=False):
        self.calls, self.pib_blocked = [], pib_blocked

    def get(self, url, params=None, headers=None):
        from app.jobs.http import FetchError
        self.calls.append(url)
        if 'pib.gov.in' in url and self.pib_blocked:
            raise FetchError('HTTP 403 for ' + url)
        if 'RssMain' in url:
            return Response(url, 200, FEED, 'text/xml')
        if 'newsonair' in url:
            body = AIR if '/national/' in url else b'<rss><channel></channel></rss>'
            return Response(url, 200, body, 'application/rss+xml')
        return Response(url, 200, RELEASE.encode(), 'text/html')


@pytest.fixture
def clean(db):
    db.query(Question).filter(Question.ca_item_id.is_not(None)).delete()
    db.query(CAItem).delete()
    db.commit()
    return db


def test_parse_feed_and_release():
    items = ca.parse_feed(FEED, 'pib')
    assert len(items) == 4 and all(i['ext_id'].startswith('pib:') for i in items)
    air = ca.parse_feed(AIR, 'air')
    assert len(air) == 3 and air[0]['content'] and air[0]['published'] == date(2026, 10, 3)
    text, posted, ministry = ca.release_text(RELEASE)
    assert posted == date(2026, 10, 2) and ministry == 'प्रधानमंत्री कार्यालय'
    assert 'गांधी स्मृति' in text and 'इन भाषाओं में' not in text


def test_without_ai_stores_official_headlines(clean, client, monkeypatch):
    monkeypatch.setattr(config, 'ANTHROPIC_API_KEY', '')
    http = Fake()
    stats = ca.run(clean, http=http)
    assert stats['headline_only'] == 7 and stats['summarised'] == 0      # 4 PIB + 3 AIR
    assert all('PressRelease' not in u for u in http.calls)              # no pages fetched without AI
    page = client.get('/current-affairs')
    assert page.status_code == 200 and 'pib.gov.in/PressReleaseIframePage.aspx' in page.text
    assert 'newsonair.gov.in' in page.text
    assert ca.run(clean, http=Fake())['new'] == 0                          # idempotent


def test_blocked_feed_does_not_stop_others(clean, monkeypatch):
    monkeypatch.setattr(config, 'ANTHROPIC_API_KEY', '')
    stats = ca.run(clean, http=Fake(pib_blocked=True))
    assert stats['feeds_failed'] == ['pib'] and stats['headline_only'] == 3


def test_with_ai_triage_summary_and_checked_questions(clean, client, db, monkeypatch):
    monkeypatch.setattr(config, 'ANTHROPIC_API_KEY', 'k')
    q = {'text_hi': 'प्रार्थना सभा कहाँ हुई?', 'text_en': 'Where was the prayer meeting held?',
         'options_hi': ['गांधी स्मृति', 'राजघाट', 'साबरमती', 'वर्धा'],
         'options_en': ['Gandhi Smriti', 'Rajghat', 'Sabarmati', 'Wardha'], 'answer_index': 0,
         'solution_hi': 'गांधी स्मृति में।', 'solution_en': 'At Gandhi Smriti.', 'difficulty': 'easy'}
    bad = {**q, 'text_en': 'Who chaired it?', 'answer_index': 2}

    def fake_call(system, user, *, schema=None, effort='low', max_tokens=4000):
        if schema is ca.TRIAGE_SCHEMA:
            return {'items': [{'n': 0, 'relevance': 4, 'category': 'national'},
                              {'n': 1, 'relevance': 1, 'category': 'national'},
                              {'n': 2, 'relevance': 3, 'category': 'states'},
                              {'n': 3, 'relevance': 0, 'category': 'national'},
                              {'n': 4, 'relevance': 5, 'category': 'international'},
                              {'n': 5, 'relevance': 0, 'category': 'international'},
                              {'n': 6, 'relevance': 2, 'category': 'environment'}]}
        if schema is ca.SUMMARY_SCHEMA:
            assert '<release>' in user
            return {'title_hi': 'शीर्षक', 'title_en': 'Headline', 'summary_hi': 'सार', 'summary_en': 'Summary',
                    'questions': [q, bad]}
        return {'answers': [{'n': 0, 'answer_index': 0, 'confident': True},
                            {'n': 1, 'answer_index': 1, 'confident': True}]}
    monkeypatch.setattr(ai, 'call', fake_call)
    http = Fake()
    stats = ca.run(clean, http=http)
    assert stats['hidden'] == 4 and stats['summarised'] == 3
    assert stats['questions'] == 3 and stats['questions_flagged'] == 3
    assert not any('newsonair.gov.in/india-calls' in u for u in http.calls)   # AIR text comes in the feed
    shown = clean.query(CAItem).filter_by(status='published').all()
    assert {i.summary_en for i in shown} == {'Summary'}
    assert {i.day for i in shown} == {date(2026, 10, 2), date(2026, 10, 3)}
    good = clean.query(Question).filter(Question.ca_item_id.is_not(None), Question.review_status == 'unreviewed').first()
    assert {q.source_ref.split(' ')[0] for q in clean.query(Question).filter(Question.ca_item_id.is_not(None))} == {'PIB', 'AIR'}

    # Weekly quiz serves only usable current-affairs questions
    client.post('/api/v1/me', json={'level': '10th'})
    topic = ca.ca_topic(clean)
    att = client.post('/api/v1/practice', json={'topic_id': topic.id, 'count': 20, 'since_days': 7}).json()
    assert len(att['questions']) == 3
    assert 'इस हफ़्ते का क्विज़' in client.get('/current-affairs').text
