"""python -m app.promo telegram --slot quiz|trick|revision|weekly [--dry-run] [--date YYYY-MM-DD]

Slots (IST): 07:30 quiz · 12:30 trick · 18:00 quiz · 20:30 revision · Sun 10:00 weekly.
--dry-run prints what the real run would post and changes nothing.
"""
import argparse
import html
import os
import sys
from datetime import date, datetime, timedelta, timezone

from . import pick, posted as plog, telegram

IST = timezone(timedelta(hours=5, minutes=30))
LETTERS = 'abcd'


def footer():
    link = os.environ.get('PROMO_LINK', '').strip()
    return '📚 रोज़ 10 मुफ़्त सवाल' + (f' · {html.escape(link)}' if link else '')


def poll_question(q):
    return f"[{pick.SUBJECT_HI.get(q['subject'], q['subject'])}] {q['question']}"


def plan(slot, day, data):
    """What this slot posts: a list of ('html', text) / ('poll', item) steps."""
    ids = set(data['telegram'])
    if slot == 'quiz':
        done = plog.batches(data, day.isoformat(), 'quiz')
        used = {it['chapter'] for b in done for it in b if it.get('chapter')}
        qs = pick.pick_quiz(day, len(done), ids, used)
        if not qs:
            return []
        when = 'सुबह' if not done else 'शाम'
        level = pick.LEVEL_HI.get(qs[0]['level'], '') if len({q['level'] for q in qs}) == 1 else 'मिला-जुला स्तर'
        head = (f'<b>🎯 {when} के {len(qs)} सवाल</b> ({level})\n'
                f'उत्तर चुनें — गलत होने पर 💡 दबाकर हल देखें। रात 8:30 बजे सभी उत्तर + हल।\n\n{footer()}')
        return [('html', head)] + [('poll', q) for q in qs]
    if slot == 'weekly':
        qs = pick.pick_weekly(day, ids)
        if not qs:
            return []
        head = (f'<b>🏆 रविवार साप्ताहिक टेस्ट — {len(qs)} सवाल</b>\n'
                f'सभी स्तर, सभी विषय, आसान से कठिन। अपने सही उत्तर गिनें: '
                f'{len(qs) * 9 // 10}+ शानदार · {len(qs) * 6 // 10}+ अच्छा · उससे कम → रोज़ के सवाल हल करते रहें।\n\n{footer()}')
        return [('html', head)] + [('poll', q) for q in qs]
    if slot == 'trick':
        t = pick.pick_trick(day, ids)
        if not t:
            return []
        title = html.escape(t['title'])
        text = (f'<b>💡 आज की ट्रिक</b> — {pick.SUBJECT_HI.get(t["subject"], "")}'
                + (f' · {title}' if title else '') + f'\n\n{telegram.md_to_html(t["text"])}\n\n{footer()}')
        return [('html', text, t)]
    if slot == 'revision':
        items = [it for b in plog.batches(data, day.isoformat(), 'quiz') for it in b]
        if not items:
            return []
        lines = [f'<b>📝 आज के {len(items)} सवालों के उत्तर + हल</b>', '']
        for i, it in enumerate(items, 1):
            q = html.escape(it['q'][:110] + ('…' if len(it['q']) > 110 else ''))
            link = telegram.message_link(it.get('msg'))
            lines.append(f'{i}. <a href="{html.escape(link)}">{q}</a>' if link else f'{i}. {q}')
            lines.append(f'✅ ({LETTERS[it["ans"]]}) {html.escape(it["opt"])}')
            if it.get('exp'):
                lines.append(f'💡 {html.escape(it["exp"])}')
            lines.append('')
        lines.append(footer())
        return [('html', '\n'.join(lines), {'id': f'revision#{day.isoformat()}'})]
    raise SystemExit(f'unknown slot {slot}')


def show(steps):
    for step in steps:
        if step[0] == 'html':
            print('--- message ---\n' + step[1] + '\n')
        else:
            q = step[1]
            print(f"--- poll ({q['difficulty']}) {q['id']} ---\n{poll_question(q)}")
            for i, o in enumerate(q['options']):
                print(f"  ({LETTERS[i]}) {o}{'  ✅' if i == q['answer'] else ''}")
            print(f"  💡 {q['explanation']}\n")


def run(slot, day, data):
    """Post the steps; record what went out even if a later send fails."""
    steps = plan(slot, day, data)
    sent, error = [], None
    try:
        for step in steps:
            if step[0] == 'html':
                ids = telegram.send_html(step[1])
                if len(step) > 2:
                    sent.append({'id': step[2]['id'], 'msg': ids[0] if ids else None})
            else:
                q = step[1]
                msg = telegram.send_poll(poll_question(q), q['options'], q['answer'], q['explanation'])
                sent.append({'id': q['id'], 'msg': msg, 'chapter': q['chapter'], 'q': q['question'],
                             'ans': q['answer'], 'opt': q['options'][q['answer']], 'exp': q['explanation']})
    except telegram.TelegramError as e:
        error = e
    if sent:
        plog.record(data, day.isoformat(), slot, sent)
        plog.save(data)
    print(f'{slot}: posted {len(sent)} item(s)' + (f'; stopped: {error}' if error else ''))
    if not steps:
        print(f'{slot}: nothing to post')
    return 1 if error else 0


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(prog='python -m app.promo', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    t = sub.add_parser('telegram', help='post one slot to the Telegram channel')
    t.add_argument('--slot', required=True, choices=['quiz', 'trick', 'revision', 'weekly'])
    t.add_argument('--dry-run', action='store_true')
    t.add_argument('--date', help='YYYY-MM-DD (default: today in IST)')
    a = ap.parse_args(argv)
    day = date.fromisoformat(a.date) if a.date else datetime.now(IST).date()
    data = plog.load()
    if a.dry_run:
        show(plan(a.slot, day, data))
        return 0
    return run(a.slot, day, data)


if __name__ == '__main__':
    sys.exit(main())
