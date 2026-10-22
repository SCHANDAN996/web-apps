"""Pick what to post, straight from the book files (no database).

Only chapters whose bookcheck is OK, only questions that pass every rule in PROMO_PLAN.md (quality check on the
Hindi and the English copy, same answer in both, short enough for a Telegram poll, no figure/passage/"both (a)
and (b)" questions), never an id that is already in the posted-log. The choice is seeded by (day, slot, batch),
so a --dry-run shows exactly what the real run will post.
"""
import json
import random
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

from .. import bookcheck
from ..importers import parse_mcq_text, quality_problem

SUBJECTS = ['GK', 'Reasoning', 'Maths', 'English']
SUBJECT_HI = {'GK': 'सामान्य ज्ञान', 'Reasoning': 'रीज़निंग', 'Maths': 'गणित', 'English': 'अंग्रेज़ी'}
LEVELS = ['10th_Level', '12th_Level', 'Graduation_Level']
LEVEL_HI = {'10th_Level': '10वीं स्तर', '12th_Level': '12वीं स्तर', 'Graduation_Level': 'स्नातक स्तर'}
# Mon/Thu 10th, Tue/Fri 12th, Wed/Sat Graduation, Sun mixed (None)
DAY_LEVEL = ['10th_Level', '12th_Level', 'Graduation_Level', '10th_Level', '12th_Level', 'Graduation_Level', None]

MAX_QUESTION = 250          # Telegram allows 300; the subject tag takes the rest
MAX_OPTION = 80             # Telegram allows 100
MAX_EXPLANATION = 200       # Telegram limit
TRICK_MIN, TRICK_MAX = 200, 900

NEEDS_PICTURE = re.compile(
    r'\b(?:figure|diagram|graph|table|passage|image|picture|venn|chart)s?\b|चित्र|आकृति|तालिका|गद्यांश|आरेख|ग्राफ|'
    r'दर्पण प्रतिबिंब|जल प्रतिबिंब|\bcloze\b|रिक्त स्थान\s*(?:सं(?:ख्या)?\.?\s*)?\(?\d+|\bblank\s*(?:no\.?\s*)?\(?\d+|paragraph|पैराग्राफ|according to the (?:author|writer)|लेखक के अनुसार', re.I)
LETTER_REF = re.compile(r'\(\s*[a-dA-D]\s*\)|\b[a-dA-D]\s*(?:and|और|तथा|&)\s*[a-dA-D]\b')
TRICK_HEAD = re.compile(
    r'^\s*(?:#{1,4}\s|\*\*\s*(?:\S+\s+)?(?:ट्रिक|Trick|Mnemonic|हुक|Hook)|\d{1,2}\.\s+\S|'
    r'[^\w\s*#|]{1,3}\s*(?:ट्रिक|Trick|Mnemonic)\s*\d)')
NUMBERED_TRICK = re.compile(r'(?:ट्रिक|Trick|Mnemonic|हुक|Hook)\s*[-–:#]?\s*\d|^[\s*#]*\d{1,2}\.\s', re.I)
RULE_LINE = re.compile(r'^\s*[━═─—_=*-]{3,}\s*$', re.M)
TIP = re.compile(r'^(?:चुनने से पहले|ध्यान दें|याद रखें|टिप|tip|note)\b', re.I)
SKIP_TRICK = re.compile(r'Skip Strategy|स्किप|│|┌|└|```|^\s*\|', re.I | re.M)


def books_root():
    return bookcheck.BOOKS_ROOT


def rel(path):
    return Path(path).resolve().relative_to(books_root().resolve()).as_posix()


def books(level=None, subject=None):
    out = []
    for b in bookcheck.queue():
        parts = Path(rel(b)).parts
        if (level is None or parts[0] == level) and (subject is None or parts[1] == subject):
            out.append(b)
    return out


@lru_cache(maxsize=None)
def chapter_ok(ch):
    return bookcheck.chapter_status(Path(ch))[0] == 'OK'


def chapter_title(ch):
    try:
        meta = json.loads((Path(ch) / 'chapter.json').read_text(encoding='utf-8'))
        return meta.get('title_hi') or meta.get('title_en') or ''
    except (OSError, ValueError):
        return ''


def _clean(text):
    return re.sub(r'\*\*|__|`', '', ' '.join((text or '').split()))


def short_solution(text, limit=MAX_EXPLANATION):
    """One line, at most `limit` chars; cut at a sentence end when possible."""
    s = _clean(text)
    if len(s) <= limit:
        return s
    cut = s[:limit - 1]
    end = max(cut.rfind('। '), cut.rfind('. '), cut.rfind('।'))
    if end > limit // 3:
        return cut[:end + 1].strip()
    return cut.rstrip() + '…'


def explanation(solution, answer, limit=MAX_EXPLANATION):
    """'उत्तर: <answer>। <the sentence of the solution that names the answer>' — solutions often open with the
    trap, so the first 200 chars alone may never say what is right."""
    head = f'उत्तर: {_clean(answer)}' + ('' if re.search(r'[।.!?]$', _clean(answer)) else '।')
    sents = [x.strip() for x in re.split(r'(?<=[।!?])\s+|(?<=\.)\s+(?=\S)', _clean(solution)) if x.strip()]
    key = _clean(answer).lower()
    trivial = re.compile(r'^(?:अतः|इसलिए|so|hence|therefore|thus)?[\s,]*(?:सही\s*)?(?:उत्तर|the answer|answer)\b.{0,%d}$' % (len(key) + 12), re.I)
    sents = [x for x in sents if not trivial.match(x)]
    sents = [re.sub(r'^\s*(?:चुनने से पहले|ध्यान दें|याद रखें|परीक्षा में)[^;]*;\s*', '', x) for x in sents]
    sents = [x for x in sents if x and not TIP.match(x)]
    best = [x for x in sents if key and key in x.lower()] or sents[-1:]
    fitting = [x for x in best if len(head) + 1 + len(x) <= limit]
    rest = max(fitting, key=len) if fitting else ''   # the fullest working that still fits
    if not rest and best:
        rest = short_solution(best[-1], limit - len(head) - 1)
    return f'{head} {rest}'.strip()[:limit]


def question_problem(hi, en):
    """Why this hi/en pair must not be posted, or None."""
    if en is None or hi.answer_index != en.answer_index:
        return 'hi/en answer differ'
    if (r := quality_problem(hi)) or (r := quality_problem(en)):
        return r
    if len(hi.text) > MAX_QUESTION:
        return 'question too long'
    if len(hi.options) != 4 or any(not o.strip() or len(o) > MAX_OPTION for o in hi.options):
        return 'option too long'
    if len({o.strip().lower() for o in hi.options}) < 4:
        return 'duplicate options'
    if NEEDS_PICTURE.search(hi.text) or NEEDS_PICTURE.search(en.text):
        return 'needs a picture/passage'
    if any(LETTER_REF.search(o) for o in hi.options + en.options):
        return 'option refers to other options'
    return None


@lru_cache(maxsize=None)
def chapter_questions(ch):
    """All postable questions of one chapter (bookcheck OK), as dicts."""
    ch = Path(ch)
    if not chapter_ok(str(ch)):
        return ()
    parts = Path(rel(ch)).parts
    out = []
    for n in range(1, bookcheck.SETS_PER_LANG + 1):
        hp, ep = ch / f'Practice_hi_Set_{n:02d}.txt', ch / f'Practice_en_Set_{n:02d}.txt'
        if not (hp.is_file() and ep.is_file()):
            continue
        en = {q.number: q for q in parse_mcq_text(ep.read_text(encoding='utf-8'))}
        for q in parse_mcq_text(hp.read_text(encoding='utf-8')):
            if question_problem(q, en.get(q.number)):
                continue
            out.append({'id': f'{rel(ch)}#Set{n:02d}#Q{q.number}', 'level': parts[0], 'subject': parts[1],
                        'chapter': rel(ch), 'question': q.text, 'options': list(q.options),
                        'answer': q.answer_index, 'explanation': explanation(q.solution, q.options[q.answer_index]),
                        'difficulty': q.difficulty or 'medium'})
    return tuple(out)


def _chapters(level, subject, rng):
    chs = [c for b in books(level, subject) for c in sorted(b.glob('Chapter_*')) if c.is_dir()]
    rng.shuffle(chs)
    return chs


def _pick_one(level, subject, rng, posted, used_chapters, difficulties, ok=None):
    for ch in _chapters(level, subject, rng):
        if rel(ch) in used_chapters:
            continue
        cands = [q for q in chapter_questions(str(ch))
                 if q['id'] not in posted and q['difficulty'] in difficulties and (ok is None or ok(q))]
        if cands:
            return rng.choice(cands)
    return None


def day_level(day, rng):
    return DAY_LEVEL[day.weekday()] or rng.choice(LEVELS)


def pick_quiz(day: date, batch: int, posted, used_chapters=(), n=5):
    """`n` polls: one per subject plus a rotating extra; easy/medium; chapters not used earlier today."""
    rng = random.Random(f'{day.isoformat()}|quiz|{batch}')
    subjects = SUBJECTS + [SUBJECTS[(day.toordinal() + batch) % len(SUBJECTS)]]
    used, picked = set(used_chapters), []
    for subject in subjects[:n]:
        level = day_level(day, rng)
        q = _pick_one(level, subject, rng, set(posted), used, ('easy', 'medium'))
        if q:
            picked.append(q)
            used.add(q['chapter'])
    return sorted(picked, key=lambda q: q['difficulty'] != 'easy')


def pick_weekly(day: date, posted, n=20):
    """Sunday test: all three levels and all four subjects, easy → hard."""
    rng = random.Random(f'{day.isoformat()}|weekly')
    used, picked = set(), []
    order = {'easy': 0, 'medium': 1, 'hard': 2}
    for i in range(n):
        subject, level = SUBJECTS[i % len(SUBJECTS)], LEVELS[(i // len(SUBJECTS)) % len(LEVELS)]
        q = _pick_one(level, subject, rng, set(posted) | {p['id'] for p in picked}, used, tuple(order))
        if q:
            picked.append(q)
            used.add(q['chapter'])
    return sorted(picked, key=lambda q: order.get(q['difficulty'], 1))


def trick_blocks(text):
    """Split a Short_Tricks/Memory_Hooks file into self-contained trick blocks of TRICK_MIN–TRICK_MAX chars."""
    blocks, cur = [], []
    for line in text.splitlines():
        if TRICK_HEAD.match(line) and cur:
            blocks.append('\n'.join(cur).strip())
            cur = []
        if line.strip() in ('---', '***'):
            continue
        cur.append(line)
    if cur:
        blocks.append('\n'.join(cur).strip())
    out = []
    for b in blocks[1:] if len(blocks) > 1 else blocks:      # the first block is the file's title/intro
        b = re.sub(r'\n{3,}', '\n\n', RULE_LINE.sub('', b)).strip()
        if not NUMBERED_TRICK.search(b.split('\n', 1)[0]):
            continue                                          # summaries/intros lean on the rest of the file
        if TRICK_MIN <= len(b) <= TRICK_MAX and not SKIP_TRICK.search(b) and '�' not in b:
            out.append(b)
    return out


def pick_trick(day: date, posted, batch=0):
    rng = random.Random(f'{day.isoformat()}|trick|{batch}')
    subjects = SUBJECTS[day.toordinal() % len(SUBJECTS):] + SUBJECTS[:day.toordinal() % len(SUBJECTS)]
    posted = set(posted)
    for subject in subjects:
        for ch in _chapters(day_level(day, rng), subject, rng):
            if not chapter_ok(str(ch)):
                continue
            for name in ('Short_Tricks_hi.txt', 'Memory_Hooks_hi.txt'):
                p = ch / name
                if not p.is_file():
                    continue
                blocks = [(f'{rel(ch)}#{name}#{i}', b) for i, b in enumerate(trick_blocks(p.read_text(encoding='utf-8')))]
                blocks = [x for x in blocks if x[0] not in posted]
                if blocks:
                    tid, text = rng.choice(blocks)
                    return {'id': tid, 'chapter': rel(ch), 'subject': subject, 'title': chapter_title(ch), 'text': text}
    return None
