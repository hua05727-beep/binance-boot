import numpy as np, wave, subprocess, re
SR = 48000
w = wave.open('sfx6_only.wav'); x = np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, 2).astype(np.float64) / 32767
def write(fn, y):
    with wave.open(fn, 'wb') as o:
        o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes((np.clip(y, -1, 1) * 32767).astype('<i2').tobytes())
def lufs(y):
    write('_tmp.wav', y)
    s = subprocess.run(['ffmpeg', '-hide_banner', '-i', '_tmp.wav', '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', s)[-1]), float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', s)[-1])
def limit(y, ceil_db=-2.2):
    c = 10 ** (ceil_db / 20); env = np.abs(y).max(1); la = int(0.004 * SR)
    pk = np.lib.stride_tricks.sliding_window_view(np.pad(env, (0, la)), la + 1).max(1)
    gr = np.minimum(1, c / np.maximum(pk, 1e-9)); out = np.empty_like(gr); cur = 1.0
    rel = np.exp(-1 / (0.08 * SR)); att = np.exp(-1 / (0.0015 * SR))
    for i in range(len(gr)):
        g = gr[i]; cur = att * cur + (1 - att) * g if g < cur else rel * cur + (1 - rel) * g; out[i] = cur
    return y * out[:, None]
I0, tp0 = lufs(x); print('sfx in', I0, tp0)
g = 10 ** ((-19.0 - I0) / 20)
for it in range(5):
    y = limit(x * g); I, tp = lufs(y); print(it, round(20 * np.log10(g), 2), I, tp)
    if abs(I + 19.0) < 0.15: break
    g *= 10 ** ((-19.0 - I) / 20)
write('audio_v6_nomusic.wav', y)
