#!/usr/bin/env python3
"""Cost report from cost.json files (machine/cost.py). Free, CPU only.

  python machine/cost_report.py [cost.json ...]      # default: out/*/cost.json
Prints one line per file (total, GPU s, CPU s, biggest step) and a grand total; writes nothing.
"""
import glob, json, sys

def main(paths):
    paths = paths or sorted(glob.glob("out/*/cost.json"))
    if not paths: print("WAIT no cost.json found (download a run's artifact or the preview branch)"); return 0
    tot = 0.0
    for p in paths:
        c = json.load(open(p)); st = c.get("steps", [])
        gpu = sum(s["secs"] for s in st if s.get("gpu")); cpu = sum(s["secs"] for s in st if not s.get("gpu"))
        big = max(st, key=lambda s: s["usd"]) if st else {"step": "-", "usd": 0}
        usd = c.get("total_usd", sum(s["usd"] for s in st)); tot += usd
        print(f"COST {p}: ${usd:.4f} | GPU {gpu:.0f} s | CPU {cpu:.0f} s | biggest {big['step']} ${big['usd']:.4f}")
    print(f"COST total ${tot:.4f} over {len(paths)} run(s)")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
