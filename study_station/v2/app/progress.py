"""Explicitly reset one learner's study history without changing their identity or settings."""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .models import Attempt, AttemptAnswer, Device, ReviewCard


def reset_progress(db: Session, device: Device):
    attempt_ids = select(Attempt.id).where(Attempt.device_id == device.id)
    try:
        db.execute(delete(AttemptAnswer).where(AttemptAnswer.attempt_id.in_(attempt_ids)))
        db.execute(delete(ReviewCard).where(ReviewCard.device_id == device.id))
        db.execute(delete(Attempt).where(Attempt.device_id == device.id))
        db.commit()
    except Exception:
        db.rollback()
        raise
