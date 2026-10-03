"""
Remove the mock NCERT data left behind by populate_all_pdfs.py's run_mock().

What run_mock() did: it copied ONE real PDF (class-8 Maths chapter 1) into
every class x every subject x 15 chapters — 1620 copies — and created a
StudyContent row for each. That produced pages like "Class 1 Biology Chapter 1"
serving a Class 8 Maths PDF, plus subjects that don't exist at that level.

What is genuine and MUST survive:
  * the ~166 PDFs that were really downloaded from NCERT (each unique, and
    sitting under a class/subject combination that actually exists)
  * the ~482 chapters that carry real notes text (original content we wrote)

This script deletes only:
  * PDF files whose md5 equals the mock placeholder's
  * StudyContent rows that have neither notes text nor a surviving PDF
  * directories left empty afterwards

Usage:
    python clean_mock_ncert.py            # dry run — reports, changes nothing
    python clean_mock_ncert.py --apply    # actually delete
"""

import hashlib
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, StudyContent

BASE = os.path.abspath(os.path.dirname(__file__))
NCERT_DIR = os.path.abspath(os.path.join(BASE, '..', 'website', 'books', 'ncert'))

APPLY = '--apply' in sys.argv


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def pdf_path_for(class_level, subject, chapter_number):
    """Rebuild the on-disk path the SSG uses for a chapter's PDF."""
    return os.path.join(
        NCERT_DIR, f'class-{class_level}', 'books',
        subject.lower().replace(' ', '_'), 'pdfs',
        f'chapter-{chapter_number}.pdf')


def find_mock_hash(pdfs):
    """The placeholder is simply the most-duplicated file."""
    counts = {}
    for p in pdfs:
        counts.setdefault(md5(p), []).append(p)
    if not counts:
        return None, {}
    top = max(counts.items(), key=lambda kv: len(kv[1]))
    return (top[0], counts) if len(top[1]) > 1 else (None, counts)


def main():
    pdfs = []
    for root, _dirs, files in os.walk(NCERT_DIR):
        pdfs.extend(os.path.join(root, f) for f in files if f.endswith('.pdf'))
    print(f'Scanning {len(pdfs)} PDFs under books/ncert ...')

    mock_hash, groups = find_mock_hash(pdfs)
    if not mock_hash:
        print('No duplicated placeholder found — nothing to clean.')
        return

    mock_files = groups[mock_hash]
    keep = len(pdfs) - len(mock_files)
    print(f'\nPlaceholder md5 {mock_hash}')
    print(f'  mock copies to delete : {len(mock_files)}')
    print(f'  genuine PDFs to keep  : {keep}')

    if APPLY:
        for p in mock_files:
            os.remove(p)
        print('  -> deleted.')

    # DB: drop rows that end up with neither notes nor a PDF.
    with app.app_context():
        rows = StudyContent.query.all()
        doomed = []
        for r in rows:
            has_notes = bool((r.content_text or '').strip())
            path = pdf_path_for(r.class_level, r.subject, r.chapter_number)
            # After the deletion above, a mock chapter has no file left.
            has_pdf = os.path.exists(path) if APPLY else (
                os.path.exists(path) and path not in mock_files)
            if not has_notes and not has_pdf:
                doomed.append(r)

        print(f'\nStudyContent rows       : {len(rows)}')
        print(f'  empty rows to delete  : {len(doomed)}')
        print(f'  rows to keep          : {len(rows) - len(doomed)}')

        if APPLY:
            for r in doomed:
                db.session.delete(r)
            db.session.commit()
            print('  -> deleted.')

    # Sweep up directories the deletions emptied.
    if APPLY:
        removed = 0
        for root, dirs, files in os.walk(NCERT_DIR, topdown=False):
            if not os.listdir(root):
                os.rmdir(root)
                removed += 1
        print(f'\nRemoved {removed} empty directories.')

    if not APPLY:
        print('\n(dry run — nothing changed. Re-run with --apply to delete.)')


if __name__ == '__main__':
    main()
