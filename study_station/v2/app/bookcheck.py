"""
Check book chapters (study_station/books/**/Chapter_NN_*) for completeness and quality.

    python -m app.bookcheck ../books/10th_Level/GK/Foundation_10th_GK_WorldClass/Chapter_07_States_Rivers
    python -m app.bookcheck ../books/10th_Level/GK/Foundation_10th_GK_WorldClass   # whole book, one line per chapter

A section file is "todo" while it still holds the generator prompt. Practice sets must parse
into 25 clean MCQs (same parser the importer uses), and hi/en set N must be the same questions
in the same order with the same answer letters. Exit code 0 = chapter complete and clean, 1 = not.
"""
import re
import sys
from pathlib import Path

from .importers import parse_mcq_text, quality_problem

PROMPT_MARK = re.compile(r'^\s*# Chapter:|@content_agent|@mcq_generator', re.M)
# Chat-UI debris and assistant chatter that must never be in a book.
JUNK = re.compile(r'^\s*(?:text|Copy|Download|Diagram|Fullscreen|markdown|Copy code)\s*$|'
                  r'^\s*(?:Here is (?:the|your)|Here\'s (?:the|your)|यह रहा आपका|I hope this|Let me know|As an AI|'
                  r'मुझे उम्मीद है|Sure[,!])', re.M | re.I)
# Claims a book must not make without a source we can check (CLAUDE.md rules 1-2).
UNSOURCED = re.compile(r'अनुमानित संख्या|approximate(?:d)? (?:count|number)|\(concept\)', re.I)
SETS_PER_LANG = 6
QS_PER_SET = 25


def is_prompt(text):
    return bool(PROMPT_MARK.search(text[:800]))


def section_files(chapter):
    """Section files of a chapter, wherever this book keeps them (chapter root or Prompts/)."""
    chapter = Path(chapter)
    files = {}
    for d in (chapter / 'Prompts', chapter):
        if d.is_dir():
            for p in sorted(d.glob('*.txt')):
                if p.name != 'Chapter_Intro_Prompt.txt' and not p.name.startswith('Master_Prompt'):
                    files.setdefault(p.name, p)       # Prompts/ wins (where finished books keep content)
    return files


def check_practice_pair(en_path, hi_path):
    problems = []
    sets = {}
    for lang, p in (('en', en_path), ('hi', hi_path)):
        if p is None:
            problems.append(f'{lang}: missing')
            continue
        text = p.read_text(errors='replace')
        if is_prompt(text):
            problems.append(f'{lang}: todo')
            continue
        qs = parse_mcq_text(text)
        sets[lang] = qs
        if len(qs) != QS_PER_SET:
            problems.append(f'{lang}: {len(qs)}/{QS_PER_SET} parsed')
        bad = [f'Q{q.number}:{r}' for q in qs if (r := quality_problem(q))]
        if bad:
            problems.append(f'{lang}: ' + ','.join(bad[:5]))
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
        text = p.read_text(errors='replace')
        if is_prompt(text) or len(text.strip()) < 300:
            todo.append(name)
            continue
        if (m := JUNK.search(text)):
            problems.append(f'{name}: chat debris "{m.group(0).strip()[:30]}"')
        if (m := UNSOURCED.search(text)):
            problems.append(f'{name}: unsourced claim "{m.group(0)}"')
        if name == 'Mind_Map.txt' and 'graph' not in text and 'mindmap' not in text:
            problems.append('Mind_Map.txt: no mermaid graph')
    for n in range(1, SETS_PER_LANG + 1):
        en, hi = files.get(f'Practice_en_Set_{n:02d}.txt'), files.get(f'Practice_hi_Set_{n:02d}.txt')
        if en is None and hi is None:
            if n == 1:
                todo.append('Practice sets')
            break
        for pr in check_practice_pair(en, hi):
            (todo if pr.endswith('todo') or pr.endswith('missing') else problems).append(f'Set {n:02d} {pr}')
    return todo, problems


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
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
