import copy
import hashlib
import uuid
from datetime import datetime,timedelta
import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI,HTTPException
from fastapi.testclient import TestClient
from app import play_billing as billing,membership
from app.classroom import router as accounts
from app.classroom_models import ClassroomRate
from app.play_billing_models import PlayPurchase
from app.membership_models import Membership
from app.db import Base,engine


@pytest.fixture
def purchase(db,monkeypatch,tmp_path):
    Base.metadata.create_all(engine)
    db.query(ClassroomRate).delete();db.commit()
    key=tmp_path/'token-key';key.write_bytes(Fernet.generate_key())
    service=tmp_path/'service-account.json';service.write_text('{}')
    for k,v in {'PLAY_BILLING_ENABLED':'1','PLAY_BILLING_SERVICE_ACCOUNT_FILE':str(service),
                'PLAY_BILLING_TOKEN_KEY_FILE':str(key),'MEMBERSHIP_ENABLED':'1'}.items():
        monkeypatch.setenv(k,v)
    monkeypatch.delenv('PLAY_BILLING_ALLOW_TEST',raising=False)
    now=datetime(2026,10,22,12)
    monkeypatch.setattr(billing,'utcnow',lambda:now)
    monkeypatch.setattr(membership,'utcnow',lambda:now)
    app=FastAPI();app.include_router(accounts);app.include_router(billing.router);app.include_router(membership.router)
    from app.account_deletion import router as deletion
    app.include_router(deletion)
    client=TestClient(app)
    response=client.post('/api/v1/classroom/signup',json={'username':'gpay'+uuid.uuid4().hex[:12],'password':'long-billing-test-password'})
    assert response.status_code==200,response.text
    account=response.json()['account']
    token='test-purchase-'+uuid.uuid4().hex
    data={'subscriptionState':'SUBSCRIPTION_STATE_ACTIVE',
          'acknowledgementState':'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED',
          'externalAccountIdentifiers':{'obfuscatedExternalAccountId':billing.account_binding(account['storage_namespace'])},
          'lineItems':[{'productId':'study_station_monthly','prepaidPlan':{},
                        'offerDetails':{'basePlanId':'monthly-prepaid'},
                        'expiryTime':(now+timedelta(days=31)).isoformat()+'Z'}]}
    monkeypatch.setattr(billing,'provider_get',lambda supplied:copy.deepcopy(data))
    yield client,account,token,data,now
    client.close()


def verify(client,token,**extra):
    return client.post('/api/v1/payments/google/verify',json={'purchase_token':token,**extra})


def test_config_is_account_bound_and_has_no_secrets(purchase):
    client,account,token,data,now=purchase
    response=client.get('/api/v1/payments/google/config')
    assert response.status_code==200
    value=response.json()
    assert value['enabled'] and value['auto_renew'] is False
    assert value['package_name']=='com.studystation.app'
    assert value['obfuscated_account_id']==billing.account_binding(account['storage_namespace'])
    assert len(value['obfuscated_account_id'])==64
    assert 'service-account' not in response.text and token not in response.text
    assert response.headers['cache-control']=='no-store'


def test_verified_token_is_encrypted_and_idempotent(purchase,db):
    client,account,token,data,now=purchase
    first=verify(client,token)
    assert first.status_code==200,first.text
    assert first.json()['entitled'] and first.json()['acknowledged']
    row=db.get(PlayPurchase,hashlib.sha256(token.encode()).hexdigest())
    assert row.namespace==account['storage_namespace'] and token not in row.token_encrypted
    assert billing.cipher().decrypt(row.token_encrypted.encode()).decode()==token
    assert token not in first.text
    again=verify(client,token)
    assert again.json()['valid_until']==first.json()['valid_until']
    assert db.query(PlayPurchase).filter_by(namespace=account['storage_namespace']).count()==1
    # Google's exact expiry is used, with no fictitious extra calendar grant.
    status=client.get('/api/v1/membership/status').json()
    assert status['state']=='paid' and status['paid_until']==first.json()['valid_until']
    assert db.get(Membership,account['storage_namespace']) is None


def test_pending_ack_needs_backend_ack_and_google_recheck(purchase,monkeypatch,db):
    client,account,token,data,now=purchase
    data['acknowledgementState']='ACKNOWLEDGEMENT_STATE_PENDING'
    calls=[]
    def acknowledge(supplied,product):
        calls.append((supplied,product))
        data['acknowledgementState']='ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED'
    monkeypatch.setattr(billing,'provider_acknowledge',acknowledge)
    assert verify(client,token).json()['entitled']
    assert calls==[(token,'study_station_monthly')]
    assert verify(client,token).json()['entitled']
    assert len(calls)==1


def test_ack_failure_never_grants_and_retry_can_recover(purchase,monkeypatch,db):
    client,account,token,data,now=purchase
    data['acknowledgementState']='ACKNOWLEDGEMENT_STATE_PENDING'
    def unavailable(*args): raise HTTPException(503,'play_billing_unavailable')
    monkeypatch.setattr(billing,'provider_acknowledge',unavailable)
    assert verify(client,token).status_code==503
    assert billing.access_until(db,account['storage_namespace'],now) is None
    monkeypatch.setattr(billing,'provider_acknowledge',lambda *args:None)
    assert verify(client,token).status_code==503 # Google still says unacknowledged.
    data['acknowledgementState']='ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED'
    assert verify(client,token).json()['entitled']


@pytest.mark.parametrize('state',['SUBSCRIPTION_STATE_PENDING','SUBSCRIPTION_STATE_PAUSED',
    'SUBSCRIPTION_STATE_ON_HOLD','SUBSCRIPTION_STATE_EXPIRED','SUBSCRIPTION_STATE_PENDING_PURCHASE_CANCELED',
    'SUBSCRIPTION_STATE_IN_GRACE_PERIOD'])
def test_non_active_prepaid_states_never_grant(purchase,state):
    client,account,token,data,now=purchase;data['subscriptionState']=state
    response=verify(client,token)
    assert response.status_code==200,response.text
    assert not response.json()['entitled']
    assert client.get('/api/v1/membership/status').json()['state']!='paid'


@pytest.mark.parametrize('mutation',[
    lambda d:d.update(subscriptionState='UNSUPPORTED_NEW_STATE'),
    lambda d:d.update(externalAccountIdentifiers={}),
    lambda d:d.update(externalAccountIdentifiers='invalid'),
    lambda d:d['externalAccountIdentifiers'].update(obfuscatedExternalAccountId='different-account'),
    lambda d:d['lineItems'][0].update(productId='other_app_product'),
    lambda d:d['lineItems'][0].update(productId=[]),
    lambda d:d['lineItems'][0].update(autoRenewingPlan={}),
    lambda d:d['lineItems'][0].update(prepaidPlan=None),
    lambda d:d['lineItems'][0]['offerDetails'].update(basePlanId='auto-renewing-monthly'),
    lambda d:d['lineItems'][0].update(expiryTime='not-a-date'),
    lambda d:d['lineItems'][0].update(expiryTime='2026-10-25T00:00:00'),
    lambda d:d.update(acknowledgementState='UNKNOWN'),
    lambda d:d['lineItems'].append(copy.deepcopy(d['lineItems'][0])),
])
def test_mismatch_malformed_or_unsupported_fails_closed(purchase,mutation,db):
    client,account,token,data,now=purchase;mutation(data)
    assert verify(client,token).status_code in (400,403)
    assert billing.access_until(db,account['storage_namespace'],now) is None


def test_token_cannot_be_reassigned_even_if_provider_account_claim_changes(purchase,monkeypatch,db):
    client,account,token,data,now=purchase
    assert verify(client,token).status_code==200
    client.post('/api/v1/classroom/logout',json={})
    other=client.post('/api/v1/classroom/signup',json={'username':'other'+uuid.uuid4().hex[:12],'password':'long-billing-test-password'}).json()['account']
    data['externalAccountIdentifiers']['obfuscatedExternalAccountId']=billing.account_binding(other['storage_namespace'])
    assert verify(client,token).status_code==403
    db.expire_all()
    assert db.get(PlayPurchase,hashlib.sha256(token.encode()).hexdigest()).namespace==account['storage_namespace']


def test_test_purchase_requires_explicit_flag(purchase,monkeypatch):
    client,account,token,data,now=purchase;data['testPurchase']={}
    assert verify(client,token).status_code==400
    monkeypatch.setenv('PLAY_BILLING_ALLOW_TEST','1')
    assert verify(client,token).json()['entitled']


def test_revocation_refresh_does_not_revoke_website_payment(purchase,db,monkeypatch):
    client,account,token,data,now=purchase
    assert verify(client,token).status_code==200
    from app.classroom_models import ClassroomAccount
    user=db.get(ClassroomAccount,account['id'])
    membership.grant_verified_payment(db,user.id,'yearly','website-'+uuid.uuid4().hex,now);db.commit()
    data['subscriptionState']='SUBSCRIPTION_STATE_EXPIRED'
    data['lineItems'][0]['expiryTime']=(now-timedelta(seconds=1)).isoformat()+'Z'
    later=now+timedelta(minutes=16)
    monkeypatch.setattr(billing,'utcnow',lambda:later)
    monkeypatch.setattr(membership,'utcnow',lambda:later)
    assert billing.access_until(db,account['storage_namespace'],later) is None
    status=client.get('/api/v1/membership/status').json()
    assert status['state']=='paid' # Independent website year still exists.
    db.expire_all()
    assert not db.get(PlayPurchase,hashlib.sha256(token.encode()).hexdigest()).entitled


def test_pending_or_expired_purchase_cannot_create_future_access(purchase):
    client,account,token,data,now=purchase
    data['lineItems'][0]['expiryTime']=(now-timedelta(seconds=1)).isoformat()+'Z'
    assert verify(client,token).json()['entitled'] is False


def test_json_auth_origin_flag_and_client_fields(purchase,monkeypatch):
    client,account,token,data,now=purchase
    assert verify(client,token,paid_until='2099-01-01').status_code==400
    assert client.post('/api/v1/payments/google/verify',json={'purchase_token':token},headers={'Origin':'https://evil.example'}).status_code==403
    assert client.post('/api/v1/payments/google/verify',content='{}').status_code==415
    monkeypatch.setenv('PLAY_BILLING_ENABLED','0')
    assert verify(client,token).status_code==503
    assert client.get('/api/v1/payments/google/config').json()['enabled'] is False
    client.cookies.clear()
    assert client.get('/api/v1/payments/google/config').status_code==401
    assert verify(client,token).status_code==401


def test_account_delete_erases_encrypted_tokens(purchase,db):
    client,account,token,data,now=purchase
    assert verify(client,token).status_code==200
    response=client.request('DELETE','/api/v1/classroom/account',json={'confirm':True,'username':account['username']})
    assert response.status_code==200,response.text
    db.expire_all()
    assert db.get(PlayPurchase,hashlib.sha256(token.encode()).hexdigest()) is None
