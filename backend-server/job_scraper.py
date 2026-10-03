"""
Study Station — Multi-Source Government Job Aggregator (v2)

Core principles:
1. NEVER invent data. A field is stored only if it was actually extracted
   from the source page. Missing fields stay NULL and the website shows
   "Refer to the official notification" instead.
2. Every job keeps its source URL (`official_url`) so students can always
   verify details on the official website before applying.
3. Polite scraping: custom User-Agent, timeouts, delays between requests.

CLI usage:
    python job_scraper.py run        # fetch feeds, add new jobs (default)
    python job_scraper.py clean      # remove legacy fake/mock data from DB
    python job_scraper.py backfill   # re-fetch real details for jobs missing them
"""

import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import JobAlert
from build_website import build_ssg

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
}

# ---------------------------------------------------------------------------
# Extraction patterns (labels seen on IndGovtJobs / FreeJobAlert / similar)
# ---------------------------------------------------------------------------

MONTHS = (r'Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
          r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?')

# 12-05-2026 | 12/05/2026 | 12.05.2026 | 12 May 2026 | May 12, 2026
DATE_RE = re.compile(
    r'(\d{1,2}\s*[-/.]\s*\d{1,2}\s*[-/.]\s*\d{2,4}'
    r'|\d{1,2}(?:st|nd|rd|th)?\s+(?:' + MONTHS + r')\.?,?\s+\d{4}'
    r'|(?:' + MONTHS + r')\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    re.IGNORECASE)

# label shown to users -> regexes matched against a line of page text
DATE_LABELS = [
    ('Application Begin',   [r'application\s+begin', r'apply\s+online\s+(?:start|begin)',
                             r'starting\s+date', r'start\s+date', r'opening\s+date',
                             r'notification\s+date', r'date\s+of\s+advertisement']),
    ('Last Date to Apply',  [r'last\s+date', r'closing\s+date', r'apply\s+(?:online\s+)?(?:till|until|upto)',
                             r'end\s+date']),
    ('Fee Payment Last Date', [r'(?:pay|payment|fee).{0,25}last\s+date', r'last\s+date.{0,25}fee']),
    ('Exam Date',           [r'exam(?:ination)?\s+date', r'date\s+of\s+exam', r'cbt\s+date']),
    ('Admit Card',          [r'admit\s+card', r'call\s+letter', r'hall\s+ticket']),
    ('Result Date',         [r'result\s+date', r'result\s+decl']),
]

FEE_CATEGORY_LABELS = [
    ('General / OBC / EWS', [r'gen(?:eral)?\s*[/,&]?\s*(?:obc|ews)', r'\bur\b.{0,10}obc', r'unreserved']),
    ('General',             [r'\bgeneral\b', r'\bgen\b', r'\bur\b']),
    ('OBC',                 [r'\bobc\b']),
    ('EWS',                 [r'\bews\b']),
    ('SC / ST',             [r'\bsc\s*[/,&]?\s*st\b', r'\bst\s*[/,&]?\s*sc\b']),
    ('SC',                  [r'\bsc\b']),
    ('ST',                  [r'\bst\b']),
    ('PH / PwD',            [r'\bp[wh]d?\b', r'divyang', r'handicap']),
    ('Female',              [r'female', r'women', r'mahila']),
]

MONEY_RE = re.compile(r'(?:rs\.?|₹|inr)\s*\.?\s*([\d,]+)(?:\s*/-)?', re.IGNORECASE)

AGE_RE_RANGE = re.compile(r'(\d{2})\s*(?:years?|yrs?)?\s*(?:to|-|–)\s*(\d{2})\s*(?:years?|yrs?)', re.IGNORECASE)
AGE_RE_MINMAX = re.compile(r'(?:minimum|min\.?)\s*age\s*[:\-]?\s*(\d{2})|(?:maximum|max\.?)\s*age\s*[:\-]?\s*(\d{2})', re.IGNORECASE)

VACANCY_RE = [
    re.compile(r'(?:total\s+(?:posts?|vacanc(?:y|ies)|seats?))\s*[:\-]?\s*([\d,]+)', re.IGNORECASE),
    re.compile(r'([\d,]+)\s+(?:posts?|vacanc(?:y|ies)|seats?)\b', re.IGNORECASE),
]

QUALIFICATION_HINTS = re.compile(
    r'(10th|12th|matric|intermediate|graduate|graduation|bachelor|b\.?tech|b\.?e\b|'
    r'b\.?sc|b\.?com|b\.?a\b|m\.?sc|m\.?a\b|mba|diploma|iti|degree|post\s*graduate|cbse|any\s+stream)',
    re.IGNORECASE)


class JobAggregator:
    def __init__(self):
        # Open/official RSS feeds. Aggregators give us the notification link;
        # real details are then extracted from the linked article page.
        self.sources = [
            {"name": "IndGovtJobs", "url": "https://www.indgovtjobs.in/feeds/posts/default?alt=rss", "type": "rss"},
            {"name": "FreeJobAlert", "url": "https://www.freejobalert.com/feed/", "type": "rss"},
            {"name": "SarkariJobFind", "url": "https://sarkarijobfind.com/feed/", "type": "rss"},
            {"name": "SarkariWallahJob", "url": "https://sarkariwallahjob.com/feed/", "type": "rss"},
        ]

    # ------------------------------------------------------------------ #
    # Feed fetching
    # ------------------------------------------------------------------ #

    def fetch_url(self, url):
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"  ! Fetch failed for {url}: {e}")
            return None

    def parse_rss(self, xml_content):
        jobs = []
        try:
            root = ET.fromstring(xml_content)
            for item in root.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                if title is not None and link is not None and title.text and link.text:
                    jobs.append({'title': title.text.strip(), 'link': link.text.strip()})
        except Exception as e:
            print(f"  ! RSS parse error: {e}")
        return jobs

    # ------------------------------------------------------------------ #
    # Real detail extraction — the heart of v2
    # ------------------------------------------------------------------ #

    def extract_details(self, url, title=""):
        """Fetch the article page and extract ONLY real, verifiable fields.

        Returns a dict where every key is optional; missing = unknown.
        """
        details = {}
        html = self.fetch_url(url)
        if not html:
            return details

        try:
            soup = BeautifulSoup(html, 'html.parser')
        except Exception as e:
            print(f"  ! HTML parse error: {e}")
            return details

        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # Table rows are the most reliable label/value source on job sites.
        lines = []
        for tr in soup.find_all('tr'):
            cells = [c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'])]
            cells = [c for c in cells if c]
            if cells:
                lines.append(' : '.join(cells))
        # Fall back to plain text lines for sites without tables.
        text = soup.get_text('\n', strip=True)
        lines.extend(l.strip() for l in text.split('\n') if 6 < len(l.strip()) < 300)

        details.update(self._extract_dates(lines))
        fee = self._extract_fees(lines)
        if fee:
            details['application_fee'] = json.dumps(fee, ensure_ascii=False)
        age = self._extract_age(lines)
        if age:
            details['age_limit'] = age
        vac = self._extract_vacancies(lines, title)
        if vac:
            details['vacancies'] = vac
        elig = self._extract_eligibility(lines)
        if elig:
            details['eligibility'] = elig
        return details

    def _extract_dates(self, lines):
        found = {}
        for line in lines:
            low = line.lower()
            date_match = DATE_RE.search(line)
            if not date_match:
                continue
            for label, patterns in DATE_LABELS:
                if label in found:
                    continue
                if any(re.search(p, low) for p in patterns):
                    found[label] = date_match.group(1).strip()
                    break
        out = {}
        if found:
            out['important_dates'] = json.dumps(found, ensure_ascii=False)
            if 'Last Date to Apply' in found:
                out['last_date'] = found['Last Date to Apply']
        return out

    def _extract_fees(self, lines):
        fees = {}
        for line in lines:
            low = line.lower()
            if 'fee' not in low and 'शुल्क' not in line:
                continue
            money = MONEY_RE.search(line)
            if not money:
                # "No fee" / "Nil" cases
                if re.search(r'\b(no\s+fee|nil|exempt)', low):
                    for label, patterns in FEE_CATEGORY_LABELS:
                        if any(re.search(p, low) for p in patterns) and label not in fees:
                            fees[label] = '₹0'
                continue
            amount = '₹' + money.group(1)
            for label, patterns in FEE_CATEGORY_LABELS:
                if any(re.search(p, low) for p in patterns):
                    fees.setdefault(label, amount)
                    break
        return fees

    def _extract_age(self, lines):
        for line in lines:
            low = line.lower()
            if 'age' not in low and 'आयु' not in line:
                continue
            m = AGE_RE_RANGE.search(line)
            if m:
                return f"{m.group(1)} - {m.group(2)} Years (as per notification)"
        mins, maxs = None, None
        for line in lines:
            if 'age' not in line.lower():
                continue
            for m in AGE_RE_MINMAX.finditer(line):
                if m.group(1):
                    mins = m.group(1)
                if m.group(2):
                    maxs = m.group(2)
        if mins and maxs:
            return f"{mins} - {maxs} Years (as per notification)"
        return None

    def _extract_vacancies(self, lines, title):
        # The feed title itself often carries "(4708 Posts)" — most reliable.
        for rx in VACANCY_RE:
            m = rx.search(title)
            if m:
                return m.group(1).replace(',', '')
        for line in lines:
            for rx in VACANCY_RE[:1]:  # only the explicit "Total Posts:" form
                m = rx.search(line)
                if m:
                    return m.group(1).replace(',', '')
        return None

    def _extract_eligibility(self, lines):
        for line in lines:
            low = line.lower()
            if re.search(r'(qualification|eligibility|योग्यता)', low) and QUALIFICATION_HINTS.search(line):
                # Keep it short and readable
                cleaned = re.sub(r'\s+', ' ', line).strip(' :-')
                return cleaned[:300]
        return None

    # ------------------------------------------------------------------ #
    # Categorisation
    # ------------------------------------------------------------------ #

    def categorize_job(self, title):
        t = title.lower()
        if any(k in t for k in ['bank', 'sbi', 'rbi', 'ibps', ' po ', 'clerk', 'nabard']):
            return "BANKING"
        if any(k in t for k in ['railway', 'rrb', 'ntpc', 'rrc', 'metro']):
            return "RAILWAY"
        if any(k in t for k in ['ssc', 'cgl', 'chsl', ' mts', 'stenographer']):
            return "SSC"
        if any(k in t for k in ['upsc', 'ias', 'ips', 'civil service']):
            return "UPSC"
        if any(k in t for k in ['psc', 'state service']):
            return "STATE_PSC"
        if any(k in t for k in ['police', 'constable', 'defence', 'army', 'navy', 'air force', 'agniveer', 'crpf', 'bsf', 'cisf', 'itbp']):
            return "POLICE_DEFENCE"
        if any(k in t for k in ['teacher', 'tet', 'b.ed', 'professor', 'faculty', 'kvs', 'nvs']):
            return "TEACHING"
        if any(k in t for k in ['private', 'tcs', 'infosys', 'wipro', 'hcl']):
            return "PRIVATE"
        return "GOVT"

    def detect_job_type(self, title):
        t = title.lower()
        if 'result' in t:
            return "RESULT"
        if 'admit card' in t or 'call letter' in t or 'hall ticket' in t:
            return "ADMIT_CARD"
        if 'syllabus' in t:
            return "SYLLABUS"
        if 'answer key' in t:
            return "ANSWER_KEY"
        return "LATEST_JOB"

    # ------------------------------------------------------------------ #
    # Main run
    # ------------------------------------------------------------------ #

    def run(self):
        print("Starting Job Aggregator v2 (real-data mode)...")
        all_items = []
        for source in self.sources:
            print(f"Fetching feed: {source['name']}")
            content = self.fetch_url(source['url'])
            if content:
                items = self.parse_rss(content)
                print(f" -> {len(items)} items")
                all_items.extend(items)
            time.sleep(2)

        if not all_items:
            print("No items retrieved from any source.")
            return

        added_jobs = []
        with app.app_context():
            for item in all_items:
                title, link = item['title'], item['link']

                if JobAlert.query.filter_by(application_url=link).first():
                    continue
                if JobAlert.query.filter_by(title=title).first():
                    continue

                job_type = self.detect_job_type(title)
                category = self.categorize_job(title)

                # Fetch REAL details from the article page (only for new jobs).
                print(f"Extracting details: {title[:70]}...")
                details = self.extract_details(link, title)
                time.sleep(1.5)  # polite delay between article fetches

                new_job = JobAlert(
                    job_type=job_type,
                    title=title,
                    organization=None,
                    post_name=title,
                    description=(
                        f"{title} — full details, eligibility and dates are available in the "
                        f"official notification. Always verify on the official website before applying."
                    ),
                    vacancies=details.get('vacancies'),
                    eligibility=details.get('eligibility'),
                    last_date=details.get('last_date'),
                    application_fee=details.get('application_fee'),
                    important_dates=details.get('important_dates'),
                    age_limit=details.get('age_limit'),
                    vacancy_details=None,
                    application_url=link,
                    official_url=link,
                    category=category,
                )
                db.session.add(new_job)
                added_jobs.append({'title': title, 'link': link, 'job_type': job_type})
                print(f"  + Added [{job_type}] {title[:70]}")

            if added_jobs:
                db.session.commit()
                print(f"Added {len(added_jobs)} new jobs.")
                print("Rebuilding static site...")
                build_ssg()
                self.broadcast_to_telegram(added_jobs)
            else:
                print("No new jobs found. Everything up to date.")

    # ------------------------------------------------------------------ #
    # Legacy data cleanup — removes the old mock values (fake dates/fees)
    # ------------------------------------------------------------------ #

    MOCK_DATE_SNIPPET = '"Application Begin": "01/05/2026"'
    MOCK_FEE_SNIPPET = '"General / OBC / EWS": "100"'
    MOCK_AGE_SNIPPET = 'Minimum Age : 18 Years.'
    MOCK_VACANCY_SNIPPET = '"post_name": "Generic Post"'

    def clean_fake_data(self):
        """Null out the hardcoded mock fields the old scraper wrote."""
        cleaned = 0
        with app.app_context():
            for job in JobAlert.query.all():
                dirty = False
                if job.important_dates and self.MOCK_DATE_SNIPPET in job.important_dates:
                    job.important_dates = None
                    dirty = True
                if job.application_fee and self.MOCK_FEE_SNIPPET in job.application_fee:
                    job.application_fee = None
                    dirty = True
                if job.age_limit and self.MOCK_AGE_SNIPPET in job.age_limit:
                    job.age_limit = None
                    dirty = True
                if job.vacancy_details and self.MOCK_VACANCY_SNIPPET in (job.vacancy_details or ''):
                    job.vacancy_details = None
                    dirty = True
                if job.last_date == '30-05-2026':
                    job.last_date = None
                    dirty = True
                if job.vacancies == 'Unknown':
                    job.vacancies = None
                    dirty = True
                if job.eligibility == 'Refer Official Notification':
                    job.eligibility = None
                    dirty = True
                if job.organization == 'Govt/Public Sector':
                    job.organization = None
                    dirty = True
                if dirty:
                    cleaned += 1
            db.session.commit()
        print(f"Cleaned mock data from {cleaned} jobs.")
        return cleaned

    def backfill_details(self, limit=None):
        """Re-fetch real details for jobs that have no important_dates yet."""
        updated = 0
        with app.app_context():
            q = JobAlert.query.filter(JobAlert.important_dates.is_(None)).order_by(JobAlert.created_at.desc())
            jobs = q.limit(limit).all() if limit else q.all()
            print(f"Backfilling {len(jobs)} jobs...")
            for job in jobs:
                url = job.official_url or job.application_url
                if not url:
                    continue
                print(f"  Backfill: {job.title[:70]}...")
                details = self.extract_details(url, job.title)
                time.sleep(1.5)
                if not details:
                    continue
                for field in ('important_dates', 'last_date', 'application_fee',
                              'age_limit', 'vacancies', 'eligibility'):
                    if details.get(field) and not getattr(job, field):
                        setattr(job, field, details[field])
                updated += 1
                if updated % 20 == 0:
                    db.session.commit()
            db.session.commit()
        print(f"Backfilled details for {updated} jobs.")
        return updated

    # ------------------------------------------------------------------ #
    # Telegram
    # ------------------------------------------------------------------ #

    def broadcast_to_telegram(self, new_jobs_list):
        from telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, IS_TELEGRAM_ENABLED

        if not IS_TELEGRAM_ENABLED:
            print("Telegram broadcasting is disabled in config.")
            return

        print(f"Broadcasting {len(new_jobs_list)} new jobs to Telegram...")
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

        for job in new_jobs_list:
            message = (
                f"🚨 *New {job.get('job_type', 'Update').replace('_', ' ').title()}!*\n\n"
                f"📌 *{job['title']}*\n"
                f"🔗 [Official Details]({job['link']})\n\n"
                f"⚠️ Verify all dates on the official website.\n"
                f"🌐 *Study Station*"
            )
            payload = {
                "chat_id": TELEGRAM_CHANNEL_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            }
            try:
                r = requests.post(url, json=payload, timeout=15)
                if r.status_code == 200:
                    print(f"  Broadcasted: {job['title'][:60]}")
                else:
                    print(f"  Telegram error: {r.text[:200]}")
            except Exception as e:
                print(f"  Failed to broadcast: {e}")


if __name__ == "__main__":
    aggregator = JobAggregator()
    command = sys.argv[1] if len(sys.argv) > 1 else 'run'
    if command == 'clean':
        aggregator.clean_fake_data()
    elif command == 'backfill':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
        aggregator.backfill_details(limit)
    elif command == 'run':
        aggregator.run()
    else:
        print(__doc__)
