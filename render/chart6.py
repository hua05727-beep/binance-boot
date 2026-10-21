# BTC/USDT candlestick frenzy layer for v2
import numpy as np, cv2, math
from PIL import Image, ImageFont, ImageDraw
import render as v1
from render import c01, ss, eo3, eo4, eios, W, H

import json as _json
_BJ = _json.load(open('/workspace/binance-boot/beats5.json'))
BEATS = _BJ['beats']
B = _BJ['period']
T_DROP = BEATS[13]
T_DIS = BEATS[42]
DC = B / 4
FPS = 30
MONO = '/usr/share/fonts/truetype/sand-box/google/IBM Plex Mono/IBMPlexMono-SemiBold.ttf'
MONO_M = '/usr/share/fonts/truetype/sand-box/google/IBM Plex Mono/IBMPlexMono-Medium.ttf'
GREEN = np.array([14, 203, 129], np.float32)
RED = np.array([246, 70, 93], np.float32)
GOLDC = np.array([240, 185, 11], np.float32)
PINK = np.array([222, 92, 178], np.float32)
SP = 19.0; BW = 11.0
XR = 1715.0
YT, YB = 200.0, 812.0
VT, VB = 850.0, 975.0
NV = 96
K0 = -110
T1 = T_DIS - 0.55

def tau(t):
    if t <= T1: return t
    u = min(t - T1, 0.55)
    return T1 + u - u * u / (2 * 0.55)

BIG = {}
def gen():
    rng = np.random.default_rng(906)
    ks = np.arange(K0, 150)
    O = np.zeros(len(ks)); C = np.zeros(len(ks)); Hh = np.zeros(len(ks)); L = np.zeros(len(ks)); V = np.zeros(len(ks))
    fixed = {0: .06, 4: .05, 6: -.015, 8: .09, 9: .08, 10: .07, 11: -.02, 12: .03, 14: -.02, 16: .04, 18: -.015, 20: .03, 22: -.02,
             24: -.13, 25: -.09, 26: -.06, 27: .02, 28: -.07, 29: -.03, 30: .025, 32: -.05, 33: -.02, 36: -.04, 38: .02, 40: -.03,
             68: .10, 69: .08, 70: .06, 71: -.02, 72: .05, 74: -.02, 76: .03, 78: -.01,
             80: -.11, 81: -.07, 82: .02, 84: -.06, 86: .015, 88: .10, 89: .07, 90: -.015,
             100: .04, 104: .11, 105: .08, 106: .05, 108: -.03, 112: .04}
    p = 1.0
    for i, k in enumerate(ks):
        beat = (k % 4 == 0); down = (k >= 0 and (k - 8) % 16 == 0)
        if k < 0: x = rng.normal(0.0003, 0.0015)
        elif k in fixed: x = fixed[k] * rng.uniform(0.95, 1.05)
        elif k < 24: x = rng.normal(0.003, 0.006)
        elif k < 44: x = rng.normal(-0.004, 0.006)
        elif k < 56: x = (rng.choice([-1, 1]) * rng.uniform(0.025, 0.04)) if beat else rng.normal(0, 0.008)
        elif k < 68: x = (0.025 * rng.uniform(0.8, 1.2)) if beat else rng.normal(0.003, 0.006)
        elif k < 80: x = rng.normal(0.004, 0.006)
        elif k < 88: x = rng.normal(-0.005, 0.006)
        elif k < 92: x = rng.normal(0.005, 0.006)
        else: x = (0.03 * rng.uniform(0.8, 1.2)) if beat else rng.normal(0.003, 0.006)
        o = p; c = p * math.exp(x)
        wk = abs(rng.normal(0, 0.002 + 0.30 * abs(x))); wl = abs(rng.normal(0, 0.002 + 0.30 * abs(x)))
        if 44 <= k < 56 and beat: wk += 0.03; wl += 0.03
        if k in (24, 80): wl += 0.05
        if k in (68, 88, 104): wk += 0.03
        O[i] = o; C[i] = c; Hh[i] = max(o, c) * math.exp(wk); L[i] = min(o, c) * math.exp(-wl)
        V[i] = 0.25 + 30 * abs(x) + rng.exponential(0.25) + (0.6 if down else 0) + (6.0 * abs(x) / 0.1 if abs(x) >= 0.045 else 0)
        if k >= 0 and abs(x) >= 0.045: BIG[int(k)] = x
        p = c
    sc = 64250.0 / C[ks == -1][0]
    return dict(ks=ks, O=O * sc, C=C * sc, H=Hh * sc, L=L * sc, V=V)

D = gen()
REF = 64250.0

def kidx(k): return int(k - K0)

def candle_at(k, kf):
    """values of candle k at chart position kf (forming if k == floor(kf))."""
    i = kidx(k)
    o, c, h, l, v = D['O'][i], D['C'][i], D['H'][i], D['L'][i], D['V'][i]
    kc = math.floor(kf)
    if k < kc: return o, c, h, l, v
    p = kf - kc
    e = eo3(min(1.0, p * 1.35))
    wig = math.sin(p * 37.0 + k) * 0.25 * abs(c - o) * (1 - p)
    cur = o + (c - o) * e + wig
    rv = ss(0.05, 0.85, p)
    hi = max(o, cur) + (h - max(o, c)) * rv
    lo = min(o, cur) - (min(o, c) - l) * rv
    return o, cur, max(hi, o, cur), min(lo, o, cur), v * (0.15 + 0.85 * e)

def visible(kf):
    kc = math.floor(kf)
    ks = list(range(kc - NV, kc + 1))
    return ks, [candle_at(k, kf) for k in ks]

# viewport per frame (precomputed, smooth)
NFMAX = 1100
VP = np.zeros((NFMAX, 3))
def _vp():
    lo = hi = vm = None
    for f in range(NFMAX):
        t = f / FPS
        kf = (tau(t) - T_DROP) / DC
        ks, cs = visible(kf)
        tl = min(c[3] for c in cs); th = max(c[2] for c in cs); tv = max(c[4] for c in cs)
        if lo is None or t < T_DROP - 0.5:
            lo, hi, vm = tl, th, tv
        else:
            dt = 1 / FPS
            a_slow = 1 - math.exp(-dt * 5.0); a_fast = 1 - math.exp(-dt * 16.0)
            lo += (tl - lo) * (a_fast if tl < lo else a_slow)
            hi += (th - hi) * (a_fast if th > hi else a_slow)
            vm += (tv - vm) * (a_fast if tv > vm else a_slow * 0.5)
        VP[f] = (lo, hi, vm)
_vp()

def nice_step(span):
    for s in [50, 100, 200, 250, 500, 1000, 2000, 2500, 5000]:
        if span / s <= 7: return s
    return 10000

_fcache = {}
def F(path, size):
    k = (path, size)
    if k not in _fcache: _fcache[k] = ImageFont.truetype(path, size)
    return _fcache[k]
def FS(size, w):
    k = ('plex', size, w)
    if k not in _fcache: _fcache[k] = v1.font(size, w)
    return _fcache[k]

# rolling digit sprites
DIG_SIZE = 66
def _digits():
    f = F(MONO, DIG_SIZE)
    cw = int(round(f.getlength('0'))); ch = int(DIG_SIZE * 1.6)
    spr = {}
    for s in '0123456789,.':
        im = Image.new('L', (cw, ch), 0)
        ImageDraw.Draw(im).text((cw / 2, ch / 2), s, font=f, fill=255, anchor='mm')
        spr[s] = np.asarray(im, np.float32) / 255
    return spr, cw, ch
DSPR, DCW, DCH = _digits()
_yy = np.linspace(0, 1, DCH)
ROLLWIN = np.clip(np.minimum(_yy, 1 - _yy) / 0.2, 0, 1).astype(np.float32)[:, None]

def fmt(p): return f"{p:,.2f}"

def draw_rolling(canvas_f, x, y, price, col):
    """odometer-style price: a digit rolls only while every lower digit is rolling 9->0"""
    s = fmt(price)
    n_int = len(s.split('.')[0].replace(',', ''))
    places = []
    pl = n_int - 1
    for chs in s:
        if chs in ',.': places.append(None)
        else: places.append(pl); pl -= 1
    # roll offsets from lowest place upward
    offs = {}
    o_prev = None
    for p_ in range(-2, n_int):
        u = price / (10 ** p_)
        d = int(math.floor(u)) % 10
        if p_ < 0: o = 0.0
        elif p_ == 0: o = ss(0.86, 1.0, u - math.floor(u))
        else:
            dl = int(math.floor(price / (10 ** (p_ - 1)))) % 10
            o = o_prev if dl == 9 else 0.0
        offs[p_] = (d, o); o_prev = o
    cx = x
    for chs, p_ in zip(s, places):
        if p_ is None:
            m = DSPR[chs]
        else:
            d, o = offs[p_]
            m = np.zeros((DCH, DCW), np.float32)
            sh = int(round(o * DCH))
            a = DSPR[str(d)]; b = DSPR[str((d + 1) % 10)]
            if sh == 0: m = a
            else:
                m[:DCH - sh] = a[sh:]
                m[DCH - sh:] = b[:sh]
                m = m * ROLLWIN
        canvas_f[y:y + DCH, cx:cx + DCW] = np.maximum(canvas_f[y:y + DCH, cx:cx + DCW], m[..., None] * col)
        cx += DCW

def rect_poly(x0, y0, x1, y1):
    return np.round(np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]) * 16).astype(np.int32)

def chart_layer(t):
    """returns float32 (H,W,3) chart image (0..1) on black, plus info dict"""
    f = int(round(t * FPS))
    tt = tau(t)
    kf = (tt - T_DROP) / DC
    lo, hi, vm = VP[min(f, NFMAX - 1)]
    span = hi - lo
    plo = lo - 0.10 * span; phi = hi + 0.10 * span
    def py(p): return YT + (phi - p) / (phi - plo) * (YB - YT)
    cv = np.zeros((H, W, 3), np.uint8)
    # grid
    step = nice_step(phi - plo)
    g0 = math.ceil(plo / step) * step
    gl = []
    gp = g0
    while gp < phi:
        y = py(gp); gl.append((gp, y))
        cv2.line(cv, (40 * 16, int(y * 16)), (int((XR + 28) * 16), int(y * 16)), (20, 20, 23), 1, cv2.LINE_AA, 4)
        gp += step
    ks, cs = visible(kf)
    xs = [XR - (kf - k) * SP + SP * 0.5 for k in ks]
    for k, x in zip(ks, xs):
        if k % 16 == 0:
            xx = x - SP / 2
            cv2.line(cv, (int(xx * 16), int((YT - 20) * 16)), (int(xx * 16), int(VB * 16)), (18, 18, 21), 1, cv2.LINE_AA, 4)
    # volume
    for (o, c, h, l, v), x in zip(cs, xs):
        col = (GREEN if c >= o else RED) * 0.42
        vh = (VB - VT) * min(1.0, v / max(vm, 1e-6))
        cv2.fillPoly(cv, [rect_poly(x - BW / 2, VB - vh, x + BW / 2, VB)], tuple(float(a) for a in col), cv2.LINE_AA, 4)
    # wicks + bodies
    for (o, c, h, l, v), x in zip(cs, xs):
        col = tuple(float(a) for a in (GREEN if c >= o else RED))
        cv2.fillPoly(cv, [rect_poly(x - 0.8, py(h), x + 0.8, py(l))], col, cv2.LINE_AA, 4)
        y0, y1 = py(max(o, c)), py(min(o, c))
        if y1 - y0 < 1.6: y1 = y0 + 1.6
        cv2.fillPoly(cv, [rect_poly(x - BW / 2, y0, x + BW / 2, y1)], col, cv2.LINE_AA, 4)
    # moving averages (need history beyond window)
    closes_all = [candle_at(k, kf)[1] for k in range(ks[0] - 25, ks[-1] + 1)]
    ca = np.array(closes_all)
    for n, colr, th in [(25, PINK, 2), (7, GOLDC, 2)]:
        ma = np.convolve(ca, np.ones(n) / n, 'valid')[-len(ks):]
        pts = np.array([[x, py(m)] for x, m in zip(xs, ma)])
        cv2.polylines(cv, [np.round(pts * 16).astype(np.int32)], False, tuple(float(a) for a in colr), th, cv2.LINE_AA, 4)
    o, cur, h, l, v = cs[-1]
    up = cur >= o
    ccol = GREEN if up else RED
    yc = py(cur)
    # dashed current price line
    x = 40.0
    while x < XR + 30:
        cv2.line(cv, (int(x * 16), int(yc * 16)), (int((x + 7) * 16), int(yc * 16)), tuple(float(a) for a in ccol * 0.7), 1, cv2.LINE_AA, 4)
        x += 13
    # price tag
    cv2.fillPoly(cv, [rect_poly(XR + 34, yc - 16, XR + 196, yc + 16)], tuple(float(a) for a in ccol), cv2.LINE_AA, 4)
    im = Image.fromarray(cv)
    d = ImageDraw.Draw(im)
    fm = F(MONO_M, 17)
    for gp, y in gl:
        if abs(y - yc) > 22 and YT - 10 < y < YB + 10:
            d.text((XR + 44, y), fmt(gp), font=fm, fill=(110, 112, 120), anchor='lm')
    d.text((XR + 115, yc), fmt(cur), font=F(MONO, 18), fill=(255, 255, 255), anchor='mm')
    # time labels
    for k, x in zip(ks, xs):
        if k % 16 == 0 and 80 < x < XR:
            secs = 21 * 3600 + 4 * 60 + (k + 200) * 1
            d.text((x - SP / 2, VB + 30), f"{secs // 3600:02d}:{secs % 3600 // 60:02d}:{secs % 60:02d}", font=fm, fill=(95, 97, 105), anchor='mm')
    # header
    d.text((60, 70), "BTC/USDT", font=FS(42, 700), fill=(240, 240, 242), anchor='lm')
    d.text((62, 112), "Perpetual", font=FS(18, 500), fill=(120, 122, 130), anchor='lm')
    pct = cur / REF - 1
    hh = max(D['H'][:kidx(math.floor(kf)) + 1][-150:]); ll = min(D['L'][:kidx(math.floor(kf)) + 1][-150:])
    vol24 = 182334.21 + kf * 913.37
    stats = [("24h High", fmt(hh)), ("24h Low", fmt(ll)), ("24h Vol(BTC)", f"{vol24:,.2f}")]
    sx = 905
    for lab, val in stats:
        d.text((sx, 58), lab, font=FS(17, 500), fill=(120, 122, 130), anchor='lm')
        d.text((sx, 86), val, font=F(MONO_M, 21), fill=(220, 220, 225), anchor='lm')
        sx += 230
    # interval chips
    for i, lab in enumerate(["1s", "15m", "1H", "4H", "1D"]):
        on = i == 0
        d.text((62 + i * 62, 160), lab, font=FS(17, 600 if on else 500), fill=(240, 185, 11) if on else (110, 112, 120), anchor='lm')
    d.text((XR - 80, 160), "MA(7)", font=FS(16, 600), fill=(240, 185, 11), anchor='lm')
    d.text((XR - 10, 160), "MA(25)", font=FS(16, 600), fill=(222, 92, 178), anchor='lm')
    out = np.asarray(im, np.float32) / 255
    out = out.copy()
    # rolling price
    pc = (ccol / 255).astype(np.float32)
    draw_rolling(out, 300, 70 - DCH // 2, round(cur, 2) + 1e-6, pc)
    # pct badge
    bx = 300 + DCW * len(fmt(cur)) + 26
    sgn = '+' if pct >= 0 else ''
    txt = f"{sgn}{pct * 100:.2f}%"
    bcol = (GREEN if pct >= 0 else RED) / 255
    beat = (t - T_DROP) / B
    flash = 0.5 + 0.5 * math.exp(-((beat - round(beat)) * B) ** 2 / 0.006) if t > T_DROP else 0.5
    bw = 150
    ov = np.zeros((44, bw, 3), np.float32)
    ov[:] = bcol * (0.55 + 0.45 * flash)
    rr = np.zeros((44, bw), np.uint8)
    cv2.rectangle(rr, (0, 0), (bw - 1, 43), 255, -1)
    im2 = Image.fromarray(np.zeros((44, bw), np.uint8)); ImageDraw.Draw(im2).text((bw / 2, 22), txt, font=F(MONO, 24), fill=255, anchor='mm')
    tm = np.asarray(im2, np.float32)[..., None] / 255
    ov = ov * (1 - tm) + tm * 1.0
    out[48:92, bx:bx + bw] = ov
    # LIVE dot
    lv = 0.5 + 0.5 * math.sin(t * 6.0)
    cv2.circle(out, (1858, 64), 6, (0.96 * lv + 0.2, 0.27 * lv, 0.36 * lv), -1, cv2.LINE_AA)
    # left fade of candles
    xr = np.arange(W, dtype=np.float32)
    fade = (0.15 + 0.85 * np.clip((xr - 30) / 320, 0, 1))[None, :, None]
    out[150:VB.__int__() + 50] *= fade
    return out, dict(cur=cur, up=up, yc=yc, kf=kf)


def price_y(t, p):
    f = int(round(t * FPS))
    lo, hi, vm = VP[min(max(f, 0), NFMAX - 1)]
    span = hi - lo; plo = lo - 0.10 * span; phi = hi + 0.10 * span
    return YT + (phi - p) / (phi - plo) * (YB - YT)

def cand_x(t, k):
    kf = (tau(t) - T_DROP) / DC
    return XR - (kf - k) * SP + SP * 0.5

# swing badges: (k_start, k_end, colour sign)
SWINGS = [(0, 23), (24, 43), (68, 79), (80, 87), (88, 115)]
def swing_pct(k0, kf):
    ref = D['C'][kidx(k0 - 1)]
    i = int(math.floor(kf)); cur = candle_at(i, kf)[1]
    return cur / ref - 1
