"""PayU hosted WEB checkout only. No browser callback can grant access alone."""
import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, urlparse
import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from .classroom import body, require, fail, rate
from .classroom_models import ClassroomAccount
from .db import get_db
from .payu_models import PayUOrder
from .payu_i18n import STRINGS
from starlette.concurrency import run_in_threadpool

router = APIRouter()
PLANS = {'monthly': 900, 'yearly': 5100}
PRODUCTS = {'monthly': 'Study Station monthly access', 'yearly': 'Study Station yearly access'}


def settings():
    """Enable the browser website checkout deployment, independently of native UI.

    Native Play screens must use eligible Play Billing. Website routes can share
    its HTTPS origin; native clients must not display hosted checkout/steering.
    No client platform flag changes authorization or payment verification.
    """
    origin = os.environ.get('SS_PAYU_WEB_ORIGIN', '').rstrip('/')
    parsed = urlparse(origin)
    allowed = (os.environ.get('SS_PAYU_WEB_ENABLED') == '1' and
               os.environ.get('SS_PAYMENT_CHANNEL') == 'website' and
               parsed.scheme == 'https' and bool(parsed.netloc) and
               not parsed.username and not parsed.password and parsed.path == '' and
               not parsed.query and not parsed.fragment)
    key = os.environ.get('SS_PAYU_MERCHANT_KEY', '')
    salt = os.environ.get('SS_PAYU_MERCHANT_SALT', '')
    env = os.environ.get('SS_PAYU_ENV', 'test')
    return dict(enabled=bool(allowed and key and salt and env in ('test', 'production')),
                origin=origin, key=key, salt=salt, production=env == 'production')


def sha(value):
    return hashlib.sha512(value.encode('utf-8')).hexdigest()


def request_hash(fields, salt):
    sequence = [fields.get(k, '') for k in ('key', 'txnid', 'amount', 'productinfo',
                'firstname', 'email', 'udf1', 'udf2', 'udf3', 'udf4', 'udf5')]
    return sha('|'.join(sequence + [''] * 5 + [salt]))


def response_valid(fields, cfg):
    if fields.get('key') != cfg['key']: return False
    seq = [cfg['salt'], fields.get('status', '')] + [''] * 5
    seq += [fields.get(k, '') for k in ('udf5', 'udf4', 'udf3', 'udf2', 'udf1',
                                      'email', 'firstname', 'productinfo', 'amount', 'txnid', 'key')]
    # PayU uses additionalCharges in form callbacks (additional_charges in JSON).
    extra = fields.get('additionalCharges', fields.get('additional_charges', ''))
    if extra: seq.insert(0, extra)
    expected = sha('|'.join(seq))
    actual = fields.get('hash', '').lower()
    return bool(re.fullmatch('[a-f0-9]{128}', actual) and hmac.compare_digest(expected, actual))


def paise(value):
    try:
        number = Decimal(str(value)) * 100
        if not number.is_finite() or number != number.to_integral_value(): return None
        return int(number)
    except (InvalidOperation, ValueError): return None


def provider_verify(txnid, cfg):
    endpoint = ('https://info.payu.in/merchant/postservice.php?form=2' if cfg['production']
                else 'https://test.payu.in/merchant/postservice.php?form=2')
    with httpx.Client(timeout=15, follow_redirects=False, trust_env=False) as client:
        response = client.post(endpoint, data=dict(key=cfg['key'], command='verify_payment',
            var1=txnid, hash=sha(f"{cfg['key']}|verify_payment|{txnid}|{cfg['salt']}")))
        response.raise_for_status()
        if len(response.content) > 200_000: raise ValueError('oversize verification')
        result = response.json()
    if not isinstance(result, dict) or str(result.get('status')) != '1': return None
    tx = result.get('transaction_details', {}).get(txnid)
    return tx if isinstance(tx, dict) else None


def verified_match(order, tx):
    # PayU domestic hosted checkout is INR; if currency is supplied require INR.
    # Never grant on auth/pending or on callback status without this S2S record.
    return bool(tx and tx.get('txnid') == order.id and
        tx.get('status') == 'success' and tx.get('unmappedstatus') == 'captured' and
        paise(tx.get('amt')) == order.amount_paise and
        tx.get('currency', 'INR') == 'INR' and
        tx.get('productinfo') == PRODUCTS.get(order.plan_id) and
        tx.get('udf1') == order.binding and tx.get('udf2') == str(order.account_id) and
        tx.get('udf3') == order.plan_id and
        bool(re.fullmatch(r'[A-Za-z0-9_-]{1,64}', str(tx.get('mihpayid', '')))))


def finalize(db, order_id, tx):
    """Claim and grant atomically. No commits inside the membership service."""
    db.rollback()  # callbacks/status did reads; acquire SQLite writer before reread
    if db.bind.dialect.name == 'sqlite': db.connection().exec_driver_sql('BEGIN IMMEDIATE')
    order = db.scalar(select(PayUOrder).where(PayUOrder.id == order_id).with_for_update())
    if not order or not verified_match(order, tx):
        db.rollback(); return False
    account = db.get(ClassroomAccount, order.account_id)
    if not account or account.storage_namespace != order.account_namespace:
        db.rollback(); return False
    if order.state == 'paid':
        same = order.provider_id == str(tx['mihpayid']); db.rollback(); return same
    if order.state != 'pending': db.rollback(); return False
    from .play_choice import record_capture
    if not record_capture(db, order, tx):
        db.rollback(); return False
    from .membership import grant_verified_payment
    now = datetime.utcnow()
    grant_verified_payment(db, account.id, order.plan_id, 'payu:' + order.id, now)
    order.state = 'paid'; order.provider_id = str(tx['mihpayid']); order.verified_at = now
    db.commit()
    return True


@router.get('/api/v1/payments/payu/config')
def payment_config():
    return dict(enabled=settings()['enabled'], channel='website', auto_renew=False,
                plans=[dict(id=k, amount_paise=v, currency='INR') for k,v in PLANS.items()])


@router.post('/api/v1/payments/payu/orders')
async def create_order(request: Request, db=Depends(get_db)):
    cfg = settings()
    if not cfg['enabled']: fail('web_payments_unavailable', 503)
    # Configured website origin required; absent Origin is rejected for creation.
    if request.headers.get('origin') != cfg['origin']: fail('origin_rejected', 403)
    account = require(request, db)
    data = await body(request)
    if data.get('contact_consent') is not True: fail('payment_contact_consent_required')
    plan = data.get('plan_id')
    if plan not in PLANS: fail('invalid_plan')
    name, email, phone = (data.get(k, '') for k in ('name', 'email', 'phone'))
    if not isinstance(name, str) or not 2 <= len(name.strip()) <= 80 or '|' in name: fail('invalid_name')
    if not isinstance(email, str) or not re.fullmatch(r'[^\s|@]{1,100}@[^\s|@]{1,100}\.[^\s|@]{2,30}', email): fail('invalid_email')
    if not isinstance(phone, str) or not re.fullmatch(r'[6-9][0-9]{9}', phone): fail('invalid_phone')
    rate(db, 'payment-create:' + str(account.id), 6)
    order = PayUOrder(id='SS_' + secrets.token_hex(16), account_id=account.id,
        account_namespace=account.storage_namespace, plan_id=plan, amount_paise=PLANS[plan],
        currency='INR', binding=secrets.token_hex(24), state='pending')
    if data.get('play_choice_id'):
        from .play_choice import bind_order
        # A choice is single-use even across simultaneous checkout requests.
        aid, namespace = account.id, account.storage_namespace
        db.rollback()
        if db.bind.dialect.name == 'sqlite': db.connection().exec_driver_sql('BEGIN IMMEDIATE')
        account = db.get(ClassroomAccount, aid)
        if not account or account.storage_namespace != namespace: fail('sign_in_required', 401)
        bind_order(db, account, data, order)
    db.add(order); db.commit()
    fields = dict(key=cfg['key'], txnid=order.id, amount=f'{order.amount_paise/100:.2f}',
        productinfo=PRODUCTS[plan], firstname=name.strip(), email=email, phone=phone,
        surl=cfg['origin'] + '/payments/payu/return', furl=cfg['origin'] + '/payments/payu/return',
        udf1=order.binding, udf2=str(account.id), udf3=plan, udf4='', udf5='')
    fields['hash'] = request_hash(fields, cfg['salt'])
    return dict(order_id=order.id, action_url=('https://secure.payu.in/_payment' if cfg['production']
                else 'https://test.payu.in/_payment'), fields=fields, auto_renew=False)


@router.post('/payments/payu/return')
@router.post('/payments/payu/webhook')
async def callback(request: Request, db=Depends(get_db)):
    cfg = settings()
    if not cfg['enabled']: fail('web_payments_unavailable', 503)
    if request.headers.get('content-type', '').split(';')[0].strip() != 'application/x-www-form-urlencoded':
        fail('form_required', 415)
    raw = await request.body()
    if len(raw) > 20_000: fail('payload_too_large', 413)
    try:
        parsed = parse_qs(raw.decode('utf-8'), keep_blank_values=True, max_num_fields=80)
        if any(len(v) != 1 for v in parsed.values()): fail('duplicate_fields')
        fields = {k:v[0] for k,v in parsed.items()}
    except (ValueError, UnicodeError): fail('invalid_form')
    if not response_valid(fields, cfg): fail('payment_signature_invalid', 400)
    order_id = fields.get('txnid', '')
    order = db.get(PayUOrder, order_id)
    if not order or fields.get('udf1') != order.binding or paise(fields.get('amount')) != order.amount_paise:
        fail('payment_order_invalid', 400)
    paid = False
    try:
        tx = await run_in_threadpool(provider_verify, order_id, cfg)
        paid = finalize(db, order_id, tx)
    except (httpx.HTTPError, ValueError): db.rollback()
    # No account/session side effects, token, PII or raw provider response in URL/UI.
    bilingual = lambda key: ' / '.join(STRINGS[key])
    heading = bilingual('payu_verified' if paid else 'payu_pending')
    detail = bilingual('payu_active_detail' if paid else 'payu_pending_detail')
    html = f'''<!doctype html><html lang="hi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Study Station — Payment</title><body style="font:18px system-ui;background:#f5f6fa;color:#182133;margin:0;padding:24px">
    <main style="max-width:520px;margin:12vh auto;padding:28px;border-radius:24px;background:white"><h1 style="font-size:24px">{heading}</h1><p>{detail}</p>
    <a href="/classroom" style="display:inline-block;padding:14px;border-radius:14px;background:#254bbc;color:white">Study Station</a>
    <p style="font-size:14px">{bilingual('payu_no_renew')}</p></main></body></html>'''
    return HTMLResponse(html, headers={'Cache-Control':'no-store', 'Referrer-Policy':'no-referrer',
        'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'"})


@router.get('/api/v1/payments/payu/orders/{order_id}')
def order_status(order_id: str, request: Request, db=Depends(get_db)):
    account = require(request, db)
    order = db.get(PayUOrder, order_id)
    if not order or order.account_id != account.id or order.account_namespace != account.storage_namespace:
        fail('order_not_found', 404)
    return dict(order_id=order.id, state=order.state, plan_id=order.plan_id,
                amount_paise=order.amount_paise, currency=order.currency, auto_renew=False)
