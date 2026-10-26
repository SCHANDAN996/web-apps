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
    from PIL import ImageChops
    L = shorts.layout(Q)
    bg = shorts.background('soft')
    for img in (shorts.frame_question(Q, L), shorts.frame_question(Q, L, show=1), shorts.frame_answer(Q, L)):
        # Only the background may show under the safe area and in the left margin (card shadows are allowed to
        # spill a few pixels, so compare from 60 px below the safe area and the outer 16 px of the side margin).
        below = (0, shorts.BOTTOM + 60, shorts.W, shorts.H)
        assert ImageChops.difference(img.crop(below), bg.crop(below)).getbbox() is None, 'drawn under the safe area'
        side = (0, shorts.TOP, shorts.LEFT - 56, shorts.BOTTOM)
        assert ImageChops.difference(img.crop(side), bg.crop(side)).getbbox() is None, 'drawn in the left margin'


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
    assert float(cmd[cmd.index('-t') + 1]) == 24
    assert '+faststart' in cmd and 'libx264' in cmd and 'aac' in cmd and any(a.startswith("aevalsrc='") for a in cmd)
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


def test_soundtrack_follows_the_scenes():
    expr = shorts.sound_expr()
    cd, ans = shorts.scene_start('countdown'), shorts.scene_start('answer')
    assert expr.count('1200') == int(ans - cd)                 # one tick per countdown second
    assert f'between(t,{ans:.2f}' in expr                       # the ding starts with the answer
    assert "'" not in expr and ':' not in expr                  # safe inside the quoted lavfi option


def test_end_screen_shows_channel_url_without_claiming_a_bio_link(monkeypatch):
    monkeypatch.setenv('PROMO_TELEGRAM', 't.me/ss_test')
    seen = []
    real = shorts.draw_block
    monkeypatch.setattr(shorts, 'draw_block', lambda d, x, y, lines, *a, **k: seen.extend(lines) or real(d, x, y, lines, *a, **k))
    drawn = []
    real_line = shorts.draw_line
    monkeypatch.setattr(shorts, 'draw_line', lambda d, x, y, line, *a, **k: drawn.append(line) or real_line(d, x, y, line, *a, **k))
    monkeypatch.setattr(shorts, 'COUNTDOWN_FPS', 1)
    end = shorts.frames(Q)[-1][0]
    assert end.size == (shorts.W, shorts.H)
    assert 'Telegram: t.me/ss_test' in drawn
    assert 'लिंक Bio में है' not in seen and 'लिंक Bio में है' not in drawn


def test_first_frame_contains_the_question_and_options():
    from PIL import ImageChops
    base = shorts.frame_question(Q, shorts.layout(Q))
    hook = shorts.frames(Q)[0][0]
    # The opening challenge badge may change the header; the question/option cards must be visible immediately.
    box = (0, shorts.TOP + 80, shorts.W, shorts.BOTTOM)
    assert ImageChops.difference(base.crop(box), hook.crop(box)).getbbox() is None


def test_answer_has_eight_seconds_and_total_remains_twenty_four():
    sequence = shorts.frames(Q)
    assert sequence[-2][1] == 8
    assert sequence[-1][1] == 2
    assert abs(sum(seconds for _, seconds in sequence) - 24) < .001


def test_public_caption_does_not_spoil_the_solution(monkeypatch):
    monkeypatch.setenv('PROMO_TELEGRAM', 't.me/ss_test')
    text = shorts.caption(Q)
    assert Q['explanation'] not in text
    assert 'अस्पृश्यता का अंत करता है।' not in text
    assert all(option in text for option in Q['options'])
    assert '10 मुफ़्त' not in text


def test_short_rejects_explanation_too_long_to_read_without_truncating():
    long = {**Q, 'explanation': 'यह तथ्य समझना जरूरी है ' * 15}
    assert not shorts.short_ok(long)
    with pytest.raises(shorts.DoesNotFit, match='explanation'):
        shorts.layout(long)
