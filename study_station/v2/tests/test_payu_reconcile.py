from datetime import datetime
import pytest
from app import payu_reconcile as rec
from app.payu_models import PayUOrder
from test_payu_payments import checkout, create, transaction


def refunds(pid,rows):
    return {'status':1,'Refund Details':{pid:rows}}


def refund(pid,rid='r1',amount='9.00',status='success'):
    return dict(PayuID=pid,RequestID=rid,Amount=amount,Status=status)


def test_refund_sum_deduplicates():
    row=refund('p')
    assert rec.refunded_paise(refunds('p',[row,row]),'p')==900
    assert rec.refunded_paise(refunds('p',[refund('p',status='QUEUED')]),'p')==0
    assert rec.refunded_paise(refunds('p',[refund('p',amount='4.00'),refund('p','r2','5.00')]),'p')==900


@pytest.mark.parametrize('value',[
    {'status':1,'Refund Details':{'other':[]}},
    {'status':1,'msg':'unknown format'},
    refunds('p',[refund('other')]),refunds('p',[refund('p',amount='NaN')]),
    refunds('p',[refund('p',status='pending-unknown')]),
    refunds('p',[refund('p'),refund('p',amount='1.00')])])
def test_refund_untrusted_shape_rejected(value):
    with pytest.raises(ValueError): rec.refunded_paise(value,'p')


def test_missed_callback_pending_capture_grants(checkout,monkeypatch,db):
    order=create(checkout).json();tx=transaction(order)
    monkeypatch.setattr(rec.pay,'provider_verify',lambda *a:tx)
    monkeypatch.setattr(rec,'refund_inquiry',lambda *a:{'status':1,'msg':'No Refunds Found for the transaction.'})
    assert rec.reconcile_one(db,order['order_id'],{},datetime.utcnow())=='paid'
    db.expire_all();assert db.get(PayUOrder,order['order_id']).state=='paid'


def test_pending_already_refunded_never_grants(checkout,monkeypatch,db):
    from app.membership_models import MembershipGrant
    order=create(checkout).json();tx=transaction(order)
    monkeypatch.setattr(rec.pay,'provider_verify',lambda *a:tx)
    monkeypatch.setattr(rec,'refund_inquiry',lambda *a:refunds(tx['mihpayid'],[refund(tx['mihpayid'])]))
    assert rec.reconcile_one(db,order['order_id'],{},datetime.utcnow())=='refunded_ungranted'
    assert db.get(MembershipGrant,'payu:'+order['order_id']) is None


def test_full_refund_revokes_only_owned_grant(checkout,monkeypatch,db):
    from app.membership_models import MembershipGrant
    order=create(checkout).json();tx=transaction(order)
    assert rec.pay.finalize(db,order['order_id'],tx)
    monkeypatch.setattr(rec,'refund_inquiry',lambda *a:refunds(tx['mihpayid'],[refund(tx['mihpayid'])]))
    assert rec.reconcile_one(db,order['order_id'],{},datetime.utcnow())=='revoked'
    db.expire_all()
    assert db.get(PayUOrder,order['order_id']).state=='revoked'
    assert db.get(MembershipGrant,'payu:'+order['order_id']).revoked_at is not None
    assert rec.reconcile_one(db,order['order_id'],{},datetime.utcnow())=='skipped'


def test_partial_refund_does_not_revoke(checkout,monkeypatch,db):
    order=create(checkout).json();tx=transaction(order)
    assert rec.pay.finalize(db,order['order_id'],tx)
    monkeypatch.setattr(rec,'refund_inquiry',lambda *a:refunds(tx['mihpayid'],[refund(tx['mihpayid'],amount='1.00')]))
    assert rec.reconcile_one(db,order['order_id'],{},datetime.utcnow())=='partial_refund_review'
    assert db.get(PayUOrder,order['order_id']).state=='paid'


def test_operator_requires_explicit_evidence_confirmation():
    with pytest.raises(ValueError): rec.operator_revoke('SS_'+'a'*32,'CASE123','chargeback')
    with pytest.raises(ValueError): rec.operator_revoke('SS_'+'a'*32,'email@example.com','chargeback',True)


def test_provider_outage_prevents_pending_grant(checkout,monkeypatch,db):
    order=create(checkout).json();tx=transaction(order)
    monkeypatch.setattr(rec.pay,'provider_verify',lambda *a:tx)
    def unavailable(*a): raise ValueError('invalid shape')
    monkeypatch.setattr(rec,'refund_inquiry',unavailable)
    with pytest.raises(ValueError):rec.reconcile_one(db,order['order_id'],{},datetime.utcnow())
    db.rollback();assert db.get(PayUOrder,order['order_id']).state=='pending'
