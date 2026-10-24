"""
One-time layout migration (BOOK_RULES.md §1). Dry run by default:

    python3 books/migrate_layout.py            # show what would change
    python3 books/migrate_layout.py --apply

For every books/**/Chapter_NN_*:
  * finished content found in Prompts/ moves to the chapter root (if the root already has a
    finished copy, the better one wins: more parsed MCQs for practice sets, else the longer text);
  * Prompts/ gets its prompt back from the old duplicate tree (study_station/<Level>/…), when there is one;
  * a prompt file sitting in the chapter root moves into Prompts/;
  * chapter.json is created if missing (titles from README.md, type dynamic for current affairs).
"""
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # study_station/books
OLD = HERE.parent                                 # study_station/ (old duplicate trees live here)
sys.path.insert(0, str(OLD / 'v2'))
from app.importers import parse_mcq_text          # noqa: E402

PROMPT_MARKS = ('# Chapter:', '@content_agent', '@mcq_generator', '@pyq_agent')
KEEP_IN_PROMPTS = ('Chapter_Intro_Prompt.txt',)
TIME_SENSITIVE = re.compile(r'Awards|Sports|Govt_Schemes|Reports_Indices|Budget|Defence|Science_Tech|Books_Authors',
                            re.I)


# English books use short stubs that point at Master_Prompt_*.txt instead of the @agent markers.
STUB = re.compile(r'प्रॉम्प्ट|prompt|तैयार करें|Each with 4 options|प्रत्येक में 4 विकल्प|MCQs \((?:Questions|प्रश्न)', re.I)


def is_prompt(text):
    return any(m in text[:800] for m in PROMPT_MARKS) or (len(text.strip()) < 700 and bool(STUB.search(text)))


def read(p):
    return p.read_text(encoding='utf-8', errors='replace')


def score(p):
    t = read(p)
    if is_prompt(t):
        return -1
    if p.name.startswith('Practice_'):
        return len(parse_mcq_text(t)) * 100000 + len(t)
    return len(t)


def old_copy(chapter, name):
    """Same chapter's prompt in the old duplicate tree, if any."""
    rel = chapter.relative_to(HERE)
    for cand in (OLD / rel / 'Prompts' / name, OLD / rel / name):
        if cand.exists() and is_prompt(read(cand)):
            return cand
    return None


def titles(chapter):
    readme = chapter / 'README.md'
    if readme.exists():
        first = read(readme).splitlines()[0].lstrip('# ').strip()
        if ' / ' in first:
            hi, en = first.split(' / ', 1)
            return hi.strip(), en.strip()
    name = re.sub(r'^Chapter_\d+_', '', chapter.name).replace('_', ' ')
    return name, name


def plan_chapter(chapter):
    ops = []
    prompts = chapter / 'Prompts'
    if prompts.is_dir():
        for p in sorted(prompts.glob('*.txt')):
            if p.name in KEEP_IN_PROMPTS or p.name.startswith('Master_Prompt') or is_prompt(read(p)):
                continue
            root = chapter / p.name
            if not root.exists() or score(p) > score(root):
                ops.append(('move', p, root))
            else:
                ops.append(('drop', p, None))          # root copy is better; prompt restored below
            if (src := old_copy(chapter, p.name)):
                ops.append(('restore', src, p))
    for p in sorted(chapter.glob('*.txt')):
        if is_prompt(read(p)) and not (prompts / p.name).exists():
            ops.append(('to_prompts', p, prompts / p.name))
    meta = chapter / 'chapter.json'
    if not meta.exists():
        hi, en = titles(chapter)
        ops.append(('meta', None, meta, {
            'title_hi': hi, 'title_en': en, 'topic': '',
            'type': 'dynamic' if 'Current_Affairs' in chapter.name else 'static',
            'status': 'draft', 'as_of': None,
            'notes': 'time-sensitive facts: set as_of after checking' if TIME_SENSITIVE.search(chapter.name) else ''}))
    return ops


def apply(op):
    kind = op[0]
    if kind == 'move':
        _, src, dst = op
        shutil.move(src, dst)
    elif kind == 'drop':
        op[1].unlink()
    elif kind == 'restore':
        _, src, dst = op
        if not dst.exists():
            shutil.copyfile(src, dst)
    elif kind == 'to_prompts':
        _, src, dst = op
        dst.parent.mkdir(exist_ok=True)
        shutil.move(src, dst)
    elif kind == 'meta':
        op[2].write_text(json.dumps(op[3], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main(argv):
    do = '--apply' in argv
    counts = {}
    for chapter in sorted(HERE.rglob('Chapter_*')):
        if not chapter.is_dir() or chapter.name == 'Prompts':
            continue
        for op in plan_chapter(chapter):
            counts[op[0]] = counts.get(op[0], 0) + 1
            if '-v' in argv:
                print(op[0], *(str(x.relative_to(OLD)) for x in op[1:3] if isinstance(x, Path)))
            if do:
                apply(op)
    print(('applied' if do else 'dry run') + ':', counts)


if __name__ == '__main__':
    main(sys.argv[1:])
