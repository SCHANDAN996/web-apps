from datetime import datetime, timedelta
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db import Base
from app.membership import trial_end
from app.membership_models import Membership
from app.classroom_models import ClassroomAccount
from app.auth_navigation import study_target
from app.trial_rollout import rollout

@pytest.mark.parametrize('start,end', [(datetime(2026,1,31),datetime(2026,4,30)),(datetime(2027,11,30),datetime(2028,2,29)),(datetime(2026,11,30),datetime(2027,2,28))])
def test_three_calendar_months(start,end):
    assert trial_end(start)==end

@pytest.mark.parametrize('target', ['https://evil.example','//evil.example','/books/../private','/books/%2e%2e/private','/books%5cevil','/api/v1/classroom/logout','/login?return_to=https://evil.example'])
def test_return_destination_rejects_untrusted(target):
    assert study_target(target)=='/'

def test_login_page_and_safe_google_return(client):
    r=client.get('/login',params={'return_to':'//evil.example'})
    assert r.status_code==200 and 'data-return-to="/"' in r.text
    assert 'no-store' in r.headers['cache-control']
    from app.google_auth import safe_target
    assert safe_target('/login?return_to=%2Fbooks')=='/login?return_to=%2Fbooks'

def test_old_user_rollout_is_idempotent_and_preserves_paid():
    engine=create_engine('sqlite:///:memory:');Base.metadata.create_all(engine)
    anchor=datetime(2026,10,26,12)
    with Session(engine) as db:
        a=ClassroomAccount(username='old',name='Old',password='test-only',created_at=anchor-timedelta(days=20))
        b=ClassroomAccount(username='paid',name='Paid',password='test-only',created_at=anchor-timedelta(days=10))
        db.add_all([a,b]);db.flush()
        paid=datetime(2028,1,1)
        db.add(Membership(namespace=b.storage_namespace,trial_started_at=anchor-timedelta(days=10),trial_ends_at=anchor-timedelta(days=7),paid_until=paid));db.commit()
        assert rollout(db,False,anchor)['accounts']==2
        db.rollback();assert db.get(Membership,a.storage_namespace) is None
        db.rollback();assert rollout(db,True,anchor)['accounts']==2
        assert db.get(Membership,a.storage_namespace).trial_ends_at==datetime(2027,1,26,12)
        assert db.get(Membership,b.storage_namespace).paid_until==paid
        db.rollback();assert rollout(db,True,anchor+timedelta(days=5))['accounts']==0
        assert db.get(Membership,a.storage_namespace).trial_ends_at==datetime(2027,1,26,12)

def test_successful_signup_starts_one_trial(client,monkeypatch):
    monkeypatch.setenv('MEMBERSHIP_ENABLED','1')
    user='auto'+uuid.uuid4().hex[:12]
    r=client.post('/api/v1/classroom/signup',json={'username':user,'password':'long-test-only-password'})
    assert r.status_code==200
    first=client.get('/api/v1/membership/status').json()
    assert first['state']=='trial' and first['trial_period']=={'unit':'calendar_month','count':3}
    assert not first['auto_renew']
    assert client.post('/api/v1/membership/start',json={'confirm':True}).json()['trial_ends_at']==first['trial_ends_at']
    client.post('/api/v1/classroom/logout',json={})


def test_auth_assets_have_valid_utf8():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]/'app/static/js'
    for name in ['login.js','membership.js','classroom.js']:
        text=(root/name).read_text(encoding='utf-8')
        assert '\u00c2\u00b7' not in text
