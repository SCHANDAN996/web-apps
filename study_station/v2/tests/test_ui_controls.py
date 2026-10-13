"""Job filter combinations and the shared, accessible appearance controls."""
from datetime import timedelta
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup

from app import services
from app.models import Job


def test_job_filters_preserve_category_and_hide_other_results(client, db):
    deadline = services.today_ist() + timedelta(days=10)
    db.add_all([
        Job(slug='ui-railway', title='Complete official railway recruitment title', org='RRB',
            category='railway', status='verified', min_qualification='12th', last_date=deadline),
        Job(slug='ui-bank', title='UI banking recruitment', category='banking',
            status='verified', min_qualification='12th', last_date=deadline),
        Job(slug='ui-pending', title='UI pending recruitment', category='railway',
            status='pending', min_qualification='12th', last_date=deadline),
    ])
    db.commit()
    doc = BeautifulSoup(client.get('/jobs?status=active&qualification=12th&category=railway').text, 'html.parser')
    cards = doc.select('[data-job-search]')
    assert any(c['href'] == '/jobs/ui-railway' for c in cards)
    assert not any(c['href'] in ['/jobs/ui-bank', '/jobs/ui-pending'] for c in cards)
    for tab in doc.select('.jobs-tabs a'):
        params = parse_qs(urlsplit(tab['href']).query)
        assert params['category'] == ['railway'] and params['qualification'] == ['12th']
    form = doc.select_one('#jobFilters')
    assert form.select_one('select[name=category] option[selected]')['value'] == 'railway'
    assert form.select_one('select[name=qualification] option[selected]')['value'] == '12th'
    assert doc.select_one('#jobSearch')['aria-label']
    assert doc.select_one('#jobShown').text == str(len(cards))
    assert 'clamp-2' not in doc.select_one('.job-title').get('class', [])
    reset = next(a for a in doc.select('a') if a.text.strip() == 'फ़िल्टर हटाएँ')
    assert parse_qs(urlsplit(reset['href']).query) == {'status': ['active'], 'qualification': ['all']}


def test_shared_theme_controls_and_numbered_home_plan(client, monkeypatch):
    from app import main
    monkeypatch.setattr(main, 'has_books', lambda: True)
    client.post('/api/v1/me', json={'level': '10th'})
    home = BeautifulSoup(client.get('/').text, 'html.parser')
    choices = home.select('#themePicker [data-theme-set]')
    assert [b['data-theme-set'] for b in choices] == ['light', 'dark', 'paper']
    assert all(b.name == 'button' and b['aria-pressed'] == 'false' for b in choices)
    assert home.select_one('#themePicker summary')['aria-label']
    steps = home.select('ol.study-sequence > li')
    assert steps[0].select_one('a')['href'] == '/books'
    assert steps[1].select_one('button')['data-practice']
    assert steps[2].select_one('a')['href'] == '/revise'
    settings = BeautifulSoup(client.get('/settings').text, 'html.parser')
    assert settings.select_one('[data-theme-set=system]')
    assert len(settings.select('[data-theme-set=paper]')) == 2
    assert settings.select_one('#resetProgress')['type'] == 'button'
    assert '"reset_progress_warning"' in client.get('/settings').text
