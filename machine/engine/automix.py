"""Wisdrop automatic mix from shots.json: music per part, ambience per set, hits on actions and numbers.

  python automix.py <ep_dir> <work_dir>        (work_dir has vo.wav + timeline.json) -> work_dir/mix.wav

Same levels every episode: voice -17 dB RMS, music a static bed 22 dB under the voice (AMC-S3/S4, owner:
no pumping duck; any voice line < 8 dB over the bed is flagged), beds -44 dB, hits 9-12 dB under the voice
peak, master -14 LUFS / -2 dBTP. No coin/ding/cash sounds (AMC-S2, owner). Only kit/ sounds (CC0 / CC BY).
"""
import json, os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import motion as MO
SYNC = []

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE)); KIT = os.path.join(REPO, "kit")
SR = 48000
DEFAULT_MUSIC = ["Spy Glass", "Investigations", "Investigations", "Hitman", "Spy Glass", "Investigations"]
HITS = {"map": ("swipe", 13, .7), "phone": ("buzz", 14, .9), "pair": ("swipe", 15, .7), "trio": ("swipe", 15, .7), "wall": ("swipe", 15, .7),
        "polaroids": ("pageturn", 13, .5), "split": ("swipe", 12, .7), "magnify": ("swipe", 14, .7), "money": ("swipe", 14, .7),
        "scrub": ("swipe", 14, .7), "barrace": ("tick", 12, .3), "stamp": ("pageturn", 16, .5), "coin": ("tick", 14, .3),
        "stat": ("tick", 12, .3), "headline": ("pageturn", 12, .5), "card": ("pageturn", 12, .5), "chapter": ("impact", 9, 1.5),
        "name": ("swoosh", 12, .8), "timeline": ("swoosh", 13, .8), "bars": ("tick", 12, .3), "end": ("subdrop", 9, 1.2),
        "scene": ("paperslide", 14, .6), "photo": ("paperslide", 14, .6), "list": ("flick", 13, .2), "flow": ("flick", 13, .2)}


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
    shots = [s for s in SH["shots"] if s["at"] in ST]      # test runs voice only some lines
    def t_of(s): return (ST[s["at"]] + .04 + s.get("offset", 0)) if s is not shots[0] else 0.0
    # music: one track per part, parts split at chapter cards, 1.5 s crossfades
    cuts = [0.0] + [t_of(s) for s in shots if s["type"] == "chapter"] + [DUR]
    for k in range(len(cuts) - 1):
        a0, a1 = cuts[k], cuts[k + 1]
        if a1 - a0 < .5: continue
        trk = os.path.join(KIT, "music", music[min(k, len(music) - 1)] + ".mp3")
        m = load(trk, 4 if k == 0 else 0, a1 - a0 + 1.5, loop=True)
        if len(m) > 10: put(mus, max(0, a0 - .75), fade(norm(m, -17 - MO.MUSIC_UNDER_VOICE_DB), 1.5, 1.5))
    if act.any():   # trim the bed so it sits exactly MUSIC_UNDER_VOICE_DB under the voice while speaking (static, no duck)
        mus *= 10 ** ((rms_db(vo[act]) - MO.MUSIC_UNDER_VOICE_DB - rms_db(mus[act])) / 20)
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
        if n in MO.BANNED_SFX: print(f"REVIEW: sound '{n}' is banned (AMC-S2), skipped"); return
        p = os.path.join(KIT, "sfx", n + ".mp3")
        if not os.path.exists(p): return
        a = load(p, 0, dur)
        if len(a) < 10: return
        a = a * 10 ** ((VO_PK - under - 20 * np.log10(np.abs(a).max() + 1e-9)) / 20); pk = np.argmax(np.abs(a).mean(1)) / SR
        start = max(0, t - pk); SYNC.append(round((start + pk - t) * 30, 2))     # AMC-S5: hit lands on its frame
        put(fx, start, fade(a, .005, .3))
    last = {}
    def hit2(n, t, under, dur):          # S5: same sound never stacked closer than 0.12 s
        if t - last.get(n, -9) < .12: return
        last[n] = t; hit(n, t, under, dur)
    for k, s in enumerate(shots):
        t0, typ = times[k], s["type"]
        if s.get("quiet"): continue
        if typ == "phone":
            st_, n_ = s.get("step", .9), len(s.get("messages", [])) or len(s.get("notes", [])) or len(s.get("rows", []))
            for j in range(min(n_, 8)):
                tj = t0 + s.get("first", .5) + j * st_
                if tj < times[k + 1] - .1: hit2("pop" if s.get("app") in ("sms", "group", "whatsapp", "notify", "inbox") else "tick", tj, 15 if s.get("app") != "live" else 20, .6)
            if s.get("app") == "notify": hit2("buzz", t0 + s.get("first", .5), 13, .9)
        if typ in ("pair", "trio", "wall", "polaroids"):
            for j in range(len(s.get("photos", []))): hit2("shutter", t0 + j * s.get("step", .45) + .05, 14, .25); hit2("tape", t0 + j * s.get("step", .45) + .4, 17, .3)
        if typ == "map":
            for j, p in enumerate(s.get("pins", [])): hit2("pop", t0 + p.get("t", .2 + j * .6), 15, .2)
            if s.get("pins") and (s.get("flight") or s.get("route")): hit2("marker", t0 + s.get("route_at", .5), 17, .4)
        if typ == "money":
            for j, fl in enumerate(s.get("flows", [])): hit2("swish", t0 + 1.1 + j * .5, 17, .6)
            if s.get("counter"): hit2("tick", t0 + s["counter"].get("t", .8) + 1.6, 13, .3)
        if typ == "stamp": hit2("stamp", t0 + s.get("at_s", .3), 8, .4); hit2("impact", t0 + s.get("at_s", .3), 12, 1.2)
        if typ == "chapter": hit("rise", t0 - 2.0, 16, 2.0)          # riser ends exactly on the chapter card (J-cut)
        if typ == "card" and s.get("kind") in ("doc", "filing", "email"): hit2("typewriter", t0 + .8, 18, 1.0)
        for j, m in enumerate(s.get("marks", [])):
            tm = t0 + m.get("t", .9 + j * .8)
            if tm >= times[k + 1] - .05: continue
            hit2({"circle": "marker", "underline": "marker", "arrow": "swipe", "sticker": "pop", "emoji": "pop"}.get(m.get("k", "circle"), "pop"), tm, 15, .4)
        for j, _ in enumerate(s.get("stickers", [])): hit2("pop", t0 + .7 + j * .6, 16, .2)
        if s["type"] in HITS and not s.get("quiet"):
            n, under, dur = HITS[s["type"]]; hit(n, times[k] + .06, under, dur)
        if s["type"] in ("scene", "photo") and not s.get("bleed") and not s.get("quiet"): hit("tape", times[k] + .45, 16, .3)
        if s["type"] == "kinetic":
            hl = {w.upper().strip(".,!?") for w in s.get("hl", "").split()}
            stp = {w.upper() for w in s.get("stamp", [])}
            for j, w in enumerate(s["text"].split()):
                tw = times[k] + j * s.get("step", .28)
                if tw >= times[k + 1] - .05: break
                b = w.upper().strip(".,!?")
                hit2("stamp" if b in stp or w.upper() in stp else "marker" if b in hl else "pop", tw, 10 if b in stp else 12 if b in hl else 17, .4)
        for x in s.get("sfx", []): hit(x["n"], times[k] + x.get("off", 0), x.get("under", 10), x.get("dur", 1.2))
    # QC (S4/S7): voice must sit above music while speaking
    def rms(a): return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)
    margin = rms(vo[act]) - rms(mus[act]) if act.any() else 99
    low_lines = []
    for sg in TL["segs"]:              # AMC-S3: every voice line >= 8 dB over the bed
        a_, b_ = int(sg["start"] * SR), int(sg["end"] * SR)
        if b_ - a_ > SR // 4 and np.abs(mus[a_:b_]).max() > 0:
            m_ = rms(vo[a_:b_]) - rms(mus[a_:b_])
            if m_ < MO.VOICE_OVER_BED_MIN_DB: low_lines.append((sg["i"], round(float(m_), 1)))
    late = [x for x in SYNC if abs(x) > MO.SYNC_MAX_FRAMES]
    mix = vo + mus + fx
    pcm = (np.clip(mix / max(1, np.abs(mix).max() / .95), -1, 1) * 32767).astype(np.int16)
    raw = os.path.join(work, "mix_raw.wav")
    with wave.open(raw, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    subprocess.run([sys.executable, os.path.join(HERE, "master.py"), raw, os.path.join(work, "mix.wav")], check=True)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", os.path.join(work, "mix.wav"), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    import re as _re
    I = float(_re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]); TP = float(_re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
    lo, hi = MO.MUSIC_BAND_DB
    qc = {"lufs": I, "true_peak": TP, "voice_over_music_db": round(float(margin), 1), "lines_under_8db": low_lines,
          "sfx_off_by_frames_max": max([abs(x) for x in SYNC] + [0]), "sfx_count": len(SYNC),
          "ok": bool(abs(I + 14) <= 1.0 and TP <= -1.0 and margin >= lo and not late)}
    json.dump(qc, open(os.path.join(work, "audio_qc.json"), "w"))
    print(("OK" if qc["ok"] else "FAIL") + f" audio: {I} LUFS (target -14), true peak {TP} dBTP (max -1), voice {margin:.1f} dB over music (band {lo}-{hi}, target {MO.MUSIC_UNDER_VOICE_DB})")
    if not lo <= margin <= hi and act.any(): print(f"REVIEW: music {margin:.1f} dB under voice, outside {lo}-{hi} (AMC-S3)")
    if low_lines: print(f"REVIEW: voice lines under {MO.VOICE_OVER_BED_MIN_DB} dB over the bed (AMC-S3): {low_lines[:8]}")
    print(("OK" if not late else "FAIL") + f": {len(SYNC)} sounds land within {MO.SYNC_MAX_FRAMES} frames of their picture (AMC-S5)")
    print("OK mix", round(DUR, 1), "s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
