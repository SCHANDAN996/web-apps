import pytest
from app import bookqa_sources as sources


@pytest.mark.parametrize('url', ['http://ssc.gov.in/a', 'https://127.0.0.1/a', 'https://ssc.gov.in.evil.com/a',
                                 'https://user:pass@ssc.gov.in/a', 'https://ssc.gov.in:444/a'])
def test_nonofficial_or_unsafe_url_rejected(url):
    assert not sources.official_url(url)


def test_official_public_dns_required(monkeypatch):
    assert sources.official_url('https://ncert.nic.in/a')
    monkeypatch.setattr(sources.socket, 'getaddrinfo', lambda *a, **k: [(None, None, None, None, ('127.0.0.1', 443))])
    with pytest.raises(ValueError):
        sources.public_url('https://ncert.nic.in/a')


def test_robots_denial_prevents_page_fetch(monkeypatch):
    monkeypatch.setattr(sources, 'public_url', lambda url: None)
    reads = []
    def read(url):
        reads.append(url)
        return 'User-agent: *\nDisallow: /'
    monkeypatch.setattr(sources, '_read', read)
    with pytest.raises(ValueError, match='robots'):
        sources.fetch_excerpt('https://ncert.nic.in/page')
    assert reads == ['https://ncert.nic.in/robots.txt']


def test_evidence_text_excludes_script(monkeypatch):
    monkeypatch.setattr(sources, 'public_url', lambda url: None)
    monkeypatch.setattr(sources, '_read', lambda url: 'User-agent: *\nAllow: /' if url.endswith('robots.txt')
                        else '<script>SECRET</script><p>' + 'Official educational text. ' * 10 + '</p>')
    assert 'SECRET' not in sources.fetch_excerpt('https://ncert.nic.in/page')


def test_refresh_binds_evidence_to_current_content_and_does_not_repeat_fetch(tmp_path, monkeypatch):
    import hashlib
    import json
    from app import bookcheck
    section = tmp_path / 'Practice_hi_Set_01.txt'
    section.write_text('स्रोत: NCERT https://ncert.nic.in/example.html\n', encoding='utf-8')
    monkeypatch.setattr(bookcheck, 'section_files', lambda ch: {section.name: section})
    monkeypatch.setattr(bookcheck, 'is_prompt', lambda text: False)
    fetched = []
    monkeypatch.setattr(sources, 'fetch_excerpt', lambda url: fetched.append(url) or 'Official text ' * 20)
    assert sources.refresh(tmp_path) == 1
    data = json.loads((tmp_path / 'QA.references.json').read_text())
    entry = data['sources'][0]
    assert entry['content_sha'] == hashlib.sha256(section.read_bytes()).hexdigest()
    assert entry['sha256'] == hashlib.sha256(entry['excerpt'].encode()).hexdigest()
    assert entry['verified_by'] == 'official-fetch'
    assert sources.refresh(tmp_path) == 0
    assert len(fetched) == 1


def test_failed_reference_fetch_is_recorded_and_cools_down(tmp_path, monkeypatch):
    from app import bookcheck
    section = tmp_path / 'Practice_hi_Set_01.txt'
    section.write_text('Source: NCERT https://ncert.nic.in/example.html\n')
    monkeypatch.setattr(bookcheck, 'section_files', lambda ch: {section.name: section})
    monkeypatch.setattr(bookcheck, 'is_prompt', lambda text: False)
    calls = []
    def failed(url):
        calls.append(url)
        raise ValueError('blocked')
    monkeypatch.setattr(sources, 'fetch_excerpt', failed)
    assert sources.refresh(tmp_path, out=lambda x: None) == 1
    assert sources.refresh(tmp_path, out=lambda x: None) == 0
    assert len(calls) == 1


def test_pdf_reference_reads_bounded_text_pages(monkeypatch):
    from types import SimpleNamespace
    import pypdf
    monkeypatch.setattr(sources, 'public_url', lambda url: None)
    class Response:
        headers = SimpleNamespace(get_content_type=lambda: 'application/pdf')
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def geturl(self): return 'https://ssc.gov.in/syllabus.pdf'
        def read(self, n): return b'%PDF-fake'
    monkeypatch.setattr(sources, 'build_opener', lambda *a: SimpleNamespace(open=lambda *a, **kw: Response()))
    monkeypatch.setattr(pypdf, 'PdfReader', lambda data: SimpleNamespace(is_encrypted=False,
                        pages=[SimpleNamespace(extract_text=lambda: 'official syllabus text')] * 25))
    assert sources._read('https://ssc.gov.in/syllabus.pdf').count('official syllabus text') == 10


def test_source_fingerprint_preserves_crlf_bytes(tmp_path, monkeypatch):
    import hashlib
    import json
    from app import bookcheck
    path = tmp_path / 'Content_en.txt'
    path.write_bytes(b'Official lesson.\r\nSource: https://ssc.gov.in/reference\r\n')
    monkeypatch.setattr(bookcheck, 'section_files', lambda ch: {path.name: path})
    monkeypatch.setattr(bookcheck, 'is_prompt', lambda text: False)
    monkeypatch.setattr(sources, 'fetch_excerpt', lambda url: 'Official source text ' * 10)
    sources.refresh(tmp_path)
    entry = json.loads((tmp_path / 'QA.references.json').read_text())['sources'][0]
    assert entry['content_sha'] == hashlib.sha256(path.read_bytes()).hexdigest()
