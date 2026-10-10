"""
Books: discover the chapter folders under BOOKS_DIR and render their sections as safe HTML.

    BOOKS_DIR/<Level>/<Subject>/[<Book>_WorldClass/]Chapter_NN_Name/
        Content_hi.txt, Key_Facts_en.txt, Mind_Map.txt, ...   finished sections (chapter root)
        Prompts/…                                              generator prompts (older chapters: content too)
        chapter.json                                           optional metadata (title, topic, type, status, as_of)

The app only reads this tree. A section is shown when its file is finished (not a prompt, not too
short, no chat debris — same rules as app/bookcheck.py). Practice sets are not shown as text: the
chapter page starts a practice attempt on the matching catalog topic instead (see topic_for_chapter;
app/seed.py uses the same mapping to import the sets).

Rendering never passes file text through as HTML: every line is escaped first, then a small,
fixed set of tags is added (headings, lists, tables, bold, rules, line breaks).
"""
import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from markupsafe import Markup, escape

from . import catalog, config
from .bookcheck import JUNK, is_prompt, section_files
from .i18n import t

log = logging.getLogger('books')

LEVEL_DIRS = {'10th_Level': '10th', '12th_Level': '12th', 'Graduation_Level': 'graduate'}
LEVEL_ORDER = ['10th', '12th', 'graduate']
SUBJECT_DIRS = {'Maths': 'quant', 'Reasoning': 'reasoning', 'GK': 'ga', 'English': 'english'}
SUBJECT_GUESS = (('Math', 'quant'), ('Reasoning', 'reasoning'), ('GK', 'ga'), ('English', 'english'))
SUBJECT_ORDER = ['quant', 'reasoning', 'ga', 'english']
SUBJECT_WORD = {'quant': 'maths', 'reasoning': 'reasoning', 'ga': 'gk', 'english': 'english'}

# (file-name key, url slug) in reading order. Mind_Map is one file for both languages.
SECTIONS = [('Content', 'content'), ('Key_Facts', 'key-facts'), ('Feynman', 'feynman'), ('Mind_Map', 'mind-map'),
            ('Flashcards', 'flashcards'), ('PYQ', 'pyq'), ('Memory_Hooks', 'memory-hooks'),
            ('Short_Tricks', 'short-tricks'), ('Important_Formulas', 'important-formulas'),
            ('Important_Rules', 'important-rules')]
SECTION_BY_SLUG = {slug: key for key, slug in SECTIONS}
MIN_CHARS = 300                       # shorter files are stubs (bookcheck counts them as todo)
BOTH = '*'                            # language key for single-file sections (Mind_Map)

# Chapter folder (subject, name) → catalog topic, where the names differ. Chapters whose name is
# already a catalog topic slug map to it directly; chapter.json "topic" overrides both.
CHAPTER_TOPICS = {
    # Chapters whose folder name differs from the catalog slug
    ('english', 'para-jumbles-adv'): 'english/para-jumbles',
    ('english', 'sentence-arrangement'): 'english/para-jumbles',
    ('english', 'rc-adv'): 'english/reading-comprehension',
    ('english', 'rc-basic'): 'english/reading-comprehension',
    ('english', 'critical-reading'): 'english/reading-comprehension',
    ('english', 'precis-writing'): 'english/reading-comprehension',
    ('english', 'error-log'): 'english/spotting-errors',
    ('english', 'placement-test'): 'english/mixed-practice',
    ('english', 'revision-tracker'): 'english/mixed-practice',
    # General knowledge
    ('ga', 'states-rivers'): 'ga/indian-geography',
    ('ga', 'world-geography'): 'ga/physical-geography',
    ('ga', 'economy-basic'): 'ga/economy',
    ('ga', 'economic-terms'): 'ga/economy',
    ('ga', 'budget-economic-survey'): 'ga/economy',
    ('ga', 'govt-schemes'): 'ga/economy',
    ('ga', 'reports-indices'): 'ga/economy',
    ('ga', 'physics-daily'): 'science/physics',
    ('ga', 'chemistry'): 'science/chemistry',
    ('ga', 'biology'): 'science/biology',
    ('ga', 'awards'): 'ga/awards-books',
    ('ga', 'books-authors'): 'ga/awards-books',
    ('ga', 'days-dates'): 'ga/important-days',
    ('ga', 'culture-art'): 'ga/art-culture',
    ('ga', 'advanced-science-tech'): 'ga/science-tech',
    ('ga', 'environment-conventions'): 'ga/environment',
    ('ga', 'advanced-polity'): 'ga/polity',
    # Maths
    ('quant', 'number-system-advanced'): 'quant/number-system',
    ('quant', 'coordinate-geometry'): 'quant/geometry',
    ('quant', 'heights-distances'): 'quant/trigonometry',
    ('quant', 'complex-numbers'): 'quant/algebra',
    # Reasoning
    ('reasoning', 'puzzles'): 'reasoning/puzzles-basic',
    ('reasoning', 'advanced-puzzles'): 'reasoning/puzzles-basic',
    ('reasoning', 'syllogism'): 'reasoning/statement-conclusion',
    ('reasoning', 'statement-assumption'): 'reasoning/statement-conclusion',
    ('reasoning', 'statement-argument'): 'reasoning/statement-conclusion',
    # English
    ('english', 'tense'): 'english/tenses',
    ('english', 'articles'): 'english/articles-prepositions',
    ('english', 'preposition'): 'english/articles-prepositions',
    ('english', 'voice'): 'english/active-passive',
    ('english', 'narration'): 'english/direct-indirect',
    ('english', 'synonyms'): 'english/synonyms-antonyms',
    ('english', 'antonyms'): 'english/synonyms-antonyms',
    ('english', 'word-roots'): 'english/synonyms-antonyms',
    ('english', 'verb'): 'english/subject-verb-agreement',
    ('english', 'pronoun'): 'english/spotting-errors',
    ('english', 'adjective'): 'english/spotting-errors',
    ('english', 'adverb'): 'english/spotting-errors',
    ('english', 'conjunction'): 'english/spotting-errors',
    ('english', 'error-spotting-basic'): 'english/spotting-errors',
    ('english', 'error-spotting-adv'): 'english/spotting-errors',
    ('english', 'fill-in-blanks-basic'): 'english/fill-in-the-blanks',
    ('english', 'fill-in-blanks-adv'): 'english/fill-in-the-blanks',
    ('english', 'cloze-test'): 'english/fill-in-the-blanks',
    ('english', 'cloze-test-adv'): 'english/fill-in-the-blanks',
    ('english', 'sentence-improvement-basic'): 'english/sentence-improvement',
    ('english', 'sentence-improvement-adv'): 'english/sentence-improvement',
    ('english', 'sentence-structure'): 'english/sentence-improvement',
}
KNOWN_TOPICS = {(s, tp[0]) for s, tps in catalog.TOPICS.items() for tp in tps}


def _topic_ref(ref):
    subj, _, slug = (ref or '').partition('/')
    return (subj, slug) if (subj, slug) in KNOWN_TOPICS else None


def topic_for_chapter(subject, chapter_name, meta=None):
    """(subject_slug, topic_slug) of the catalog topic a chapter's practice sets belong to, or None.
    `chapter_name` is the folder name part after the number, e.g. 'States_Rivers' or 'states-rivers'."""
    name = chapter_name.lower().replace('_', '-')
    if meta and (ref := _topic_ref(meta.get('topic'))):
        return ref
    if (subject, name) in CHAPTER_TOPICS:
        return _topic_ref(CHAPTER_TOPICS[(subject, name)])
    # Current-affairs chapters (Current_Affairs_6M …) have no static topic: CA quizzes come from AIR/PIB.
    return (subject, name) if (subject, name) in KNOWN_TOPICS else None


# ------------------------------------------------------------------ chapter.json
META_TYPES = ('static', 'dynamic')
META_STATUS = ('draft', 'reviewed')


def regular_file(p):
    """A real file, not a symlink: a link in books/ could expose any file the app can read."""
    p = Path(p)
    return p.is_file() and not p.is_symlink()


def atomic_write(path, text):
    """Write via a random temp file in the same folder + fsync + rename (never follows a planted link)."""
    import tempfile
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_meta(chapter_dir):
    """Validated chapter.json fields ({} when missing or broken — a warning is logged)."""
    p = Path(chapter_dir) / 'chapter.json'
    if not regular_file(p):
        return {}
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        log.warning('ignoring %s: %s', p, e)
        return {}
    if not isinstance(data, dict):
        log.warning('ignoring %s: not a JSON object', p)
        return {}
    out = {}
    for k in ('title_hi', 'title_en', 'notes'):
        if isinstance(data.get(k), str) and data[k].strip():
            out[k] = data[k].strip()[:200]
    if isinstance(data.get('topic'), str) and data['topic'].strip():    # '' = use the mapping table
        if _topic_ref(data['topic']):
            out['topic'] = data['topic']
        else:
            log.warning('%s: unknown topic %r', p, data['topic'])
    out['type'] = data.get('type') if data.get('type') in META_TYPES else 'static'
    out['status'] = data.get('status') if data.get('status') in META_STATUS else 'draft'
    as_of = data.get('as_of')
    out['as_of'] = str(as_of) if as_of is not None and re.fullmatch(r'(19|20)\d\d', str(as_of)) else None
    return out


# ------------------------------------------------------------------ index
@dataclass
class Chapter:
    slug: str                    # '07-states-rivers'
    number: int
    name: str                    # 'States_Rivers'
    path: Path
    title_hi: str
    title_en: str
    sections: dict               # 'Content' → {'hi': Path, 'en': Path}; 'Mind_Map' may also have '*' (both)
    meta: dict
    topic: tuple | None          # catalog (subject, topic)
    book: 'Book' = field(default=None, repr=False)

    @property
    def dynamic(self):
        return self.meta.get('type') == 'dynamic'

    @property
    def reviewed(self):
        return self.meta.get('status') == 'reviewed'

    @property
    def readable(self):
        return self.dynamic or bool(self.sections)

    def langs(self, key):
        return [l for l in ('hi', 'en', BOTH) if l in self.sections.get(key, {})]


@dataclass
class Book:
    slug: str
    level: str
    subject: str
    path: Path
    chapters: list

    @property
    def readable_chapters(self):
        return [c for c in self.chapters if c.readable]

    def title(self, lang):
        return f"{t('book_subject_' + self.subject, lang)} · {t('book_level_' + self.level, lang)}"

    def chapter(self, slug):
        return next((c for c in self.chapters if c.slug == slug), None)

    def neighbours(self, chapter):
        """(previous, next) readable chapter around `chapter`."""
        rs = self.readable_chapters
        i = rs.index(chapter) if chapter in rs else -1
        if i < 0:
            return None, None
        return (rs[i - 1] if i > 0 else None), (rs[i + 1] if i + 1 < len(rs) else None)


_lock = threading.Lock()
_state = {'at': 0.0, 'root': None, 'books': [], 'by_slug': {}}
_chapter_cache = {}                   # path → (signature, Chapter)
_file_cache = {}                      # path → ((mtime_ns, size), ok)
_render_cache = {}                    # (path, mtime_ns, size, key, lang) → Markup
CHAPTER_RE = re.compile(r'^Chapter_(\d+)_(.+)$')


def _slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def _has_chapters(d):
    try:
        return any(c.is_dir() and CHAPTER_RE.match(c.name) for c in d.iterdir())
    except OSError:
        return False


def _subject(dir_name, book_name=None):
    if dir_name in SUBJECT_DIRS:
        return SUBJECT_DIRS[dir_name]
    for word, slug in SUBJECT_GUESS:
        if word in (book_name or dir_name):
            return slug
    return None


def _signature(chapter_dir):
    sig = []
    for d in (chapter_dir, chapter_dir / 'Prompts'):
        try:
            with os.scandir(d) as it:
                for e in it:
                    if e.is_file():
                        st = e.stat()
                        sig.append((d.name, e.name, st.st_mtime_ns, st.st_size))
        except OSError:
            pass
    return tuple(sorted(sig))


def _read(path):
    return Path(path).read_text(encoding='utf-8', errors='replace')


def _file_ok(path, key):
    """Finished, clean section file? Cached until the file changes."""
    st = path.stat()
    stamp = (st.st_mtime_ns, st.st_size)
    hit = _file_cache.get(path)
    if hit and hit[0] == stamp:
        return hit[1]
    text = _read(path)
    ok = not is_prompt(text) and len(text.strip()) >= MIN_CHARS and not JUNK.search(text)
    if ok and key == 'Mind_Map':
        ok = parse_mermaid(text) is not None
    _file_cache[path] = (stamp, ok)
    return ok


README_TITLE = re.compile(r'^#\s*(.+?)\s+/\s+(.+?)\s*$')


def _titles(chapter_dir, name, meta):
    hi = en = None
    readme = chapter_dir / 'README.md'
    if regular_file(readme):
        first = _read(readme).lstrip().split('\n', 1)[0]
        if (m := README_TITLE.match(first)):
            hi, en = m.group(1), m.group(2)
    fallback = name.replace('_', ' ')
    return meta.get('title_hi') or hi or fallback, meta.get('title_en') or en or fallback


def _load_chapter(chapter_dir, subject):
    sig = _signature(chapter_dir)
    hit = _chapter_cache.get(chapter_dir)
    if hit and hit[0] == sig:
        return hit[1]
    m = CHAPTER_RE.match(chapter_dir.name)
    files = section_files(chapter_dir)
    sections = {}
    for key, _ in SECTIONS:
        names = {l: f'{key}_{l}.txt' for l in ('hi', 'en')}
        if key == 'Mind_Map':
            names[BOTH] = 'Mind_Map.txt'          # one file for both languages, or Mind_Map_{hi,en}.txt
        avail = {l: files[n] for l, n in names.items() if n in files and _file_ok(files[n], key)}
        if avail:
            sections[key] = avail
    meta = load_meta(chapter_dir)
    title_hi, title_en = _titles(chapter_dir, m.group(2), meta)
    ch = Chapter(slug=f'{int(m.group(1)):02d}-{_slug(m.group(2))}', number=int(m.group(1)), name=m.group(2),
                 path=chapter_dir, title_hi=title_hi, title_en=title_en, sections=sections, meta=meta,
                 topic=topic_for_chapter(subject, m.group(2), meta))
    _chapter_cache[chapter_dir] = (sig, ch)
    return ch


def subject_of(chapter_dir):
    """Catalog subject slug of a chapter, from its folder path (…/<Subject>/[<Book>_WorldClass/]Chapter_NN_…)."""
    for part in reversed(Path(chapter_dir).parts[:-1]):
        if (subj := _subject(part)) and (part in SUBJECT_DIRS or part.endswith('_WorldClass')):
            return subj
    return None


def fill_meta(chapter_dir):
    """Create chapter.json, or fill its missing/invalid fields (never overwrites valid ones).
    Returns the list of fields it set. The topic comes from the chapter→topic mapping; if no catalog
    topic fits, it stays '' and bookcheck keeps reporting it for a human/agent to choose."""
    chapter_dir = Path(chapter_dir)
    p = chapter_dir / 'chapter.json'
    try:
        meta = json.loads(p.read_text(encoding='utf-8')) if regular_file(p) else {}
    except ValueError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    m = CHAPTER_RE.match(chapter_dir.name)
    name = m.group(2) if m else chapter_dir.name
    changed = []
    hi, en = _titles(chapter_dir, name, {})
    if not meta.get('title_hi'):
        meta['title_hi'] = hi; changed.append('title_hi')
    if not meta.get('title_en'):
        meta['title_en'] = en; changed.append('title_en')
    if meta.get('type') not in META_TYPES:
        meta['type'] = 'dynamic' if 'Current_Affairs' in chapter_dir.name else 'static'; changed.append('type')
    if meta.get('status') not in META_STATUS:
        meta['status'] = 'draft'; changed.append('status')
    if meta['type'] == 'static' and not _topic_ref(meta.get('topic')):
        ref = topic_for_chapter(subject_of(chapter_dir), name, None)
        new = f'{ref[0]}/{ref[1]}' if ref else ''
        if new != meta.get('topic'):
            meta['topic'] = new; changed.append('topic')
    meta.setdefault('as_of', None)
    meta.setdefault('notes', '')
    if changed:
        atomic_write(p, json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
    return changed


def _make_book(path, level, subject, generic, taken):
    slug = f'{level}-{SUBJECT_WORD[subject]}' if generic else _slug(re.sub(r'_WorldClass$', '', path.name))
    base, n = slug, 2
    while slug in taken:
        slug, n = f'{base}-{n}', n + 1
    taken.add(slug)
    chapters = []
    for d in sorted(path.iterdir()):
        if d.is_dir() and CHAPTER_RE.match(d.name):
            chapters.append(_load_chapter(d, subject))
    chapters.sort(key=lambda c: c.number)
    book = Book(slug=slug, level=level, subject=subject, path=path, chapters=chapters)
    for c in chapters:
        c.book = book
    return book


def _scan(root):
    books, taken = [], set()
    if not root.is_dir():
        return books
    for level_dir in sorted(root.iterdir()):
        level = LEVEL_DIRS.get(level_dir.name)
        if not level or not level_dir.is_dir():
            continue
        for child in sorted(level_dir.iterdir()):
            if not child.is_dir():
                continue
            if _has_chapters(child):
                if (subj := _subject(child.name)):
                    books.append(_make_book(child, level, subj, child.name in SUBJECT_DIRS, taken))
                continue
            for gc in sorted(child.iterdir()):
                if gc.is_dir() and _has_chapters(gc) and (subj := _subject(child.name, gc.name)):
                    books.append(_make_book(gc, level, subj, False, taken))
    books.sort(key=lambda b: (LEVEL_ORDER.index(b.level), SUBJECT_ORDER.index(b.subject), b.slug))
    return books


def index(force=False):
    """All books (readable or not). Re-scanned at most every BOOKS_RECHECK_SECONDS; unchanged
    chapters and files are not re-read (mtime/size signatures)."""
    root = Path(config.BOOKS_DIR)
    fresh = lambda: _state['root'] == root and time.monotonic() - _state['at'] < config.BOOKS_RECHECK_SECONDS  # noqa: E731
    if not force and fresh():
        return _state['books']
    # Stale but present: answer from the old index and refresh in the background (no request waits).
    if not force and _state.get('books') is not None and _state['root'] == root and config.BOOKS_RECHECK_SECONDS > 0:
        if _lock.acquire(blocking=False):
            def refresh():
                try:
                    books = _scan(root)
                    _state.update(at=time.monotonic(), root=root, books=books, by_slug={b.slug: b for b in books})
                finally:
                    _lock.release()
            threading.Thread(target=refresh, daemon=True, name='books-refresh').start()
        return _state['books']
    with _lock:
        if force or not fresh():
            books = _scan(root)
            _state.update(at=time.monotonic(), root=root, books=books, by_slug={b.slug: b for b in books})
    return _state['books']


def get_book(slug):
    index()
    return _state['by_slug'].get(slug)


def readable_books():
    # A book whose only "readable" chapter is the live current-affairs link has nothing to read yet.
    return [b for b in index() if any(not c.dynamic for c in b.readable_chapters)]


# ------------------------------------------------------------------ text → safe HTML
EMOJI_START = re.compile('^[\U0001F000-\U0001FAFF☀-➿⬀-⯿⌚-⏿]')
HEADING = re.compile(r'^(#{1,6})\s+(.+?)\s*#*$')
RULE = re.compile(r'^(?:-{3,}|─{3,}|━{3,}|═{3,}|_{3,}|\*{3,}|={3,}|—{3,})$')
BULLET = re.compile(r'^\s*[-•·*▪●◦➤►✓✔]\s+(.+)$')
NUMBERED = re.compile(r'^\s*(\d{1,3})[.)]\s+(.+)$')
PIPE_SEP = re.compile(r'^:?-{2,}:?$')
BOLD = re.compile(r'\*\*(?=\S)(.+?)(?<=\S)\*\*')
BR_ESCAPED = re.compile(r'&lt;br\s*/?&gt;', re.I)
LABEL = re.compile(r'^([^\d:：<>&]{2,28}?)([:：])(\s)')
END_PUNCT = ('.', '।', '?', '!', ':', ';', ',', '|')


MAX_LINE = 4000          # longer lines are shown as plain escaped text (keeps every regex linear-time)
MAX_MERMAID_LINE = 500   # real mermaid lines are short


def inline(text):
    """Escape one line, then add the few inline marks we support (bold, <br>)."""
    if len(text) > MAX_LINE:
        return str(escape(text.strip()))
    s = str(escape(text.strip()))
    s = BR_ESCAPED.sub('<br>', s)
    return BOLD.sub(r'<strong>\1</strong>', s)


def _label_line(text):
    """'स्मृति-सूत्र: …' → bold label. Only short, word-only labels."""
    s = inline(text)
    m = LABEL.match(s)
    if m and len(m.group(1).split()) <= 4 and '<' not in m.group(1):
        return f'<strong>{m.group(1)}{m.group(2)}</strong>{s[m.end(2):]}'
    return s


def _cells(line, sep):
    if sep == '|':
        line = line.strip()
        line = line[1:] if line.startswith('|') else line
        line = line[:-1] if line.endswith('|') else line
        return [c.strip() for c in line.split('|')]
    return [c.strip() for c in line.strip().split('\t')]


def _table(rows):
    rows = [r for r in rows if not all(PIPE_SEP.match(c) for c in r if c) or not any(r)]
    if not rows:
        return ''
    width = max(len(r) for r in rows)
    head, body = rows[0], rows[1:]
    th = ''.join(f'<th scope="col">{inline(c)}</th>' for c in head + [''] * (width - len(head)))
    trs = ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r + [''] * (width - len(r))) + '</tr>'
                  for r in body)
    return (f'<div class="table-scroll"><table class="book-table"><thead><tr>{th}</tr></thead>'
            f'<tbody>{trs}</tbody></table></div>')


def _is_tab_row(line):
    s = line.strip()
    return '\t' in s and len([c for c in s.split('\t') if c.strip()]) >= 2


def _is_block_start(s, raw):
    return bool(not s or s.startswith('```') or RULE.match(s) or (len(s) <= 300 and HEADING.match(s)) or BULLET.match(raw)
                or NUMBERED.match(raw) or (s.startswith('|') and s.count('|') >= 2) or _is_tab_row(raw))


def render_text(text):
    """Book text → safe HTML (Markup). Everything from the file is escaped."""
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    out, para = [], []
    i, n = 0, len(lines)

    def flush():
        if para:
            out.append('<p>' + '<br>'.join(para) + '</p>')
            para.clear()

    while i < n:
        raw = lines[i].rstrip()
        s = raw.strip()
        if not s:
            flush()
            i += 1
            continue
        if s.startswith('```'):
            flush()
            lang, body, i = s[3:].strip().lower(), [], i + 1
            while i < n and not lines[i].strip().startswith('```'):
                body.append(lines[i])
                i += 1
            i += 1
            tree = parse_mermaid('\n'.join(body)) if lang in ('mermaid', '') else None
            out.append(render_tree(tree) if tree else '<pre class="book-pre">' + str(escape('\n'.join(body))) + '</pre>')
            continue
        if RULE.match(s):
            flush()
            out.append('<hr>')
            i += 1
            continue
        if len(s) <= 300 and (m := HEADING.match(s)):
            flush()
            lvl = min(len(m.group(1)) + 1, 4)
            out.append(f'<h{lvl}>{inline(m.group(2))}</h{lvl}>')
            i += 1
            continue
        if s.startswith('|') and s.count('|') >= 2:
            flush()
            rows = []
            while i < n and lines[i].strip().startswith('|'):
                rows.append(_cells(lines[i], '|'))
                i += 1
            out.append(_table(rows))
            continue
        if _is_tab_row(raw) and i + 1 < n and _is_tab_row(lines[i + 1]):
            flush()
            rows = []
            while i < n and _is_tab_row(lines[i]):
                rows.append(_cells(lines[i], '\t'))
                i += 1
            out.append(_table(rows))
            continue
        if BULLET.match(raw) or NUMBERED.match(raw):
            numbered = not BULLET.match(raw)
            pat = NUMBERED if numbered else BULLET
            items, j = [], i
            while j < n and (m := pat.match(lines[j].rstrip())):
                items.append([m.group(m.lastindex)])
                j += 1
                # lazy continuation lines belong to the item
                while j < n and lines[j].strip() and not _is_block_start(lines[j].strip(), lines[j].rstrip()):
                    items[-1].append(lines[j])
                    j += 1
            first = NUMBERED.match(raw)
            if numbered and len(items) == 1 and len(items[0]) == 1 and len(s) <= 70 and not s.endswith(END_PUNCT):
                flush()      # a lone short "2. सिंधु घाटी सभ्यता" line is a section title
                out.append(f'<h3>{inline(s)}</h3>')
                i = j
                continue
            flush()
            lis = ''.join('<li>' + '<br>'.join(_label_line(x) for x in it) + '</li>' for it in items)
            out.append(f'<ol start="{int(first.group(1))}">{lis}</ol>' if numbered else f'<ul>{lis}</ul>')
            i = j
            continue
        if EMOJI_START.match(s) and len(s) <= 80 and '?' not in s and not s.endswith(END_PUNCT):
            flush()      # "📖 Content — प्रतिशत", "⚠️ सावधान: परीक्षक का जाल" are titles
            tag = 'h2' if not out else 'h3'
            out.append(f'<{tag}>{inline(s)}</{tag}>')
            i += 1
            continue
        para.append(_label_line(s))
        i += 1
    flush()
    return Markup('\n'.join(out))


# ------------------------------------------------------------------ mind map (mermaid → nested list)
MERMAID_HEAD = re.compile(r'^\s*(?:graph|flowchart)\b', re.I)
MERMAID_SKIP = re.compile(r'^(?:classDef|class|style|linkStyle|click|subgraph|end|direction|%%)\b')
EDGE = re.compile(r'\s*(?:--\s+[^|\s](?:[^|]*?\S)?\s+-->|==\s+[^|\s](?:[^|]*?\S)?\s+==>|<?-{2,}>|<?={2,}>|-\.+->|-{3,}|-\.+-|--[ox])\s*(?:\|[^|]*\|)?\s*')
NODE_ID = re.compile(r'^([\w.]+)')
QUOTED = re.compile(r'"[^"]*"')


def _clean_label(s):
    s = re.sub(r'<br\s*/?>', '\n', s, flags=re.I)
    s = s.replace('#quot;', '"').replace('#amp;', '&').replace('**', '')
    s = re.sub(r'fa:fa-[\w-]+\s*', '', s)
    s = re.sub(r'</?[a-z][^>]*>', '', s, flags=re.I)          # stray tags inside labels (<b>, <i>)
    return '\n'.join(' '.join(x.split()) for x in s.split('\n') if x.strip()).strip()


def _node(part, quotes):
    part = part.strip()
    m = NODE_ID.match(part)
    if not m:
        return None, None
    rest = re.sub(r':::[\w-]+$', '', part[m.end():].strip()).strip()
    rest = re.sub(r'\x00(\d+)\x00', lambda q: quotes[int(q.group(1))], rest)
    label = None
    if rest:
        while rest and rest[0] in '([{>/\\':
            rest = rest[1:]
        while rest and rest[-1] in ')]}/\\':
            rest = rest[:-1]
        label = _clean_label(rest.strip().strip('"'))
    return m.group(1), label or None


def _parse_mindmap(lines):
    root, stack = None, []
    for line in lines:
        if line.strip().startswith('```'):
            break
        if not line.strip() or line.strip().startswith(('::icon', '%%')):
            continue
        indent = len(line) - len(line.lstrip())
        text = line.strip()
        text = re.sub(r'^[\w.-]*\s*(?=[(\[{])', '', text) if re.match(r'^[\w.-]*\s*[(\[{]', text) else text
        while text and text[0] in '([{)':
            text = text[1:]
        while text and text[-1] in ')]}(':
            text = text[:-1]
        node = (_clean_label(text.strip('"')), [])
        if not node[0]:
            continue
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if stack:
            stack[-1][1][1].append(node)
        elif root is None:
            root = node
        else:
            root[1].append(node)
        stack.append((indent, node))
    return [root] if root and root[1] else None


def parse_mermaid(text):
    """Mermaid flowchart / mindmap → list of root nodes (label, [children]); None if unparseable."""
    lines = [l for l in text.splitlines() if len(l) <= MAX_MERMAID_LINE]
    start = next((i for i, l in enumerate(lines) if MERMAID_HEAD.match(l)), None)
    if start is None:
        mi = next((i for i, l in enumerate(lines) if l.strip() == 'mindmap'), None)
        return _parse_mindmap(lines[mi + 1:]) if mi is not None else None
    labels, order, kids, incoming = {}, [], {}, set()

    def see(nid, label):
        if nid not in labels:
            labels[nid] = label or nid
            order.append(nid)
        elif label and labels[nid] == nid:
            labels[nid] = label

    for line in lines[start + 1:]:
        s = line.strip().rstrip(';').strip()
        if s.startswith('```'):
            break
        if not s or MERMAID_SKIP.match(s):
            continue
        quotes = []
        masked = QUOTED.sub(lambda q: (quotes.append(q.group(0)), f'\x00{len(quotes) - 1}\x00')[1], s)
        groups = []
        for part in EDGE.split(masked):
            ids = []
            for sub in part.split(' & '):
                nid, label = _node(sub, quotes)
                if nid:
                    see(nid, label)
                    ids.append(nid)
            if ids:
                groups.append(ids)
        for a, b in zip(groups, groups[1:]):
            for x in a:
                for y in b:
                    if y not in kids.setdefault(x, []) and x != y:
                        kids[x].append(y)
                        incoming.add(y)
    if not kids:
        return None
    roots = [nid for nid in order if nid not in incoming and nid in kids] or [order[0]]
    seen = set()

    def build(nid):
        seen.add(nid)
        children = [build(c) if c not in seen else (labels[c], []) for c in kids.get(nid, [])]
        return labels[nid], children

    return [build(r) for r in roots if r not in seen]


def _label_html(label):
    return '<br>'.join(str(escape(x)) for x in label.split('\n'))


def render_tree(roots):
    def li(node, depth):
        label, children = node
        if not children:
            return f'<li><span class="mm-node">{_label_html(label)}</span></li>'
        inner = ''.join(li(c, depth + 1) for c in children)
        return (f'<li><details{" open" if depth < 2 else ""}><summary class="mm-node">{_label_html(label)}</summary>'
                f'<ul>{inner}</ul></details></li>')
    return Markup('<ul class="mm-tree">' + ''.join(li(r, 0) for r in roots) + '</ul>')


# ------------------------------------------------------------------ flashcards
CARD_HEAD = re.compile(r'^(?:#+\s*)?(?:\*\*)?\s*(?:फ़्लैशकार्ड|फ्लैशकार्ड|फ्लैश\s*कार्ड|कार्ड|Flash\s*card|Card)\s*'
                       r'(?:#|No\.?|नं\.?|संख्या)?\s*(\d{1,3})\s*(?:\*\*)?\s*[:：.)\-–—]?\s*(?:\*\*)?\s*(.*)$', re.I)
LEAD = r'^(?:[^\w\s*#]{1,3}\s*)?'          # optional emoji before the label (🃏 सामने:)
FRONT = re.compile(LEAD + r'(?:\*\*)?(?:सामने|Front|प्रश्न|प्र|Q|Question)\s*(?:\*\*)?\s*[:：]\s*(?:\*\*)?\s*(.*)$', re.I)
BACK = re.compile(LEAD + r'(?:\*\*)?(?:पीछे|Back|उत्तर|उ|A|Ans|Answer)\s*(?:\*\*)?\s*[:：]\s*(?:\*\*)?\s*(.*)$', re.I)


def parse_flashcards(text):
    """→ (intro_text, [(front, back)], outro_text) or None when the file is not in card format."""
    intro, cards, pending = [], [], []
    cur, mode = None, None

    def new_card():
        nonlocal cur
        if cur is not None and pending:
            cur['back'].extend(x.strip() for x in pending if x.strip())
            pending.clear()
        cur = {'front': [], 'back': []}
        cards.append(cur)

    for line in text.replace('\r\n', '\n').split('\n'):
        s = line.strip()
        if (m := CARD_HEAD.match(s)):
            new_card()
            mode = 'head'
            rest = m.group(2).strip()
            if rest and (f := FRONT.match(rest)):
                rest = f.group(1)
            if rest:
                cur['front'].append(rest)
                mode = 'front'
            continue
        if (m := FRONT.match(s)):
            if cur is None or cur['back']:
                new_card()
            cur['front'].append(m.group(1))
            mode = 'front'
            continue
        if cur is not None and cur['front'] and mode in ('front', 'head') and (m := BACK.match(s)):
            cur['back'].append(m.group(1))
            mode = 'back'
            continue
        if not s:
            if mode == 'back':
                mode = 'after'
            elif mode == 'after':
                pending.append('')
            continue
        if cur is None:
            intro.append(line)
        elif mode in ('front', 'head'):
            cur['front'].append(s)
            mode = 'front'
        elif mode == 'back':
            cur['back'].append(s)
        else:
            pending.append(line)
    if len(cards) < 2 or any(not c['front'] or not c['back'] for c in cards):
        return None
    clean = lambda xs: '\n'.join(x for x in xs if x.strip())  # noqa: E731
    return '\n'.join(intro), [(clean(c['front']), clean(c['back'])) for c in cards], '\n'.join(pending)


def render_flashcards(parsed, lang):
    intro, cards, outro = parsed
    items = []
    for i, (front, back) in enumerate(cards, 1):
        f = '<br>'.join(inline(x) for x in front.split('\n'))
        b = '<br>'.join(inline(x) for x in back.split('\n'))
        items.append(
            f'<li><button type="button" class="fc" data-flip aria-expanded="false">'
            f'<span class="fc-inner">'
            f'<span class="fc-face fc-front"><span class="fc-num">{escape(t("fc_card", lang))} {i}</span>'
            f'<span class="fc-text">{f}</span><span class="fc-hint">{escape(t("fc_tap", lang))}</span></span>'
            f'<span class="fc-face fc-back"><span class="fc-num">{escape(t("fc_answer", lang))}</span>'
            f'<span class="fc-text">{b}</span></span>'
            f'</span></button></li>')
    html = (str(render_text(intro)) if intro.strip() else '') + f'<ol class="fc-list">{"".join(items)}</ol>'
    if outro.strip():
        html += str(render_text(outro))
    return Markup(html)


# ------------------------------------------------------------------ sections
def render_section(path, key, lang):
    """HTML for one section file; cached until the file changes."""
    st = path.stat()
    ck = (path, st.st_mtime_ns, st.st_size, key, lang)
    if ck in _render_cache:
        return _render_cache[ck]
    text = _read(path)
    html = None
    if key == 'Mind_Map':
        tree = parse_mermaid(text)
        html = render_tree(tree) if tree else None
    elif key == 'Flashcards':
        parsed = parse_flashcards(text)
        html = render_flashcards(parsed, lang) if parsed else None
    if html is None:
        html = render_text(text)
    if len(_render_cache) > 400:
        _render_cache.clear()
    _render_cache[ck] = html
    return html


def pick_lang(chapter, key, want):
    """Language to show a section in: the wanted one, else a both-languages file, else the other."""
    have = chapter.sections.get(key, {})
    if want in have:
        return want
    if BOTH in have:
        return BOTH
    other = 'en' if want == 'hi' else 'hi'
    return other if other in have else None
