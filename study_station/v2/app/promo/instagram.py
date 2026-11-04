"""API-free Instagram queue and optional local browser publisher.

No browser runs during rendering. Login, browser profile and upload journal stay on
an operator's PC/VPS, outside Git. UI selectors must be checked against the live UI
before unattended operation; an unfamiliar UI stops instead of guessing.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[4]


class InstagramError(RuntimeError):
    pass


def account_name(value):
    value = value.strip().lstrip('@').lower()
    if not re.fullmatch(r'[a-z0-9._]{1,30}', value):
        raise InstagramError('invalid account name')
    return value


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        if os.name != 'nt':
            directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def enqueue(question_id, video, caption, day):
    video = Path(video)
    revision = subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True, timeout=10, check=True).stdout.strip()
    atomic_json(video.with_suffix('.instagram.json'), {
        'version': 1, 'id': question_id, 'day': day, 'video': video.name,
        'sha256': hashlib.sha256(video.read_bytes()).hexdigest(), 'caption': caption,
        'source_ref': os.environ.get('PROMO_YOUTUBE_BRANCH', ''), 'source_sha': revision,
    })


def load_queue(folder):
    folder = Path(folder).resolve()
    items, seen = [], set()
    for meta in sorted(folder.glob('*.instagram.json')):
        try:
            if meta.is_symlink() or meta.stat().st_size > 65536:
                raise InstagramError('invalid Instagram manifest file')
            item = json.loads(meta.read_text(encoding='utf-8'))
            if not isinstance(item, dict):
                raise InstagramError('invalid Instagram queue artifact')
            name = item['video']
            if not isinstance(name, str) or '/' in name or '\\' in name or not name.endswith('.mp4'):
                raise InstagramError('queue video must be a plain MP4 filename')
            video = (folder / name).resolve()
            if video.parent != folder:
                raise InstagramError('queue filename escapes artifact directory')
            if item.get('version') != 1 or not isinstance(item['id'], str) or not item['id']:
                raise InstagramError('invalid queue version or question id')
            if item['id'] in seen:
                raise InstagramError('duplicate question in queue')
            if not isinstance(item['caption'], str) or len(item['caption']) > 2200:
                raise InstagramError('invalid caption or caption exceeds 2200 characters')
            if hashlib.sha256(video.read_bytes()).hexdigest() != item['sha256']:
                raise InstagramError('video checksum mismatch')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise InstagramError('invalid Instagram queue artifact') from exc
        seen.add(item['id'])
        items.append(dict(item, path=video))
    return items


def private_state(folder):
    folder = Path(folder).expanduser().resolve()
    if folder == REPO or REPO in folder.parents or any((parent / '.git').exists() for parent in (folder, *folder.parents)):
        raise InstagramError('browser state must be outside all Git repositories')
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != 'nt':
        folder.chmod(0o700)
    return folder


def read_journal(path):
    if not Path(path).exists():
        return {'uploads': {}}
    try:
        result = json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(result, dict) or not isinstance(result.get('uploads'), dict):
            raise ValueError()
        return result
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise InstagramError('invalid upload journal; restore it before continuing') from exc


@contextmanager
def locked(journal):
    lock = Path(str(journal) + '.lock')
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise InstagramError('publisher locked; check running process before removing stale lock') from exc
    os.close(fd)
    try:
        yield
    finally:
        lock.unlink()


def process(folder, journal, account, share):
    """share(item, checkpoint) must call checkpoint immediately before Share."""
    account = account_name(account)
    with locked(journal):
        data = read_journal(journal)
        count = 0
        for item in load_queue(folder):
            key = f"{account}:{item['id']}"
            previous = data['uploads'].get(key, {})
            if previous.get('status') == 'uploaded':
                continue
            if previous.get('status') == 'pending':
                raise InstagramError('pending Share result: inspect Instagram and reconcile before retry')
            if previous.get('status') not in (None, 'ready'):
                raise InstagramError('unknown journal status; reconcile before publishing')
            checkpointed = False

            def checkpoint():
                nonlocal checkpointed
                data['uploads'][key] = {
                    'status': 'pending', 'sha256': item['sha256'],
                    'at': datetime.now(timezone.utc).isoformat(),
                }
                atomic_json(journal, data)
                checkpointed = True

            confirmation = share(item, checkpoint)
            if not checkpointed or not confirmation:
                raise InstagramError('publisher did not confirm Share')
            data['uploads'][key]['status'] = 'uploaded'
            atomic_json(journal, data)
            count += 1
        return count


def reconcile(journal, account, question_id, status, url):
    with locked(journal):
        data = read_journal(journal)
        key = f'{account_name(account)}:{question_id}'
        if data['uploads'].get(key, {}).get('status') != 'pending':
            raise InstagramError('only pending records can be reconciled')
        if status == 'uploaded' and not re.fullmatch(r'https://www\.instagram\.com/(?:reel|p)/[A-Za-z0-9_-]+/?', url or ''):
            raise InstagramError('supply the confirmed Instagram reel/post URL')
        if status not in ('uploaded', 'retry'):
            raise InstagramError('invalid reconciliation status')
        data['uploads'][key].update(status='uploaded' if status == 'uploaded' else 'ready',
                                    reconciled_at=datetime.now(timezone.utc).isoformat(), url=url)
        atomic_json(journal, data)


class BrowserPublisher:
    def __init__(self, context, account):
        self.context, self.account = context, account
        self.page = context.pages[0] if context.pages else context.new_page()

    def verify_account(self):
        # A logged-in navigation link to the expected profile must be visible.
        # No fallback to the username supplied by an artifact or hidden page state.
        if any(part in self.page.url for part in ('/accounts/', '/challenge', '/checkpoint')):
            raise InstagramError('manual Instagram login/verification required')
        profile = self.page.get_by_role('link', name=re.compile(r'^Profile(?:\s.*)?$'))
        profile.wait_for(state='visible', timeout=15000)
        if profile.get_attribute('href') != f'/{self.account}/':
            raise InstagramError('logged-in account does not match expected Instagram account')

    def share(self, item, checkpoint):
        page = self.page
        page.goto('https://www.instagram.com/', wait_until='domcontentloaded')
        self.verify_account()
        page.get_by_role('link', name='New post', exact=True).click(timeout=15000)
        page.locator('input[type="file"]').set_input_files(str(item['path']), timeout=15000)
        # Crop -> edit -> caption. Exact English labels, no speculative clicks.
        page.get_by_role('button', name='Next', exact=True).click(timeout=30000)
        page.get_by_role('button', name='Next', exact=True).click(timeout=30000)
        page.get_by_role('textbox', name='Write a caption...', exact=True).fill(item['caption'], timeout=15000)
        self.verify_account()
        checkpoint()
        page.get_by_role('button', name='Share', exact=True).click(timeout=15000)
        page.get_by_text(re.compile(r'^Your (?:reel|post) has been shared\.?$')).wait_for(timeout=120000)
        return 'confirmed'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'login', 'publish', 'reconcile'])
    parser.add_argument('--account', required=True, help='expected Instagram username')
    parser.add_argument('--state-dir', required=True, help='private absolute folder outside Git')
    parser.add_argument('--queue', type=Path)
    parser.add_argument('--enable-publish', action='store_true', help='explicitly enable public Share')
    parser.add_argument('--headless', action='store_true', help='publish using the previously verified server profile')
    parser.add_argument('--id')
    parser.add_argument('--status', choices=['uploaded', 'retry'])
    parser.add_argument('--url')
    args = parser.parse_args(argv)
    try:
        account = account_name(args.account)
        if not Path(args.state_dir).expanduser().is_absolute():
            raise InstagramError('state-dir must be an absolute path outside Git')
        state = private_state(args.state_dir)
        journal = state / 'uploads.json'
        if args.command == 'reconcile':
            if not args.id or not args.status:
                raise InstagramError('reconcile needs --id and --status')
            reconcile(journal, account, args.id, args.status, args.url)
            print('Reconciled; next publish uses the recorded resolution.')
            return 0
        if args.command in ('check', 'publish'):
            if not args.queue:
                raise InstagramError('queue directory is required')
            items = load_queue(args.queue)
            if not items:
                raise InstagramError('no Instagram queue artifacts found')
            if args.command == 'check':
                print(f'Validated {len(items)} video/caption pairs; no browser opened and nothing published.')
                return 0
            if not args.enable_publish:
                raise InstagramError('publishing disabled; add --enable-publish after setup verification')
        from playwright.sync_api import sync_playwright
        with locked(state / 'browser'):
            with sync_playwright() as pw:
                if args.command == 'login' and args.headless:
                    raise InstagramError('manual login needs a display; omit --headless')
                with pw.chromium.launch_persistent_context(str(state / 'profile'), headless=args.headless, locale='en-US') as context:
                    publisher = BrowserPublisher(context, account)
                    if args.command == 'login':
                        publisher.page.goto('https://www.instagram.com/accounts/login/', wait_until='domcontentloaded')
                        input('Complete login/OTP yourself in the browser, then press Enter here: ')
                        publisher.verify_account()
                        print('Expected account verified; local profile saved.')
                    else:
                        count = process(args.queue, journal, account, publisher.share)
                        print(f'Confirmed {count} new Instagram posts.')
        return 0
    except (InstagramError, ImportError) as exc:
        print(f'instagram: {exc}')
        return 1
    except Exception:
        print('instagram: browser stopped; inspect the account and journal before retrying')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
