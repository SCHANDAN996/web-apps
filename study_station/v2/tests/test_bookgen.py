import pytest

from app import ai, bookgen, config
from test_bookcheck import mcq_set
from test_books import PROMPT, write

INTRO = 'You are writing the chapter "States & Rivers" for 10th-level learners.'
BODY = 'राज्य और नदियों (States & Rivers) का पूरा पाठ। ' * 40


def test_legacy_autopilot_rollover_preserves_work_and_ignores_new_or_manual_runs(tmp_path, monkeypatch):
    state = tmp_path / 'autopilot'
    state.mkdir()
    (state / 'state.json').write_text('{}')
    source = state / 'unfinished.txt'
    source.write_text('saved Hindi work')
    monkeypatch.setenv('BOOKGEN_REVIEW_CACHE', str(state / 'reviewed.json'))
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path))
    monkeypatch.setenv('GITHUB_REF_NAME', 'main')
    monkeypatch.delenv('BOOKGEN_HINDI_ONLY', raising=False)
    monkeypatch.delenv('BOOKGEN_RATE_POLICY', raising=False)
    monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
    bookgen.request_legacy_autopilot_rollover(lambda *a: None)
    assert not (state / 'STOP').exists()
    monkeypatch.setenv('GITHUB_ACTIONS', 'true')
    bookgen.request_legacy_autopilot_rollover(lambda *a: None)
    assert (state / 'STOP').exists() and source.read_text() == 'saved Hindi work'
    (state / 'STOP').unlink()
    monkeypatch.setenv('BOOKGEN_HINDI_ONLY', '1')
    bookgen.request_legacy_autopilot_rollover(lambda *a: None)
    assert (state / 'STOP').exists()    # Hindi-only runner also needs to adopt the bounded parallel policy.
    (state / 'STOP').unlink()
    monkeypatch.setenv('BOOKGEN_RATE_POLICY', 'parallel-v1')
    bookgen.request_legacy_autopilot_rollover(lambda *a: None)
    assert not (state / 'STOP').exists()


@pytest.fixture
def chapter(tmp_path, monkeypatch):
    root = tmp_path / 'books'
    ch = root / '10th_Level' / 'GK' / 'Foundation_10th_GK_WorldClass' / 'Chapter_07_States_Rivers'
    write(ch / 'Prompts' / 'Chapter_Intro_Prompt.txt', INTRO)
    for name in ('Content_hi.txt', 'Mind_Map.txt', 'Practice_en_Set_01.txt', 'Practice_hi_Set_01.txt'):
        write(ch / 'Prompts' / name, PROMPT + f' ({name})')
    write(ch / 'Content_en.txt', 'Finished English lesson on States & Rivers. ' * 30)                   # done: never touched
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
    assert (chapter / 'Content_en.txt').read_text().startswith('Finished English lesson on States')
    system, first_user = fake_ai[0]
    assert 'No invented PYQs.' in system                                                  # BOOK_RULES.md
    assert INTRO in first_user and '<section_prompt file="Content_hi.txt">' in first_user
    # hi practice set = translation of exactly the English set that was just written
    translate = [u for _, u in fake_ai if 'Translate exactly these questions' in u]
    assert len(translate) == 1 and mcq_set('en').strip() in translate[0]
    assert len(fake_ai) == 4 and bookgen.used_today(db) == 6          # + two blind re-solves of the new set
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
    monkeypatch.setattr(bookgen, '_ask_check', lambda db, user, **kw: checker(user))
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
        return '- "Ganga rises in Kerala" → it rises at Gangotri' if ('file="Content_en.txt"' in user and 'Corrected chapter text' not in user) else 'OK'

    def ask(db, user):
        rewritten.append(user)
        assert 'Gangotri' in user and '<current_file name="Content_en.txt">' in user
        return 'Corrected chapter text about states and rivers. ' * 20
    monkeypatch.setattr(bookgen, '_ask_review', reviewer)
    monkeypatch.setattr(bookgen, '_ask', ask)
    fixed, failed = bookgen.review(db, ch, out=lambda *a: None)
    assert fixed == ['Content_en.txt'] and failed == [] and len(rewritten) == 1
    assert not any('Practice_' in u for u in reviewed) and len(reviewed) == 12      # 10 sections + mind map + corrected section re-review
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
    monkeypatch.setattr(config, 'NVIDIA_CHECK_MODEL', 'test/checker')
    monkeypatch.setattr(config, 'NVIDIA_FALLBACK_MODELS', ['test/fallback'])

    def call(system, user, *, model=None, **k):
        tried.append(model)
        if model == config.NVIDIA_CHECK_MODEL:
            raise ai.AIUnavailable('empty')
        return 'OK'
    monkeypatch.setattr(nvidia, 'call', call)
    assert bookgen._nvidia_second_opinion('s', 'u') == 'OK'
    assert tried == [config.NVIDIA_CHECK_MODEL, config.NVIDIA_FALLBACK_MODELS[0]]


def test_review_skips_sections_that_already_passed(broken_chapter, db, monkeypatch, tmp_path):
    (broken_chapter / 'Prompts' / 'PYQ_en.txt').write_text('Exam pattern notes. ' * 30)
    monkeypatch.setenv('BOOKGEN_REVIEW_CACHE', str(tmp_path / 'reviewed.json'))
    seen = []
    monkeypatch.setattr(bookgen, '_ask_review', lambda db, user: seen.append(user) or 'OK')
    bookgen.review(db, broken_chapter, out=lambda *a: None)
    first = len(seen)
    bookgen.review(db, broken_chapter, out=lambda *a: None)
    assert first > 0 and len(seen) == first                    # second pass: nothing re-reviewed


def test_too_long_section_is_retried_tighter(chapter, db, monkeypatch):
    usage_reset(db)
    asks = []

    def ask(db, user):
        asks.append(user)
        if len(asks) == 1:
            raise ai.AIUnavailable('too_long')
        return BODY
    monkeypatch.setattr(bookgen, '_ask', ask)
    written, failed = bookgen.run(db, chapter, ['Content_hi'], out=lambda *a: None)
    assert written == ['Content_hi.txt'] and 'tighter version' in asks[1]


def test_review_fix_in_the_wrong_language_is_retried(broken_chapter, db, monkeypatch):
    ch = broken_chapter
    (ch / 'Prompts' / 'PYQ_en.txt').write_text('Exam pattern notes. ' * 30)
    monkeypatch.setattr(bookgen, '_ask_review',
                        lambda db, user: '- wrong fact → fix' if ('file="Content_hi.txt"' in user and 'सुधरा हुआ पाठ' not in user) else 'OK')
    answers = iter(['Only English text about states and rivers. ' * 20,
                    'राज्य और नदियों के बारे में सुधरा हुआ पाठ। ' * 20])
    monkeypatch.setattr(bookgen, '_ask', lambda db, user: next(answers))
    fixed, failed = bookgen.review(db, ch, out=lambda *a: None)
    assert fixed == ['Content_hi.txt'] and failed == []
    assert (ch / 'Content_hi.txt').read_text().startswith('राज्य और नदियों के बारे में सुधरा')


def test_question_fixes_turn_problems_into_targeted_instructions():
    fixes = bookgen.question_fixes('Q53:answer_solution_conflict,Q60:leaked_reasoning')
    assert fixes[0].startswith('Q53: the solution') and fixes[1].startswith('Q60: remove')
    assert bookgen.question_fixes('parsed 22 questions, numbers 1…25') is None


def test_audit_confirms_good_keys_and_repairs_disputed_sets(chapter, db, monkeypatch):
    write(chapter / 'Practice_en_Set_01.txt', mcq_set('en'))
    write(chapter / 'Practice_hi_Set_01.txt', mcq_set('hi'))
    agree = '\n'.join(f'{i}: {"abcd"[i % 4]}' for i in range(1, 26))
    monkeypatch.setattr(bookgen, '_ask_check', lambda db, user, system=None, model=None: agree)
    repaired = []
    monkeypatch.setattr(bookgen, 'repair_set', lambda db, ch, n, problems, out, strict=False: repaired.append((n, problems)) or True)
    lines = []
    assert bookgen.audit(db, chapter, lines.append) == ([], [])
    assert lines == ['set 01: key confirmed'] and repaired == []
    monkeypatch.setattr(bookgen, '_ask_check', lambda db, user, system=None, model=None: agree.replace('3: d', '3: a'))
    assert bookgen.audit(db, chapter, lines.append) == (['set 01'], [])
    assert repaired[0][0] == 1 and 'Q3 key d vs re-solve a' in repaired[0][1][0]
    assert repaired[0][1][0].startswith('Set 01 en: answer check:')


def test_puzzle_chapters_also_run_the_solver(db, monkeypatch):
    text = mcq_set('en')
    agree = '\n'.join(f'{i}: {"abcd"[i % 4]}' for i in range(1, 26))
    asked = []
    monkeypatch.setattr(bookgen, '_ask_check', lambda db, user, system=None, model=None: asked.append(system) or (
        agree if system is None else '[{"q": 2, "layout": "row", "n": 3, "people": ["A", "B", "C"], '
        '"clues": [["left_end", "A"], ["right_end", "A"]], "ask": ["who_middle"], '
        '"options": {"a": "A", "b": "B", "c": "C", "d": "cannot be determined"}}]'))
    assert bookgen._key_problem(db, text, puzzles=False) == '' and asked == [None, None]
    assert bookgen._key_problem(db, text, puzzles=True) == 'Q2: clues contradict each other — no arrangement fits all of them'
    assert bookgen.PUZZLE_CHAPTER.search('Chapter_07_Sitting_Arrangement')
    assert not bookgen.PUZZLE_CHAPTER.search('Chapter_23_Sentence_Arrangement')      # English para-jumbles


def test_new_and_audit_sets_both_require_two_blind_resolves(db, monkeypatch):
    agree = '\n'.join(f'{i}: {"abcd"[i % 4]}' for i in range(1, 26))
    calls = []
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'k')
    monkeypatch.setattr(config, 'BOOKGEN_PROVIDER', 'nvidia')

    def check(db, user, system=None, model=None):
        calls.append((model, user))
        assert 'Answer:' not in user and 'Solution:' not in user and 'Source:' not in user
        return agree.replace('\n5: b', '\n5: c') if model else agree

    monkeypatch.setattr(bookgen, '_ask_check', check)
    for strict in (False, True):
        calls.clear()
        assert bookgen._key_problem(db, mcq_set('en'), strict=strict) == 'Q5 key b vs re-solve c'
        assert [model for model, _ in calls] == [None, config.NVIDIA_MODEL]
        assert calls[0][1] == calls[1][1]           # separate solves, neither answer leaks to the other


def test_new_set_is_rejected_when_only_second_checker_disagrees(chapter, db, monkeypatch):
    usage_reset(db)
    monkeypatch.setattr(bookgen, 'balance_answers', lambda text: text)
    monkeypatch.setattr(bookgen, '_ask', lambda db, user: mcq_set('en'))
    agree = '\n'.join(f'{i}: {"abcd"[i % 4]}' for i in range(1, 26))
    calls = []

    def check(db, user, **kwargs):
        calls.append(user)
        return agree if len(calls) % 2 else agree.replace('\n5: b', '\n5: c')

    monkeypatch.setattr(bookgen, '_ask_check', check)
    written, failed = bookgen.run(db, chapter, ['Practice_en_Set_01.txt'], out=lambda *a: None)
    assert written == [] and failed == ['Practice_en_Set_01.txt']
    assert len(calls) == 2 * bookgen.MAX_REPAIR_TRIES
    assert not (chapter / 'Practice_en_Set_01.txt').exists()


@pytest.mark.parametrize('followup', ['- still wrong → another correction', 'OK but I am not sure', ''])
def test_review_rejects_correction_until_reviewer_explicitly_accepts(broken_chapter, db, monkeypatch, tmp_path, followup):
    import json
    ch = broken_chapter
    (ch / 'Prompts' / 'PYQ_en.txt').write_text('Exam pattern notes. ' * 30)
    before = (ch / 'Prompts' / 'Content_hi.txt').read_text()
    replacement = 'राज्य और नदियों के बारे में सुधरा हुआ पाठ। ' * 20
    cache = tmp_path / 'reviewed.json'
    monkeypatch.setenv('BOOKGEN_REVIEW_CACHE', str(cache))

    def reviewer(db, user):
        if 'file="Content_hi.txt"' not in user:
            return 'OK'
        return followup if replacement.strip() in user else '- wrong fact → fix'

    monkeypatch.setattr(bookgen, '_ask_review', reviewer)
    monkeypatch.setattr(bookgen, '_ask', lambda db, user: replacement)
    fixed, failed = bookgen.review(db, ch, out=lambda *a: None)
    assert fixed == [] and failed == ['Content_hi.txt']
    assert not (ch / 'Content_hi.txt').exists()
    assert (ch / 'Prompts' / 'Content_hi.txt').read_text() == before
    import hashlib
    assert hashlib.sha256((replacement.strip() + '\n').encode()).hexdigest() not in json.loads(cache.read_text())


def test_review_checker_failure_does_not_write_or_cache_correction(broken_chapter, db, monkeypatch):
    ch = broken_chapter
    (ch / 'Prompts' / 'PYQ_en.txt').write_text('Exam pattern notes. ' * 30)
    replacement = 'राज्य और नदियों के बारे में सुधरा हुआ पाठ। ' * 20

    def reviewer(db, user):
        if 'file="Content_hi.txt"' not in user:
            return 'OK'
        if replacement.strip() in user:
            raise ai.AIUnavailable('network')
        return '- wrong fact → fix'

    monkeypatch.setattr(bookgen, '_ask_review', reviewer)
    monkeypatch.setattr(bookgen, '_ask', lambda db, user: replacement)
    assert bookgen.review(db, ch, out=lambda *a: None) == ([], ['Content_hi.txt'])
    assert not (ch / 'Content_hi.txt').exists()


def test_repair_translates_a_gutted_hindi_section_from_english(chapter, db, monkeypatch):
    usage_reset(db)
    english = 'Card 1: Trick for counting seats in a row. ' * 40
    write(chapter / 'Flashcards_en.txt', english)
    write(chapter / 'Flashcards_hi.txt', 'कार्ड 1: बहुत छोटा। ' * 12)
    asked = []
    monkeypatch.setattr(bookgen, 'repair_targets', lambda ch: (['Flashcards_hi.txt'], [], [
        'Flashcards_hi.txt: much shorter than the English section (240 vs 1760 chars)']))
    monkeypatch.setattr(bookgen, '_ask', lambda db, user: asked.append(user) or 'कार्ड 1: पंक्ति में सीटें गिनने की ट्रिक। ' * 40)
    written, failed = bookgen.repair(db, chapter)
    assert written == ['Flashcards_hi.txt'] and failed == []
    assert '<section file="Flashcards_en.txt">' in asked[0] and english.strip() in asked[0]
    assert 'translate the whole section above into natural, simple Hindi' in asked[0]


def test_hindi_subject_prompts_preserve_tested_hindi(tmp_path):
    chapter = tmp_path / '10th_Level' / 'Hindi' / 'Chapter_01_Grammar'
    assert bookgen.is_hindi_book(chapter)
    request = bookgen.translation_request('Practice_en_Set_01.txt', 'Which is correct?',
                                          'Practice_hi_Set_01.txt', hindi_book=True)
    assert 'NEVER translate or transliterate a tested Hindi word' in request
    assert 'Keep every answer option exactly identical' in request
    lesson = bookgen.section_translation_request('Content_en.txt', 'Grammar lesson',
                                                 'Content_hi.txt', hindi_book=True)
    assert bookgen.HINDI_BOOK_TRANSLATION in lesson


def test_hindi_subject_translation_rejects_changed_targets_and_options(db, monkeypatch):
    options_en = '(a) Ganga (b) Yamuna (c) Kaveri (d) Narmada'
    options_hi = '(a) "गंगा" (b) "यमुना" (c) "कावेरी" (d) "नर्मदा"'
    english = mcq_set('en').replace(options_en, options_hi).replace('Question about rivers', 'Identify the word "गंगा" in question')
    hindi = mcq_set('hi').replace('(a) गंगा (b) यमुना (c) कावेरी (d) नर्मदा', options_hi).replace('नदी के बारे में प्रश्न', '"गंगा" शब्द का प्रश्न')
    asks = []
    monkeypatch.setattr(bookgen, '_ask', lambda db, request: asks.append(request) or hindi.replace('"कावेरी"', '"नदी"'))
    assert bookgen.translate_set(db, 'Practice_en_Set_01.txt', english, 'Practice_hi_Set_01.txt',
                                 1, out=lambda *a: None, hindi_book=True) is None
    assert len(asks) == bookgen.MAX_REPAIR_TRIES
    monkeypatch.setattr(bookgen, '_ask', lambda db, request: hindi)
    assert bookgen.translate_set(db, 'Practice_en_Set_01.txt', english, 'Practice_hi_Set_01.txt',
                                 1, out=lambda *a: None, hindi_book=True) == hindi.strip() + '\n'


def test_repair_rejects_pair_when_only_second_checker_disagrees(broken_chapter, db, monkeypatch):
    agree = '\n'.join(f'{i}: {"abcd"[i % 4]}' for i in range(1, 26))
    calls = []

    def checker(user):
        calls.append(user)
        return agree if len(calls) % 2 else agree.replace('\n5: b', '\n5: c')

    fake_repair(monkeypatch, checker)
    original = (broken_chapter / 'Prompts' / 'Practice_en_Set_01.txt').read_text()
    assert not bookgen.repair_set(db, broken_chapter, 1, [], out=lambda *a: None)
    assert len(calls) == 2 * bookgen.MAX_REPAIR_TRIES
    assert (broken_chapter / 'Prompts' / 'Practice_en_Set_01.txt').read_text() == original
    assert not (broken_chapter / 'Practice_en_Set_01.txt').exists()
    assert not (broken_chapter / 'Practice_hi_Set_01.txt').exists()


@pytest.fixture
def hindi_chapter(chapter):
    import shutil
    native = chapter.parents[2] / 'Hindi' / chapter.parent.name / chapter.name
    native.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(chapter, native)
    return native


def test_hindi_book_writes_only_native_hindi_and_never_uses_old_english(hindi_chapter, db, monkeypatch):
    old_english = (hindi_chapter / 'Content_en.txt').read_text()
    write(hindi_chapter / 'Practice_en_Set_01.txt', mcq_set('en'))
    asks, checks = [], []
    agree = '\n'.join(f'{i}: {"abcd"[i % 4]}' for i in range(1, 26))
    monkeypatch.setattr(bookgen, 'balance_answers', lambda text: text)
    monkeypatch.setattr(bookgen, '_ask_check', lambda db, user, **kw: checks.append(user) or agree)

    def ask(db, user):
        asks.append(user)
        assert bookgen.HINDI_WRITER in user
        assert 'Translate exactly these questions' not in user
        assert 'Finished English lesson' not in user
        return mcq_set('hi') if 'Practice_hi_Set_01.txt' in user else BODY

    monkeypatch.setattr(bookgen, '_ask', ask)
    written, failed = bookgen.run(db, hindi_chapter, ['Content_hi', 'Content_en', 'Practice_hi_Set_01', 'Practice_en_Set_01'], out=lambda *a: None)
    assert written == ['Content_hi.txt', 'Practice_hi_Set_01.txt'] and failed == []
    assert len(asks) == 2 and len(checks) == 2
    assert all('उत्तर:' not in c and 'हल:' not in c for c in checks)
    assert (hindi_chapter / 'Content_en.txt').read_text() == old_english
    assert (hindi_chapter / 'Practice_en_Set_01.txt').read_text() == mcq_set('en')
    asks.clear()
    assert bookgen.run(db, hindi_chapter, ['Content_hi', 'Practice_hi_Set_01'], out=lambda *a: None) == ([], [])
    assert asks == []  # native results survive chapter retries without new authoring calls


def test_hindi_repair_set_is_native_and_requires_two_blind_checks(hindi_chapter, db, monkeypatch):
    asks, checks = [], []
    agree = '\n'.join(f'{i}: {"abcd"[i % 4]}' for i in range(1, 26))
    monkeypatch.setattr(bookgen, 'balance_answers', lambda text: text)
    monkeypatch.setattr(bookgen, '_ask_check', lambda db, user, **kw: checks.append(user) or agree)
    monkeypatch.setattr(bookgen, '_ask', lambda db, user: asks.append(user) or mcq_set('hi'))
    assert bookgen.repair_set(db, hindi_chapter, 1, ['Set 01 hi: wrong answer'], out=lambda *a: None)
    assert len(checks) == 2 and len(asks) == 1 and bookgen.HINDI_WRITER in asks[0]
    assert (hindi_chapter / 'Practice_hi_Set_01.txt').read_text() == mcq_set('hi').strip() + '\n'
    assert not (hindi_chapter / 'Practice_en_Set_01.txt').exists()


def test_hindi_review_and_repair_ignore_english_files(hindi_chapter, db, monkeypatch):
    write(hindi_chapter / 'Content_hi.txt', BODY)
    seen = []
    monkeypatch.setattr(bookgen, '_ask_review', lambda db, user: seen.append(user) or 'OK')
    assert bookgen.review(db, hindi_chapter, out=lambda *a: None) == ([], [])
    assert len(seen) == 1 and 'file="Content_hi.txt"' in seen[0]
    monkeypatch.setattr(bookgen, 'repair_targets', lambda ch: (['Content_hi.txt', 'Content_en.txt'], [], ['Content_hi.txt: wrong fact']))
    asks = []
    monkeypatch.setattr(bookgen, '_ask', lambda db, user: asks.append(user) or BODY)
    assert bookgen.repair(db, hindi_chapter, out=lambda *a: None) == (['Content_hi.txt'], [])
    assert len(asks) == 1 and bookgen.HINDI_WRITER in asks[0]


def test_hindi_audit_uses_hindi_without_english_dependency(hindi_chapter, db, monkeypatch):
    write(hindi_chapter / 'Practice_hi_Set_01.txt', mcq_set('hi'))
    write(hindi_chapter / 'Practice_en_Set_01.txt', mcq_set('en'))
    asks = []
    agree = '\n'.join(f'{i}: {"abcd"[i % 4]}' for i in range(1, 26))
    monkeypatch.setattr(bookgen, '_ask_check', lambda db, user, **kw: asks.append(user) or agree)
    assert bookgen.audit(db, hindi_chapter, out=lambda *a: None) == ([], [])
    assert len(asks) == 2 and all('नदी के बारे में प्रश्न' in user and 'Question about rivers' not in user for user in asks)


def test_hindi_native_system_overrides_generic_bilingual_rules(hindi_chapter, db, monkeypatch):
    from app import nvidia
    monkeypatch.setattr(config, 'NVIDIA_API_KEY', 'test-key')
    monkeypatch.setattr(config, 'BOOKGEN_PROVIDER', 'nvidia')
    seen = []
    monkeypatch.setattr(nvidia, 'call', lambda system, user, **kw: seen.append((system, user)) or BODY)
    assert bookgen.run(db, hindi_chapter, ['Content_hi'], out=lambda *a: None) == (['Content_hi.txt'], [])
    assert bookgen.HINDI_ONLY_POLICY in seen[0][0] and bookgen.HINDI_WRITER in seen[0][1]
    mindmap = bookgen.section_request(hindi_chapter, 'Mind_Map.txt')
    assert 'only Hindi labels' in mindmap and 'Hindi (Devanagari) only' in mindmap
