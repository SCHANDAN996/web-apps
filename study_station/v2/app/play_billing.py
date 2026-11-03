"""Google Play prepaid subscription verification. No client-owned paid grants.

Raw purchase tokens are encrypted with an external Fernet key, never logged or
returned. Google S2S state/expiry is authoritative; website paid_until is untouched.
"""
import hashlib
import hmac
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from sqlalchemy import select, func
from cryptography.fernet import Fernet, InvalidToken
from .classroom import require, body, fail, rate
from .classroom_models import ClassroomAccount
from .db import get_db
from .play_billing_models import PlayPurchase

router=APIRouter(prefix='/api/v1/payments/google',tags=['play-billing'])
PACKAGE='com.studystation.app'
PRODUCTS={'study_station_monthly':('monthly','monthly-prepaid'),
          'study_station_yearly':('yearly','yearly-prepaid')}
CACHE_TTL=timedelta(minutes=15)


def utcnow():
    return datetime.utcnow()


def settings():
    account_file=os.environ.get('PLAY_BILLING_SERVICE_ACCOUNT_FILE','')
    token_key_file=os.environ.get('PLAY_BILLING_TOKEN_KEY_FILE','')
    return {'enabled':os.environ.get('PLAY_BILLING_ENABLED','0')=='1' and bool(account_file and token_key_file)
            and Path(account_file).is_file() and Path(token_key_file).is_file(),
            'account_file':account_file,'token_key_file':token_key_file,
            'allow_test':os.environ.get('PLAY_BILLING_ALLOW_TEST','0')=='1'}


def account_binding(namespace):
    return hashlib.sha256(('StudyStation:play:'+namespace).encode()).hexdigest()


def cipher():
    try:
        return Fernet(Path(settings()['token_key_file']).read_bytes().strip())
    except (OSError,ValueError,TypeError):
        fail('play_billing_unavailable',503)


def provider_request(method,path,payload=None):
    """Only fixed Android Publisher endpoints; secret-bearing exceptions stay local."""
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    try:
        credentials=service_account.Credentials.from_service_account_file(
            settings()['account_file'],scopes=['https://www.googleapis.com/auth/androidpublisher'])
        with AuthorizedSession(credentials) as session:
            result=session.request(method,'https://androidpublisher.googleapis.com/androidpublisher/v3/applications/'+PACKAGE+path,
                                   json=payload,timeout=15,allow_redirects=False)
            if result.status_code in (404,410):
                return {'_not_found':True}
            if result.status_code < 200 or result.status_code >= 300 or len(result.content)>200000:
                raise ValueError('provider_unavailable')
            return result.json() if result.content else {}
    except Exception:
        # Never interpolate requests exceptions: their URLs contain purchase tokens.
        fail('play_billing_unavailable',503)


def provider_get(token):
    return provider_request('GET','/purchases/subscriptionsv2/tokens/'+quote(token,safe=''))


def provider_acknowledge(token,product_id):
    result=provider_request('POST','/purchases/subscriptions/'+quote(product_id,safe='')+'/tokens/'+quote(token,safe='')+':acknowledge',{})
    if result.get('_not_found'): fail('play_purchase_invalid',400)


def timestamp(value):
    try:
        if not isinstance(value,str): raise ValueError()
        parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
        if parsed.tzinfo is None: raise ValueError()
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    except (ValueError,TypeError):
        fail('play_purchase_invalid',400)


def inspect_purchase(data,namespace):
    if not isinstance(data,dict) or data.get('_not_found'): fail('play_purchase_invalid',400)
    identifiers=data.get('externalAccountIdentifiers')
    binding=identifiers.get('obfuscatedExternalAccountId','') if isinstance(identifiers,dict) else ''
    if not isinstance(binding,str) or not re.fullmatch(r'[a-f0-9]{64}',binding) or not hmac.compare_digest(binding,account_binding(namespace)):
        fail('play_purchase_account_mismatch',403)
    items=data.get('lineItems')
    if not isinstance(items,list) or len(items)!=1 or not isinstance(items[0],dict):
        fail('play_purchase_invalid',400)
    item=items[0]; product=item.get('productId'); offer=item.get('offerDetails',{})
    if (not isinstance(product,str) or product not in PRODUCTS or not isinstance(offer,dict) or offer.get('basePlanId')!=PRODUCTS[product][1]
        or not isinstance(item.get('prepaidPlan'),dict) or 'autoRenewingPlan' in item):
        fail('play_purchase_plan_mismatch',400)
    test='testPurchase' in data
    if test and not settings()['allow_test']: fail('play_test_purchase_disabled',400)
    state=data.get('subscriptionState','')
    known={'SUBSCRIPTION_STATE_PENDING','SUBSCRIPTION_STATE_ACTIVE','SUBSCRIPTION_STATE_CANCELED',
           'SUBSCRIPTION_STATE_PAUSED','SUBSCRIPTION_STATE_ON_HOLD','SUBSCRIPTION_STATE_EXPIRED',
           'SUBSCRIPTION_STATE_PENDING_PURCHASE_CANCELED','SUBSCRIPTION_STATE_IN_GRACE_PERIOD'}
    if not isinstance(state,str) or state not in known: fail('play_purchase_invalid',400)
    expiry=timestamp(item['expiryTime']) if item.get('expiryTime') else None
    entitled=state in ('SUBSCRIPTION_STATE_ACTIVE','SUBSCRIPTION_STATE_CANCELED') and expiry is not None and expiry>utcnow()
    if state in ('SUBSCRIPTION_STATE_ACTIVE','SUBSCRIPTION_STATE_CANCELED') and expiry is None:
        fail('play_purchase_invalid',400)
    ack=data.get('acknowledgementState')
    if ack not in ('ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED','ACKNOWLEDGEMENT_STATE_PENDING'):
        fail('play_purchase_invalid',400)
    return dict(product_id=product,base_plan_id=offer['basePlanId'],state=state,expires_at=expiry,
                entitled=entitled,acknowledged=ack=='ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED',test_purchase=test)


def _write_verified(db,account_id,namespace,token,details):
    """Reserve a verified token atomically; acknowledges separately before granting."""
    encrypted=cipher().encrypt(token.encode()).decode()
    digest=hashlib.sha256(token.encode()).hexdigest()
    db.rollback()
    if db.bind.dialect.name=='sqlite': db.connection().exec_driver_sql('BEGIN IMMEDIATE')
    account=db.get(ClassroomAccount,account_id)
    if not account or account.storage_namespace!=namespace:
        db.rollback(); fail('sign_in_required',401)
    row=db.get(PlayPurchase,digest)
    if row and row.namespace!=namespace:
        db.rollback(); fail('play_purchase_account_mismatch',403)
    if not row:
        row=PlayPurchase(token_hash=digest,namespace=namespace,token_encrypted=encrypted,
                         checked_at=utcnow(),**details)
        db.add(row)
    else:
        row.token_encrypted=encrypted;row.checked_at=utcnow()
        for key,value in details.items(): setattr(row,key,value)
    db.commit()
    return digest


def verify_token(db,account,token):
    namespace=account.storage_namespace; aid=account.id
    data=provider_get(token)
    try:
        details=inspect_purchase(data,namespace)
    except HTTPException:
        row=db.get(PlayPurchase,hashlib.sha256(token.encode()).hexdigest())
        if row and row.namespace==namespace:
            row.entitled=False;row.acknowledged=False;row.checked_at=utcnow()
            row.state='VERIFICATION_REJECTED';db.commit()
        raise
    digest=_write_verified(db,aid,namespace,token,details)
    if details['entitled'] and not details['acknowledged']:
        provider_acknowledge(token,details['product_id'])
        # Re-query Google; neither a client assertion nor a successful POST is enough.
        details=inspect_purchase(provider_get(token),namespace)
        if not details['acknowledged']: fail('play_acknowledgement_pending',503)
        _write_verified(db,aid,namespace,token,details)
    return db.get(PlayPurchase,digest)


def access_until(db,namespace,now=None):
    """Fail closed once verified cache is stale. Does not mutate website grants."""
    now=now or utcnow()
    if not settings()['enabled']: return None
    return db.scalar(select(func.max(PlayPurchase.expires_at)).where(
        PlayPurchase.namespace==namespace,PlayPurchase.entitled.is_(True),
        PlayPurchase.acknowledged.is_(True),PlayPurchase.expires_at>now,
        PlayPurchase.checked_at>now-CACHE_TTL))


def refresh_account(db,account):
    """Bounded per-account S2S reconciliation on membership/lease/guard requests."""
    if not settings()['enabled']: return
    now=utcnow()
    rows=list(db.scalars(select(PlayPurchase).where(PlayPurchase.namespace==account.storage_namespace,
         PlayPurchase.expires_at>now,PlayPurchase.checked_at<=now-CACHE_TTL)
         .order_by(PlayPurchase.checked_at).limit(20)))
    for row in rows:
        try:
            token=cipher().decrypt(row.token_encrypted.encode()).decode()
        except (InvalidToken,UnicodeError): fail('play_billing_unavailable',503)
        raw=provider_get(token)
        if raw.get('_not_found'):
            row.entitled=False;row.checked_at=utcnow();db.commit()
            continue
        verify_token(db,account,token)


@router.get('/config')
def billing_config(request:Request,response:Response,db=Depends(get_db)):
    from .play_choice import config as choice_config
    account=require(request,db)
    response.headers['Cache-Control']='no-store'
    return {'enabled':settings()['enabled'],'package_name':PACKAGE,'auto_renew':False,
            'user_choice':choice_config(),
            'obfuscated_account_id':account_binding(account.storage_namespace),
            'products':[{'plan_id':plan,'product_id':product,'base_plan_id':base}
                        for product,(plan,base) in PRODUCTS.items()]}


@router.post('/verify')
async def billing_verify(request:Request,response:Response,db=Depends(get_db)):
    from starlette.concurrency import run_in_threadpool
    account=require(request,db)
    payload=await body(request)
    if set(payload)!={'purchase_token'}: fail('play_purchase_invalid',400)
    token=payload.get('purchase_token')
    if not isinstance(token,str) or not 16<=len(token)<=4096 or not re.fullmatch(r'[A-Za-z0-9._~+\-/=]+',token):
        fail('play_purchase_invalid',400)
    if not settings()['enabled']: fail('play_billing_unavailable',503)
    rate(db,'play-verify:'+str(account.id),30)
    row=await run_in_threadpool(verify_token,db,account,token)
    response.headers['Cache-Control']='no-store'
    return {'verified':True,'entitled':bool(row.entitled and row.acknowledged),
            'state':row.state,'acknowledged':row.acknowledged,
            'valid_until':row.expires_at.isoformat()+'Z' if row.expires_at else None,
            'plan_id':PRODUCTS[row.product_id][0],'auto_renew':False}
