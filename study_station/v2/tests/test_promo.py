"""Telegram promotion: picker rules, explanation text, Telegram client, posted-log, slot runs."""
from datetime import date, datetime

import httpx
import pytest

from app.importers import ParsedQuestion
from app.promo import __main__ as cli, pick, posted as plog, telegram


def pq(text='भारत की राजधानी क्या है?', options=('दिल्ली', 'मुंबई', 'कोलकाता', 'चेन्नई'), ans=0, sol='दिल्ली राजधानी है।'):
    return ParsedQuestion(1, text, list(options), ans, sol)


@pytest.fixture(autouse=True)
def no_wait(monkeypatch, tmp_path):
    monkeypatch.setattr(telegram, 'SEND_GAP', 0)
    monkeypatch.setattr(plog, 'POSTED', tmp_path / 'posted.json')
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', '123:SECRET-TOKEN')
    monkeypatch.setenv('TELEGRAM_CHANNEL_ID', '@ss_test')


# ------------------------------------------------------------------------------------------- picker rules
def test_question_rules():
    en = pq('What is the capital of India?', ('Delhi', 'Mumbai', 'Kolkata', 'Chennai'))
    assert pick.question_problem(pq(), en) is None
    assert pick.question_problem(pq(), None) == 'hi/en answer differ'
    assert pick.question_problem(pq(ans=1), en) == 'hi/en answer differ'
    assert pick.question_problem(pq('क' * 251 + '?'), en) == 'question too long'
    assert pick.question_problem(pq(options=('दिल्ली', 'म' * 81, 'क', 'च')), en) == 'option too long'
    assert pick.question_problem(pq('दी गई आकृति में कितने त्रिभुज हैं?'), en) == 'needs a picture/passage'
    assert pick.question_problem(pq('रिक्त स्थान 131 के लिए सही शब्द चुनें।'), en) == 'needs a picture/passage'
    assert pick.question_problem(pq(options=('दिल्ली', 'मुंबई', '(a) और (b) दोनों', 'चेन्नई')), en) \
        == 'option refers to other options'


def test_explanation_names_the_answer():
    sol = ('जिनेवा सामान्य जाल है क्योंकि कई एजेंसियाँ वहीं हैं। 1957 में स्थापित IAEA का मुख्यालय वियना में है। '
           'अतः उत्तर वियना है।')
    e = pick.explanation(sol, 'वियना')
    assert e.startswith('उत्तर: वियना।') and 'मुख्यालय वियना' in e and len(e) <= 200
    assert len(pick.explanation('क ' * 300, 'ख')) <= 200


def test_trick_blocks():
    text = ('# शीर्षक\nपरिचय\n\n**ट्रिक 1 — पहली**\n' + 'क' * 250 + '\n\n**ट्रिक 2 — छोटी**\nबस\n\n'
            '## ⏭️ Skip Strategy\n' + 'ख' * 300 + '\n\n## सारांश\n' + 'ग' * 300)
    blocks = pick.trick_blocks(text)
    assert len(blocks) == 1 and blocks[0].startswith('**ट्रिक 1')


def test_real_picks_follow_the_rules():
    day = date(2026, 10, 23)
    qs = pick.pick_quiz(day, 0, set())
    assert len(qs) == 5
    assert pick.pick_quiz(day, 0, set()) == qs                          # seeded: dry-run == real run
    assert {q['subject'] for q in qs} == set(pick.SUBJECTS)
    for q in qs:
        assert q['difficulty'] in ('easy', 'medium')
        assert len(q['question']) <= pick.MAX_QUESTION and all(len(o) <= pick.MAX_OPTION for o in q['options'])
        assert len(q['explanation']) <= 200
        assert pick.chapter_ok(str(pick.books_root() / q['chapter']))
    later = pick.pick_quiz(day, 0, {q['id'] for q in qs}, {q['chapter'] for q in qs})
    assert not {q['id'] for q in qs} & {q['id'] for q in later}


# ------------------------------------------------------------------------------------------- telegram client
class Resp:
    def __init__(self, status, body):
        self.status_code, self._body = status, body

    def json(self):
        return self._body


def test_poll_payload_and_retry(monkeypatch):
    calls = []

    def post(url, json, timeout):
        calls.append((url, json))
        if len(calls) == 1:
            return Resp(429, {'ok': False, 'parameters': {'retry_after': 0}})
        return Resp(200, {'ok': True, 'result': {'message_id': 42}})
    monkeypatch.setattr(httpx, 'post', post)
    monkeypatch.setattr(telegram.time, 'sleep', lambda s: None)
    assert telegram.send_poll('Q?', ['a', 'b', 'c', 'd'], 2, 'उत्तर: c') == 42
    body = calls[-1][1]
    assert body['type'] == 'quiz' and body['correct_option_ids'] == [2] and body['chat_id'] == '@ss_test'
    assert body['options'] == [{'text': o} for o in 'abcd']


def test_token_never_in_errors(monkeypatch):
    def boom(url, **kw):
        raise httpx.ConnectError(f'cannot reach {url}')
    monkeypatch.setattr(httpx, 'post', boom)
    with pytest.raises(telegram.TelegramError) as e:
        telegram.send_html('hi')
    assert 'SECRET' not in str(e.value)
    monkeypatch.setattr(httpx, 'post', lambda url, **kw: Resp(401, {'ok': False, 'description': 'Unauthorized'}))
    with pytest.raises(telegram.TelegramError) as e:
        telegram.send_html('hi')
    assert 'SECRET' not in str(e.value) and '401' in str(e.value)


def test_md_to_html_escapes():
    assert telegram.md_to_html('## शीर्षक\n**<b>x</b>** & y') == '<b>शीर्षक</b>\n<b>&lt;b&gt;x&lt;/b&gt;</b> &amp; y'


def test_chunks_split_on_lines():
    parts = telegram.chunks('\n'.join(['क' * 100] * 100), limit=1000)
    assert all(len(p) <= 1000 for p in parts) and ''.join(parts).count('क') == 10000


# ------------------------------------------------------------------------------------------- slots end to end
def fake_telegram(monkeypatch):
    sent = []
    monkeypatch.setattr(telegram, 'send_poll', lambda *a: sent.append(('poll', a)) or len(sent))
    monkeypatch.setattr(telegram, 'send_html', lambda t: sent.append(('html', t)) or [len(sent)])
    return sent


def test_quiz_then_revision(monkeypatch):
    sent = fake_telegram(monkeypatch)
    day = date(2026, 10, 23)
    assert cli.main(['telegram', '--slot', 'quiz', '--date', day.isoformat()]) == 0
    assert cli.main(['telegram', '--slot', 'quiz', '--date', day.isoformat()]) == 0
    data = plog.load()
    morning, evening = plog.batches(data, day.isoformat(), 'quiz')
    assert len(morning) == 5 and len(evening) == 5
    assert not {i['id'] for i in morning} & {i['id'] for i in evening}
    assert not {i['chapter'] for i in morning} & {i['chapter'] for i in evening}
    assert len(data['telegram']) == 10
    sent.clear()
    assert cli.main(['telegram', '--slot', 'revision', '--date', day.isoformat()]) == 0
    text = sent[0][1]
    assert 'आज के 10 सवालों' in text and text.count('✅') == 10 and 'https://t.me/ss_test/' in text


def test_partial_failure_is_recorded(monkeypatch):
    n = []

    def poll(*a):
        n.append(1)
        if len(n) == 3:
            raise telegram.TelegramError('Telegram HTTP 400: bad')
        return len(n)
    monkeypatch.setattr(telegram, 'send_poll', poll)
    monkeypatch.setattr(telegram, 'send_html', lambda t: [0])
    assert cli.main(['telegram', '--slot', 'quiz', '--date', '2026-10-24']) == 1
    assert len(plog.load()['telegram']) == 2


def test_dry_run_changes_nothing(monkeypatch, capsys):
    sent = fake_telegram(monkeypatch)
    assert cli.main(['telegram', '--slot', 'trick', '--dry-run', '--date', '2026-10-23']) == 0
    assert 'आज की ट्रिक' in capsys.readouterr().out
    assert not sent and not plog.POSTED.exists()


def test_auto_posts_each_slot_once_inside_its_window(monkeypatch):
    sent = fake_telegram(monkeypatch)
    day = '2026-10-23'                                                      # a Friday
    run = lambda now: cli.main(['telegram', '--slot', 'auto', '--date', day, '--now', now])
    assert run('06:00') == 0 and not sent                                   # too early
    assert run('11:05') == 0                                                # schedule was late: still posts
    assert len(plog.batches(plog.load(), day, 'quiz')) == 1
    n = len(sent)
    assert run('11:35') == 0 and len(sent) == n                             # already done
    assert run('15:00') == 0 and len(plog.batches(plog.load(), day, 'trick')) == 1
    assert run('19:00') == 0 and len(plog.batches(plog.load(), day, 'quiz')) == 2
    assert run('19:30') == 0 and len(plog.batches(plog.load(), day, 'quiz')) == 2   # evening done once
    assert run('22:10') == 0 and len(plog.batches(plog.load(), day, 'revision')) == 1
    assert not plog.batches(plog.load(), day, 'weekly')
    n = len(sent)
    assert run('23:30') == 0 and len(sent) == n


def test_auto_windows():
    data = {'telegram': [], 'shorts': [], 'days': {}}
    t = lambda hm: datetime.strptime(hm, '%H:%M').time()
    assert cli.due_slots(date(2026, 10, 23), t('19:00'), data) == [('quiz', 'pm')]   # morning missed: evening still goes
    assert cli.due_slots(date(2026, 10, 23), t('12:10'), data) == []                 # morning window is over
    assert cli.due_slots(date(2026, 10, 25), t('10:30'), data) == [('quiz', 'am'), ('weekly', None)]
