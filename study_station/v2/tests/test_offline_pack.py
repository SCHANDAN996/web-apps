import hashlib
import json

import pytest

from app import offline_pack


def test_pack_is_public_deterministic_and_contains_all_usable_questions(db, tmp_path):
    output = tmp_path / 'pack'
    first = offline_pack.export_pack(db, output, tmp_path / 'no-books')
    assert first['counts']['questions'] >= 120
    assert first['format'] == 'study-station-content'
    catalog = json.loads((output / 'catalog.json').read_text(encoding='utf-8'))
    seen = []
    for subject in catalog['subjects']:
        for topic in subject['topics']:
            chunk = json.loads((output / topic['questions_path']).read_text(encoding='utf-8'))
            assert len(chunk) == topic['question_count']
            seen.extend(chunk)
    assert all(set(q) == set(offline_pack.QUESTION_FIELDS) for q in seen)
    assert all(q['review_status'] != 'flagged' for q in seen)
    assert all('import_key' not in q and 'review_note' not in q for q in seen)
    assert len(seen) == first['counts']['questions']
    for relative, digest in first['files'].items():
        assert hashlib.sha256((output / relative).read_bytes()).hexdigest() == digest
    before = {str(p.relative_to(output)): p.read_bytes() for p in output.rglob('*.json')}
    assert offline_pack.export_pack(db, output, tmp_path / 'no-books') == first
    assert before == {str(p.relative_to(output)): p.read_bytes() for p in output.rglob('*.json')}
    assert not any(name in before for name in ('device.json', 'attempt.json', '.env'))


def test_pack_failure_preserves_existing_pack_and_rejects_unknown_directory(db, tmp_path, monkeypatch):
    output = tmp_path / 'pack'
    offline_pack.export_pack(db, output, tmp_path / 'no-books')
    old = (output / 'manifest.json').read_bytes()
    monkeypatch.setattr(offline_pack, 'MAX_FILE_BYTES', 1)
    with pytest.raises(ValueError, match='size bound'):
        offline_pack.export_pack(db, output, tmp_path / 'no-books')
    assert (output / 'manifest.json').read_bytes() == old
    unknown = tmp_path / 'unknown'
    unknown.mkdir()
    with pytest.raises(ValueError, match='Refusing'):
        offline_pack.export_pack(db, unknown, tmp_path / 'no-books')


def test_pack_uses_finished_book_sections_not_prompts_and_checks_link_ancestors(db, tmp_path, monkeypatch):
    root = tmp_path / 'books'
    chapter = root / '10th_Level/Maths/Chapter_01_Percentage'
    chapter.mkdir(parents=True)
    (chapter / 'Content_hi.txt').write_text('प्रतिशत पढ़ाई की पूर्ण सामग्री। ' * 40, encoding='utf-8')
    (chapter / 'Key_Facts_en.txt').write_text('Write a world class chapter about percentages.', encoding='utf-8')
    output = tmp_path / 'pack'
    result = offline_pack.export_pack(db, output, root)
    assert result['counts']['chapters'] == 1
    index = json.loads((output / 'books/index.json').read_text(encoding='utf-8'))
    body = json.loads((output / index[0]['chapters'][0]['path']).read_text(encoding='utf-8'))
    assert [s['key'] for s in body['sections']] == ['Content']
    original = offline_pack.Path.is_symlink
    monkeypatch.setattr(offline_pack.Path, 'is_symlink', lambda p: p == chapter or original(p))
    assert not offline_pack._safe_file(chapter / 'Content_hi.txt', root)
    assert offline_pack.export_pack(db, output, root)['counts']['chapters'] == 0
