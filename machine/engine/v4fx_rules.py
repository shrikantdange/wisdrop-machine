"""Free checks for the v4 fx (no image libraries). Used by craft_check.py."""
GLITCH_FRAMES = 8   # keep equal to v4fx.GLITCH_FRAMES
CRYPTO = ("crypto", "coin", "bitcoin", "blockchain", "token", "wallet", "mining")


def check(sh):
    res = []
    g = [s["at"] for s in sh if s.get("trans") == "glitch" and not (s.get("crypto") or any(w in str(s).lower() for w in CRYPTO))]
    res.append(("V1 glitch transition only on crypto moments", "FAIL" if g else "OK", f"lines {g[:8]}" if g else ""))
    res.append(("V2 glitch lasts 6-10 frames", "OK" if 6 <= GLITCH_FRAMES <= 10 else "FAIL", ""))
    prev = [None] + [s["type"] for s in sh[:-1]]
    lk = [s["at"] for s, p in zip(sh, prev) if s.get("trans") == "leak" and s["type"] != "chapter" and p != "chapter"]
    res.append(("V3 light-leak wipe only between parts (chapter card or the shot after it)", "FAIL" if lk else "OK", f"lines {lk[:8]}" if lk else ""))
    hn = [s["at"] for s in sh if s["type"] == "headlines" and not all(i.get("source") or s.get("source") for i in s.get("items", []))]
    hu = [s["at"] for s in sh if s["type"] == "headlines" and not all(i.get("outlet") and i.get("date") for i in s.get("items", []))]
    res.append(("V4 headline montage: real sourced headlines only (outlet, date, source)", "FAIL" if hn or hu else "OK", f"lines {(hn + hu)[:8]}" if hn or hu else ""))
    la = [s["at"] for s in sh if s["type"] == "lineart" and not (s.get("flashback") or "flashback" in str(s.get("label", "")).lower())]
    if la: res.append(("V5 line-art trace is for flashbacks (set flashback: true)", "REVIEW", f"lines {la[:8]}"))
    many = sum(1 for s in sh if s.get("trans") == "glitch")
    res.append(("V6 at most 4 glitch transitions per episode", "FAIL" if many > 4 else "OK", f"{many}"))
    return res
