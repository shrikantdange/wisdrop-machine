#!/usr/bin/env python3
"""Script scorer (free): hook timing, open loops per part, pace, sentence length, jargon.

  python machine/score_script.py <ep_dir>                 # score lines.json
  python machine/score_script.py <ep_dir> --hooks         # also score every opening in hooks.json

Times are estimated at 2.6 spoken words per second (~156 wpm, our narrator's pace) plus each
line's gap. Prints a 0-100 score with the reasons; REVIEW lines are suggestions for the owner,
never automatic script changes (the owner approves every script).
"""
import json, os, re, sys

WPS = 2.6
NUM = re.compile(r"[$€£]\s?\d|\d+(\.\d+)?\s?(%|m\b|bn|b\b)|\b(thousand|million|billion|percent)\b", re.I)
SHOCK = re.compile(r"\b(billion|million|vanished|disappeared|fbi|most wanted|prison|fraud|never existed|stole|lost)\b", re.I)
PROMISE = re.compile(r"\b(this is the story|this is how|here is how|how (do|did|does)|why|we'll|you'll|by the end|the answer)\b", re.I)
JARGON = ["blockchain", "mining", "ledger", "token", "ico", "kyc", "liquidity", "pyramid scheme", "ponzi", "mlm",
          "multi-level", "securities", "wire fraud", "money laundering", "escrow", "fiat", "exchange", "wallet", "indictment", "plea"]


def times(lines):
    t, out = 0.4, []
    for L in lines:
        d = len(L["text"].split()) / WPS; out.append((t, t + d)); t += d + L.get("gap", .3)
    return out, t


def score(lines, chapters=None, label="script"):
    tm, dur = times(lines); pts, notes = 0, []
    def first(rx):
        return next((a for (a, _), L in zip(tm, lines) if rx.search(L["text"])), 99)
    shock = min(first(NUM), first(SHOCK)); q = next((a for (a, _), L in zip(tm, lines) if L["text"].strip().endswith("?") or L.get("preset") == "question"), 99)
    prom = first(PROMISE)
    pts += 25 if shock <= 5 else 12 if shock <= 10 else 0; notes.append(f"shock fact at {shock:.1f} s (target <= 5)")
    pts += 25 if q <= 8 else 12 if q <= 20 else 5 if q < 99 else 0; notes.append(f"first question at {q:.1f} s (target <= 8)")
    pts += 15 if prom <= 15 else 7 if prom <= 30 else 0; notes.append(f"promise at {prom:.1f} s (target <= 15)")
    # open loops per part
    if chapters:
        bounds = sorted(set([0] + chapters + [len(lines)])); parts = [lines[a:b] for a, b in zip(bounds, bounds[1:]) if b > a]
        loops = [sum(1 for L in p if L["text"].strip().endswith("?")) for p in parts]
        ok = sum(1 for x in loops if x >= 1); pts += round(15 * ok / max(1, len(parts))); notes.append(f"open questions per part {loops} (target >= 1 each)")
    else:
        pts += 15 if any(L["text"].strip().endswith("?") for L in lines) else 0
    long_ = [L["id"] for L in lines if len(L["text"].split()) > 25]
    pts += 10 if not long_ else max(0, 10 - 2 * len(long_)); notes.append(f"sentences over 25 words: {long_[:8]}")
    jar = {}
    for L in lines:
        for j in JARGON:
            if re.search(r"\b" + re.escape(j) + r"\b", L["text"], re.I) and j not in jar: jar[j] = L["id"]
    pts += 10 if len(jar) <= 6 else 5; notes.append(f"jargon first used (explain it on screen): {jar}")
    print(f"{'OK' if pts >= 70 else 'REVIEW'}: {label} score {pts}/100 ~{dur / 60:.1f} min")
    for n in notes: print("   ", n)
    return pts


def main(ep, hooks=False):
    lines = json.load(open(os.path.join(ep, "lines.json")))
    chapters = []
    sp = os.path.join(ep, "shots.json")
    if os.path.exists(sp): chapters = sorted({s["at"] for s in json.load(open(sp))["shots"] if s["type"] == "chapter"})
    if not chapters: chapters = [L["id"] for L in lines if "CHAPTER" in L.get("visual", "").upper()]
    res = {"script": score(lines, chapters)}
    hp = os.path.join(ep, "hooks.json")
    if hooks and os.path.exists(hp):
        for h in json.load(open(hp)):
            res[h["name"]] = score([{"id": k, "text": t, "gap": .3} for k, t in enumerate(h["lines"])], None, f"hook {h['name']}")
    os.makedirs(os.path.join(ep, "qa"), exist_ok=True); json.dump(res, open(os.path.join(ep, "qa", "script_score.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], "--hooks" in sys.argv)
