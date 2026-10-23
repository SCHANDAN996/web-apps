"""Three-day trial foundation. Disabled until the operator explicitly enables it.

A client cannot set dates, prices, a paid entitlement or a payment success flag.
No card, payment order, recurring mandate or automatic charge is created here.
"""
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request
from sqlalchemy.exc import IntegrityError
from .db import get_db
from .classroom import require, body, fail
from .membership_models import Membership

router = APIRouter(prefix='/api/v1/membership', tags=['membership'])
TRIAL_DURATION = timedelta(hours=72)
PLANS = ({'id': 'monthly', 'amount_paise': 900, 'currency': 'INR', 'period': 'calendar_month'},
         {'id': 'yearly', 'amount_paise': 5100, 'currency': 'INR', 'period': 'calendar_year'})

def enabled():
    return os.environ.get('MEMBERSHIP_ENABLED', '0') == '1'

def utcnow():
    return datetime.utcnow()

def stamp(value):
    return value.isoformat(timespec='seconds') + 'Z' if value else None


def paid_access_until(db,account,now=None):
    from .play_billing import access_until as google_access_until
    now=now or utcnow()
    row=db.get(Membership,account.storage_namespace) if account.storage_namespace else None
    candidates=[row.paid_until if row else None,google_access_until(db,account.storage_namespace,now)]
    return max((value for value in candidates if value is not None),default=None)


def effective_access_until(db,account,now=None):
    row=db.get(Membership,account.storage_namespace) if account.storage_namespace else None
    candidates=[row.trial_ends_at if row else None,paid_access_until(db,account,now)]
    return max((value for value in candidates if value is not None),default=None)


def status_for(db, account, now=None):
    now = now or utcnow()
    active = enabled()
    row = db.get(Membership, account.storage_namespace) if account.storage_namespace else None
    trial_active = bool(row and row.trial_ends_at > now)
    paid_until=paid_access_until(db,account,now)
    paid_active = bool(paid_until and paid_until > now)
    state = 'disabled' if not active else ('paid' if paid_active else 'trial' if trial_active else 'expired' if row else 'available')
    return {'enabled': active, 'state': state, 'server_time': stamp(now),
            'trial_started_at': stamp(row.trial_started_at) if row else None,
            'trial_ends_at': stamp(row.trial_ends_at) if row else None,
            'paid_until': stamp(paid_until),
            'account_namespace': account.storage_namespace,
            'access_until': stamp(effective_access_until(db,account,now)),
            'remaining_seconds': max(0, int((row.trial_ends_at-now).total_seconds())) if row else 0,
            'premium_access': not active or trial_active or paid_active,
            'payment_available': False, 'auto_renew': False,
            'plans': list(PLANS), 'protected_actions': ['privacy', 'delete_account', 'export', 'restore', 'private_data']}

@router.get('/status')
def membership_status(request: Request, db=Depends(get_db)):
    account = require(request, db)
    from .play_billing import refresh_account
    refresh_account(db,account)
    return status_for(db, account)

@router.post('/start')
async def membership_start(request: Request, db=Depends(get_db)):
    account = require(request, db)
    data = await body(request)
    if set(data) != {'confirm'} or data.get('confirm') is not True:
        fail('trial_confirmation_required')
    if not enabled():
        fail('membership_not_enabled', 409)
    if not account.storage_namespace:
        fail('account_namespace_required', 409)
    row = db.get(Membership, account.storage_namespace)
    if not row:
        now = utcnow()
        db.add(Membership(namespace=account.storage_namespace, trial_started_at=now,
                          trial_ends_at=now+TRIAL_DURATION))
        try:
            db.commit()
        except IntegrityError:
            # A concurrent activation must return the first period, never restart it.
            db.rollback()
    return status_for(db, account)




def calendar_end(value, plan_id):
    """One calendar month/year, clamped to the destination month's last day."""
    import calendar
    if plan_id == 'monthly':
        year, month = value.year + (value.month == 12), value.month % 12 + 1
    elif plan_id == 'yearly':
        year, month = value.year + 1, value.month
    else:
        raise ValueError('invalid_membership_plan')
    return value.replace(year=year, month=month, day=min(value.day, calendar.monthrange(year,month)[1]))


def grant_verified_payment(db, account_id, plan_id, unique_payment_reference, verified_at):
    """INTERNAL ONLY: caller verified provider S2S and holds the write transaction.

    Caller must serialize payment finalization (SQLite BEGIN IMMEDIATE), and commit
    this together with its successful order ledger. Never exposed as an API.
    """
    from .classroom_models import ClassroomAccount
    from .membership_models import MembershipGrant
    if plan_id not in {x['id'] for x in PLANS}:
        raise ValueError('invalid_membership_plan')
    if not isinstance(unique_payment_reference,str) or not 1 <= len(unique_payment_reference) <= 160:
        raise ValueError('invalid_payment_reference')
    if not isinstance(verified_at,datetime):
        raise ValueError('invalid_verification_time')
    if verified_at.tzinfo:
        from datetime import timezone
        verified_at=verified_at.astimezone(timezone.utc).replace(tzinfo=None)
    account=db.get(ClassroomAccount,account_id)
    if not account or not account.storage_namespace:
        raise ValueError('membership_account_missing')
    old=db.get(MembershipGrant,unique_payment_reference)
    if old:
        if old.namespace != account.storage_namespace or old.plan_id != plan_id:
            raise ValueError('membership_reference_conflict')
        return old.paid_until
    row=db.get(Membership,account.storage_namespace)
    if not row:
        # Purchase does not silently activate an extra free trial.
        row=Membership(namespace=account.storage_namespace,trial_started_at=verified_at,
                       trial_ends_at=verified_at)
        db.add(row)
    begin=max(verified_at,row.paid_until) if row.paid_until else verified_at
    row.paid_until=calendar_end(begin,plan_id)
    db.add(MembershipGrant(reference=unique_payment_reference,namespace=account.storage_namespace,
                            plan_id=plan_id,verified_at=verified_at,paid_until=row.paid_until))
    db.flush()
    return row.paid_until


def revoke_verified_payment(db,reference,verified_at):
    """Internal verified refund/chargeback path, in the caller's write transaction.

    Rebuild only website grants; Google entitlements and free trials are separate.
    No commit here. Unknown references are a safe no-op.
    """
    from sqlalchemy import select
    from .membership_models import MembershipGrant
    if not isinstance(verified_at,datetime): raise ValueError('invalid_verification_time')
    if verified_at.tzinfo:
        from datetime import timezone
        verified_at=verified_at.astimezone(timezone.utc).replace(tzinfo=None)
    grant=db.get(MembershipGrant,reference)
    if not grant: return False
    if grant.revoked_at: return True
    grant.revoked_at=verified_at
    db.flush()
    grants=list(db.scalars(select(MembershipGrant).where(MembershipGrant.namespace==grant.namespace,
                     MembershipGrant.revoked_at.is_(None)).order_by(MembershipGrant.verified_at,MembershipGrant.reference)))
    end=None
    for item in grants:
        begin=max(item.verified_at,end) if end else item.verified_at
        end=calendar_end(begin,item.plan_id)
        item.paid_until=end
    membership=db.get(Membership,grant.namespace)
    if membership: membership.paid_until=end
    db.flush()
    return True

# Paths intentionally omit personal history, existing attempts, notebooks and exports.
def premium_path(path, method):
    import re
    if method in ('GET','HEAD'):
        return (path in ('/books','/practice','/mock','/revise','/questions','/api/v1/revise')
                or any(path.startswith(p) for p in ('/books/','/practice/','/mock/','/questions/')))
    if method == 'POST':
        return (path in ('/api/v1/practice','/api/v1/mock')
                or bool(re.fullmatch(r'/api/v1/questions/[0-9]+/(practice|explain)',path))
                or bool(re.fullmatch(r'/api/v1/attempts/[0-9]+/retry-wrong',path)))
    return False


def access_decision(request):
    """Read-only check executed in a worker, without keeping a DB session open."""
    from .db import SessionLocal
    from .classroom import current
    with SessionLocal() as db:
        account=current(request,db)
        if not account:
            return 401,'sign_in_required'
        from .play_billing import refresh_account
        from fastapi import HTTPException
        try:
            refresh_account(db,account)
        except HTTPException as error:
            return error.status_code,error.detail
        if not status_for(db,account)['premium_access']:
            return 402,'membership_required'
    return None


async def guard_request(request, call_next):
    from urllib.parse import urlencode
    from starlette.concurrency import run_in_threadpool
    from fastapi.responses import JSONResponse, RedirectResponse
    if enabled() and premium_path(request.url.path,request.method):
        denied=await run_in_threadpool(access_decision,request)
        if denied:
            code,reason=denied
            if request.url.path.startswith('/api/'):
                return JSONResponse({'detail':reason,'membership_url':'/membership'},status_code=code,
                                    headers={'Cache-Control':'no-store','Vary':'Cookie'})
            # Only the actual same-origin allowlisted path is carried, no arbitrary return URL.
            return RedirectResponse('/membership?'+urlencode({'return_to':request.url.path}),status_code=303,
                                    headers={'Cache-Control':'no-store','Vary':'Cookie'})
    response=await call_next(request)
    if request.url.path.startswith('/api/v1/membership') or request.url.path=='/membership':
        response.headers['Cache-Control']='no-store'
        response.headers['Vary']='Cookie'
    return response

@router.get('/lease')
def membership_lease(request: Request, db=Depends(get_db)):
    """Optional short offline lease; native verifier must bind namespace and monotonic time.

    Does not make the bundled question bank encrypted or tamper-proof.
    Disabled until an external RSA signing key is deliberately configured.
    """
    import base64
    import calendar
    import json
    import secrets
    from pathlib import Path
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    account=require(request,db)
    if not enabled(): fail('membership_not_enabled',409)
    from .play_billing import refresh_account
    refresh_account(db,account)
    now=utcnow()
    state=status_for(db,account,now)
    if not state['premium_access']: fail('membership_required',402)
    valid_until=effective_access_until(db,account,now)
    expires=min(valid_until,now+timedelta(hours=24))
    key_file=os.environ.get('MEMBERSHIP_LEASE_PRIVATE_KEY_FILE','')
    if not key_file: fail('membership_offline_unavailable',503)
    try:
        key=serialization.load_pem_private_key(Path(key_file).read_bytes(),password=None)
        if not isinstance(key,rsa.RSAPrivateKey) or key.key_size < 2048:
            raise ValueError('invalid_signing_key')
    except (OSError,ValueError,TypeError):
        fail('membership_offline_unavailable',503)
    claims={'iss':'StudyStation','aud':'com.studystation.app','namespace':account.storage_namespace,
            'iat':calendar.timegm(now.utctimetuple()),'exp':calendar.timegm(expires.utctimetuple()),
            'jti':secrets.token_urlsafe(18)}
    def encode(value):
        return base64.urlsafe_b64encode(value).decode('ascii').rstrip('=')
    message=encode(b'{"alg":"RS256","typ":"JWT"}')+'.'+encode(json.dumps(claims,separators=(',',':')).encode('utf-8'))
    signature=key.sign(message.encode('ascii'),padding.PKCS1v15(),hashes.SHA256())
    return {'scheme':'RS256','lease':message+'.'+encode(signature),'server_time':stamp(now),'valid_until':stamp(expires)}
