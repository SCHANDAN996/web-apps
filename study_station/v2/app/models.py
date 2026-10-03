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
    topic: Mapped[Topic] = relationship()


# ---------------------------------------------------------------- learners
class Device(Base):
    """Anonymous learner. A login (phase 2) will attach a user to devices."""
    __tablename__ = 'device'
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True)
    lang: Mapped[str] = mapped_column(String(2), default='hi')
    level: Mapped[str | None] = mapped_column(String(20))
    target_exams: Mapped[list] = mapped_column(JSON, default=list)
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


# ---------------------------------------------------------------- jobs
class Job(Base):
    __tablename__ = 'job'
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    org: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(20), default='govt')   # ssc/railway/banking/govt
    job_type: Mapped[str] = mapped_column(String(20), default='latest')  # latest/admit/results/answer
    min_qualification: Mapped[str | None] = mapped_column(String(20))   # 10th/12th/graduate
    vacancies: Mapped[str | None] = mapped_column(String(100))
    eligibility: Mapped[str | None] = mapped_column(Text)
    last_date: Mapped[date | None] = mapped_column(Date, index=True)
    last_date_text: Mapped[str | None] = mapped_column(String(100))
    official_url: Mapped[str | None] = mapped_column(String(500))
    source: Mapped[str | None] = mapped_column(String(100))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
