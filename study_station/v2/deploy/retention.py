"""Study Station allowlisted retention maintenance; dry run unless --apply.

13-day expiry leaves a full day of scheduling margin beneath the 14-day policy.
Never follows symlinks, touches live databases, or vacuums the shared journal.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import time

BACKUP_ROOTS = (Path('/var/backups/studystation'), Path('/root/ss-backups'))
LOG_ROOT = Path('/var/log/studystation')
LOG_FILES = (Path('/var/log/studystation-nginx-errors.log'), Path('/var/log/nginx/studystation-access.log'))
LEGACY_LOG_FILES = (Path('/var/log/nginx/studystation-error.log'),)
EXPIRE_SECONDS = 13 * 24 * 60 * 60


def safe_directory(path: Path) -> bool:
    """Reject symbolic links in every existing ancestor, including the root."""
    for part in (path, *path.parents):
        try:
            mode = part.lstat().st_mode
        except FileNotFoundError:
            return False
        if stat.S_ISLNK(mode):
            raise ValueError(f'Symlink directory refused: {part}')
    return path.is_dir()


def candidates(now: float) -> list[Path]:
    cutoff = now - EXPIRE_SECONDS
    result = []
    for root in BACKUP_ROOTS:
        if not safe_directory(root):
            continue
        for directory, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = [name for name in dirs if not Path(directory, name).is_symlink()]
            for name in files:
                path = Path(directory, name)
                info = path.lstat()
                if stat.S_ISREG(info.st_mode) and info.st_mtime <= cutoff:
                    result.append(path)
    # Only archives, never truncate or unlink a currently open log.
    archives = []
    if safe_directory(LOG_ROOT):
        archives.extend(path for path in LOG_ROOT.iterdir() if '.log.' in path.name)
    for active in LOG_FILES:
        if safe_directory(active.parent):
            archives.extend(active.parent.glob(active.name + '.*'))
    for path in archives:
        info = path.lstat()
        if stat.S_ISREG(info.st_mode) and info.st_mtime <= cutoff:
            result.append(path)
    # The old nginx error destination is no longer written. Its exact path
    # (and only that path) is retired once its final write passes the cutoff.
    for path in LEGACY_LOG_FILES:
        if safe_directory(path.parent) and path.exists():
            info = path.lstat()
            if stat.S_ISREG(info.st_mode) and info.st_mtime <= cutoff:
                result.append(path)
    return sorted(set(result))


def unlink_expired(path: Path, cutoff: float) -> None:
    """Resolve every parent via no-follow directory FDs, avoiding rename races.

    Production is Linux. Holding directory descriptors prevents an app-writable
    parent being replaced with an escape symlink between inspection and unlink.
    """
    descriptor = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in path.parent.parts[1:]:
            next_descriptor = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                      dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        info = os.stat(path.name, dir_fd=descriptor, follow_symlinks=False)
        if stat.S_ISREG(info.st_mode) and info.st_mtime <= cutoff:
            os.unlink(path.name, dir_fd=descriptor)
    finally:
        os.close(descriptor)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    now = time.time()
    expired = candidates(now)
    report = {'apply': args.apply, 'cutoff_unix': now - EXPIRE_SECONDS,
              'expired_count': len(expired), 'expired_bytes': sum(p.stat().st_size for p in expired),
              'paths': [str(p) for p in expired], 'shared_journal_touched': False}
    print(json.dumps(report, sort_keys=True))
    if not args.apply:
        return
    for path in expired:
        unlink_expired(path, now - EXPIRE_SECONDS)
    # The namespace is exclusive to this app; never call global journal vacuum.
    subprocess.run(['/usr/bin/journalctl', '--namespace=studystation', '--rotate'], check=True)
    subprocess.run(['/usr/bin/journalctl', '--namespace=studystation', '--vacuum-time=13days'], check=True)


if __name__ == '__main__':
    main()
