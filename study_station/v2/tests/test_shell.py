"""The app frame shipped in the APK must be the one the current templates and static files produce."""
import pytest

from app import shell


@pytest.mark.parametrize('lang', shell.LANGS)
def test_apk_frame_is_up_to_date(lang):
    path = shell.SHELL_DIR / f'{lang}.html'
    assert path.is_file(), 'run: python -m app.shell'
    assert path.read_text(encoding='utf-8') == shell.shell_html(lang), 'run: python -m app.shell'


def test_frame_has_structure_but_no_content_and_no_learner_data():
    html = shell.shell_html('hi')
    assert 'id="shellWait"' in html and 'class="tabbar"' in html and 'class="topbar"' in html
    assert 'Content-Security-Policy' in html and 'frame-ancestors' not in html
    assert '/static/js/app.js?v=' in html and 'rel="canonical"' not in html
    assert shell.shell_html('en') != html


def test_served_pages_are_not_the_frame(client):
    r = client.get('/')
    assert 'id="shellWait"' not in r.text and 'class="nav-progress"' in r.text
