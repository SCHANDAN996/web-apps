"""
Check book chapters (study_station/books/**/Chapter_NN_*) for completeness and quality.

    python -m app.bookcheck ../books/10th_Level/GK/Foundation_10th_GK_WorldClass/Chapter_07_States_Rivers
    python -m app.bookcheck ../books/10th_Level/GK/Foundation_10th_GK_WorldClass   # whole book, one line per chapter

    python -m app.bookcheck --status           # every book in books/QUEUE.txt: chapters OK / TODO / FIX
    python -m app.bookcheck --next             # the next chapter to work on (queue order), with its todo list
    python -m app.bookcheck --fill-meta <book or chapter dir>   # create/complete chapter.json files

A section file is "todo" while it still holds the generator prompt. Practice sets must parse
into 25 clean MCQs (same parser the importer uses), and hi/en set N must be the same questions
in the same order with the same answer letters. The rules are in books/BOOK_RULES.md; every rule
that a program can check is checked here. Exit code 0 = chapter complete and clean, 1 = not.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

from .catalog import TOPICS
from .importers import parse_mcq_text, quality_problem

BOOKS_ROOT = Path(__file__).resolve().parents[2] / 'books'
KNOWN_TOPICS = {f'{subj}/{slug}' for subj, items in TOPICS.items() for slug, *_ in items}

PROMPT_MARK = re.compile(r'^\s*# Chapter:|@content_agent|@mcq_generator', re.M)
# Chat-UI debris and assistant chatter that must never be in a book.
JUNK = re.compile(r'^\s*(?:text|Copy|Download|Diagram|Fullscreen|markdown|Copy code)\s*$|'
                  r'^\s*(?:Here is (?:the|your)|Here\'s (?:the|your)|यह रहा आपका|I hope this|Let me know|As an AI|'
                  r'मुझे उम्मीद है|Sure[,!])', re.M | re.I)
# Claims a book must not make without a source we can check (CLAUDE.md rules 1-2).
UNSOURCED = re.compile(r'अनुमानित संख्या|approximate(?:d)? (?:count|number)|\(concept\)', re.I)
# "Source: SSC CGL 2019 …" is allowed only with a link to the official paper/answer key (BOOK_RULES §4).
SOURCE_LINE = re.compile(r'^\s*(?:Source|स्रोत)\s*[:：](.*)$', re.M | re.I)
EXAM = re.compile(r'UPSC|SSC|CGL|CHSL|MTS|NTPC|RRB|IBPS|SBI|PCS|CDS|NDA|Railway|रेलवे|बैंक', re.I)
YEAR = re.compile(r'\b(?:19[5-9]\d|20[0-4]\d)\b')
DEVANAGARI = re.compile(r'[\u0900-\u097F]')
LATIN = re.compile(r'[A-Za-z]')
SETS_PER_LANG = 6
QS_PER_SET = 25


# Short "stub" prompts (English books) carry no @agent markers — same rule as books/migrate_layout.py.
STUB = re.compile(r'प्रॉम्प्ट|prompt|तैयार करें|Each with 4 options|प्रत्येक में 4 विकल्प|MCQs \((?:Questions|प्रश्न)', re.I)
STUB_MAX_CHARS = 700


def is_prompt(text):
    return bool(PROMPT_MARK.search(text[:800])) or (len(text.strip()) < STUB_MAX_CHARS and bool(STUB.search(text)))


def _head(path, n=2000):        # enough for the marker and the stub-length test
    with open(path, encoding='utf-8', errors='replace') as f:
        return f.read(n)


def section_files(chapter):
    """Section files of a chapter. Finished content lives in the chapter root; Prompts/ holds the
    generator prompts (older chapters still keep their content there). Per section: the root file
    unless it is still a prompt, else the Prompts/ copy unless that is a prompt, else the prompt."""
    chapter = Path(chapter)
    found = {}
    for d in (chapter, chapter / 'Prompts'):
        if d.is_dir():
            for p in sorted(d.glob('*.txt')):
                if p.is_symlink():                       # never read through links (see check_chapter)
                    continue
                if p.name != 'Chapter_Intro_Prompt.txt' and not p.name.startswith('Master_Prompt'):
                    found.setdefault(p.name, []).append(p)
    return {name: next((p for p in paths if not is_prompt(_head(p))), paths[-1])
            for name, paths in sorted(found.items())}


def language_problem(name, text):
    """A *_hi file must be mostly Devanagari, an *_en file mostly Latin letters."""
    m = re.search(r'_(hi|en)(?:_Set_\d+)?\.txt$', name)
    if not m:
        return None
    dev, lat = len(DEVANAGARI.findall(text)), len(LATIN.findall(text))
    if m.group(1) == 'hi' and dev < lat * 0.5:
        return f'{name}: Hindi file is mostly not in Hindi'
    if m.group(1) == 'en' and dev > lat * 0.2:
        return f'{name}: English file contains a lot of Hindi'
    return None


def source_problems(name, text):
    bad = [line.strip() for line in SOURCE_LINE.findall(text)
           if EXAM.search(line) and YEAR.search(line) and 'http' not in line]
    return [f'{name}: unverified exam/year source "{bad[0][:50]}" (+{len(bad) - 1} more)'] if bad else []


def check_practice_pair(en_path, hi_path):
    problems = []
    sets = {}
    for lang, p in (('en', en_path), ('hi', hi_path)):
        if p is None:
            problems.append(f'{lang}: missing')
            continue
        text = p.read_text(encoding='utf-8', errors='replace')
        if is_prompt(text):
            problems.append(f'{lang}: todo')
            continue
        qs = parse_mcq_text(text)
        sets[lang] = qs
        if len(qs) != QS_PER_SET:
            problems.append(f'{lang}: {len(qs)}/{QS_PER_SET} parsed')
        bad = [f'Q{q.number}:{r}' for q in qs if (r := quality_problem(q))]
        bad += [f'Q{q.number}:duplicate_options' for q in qs
                if len({o.strip().lower() for o in q.options}) < 4]
        if bad:
            problems.append(f'{lang}: ' + ','.join(bad[:5]))
        n = int(re.search(r'_Set_(\d+)', p.name).group(1))
        want = list(range((n - 1) * QS_PER_SET + 1, n * QS_PER_SET + 1))
        if len(qs) == QS_PER_SET and [q.number for q in qs] != want:
            problems.append(f'{lang}: numbering should be {want[0]}–{want[-1]}')
        if len(qs) == QS_PER_SET and Counter(q.answer_index for q in qs).most_common(1)[0][1] > 15:
            problems.append(f'{lang}: answers not spread (one letter is correct in >15 of 25)')
        if (lp := language_problem(p.name, text)):
            problems.append(lp)
        problems += source_problems(p.name, text)
    if len(sets) == 2 and len(sets['en']) == len(sets['hi']):
        diff = [q.number for q, h in zip(sets['en'], sets['hi']) if q.answer_index != h.answer_index]
        if diff:
            problems.append(f'hi/en answer mismatch at Q{diff[:5]}')
    return problems


def check_chapter(chapter):
    """Return (todo_sections, problems) for one chapter directory."""
    files = section_files(chapter)
    todo, problems = [], []
    for name, p in files.items():
        if name.startswith('Practice_'):
            continue
        text = p.read_text(encoding='utf-8', errors='replace')
        if is_prompt(text) or len(text.strip()) < 300:
            todo.append(name)
            continue
        if (m := JUNK.search(text)):
            problems.append(f'{name}: chat debris "{m.group(0).strip()[:30]}"')
        if (m := UNSOURCED.search(text)):
            problems.append(f'{name}: unsourced claim "{m.group(0)}"')
        if name.startswith('Mind_Map') and not re.search(r'```mermaid\s*\n\s*(?:graph|flowchart|mindmap)', text):
            problems.append(f'{name}: no ```mermaid graph block')
        if (lp := language_problem(name, text)):
            problems.append(lp)
        problems += source_problems(name, text)
        if '10th_Level' in str(chapter) and re.search(r'\bUPSC\b', text):
            problems.append(f'{name}: mentions UPSC in a 10th-level book (BOOK_RULES §2)')
    for n in range(1, SETS_PER_LANG + 1):
        en, hi = files.get(f'Practice_en_Set_{n:02d}.txt'), files.get(f'Practice_hi_Set_{n:02d}.txt')
        if en is None and hi is None:
            if n == 1:
                todo.append('Practice sets')
            break
        for pr in check_practice_pair(en, hi):
            (todo if pr.endswith('todo') or pr.endswith('missing') else problems).append(f'Set {n:02d} {pr}')
    problems += meta_problems(chapter)
    links = [p.name for d in (Path(chapter), Path(chapter) / 'Prompts') if d.is_dir() for p in d.iterdir() if p.is_symlink()]
    if links:
        problems.append(f'symlinks are not allowed in books (security): {", ".join(sorted(links))}')
    return todo, problems


def meta_problems(chapter):
    p = Path(chapter) / 'chapter.json'
    if not p.is_file():
        return ['chapter.json missing']
    try:
        meta = json.loads(p.read_text(encoding='utf-8'))
    except ValueError:
        return ['chapter.json is not valid JSON']
    out = []
    if not (meta.get('title_hi') and meta.get('title_en')):
        out.append('chapter.json: title_hi/title_en missing')
    if meta.get('type') not in ('static', 'dynamic'):
        out.append('chapter.json: type must be "static" or "dynamic"')
    elif meta['type'] == 'static' and meta.get('topic') not in KNOWN_TOPICS:
        out.append(f'chapter.json: topic {meta.get("topic")!r} is not a catalog topic (app/catalog.py)')
    if meta.get('status') not in ('draft', 'reviewed'):
        out.append('chapter.json: status must be "draft" or "reviewed"')
    return out


def is_dynamic(chapter):
    try:
        return json.loads((Path(chapter) / 'chapter.json').read_text(encoding='utf-8')).get('type') == 'dynamic'
    except (OSError, ValueError):
        return False


def queue():
    """Book directories in priority order (books/QUEUE.txt, one path per line, # comments)."""
    q = BOOKS_ROOT / 'QUEUE.txt'
    lines = q.read_text(encoding='utf-8').splitlines() if q.is_file() else []
    return [BOOKS_ROOT / l.split('#')[0].strip() for l in lines if l.split('#')[0].strip()]


def chapter_status(ch):
    todo, problems = check_chapter(ch)
    return ('OK' if not todo and not problems else 'TODO' if todo else 'FIX'), todo, problems


def next_chapter():
    """First chapter in queue order that is not OK; FIX before TODO within a book is not needed —
    chapters are taken in book order so a book gets finished before the next one starts."""
    for book in queue():
        for ch in sorted(book.glob('Chapter_*')):
            if is_dynamic(ch):
                continue
            status, todo, problems = chapter_status(ch)
            if status != 'OK':
                return ch, status, todo, problems
    return None


def main(argv=None):
    argv = argv or sys.argv[1:]
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')    # Hindi output on a Windows console
    except (AttributeError, ValueError):
        pass
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == '--status':
        total = Counter()
        for book in queue():
            c = Counter(chapter_status(ch)[0] if not is_dynamic(ch) else 'LIVE' for ch in sorted(book.glob('Chapter_*')))
            total.update(c)
            print(f'{book.relative_to(BOOKS_ROOT)}:  ' + '  '.join(f'{k} {c[k]}' for k in ('OK', 'FIX', 'TODO', 'LIVE') if c[k]))
        print('ALL: ' + '  '.join(f'{k} {total[k]}' for k in ('OK', 'FIX', 'TODO', 'LIVE') if total[k]))
        return 0
    if argv[0] == '--fill-meta' and len(argv) > 1:
        from .books import fill_meta
        t = Path(argv[1])
        for ch in ([t] if t.name.startswith('Chapter_') else sorted(t.glob('Chapter_*'))):
            if (fields := fill_meta(ch)):
                print(f'{ch.name}: set {", ".join(fields)}')
        return 0
    if argv[0] == '--next':
        nxt = next_chapter()
        if nxt is None:
            print('ALL DONE — every chapter in books/QUEUE.txt is OK')
            return 0
        ch, status, todo, problems = nxt
        mode = 'fix' if status == 'FIX' else 'write'
        print(f'NEXT: {ch}\nMODE: {mode}')
        for t in todo:
            print('   todo   ', t)
        for pr in problems:
            print('   problem', pr)
        return 1
    target = Path(argv[0])
    chapters = [target] if target.name.startswith('Chapter_') else sorted(target.glob('Chapter_*'))
    ok = True
    for ch in chapters:
        todo, problems = check_chapter(ch)
        status = 'OK  ' if not todo and not problems else 'TODO' if todo else 'FIX '
        ok &= status == 'OK  '
        print(f'{status} {ch.name}  todo={len(todo)} problems={len(problems)}')
        if len(chapters) == 1 or '-v' in argv:
            for t in todo:
                print('   todo   ', t)
            for pr in problems:
                print('   problem', pr)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
