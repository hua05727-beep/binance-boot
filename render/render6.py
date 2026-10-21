import numpy as np, cv2, math, sys, os, json
from PIL import Image
import render as v1
from render import c01, ss, eo3, eo4, eios, eio3, v_eio, v_ss, W, H, CX, CY, QW, QH, FPS, U
import chart6 as chart3
import fx6
import render2 as r2
import text5 as text4
from scipy.interpolate import PchipInterpolator
cv2.setNumThreads(1)

BJ = json.load(open('/workspace/binance-boot/beats5.json'))
BT = BJ['beats']; B = BJ['period']
bt = text4.bt
T_DROP, T_DIS, T_LOCK = bt(13), bt(42), bt(44)
HITS = [bt(42.5), bt(43), bt(43.5)]
OFF = T_LOCK - v1.T_LOCK
DUR = 25.0; NF = int(round(DUR * FPS))
FADE = (bt(52), 25.0)
v1.A_PIECE = [HITS[0] - OFF, HITS[1] - OFF, HITS[1] - OFF, HITS[2] - OFF, HITS[2] - OFF]
v1.T_TEXT = 9.1
# post-lock time warp (video t -> v1 time): lock 6.35 @ b44, wordmark 9.1 @ b45, STARTING 11.6 @ b47, bar done 13.1 @ b49, then real-time
_KN_T = [T_LOCK, bt(45), bt(47), bt(49), bt(49) + 0.6, 26.0]
_KN_V = [6.35, 9.1, 11.6, 13.1, 13.7, 13.1 + 26.0 - bt(49)]
_PW = PchipInterpolator(_KN_T, _KN_V)
def TV(t): return t - OFF if t <= T_LOCK else float(_PW(t))
# patch render2 globals
r2.chart2 = chart3
r2.T_DROP, r2.T_DIS, r2.T_LOCK2, r2.OFF = T_DROP, T_DIS, T_LOCK, OFF
r2.LS = [1000.0, 1001.0, 1002.0, 1003.0]
r2.A2 = [HITS[0], HITS[1], HITS[1], HITS[2], HITS[2]]
P = r2.P
EVENTS = {}

def init():
    text4.init()
    orig = r2.frenzy
    def fz(t, with_text=True):
        fr, info = orig(t, with_text)
        b = text4.backing(t)
        if b is not None: fr *= (1 - b[..., None])
        text4.draw(fr, t, 0.0)
        return fr, info
    r2.frenzy = fz          # dissolve particles get sampled from chart + line 5
    r2.init()
    r2.frenzy = orig
    # compress the dissolve: release over ~0.35 s, fast implosion into the 3 assembly hits
    rng = np.random.default_rng(5)
    nrel = (P['rel'] - (T_DIS + 0.05)) / 0.95
    P['rel'] = (T_DIS + 0.02 + nrel * 0.33).astype(np.float32)
    dp = P['dp']
    dp['rel'] = T_DIS + 0.02 + (dp['rel'] - (T_DIS + 0.05)) / 0.95 * 0.33
    s0 = 360 / (24 * U)
    pk1 = (dp['tx'] - CX) / s0 + v1.MC; pk0 = (dp['ty'] - CY) / s0 + v1.MC
    pid_map = np.argmax(np.stack(v1.P['logo']['pm']), 0)
    pid = pid_map[pk0.astype(int).clip(0, v1.MS - 1), pk1.astype(int).clip(0, v1.MS - 1)]
    ta = np.array(r2.A2)[pid] + rng.normal(-0.03, 0.05, len(pid)).clip(-0.12, 0.1)
    ts = np.maximum(np.minimum(dp['rel'] + rng.uniform(0.02, 0.10, len(pid)), ta - 0.28), dp['rel'])
    dp['ta'] = ta; dp['ts'] = ts; dp['D'] = np.maximum(ta - ts, 0.12)
    dp['vx'] *= 0.5; dp['vy'] *= 0.5
    L = np.load('/workspace/binance-boot/poster_layers.npz')
    P['bgp'] = L['bg'].astype(np.float32)
    els = {}
    for key in L.files:
        if '__' in key:
            n, kk = key.split('__')
            els.setdefault(n, {})[kk] = L[key].astype(np.float32) if kk not in ('box', 'anchor') else L[key]
    P['el'] = els
    fx6.split_head2(els)
    fx6.init_fx()
    # shakes: poster slams + K-line beat candles + downbeat zoom punches
    sh = [(bt(0), 9, 0.02), (bt(2), 16, 0.035), (bt(3), 16, 0.035), (bt(4), 8, 0.015), (T_DROP, 18, 0.0)]
    for k in range(1, 116):
        i = chart3.kidx(k)
        r = abs(math.log(chart3.D['C'][i] / chart3.D['O'][i]))
        te = T_DROP + k * chart3.DC
        if k in chart3.BIG: sh.append((te, min(34, 10 + 230 * r), 0.0))
        elif k % 4 == 0: sh.append((te, min(10, 3 + r * 300), 0.03 if (k - 8) % 16 == 0 else 0.008))
    sh += [(bt(19), 22, 0.02), (bt(21), 9, 0.0), (bt(23), 9, 0.0), (text4.SHATTER, 7, 0.0), (bt(30), 8, 0.035),
           (bt(33), 20, 0.02), (bt(35), 8, 0.03), (bt(36), 6, 0.02)] + [(h, 6, 0.01) for h in HITS]
    P['shakes'] = sh
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    P['flashm'] = (0.25 + 0.75 * np.exp(-(((xx - CX) / 1000) ** 2 + ((yy - CY) / 650) ** 2)))[..., None].astype(np.float32)

def pulse(t):
    """beat-synced pulse, stronger on downbeats"""
    if t < 0: return 0.0
    i = int(math.floor((t - BT[0]) / B + 1e-6))
    i = max(0, min(i, len(BT) - 1))
    while i > 0 and BT[i] > t: i -= 1
    dt = t - BT[i]
    return math.exp(-dt / 0.11) * (1.0 if i % 4 == 0 else 0.55)

def eoexpo(x):
    x = c01(x); return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)

def draw_el(img, name, s=1.0, al=1.0, dx=0.0, dy=0.0, wipe=None, gmul=1.0, add=None):
    if al <= 0.003: return img
    e = P['el'][name]
    x0, y0, x1, y1 = [int(v) for v in e['box']]
    ax, ay = e['anchor']
    tx = s * (x0 - ax) + ax + dx; ty = s * (y0 - ay) + ay + dy
    w, h = x1 - x0, y1 - y0
    X0 = max(int(math.floor(tx)) - 1, 0); Y0 = max(int(math.floor(ty)) - 1, 0)
    X1 = min(int(math.ceil(tx + w * s)) + 2, W); Y1 = min(int(math.ceil(ty + h * s)) + 2, H)
    if X1 <= X0 or Y1 <= Y0: return img
    M = np.array([[s, 0, tx - X0], [0, s, ty - Y0]], np.float32)
    def wp(a): return cv2.warpAffine(a, M, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR)
    m = al
    if wipe is not None:
        xs = np.arange(X0, X1, dtype=np.float32)
        m = al * wipe(xs)[None, :]
    roi = img[Y0:Y1, X0:X1]
    if 'Sh' in e:
        sh = wp(e['Sh']) * m; roi *= (1 - sh[..., None])
    if 'G' in e:
        roi += wp(e['G']) * (np.asarray(m)[..., None] if np.ndim(m) else m) * gmul
    if 'A' in e:
        A = wp(e['A']) * m; C = wp(e['C']) * (np.asarray(m)[..., None] if np.ndim(m) else m)
        if add is not None and 'F' in e:
            F = wp(e['F']) * m
            C = C + add(X0, Y0, X1, Y1)[..., None] * F[..., None] * np.array([1, 0.97, 0.88], np.float32)
        roi[:] = roi * (1 - A[..., None]) + C
    img[Y0:Y1, X0:X1] = roi
    return img

def poster_frame(t):
    p = pulse(t)
    img = P['bgp'] * (0.85 + 0.15 * ss(bt(0) - 0.02, bt(0) + 0.1, t)) * (1 + 0.10 * p)
    def punch(i, amt, dur=0.22):
        u = (t - bt(i)) / dur
        return (1 + amt * (1 - eoexpo(u))), ss(0, 0.06, t - bt(i))
    s, a = punch(0, 0.35, 0.28)
    if t < bt(0): s, a = 1.35 + 0.08 * (bt(0) - t) / bt(0), 0.45 + 0.4 * t / bt(0)   # visible from frame 1, slams on beat 0
    img = draw_el(img, 'logo', s, max(a, 0.85) if t >= bt(0) else a, gmul=1 + 0.9 * p)
    s, a = punch(8, 0.12)
    img = draw_el(img, 'word', s, a)
    img = draw_el(img, 'frames', 1.0, ss(bt(8), bt(9), t), gmul=1 + 0.6 * p)
    # headline sweep (beats 12 -> 14)
    def sweep(X0, Y0, X1, Y1):
        if not (bt(8) <= t <= bt(10)): return np.zeros((Y1 - Y0, X1 - X0), np.float32)
        pos = 700 + 1250 * eios((t - bt(8)) / (bt(10) - bt(8)))
        yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
        d = (xx - pos) + (yy - 380) * 0.5
        return np.exp(-(d / 36) ** 2) * 1.0 + np.exp(-(d / 130) ** 2) * 0.2
    s, a = punch(2, 0.7, 0.20)
    img = draw_el(img, 'head1', s, a, add=sweep)
    img = fx6.draw_head2(img, t, draw_el, sweep, p)
    e = P['el']['divider']; ax = e['anchor'][0]
    wv = eo4((t - bt(3.5)) / (B * 0.9)) * 420
    img = draw_el(img, 'divider', 1.0, 1.0 if t >= bt(3.5) else 0, wipe=lambda xs: (np.abs(xs - ax) < wv).astype(np.float32))
    s, a = punch(4, 0.22, 0.2)
    img = draw_el(img, 'sub', s, a)
    pr = eo3((t - bt(4)) / B)
    eL = P['el']['ecgL']; eR = P['el']['ecgR']
    xl0 = float(eL['box'][0]); xl1 = float(eL['anchor'][0]); xr0 = float(eR['box'][2]); xr1 = float(eR['anchor'][0])
    if t >= bt(4):
        img = draw_el(img, 'ecgL', 1, 1, wipe=lambda xs: v_ss(-6, 6, xl0 + (xl1 - xl0 + 10) * pr - xs), gmul=1 + 1.2 * p)
        img = draw_el(img, 'ecgR', 1, 1, wipe=lambda xs: v_ss(-6, 6, xs - (xr0 - (xr0 - xr1 + 10) * pr)), gmul=1 + 1.2 * p)
        # pulsing dots at inner ends
        for (dxp, dyp) in [(xl1, eL['anchor'][1]), (xr1, eR['anchor'][1])]:
            X0, Y0 = int(dxp) - 30, int(dyp) - 30
            yy, xx = np.mgrid[Y0:Y0 + 60, X0:X0 + 60].astype(np.float32)
            dot = np.exp(-((xx - dxp) ** 2 + (yy - dyp) ** 2) / (12 + 40 * p)) * (0.8 + 1.2 * p) * ss(bt(4) + B * 0.8, bt(5), t)
            img[Y0:Y0 + 60, X0:X0 + 60] += dot[..., None] * np.array([1, .88, .6], np.float32)
    e3 = P['el']['third']
    t0x, t1x = float(e3['box'][0]), float(e3['box'][2])
    pw = eo3((t - bt(6)) / (1.5 * B))
    wx = t0x + (t1x - t0x + 40) * pw
    def third_shine(X0, Y0, X1, Y1):
        xx = np.arange(X0, X1, dtype=np.float32)[None, :] * np.ones((Y1 - Y0, 1), np.float32)
        return np.exp(-((xx - wx) / 30) ** 2) * 1.2 * (pw < 1)
    if t >= bt(6):
        img = draw_el(img, 'third', 1, 1, wipe=lambda xs: v_ss(-20, 0, wx - xs), add=third_shine)
    # flashes on slams
    for i, amp in [(0, 0.20), (2, 0.30), (3, 0.30), (4, 0.12), (6, 0.06), (8, 0.10)]:
        if bt(i) <= t < bt(i) + 0.5:
            img += P['flashm'] * (0.55 * amp * math.exp(-(t - bt(i)) / 0.08)) * np.array([1, .88, .6], np.float32)
    # transition build: push-in (beats 14 -> 16) with brightening
    u = c01((t - bt(11)) / (T_DROP - bt(11)))
    z = 1 + 0.30 * u ** 3
    br = 1 + 0.9 * u ** 4
    sx, sy, zs = r2.shake(t)
    s = z + zs
    M = np.array([[s, 0, CX - CX * s + sx], [0, s, CY - CY * s + sy]], np.float32)
    img = cv2.warpAffine(img * br, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    if u > 0:  # radial zoom blur feel
        k = int(1 + 10 * u ** 2)
        if k > 1:
            s2 = 1 + 0.02 * u ** 2
            M2 = np.array([[s2, 0, CX - CX * s2], [0, s2, CY - CY * s2]], np.float32)
            img = 0.6 * img + 0.4 * cv2.warpAffine(img, M2, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return img

def frame(t):
    tv = TV(t)
    c = v1.cam(tv)
    p = pulse(t)
    mf = 1 - eios((t - FADE[0]) / (FADE[1] - FADE[0]))
    q = np.zeros((QH, QW, 3), np.float32)
    small = np.zeros((H, W, 3), np.float32); big = np.zeros((H, W, 3), np.float32)
    if t < T_DROP:
        img = poster_frame(t)
        r2.render_intro(t, small, big)
        r2.render_dust(t, c, small, 0.0)
        img = fx6.head2_fx(t, small, img)
        img += cv2.GaussianBlur(small, (0, 0), 0.85) * 0.8 + cv2.GaussianBlur(big, (0, 0), 1.9) * 0.8
        lg = None; lcy = CY
    else:
        chart_vis = ss(T_DROP - 0.02, T_DROP + 0.06, t) * (1 - ss(T_DIS, T_DIS + 0.45, t))
        img = v1.P['bg'].copy()
        ch = 1 + (c - 1) * 0.45
        M = np.array([[ch, 0, CX - CX * ch], [0, ch, CY - CY * ch]], np.float32)
        hx = cv2.warpAffine(v1.P['hex'], M, (W, H), flags=cv2.INTER_LINEAR)
        wave = 0.55 + 0.45 * np.cos((v1.P['r'] - 140 * t) / 210)
        henv = (1 - 0.75 * chart_vis) * (1 - 0.65 * ss(8.5, 11, tv)) * (1 + 0.5 * p) \
            + 0.6 * math.exp(-max(tv - v1.T_LOCK, 0) / 0.8) * ss(v1.T_LOCK - .1, v1.T_LOCK, tv)
        img += (hx * wave * (0.13 * henv))[..., None] * np.array([0.95, 0.72, 0.25], np.float32)
        lc_y = CY + (v1.logo_y(tv) - CY) * c
        qx, qy = v1.P['qx'], v1.P['qy']
        dx = qx - CX; dy = qy - lc_y
        rq = np.sqrt(dx * dx + dy * dy)
        rev = ss(4.6, 6.6, tv)
        glow = (0.05 * rev * (1 + 0.6 * p) + 0.10 * math.exp(-max(tv - v1.T_LOCK, 0) / 0.9) * ss(v1.T_LOCK - .15, v1.T_LOCK, tv)) * np.exp(-(rq / (330 * c)) ** 2)
        q += glow[..., None] * np.array([1.0, 0.70, 0.18], np.float32)
        hz = np.zeros_like(rq)
        for (hx0, hy0, hr, hvx, hvy, ha) in [(700, 420, 420, 18, 6, 1.0), (1250, 640, 520, -14, -5, 0.8), (980, 300, 380, 6, 10, 0.6)]:
            hz += ha * np.exp(-((qx - hx0 - hvx * t) ** 2 + (qy - hy0 - hvy * t) ** 2) / hr ** 2)
        q += (hz * 0.028 * (1 - 0.5 * chart_vis) * (1 - 0.4 * ss(6, 9, tv)))[..., None] * np.array([1.0, 0.68, 0.20], np.float32)
        renv = 0.20 * math.exp(-max(tv - v1.T_LOCK, 0) / 0.7) * ss(v1.T_LOCK - 0.1, v1.T_LOCK + 0.05, tv) + 0.06 * ss(6.0, 7.5, tv) * (1 - 0.4 * ss(9, 11, tv)) * (1 + 0.5 * p)
        if renv > 0.001:
            th = np.arctan2(dy, dx)
            pat = np.zeros_like(rq)
            for (n, amp, ph, w) in v1.P['rays']:
                pat += amp * np.cos(n * th + ph + w * t * 6.283)
            pat = np.clip(pat / 3.0, 0, 1) ** 2.2
            q += (pat * v_ss(120, 260, rq) * np.exp(-rq / 420) * renv)[..., None] * np.array([1.0, 0.78, 0.30], np.float32)
        if v1.T_LOCK - 0.05 < tv < v1.T_LOCK + 1.6:
            u = c01((tv - v1.T_LOCK) / 1.5)
            R = 160 + 1100 * eo3(u)
            q += (np.exp(-((rq - R) / (10 + 30 * u)) ** 2) * 0.35 * (1 - u) ** 1.5)[..., None] * np.array([1.0, 0.80, 0.35], np.float32)
        # small shock rings on each assembly hit (beats 33-35)
        for hb in HITS:
            if hb <= t < hb + 0.6:
                u = (t - hb) / 0.6
                R = 120 + 500 * eo3(u)
                q += (np.exp(-((rq - R) / 14) ** 2) * 0.16 * (1 - u) ** 2)[..., None] * np.array([1.0, 0.80, 0.35], np.float32)
        benv = (1 - 0.7 * chart_vis) * (1 - 0.6 * ss(6.0, 9.0, tv))
        bok = r2.render_bokeh(t, c, benv)
        if bok is not None: img += bok
        r2.render_dust(t, c, small, chart_vis)
        r2.render_dis(t, c, small, big)
        img += cv2.GaussianBlur(small, (0, 0), 0.85) + cv2.GaussianBlur(big, (0, 0), 1.9)
        back = None
        tilt = 0.0
        if t < T_DIS + 0.6:
            fr, info = r2.frenzy(min(t, T_DIS + 1e-3) if t >= T_DIS else t, with_text=False)
            fr *= (1 + 0.10 * p)
            ttx = min(t, T_DIS + 1e-3)
            tilt, zx, cflash, edge = fx6.chart_fx(fr, ttx, info)
            back = text4.backing(ttx)
            if back is not None: back = np.minimum(back * 1.18, 0.78)
            if back is not None: fr *= (1 - back[..., None])
            text4.draw(fr, ttx, p)
            sx, sy, zs = r2.shake(t)
            zin = 0.12 * (1 - eo4((t - T_DROP) / 0.6))
            s = 1 + zs + zin
            s += zx
            fcy = CY + (min(max(info['yc'], 200), 880) - CY) * 0.35
            fcx = CX + 300
            M = cv2.getRotationMatrix2D((fcx, fcy), tilt, s).astype(np.float32)
            M[0, 2] += sx; M[1, 2] += sy
            fr = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_LINEAR)
            fr = text4.glitch_band(fr, t)
            if t >= T_DIS:
                rel = P['rel']
                keep = np.clip((rel - t) / 0.08, 0, 1)
                burn = np.exp(-((t - rel) / 0.07) ** 2)
                lum = fr.max(axis=2)
                fr = fr * keep[..., None] + (burn * np.clip(lum * 2.5, 0, 1))[..., None] * np.array([1.0, 0.78, 0.3], np.float32) * 0.8
            img = img * (1 - 0.55 * chart_vis)
            if back is not None: img *= (1 - back[..., None])
            img += fr
            tn = text4.tint(t)
            if tn is not None: img += text4.LAY['vig'] * tn
            if edge.max() > 0.003 and t < T_DIS: img += fx6.FX['edge'] * edge
            if t < T_DIS:
                for te, amp, col in cflash:
                    if te <= t < te + 0.5:
                        img += P['flashm'] * (0.6 * amp * math.exp(-(t - te) / 0.08)) * col
        # beat flashes
        for te, amp, col in [(T_DROP, 0.40, (1, .92, .75)), (bt(19), 0.30, (1, .35, .4)), (bt(21), 0.10, (1, .35, .4)), (bt(24), 0.08, (1, 1, 1)),
                             (bt(27), 0.10, (.5, 1, .7)), (bt(30), 0.30, (.5, 1, .7)), (bt(33), 0.26, (1, .35, .4)), (bt(35), 0.24, (.5, 1, .7)),
                             (bt(36), 0.14, (1, .85, .5)), (bt(39), 0.14, (.5, 1, .7)), (T_DIS, 0.16, (1, .85, .5)),
                             (HITS[0], 0.07, (1, .85, .5)), (HITS[1], 0.07, (1, .85, .5)), (HITS[2], 0.08, (1, .85, .5)), (T_LOCK, 0.10, (1, .85, .5))]:
            if te <= t < te + 0.6:
                img += P['flashm'] * (0.7 * amp * math.exp(-(t - te) / 0.09)) * np.array(col, np.float32)
        lg = v1.render_logo(tv, c)
        lcy = CY
        if lg is not None:
            out, Mlg, sc, lcy = lg
            img = img * (1 - out[..., 3:4]) + out[..., :3] * (1 + 0.06 * p * ss(7, 9, tv))
        txv = v1.render_text(tv, c)
        if txv is not None:
            img = img * (1 - txv[..., 3:4]) + txv[..., :3]
        gk = math.exp(-((tv - 8.45) / 0.22) ** 2) + 0.5 * math.exp(-((tv - (v1.SHIM[1] - 0.15)) / 0.2) ** 2)
        if gk > 0.01 and lg is not None:
            sc = v1.logo_h(tv) / (24 * U) * c
            gx = CX + (v1.A - 12 + 0.6) * U * sc; gy = lcy + (v1.A - 12 - 0.6) * U * sc
            x0, x1, y0, y1 = int(gx - 160), int(gx + 160), int(gy - 160), int(gy + 160)
            yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            ddx = xx - gx; ddy = yy - gy
            star = (np.exp(-(ddy / 1.4) ** 2) * np.exp(-np.abs(ddx) / 55) + np.exp(-(ddx / 1.4) ** 2) * np.exp(-np.abs(ddy) / 40)) * 0.9 \
                + np.exp(-(ddx ** 2 + ddy ** 2) / 30) * 1.2 + np.exp(-(ddx ** 2 + ddy ** 2) / 900) * 0.2
            img[y0:y1, x0:x1] += (star * gk)[..., None] * np.array([1.0, 0.93, 0.75], np.float32)
    lum = img.max(axis=2, keepdims=True)
    bsrc = img * np.clip((lum - 0.45) / 0.5, 0, 1)
    bq = cv2.resize(bsrc, (QW, QH), interpolation=cv2.INTER_AREA)
    bm = 1 + 0.35 * p
    q += (cv2.GaussianBlur(bq, (0, 0), 2.5) * 0.32 + cv2.GaussianBlur(bq, (0, 0), 9) * 0.30 + cv2.GaussianBlur(bq, (0, 0), 24) * 0.30) * bm
    img += cv2.resize(q, (W, H), interpolation=cv2.INTER_CUBIC)
    img *= mf
    img = np.where(img < 0.8, img, 0.8 + 0.2 * np.tanh((img - 0.8) / 0.2))
    img += v1.P['dither'][int(t * FPS) % 3]
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)

def render_range(args):
    i0, i1 = args
    return [frame(i / FPS).tobytes() for i in range(i0, i1)]

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'preview':
        init()
        V = os.environ.get('V', '0')
        for t in [float(x) for x in sys.argv[2:]]:
            im = Image.fromarray(frame(t))
            im.resize((960, 540), Image.LANCZOS).save(f'/workspace/binance-boot/p6s_{t:05.2f}_{V}.png')
            print('ok', t, flush=True)
    elif mode == 'video':
        import subprocess, multiprocessing as mp
        out = sys.argv[2]; audio = sys.argv[3]
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
               '-i', audio, '-map', '0:v', '-map', '1:a',
               '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
               '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
               '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out]
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        chunks = [(i, min(i + 6, NF)) for i in range(0, NF, 6)]
        nw = int(os.environ.get('NW', '4'))
        with mp.get_context('fork').Pool(nw, initializer=init) as pool:
            for k, fr in enumerate(pool.imap(render_range, chunks)):
                for b_ in fr: ff.stdin.write(b_)
                if k % 10 == 0: print('chunk', k, '/', len(chunks), flush=True)
        ff.stdin.close(); ff.wait()
        print('done')
