"""Privileged, explicit one-year Play review access; no charge or provider order."""
import argparse
from datetime import datetime
from sqlalchemy import select


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-id', type=int, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        parser.error('--apply is required')
    import app.main  # register all models
    from app.db import SessionLocal
    from app.classroom_models import ClassroomAccount
    from app.membership import grant_verified_payment
    with SessionLocal() as db:
        if db.bind.dialect.name == 'sqlite':
            db.connection().exec_driver_sql('BEGIN IMMEDIATE')
        account = db.scalar(select(ClassroomAccount).where(ClassroomAccount.username == 'playreview.study'))
        if not account or account.id != args.expected_id:
            raise SystemExit('Review account does not match the approved account')
        # An operator grant is clearly labelled, never disguised as a payment.
        reference = 'operator-review:2026:' + account.storage_namespace
        until = grant_verified_payment(db, account.id, 'yearly', reference, datetime.utcnow())
        db.commit()
    print('Approved review access valid until ' + until.isoformat() + 'Z; no payment created')


if __name__ == '__main__':
    main()
