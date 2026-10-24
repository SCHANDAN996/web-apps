import httpx
import pytest

from app.jobs import http


def fetcher(monkeypatch, handler):
    monkeypatch.setattr(http, 'public_host', lambda h: h in ('public.example', 'cdn.example'))
    return http.Fetcher(client=httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True), host_gap=0)


def test_robots_redirect_never_requests_private_target(monkeypatch):
    visited = []
    def handler(request):
        visited.append(str(request.url))
        return httpx.Response(302, headers={'location': 'http://169.254.169.254/latest/meta-data'})
    f = fetcher(monkeypatch, handler)
    with pytest.raises(http.FetchError, match='refusing private'):
        f.get('https://public.example/notice', retries=0)
    assert visited == ['https://public.example/robots.txt']


def test_public_robots_redirect_still_enforces_disallow_and_caches(monkeypatch):
    visited = []
    def handler(request):
        visited.append(str(request.url))
        if request.url.host == 'public.example' and request.url.path == '/robots.txt':
            return httpx.Response(302, headers={'location': 'https://cdn.example/robots'})
        if request.url.host == 'cdn.example':
            return httpx.Response(200, text='User-agent: *\nDisallow: /private\n')
        return httpx.Response(200, text='notice')
    f = fetcher(monkeypatch, handler)
    with pytest.raises(http.FetchError, match='robots.txt disallows'):
        f.get('https://public.example/private', retries=0)
    assert f.get('https://public.example/notice', retries=0).text == 'notice'
    assert len(visited) == 3


def test_robots_response_is_bounded(monkeypatch):
    monkeypatch.setattr(http, 'MAX_ROBOTS_BYTES', 32)
    visited = []
    def handler(request):
        visited.append(str(request.url))
        return httpx.Response(200, content=b'x' * 33)
    with pytest.raises(http.FetchError, match='too large'):
        fetcher(monkeypatch, handler).get('https://public.example/notice', retries=0)
    assert len(visited) == 1


def test_robots_redirect_loop_is_bounded(monkeypatch):
    visited = []
    def handler(request):
        visited.append(str(request.url))
        return httpx.Response(302, headers={'location': '/robots.txt'})
    with pytest.raises(http.FetchError, match='robots.txt redirects'):
        fetcher(monkeypatch, handler).get('https://public.example/notice', retries=0)
    assert len(visited) == http.MAX_REDIRECTS + 1
