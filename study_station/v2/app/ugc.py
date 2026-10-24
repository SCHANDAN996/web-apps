"""Server-enforced community rules, personal blocks and moderation audit."""
import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy import String, Text, Integer, DateTime, UniqueConstraint, select, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base, get_db
VERSION='2026-10-19'
TERMS={'hi':'साझा पढ़ाई में उत्पीड़न, नफ़रत, यौन सामग्री, बच्चों का शोषण, हिंसा की धमकी, निजी जानकारी और स्पैम प्रतिबंधित हैं। केवल अधिकार वाली सामग्री साझा करें। अनुचित सामग्री और उपयोगकर्ता को रिपोर्ट या ब्लॉक करें। समीक्षा के बाद सामग्री हटाई और अकाउंट निलंबित किया जा सकता है। निजी ऑफलाइन workspace के लिए सहमति आवश्यक नहीं है।','en':'Shared study prohibits harassment, hate, sexual content, child exploitation, threats, private personal information and spam. Share only content you have rights to. Report inappropriate content and block users. Reviewed content may be removed and accounts suspended. Private offline workspaces do not require acceptance.'}
class Acceptance(Base):
 __tablename__='ugc_acceptance'
 account_id:Mapped[int]=mapped_column(primary_key=True)
 version:Mapped[str]=mapped_column(String(32))
 accepted_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class Block(Base):
 __tablename__='ugc_block'
 __table_args__=(UniqueConstraint('account_id','target_id'),)
 id:Mapped[int]=mapped_column(primary_key=True)
 account_id:Mapped[int]=mapped_column(Integer,index=True)
 target_id:Mapped[int]=mapped_column(Integer,index=True)
class Moderation(Base):
 __tablename__='ugc_moderation'
 record_id:Mapped[str]=mapped_column(String(48),primary_key=True)
class Suspension(Base):
 __tablename__='ugc_suspension'
 account_id:Mapped[int]=mapped_column(primary_key=True)
class Report(Base):
 __tablename__='ugc_report'
 id:Mapped[str]=mapped_column(String(48),primary_key=True,default=lambda:secrets.token_urlsafe(18))
 reporter_id:Mapped[int]=mapped_column(Integer,index=True)
 record_id:Mapped[str]=mapped_column(String(48),index=True)
 owner_id:Mapped[int]=mapped_column(Integer)
 reason:Mapped[str]=mapped_column(String(24))
 text:Mapped[str]=mapped_column(Text,default='')
 evidence:Mapped[dict]=mapped_column(JSON,default=dict)
 created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
 resolved_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
 action:Mapped[str|None]=mapped_column(String(24),nullable=True)
 note:Mapped[str|None]=mapped_column(Text,nullable=True)
def accepted(db,aid):
 row=db.get(Acceptance,aid)
 return bool(row and row.version==VERSION)
def require_terms(db,aid):
 from .classroom import fail
 if db.get(Suspension,aid):fail('account_suspended',403)
 if not accepted(db,aid):fail('content_terms_required',403)
def blocked(db,a,b):
 if a==b:return False
 return db.scalar(select(Block.id).where(((Block.account_id==a)&(Block.target_id==b))|((Block.account_id==b)&(Block.target_id==a))).limit(1)) is not None
def visible(db,r,aid):
 return not db.get(Moderation,r.id) and not db.get(Suspension,r.owner_id) and not blocked(db,aid,r.owner_id)
def guard(db,r,aid):
 from .classroom import fail
 if not visible(db,r,aid):fail('content_unavailable',403)

def snapshot_authors(db, record, include_events=False):
 """Full snapshots may include ink from several collaborators, not just the owner."""
 from .classroom_models import ClassroomEvent
 authors = set(record.data.get('snapshot_authors', []))
 if record.kind == 'live' and (include_events or 'snapshot_authors' not in record.data):
  authors.update(db.scalars(select(ClassroomEvent.account_id).where(
   ClassroomEvent.room_id == record.id,
   ClassroomEvent.data['type'].as_string().in_(('snapshot', 'stroke', 'page', 'undo'))).distinct()))
 elif record.kind == 'workspace' and 'snapshot_authors' not in record.data:
  authors.update(record.data.get('editors', []))
 authors.add(record.owner_id)
 return sorted(authors)

def snapshot_allowed(db, record, aid, data=None):
 data = record.data if data is None else data
 if not data.get('snapshot', {}).get('pages'): return True
 authors = set(data.get('snapshot_authors', []))
 # Legacy and cached snapshots have no reliable attribution; retain every
 # historical visual contributor rather than trust the container owner.
 authors.update(snapshot_authors(db, record))
 return not any(blocked(db, aid, author) or db.get(Suspension, author) for author in authors)

def guard_cached(db, value, aid):
 """Cached idempotent replies cannot bypass a later block or moderation decision."""
 from .classroom_models import ClassroomRecord
 from .classroom import fail
 if isinstance(value, dict):
  if 'owner_id' in value and 'kind' in value and isinstance(value.get('id'), str):
   row = db.get(ClassroomRecord, value['id'])
   if row is None or not visible(db, row, aid): fail('content_unavailable', 403)
   if row.kind in ('live', 'workspace') and not snapshot_allowed(db, row, aid, value.get('data', {})):
    fail('content_unavailable', 403)
  author = value.get('account_id')
  if type(author) is int and (blocked(db, aid, author) or db.get(Suspension, author)):
   fail('content_unavailable', 403)
  for item in value.values(): guard_cached(db, item, aid)
 elif isinstance(value, list):
  for item in value: guard_cached(db, item, aid)

router=APIRouter()
@router.get('/safety')
def safety(request:Request,db=Depends(get_db)):
 from .classroom import require,Account
 a=require(request,db);rows=list(db.scalars(select(Block).where(Block.account_id==a.id)))
 ids=[r.target_id for r in rows];names={v.id:v.name for v in db.scalars(select(Account).where(Account.id.in_(ids)))}
 return {'version':VERSION,'accepted':accepted(db,a.id),'terms':TERMS,'blocked':[{'account_id':i,'name':names.get(i,str(i))} for i in ids]}
@router.post('/safety/terms')
async def accept(request:Request,db=Depends(get_db)):
 from .classroom import require,body,fail
 a=require(request,db);d=await body(request)
 if d.get('version')!=VERSION or d.get('accept') is not True:fail('explicit_acceptance_required')
 row=db.get(Acceptance,a.id)
 if row:row.version=VERSION;row.accepted_at=datetime.utcnow()
 else:db.add(Acceptance(account_id=a.id,version=VERSION))
 db.commit();return {'ok':True}
@router.post('/safety/blocks')
async def block(request:Request,db=Depends(get_db)):
 from .classroom import require,body,fail,Account
 a=require(request,db);d=await body(request);aid=d.get('account_id')
 if type(aid) is not int or aid==a.id or not db.get(Account,aid):fail('invalid_member')
 if type(d.get('blocked')) is not bool:fail('invalid_block')
 row=db.scalar(select(Block).where(Block.account_id==a.id,Block.target_id==aid))
 if d['blocked'] and not row:db.add(Block(account_id=a.id,target_id=aid))
 elif not d['blocked'] and row:db.delete(row)
 db.commit();return {'ok':True}
@router.post('/safety/reports')
async def report(request:Request,db=Depends(get_db)):
 from .classroom import require,body,text,record,workspace_access,group_access,rate,fail
 a=require(request,db);d=await body(request);r=record(db,text(d.get('record_id'),48))
 if r.kind=='workspace':workspace_access(db,r,a,d.get('token'))
 elif r.kind=='group':group_access(db,r.id,a)
 elif r.kind in ('discussion','assignment','live'):group_access(db,r.parent,a)
 elif r.kind=='submission':
  ass=record(db,r.parent,'assignment');_,member=group_access(db,ass.parent,a)
  if r.owner_id!=a.id and member.role not in ('owner','teacher'):fail('not_allowed',403)
 else:fail('not_allowed',403)
 reason=d.get('reason')
 if reason not in ('abuse','sexual','violence','spam','other'):fail('invalid_reason')
 rate(db,'ugc-report:'+str(a.id),5)
 report=Report(reporter_id=a.id,record_id=r.id,owner_id=r.owner_id,reason=reason,text=text(d.get('text',''),2000,False),evidence={'kind':r.kind,'data':r.data})
 db.add(report);db.commit();return {'ok':True,'report_id':report.id}
