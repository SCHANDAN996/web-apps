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
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', '')
    monkeypatch.setattr(config, 'BOOKGEN_PROVIDER', '')
    monkeypatch.setattr(config, 'AI_DAILY_BOOK_SECTIONS', 60)
    return ch


@pytest.fixture
def fake_ai(monkeypatch):
    calls = []

    def fake_call(system, user, *, schema=None, effort='low', max_tokens=4000):
        if system == bookgen.CHECK_SYSTEM:                   # the independent re-solve agrees with mcq_set's key
            return '\n'.join(f'{i}: {"abcd"[i % 4]}' for i in range(1, 26))
        calls.append((system, user))
        if 'Translate exactly these questions' in user:
            return mcq_set('hi')
        if 'Practice_en_Set_01.txt' in user:
            return mcq_set('en')
        if 'Mind_Map.txt' in user:
            return '```mermaid\ngraph TD\n  A["राज्य<br>States"] --> B["नदियाँ"]\n  A --> C["राजधानियाँ"]\n```\n' + '%%' * 200
        return '```\n' + BODY + '\n```'
    monkeypatch.setattr(ai, 'call', fake_call)
    monkeypatch.setattr(bookgen, 'balance_answers', lambda text: text)      # fixed keys in these fakes
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
    assert len(fake_ai) == 4 and bookgen.used_today(db) == 5          # + 1 independent re-solve of the new set
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


# ------------------------------------------------------------------ NVIDIA provider
class FakeStream:
    def __init__(self, lines):
        self.lines = [l.encode() for l in lines]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __iter__(self):
        return iter(self.lines)


def sse(*chunks, finish='stop'):
    import json
    out = [f'data: {json.dumps({"choices": [{"delta": {"content": c}, "finish_reason": None}]})}\n' for c in chunks]
    out.append(f'data: {json.dumps({"choices": [{"delta": {}, "finish_reason": finish}]})}\n')
    return out + ['data: [DONE]\n']


def test_nvidia_call_streams_and_strips_reasoning(monkeypatch):
    from app import nvidia
    seen = {}

    def fake_urlopen(req, timeout):
        import json
        seen['auth'] = req.get_header('Authorization')
        seen['body'] = json.loads(req.data)
        return FakeStream(sse('<think>hidden</think>', 'प्रश्न ', 'एक'))
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'nvapi-test')
    monkeypatch.setattr(nvidia.urllib.request, 'urlopen', fake_urlopen)
    assert nvidia.call('sys', 'user') == 'प्रश्न एक'
    assert seen['auth'] == 'Bearer nvapi-test' and seen['body']['stream'] is True
    assert seen['body']['messages'][0] == {'role': 'system', 'content': 'sys'}


def test_nvidia_errors_map_to_ai_unavailable(monkeypatch):
    import urllib.error
    from app import nvidia
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', '')
    with pytest.raises(ai.AIUnavailable, match='not_configured'):
        nvidia.call('s', 'u')
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'nvapi-test')

    def denied(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 401, 'no', {}, None)
    monkeypatch.setattr(nvidia.urllib.request, 'urlopen', denied)
    with pytest.raises(ai.AIUnavailable, match='auth'):
        nvidia.call('s', 'u')
    tries = []

    def busy(req, timeout):
        tries.append(1)
        raise urllib.error.HTTPError(req.full_url, 429, 'busy', {}, None)
    monkeypatch.setattr(nvidia, 'RETRY_WAITS', (0, 0))
    monkeypatch.setattr(nvidia.urllib.request, 'urlopen', busy)
    with pytest.raises(ai.AIUnavailable, match='rate_limited'):
        nvidia.call('s', 'u')
    assert len(tries) == 3                                   # first try + one per wait
    monkeypatch.setattr(nvidia.urllib.request, 'urlopen', lambda req, timeout: FakeStream(sse('x', finish='length')))
    with pytest.raises(ai.AIUnavailable, match='too_long'):
        nvidia.call('s', 'u')


def test_bookgen_uses_nvidia_when_its_key_is_set(chapter, db, monkeypatch, capsys):
    from app import nvidia
    usage_reset(db)
    used = []
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'nvapi-test')
    monkeypatch.setattr(ai, 'call', lambda *a, **k: pytest.fail('Claude must not be called'))
    monkeypatch.setattr(nvidia, 'call', lambda system, user, **k: used.append(user) or BODY)
    assert bookgen.provider() == 'nvidia'
    bookgen.main(['--chapter', str(chapter), '--sections', 'Content_hi'])
    assert len(used) == 1 and (chapter / 'Content_hi.txt').is_file()
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', '')
    assert bookgen.main(['--chapter', str(chapter), '--provider', 'nvidia']) == 2
    assert 'NVIDIA_API_KEY is not set' in capsys.readouterr().err


# ------------------------------------------------------------------ repair mode
@pytest.fixture
def broken_chapter(tmp_path, monkeypatch):
    from test_bookcheck import write_chapter
    old_set = '\n'.join(f'Q{i}. Old style question {i}?\n(a) 1 (b) 2 (c) 3 (d) 4' for i in range(1, 26)) + '\nAnswer key: 1-a 2-b'
    ch = write_chapter(tmp_path, **{'PYQ_en.txt': 'Here is the PYQ analysis.\n' + 'Exam pattern notes. ' * 30,
                                    'Practice_en_Set_01.txt': old_set})
    monkeypatch.setattr(config, 'ANTHROPIC_API_KEY', 'test-key')
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', '')
    monkeypatch.setattr(config, 'BOOKGEN_PROVIDER', '')
    monkeypatch.setattr(config, 'AI_DAILY_BOOK_SECTIONS', 60)
    return ch


def fake_repair(monkeypatch, checker):
    def ask(db, user):
        if '<current_file name="PYQ_en.txt">' in user:
            return 'Exam pattern notes, rewritten. ' * 30
        if 'Translate exactly these questions' in user:
            return mcq_set('hi')
        assert '<current_set name="Practice_en_Set_01.txt">' in user and 'numbered 1 to 25' in user
        return mcq_set('en')
    monkeypatch.setattr(bookgen, '_ask', ask)
    monkeypatch.setattr(bookgen, '_ask_check', lambda db, user: checker(user))
    monkeypatch.setattr(bookgen, 'balance_answers', lambda text: text)


def test_repair_rewrites_flagged_sections_after_an_independent_resolve(broken_chapter, db, monkeypatch):
    from app import bookcheck
    seen = []

    def checker(user):
        seen.append(user)
        return '\n'.join(f'{i}: {"abcd"[i % 4]}' for i in range(1, 26))
    fake_repair(monkeypatch, checker)
    written, failed = bookgen.repair(db, broken_chapter, out=lambda *a: None)
    assert written == ['PYQ_en.txt', 'set 01'] and failed == []
    assert 'Answer' not in seen[0] and 'Solution' not in seen[0]          # the checker never sees the key
    assert bookcheck.check_chapter(broken_chapter) == ([], [])


def test_repair_writes_nothing_when_the_resolve_keeps_disagreeing(broken_chapter, db, monkeypatch):
    before = (broken_chapter / 'Prompts' / 'Practice_en_Set_01.txt').read_text()
    fake_repair(monkeypatch, lambda user: '\n'.join(f'{i}: a' for i in range(1, 26)))
    msgs = []
    written, failed = bookgen.repair(db, broken_chapter, out=msgs.append)
    assert 'set 01' in failed and not (broken_chapter / 'Practice_en_Set_01.txt').exists()
    assert (broken_chapter / 'Prompts' / 'Practice_en_Set_01.txt').read_text() == before
    assert sum('re-solve disagrees' in m for m in msgs) == bookgen.MAX_REPAIR_TRIES


# ------------------------------------------------------------------ review gate
def test_review_fixes_only_sections_the_reviewer_flags(broken_chapter, db, monkeypatch):
    from app import bookcheck
    ch = broken_chapter
    (ch / 'Prompts' / 'PYQ_en.txt').write_text('Exam pattern notes. ' * 30)          # make it clean first
    (ch / 'Prompts' / 'Practice_en_Set_01.txt').write_text(mcq_set('en'))
    reviewed, rewritten = [], []

    def reviewer(db, user):
        reviewed.append(user)
        return '- "Ganga rises in Kerala" → it rises at Gangotri' if 'file="Content_en.txt"' in user else 'OK'

    def ask(db, user):
        rewritten.append(user)
        assert 'Gangotri' in user and '<current_file name="Content_en.txt">' in user
        return 'Corrected chapter text about states and rivers. ' * 20
    monkeypatch.setattr(bookgen, '_ask_review', reviewer)
    monkeypatch.setattr(bookgen, '_ask', ask)
    fixed, failed = bookgen.review(db, ch, out=lambda *a: None)
    assert fixed == ['Content_en.txt'] and failed == [] and len(rewritten) == 1
    assert not any('Practice_' in u for u in reviewed) and len(reviewed) == 11      # 10 sections + mind map
    assert (ch / 'Content_en.txt').read_text().startswith('Corrected chapter text')
    assert bookcheck.check_chapter(ch) == ([], [])


def test_review_answer_parsing():
    assert bookgen._review_issues('OK') == [] and bookgen._review_issues('OK.\n') == []
    assert bookgen._review_issues('- wrong date → 1857\n- wrong name → Ashoka') == ['- wrong date → 1857', '- wrong name → Ashoka']


def test_balance_answers_spreads_keys_and_keeps_letter_references():
    from collections import Counter
    from app.importers import parse_mcq_text
    blocks = []
    for i in range(1, 26):
        why = 'Option (b) is right: "goes" agrees with she.' if i == 7 else '"goes" agrees with she.'
        blocks.append(f'{i}. Question {i}: she ___ daily?\n(a) go (b) goes (c) going (d) gone\nAnswer: (b)\nSolution: {why}\nSource: PYQ-style')
    text = 'Questions 1–20: Easy | Questions 21–25: Medium\n\n' + '\n\n'.join(blocks)
    out = bookgen.balance_answers(text)
    qs = parse_mcq_text(out)
    assert len(qs) == 25 and max(Counter(q.answer_index for q in qs).values()) <= 7
    assert all(q.options[q.answer_index] == 'goes' for q in qs if q.number != 7)       # the right option moved with its letter
    q7 = qs[6]                                          # its solution names the letter: it follows the swap
    assert q7.options[q7.answer_index] == 'goes' and f'Option ({"abcd"[q7.answer_index]}) is right' in q7.solution
    assert bookgen.balance_answers(out) == bookgen.balance_answers(out)                 # deterministic


def test_review_failure_is_reported_not_swallowed(broken_chapter, db, monkeypatch, capsys):
    def down(db, user):
        raise ai.AIUnavailable('empty')
    monkeypatch.setattr(bookgen, '_ask_review', down)
    fixed, failed = bookgen.review(db, broken_chapter, out=print)
    assert fixed == [] and failed and 'must not be published unreviewed' in capsys.readouterr().out


def test_checker_falls_back_to_another_model(monkeypatch):
    from app import nvidia
    tried = []

    def call(system, user, *, model=None, **k):
        tried.append(model)
        if model == config.NVIDIA_CHECK_MODEL:
            raise ai.AIUnavailable('empty')
        return 'OK'
    monkeypatch.setattr(nvidia, 'call', call)
    assert bookgen._nvidia_second_opinion('s', 'u') == 'OK'
    assert tried == [config.NVIDIA_CHECK_MODEL, config.NVIDIA_FALLBACK_MODELS[0]]
