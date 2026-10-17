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
