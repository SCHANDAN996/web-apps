"""Job aggregation tests — offline, on trimmed copies of real pages (tests/fixtures)."""
from datetime import date
from pathlib import Path

import pytest

from app.jobs import pipeline
from app.jobs.extract import (application_window, classify, extract_facts, is_academic, is_roundup,
                              qualification, similar, vacancies)
from app.jobs.http import FetchError, Response
from app.jobs.sources import (HtmlListingSource, Item, RSSDiscoverySource, SSCSource, is_official,
                              official_links_from_page)
from app.models import Job, JobSource, SeenItem, SourceHealth

FX = Path(__file__).parent / 'fixtures'


def fx(name):
    return (FX / name).read_text(encoding='utf-8')


class FakeFetcher:
    """Serves canned responses; unknown URLs fail like an unreachable site."""
    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def get(self, url, params=None, headers=None):
        self.calls.append(url)
        for key, body in self.pages.items():
            if url.startswith(key):
                if isinstance(body, Exception):
                    raise body
                ctype = 'application/json' if key.endswith('records') else 'text/html'
                return Response(url, 200, body.encode('utf-8'), ctype)
        raise FetchError(f'no route {url}')


# ------------------------------------------------------------------ extraction
def test_ssc_chsl_notice_facts():
    f = extract_facts(fx('ssc_chsl_2026_notice.txt'))
    assert f['start_date'] == date(2026, 9, 7) and f['last_date'] == date(2026, 10, 7)
    assert f['vacancies'] == '2536'
    assert (f['age_min'], f['age_max']) == (18, 27)


def test_hindi_and_word_dates():
    assert application_window('आवेदन की अंतिम तिथि: 15/11/2026')[1] == date(2026, 11, 15)
    assert application_window('Last Date for Submission of\nApplications online\nOctober 13, 2026')[1] == date(2026, 10, 13)
    assert application_window('Last date: 5th December 2026')[1] == date(2026, 12, 5)
    # fee deadlines are not the application deadline
    assert application_window('Last date for fee payment 20.10.2026')[1] is None


def test_vacancies_and_qualification():
    assert vacancies('There are approx. 2536 tentative vacancies. Post code 12 posts') == '2536'
    assert vacancies('कुल पद: 120') == '120'
    assert qualification('Notice of Combined Higher Secondary (10+2) Level Examination') == '12th'
    assert qualification('Educational Qualification: Bachelor’s Degree from a recognised University') == 'graduate'
    assert qualification('the candidate should be eligible') is None      # "be" is not B.E.


def test_classify():
    assert classify('Notice of Junior Engineer Examination, 2026') == 'latest'
    assert classify('Uploading of Tentative Answer Keys') == 'answer'
    assert classify('Information regarding Admission Certificate') == 'admit'
    assert classify('Declaration of Result of Skill Test') == 'results'
    assert classify('Cancellation Notice for the post of Agriculture Assistant') == 'notice'
    assert is_academic('Calicut University Result 2026 Out - Check UG & PG Result')
    assert is_roundup('Latest Graduate Government Jobs 2026 (25000+ Vacancies Opening)')
    assert not is_roundup('MECL Non Executive Recruitment 2026 Apply Online for 121 Posts')


def test_similarity_respects_year():
    assert similar('SSC CGL Recruitment 2026 Notification', 'SSC CGL 2026 Notification Out')
    assert not similar('SSC CGL 2025 Notification', 'SSC CGL 2026 Notification')


def test_official_domains():
    assert is_official('https://ssc.gov.in/x.pdf') and is_official('https://www.aiimsbhopal.edu.in/a.pdf')
    assert is_official('https://www.licindia.in/careers')
    assert not is_official('https://www.freejobalert.com/articles/x')
    assert not is_official('https://sarkariresult.gov.in.example.com/')


# ------------------------------------------------------------------ sources
def test_ssc_source_parses_api():
    items = SSCSource().parse(fx('ssc_notice_boards.json'))
    chsl = next(i for i in items if i.title.startswith('Notice of Combined Higher Secondary'))
    assert chsl.kind == 'official' and chsl.doc_urls[0].endswith('Notice_of_adv_chsle_2026.pdf')
    assert chsl.doc_urls[0].startswith('https://ssc.gov.in/api/attachment/uploads/masterData/')
    assert len({i.url for i in items}) == len(items)      # unique even when files repeat


def test_uppsc_table_rows_give_dates():
    items = HtmlListingSource('uppsc', 'https://uppsc.up.nic.in/x', 'UPPSC', 'psc').parse(
        fx('uppsc_notifications.html'), 'https://uppsc.up.nic.in/CandidatePages/Notifications.aspx')
    assert len(items) == 2
    f = extract_facts(items[0].hint_text)
    assert f['advt_no'] == 'D-6/E-1/2025' and f['start_date'] == date(2026, 9, 21) and f['last_date'] == date(2026, 10, 21)


def test_isro_listing():
    items = HtmlListingSource('isro', 'https://www.isro.gov.in/Careers.html', 'ISRO').parse(
        fx('isro_careers.html'), 'https://www.isro.gov.in/Careers.html')
    assert any('LPSC/03/2026' in i.title for i in items)
    assert all(i.url.startswith('https://www.isro.gov.in/') for i in items)


def test_rss_and_official_link_resolution():
    items = RSSDiscoverySource('fja', 'u').parse(fx('freejobalert_feed.xml').encode())
    assert items and items[0].kind == 'discovery' and items[0].published
    docs, sites = official_links_from_page(fx('freejobalert_article.html'), 'https://www.freejobalert.com/a')
    assert docs[0].startswith('https://www.aiimsbhopal.edu.in/') and docs[0].endswith('.pdf')
    assert all('t.me' not in u and 'freejobalert' not in u for u in docs + sites)


# ------------------------------------------------------------------ pipeline
class StaticSource:
    def __init__(self, name, items, fail=False):
        self.name, self.items, self.fail = name, items, fail

    def fetch(self, http):
        if self.fail:
            raise FetchError('Connection reset by peer')
        return self.items


@pytest.fixture
def clean_jobs(db):
    for model in (JobSource, SeenItem, SourceHealth, Job):
        db.query(model).delete()
    db.commit()
    yield db


def test_pipeline_merges_discovery_into_official_and_survives_broken_source(clean_jobs):
    db = clean_jobs
    notice = 'https://ssc.gov.in/api/attachment/uploads/masterData/NoticeBoards/chsl.pdf'
    official = Item('ssc', 'official', 'Notice of Combined Higher Secondary (10+2) Level Examination, 2026',
                    'https://ssc.gov.in/#notice-1', org='SSC', category='ssc', doc_urls=[notice])
    discovered = Item('fja', 'discovery', 'SSC CHSL 2026 Notification Out - Apply Online for 2536 Posts',
                      'https://www.freejobalert.com/articles/ssc-chsl-2026')
    roundup = Item('fja', 'discovery', 'Latest All India Govt Jobs 2026 Notifications List (69313+ Vacancies)',
                   'https://www.freejobalert.com/articles/latest')
    article = f'<a href="{notice}">Download SSC CHSL Notification</a><a href="https://ssc.gov.in">Official</a>'
    http = FakeFetcher({notice: fx('ssc_chsl_2026_notice.txt'), 'https://www.freejobalert.com/articles/ssc-chsl': article})

    report = pipeline.run(db, [StaticSource('ssc', [official]), StaticSource('ibps', [], fail=True),
                               StaticSource('fja', [discovered, roundup])], http=http)

    assert report['ibps'] == {'error': 'FetchError: Connection reset by peer'}
    assert report['ssc']['new'] == 1 and report['fja']['merged'] == 1 and report['fja']['skipped'] == 1
    [job] = db.query(Job).all()
    assert job.status == 'verified' and job.title.startswith('Notice of Combined Higher Secondary')
    assert (job.start_date, job.last_date, job.vacancies) == (date(2026, 9, 7), date(2026, 10, 7), '2536')
    assert job.min_qualification == '12th' and job.notification_url == notice
    assert sorted(s.source for s in job.sources) == ['fja', 'ssc']
    assert db.get(SourceHealth, 'ibps').consecutive_failures == 1

    # Second run: nothing new to fetch, no duplicates.
    http.calls.clear()
    again = pipeline.run(db, [StaticSource('ssc', [official]), StaticSource('fja', [discovered])], http=http)
    assert again['ssc']['new'] == 0 and http.calls == []
    assert db.query(Job).count() == 1


def test_discovery_without_official_link_stays_hidden(clean_jobs, client):
    db = clean_jobs
    item = Item('fja', 'discovery', 'XYZ Board Clerk Recruitment 2026 - Apply Online for 50 Posts',
                'https://www.freejobalert.com/articles/xyz')
    http = FakeFetcher({'https://www.freejobalert.com/articles/xyz': '<a href="https://t.me/x">Telegram</a>'})
    pipeline.run(db, [StaticSource('fja', [item])], http=http)
    job = db.query(Job).one()
    assert job.status == 'pending'
    assert client.get('/api/v1/jobs?status=undated').json()['jobs'] == []   # never shown to students
