#!/usr/bin/env python3
"""Free editing-craft checks (docs/EDITING_CRAFT.md), run before any GPU or render spend.

  python machine/craft_check.py <ep_dir> [timeline.json] [--upto SECONDS]

Without a timeline the line times are estimated from lines.json (words at 2.6 words/s plus gaps).
Prints OK / FAIL / REVIEW lines, writes <ep>/qa/craft.json, exits 1 on any FAIL.
REVIEW = a human (owner) decision, never blocks (e.g. the hook question needs a script change).
"""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
import shotspec as SS

LEAD = 0.04; LEAD_IN = 0.4; WPS = 2.6


def timeline(ep, tl_path=None):
    lines = json.load(open(os.path.join(ep, "lines.json")))
    if tl_path and os.path.exists(tl_path):
        tl = json.load(open(tl_path)); return {s["i"]: s["start"] for s in tl["segs"]}, tl["dur"], lines, True
    st, cur = {}, LEAD_IN
    for L in lines:
        st[L["id"]] = round(cur, 3); cur += len(L["text"].split()) / WPS + L.get("gap", .3)
    return st, cur + 1.5, lines, False


def main(ep, tl_path=None, upto=None):
    ST, DUR, lines, real = timeline(ep, tl_path)
    sh = json.load(open(os.path.join(ep, "shots.json")))["shots"]
    sh = [s for s in sh if s["at"] in ST]
    starts = [0.0] + [ST[s["at"]] + LEAD + s.get("offset", 0) for s in sh[1:]]
    end = min(DUR, upto) if upto else max(ST[max(ST)] + 6, starts[-1] + 3) if not real else DUR
    if upto: sh = [s for s, t in zip(sh, starts) if t < upto]; starts = starts[:len(sh)]
    durs = [b - a for a, b in zip(starts, starts[1:] + [end])]
    res = []
    def out(rule, status, detail=""):
        detail = detail if status != "OK" or "first" in detail or "distinct" in detail else ""
        res.append({"rule": rule, "status": status, "detail": detail}); print(f"{status}: {rule}" + (f" ({detail})" if detail else ""), flush=True)
    print(f"PLAN {len(sh)} shots over {end:.1f} s ({'measured' if real else 'estimated'} timeline)")

    # P1 dead frames
    long_static = [(s["at"], round(SS.max_gap(s, d), 2)) for s, d in zip(sh, durs) if SS.max_gap(s, d) > SS.MAX_HOLD]
    out("P1 nothing holds still > 2.5 s", "FAIL" if long_static else "OK", f"shots at lines {long_static[:6]}" if long_static else "")
    heavy = [s["at"] for s, d in zip(sh, durs) if len(SS.accents(s, d)) > 2]
    if heavy: out("P1b shots needing >2 automatic accents (split them or add marks)", "REVIEW", f"lines {heavy[:8]}")
    # P2 first minute: a visual change every <= 3 s (cuts + element events)
    ev = sorted({round(t + e, 2) for s, t, d in zip(sh, starts, durs) for e in (SS.events(s, d) if s["type"] not in SS.CONTINUOUS else [x * .5 for x in range(int(d * 2) + 1)])} | {round(t, 2) for t in starts})
    ev = [e for e in ev if e < min(60, end)] + [min(60, end)]
    gaps = [(round(a, 1), round(b - a, 1)) for a, b in zip(ev, ev[1:]) if b - a > 3.0]
    out("P2 first minute changes every <= 3 s", "FAIL" if gaps else "OK", f"gaps at {gaps[:5]}" if gaps else "")
    short = [s["at"] for s, d in zip(sh, durs) if d < 0.8 and s["type"] not in ("kinetic",)]
    out("T1 every shot >= 0.8 s", "FAIL" if short else "OK", f"lines {short[:8]}" if short else "")
    # H1 / H2 hook
    first_strike = next((t for s, t in zip(sh, starts) if s["type"] in SS.STRIKING or s.get("striking")), 99)
    out("H1 shock fact or striking visual inside 5 s", "OK" if first_strike <= 5 else "FAIL", f"first at {first_strike:.1f} s")
    q = next((ST[L["id"]] for L in lines if L.get("preset") == "question" or L["text"].strip().endswith("?")), 99)
    out("H2 question by 8 s", "OK" if q <= 8 else "REVIEW", f"first question at {q:.1f} s; script change needs owner approval, see hooks.md" if q > 8 else "")
    # P4 same type 3x in a row
    run = [sh[k]["at"] for k in range(2, len(sh)) if sh[k]["type"] == sh[k - 1]["type"] == sh[k - 2]["type"] and sh[k]["type"] != "kinetic"]
    out("P4 never the same shot type 3 times in a row", "FAIL" if run else "OK", f"at lines {run[:6]}" if run else "")
    # no repeats, AI picture budget, lone pictures
    seen, rep = {}, []
    for s in sh:
        for k in SS.media_keys(s):
            if k in seen and s["type"] != "scene": rep.append(k)
            seen[k] = 1
    out("No photo repeated in an episode", "FAIL" if rep else "OK", ", ".join(rep[:5]))
    ai = {k for s in sh if s["type"] in SS.AI_PICTURE for k in SS.media_keys(s)}
    out("AI pictures <= 6 per episode", "FAIL" if len(ai) > 6 else "OK", f"{len(ai)} distinct")
    lone = [s["at"] for s in sh if s["type"] in ("photo", "scene") and not (s.get("marks") or s.get("label") or s.get("stickers"))]
    out("No lone picture without surround motion (label, marks or stickers)", "FAIL" if lone else "OK", f"lines {lone[:8]}")
    # numbers on screen need a source
    def has_num(s):
        if s["type"] in ("stat", "bars", "barrace", "chart3d"): return True
        if s["type"] == "chart" and not s.get("illustrative", True): return True
        if s["type"] == "money" and (s.get("counter") or any(re.search(r"\d", f.get("label", "")) for f in s.get("flows", []))): return True
        if s["type"] == "phone" and s.get("app") in ("bank", "ticker") and not s.get("illustrative"): return True
        txt = " ".join(str(s.get(k, "")) for k in ("text", "label", "title", "sub"))
        return bool(re.search(r"\d[\d,.]*\s*(%|M|B|K|million|billion|bn)|[$€£]\s*\d", txt))
    nos = [s["at"] for s in sh if has_num(s) and not s.get("source")]
    out("Every number on screen has a source", "FAIL" if nos else "OK", f"lines {nos[:8]}")
    # captions never overlap cards; text volume
    low = [s["at"] for s in sh if float(s.get("y", .4)) > .78 or any(max(m.get("y", 0), m.get("y0", 0), m.get("y1", 0)) > .8 for m in s.get("marks", []))]
    out("T6 nothing placed in the caption band", "FAIL" if low else "OK", f"lines {low[:8]}")
    wordy = [s["at"] for s in sh if s["type"] in ("kinetic", "stamp") and len(s.get("text", "")) > 90]
    out("T2 kinetic text short (<= 90 characters)", "FAIL" if wordy else "OK", f"lines {wordy[:8]}")
    slow = []
    for s, d in zip(sh, durs):
        if s["type"] in ("card", "headline"):
            chars = len(" ".join(s.get("lines", [])) + s.get("title", "") + s.get("sub", ""))
            if chars / 13 > d + 1.5: slow.append(s["at"])
    out("T1 cards stay long enough to read (13 chars/s)", "REVIEW" if slow else "OK", f"lines {slow[:8]}" if slow else "")
    # every line covered from its own start (visuals never before the voice)
    # v4 fx rules (docs/SHOTS.md T21-T27)
    import v4fx_rules as VR
    for rule, status, detail in VR.check(sh): out(rule, status, detail)
    out("Loudness -14 LUFS / -2 dBTP, voice above music", "PLAN", "measured on the mix after render (automix prints it)")
    os.makedirs(os.path.join(ep, "qa"), exist_ok=True)
    json.dump(res, open(os.path.join(ep, "qa", "craft.json"), "w"), indent=1)
    fails = [r for r in res if r["status"] == "FAIL"]; rev = [r for r in res if r["status"] == "REVIEW"]
    print(f"{'FAIL' if fails else 'OK'}: craft checks, {len(fails)} fail, {len(rev)} for review")
    return 1 if fails else 0


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    up = float(sys.argv[sys.argv.index("--upto") + 1]) if "--upto" in sys.argv else None
    if up is not None: a = [x for x in a if x != str(sys.argv[sys.argv.index("--upto") + 1])]
    sys.exit(main(a[0], a[1] if len(a) > 1 else None, up))
