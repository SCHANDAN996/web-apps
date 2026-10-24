"""Server-only payment inquiry/revocation. Never initiates a charge or refund."""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta
import httpx
from sqlalchemy import select, or_
from .db import SessionLocal
from .payu_models import PayUOrder
from . import payu_payments as pay


def refund_inquiry(order_id, cfg):
    command = 'getAllRefundsFromTxnIds'
    url = ('https://info.payu.in/merchant/postservice.php?form=2' if cfg['production'] else
           'https://test.payu.in/merchant/postservice.php?form=2')
    with httpx.Client(timeout=15, follow_redirects=False, trust_env=False) as client:
        response = client.post(url, data=dict(key=cfg['key'],command=command,var1=order_id,
            hash=pay.sha(f"{cfg['key']}|{command}|{order_id}|{cfg['salt']}")))
        response.raise_for_status()
        if len(response.content) > 200_000: raise ValueError('provider_shape')
        result=response.json()
    if not isinstance(result,dict) or str(result.get('status'))!='1': raise ValueError('provider_shape')
    return result


def refunded_paise(result, provider_id):
    """Parse only documented successful refunds for this precise PayU ID."""
    details=result.get('Refund Details')
    if details is None:
        if result.get('msg') == 'No Refunds Found for the transaction.': return 0
        raise ValueError('provider_shape')
    if not isinstance(details,dict) or set(details) != {str(provider_id)}: raise ValueError('provider_binding')
    rows=details[str(provider_id)]
    if not isinstance(rows,list): raise ValueError('provider_shape')
    seen={}; total=0
    for row in rows:
        if not isinstance(row,dict) or str(row.get('PayuID'))!=str(provider_id): raise ValueError('provider_binding')
        rid=str(row.get('RequestID',''))
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',rid): raise ValueError('provider_shape')
        status=str(row.get('Status','')).upper()
        if status not in ('SUCCESS','FAILURE','QUEUED','IN PROGRESS','REQUESTED','OD_HIT'): raise ValueError('provider_shape')
        amount=pay.paise(row.get('Amount'))
        if amount is None or amount<0: raise ValueError('provider_shape')
        item=(status,amount)
        if rid in seen:
            if seen[rid]!=item: raise ValueError('provider_shape')
            continue
        seen[rid]=item
        if status=='SUCCESS': total+=amount
    return total


def revoke(db, order_id, reason, at, evidence='provider_refund_api'):
    from .membership import revoke_verified_payment
    db.rollback()
    if db.bind.dialect.name=='sqlite': db.connection().exec_driver_sql('BEGIN IMMEDIATE')
    order=db.scalar(select(PayUOrder).where(PayUOrder.id==order_id).with_for_update())
    if not order or order.state not in ('paid','revoked'): db.rollback();return False
    if order.state=='revoked': db.rollback();return True
    revoke_verified_payment(db,'payu:'+order.id,at)
    order.state='revoked';order.revoked_at=at;order.revocation_reason=reason
    order.revocation_evidence=evidence
    db.commit();return True


def reconcile_one(db, order_id, cfg, now):
    order=db.get(PayUOrder,order_id)
    if not order or order.state not in ('pending','paid'): return 'skipped'
    if order.state=='pending':
        tx=pay.provider_verify(order.id,cfg)
        if not pay.verified_match(order,tx): return 'pending'
        result=refund_inquiry(order.id,cfg)
        refunded=refunded_paise(result,tx['mihpayid'])
        if refunded>=order.amount_paise:
            oid=order.id
            db.rollback()
            if db.bind.dialect.name=='sqlite': db.connection().exec_driver_sql('BEGIN IMMEDIATE')
            order=db.scalar(select(PayUOrder).where(PayUOrder.id==oid).with_for_update())
            if not order: db.rollback();return 'skipped'
            if order.state=='paid':
                return 'revoked' if revoke(db,oid,'full_refund',now) else 'skipped'
            if order.state!='pending': db.rollback();return 'skipped'
            from .play_choice import record_capture
            if not record_capture(db, order, tx):
                db.rollback(); return 'provider_timestamp_unavailable'
            order.provider_id = str(tx['mihpayid']); order.verified_at = now
            # No grant ever existed; preserve a terminal local audit state.
            order.state='refunded_ungranted';order.revoked_at=now
            order.revocation_reason='full_refund';order.revocation_evidence='provider_refund_api'
            db.commit();return 'refunded_ungranted'
        if not pay.finalize(db,order.id,tx): return 'pending'
        order=db.get(PayUOrder,order_id)
    else:
        result=refund_inquiry(order.id,cfg)
        refunded=refunded_paise(result,order.provider_id)
    if refunded>=order.amount_paise:
        return 'revoked' if revoke(db,order.id,'full_refund',now) else 'skipped'
    return 'partial_refund_review' if refunded else 'paid'


def run(limit=50, now=None):
    cfg=pay.settings()
    if not cfg['enabled']: raise ValueError('web_payments_unavailable')
    now=now or datetime.utcnow()
    counts={}
    with SessionLocal() as db:
        ids=list(db.scalars(select(PayUOrder.id).where(PayUOrder.state.in_(('pending','paid')),
            or_(PayUOrder.next_check_at.is_(None),PayUOrder.next_check_at<=now))
            .order_by(PayUOrder.next_check_at,PayUOrder.created_at).limit(limit)))
        db.rollback()
        for oid in ids:
            try: outcome=reconcile_one(db,oid,cfg,now)
            except (httpx.HTTPError,ValueError,TypeError,KeyError):
                db.rollback();outcome='provider_unavailable'
            row=db.get(PayUOrder,oid)
            if row:
                row.last_checked_at=now
                # Pending inquiries retry in 5min; old pending orders daily forever
                # rather than silently expiring a delayed real captured payment.
                delay=timedelta(minutes=5) if row.state=='pending' and now-row.created_at<timedelta(days=7) else timedelta(hours=6)
                row.next_check_at=now+delay
                row.reconcile_error=outcome if outcome in ('partial_refund_review','provider_unavailable') else None
                db.commit()
            counts[outcome]=counts.get(outcome,0)+1
    return counts


def operator_revoke(order_id,evidence_ref,reason,confirmed=False):
    """Privileged server operator attestation after merchant-dashboard verification.

    No arbitrary browser endpoint or imported provider webhook is trusted here.
    Evidence reference is an internal case ID, never a PII-containing report.
    """
    if not confirmed or reason not in ('chargeback','full_refund'): raise ValueError('operator_confirmation_required')
    if not re.fullmatch(r'[A-Za-z0-9_-]{6,80}',evidence_ref): raise ValueError('invalid_evidence_reference')
    if not re.fullmatch(r'SS_[a-f0-9]{32}',order_id): raise ValueError('invalid_order')
    with SessionLocal() as db:
        result=revoke(db,order_id,reason,datetime.utcnow(),evidence_ref)
    # Never print customer identity, contacts, credentials or raw provider results.
    return dict(revoked=result,evidence_reference=evidence_ref,reason=reason)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true',help='Explicitly enable local ledger writes')
    parser.add_argument('--limit',type=int,default=50)
    parser.add_argument('--revoke-order')
    parser.add_argument('--reason',choices=['chargeback','full_refund'])
    parser.add_argument('--evidence-reference')
    parser.add_argument('--confirm-dashboard-verified',action='store_true')
    args=parser.parse_args()
    if not args.apply: parser.error('--apply required; inquiries and ledger changes are privileged operations')
    if not 1<=args.limit<=200: parser.error('limit must be 1..200')
    try:
        if args.revoke_order:
            result=operator_revoke(args.revoke_order,args.evidence_reference or '',args.reason,
                                   args.confirm_dashboard_verified)
        else: result=run(args.limit)
    except (ValueError,httpx.HTTPError):
        print(json.dumps({'error':'reconciliation_unavailable'}));return 1
    print(json.dumps(result))
    return 1 if result.get('provider_unavailable') else 0


if __name__=='__main__': sys.exit(main())
