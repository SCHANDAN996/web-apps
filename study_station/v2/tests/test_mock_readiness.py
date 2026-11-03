from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from app import services
from app.mock_audit import audit
from app.models import Attempt, Device, Exam, Subject, Question, Topic


def test_audit_exposes_level_and_rule_gaps_without_certifying_patterns(db):
    report = audit(db)
    rows = {r['exam']: r for r in report['exams']}
    assert {'ssc-gd', 'ssc-mts', 'ssc-chsl', 'ssc-cgl', 'rrb-group-d', 'rrb-ntpc',
            'ibps-clerk', 'ibps-po'} <= rows.keys()
    assert 'sectional_timer_not_enforced' in rows['ibps-po']['engine_gaps']
    assert 'separate_sessions_not_enforced' in rows['ssc-mts']['engine_gaps']
    assert all(not r['official_pattern_verified'] for r in rows.values())
    for row in rows.values():
        for section in row['sections']:
            assert section['online_pool'] >= section['exact_level_pool']
    assert all('review_status' in row and 'difficulty' in row for row in report['topic_breakdown'])


def test_partial_card_metrics_are_the_paper_that_will_actually_start(client, db, monkeypatch):
    counts = {(s.id, '10th'): (100, 100) if s.slug != 'science' else (0, 0) for s in db.query(Subject)}
    monkeypatch.setattr(services, 'recent_section_counts', lambda _db: counts)
    exam = db.query(Exam).filter_by(slug='rrb-group-d').one()
    summary = services.mock_summary(exam, services.mock_plan(db, exam, counts))
    assert summary == {'questions': 75, 'required': 100, 'duration_sec': 4050,
                       'marks': 75, 'complete': False}
    doc = BeautifulSoup(client.get('/mock').text, 'html.parser')
    card = doc.select_one(f'#mock-title-{exam.id}').find_parent('article')
    assert [n.text for n in card.select('dd')] == ['75', '67.5', '75']
    assert 'छोटा अभ्यास' in card.text
    assert doc.select_one('[data-mock-search]')
    detail = BeautifulSoup(client.get('/mock/rrb-group-d').text, 'html.parser')
    assert '75 सवाल' in detail.text and '67.5' in detail.text


def test_exam_pool_and_availability_use_exam_level_not_learner_qualification(db):
    topic = db.query(Topic).filter_by(slug='percentage').one()
    row = Question(topic_id=topic.id, level='12th', difficulty='easy', answer_index=0,
                   text_hi='केवल level-selection परीक्षण', options_hi=['क','ख','ग','घ'],
                   review_status='verified', import_key='readiness-level-filter')
    db.add(row); db.commit()
    try:
        counts = services.section_counts(db)
        assert counts[(topic.subject_id, '12th')][0] >= 1
        own, other = services._pool(db, services.section_pool_filter('quant', topic.subject_id, '10th'), 'hi')
        assert row.id not in own + other
        own, other = services._pool(db, services.section_pool_filter('quant', topic.subject_id, '12th'), 'hi')
        assert row.id in own + other
    finally:
        db.delete(row); db.commit()


def test_mock_resume_only_links_to_current_learners_unexpired_test(client, db):
    client.post('/api/v1/me', json={'level': '10th'})
    device = db.query(Device).filter_by(token=client.cookies.get('ss_device')).one()
    other = Device(token='readiness-other-learner')
    db.add(other)
    db.flush()
    now = datetime.utcnow()
    own = Attempt(device_id=device.id, mode='mock', title='My active mock', question_ids=[],
                  duration_sec=3600, started_at=now)
    private = Attempt(device_id=other.id, mode='mock', title='Private other mock', question_ids=[],
                      duration_sec=3600, started_at=now)
    db.add_all([own, private]); db.commit()
    try:
        doc = BeautifulSoup(client.get('/mock').text, 'html.parser')
        assert doc.select_one(f'a[href="/attempt/{own.id}"]')
        assert not doc.select_one(f'a[href="/attempt/{private.id}"]')
        own.started_at = now - timedelta(hours=2); db.commit()
        assert 'My active mock' not in client.get('/mock').text
    finally:
        db.delete(own); db.delete(private); db.delete(other); db.commit()
