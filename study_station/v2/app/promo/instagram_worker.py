"""Persistent server companion: trusted Shorts artifacts -> private Telegram approval -> Instagram.

Run only after configuring a dedicated approval bot and verifying the browser UI.
Never renders videos, executes downloaded code, or handles Instagram passwords.
"""
import argparse
from datetime import datetime, timezone
import io
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import zipfile

import httpx

from . import instagram as ig

REPOSITORY = 'SCHANDAN996/web-apps'
BRANCH = 'claude/elegant-rubin-sgov1q'
MAX_ARCHIVE = 200 * 1024 * 1024


def trusted(run):
    return (run.get('head_repository', {}).get('full_name') == REPOSITORY
            and run.get('path') == '.github/workflows/promo-shorts.yml'
            and run.get('head_branch') == BRANCH
            and run.get('event') in ('schedule', 'workflow_dispatch')
            and run.get('status') == 'completed' and run.get('conclusion') == 'success')


def gh_json(endpoint):
    result = subprocess.run(['gh', 'api', endpoint], check=True, capture_output=True)
    return json.loads(result.stdout)


def discover():
    payload = gh_json(f'repos/{REPOSITORY}/actions/workflows/promo-shorts.yml/runs?status=success&per_page=20')
    return [r for r in reversed(payload['workflow_runs']) if trusted(r)]


def download(run, folder):
    artifacts = gh_json(f'repos/{REPOSITORY}/actions/runs/{int(run["id"])}/artifacts')['artifacts']
    expected = f'shorts-{int(run["run_number"])}'
    matches = [a for a in artifacts if a.get('name') == expected and not a.get('expired')]
    if len(matches) != 1:
        raise ig.InstagramError('trusted run has no unique unexpired Shorts artifact')
    artifact = matches[0]
    if int(artifact.get('size_in_bytes', 0)) > MAX_ARCHIVE:
        raise ig.InstagramError('artifact too large')
    result = subprocess.run(['gh', 'api', f'repos/{REPOSITORY}/actions/artifacts/{int(artifact["id"])}/zip'],
                            check=True, capture_output=True)
    unpack(result.stdout, folder)


def unpack(raw, folder):
    if len(raw) > MAX_ARCHIVE:
        raise ig.InstagramError('artifact too large')
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) > 200 or sum(e.file_size for e in entries) > MAX_ARCHIVE:
            raise ig.InstagramError('artifact exceeds extraction limits')
        names = set()
        for entry in entries:
            name = entry.filename
            if '/' in name or '\\' in name or name in ('.', '..') or name in names:
                raise ig.InstagramError('artifact must contain unique plain filenames')
            names.add(name)
            # Ignore frames, metadata and thumbnails. Never execute or extract scripts.
            if not (name.endswith('.mp4') or name.endswith('.instagram.json')):
                continue
            target = folder / name
            if target.is_symlink():
                raise ig.InstagramError('artifact destination cannot be a symlink')
            target.write_bytes(archive.read(entry))
    if not ig.load_queue(folder):
        raise ig.InstagramError('no Instagram manifests; run updated renderer first')


class ApprovalBot:
    def __init__(self, token, chat_id):
        if not token or not str(chat_id).isdigit():
            raise ig.InstagramError('dedicated approval bot token and private owner chat ID required')
        self.token, self.chat_id = token, str(chat_id)

    def call(self, method, **payload):
        # Never include HTTP exception URLs: Telegram URLs contain the bot token.
        try:
            response = httpx.post(f'https://api.telegram.org/bot{self.token}/{method}', json=payload, timeout=35)
            data = response.json()
            if response.status_code != 200 or not data.get('ok'):
                raise ig.InstagramError('approval bot request failed; check bot configuration')
            return data['result']
        except (httpx.HTTPError, ValueError) as exc:
            raise ig.InstagramError('approval bot unavailable; no publishing attempted') from None

    def verify(self):
        if self.call('getWebhookInfo').get('url'):
            raise ig.InstagramError('approval bot has a webhook; use a separate dedicated bot')
        chat = self.call('getChat', chat_id=self.chat_id)
        if chat.get('type') != 'private' or str(chat.get('id')) != self.chat_id:
            raise ig.InstagramError('approval destination must be the owner private chat')

    def request(self, run_id, record, account):
        return self.call('sendMessage', chat_id=self.chat_id,
                         text=(f'StudyStation Instagram @{account}\nबैच {run_id}: '
                               f'{record["count"]} वीडियो। ऊपर सभी वीडियो और पूरे caption देखें। '
                               'मंज़ूरी देने पर इस बैच के सभी वीडियो सार्वजनिक पोस्ट होंगे।'),
                         reply_markup={'inline_keyboard': [[
                             {'text': 'मंज़ूर — सार्वजनिक पोस्ट करें', 'callback_data': f'ig:{run_id}:{record["nonce"]}:yes'},
                             {'text': 'रद्द करें', 'callback_data': f'ig:{run_id}:{record["nonce"]}:no'},
                         ]]})

    def preview(self, folder):
        for item in ig.load_queue(folder):
            self.call('sendMessage', chat_id=self.chat_id, text=f'पूरा Instagram caption:\n\n{item["caption"]}')
            try:
                with item['path'].open('rb') as stream:
                    response = httpx.post(f'https://api.telegram.org/bot{self.token}/sendVideo',
                                          data={'chat_id': self.chat_id, 'caption': item['caption'][:1024]},
                                          files={'video': (item['path'].name, stream, 'video/mp4')}, timeout=120)
                if response.status_code != 200 or not response.json().get('ok'):
                    raise ig.InstagramError('Telegram preview failed; approval withheld')
            except (OSError, httpx.HTTPError, ValueError):
                raise ig.InstagramError('Telegram preview failed; approval withheld') from None


def apply_callback(update, runs, owner):
    query = update.get('callback_query', {})
    message = query.get('message', {})
    chat = message.get('chat', {})
    if (chat.get('type') != 'private' or str(chat.get('id')) != str(owner)
            or str(query.get('from', {}).get('id')) != str(owner)):
        return False
    parts = query.get('data', '').split(':')
    if len(parts) != 4 or parts[0] != 'ig' or parts[3] not in ('yes', 'no'):
        return False
    record = runs.get(parts[1])
    if (not record or record.get('status') != 'waiting'
            or not secrets.compare_digest(record.get('nonce', ''), parts[2])
            or record.get('message_id') != message.get('message_id')):
        return False
    record['status'] = 'approved' if parts[3] == 'yes' else 'rejected'
    record['decision_at'] = datetime.now(timezone.utc).isoformat()
    return True


def queue_digest(folder):
    items = ig.load_queue(folder)
    bound = [{'id': i['id'], 'sha256': i['sha256'], 'caption': i['caption'], 'video': i['video']} for i in items]
    return hashlib.sha256(json.dumps(bound, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def cycle(state, bot, account, publisher):
    ledger = state / 'batches.json'
    if ledger.exists():
        data = json.loads(ledger.read_text(encoding='utf-8'))
        if data.get('account') != account:
            raise ig.InstagramError('worker state belongs to a different Instagram account')
    else:
        data = {'account': account, 'runs': {}, 'offset': 0}
    # Do not publish recent historical runs on first start: discovery establishes a baseline.
    if not data.get('initialized'):
        for run in discover():
            data['runs'][str(run['id'])] = {'status': 'baseline'}
        data['initialized'] = True
        ig.atomic_json(ledger, data)
    for run in discover():
        rid = str(run['id'])
        if rid in data['runs']:
            continue
        folder = state / 'queue' / rid
        download(run, folder)
        count = len(ig.load_queue(folder))
        record = {'status': 'preparing', 'count': count, 'nonce': secrets.token_hex(8), 'digest': queue_digest(folder)}
        data['runs'][rid] = record
        ig.atomic_json(ledger, data)
        bot.preview(folder)
        message = bot.request(rid, record, account)
        record.update(status='waiting', message_id=message['message_id'])
        ig.atomic_json(ledger, data)
    for update in bot.call('getUpdates', offset=data['offset'], timeout=0, allowed_updates=['callback_query']):
        apply_callback(update, data['runs'], bot.chat_id)
        data['offset'] = max(data['offset'], int(update['update_id']) + 1)
        ig.atomic_json(ledger, data)
    for rid, record in data['runs'].items():
        if record['status'] != 'approved':
            continue
        record['status'] = 'publishing'
        ig.atomic_json(ledger, data)
        try:
            if queue_digest(state / 'queue' / rid) != record['digest']:
                raise ig.InstagramError('approved batch changed; publishing blocked')
            count = publisher(state / 'queue' / rid)
        except Exception:
            record['status'] = 'blocked'
            ig.atomic_json(ledger, data)
            bot.call('sendMessage', chat_id=bot.chat_id,
                     text=f'Instagram बैच {rid} रुक गया। दोबारा चलाने से पहले Instagram और upload journal जाँचें।')
            raise ig.InstagramError('upload blocked; manual reconciliation required') from None
        record.update(status='done', confirmed_count=count)
        ig.atomic_json(ledger, data)
        bot.call('sendMessage', chat_id=bot.chat_id, text=f'Instagram बैच {rid}: {count} नई पोस्ट की पुष्टि हुई।')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', required=True)
    parser.add_argument('--account', required=True)
    parser.add_argument('--enable-publish', action='store_true')
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args(argv)
    try:
        if not args.enable_publish:
            raise ig.InstagramError('worker disabled; verify setup before --enable-publish')
        if not Path(args.state_dir).expanduser().is_absolute():
            raise ig.InstagramError('state-dir must be absolute')
        state, account = ig.private_state(args.state_dir), ig.account_name(args.account)
        (state / 'tmp').mkdir(mode=0o700, exist_ok=True)
        os.environ['TMPDIR'] = str(state / 'tmp')
        # tempfile caches its initial choice; force the worker's private writable temp root.
        import tempfile
        tempfile.tempdir = str(state / 'tmp')
        bot = ApprovalBot(os.environ.get('IG_APPROVAL_BOT_TOKEN'), os.environ.get('IG_APPROVAL_CHAT_ID'))
        bot.verify()

        def publish(folder):
            # Browser remains on the same server/profile used for manual first login.
            from playwright.sync_api import sync_playwright
            with ig.locked(state / 'browser'):
                with sync_playwright() as pw:
                    with pw.chromium.launch_persistent_context(str(state / 'profile'), headless=False, locale='en-US') as context:
                        browser = ig.BrowserPublisher(context, account)
                        return ig.process(folder, state / 'uploads.json', account, browser.share)

        with ig.locked(state / 'worker'):
            while True:
                cycle(state, bot, account, publish)
                if args.once:
                    return 0
                time.sleep(30)
    except Exception:
        # Suppress raw exception messages: subprocess/HTTP errors may contain credentials.
        print('Instagram worker stopped. Check private state/configuration and reconcile any pending upload before restarting.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
