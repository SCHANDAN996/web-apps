"""Turn an official notice (PDF or HTML) into structured facts. Hindi + English."""
import re
from datetime import date

from bs4 import BeautifulSoup

PDF_PAGES = 6        # dates, vacancies, age are on the first pages of every notice

DATE = r'(\d{1,2})\s*[./\-]\s*(\d{1,2})\s*[./\-]\s*(\d{4}|\d{2})'
MONTHS = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}
DATE_WORDS = r'(\d{1,2})(?:st|nd|rd|th)?[\s\-]*([A-Za-z]{3,9})[,\s\-]*(\d{4})'
DATE_WORDS_US = r'\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})'


_PDF_WORKER = '''
import io, resource, sys
resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024,) * 2)   # hostile PDFs can't eat the server
from pypdf import PdfReader
try:
    reader = PdfReader(io.BytesIO(sys.stdin.buffer.read()))
    sys.stdout.write("\\n".join((p.extract_text() or "") for p in reader.pages[:int(sys.argv[1])]))
except Exception:
    pass
'''


def pdf_text(content: bytes, pages=PDF_PAGES, timeout=60):
    """Extract text in a separate, memory- and time-limited process (PDFs come from the internet)."""
    import subprocess
    import sys
    try:
        r = subprocess.run([sys.executable, '-c', _PDF_WORKER, str(pages)], input=content,
                           capture_output=True, timeout=timeout)
        return r.stdout.decode('utf-8', errors='replace')
    except (subprocess.TimeoutExpired, OSError):
        return ''


def html_text(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'noscript', 'header', 'footer', 'nav']):
        tag.decompose()
    text = re.sub(r'[ \t\xa0]+', ' ', soup.get_text('\n'))
    return '\n'.join(l.strip() for l in text.splitlines() if l.strip())


def _mk(d, m, y):
    y = int(y)
    y = y + 2000 if y < 100 else y
    try:
        return date(y, int(m), int(d))
    except ValueError:
        return None


def parse_dates(s):
    out = [_mk(*m) for m in re.findall(DATE, s)]
    for d, mon, y in re.findall(DATE_WORDS, s):
        m = MONTHS.get(mon[:3].lower())
        if m:
            out.append(_mk(d, m, y))
    for mon, d, y in re.findall(DATE_WORDS_US, s):
        m = MONTHS.get(mon[:3].lower())
        if m:
            out.append(_mk(d, m, y))
    return [d for d in out if d and 2000 < d.year < 2100]


LAST_DATE_HINT = re.compile(
    r'(last\s+date|closing\s+date|last\s+day|end\s+date|अंतिम\s+(?:तिथि|तारीख|दिनांक)|आवेदन\s+की\s+अंतिम)', re.I)
START_HINT = re.compile(r'(start(?:ing)?\s+date|opening\s+date|commencement|प्रारंभ|आरंभ|शुरू)', re.I)
RANGE = re.compile(DATE + r'\s*(?:to|till|until|से|–|-|—)\s*' + DATE, re.I)


def application_window(text):
    """(start, last) application dates from the notice text."""
    start = last = None
    lines = text.splitlines()
    for i, line in enumerate(lines):
        window = ' '.join(lines[i:i + 4])
        if re.search(r'submission of online application|online application|apply online|आवेदन', window, re.I):
            m = RANGE.search(window)
            if m and not last:
                start, last = _mk(*m.groups()[:3]), _mk(*m.groups()[3:])
        if not last and LAST_DATE_HINT.search(line) and not re.search(r'fee|शुल्क|payment|correction', line, re.I):
            ds = parse_dates(window)
            if ds:
                last = ds[0]
        if not start and START_HINT.search(line):
            ds = parse_dates(window)
            if ds:
                start = ds[0]
    if start and last and start > last:
        start = None
    return start, last


VAC_PATTERNS = [
    r'(\d{1,3}(?:,\d{3})+|\d+)\s+(?:tentative\s+)?(?:vacancies|vacancy|posts)\b',
    r'(?:vacancies|posts|पदों\s+की\s+संख्या|कुल\s+पद)\s*[:\-–]?\s*(\d{1,3}(?:,\d{3})+|\d+)',
    r'(\d+)\s+पद',
]
VAC_HINT = re.compile(r'approx|about|total|tentative|कुल|लगभग', re.I)


def vacancies(text):
    """Best guess at the total number of posts; prefers 'approx./total N vacancies'."""
    found = []
    for p in VAC_PATTERNS:
        for m in re.finditer(p, text, re.I):
            n = int(m.group(1).replace(',', ''))
            if 1 <= n <= 200000:
                hinted = bool(VAC_HINT.search(text[max(0, m.start() - 30):m.start()]))
                found.append((hinted, n, m.start()))
    if not found:
        return None
    hinted = [f for f in found if f[0]]
    best = min(hinted, key=lambda f: f[2]) if hinted else max(found, key=lambda f: f[1])
    return str(best[1])


def age_limits(text):
    m = re.search(r'age[^.\n]{0,60}?(\d{2})\s*(?:-|–|to|से)\s*(\d{2})\s*(?:years|yrs|वर्ष)', text, re.I) or \
        re.search(r'आयु[^.\n]{0,60}?(\d{2})\s*(?:-|–|से)\s*(\d{2})\s*वर्ष', text)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        if 14 <= lo < hi <= 70:
            return lo, hi
    m = re.search(r'(?:not\s+exceeding|maximum\s+age|upper\s+age\s+limit)[^.\n]{0,30}?(\d{2})\s*(?:\([^)]*\)\s*)?years', text, re.I)
    if m and 18 <= int(m.group(1)) <= 70:
        return None, int(m.group(1))
    return None, None


QUAL_SECTION = re.compile(r'(essential|educational|minimum)\s+qualification|शैक्षिक\s+योग्यता|शैक्षणिक\s+अर्हता', re.I)


def _qual_in(t):
    t = t.lower()
    if re.search(r"\b(bachelor'?s?\s+degree|graduat(?:e|ion)|degree\s+(?:from|in)|b\.\s?tech|btech|b\.\s?e\.|mbbs|स्नातक)", t):
        return 'graduate'
    if re.search(r'\b(12th\s+(?:class|pass|standard)|10\+2|intermediate|higher\s+secondary|इंटरमीडिएट|12वीं)', t):
        return '12th'
    if re.search(r'\b(matriculation|10th\s+(?:class|pass|standard)|high\s+school|हाईस्कूल|10वीं)', t):
        return '10th'
    return None


def qualification(text):
    """Minimum qualification, read from the 'Educational Qualification' section when present.

    Notices mention matriculation for date-of-birth proof and degrees in other
    contexts, so a whole-document guess is only the fallback.
    """
    m = QUAL_SECTION.search(text or '')
    if m:
        found = _qual_in(text[m.start(): m.start() + 900])
        if found:
            return found
    return _qual_in(text or '')


def advt_no(text):
    for m in re.finditer(r'(?:advt\.?|advertisement|notice|विज्ञापन)\s*(?:no\.?|number|संख्या|सं\.?)\s*(?:date)?\s*[:\-–]?\s*'
                         r'([A-Z0-9][A-Z0-9/\-.():]{2,40})', text, re.I):
        code = m.group(1).rstrip('.,:)')
        if re.search(r'\d', code):
            return code
    return None


def extract_facts(text):
    text = (text or '').replace(' | ', '\n')      # "Header: value | Header: value" rows
    start, last = application_window(text)
    age_lo, age_hi = age_limits(text)
    return {'start_date': start, 'last_date': last, 'vacancies': vacancies(text),
            'age_min': age_lo, 'age_max': age_hi, 'min_qualification': qualification(text),
            'advt_no': advt_no(text)}


# ------------------------------------------------------------------ classify
TYPE_RULES = [
    ('answer', r'answer\s*key|उत्तर\s*कुंजी|response\s+sheet'),
    ('results', r'\bresult|marks|merit\s+list|list\s+of\s+(?:candidates|selected)|provisionally\s+(?:selected|shortlisted)|selection\s+list|shortlist|qualified|परिणाम|cut.?off'),
    ('admit', r'admit\s*card|admission\s+certificate|hall\s*ticket|call\s*letter|प्रवेश\s*पत्र|city\s+of\s+exam'),
    ('notice', r'(?:tentative|final)\s+vacanc|date\s+of\s+(?:conducting|interview)|schedule\s+of\s+interview|tentative\s+date|recommended\s+candidates|allocation|document\s+verification|physical\s+(?:standard|efficiency)|cancel|corrigendum|addendum|schedule|postpone|extension|important\s+notice|calendar|option|preference|vacanc(y|ies)\s+(?:of|as\s+on)|tender|scholarship|शुद्धिपत्र|स्थगित'),
    ('latest', r'recruit|notice\s+of|notification|advertisement|advt|apply|vacanc|engagement|walk.?in|भर्ती|विज्ञापन|आवेदन|post\s+of|posts\b'),
]


def classify(title):
    t = title or ''
    for kind, pat in TYPE_RULES:
        if re.search(pat, t, re.I):
            return kind
    return None


CATEGORY_RULES = [
    ('ssc', r'\bssc\b|staff selection'),
    ('railway', r'\brrb\b|\brrc\b|railway|रेलवे|metro'),
    ('banking', r'\bibps\b|\bsbi\b|\brbi\b|bank|nabard|बैंक'),
    ('defence', r'army|navy|air\s*force|agniveer|\bcrpf|\bbsf|\bcisf|\bitbp|\bssb\b|coast guard|police|सेना|पुलिस'),
    ('psc', r'public service commission|\b[a-z]{1,3}psc\b|लोक सेवा आयोग'),
    ('teaching', r'teacher|\btet\b|lecturer|professor|शिक्षक|kvs|nvs'),
    ('psu', r'\bntpc\b|\bongc\b|\bbhel\b|\bgail\b|\biocl?\b|\bbel\b|\bhal\b|\bisro\b|\bdrdo\b|\blic\b|limited|ltd'),
]


def categorize(text):
    for cat, pat in CATEGORY_RULES:
        if re.search(pat, text or '', re.I):
            return cat
    return 'govt'


# ------------------------------------------------------------------ dedupe
STOP = {'the', 'of', 'for', 'and', 'in', 'to', 'a', 'notice', 'notification', 'recruitment', 'online', 'apply',
        'form', 'post', 'posts', 'advt', 'advertisement', 'no', 'examination', 'exam', 'out', 'download', 'link', 'date'}


def tokens(title):
    words = re.findall(r'[a-z0-9]+', (title or '').lower())
    return {w for w in words if w not in STOP and len(w) > 1}


def similar(a, b, threshold=0.6):
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return False
    years_a, years_b = {w for w in ta if re.fullmatch(r'20\d\d', w)}, {w for w in tb if re.fullmatch(r'20\d\d', w)}
    if years_a and years_b and not years_a & years_b:
        return False          # "CGL 2025" and "CGL 2026" are different recruitments
    return len(ta & tb) / len(ta | tb) >= threshold


def dedupe_key(org, title, advt):
    if advt:
        return f'{(org or "").lower()}|advt|{re.sub(r"[^a-z0-9]", "", advt.lower())}'[:200]
    return f'{(org or "").lower()}|' + ' '.join(sorted(tokens(title)))[:180]


ACADEMIC = re.compile(r'university|semester|\bsem\b|\b(?:ug|pg)\b|\b(?:b|m)\.?\s?(?:a|sc|com|ed)\b|\bbsc\b|\bmsc\b|'
                      r'admission|ph\.?d|entrance\s+test\s+for\s+admission|counselling|scholarship', re.I)


def is_academic(title):
    """University exam results/admissions — not government jobs."""
    return bool(ACADEMIC.search(title or ''))


# Aggregator round-ups ("Latest Govt Jobs 2026 (25000+ Vacancies)") and how-to posts are not recruitments.
ROUNDUP = re.compile(r'\b(latest|all\s+india|top)\b.*\bjobs\b|\bgovt\.?\s+jobs\s+(?:for|20\d\d)|\d{3,}\+|'
                     r'notifications?\s+list|employment\s+news|rozgar\s+samachar|how\s+to\s+apply|jobs\s+20\d\d\s*\(|syllabus|exam\s+pattern|previous\s+(?:year\s+)?papers', re.I)


def is_roundup(title):
    return bool(ROUNDUP.search(title or ''))
