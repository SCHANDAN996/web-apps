"""
Parsers for the MCQ text files generated earlier (books/**/Practice_{en,hi}_Set_NN.txt)
and for the jobs export (website/js/jobs_data.js).

The generated files come in many slightly different shapes, and some were saved
from a math renderer that split fractions over several lines. We only keep a
question when every part is clean: text, exactly four options, an answer letter.
Anything doubtful is dropped rather than shown to students.
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

LETTERS = 'abcd'

QSTART = re.compile(r'^\s*(?:\*\*)?(?:Q\.?\s*|प्रश्न\s*)?(\d{1,3})\s*[.)।:]\s*(?:\*\*)?\s*(.*)$')
OPT = re.compile(r'\(([a-dA-D])\)\s*|(?:^|\s)([A-D])\)\s+')
ANSWER = re.compile(r'^\s*(?:\*\*)?(?:Correct\s+Answer|Answer|Ans|उत्तर|सही\s+उत्तर)\s*(?:\*\*)?\s*[:：]\s*(?:\*\*)?\s*\(?([a-dA-D])\b')
SOLUTION = re.compile(r'^\s*(?:\*\*)?(?:Solution|Explanation|हल|व्याख्या)\s*(?:\*\*)?\s*[:：]\s*(?:\*\*)?\s*(.*)$')
SOURCE = re.compile(r'^\s*(?:\*\*)?(?:Source|स्रोत)\s*(?:\*\*)?\s*[:：]\s*(.*)$')
DIFF_INLINE = re.compile(r'^\((easy|medium|hard|आसान|सरल|मध्यम|कठिन)\)\s*', re.I)
DIFF_RANGE = re.compile(r'(?:Questions?|Q|प्रश्न)\s*(\d+)\s*[–\-]\s*(?:Q)?(\d+)\s*[:：]?\s*\(?(Easy|Medium|Hard|आसान|सरल|मध्यम|कठिन)', re.I)
DIFF_WORD = {'easy': 'easy', 'आसान': 'easy', 'सरल': 'easy',
             'medium': 'medium', 'मध्यम': 'medium', 'hard': 'hard', 'कठिन': 'hard'}


@dataclass
class ParsedQuestion:
    number: int
    text: str
    options: list
    answer_index: int
    solution: str = ''
    source_claim: str = ''
    difficulty: str = ''


@dataclass
class _Draft:
    number: int
    lines: list = field(default_factory=list)


def _garbled(text):
    """Math-renderer debris: many lines that are a lone digit or symbol."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return False
    tiny = sum(1 for l in lines if len(l) <= 2)
    return tiny >= 4 and tiny / len(lines) > 0.3


def _clean(s):
    s = s.replace('​', '').replace('**', '')
    s = re.sub(r'\\([~*_])', r'\1', s)
    return re.sub(r'\s+', ' ', s).strip()


def _clean_keep_lines(s):
    # Also drop markdown emphasis left around whole lines: "*question?*" → "question?"
    lines = [re.sub(r'^\*(.+)\*$', r'\1', _clean(l)) for l in s.splitlines()]
    return '\n'.join(l for l in lines if l)


def _split_options(text):
    """'(a) 1 (b) 2 (c) 3 (d) 4' → ['1','2','3','4'] or None."""
    marks = list(OPT.finditer(text))
    if len(marks) != 4:
        return None, None
    found = [(m.group(1) or m.group(2)).lower() for m in marks]
    if found != list(LETTERS):
        return None, None
    stem = text[:marks[0].start()]
    opts = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i < 3 else len(text)
        opts.append(_clean(text[m.end():end]))
    if any(not o for o in opts):
        return None, None
    return stem, opts


def _parse_draft(d):
    body, answer, solution, source = [], None, [], ''
    mode = 'body'
    for line in d.lines:
        if (m := ANSWER.match(line)):
            answer = LETTERS.index(m.group(1).lower())
            mode = 'after'
            continue
        if (m := SOLUTION.match(line)):
            solution.append(m.group(1))
            mode = 'solution'
            continue
        if (m := SOURCE.match(line)):
            source = _clean(m.group(1))
            mode = 'after'
            continue
        if mode == 'body':
            body.append(line)
        elif mode == 'solution':
            solution.append(line)
    raw = '\n'.join(body)
    if answer is None or _garbled(raw) or _garbled('\n'.join(solution)):
        return None
    stem, options = _split_options('\n'.join(body))
    if options is None:
        return None
    stem = _clean_keep_lines(TRAP_HINT.sub('', stem))
    difficulty = ''
    if (m := DIFF_INLINE.match(stem)):
        difficulty = DIFF_WORD[m.group(1).lower()]
        stem = stem[m.end():]
    if len(stem) < 3 or len(stem) > 1200:
        return None
    return ParsedQuestion(d.number, stem, options, answer, _clean(' '.join(solution)), source, difficulty)


def parse_mcq_text(text):
    """Return a list of clean ParsedQuestion from one practice-set file."""
    ranges = [(int(a), int(b), DIFF_WORD[w.lower()]) for a, b, w in DIFF_RANGE.findall(text)]
    drafts, cur = [], None
    for line in text.splitlines():
        m = QSTART.match(line)
        # A new question starts only when the number follows on from the last one
        # (stops "2. Then..." inside a solution from being read as a question).
        if m and (cur is None or int(m.group(1)) == cur.number + 1 or not cur.lines):
            cur = _Draft(int(m.group(1)), [m.group(2)])
            drafts.append(cur)
        elif cur is not None:
            cur.lines.append(line)
    out, seen = [], set()
    for d in drafts:
        q = _parse_draft(d)
        if q is None or q.number in seen:
            continue
        seen.add(q.number)
        if not q.difficulty:
            q.difficulty = next((w for a, b, w in ranges if a <= q.number <= b), 'medium')
        out.append(q)
    return out


PATH_RE = re.compile(r'(10th|12th|Graduation)_Level/(\w+?)/(?:.*/)?Chapter_(\d+)_([A-Za-z_]+)/(?:Prompts/)?Practice_(en|hi)_Set_(\d+)\.txt$')
SUBJECT_DIRS = {'Maths': 'quant', 'Reasoning': 'reasoning', 'GK': 'ga', 'English': 'english'}
LEVELS = {'10th': '10th', '12th': '12th', 'Graduation': 'graduate'}


def discover_practice_files(root):
    """Yield (level, subject, topic_slug, lang, set_no, path) for every practice file."""
    for p in sorted(Path(root).rglob('Practice_*_Set_*.txt')):
        rel = p.as_posix()
        if '/website/' in rel or p.stat().st_size < 1500:
            continue
        m = PATH_RE.search(rel)
        if not m or m.group(2) not in SUBJECT_DIRS:
            continue
        level, subj, _, name, lang, set_no = m.groups()
        yield LEVELS[level], SUBJECT_DIRS[subj], name.lower().replace('_', '-'), lang, int(set_no), p


def parse_jobs_js(text):
    """Extract the JOBS_DATA array from website/js/jobs_data.js."""
    start = text.index('[')
    end = text.rindex(']') + 1
    return json.loads(text[start:end])


NUM = re.compile(r'-?\d+(?:\.\d+)?')


def _first_number(s):
    m = NUM.search(s.replace(',', ''))
    return m.group(0) if m else None


def answer_conflicts_with_solution(q):
    """True when the solution's final result matches a *different* option.

    Catches the common AI mistake where the worked solution reaches one value
    but the answer key names another. Only all-numeric, distinct options are checked.
    """
    nums = [_first_number(o) for o in q.options]
    if any(n is None for n in nums) or len(set(nums)) < 4 or not q.solution:
        return False
    tail = set(NUM.findall(q.solution.replace(',', '')[-60:]))
    if nums[q.answer_index] in tail:
        return False
    return any(n in tail for i, n in enumerate(nums) if i != q.answer_index)


# AI "thinking out loud" that leaked into generated solutions.
LEAKED_REASONING = re.compile(
    r"\b(?:I'll|I will|Let me|Let us re|Nice!|Hmm|Wait|Actually,|Oops|recalculat\w*|re-?check\w*|"
    r"I think|मैं इसे|मैं इस|रुकिए|दोबारा जाँच|तो Q\d+|Q\d+:)(?![A-Za-z])", re.I)
# Teaching phrases ("Let's decode…", "We need to find…", "ठीक है, अब…") are normal in solutions and are not
# treated as leaked reasoning; first-person chatter and self-correction still are.
# In the question itself ordinary sentences ("I will meet you…", "मैं इस बिंदु पर…") are content, so only
# unmistakable model chatter counts there.
LEAKED_IN_QUESTION = re.compile(
    r"\b(?:Let me|Hmm|Wait,|Oops|recalculat\w*|re-?check\w*|रुकिए|दोबारा जाँच|तो Q\d+)(?![A-Za-z])", re.I)


# The generator sometimes admits the question is broken ("figures may be inconsistent") — never show those.
BROKEN = re.compile(r'असंगत हो सकत|आँकड़े असंगत|अपूर्ण (?:जानकारी|डेटा)|data (?:may be|is|are) (?:inconsistent|insufficient)|'
                    r'inconsistent (?:data|figures)|question (?:is|seems) (?:flawed|ambiguous|incorrect)', re.I)
# "(⚠️ परीक्षक का जाल: …)" / "(Examiner's Trap: …)" inside a question gives the answer away — cut it out.
WARN = '(?:\u26a0\ufe0f?\\s*)?'          # optional ⚠️ (the emoji is two code points)
TRAP_HINT = re.compile(WARN + r'\(\s*' + WARN + r'(?:परीक्षक का जाल|Examiner[’\']?s? Trap|Trap\b)[^)\n]{0,300}\)\s*'
                       r'|^\s*' + WARN + r'(?:परीक्षक का जाल|Examiner[’\']?s? Trap)\b[^\n]*\n?', re.I | re.M)

# Questions that only make sense next to an earlier question or passage.
NEEDS_CONTEXT = re.compile(
    r"same arrangement|another question|above (information|passage|data|arrangement)|"
    r"previous question|उपरोक्त|ऊपर दी|पिछले प्रश्न|इसी व्यवस्था", re.I)
# "Consider the statements: 1… 2… Which of the above…?" carries its own context.
STATEMENTS = re.compile(r'कथन|statements?\b', re.I)


# Quoted example sentences ("I will wait for you") are content, not leaked reasoning.
QUOTED = re.compile(r'"[^"\n]{1,200}"|“[^”\n]{1,200}”|‘[^’\n]{1,200}’|\*[^*\n]{1,200}\*|_{2}[^_\n]{1,200}_{2}|'
                    r"(?<![A-Za-z])'[^'\n]{1,200}'(?![A-Za-z])")
BLANK = re.compile(r'_{3,}')


def _unquoted(text):
    return QUOTED.sub(' ', text or '')


def quality_problem(q):
    """Return a short reason string if the question should not reach students."""
    if LEAKED_REASONING.search(_unquoted(q.solution)) or LEAKED_IN_QUESTION.search(_unquoted(q.text)):
        return 'leaked_reasoning'
    if BROKEN.search(q.text) or any(BROKEN.search(o) for o in q.options):
        return 'broken_question'
    self_contained = STATEMENTS.search(q.text) and q.text.count('\n') >= 2
    if NEEDS_CONTEXT.search(q.text) and not self_contained:
        return 'needs_context'
    if answer_conflicts_with_solution(q):
        return 'answer_solution_conflict'
    return None


def _signature(q):
    return set(NUM.findall(q.text + ' ' + ' '.join(q.options)))


def is_translation_pair(en, hi):
    """Same question in two languages? Generated hi/en sets often differ, so only
    pair when the answer agrees and the numbers in question+options match."""
    if en.answer_index != hi.answer_index:
        return False
    a, b = _signature(en), _signature(hi)
    if len(a | b) < 2:
        return False       # nothing to compare reliably (most GK questions)
    return len(a & b) / len(a | b) >= 0.8
