import uuid
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import pytest
from app import play_choice as choice
from app import payu_payments as pay
from app import play_billing as play
from app.play_choice_models import PlayChoice
from app.payu_models import PayUOrder


@pytest.fixture
def configured(monkeypatch, tmp_path):
    key = tmp_path / 'key'; key.write_bytes(Fernet.generate_key())
    monkeypatch.setattr(play, 'settings', lambda: {'enabled': True, 'token_key_file': str(key)})
    monkeypatch.setattr(pay, 'settings', lambda: {'enabled': True})
    monkeypatch.setenv('SS_PLAY_UCB_ENABLED', '1')
    monkeypatch.setenv('SS_PLAY_UCB_ENROLLED_IN', '1')
    monkeypatch.setenv('SS_PLAY_UCB_TAX_BPS', '1800')
    monkeypatch.setenv('SS_PLAY_UCB_CAPTURE_TIME_CONFIRMED', '1')
    monkeypatch.setenv('SS_PLAY_UCB_CAPTURE_TIME_SEMANTICS_CONFIRMED', '1')
    monkeypatch.setenv('SS_PLAY_UCB_CAPTURE_TIME_FIELD', 'addedon')
    monkeypatch.setenv('SS_PLAY_UCB_PROVIDER_UTC_OFFSET', '+05:30')
    monkeypatch.setenv('SS_PLAY_UCB_RETENTION_APPROVED', '1')
    monkeypatch.setenv('SS_PLAY_UCB_RETENTION_DAYS', '14')


def test_default_off_and_tax_required(configured, monkeypatch):
    assert choice.config()['enabled']
    monkeypatch.delenv('SS_PLAY_UCB_TAX_BPS')
    assert not choice.config()['enabled']
    monkeypatch.setenv('SS_PLAY_UCB_TAX_BPS', '0')
    monkeypatch.delenv('SS_PLAY_UCB_ENROLLED_IN')
    assert not choice.config()['enabled']


def test_start_binds_account_and_rejects_reuse(client, configured, db):
    signup = lambda: client.post('/api/v1/classroom/signup', json={
        'username': 'ucb' + uuid.uuid4().hex[:12], 'password': 'long-safe-password'})
    assert signup().status_code == 200
    data = {'external_transaction_token': 'sdk-token-' + uuid.uuid4().hex,
            'plan_id': 'monthly', 'product_id': 'study_station_monthly',
            'base_plan_id': 'monthly-prepaid', 'country_code': 'IN'}
    url = '/api/v1/payments/google/alternative/start'
    result = client.post(url, json=data)
    assert result.status_code == 200, result.text
    cid = result.json()['choice_id']
    assert result.json()['checkout_url'] == '/membership?play_choice=' + cid
    row = db.get(PlayChoice, cid)
    assert data['external_transaction_token'] not in row.token_encrypted
    assert client.post(url, json=data).json()['choice_id'] == cid
    check = client.get('/api/v1/payments/google/alternative/checkout', params={'choice_id':cid})
    assert check.status_code == 200 and check.json()['plan_id'] == 'monthly'
    assert 'BIHAR' in check.json()['states']
    assert set(check.json()) == {'enabled','choice_id','plan_id','states','expires_at'}
    assert client.post(url, json=dict(data, country_code='US')).status_code == 400
    client.post('/api/v1/classroom/logout', json={}); signup()
    assert client.post(url, json=data).status_code == 403
    assert client.get('/api/v1/payments/google/alternative/checkout', params={'choice_id':cid}).status_code == 404


def test_atomic_bind_and_server_owned_tax(configured, db):
    from types import SimpleNamespace
    ns = uuid.uuid4().hex; cid = uuid.uuid4().hex
    row = PlayChoice(id=cid, namespace=ns, token_hash=uuid.uuid4().hex,
        token_encrypted='encrypted', plan_id='monthly', expires_at=datetime.utcnow()+timedelta(minutes=1))
    db.add(row); db.commit()
    order = PayUOrder(id='SS_' + uuid.uuid4().hex, account_id=1, account_namespace=ns,
        plan_id='monthly', amount_paise=900, currency='INR', binding='binding')
    choice.bind_order(db, SimpleNamespace(storage_namespace=ns,id=1),
        {'play_choice_id': cid, 'billing_state': 'BIHAR', 'tax_paise': 0}, order)
    assert (row.pretax_paise, row.tax_paise) == (763, 137)
    with pytest.raises(Exception):
        choice.bind_order(db, SimpleNamespace(storage_namespace=ns,id=1), {'play_choice_id': cid}, order)
    db.rollback()


def test_unverified_never_reported(configured, db, monkeypatch):
    row = PlayChoice(id=uuid.uuid4().hex, namespace='ns', token_hash=uuid.uuid4().hex,
        token_encrypted='x', plan_id='monthly', expires_at=datetime.utcnow(), order_id='missing')
    monkeypatch.setattr(play, 'provider_request', lambda *a: pytest.fail('must not contact Google'))
    monkeypatch.setattr(pay, 'provider_verify', lambda *a: None)
    assert choice.reconcile_one(db, row) == 'waiting_payment'


def test_choice_capture_requires_provider_timestamp(db,configured):
    from datetime import timezone
    oid = 'SS_' + uuid.uuid4().hex
    order = PayUOrder(id=oid, account_id=1, account_namespace='ns', plan_id='monthly',
        amount_paise=900, currency='INR', binding='binding', created_at=datetime.utcnow())
    row = PlayChoice(id=uuid.uuid4().hex, namespace='ns', token_hash=uuid.uuid4().hex,
        token_encrypted='x', plan_id='monthly', expires_at=datetime.utcnow(), order_id=oid)
    db.add_all([order,row]); db.commit()
    assert not choice.record_capture(db,order,{})
    stamp = datetime.now(timezone(timedelta(hours=5,minutes=30))).strftime('%Y-%m-%d %H:%M:%S')
    assert choice.record_capture(db,order,{'addedon':stamp,'mihpayid':'test-provider'})
    assert abs((row.captured_at-datetime.utcnow()).total_seconds()) < 2
    db.rollback()


def test_report_recovers_existing_and_full_refund(configured, db, monkeypatch):
    import app.payu_reconcile as recon
    order = PayUOrder(id='SS_'+uuid.uuid4().hex, account_id=1, account_namespace='ns',
        plan_id='monthly', amount_paise=900, currency='INR', binding='b', state='paid',
        provider_id=uuid.uuid4().hex, verified_at=datetime.utcnow())
    row = PlayChoice(id=uuid.uuid4().hex, namespace='ns', token_hash=uuid.uuid4().hex,
        token_encrypted='never-decrypt-existing', plan_id='monthly', expires_at=datetime.utcnow(),
        order_id=order.id, administrative_area='BIHAR', pretax_paise=763, tax_paise=137,
        provider_id=order.provider_id,amount_paise=900,captured_at=datetime.utcnow()-timedelta(hours=1))
    db.add_all([order,row]); db.commit()
    result = dict(externalTransactionId=choice.external_id(row), packageName=play.PACKAGE,
        originalPreTaxAmount=choice.price(763), originalTaxAmount=choice.price(137),
        currentPreTaxAmount=choice.price(763))
    calls = []
    def provider(*args):
        calls.append(args)
        if args[0] == 'POST':
            result['currentPreTaxAmount'] = choice.price(0)
        return result
    monkeypatch.setattr(play, 'provider_request', provider)
    stamp = (datetime.utcnow()+timedelta(hours=5,minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
    monkeypatch.setattr(recon, 'refund_inquiry', lambda *a: {'Refund Details':{order.provider_id:[
        {'PayuID':order.provider_id,'RequestID':'refund123','Amount':'9.00','Status':'SUCCESS','success_at':stamp}]}})
    monkeypatch.setattr(recon, 'refunded_paise', lambda *a: 900)
    assert choice.reconcile_one(db,row) == 'reported'
    assert calls[1][2]['fullRefund'] == {} and row.refunded_paise == 900
    assert choice.reconcile_one(db,row) == 'reported'
    assert len(calls) == 4  # GET/POST/verify GET, then second run GET only


def test_provider_and_retention_configuration_fail_closed(configured,monkeypatch):
    for name in ('SS_PLAY_UCB_CAPTURE_TIME_CONFIRMED','SS_PLAY_UCB_CAPTURE_TIME_SEMANTICS_CONFIRMED',
                 'SS_PLAY_UCB_RETENTION_APPROVED'):
        monkeypatch.setenv(name,'0'); assert not choice.settings()['enabled']; monkeypatch.setenv(name,'1')
    monkeypatch.delenv('SS_PLAY_UCB_PROVIDER_UTC_OFFSET')
    assert not choice.settings()['enabled']


def test_missing_success_timestamp_never_invents_refund_time(configured):
    result={'Refund Details':{'p':[{'Status':'SUCCESS','RefundCreationDate':'2026-10-22 00:00:00'}]}}
    with pytest.raises(ValueError,match='refund_timestamp_unavailable'):
        choice.verified_refund_time(result,'p',datetime.utcnow()-timedelta(days=1),datetime.utcnow())


def test_queue_fairness_over_fifty(configured,db,monkeypatch):
    from app import db as storage
    from sqlalchemy import select
    db.query(PlayChoice).delete();db.commit()
    now=datetime.utcnow()
    for i in range(61):
        db.add(PlayChoice(id='queue_'+str(i),namespace='queue',token_hash=uuid.uuid4().hex,
            token_encrypted='x',plan_id='monthly',expires_at=now,order_id='order_'+str(i),
            created_at=now-timedelta(days=1)+timedelta(seconds=i)))
    db.commit(); touched=[]
    def work(session,row,at):
        touched.append(row.id);row.next_check_at=at+timedelta(minutes=5);session.commit();return 'reported'
    monkeypatch.setattr(choice,'reconcile_one',work)
    choice.run(50,now);choice.run(50,now+timedelta(minutes=5))
    assert len(set(touched)) == 61


def test_delete_detaches_minimal_outbox_and_preserves_reporting(configured,db):
    ns='delete_'+uuid.uuid4().hex;now=datetime.utcnow()
    pending=PlayChoice(id=uuid.uuid4().hex,namespace=ns,token_hash=uuid.uuid4().hex,
        token_encrypted='encrypted',plan_id='monthly',expires_at=now,order_id='pending-provider-id',
        amount_paise=900,provider_binding='opaque-binding',provider_account_hash='hashed')
    unused=PlayChoice(id=uuid.uuid4().hex,namespace=ns,token_hash=uuid.uuid4().hex,
        token_encrypted='encrypted',plan_id='monthly',expires_at=now)
    db.add_all([pending,unused]);db.commit();uid=unused.id
    choice.detach_account(db,ns,now);db.commit()
    assert pending.namespace != ns and pending.account_deleted_at == now
    assert pending.purge_after == now+timedelta(days=14)
    assert db.get(PlayChoice,uid) is None
    assert pending.provider_binding == 'opaque-binding'


def test_no_retention_approval_deletes_payment_choice(configured,db,monkeypatch):
    monkeypatch.setenv('SS_PLAY_UCB_RETENTION_APPROVED','0')
    ns='no-retention-'+uuid.uuid4().hex
    row=PlayChoice(id=uuid.uuid4().hex,namespace=ns,token_hash=uuid.uuid4().hex,
        token_encrypted='encrypted',plan_id='monthly',expires_at=datetime.utcnow(),
        order_id='paid-'+uuid.uuid4().hex,amount_paise=900)
    db.add(row);db.commit();rid=row.id
    choice.detach_account(db,ns);db.commit();db.expire_all()
    assert db.get(PlayChoice,rid) is None
    assert not choice.settings()['enabled']
