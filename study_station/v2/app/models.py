from datetime import date, datetime

from sqlalchemy import (JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer,
                        String, Text, UniqueConstraint, Index)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now():
    return datetime.utcnow()


# ---------------------------------------------------------------- catalogue
class Subject(Base):
    __tablename__ = 'subject'
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True)
    name_hi: Mapped[str] = mapped_column(String(80))
    name_en: Mapped[str] = mapped_column(String(80))
    topics: Mapped[list['Topic']] = relationship(back_populates='subject', order_by='Topic.order')


class Topic(Base):
    __tablename__ = 'topic'
    __table_args__ = (UniqueConstraint('subject_id', 'slug'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey('subject.id'))
    slug: Mapped[str] = mapped_column(String(80))
    name_hi: Mapped[str] = mapped_column(String(120))
    name_en: Mapped[str] = mapped_column(String(120))
    order: Mapped[int] = mapped_column(Integer, default=0)
    subject: Mapped[Subject] = relationship(back_populates='topics')


class Exam(Base):
    __tablename__ = 'exam'
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True)
    body: Mapped[str] = mapped_column(String(20))              # SSC / RRB / IBPS
    name_hi: Mapped[str] = mapped_column(String(120))
    name_en: Mapped[str] = mapped_column(String(120))
    stage_en: Mapped[str] = mapped_column(String(80))          # "Tier-I (CBT)"
    level: Mapped[str] = mapped_column(String(20))             # 10th / 12th / graduate
    duration_min: Mapped[int] = mapped_column(Integer)
    pattern_note_hi: Mapped[str] = mapped_column(Text, default='')
    pattern_note_en: Mapped[str] = mapped_column(Text, default='')
    sections: Mapped[list['ExamSection']] = relationship(back_populates='exam', order_by='ExamSection.order')


class ExamSection(Base):
    __tablename__ = 'exam_section'
    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exam.id'))
    subject_id: Mapped[int] = mapped_column(ForeignKey('subject.id'))
    questions: Mapped[int] = mapped_column(Integer)
    marks_per_q: Mapped[float] = mapped_column(Float)
    negative_per_q: Mapped[float] = mapped_column(Float)
    order: Mapped[int] = mapped_column(Integer, default=0)
    exam: Mapped[Exam] = relationship(back_populates='sections')
    subject: Mapped[Subject] = relationship()


class Question(Base):
    __tablename__ = 'question'
    __table_args__ = (
        UniqueConstraint('import_key'),
        Index('ix_question_topic_status', 'topic_id', 'review_status'),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey('topic.id'))
    level: Mapped[str] = mapped_column(String(20))
    difficulty: Mapped[str] = mapped_column(String(10), default='medium')
    text_hi: Mapped[str | None] = mapped_column(Text)
    text_en: Mapped[str | None] = mapped_column(Text)
    options_hi: Mapped[list | None] = mapped_column(JSON)
    options_en: Mapped[list | None] = mapped_column(JSON)
    answer_index: Mapped[int] = mapped_column(Integer)
    solution_hi: Mapped[str | None] = mapped_column(Text)
    solution_en: Mapped[str | None] = mapped_column(Text)
    # pyq = real previous-year question (needs source_ref), ai_generated, editorial
    source_type: Mapped[str] = mapped_column(String(20), default='ai_generated')
    source_ref: Mapped[str | None] = mapped_column(String(200))
    # unreviewed (shown, labelled) / verified / flagged (hidden from students)
    review_status: Mapped[str] = mapped_column(String(20), default='unreviewed')
    review_note: Mapped[str | None] = mapped_column(String(200))
    import_key: Mapped[str | None] = mapped_column(String(200))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=now)
    ca_item_id: Mapped[int | None] = mapped_column(ForeignKey('ca_item.id', ondelete='SET NULL'), index=True)
    topic: Mapped[Topic] = relationship()


class CAItem(Base):
    """One current-affairs item, always tied to an official press release (PIB)."""
    __tablename__ = 'ca_item'
    id: Mapped[int] = mapped_column(primary_key=True)
    prid: Mapped[str] = mapped_column(String(40), unique=True)          # PIB release id
    day: Mapped[date] = mapped_column(Date, index=True)
    title_hi: Mapped[str | None] = mapped_column(String(400))
    title_en: Mapped[str | None] = mapped_column(String(400))
    summary_hi: Mapped[str | None] = mapped_column(Text)
    summary_en: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(30), default='national')
    relevance: Mapped[int] = mapped_column(Integer, default=0)          # 0 = not scored (no AI)
    source_url: Mapped[str] = mapped_column(String(500))
    ministry: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(12), default='published')  # published / hidden
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class QuestionExplanation(Base):
    """AI tutor explanation, generated once per question+language and reused."""
    __tablename__ = 'question_explanation'
    __table_args__ = (UniqueConstraint('question_id', 'lang'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey('question.id', ondelete='CASCADE'))
    lang: Mapped[str] = mapped_column(String(2))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class AiUsage(Base):
    __tablename__ = 'ai_usage'
    __table_args__ = (UniqueConstraint('day', 'device_id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    device_id: Mapped[int | None] = mapped_column(Integer)      # None = admin/CLI jobs
    count: Mapped[int] = mapped_column(Integer, default=0)


# ---------------------------------------------------------------- learners
class Device(Base):
    """Anonymous learner. A login (phase 2) will attach a user to devices."""
    __tablename__ = 'device'
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True)
    lang: Mapped[str] = mapped_column(String(2), default='hi')
    level: Mapped[str | None] = mapped_column(String(20))
    target_exams: Mapped[list] = mapped_column(JSON, default=list)
    # sha256 of the learner's recovery code (the code itself is shown once, never stored)
    recovery_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=now)


class Attempt(Base):
    __tablename__ = 'attempt'
    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey('device.id'), index=True)
    mode: Mapped[str] = mapped_column(String(10))               # practice / mock
    exam_id: Mapped[int | None] = mapped_column(ForeignKey('exam.id'))
    topic_id: Mapped[int | None] = mapped_column(ForeignKey('topic.id'))
    title: Mapped[str] = mapped_column(String(200), default='')
    question_ids: Mapped[list] = mapped_column(JSON)
    duration_sec: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    score: Mapped[float | None] = mapped_column(Float)
    max_score: Mapped[float | None] = mapped_column(Float)
    answers: Mapped[list['AttemptAnswer']] = relationship(back_populates='attempt', cascade='all, delete-orphan')
    exam: Mapped[Exam | None] = relationship()


class AttemptAnswer(Base):
    __tablename__ = 'attempt_answer'
    __table_args__ = (UniqueConstraint('attempt_id', 'question_id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey('attempt.id'))
    question_id: Mapped[int] = mapped_column(ForeignKey('question.id'))
    chosen_index: Mapped[int | None] = mapped_column(Integer)   # None = skipped
    correct: Mapped[bool | None] = mapped_column(Boolean)
    time_ms: Mapped[int] = mapped_column(Integer, default=0)
    marked: Mapped[bool] = mapped_column(Boolean, default=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    attempt: Mapped[Attempt] = relationship(back_populates='answers')
    question: Mapped[Question] = relationship()


class ReviewCard(Base):
    """Mistake notebook entry, scheduled with a 5-box Leitner system."""
    __tablename__ = 'review_card'
    __table_args__ = (UniqueConstraint('device_id', 'question_id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey('device.id'), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey('question.id'))
    box: Mapped[int] = mapped_column(Integer, default=1)
    due_on: Mapped[date] = mapped_column(Date)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    question: Mapped[Question] = relationship()


class QuestionReport(Base):
    __tablename__ = 'question_report'
    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey('question.id'), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey('device.id'))
    reason: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(String(500), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    question: Mapped[Question] = relationship()


# ---------------------------------------------------------------- jobs
class Job(Base):
    """One recruitment (or exam update) — merged from every source that mentioned it.

    Facts shown to students (dates, posts, age) come only from the official
    notice; aggregators only tell us where to look.
    """
    __tablename__ = 'job'
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(200), index=True)
    title: Mapped[str] = mapped_column(String(300))
    org: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(20), default='govt')   # ssc/railway/banking/psc/defence/psu/govt
    job_type: Mapped[str] = mapped_column(String(20), default='latest')  # latest/admit/results/answer/upcoming
    # For job_type='upcoming', start_date = expected notification date (from an official exam calendar).
    # verified = facts read from an official notice on an official domain
    # pending  = only an aggregator mentioned it so far (hidden from students)
    # legacy   = imported from the old site, not re-checked
    status: Mapped[str] = mapped_column(String(10), default='pending', index=True)
    min_qualification: Mapped[str | None] = mapped_column(String(20))   # 10th/12th/graduate
    advt_no: Mapped[str | None] = mapped_column(String(120))
    vacancies: Mapped[str | None] = mapped_column(String(100))
    eligibility: Mapped[str | None] = mapped_column(Text)
    age_min: Mapped[int | None] = mapped_column(Integer)
    age_max: Mapped[int | None] = mapped_column(Integer)
    start_date: Mapped[date | None] = mapped_column(Date)
    last_date: Mapped[date | None] = mapped_column(Date, index=True)
    last_date_text: Mapped[str | None] = mapped_column(String(100))
    official_url: Mapped[str | None] = mapped_column(String(500))       # org website / apply page
    notification_url: Mapped[str | None] = mapped_column(String(500))   # official PDF / notice page
    source: Mapped[str | None] = mapped_column(String(100))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime)       # sent in an alert digest
    sources: Mapped[list['JobSource']] = relationship(back_populates='job', cascade='all, delete-orphan')


class JobSource(Base):
    """Every place a job was seen — lets us survive any single site going down."""
    __tablename__ = 'job_source'
    __table_args__ = (UniqueConstraint('job_id', 'url'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey('job.id'), index=True)
    source: Mapped[str] = mapped_column(String(60))
    kind: Mapped[str] = mapped_column(String(12))          # official / discovery
    url: Mapped[str] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(300))
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=now)
    job: Mapped[Job] = relationship(back_populates='sources')


class SeenItem(Base):
    """Items already processed, so each run only does new work."""
    __tablename__ = 'seen_item'
    __table_args__ = (UniqueConstraint('source', 'url'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(60))
    url: Mapped[str] = mapped_column(String(500))
    outcome: Mapped[str] = mapped_column(String(30))       # job / skipped:<why> / error
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=now)


class SourceHealth(Base):
    __tablename__ = 'source_health'
    source: Mapped[str] = mapped_column(String(60), primary_key=True)
    last_run: Mapped[datetime | None] = mapped_column(DateTime)
    last_ok: Mapped[datetime | None] = mapped_column(DateTime)
    last_error: Mapped[str | None] = mapped_column(String(300))
    last_items: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
