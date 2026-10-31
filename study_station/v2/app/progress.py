"""Explicitly reset one learner's study history without changing their identity or settings."""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from .models import Attempt, AttemptAnswer, BackupImport, Device, Question, ReviewCard, Subject, Topic


def reset_options(db: Session):
    """Use the same chapter→catalog mapping as reading/practice; never infer from titles."""
    from . import books
    subjects = list(db.scalars(select(Subject).order_by(Subject.id)))
    topics = {(tp.subject.slug, tp.slug): tp for tp in db.scalars(
        select(Topic).options(selectinload(Topic.subject)))}
    chapters = []
    for book in books.readable_books():
        for chapter in book.readable_chapters:
            topic = topics.get(chapter.topic)
            chapters.append({'book': book.slug, 'chapter': chapter.slug, 'subject': book.subject,
                             'title_hi': chapter.title_hi, 'title_en': chapter.title_en,
                             'book_title_hi': book.title('hi'), 'book_title_en': book.title('en'),
                             'topic_label_hi': topic.name_hi if topic else None,
                             'topic_label_en': topic.name_en if topic else None,
                             'url': f'/books/{book.slug}/{chapter.slug}'})
    return {'subjects': [{'slug': s.slug, 'title_hi': s.name_hi, 'title_en': s.name_en} for s in subjects],
            'chapters': chapters}


def scoped_selection(db: Session, scope, subject=None, book=None, chapter=None):
    from . import books
    if scope == 'subject':
        row = db.scalar(select(Subject).where(Subject.slug == subject))
        if row is None:
            raise HTTPException(422, 'unknown_reset_subject')
        selected = select(Question.id).join(Topic).where(Topic.subject_id == row.id)
        urls = [f'/books/{b.slug}/{c.slug}' for b in books.readable_books()
                if b.subject == row.slug for c in b.readable_chapters]
    else:
        b = books.get_book(book)
        c = b.chapter(chapter) if b else None
        if c is None or not c.readable:
            raise HTTPException(422, 'unknown_reset_chapter')
        urls = [f'/books/{b.slug}/{c.slug}']
        if c.topic:
            selected = (select(Question.id).join(Topic).join(Subject)
                        .where(Subject.slug == c.topic[0], Topic.slug == c.topic[1]))
        else:
            selected = select(Question.id).where(Question.id < 0)
    return selected, urls


def reset_scoped_progress(db, device, selected, reading_urls, whiteboard_question_ids):
    """Reset selected practice/revision only. Complete mock history remains intact."""
    qids = set(db.scalars(selected))
    local_ids = [qid for qid in whiteboard_question_ids if qid in qids]
    if device is None:
        return {'ok': True, 'reading_urls': reading_urls, 'whiteboard_question_ids': local_ids}
    try:
        attempts = db.scalars(select(Attempt).where(Attempt.device_id == device.id, Attempt.mode == 'practice')
                              .options(selectinload(Attempt.answers)))
        for attempt in attempts:
            remaining = [qid for qid in attempt.question_ids if qid not in qids]
            if len(remaining) == len(attempt.question_ids):
                continue
            if not remaining:
                db.delete(attempt)
                continue
            # Mixed-topic retry attempts retain every unrelated question and answer.
            for answer in attempt.answers:
                if answer.question_id in qids:
                    db.delete(answer)
            attempt.question_ids = remaining
            if attempt.finished_at is not None:
                attempt.score = sum(1 for a in attempt.answers if a.question_id not in qids and a.correct is True)
                attempt.max_score = len(remaining)
        db.execute(delete(ReviewCard).where(ReviewCard.device_id == device.id,
                                            ReviewCard.question_id.in_(selected)))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {'ok': True, 'reading_urls': reading_urls, 'whiteboard_question_ids': local_ids}


def reset_progress(db: Session, device: Device):
    attempt_ids = select(Attempt.id).where(Attempt.device_id == device.id)
    try:
        db.execute(delete(AttemptAnswer).where(AttemptAnswer.attempt_id.in_(attempt_ids)))
        db.execute(delete(ReviewCard).where(ReviewCard.device_id == device.id))
        db.execute(delete(BackupImport).where(BackupImport.device_id == device.id))
        db.execute(delete(Attempt).where(Attempt.device_id == device.id))
        # SQLite may reuse deleted attempt IDs; a reset starts a new backup namespace.
        device.backup_source_id = None
        db.commit()
    except Exception:
        db.rollback()
        raise
