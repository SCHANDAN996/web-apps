import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.classroom import router
from app.classroom_models import ClassroomRate
from app.db import Base, engine
from app.models import Question

@pytest.fixture
def people(db):
    Base.metadata.create_all(engine)
    db.query(ClassroomRate).delete(); db.commit()
    app = FastAPI(); app.include_router(router)
    clients = [TestClient(app) for _ in range(3)]
    for c in clients:
        r=c.post('/api/v1/classroom/signup',json={'username':'u'+uuid.uuid4().hex[:12],'password':'long-safe-password'})
        assert r.status_code == 200, r.text
    yield clients
    for c in clients: c.close()

def post(c,p,**kw):
    return c.post('/api/v1/classroom'+p,json=dict(op_id=uuid.uuid4().hex,**kw))

def joined(people):
    a,b,c=people
    g=post(a,'/groups',name='Math',kind='class').json()['group']['id']
    token=post(a,f'/groups/{g}/invite').json()['token']
    assert post(b,'/join',token=token).status_code == 200
    assert post(c,'/join',token=token).status_code == 200
    return a,b,c,g

def test_account_origin_logout(people):
    a,_,_=people
    assert a.get('/api/v1/classroom/me').json()['account']['id']
    assert a.post('/api/v1/classroom/groups',json={},headers={'Origin':'https://bad.example'}).status_code == 403
    assert post(a,'/logout').status_code == 200
    assert a.get('/api/v1/classroom/hub').status_code == 401

def test_share_copy_revoke_and_version(people):
    a,b,c=people
    w=post(a,'/workspaces',name='Algebra',snapshot={'pages':[{'id':'p','text':'Private'}]}).json()['workspace']; wid=w['id']
    assert b.get('/api/v1/classroom/workspaces/'+wid).status_code == 403
    token=post(a,f'/workspaces/{wid}/share').json()['token']
    app=FastAPI();app.include_router(router)
    with TestClient(app) as public:
        assert public.get('/api/v1/classroom/shared/'+token).status_code == 401
    assert b.get('/api/v1/classroom/shared/'+token).status_code == 200
    linked=post(b,f'/workspaces/{wid}/copy',token=token,linked=True).json()['workspace']
    copied=post(b,f'/workspaces/{wid}/copy',token=token,linked=False).json()['workspace']
    assert a.request('DELETE',f'/api/v1/classroom/workspaces/{wid}/share',json={}).status_code == 200
    assert c.get('/api/v1/classroom/shared/'+token).status_code == 404
    assert b.get('/api/v1/classroom/workspaces/'+linked['id']).json()['source_status']=='revoked'
    assert b.get('/api/v1/classroom/workspaces/'+copied['id']).json()['workspace']['data']['snapshot']['pages']
    url='/api/v1/classroom/workspaces/'+wid
    assert b.put(url,json={'version':1,'op_id':uuid.uuid4().hex,'name':'Hijack'}).status_code==403
    assert a.put(url,json={'version':1,'op_id':uuid.uuid4().hex,'name':'New'}).status_code==200
    assert a.put(url,json={'version':1,'op_id':uuid.uuid4().hex,'name':'Stale'}).status_code==409

def test_private_submission_retry_feedback(people,db):
    a,b,c,g=joined(people)
    qid=db.query(Question).filter(Question.review_status!='flagged').first().id
    aid=post(a,f'/groups/{g}/assignments',name='Fractions',question_ids=[qid]).json()['assignment']['id']
    assert post(b,f'/groups/{g}/assignments',name='No',question_ids=[]).status_code==403
    assert 'answer_index' not in b.get('/api/v1/classroom/assignments/'+aid).text
    url=f'/api/v1/classroom/assignments/{aid}/submissions'; payload={'op_id':uuid.uuid4().hex,'answers':{str(qid):1}}
    s=b.post(url,json=payload).json()['submission']
    assert b.post(url,json=payload).json()['submission']['id']==s['id']
    assert c.get('/api/v1/classroom/assignments/'+aid).json()['submissions']==[]
    assert c.get('/api/v1/classroom/submissions/'+s['id']).status_code==403
    assert post(c,'/submissions/'+s['id']+'/feedback',text='No').status_code==403
    assert post(a,'/submissions/'+s['id']+'/feedback',text='Try again').status_code==200
    assert post(b,f'/assignments/{aid}/submissions',answers={}).json()['submission']['data']['attempt']==2

def test_live_replay_permissions_revoke(people):
    a,b,c,g=joined(people)
    r=post(a,f'/groups/{g}/sessions',name='Board').json()['session'];rid=r['id']
    assert post(b,f'/sessions/{rid}/events',version=1,type='stroke',payload={}).status_code==403
    url=f'/api/v1/classroom/sessions/{rid}/events';data={'op_id':uuid.uuid4().hex,'version':1,'type':'page','payload':{'id':'p'}}
    assert a.post(url,json=data).json()['event']['seq']==1
    assert a.post(url,json=data).json()['event']['seq']==1
    assert post(a,f'/sessions/{rid}/events',version=1,type='page').status_code==409
    assert post(b,f'/sessions/{rid}/events',version=2,type='hand').json()['event']['seq']==2
    assert [e['seq'] for e in c.get(f'/api/v1/classroom/sessions/{rid}?after=1').json()['events']]==[2]
    bid=b.get('/api/v1/classroom/me').json()['account']['id']
    assert post(a,f'/groups/{g}/members',account_id=bid,role='editor').status_code==200
    assert post(b,f'/sessions/{rid}/events',version=3,type='stroke',payload={'tool':'pen','color':'#333333','width':3,'points':[[0.1,0.2],[0.4,0.5]]}).status_code==200
    assert post(a,f'/groups/{g}/members',account_id=bid,role='removed').status_code==200
    assert b.get(f'/api/v1/classroom/sessions/{rid}').status_code==403
    assert post(a,f'/sessions/{rid}/events',version=4,type='end').status_code==200
    assert post(c,f'/sessions/{rid}/events',version=5,type='hand').status_code==409

def test_creation_dedup(people):
    a,_,_=people
    data={'op_id':uuid.uuid4().hex,'name':'One'}
    r=a.post('/api/v1/classroom/workspaces',json=data).json()['workspace']
    assert a.post('/api/v1/classroom/workspaces',json=data).json()['workspace']['id']==r['id']
    assert a.post('/api/v1/classroom/workspaces',json=dict(data,name='Other')).status_code==409


def test_reject_malformed_board_and_live_data(people):
    a,b,c,g=joined(people)
    bad={'pages':[{'strokes':[{'tool':'pen','color':'#333333','width':3,'points':[[2,.1]]}]}]}
    assert post(a,'/workspaces',name='bad',snapshot=bad).status_code == 400
    r=post(a,f'/groups/{g}/sessions',name='Board').json()['session']
    assert post(a,f"/sessions/{r['id']}/events",version=1,type='stroke',payload={'points':[]}).status_code == 400
    assert a.get(f"/api/v1/classroom/sessions/{r['id']}").json()['last_seq']==0


@pytest.mark.parametrize('tool', ['pen', 'marker', 'highlighter', 'erase', 'line', 'rect', 'circle'])
def test_drawing_formats_accept_additive_fields(tool):
    from app.classroom import stroke, snapshot
    value = {'tool': tool, 'color': '#123456', 'width': 4, 'points': [[.1, .2], [.9, .8]], 'opacity': .25, 'id': 'stable-stroke'}
    assert stroke(value) == value
    assert snapshot({'pages': [{'paper': 'grid', 'strokes': [value]}]})['pages'][0]['strokes'] == [value]


@pytest.mark.parametrize('extra', [
    {'tool': 'unknown'}, {'opacity': -1}, {'opacity': 1.1}, {'opacity': True},
    {'opacity': '0.25'}, {'opacity': float('nan')}, {'opacity': float('inf')},
    {'id': ''}, {'id': 4}, {'id': 'x' * 129},
])
def test_drawing_formats_reject_malformed_fields(extra):
    from fastapi import HTTPException
    from app.classroom import stroke
    value = {'tool': 'pen', 'color': '#123456', 'width': 4, 'points': [[.1, .2]], **extra}
    with pytest.raises(HTTPException) as e:
        stroke(value)
    assert e.value.detail == 'invalid_stroke'


def test_drawing_formats_legacy_and_paper_validation():
    from fastapi import HTTPException
    from app.classroom import stroke, snapshot
    old = {'color': '#123456', 'width': 4, 'points': [[.1, .2]]}
    assert stroke(old) == old
    with pytest.raises(HTTPException):
        snapshot({'pages': [{'paper': 'unknown', 'strokes': []}]})


def test_drawing_formats_live_reject_without_mutating(people):
    a,b,c,g = joined(people)
    session = post(a, f'/groups/{g}/sessions', name='Ink').json()['session']
    rid = session['id']
    base = {'tool': 'highlighter', 'color': '#ffcc00', 'width': 18, 'points': [[.1, .2], [.8, .2]], 'id': 'highlight-1'}
    for extra in ({'tool': 'unsupported'}, {'opacity': -1}, {'opacity': '0.25'}):
        r = post(a, f'/sessions/{rid}/events', version=1, type='stroke', payload={**base, **extra})
        assert r.status_code == 400
        assert a.get(f'/api/v1/classroom/sessions/{rid}').json()['last_seq'] == 0
    r = post(a, f'/sessions/{rid}/events', version=1, type='stroke', payload=base)
    assert r.status_code == 200
    events = b.get(f'/api/v1/classroom/sessions/{rid}?after=0').json()['events']
    assert events[0]['data']['payload']['tool'] == 'highlighter'
