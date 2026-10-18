import pytest

from app.models import Device, Question


@pytest.fixture
def shared_record(db):
    question = db.query(Question).filter(Question.review_status == 'unreviewed').first()
    fields = ('text_en', 'options_en', 'solution_en', 'solution_hi', 'review_status')
    original = {key: getattr(question, key) for key in fields}
    question.text_en = 'PUBLIC QUESTION <script>bad()</script>'
    question.options_en = ['FIRST <img src=x onerror=bad()>', 'SECOND', 'THIRD', 'FOURTH']
    question.solution_en = 'SECRET_SOLUTION_SENTINEL'
    question.solution_hi = 'SECRET_HINDI_SENTINEL'
    db.commit()
    yield question
    for key, value in original.items():
        setattr(question, key, value)
    db.commit()


def test_shared_question_is_answer_free_anonymous_and_escaped(client, db, shared_record):
    before = db.query(Device).count()
    response = client.get(f'/q/{shared_record.id}?lang=en')
    assert response.status_code == 200
    assert f'SS-{shared_record.id}' in response.text
    assert 'PUBLIC QUESTION &lt;script&gt;bad()&lt;/script&gt;' in response.text
    assert '&lt;img src=x onerror=bad()&gt;' in response.text
    assert 'SECRET_SOLUTION_SENTINEL' not in response.text
    assert 'SECRET_HINDI_SENTINEL' not in response.text
    assert 'answer_index' not in response.text
    assert 'solution_en' not in response.text
    assert 'set-cookie' not in response.headers
    assert db.query(Device).count() == before
    assert response.headers['X-SS-Public-Content'] == 'shared-question-v1'
    assert '/offline-study' not in response.text


def test_shared_question_languages_and_unavailable_status(client, db, shared_record):
    response = client.get(f'/q/{shared_record.id}?lang=hi')
    assert response.status_code == 200
    assert '<html lang="hi">' in response.text
    assert shared_record.text_hi in response.text
    assert client.get(f'/q/{shared_record.id}?lang=invalid').status_code == 422
    shared_record.review_status = 'flagged'
    db.commit()
    assert client.get(f'/q/{shared_record.id}').status_code == 404
    assert client.get('/q/999999999999').status_code == 404


def test_android_association_is_public_and_matches_current_build(client):
    response = client.get('/.well-known/assetlinks.json')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('application/json')
    association = response.json()
    assert len(association) == 1
    assert association[0]['target']['package_name'] == 'com.studystation.app.debug'
    assert len(association[0]['target']['sha256_cert_fingerprints'][0].split(':')) == 32
    assert 'set-cookie' not in response.headers


def test_shared_page_only_links_configured_android_package(client, shared_record, monkeypatch):
    from app import shared_questions
    monkeypatch.setattr(shared_questions, 'ANDROID_APP_PACKAGE', 'com.studystation.app.debug')
    response = client.get(f'/q/{shared_record.id}?lang=en')
    assert f'intent://studystation.ebookcart.in/q/{shared_record.id}?lang=en' in response.text
    assert 'package=com.studystation.app.debug;end' in response.text
    assert 'SECRET_SOLUTION_SENTINEL' not in response.text
    monkeypatch.setattr(shared_questions, 'ANDROID_APP_PACKAGE', 'untrusted;scheme=evil')
    assert 'intent://' not in client.get(f'/q/{shared_record.id}?lang=en').text
