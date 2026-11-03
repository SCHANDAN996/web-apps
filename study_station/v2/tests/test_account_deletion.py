import secrets
import uuid
import pytest
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.account_deletion import router
from app.classroom import router as classroom_router
from app.classroom_models import (ClassroomAccount as Account, ClassroomSession as Session,
    ClassroomRecord as Record, ClassroomMember as Member, ClassroomEvent as Event,
    ClassroomOperation as Operation, ClassroomRate)
from app.google_auth_models import GoogleIdentity
from app.db import Base, engine
from app.models import Device


@pytest.fixture
def family(db):
    Base.metadata.create_all(engine)
    db.query(ClassroomRate).delete(); db.commit()
    app=FastAPI(); app.include_router(router); app.include_router(classroom_router)
    clients=[TestClient(app) for _ in range(3)]
    accounts=[]
    for client in clients:
        r=client.post('/api/v1/classroom/signup',json={'username':'del'+uuid.uuid4().hex[:12],'password':'long-enough-password'})
        assert r.status_code==200,r.text
        accounts.append(r.json()['account'])
    yield clients,accounts
    for client in clients: client.close()


def record(db,owner,kind,parent=None,data=None):
    row=Record(id=secrets.token_urlsafe(18),owner_id=owner,kind=kind,parent=parent,data=data or {})
    db.add(row); db.flush()
    return row


def test_delete_owned_tree_preserves_other_accounts_and_local_data(family,db):
    clients,ac=family; a,b,c=[x['id'] for x in ac]
    group=record(db,a,'group')
    assignment=record(db,a,'assignment',group.id)
    submission=record(db,b,'submission',assignment.id)
    live=record(db,a,'live',group.id)
    own=record(db,a,'workspace')
    othergroup=record(db,c,'group')
    otherassignment=record(db,c,'assignment',othergroup.id)
    otherlive=record(db,c,'live',othergroup.id)
    unrelated=record(db,b,'submission',otherassignment.id,{'feedback':[{'account_id':a,'text':'remove me'},{'account_id':c,'text':'keep'}]})
    board=record(db,b,'workspace',data={'editors':[a,c],'source':{'id':own.id,'hash':'old'}})
    for gid,aid in [(group.id,a),(group.id,b),(group.id,c),(othergroup.id,a),(othergroup.id,b),(othergroup.id,c)]:
        db.add(Member(group_id=gid,account_id=aid,role='student'))
    db.add(Event(room_id=live.id,account_id=b,op_id='event',seq=1,data={'type':'hand'}))
    db.add(Event(room_id=otherlive.id,account_id=a,op_id='erase-author',seq=1,data={'type':'hand'}))
    db.add(Event(room_id=otherlive.id,account_id=c,op_id='keep-author',seq=2,data={'type':'hand'}))
    db.add(Operation(account_id=b,op_id='old-submit',fingerprint='x',result={'submission':{'id':submission.id}}))
    db.add(Operation(account_id=c,op_id='unrelated',fingerprint='x',result={'ok':True}))
    subject='test-'+uuid.uuid4().hex
    db.add(GoogleIdentity(subject=subject,account_id=a))
    db.add(Session(token=uuid.uuid4().hex,account_id=a,expires=datetime.utcnow()+timedelta(days=1)))
    token='device-'+uuid.uuid4().hex
    db.add(Device(token=token))
    db.commit()
    deleted=[group.id,assignment.id,submission.id,live.id,own.id]
    preview=clients[0].get('/api/v1/classroom/account')
    assert preview.status_code==200
    assert preview.json()['counts']==dict(groups=1,workspaces=1,assignments=1,submissions=1,sessions=1,discussions=0,records=5)
    assert db.get(Account,a) # Preview never mutates.
    result=clients[0].request('DELETE','/api/v1/classroom/account',json={'confirm':True,'username':ac[0]['username']})
    assert result.status_code==200,result.text
    db.expire_all()
    assert db.get(Account,a) is None
    assert db.get(GoogleIdentity,subject) is None
    assert db.query(Session).filter(Session.account_id==a).count()==0
    assert all(db.get(Record,rid) is None for rid in deleted)
    assert db.get(Account,b) and db.get(Account,c)
    assert db.get(Record,othergroup.id) and db.get(Record,otherassignment.id)
    assert db.query(Event).filter(Event.room_id==otherlive.id,Event.account_id==a).count()==0
    assert db.query(Event).filter(Event.room_id==otherlive.id,Event.account_id==c).count()==1
    assert db.get(Record,unrelated.id).data['feedback']==[{'account_id':c,'text':'keep'}]
    assert db.get(Record,board.id).data['editors']==[c]
    assert db.query(Operation).filter(Operation.op_id=='old-submit',Operation.account_id==b).count()==0
    assert db.query(Operation).filter(Operation.op_id=='unrelated',Operation.account_id==c).count()==1
    assert db.query(Device).filter(Device.token==token).count()==1
    assert clients[0].get('/api/v1/classroom/me').json()['account'] is None
    assert clients[1].get('/api/v1/classroom/me').json()['account']['id']==b
    assert clients[0].get('/api/v1/classroom/account').status_code==401


@pytest.mark.parametrize('data',[{}, {'confirm':False}, {'confirm':1}, {'confirm':True,'username':'other'}])
def test_confirmation_guard(family,db,data):
    clients,ac=family
    r=clients[0].request('DELETE','/api/v1/classroom/account',json=data)
    assert r.status_code==400
    assert db.get(Account,ac[0]['id'])


def test_origin_and_json_guard(family):
    clients,ac=family
    payload={'confirm':True,'username':ac[0]['username']}
    assert clients[0].request('DELETE','/api/v1/classroom/account',json=payload,headers={'Origin':'https://evil.example'}).status_code==403
    assert clients[0].request('DELETE','/api/v1/classroom/account',content='{}',headers={'Content-Type':'text/plain'}).status_code==415
