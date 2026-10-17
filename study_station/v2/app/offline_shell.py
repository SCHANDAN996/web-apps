"""Build the fully local Android study entry pages; contains no learner data."""
from .config import BASE_DIR
from .i18n import client_strings, t

OUT = BASE_DIR / 'android/app/src/main/assets/offline'


def render(lang):
    from .main import ASSET_V, CSP, templates
    policy = '; '.join(p.strip() for p in CSP.split(';') if not p.strip().startswith('frame-ancestors'))
    return templates.get_template('offline_study.html').render(
        lang=lang, tr=lambda k: t(k, lang), L=lambda hi, en: hi if lang == 'hi' else en,
        device=None, site_url='', path='/offline-study', strings=client_strings(lang),
        ai_enabled=False, asset_v=ASSET_V, csp=policy)


def main(check=False):
    OUT.mkdir(parents=True, exist_ok=True)
    stale = []
    for lang in ('hi', 'en'):
        path, html = OUT / f'{lang}.html', render(lang)
        if check:
            if not path.is_file() or path.read_text(encoding='utf-8') != html:
                stale.append(lang)
        else:
            path.write_text(html, encoding='utf-8', newline='\n')
            print(f'wrote offline/{lang}.html')
    if stale:
        print('out of date offline shells: ' + ', '.join(stale))
    return int(bool(stale))


if __name__ == '__main__':
    main()
