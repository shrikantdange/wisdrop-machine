"""Wisdrop automatic mix from shots.json: music per part, ambience per set, hits on actions and numbers.

  python automix.py <ep_dir> <work_dir>        (work_dir has vo.wav + timeline.json) -> work_dir/mix.wav

Same levels every episode: voice -17 dB RMS, music -31 dB ducked 4 dB under voice, beds -44 dB,
hits 9-12 dB under the voice peak, master -14 LUFS / -2 dBTP. Only kit/ sounds (CC0 / CC BY).
"""
import json, os, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE)); KIT = os.path.join(REPO, "kit")
SR = 48000
DEFAULT_MUSIC = ["Spy Glass", "Investigations", "Investigations", "Hitman", "Spy Glass", "Investigations"]
HITS = {"stat": ("tick", 12, .3), "headline": ("paper", 12, .9), "card": ("paper", 12, .9), "chapter": ("darkhit", 8, 1.4),
        "name": ("swoosh", 12, .8), "timeline": ("swoosh", 13, .8), "bars": ("tick", 12, .3), "end": ("subdrop", 9, 1.2)}


def load(p, ss=0, t=None, loop=False):
    cmd = ["ffmpeg", "-v", "error"] + (["-stream_loop", "-1"] if loop else []) + ["-ss", str(ss)] + (["-t", str(t)] if t else []) + ["-i", p, "-ac", "2", "-ar", str(SR), "-f", "s16le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.int16).astype(float).reshape(-1, 2) / 32768
def rms_db(a): return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)
def norm(a, db): return a * 10 ** ((db - rms_db(a)) / 20)
def fade(a, fi=.02, fo=.3):
    i = min(int(fi * SR), len(a)); o = min(int(fo * SR), len(a))
    if i: a[:i] *= np.linspace(0, 1, i)[:, None]
    if o: a[-o:] *= np.linspace(1, 0, o)[:, None]
    return a


def main(ep, work):
    TL = json.load(open(os.path.join(work, "timeline.json"))); DUR = TL["dur"]; N = int(DUR * SR)
    ST = {s["i"]: s["start"] for s in TL["segs"]}
    SH = json.load(open(os.path.join(ep, "shots.json"))); lib = json.load(open(os.path.join(REPO, "library", "library.json")))
    music = SH.get("music") or DEFAULT_MUSIC
    vo = load(os.path.join(work, "vo.wav"))[:N]; vo = np.pad(vo, ((0, N - len(vo)), (0, 0)))
    act = np.zeros(N, bool)
    for s in TL["segs"]: act[int(s["start"] * SR):int(s["end"] * SR)] = True
    vo = vo * 10 ** ((-17 - rms_db(vo[act])) / 20); VO_PK = 20 * np.log10(np.abs(vo).max() + 1e-9)
    mus = np.zeros((N, 2)); fx = np.zeros((N, 2))
    def put(buf, t, a):
        i = int(t * SR); m = min(len(a), N - i)
        if m > 0 and i >= 0: buf[i:i + m] += a[:m]
    def t_of(s): return (ST.get(s["at"], 0) + .04 + s.get("offset", 0)) if s is not SH["shots"][0] else 0.0
    shots = SH["shots"]
    # music: one track per part, parts split at chapter cards, 1.5 s crossfades
    cuts = [0.0] + [t_of(s) for s in shots if s["type"] == "chapter"] + [DUR]
    for k in range(len(cuts) - 1):
        a0, a1 = cuts[k], cuts[k + 1]
        if a1 - a0 < .5: continue
        trk = os.path.join(KIT, "music", music[min(k, len(music) - 1)] + ".mp3")
        m = load(trk, 4 if k == 0 else 0, a1 - a0 + 1.5, loop=True)
        if len(m) > 10: put(mus, max(0, a0 - .75), fade(norm(m, -31), 1.5, 1.5))
    g = np.where(act, 10 ** (-4 / 20), 1.0); kk = int(.25 * SR); g = np.convolve(g, np.ones(kk) / kk, "same"); mus *= g[:, None]
    # beds: ambience of each scene's set, for as long as consecutive shots stay on that set
    times = [t_of(s) for s in shots] + [DUR]
    for k, s in enumerate(shots):
        if s["type"] != "scene": continue
        bed = lib["sets"].get(s.get("set", ""), {}).get("bed", "")
        if not bed or times[k + 1] - times[k] < .5: continue
        a = load(os.path.join(KIT, "sfx", bed + ".mp3"), (k * 7.3) % 20, times[k + 1] - times[k], loop=True)
        if len(a) > 10: put(fx, times[k], fade(norm(a, -44), .4, .5))
    # hits: by shot type, plus any explicit "sfx": [{"n": "coins", "off": 0.3}]
    def hit(n, t, under, dur):
        p = os.path.join(KIT, "sfx", n + ".mp3")
        if not os.path.exists(p): return
        a = load(p, 0, dur)
        if len(a) < 10: return
        a = a * 10 ** ((VO_PK - under - 20 * np.log10(np.abs(a).max() + 1e-9)) / 20); t -= np.argmax(np.abs(a).mean(1)) / SR
        put(fx, max(0, t), fade(a, .005, .3))
    for k, s in enumerate(shots):
        if s["type"] in HITS and not s.get("quiet"):
            n, under, dur = HITS[s["type"]]; hit(n, times[k] + .06, under, dur)
        for x in s.get("sfx", []): hit(x["n"], times[k] + x.get("off", 0), x.get("under", 10), x.get("dur", 1.2))
    mix = vo + mus + fx
    pcm = (np.clip(mix / max(1, np.abs(mix).max() / .95), -1, 1) * 32767).astype(np.int16)
    raw = os.path.join(work, "mix_raw.wav")
    with wave.open(raw, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    subprocess.run([sys.executable, os.path.join(HERE, "master.py"), raw, os.path.join(work, "mix.wav")], check=True)
    print("OK mix", round(DUR, 1), "s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
