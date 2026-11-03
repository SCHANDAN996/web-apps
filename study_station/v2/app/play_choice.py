"""India SDK user-choice checkout gate and durable external transaction reporting.

Disabled until enrollment, credentials and accountant-approved tax split are set.
No payment is initiated by this module; only verified PayU captures are reported.
"""
import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import quote
from fastapi import Depends, Request, Response
from sqlalchemy import select, delete
from . import play_billing as play
from .classroom import require, body, fail, rate
from .db import get_db
from .play_choice_models import PlayChoice
from .payu_models import PayUOrder

STATES = ('ANDAMAN AND NICOBAR ISLANDS|ANDHRA PRADESH|ARUNACHAL PRADESH|ASSAM|BIHAR|'
          'CHANDIGARH|CHHATTISGARH|DADRA AND NAGAR HAVELI|DADRA AND NAGAR HAVELI AND DAMAN AND DIU|'
          'DAMAN AND DIU|DELHI|GOA|GUJARAT|HARYANA|HIMACHAL PRADESH|JAMMU AND KASHMIR|'
          'JHARKHAND|KARNATAKA|KERALA|LADAKH|LAKSHADWEEP|MADHYA PRADESH|MAHARASHTRA|'
          'MANIPUR|MEGHALAYA|MIZORAM|NAGALAND|ODISHA|PUDUCHERRY|PUNJAB|RAJASTHAN|SIKKIM|'
          'TAMIL NADU|TELANGANA|TRIPURA|UTTAR PRADESH|UTTARAKHAND|WEST BENGAL').split('|')


def settings():
    from .payu_payments import settings as payu_settings
    raw = os.environ.get('SS_PLAY_UCB_TAX_BPS', '')
    tax = int(raw) if re.fullmatch(r'\d{1,4}', raw) else None
    offset = os.environ.get('SS_PLAY_UCB_PROVIDER_UTC_OFFSET', '')
    offset_valid = bool(re.fullmatch(r'[+-](?:0\d|1[0-4]):[0-5]\d', offset))
    retention = os.environ.get('SS_PLAY_UCB_RETENTION_DAYS', '')
    retention_days = int(retention) if re.fullmatch(r'[1-9]\d{0,3}', retention) else None
    capture_confirmed = (os.environ.get('SS_PLAY_UCB_CAPTURE_TIME_CONFIRMED') == '1' and
        os.environ.get('SS_PLAY_UCB_CAPTURE_TIME_SEMANTICS_CONFIRMED') == '1' and
        os.environ.get('SS_PLAY_UCB_CAPTURE_TIME_FIELD') == 'addedon' and offset_valid)
    enabled = (os.environ.get('SS_PLAY_UCB_ENABLED') == '1' and
               os.environ.get('SS_PLAY_UCB_ENROLLED_IN') == '1' and
               os.environ.get('SS_PLAY_UCB_RETENTION_APPROVED') == '1' and retention_days is not None and
               capture_confirmed and
               play.settings()['enabled'] and payu_settings()['enabled'] and tax is not None)
    return {'enabled': bool(enabled), 'tax_bps': tax, 'provider_offset': offset,
            'capture_confirmed': capture_confirmed, 'retention_days': retention_days}


def config():
    return {'enabled': settings()['enabled'], 'countries': ['IN']}


@play.router.get('/alternative/checkout')
def checkout(choice_id: str, request: Request, response: Response, db=Depends(get_db)):
    account = require(request, db)
    if not settings()['enabled']: fail('play_billing_unavailable', 503)
    row = db.get(PlayChoice, choice_id) if re.fullmatch(r'[A-Za-z0-9_-]{20,64}', choice_id) else None
    if (not row or row.namespace != account.storage_namespace or row.order_id or
        row.expires_at <= datetime.utcnow()): fail('play_purchase_invalid', 404)
    response.headers['Cache-Control'] = 'no-store'
    return {'enabled': True, 'choice_id': row.id, 'plan_id': row.plan_id, 'states': STATES,
            'expires_at': row.expires_at.isoformat() + 'Z'}


@play.router.post('/alternative/start')
async def start(request: Request, response: Response, db=Depends(get_db)):
    account = require(request, db)
    data = await body(request)
    if not settings()['enabled']: fail('play_billing_unavailable', 503)
    required = {'external_transaction_token', 'plan_id', 'product_id', 'base_plan_id', 'country_code'}
    if set(data) != required: fail('play_purchase_invalid', 400)
    token = data['external_transaction_token']; product = data['product_id']
    if (not isinstance(token, str) or not 16 <= len(token) <= 4096 or
        not re.fullmatch(r'[A-Za-z0-9._~+\-/=]+', token) or not isinstance(product, str) or
        product not in play.PRODUCTS or play.PRODUCTS[product] != (data['plan_id'], data['base_plan_id']) or
        data['country_code'] != 'IN'): fail('play_purchase_invalid', 400)
    rate(db, 'play-choice:' + str(account.id), 10)
    digest = hashlib.sha256(token.encode()).hexdigest()
    now = datetime.utcnow()
    db.rollback()
    if db.bind.dialect.name == 'sqlite': db.connection().exec_driver_sql('BEGIN IMMEDIATE')
    row = db.scalar(select(PlayChoice).where(PlayChoice.token_hash == digest))
    if row:
        if row.namespace != account.storage_namespace or row.plan_id != data['plan_id']:
            db.rollback(); fail('play_purchase_account_mismatch', 403)
        if row.order_id or row.expires_at <= now:
            db.rollback(); fail('play_purchase_invalid', 400)
    else:
        row = PlayChoice(id=secrets.token_urlsafe(32), namespace=account.storage_namespace,
            token_hash=digest, token_encrypted=play.cipher().encrypt(token.encode()).decode(),
            plan_id=data['plan_id'], expires_at=now + timedelta(minutes=15))
        db.add(row)
    db.commit()
    response.headers['Cache-Control'] = 'no-store'
    return {'choice_id': row.id, 'checkout_url': '/membership?play_choice=' + row.id,
            'expires_at': row.expires_at.isoformat() + 'Z', 'auto_renew': False}


def bind_order(db, account, data, order):
    """Called inside the same writer transaction that inserts the PayU order."""
    cid = data.get('play_choice_id')
    if not cid: return
    if not settings()['enabled']: fail('play_billing_unavailable', 503)
    if not isinstance(cid, str): fail('play_purchase_invalid', 400)
    row = db.get(PlayChoice, cid)
    if (not row or row.namespace != account.storage_namespace or row.order_id or
        row.expires_at <= datetime.utcnow() or row.plan_id != order.plan_id):
        fail('play_purchase_invalid', 400)
    state = data.get('billing_state')
    if state not in STATES: fail('play_tax_address_required', 400)
    row.order_id = order.id; row.administrative_area = state
    row.amount_paise = order.amount_paise
    row.provider_binding = order.binding
    row.provider_account_hash = provider_account_digest(account.id)
    # Prices include tax. This rate MUST be supplied by the merchant/accountant.
    gross = Decimal(order.amount_paise)
    pre = int((gross * 10000 / (10000 + settings()['tax_bps'])).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    row.pretax_paise = pre; row.tax_paise = order.amount_paise - pre


def price(paise):
    return {'currency': 'INR', 'priceMicros': str(paise * 10000)}


def provider_account_digest(value):
    # A bare digest of a sequential account ID is reversible by enumeration.
    key = Path(play.settings()['token_key_file']).read_bytes().strip()
    return hmac.new(key, ('payu-udf2:' + str(value)).encode(), hashlib.sha256).hexdigest()


def external_id(row):
    return 'ss_' + hashlib.sha256(row.id.encode()).hexdigest()[:48]


def record_capture(db, order, tx):
    """Only merchant-confirmed S2S completion field/zone; never browser time."""
    row = db.scalar(select(PlayChoice).where(PlayChoice.order_id == order.id))
    if not row: return True  # existing website/direct orders are unchanged
    cfg = settings()
    if not cfg['capture_confirmed']: return False
    try:
        captured = provider_timestamp(tx['addedon'])
        if captured > datetime.utcnow() + timedelta(minutes=5) or captured < order.created_at - timedelta(minutes=5):
            return False
    except (KeyError, TypeError, ValueError): return False
    row.captured_at = captured
    row.provider_id = str(tx['mihpayid']); row.amount_paise = order.amount_paise
    return True


def provider_timestamp(value):
    cfg = settings()
    if not cfg['capture_confirmed']: raise ValueError('provider_timezone_unconfirmed')
    stamp = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    offset = cfg['provider_offset']; sign = 1 if offset[0] == '+' else -1
    delta = timedelta(hours=int(offset[1:3]), minutes=int(offset[4:6])) * sign
    return stamp.replace(tzinfo=timezone(delta)).astimezone(timezone.utc).replace(tzinfo=None)


def report_payload(row, order, token):
    if (not row.captured_at or not row.provider_id or
        row.pretax_paise is None or row.tax_paise is None or
        row.pretax_paise + row.tax_paise != row.amount_paise or
        row.administrative_area not in STATES): raise ValueError('unverified_payment')
    return {'originalPreTaxAmount': price(row.pretax_paise), 'originalTaxAmount': price(row.tax_paise),
            'transactionTime': row.captured_at.isoformat() + 'Z',
            'userTaxAddress': {'regionCode': 'IN', 'administrativeArea': row.administrative_area},
            'recurringTransaction': {'externalTransactionToken': token,
                'externalSubscription': {'subscriptionType': 'PREPAID'}}}


def reconcile_one(db, row, now=None):
    """Retry the same opaque Google ID, including timeout-after-success recovery."""
    from .payu_reconcile import refund_inquiry, refunded_paise
    from .payu_payments import settings as payu_settings
    now = now or datetime.utcnow()
    order = db.get(PayUOrder, row.order_id) if row.order_id else None
    if not row.captured_at or not row.provider_id:
        # Account deletion must not erase a late real capture's report obligation.
        from .payu_payments import provider_verify, paise, PRODUCTS
        tx = provider_verify(row.order_id, payu_settings())
        valid = (isinstance(tx, dict) and tx.get('txnid') == row.order_id and
            tx.get('status') == 'success' and tx.get('unmappedstatus') == 'captured' and
            tx.get('currency', 'INR') == 'INR' and paise(tx.get('amt')) == row.amount_paise and
            tx.get('productinfo') == PRODUCTS.get(row.plan_id) and tx.get('udf1') == row.provider_binding and
            hmac.compare_digest(provider_account_digest(tx.get('udf2')), row.provider_account_hash or '') and
            tx.get('udf3') == row.plan_id and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', str(tx.get('mihpayid', ''))))
        if not valid:
            row.next_check_at = now + timedelta(minutes=5); db.commit()
            return 'waiting_payment'
        captured = provider_timestamp(tx.get('addedon'))
        if captured > now + timedelta(minutes=5) or captured < row.created_at - timedelta(minutes=5):
            raise ValueError('capture_timestamp_invalid')
        row.captured_at = captured; row.provider_id = str(tx['mihpayid']); db.commit()
    path = '/externalTransactions/' + quote(external_id(row), safe='')
    result = play.provider_request('GET', path)
    if result.get('_not_found'):
        token = play.cipher().decrypt(row.token_encrypted.encode()).decode()
        payload = report_payload(row, order, token)
        result = play.provider_request('POST', '/externalTransactions?externalTransactionId=' + external_id(row), payload)
    if (result.get('externalTransactionId') != external_id(row) or
        result.get('packageName') != play.PACKAGE or
        result.get('originalPreTaxAmount') != price(row.pretax_paise) or
        result.get('originalTaxAmount') != price(row.tax_paise)):
        raise ValueError('report_binding')
    row.reported_at = row.reported_at or now
    # Provider inquiry remains the only source of refund totals. No client amount.
    refund_result = refund_inquiry(row.order_id, payu_settings())
    refunded = refunded_paise(refund_result, row.provider_id)
    if refunded > row.amount_paise: raise ValueError('refund_amount')
    if refunded > row.refunded_paise:
        refund = {'refundTime': verified_refund_time(refund_result, row.provider_id, row.captured_at, now)}
        if refunded == row.amount_paise:
            refund['fullRefund'] = {}
        else:
            cumulative = row.pretax_paise * refunded // row.amount_paise
            prior = row.pretax_paise * row.refunded_paise // row.amount_paise
            refund['partialRefund'] = {'refundId': 'r_' + str(refunded),
                                      'refundPreTaxAmount': price(cumulative - prior)}
        # GET current amounts first, so retry after a lost response is idempotent.
        target = row.pretax_paise - row.pretax_paise * refunded // row.amount_paise
        current = result.get('currentPreTaxAmount', {})
        if current != price(target):
            play.provider_request('POST', path + ':refund', refund)
            checked = play.provider_request('GET', path)
            if checked.get('currentPreTaxAmount') != price(target):
                raise ValueError('refund_pending')
        row.refunded_paise = refunded
    row.last_error = None; row.next_check_at = now + timedelta(minutes=5)
    db.commit()
    return 'reported'


def verified_refund_time(result, provider_id, captured_at, now):
    # PayU documents success_at separately from RefundCreationDate. The latter
    # is only request creation and must never be substituted for refund time.
    rows = result.get('Refund Details', {}).get(str(provider_id), [])
    stamps = []
    for item in rows:
        if str(item.get('Status', '')).upper() != 'SUCCESS': continue
        try: stamp = provider_timestamp(item['success_at'])
        except (KeyError, ValueError, TypeError): raise ValueError('refund_timestamp_unavailable')
        if stamp < captured_at or stamp > now + timedelta(minutes=5):
            raise ValueError('refund_timestamp_invalid')
        stamps.append(stamp)
    if not stamps: raise ValueError('refund_timestamp_unavailable')
    return max(stamps).isoformat() + 'Z'


def detach_account(db, namespace, now=None):
    """Keep only the minimum reporting snapshot; erase all account linkage."""
    # The operator declined post-deletion payment retention. The dormant option
    # must never preserve a snapshot without a separate explicit policy approval.
    if os.environ.get('SS_PLAY_UCB_RETENTION_APPROVED') != '1':
        db.execute(delete(PlayChoice).where(PlayChoice.namespace == namespace))
        return
    now = now or datetime.utcnow()
    rows = list(db.scalars(select(PlayChoice).where(PlayChoice.namespace == namespace)))
    for row in rows:
        if not row.order_id:
            db.delete(row); continue
        row.namespace = 'deleted_' + secrets.token_hex(24)
        row.account_deleted_at = now
        # Enabling checkout requires a separately approved financial retention.
        days = settings()['retention_days']
        row.purge_after = now + timedelta(days=days or 14)


def run(limit=50, now=None):
    """Run every five minutes; deadline breaches are visible, never silently dropped."""
    from .db import SessionLocal
    if not settings()['enabled']: raise ValueError('play_billing_unavailable')
    now = now or datetime.utcnow(); counts = {}
    with SessionLocal() as db:
        expired = list(db.scalars(select(PlayChoice).where(PlayChoice.purge_after <= now).limit(200)))
        for row in expired:
            if not row.reported_at: counts['retention_deadline_alert'] = counts.get('retention_deadline_alert', 0) + 1
            db.delete(row)
        db.commit()
        rows = list(db.scalars(select(PlayChoice).where(PlayChoice.order_id.is_not(None),
            (PlayChoice.next_check_at.is_(None)) | (PlayChoice.next_check_at <= now))
            .order_by(PlayChoice.next_check_at.asc().nullsfirst(), PlayChoice.created_at).limit(limit)))
        for row in rows:
            try: outcome = reconcile_one(db, row, now)
            except Exception:
                # Never log SDK token, provider URL, response, contacts or exception.
                db.rollback(); row = db.get(PlayChoice, row.id)
                row.last_error = 'report_unavailable'; row.next_check_at = now + timedelta(minutes=5)
                db.commit(); outcome = 'report_unavailable'
            if row.captured_at and not row.reported_at and now - row.captured_at >= timedelta(hours=20):
                counts['deadline_alert'] = counts.get('deadline_alert', 0) + 1
            counts[outcome] = counts.get(outcome, 0) + 1
    return counts


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply: parser.error('--apply required')
    counts = run()
    print(json.dumps(counts))
    raise SystemExit(1 if any(counts.get(k) for k in ('report_unavailable', 'deadline_alert', 'retention_deadline_alert')) else 0)
