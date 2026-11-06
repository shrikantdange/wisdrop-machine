"""Print each chapter's test_lines range from <ep>/chapters.json and check the chapter chain.
Usage: python tools/chapter_lines.py episodes/<ep>   (free, CPU). Exit 1 on a FAIL."""
import json, os, sys
ep = sys.argv[1]; cj = json.load(open(os.path.join(ep, "chapters.json")))
ch = cj["chapters"]; bad = 0; nxt = 0
for i, c in enumerate(ch):
    a, b = c["lines"]
    if a != nxt: print(f"FAIL {c['id']} starts at line {a}, expected {nxt}"); bad = 1
    nxt = b + 1
    if i:
        p = ch[i - 1]; po, ci = p["exit"].get("counter"), c["entry"].get("counter")
        if (po or {}).get("value") != (ci or {}).get("value"): print(f"FAIL FM-C01 counter {p['id']}->{c['id']}: {po} vs {ci}"); bad = 1
        if p["part"] == c["part"] and (p["exit"]["board"], p["exit"].get("accent"), p["exit"]["music"]) != (c["entry"]["board"], c["entry"].get("accent"), c["entry"]["music"]):
            print(f"FAIL FM-C02/C05 board/accent/music change inside part {c['part']} at {p['id']}->{c['id']}"); bad = 1
    print(f"{c['id']}  part={c['part']}  test_lines={a}-{b}  target={c['target_s']}s")
lj = os.path.join(ep, "lines.json")
if os.path.exists(lj) and nxt != len(json.load(open(lj))): print(f"FAIL chapters cover lines 0-{nxt-1}, lines.json has {len(json.load(open(lj)))}"); bad = 1
print("OK chapters chain" if not bad else "FAIL chapters chain"); sys.exit(bad)
