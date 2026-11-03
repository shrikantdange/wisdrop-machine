"""Wisdrop mix TEMPLATE (example = Ep1 opening). usage: python mix_template.py <episode_dir>. Edit music per part, beds per set, hits per action/number."""
import os as _o, sys as _s; _R = _o.environ.get("WIS_REPO") or _o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "..")); _s.path.insert(0, _o.path.join(_R, "machine"))
from paths import KIT as _KIT, ENGINE as _ENG
import json, subprocess, wave
import numpy as np
import sys, os
EP = sys.argv[1]; TL = json.load(open(os.path.join(EP, 'timeline.json'))); DUR = TL['dur']; SR = 48000; N = int(DUR * SR)
ST = {s['i']: s['start'] for s in TL['segs']}; EN = {s['i']: s['end'] for s in TL['segs']}
KIT = _KIT
def S(n): return os.path.join(KIT, 'sfx', n + '.mp3')
def MU(n): return os.path.join(KIT, 'music', n + '.mp3')
def load(p, ss=0, t=None, af=None):
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(ss)] + (['-t', str(t)] if t else []) + ['-i', p] + (['-af', af] if af else []) + ['-ac', '2', '-ar', str(SR), '-f', 's16le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.int16).astype(float).reshape(-1, 2) / 32768
def rms_db(a): return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)
def norm(a, db): return a * 10 ** ((db - rms_db(a)) / 20)
def fade(a, fi=.02, fo=.3):
    i = min(int(fi * SR), len(a)); o = min(int(fo * SR), len(a))
    if i: a[:i] *= np.linspace(0, 1, i)[:, None]
    if o: a[-o:] *= np.linspace(1, 0, o)[:, None]
    return a
vo = load(os.path.join(EP, 'vo.wav'))[:N]; vo = np.pad(vo, ((0, N - len(vo)), (0, 0)))
act = np.zeros(N, bool)
for s in TL['segs']: act[int(s['start'] * SR):int(s['end'] * SR)] = True
VO_RMS = -17; vo = vo * 10 ** ((VO_RMS - rms_db(vo[act])) / 20); VO_PK = 20 * np.log10(np.abs(vo).max())
mus = np.zeros((N, 2)); fx = np.zeros((N, 2))
def put(buf, t, a):
    i = int(t * SR); m = min(len(a), N - i)
    if m > 0 and i >= 0: buf[i:i + m] += a[:m]
def bed(n, t0, t1, db, ss=0, af=None):
    a = load(S(n), ss, t1 - t0, af)
    if len(a) > 10: put(fx, t0, fade(norm(a, db), .4, .5))
def hit(n, t, under=9, ss=0, dur=1.2, fo=.3, peak=True):
    a = load(S(n), ss, dur)
    if len(a) < 10: return
    a = a * 10 ** ((VO_PK - under - 20 * np.log10(np.abs(a).max() + 1e-9)) / 20)
    if peak: t -= np.argmax(np.abs(a).mean(1)) / SR
    put(fx, max(0, t), fade(a, .005, fo))
# music: cold open = Spy Glass (tension/curious)
m = load(MU('Spy Glass'), 4, DUR); m = fade(norm(m, -31), .8, 1.5)
# 1 s near-silence before the act question
q = np.ones(len(m)); a0, a1 = int((ST[5] - 1.0) * SR), int((ST[5] - .1) * SR)
if a0 > 0: q[a0:a1] = .25; q = np.convolve(q, np.ones(int(.2 * SR)) / int(.2 * SR), 'same')
put(mus, 0, m * q[:, None])
g = np.where(act, 10 ** (-4 / 20), 1.0); k = int(.25 * SR); g = np.convolve(g, np.ones(k) / k, 'same'); mus *= g[:, None]
# beds
bed('city', 0, ST[2] - .1, -44, ss=30, af='lowpass=f=3000')
# hits: actions and numbers only
hit('darkhit', 0.08, under=8, dur=1.4, fo=.6)
hit('subdrop', ST[1] + .1, under=9, dur=1.2, fo=.5)
hit('tick', ST[2] + .06, under=12, dur=.3)
hit('swoosh', ST[3] + .04 + .55, under=12, dur=.8, fo=.3)
hit('paper', ST[4] + .06, under=12, dur=.9, peak=False)
mix = vo + mus + fx
print('levels dB  vo', round(rms_db(vo[act]), 1), ' music', round(rms_db(mus[act & (np.abs(mus).mean(1) > 0)]), 1), ' sfx peak', round(20 * np.log10(np.abs(fx).max() + 1e-9), 1), ' vo peak', round(VO_PK, 1))
pcm = (np.clip(mix / max(1, np.abs(mix).max() / .95), -1, 1) * 32767).astype(np.int16)
with wave.open(os.path.join(EP, 'mix_raw.wav'), 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
subprocess.run([sys.executable, _o.path.join(_ENG, 'master.py'), os.path.join(EP, 'mix_raw.wav'), os.path.join(EP, 'mix.wav')], check=True)
print('mix ok', DUR)
