"""Remove only Study Station recruitment cron tasks; preserve all other entries.

Run as the server operator: python deploy/retire_jobs.py --apply
"""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess


TASK = re.compile(r'python(?:3)?\s+-m\s+app\.jobs\s+(run|cleanup|digest)(?:\s|$)')


def retire_lines(text):
    lines = text.splitlines(keepends=True)
    kept = [line for line in lines if line.lstrip().startswith('#') or not TASK.search(line)]
    return ''.join(kept), len(lines) - len(kept)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    before = subprocess.check_output(['crontab', '-u', 'studystation', '-l'], text=True)
    after, count = retire_lines(before)
    if args.apply and count:
        folder = Path('/root/ss-backups')
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        target = folder / ('recruitment-cron-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S') + '.txt')
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            output.write(before)
        subprocess.run(['crontab', '-u', 'studystation', '-'], input=after, text=True, check=True)
        actual = subprocess.check_output(['crontab', '-u', 'studystation', '-l'], text=True)
        if actual != after:
            raise RuntimeError('Scheduler verification failed')
    print(f'Recruitment tasks matched: {count}; applied: {args.apply}. Other entries preserved.')


if __name__ == '__main__':
    main()
