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
# ---- v3 additions (each element type gets its own sound; docs/EDITING_CRAFT.md S6) ----
def bp(x, lo, hi): return lp(hp(x, lo), hi)
# swipe: band-passed noise swoosh, loudest at 60% (put the peak on the cut)
T = .7; e = np.sin(np.pi * np.clip(t(T) / T, 0, 1) ** 1.4) ** 2; save("swipe", bp(R.normal(0, 1, n(T)), .98, .35) * e)
# typewriter: 9 key clicks with a little body
x = np.zeros(n(1.2))
for k in range(9):
    i = n(.05 + k * .12 + R.uniform(-.02, .02)); c = hp(R.normal(0, 1, n(.03)), .7) * env(n(.03), .0005, .006) + .4 * np.sin(2 * np.pi * 900 * t(.03)) * env(n(.03), .001, .01)
    x[i:i + len(c)] += c
save("typewriter", x)
# ding: notification chime, two partials
x = (np.sin(2 * np.pi * 1318 * t(.9)) + .5 * np.sin(2 * np.pi * 1976 * t(.9))) * env(n(.9), .002, .25); save("ding", x)
# buzz: phone vibration, three pulses
x = np.zeros(n(.9))
for k in range(2):
    i = n(k * .4); seg = np.sign(np.sin(2 * np.pi * 160 * t(.28))) * .6 + .4 * np.sin(2 * np.pi * 320 * t(.28)); seg *= np.minimum(1, t(.28) / .02) * np.minimum(1, (.28 - t(.28)) / .03)
    x[i:i + len(seg)] += lp(seg, .5)
save("buzz", x)
# cash: register bell + drawer slide
x = (np.sin(2 * np.pi * 2093 * t(1.0)) + .6 * np.sin(2 * np.pi * 2637 * t(1.0))) * env(n(1.0), .002, .3); x[:n(.35)] += .5 * bp(R.normal(0, 1, n(.35)), .99, .5) * env(n(.35), .02, .2); save("cash", x)
# coindrop: metallic bounces
x = np.zeros(n(1.1))
for k, (dt, a) in enumerate([(0, 1), (.22, .6), (.38, .4), (.5, .25), (.58, .15)]):
    i = n(dt); c = a * sum(np.sin(2 * np.pi * f * t(.4)) for f in (3200, 4700, 6100)) * env(n(.4), .0005, .06); x[i:i + len(c)] += c
save("coindrop", x)
# shutter: camera click-clack
x = np.zeros(n(.25)); c = hp(R.normal(0, 1, n(.04)), .6) * env(n(.04), .0005, .008); x[:len(c)] += c; x[n(.09):n(.09) + len(c)] += .8 * c; save("shutter", x)
# rise: 2 s riser that stops dead (end it ON the reveal)
T = 2.0; f = 200 * (40 ** (t(T) / T)); x = bp(R.normal(0, 1, n(T)), .995, .2) * (t(T) / T) ** 2 + .3 * np.sin(2 * np.pi * np.cumsum(220 * 2 ** (t(T) / T)) / SR) * (t(T) / T) ** 2
x[-n(.004):] *= np.linspace(1, 0, n(.004)); save("rise", x)
# impact: sub drop + noise burst
x = np.sin(2 * np.pi * np.cumsum(40 + 80 * np.exp(-t(1.5) * 6)) / SR) * env(n(1.5), .002, .45) + .6 * hp(R.normal(0, 1, n(1.5)), .7) * env(n(1.5), .001, .03); save("impact", x)
# pageturn: paper flip
x = bp(R.normal(0, 1, n(.5)), .99, .3) * np.sin(np.pi * np.clip(t(.5) / .5, 0, 1)) ** 3 * (1 + .5 * np.sin(2 * np.pi * 13 * t(.5))); save("pageturn", x)
# room tone beds (20 s loops): quiet room and office hum
x = lp(R.normal(0, 1, n(20)), .97) * .6 + .05 * np.sin(2 * np.pi * 50 * t(20)); save("room_quiet", x)
x = lp(R.normal(0, 1, n(20)), .9) * .4 + .08 * (np.sin(2 * np.pi * 100 * t(20)) + .5 * np.sin(2 * np.pi * 150 * t(20))); save("room_office", x)
print("OK sfx: pop marker tape paperslide stamp flick swipe typewriter ding buzz cash coindrop shutter rise impact pageturn room_quiet room_office")
