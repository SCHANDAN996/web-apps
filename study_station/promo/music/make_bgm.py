"""Builds bgm.m4a: an original 24-second quiz bed (no samples, nothing to license), timed to the Shorts.

0–2 s hook: pad swell · 2–9 s question: pad + bass + soft pulse · 9–14 s countdown: tension, drums thin out
· 14–22 s answer: brighter arpeggio and full beat · 22–24 s call to action: fade.
A minor, 120 bpm (one bar = 2 s): Am – F – C – G, countdown on Dm – E.

    python study_station/promo/music/make_bgm.py      (needs numpy and ffmpeg)
"""
import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 44100
SECONDS = 24
BAR = 2.0
OUT = Path(__file__).with_name('bgm.m4a')
rng = np.random.default_rng(7)
t_all = np.arange(int(SR * SECONDS)) / SR


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def tone(freq, dur, harmonics=(1, .5, .25, .12), attack=.01, release=.2, detune=0.0):
    t = np.arange(int(SR * dur)) / SR
    wave_ = sum(a * np.sin(2 * np.pi * freq * k * (1 + detune) * t) for k, a in enumerate(harmonics, 1))
    env = np.minimum(1, t / attack) * np.minimum(1, (dur - t) / release).clip(0)
    return wave_ * env


def place(track, sig, start):
    i = int(start * SR)
    j = min(len(track), i + len(sig))
    if i < len(track):
        track[i:j] += sig[:j - i]


# (root midi, chord tones) per bar
PROG = [(57, (57, 60, 64)), (53, (53, 57, 60)), (48, (55, 60, 64)), (55, (55, 59, 62)),       # 0–8 s
        (57, (57, 60, 64)), (53, (53, 57, 60)),                                                # 8–12 s
        (50, (50, 53, 57)), (52, (52, 56, 59)),                                                # 12–16 s tension
        (57, (57, 60, 64)), (53, (53, 57, 60)), (48, (55, 60, 64)), (55, (55, 59, 62))]        # 16–24 s

pad, bass, arp, drums = (np.zeros_like(t_all) for _ in range(4))
for bar, (root, chord) in enumerate(PROG):
    start = bar * BAR
    for note in chord:            # warm pad: two detuned voices per note
        for d in (-.003, .003):
            place(pad, .10 * tone(hz(note), BAR + .3, (1, .3, .1), attack=.5, release=.6, detune=d), start)
    if start >= 2:                # bass: eighth notes from the question onwards
        for k in range(4):
            place(bass, .28 * tone(hz(root - 12), .45, (1, .4, .1), attack=.005, release=.15), start + k * .5)
    if start >= 8:                # arpeggio: sixteenth notes; brighter (octave up) on the answer
        notes = [n + (12 if start >= 14 else 0) for n in chord] + [chord[0] + 12 + (12 if start >= 14 else 0)]
        for k in range(8):
            place(arp, .07 * tone(hz(notes[k % 4]), .22, (1, .2, .05), attack=.003, release=.18), start + k * .25)

beat = np.arange(0, SECONDS, .5)
for b in beat:
    if b < 2 or b >= 22:
        continue
    countdown = 9 <= b < 14
    if not countdown or b % 1 == 0:               # kick: every beat, half-time in the countdown
        t = np.arange(int(SR * .3)) / SR
        kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-t * 30)) * t) * np.exp(-t * 12)
        place(drums, .45 * kick, b)
    if not countdown and b >= 14:                 # hats on the answer
        t = np.arange(int(SR * .06)) / SR
        place(drums, .05 * rng.standard_normal(len(t)) * np.exp(-t * 60), b + .25)

mix = pad + bass + arp + drums
fade = np.ones_like(t_all)
fade[t_all < 1.5] = t_all[t_all < 1.5] / 1.5
tail = t_all > SECONDS - 2.5
fade[tail] = (SECONDS - t_all[tail]) / 2.5
mix *= fade
mix /= np.abs(mix).max() / .89
left = mix + .3 * np.roll(arp, int(.012 * SR))               # a little width
right = mix + .3 * np.roll(arp, int(.019 * SR))
stereo = np.stack([left, right], 1)
stereo /= np.abs(stereo).max() / .89

tmp = OUT.with_suffix('.wav')
with wave.open(str(tmp), 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((stereo * 32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(tmp), '-c:a', 'aac', '-b:a', '128k', str(OUT)], check=True)
tmp.unlink()
print(OUT)
