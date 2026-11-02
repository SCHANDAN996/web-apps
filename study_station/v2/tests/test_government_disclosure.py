"""The rejection fix keeps sources and non-affiliation visible in both languages."""
from pathlib import Path

from bs4 import BeautifulSoup

from app.models import Job


def test_public_information_discloses_identity_and_original_source(client, db):
    row = Job(slug='disclosure-notice', title='Official notice', status='verified',
              category='ssc', official_url='https://ssc.gov.in/',
              notification_url='https://ssc.gov.in/notice.pdf')
    db.add(row)
    db.commit()
    try:
        for language, phrase in [('hi', 'किसी सरकारी संस्था'), ('en', 'does not represent any government')]:
            client.post('/api/v1/me', json={'lang': language})
            for url in ['/jobs', '/jobs/disclosure-notice', '/current-affairs']:
                response = client.get(url)
                assert response.status_code == 200
                doc = BeautifulSoup(response.text, 'html.parser')
                assert phrase in doc.select_one('aside.notice').text
                assert doc.select_one('details a[href="https://ssc.gov.in/"]')
            detail = BeautifulSoup(client.get('/jobs/disclosure-notice').text, 'html.parser')
            assert detail.select_one('.jobs-links a[href="https://ssc.gov.in/notice.pdf"]')
    finally:
        db.delete(row)
        db.commit()


def test_store_descriptions_include_sources_and_current_trial():
    listing = (Path(__file__).parents[1] / 'docs/play-release/store-listing.md').read_text(encoding='utf-8')
    for marker, end, trial in [('**Full description:**', '## हिन्दी', '3-month'),
                               ('**पूरा विवरण:**', '## Claim exclusions', '3 महीने')]:
        text = listing.split(marker)[1].split(end)[0].strip()
        assert len(text) <= 4000
        assert trial in text
        for source in ['https://ssc.gov.in/', 'https://upsc.gov.in/', 'https://pib.gov.in/',
                       'https://www.newsonair.gov.in/', 'https://www.rrbcdg.gov.in/']:
            assert source in text
    assert '3-day' not in listing and '3 दिन' not in listing
