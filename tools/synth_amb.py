"""v5 ambience + scene sounds, made by code (CC0, ours). python tools/synth_amb.py -> kit/sfx/amb_*.mp3
amb_airport (hall hum + far PA murmur), amb_room (quiet room tone), amb_crowd (crowd murmur),
amb_wind (fog wind), amb_printer (printer whirr), amb_click (camera shutter click), amb_flaps (split-flap clatter)."""
import numpy as np, subprocess, os, wave
SR = 48000; OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit", "sfx")
R = np.random.default_rng(55)
def n(s): return int(SR * s)
def t(s): return np.arange(n(s)) / SR
def lp(x, a):   # fast one-pole low-pass via cumulative filter (scipy-free)
    y = np.empty_like(x); acc = 0.0
    for i in range(0, len(x), 4800):
        seg = x[i:i + 4800]; out = np.empty_like(seg)
        for j, v in enumerate(seg): acc = acc * a + v * (1 - a); out[j] = acc
        y[i:i + 4800] = out
    return y
def hp(x, a): return x - lp(x, a)
def save(name, x, stereo_shift=60):
    x = x / (np.abs(x).max() + 1e-9) * .9; x = np.stack([x, np.roll(x, stereo_shift)], 1); w = f"/tmp/{name}.wav"
    with wave.open(w, "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes((x * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", w, "-b:a", "128k", os.path.join(OUT, name + ".mp3")], check=True)
L = 12.0
# airport: low HVAC hum + band noise + soft unintelligible PA formant blobs
x = .5 * np.sin(2 * np.pi * 60 * t(L)) * .1 + lp(R.normal(0, 1, n(L)), .985) * 3 + .15 * hp(lp(R.normal(0, 1, n(L)), .9), .99)
pa = np.zeros(n(L))
for k in range(6):
    s0 = int(R.uniform(0, L - 1.5) * SR); d = n(R.uniform(.6, 1.4)); f0 = R.uniform(180, 260)
    env = np.sin(np.pi * np.arange(d) / d) ** 2 * (1 + .5 * np.sin(2 * np.pi * 5 * np.arange(d) / SR))
    pa[s0:s0 + d] += np.sin(2 * np.pi * f0 * np.arange(d) / SR) * env * .08
save("amb_airport", x + lp(pa, .7))
save("amb_room", lp(R.normal(0, 1, n(L)), .992) * 2 + .05 * hp(lp(R.normal(0, 1, n(L)), .8), .995))
cr = np.zeros(n(L))
for k in range(40):   # many soft voice-like blobs = murmur (no words)
    s0 = int(R.uniform(0, L - 1) * SR); d = n(R.uniform(.3, .9)); f0 = R.uniform(110, 240)
    env = np.sin(np.pi * np.arange(d) / d) ** 2; ph = 2 * np.pi * np.cumsum(f0 * (1 + .06 * np.sin(2 * np.pi * 4 * np.arange(d) / SR))) / SR
    cr[s0:s0 + d] += (np.sin(ph) + .5 * np.sin(2 * ph) + .25 * np.sin(3 * ph)) * env
save("amb_crowd", lp(cr, .8) + .6 * lp(R.normal(0, 1, n(L)), .97))
w = lp(R.normal(0, 1, n(L)), .995) * (1 + .6 * np.sin(2 * np.pi * .15 * t(L))) * 3; save("amb_wind", w)
T = 2.2; m = np.sin(2 * np.pi * 38 * t(T)) * .4 + hp(R.normal(0, 1, n(T)), .6) * .25 * (1 + np.sign(np.sin(2 * np.pi * 11 * t(T)))) * .5
save("amb_printer", m * np.minimum(1, t(T) / .05) * np.minimum(1, (T - t(T)) / .1))
T = .25; c = hp(R.normal(0, 1, n(T)), .7) * np.exp(-t(T) / .008); c[n(.07):] += hp(R.normal(0, 1, n(T) - n(.07)), .7) * np.exp(-t(T - .07) / .01) * .7
save("amb_click", c)
T = 1.6; fl = np.zeros(n(T))
for k in range(60):
    s0 = int(R.uniform(0, T - .02) * SR); d = n(.012); fl[s0:s0 + d] += hp(R.normal(0, 1, d), .5) * np.exp(-np.arange(d) / (SR * .003))
save("amb_flaps", fl * np.minimum(1, (T - t(T)) / .4))
print("OK amb: airport room crowd wind printer click flaps")
