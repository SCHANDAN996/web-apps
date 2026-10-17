import json

from app import observe, review
from app.models import Question, QuestionReport


def test_observe_reports_and_alerts(db):
    r = observe.collect(db)
    assert set(r) >= {'learners', 'content', 'jobs', 'current_affairs', 'ai', 'alerts'}
    msgs = ' '.join(a['msg'] for a in r['alerts'])
    assert 'no successful job sweep' in msgs                      # nothing has run in tests
    assert observe.exit_code(r) == 2
    md = observe.to_markdown(r)
    assert '## Jobs' in md and '🔴' in md


def test_review_list_and_apply(db, client, tmp_path, capsys):
    from conftest import make_questions
    make_questions(db, 'ga', 'economy', 1, tag=__name__)
    q = db.query(Question).filter(Question.import_key == f'economy-0-{__name__}').one()
    client.post('/api/v1/me', json={'level': '10th'})
    client.post(f'/api/v1/questions/{q.id}/report', json={'reason': 'wrong_answer', 'note': 'key'})
    items = review.list_queue(db, 'reported')
    assert any(i['id'] == q.id and i['reports'] for i in items)

    edits = [{'id': q.id, 'action': 'verify', 'answer_index': 3, 'note': 'fixed key per NCERT'},
             {'id': q.id, 'action': 'save', 'options_en': ['a', 'a', 'b', 'c']},       # invalid → rejected
             {'id': 999999, 'action': 'verify'}]
    f = tmp_path / 'edits.json'
    f.write_text(json.dumps(edits))
    assert review.main(['apply', str(f)]) == 1                       # some failed
    out = capsys.readouterr().out
    assert 'applied 1, failed 2' in out
    db.expire_all()
    q = db.get(Question, q.id)
    assert q.review_status == 'verified' and q.answer_index == 3 and q.review_note == 'fixed key per NCERT'
    assert db.query(QuestionReport).filter_by(question_id=q.id, resolved_at=None).count() == 0
