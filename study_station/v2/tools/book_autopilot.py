"""
Book autopilot — writes/repairs book chapters one after another with bookgen (NVIDIA by default) and commits
each chapter that passes bookcheck. Runs until every chapter is done or it is stopped.

    cd study_station/v2
    NVIDIA_API_KEY=… python tools/book_autopilot.py --workers 3 [--reverse] [--dry-run]

Order: the books in books/QUEUE.txt (--reverse = last book first, so it never meets a writer working from the
front), chapters 01 → last inside a book. Several workers run on different chapters; git is serialized by a lock.

Safety:
- A chapter is committed only when `bookcheck` prints OK (chapter folder only, status stays "draft").
- A chapter changed on the remote in the last SKIP_HOURS by someone else is skipped (another writer has it).
- Failed chapters stay uncommitted and are listed in the state file; they are retried on the next pass.
- Stop: create the file named by --stop-file (default: <state dir>/STOP); the running chapters finish first.
State and log: --state-dir (default ~/.book_autopilot): log.txt, state.json.
"""
import argparse
import fcntl
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

V2 = Path(__file__).resolve().parents[1]
REPO = V2.parents[1]
sys.path.insert(0, str(V2))

from app import bookcheck  # noqa: E402

SKIP_HOURS = 6
MAX_REPAIR_ROUNDS = 2


class Pilot:
    def __init__(self, args):
        self.args = args
        self.state_dir = Path(args.state_dir).expanduser()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.stop_file = Path(args.stop_file).expanduser() if args.stop_file else self.state_dir / 'STOP'
        self.lock = threading.Lock()
        self.git_lock_path = self.state_dir / 'git.lock'
        self.state = self._load()
        self.claimed = set()

    # ------------------------------------------------------------ state + log
    def _load(self):
        p = self.state_dir / 'state.json'
        try:
            return json.loads(p.read_text())
        except (OSError, ValueError):
            return {'done': [], 'failed': {}, 'skipped': [], 'started': datetime.now().isoformat(timespec='seconds')}

    def save(self):
        p = self.state_dir / 'state.json'
        tmp = p.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=1))
        os.replace(tmp, p)

    def log(self, msg):
        line = f'{datetime.now():%m-%d %H:%M:%S} {msg}'
        with self.lock:
            with open(self.state_dir / 'log.txt', 'a', encoding='utf-8') as f:
                f.write(line + '\n')
        print(line, flush=True)

    # ------------------------------------------------------------ git (one at a time)
    def git(self, *cmd, check=True):
        return subprocess.run(['git', *cmd], cwd=REPO, capture_output=True, text=True, check=check)

    def with_git_lock(self, fn):
        with open(self.git_lock_path, 'w') as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            try:
                return fn()
            finally:
                fcntl.flock(lk, fcntl.LOCK_UN)

    def pull(self):
        def do():
            r = self.git('pull', '--rebase', '--autostash', '-q', 'origin', self.args.branch, check=False)
            if r.returncode:
                self.log(f'git pull failed: {r.stderr.strip()[:200]}')
        self.with_git_lock(do)

    def taken_by_other(self, ch):
        """Changed on the remote recently by a commit that is not ours → another writer owns it."""
        rel = ch.relative_to(REPO)
        r = self.git('log', f'--since={SKIP_HOURS} hours ago', '--format=%B%x00', '--', str(rel), check=False)
        return any(msg.strip() and 'bookgen autopilot' not in msg for msg in r.stdout.split('\x00'))

    def commit(self, ch, summary):
        rel = ch.relative_to(REPO)

        def do():
            self.git('add', '--', str(rel))
            staged = self.git('diff', '--cached', '--name-only').stdout.split()
            if not staged:
                return 'nothing to commit'
            outside = [p for p in staged if not p.startswith(str(rel) + '/')]
            if outside:
                self.git('reset', '-q', '--', *outside)
            msg = (f'Books: {summary} (draft, bookcheck OK, bookgen autopilot)\n\n'
                   'Written with bookgen (NVIDIA); practice keys confirmed by an independent re-solve.\n\n'
                   'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n'
                   'Claude-Session: https://claude.ai/code/session_01NkSvMYCcJQMogjnRs94E6r')
            self.git('commit', '-q', '-m', msg, '--', str(rel))
            for wait in (2, 4, 8, 16, None):
                r = self.git('push', '-q', 'origin', f'HEAD:{self.args.branch}', check=False)
                if r.returncode == 0:
                    return self.git('rev-parse', '--short', 'HEAD').stdout.strip()
                self.git('pull', '--rebase', '--autostash', '-q', 'origin', self.args.branch, check=False)
                if wait:
                    time.sleep(wait)
            return 'PUSH FAILED (committed locally)'
        return self.with_git_lock(do)

    # ------------------------------------------------------------ work
    def chapters(self):
        books = bookcheck.queue()
        if self.args.reverse:
            books = books[::-1]
        if self.args.only:
            books = [b for b in books if any(o in str(b) for o in self.args.only)]
        if self.args.exclude:
            books = [b for b in books if not any(o in str(b) for o in self.args.exclude)]
        for book in books:
            for ch in sorted(book.glob('Chapter_*')):
                if ch.is_dir() and not bookcheck.is_dynamic(ch):
                    yield ch

    def next_job(self):
        with self.lock:
            for ch in self.chapters():
                key = str(ch.relative_to(bookcheck.BOOKS_ROOT))
                if key in self.claimed or self.state['failed'].get(key, 0) >= self.args.max_fails:
                    continue
                if bookcheck.chapter_status(ch)[0] == 'OK':
                    continue
                if self.taken_by_other(ch):
                    if key not in self.state['skipped']:
                        self.state['skipped'].append(key)
                        self.save()
                        self.log(f'skip {key}: changed recently by another writer')
                    continue
                self.claimed.add(key)
                return ch, key
        return None

    def bookgen(self, ch, *extra):
        cmd = [sys.executable, '-m', 'app.bookgen', '--chapter', str(ch), *extra]
        env = {**os.environ, 'AI_DAILY_BOOK_SECTIONS': os.environ.get('AI_DAILY_BOOK_SECTIONS', '100000'),
               'AI_DAILY_LIMIT_TOTAL': os.environ.get('AI_DAILY_LIMIT_TOTAL', '1000000')}
        r = subprocess.run(cmd, cwd=V2, capture_output=True, text=True, env=env)
        lines = [l for l in (r.stdout + r.stderr).splitlines() if ' INFO ' not in l]
        bad = [l for l in lines if l.startswith(('FAILED', 'REJECTED', 'stopping'))]
        return lines, bad

    def work(self, ch, key):
        t0 = time.time()
        status, todo, problems = bookcheck.chapter_status(ch)
        self.log(f'START {key} ({status}: todo {len(todo)}, problems {len(problems)})')
        if self.args.dry_run:
            return
        if todo:
            _, bad = self.bookgen(ch)
            for b in bad[:6]:
                self.log(f'  {key}: {b[:160]}')
            if any('auth' in b or 'not_configured' in b for b in bad):
                self.log('NVIDIA key rejected — stopping')
                self.stop_file.touch()
                return
        for _ in range(MAX_REPAIR_ROUNDS):
            status, todo, problems = bookcheck.chapter_status(ch)
            if status != 'FIX':
                break
            _, bad = self.bookgen(ch, '--repair')
            for b in bad[:6]:
                self.log(f'  {key} repair: {b[:160]}')
        status, todo, problems = bookcheck.chapter_status(ch)
        mins = (time.time() - t0) / 60
        if status == 'OK':
            parts = key.split('/')
            summary = f'{parts[0].replace("_Level", "")} {parts[1]} {parts[-1].replace("_", " ")}'
            sha = self.commit(ch, summary)
            with self.lock:
                self.state['done'].append(key)
                self.state['failed'].pop(key, None)
                self.save()
            self.log(f'DONE {key} in {mins:.0f} min → {sha}')
        else:
            with self.lock:
                self.state['failed'][key] = self.state['failed'].get(key, 0) + 1
                self.save()
            self.log(f'NOT OK {key} after {mins:.0f} min: todo {todo[:4]} problems {[p[:60] for p in problems[:4]]}')

    def worker(self, n):
        while not self.stop_file.exists():
            job = self.next_job()
            if job is None:
                self.log(f'worker {n}: nothing left')
                return
            ch, key = job
            try:
                self.work(ch, key)
            except Exception as e:                                   # keep the other chapters going
                self.log(f'ERROR {key}: {type(e).__name__}: {str(e)[:200]}')
            finally:
                if not self.args.dry_run:                            # dry run: list each chapter once
                    with self.lock:
                        self.claimed.discard(key)
        self.log(f'worker {n}: stop file found — stopping')

    def run(self):
        if not os.environ.get('NVIDIA_API_KEY') and not self.args.dry_run:
            print('NVIDIA_API_KEY is not set', file=sys.stderr)
            return 2
        self.stop_file.unlink(missing_ok=True)
        self.pull()
        self.log(f'autopilot start: {self.args.workers} workers, reverse={self.args.reverse}')
        threads = [threading.Thread(target=self.worker, args=(i,), daemon=True) for i in range(self.args.workers)]
        for i, t in enumerate(threads):
            t.start()
            time.sleep(5 if i < len(threads) - 1 else 0)
        while any(t.is_alive() for t in threads):
            time.sleep(600)
            if not self.args.dry_run and not self.stop_file.exists():
                self.pull()                                          # pick up other writers' chapters
        self.log(f'autopilot end: done {len(self.state["done"])}, failed {len(self.state["failed"])}')
        return 0


def main():
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('--workers', type=int, default=3)
    p.add_argument('--reverse', action='store_true', help='last book in QUEUE.txt first')
    p.add_argument('--only', nargs='*', help='only books whose path contains one of these strings')
    p.add_argument('--exclude', nargs='*', help='skip books whose path contains one of these strings')
    p.add_argument('--branch', default='claude/elegant-rubin-sgov1q')
    p.add_argument('--state-dir', default='~/.book_autopilot')
    p.add_argument('--stop-file')
    p.add_argument('--max-fails', type=int, default=2, help='give a chapter up after this many failed passes')
    p.add_argument('--dry-run', action='store_true')
    return Pilot(p.parse_args()).run()


if __name__ == '__main__':
    sys.exit(main())
