import librosa, numpy as np, json
S0, DUR = 109.050, 25.0
y, sr = librosa.load('music_full.wav', sr=22050, mono=True, offset=S0 - 6, duration=DUR + 12)
oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=128)
tempo, beats = librosa.beat.beat_track(onset_envelope=oenv, sr=sr, hop_length=128, start_bpm=134.6, tightness=300)
bt = librosa.frames_to_time(beats, sr=sr, hop_length=128) + (S0 - 6)
bt = bt[(bt > S0 - 0.2) & (bt < S0 + DUR + 0.3)]
n = np.round((bt - bt[0]) / 0.4456)
p = np.polyfit(n, bt, 1)
grid = np.polyval(p, np.arange(0, int(n.max()) + 1))
res = bt - np.polyval(p, n)
# downbeat phase: strongest low-band onset energy among 4 phases
yl = librosa.effects.preemphasis(y, coef=-0.97)
oenv_l = librosa.onset.onset_strength(y=y, sr=sr, hop_length=128, fmax=200, n_mels=32)
tt = librosa.times_like(oenv_l, sr=sr, hop_length=128) + (S0 - 6)
sc = [np.mean([oenv_l[np.argmin(abs(tt - g))] for g in grid[ph::4]]) for ph in range(4)]
print('detected', len(bt), 'beats; period', p[0], 'bpm', 60 / p[0], 'max resid ms', 1000 * abs(res).max(), 'phase scores', np.round(sc, 3))
vt = grid - S0
import sys
ph = int(np.argmax(sc)); print('downbeat phase', ph)
keep = vt > -0.01
vt = vt[keep]; ph = (ph - int((~keep).sum())) % 4
json.dump(dict(S0=S0, DUR=DUR, period=p[0], downbeat_phase=ph, beats=[round(float(x), 4) for x in vt], detected=[round(float(x - S0), 4) for x in bt]), open('beats5.json', 'w'))
print('video beat times:', np.round(vt, 3))
