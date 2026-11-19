"""Preserve corrections to tracked book files without replacing newer upstream content."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess


BOOK_PATHS = ['study_station/books', ':!study_station/books/autopilot',
              ':!study_station/books/AUTOPILOT_STATUS.md']
APPLY_SCOPE = ['--exclude=study_station/books/autopilot/**',
               '--exclude=study_station/books/AUTOPILOT_STATUS.md', '--include=study_station/books/**']


def save_tracked(repo, patch):
    patch = Path(patch)
    patch.parent.mkdir(parents=True, exist_ok=True)
    temporary = patch.with_suffix('.tmp')
    with temporary.open('wb') as output:
        subprocess.run(['git', 'diff', '--binary', '--no-renames', 'HEAD', '--', *BOOK_PATHS], cwd=repo,
                       stdout=output, stderr=subprocess.PIPE, check=True)
    os.replace(temporary, patch)


def retain_conflict(patch, content):
    conflicts = patch.parent / 'tracked-conflicts'
    conflicts.mkdir(parents=True, exist_ok=True)
    (conflicts / (hashlib.sha256(content).hexdigest() + '.patch')).write_bytes(content)


def restore_tracked(repo, patch):
    patch = Path(patch)
    if not patch.is_file() or not patch.stat().st_size:
        return None
    content = patch.read_bytes()
    # Git's path filters apply to a rename's destination; reject rename/copy metadata so a
    # malformed cache cannot move/delete a source file outside the allowed books directory.
    metadata = (b'rename from ', b'rename to ', b'copy from ', b'copy to ')
    if any(line.startswith(metadata) for line in content.splitlines()):
        retain_conflict(patch, content)
        return False
    check = subprocess.run(['git', 'apply', *APPLY_SCOPE, '--check', '-'], cwd=repo, input=content,
                           capture_output=True)
    if check.returncode:
        retain_conflict(patch, content)
        return False               # a newer source wins; never force/reject/partially apply the patch
    subprocess.run(['git', 'apply', *APPLY_SCOPE, '-'], cwd=repo, input=content, capture_output=True, check=True)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['save', 'restore'])
    parser.add_argument('patch', type=Path)
    args = parser.parse_args()
    if args.action == 'save':
        save_tracked(Path.cwd(), args.patch)
        print('Saved tracked book corrections for the next run')
    else:
        restored = restore_tracked(Path.cwd(), args.patch)
        if restored:
            print('Restored tracked book corrections; normal bookcheck and review gates still apply')
        elif restored is False:
            print('Tracked book corrections conflict with newer source; source unchanged, original patch retained for review')


if __name__ == '__main__':
    main()
