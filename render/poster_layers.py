# Build poster elements as separate 1080p layers (rendered at 4K, downsampled) for the v3 animation.
import numpy as np, cv2, math
exec(open('/tmp/poster_head.py').read().replace("# faint candlestick", "# faint candlestick"))   # background into `img`
from PIL import Image, ImageFont, ImageDraw
BG = img.copy()
EL = {}
def blank(): return np.zeros((H, W), np.float32)
def blank3(): return np.zeros((H, W, 3), np.float32)
def store(name, C=None, A=None, G=None, Sh=None, F=None, anchor=(0, 0)):
    EL[name] = dict(C=C, A=A, G=G, Sh=Sh, F=F, anchor=anchor)

# ---- logo ----
U = LH / 24.0
MSZ = int(LH + 400); MC = MSZ / 2
k = U / 16.0; SSF = 3
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
C = np.clip(C + (sw * (0.45 + 1.3 * hl))[..., None] * np.array([1.0, 0.96, 0.84], np.float32) * 0.8, 0, 1.5)
x0 = int(LCX - MC); y0 = int(LCY - MC)
la = blank(); lc = blank3()
la[y0:y0 + MSZ, x0:x0 + MSZ] = m
lc[y0:y0 + MSZ, x0:x0 + MSZ] = C * m[..., None]
gl = cv2.GaussianBlur(la, (0, 0), 40) * 0.45 + cv2.GaussianBlur(la, (0, 0), 140) * 0.35
store('logo', C=lc, A=la, G=gl[..., None] * np.array([1.0, 0.72, 0.15], np.float32), anchor=(LCX, LCY))

# ---- text helpers (element versions) ----
exec(open('poster.py').read().split('# ---------------- text helpers ----------------')[1].split('# ---------------- headline ----------------')[0])

def el_headline(name, s, size, cx, cy, shear, stops, sd, sg):
    (F, S1, S2), w, h = text_masks(s, SANS, size, [sd, sd + sg])
    F, S1, S2 = place_layers([F, S1, S2], w, h, cx, cy, shear)
    sh = cv2.GaussianBlur(np.roll(np.roll(S2, 18, 0), 10, 1), (0, 0), 16) * 0.85
    glw = (cv2.GaussianBlur(S2, (0, 0), 30) * 0.35 + cv2.GaussianBlur(S2, (0, 0), 90) * 0.25)[..., None] * np.array([1.0, 0.70, 0.12], np.float32)
    bf = cv2.GaussianBlur(F, (0, 0), 3.0)
    gx = cv2.Sobel(bf, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(bf, cv2.CV_32F, 0, 1, ksize=3) / 8
    shd = np.clip((gx * 0.55 + gy * 0.83) * 14, -1, 1)
    fill = grad_v(cy, size * 0.5, stops) * np.ones((1, W, 1), np.float32)
    fill = fill * (1 - 0.30 * np.clip(-shd, 0, 1))[..., None] + (np.clip(shd, 0, 1) ** 1.4)[..., None] * 0.45
    dark = np.array([0.045, 0.030, 0.008], np.float32)
    rimc = grad_v(cy, size * 0.55, GOLD_TXT)
    col = fill * F[..., None] + dark * np.clip(S1 - F, 0, 1)[..., None] + rimc * np.clip(S2 - S1, 0, 1)[..., None]
    store(name, C=col, A=S2, G=glw, Sh=sh, F=F, anchor=(cx, cy))

def el_simple(name, s, path, size, cx, cy, colfn, stroke, glow):
    lst, w, h = text_masks(s, path, size, [stroke])
    F, S = place_layers(lst, w, h, cx, cy)
    sh = cv2.GaussianBlur(np.roll(S, 8, 0), (0, 0), 10) * 0.8
    G = (cv2.GaussianBlur(S, (0, 0), 22) * glow)[..., None] * np.array([1.0, 0.72, 0.15], np.float32)
    col = colfn(cy, size) * F[..., None] + np.array([0.04, 0.03, 0.01], np.float32) * np.clip(S - F, 0, 1)[..., None]
    store(name, C=col, A=S, G=G, Sh=sh, F=F, anchor=(cx, cy))
    return w

el_headline('head1', "天才，", 380, TCX - 330, 560, 0.10, HEAD_STOPS, 18, 7)
el_headline('head2', "证明给我看！", 300, TCX + 20, 930, 0.10, HEAD_STOPS, 16, 6)
dv = np.exp(-((yy - 1150) / 2.2) ** 2) * (1 - ssv(0, 820, np.abs(xx - TCX))) * 0.9
G = dv[..., None] * np.array([1.0, 0.80, 0.30], np.float32) + (np.exp(-(((xx - TCX) / 40) ** 2 + ((yy - 1150) / 3) ** 2)) * 1.2)[..., None] * np.array([1, 0.95, 0.8], np.float32)
store('divider', G=G, anchor=(TCX, 1150))
def white(cy, size): return np.array([0.98, 0.97, 0.94], np.float32)
sw_w = el_simple('sub', "老实赚钱，很枯燥吧", SANS, 132, TCX, 1305, white, 6, 0.12)
def ecg_el(name, x_from, x_to, y):
    L = abs(x_to - x_from)
    shape = [(0, 0), (0.48, 0), (0.54, -0.25), (0.60, 0.15), (0.66, -1.0), (0.73, 0.75), (0.79, -0.2), (0.85, 0), (1.0, 0)]
    pts = [(x_from + (x_to - x_from) * u, y + v * 62) for u, v in shape]
    lay = np.zeros((H, W), np.uint8)
    cv2.polylines(lay, [np.round(np.array(pts) * 16).astype(np.int32)], False, 255, 7, cv2.LINE_AA, 4)
    lf = lay.astype(np.float32) / 255 * np.clip(np.abs(xx - x_from) / L, 0, 1) ** 0.8
    G = (cv2.GaussianBlur(lf, (0, 0), 14) * 0.9)[..., None] * np.array([1.0, 0.55, 0.12], np.float32)
    store(name, C=lf[..., None] * np.array([1.0, 0.86, 0.45], np.float32), A=lf, G=G, anchor=(x_to, y))
half = sw_w / 2 - 50
ecg_el('ecgL', TCX - half - 400, TCX - half - 40, 1305)
ecg_el('ecgR', TCX + half + 400, TCX + half + 40, 1305)
def goldf(cy, size): return grad_v(cy, size * 0.55, GOLD_TXT)
el_simple('third', "放弃垃圾游戏　与世界顶级资本同台博弈", SERIF, 92, TCX, 1500, goldf, 4, 0.22)
# wordmark
f = v1.font(150, 700)
word = "BINANCE"; track = 0.30 * 150
adv = [f.getlength(c) for c in word]; tw = sum(adv) + track * 6
im = Image.new('L', (W, 300), 0); dr = ImageDraw.Draw(im); x = LCX - tw / 2
for c, a in zip(word, adv):
    dr.text((x, 150), c, font=f, fill=255, anchor='lm'); x += a + track
wm = blank(); wy = int(LCY + LH / 2 + 250)
wm[wy - 150:wy + 150] = np.asarray(im, np.float32) / 255
ln = np.exp(-((yy - (wy + 135)) / 2.0) ** 2) * (1 - ssv(0, 560, np.abs(xx - LCX))) * 0.85
store('word', C=wm[..., None] * grad_v(wy, 80, GOLD_TXT), A=wm,
      G=(cv2.GaussianBlur(wm, (0, 0), 20) * 0.25)[..., None] * np.array([1.0, 0.72, 0.15], np.float32) + ln[..., None] * np.array([1.0, 0.80, 0.30], np.float32),
      Sh=0.7 * cv2.GaussianBlur(np.roll(wm, 6, 0), (0, 0), 8), anchor=(LCX, wy))
fr = np.zeros((H, W), np.uint8)
m_ = 90; Lc = 220
for (cx_, cy_, sx, sy) in [(m_, m_, 1, 1), (W - m_, m_, -1, 1), (m_, H - 200, 1, -1), (W - m_, H - 200, -1, -1)]:
    cv2.line(fr, (cx_, cy_), (cx_ + sx * Lc, cy_), 255, 3, cv2.LINE_AA)
    cv2.line(fr, (cx_, cy_), (cx_, cy_ + sy * Lc), 255, 3, cv2.LINE_AA)
store('frames', G=(fr.astype(np.float32) / 255)[..., None] * np.array([0.75, 0.56, 0.18], np.float32) * 0.8, anchor=(W / 2, H / 2))

# ---- downsample to 1080p and crop to bbox ----
def ds(a): return cv2.resize(a, (1920, 1080), interpolation=cv2.INTER_AREA)
out = {'bg': ds(BG).astype(np.float16)}
for name, e in EL.items():
    arrs = {kk: ds(v) for kk, v in e.items() if kk != 'anchor' and v is not None}
    occ = np.zeros((1080, 1920), bool)
    for v in arrs.values():
        vv = v if v.ndim == 2 else v.max(axis=2)
        occ |= vv > 1.5 / 1024
    ys, xs = np.where(occ)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    for kk, v in arrs.items():
        out[f'{name}__{kk}'] = v[y0:y1, x0:x1].astype(np.float16)
    out[f'{name}__box'] = np.array([x0, y0, x1, y1])
    out[f'{name}__anchor'] = np.array(e['anchor']) / 2
    print(name, (x0, y0, x1, y1), list(arrs))
np.savez('poster_layers.npz', **out)
print('saved')
