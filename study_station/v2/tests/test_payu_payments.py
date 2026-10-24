import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app import payu_payments as pay
from app import config
from app.classroom import router as accounts
from app.classroom_models import ClassroomRate
from app.db import Base, engine
from app.payu_models import PayUOrder


@pytest.fixture
def checkout(db, monkeypatch):
    Base.metadata.create_all(engine)
    db.query(ClassroomRate).delete(); db.commit()
    for key, value in {'SS_PAYU_WEB_ENABLED':'1', 'SS_PAYMENT_CHANNEL':'website',
        'SS_PAYU_WEB_ORIGIN':'https://payments.example', 'SS_PAYU_MERCHANT_KEY':'test-key',
        'SS_PAYU_MERCHANT_SALT':'test-salt', 'SS_PAYU_ENV':'test'}.items(): monkeypatch.setenv(key,value)
    monkeypatch.setattr(config, 'SITE_URL', 'https://payments.example')
    app=FastAPI(); app.include_router(accounts); app.include_router(pay.router)
    with TestClient(app) as c:
        assert c.post('/api/v1/classroom/signup',json={'username':'pay'+uuid.uuid4().hex[:12],
            'password':'long-safe-password'}).status_code == 200
        yield c


def create(c, **changes):
    data=dict(plan_id='monthly', contact_consent=True,name='Test Student',
              email='test@example.com',phone='9876543210')
    data.update(changes)
    return c.post('/api/v1/payments/payu/orders',json=data,headers={'Origin':'https://payments.example'})


def transaction(order):
    f=order['fields']
    return dict(txnid=f['txnid'],status='success',unmappedstatus='captured',amt=f['amount'],
        productinfo=f['productinfo'],udf1=f['udf1'],udf2=f['udf2'],udf3=f['udf3'],mihpayid=uuid.uuid4().hex)


def callback_fields(order):
    f=dict(order['fields'],status='success')
    seq=['test-salt','success']+['']*5+[f.get(k,'') for k in
        ('udf5','udf4','udf3','udf2','udf1','email','firstname','productinfo','amount','txnid','key')]
    f['hash']=pay.sha('|'.join(seq))
    return f


def test_server_owned_price_and_no_contact_storage(checkout, db):
    r=create(checkout,amount=1,currency='USD',account_id=999)
    assert r.status_code==200,r.text
    o=r.json(); assert o['fields']['amount']=='9.00'
    row=db.get(PayUOrder,o['order_id'])
    assert row.amount_paise==900 and row.currency=='INR'
    assert 'email' not in row.__table__.columns and 'phone' not in row.__table__.columns
    assert 'test-salt' not in r.text and o['fields']['hash']==pay.request_hash(o['fields'],'test-salt')
    assert create(checkout,plan_id='yearly').json()['fields']['amount']=='51.00'


@pytest.mark.parametrize('field,value',[('plan_id','arbitrary'),('contact_consent',False),
    ('phone','123'),('email','bad'),('name','x|tamper')])
def test_invalid_checkout(checkout, field,value):
    assert create(checkout,**{field:value}).status_code==400


def test_disabled_and_origin(checkout,monkeypatch):
    assert checkout.post('/api/v1/payments/payu/orders',json={}).status_code==403
    monkeypatch.setenv('SS_PAYMENT_CHANNEL','play')
    assert create(checkout).status_code==503
    monkeypatch.setenv('SS_PAYMENT_CHANNEL','website'); monkeypatch.delenv('SS_PAYU_WEB_ENABLED')
    assert checkout.get('/api/v1/payments/payu/config').json()['enabled'] is False


def test_callback_requires_hash_and_server_verification(checkout,monkeypatch,db):
    o=create(checkout).json(); called=[]
    monkeypatch.setattr(pay,'provider_verify',lambda *args: called.append(1) or None)
    assert checkout.post('/payments/payu/return',data=dict(o['fields'],status='success')).status_code==400
    assert called==[]
    r=checkout.post('/payments/payu/return',data=callback_fields(o))
    assert r.status_code==200 and 'Verification pending' in r.text
    db.expire_all(); assert db.get(PayUOrder,o['order_id']).state=='pending'


@pytest.mark.parametrize('field,value',[('txnid','another'),('amt','1.00'),('currency','USD'),
    ('unmappedstatus','auth'),('status','failure'),('udf1','wrong'),('udf2','999'),
    ('udf3','yearly'),('productinfo','Other product')])
def test_s2s_binding_rejects_mismatch(checkout,db,field,value):
    o=create(checkout).json(); tx=transaction(o);tx[field]=value
    assert pay.finalize(db,o['order_id'],tx) is False
    assert db.get(PayUOrder,o['order_id']).state=='pending'


def test_verified_grant_atomic_and_idempotent(checkout,monkeypatch,db):
    from app import membership
    called=[]
    monkeypatch.setattr(membership,'grant_verified_payment',lambda *args: called.append(args))
    o=create(checkout).json();tx=transaction(o)
    assert pay.finalize(db,o['order_id'],tx)
    assert pay.finalize(db,o['order_id'],tx)
    assert len(called)==1
    assert checkout.get('/api/v1/payments/payu/orders/'+o['order_id']).json()['state']=='paid'
    # Same order cannot be rebound to another provider transaction after payment.
    tx['mihpayid']='different'; assert not pay.finalize(db,o['order_id'],tx)


def test_other_account_cannot_read_order(checkout):
    o=create(checkout).json()
    checkout.post('/api/v1/classroom/logout',json={})
    checkout.post('/api/v1/classroom/signup',json={'username':'other'+uuid.uuid4().hex[:12],
        'password':'long-safe-password'})
    assert checkout.get('/api/v1/payments/payu/orders/'+o['order_id']).status_code==404


def test_provider_failure_never_grants(checkout,monkeypatch,db):
    o=create(checkout).json()
    def unavailable(*args): raise ValueError('not json')
    monkeypatch.setattr(pay,'provider_verify',unavailable)
    r=checkout.post('/payments/payu/return',data=callback_fields(o))
    assert r.status_code==200
    db.expire_all();assert db.get(PayUOrder,o['order_id']).state=='pending'


def test_additional_charge_reverse_hash():
    fields=dict(key='key',status='success',txnid='txn',amount='9.00',additionalCharges='1.00')
    sequence=['1.00','salt','success']+['']*5+['']*8+['9.00','txn','key']
    fields['hash']=pay.sha('|'.join(sequence))
    assert pay.response_valid(fields,dict(key='key',salt='salt'))


def test_grant_failure_rolls_back_with_no_paid_ledger(checkout,monkeypatch,db):
    from app import membership
    o=create(checkout).json()
    def failure(*args): raise ValueError('grant failed')
    monkeypatch.setattr(membership,'grant_verified_payment',failure)
    monkeypatch.setattr(pay,'provider_verify',lambda *args: transaction(o))
    r=checkout.post('/payments/payu/webhook',data=callback_fields(o))
    assert r.status_code==200
    db.expire_all();assert db.get(PayUOrder,o['order_id']).state=='pending'


def test_real_membership_grant_once(checkout,db):
    from app.membership_models import MembershipGrant
    o=create(checkout).json(); tx=transaction(o)
    assert pay.finalize(db,o['order_id'],tx)
    assert pay.finalize(db,o['order_id'],tx)
    assert db.query(MembershipGrant).filter_by(reference='payu:'+o['order_id']).count()==1
