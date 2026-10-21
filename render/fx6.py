# v6 effects: 证明给我看！ stamp-in cascade + dramatic K-line FX
import numpy as np, cv2, math
from PIL import Image, ImageDraw, ImageFont
import render as v1
from render import c01, ss, eo3, eo4, W, H, CX, CY, v_ss
import chart6 as ch
import text5

bt = text5.bt
B = text5.B
SANS = '/workspace/binance-boot/fonts/NotoSansCJKsc-Black.otf'
MONO = ch.MONO
GREEN = np.array([14, 203, 129], np.float32) / 255
RED = np.array([246, 70, 93], np.float32) / 255
GOLD = np.array([1.0, 0.80, 0.30], np.float32)
FX = {}

# ------------------------------------------------------------------ 证明给我看！
NCH = 6
def land_t(i): return bt(3) - (NCH - 1 - i) * B / 6       # sextuplet roll that lands on downbeat 3
FLY = 0.14

def split_head2(EL):
    e = EL['head2']
    A = e['F']; h, w = A.shape
    x0, y0 = e['box'][0], e['box'][1]
    cy = e['anchor'][1] - y0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = xx + 0.10 * (yy - cy)
    bnd = [-1e9, 263.5, 408.0, 562.0, 711.5, 868.0, 1e9]
    for i in range(NCH):
        for fe, suf in [(1.5, ''), (22.0, 'g')]:
            lo = 1 - np.clip((bnd[i] - u) / fe + 0.5, 0, 1) if i > 0 else np.ones_like(u)
            hi = np.clip((bnd[i + 1] - u) / fe + 0.5, 0, 1) if i < NCH - 1 else np.ones_like(u)
            m = (lo * hi).astype(np.float32)
            if suf == '': mc = m
            else: mg = m
        cu = 0.5 * (max(bnd[i], 115) + min(bnd[i + 1], 913))
        d = {k: (e[k] * (mc if k != 'G' else mg)[..., None] if e[k].ndim == 3 else e[k] * (mc if k != 'G' else mg)) for k in ('C', 'A', 'G', 'Sh', 'F')}
        d['box'] = e['box']; d['anchor'] = np.array([x0 + cu - 0.10 * 0, e['anchor'][1]], np.float32)
        EL[f'h2c{i}'] = d
    rng = np.random.default_rng(31)
    sp = []
    for i in range(NCH):
        n = 70
        ax, ay = EL[f'h2c{i}']['anchor']
        side = -1 if i % 2 == 0 else 1          # even chars come from above, odd from below
        ang = rng.uniform(0, 2 * np.pi, n)
        spd = rng.uniform(250, 900, n)
        sp.append(dict(x=ax + rng.normal(0, 40, n), y=ay + side * -1 * rng.uniform(40, 90, n) * 0 + rng.normal(0, 35, n),
                       vx=np.cos(ang) * spd * 1.3, vy=np.sin(ang) * spd * 0.7 + side * 280, life=rng.uniform(0.22, 0.5, n),
                       z=rng.uniform(0.4, 1.0, n)))
    FX['h2sp'] = sp

def draw_head2(img, t, draw_el, sweep, p):
    """returns img; per-char stamp-in with motion blur, then the full line"""
    tl = land_t(NCH - 1)
    if t >= tl + 0.02:
        tau = t - tl
        s = 1 + 0.07 * math.exp(-tau / 0.09)
        return draw_el(img, 'head2', s, 1.0, add=sweep, gmul=1 + 2.2 * math.exp(-tau / 0.16) + 0.9 * p)
    for i in range(NCH):
        T = land_t(i)
        u0 = (t - (T - FLY)) / FLY
        if u0 <= 0: continue
        side = -1 if i % 2 == 0 else 1
        if t < T:
            K = 5
            for kk in range(K):
                tk = t - kk / K * (1 / 30)
                u = c01((tk - (T - FLY)) / FLY)
                e = u ** 2.2                      # accelerate into the hit
                dist = 300 * (1 - e)
                dy = side * dist
                dx = -0.10 * dy
                s = 1 + 0.55 * (1 - e)
                img = draw_el(img, f'h2c{i}', s, ss(0, 0.35, u) / K * 1.6 if kk else ss(0, 0.35, u) * 0.75, dx, dy, gmul=0.6)
        else:
            tau = t - T
            s = 1 + 0.10 * math.exp(-tau / 0.05) - 0.04 * math.exp(-tau / 0.03)
            img = draw_el(img, f'h2c{i}', s, 1.0, gmul=1 + 2.5 * math.exp(-tau / 0.08))
    return img

def head2_fx(t, small, img):
    """impact sparks per character + chromatic shockwave on the downbeat"""
    for i in range(NCH):
        T = land_t(i); tau = t - T
        if not (0 <= tau < 0.6): continue
        d = FX['h2sp'][i]
        K = 4
        for kk in range(K):
            tk = max(tau - kk / K * (1 / 30), 0)
            x = d['x'] + d['vx'] * tk; y = d['y'] + d['vy'] * tk + 900 * tk * tk
            a = np.clip(1 - tk / d['life'], 0, 1) ** 1.5 * d['z'] * (1.6 if i == NCH - 1 else 1.0)
            col = np.where((tk < 0.08)[..., None] if np.ndim(tk) else np.full((len(x), 1), tk < 0.08), np.array([1, .97, .9]), np.array([1, .78, .3]))
            v1.splat(small, x, y, a / K * 2.6, np.broadcast_to(col, (len(x), 3)).astype(np.float32))
    tl = land_t(NCH - 1); tau = t - tl
    if 0 <= tau < 0.55:
        ax, ay = 1340.0, 465.0
        u = tau / 0.55
        R = 80 + 900 * eo3(u)
        x0, x1 = int(max(ax - R - 60, 0)), int(min(ax + R + 60, W)); y0, y1 = int(max(ay - R - 60, 0)), int(min(ay + R + 60, H))
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        rr = np.hypot(xx - ax, (yy - ay) * 1.6)
        wdt = 6 + 26 * u; amp = 0.55 * (1 - u) ** 1.6
        for c_, off in ((0, -10 * (1 + 2 * u)), (1, 0), (2, 10 * (1 + 2 * u))):
            img[y0:y1, x0:x1, c_] += np.exp(-((rr - R - off) / wdt) ** 2) * amp * (1.0, 0.85, 0.6)[c_] * (1.3 if c_ != 1 else 1.0)
    return img

# ------------------------------------------------------------------ K-line FX
def te_of(k): return ch.T_DROP + k * ch.DC

def init_fx():
    EV = sorted(ch.BIG.items())
    FX['ev'] = EV
    rng = np.random.default_rng(64)
    FX['spray'] = {}
    FX['streak'] = {}
    for k, x in EV:
        n = int(90 + 900 * abs(x))
        sg = 1 if x > 0 else -1
        ang = -sg * np.pi / 2 + rng.normal(0, 0.75, n)
        spd = rng.uniform(300, 1400, n) * (0.6 + 4 * abs(x))
        FX['spray'][k] = dict(vx=np.cos(ang) * spd - rng.uniform(0, 300, n), vy=np.sin(ang) * spd, life=rng.uniform(0.25, 0.7, n), z=rng.uniform(0.4, 1, n),
                              ox=rng.normal(0, 6, n), oy=rng.normal(0, 10, n))
        m = 30 + int(400 * abs(x))
        FX['streak'][k] = dict(x=rng.uniform(ch.XR - 520, ch.XR + 40, m), y=rng.uniform(ch.YT - 60, ch.YB + 60, m), L=rng.uniform(60, 280, m),
                               v=rng.uniform(1800, 4200, m), a=rng.uniform(0.25, 0.8, m))
    # waterfall rain during crash 1
    n = 260
    FX['rain'] = dict(x=rng.uniform(0, W, n), y=rng.uniform(-300, H, n), L=rng.uniform(80, 300, n), v=rng.uniform(1500, 3200, n), a=rng.uniform(0.15, 0.5, n))
    # 爆仓 tag
    tag = Image.new('RGBA', (430, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(tag)
    d.rounded_rectangle((4, 4, 426, 116), 18, fill=(150, 10, 28, 235), outline=(255, 120, 130, 255), width=3)
    d.text((26, 60), "爆仓", font=ImageFont.truetype(SANS, 66), fill=(255, 255, 255, 255), anchor='lm')
    d.text((190, 42), "LIQUIDATED", font=ImageFont.truetype(MONO, 24), fill=(255, 205, 210, 255), anchor='lm')
    d.text((190, 82), "$2.31B LONGS", font=ImageFont.truetype(MONO, 24), fill=(255, 255, 255, 255), anchor='lm')
    FX['tag'] = np.asarray(tag, np.float32) / 255
    FX['bfont'] = ImageFont.truetype(MONO, 64)
    FX['bcache'] = {}
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    FX['edge'] = (np.clip(np.hypot((xx - CX) / 960, (yy - CY) / 540) - 0.55, 0, 1) ** 1.2 * 1.8)[..., None].astype(np.float32)
    FX['rightmask'] = np.clip((np.arange(W, dtype=np.float32) - 700) / 400, 0, 1)[None, :, None]

def ev_strength(t):
    """list of (k, x, tau) for big candles active at t"""
    out = []
    for k, x in FX['ev']:
        tau = t - te_of(k)
        if -0.01 <= tau < 1.0: out.append((k, x, tau))
    return out

def badge_img(txt, pos):
    key = (txt, pos)
    if key in FX['bcache']: return FX['bcache'][key]
    f = FX['bfont']; w = int(f.getlength(txt)) + 60; h = 96
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = (14, 203, 129, 245) if pos else (246, 70, 93, 245)
    d.rounded_rectangle((2, 2, w - 2, h - 2), 20, fill=c)
    d.text((w / 2, h / 2 + 2), txt, font=f, fill=(255, 255, 255, 255), anchor='mm')
    a = np.asarray(im, np.float32) / 255
    if len(FX['bcache']) > 400: FX['bcache'].clear()
    FX['bcache'][key] = a
    return a

def paste(fr, rgba, cx, cy, sx=1.0, sy=1.0, al=1.0, glow=0.0, gcol=None):
    h, w = rgba.shape[:2]
    if sx < 0.02 or sy < 0.02 or al < 0.01: return
    M = np.array([[sx, 0, cx - sx * w / 2], [0, sy, cy - sy * h / 2]], np.float32)
    x0, y0 = int(max(cx - sx * w / 2 - 40, 0)), int(max(cy - sy * h / 2 - 40, 0))
    x1, y1 = int(min(cx + sx * w / 2 + 40, W)), int(min(cy + sy * h / 2 + 40, H))
    M[0, 2] -= x0; M[1, 2] -= y0
    o = cv2.warpAffine(rgba, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR)
    a = o[..., 3:4] * al
    roi = fr[y0:y1, x0:x1]
    if glow > 0:
        roi += cv2.GaussianBlur(a[..., 0], (0, 0), 14)[..., None] * gcol * glow
    roi[:] = roi * (1 - a) + o[..., :3] * a

def chart_fx(fr, t, info):
    """mutates the chart layer (pre-text); returns camera tilt (deg), extra zoom, flash list, edge tint colour"""
    evs = ev_strength(t)
    tilt = 0.0; zoom = 0.0; flashes = []; edge = np.zeros(3, np.float32)
    streak = np.zeros_like(fr[:, 700:]) if evs else None
    small = None
    for k, x, tau in evs:
        sg = 1 if x > 0 else -1; col = GREEN if x > 0 else RED; ax = abs(x)
        tilt += sg * min(2.6, 22 * ax) * math.exp(-max(tau, 0) / 0.32) * ss(0, 0.05, tau)
        zoom += min(0.07, 0.6 * ax) * math.exp(-max(tau, 0) / 0.2) * ss(-0.01, 0.03, tau)
        edge += col * min(0.30, 1.8 * ax) * math.exp(-max(tau, 0) / 0.18)
        flashes.append((te_of(k), min(0.24, 0.05 + 1.3 * ax), col))
        # vertical motion blur while the candle forms
        if 0 <= tau < ch.DC * 1.3:
            L = int(min(71, 11 + 520 * ax)) | 1
            sub = fr[:, 700:]
            bl = cv2.blur(sub, (1, L))
            wgt = 0.65 * (1 - tau / (ch.DC * 1.3))
            fr[:, 700:] = sub * (1 - wgt * FX['rightmask'][:, 700:]) + bl * wgt * FX['rightmask'][:, 700:]
        # speed streaks along the candle direction
        if 0 <= tau < 0.4:
            s = FX['streak'][k]
            yy = s['y'] - sg * s['v'] * tau
            a = s['a'] * (1 - tau / 0.4) ** 1.3
            for xi, yi, Li, ai in zip(s['x'], yy, s['L'], a):
                cv2.line(streak, (int(xi - 700), int(yi)), (int(xi - 700), int(yi + sg * Li)), tuple(float(c) * ai * 0.7 for c in col), 2, cv2.LINE_AA)
        # spray of particles off the candle tip
        if 0 <= tau < 0.8:
            if small is None: small = np.zeros_like(fr)
            sp = FX['spray'][k]
            tip_t = te_of(k) + ch.DC * 0.85
            x0 = ch.cand_x(t, k); y0 = ch.price_y(min(t, tip_t), ch.D['C'][ch.kidx(k)])
            tt_ = max(tau - ch.DC * 0.5, 0)
            if tau > ch.DC * 0.5:
                for kk in range(3):
                    tk = max(tt_ - kk / 3 / 30, 0)
                    px = x0 + sp['ox'] + sp['vx'] * tk; py = y0 + sp['oy'] + sp['vy'] * tk + 1400 * tk * tk
                    al = np.clip(1 - tk / sp['life'], 0, 1) ** 1.4 * sp['z']
                    cc = np.broadcast_to(col * 0.6 + 0.4, (len(px), 3)).astype(np.float32)
                    v1.splat(small, px, py, al / 3 * 1.5, cc)
            # volume spike burst
            vx = int(x0); vb = int(ch.VB)
            gy0, gy1 = max(vb - 260, 0), min(vb + 40, H); gx0, gx1 = max(vx - 120, 0), min(vx + 120, W)
            yy, xx = np.mgrid[gy0:gy1, gx0:gx1].astype(np.float32)
            g = np.exp(-((xx - vx) / 26) ** 2 - ((yy - vb) / 140) ** 2) * min(1.0, 8 * ax) * math.exp(-tau / 0.22)
            fr[gy0:gy1, gx0:gx1] += g[..., None] * (col * 0.8 + 0.2)
    if streak is not None:
        fr[:, 700:] += cv2.GaussianBlur(streak, (0, 0), 1.2) * 1.2
    if small is not None:
        fr += cv2.GaussianBlur(small, (0, 0), 0.9) * 1.2 + cv2.GaussianBlur(small, (0, 0), 4) * 0.5
    # red waterfall rain (crash 1)
    ta, tb = te_of(24), te_of(24) + 1.1
    if ta <= t < tb:
        r = FX['rain']; tau = t - ta
        buf = np.zeros_like(fr)
        yy = (r['y'] + r['v'] * tau) % (H + 300) - 150
        fa = math.sin(math.pi * c01(tau / 1.1)) ** 0.7
        for xi, yi, Li, ai in zip(r['x'], yy, r['L'], r['a']):
            cv2.line(buf, (int(xi), int(yi - Li)), (int(xi), int(yi)), tuple(float(c) * ai * fa for c in RED), 2, cv2.LINE_AA)
        fr += cv2.GaussianBlur(buf, (0, 0), 1.5)
    # 爆仓 liquidation tag
    t0 = te_of(24) + 0.05
    if t0 <= t < t0 + 1.7:
        tau = t - t0
        sy = min(1.0, eo3(tau / 0.12)) * (1 + 0.15 * math.exp(-tau / 0.08)); sx = 1 + 0.15 * math.exp(-tau / 0.08)
        al = 1 - ss(1.45, 1.7, tau)
        jx = 8 * math.sin(tau * 80) * math.exp(-tau / 0.2)
        paste(fr, FX['tag'], 1430 + jx, 300, sx, sy, al, glow=0.9 * (0.5 + 0.5 * math.exp(-tau / 0.3)), gcol=RED)
    # glowing ticker + big % badge (flip-in per swing, rolls with price)
    kf = info['kf']
    up = info['up']
    tick_col = GREEN if up else RED
    hb = fr[34:108, 290:740]
    pulse = 0.35 + sum(min(1.0, 6 * abs(x)) * math.exp(-max(tau, 0) / 0.2) for k, x, tau in evs)
    fr[34:108, 290:740] += cv2.GaussianBlur(hb, (0, 0), 9) * (0.9 * pulse)
    for (k0, k1) in ch.SWINGS:
        a0, a1 = te_of(k0), te_of(k1 + 1)
        if not (a0 <= t < a1 + 0.2): continue
        pct = ch.swing_pct(k0, min(kf, k1 + 0.999))
        txt = f"{'+' if pct >= 0 else ''}{pct * 100:.1f}%"
        tau = t - a0
        flip = math.cos(math.pi * (1 - c01(tau / 0.14))) * -1 if tau < 0.14 else 1.0
        sy = max(0.0, (0.5 - 0.5 * math.cos(math.pi * c01(tau / 0.14)))) * (1 + 0.12 * math.exp(-max(tau - 0.14, 0) / 0.07))
        out = ss(a1 + 0.0, a1 + 0.15, t)
        sy *= 1 - out
        pop = sum(0.10 * math.exp(-max(tt, 0) / 0.08) for kk, x, tt in evs if k0 <= kk <= k1 and tt >= 0)
        paste(fr, badge_img(txt, pct >= 0), 250, 238, 1 + pop, sy * (1 + pop), 1.0, glow=0.8 + 2 * pop, gcol=GREEN if pct >= 0 else RED)
    return tilt, zoom, flashes, edge
