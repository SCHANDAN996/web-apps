import uuid
from datetime import datetime, timedelta
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app import membership as service
from app.classroom import router as accounts
from app.classroom_models import ClassroomAccount, ClassroomRate
from app.membership_models import Membership
from app.db import Base, engine

@pytest.fixture
def trial(db, monkeypatch):
    Base.metadata.create_all(engine)
    db.query(ClassroomRate).delete(); db.commit()
    monkeypatch.setenv('MEMBERSHIP_ENABLED', '0')
    app=FastAPI(); app.include_router(accounts); app.include_router(service.router)
    from app.account_deletion import router as deletion_router
    app.include_router(deletion_router)
    client=TestClient(app)
    user='trial'+uuid.uuid4().hex[:12]
    response=client.post('/api/v1/classroom/signup',json={'username':user,'password':'long-enough-password'})
    assert response.status_code==200,response.text
    monkeypatch.setenv('MEMBERSHIP_ENABLED','1')
    yield client,response.json()['account']
    client.close()

def test_start_is_explicit_and_does_not_charge(trial,db,monkeypatch):
    client,account=trial
    now=datetime(2026,1,1,12)
    monkeypatch.setattr(service,'utcnow',lambda:now)
    assert client.get('/api/v1/membership/status').json()['state']=='available'
    assert db.query(Membership).filter_by(namespace=account['storage_namespace']).first() is None
    first=client.post('/api/v1/membership/start',json={'confirm':True}).json()
    assert first['trial_started_at']=='2026-01-01T12:00:00Z'
    assert first['trial_ends_at']=='2026-04-01T12:00:00Z'
    assert first['remaining_seconds']==int((service.trial_end(now)-now).total_seconds())
    assert first['premium_access'] and not first['payment_available'] and not first['auto_renew']
    monkeypatch.setattr(service,'utcnow',lambda:service.trial_end(now)-timedelta(seconds=1))
    assert client.get('/api/v1/membership/status').json()['state']=='trial'
    monkeypatch.setattr(service,'utcnow',lambda:service.trial_end(now))
    expired=client.post('/api/v1/membership/start',json={'confirm':True}).json()
    assert expired['state']=='expired' and not expired['premium_access']
    assert expired['trial_ends_at']==first['trial_ends_at']
    assert 'export' in expired['protected_actions']
    assert client.get('/api/v1/classroom/me').json()['account']['id']==account['id']

def test_feature_disabled_preserves_existing_access(trial,monkeypatch):
    client,_=trial; monkeypatch.delenv('MEMBERSHIP_ENABLED')
    value=client.get('/api/v1/membership/status').json()
    assert value['state']=='disabled' and value['premium_access']
    assert client.post('/api/v1/membership/start',json={'confirm':True}).status_code==409

@pytest.mark.parametrize('payload',[{}, {'confirm':1},{'confirm':False},{'confirm':True,'paid_until':'2099-01-01'},{'confirm':True,'plan':'yearly'}])
def test_no_client_dates_or_paid_grants(trial,payload):
    client,_=trial
    assert client.post('/api/v1/membership/start',json=payload).status_code==400

def test_requires_login_and_same_origin_json(trial):
    client,_=trial
    assert client.post('/api/v1/membership/start',json={'confirm':True},headers={'Origin':'https://evil.example'}).status_code==403
    assert client.post('/api/v1/membership/start',content='{}').status_code==415
    client.cookies.clear()
    assert client.get('/api/v1/membership/status').status_code==401
    assert client.post('/api/v1/membership/start',json={'confirm':True}).status_code==401

def test_restart_after_logout_and_other_account_isolation(trial,db,monkeypatch):
    client,account=trial
    first=client.post('/api/v1/membership/start',json={'confirm':True}).json()
    original=db.get(ClassroomAccount,account['id'])
    original.created_at=datetime(2020,1,1); db.commit()
    client.post('/api/v1/classroom/logout',json={})
    login=client.post('/api/v1/classroom/login',json={'username':account['username'],'password':'long-enough-password'})
    assert login.status_code==200
    assert client.post('/api/v1/membership/start',json={'confirm':True}).json()['trial_started_at']==first['trial_started_at']
    client.post('/api/v1/classroom/logout',json={})
    second=client.post('/api/v1/classroom/signup',json={'username':'other'+uuid.uuid4().hex[:12],'password':'long-enough-password'})
    assert second.status_code==200
    assert client.get('/api/v1/membership/status').json()['state']=='trial'
    assert client.get('/api/v1/membership/status').json()['account_namespace']!=first['account_namespace']

def test_verified_payment_grants_calendar_period_once(trial,db):
    client,account=trial
    start=datetime(2028,1,31,12)
    end=service.grant_verified_payment(db,account['id'],'monthly','test-'+uuid.uuid4().hex,start)
    assert end==datetime(2028,2,29,12)
    reference='test-'+uuid.uuid4().hex
    end=service.grant_verified_payment(db,account['id'],'yearly',reference,start)
    assert end==datetime(2029,2,28,12)
    assert service.grant_verified_payment(db,account['id'],'yearly',reference,start)==end
    with pytest.raises(ValueError,match='reference_conflict'):
        service.grant_verified_payment(db,account['id'],'monthly',reference,start)
    db.rollback()


def test_calendar_clamps_and_invalid_plan():
    assert service.calendar_end(datetime(2026,12,31),'monthly')==datetime(2027,1,31)
    assert service.calendar_end(datetime(2028,2,29),'yearly')==datetime(2029,2,28)
    with pytest.raises(ValueError): service.calendar_end(datetime(2026,1,1),'client-free-plan')

@pytest.mark.parametrize('path,method',[
    ('/books','GET'),('/books/book/chapter','GET'),('/practice/quant/percentage','GET'),
    ('/mock/exam','GET'),('/questions/123','GET'),('/api/v1/revise','GET'),
    ('/api/v1/practice','POST'),('/api/v1/questions/123/explain','POST'),
    ('/api/v1/attempts/1/retry-wrong','POST')])
def test_study_route_allowlist(path,method):
    assert service.premium_path(path,method)

@pytest.mark.parametrize('path,method',[
    ('/api/v1/backup/export','GET'),('/api/v1/backup/restore','POST'),
    ('/api/v1/attempts/1/answer','POST'),('/api/v1/attempts/1/finish','POST'),
    ('/api/v1/attempts/1/result','GET'),('/result/1','GET'),('/progress','GET'),
    ('/privacy','GET'),('/api/v1/classroom/account','DELETE'),('/classroom','GET'),
    ('/membership','GET'),('/q/123','GET'),('/static/js/app.js','GET')])
def test_private_data_and_account_controls_never_gated(path,method):
    assert not service.premium_path(path,method)


def test_full_app_enforcement_and_html_entry(client,monkeypatch):
    monkeypatch.setenv('MEMBERSHIP_ENABLED','1')
    result=client.post('/api/v1/practice',json={})
    assert result.status_code==401 and result.json()['detail']=='sign_in_required'
    redirect=client.get('/books',follow_redirects=False)
    assert redirect.status_code==303 and redirect.headers['location'].startswith('/login?return_to=%2Fbooks')
    assert client.get('/membership').status_code==200
    assert 'no-store' in client.get('/membership').headers['cache-control']
    assert client.get('/privacy').status_code==200
    signup=client.post('/api/v1/classroom/signup',json={'username':'gate'+uuid.uuid4().hex[:12],'password':'long-enough-password'})
    assert signup.status_code==200,signup.text
    assert client.get('/books',follow_redirects=False).status_code==200
    assert client.get('/api/v1/membership/status').json()['state']=='trial'
    assert client.post('/api/v1/membership/start',json={'confirm':True}).status_code==200
    assert client.get('/books',follow_redirects=False).status_code==200
    assert client.get('/api/v1/membership/status').headers['cache-control']=='no-store'
    assert client.get('/membership').status_code==200

@pytest.mark.parametrize('hours',[1,72])
def test_lease_signature_and_expiry_clamped_to_trial(trial,db,monkeypatch,tmp_path,hours):
    import base64,json,calendar
    from cryptography.hazmat.primitives import serialization,hashes
    from cryptography.hazmat.primitives.asymmetric import rsa,padding
    client,account=trial
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    path=tmp_path/'lease-key.pem'
    path.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    monkeypatch.setenv('MEMBERSHIP_LEASE_PRIVATE_KEY_FILE',str(path))
    start=datetime(2026,1,1)
    monkeypatch.setattr(service,'utcnow',lambda:start)
    assert client.post('/api/v1/membership/start',json={'confirm':True}).status_code==200
    now=service.trial_end(start)-timedelta(hours=hours)
    monkeypatch.setattr(service,'utcnow',lambda:now)
    response=client.get('/api/v1/membership/lease')
    assert response.status_code==200,response.text
    head,body,signature=response.json()['lease'].split('.')
    decode=lambda value:base64.urlsafe_b64decode(value+'='*((4-len(value)%4)%4))
    key.public_key().verify(decode(signature),(head+'.'+body).encode(),padding.PKCS1v15(),hashes.SHA256())
    claims=json.loads(decode(body))
    assert claims['aud']=='com.studystation.app' and claims['iss']=='StudyStation'
    assert claims['namespace']==account['storage_namespace']
    assert claims['exp']-claims['iat']==min(hours,24)*3600
    assert claims['exp']<=calendar.timegm(service.trial_end(start).utctimetuple())
    assert 'email' not in claims and 'username' not in claims


def test_lease_fails_closed_without_eligible_membership_or_key(trial,monkeypatch):
    client,_=trial
    assert client.get('/api/v1/membership/lease').status_code==402
    assert client.post('/api/v1/membership/start',json={'confirm':True}).status_code==200
    monkeypatch.delenv('MEMBERSHIP_LEASE_PRIVATE_KEY_FILE',raising=False)
    assert client.get('/api/v1/membership/lease').status_code==503
    monkeypatch.setenv('MEMBERSHIP_LEASE_PRIVATE_KEY_FILE','nonexistent-private-key.pem')
    assert client.get('/api/v1/membership/lease').status_code==503


def test_account_deletion_removes_only_its_membership_and_orders(trial,db):
    from app.membership_models import MembershipGrant
    from app.payu_models import PayUOrder
    client,account=trial
    reference='delete-'+uuid.uuid4().hex
    service.grant_verified_payment(db,account['id'],'monthly',reference,datetime(2026,1,1))
    order_id='SS_'+uuid.uuid4().hex
    db.add(PayUOrder(id=order_id,account_id=account['id'],account_namespace=account['storage_namespace'],
                    plan_id='monthly',amount_paise=900,binding=uuid.uuid4().hex,state='pending'))
    other_namespace=uuid.uuid4().hex
    db.add(Membership(namespace=other_namespace,trial_started_at=datetime(2026,1,1),trial_ends_at=datetime(2026,1,4)))
    db.commit()
    response=client.request('DELETE','/api/v1/classroom/account',json={'confirm':True,'username':account['username']})
    assert response.status_code==200,response.text
    db.expire_all()
    assert db.get(Membership,account['storage_namespace']) is None
    assert db.get(MembershipGrant,reference) is None
    assert db.get(PayUOrder,order_id) is None
    assert db.get(Membership,other_namespace) is not None


def test_membership_privacy_and_checkout_csp_are_scoped(client,monkeypatch):
    client.cookies.set('ss_lang','en')
    privacy=client.get('/privacy')
    assert privacy.status_code==200
    assert 'Trial and offline membership' in privacy.text
    assert 'Optional website payments' in privacy.text
    assert 'There is no automatic charge' in privacy.text
    assert 'secure.payu.in' not in privacy.headers['content-security-policy']
    for key,value in {'SS_PAYU_WEB_ENABLED':'1','SS_PAYMENT_CHANNEL':'website',
        'SS_PAYU_WEB_ORIGIN':'https://payments.example','SS_PAYU_MERCHANT_KEY':'local-test-key',
        'SS_PAYU_MERCHANT_SALT':'local-test-salt','SS_PAYU_ENV':'test'}.items():
        monkeypatch.setenv(key,value)
    response=client.get('/membership')
    assert 'form-action \'self\' https://secure.payu.in https://test.payu.in' in response.headers['content-security-policy']
    assert 'secure.payu.in' not in client.get('/privacy').headers['content-security-policy']


def test_verified_refund_rebuilds_other_grants_and_is_idempotent(trial,db):
    from app.membership_models import MembershipGrant
    client,account=trial
    first='first-'+uuid.uuid4().hex;second='second-'+uuid.uuid4().hex
    service.grant_verified_payment(db,account['id'],'monthly',first,datetime(2026,1,1))
    service.grant_verified_payment(db,account['id'],'yearly',second,datetime(2026,1,15))
    assert db.get(Membership,account['storage_namespace']).paid_until==datetime(2027,2,1)
    assert service.revoke_verified_payment(db,first,datetime(2026,1,20)) is True
    assert db.get(Membership,account['storage_namespace']).paid_until==datetime(2027,1,15)
    assert service.revoke_verified_payment(db,first,datetime(2026,1,21)) is True
    assert db.get(MembershipGrant,first).revoked_at==datetime(2026,1,20)
    assert db.get(Membership,account['storage_namespace']).paid_until==datetime(2027,1,15)
    assert service.revoke_verified_payment(db,'unknown',datetime(2026,1,21)) is False
    assert service.revoke_verified_payment(db,second,datetime(2026,1,21)) is True
    assert db.get(Membership,account['storage_namespace']).paid_until is None
    db.rollback()
