"""Deterministic, Hindi-first metadata from the rendered question and book chapter.

No model/network/cost dependency. The shared template is a generator, not an
identical keyword block pasted into every video. Public metadata never identifies
the correct option or copies the solution. Unknown topics get subject-only SEO.
"""
import json
from pathlib import Path
import re
import unicodedata

from . import pick

SUBJECTS = {
    'GK': ('सामान्य ज्ञान', 'GK', '#GK', ['GK in Hindi', 'General Knowledge', 'GK Quiz']),
    'Maths': ('गणित', 'Maths', '#Maths', ['Maths in Hindi', 'Quantitative Aptitude', 'Maths Quiz']),
    'Reasoning': ('रीज़निंग', 'Reasoning', '#Reasoning', ['Reasoning in Hindi', 'Logical Reasoning', 'Reasoning Quiz']),
    'English': ('अंग्रेज़ी', 'English', '#EnglishGrammar', ['English Grammar', 'English Quiz', 'अंग्रेज़ी अभ्यास']),
}
# Audience/context labels only, not a claim that a question appeared in an exam.
# Level alone cannot justify every exam: banking tags are limited to quant/reasoning.
EXAMS = {
    ('10th_Level', 'GK'): ['SSC GD', 'SSC MTS'],
    ('10th_Level', 'Maths'): ['SSC GD', 'Railway Group D'],
    ('10th_Level', 'Reasoning'): ['SSC GD', 'Railway Group D'],
    ('10th_Level', 'English'): ['SSC MTS'],
    ('12th_Level', 'GK'): ['SSC CHSL', 'Railway NTPC'],
    ('12th_Level', 'Maths'): ['SSC CHSL', 'Railway NTPC'],
    ('12th_Level', 'Reasoning'): ['SSC CHSL', 'Railway NTPC'],
    ('12th_Level', 'English'): ['SSC CHSL'],
    ('Graduation_Level', 'GK'): ['SSC CGL'],
    ('Graduation_Level', 'Maths'): ['SSC CGL', 'Bank PO'],
    ('Graduation_Level', 'Reasoning'): ['SSC CGL', 'Bank PO'],
    ('Graduation_Level', 'English'): ['SSC CGL'],
}
DEFAULT = ('अभ्यास', 'Quiz', '#Quiz', ['Hindi Quiz'])


def clean(value):
    """Plain API text: normalize spacing, remove controls and forbidden brackets."""
    if not isinstance(value, str):
        return ''
    value = ''.join(c for c in value if not unicodedata.category(c).startswith('C') or c in '\n\t')
    return ' '.join(value.replace('<', '＜').replace('>', '＞').split()).strip()


def whole_prefix(value, limit):
    """Fit whole whitespace-delimited tokens; never slice a Hindi grapheme/word."""
    value = clean(value)
    if len(value) <= limit:
        return value
    words, size = [], 0
    for word in value.split():
        if size + bool(words) + len(word) + 1 > limit:
            break
        words.append(word)
        size += bool(len(words) > 1) + len(word)
    return ' '.join(words).rstrip(' ,;:|') + '…' if words else ''


def chapter_topics(q):
    """Read bilingual chapter titles, falling back to its honest human-readable name."""
    subject_key = q.get('subject')
    subject = SUBJECTS.get(subject_key, DEFAULT) if isinstance(subject_key, str) else DEFAULT
    chapter = q.get('chapter')
    if not isinstance(chapter, str) or not chapter:
        return subject[0], subject[1]
    root = Path(pick.books_root()).resolve()
    path = (root / chapter).resolve()
    if path == root or root not in path.parents:
        return subject[0], subject[1]
    try:
        value = json.loads((path / 'chapter.json').read_text(encoding='utf-8'))
        hi, en = clean(value.get('title_hi')), clean(value.get('title_en'))
    except (OSError, ValueError, AttributeError):
        hi = en = ''
    folder = clean(re.sub(r'^Chapter_\d+_', '', path.name).replace('_', ' '))
    # Bare placeholders carry no meaningful topic, so use the actual subject.
    if not folder or folder.casefold() in ('x', 'b', 'unknown'):
        folder = ''
    return hi or folder or subject[0], en or folder or subject[1]


def exam_names(q):
    level, subject = q.get('level'), q.get('subject')
    if not isinstance(level, str) or not isinstance(subject, str):
        return []
    return list(EXAMS.get((level, subject), ()))


def bounded_tags(values):
    seen, result, size = set(), [], 0
    for value in values:
        tag = whole_prefix(re.sub(r'[,"#]', ' ', clean(value)), 60).rstrip('…')
        if not tag or tag.casefold() in seen or size + len(tag) + 3 > 450:
            continue
        seen.add(tag.casefold())
        result.append(tag)
        size += len(tag) + 3
    return result


def _valid_question(q):
    options, answer = q.get('options'), q.get('answer')
    return (bool(clean(q.get('question'))) and isinstance(options, (list, tuple)) and
            2 <= len(options) <= 4 and all(isinstance(o, str) and clean(o) for o in options) and
            isinstance(answer, int) and not isinstance(answer, bool) and 0 <= answer < len(options))


def build(q, link=''):
    """Return one validated payload usable by uploader, artifacts and local preview.

    Invalid topic metadata falls back to the subject. Malformed option/answer
    structure suppresses options/exam targeting but retains the real question.
    Oversize question text is omitted from description rather than cut into a
    misleading question; the video renderer has its own stricter text limits.
    """
    if not isinstance(q, dict):
        q = {}
    subject_key = q.get('subject')
    subject = SUBJECTS.get(subject_key, DEFAULT) if isinstance(subject_key, str) else DEFAULT
    fallback = not _valid_question(q)
    try:
        hi, en = chapter_topics(q)
    except (OSError, ValueError, TypeError):
        hi, en = subject[:2]
        fallback = True
    hi = whole_prefix(hi, 100) or subject[0]
    en = whole_prefix(en, 100) or subject[1]
    question = clean(q.get('question'))
    exams = [] if fallback else exam_names(q)
    # Reserve the readable bilingual search label and #Shorts before fitting topic/hook.
    suffix = f' | {subject[1]} Quiz Hindi #Shorts' if subject is not DEFAULT else ' | Hindi Quiz #Shorts'
    room = 90 - len(suffix)
    head = whole_prefix(hi, min(30, room)) or subject[0]
    hook = whole_prefix(question, room - len(head) - 3)
    if hook:
        head += ' — ' + hook
    title = head + suffix
    # Entire trusted question/options are retained when they fit the API byte budget.
    intro = [f'{hi} — एक सवाल की practice | {en}.',
             f'{subject[0]} क्विज़ हिंदी में: उत्तर चुनें और हल वीडियो में समझें।']
    if exams:
        intro.append(f"अभ्यास संदर्भ / Practice for: {', '.join(exams)}.")
    body = []
    if question and len(question.encode('utf-8')) <= 2000:
        body = [question]
        if not fallback:
            options = [f"{'ABCD'[i]}. {clean(o)}" for i, o in enumerate(q['options'])]
            if len('\n'.join(options).encode('utf-8')) <= 1500:
                body += options
            else:
                fallback = True
    elif question:
        fallback = True
    footer = ['उत्तर और हल वीडियो में देखें; पहले अपना विकल्प चुनें।',
              'StudyStation: GK, Maths, Reasoning और English के छोटे अभ्यास वीडियो।',
              'Short question practice in Hindi with English topic labels.']
    safe_link = clean(link)
    if safe_link and re.fullmatch(r'(?:https://)?t\.me/[A-Za-z0-9_]+', safe_link):
        footer.append(f'मुफ़्त अभ्यास / Free practice: {safe_link}')
    hashtags = ['#Shorts', subject[2], '#StudyStation']
    description = '\n'.join(intro) + '\n\n' + '\n'.join(body) + '\n\n' + '\n'.join(footer) + '\n\n' + ' '.join(hashtags)
    # The bounded chapter/question/option budgets guarantee <= 5000 UTF-8 bytes.
    if len(description.encode('utf-8')) > 5000:
        description = '\n'.join(intro) + '\n\n' + '\n'.join(footer) + '\n\n' + ' '.join(hashtags)
        fallback = True
    tags = bounded_tags(['StudyStation', *subject[3], hi, en, *exams, 'quiz in Hindi'])
    return {'version': 1, 'generator': 'topic-template-v1', 'title': title,
            'description': description, 'tags': tags, 'topic_hi': hi, 'topic_en': en,
            'exams': exams, 'fallback': fallback}
