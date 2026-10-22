"""Shorts: mixed-script text, layout inside the safe area, ffmpeg command, captions, picker."""
from datetime import date

import pytest

from app.promo import shorts

Q = {'id': 'x#Set01#Q1', 'subject': 'GK', 'level': '12th_Level', 'chapter': '12th_Level/GK/B/Chapter_01_X',
     'question': 'भारत के संविधान (Constitution) का कौन-सा अनुच्छेद (Article) अस्पृश्यता का अंत करता है और '
                 'इसे दंडनीय अपराध बनाता है?',
     'options': ['अनुच्छेद 14', 'अनुच्छेद 17', 'अनुच्छेद 21', 'अनुच्छेद 32'], 'answer': 1,
     'explanation': 'उत्तर: अनुच्छेद 17। अनुच्छेद 17 अस्पृश्यता का अंत करता है।', 'difficulty': 'easy'}


def test_runs_split_scripts_and_refuse_missing_glyphs():
    assert [k for k, _ in shorts.runs('अनुच्छेद 17 (Article)')] == ['dev', 'lat']
    with pytest.raises(shorts.DoesNotFit):
        shorts.runs('√2 का मान')


def test_frames_stay_inside_the_safe_area():
    L = shorts.layout(Q)
    for img in (shorts.frame_question(Q, L), shorts.frame_question(Q, L, show=1), shorts.frame_answer(Q, L)):
        below = img.crop((0, shorts.BOTTOM, shorts.W, shorts.H))
        assert below.getcolors(1) is not None, 'something was drawn under the safe area'
        side = img.crop((0, shorts.TOP, shorts.LEFT - 4, shorts.BOTTOM))
        assert side.getcolors(1) is not None, 'something was drawn in the left margin'


def test_too_long_question_is_refused():
    with pytest.raises(shorts.DoesNotFit):
        shorts.layout({**Q, 'question': 'बहुत लंबा प्रश्न ' * 60})


def test_render_builds_the_ffmpeg_command(monkeypatch, tmp_path):
    seen = {}

    def run(cmd, check):
        seen['cmd'] = cmd
        seen['list'] = (tmp_path / 'w' / 'list.txt').read_text()
    monkeypatch.setattr(shorts.subprocess, 'run', run)
    monkeypatch.setattr(shorts, 'COUNTDOWN_FPS', 1)
    shorts.render(Q, tmp_path / 'out.mp4', tmp_path / 'w')
    cmd = seen['cmd']
    assert cmd[0] == 'ffmpeg' and cmd[-1] == str(tmp_path / 'out.mp4')
    assert '+faststart' in cmd and 'libx264' in cmd and 'aac' in cmd and 'anullsrc=r=44100:cl=stereo' in cmd
    durations = [float(l.split()[1]) for l in seen['list'].splitlines() if l.startswith('duration')]
    assert abs(sum(durations) - 24) < 0.01
    assert not (tmp_path / 'w').exists()                     # frames are cleaned up


def test_caption(monkeypatch):
    monkeypatch.setenv('PROMO_TELEGRAM', 't.me/ss_test')
    text = shorts.caption(Q)
    title = text.split('\n')[0]
    assert len(title) <= 90 and title.endswith('#Shorts')
    assert 't.me/ss_test' in text and text.count('#') >= 5 and 'अनुच्छेद 17' in text


def test_pick_shorts():
    day = date(2026, 10, 24)
    qs = shorts.pick_shorts(day, 3, [])
    assert len(qs) == 3 and qs == shorts.pick_shorts(day, 3, [])
    for q in qs:
        assert shorts.short_ok(q) and 'Current_Affairs' not in q['chapter']
        assert q['difficulty'] in ('easy', 'medium')
    assert not {q['id'] for q in qs} & {q['id'] for q in shorts.pick_shorts(day, 3, [q['id'] for q in qs])}


def test_send_video_upload(monkeypatch, tmp_path):
    from app.promo import telegram
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', '1:SECRET')
    monkeypatch.setenv('TELEGRAM_CHANNEL_ID', '@ss_test')
    monkeypatch.setattr(telegram, 'SEND_GAP', 0)
    seen = {}

    class R:
        status_code = 200

        def json(self):
            return {'ok': True, 'result': {'message_id': 7}}

    def post(url, data=None, files=None, timeout=None, json=None):
        seen.update(url=url, data=data, name=files['video'][0])
        return R()
    monkeypatch.setattr(telegram.httpx, 'post', post)
    v = tmp_path / '01.mp4'
    v.write_bytes(b'x')
    assert telegram.send_video(v, shorts.telegram_caption(Q)) == 7
    assert seen['url'].endswith('/sendVideo') and seen['name'] == '01.mp4'
    assert seen['data']['chat_id'] == '@ss_test' and 'अनुच्छेद 17' not in seen['data']['caption']   # no spoiler
