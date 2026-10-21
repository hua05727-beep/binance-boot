import numpy as np, wave, subprocess, re, sys
from scipy import signal
import json
BJ = json.load(open('beats5.json'))
BT = BJ['beats']; B = BJ['period']
def bt(x):
    i = int(np.floor(x)); f = x - i
    return (BT[i] if i < len(BT) else BT[-1] + (i - len(BT) + 1) * B) + f * B
SR = 48000; DUR = 25.0; N = int(SR * DUR)
T_DROP, T_DIS, T_LOCK = bt(13), bt(42), bt(44)
HITS = [bt(42.5), bt(43), bt(43.5)]
OFF = T_LOCK - 6.35
FADE = (bt(52), 25.0)
SRC_START = BJ['S0']
t = np.arange(N) / SR
rng = np.random.default_rng(21)
def ss(a, b, x):
    u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
L = np.zeros(N); R = np.zeros(N)
def add(i0, s, pan=0.5):
    i0 = int(i0)
    if i0 < 0: s = s[-i0:]; i0 = 0
    n = min(len(s), N - i0)
    L[i0:i0 + n] += s[:n] * np.cos(pan * np.pi / 2) * 1.414
    R[i0:i0 + n] += s[:n] * np.sin(pan * np.pi / 2) * 1.414

# ---- pad (G minor) ----
pad = np.zeros((2, N))
notes = [49.0, 98.0, 146.83, 196.0, 233.08, 293.66, 392.0]
amps = [0.30, 0.45, 0.40, 0.36, 0.26, 0.22, 0.10]
env = 0.15 * ss(0.0, 1.0, t) * (1 - 0.75 * ss(T_DROP - 0.1, T_DROP + 0.4, t)) + 0.35 * ss(T_DIS - 0.3, T_LOCK, t)
env *= 1 - ss(FADE[0], FADE[1], t)
for f, a in zip(notes, amps):
    for det, pan in [(-0.0018, 0.2), (0.0, 0.5), (0.0021, 0.8)]:
        ph = rng.uniform(0, 6.28)
        lfo = 1 + 0.25 * np.sin(2 * np.pi * rng.uniform(0.07, 0.2) * t + ph)
        ff = f * (1 + det)
        sg = (np.sin(2 * np.pi * ff * t + ph) + 0.25 * np.sin(4 * np.pi * ff * t + ph)) * a * lfo / 3
        pad[0] += sg * (1 - pan); pad[1] += sg * pan
b_, a_ = signal.butter(2, 2200 / (SR / 2))
pad = signal.lfilter(b_, a_, pad, axis=1) * env * 0.30
L += pad[0]; R += pad[1]

def bp_noise(t0, t1, f0, f1, gain, p0, p1, shp=2.0, q=1.2, cut_end=True, falling=False):
    i0, i1 = int(t0 * SR), int(t1 * SR)
    n = rng.standard_normal(i1 - i0)
    out = np.zeros_like(n); zi = None; blk = 256
    u = np.linspace(0, 1, i1 - i0)
    for i in range(0, len(n), blk):
        fc = f0 * (f1 / f0) ** (u[i] ** 1.5 if not falling else u[i] ** 0.6)
        lo, hi = fc / (1 + 1 / q), min(fc * (1 + 1 / q), SR / 2 * 0.95)
        b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], btype='band')
        if zi is None: zi = np.zeros(max(len(a), len(b)) - 1)
        out[i:i + blk], zi = signal.lfilter(b, a, n[i:i + blk], zi=zi)
    e = (u ** shp) * ((1 - ss(0.94, 1.0, u)) if cut_end else 1)
    if falling: e = (1 - u) ** 1.6 * ss(0, 0.05, u)
    out *= e * gain
    p = p0 + (p1 - p0) * u
    L[i0:i1] += out * np.cos(p * np.pi / 2) * 1.414; R[i0:i1] += out * np.sin(p * np.pi / 2) * 1.414

def impact(t0, gain=1.0, f_hi=90, f_lo=38, dec=0.7, thump=0.5):
    n = int(2.5 * SR); tt = np.arange(n) / SR
    fs = f_lo + (f_hi - f_lo) * np.exp(-tt / 0.10)
    boom = np.sin(2 * np.pi * np.cumsum(fs) / SR) * np.exp(-tt / dec) * (1 - np.exp(-tt / 0.003))
    th = signal.lfilter(*signal.butter(2, 200 / (SR / 2)), rng.standard_normal(n)) * np.exp(-tt / 0.05) * 2.5
    add(t0 * SR, (boom * 0.75 + th * thump) * gain)

def metal(t0, gain=0.3, f=2600, dec=0.25, pan=0.5):
    n = int(1.2 * SR); tt = np.arange(n) / SR
    nz = rng.standard_normal(n)
    b, a = signal.butter(2, [f * 0.6 / (SR / 2), min(f * 2.2, 20000) / (SR / 2)], btype='band')
    s = signal.lfilter(b, a, nz) * np.exp(-tt / dec) * (1 - np.exp(-tt / 0.001))
    add(t0 * SR, s * gain, pan)

def bell(t0, f0, gain, decay=2.4, pan=0.5):
    n = int(min(decay * 3, 6) * SR); tt = np.arange(n) / SR
    s = np.zeros(n)
    for ratio, a, d in [(1, 1.0, 1.0), (2.0, 0.5, 0.7), (2.76, 0.35, 0.55), (5.4, 0.18, 0.3), (8.93, 0.08, 0.2)]:
        s += a * np.sin(2 * np.pi * f0 * ratio * tt + rng.uniform(0, 6)) * np.exp(-tt / (decay * d))
    add(t0 * SR, s * (1 - np.exp(-tt / 0.003)) * gain, pan)

def tick(t0, gain=0.10, f=2400, pan=0.5):
    n = int(0.08 * SR); tt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * tt) * 0.6 + signal.lfilter(*signal.butter(2, 3000 / (SR / 2), 'high'), rng.standard_normal(n)) * 0.5) * np.exp(-tt / 0.012)
    add(t0 * SR, s * gain, pan)

def glitch_burst(t0, dur, gain=0.18):
    n = int(dur * SR)
    s = np.zeros(n); i = 0
    while i < n:
        seg = int(rng.uniform(0.008, 0.035) * SR)
        kind = rng.integers(0, 3)
        tt = np.arange(seg) / SR
        if kind == 0: x = np.sign(np.sin(2 * np.pi * rng.uniform(200, 1800) * tt))
        elif kind == 1: x = np.repeat(rng.uniform(-1, 1, seg // 40 + 1), 40)[:seg]
        else: x = rng.standard_normal(seg) * (rng.random() < 0.6)
        s[i:i + seg] = x[:n - i] * rng.uniform(0.4, 1.0)
        i += seg
    s = signal.lfilter(*signal.butter(2, [300 / (SR / 2), 9000 / (SR / 2)], btype='band'), s)
    s *= ss(0, 0.004, np.arange(n) / SR) * (1 - ss(dur - 0.01, dur, np.arange(n) / SR))
    add(t0 * SR, s * gain, rng.uniform(0.3, 0.7))


def beep(t0, f=1046.5, g=0.05, d=0.12):
    n = int(d * SR); tt = np.arange(n) / SR
    add(t0 * SR, np.sin(2 * np.pi * f * tt) * ss(0, 0.005, tt) * (1 - ss(d * 0.6, d, tt)) * g)
def beep(t0, f=1046.5, g=0.05, d=0.12):
    n = int(d * SR); tt = np.arange(n) / SR
    add(t0 * SR, np.sin(2 * np.pi * f * tt) * ss(0, 0.005, tt) * (1 - ss(d * 0.6, d, tt)) * g)
# ---- poster (beats 0-13) ----
impact(bt(0), 0.7, 80, 38, 0.6, 0.35); metal(bt(0), 0.22, 2600, 0.3); bell(bt(0) + 0.01, 392.0, 0.10, 2.0)
bp_noise(bt(2) - 0.3, bt(2) + 0.01, 600, 4000, 0.10, 0.5, 0.5, 2.0)
impact(bt(2), 1.0); metal(bt(2), 0.32, 2400, 0.3)
impact(bt(3), 1.0, 95, 36); metal(bt(3), 0.32, 2800, 0.3)
bp_noise(bt(3.5), bt(3.5) + 0.4, 4000, 11000, 0.06, 0.2, 0.8, 1.0, 3.0)
impact(bt(4), 0.45, 70, 40, 0.4, 0.3); beep(bt(4) + 0.05); beep(bt(5), g=0.04); beep(bt(6), g=0.03)
bp_noise(bt(6), bt(6) + 1.5 * B, 5000, 12000, 0.07, 0.2, 0.8, 1.0, 3.0)
bell(bt(8), 587.33, 0.07, 2.4, 0.4); bell(bt(8) + 0.02, 783.99, 0.05, 2.2, 0.6)
bp_noise(bt(8), bt(10), 5000, 12000, 0.06, 0.15, 0.85, 1.0, 3.0)
bp_noise(bt(10), T_DROP + 0.01, 250, 6500, 0.42, 0.3, 0.7, 2.6)
bp_noise(bt(11), T_DROP + 0.01, 3000, 12000, 0.18, 0.8, 0.2, 3.0, 2.0)
# ---- K-line (beats 13-42) ----
impact(T_DROP, 1.1, 110, 34, 0.9, 0.6); metal(T_DROP, 0.35, 2200, 0.4); bell(T_DROP + 0.01, 392.0, 0.10, 2.0); bell(T_DROP + 0.02, 783.99, 0.06, 2.0)
for i in range(14, 42):
    tick(bt(i), 0.05, 2600 if i % 2 else 2200, 0.5)
def crash(b, g=0.9):
    impact(bt(b), g, 100, 34, 0.8, 0.5); metal(bt(b), 0.25 * g, 1800, 0.35); glitch_burst(bt(b), 0.35, 0.18 * g)
    n = int(1.6 * SR); tt = np.arange(n) / SR
    fsw = 900 * np.exp(-tt / 0.45) + 60
    add(bt(b) * SR, np.sin(2 * np.pi * np.cumsum(fsw) / SR) * np.exp(-tt / 0.7) * 0.10 * g)
def rally(b, g=0.9):
    impact(bt(b), g, 95, 36, 0.8, 0.5); metal(bt(b), 0.22 * g, 3000, 0.4); bell(bt(b) + 0.01, 783.99, 0.08 * g, 2.4, 0.4); bell(bt(b) + 0.02, 587.33, 0.06 * g, 2.4, 0.6)
crash(19); glitch_burst(bt(21), 0.10, 0.10); glitch_burst(bt(23), 0.10, 0.10)
t_sh = bt(24) - 0.30   # 恐惧 shatter
bp_noise(t_sh, t_sh + 0.35, 9000, 3000, 0.16, 0.4, 0.6, 1.0, 1.5, falling=True)
for k in range(14):
    bell(t_sh + rng.uniform(0, 0.25), rng.uniform(2500, 6000), rng.uniform(0.006, 0.014), 0.25, rng.uniform(0.15, 0.85))
for i in range(8):   # 别人恐惧时我贪婪 per-character pops
    tick(bt(24) + i * B / 8, 0.05, 1800 * 2 ** (i / 12), 0.25 + 0.5 * i / 7)
rally(30); crash(33, 0.8); rally(35, 0.8)
bp_noise(bt(28), bt(30) + 0.01, 400, 6000, 0.10, 0.4, 0.6, 2.2)
bell(bt(36), 783.99, 0.05, 1.6, 0.4)
bp_noise(bt(36) + 0.08, bt(37.75), 5000, 12000, 0.07, 0.2, 0.8, 1.0, 3.0)
bp_noise(bt(39), bt(40.5), 5000, 12000, 0.06, 0.8, 0.2, 1.0, 3.0)
impact(bt(39), 0.5, 90, 40, 0.5, 0.3)
bp_noise(bt(40), T_DIS + 0.01, 300, 6000, 0.25, 0.3, 0.7, 2.4)
# ---- logo (beats 42-end) ----
impact(T_DIS, 0.55, 80, 40, 0.5, 0.3)
for k in range(22):
    bell(T_DIS + 0.02 + rng.uniform(0, 0.4), rng.choice([1568.0, 2349.3, 3136.0, 3729.3, 4698.6]), rng.uniform(0.008, 0.018), 0.4, rng.uniform(0.1, 0.9))
bp_noise(T_DIS, T_LOCK + 0.02, 400, 6500, 0.30, 0.2, 0.8, 2.0)
for h, f in zip(HITS, [587.33, 783.99, 1174.66]):
    impact(h, 0.35, 70, 45, 0.25, 0.25); metal(h, 0.10, 3200, 0.12); bell(h, f, 0.035, 1.0)
impact(T_LOCK, 0.95, 88, 38, 0.75, 0.4)
bell(T_LOCK + 0.01, 783.99, 0.15, 2.6, 0.45); bell(T_LOCK + 0.03, 1174.66, 0.06, 2.2, 0.6); bell(T_LOCK + 0.02, 392.0, 0.08, 3.0, 0.5)
bp_noise(T_LOCK + 0.15, bt(45), 5000, 11000, 0.08, 0.15, 0.85, 1.0, 3.0)
tw = bt(45)
bell(tw, 392.0, 0.08, 2.4); bell(tw + 0.02, 466.16, 0.05, 2.2, 0.4); bell(tw + 0.04, 587.33, 0.045, 2.2, 0.6)
bell(bt(47), 1567.98, 0.025, 0.6)
# ---- v6 additions ----
for i in range(5):   # 证明给我看！ per-character stamps (sextuplet roll into beat 3)
    tl = bt(3) - (5 - i) * B / 6
    impact(tl, 0.30, 130, 60, 0.12, 0.45); metal(tl, 0.10, 3200 + 300 * i, 0.07, 0.3 + 0.1 * i)
bp_noise(bt(3) - 0.42, bt(3) + 0.01, 1500, 9000, 0.10, 0.3, 0.7, 2.0)
import json as _j
DCK = B / 4
import importlib.util as _u
_sp = _u.spec_from_file_location('chart6', 'chart6.py'); _c6 = _u.module_from_spec(_sp); _sp.loader.exec_module(_c6)
for k, x in sorted(_c6.BIG.items()):
    te = T_DROP + k * DCK
    if k not in (24, 68, 80, 88):
        impact(te, min(0.75, 5 * abs(x)), 90 if x > 0 else 70, 34, 0.45, 0.5)
    if x > 0: bp_noise(te - 0.02, te + 0.22, 400, 5000, min(0.22, 2.0 * abs(x)), 0.4, 0.6, 1.2)
    else: bp_noise(te - 0.02, te + 0.30, 5000, 300, min(0.22, 2.0 * abs(x)), 0.6, 0.4, 1.0, 1.2, falling=True)
tl0 = T_DROP + 24 * DCK + 0.05
for j in range(3): beep(tl0 + j * 0.12, 1318.5 if j % 2 == 0 else 1760.0, 0.05, 0.09)
# ---- reverb ----
irn = int(2.4 * SR); ti = np.arange(irn) / SR
irL = signal.lfilter(*signal.butter(1, 6000 / (SR / 2)), rng.standard_normal(irn) * np.exp(-ti / 0.6))
irR = signal.lfilter(*signal.butter(1, 6000 / (SR / 2)), rng.standard_normal(irn) * np.exp(-ti / 0.6))
irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())
L = L + 0.38 * signal.fftconvolve(L, irL)[:N]; R = R + 0.38 * signal.fftconvolve(R, irR)[:N]
b, a = signal.butter(2, 28 / (SR / 2), 'high')
L = signal.lfilter(b, a, L); R = signal.lfilter(b, a, R)
fd = (1 - ss(FADE[0], FADE[1], t)) * np.clip(t / 0.003, 0, 1)
sfx = np.stack([L * fd, R * fd], 1)
sfx /= np.abs(sfx).max()
# ---- music segment ----
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{SRC_START:.3f}', '-t', f'{DUR:.3f}', '-i', 'music.mp3', '-ac', '2', '-ar', str(SR), '-f', 'f32le', 'music_seg.f32'], check=True)
mus = np.fromfile('music_seg.f32', np.float32).reshape(-1, 2).astype(np.float64)
mus = np.pad(mus, ((0, max(0, N - len(mus))), (0, 0)))[:N]
mfd = np.clip(t / 0.03, 0, 1) * (1 - ss(FADE[0], FADE[1], t))
mus *= mfd[:, None]

def write(fn, x):
    with wave.open(fn, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())
def lufs(x):
    write('_tmp.wav', x)
    o = subprocess.run(['ffmpeg', '-hide_banner', '-i', '_tmp.wav', '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1]); tp = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', o)[-1])
    return I, tp
mI, _ = lufs(mus * 0.5)
mus_g = 0.5 * 10 ** ((float(__import__('os').environ.get('MUS', '-17.6')) - mI) / 20)
mus *= mus_g
print('music LUFS ->', lufs(mus))
write('music_bg6.wav', mus)
sI, _ = lufs(sfx * 0.5)
target = float(__import__('os').environ.get('MIXT', '-19.0'))
g = 0.5 * 10 ** ((-21.0 - sI) / 20)
def limit(x, ceil_db=-1.9):
    c = 10 ** (ceil_db / 20)
    env = np.abs(x).max(axis=1)
    # lookahead peak hold + smoothing
    la = int(0.004 * SR)
    pk = np.maximum.accumulate(np.lib.stride_tricks.sliding_window_view(np.pad(env, (0, la)), la + 1).max(axis=1)[None])[0] if False else \
        np.lib.stride_tricks.sliding_window_view(np.pad(env, (0, la)), la + 1).max(axis=1)
    gr = np.minimum(1, c / np.maximum(pk, 1e-9))
    # release smoothing
    out = np.empty_like(gr); cur = 1.0; rel = np.exp(-1 / (0.08 * SR)); att = np.exp(-1 / (0.0015 * SR))
    for i in range(len(gr)):
        gi = gr[i]
        cur = att * cur + (1 - att) * gi if gi < cur else rel * cur + (1 - rel) * gi
        out[i] = cur
    return x * out[:, None]
for it in range(4):
    mix = limit(sfx * g + mus)
    I, tp = lufs(mix)
    print('iter', it, 'gain', g, 'mix I', I, 'TP', tp)
    if abs(I - target) < 0.3: break
    g *= 10 ** ((target - I) / 20)
write('sfx6_only.wav', sfx * g)
write('audio_v6.wav', mix)
print('sfx alone', lufs(sfx * g), 'final', lufs(mix))
