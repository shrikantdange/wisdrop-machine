"""Free local preview: render sample frames for chosen lines with an estimated timeline (no voice, no Modal).
  python tools/v5_local_frames.py <ep> <line ids e.g. 0-3 or 78,85> <out_dir> [n_frames=12]
"""
import json, os, sys
ep, ids, out = sys.argv[1], sys.argv[2], sys.argv[3]; n = int(sys.argv[4]) if len(sys.argv) > 4 else 12
sel = []
for p in ids.split(","):
    a, _, b = p.partition("-"); sel += list(range(int(a), int(b or a) + 1))
L = {x["id"]: x for x in json.load(open(os.path.join(ep, "lines.json")))}
cur = .4; segs = []
for i in sel:
    ws = L[i]["text"].split(); d = len(ws) / 2.6; words = []
    for k, w in enumerate(ws): words.append([round(cur + d * k / len(ws), 3), round(cur + d * (k + 1) / len(ws), 3), w])
    segs.append({"i": i, "start": round(cur, 3), "end": round(cur + d, 3), "text": L[i]["text"], "words": words}); cur += d + L[i].get("gap", .3)
os.makedirs(out, exist_ok=True); tl = os.path.join(out, "timeline.json"); json.dump({"dur": round(cur + 1.5, 3), "segs": segs}, open(tl, "w"))
os.environ.update(WIS_TIMELINE=tl, WIS_ASSETS="/tmp/no_assets", WIS_NO_BEATS="1")
sys.argv = ["x", ep, "/tmp/x.mp4"]; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "machine", "engine"))
import shots_render as R
times = [float(x) for x in os.environ["T"].split(",")] if os.environ.get("T") else [R.DUR * (k + .5) / n for k in range(n)]
for t in times:
    R.render(int(t * R.FPS)).save(os.path.join(out, f"t{t:05.2f}.jpg"), quality=82)
print("OK", len(times), "frames, dur", R.DUR, [(round(a, 2), s["type"]) for a, s in R.SHOTS])
