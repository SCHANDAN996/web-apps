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


def test_shared_theme_controls_and_reading_first_home_cards(client, monkeypatch):
    from app import main
    monkeypatch.setattr(main, 'has_books', lambda: True)
    client.post('/api/v1/me', json={'level': '10th'})
    home = BeautifulSoup(client.get('/').text, 'html.parser')
    choices = home.select('#themePicker [data-theme-set]')
    assert [b['data-theme-set'] for b in choices] == ['light', 'dark', 'paper']
    assert all(b.name == 'button' and b['aria-pressed'] == 'false' for b in choices)
    assert home.select_one('#themePicker summary')['aria-label']
    steps = home.select('[aria-labelledby="plan-h"] .home-image-card')
    assert len(steps) == 4
    assert steps[0]['href'] == '/books'
    assert steps[0]['id'] == 'planRead'
    assert steps[1]['data-practice']
    assert steps[2]['href'] == '/revise'
    assert steps[3]['href'] == '/current-affairs'
    assert all(card.select_one('img')['alt'] == '' for card in steps)
    settings = BeautifulSoup(client.get('/settings').text, 'html.parser')
    assert settings.select_one('[data-theme-set=system]')
    assert len(settings.select('[data-theme-set=paper]')) == 2
    assert settings.select_one('#resetProgress')['type'] == 'button'
    assert '"reset_progress_warning"' in client.get('/settings').text


def test_home_collaboration_cards_precede_learning(client):
    client.post('/api/v1/me', json={'level': '10th'})
    home=BeautifulSoup(client.get('/').text, 'html.parser')
    cards=home.select('.home-collaboration-grid .home-image-card')
    assert [c['href'] for c in cards] == ['/classroom?view=workspace','/classroom?view=groups','/classroom?view=classes','/classroom?view=shared']
    assert all(c.select_one('img[alt=""]') for c in cards)
    # Owner's UI plan (design/UI_UX_NEXT_AND_AI_HANDOFF.md, P0 Home): today's action first, then the four
    # collaboration cards, then the study block.
    order = [s.get('aria-labelledby') for s in home.select('main .stack > section')]
    assert order[:3] == ['home-today-h', 'home-collaboration-h', 'plan-h']


def test_home_today_card_leads_with_one_action(client):
    client.post('/api/v1/me', json={'level': '10th'})
    home = BeautifulSoup(client.get('/').text, 'html.parser')
    today = home.select_one('main .stack > section')
    start = today.select_one('#homeStart')
    assert 'btn-primary' in start['class'] and (start.get('data-practice') or start.get('href') == '/practice')
    assert 'आज के 10 सवाल' in start.text
    cont = today.select_one('#continueRead')
    assert cont['href'] == '/books' and cont.select_one('[data-continue-label]')
    # membership is a small status link right after the card, not a big button above everything
    link = home.select_one('main .stack > a.home-status-link')
    assert link['href'] == '/membership' and link.find_previous_sibling('section') is today
    assert not home.select('main .stack > a.btn[href="/membership"], main > a.btn[href="/membership"]')
    client.cookies.set('ss_lang', 'en')
    en = BeautifulSoup(client.get('/').text, 'html.parser')
    assert "Start today's 10 questions" in en.select_one('#homeStart').text
