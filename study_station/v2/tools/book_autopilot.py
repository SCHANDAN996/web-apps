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
Live status for the owner: books/AUTOPILOT_STATUS.md (what each worker is doing, progress per book, recent
activity) — committed with every chapter and every STATUS_MINUTES as a heartbeat; readable on GitHub.
"""
import argparse
import fcntl
import json
import os
import subprocess
import sys
import threading
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

V2 = Path(__file__).resolve().parents[1]
REPO = V2.parents[1]
sys.path.insert(0, str(V2))

from app import bookcheck  # noqa: E402

SKIP_HOURS = 6
STATUS_MINUTES = 15
IST = ZoneInfo('Asia/Kolkata')
STATUS_FILE = bookcheck.BOOKS_ROOT / 'AUTOPILOT_STATUS.md'
STEP_HI = {'write': '✍️ लिख रहा है', 'repair': '🔧 सुधार रहा है', 'review': '🔎 review हो रहा है',
           'commit': '📤 push हो रहा है', 'pick': '⏳ अगला अध्याय चुन रहा है'}
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
        self.current = {}                       # thread name -> {key, step, since}
        self.started = datetime.now(IST)

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
        line = f'{datetime.now(IST):%d-%m %H:%M:%S} {msg}'
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

    def uncommitted(self, ch):
        return bool(self.git('status', '--porcelain', '--', str(ch.relative_to(REPO)), check=False).stdout.strip())

    def commit(self, ch, summary):
        rel = ch.relative_to(REPO)

        def do():
            self.write_status()
            self.git('add', '--', str(rel), str(STATUS_FILE.relative_to(REPO)))
            staged = self.git('diff', '--cached', '--name-only').stdout.split()
            if not staged:
                return 'nothing to commit'
            status_rel = str(STATUS_FILE.relative_to(REPO))
            outside = [p for p in staged if not p.startswith(str(rel) + '/') and p != status_rel]
            if outside:
                self.git('reset', '-q', '--', *outside)
            msg = (f'Books: {summary} (draft, bookcheck OK, bookgen autopilot)\n\n'
                   'Written with bookgen (NVIDIA); practice keys confirmed by an independent re-solve;\n'
                   'every section read by an independent reviewer model and corrected before publishing.\n\n'
                   'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n'
                   'Claude-Session: https://claude.ai/code/session_01NkSvMYCcJQMogjnRs94E6r')
            self.git('commit', '-q', '-m', msg, '--', str(rel), status_rel)
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
                if bookcheck.chapter_status(ch)[0] == 'OK' and not self.uncommitted(ch):
                    continue                                 # done and published (OK + changes → review, commit)
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
        env = {**os.environ, 'BOOKGEN_REVIEW_CACHE': str(self.state_dir / 'reviewed.json'),
               'AI_DAILY_BOOK_SECTIONS': os.environ.get('AI_DAILY_BOOK_SECTIONS', '100000'),
               'AI_DAILY_LIMIT_TOTAL': os.environ.get('AI_DAILY_LIMIT_TOTAL', '1000000')}
        short = ch.name.split('_', 2)[-1] if '_' in ch.name else ch.name
        lines = []
        with subprocess.Popen(cmd, cwd=V2, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                              env={**env, 'PYTHONUNBUFFERED': '1'}) as proc:
            for line in proc.stdout:
                line = line.rstrip()
                if not line or ' INFO ' in line or ' WARNING ' in line or line.startswith(('---', 'TODO ', 'FIX ', 'OK ')):
                    continue
                if line.lstrip().startswith(('todo ', 'problem ')):
                    continue
                lines.append(line)
                self.log(f'  [{short}] {line.strip()[:150]}')
        bad = [l for l in lines if l.startswith(('FAILED', 'REJECTED', 'stopping', 'Traceback'))]
        if proc.returncode and not bad and '--review' in extra:
            bad = [f'bookgen exit code {proc.returncode}']              # never publish an unfinished review
        return lines, bad

    def step(self, key, step):
        with self.lock:
            self.current[threading.current_thread().name] = {'key': key, 'step': step, 'since': datetime.now(IST)}

    def work(self, ch, key):
        t0 = time.time()
        status, todo, problems = bookcheck.chapter_status(ch)
        self.log(f'START {key} ({status}: todo {len(todo)}, problems {len(problems)})')
        if self.args.dry_run:
            return
        if todo:
            self.step(key, 'write')
            _, bad = self.bookgen(ch)
            if any('auth' in b or 'not_configured' in b for b in bad):
                self.log('NVIDIA key rejected — stopping')
                self.stop_file.touch()
                return
        for _ in range(MAX_REPAIR_ROUNDS):
            status, todo, problems = bookcheck.chapter_status(ch)
            if status != 'FIX':
                break
            self.step(key, 'repair')
            self.bookgen(ch, '--repair')
        status, todo, problems = bookcheck.chapter_status(ch)
        if status == 'OK':                                           # publish gate: independent review first
            self.step(key, 'review')
            lines, bad = self.bookgen(ch, '--review')
            status, todo, problems = bookcheck.chapter_status(ch)
            if bad:
                status = 'REVIEW'
        mins = (time.time() - t0) / 60
        if status == 'OK':
            parts = key.split('/')
            summary = f'{parts[0].replace("_Level", "")} {parts[1]} {parts[-1].replace("_", " ")}'
            self.step(key, 'commit')
            with self.lock:
                self.state.setdefault('done_at', {})[key] = datetime.now(IST).strftime('%d-%m %H:%M')
                self.state['done'].append(key)
            sha = self.commit(ch, summary)
            with self.lock:
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
            self.step(key, 'pick')
            try:
                self.work(ch, key)
            except Exception as e:                                   # keep the other chapters going
                self.log(f'ERROR {key}: {type(e).__name__}: {str(e)[:200]}')
            finally:
                with self.lock:
                    self.current.pop(threading.current_thread().name, None)
                    if not self.args.dry_run:                        # dry run: list each chapter once
                        self.claimed.discard(key)
        self.log(f'worker {n}: stop file found — stopping')

    def run(self):
        if not os.environ.get('NVIDIA_API_KEY') and not self.args.dry_run:
            print('NVIDIA_API_KEY is not set', file=sys.stderr)
            return 2
        self.stop_file.unlink(missing_ok=True)
        self.pull()
        self.log(f'autopilot start: {self.args.workers} workers, reverse={self.args.reverse}')
        threads = [threading.Thread(target=self.worker, args=(i,), daemon=True, name=f'W{i + 1}')
                   for i in range(self.args.workers)]
        for i, t in enumerate(threads):
            t.start()
            time.sleep(5 if i < len(threads) - 1 else 0)
        if not self.args.dry_run:
            time.sleep(30)
            self.heartbeat()
        while any(t.is_alive() for t in threads):
            time.sleep(STATUS_MINUTES * 60)
            if not self.args.dry_run and not self.stop_file.exists():
                self.pull()                                          # pick up other writers' chapters
                self.heartbeat()
        self.log(f'autopilot end: done {len(self.state["done"])}, failed {len(self.state["failed"])}')
        if not self.args.dry_run:
            self.heartbeat()
        return 0

    # ------------------------------------------------------------ live status page
    def write_status(self):
        now = datetime.now(IST)
        with self.lock:
            current = sorted(self.current.items())
            done_at = dict(self.state.get('done_at', {}))
            failed = dict(self.state['failed'])
        out = ['# 📚 Book Autopilot — लाइव स्थिति', '',
               f'**आख़िरी update:** {now:%d-%m-%Y %I:%M %p} IST · हर {STATUS_MINUTES} मिनट और हर पूरे अध्याय पर अपने-आप '
               f'update होता है · autopilot शुरू: {self.started:%d-%m %I:%M %p}',
               '', '> NVIDIA (Kimi-K3) लिखता है → दूसरा model हर सवाल ख़ुद हल करके उत्तर जाँचता है → `bookcheck` → '
               'reviewer model हर section पढ़कर गलती सुधरवाता है → तभी push।', '',
               '## ⚙️ अभी क्या चल रहा है', '']
        if current and not self.stop_file.exists():
            out += ['| worker | अध्याय | काम | कब से |', '|---|---|---|---|']
            for name, c in current:
                mins = int((now - c['since']).total_seconds() // 60)
                out.append(f"| {name} | {c['key'].split('/')[-1].replace('_', ' ')} "
                           f"({c['key'].split('/')[0].replace('_Level', '')} {c['key'].split('/')[1]}) | "
                           f"{STEP_HI.get(c['step'], c['step'])} | {mins} मिनट |")
        else:
            out.append('⏸️ अभी कोई worker नहीं चल रहा (रुका हुआ या सब पूरा)।')
        out += ['', '## 📊 हर किताब की प्रगति', '', '| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |', '|---|---|---|---|']
        total = Counter()
        for book in bookcheck.queue():
            c = Counter()
            for ch in sorted(book.glob('Chapter_*')):
                if ch.is_dir() and not bookcheck.is_dynamic(ch):
                    c[bookcheck.chapter_status(ch)[0]] += 1
            total.update(c)
            name = str(book.relative_to(bookcheck.BOOKS_ROOT)).replace('_Level', '').split('/')
            out.append(f"| {name[0]} {name[1]} | {c['OK']} | {c['FIX']} | {c['TODO']} |")
        out.append(f"| **कुल** | **{total['OK']}** | **{total['FIX']}** | **{total['TODO']}** |")
        recent = sorted(done_at.items(), key=lambda kv: kv[1], reverse=True)[:15]
        out += ['', '## ✅ autopilot से हाल में पूरे हुए', '']
        out += [f"- {t} — {k.split('/')[0].replace('_Level', '')} {k.split('/')[1]} · {k.split('/')[-1].replace('_', ' ')}"
                for k, t in recent] or ['- अभी कोई नहीं']
        if failed:
            out += ['', '## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)', '']
            out += [f"- {k.split('/')[-1].replace('_', ' ')} ({k.split('/')[1]}) — {n} बार" for k, n in failed.items()]
        try:
            tail = (self.state_dir / 'log.txt').read_text(encoding='utf-8').splitlines()[-40:]
        except OSError:
            tail = []
        out += ['', '## 📜 हाल की गतिविधि (नया सबसे नीचे)', '', '```', *tail, '```', '']
        tmp = STATUS_FILE.with_suffix('.tmp')
        tmp.write_text('\n'.join(out), encoding='utf-8')
        os.replace(tmp, STATUS_FILE)

    def heartbeat(self):
        def do():
            self.write_status()
            rel = str(STATUS_FILE.relative_to(REPO))
            self.git('add', '--', rel)
            if not self.git('diff', '--cached', '--name-only', '--', rel).stdout.strip():
                return
            self.git('commit', '-q', '-m', 'Books autopilot: live status update\n\n'
                     'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n'
                     'Claude-Session: https://claude.ai/code/session_01NkSvMYCcJQMogjnRs94E6r', '--', rel)
            for wait in (2, 4, 8, None):
                if self.git('push', '-q', 'origin', f'HEAD:{self.args.branch}', check=False).returncode == 0:
                    return
                self.git('pull', '--rebase', '--autostash', '-q', 'origin', self.args.branch, check=False)
                if wait:
                    time.sleep(wait)
        try:
            self.with_git_lock(do)
        except Exception as e:
            self.log(f'status update failed: {type(e).__name__}: {str(e)[:150]}')


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
