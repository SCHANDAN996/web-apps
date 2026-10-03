import pytest

from app import ai, bookgen, config
from test_bookcheck import mcq_set
from test_books import PROMPT, write

INTRO = 'You are writing the chapter "States & Rivers" for 10th-level learners.'
BODY = 'राज्य और नदियों का पूरा पाठ। ' * 40


@pytest.fixture
def chapter(tmp_path, monkeypatch):
    root = tmp_path / 'books'
    ch = root / '10th_Level' / 'GK' / 'Foundation_10th_GK_WorldClass' / 'Chapter_07_States_Rivers'
    write(ch / 'Prompts' / 'Chapter_Intro_Prompt.txt', INTRO)
    for name in ('Content_hi.txt', 'Mind_Map.txt', 'Practice_en_Set_01.txt', 'Practice_hi_Set_01.txt'):
        write(ch / 'Prompts' / name, PROMPT + f' ({name})')
    write(ch / 'Content_en.txt', 'Finished English lesson. ' * 30)                   # done: never touched
    write(root / 'BOOK_RULES.md', '# BOOK_RULES\nNo invented PYQs.')
    monkeypatch.setattr(config, 'BOOKS_DIR', root)
    monkeypatch.setattr(config, 'ANTHROPIC_API_KEY', 'test-key')
    monkeypatch.setattr(config, 'AI_DAILY_BOOK_SECTIONS', 60)
    return ch


@pytest.fixture
def fake_ai(monkeypatch):
    calls = []

    def fake_call(system, user, *, schema=None, effort='low', max_tokens=4000):
        calls.append((system, user))
        if 'Translate exactly these questions' in user:
            return mcq_set('hi')
        if 'Practice_en_Set_01.txt' in user:
            return mcq_set('en')
        if 'Mind_Map.txt' in user:
            return '```mermaid\ngraph TD\n  A["राज्य<br>States"] --> B["नदियाँ"]\n  A --> C["राजधानियाँ"]\n```\n' + '%%' * 200
        return '```\n' + BODY + '\n```'
    monkeypatch.setattr(ai, 'call', fake_call)
    return calls


def usage_reset(db):
    from app.models import AiUsage
    db.query(AiUsage).filter(AiUsage.device_id == bookgen.BOOK_USAGE_ID).delete()
    db.commit()


def test_bookgen_writes_root_keeps_prompts_and_translates(chapter, fake_ai, db, capsys):
    usage_reset(db)
    code = bookgen.main(['--chapter', str(chapter)])
    out = capsys.readouterr().out
    assert [n for n in ('Content_hi', 'Mind_Map', 'Practice_en_Set_01', 'Practice_hi_Set_01')
            if f'wrote {n}.txt' in out] == ['Content_hi', 'Mind_Map', 'Practice_en_Set_01', 'Practice_hi_Set_01']
    assert (chapter / 'Content_hi.txt').read_text().startswith('राज्य और नदियों')         # code fence removed
    assert (chapter / 'Prompts' / 'Content_hi.txt').read_text().startswith('# Chapter:')  # prompt untouched
    assert (chapter / 'Content_en.txt').read_text().startswith('Finished English lesson.')
    system, first_user = fake_ai[0]
    assert 'No invented PYQs.' in system                                                  # BOOK_RULES.md
    assert INTRO in first_user and '<section_prompt file="Content_hi.txt">' in first_user
    # hi practice set = translation of exactly the English set that was just written
    translate = [u for _, u in fake_ai if 'Translate exactly these questions' in u]
    assert len(translate) == 1 and mcq_set('en').strip() in translate[0]
    assert len(fake_ai) == 4 and bookgen.used_today(db) == 4
    assert '--- bookcheck\nOK   Chapter_07_States_Rivers' in out and code == 0
    # Second run: nothing left in these files, finished sections are never overwritten
    fake_ai.clear()
    bookgen.main(['--chapter', str(chapter), '--sections', 'Content_hi,Content_en'])
    assert fake_ai == [] and 'not a todo section' in capsys.readouterr().out


def test_bookgen_moves_root_prompt_and_rejects_debris(chapter, fake_ai, db, monkeypatch, capsys):
    usage_reset(db)
    write(chapter / 'Feynman_hi.txt', PROMPT + ' (Feynman_hi.txt)')                     # prompt in the root
    bookgen.main(['--chapter', str(chapter), '--sections', 'Feynman_hi'])
    assert (chapter / 'Prompts' / 'Feynman_hi.txt').read_text().startswith('# Chapter:')
    assert (chapter / 'Feynman_hi.txt').read_text().startswith('राज्य')
    monkeypatch.setattr(ai, 'call', lambda *a, **k: 'Sure! Here is the section:\n' + BODY)
    bookgen.main(['--chapter', str(chapter), '--sections', 'Content_hi'])
    assert 'REJECTED Content_hi.txt: chat debris' in capsys.readouterr().out
    assert not (chapter / 'Content_hi.txt').exists()


def test_bookgen_daily_limit(chapter, fake_ai, db, monkeypatch, capsys):
    usage_reset(db)
    monkeypatch.setattr(config, 'AI_DAILY_BOOK_SECTIONS', 2)
    assert bookgen.main(['--chapter', str(chapter)]) == 1
    out = capsys.readouterr().out
    assert len(fake_ai) == 2 and 'stopping: daily_limit' in out and bookgen.used_today(db) == 2


def test_bookgen_refunds_failed_call(chapter, db, monkeypatch, capsys):
    usage_reset(db)

    def broken(*a, **k):
        raise ai.AIUnavailable('api_error')
    monkeypatch.setattr(ai, 'call', broken)
    bookgen.main(['--chapter', str(chapter), '--sections', 'Content_hi'])
    assert 'FAILED Content_hi.txt: api_error' in capsys.readouterr().out and bookgen.used_today(db) == 0


def test_bookgen_needs_key_but_dry_run_does_not(chapter, fake_ai, monkeypatch, capsys):
    monkeypatch.setattr(config, 'ANTHROPIC_API_KEY', '')
    assert bookgen.main(['--chapter', str(chapter)]) == 2
    assert 'ANTHROPIC_API_KEY is not set' in capsys.readouterr().err
    bookgen.main(['--chapter', str(chapter), '--dry-run'])
    out = capsys.readouterr().out
    assert 'would write: Content_hi.txt' in out and 'would translate from Practice_en_Set_01.txt: Practice_hi_Set_01.txt' in out
    assert fake_ai == [] and not (chapter / 'Content_hi.txt').exists()


def test_rules_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'BOOKS_DIR', tmp_path)               # no BOOK_RULES.md here
    rules = bookgen.rules_text()
    assert 'PYQ' in rules and 'mermaid' in rules
