"""
The app frame for the Android APK: top bar, tab bar, icons and the links to CSS/JS, with an empty
content area. The APK shows it at once and app.js fetches the screen's content from the server.

    python -m app.shell           # write android/app/src/main/assets/shell/{hi,en}.html
    python -m app.shell --check   # exit 1 when those files are out of date (tests do the same)

Regenerate after changing templates/base.html, templates/shell.html, any file in static/ or the
strings the frame uses — tests/test_shell.py fails until you do.
"""
import sys

from .config import BASE_DIR
from .i18n import client_strings, t

SHELL_DIR = BASE_DIR / 'android' / 'app' / 'src' / 'main' / 'assets' / 'shell'
LANGS = ('hi', 'en')


def shell_html(lang):
    from .main import ASSET_V, CSP, templates
    # frame-ancestors only works as a response header; a <meta> policy must leave it out.
    csp = '; '.join(p.strip() for p in CSP.split(';') if not p.strip().startswith('frame-ancestors'))
    html = templates.get_template('shell.html').render(
        lang=lang, tr=lambda k: t(k, lang), L=lambda hi, en: hi if lang == 'hi' else en, device=None,
        site_url='', path='/', strings=client_strings(lang), ai_enabled=False, asset_v=ASSET_V, csp=csp)
    return '\n'.join(line.rstrip() for line in html.splitlines()) + '\n'


def main(argv=None):
    check = '--check' in (sys.argv[1:] if argv is None else argv)
    stale = []
    for lang in LANGS:
        path, html = SHELL_DIR / f'{lang}.html', shell_html(lang)
        if check:
            if not path.is_file() or path.read_text(encoding='utf-8') != html:
                stale.append(path.name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding='utf-8', newline='\n')
            print(f'wrote {path.relative_to(BASE_DIR)}')
    if stale:
        print('out of date: ' + ', '.join(stale) + ' — run: python -m app.shell')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
