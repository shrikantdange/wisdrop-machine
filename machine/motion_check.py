#!/usr/bin/env python3
"""Free motion-craft checks from docs/AI_MOTION_CRAFT.md (rule IDs AMC-*). No GPU, no render needed
for the spec part; the frame part reads a rendered video or a folder of PNG frames.

  python machine/motion_check.py <ep_dir>                     spec + code checks (run before any spend)
  python machine/motion_check.py <ep_dir> --video out.mp4     also checks frames of a rendered video

Prints OK / FAIL / REVIEW lines, writes <ep>/qa/motion.json, exits 1 on any FAIL.
FAIL = an owner-approved hard rule (punch-ins, headline size, nothing before the voice, banned sounds,
unseeded randomness, contrast, flashes). REVIEW = worth a look, never blocks.
"""
import ast, glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
import motion as MO

SIGNPOSTS = ["let's get into it", "let's get started", "in today's video", "don't forget to", "let's dive in", "without further ado"]
RES = []


def out(rule, status, detail=""):
    RES.append({"rule": rule, "status": status, "detail": detail})
    print(f"{status}: {rule}" + (f" ({detail})" if detail else ""), flush=True)


# ---------------- code lint (AMC-W1) ----------------
def lint_seeds():
    bad = []
    for f in sorted(glob.glob(os.path.join(HERE, "engine", "*.py"))):
        if os.path.basename(f) in ("vo_runner.py", "whisper_words.py", "motion.py"): continue
        tree = ast.parse(open(f).read())
        for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.Lambda))]:
            for c in [n for n in ast.walk(fn) if isinstance(n, ast.Call)]:
                src = ast.unparse(c.func)
                if src in ("random.random", "random.uniform", "random.randint", "random.choice", "random.shuffle", "time.time", "hash") \
                        or (src.startswith("np.random.") and not src.startswith("np.random.default_rng")) \
                        or (src == "np.random.default_rng" and not c.args):
                    bad.append(f"{os.path.basename(f)}:{c.lineno} {src}")
    out("AMC-W1 no unseeded randomness, wall clock or hash() in render code", "FAIL" if bad else "OK", ", ".join(sorted(set(bad))[:6]))


def theme_contrast():
    try:
        import v3kit as V
    except Exception as e:
        out("AMC-C3 board text contrast", "REVIEW", f"could not load boards: {e}"); return
    low, large_only = [], []
    for th in V.THEMES:
        for role in ("ink", "sub"):
            c = MO.contrast(th[role], th["bg"])
            if c < MO.CONTRAST_BODY: low.append(f"{th['name']} {role} {c:.1f}:1")
        c = MO.contrast(th["acc"], th["bg"])
        if c < MO.CONTRAST_LARGE: low.append(f"{th['name']} accent {c:.1f}:1")
        elif c < MO.CONTRAST_BODY: large_only.append(f"{th['name']} {c:.1f}:1")
    out("AMC-C3 text >= 4.5:1 on every board (accent >= 3:1, large type only)", "FAIL" if low else "OK", ", ".join(low))
    if large_only: out("AMC-C3 accent colour as text only at >= 76 px on these boards", "REVIEW", ", ".join(large_only))


# ---------------- shots.json + lines.json ----------------
def spec(ep):
    sh = json.load(open(os.path.join(ep, "shots.json")))["shots"]
    lines = {L["id"]: L for L in json.load(open(os.path.join(ep, "lines.json")))}
    # owner: punch-in only on stamps
    p = [s["at"] for s in sh if s.get("punch") and s["type"] != "stamp"]
    out("AMC-V3 punch-in only on stamps (owner)", "FAIL" if p else "OK", f"lines {p[:8]}" if p else "")
    # owner: headline >= 76 px
    small = [s["at"] for s in sh if s["type"] in ("kinetic", "chapter", "stat") and s.get("size") and s["size"] < MO.HEADLINE_MIN_PX]
    out(f"AMC-L2 headline type >= {MO.HEADLINE_MIN_PX} px (owner)", "FAIL" if small else "OK", f"lines {small[:8]}" if small else "")
    # nothing before the voice names it
    early = [s["at"] for s in sh if s.get("offset", 0) < 0]
    out("AMC-N4 nothing appears before the voice names it (no negative offsets)", "FAIL" if early else "OK", f"lines {early[:8]}" if early else "")
    # banned sounds
    snd = [f"{s['at']}:{x['n']}" for s in sh for x in s.get("sfx", []) if x.get("n") in MO.BANNED_SFX]
    out("AMC-S2 no coin / ding / cash sounds (owner)", "FAIL" if snd else "OK", ", ".join(snd[:8]))
    # maps show change
    still = [s["at"] for s in sh if s["type"] == "map" and not (s.get("route") or s.get("flight") or s.get("fill") or s.get("flows")
                                                                  or len(s.get("pins", [])) > 1 or s.get("date"))]
    out("AMC-E1 every map shows a change (route, flight, fill, date or 2+ pins)", "REVIEW" if still else "OK", f"lines {still[:8]}" if still else "")
    flights = [b["at"] for a, b in zip(sh, sh[1:]) if a["type"] == b["type"] == "map" and (a.get("flight") and b.get("flight"))]
    if flights: out("AMC-V4 never two map flights in a row", "REVIEW", f"lines {flights[:6]}")
    snaps = sum(1 for s in sh if s["type"] == "stamp")
    out("AMC-E8 snap beats (stamps) <= 3 per episode", "REVIEW" if snaps > 3 else "OK", f"{snaps} stamps")
    # stagger cap (kinetic word steps)
    stag = [s["at"] for s in sh if s["type"] == "kinetic" and s.get("step", .28) > .6]
    if stag: out("AMC-M5 word stagger <= 0.6 s per word", "REVIEW", f"lines {stag[:6]}")
    # narration: signposts, long sentences on one picture, pause after a question
    sp = [i for i, L in lines.items() if any(x in L["text"].lower() for x in SIGNPOSTS)]
    out("AMC-H3 no signpost phrases", "REVIEW" if sp else "OK", f"lines {sp[:8]}" if sp else "")
    per_line = {}
    for s in sh: per_line[s["at"]] = per_line.get(s["at"], 0) + 1
    longp = [i for i, L in lines.items() if len(L["text"].split()) > 20 and per_line.get(i, 0) < 2]
    out("AMC-N2 sentence > 20 words gets two pictures", "REVIEW" if longp else "OK", f"lines {longp[:10]}" if longp else "")
    qs = [i for i, L in lines.items() if L["text"].strip().endswith("?") and L.get("gap", .3) < .5 and i + 1 in lines]
    out("AMC-N3 0.5 s pause after a question", "REVIEW" if qs else "OK", f"lines {qs[:8]} (set gap >= 0.5)" if qs else "")


# ---------------- rendered frames ----------------
def frames(video, ep):
    import numpy as np
    from PIL import Image
    tmp = os.path.join(ep, "qa", "motion_frames"); os.makedirs(tmp, exist_ok=True)
    for f in glob.glob(os.path.join(tmp, "*.png")): os.remove(f)
    subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", "fps=10,scale=480:270", os.path.join(tmp, "f%05d.png")], check=True)
    fs = sorted(glob.glob(os.path.join(tmp, "*.png")))
    if not fs: out("frames", "FAIL", "no frames decoded"); return
    import v3kit as V
    acc = np.array([V.YEL, V.RED] + [th["acc"] for th in V.THEMES], float)
    lum_prev, flashes, acc_hi, bw = None, [], [], []
    for k, f in enumerate(fs):
        a = np.asarray(Image.open(f).convert("RGB")).astype(float)
        d = np.min(np.linalg.norm(a[:, :, None, :] - acc[None, None], axis=3), axis=2)
        share = float((d < 40).mean())
        if share > MO.ACCENT_MAX: acc_hi.append((round(k / 10, 1), round(share * 100)))
        l = (0.2126 * (a[..., 0] / 255) ** 2.2 + 0.7152 * (a[..., 1] / 255) ** 2.2 + 0.0722 * (a[..., 2] / 255) ** 2.2)
        y = a.mean(2)
        if ((y <= 1) | (y >= 254)).mean() > .2: bw.append(round(k / 10, 1))
        if lum_prev is not None and (np.abs(l - lum_prev) >= .1).mean() >= .25: flashes.append(k / 10)
        lum_prev = l
        if k == 0:
            out("AMC-H1 frame 0 is a picture, not black or flat", "FAIL" if y.std() < 6 or y.mean() < 8 else "OK", f"mean {y.mean():.0f}, spread {y.std():.0f}")
    burst = max([sum(1 for x in flashes if t <= x < t + 1) for t in flashes] + [0])
    out("AMC-M10 at most 3 flashes in any second", "FAIL" if burst > 3 else "OK", f"max {burst}/s")
    out(f"AMC-C2 accent colour on <= {int(MO.ACCENT_MAX * 100)} % of the frame", "REVIEW" if acc_hi else "OK",
        f"{len(acc_hi)} of {len(fs)} sampled frames over, e.g. {acc_hi[:4]} (s, %)" if acc_hi else f"{len(fs)} frames sampled")
    out("AMC-C4 no large pure black / white areas", "REVIEW" if bw else "OK", f"at {bw[:6]} s" if bw else "")


def main(ep, video=None):
    lint_seeds(); theme_contrast(); spec(ep)
    if video: frames(video, ep)
    os.makedirs(os.path.join(ep, "qa"), exist_ok=True)
    json.dump(RES, open(os.path.join(ep, "qa", "motion.json"), "w"), indent=1)
    fails = [r for r in RES if r["status"] == "FAIL"]; rev = [r for r in RES if r["status"] == "REVIEW"]
    print(f"{'FAIL' if fails else 'OK'}: motion checks, {len(fails)} fail, {len(rev)} for review")
    return 1 if fails else 0


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    v = sys.argv[sys.argv.index("--video") + 1] if "--video" in sys.argv else None
    a = [x for x in a if x != v]
    sys.exit(main(a[0], v))
