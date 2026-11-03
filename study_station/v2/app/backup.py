"""Bounded, owner-scoped progress backups. No credentials or question solutions."""
import hashlib
import json
from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from .models import Attempt, AttemptAnswer, BackupImport, Device, Exam, Question, ReviewCard, Topic, new_backup_id

MAX_BYTES = 2 * 1024 * 1024


class Record(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Answer(Record):
    question_id: StrictInt = Field(gt=0, le=(1 << 53) - 1)
    chosen_index: StrictInt | None = Field(default=None, ge=0, le=9)
    time_ms: StrictInt = Field(ge=0, le=604800000)
    marked: StrictBool
    answered_at: datetime


class AttemptRecord(Record):
    id: StrictInt = Field(gt=0, le=(1 << 53) - 1)
    mode: Literal['practice', 'mock']
    exam: str | None = Field(default=None, max_length=40)
    topic_id: StrictInt | None = Field(default=None, gt=0, le=(1 << 53) - 1)
    question_ids: list[StrictInt] = Field(min_length=1, max_length=500)
    started_at: datetime
    finished_at: datetime | None
    duration_sec: StrictInt | None = Field(default=None, ge=1, le=604800)
    answers: list[Answer] = Field(max_length=500)


class Card(Record):
    question_id: StrictInt = Field(gt=0, le=(1 << 53) - 1)
    box: StrictInt = Field(ge=1, le=5)
    due_on: date
    lapses: StrictInt = Field(ge=0, le=1000000)


class Settings(Record):
    lang: Literal['hi', 'en']
    level: Literal['10th', '12th', 'graduate'] | None
    target_exams: list[str] = Field(max_length=50)


class ProgressBackup(Record):
    schema_version: Literal[1]
    source_id: UUID
    settings: Settings
    attempts: list[AttemptRecord] = Field(max_length=1000)
    revision: list[Card] = Field(max_length=5000)

    @field_validator('schema_version', mode='before')
    @classmethod
    def version_is_integer(cls, value):
        if type(value) is not int:
            raise ValueError('invalid_schema_version')
        return value

    @model_validator(mode='after')
    def unique_and_bounded(self):
        if sum(len(a.answers) for a in self.attempts) > 10000:
            raise ValueError('too_many_answers')
        if len({a.id for a in self.attempts}) != len(self.attempts):
            raise ValueError('duplicate_attempt')
        if len({c.question_id for c in self.revision}) != len(self.revision):
            raise ValueError('duplicate_card')
        for a in self.attempts:
            ids = set(a.question_ids)
            if len(ids) != len(a.question_ids) or any(q < 1 or q >= 1 << 53 for q in ids):
                raise ValueError('invalid_question_ids')
            if len({x.question_id for x in a.answers}) != len(a.answers):
                raise ValueError('duplicate_answer')
            if any(x.question_id not in ids for x in a.answers):
                raise ValueError('answer_outside_attempt')
            start = naive(a.started_at)
            end = naive(a.finished_at) if a.finished_at else None
            if end and end < start:
                raise ValueError('invalid_attempt_dates')
            for dt in [start, end, *(naive(x.answered_at) for x in a.answers)]:
                if dt and (dt.year < 2000 or dt > datetime.utcnow()):
                    raise ValueError('invalid_date')
            if any(naive(x.answered_at) < start or (end and naive(x.answered_at) > end)
                   for x in a.answers):
                raise ValueError('invalid_answer_dates')
        return self


class RestoreRequest(Record):
    confirm: StrictBool
    backup: ProgressBackup

    @model_validator(mode='after')
    def confirmed(self):
        if not self.confirm:
            raise ValueError('confirmation_required')
        return self


def naive(dt):
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def ensure_backup_ids(db, attempts):
    """Assign legacy rows once, including concurrent first exports, without changing API row IDs."""
    changed = False
    for attempt in attempts:
        if attempt.backup_id is None:
            db.execute(update(Attempt).where(Attempt.id == attempt.id, Attempt.backup_id.is_(None))
                       .values(backup_id=new_backup_id()).execution_options(synchronize_session=False))
            db.refresh(attempt, ['backup_id'])
            changed = True
    return changed


def attempt_record(a):
    return AttemptRecord(id=a.backup_id or a.id, mode=a.mode, exam=a.exam.slug if a.exam else None,
                         topic_id=a.topic_id, question_ids=a.question_ids, started_at=a.started_at,
                         finished_at=a.finished_at, duration_sec=a.duration_sec,
                         answers=[Answer(question_id=x.question_id, chosen_index=x.chosen_index,
                                         time_ms=x.time_ms, marked=x.marked, answered_at=x.answered_at)
                                  for x in sorted(a.answers, key=lambda x: x.question_id)])


def checksum(record):
    value = record.model_dump(mode='json')
    value['answers'].sort(key=lambda x: x['question_id'])
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def export_progress(db, device):
    if device is None:
        raise HTTPException(404, 'progress_not_found')
    answer_count = db.scalar(select(func.count(AttemptAnswer.id)).join(Attempt)
                             .where(Attempt.device_id == device.id))
    if answer_count > 10000:
        raise HTTPException(413, 'backup_too_large')
    attempts = list(db.scalars(select(Attempt).where(Attempt.device_id == device.id)
                              .options(selectinload(Attempt.answers), selectinload(Attempt.exam))
                              .order_by(Attempt.id).limit(1001)))
    cards = list(db.scalars(select(ReviewCard).where(ReviewCard.device_id == device.id).limit(5001)))
    if len(attempts) > 1000 or len(cards) > 5000 or sum(len(a.answers) for a in attempts) > 10000:
        raise HTTPException(413, 'backup_too_large')
    changed = ensure_backup_ids(db, attempts)
    source = device.backup_source_id or str(uuid4())
    payload = ProgressBackup(schema_version=1, source_id=UUID(source),
                             settings=Settings(lang=device.lang, level=device.level,
                                               target_exams=device.target_exams or []),
                             attempts=[attempt_record(a) for a in attempts],
                             revision=[Card(question_id=c.question_id, box=c.box,
                                            due_on=c.due_on, lapses=c.lapses) for c in cards])
    if len(RestoreRequest(confirm=True, backup=payload).model_dump_json().encode()) > MAX_BYTES:
        raise HTTPException(413, 'backup_too_large')
    if not device.backup_source_id:
        # Concurrent first exports must share one stable non-secret source identifier.
        db.execute(update(Device).where(Device.id == device.id, Device.backup_source_id.is_(None))
                   .values(backup_source_id=source).execution_options(synchronize_session=False))
        changed = True
    if changed:
        db.commit()
        db.refresh(device)
        payload.source_id = UUID(device.backup_source_id)
    return payload.model_dump(mode='json')


def validate_references(db, backup):
    qids = {q for a in backup.attempts for q in a.question_ids} | {c.question_id for c in backup.revision}
    # Chunked queries avoid SQLite's bind-variable limit on large backups.
    qs = {}
    ordered = list(qids)
    for start in range(0, len(ordered), 400):
        qs.update({q.id: q for q in db.scalars(select(Question).where(Question.id.in_(ordered[start:start+400]))
                                              .options(joinedload(Question.topic)))})
    exams = {e.slug: e for e in db.scalars(select(Exam).options(selectinload(Exam.sections)))}
    topics = set(db.scalars(select(Topic.id)))
    if set(qs) != qids or any(s not in exams for s in backup.settings.target_exams):
        raise HTTPException(422, 'unknown_backup_reference')
    for a in backup.attempts:
        if (a.topic_id is not None and a.topic_id not in topics) or (a.exam is not None and a.exam not in exams):
            raise HTTPException(422, 'unknown_backup_reference')
        if (a.mode == 'mock' and (a.exam is None or a.topic_id is not None)) or (a.mode == 'practice' and a.exam is not None):
            raise HTTPException(422, 'invalid_attempt_kind')
        if a.topic_id is not None and any(qs[qid].topic_id != a.topic_id for qid in a.question_ids):
            raise HTTPException(422, 'question_outside_topic')
        if a.exam is not None:
            subjects = {s.subject_id for s in exams[a.exam].sections}
            if any(qs[qid].topic.subject_id not in subjects for qid in a.question_ids):
                raise HTTPException(422, 'question_outside_exam')
        for answer in a.answers:
            q = qs[answer.question_id]
            count = len(q.options_hi or q.options_en or [])
            if answer.chosen_index is not None and answer.chosen_index >= count:
                raise HTTPException(422, 'invalid_answer_option')
    return qs, exams


def restore_progress(db, device, backup, qs, exams):
    """All references validated before creating a learner; one atomic commit."""
    imported = skipped = 0
    try:
        if device is None:
            import secrets
            device = Device(token=secrets.token_urlsafe(32), backup_source_id=str(uuid4()))
            db.add(device)
            db.flush()
        source = str(backup.source_id)
        receipts = {r.original_id: r for r in db.scalars(select(BackupImport).where(
            BackupImport.device_id == device.id, BackupImport.source_id == source))}
        own = {}
        if source == device.backup_source_id:
            own = {(a.backup_id or a.id): a for a in db.scalars(select(Attempt).where(Attempt.device_id == device.id)
                                              .options(selectinload(Attempt.answers), selectinload(Attempt.exam)))}
        for record in backup.attempts:
            digest = checksum(record)
            existing = receipts.get(record.id)
            if existing or record.id in own:
                previous = existing.checksum if existing else checksum(attempt_record(own[record.id]))
                if previous != digest:
                    raise HTTPException(409, 'backup_attempt_conflict')
                skipped += 1
                continue
            exam = exams.get(record.exam)
            a = Attempt(device_id=device.id, mode=record.mode, exam_id=exam.id if exam else None,
                        topic_id=record.topic_id, title=exam.name_en if exam else 'Practice',
                        question_ids=record.question_ids, started_at=naive(record.started_at),
                        finished_at=naive(record.finished_at) if record.finished_at else None,
                        duration_sec=record.duration_sec)
            db.add(a)
            db.flush()
            marks = {s.subject_id: (s.marks_per_q, s.negative_per_q) for s in exam.sections} if exam else {}
            score = 0.0
            maximum = sum(marks.get(qs[qid].topic.subject_id, (1, 0))[0] for qid in record.question_ids)
            for answer in record.answers:
                q = qs[answer.question_id]
                correct = None if answer.chosen_index is None else answer.chosen_index == q.answer_index
                m, neg = marks.get(q.topic.subject_id, (1, 0))
                score += m if correct is True else -neg if correct is False else 0
                db.add(AttemptAnswer(attempt_id=a.id, question_id=q.id, chosen_index=answer.chosen_index,
                                     correct=correct, time_ms=answer.time_ms, marked=answer.marked,
                                     answered_at=naive(answer.answered_at)))
            if a.finished_at:
                a.score, a.max_score = round(score, 2), maximum
            db.add(BackupImport(device_id=device.id, source_id=source, original_id=record.id, checksum=digest))
            imported += 1
        existing_cards = {c.question_id for c in db.scalars(select(ReviewCard).where(ReviewCard.device_id == device.id))}
        for card in backup.revision:
            if card.question_id not in existing_cards:
                db.add(ReviewCard(device_id=device.id, **card.model_dump()))
        device.lang, device.level = backup.settings.lang, backup.settings.level
        device.target_exams = backup.settings.target_exams
        db.commit()
        return device, {'ok': True, 'imported': imported, 'skipped': skipped}
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'backup_attempt_conflict')
    except Exception:
        db.rollback()
        raise
