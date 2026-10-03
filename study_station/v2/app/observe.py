"""
Read-only health & metrics report for humans and the observer agent.

  python -m app.observe              # JSON
  python -m app.observe --markdown   # short Hindi/English report
  python -m app.observe --url https://studystation.in   # also ping /healthz

Exit code 0 = healthy, 1 = warnings, 2 = critical — handy for cron/monitoring.
Never writes to the database.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import case, func, select

from . import config
from .db import SessionLocal, engine, ensure_schema
from .models import (AiUsage, Attempt, AttemptAnswer, CAItem, Device, Job, Question, QuestionReport,
                     SourceHealth, Subject, Topic)
from .services import USABLE, today_ist

THIN_TOPIC = 30          # fewer usable questions than this = content gap


def collect(db, url=None):
    today = today_ist()
    now = datetime.utcnow()
    day_ago, week_ago = now - timedelta(days=1), now - timedelta(days=7)
    c = lambda q: db.scalar(q) or 0

    # ---- learners
    learners = {
        'devices_total': c(select(func.count(Device.id))),
        'active_24h': c(select(func.count(Device.id)).where(Device.last_seen >= day_ago)),
        'active_7d': c(select(func.count(Device.id)).where(Device.last_seen >= week_ago)),
        'answers_24h': c(select(func.count(AttemptAnswer.id)).where(AttemptAnswer.answered_at >= day_ago)),
        'mocks_finished_7d': c(select(func.count(Attempt.id)).where(Attempt.mode == 'mock', Attempt.finished_at >= week_ago)),
    }

    # ---- content
    status = dict(db.execute(select(Question.review_status, func.count()).group_by(Question.review_status)).all())
    per_topic = dict(db.execute(select(Question.topic_id, func.count()).where(USABLE).group_by(Question.topic_id)).all())
    thin = [{'topic': f'{t.subject.slug}/{t.slug}', 'usable': per_topic.get(t.id, 0)}
            for t in db.scalars(select(Topic).join(Subject).order_by(Subject.id, Topic.order))
            if per_topic.get(t.id, 0) < THIN_TOPIC]
    # questions students get wrong unusually often → maybe a wrong key
    hard = db.execute(
        select(AttemptAnswer.question_id, func.count(), func.sum(case((AttemptAnswer.correct.is_(True), 1), else_=0)))
        .where(AttemptAnswer.chosen_index.is_not(None)).group_by(AttemptAnswer.question_id)
        .having(func.count() >= 20)).all()
    suspicious = [qid for qid, n, ok in hard if ok is not None and n and ok / n < 0.15]
    content = {
        'questions_by_status': status,
        'open_reports': c(select(func.count(QuestionReport.id)).where(QuestionReport.resolved_at.is_(None))),
        'thin_topics': thin,
        'suspicious_keys': suspicious[:50],          # <15% correct over ≥20 answers
    }

    # ---- jobs
    health = [{'source': h.source, 'failures': h.consecutive_failures, 'last_ok': h.last_ok.isoformat() if h.last_ok else None,
               'error': h.last_error} for h in db.scalars(select(SourceHealth).order_by(SourceHealth.source))]
    last_ok = max((h.last_ok for h in db.scalars(select(SourceHealth)) if h.last_ok), default=None)
    jobs = {
        'open_verified': c(select(func.count(Job.id)).where(Job.status == 'verified', Job.job_type == 'latest', Job.last_date >= today)),
        'pending': c(select(func.count(Job.id)).where(Job.status == 'pending')),
        'upcoming': c(select(func.count(Job.id)).where(Job.job_type == 'upcoming')),
        'closing_3d': c(select(func.count(Job.id)).where(Job.status == 'verified', Job.job_type == 'latest',
                                                         Job.last_date >= today, Job.last_date <= today + timedelta(days=3))),
        'last_successful_sweep': last_ok.isoformat() if last_ok else None,
        'sources': health,
    }

    # ---- current affairs & AI
    last_ca = db.scalar(select(func.max(CAItem.created_at)))
    ca = {'items_7d': c(select(func.count(CAItem.id)).where(CAItem.created_at >= week_ago, CAItem.status == 'published')),
          'last_item_at': last_ca.isoformat() if last_ca else None}
    ai = {'enabled': bool(config.ANTHROPIC_API_KEY),
          'calls_today': c(select(func.coalesce(func.sum(AiUsage.count), 0)).where(AiUsage.day == today)),
          'daily_limit_total': config.AI_DAILY_LIMIT_TOTAL}

    # ---- web
    web = None
    if url:
        import httpx
        try:
            r = httpx.get(url.rstrip('/') + '/healthz', timeout=10)
            web = {'healthz_status': r.status_code, 'ok': r.status_code == 200}
        except httpx.HTTPError as e:
            web = {'ok': False, 'error': str(e)[:200]}

    # ---- alerts (critical first)
    alerts = []

    def alert(level, msg):
        alerts.append({'level': level, 'msg': msg})
    if web and not web['ok']:
        alert('critical', 'website /healthz is failing')
    if not last_ok or now - last_ok > timedelta(hours=12):
        alert('critical', 'no successful job sweep in 12h — check cron / sources')
    broken = [h['source'] for h in health if h['failures'] >= 3]
    if broken:
        alert('warning', f'job sources failing ≥3 runs: {", ".join(broken)}')
    if jobs['open_verified'] == 0:
        alert('warning', 'no open verified jobs on the site')
    if content['open_reports'] >= 10:
        alert('warning', f'{content["open_reports"]} student reports waiting in /admin')
    if suspicious:
        alert('warning', f'{len(suspicious)} questions with <15% correct — possible wrong answer keys')
    if not last_ca or now - last_ca > timedelta(hours=36):
        alert('warning', 'no current-affairs items in 36h — check cron / feeds')
    if ai['enabled'] and ai['calls_today'] >= 0.8 * ai['daily_limit_total']:
        alert('warning', 'AI usage above 80% of today\'s limit')
    if thin:
        alert('info', f'{len(thin)} topics have < {THIN_TOPIC} questions (python -m app.generate --fill)')
    backups = sorted(Path('/var/backups/studystation').glob('*.db.gz')) if Path('/var/backups/studystation').exists() else []
    if backups and datetime.fromtimestamp(backups[-1].stat().st_mtime) < now - timedelta(days=2):
        alert('warning', 'latest backup is older than 2 days')

    return {'generated_at': now.isoformat(timespec='seconds'), 'learners': learners, 'content': content,
            'jobs': jobs, 'current_affairs': ca, 'ai': ai, 'web': web, 'alerts': alerts}


def to_markdown(r):
    icon = {'critical': '🔴', 'warning': '🟠', 'info': '🔵'}
    out = [f"# Study Station — हालत ({r['generated_at']} UTC)", '']
    out += [f"- {icon[a['level']]} {a['msg']}" for a in r['alerts']] or ['- ✅ सब ठीक']
    L, C, J = r['learners'], r['content'], r['jobs']
    out += ['', '## Students',
            f"- सक्रिय: 24h {L['active_24h']} · 7d {L['active_7d']} · कुल {L['devices_total']}",
            f"- 24h में जवाब: {L['answers_24h']} · 7d में mock: {L['mocks_finished_7d']}",
            '', '## Content',
            f"- सवाल: {C['questions_by_status']} · खुली reports: {C['open_reports']}",
            f"- कमज़ोर topics: {len(C['thin_topics'])} · संदिग्ध answer keys: {len(C['suspicious_keys'])}",
            '', '## Jobs',
            f"- खुली: {J['open_verified']} · 3 दिन में बंद: {J['closing_3d']} · आने वाली: {J['upcoming']} · pending: {J['pending']}",
            f"- आख़िरी सफल sweep: {J['last_successful_sweep']}",
            '', '## Current affairs / AI',
            f"- 7 दिन में ख़बरें: {r['current_affairs']['items_7d']} · AI: {'on' if r['ai']['enabled'] else 'off'}, आज {r['ai']['calls_today']} calls"]
    return '\n'.join(out)


def exit_code(r):
    levels = {a['level'] for a in r['alerts']}
    return 2 if 'critical' in levels else (1 if 'warning' in levels else 0)


def main(argv=None):
    p = argparse.ArgumentParser(prog='python -m app.observe')
    p.add_argument('--markdown', action='store_true')
    p.add_argument('--url', default=config.SITE_URL or None)
    args = p.parse_args(argv)
    ensure_schema(engine)
    with SessionLocal() as db:
        r = collect(db, args.url)
    print(to_markdown(r) if args.markdown else json.dumps(r, ensure_ascii=False, indent=1, default=str))
    return exit_code(r)


if __name__ == '__main__':
    sys.exit(main())
