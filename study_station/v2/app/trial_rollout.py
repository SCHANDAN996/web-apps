"""Versioned launch extension. Dry-run by default; no payment or progress changes."""
import argparse,json
from datetime import datetime
from sqlalchemy import select,text
from .membership import TRIAL_POLICY_VERSION,trial_end
from .membership_models import Membership,TrialRollout
from .classroom_models import ClassroomAccount

def rollout(db,apply=False,now=None):
    now=now or datetime.utcnow()
    if apply: db.execute(text('BEGIN IMMEDIATE'))
    marker=db.get(TrialRollout,TRIAL_POLICY_VERSION)
    anchor=marker.activated_at if marker else now
    end=trial_end(anchor)
    if apply and marker is None:db.add(TrialRollout(version=TRIAL_POLICY_VERSION,activated_at=anchor))
    changed=0
    for a in db.scalars(select(ClassroomAccount).where(ClassroomAccount.created_at<=anchor)):
        if not a.storage_namespace:continue
        m=db.get(Membership,a.storage_namespace)
        if m and m.trial_policy_version==TRIAL_POLICY_VERSION:continue
        changed+=1
        if not apply:continue
        if m is None:
            m=Membership(namespace=a.storage_namespace,trial_started_at=anchor,trial_ends_at=end)
            db.add(m)
        else:m.trial_ends_at=max(m.trial_ends_at,end)
        m.trial_policy_version=TRIAL_POLICY_VERSION
    if apply:db.commit()
    return dict(apply=apply,version=TRIAL_POLICY_VERSION,activated_at=anchor.isoformat()+'Z',minimum_trial_end=end.isoformat()+'Z',accounts=changed)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    from . import main as application
    from .db import SessionLocal,ensure_schema
    ensure_schema()
    with SessionLocal() as db:print(json.dumps(rollout(db,args.apply)))
if __name__=='__main__':main()
