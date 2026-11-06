#!/usr/bin/env python3
"""FM-* checks from docs/FAILURE_MODES.md (free, CPU, no network). Run before any spend.

  python machine/fm_check.py <ep_dir>

Prints OK / FAIL / REVIEW / TODO lines, writes <ep>/qa/fm.json, exits 1 on any FAIL.
Implemented: R01 R02 R12 W02 W03 W04 W05 W08 L15 P04 C05 C08 X12 X14 K05.
Every other [CODE-TODO] rule in FAILURE_MODES.md is listed as a TODO stub below (cheap to add later).
"""
import json, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODO = ["R04 status-check date", "R06 recompute formulas", "R07 currency vs F-row", "R08 dates vs timeline",
        "R10 dead URLs (--net)", "L01 guilt words w/o attribution", "L04 stamp text vs banned list",
        "P01 template/music sameness vs last ep", "P03 AI disclosure flag", "P06 media without credits",
        "P07 TASL fields", "S02 twist near 40%", "S03 loops opened vs closed", "S05 named people <= 5",
        "S06 F-id overuse", "S13 runtime band", "W01 names without say", "V02 per-line LUFS spread",
        "V04 voice ref hash", "V05 wpm band", "G02 media reuse across chapters", "G08 recreation tags",
        "G09 ISO-3 + lat/lon", "G10 invented clock times", "G15 safe area", "A04 seam loudness",
        "A07 ambience across chapter card", "A08 silence holes", "A09 bed shorter than part",
        "C01 counter monotonic", "C02 colour change off chapter card", "C03 cast prompt stem",
        "C04 name/role label", "X04 render length", "X05 A/V drift", "X06 format", "X07 glyph coverage",
        "X13 big tracked files", "K03 title/thumb overlap", "K04 description completeness"]
SECRET = re.compile(r"(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|\bak-[A-Za-z0-9]{16,}|\bas-[A-Za-z0-9]{16,}|"
                    r"sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
BANNED_OPEN = ("let's get into it", "in this video", "welcome back", "hey guys", "what's up")
ADVICE = re.compile(r"\byou should (invest|buy|sell)\b", re.I)
NUMWORD = re.compile(r"\b(\d|one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|billion|percent)\b", re.I)


def main(ep):
    res = []
    def out(rid, st, msg): res.append({"id": "FM-" + rid, "status": st, "msg": msg}); print(f"{st} FM-{rid} {msg}")
    lines = json.load(open(os.path.join(ep, "lines.json")))
    sj = json.load(open(os.path.join(ep, "shots.json"))); shots = sj.get("shots", [])
    rs = open(os.path.join(ep, "research.md")).read() if os.path.exists(os.path.join(ep, "research.md")) else ""
    rows = {m.group(1): m.group(0) for m in re.finditer(r"^\|\s*(F\d+)\s*\|.*$", rs, re.M)}
    # R01: lines with numbers need src, and every src F-id must exist
    bad = [L["id"] for L in lines if NUMWORD.search(L["text"]) and str(L.get("src", "")).strip().lower() in ("", "none")]
    miss = sorted({f for L in lines for f in re.findall(r"F\d+", str(L.get("src", ""))) if f not in rows})
    out("R01", "FAIL" if miss else ("REVIEW" if bad else "OK"), f"unknown F-ids {miss}; number-like lines without src {bad[:12]}")
    # R02/R12: key rows need two URLs, no wikipedia
    one = [f for f, r in rows.items() if re.search(r"\|\s*yes\s*\|\s*$", r) and len(re.findall(r"https?://", r)) < 2]
    wik = [f for f, r in rows.items() if re.search(r"\|\s*yes\s*\|\s*$", r) and "wikipedia.org" in r]
    out("R02", "FAIL" if one else "OK", f"key rows with < 2 URLs: {one}")
    out("R12", "FAIL" if wik else "OK", f"key rows citing Wikipedia: {wik}")
    # W02-W05, W08, L15: script text for TTS
    dig = [L["id"] for L in lines if re.search(r"[\d$%€£]", L["text"]) and not L.get("say")]
    out("W02", "FAIL" if dig else "OK", f"digits/symbols in text without say: {dig[:12]}")
    lng = [L["id"] for L in lines if len(L["text"].split()) > 20]
    out("W03", "REVIEW" if lng else "OK", f"lines over 20 words: {lng[:12]}")
    q = [L["id"] for L in lines if L["text"].rstrip().endswith("?") and L.get("gap", 0) < 0.5]
    out("W04", "REVIEW" if q else "OK", f"questions with gap < 0.5 s: {q}")
    ac = [L["id"] for L in lines if re.search(r"\b[A-Z]{2,5}\b", L["text"]) and not L.get("say")]
    out("W05", "REVIEW" if ac else "OK", f"bare acronyms (TTS may read as a word): {ac[:12]}")
    bo = [L["id"] for L in lines if any(b in L["text"].lower() for b in BANNED_OPEN)]
    out("W08", "FAIL" if bo else "OK", f"banned openers: {bo}")
    adv = [L["id"] for L in lines if ADVICE.search(L["text"])]
    out("L15", "FAIL" if adv else "OK", f"investment-advice phrasing: {adv}")
    # P04: thumbnail words appear in the first ~30 s (first 12 lines + their shots)
    early_ids = {L["id"] for L in lines[:12]}
    early = " ".join(L["text"] for L in lines[:12]) + " " + json.dumps([s for s in shots if s.get("at") in early_ids])
    early = early.lower()
    tw = sj.get("thumb_pick", {}).get("text") or (sj.get("thumb_text") or [""])[0]
    toks = [t for t in re.findall(r"[a-z0-9]+", tw.lower()) if len(t) > 1]
    gone = [t for t in toks if t not in early]
    out("P04", "REVIEW" if gone else "OK", f"thumbnail '{tw}' words not found early: {gone} (numbers may be spoken as words)")
    # C05: one music bed per part
    nch = sum(1 for s in shots if s.get("type") == "chapter"); nm = len(sj.get("music", []))
    out("C05", "OK" if nm in (nch + 1, nch + 2) else "FAIL", f"music beds {nm} vs chapter cards {nch} (+cold open, +end)")
    # C08: shot 'at' exists, ids unique
    ids = [L["id"] for L in lines]; orphan = sorted({s["at"] for s in shots if s.get("at") not in set(ids)})
    out("C08", "FAIL" if orphan or len(ids) != len(set(ids)) else "OK", f"shots pointing at missing lines {orphan[:10]}; dup ids {len(ids)-len(set(ids))}")
    # X14: every json in the episode parses
    badj = []
    for root, _, fs in os.walk(ep):
        if "/out" in root or "/vo" in root: continue
        for f in fs:
            if f.endswith(".json"):
                try: json.load(open(os.path.join(root, f)))
                except Exception: badj.append(os.path.relpath(os.path.join(root, f), ep))
    out("X14", "FAIL" if badj else "OK", f"invalid json: {badj}")
    # X12: secret patterns in tracked text files
    try: tracked = subprocess.run(["git", "-C", REPO, "ls-files"], capture_output=True, text=True).stdout.split()
    except Exception: tracked = []
    hits = []
    for f in tracked:
        p = os.path.join(REPO, f)
        if not f.endswith((".py", ".md", ".json", ".yml", ".yaml", ".txt", ".sh", ".toml", ".cfg", ".env")) or os.path.getsize(p) > 2_000_000: continue
        try:
            if SECRET.search(open(p, errors="ignore").read()): hits.append(f)
        except Exception: pass
    out("X12", "FAIL" if hits else "OK", f"possible secrets in: {hits}")
    # K05: chapters in package (00:00 first, >= 3, ascending, >= 10 s)
    cp = next((os.path.join(ep, "package", n) for n in ("chapters.txt", "description.txt") if os.path.exists(os.path.join(ep, "package", n))), None)
    if cp:
        ts = [int(m.group(1)) * 60 + int(m.group(2)) for m in re.finditer(r"^\s*(\d{1,2}):(\d{2})\b", open(cp).read(), re.M)]
        ok = len(ts) >= 3 and ts[0] == 0 and all(b - a >= 10 for a, b in zip(ts, ts[1:]))
        out("K05", "OK" if ok else "FAIL", f"{len(ts)} chapter stamps in {os.path.basename(cp)}")
    else: out("K05", "TODO", "no package/chapters.txt or description.txt yet")
    for t in TODO: out(t.split()[0], "TODO", t.split(" ", 1)[1])
    os.makedirs(os.path.join(ep, "qa"), exist_ok=True)
    json.dump(res, open(os.path.join(ep, "qa", "fm.json"), "w"), indent=1)
    return 1 if any(r["status"] == "FAIL" for r in res) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
