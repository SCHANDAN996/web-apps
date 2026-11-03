"""Current-affairs book chapters from All India Radio News — the tools used to write the four
`Chapter_*_Current_Affairs_*` chapters (see README.md in this folder for the step-by-step refresh).

Run from study_station/v2:

    python tools/current_affairs/cabook.py crawl --from 2026-10-01           # AIR feeds → cache/air_<cat>.jsonl
    python tools/current_affairs/cabook.py find "appointed|sworn in" --from 2026-10-01
    python tools/current_affairs/cabook.py read <link-or-slug> [...]
    python tools/current_affairs/cabook.py verify --model z-ai/glm-5.3      # check facts.tsv against the articles
    python tools/current_affairs/cabook.py sets  <10|12|G6|G12> <out_dir>   # 6 English practice sets
    python tools/current_affairs/cabook.py prose <10|12|G6|G12> <chapter>   # English sections + Mind_Map
    python tools/current_affairs/cabook.py review <chapter> [...]           # report-only review

facts.tsv is the hand-written fact bank: one MCQ per row, each tied to the AIR report it came from
(date, link, title). Every fact must be checked against its article (`verify`) before it is used.
"""
import argparse
import csv
import glob
import html
import json
import os
import random
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = Path(os.environ.get('CA_CACHE', HERE / 'cache'))         # crawled feeds (git-ignored)
FACTS = HERE / 'facts.tsv'
UA = 'StudyStationBot/1.0 (+https://github.com/SCHANDAN996/web-apps; exam current-affairs notes)'
CATEGORIES = ['national', 'international', 'business', 'sports', 'miscellaneous']
MON = 'January February March April May June July August September October November December'.split()
LEVEL_ORDER = {'E': 0, 'M': 1, 'H': 2}
TAG = re.compile(r'<[^>]+>')


# ---------------------------------------------------------------------------------------------- data
def load_items():
    items = []
    for f in sorted(glob.glob(str(CACHE / 'air_*.jsonl'))):
        items += [json.loads(line) for line in open(f, encoding='utf-8')]
    return items


def load_facts():
    with open(FACTS, encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh, delimiter='\t'))
    for r in rows:
        r['wrong'] = [w.strip() for w in r['wrong_options'].split(';')]
    return rows


def article_text(link, items_by_link):
    it = items_by_link.get(link)
    if it:
        return it['title'], it['text']
    req = urllib.request.Request(link, headers={'User-Agent': UA})       # not cached: fetch the page once
    page = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
    body = re.sub(r'\s+', ' ', html.unescape(TAG.sub(' ', page)))
    return link, body[:6000]


# --------------------------------------------------------------------------------------------- crawl
def crawl(cat, cutoff, delay=2.0):
    """Walk an AIR category feed page by page back to `cutoff` (polite: 1 request / `delay` s)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f'air_{cat}.jsonl'
    seen = {json.loads(line)['link'] for line in open(out, encoding='utf-8')} if out.exists() else set()
    page, misses = 1, 0
    with open(out, 'a', encoding='utf-8') as f:
        while True:
            url = f'https://newsonair.gov.in/category/{cat}/feed/' + (f'?paged={page}' if page > 1 else '')
            try:
                data = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60).read()
                root = ET.fromstring(data)
            except Exception as e:  # noqa: BLE001 — network blip: retry, then skip the page
                misses += 1
                print(f'{cat} page {page}: {e}', flush=True)
                if misses > 5:
                    page, misses = page + 1, 0
                time.sleep(delay * 3)
                continue
            misses = 0
            items = root.findall('./channel/item')
            if not items:
                break
            oldest = None
            for it in items:
                link = (it.findtext('link') or '').strip()
                when = parsedate_to_datetime(it.findtext('pubDate'))
                oldest = when if oldest is None or when < oldest else oldest
                if link in seen or when < cutoff:
                    continue
                seen.add(link)
                body = it.findtext('{http://purl.org/rss/1.0/modules/content/}encoded') or it.findtext('description') or ''
                text = re.sub(r'\s+', ' ', html.unescape(TAG.sub(' ', body))).strip()
                f.write(json.dumps({'cat': cat, 'date': when.date().isoformat(),
                                    'title': html.unescape(it.findtext('title') or '').strip(),
                                    'link': link, 'text': text[:4000]}, ensure_ascii=False) + '\n')
            f.flush()
            if oldest and oldest < cutoff:
                break
            page += 1
            time.sleep(delay)
    print(f'{cat}: done at page {page}')


# ------------------------------------------------------------------------------------------- verify
VERIFY_SYSTEM = """You check exam MCQs against a news article. Use ONLY the article text given — the events are recent
and you must not rely on memory. For the MCQ decide:
- OK: the article clearly supports the keyed answer, and no other option is also correct.
- PROBLEM: the article does not support the key, contradicts it, or another option could also be correct.
Reply with exactly one line: "OK" or "PROBLEM: <short reason>"."""


def verify(model, since=None):
    sys.path.insert(0, '.')
    from app import nvidia
    by_link = {it['link']: it for it in load_items()}
    facts = [f for f in load_facts() if not since or f['date'] >= since]

    def check(f):
        title, text = article_text(f['air_link'], by_link)
        user = (f"ARTICLE ({f['date']}): {title}\n{text[:3500]}\n\nMCQ: {f['question']}\nOptions: "
                + ' | '.join([f['answer']] + f['wrong']) + f"\nKeyed answer: {f['answer']}")
        try:
            ans = nvidia.call(VERIFY_SYSTEM, user, max_tokens=8000, temperature=0, model=model).strip()
        except Exception as e:  # noqa: BLE001
            ans = f'ERROR {e}'
        return f, (ans.splitlines()[-1] if ans else 'EMPTY')

    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(check, facts))
    bad = [(f, v) for f, v in res if not v.upper().startswith('OK')]
    print(f'{model}: {len(res)} checked, {len(bad)} flagged')
    for f, v in bad:
        print(f"{f['date']} | {f['question'][:90]} | {v[:200]}")


# --------------------------------------------------------------------------------------------- sets
HEADERS = ['Questions 1–20: Easy | Questions 21–25: Medium', 'Questions 26–50: Medium', 'Questions 51–75: Medium',
           'Questions 76–100: Medium', 'Questions 101–120: Medium | Questions 121–125: Hard', 'Questions 126–150: Hard']


def window(kind, facts):
    """The facts a chapter covers: the last 6 months (6M chapters) or 12 months (G12) before the newest fact."""
    newest = max(date.fromisoformat(f['date']) for f in facts)
    months = 12 if kind == 'G12' else 6
    m = newest.month - months
    start = date(newest.year + (m - 1) // 12, (m - 1) % 12 + 1, 1)
    return [f for f in facts if date.fromisoformat(f['date']) >= start], start


def make_sets(kind, out):
    sys.path.insert(0, str(HERE.parents[1]))
    from app.bookgen import balance_answers
    facts, start = window(kind, load_facts())
    rng = random.Random({'10': 10, '12': 12, 'G6': 66, 'G12': 1212}[kind])
    half = date(start.year + (start.month + 5) // 12, (start.month + 5) % 12 + 1, 1).isoformat()
    recent = [f for f in facts if f['date'] >= half] if kind == 'G12' else facts
    older = [f for f in facts if f['date'] < half] if kind == 'G12' else []
    rank = {'10': lambda f: (LEVEL_ORDER[f['level']], rng.random()),
            '12': lambda f: ({'E': 1, 'M': 0, 'H': 1}[f['level']], rng.random()),
            'G6': lambda f: (-LEVEL_ORDER[f['level']], rng.random()),
            'G12': lambda f: (-LEVEL_ORDER[f['level']], rng.random())}[kind]
    pool = older + sorted(recent, key=rank)[:150 - len(older)]
    if len(pool) < 150:
        sys.exit(f'only {len(pool)} facts in the window — add more to facts.tsv (need 150)')
    pool = pool[:150]
    pool.sort(key=lambda f: (LEVEL_ORDER[f['level']], f['date'], rng.random()))
    Path(out).mkdir(parents=True, exist_ok=True)
    for s in range(6):
        blocks = [HEADERS[s]]
        for k, f in enumerate(pool[s * 25:(s + 1) * 25]):
            opts = [f['answer']] + f['wrong'][:3]
            rng.shuffle(opts)
            d = date.fromisoformat(f['date'])
            blocks.append(f"{s * 25 + k + 1}. {f['question']}\n" + ' '.join(f'({l}) {o}' for l, o in zip('abcd', opts))
                          + f"\nAnswer: ({'abcd'[opts.index(f['answer'])]})\nSolution: {f['explanation']} So the answer is "
                          f"{f['answer']}.\nSource: All India Radio News, {d.day} {MON[d.month - 1][:3]} {d.year} ({f['air_link']})")
        Path(out, f'Practice_en_Set_0{s + 1}.txt').write_text(balance_answers('\n\n'.join(blocks) + '\n'),
                                                            encoding='utf-8')
    print(kind, 'levels:', {l: sum(f['level'] == l for f in pool) for l in 'EMH'})


# -------------------------------------------------------------------------------------------- prose
THEMES = OrderedDict([
    ('Awards & Honours', r'Nobel|Padma|award|prize|honou?r|Phalke|Booker|Agricola|Order of|Golden Conch|Golden Peacock|BAFTA|Academy Awards|Best (Picture|Actor|Actress|Feature)'),
    ('Appointments & Elections', r'appointed|took charge|takes charge|assumed (office|charge)|Chief Minister|President of|Prime Minister|Governor|sworn|oath|Chief of|elected|Chairperson|Chief Justice|High Commissioner|Interim President|Vice-President of the Financial|presidential|Education Minister'),
    ('Sports', r'medal|Games|Cup|title|chess|cricket|hockey|tennis|badminton|shoot|wrestl|athlet|\bIPL\b|FIFA|squash|Olympic|kabaddi|golf|boxing|javelin|Wimbledon|(?:US|Australian|French|Italian|Masters) Open|WTT|Grandmaster|UCI|Championships'),
    ('Defence & Security', r'missile|\bINS\b|Navy|Naval|exercise|DRDO|Army|warship|frigate|ICGS|Agni|Pinaka|Kusha|Air Force|Dronathon|peacekeeping'),
    ('Space, Science & Technology', r'ISRO|satellite|Gaganyaan|NASA|telescope|Olympiad|astronaut|Skyroot|OptoSAR|launch vehicle|LVM3|GSLV|helicopter|AI Impact'),
    ('Economy, Banking & Reports', r'GDP|RBI|repo|inflation|forex|IPO|Budget|Economic Survey|Financial Inclusion|surplus|steel|WPI|CPI|Index of Services|SEBI|OECD|QS World|NFHS|Survey|Finance Commission|Jan Dhan'),
    ('Environment, Heritage & Culture', r'Ramsar|cheetah|UNESCO|heritage|wetland|grassland|Kuno|Deepavali|Creative City|Champions of the Earth|Vande Mataram|Sangeet Natak'),
    ('Government Schemes & Governance', r'Yojana|Mission|launched|portal|\bapp\b|Census|campaign|Abhiyan|Act\b|Parliament|Kapas|scheme|chatbot|Cell Broadcast|rename|Keralam|PMGSY|Labour Codes|Cabinet|Victims Rights'),
    ('International Relations & Summits', r'summit|G7|BRICS|SCO|ASEAN|NPT|\bUN\b|treaty|FATF|G20|ICAO|Executive Board'),
])
THEME_HI = {'Awards & Honours': 'पुरस्कार और सम्मान', 'Appointments & Elections': 'नियुक्तियाँ और चुनाव', 'Sports': 'खेल',
            'Defence & Security': 'रक्षा और सुरक्षा', 'Space, Science & Technology': 'अंतरिक्ष, विज्ञान और तकनीक',
            'Economy, Banking & Reports': 'अर्थव्यवस्था, बैंकिंग और रिपोर्ट',
            'Environment, Heritage & Culture': 'पर्यावरण, विरासत और संस्कृति',
            'Government Schemes & Governance': 'सरकारी योजनाएँ और शासन',
            'International Relations & Summits': 'अंतरराष्ट्रीय संबंध और शिखर सम्मेलन', 'Other': 'अन्य'}
TITLE_FIX = {'Noble Peace': 'Nobel Peace', 'digitallly': 'digitally', 'improvised Financial': 'improved Financial',
             'improvenment': 'improvement', 'Brahmos': 'BrahMos', '  ': ' '}


def theme_of(f):
    text = f['question'] + ' ' + f['explanation']
    return next((t for t, rx in THEMES.items() if re.search(rx, text, re.I)), 'Other')


def when(f):
    d = date.fromisoformat(f['date'])
    return f'{d.day} {MON[d.month - 1][:3]} {d.year}'


def grouped(facts):
    by_article = OrderedDict()
    for f in sorted(facts, key=lambda f: (f['date'], f['air_link'])):
        by_article.setdefault(f['air_link'], []).append(f)
    groups = OrderedDict((t, []) for t in list(THEMES) + ['Other'])
    for link, fs in by_article.items():
        exps = []
        for f in fs:                                    # drop near-duplicate sentences from the same report
            words = set(re.findall(r'\w+', f['explanation'].lower()))
            if all(len(words & set(re.findall(r'\w+', e.lower()))) < 0.5 * len(words) for e in exps):
                exps.append(f['explanation'])
        title = fs[0]['air_title']
        for a, b in TITLE_FIX.items():
            title = title.replace(a, b)
        groups[theme_of(fs[0])].append(dict(fs[0], title=title.rstrip('.'), exps=exps))
    return OrderedDict((k, v) for k, v in groups.items() if v)


def write_prose(kind, ch):
    """English sections + bilingual Mind_Map. The fixed teaching text (hook, mnemonics, traps, static links) is
    in this function — update the mnemonics and traps when the period changes (see README)."""
    ch = Path(ch)
    facts, start = window(kind, load_facts())
    newest = max(date.fromisoformat(f['date']) for f in facts)
    period = f'{MON[start.month - 1]} {start.year} – {MON[newest.month - 1]} {newest.year}'
    groups = grouped(facts)
    exams = ('school quizzes, Navodaya/Sainik-style tests, state Class 10 GK papers and the first rung of SSC/Railway '
             'exams' if kind == '10' else 'SSC CHSL/MTS, Railway NTPC/Group D, State Police and Agniveer exams'
             if kind == '12' else 'SSC CGL/CHSL, Banking (IBPS/SBI PO & Clerk), RRB NTPC, CDS/NDA, CAPF and State PCS exams')
    bullets = lambda fs: '\n'.join(f'- **{when(f)} — {f["title"]}.** ' + ' '.join(f['exps'][:2]) for f in fs)
    content = [f'# Current Affairs ({period})', '', '## The Hook',
               'Every competitive exam has a few "free" marks hiding in plain sight: questions on what happened in the '
               'last few months. This chapter turns the news of this period into a short, organised revision kit — '
               'one line per event, with its month, place, number and "first".', '',
               '## Learning Objectives', '', 'By the end of this chapter you will be able to:',
               f'1. Recall the most exam-worthy events of {period} under nine themes.',
               '2. Link each event to its month, place, number and "first".',
               "3. Spot the examiner's favourite traps in current-affairs options.",
               '4. Revise the whole period in 15 minutes using the summary table.', '',
               '> Every fact in this chapter comes from All India Radio News (newsonair.gov.in), the public '
               'broadcaster. Dates are the dates of the AIR report.', '']
    recall = ['Close the book: name three facts from this section with their month.',
              'Which fact in this section has a number (rank, count, percentage)? Say it aloud.',
              'Pick one name from this section and recall the event linked to it.']
    for n, (t, fs) in enumerate(groups.items()):
        content += [f'## {n + 1}. {t}', '', bullets(fs), '']
        if n % 2 == 1:
            content += [f'🧠 **Active Recall:** {recall[(n // 2) % 3]}', '']
    content += ['## Summary Table', '', '| Theme | Facts in this chapter | One to remember |', '|---|---|---|']
    content += [f'| {t} | {len(fs)} | {fs[-1]["title"][:90]} |' for t, fs in groups.items()]
    content += ['', '📅 **Revision Planner:** review this chapter after 2 days, blurt the summary table every week, '
                'and do one practice set every month until the exam.', '',
                "## ⚠️ Caution: Examiner's Trap", '',
                '1. **Similar names / years (समान नाम/वर्ष):** events with the same name in different years or places.',
                '2. **Nearly-correct statement (लगभग सही कथन):** a count that was true a few months ago (e.g. Ramsar sites) '
                '— always check *as of when* the question is set.',
                '3. **Chronological confusion (कालानुक्रमिक भ्रम):** policy-rate decisions and appointments in the wrong order.', '']
    (ch / 'Content_en.txt').write_text('\n'.join(content) + '\n', encoding='utf-8')
    kf = [f'# Key Facts — Current Affairs ({period})', '', '| Theme | Fact | Date (AIR report) |', '|---|---|---|']
    kf += [f'| {t} | {f["title"]} — {f["exps"][0]} | {when(f)} |' for t, fs in groups.items() for f in fs]
    (ch / 'Key_Facts_en.txt').write_text('\n'.join(kf) + '\n', encoding='utf-8')
    rng = random.Random(7)
    pick = sorted(facts, key=lambda f: (LEVEL_ORDER[f['level']] * (1 if kind == '10' else -1), rng.random()))[:20]
    fc = [f'# Flashcards — Current Affairs ({period})', '']
    for k, f in enumerate(pick, 1):
        fc += [f'Card {k}', f'Front: {f["question"]}', f'Back: {f["answer"]} — {f["explanation"]}', '']
    (ch / 'Flashcards_en.txt').write_text('\n'.join(fc), encoding='utf-8')
    hy = sorted(facts, key=lambda f: (LEVEL_ORDER[f['level']] if kind == '10' else -LEVEL_ORDER[f['level']], f['date']))[:10]
    pq = [f'# PYQ Analysis — Current Affairs ({period})', '',
          f'*(How {exams} ask current affairs. We describe the pattern of questions; we do not quote invented counts.)*', '',
          '## 1. How exams ask current affairs', '', '- **One-liners:** "Who won…", "Where was … held", "Who has been appointed…".',
          '- **Number questions:** medal tallies, ranks, percentages, counts.', '- **Firsts and records:** "first Indian to…".',
          '- **Pair-matching:** event ↔ host city, award ↔ winner, exercise ↔ partner country.', '',
          '## 2. Ten high-yield questions (PYQ-style, with answers)', '']
    for k, f in enumerate(hy, 1):
        pq += [f'**Q{k}.** {f["question"]}', f'**Answer:** {f["answer"]}', f'**Why:** {f["explanation"]}', '**Source:** PYQ-style', '']
    pq += ['## 3. 15-second / 45-second rule', '', '- Name/place questions: 15 seconds — you know it or you skip it.',
           '- Number questions: up to 45 seconds — eliminate outdated figures first.']
    (ch / 'PYQ_en.txt').write_text('\n'.join(pq) + '\n', encoding='utf-8')
    mm = ['```mermaid', 'graph TD', f'    A["करंट अफेयर्स<br>Current Affairs<br>{period}"]']
    for k, (t, fs) in enumerate(groups.items()):
        mm.append(f'    A --> T{k}["{THEME_HI.get(t, t)}<br>{t.replace("&", "and")}"]')
        for j, f in enumerate(sorted(fs, key=lambda f: LEVEL_ORDER[f['level']])[:4]):
            d = date.fromisoformat(f['date'])
            t2 = f['title'] if len(f['title']) <= 75 else f['title'][:72].rsplit(' ', 1)[0] + '…'
            mm.append(f'    T{k} --> T{k}_{j}["' + re.sub(r'["<>]', "'", f'{t2} ({MON[d.month - 1][:3]} {d.year})') + '"]')
    mm.append('```')
    (ch / 'Mind_Map.txt').write_text('\n'.join(mm) + '\n', encoding='utf-8')
    print(kind, period, {t: len(v) for t, v in groups.items()})
    print('Feynman_en and Memory_Hooks_en are short hand-written sections: update them by hand for the new period.')


# ------------------------------------------------------------------------------------------- review
REVIEW_NOTE = ('NOTE FOR THE REVIEWER: this is a current-affairs chapter about events newer than your training data. '
               'Every fact comes from All India Radio News reports of that period. Do NOT flag a fact only because it '
               'differs from what you remember; flag only internal contradictions, wrong arithmetic, wrong static '
               '(historical) facts, broken Hindi/English, mistranslations between the two languages, or chat debris.\n\n')


def review(chapters):
    sys.path.insert(0, '.')
    from app import bookgen
    from app.db import SessionLocal, engine, ensure_schema
    ensure_schema(engine)
    jobs = [p for c in chapters for p in sorted(Path(c).glob('*.txt')) if not p.name.startswith('Practice')]

    def go(p):
        with SessionLocal() as db:
            try:
                ans = bookgen._ask_review(db, REVIEW_NOTE + bookgen.review_request(p.name, p.read_text(encoding='utf-8')))
                return p, bookgen._review_issues(ans)
            except Exception as e:  # noqa: BLE001
                return p, [f'ERROR {e}']

    with ThreadPoolExecutor(4) as ex:
        for p, issues in ex.map(go, jobs):
            print(f'== {p.parent.name}/{p.name}: {"OK" if not issues else ""}')
            for i in issues:
                print('   -', i[:400])


# ---------------------------------------------------------------------------------------------- cli
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('crawl')
    c.add_argument('--from', dest='since', required=True)
    c.add_argument('--categories', default=','.join(CATEGORIES))
    f = sub.add_parser('find')
    f.add_argument('regex')
    f.add_argument('--from', dest='since', default='2000-01-01')
    f.add_argument('--to', default='2999-12-31')
    r = sub.add_parser('read')
    r.add_argument('links', nargs='+')
    r.add_argument('--n', type=int, default=700)
    v = sub.add_parser('verify')
    v.add_argument('--model', required=True)
    v.add_argument('--from', dest='since')
    s = sub.add_parser('sets')
    s.add_argument('kind', choices=['10', '12', 'G6', 'G12'])
    s.add_argument('out')
    p = sub.add_parser('prose')
    p.add_argument('kind', choices=['10', '12', 'G6', 'G12'])
    p.add_argument('chapter')
    rv = sub.add_parser('review')
    rv.add_argument('chapters', nargs='+')
    a = ap.parse_args(argv)
    if a.cmd == 'crawl':
        cutoff = datetime.fromisoformat(a.since).replace(tzinfo=timezone.utc)
        with ThreadPoolExecutor(len(a.categories.split(','))) as ex:
            list(ex.map(lambda cat: crawl(cat, cutoff), a.categories.split(',')))
    elif a.cmd == 'find':
        rx, seen = re.compile(a.regex, re.I), set()
        for it in sorted(load_items(), key=lambda it: it['date']):
            if a.since <= it['date'] <= a.to and rx.search(it['title']) and it['title'][:50] not in seen:
                seen.add(it['title'][:50])
                print(f"{it['date']} | {it['title'][:140]} | {it['link']}")
    elif a.cmd == 'read':
        items = load_items()
        for key in a.links:
            for it in items:
                if key in it['link']:
                    print(f"[{it['date']}] {it['title']}\n{it['link']}\n{it['text'][:a.n]}\n")
                    break
    elif a.cmd == 'verify':
        verify(a.model, a.since)
    elif a.cmd == 'sets':
        make_sets(a.kind, a.out)
    elif a.cmd == 'prose':
        write_prose(a.kind, a.chapter)
    else:
        review(a.chapters)


if __name__ == '__main__':
    main()
