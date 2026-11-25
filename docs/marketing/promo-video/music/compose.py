"""Original music bed for the FairMind promo (63 s). No samples: every sound is synthesised here.

Run: uv run --with numpy --with scipy python compose.py   ->  bed.wav
The beat grid is anchored to the video: the beat at 3.70 s (second question line),
the downbeat at 5.80 s (logo) and 9.50 s (first product scene).
"""

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
T = 63.0
N = int(SR * T)
P = 3.7 / 6  # beat length, ~97.3 BPM
A0 = 5.8  # downbeat anchor
BAR = 4 * P
rng = np.random.default_rng(7)  # fixed seed: same file every run


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def bar_start(m):
    return A0 + m * BAR


# Dmaj9, Bm9, Gmaj9, A6sus4 - two bars each
CHORDS = [
    [50, 57, 61, 64, 66],
    [47, 54, 57, 61, 62],
    [43, 50, 54, 57, 59],
    [45, 52, 54, 59, 62],
]
ROOTS = [38, 35, 31, 33]
END_BAR = 20  # from here the piece resolves on Dmaj9 and rings out


def chord_at_bar(m):
    return 0 if m >= END_BAR or m < 0 else (m // 2) % 4


L = np.zeros(N)
R = np.zeros(N)
padL = np.zeros(N)
padR = np.zeros(N)


def add(buf, start, sig):
    i = int(start * SR)
    if i >= N:
        return
    if i < 0:
        sig, i = sig[-i:], 0
    j = min(N, i + len(sig))
    buf[i:j] += sig[: j - i]


def env_adsr(n, a, r, sustain_len):
    t = np.arange(n) / SR
    e = np.clip(t / a, 0, 1)
    rel = np.clip(1 - (t - sustain_len) / r, 0, 1)
    return e * np.where(t > sustain_len, rel, 1) ** 2


# ---------- pad: detuned additive saws, slow swell ----------
def pad_note(freq, dur, a=0.9, r=1.6):
    n = int((dur + r) * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for cents, ph in ((-7, 0.0), (0, 1.3), (7, 2.1)):
        f = freq * 2 ** (cents / 1200)
        for k in range(1, 9):
            if f * k > 6000:
                break
            out += np.sin(2 * np.pi * f * k * t + ph * k) / k ** 1.3
    return out * env_adsr(n, a, r, dur)


def pad_segment(notes, start, dur, gain):
    for idx, m in enumerate(notes):
        sig = pad_note(mtof(m), dur) * gain / len(notes)
        pan = 0.35 + 0.3 * (idx / (len(notes) - 1))
        add(padL, start, sig * (1 - pan))
        add(padR, start, sig * pan)


# intro pad on Dmaj9 from 0 until the first chord change at bar 0 (+ overlap)
pad_segment(CHORDS[0], 0.0, A0 + 2 * BAR - 0.2, 0.55)
m = 2
while bar_start(m) < T:
    c = chord_at_bar(m)
    if m >= END_BAR:
        pad_segment(CHORDS[0], bar_start(m), T - bar_start(m) - 1.0, 0.6)
        break
    pad_segment(CHORDS[c], bar_start(m) - 0.15, 2 * BAR, 0.6)
    m += 2

pad_lp = butter(2, 1700, "low", fs=SR, output="sos")
padL = sosfilt(pad_lp, padL)
padR = sosfilt(pad_lp, padR)


# ---------- felt piano plucks ----------
def pluck(freq, vel, tau=0.7):
    n = int(2.2 * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * freq * t)
         + 0.35 * np.sin(2 * np.pi * 2 * freq * t) * np.exp(-t / 0.25)
         + 0.12 * np.sin(2 * np.pi * 3 * freq * t) * np.exp(-t / 0.12))
    e = np.exp(-t / tau) * np.clip(t / 0.004, 0, 1)
    return s * e * vel


keysL = np.zeros(N)
keysR = np.zeros(N)
PATTERN = [0, 2, 4, 1, 3, 4, 2, 3]
for mm in range(0, END_BAR):
    c = chord_at_bar(mm)
    tones = [x + 12 for x in CHORDS[c]]
    step = 2 if mm < 2 else 1  # quarter notes for the logo bars, eighths after
    for s in range(0, 8, step):
        t0 = bar_start(mm) + s * P / 2
        vel = 0.16 * (1.0 if s % 4 == 0 else 0.78) * (0.9 + 0.2 * rng.random())
        sig = pluck(mtof(tones[PATTERN[s]]), vel)
        pan = 0.4 if s % 2 == 0 else 0.6
        add(keysL, t0, sig * (1 - pan))
        add(keysR, t0, sig * pan)
# final strum on the logo of the outro
for i, x in enumerate([50, 57, 61, 64, 66, 69, 74]):
    sig = pluck(mtof(x + 12), 0.15, tau=1.6)
    add(keysL, 55.94 + i * 0.045, sig * 0.5)
    add(keysR, 55.94 + i * 0.045, sig * 0.5)

# ---------- bass, kick, hats (product scenes only) ----------
bass = np.zeros(N)
kick = np.zeros(N)
hats = np.zeros(N)
duck = np.ones(N)


def drums_on(mm):
    return 2 <= mm < END_BAR and not (mm == 17)  # one bar of air before "a person decides"


def bass_note(freq, dur):
    n = int((dur + 0.15) * SR)
    t = np.arange(n) / SR
    s = np.tanh(1.6 * np.sin(2 * np.pi * freq * t)) * 0.55
    return s * env_adsr(n, 0.01, 0.15, dur) * np.exp(-t / 1.2)


def kick_hit():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 46 + 70 * np.exp(-t / 0.03)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.16)


def hat_hit():
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return rng.standard_normal(n) * np.exp(-t / 0.012)


hat_hp = butter(4, 7500, "high", fs=SR, output="sos")
for mm in range(2, END_BAR):
    c = chord_at_bar(mm)
    b = bar_start(mm)
    f = mtof(ROOTS[c])
    if mm != 17:
        add(bass, b, bass_note(f, P * 1.4))
        add(bass, b + 2.5 * P, bass_note(f, P * 1.2))
    if drums_on(mm):
        for beat in (0, 2):
            add(kick, b + beat * P, kick_hit() * 0.5)
            i = int((b + beat * P) * SR)
            dn = int(0.32 * SR)
            if i < N:
                curve = 1 - 0.28 * np.exp(-np.arange(min(dn, N - i)) / (0.09 * SR))
                duck[i:i + len(curve)] = np.minimum(duck[i:i + len(curve)], curve)
    if drums_on(mm) and mm >= 5:  # hats from the second product scene
        for s in range(8):
            if s % 2 == 1:
                add(hats, b + s * P / 2, hat_hit() * 0.025)
hats = sosfilt(hat_hp, hats)

# ---------- mix ----------
L = padL * duck + keysL + bass + kick + hats
R = padR * duck + keysR + bass + kick + hats * 0.8


# stereo reverb from decaying noise
def ir(seed):
    g = np.random.default_rng(seed)
    n = int(2.4 * SR)
    t = np.arange(n) / SR
    x = g.standard_normal(n) * np.exp(-t / 0.55)
    return sosfilt(butter(1, 5000, "low", fs=SR, output="sos"), x) / 40


send_l = padL * 0.5 + keysL
send_r = padR * 0.5 + keysR
L += 0.35 * fftconvolve(send_l, ir(1))[:N]
R += 0.35 * fftconvolve(send_r, ir(2))[:N]

hp = butter(2, 30, "high", fs=SR, output="sos")
L, R = sosfilt(hp, L), sosfilt(hp, R)

# fade the tail into silence by 63 s
t = np.arange(N) / SR
fade = np.clip((T - t) / 3.0, 0, 1)
L *= fade
R *= fade

out = np.stack([L, R], axis=1)
out = np.tanh(out / np.abs(out).max() * 1.2) * 0.89
wavfile.write("bed.wav", SR, (out * 32767).astype(np.int16))
print("wrote bed.wav", out.shape[0] / SR, "s")
