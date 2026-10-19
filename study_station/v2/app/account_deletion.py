"""Explicit account deletion; anonymous device progress stays on its own lifecycle."""
from collections import Counter
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import delete, select
from .db import get_db
from .classroom import body, require, fail, public_account, COOKIE
from .classroom_models import (ClassroomAccount as Account, ClassroomSession as Session,
    ClassroomRecord as Record, ClassroomMember as Member, ClassroomEvent as Event,
    ClassroomOperation as Operation)
from .google_auth_models import GoogleIdentity

router = APIRouter(prefix='/api/v1/classroom')


def affected(db, account_id):
    # UNION (rather than UNION ALL) terminates even if malformed ancestry cycles.
    descendants = select(Record.id).where(Record.owner_id == account_id).cte('deleted_records', recursive=True)
    descendants = descendants.union(select(Record.id).join(descendants, Record.parent == descendants.c.id))
    return list(db.execute(select(Record.id, Record.kind).where(Record.id.in_(select(descendants.c.id)))))


def counts(rows):
    by_kind = Counter(kind for _, kind in rows)
    return dict(groups=by_kind['group'], workspaces=by_kind['workspace'],
                assignments=by_kind['assignment'], submissions=by_kind['submission'],
                sessions=by_kind['live'], discussions=by_kind['discussion'], records=len(rows))


@router.get('/account')
def preview(request: Request, response: Response, db=Depends(get_db)):
    account = require(request, db)
    response.headers['Cache-Control'] = 'no-store'
    return dict(account=public_account(account), counts=counts(affected(db, account.id)),
                local_data_preserved=True, includes_owned_group_content=True)


def refers(value, ids, account_id):
    """Invalidate cached operation replies containing erased records or authors."""
    if isinstance(value, dict):
        rid = value.get('id')
        if (isinstance(rid, str) and rid in ids) or value.get('account_id') == account_id or value.get('owner_id') == account_id:
            return True
        return any(refers(item, ids, account_id) for item in value.values())
    if isinstance(value, list):
        return any(refers(item, ids, account_id) for item in value)
    return False


@router.delete('/account')
async def remove_account(request: Request, response: Response, db=Depends(get_db)):
    data = await body(request)
    # Acquire the SQLite writer lock before authentication and ancestry reads.
    # This prevents another worker adding descendants between preview and delete.
    if db.bind.dialect.name == 'sqlite':
        db.connection().exec_driver_sql('BEGIN IMMEDIATE')
    try:
        account = require(request, db)
        if data.get('confirm') is not True or data.get('username') != account.username:
            fail('account_delete_confirmation_required', 400)
        aid = account.id
        rows = affected(db, aid)
        ids = {rid for rid, _ in rows}
        db.execute(delete(Member).where(Member.account_id == aid))
        db.execute(delete(Event).where(Event.account_id == aid))
        db.execute(delete(Operation).where(Operation.account_id == aid))
        # Replies from other accounts may cache submissions or teacher feedback
        # under deleted containers, and must not return erased content on replay.
        for op in db.scalars(select(Operation).execution_options(yield_per=200)):
            if refers(op.result, ids, aid):
                db.delete(op)
        for record in db.scalars(select(Record).execution_options(yield_per=200)):
            if record.id in ids:
                continue
            data_copy = dict(record.data)
            changed = False
            editors = data_copy.get('editors')
            if isinstance(editors, list) and aid in editors:
                data_copy['editors'] = [x for x in editors if x != aid]
                changed = True
            feedback = data_copy.get('feedback')
            if isinstance(feedback, list):
                cleaned = [x for x in feedback if not isinstance(x, dict) or x.get('account_id') != aid]
                if cleaned != feedback:
                    data_copy['feedback'] = cleaned
                    changed = True
            if changed:
                record.data = data_copy
                record.version += 1
        # Batch parameters to work with conservative SQLite variable limits.
        ordered_ids = list(ids)
        for start in range(0, len(ordered_ids), 400):
            chunk = ordered_ids[start:start+400]
            db.execute(delete(Member).where(Member.group_id.in_(chunk)))
            db.execute(delete(Event).where(Event.room_id.in_(chunk)))
        db.flush()
        # parent is deliberately not a foreign key; event/member dependencies
        # above are removed before the owning record and account foreign keys.
        for start in range(0, len(ordered_ids), 400):
            db.execute(delete(Record).where(Record.id.in_(ordered_ids[start:start+400])),
                       execution_options={'synchronize_session': False})
        db.execute(delete(Session).where(Session.account_id == aid))
        db.execute(delete(GoogleIdentity).where(GoogleIdentity.account_id == aid))
        db.execute(delete(Account).where(Account.id == aid), execution_options={'synchronize_session': False})
        db.commit()
    except Exception:
        db.rollback()
        raise
    response.delete_cookie(COOKIE, path='/')
    response.headers['Cache-Control'] = 'no-store'
    return dict(deleted=True, local_data_preserved=True)
