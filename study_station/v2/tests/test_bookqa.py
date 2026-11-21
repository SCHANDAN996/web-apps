"""QA receipts must remain scoped to current bytes and never certify missing evidence."""
import json

import pytest

from app import ai, bookgen, bookqa
from app.importers import ParsedQuestion
from test_bookcheck import write_chapter


@pytest.fixture
def chapter(tmp_path):
    return write_chapter(tmp_path / 'GK')


def test_budget_resume_persists_success_and_keeps_reference_blockers_separate(chapter, db, monkeypatch):
    calls = []
    monkeypatch.setattr(bookgen, '_ask_review', lambda *a: calls.append(1) or 'OK')
    first = bookqa.run_chapter(db, chapter, max_checks=2)
    assert first['checks_run'] == 2 and first['passed'] == 2 and first['verified'] is False
    second = bookqa.run_chapter(db, chapter, max_checks=1)
    assert second['needs_reference'] == 1 and len(calls) == 1
    assert bookqa.needs_qa(chapter)  # a blocked reference does not starve the remaining runnable checks


def test_infrastructure_failure_keeps_earlier_receipts_and_can_resume(chapter, db, monkeypatch):
    def fail(*args):
        raise ai.AIUnavailable('network')
    monkeypatch.setattr(bookgen, '_ask_review', fail)
    result = bookqa.run_chapter(db, chapter, max_checks=2)
    saved = json.loads((chapter / 'QA.json').read_text())
    assert result['infrastructure_error'] == 'network'
    assert saved['checks']['structure']['status'] == 'passed'
    assert 'editorial:Content_en.txt' not in saved['checks']
    monkeypatch.setattr(bookgen, '_ask_review', lambda *a: 'OK')
    result = bookqa.run_chapter(db, chapter, max_checks=1)
    assert result['passed'] == 2 and not result.get('infrastructure_error')


def test_content_hash_changes_invalidate_only_dependent_receipts(chapter, db, monkeypatch):
    monkeypatch.setattr(bookqa, '_execute', lambda *args: ('passed', []))
    assert bookqa.run_chapter(db, chapter, max_checks=200)['verified'] is True
    files = bookqa._chapter_files(chapter)
    path = files['Content_hi.txt']['path']
    path.write_text(path.read_text() + '\nहिंदी पाठ में नया तथ्य।')
    assert bookqa.summary(chapter)['verified'] is False
    ledger = bookqa._load(chapter)
    plan, _ = bookqa._plan(chapter)
    current = {check['id']: bookqa._current(check, ledger) for check in plan}
    assert current['editorial:Content_en.txt']['status'] == 'passed'
    assert current['editorial:Content_hi.txt'] == {}
    assert current['consistency'] == {}


def test_changed_source_during_review_discards_the_receipt(chapter, db, monkeypatch):
    path = bookqa._chapter_files(chapter)['Content_en.txt']['path']
    def reviewer(*args):
        path.write_text(path.read_text() + '\nA concurrent change.')
        return 'OK'
    monkeypatch.setattr(bookgen, '_ask_review', reviewer)
    result = bookqa.run_chapter(db, chapter, max_checks=2)
    assert not result['verified']
    assert 'editorial:Content_en.txt' not in bookqa._load(chapter)['checks']


def test_unknown_status_cannot_create_a_permanent_pending_loop(chapter, db):
    check = bookqa._plan(chapter)[0][0]
    ledger = bookqa._load(chapter)
    ledger['checks'][check['id']] = {'fingerprint': check['fingerprint'], 'status': 'unknown'}
    bookqa._save(chapter, ledger)
    assert bookqa.needs_qa(chapter)
    bookqa.run_chapter(db, chapter, max_checks=1)
    assert bookqa._load(chapter)['checks']['structure']['status'] == 'passed'


def test_old_verified_flag_is_cleared_before_partial_api_failure(chapter, db, monkeypatch):
    original = bookqa._execute
    monkeypatch.setattr(bookqa, '_execute', lambda *args: ('passed', []))
    assert bookqa.run_chapter(db, chapter, max_checks=200)['verified']
    path = bookqa._chapter_files(chapter)['Content_en.txt']['path']
    path.write_text(path.read_text() + '\nA changed fact.')
    monkeypatch.setattr(bookqa, '_execute', original)
    def fail(*args):
        raise ai.AIUnavailable('network')
    monkeypatch.setattr(bookgen, '_ask_review', fail)
    assert bookqa.run_chapter(db, chapter, max_checks=2)['infrastructure_error'] == 'network'
    saved = bookqa._load(chapter)
    assert saved['verified'] is False and saved['status'] != 'passed'


def test_uncited_content_and_pyq_style_are_not_grounded(chapter, db):
    checks, files = bookqa._plan(chapter)
    source = next(check for check in checks if check['id'] == 'sources:Content_en.txt')
    assert bookqa._execute(db, chapter, source, files)[0] == 'needs_reference'
    name = 'Practice_en_Set_01.txt'
    files[name]['text'] += '\nSource: PYQ-style\n'
    source = next(check for check in checks if check['id'] == 'sources:' + name)
    assert bookqa._execute(db, chapter, source, files)[0] == 'needs_reference'


def test_last_budget_slot_defers_repair_without_repeating_failed_check(chapter, db, monkeypatch):
    original_plan = bookqa._plan
    check, files = original_plan(chapter)
    check = next(item for item in check if item['id'] == 'answers:Practice_en_Set_01.txt')
    monkeypatch.setattr(bookqa, '_plan', lambda ch: ([check], files))
    reviews, repairs = [], []
    monkeypatch.setattr(bookqa, '_execute', lambda *a: reviews.append(1) or ('blocked', ['wrong key']))
    monkeypatch.setattr(bookqa, '_repair', lambda *a: repairs.append(1))
    first = bookqa.run_chapter(db, chapter, max_checks=1)
    assert first['pending'] == 1 and len(reviews) == 1 and not repairs
    second = bookqa.run_chapter(db, chapter, max_checks=1)
    assert second['pending'] == 1 and len(reviews) == 1 and len(repairs) == 1
    third = bookqa.run_chapter(db, chapter, max_checks=1)
    assert third['blocked'] == 1 and len(repairs) == 2 and not bookqa.needs_qa(chapter)


def test_hindi_scope_ignores_legacy_english_files(tmp_path):
    chapter = write_chapter(tmp_path / 'Hindi')
    checks, files = bookqa._plan(chapter)
    assert not any(bookgen._lang_of(name) == 'en' for name in files)
    assert not any(check['kind'] == 'semantic' for check in checks)
    assert not any(bookgen._lang_of(name) == 'en' for name in checks[0]['dependencies']['inventory'])


def test_duplicate_signature_preserves_hindi_matras():
    def question(word):
        return ParsedQuestion(1, word, ['एक', 'दो', 'तीन', 'चार'], 0, 'हल')
    assert bookqa._question_signature(question('दिन')) != bookqa._question_signature(question('दीन'))
    assert bookqa._question_signature(question('मन')) != bookqa._question_signature(question('मान'))


def test_cli_rejects_symlink_before_rollover_or_network(chapter, tmp_path, monkeypatch):
    alias = tmp_path / 'Chapter_01_alias'
    alias.symlink_to(chapter, target_is_directory=True)
    def unexpected(*args, **kwargs):
        pytest.fail('symlink rejection must happen before runtime actions')
    monkeypatch.setattr(bookgen, 'request_legacy_autopilot_rollover', unexpected)
    with pytest.raises(SystemExit) as result:
        bookqa.main(['--chapter', str(alias)])
    assert result.value.code == 2
