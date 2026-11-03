"""Export only public study content, never the database itself, into an APK asset pack.

Run ``python -m app.offline_pack --output /tmp/study-pack`` on the content host.
No schema creation, learner queries, or database writes are performed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import books, config
from .db import engine
from .models import Exam, ExamSection, Question, Subject, Topic

MAX_SECTION_BYTES = 4 * 1024 * 1024
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_PACK_BYTES = 512 * 1024 * 1024
QUESTION_FIELDS = ('id', 'topic_id', 'level', 'difficulty', 'text_hi', 'text_en',
                   'options_hi', 'options_en', 'answer_index', 'solution_hi', 'solution_en',
                   'source_type', 'source_ref', 'review_status')


def _fields(row, names):
    return {name: getattr(row, name) for name in names}


def _safe_file(path, root):
    """Reject linked directories too, not only a linked leaf file."""
    path, root = Path(path).absolute(), Path(root).absolute()
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return all(not p.is_symlink() for p in (path, *path.parents)) and path.is_file()


def _snapshot_books(root, target):
    """Give the existing indexer a bounded tree that cannot traverse directory links."""
    copied = 0
    for directory, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not (Path(directory) / d).is_symlink())
        for name in sorted(names):
            source = Path(directory) / name
            if (source.suffix.lower() != '.txt' and name != 'chapter.json') or not _safe_file(source, root):
                continue
            size = source.stat().st_size
            copied += size
            if size > MAX_SECTION_BYTES or copied > MAX_PACK_BYTES:
                raise ValueError('Book source exceeds configured size bound')
            destination = target / source.relative_to(root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())


def export_pack(db: Session, output, books_dir=None):
    """Build deterministically in a sibling directory, publish only after all checks pass."""
    if db.new or db.dirty or db.deleted:
        raise ValueError('Export requires a clean read-only session')
    output = Path(output).absolute()
    if output.is_symlink() or any(p.is_symlink() for p in output.parents):
        raise ValueError('Output must not contain symlinks')
    if output.exists() and not (output / 'manifest.json').is_file():
        raise ValueError('Refusing to replace a directory without an offline pack manifest')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.study-pack-', dir=output.parent))
    files, total = {}, 0

    def write(relative, value):
        nonlocal total
        payload = (json.dumps(value, ensure_ascii=False, sort_keys=True,
                              separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')
        total += len(payload)
        if len(payload) > MAX_FILE_BYTES or total > MAX_PACK_BYTES:
            raise ValueError('Public content pack exceeds configured size bound')
        path = staging / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        files[relative] = hashlib.sha256(payload).hexdigest()

    try:
        topics = db.scalars(select(Topic).order_by(Topic.id)).all()
        topic_data = {}
        question_count = 0
        question_index = {}
        # A single ordered scan, no per-topic database queries and no private tables.
        chunks = {t.id: [] for t in topics}
        for q in db.scalars(select(Question).where(
                Question.review_status.in_(('unreviewed', 'verified'))).order_by(Question.id)):
            if q.topic_id in chunks:
                chunks[q.topic_id].append(_fields(q, QUESTION_FIELDS))
                question_count += 1
                question_index[str(q.id)] = q.topic_id
        write('question-index.json', question_index)
        for t in topics:
            relative = f'questions/{t.id}.json'
            write(relative, chunks[t.id])
            topic_data[t.id] = dict(_fields(t, ('id', 'subject_id', 'slug', 'name_hi', 'name_en', 'order')),
                                   question_count=len(chunks[t.id]), questions_path=relative)
        subjects = [dict(_fields(s, ('id', 'slug', 'name_hi', 'name_en')),
                         topics=[topic_data[t.id] for t in topics if t.subject_id == s.id])
                    for s in db.scalars(select(Subject).order_by(Subject.id))]
        sections = db.scalars(select(ExamSection).order_by(ExamSection.order, ExamSection.id)).all()
        exams = [dict(_fields(e, ('id', 'slug', 'body', 'name_hi', 'name_en', 'stage_en', 'level',
                                  'duration_min', 'pattern_note_hi', 'pattern_note_en')),
                      sections=[_fields(s, ('id', 'subject_id', 'questions', 'marks_per_q',
                                             'negative_per_q', 'order')) for s in sections if s.exam_id == e.id])
                 for e in db.scalars(select(Exam).order_by(Exam.id))]
        write('catalog.json', {'subjects': subjects, 'exams': exams})
        root = Path(books_dir if books_dir is not None else config.BOOKS_DIR).absolute()
        book_list, chapter_count = [], 0
        if not any(p.is_symlink() for p in (root, *root.parents)):
            source_snapshot = staging / '.book-source'
            _snapshot_books(root, source_snapshot)
            for book in sorted(books._scan(source_snapshot), key=lambda b: b.slug):
                chapters = []
                for chapter in book.readable_chapters:
                    if chapter.dynamic:
                        continue  # Changing current affairs remain online.
                    content = []
                    for key, slug in books.SECTIONS:
                        langs = {}
                        for lang, path in sorted(chapter.sections.get(key, {}).items()):
                            if not _safe_file(path, source_snapshot):
                                continue
                            if path.stat().st_size > MAX_SECTION_BYTES:
                                raise ValueError('Book section exceeds configured size bound')
                            langs[lang] = path.read_text(encoding='utf-8').replace('\r\n', '\n')
                        if langs:
                            content.append({'key': key, 'slug': slug, 'content': langs})
                    if not content:
                        continue
                    relative = f'chapters/{book.slug}--{chapter.slug}.json'
                    descriptor = dict(_fields(chapter, ('slug', 'number', 'title_hi', 'title_en', 'topic')),
                                      path=relative)
                    write(relative, dict(descriptor, sections=content))
                    chapters.append(descriptor)
                    chapter_count += 1
                if chapters:
                    book_list.append(dict(_fields(book, ('slug', 'level', 'subject')),
                                          title_hi=book.title('hi'), title_en=book.title('en'), chapters=chapters))
            if source_snapshot.exists():
                shutil.rmtree(source_snapshot)
        write('books/index.json', book_list)
        content_hash = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        manifest = {'format': 'study-station-content', 'version': 1, 'content_hash': content_hash,
                    'counts': {'questions': question_count, 'books': len(book_list), 'chapters': chapter_count,
                               'subjects': len(subjects), 'topics': len(topics)}, 'files': dict(files)}
        write('manifest.json', manifest)
        old = output.with_name(output.name + '.previous')
        if old.exists():
            raise ValueError('Previous pack backup already exists; inspect it before replacing')
        if output.exists():
            os.replace(output, old)
        try:
            os.replace(staging, output)
        except BaseException:
            if old.exists():
                os.replace(old, output)
            raise
        if old.exists():
            shutil.rmtree(old)
        return manifest
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] /
                        'android/app/src/main/assets/study')
    parser.add_argument('--books-dir', type=Path)
    args = parser.parse_args()
    with Session(engine, autoflush=False) as db:
        if engine.dialect.name == 'sqlite':
            from sqlalchemy import text
            db.execute(text('PRAGMA query_only=ON'))
        result = export_pack(db, args.output, args.books_dir)
    print(json.dumps({'output': str(args.output), **result['counts'], 'content_hash': result['content_hash']}))


if __name__ == '__main__':
    main()
