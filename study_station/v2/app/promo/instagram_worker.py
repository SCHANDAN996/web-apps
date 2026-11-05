"""Pull trusted GitHub Shorts artifacts; publish using a persistent server browser.

Instagram has no API integration here. No password, OTP, stealth or challenge
handling. All network/browser work is opt-in; init/status are local-only.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import zipfile

from . import instagram as ig

REPOSITORY = 'SCHANDAN996/web-apps'
BRANCH = 'claude/elegant-rubin-sgov1q'
MAX_ARCHIVE = 200 * 1024 * 1024


def now():
    return datetime.now(timezone.utc).isoformat()


def trusted(run):
    return (run.get('head_repository', {}).get('full_name') == REPOSITORY
            and run.get('path') == '.github/workflows/promo-shorts.yml'
            and run.get('head_branch') in (BRANCH, 'main')
            and run.get('event') in ('schedule', 'workflow_dispatch')
            and run.get('status') == 'completed' and run.get('conclusion') == 'success')


def gh_json(endpoint):
    try:
        result = subprocess.run(['gh', 'api', endpoint], check=True, capture_output=True, timeout=60)
        return json.loads(result.stdout)
    except (subprocess.SubprocessError, OSError, ValueError):
        raise ig.InstagramError('GitHub request failed; check gh authentication and Actions read permission') from None


def discover(since):
    # GitHub's created filter excludes historical runs even if they finish later.
    # Fetch all pages, bounded; do not silently lose a backlog above the bound.
    since = max(datetime.fromisoformat(since), datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    runs = []
    for page in range(1, 11):
        payload = gh_json(f'repos/{REPOSITORY}/actions/workflows/promo-shorts.yml/runs'
                          f'?status=success&created=%3E%3D{since[:10]}&per_page=100&page={page}')
        batch = payload['workflow_runs']
        runs.extend(r for r in batch if trusted(r) and
                    datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')) >= datetime.fromisoformat(since))
        if len(batch) < 100:
            return sorted(runs, key=lambda r: (r['created_at'], r['id']))
    raise ig.InstagramError('too many workflow runs; inspect backlog before continuing')


def unpack(archive_path, folder):
    folder = Path(folder)
    if folder.exists():
        raise ig.InstagramError('artifact destination already exists; inspect before retry')
    if Path(archive_path).stat().st_size > MAX_ARCHIVE:
        raise ig.InstagramError('artifact too large')
    folder.mkdir(parents=True, mode=0o700)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            if len(entries) > 200 or sum(e.file_size for e in entries) > MAX_ARCHIVE:
                raise ig.InstagramError('artifact exceeds extraction limits')
            names = set()
            for entry in entries:
                name = entry.filename
                if '/' in name or '\\' in name or name in ('.', '..') or name in names:
                    raise ig.InstagramError('artifact must contain unique plain filenames')
                names.add(name)
                # Never extract executable source. ZIP symlinks become ordinary bytes.
                if name.endswith(('.mp4', '.instagram.json')):
                    with archive.open(entry) as source, (folder / name).open('xb') as target:
                        shutil.copyfileobj(source, target)
        if not ig.load_queue(folder):
            raise ig.InstagramError('no Instagram manifests; use an updated renderer run')
    except Exception:
        shutil.rmtree(folder)
        raise


def validate_source(folder):
    """Require each rendered revision to belong to the current canonical history.

    A main-scheduled run's head SHA describes the workflow, not checked-out code.
    YouTube's durable checkpoints may advance HEAD between videos, so validate
    each distinct manifest SHA rather than assuming one SHA for the whole run.
    """
    checked = set()
    for item in ig.load_queue(folder):
        revision = item.get('source_sha')
        if item.get('source_ref') != BRANCH or not isinstance(revision, str) or not re.fullmatch('[a-f0-9]{40}', revision):
            raise ig.InstagramError('artifact was not rendered from the expected source ref/revision')
        if revision not in checked:
            result = gh_json(f'repos/{REPOSITORY}/compare/{revision}...{BRANCH}')
            if result.get('status') not in ('ahead', 'identical'):
                raise ig.InstagramError('rendered revision is not in canonical source history')
            checked.add(revision)


def download(run, folder):
    artifacts = gh_json(f'repos/{REPOSITORY}/actions/runs/{int(run["id"])}/artifacts')['artifacts']
    expected = f'shorts-{int(run["run_number"])}'
    matches = [a for a in artifacts if a.get('name') == expected and not a.get('expired')]
    # The scheduler retries with --once. Successful no-output runs are normal.
    if not artifacts:
        return False
    if len(matches) != 1 or not 0 < matches[0].get('size_in_bytes', 0) <= MAX_ARCHIVE:
        raise ig.InstagramError('no unique unexpired Shorts artifact within size limit')
    endpoint = f'repos/{REPOSITORY}/actions/artifacts/{int(matches[0]["id"])}/zip'
    # Stream stdout with a hard byte cap; never buffer a whole ZIP in RAM.
    with tempfile.TemporaryDirectory(dir=Path(folder).parent) as tmp:
        archive = Path(tmp) / 'artifact.zip'
        with archive.open('wb') as stream:
            proc = subprocess.Popen(['gh', 'api', endpoint], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            import threading
            timer = threading.Timer(180, proc.kill)
            timer.start()
            try:
                size = 0
                while chunk := proc.stdout.read(65536):
                    size += len(chunk)
                    if size > MAX_ARCHIVE:
                        raise ig.InstagramError('artifact download exceeded byte limit')
                    stream.write(chunk)
                if proc.wait(timeout=5):
                    raise ig.InstagramError('artifact download failed')
            finally:
                timer.cancel()
                if proc.poll() is None:
                    proc.kill()
                proc.wait()
                proc.stdout.close()
        unpack(archive, folder)
        try:
            validate_source(folder)
        except Exception:
            shutil.rmtree(folder)
            raise
    return True


def digest(folder):
    items = ig.load_queue(folder)
    value = [{k: item.get(k) for k in ('id', 'sha256', 'caption', 'video', 'source_ref', 'source_sha')} for item in items]
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def ledger(state, account):
    path = state / 'batches.json'
    if not path.exists():
        raise ig.InstagramError('run init first; historical videos are never imported automatically')
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if data['account'] != account or not isinstance(data['runs'], dict):
            raise ValueError()
        datetime.fromisoformat(data['since'])
        return data
    except (ValueError, KeyError, TypeError):
        raise ig.InstagramError('invalid batch journal or different account; restore private state') from None


def save(state, data):
    ig.atomic_json(state / 'batches.json', data)


def sync(state, data):
    for run in discover(data['since']):
        rid = str(int(run['id']))
        if rid in data['runs']:
            continue
        root = state / 'queue'
        root.mkdir(exist_ok=True, mode=0o700)
        folder = root / rid
        # A crash during download cannot become a ready batch.
        if folder.exists():
            raise ig.InstagramError('untracked artifact directory; inspect and remove it before retry')
        if not download(run, folder):
            data['runs'][rid] = {'status': 'no-output', 'at': now()}
            save(state, data)
            continue
        data['runs'][rid] = {'status': 'ready', 'digest': digest(folder), 'at': now()}
        save(state, data)


def cleanup(state, data):
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    for rid, record in data['runs'].items():
        if record['status'] == 'done' and datetime.fromisoformat(record['at']) < cutoff:
            folder = state / 'queue' / str(int(rid))
            if folder.exists():
                shutil.rmtree(folder)
    # Upload journal and batch records are never removed.


def cycle(state, data, publisher, only=None):
    # Any ambiguous/blocked batch halts newer work until an operator resolves it.
    for rid, record in data['runs'].items():
        if record['status'] not in ('ready', 'done', 'no-output'):
            raise ig.InstagramError(f'batch {rid} requires manual resume; inspect Instagram and upload journal')
    for rid, record in data['runs'].items():
        if record['status'] != 'ready' or (only and rid != only):
            continue
        folder = state / 'queue' / str(int(rid))
        if digest(folder) != record['digest']:
            raise ig.InstagramError('queued media changed; publishing blocked')
        record.update(status='publishing', at=now())
        save(state, data)
        try:
            count = publisher(folder)
        except Exception:
            record.update(status='blocked', at=now())
            save(state, data)
            raise ig.InstagramError(f'batch {rid} stopped; inspect journal before resume') from None
        record.update(status='done', at=now(), confirmed_count=count)
        save(state, data)
    cleanup(state, data)


def resume(state, data, rid):
    record = data['runs'].get(rid)
    if not record or record['status'] not in ('blocked', 'publishing'):
        raise ig.InstagramError('resume requires a blocked/interrupted batch')
    folder = state / 'queue' / str(int(rid))
    if digest(folder) != record['digest']:
        raise ig.InstagramError('batch changed; cannot resume')
    journal = ig.read_journal(state / 'uploads.json')
    for item in ig.load_queue(folder):
        status = journal['uploads'].get(f'{data["account"]}:{item["id"]}', {}).get('status')
        if status not in (None, 'ready', 'uploaded'):
            raise ig.InstagramError('reconcile pending uploads against actual Instagram posts first')
    record.update(status='ready', at=now())
    save(state, data)


def browser_publish(state, account, folder):
    from playwright.sync_api import sync_playwright
    with ig.locked(state / 'browser'):
        with sync_playwright() as pw:
            with pw.chromium.launch_persistent_context(str(state / 'profile'), headless=True, locale='en-US') as context:
                publisher = ig.BrowserPublisher(context, account)
                return ig.process(folder, state / 'uploads.json', account, publisher.share)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'sync', 'run', 'status', 'resume'])
    parser.add_argument('--state-dir', required=True)
    parser.add_argument('--account', required=True)
    parser.add_argument('--enable-publish', action='store_true')
    parser.add_argument('--run-id', type=int, help='one ready batch for pilot, or batch to resume')
    args = parser.parse_args(argv)
    try:
        if not Path(args.state_dir).expanduser().is_absolute():
            raise ig.InstagramError('state-dir must be absolute')
        state, account = ig.private_state(args.state_dir), ig.account_name(args.account)
        with ig.locked(state / 'worker'):
            if args.command == 'init':
                if (state / 'batches.json').exists():
                    raise ig.InstagramError('already initialized; keep existing journal')
                save(state, {'account': account, 'since': now(), 'runs': {}})
                print('Initialized; only new trusted workflow runs will be queued. Nothing published.')
                return 0
            data = ledger(state, account)
            if args.command == 'status':
                print(json.dumps({rid: r['status'] for rid, r in data['runs'].items()}))
            elif args.command == 'resume':
                if not args.run_id:
                    raise ig.InstagramError('resume requires --run-id')
                resume(state, data, str(args.run_id))
                print('Batch ready; no post published by resume.')
            else:
                if args.command == 'run' and not args.enable_publish:
                    raise ig.InstagramError('publishing disabled; verify live UI before --enable-publish')
                sync(state, data)
                if args.command == 'run':
                    cycle(state, data, lambda folder: browser_publish(state, account, folder),
                          str(args.run_id) if args.run_id else None)
                print(f'{args.command}: completed')
        return 0
    except ig.InstagramError as exc:
        print(f'instagram-worker: {exc}')
        return 1
    except Exception:
        print('instagram-worker: stopped; check configuration, private journal and login; no automatic retry of uncertain Share')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
