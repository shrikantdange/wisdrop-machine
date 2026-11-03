"""Make Wisdrop's own sound effects with code (CC0, ours). python tools/synth_sfx.py -> kit/sfx/*.mp3"""
import numpy as np, subprocess, os, wave
SR = 48000; R = np.random.default_rng(5); OUT = os.path.join(os.path.dirname(__file__), "..", "kit", "sfx")
def env(n, a=.004, d=.2):
    t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / d)
def lp(x, k):  # one-pole low-pass, k 0-1 (higher = darker)
    y = np.zeros_like(x); acc = 0.
    for i, v in enumerate(x): acc = acc * k + v * (1 - k); y[i] = acc
    return y
def hp(x, k): return x - lp(x, k)
def save(name, x):
    x = x / (np.abs(x).max() + 1e-9) * .9; x = np.stack([x, np.roll(x, 40)], 1)
    w = f"/tmp/{name}.wav"
    with wave.open(w, "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes((x * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", w, "-b:a", "160k", os.path.join(OUT, name + ".mp3")], check=True)
n = lambda s: int(SR * s); t = lambda s: np.arange(n(s)) / SR
# pop: pitched bubble with fast downward glide
f = 900 * np.exp(-t(.12) * 18) + 220; save("pop", np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n(.12), .002, .035))
# marker: felt-tip squeak-scrape, band-limited noise with wobble
x = hp(lp(R.normal(0, 1, n(.38)), .55), .97) * (1 + .4 * np.sin(2 * np.pi * 23 * t(.38))); save("marker", x * env(n(.38), .03, .25))
# tape: quick rip, bright noise with crackle
x = hp(R.normal(0, 1, n(.28)), .9) * (R.random(n(.28)) > .6); save("tape", lp(x, .2) * env(n(.28), .005, .12))
# paperslide: soft paper drag
x = lp(hp(R.normal(0, 1, n(.55)), .995), .6) * np.sin(np.pi * t(.55) / .55) ** 1.5; save("paperslide", x)
# stamp: low thump + click
x = np.sin(2 * np.pi * (70 + 60 * np.exp(-t(.35) * 30)) * t(.35)) * env(n(.35), .002, .09) + .5 * hp(R.normal(0, 1, n(.35)), .8) * env(n(.35), .001, .01)
save("stamp", x)
# flick: tiny card flip
x = hp(R.normal(0, 1, n(.09)), .95) * env(n(.09), .001, .02); save("flick", x)
print("OK sfx: pop marker tape paperslide stamp flick")
