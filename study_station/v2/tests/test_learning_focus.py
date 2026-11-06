from bs4 import BeautifulSoup
from app import config, observe


def test_learning_product_has_no_public_recruitment_routes_or_links(client):
    assert config.JOBS_ENABLED is False
    for path in ['/jobs', '/jobs/old-notice', '/api/v1/jobs']:
        assert client.get(path).status_code == 410
    client.post('/api/v1/me', json={'level':'10th'})
    for path in ['/', '/settings', '/mock', '/current-affairs']:
        doc=BeautifulSoup(client.get(path).text,'html.parser')
        assert not doc.select('a[href^="/jobs"]')
    assert '/jobs' not in client.get('/sitemap.xml').text
    assert '/current-affairs' in client.get('/sitemap.xml').text
    assert not any('/jobs' in path for path in client.get('/openapi.json').json()['paths'])


def test_retired_jobs_do_not_raise_scheduler_health_alerts(db):
    messages=' '.join(a['msg'] for a in observe.collect(db)['alerts'])
    assert 'job sweep' not in messages
    assert 'job sources' not in messages
    assert 'verified jobs' not in messages


def test_scheduler_retirement_preserves_other_services_and_current_affairs():
    from deploy.retire_jobs import retire_lines
    text=('API_KEY=not-a-real-key\n'
          '17 */3 * * * $SS/deploy/run.sh python -m app.jobs run >> jobs.log\n'
          '40 6 * * * $SS/deploy/run.sh python -m app.current_affairs run\n'
          '0 8 * * * $SS/deploy/run.sh python -m app.jobs digest --telegram\n'
          '45 2 * * * $SS/deploy/backup.sh\n')
    after,count=retire_lines(text)
    assert count == 2 and 'app.jobs' not in after
    assert 'API_KEY=not-a-real-key' in after
    assert 'app.current_affairs' in after and 'backup.sh' in after
    assert retire_lines(after) == (after,0)
