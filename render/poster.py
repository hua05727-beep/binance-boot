import numpy as np, cv2, math
from PIL import Image, ImageFont, ImageDraw
import render as v1
W, H = 3840, 2160
rng = np.random.default_rng(8)
SANS = '/workspace/binance-boot/fonts/NotoSansCJKsc-Black.otf'
SERIF = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
def font(p, s): return ImageFont.truetype(p, s, index=2) if p.endswith('.ttc') else ImageFont.truetype(p, s)
def ssv(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

# ---------------- layout ----------------
LCX, LCY, LH = 1060.0, 930.0, 1080.0      # logo centre / height
TCX = 2660.0                               # text block centre x

# ---------------- background ----------------
r_logo = np.sqrt((xx - LCX) ** 2 + (yy - LCY) ** 2)
r_c = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
img = np.zeros((H, W, 3), np.float32)
img += np.array([0.010, 0.009, 0.007], np.float32)
img += np.exp(-(r_logo / 1250) ** 2)[..., None] * np.array([0.11, 0.075, 0.018], np.float32)
img += np.exp(-(((xx - TCX) / 1400) ** 2 + ((yy - 1000) / 700) ** 2))[..., None] * np.array([0.035, 0.024, 0.006], np.float32)
img *= (1 - 0.55 * ssv(0.35, 0.75, r_c))[..., None]
# hex grid
SSF = 2; R = 96.0
hx = np.zeros((H, W), np.uint8)
dx = R * 1.5; dy = R * math.sqrt(3)
polys = []
for i in range(-2, int(W / dx) + 3):
    for j in range(-2, int(H / dy) + 3):
        cx = i * dx; cy = j * dy + (dy / 2 if i % 2 else 0)
        pts = [(cx + R * math.cos(math.pi / 3 * k), cy + R * math.sin(math.pi / 3 * k)) for k in range(6)]
        polys.append(np.round(np.array(pts) * 16).astype(np.int32))
cv2.polylines(hx, polys, True, 255, thickness=2, lineType=cv2.LINE_AA, shift=4)
hexg = hx.astype(np.float32) / 255
hm = 0.065 * np.exp(-(r_logo / 1500) ** 2) * ssv(300, 700, r_logo) + 0.035 * (1 - ssv(0.2, 0.7, r_c))
img += (hexg * hm)[..., None] * np.array([0.95, 0.72, 0.25], np.float32)
# light rays behind logo
th = np.arctan2(yy - LCY, xx - LCX)
pat = np.zeros((H, W), np.float32)
rr = np.random.default_rng(3)
for n in rr.integers(5, 46, 14):
    pat += rr.uniform(0.4, 1.0) * np.cos(n * th + rr.uniform(0, 6.3))
pat = np.clip(pat / 3.0, 0, 1) ** 2.2
img += (pat * ssv(380, 700, r_logo) * np.exp(-r_logo / 1100) * 0.07)[..., None] * np.array([1.0, 0.78, 0.30], np.float32)
# bokeh
bok = np.zeros((H // 2, W // 2, 3), np.float32)
for _ in range(70):
    bx, by = rng.uniform(0, W / 2), rng.uniform(0, H / 2); br = rng.uniform(12, 70)
    a = rng.uniform(0.02, 0.085)
    x0, x1, y0, y1 = int(max(bx - br - 3, 0)), int(min(bx + br + 4, W / 2)), int(max(by - br - 3, 0)), int(min(by + br + 4, H / 2))
    gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.sqrt((gx - bx) ** 2 + (gy - by) ** 2) / br
    prof = ssv(1.0, 0.72, d) * (0.8 + 0.2 * ssv(0.5, 0.92, d))
    h = rng.uniform()
    bok[y0:y1, x0:x1] += prof[..., None] * ((v1.GOLD_A * (1 - h) + v1.GOLD_B * h) * a).astype(np.float32)
img += cv2.resize(bok, (W, H), interpolation=cv2.INTER_LINEAR)
# particles
pl = np.zeros((H, W, 3), np.float32)
N = 2600
px = rng.uniform(0, W, N); py = rng.uniform(0, H, N)
# denser around logo
M2 = 900
ang = rng.uniform(0, 6.283, M2); rad = rng.normal(0, 1, M2) * 360 + 700
px = np.concatenate([px, LCX + np.cos(ang) * rad]); py = np.concatenate([py, LCY + np.sin(ang) * rad * 0.9])
z = rng.uniform(0.2, 1.0, len(px)) ** 1.5
hues = rng.uniform(0, 1, len(px))
col = v1.GOLD_A[None] * (1 - hues[:, None]) + v1.GOLD_B[None] * hues[:, None]
v1.W, v1.H = W, H
v1.splat(pl, px, py, (0.6 + 1.6 * z) * 0.9, col)
pl = cv2.GaussianBlur(pl, (0, 0), 1.6) * 2.2 + cv2.GaussianBlur(pl, (0, 0), 5) * 1.5
img += pl * (1 - 0.6 * ssv(0, 1, np.exp(-(((xx - TCX) / 900) ** 2 + ((yy - 1050) / 520) ** 2))))[..., None]
# faint candlestick silhouette (theme), lower right, above taskbar zone
cs = np.zeros((H, W, 3), np.uint8)
p = 0.0; xk = 1700.0
for k in range(70):
    o = p; p = p + rng.normal(0.25, 1.0) + (2.5 if k % 9 == 0 else 0) - (3.5 if k % 13 == 7 else 0)
    c = p; hi = max(o, c) + abs(rng.normal(0, 0.6)); lo = min(o, c) - abs(rng.normal(0, 0.6))
    def Y(v): return 1930 - v * 16
    colc = (14, 203, 129) if c >= o else (246, 70, 93)
    cv2.rectangle(cs, (int(xk), int(Y(hi))), (int(xk + 3), int(Y(lo))), colc, -1, cv2.LINE_AA)
    y0, y1 = sorted([Y(o), Y(c)])
    cv2.rectangle(cs, (int(xk - 9), int(y0)), (int(xk + 12), int(max(y1, y0 + 3))), colc, -1, cv2.LINE_AA)
    xk += 31
csf = cs.astype(np.float32) / 255
cmask = ssv(1700, 2600, xx) * (1 - ssv(3500, 3840, xx)) * 0.10
img += csf * cmask[..., None]

# ---------------- logo ----------------
U = LH / 24.0
MSZ = int(LH + 400); MC = MSZ / 2
k = U / 16.0
SSF = 3
pm = []
for poly in v1.pieces():
    im = np.zeros((MSZ * SSF, MSZ * SSF), np.uint8)
    pts = ((poly - 12) * U + MC) * SSF
    cv2.fillPoly(im, [np.round(pts * 16).astype(np.int32)], 255, lineType=cv2.LINE_AA, shift=4)
    pm.append(cv2.resize(im, (MSZ, MSZ), interpolation=cv2.INTER_AREA).astype(np.float32) / 255)
m = np.clip(sum(pm), 0, 1)
b = cv2.GaussianBlur(m, (0, 0), 2.4 * k)
gx = cv2.Sobel(b, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(b, cv2.CV_32F, 0, 1, ksize=3) / 8
shade = np.clip((-gx * -0.55 - gy * -0.83) * 9.0 * k, -1, 1)
my, mx = np.mgrid[0:MSZ, 0:MSZ].astype(np.float32)
X = (mx - MC) / (12 * U); Yq = (my - MC) / (12 * U)
base = v1.gold_lut((X * 0.42 + Yq * 0.91) / 1.05, v1.GOLD_STOPS)
rim = np.clip(1 - b, 0, 1) * m
sp = np.clip(shade, 0, 1); sn = np.clip(-shade, 0, 1)
C = base * (1 - 0.18 * rim[..., None]) + sp[..., None] ** 1.5 * np.array([1.0, 0.95, 0.80], np.float32) * 0.55 - sn[..., None] * base * 0.38
edge = np.clip(m - cv2.erode(m, np.ones((3, 3), np.uint8), iterations=int(2 * k)), 0, 1)
C += (edge * sp)[..., None] * 0.35
hl = np.clip(sp + 0.6 * rim, 0, 1.5)
q = X * math.cos(math.radians(-24)) + Yq * math.sin(math.radians(-24))
d = q - (-0.28)
sw = np.exp(-(d / 0.09) ** 2) * 1.0 + np.exp(-(d / 0.26) ** 2) * 0.22
C = C + (sw * (0.45 + 1.3 * hl))[..., None] * np.array([1.0, 0.96, 0.84], np.float32) * 0.8
C = np.clip(C, 0, 1.5)
x0 = int(LCX - MC); y0 = int(LCY - MC)
la = np.zeros((H, W), np.float32); lc = np.zeros((H, W, 3), np.float32)
la[y0:y0 + MSZ, x0:x0 + MSZ] = m
lc[y0:y0 + MSZ, x0:x0 + MSZ] = C * m[..., None]
# logo glow + shadow
gl = cv2.GaussianBlur(la, (0, 0), 40) * 0.45 + cv2.GaussianBlur(la, (0, 0), 140) * 0.35
img += gl[..., None] * np.array([1.0, 0.72, 0.15], np.float32)
img = img * (1 - la[..., None]) + lc

# ---------------- text helpers ----------------
def text_masks(s, path, size, strokes, track=0.0, pad=60):
    f = font(path, size)
    adv = [f.getlength(c) for c in s]
    tw = sum(adv) + track * size * (len(s) - 1)
    w = int(tw + 2 * pad + 2 * max(strokes)); h = int(size * 1.45 + 2 * pad)
    outs = []
    for sw_ in [0] + list(strokes):
        im = Image.new('L', (w, h), 0); dr = ImageDraw.Draw(im)
        x = pad + max(strokes)
        for c, a in zip(s, adv):
            dr.text((x + a / 2, h / 2), c, font=f, fill=255, anchor='mm', stroke_width=sw_, stroke_fill=255)
            x += a + track * size
        outs.append(np.asarray(im, np.float32) / 255)
    return outs, w, h

def place_layers(layers, w, h, cx, cy, shear=0.0):
    """affine into full canvas, centre at (cx,cy), shear x by y"""
    M = np.array([[1, -shear, cx - w / 2 + shear * h / 2], [0, 1, cy - h / 2]], np.float32)
    return [cv2.warpAffine(l, M, (W, H), flags=cv2.INTER_LINEAR) for l in layers]

def grad_v(cy, half, stops):
    g = np.clip((np.arange(H, dtype=np.float32) - cy) / half, -1, 1)
    return v1.gold_lut(g, stops)[:, None, :]

HEAD_STOPS = [(-1.0, (1.0, 0.99, 0.93)), (-0.25, (1.0, 0.93, 0.66)), (0.1, (0.99, 0.80, 0.22)), (0.55, (0.93, 0.67, 0.05)), (1.0, (0.70, 0.45, 0.02))]
GOLD_TXT = [(-1.0, (1.0, 0.93, 0.62)), (-0.35, (0.99, 0.80, 0.22)), (0.1, (0.92, 0.66, 0.05)), (0.45, (1.0, 0.86, 0.38)), (1.0, (0.72, 0.48, 0.02))]

def comp_headline(img, s, size, cx, cy, shear, stops, stroke_dark, stroke_gold, sweep_pos=None, track=0.0):
    (F, S1, S2), w, h = text_masks(s, SANS, size, [stroke_dark, stroke_dark + stroke_gold], track)
    F, S1, S2 = place_layers([F, S1, S2], w, h, cx, cy, shear)
    # drop shadow + glow
    sh = cv2.GaussianBlur(np.roll(np.roll(S2, 18, 0), 10, 1), (0, 0), 16)
    img = img * (1 - 0.85 * sh[..., None])
    glw = cv2.GaussianBlur(S2, (0, 0), 30) * 0.35 + cv2.GaussianBlur(S2, (0, 0), 90) * 0.25
    img += glw[..., None] * np.array([1.0, 0.70, 0.12], np.float32)
    # emboss on fill
    bf = cv2.GaussianBlur(F, (0, 0), 3.0)
    gx = cv2.Sobel(bf, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(bf, cv2.CV_32F, 0, 1, ksize=3) / 8
    shd = np.clip((gx * 0.55 + gy * 0.83) * 14, -1, 1)
    fill = grad_v(cy, size * 0.5, stops) * np.ones((1, W, 1), np.float32)
    fill = fill * (1 - 0.30 * np.clip(-shd, 0, 1))[..., None] + (np.clip(shd, 0, 1) ** 1.4)[..., None] * 0.45
    if sweep_pos is not None:
        dd = (xx - sweep_pos) + (yy - cy) * 0.5
        fill += (np.exp(-(dd / 70) ** 2) * 0.9 + np.exp(-(dd / 260) ** 2) * 0.18)[..., None] * np.array([1, 0.97, 0.88], np.float32)
    dark = np.array([0.045, 0.030, 0.008], np.float32)
    rimc = grad_v(cy, size * 0.55, GOLD_TXT)
    col = fill * F[..., None] + dark * np.clip(S1 - F, 0, 1)[..., None] + rimc * np.clip(S2 - S1, 0, 1)[..., None]
    img = img * (1 - S2[..., None]) + col
    return img, S2

def comp_simple(img, s, path, size, cx, cy, colfn, stroke=0, glow=0.25, track=0.0, shadow=True):
    lst, w, h = text_masks(s, path, size, [stroke] if stroke else [1], track)
    F, S = place_layers(lst, w, h, cx, cy)
    if not stroke: S = F
    if shadow:
        sh = cv2.GaussianBlur(np.roll(S, 8, 0), (0, 0), 10)
        img = img * (1 - 0.8 * sh[..., None])
    img += (cv2.GaussianBlur(S, (0, 0), 22) * glow)[..., None] * np.array([1.0, 0.72, 0.15], np.float32)
    col = colfn(cy, size) * F[..., None] + np.array([0.04, 0.03, 0.01], np.float32) * np.clip(S - F, 0, 1)[..., None]
    img = img * (1 - S[..., None]) + col
    return img, w

# ---------------- headline ----------------
img, _ = comp_headline(img, "天才，", 380, TCX - 330, 560, 0.10, HEAD_STOPS, 18, 7, sweep_pos=TCX - 460)
img, _ = comp_headline(img, "证明给我看！", 300, TCX + 20, 930, 0.10, HEAD_STOPS, 16, 6, sweep_pos=TCX + 420)
# divider
dv = np.exp(-((yy - 1150) / 2.2) ** 2) * (1 - ssv(0, 820, np.abs(xx - TCX))) * 0.9
img += dv[..., None] * np.array([1.0, 0.80, 0.30], np.float32)
img += (np.exp(-(((xx - TCX) / 40) ** 2 + ((yy - 1150) / 3) ** 2)) * 1.2)[..., None] * np.array([1, 0.95, 0.8], np.float32)

# ---------------- subline with heartbeat accents ----------------
def white(cy, size): return np.array([0.98, 0.97, 0.94], np.float32)
img, sw_w = comp_simple(img, "老实赚钱，很枯燥吧", SANS, 132, TCX, 1305, white, stroke=6, glow=0.12)
def ecg(img, x_from, x_to, y, mirror):
    pts = []
    L = abs(x_to - x_from)
    shape = [(0, 0), (0.48, 0), (0.54, -0.25), (0.60, 0.15), (0.66, -1.0), (0.73, 0.75), (0.79, -0.2), (0.85, 0), (1.0, 0)]
    for u, v in shape:
        uu = 1 - u if mirror else u
        pts.append((x_from + (x_to - x_from) * (u), y + v * 62))
    lay = np.zeros((H, W), np.uint8)
    cv2.polylines(lay, [np.round(np.array(pts) * 16).astype(np.int32)], False, 255, 7, cv2.LINE_AA, 4)
    lf = lay.astype(np.float32) / 255
    # fade toward the outer end
    xs = xx
    fade = np.clip(np.abs(xs - x_from) / L, 0, 1) ** 0.8
    lf = lf * fade
    img += (cv2.GaussianBlur(lf, (0, 0), 14) * 0.9)[..., None] * np.array([1.0, 0.55, 0.12], np.float32)
    img = img * (1 - lf[..., None]) + lf[..., None] * np.array([1.0, 0.86, 0.45], np.float32)
    # bright pulse dot at inner end
    img += (np.exp(-(((xx - x_to) / 9) ** 2 + ((yy - y) / 9) ** 2)) * 1.4)[..., None] * np.array([1, .9, .7], np.float32)
    return img
half = sw_w / 2 - 50
img = ecg(img, TCX - half - 400, TCX - half - 40, 1305, False)
img = ecg(img, TCX + half + 400, TCX + half + 40, 1305, True)

# ---------------- third line ----------------
def goldf(cy, size): return grad_v(cy, size * 0.55, GOLD_TXT)
img, _ = comp_simple(img, "放弃垃圾游戏　与世界顶级资本同台博弈", SERIF, 92, TCX, 1500, goldf, stroke=4, glow=0.22)

# ---------------- wordmark under logo ----------------
f = v1.font(150, 700)
word = "BINANCE"; track = 0.30 * 150
adv = [f.getlength(c) for c in word]; tw = sum(adv) + track * 6
im = Image.new('L', (W, 300), 0); dr = ImageDraw.Draw(im); x = LCX - tw / 2
for c, a in zip(word, adv):
    dr.text((x, 150), c, font=f, fill=255, anchor='lm'); x += a + track
wm = np.zeros((H, W), np.float32); wy = int(LCY + LH / 2 + 250)
wm[wy - 150:wy + 150] = np.asarray(im, np.float32) / 255
img = img * (1 - 0.7 * cv2.GaussianBlur(np.roll(wm, 6, 0), (0, 0), 8)[..., None])
img += (cv2.GaussianBlur(wm, (0, 0), 20) * 0.25)[..., None] * np.array([1.0, 0.72, 0.15], np.float32)
img = img * (1 - wm[..., None]) + wm[..., None] * grad_v(wy, 80, GOLD_TXT)
ln = np.exp(-((yy - (wy + 135)) / 2.0) ** 2) * (1 - ssv(0, 560, np.abs(xx - LCX))) * 0.85
img += ln[..., None] * np.array([1.0, 0.80, 0.30], np.float32)

# ---------------- corner frame accents ----------------
fr = np.zeros((H, W), np.uint8)
m_ = 90; Lc = 220
for (cx_, cy_, sx, sy) in [(m_, m_, 1, 1), (W - m_, m_, -1, 1), (m_, H - 200, 1, -1), (W - m_, H - 200, -1, -1)]:
    cv2.line(fr, (cx_, cy_), (cx_ + sx * Lc, cy_), 255, 3, cv2.LINE_AA)
    cv2.line(fr, (cx_, cy_), (cx_, cy_ + sy * Lc), 255, 3, cv2.LINE_AA)
frf = fr.astype(np.float32) / 255
img += frf[..., None] * np.array([0.75, 0.56, 0.18], np.float32) * 0.8

# ---------------- finish ----------------
lum = img.max(axis=2, keepdims=True)
bs = img * np.clip((lum - 0.6) / 0.5, 0, 1)
bq = cv2.resize(bs, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
bl = cv2.GaussianBlur(bq, (0, 0), 3) * 0.25 + cv2.GaussianBlur(bq, (0, 0), 12) * 0.22
img += cv2.resize(bl, (W, H), interpolation=cv2.INTER_CUBIC)
img = np.where(img < 0.82, img, 0.82 + 0.18 * np.tanh((img - 0.82) / 0.18))
img += rng.triangular(-1, 0, 1, img.shape).astype(np.float32) / 255 * 0.8
out = (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
Image.fromarray(out).save('/workspace/binance-boot/poster_desktop_4k.png', optimize=False, compress_level=6)
for (w_, h_, n_) in [(2560, 1440, 'poster_desktop_2k.png'), (1920, 1080, 'poster_horizontal.png')]:
    Image.fromarray(cv2.resize(out, (w_, h_), interpolation=cv2.INTER_AREA)).save('/workspace/binance-boot/' + n_)
Image.fromarray(cv2.resize(out, (1600, 900), interpolation=cv2.INTER_AREA)).save('/tmp/poster_prev_%s.png' % __import__('os').environ.get('V', '0'))
print('ok')
