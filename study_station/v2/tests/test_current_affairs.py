from datetime import date
from pathlib import Path

import pytest

from app import ai, config, current_affairs as ca
from app.jobs.http import Response
from app.models import CAItem, Question

FX = Path(__file__).parent / 'fixtures'
FEED = (FX / 'pib_feed.xml').read_bytes()
RELEASE = (FX / 'pib_release.html').read_text(encoding='utf-8')


class Fake:
    def __init__(self):
        self.calls = []

    def get(self, url, params=None, headers=None):
        self.calls.append(url)
        if 'RssMain' in url:
            return Response(url, 200, FEED, 'text/xml')
        return Response(url, 200, RELEASE.encode(), 'text/html')


@pytest.fixture
def clean(db):
    db.query(Question).filter(Question.ca_item_id.is_not(None)).delete()
    db.query(CAItem).delete()
    db.commit()
    return db


def test_parse_feed_and_release():
    items = ca.parse_feed(FEED)
    assert len(items) == 4 and all(i['prid'].isdigit() for i in items)
    text, posted, ministry = ca.release_text(RELEASE)
    assert posted == date(2026, 10, 2) and ministry == 'प्रधानमंत्री कार्यालय'
    assert 'गांधी स्मृति' in text and 'इन भाषाओं में' not in text


def test_without_ai_stores_official_headlines(clean, client, monkeypatch):
    monkeypatch.setattr(config, 'ANTHROPIC_API_KEY', '')
    http = Fake()
    stats = ca.run(clean, http=http)
    assert stats['headline_only'] == 4 and stats['summarised'] == 0
    assert http.calls == [ca.PIB_FEEDS[0]]                # no release pages fetched without AI
    page = client.get('/current-affairs')
    assert page.status_code == 200 and 'pib.gov.in/PressReleaseIframePage.aspx' in page.text
    assert ca.run(clean, http=Fake())['new'] == 0          # idempotent


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
                              {'n': 3, 'relevance': 0, 'category': 'national'}]}
        if schema is ca.SUMMARY_SCHEMA:
            assert '<release>' in user
            return {'title_hi': 'शीर्षक', 'title_en': 'Headline', 'summary_hi': 'सार', 'summary_en': 'Summary',
                    'questions': [q, bad]}
        return {'answers': [{'n': 0, 'answer_index': 0, 'confident': True},
                            {'n': 1, 'answer_index': 1, 'confident': True}]}
    monkeypatch.setattr(ai, 'call', fake_call)
    stats = ca.run(clean, http=Fake())
    assert stats['hidden'] == 2 and stats['summarised'] == 2
    assert stats['questions'] == 2 and stats['questions_flagged'] == 2
    shown = clean.query(CAItem).filter_by(status='published').all()
    assert {i.summary_en for i in shown} == {'Summary'} and all(i.day == date(2026, 10, 2) for i in shown)
    good = clean.query(Question).filter(Question.ca_item_id.is_not(None), Question.review_status == 'unreviewed').first()
    assert good.source_ref.startswith('PIB 02-10-2026')

    # Weekly quiz serves only usable current-affairs questions
    client.post('/api/v1/me', json={'level': '10th'})
    topic = ca.ca_topic(clean)
    att = client.post('/api/v1/practice', json={'topic_id': topic.id, 'count': 20, 'since_days': 7}).json()
    assert len(att['questions']) == 2
    assert 'इस हफ़्ते का क्विज़' in client.get('/current-affairs').text
