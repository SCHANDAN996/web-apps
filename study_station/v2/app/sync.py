"""
Move progress between phones without accounts: the learner creates a recovery
code on phone A and types it on phone B. Only a hash is stored; making a new
code invalidates the old one. Whatever phone B already did is merged in.
"""
import hashlib
import secrets

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from .models import Attempt, BackupImport, Device, QuestionReport, ReviewCard

ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'   # no 0/O, 1/I — easy to read aloud


def _hash(code):
    return hashlib.sha256(normalize(code).encode()).hexdigest()


def normalize(code):
    c = ''.join(ch for ch in (code or '').upper() if ch.isalnum())
    return c[2:] if c.startswith('SS') and len(c) == 14 else c


def new_code(db: Session, device: Device):
    raw = ''.join(secrets.choice(ALPHABET) for _ in range(12))          # 60 bits
    device.recovery_hash = _hash(raw)
    db.commit()
    return f'SS-{raw[:4]}-{raw[4:8]}-{raw[8:]}'


def restore(db: Session, current: Device | None, code: str):
    """Return the device that owns `code`, after merging `current` into it."""
    if len(normalize(code)) != 12:
        raise ValueError('bad_code')
    owner = db.scalar(select(Device).where(Device.recovery_hash == _hash(code)))
    if owner is None:
        raise LookupError('code_not_found')
    if current is not None and current.id != owner.id:
        receipts = {(r.source_id, r.original_id) for r in db.scalars(
            select(BackupImport).where(BackupImport.device_id == owner.id))}
        for receipt in db.scalars(select(BackupImport).where(BackupImport.device_id == current.id)):
            if (receipt.source_id, receipt.original_id) in receipts:
                db.delete(receipt)
            else:
                receipt.device_id = owner.id
                receipts.add((receipt.source_id, receipt.original_id))
        # Preserve the disappearing learner's native export namespace as receipts.
        # Otherwise importing an earlier file after recovery would duplicate these moved attempts.
        if current.backup_source_id:
            from .backup import attempt_record, checksum, ensure_backup_ids
            attempts = list(db.scalars(select(Attempt).where(Attempt.device_id == current.id)
                                       .options(selectinload(Attempt.answers), selectinload(Attempt.exam))))
            ensure_backup_ids(db, attempts)
            for attempt in attempts:
                key = (current.backup_source_id, attempt.backup_id)
                if key not in receipts:
                    db.add(BackupImport(device_id=owner.id, source_id=key[0], original_id=key[1],
                                        checksum=checksum(attempt_record(attempt))))
                    receipts.add(key)
        db.execute(update(Attempt).where(Attempt.device_id == current.id).values(device_id=owner.id))
        db.execute(update(QuestionReport).where(QuestionReport.device_id == current.id).values(device_id=owner.id))
        have = {c.question_id: c for c in db.scalars(select(ReviewCard).where(ReviewCard.device_id == owner.id))}
        for card in db.scalars(select(ReviewCard).where(ReviewCard.device_id == current.id)):
            mine = have.get(card.question_id)
            if mine is None:
                card.device_id = owner.id
            else:   # keep the stricter schedule: lower box, earlier due date
                mine.box, mine.due_on = min(mine.box, card.box), min(mine.due_on, card.due_on)
                mine.lapses = max(mine.lapses, card.lapses)
                db.delete(card)
        if not owner.level and current.level:
            owner.level, owner.target_exams = current.level, current.target_exams
        db.flush()
        db.delete(current)
    owner.recovery_hash = None          # single use: a code seen once (screenshot, group chat) stops working
    db.commit()
    return owner
