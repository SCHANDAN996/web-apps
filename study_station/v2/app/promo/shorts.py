"""Shorts / Reels from the books: a 24-second 1080×1920 video per question (no voice).

0–2 s hook · 2–9 s question + options · 9–14 s countdown 5…1 · 14–20 s answer + solution · 20–24 s call to action.
Sound: synthesised chime, countdown ticks and an answer 'ding' (sound_expr) — no music file, no licence.
Frames are drawn with Pillow (Noto Sans Devanagari for Hindi, Noto Sans for Latin — both OFL, in
study_station/promo/fonts) and joined with ffmpeg. A question whose text cannot be drawn (missing glyph, does
not fit at the smallest size) is refused and the next one is taken.

    python -m app.promo shorts --count 3 [--level 12th] [--out DIR] [--date YYYY-MM-DD] [--dry-run]
"""
import os
import random
import re
import shutil
import subprocess
from datetime import date
from functools import lru_cache
from pathlib import Path

from . import pick

W, H = 1080, 1920
LEFT, RIGHT, TOP, BOTTOM = 72, W - 72, 210, 1560     # YouTube/Instagram cover the bottom ~350 px and the top bar
FONTS = Path(__file__).resolve().parents[3] / 'promo' / 'fonts'
C = {'bg': '#F9F9FF', 'card': '#F3F3FA', 'card_hi': '#E8E7EE', 'text': '#1A1B20', 'muted': '#44474F',
     'primary': '#005BBF', 'on_primary': '#FFFFFF', 'primary_c': '#D8E2FF', 'on_primary_c': '#2A4678',
     'success': '#1B6B45', 'success_c': '#ABF9C8', 'on_success_c': '#003920', 'outline': '#C4C6D0'}
SCENES = [('hook', 2.0), ('question', 7.0), ('countdown', 5.0), ('answer', 6.0), ('cta', 4.0)]
COUNTDOWN_FPS = 10
MAX_Q, MAX_OPT = 160, 40
LEVEL_ARG = {'10th': '10th_Level', '12th': '12th_Level', 'graduation': 'Graduation_Level'}
HASHTAG = {'GK': '#GKinHindi', 'Reasoning': '#Reasoning', 'Maths': '#MathsTricks', 'English': '#EnglishGrammar'}
DEVANAGARI = re.compile(r'[ऀ-ॿ꣠-ꣿ᳐-᳿‌‍]')


class DoesNotFit(Exception):
    pass


# ------------------------------------------------------------------------------------------------ text
@lru_cache(maxsize=None)
def _cmap(name):
    from fontTools.ttLib import TTFont
    return set(TTFont(FONTS / name).getBestCmap())


@lru_cache(maxsize=None)
def font(kind, size, bold=False):
    from PIL import ImageFont
    name = {'dev': 'NotoSansDevanagari', 'lat': 'NotoSans'}[kind] + ('-Bold' if bold else '-Regular') + '.ttf'
    return ImageFont.truetype(str(FONTS / name), size, layout_engine=ImageFont.Layout.RAQM)


def runs(text):
    """Split text into (kind, chunk) runs: Devanagari letters → 'dev', the rest → 'lat'. Characters both fonts
    have (digits, punctuation, spaces) stay in the current run so shaping is not broken up."""
    dev, lat = _cmap('NotoSansDevanagari-Regular.ttf'), _cmap('NotoSans-Regular.ttf')
    out, cur, kind = [], '', None
    for ch in text:
        cp = ord(ch)
        if DEVANAGARI.match(ch):
            k = 'dev'
        elif cp in lat and cp in dev or ch.isspace():
            k = kind or ('lat' if cp in lat else 'dev')
        elif cp in lat:
            k = 'lat'
        elif cp in dev:
            k = 'dev'
        else:
            raise DoesNotFit(f'no glyph for {ch!r}')
        if k != kind and cur:
            out.append((kind, cur))
            cur = ''
        kind, cur = k, cur + ch
    if cur:
        out.append((kind, cur))
    return out


def width(text, size, bold=False):
    return sum(font(k, size, bold).getlength(t) for k, t in runs(text))


def wrap(text, size, maxw, bold=False):
    lines = []
    for para in text.split('\n'):
        cur = ''
        for word in para.split():
            trial = f'{cur} {word}' if cur else word
            if width(trial, size, bold) <= maxw:
                cur = trial
            elif not cur or width(word, size, bold) > maxw:
                raise DoesNotFit('word wider than the box')
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return [l for l in lines if l.strip()] or ['']


def line_h(size):
    return int(size * 1.5)                 # room for Devanagari matras above and below


def fit(text, maxw, maxh, sizes, bold=False):
    """Largest size from `sizes` at which `text` fits the box → (size, lines); else DoesNotFit."""
    for s in sizes:
        try:
            lines = wrap(text, s, maxw, bold)
        except DoesNotFit:
            continue
        if len(lines) * line_h(s) <= maxh:
            return s, lines
    raise DoesNotFit(f'does not fit {maxw}×{maxh}: {text[:40]}')


def draw_line(d, x, y, line, size, fill, bold=False):
    for k, t in runs(line):
        f = font(k, size, bold)
        d.text((x, y + line_h(size) // 2), t, font=f, fill=fill, anchor='lm')
        x += f.getlength(t)


def draw_block(d, x, y, lines, size, fill, bold=False, center_w=None):
    for i, line in enumerate(lines):
        lx = x + (center_w - width(line, size, bold)) / 2 if center_w else x
        draw_line(d, lx, y + i * line_h(size), line, size, fill, bold)
    return y + len(lines) * line_h(size)


# ------------------------------------------------------------------------------------------------ frames
LETTER_COLORS = ['#005BBF', '#7A3EC8', '#C2570C', '#0F7B6C']     # A–D: one colour each, white letter
BRAND_TOP, BRAND_BOTTOM = '#0B6BD8', '#003A85'                    # hook/end screens: brand-blue gradient
SOFT_TOP, SOFT_BOTTOM = '#E3ECFF', '#F9F9FF'                      # question/answer screens


def _gradient(top, bottom):
    from PIL import Image
    mask = Image.linear_gradient('L').resize((W, H))
    return Image.composite(Image.new('RGB', (W, H), bottom), Image.new('RGB', (W, H), top), mask)


@lru_cache(maxsize=None)
def background(kind):
    """The full-frame background of a screen; text and cards stay inside the safe area on top of it."""
    from PIL import Image, ImageDraw
    img = _gradient(*((BRAND_TOP, BRAND_BOTTOM) if kind == 'brand' else (SOFT_TOP, SOFT_BOTTOM)))
    d = ImageDraw.Draw(img)
    light = (255, 255, 255) if kind == 'brand' else (0, 91, 191)
    for cx, cy, r, a in ((W - 60, 180, 260, 18), (80, H - 260, 300, 14), (W - 140, H - 520, 120, 10)):   # soft discs
        layer = img.copy()
        ImageDraw.Draw(layer).ellipse((cx - r, cy - r, cx + r, cy + r), fill=light)
        img = Image.blend(img, layer, a / 100)
    return img


def _canvas(kind='soft'):
    from PIL import ImageDraw
    img = background(kind).copy()
    return img, ImageDraw.Draw(img)


def _shadow_card(img, box, radius, fill, outline=None, width=0, blur=22, offset=10, alpha=55):
    """Rounded card with a soft drop shadow (drawn on the frame, so the frame stays RGB)."""
    from PIL import Image, ImageDraw, ImageFilter
    x0, y0, x1, y1 = box = tuple(int(v) for v in box)
    pad = blur * 3
    sh = Image.new('L', (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), 0)
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad, pad + x1 - x0, pad + y1 - y0), radius=radius, fill=alpha)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    img.paste(Image.new('RGB', sh.size, '#1A2A55'), (x0 - pad, y0 - pad + offset), sh)
    ImageDraw.Draw(img).rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _chip(d, x, y, text, size=40, bg=None, fg=None):
    w = width(text, size, True) + 64
    d.rounded_rectangle((x, y, x + w, y + line_h(size) + 20), radius=999, fill=bg or C['primary_c'])
    draw_line(d, x + 32, y + 10, text, size, fg or C['on_primary_c'], True)
    return y + line_h(size) + 20


def _brand(d, on_brand=False):
    """'Study Station' pill at the top of every screen."""
    size, x, y = 40, LEFT, TOP - 120
    w = width('Study Station', size, True) + 64
    d.rounded_rectangle((x, y, x + w, y + line_h(size) + 16), radius=999,
                        fill=(255, 255, 255) if on_brand else C['primary'])
    draw_line(d, x + 32, y + 8, 'Study Station', size, C['primary'] if on_brand else C['on_primary'], True)


def _check(d, cx, cy, r, color):
    d.line([(cx - r * .5, cy), (cx - r * .1, cy + r * .4), (cx + r * .55, cy - r * .45)], fill=color, width=max(6, r // 4),
           joint='curve')


def _arrow_up(d, cx, top, size, color):
    d.polygon([(cx, top), (cx - size, top + size), (cx + size, top + size)], fill=color)
    d.rounded_rectangle((cx - size // 3, top + size - 2, cx + size // 3, top + size * 2), radius=size // 6, fill=color)


def layout(q):
    """Measure everything once; DoesNotFit if the question cannot be shown readably."""
    inner = RIGHT - LEFT - 2 * 48
    opt = []
    for i, o in enumerate(q['options']):
        s, lines = fit(o, inner - 120, 2 * line_h(48), range(60, 39, -4))
        opt.append((s, lines))
    osize = min(s for s, _ in opt)
    opt = [wrap(o, osize, inner - 120) for o in q['options']]
    sol = re.sub(r'^उत्तर:\s*[^।]*।\s*', '', q['explanation']).strip()
    ssize, slines = fit(sol, inner, 480, range(52, 33, -4)) if sol else (40, [])
    qsmall = fit(q['question'], inner, 320, range(56, 31, -4), True)
    fit(f"A.  {q['options'][q['answer']]}", RIGHT - LEFT - 160, 3 * line_h(60), range(64, 39, -4), True)
    opt_h = sum(max(1, len(l)) * line_h(osize) + 64 for l in opt) + 3 * 28
    room = BOTTOM - TOP - 120 - 96 - 48 - opt_h            # what is left for the question text
    qs, qlines = fit(q['question'], inner, min(560, room), range(84, 43, -4), True)
    total = 120 + len(qlines) * line_h(qs) + 96 + 48 + opt_h
    return {'top': TOP + (BOTTOM - TOP - total) // 3, 'qs': qs, 'qlines': qlines, 'osize': osize, 'opt': opt,
            'ssize': ssize, 'slines': slines, 'qsmall': qsmall}


def frame_question(q, L, show=None):
    """Question card + four options. show = answer index to highlight."""
    img, d = _canvas()
    _brand(d)
    y = _chip(d, LEFT, L['top'], f"{pick.SUBJECT_HI.get(q['subject'], '')} · {pick.LEVEL_HI.get(q['level'], '')}",
              bg=C['primary'], fg=C['on_primary'])
    y += 40
    qh = len(L['qlines']) * line_h(L['qs']) + 96
    _shadow_card(img, (LEFT, y, RIGHT, y + qh), 44, '#FFFFFF')
    d.rounded_rectangle((LEFT, y + 30, LEFT + 12, y + qh - 30), radius=6, fill=C['primary'])    # accent bar
    draw_block(d, LEFT + 52, y + 48, L['qlines'], L['qs'], C['text'], True)
    y += qh + 44
    for i, lines in enumerate(L['opt']):
        h = max(1, len(lines)) * line_h(L['osize']) + 64
        right = show is not None and i == q['answer']
        dim = show is not None and not right
        if dim:
            d.rounded_rectangle((LEFT, y, RIGHT, y + h), radius=36, fill='#EEF0F6')
        else:
            _shadow_card(img, (LEFT, y, RIGHT, y + h), 36, C['success_c'] if right else '#FFFFFF',
                         outline=C['success'] if right else None, width=5 if right else 0, blur=14, offset=6, alpha=40)
        cx, cy = LEFT + 66, y + h // 2
        d.ellipse((cx - 38, cy - 38, cx + 38, cy + 38),
                  fill=C['success'] if right else '#B8BCC8' if dim else LETTER_COLORS[i])
        if right:
            _check(d, cx, cy, 30, C['on_primary'])
        else:
            draw_line(d, cx - width('ABCD'[i], 42, True) / 2, cy - line_h(42) // 2, 'ABCD'[i], 42, '#FFFFFF', True)
        draw_block(d, LEFT + 130, y + 32, lines, L['osize'],
                   C['on_success_c'] if right else '#7A7E8A' if dim else C['text'], True)
        y += h + 28
    return img


def frame_countdown(base, left, frac):
    """The question frame with the countdown ring on top (base is drawn once, the ring per frame)."""
    img = base.copy()
    _ring(img, RIGHT - 160, TOP - 140, 160, left, frac)
    return img


def _ring(img, x, y, size, left, frac):
    from PIL import Image, ImageDraw
    k = 4
    ring = Image.new('RGBA', (size * k, size * k), (0, 0, 0, 0))
    r = ImageDraw.Draw(ring)
    r.ellipse((0, 0, size * k - 1, size * k - 1), fill='#E8590C')
    r.arc((10 * k, 10 * k, (size - 10) * k, (size - 10) * k), -90, -90 + 360 * frac, fill='#FFFFFF', width=10 * k)
    ring = ring.resize((size, size), Image.LANCZOS)
    img.paste(ring, (x, y), ring)
    d = ImageDraw.Draw(img)
    s = 68
    draw_line(d, x + (size - width(str(left), s, True)) / 2, y + (size - line_h(s)) / 2, str(left), s, '#FFFFFF', True)


def frame_answer(q, L):
    img, d = _canvas()
    _brand(d)
    s, qlines = L['qsmall']
    ans = f"{'ABCD'[q['answer']]}.  {q['options'][q['answer']]}"
    asz, alines = fit(ans, RIGHT - LEFT - 160, 3 * line_h(60), range(64, 39, -4), True)
    ah = len(alines) * line_h(asz) + 64
    sh = len(L['slines']) * line_h(L['ssize']) + 140 if L['slines'] else 0
    total = 120 + len(qlines) * line_h(s) + 32 + ah + 40 + sh
    y = _chip(d, LEFT, TOP + max(0, (BOTTOM - TOP - total) // 3), 'सही उत्तर', bg=C['success'], fg=C['on_primary']) + 48
    y = draw_block(d, LEFT, y, qlines, s, C['muted'], True) + 32
    _shadow_card(img, (LEFT, y, RIGHT, y + ah), 44, C['success_c'], outline=C['success'], width=5)
    d.ellipse((LEFT + 34, y + ah // 2 - 36, LEFT + 106, y + ah // 2 + 36), fill=C['success'])
    _check(d, LEFT + 70, y + ah // 2, 30, '#FFFFFF')
    draw_block(d, LEFT + 136, y + 32, alines, asz, C['on_success_c'], True)
    y += ah + 40
    if sh:
        _shadow_card(img, (LEFT, y, RIGHT, y + sh), 44, '#FFFFFF')
        draw_line(d, LEFT + 48, y + 28, 'हल', 40, C['primary'], True)
        draw_block(d, LEFT + 48, y + 28 + line_h(40) + 16, L['slines'], L['ssize'], C['text'])
    return img


def frame_text(title, sub, footer='', link='', bio=False):
    """Hook and end screens: white text on the brand gradient; optional link pill and 'link in bio'."""
    img, d = _canvas('brand')
    _brand(d, on_brand=True)
    inner = RIGHT - LEFT
    ts, tl = fit(title, inner, 600, range(104, 47, -4), True)
    ss, sl = fit(sub, inner, 400, range(56, 31, -4)) if sub else (40, [])
    total = len(tl) * line_h(ts) + 60 + len(sl) * line_h(ss)
    y = (TOP + BOTTOM - total) // 2 - (120 if link else 0)
    y = draw_block(d, LEFT, y, tl, ts, '#FFFFFF', True, inner) + 60
    y = draw_block(d, LEFT, y, sl, ss, '#DCE7FF', False, inner)
    if link:
        size = fit(link, inner - 96, line_h(52), range(52, 31, -2), True)[0]
        w = width(link, size, True) + 96
        x0, y0 = LEFT + (inner - w) // 2, y + 70
        _shadow_card(img, (x0, y0, x0 + w, y0 + line_h(size) + 40), 999, '#FFFFFF', blur=16, alpha=70)
        draw_line(d, x0 + 48, y0 + 20, link, size, C['primary'], True)
        y = y0 + line_h(size) + 40
        if bio:
            _arrow_up(d, W // 2, y + 44, 26, '#FFD54F')
            fs, fl = fit('लिंक Bio में है', inner, line_h(56), range(56, 35, -4), True)
            y = draw_block(d, LEFT, y + 110, fl, fs, '#FFD54F', True, inner)
    if footer:
        fs, fl = fit(footer, inner, 200, range(48, 31, -4), True)
        draw_block(d, LEFT, BOTTOM - len(fl) * line_h(fs), fl, fs, '#DCE7FF', True, inner)
    return img


def channel_link():
    return os.environ.get('PROMO_TELEGRAM', '').strip() or os.environ.get('PROMO_LINK', '').strip()


def frames(q):
    """[(image, seconds)] for one video."""
    L = layout(q)
    link = channel_link()
    out = [(frame_text('आज का सवाल', f"{pick.SUBJECT_HI.get(q['subject'], '')} · SSC · Railway · Bank की तैयारी",
                       'अंत तक देखें — उत्तर और हल वीडियो में'), 2.0)]
    base = frame_question(q, L)
    out.append((base, 7.0))
    for i in range(int(5 * COUNTDOWN_FPS)):
        out.append((frame_countdown(base, 5 - i // COUNTDOWN_FPS, 1 - (i % COUNTDOWN_FPS) / COUNTDOWN_FPS),
                    1 / COUNTDOWN_FPS))
    out.append((frame_answer(q, L), 6.0))
    out.append((frame_text('रोज़ ऐसे 10 सवाल', 'मुफ़्त · हिंदी में · हल के साथ',
                           '' if link else 'फ़ॉलो करें — Study Station',
                           link=f"Telegram: {re.sub(r'^https?://', '', link)}" if link else '', bio=bool(link)), 4.0))
    return out


# ------------------------------------------------------------------------------------------------ video
def scene_start(name):
    t = 0.0
    for n, secs in SCENES:
        if n == name:
            return t
        t += secs
    raise KeyError(name)


def sound_expr():
    """The soundtrack, synthesised by ffmpeg (no music file, so nothing to license): a soft chime when the video
    opens, a short tick on each second of the countdown and a two-note 'ding' when the answer appears."""
    def tone(t0, freq, dur, decay, vol):
        return (f'{vol}*between(t,{t0:.2f},{t0 + dur:.2f})*sin(2*PI*{freq}*(t-{t0:.2f}))'
                f'*exp(-(t-{t0:.2f})*{decay})')
    cd, ans = scene_start('countdown'), scene_start('answer')
    parts = [tone(0.15, 660, 0.6, 6, 0.25), tone(0.15, 990, 0.6, 7, 0.12)]
    parts += [tone(cd + i, 1200, 0.08, 45, 0.35) for i in range(int(scene_start('answer') - cd))]
    parts += [tone(ans, 880, 1.6, 3, 0.35), tone(ans + 0.12, 1320, 1.4, 3.5, 0.25)]
    return '+'.join(parts)


def ffmpeg_cmd(listfile, out):
    return ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(listfile),
            '-f', 'lavfi', '-i', f"aevalsrc='{sound_expr()}':s=44100:d={sum(secs for _, secs in SCENES)}",
            '-ac', '2', '-shortest',
            '-vf', 'fps=30,format=yuv420p', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22',
            '-c:a', 'aac', '-b:a', '64k', '-t', str(sum(secs for _, secs in SCENES)),
            '-movflags', '+faststart', str(out)]


def render(q, out_mp4, workdir):
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    lines = []
    for i, (img, secs) in enumerate(frames(q)):
        p = workdir / f'f{i:03d}.png'
        img.save(p, compress_level=1)
        lines.append(f"file '{p.resolve()}'\nduration {secs:.3f}")
    lines.append(f"file '{(workdir / f'f{i:03d}.png').resolve()}'")       # concat needs the last file twice
    listfile = workdir / 'list.txt'
    listfile.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    try:
        subprocess.run(ffmpeg_cmd(listfile, out_mp4), check=True)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def caption(q):
    subj = pick.SUBJECT_HI.get(q['subject'], q['subject'])
    head = q['question'].split('\n')[0]
    title = f'{subj} क्विज़: {head}'
    title = title if len(title) <= 80 else title[:79].rstrip() + '…'
    link = channel_link()
    body = [q['question'], ''] + [f"{'ABCD'[i]}. {o}" for i, o in enumerate(q['options'])] + [
        '', 'उत्तर वीडियो के अंत में 👆 — कमेंट में अपना उत्तर लिखें!', '', q['explanation'], '']
    if link:
        body.append(f'रोज़ 10 मुफ़्त सवाल: {link}')
    body.append(' '.join([HASHTAG.get(q['subject'], '#GK'), '#SSC', '#RailwayExam', '#Shorts', '#StudyStation']))
    return f"{title} #Shorts\n\n" + '\n'.join(body) + '\n'


def short_ok(q):
    """Short enough for a phone screen; no current affairs (a video stays up long after the news is old)."""
    return 'Current_Affairs' not in q['chapter'] and len(q['question']) <= MAX_Q and all(len(o) <= MAX_OPT for o in q['options'])


def pick_shorts(day: date, count, posted, level=None):
    """Questions for today's videos: rotating subjects, easy/medium, short, drawable."""
    rng = random.Random(f'{day.isoformat()}|shorts')
    posted, out = set(posted), []
    tries = 0
    i = 0
    while len(out) < count and tries < count * 15:
        tries += 1
        subject = pick.SUBJECTS[(day.toordinal() + i) % len(pick.SUBJECTS)]
        lvl = LEVEL_ARG.get(level) if level else pick.day_level(day, rng)
        q = pick._pick_one(lvl, subject, rng, posted, set(), ('easy', 'medium'), short_ok)
        if q is None:
            i += 1
            continue
        posted.add(q['id'])
        try:
            layout(q)
        except DoesNotFit:
            continue
        out.append(q)
        i += 1
    return out


def telegram_caption(q):
    """Channel caption: no answer in the text — the video reveals it."""
    import html
    subj = html.escape(pick.SUBJECT_HI.get(q['subject'], q['subject']))
    link = channel_link()
    return (f'<b>🎬 {subj} क्विज़</b> — उत्तर वीडियो के अंत में! अपना उत्तर पहले सोचें 🤔'
            + (f'\n\n📚 रोज़ 10 मुफ़्त सवाल · {html.escape(link)}' if link else ''))
