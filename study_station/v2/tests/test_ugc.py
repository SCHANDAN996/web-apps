import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.classroom import router
from app.ugc import Acceptance,Block,Report,Moderation,Suspension,VERSION
from app import config
from test_classroom import people,joined,post
from test_account_deletion import family


def test_existing_account_must_explicitly_accept(people,db):
    a,_,_=people
    aid=a.get('/api/v1/classroom/me').json()['account']['id']
    db.delete(db.get(Acceptance,aid));db.commit()
    assert not a.get('/api/v1/classroom/safety').json()['accepted']
    assert post(a,'/groups',name='No consent',kind='class').json()['detail']=='content_terms_required'
    assert a.post('/api/v1/classroom/safety/terms',json={'version':VERSION}).status_code==400
    assert a.post('/api/v1/classroom/safety/terms',json={'version':'old','accept':True}).status_code==400
    assert a.post('/api/v1/classroom/safety/terms',json={'version':VERSION,'accept':True},headers={'origin':'https://evil.test'}).status_code==403
    assert a.post('/api/v1/classroom/safety/terms',json={'version':VERSION,'accept':True}).status_code==200
    assert post(a,'/groups',name='Consent',kind='class').status_code==200


def test_share_block_hides_linked_source_and_prevents_editor(people):
    a,b,_=people
    wid=post(a,'/workspaces',name='Reported board',snapshot={'pages':[{'text':'original'}]}).json()['workspace']['id']
    token=post(a,f'/workspaces/{wid}/share').json()['token']
    linked=post(b,f'/workspaces/{wid}/copy',token=token,linked=True).json()['workspace']['id']
    aid=a.get('/api/v1/classroom/me').json()['account']['id']
    bid=b.get('/api/v1/classroom/me').json()['account']['id']
    assert post(a,f'/workspaces/{wid}/editors',account_id=bid,allow=True,version=1).status_code==200
    assert b.post('/api/v1/classroom/safety/blocks',json={'account_id':aid,'blocked':True}).status_code==200
    assert b.get('/api/v1/classroom/shared/'+token).status_code==403
    assert b.get('/api/v1/classroom/workspaces/'+linked).json()['source_status']=='revoked'
    assert b.put('/api/v1/classroom/workspaces/'+wid,json={'op_id':uuid.uuid4().hex,'version':2,'name':'blocked edit'}).status_code==403
    assert post(a,f'/workspaces/{wid}/editors',account_id=bid,allow=True,version=2).status_code==403
    assert b.post('/api/v1/classroom/safety/blocks',json={'account_id':aid,'blocked':False}).status_code==200
    assert b.get('/api/v1/classroom/shared/'+token).status_code==200


def test_report_requires_access_and_freezes_evidence(people,db):
    a,b,c=people
    wid=post(a,'/workspaces',name='Evidence',snapshot={'pages':[{'text':'<script>bad()</script>'}]}).json()['workspace']['id']
    data={'record_id':wid,'reason':'abuse','text':'Please review'}
    assert b.post('/api/v1/classroom/safety/reports',json=data).status_code==403
    token=post(a,f'/workspaces/{wid}/share').json()['token']
    r=b.post('/api/v1/classroom/safety/reports',json=dict(data,token=token))
    assert r.status_code==200
    report=db.get(Report,r.json()['report_id'])
    assert report.owner_id==a.get('/api/v1/classroom/me').json()['account']['id']
    assert report.evidence['data']['snapshot']['pages'][0]['text']=='<script>bad()</script>'
    assert a.put('/api/v1/classroom/workspaces/'+wid,json={'op_id':uuid.uuid4().hex,'version':1,'snapshot':{'pages':[]}}).status_code==200
    db.refresh(report)
    assert report.evidence['data']['snapshot']['pages']
    # The route exists for POST only; learners cannot enumerate private reports.
    assert c.get('/api/v1/classroom/safety/reports').status_code==405


def test_block_filters_discussions_roster_and_events(people):
    a,b,c,g=joined(people)
    bid=b.get('/api/v1/classroom/me').json()['account']['id']
    rid=post(b,f'/groups/{g}/discussions',text='hidden message').json()['discussion']['id']
    assert c.post('/api/v1/classroom/safety/blocks',json={'account_id':bid,'blocked':True}).status_code==200
    data=c.get('/api/v1/classroom/groups/'+g).json()
    assert rid not in [r['id'] for r in data['discussions']]
    assert bid not in [m['id'] for m in data['members']]
    live=post(a,f'/groups/{g}/sessions',name='Board').json()['session']['id']
    assert post(b,f'/sessions/{live}/events',version=1,type='hand',payload={'name':'hidden'}).status_code==200
    assert c.get(f'/api/v1/classroom/sessions/{live}').json()['events']==[]


def test_admin_queue_actions_require_auth_and_origin(people,db,monkeypatch):
    from app.main import app
    monkeypatch.setattr(config,'SECRET_KEY','ugc-test-secret');monkeypatch.setattr(config,'ADMIN_PASSWORD','ugc-password')
    from app import admin
    admin._attempts.clear()
    a,b,_=people
    wid=post(a,'/workspaces',name='Moderate me').json()['workspace']['id']
    token=post(a,f'/workspaces/{wid}/share').json()['token']
    rid=b.post('/api/v1/classroom/safety/reports',json={'record_id':wid,'token':token,'reason':'spam'}).json()['report_id']
    with TestClient(app) as moderator:
        assert moderator.get('/admin/community',follow_redirects=False).status_code==303
        assert moderator.post('/admin/login',data={'password':'ugc-password'},headers={'origin':'http://testserver'},follow_redirects=False).status_code==303
        view=moderator.get('/admin/community?report_id='+rid)
        assert view.status_code==200 and 'Moderate me' in view.text
        assert moderator.post('/admin/community/'+rid,data={'action':'suspend','note':'Reviewed threat'},headers={'origin':'https://evil.test'}).status_code==403
        assert moderator.post('/admin/community/'+rid,data={'action':'remove','note':'Confirmed spam'},headers={'origin':'http://testserver'},follow_redirects=False).status_code==303
        assert b.get('/api/v1/classroom/shared/'+token).status_code==403
        db.expire_all();assert db.get(Report,rid).resolved_at and db.get(Moderation,wid)
        assert moderator.post('/admin/community/'+rid,data={'action':'dismiss','note':'retry'},headers={'origin':'http://testserver'}).status_code==409


def test_moderation_cannot_be_bypassed_by_cached_creation(people,db):
    a,_,_=people
    payload=dict(op_id=uuid.uuid4().hex,name='Removed board')
    first=a.post('/api/v1/classroom/workspaces',json=payload)
    wid=first.json()['workspace']['id']
    db.add(Moderation(record_id=wid));db.commit()
    assert a.post('/api/v1/classroom/workspaces',json=payload).status_code==403
    assert wid not in [w['id'] for w in a.get('/api/v1/classroom/hub').json()['workspaces']]


def test_roster_keeps_private_storage_namespace_private(people):
    a,_,_,gid=joined(people)
    for member in a.get('/api/v1/classroom/groups/'+gid).json()['members']:
        assert 'storage_namespace' not in member
        assert 'legacy_workspace_scope' not in member
    assert a.get('/api/v1/classroom/me').json()['account']['storage_namespace']


def test_deleted_class_erases_descendant_report_evidence(family,db):
    from test_account_deletion import record
    clients,accounts=family
    owner,student,reporter=[x['id'] for x in accounts]
    group=record(db,owner,'group')
    submission=record(db,student,'submission',group.id,{'snapshot':{'pages':[{'text':'erase'}]}})
    report=Report(reporter_id=reporter,record_id=submission.id,owner_id=student,
                  reason='abuse',text='erase report text',note='erase moderator text',
                  evidence={'kind':'submission','data':submission.data})
    ownreport=Report(reporter_id=owner,record_id='unrelated',owner_id=student,
                     reason='other',text='erase own report',evidence={'private':'erase'})
    db.add_all([report,ownreport,Acceptance(account_id=owner,version=VERSION),
                Block(account_id=owner,target_id=student),Suspension(account_id=owner)])
    db.commit();rid=report.id;oid=ownreport.id
    response=clients[0].request('DELETE','/api/v1/classroom/account',
                               json={'confirm':True,'username':accounts[0]['username']})
    assert response.status_code==200,response.text
    db.expire_all()
    erased=db.get(Report,rid)
    assert erased.record_id=='' and erased.evidence=={} and erased.text=='' and erased.note==''
    own=db.get(Report,oid)
    assert own.reporter_id==0 and own.evidence=={} and own.text==''
    assert db.get(Acceptance,owner) is None and db.get(Suspension,owner) is None
    assert not db.query(Block).filter((Block.account_id==owner)|(Block.target_id==owner)).first()


def test_blocked_editor_snapshot_hidden_in_reads_legacy_and_cached_posts(people,db):
    from app.classroom_models import ClassroomRecord
    a,b,c,gid=joined(people)
    bid=b.get('/api/v1/classroom/me').json()['account']['id']
    assert post(a,f'/groups/{gid}/members',account_id=bid,role='editor').status_code==200
    rid=post(a,f'/groups/{gid}/sessions',name='Shared ink').json()['session']['id']
    snap={'pages':[{'text':'blocked editor ink'}]}
    assert post(b,f'/sessions/{rid}/events',version=1,type='snapshot',payload=snap).status_code==200
    cached=dict(op_id=uuid.uuid4().hex,version=2,type='snapshot',payload=snap)
    url=f'/api/v1/classroom/sessions/{rid}'
    assert a.post(url+'/events',json=cached).status_code==200
    assert c.get(url).json()['session']['data']['snapshot']==snap
    assert a.post('/api/v1/classroom/safety/blocks',json={'account_id':bid,'blocked':True}).status_code==200
    assert a.get(url).json()['session']['data']['snapshot']=={'pages':[]}
    assert 'blocked editor ink' not in a.get(url).text
    assert a.post(url+'/events',json=cached).status_code==403
    # Existing snapshots predate explicit author metadata. Their event authors
    # still prevent a container owner's identity from laundering blocked ink.
    row=db.get(ClassroomRecord,rid);row.data={k:v for k,v in row.data.items() if k!='snapshot_authors'};db.commit()
    assert a.get(url).json()['session']['data']['snapshot']=={'pages':[]}
    db.add(Suspension(account_id=bid));db.commit()
    assert c.get(url).json()['session']['data']['snapshot']=={'pages':[]}
    assert 'blocked editor ink' not in c.get(url).text


def test_delete_teacher_scrubs_feedback_in_other_owners_frozen_report(people,db):
    from app.account_deletion import router as deletion_router
    from app.classroom_models import ClassroomRecord
    a,b,c,gid=joined(people)
    aid=a.get('/api/v1/classroom/me').json()['account']['id']
    cid=c.get('/api/v1/classroom/me').json()['account']['id']
    # C owns the classroom; A only authors feedback on B's submission.
    other=post(c,'/groups',name='Other owner',kind='class').json()['group']['id']
    token=post(c,f'/groups/{other}/invite').json()['token']
    assert post(a,'/join',token=token).status_code==200
    assert post(b,'/join',token=token).status_code==200
    assert post(c,f'/groups/{other}/members',account_id=aid,role='teacher').status_code==200
    ass=post(c,f'/groups/{other}/assignments',name='Homework',question_ids=[]).json()['assignment']['id']
    sub=post(b,f'/assignments/{ass}/submissions',answers={}).json()['submission']['id']
    assert post(a,f'/submissions/{sub}/feedback',text='erase teacher private feedback').status_code==200
    rid=c.post('/api/v1/classroom/safety/reports',json={'record_id':sub,'reason':'abuse'}).json()['report_id']
    assert 'erase teacher private feedback' in str(db.get(Report,rid).evidence)
    app=FastAPI();app.include_router(deletion_router)
    with TestClient(app) as deletion:
        deletion.cookies.update(a.cookies)
        username=a.get('/api/v1/classroom/me').json()['account']['username']
        result=deletion.request('DELETE','/api/v1/classroom/account',json={'confirm':True,'username':username})
        assert result.status_code==200,result.text
    db.expire_all();report=db.get(Report,rid)
    assert report.owner_id!=aid and report.reporter_id==cid
    assert report.evidence=={} and report.text=='' and report.note==''
    assert db.get(ClassroomRecord,sub).data['feedback']==[]
