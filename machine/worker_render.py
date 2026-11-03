"""Wisdrop render + mix on Modal CPUs (no GPU), with a SHOT-LEVEL CACHE.

Every shot is rendered to its own small mp4 and stored in the volume under a hash of everything
that can change its pixels (engine code, library, the shot, its timing, its captions, its pictures).
A re-run renders only shots whose hash changed; unchanged shots cost nothing. Uncached shots are
grouped into ~15 s batches that run side by side on up to 20 one-core containers.

Cost (modal.com/pricing, 2026-11-03): CPU $0.0000131 per core-second; measured per run in
out/<ep>/cost.json (machine/cost.py).

  modal run machine/worker_render.py::render --ep episodes/ep01-onecoin [--seconds 15]
"""
import json, pathlib, time
import modal

ROOT = pathlib.Path(__file__).resolve().parents[1]
app = modal.App("wisdrop-render")
avol = modal.Volume.from_name("wisdrop-assets", create_if_missing=True)
image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("ffmpeg")
         .pip_install("numpy", "pillow")
         .env({"WIS_REPO": "/repo"})
         .add_local_dir(str(ROOT), "/repo", ignore=[".git", "out", "**/__pycache__", "**/*.mp4", "**/vo/*.wav"]))
BATCH_S = 15          # seconds of uncached video per container call
MAX_PAR = 20
FPS = 30


def _load(ep):
    import importlib.util, os, sys
    name = os.path.basename(ep); os.environ["WIS_TIMELINE"] = f"/assets/eps/{name}/work/timeline.json"
    sys.argv = ["render.py", f"/repo/{ep}", "/tmp/x.mp4"]
    spec = importlib.util.spec_from_file_location("ep_render", "/repo/machine/engine/shots_render.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


@app.function(image=image, cpu=1.0, memory=2048, timeout=600, scaledown_window=2, volumes={"/assets": avol})
def prepare(ep: str) -> float:
    """vo_index (from the voice worker) + cached line wavs -> vo.wav + timeline.json in the volume."""
    import subprocess, sys, os
    name = os.path.basename(ep); w = f"/assets/eps/{name}/work"
    subprocess.run([sys.executable, "/repo/machine/engine/assemble.py", f"/repo/{ep}", f"/assets/eps/{name}/vo_index.json", "/assets/vo", w], check=True)
    avol.commit()
    return json.load(open(f"{w}/timeline.json"))["dur"]


@app.function(image=image, cpu=1.0, memory=2048, timeout=600, scaledown_window=2, volumes={"/assets": avol})
def plan(ep: str, seconds: float = 0) -> list:
    """[(a_frame, b_frame, key, cached)] for every shot in range; key hashes all that changes pixels."""
    import hashlib, os, glob
    m = _load(ep); n = int((min(m.DUR, seconds) if seconds else m.DUR) * FPS)
    eng = hashlib.sha256()
    for f in sorted(glob.glob("/repo/machine/engine/*.py")) + ["/repo/library/library.json"]: eng.update(open(f, "rb").read())
    out = []
    for k, (st, s) in enumerate(m.SHOTS):
        a, b = int(round(st * FPS)), min(n, int(round(m.STARTS[k + 1] * FPS)))
        if a >= n: break
        if b <= a: continue
        caps = [c for c in m.chunks if c[-1][1] >= st - .2 and c[0][0] <= m.STARTS[k + 1] + .2]
        names = []
        if s.get("set"):
            tm = s.get("time", "night"); names.append(f"set_{s['set']}__{tm}")
            if s.get("cast"): names.append(f"shot_{s['set']}__{tm}__" + "+".join(f"{c['who']}-{c.get('pose', 'front_neutral')}" for c in s["cast"][:2]))
        pics = [m.MAN.get(x, {}).get("hash", "") for x in names]
        files = [p.get("file") or m._re2.sub(r"[^a-z0-9]+", "-", (p.get("commons") or p.get("q", "")).lower()).strip("-")[:60] + ".jpg"
                 for p in (s.get("photos", []) + ([s] if s["type"] in ("photo", "magnify", "parallax", "lineart") else []))] if hasattr(m, "_re2") else []
        media = [f"/repo/{ep}/media/{f}" for f in files if os.path.exists(f"/repo/{ep}/media/{f}")]
        h = hashlib.sha256(json.dumps([eng.hexdigest(), s, a, b, k > 0, m.PART[k], caps, pics, m.SH.get("counter"),
                                       [x for x in m.SHOTS if "counter_to" in x[1] and x[0] <= m.STARTS[k + 1]].__repr__(),
                                       [os.path.getsize(p) for p in media]], sort_keys=True, default=str).encode()).hexdigest()[:24]
        out.append((a, b, h, os.path.exists(f"/assets/cache/shots/{h}.mp4")))
    return out


@app.function(image=image, cpu=1.0, memory=2048, timeout=900, max_containers=MAX_PAR, scaledown_window=2,
              volumes={"/assets": avol})
def render_batch(ep: str, items: list) -> float:
    """render each (a, b, key) to /assets/cache/shots/key.mp4; returns seconds spent."""
    import subprocess, os, hashlib, time as _t
    t0 = _t.time(); m = _load(ep); os.makedirs("/assets/cache/shots", exist_ok=True)
    for a, b, key in items:
        tmp = f"/tmp/{key}.mp4"
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{m.W}x{m.H}",
                               "-r", str(m.FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                               "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for i in range(a, b):
            px = m.render(i).convert("RGB").tobytes(); ff.stdin.write(px)
            if i == a and "probe" not in locals(): probe = (i, hashlib.sha256(px).hexdigest())
        ff.stdin.close(); ff.wait()
        subprocess.run(["cp", tmp, f"/assets/cache/shots/{key}.mp4"], check=True)
    if items:   # AMC-W1/W2 determinism probe: the first frame rendered again, after later frames, must be identical
        same = hashlib.sha256(m.render(probe[0]).convert("RGB").tobytes()).hexdigest() == probe[1]
        print(("OK" if same else "FAIL") + f": determinism, frame {probe[0]} re-rendered out of order is {'identical' if same else 'DIFFERENT'} (AMC-W2)")
    avol.commit()
    return _t.time() - t0


@app.function(image=image, cpu=1.0, memory=2048, timeout=600, scaledown_window=2, volumes={"/assets": avol})
def join(keys: list, audio: bytes = b"") -> bytes:
    import subprocess
    avol.reload()
    open("/tmp/list.txt", "w").write("\n".join(f"file '/assets/cache/shots/{k}.mp4'" for k in keys))
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "/tmp/list.txt"]
    if audio:
        open("/tmp/mix.wav", "wb").write(audio)
        cmd += ["-i", "/tmp/mix.wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    else:
        cmd += ["-c", "copy"]
    subprocess.run(cmd + ["/tmp/final.mp4"], check=True)
    return open("/tmp/final.mp4", "rb").read()


@app.function(image=image, cpu=1.0, memory=4096, timeout=900, scaledown_window=2, volumes={"/assets": avol})
def automix(ep: str) -> dict:
    import subprocess, sys, os
    w = f"/assets/eps/{os.path.basename(ep)}/work"
    r = subprocess.run([sys.executable, "/repo/machine/engine/automix.py", f"/repo/{ep}", w], check=True, capture_output=True, text=True)
    print(r.stdout[-2000:])
    avol.commit()
    return {"wav": open(f"{w}/mix.wav", "rb").read(), "qc": json.load(open(f"{w}/audio_qc.json")), "log": r.stdout[-600:]}


@app.function(image=image, cpu=1.0, memory=3072, timeout=600, scaledown_window=2, volumes={"/assets": avol})
def package(ep: str) -> dict:
    import subprocess, sys, os, pathlib
    name = os.path.basename(ep); o = f"/tmp/pkg_{name}"
    subprocess.run([sys.executable, "/repo/machine/package.py", f"/repo/{ep}", f"/assets/eps/{name}/work/timeline.json", "/assets", o], check=True)
    return {f.name: f.read_bytes() for f in pathlib.Path(o).iterdir()}


@app.local_entrypoint()
def render(ep: str, with_audio: bool = True, seconds: float = 0):
    """seconds>0 renders only the first N seconds (cheap preview)."""
    import sys
    sys.path.insert(0, str(ROOT / "machine")); import cost
    t0 = time.time()
    with cost.timer() as tm: dur = prepare.remote(ep)
    with cost.timer() as tp: shots = plan.remote(ep, seconds)
    cost.add(ep, "prepare+plan", tm.secs + tp.secs, n=2)
    todo = [(a, b, k) for a, b, k, c in shots if not c]
    print(f"PLAN {len(shots)} shots, {len(shots) - len(todo)} cached, {len(todo)} to render ({sum(b - a for a, b, _ in todo)} frames)")
    batches, cur, fr = [], [], 0
    for it in todo:
        cur.append(it); fr += it[1] - it[0]
        if fr >= BATCH_S * FPS: batches.append(cur); cur, fr = [], 0
    if cur: batches.append(cur)
    if batches:
        secs = list(render_batch.starmap([(ep, b) for b in batches]))
        cost.add(ep, "render", sum(secs), n=len(batches))
    audio = b""
    if with_audio:
        with cost.timer() as ta: mx = automix.remote(ep)
        cost.add(ep, "mix", ta.secs, mem_gib=4); audio = mx["wav"]; print(mx["log"])
        od = ROOT / "out" / pathlib.Path(ep).name; od.mkdir(parents=True, exist_ok=True); (od / "audio_qc.json").write_text(json.dumps(mx["qc"]))
    with cost.timer() as tj: vid = join.remote([k for _, _, k, _ in shots], audio)
    cost.add(ep, "join", tj.secs)
    od = ROOT / "out" / pathlib.Path(ep).name; od.mkdir(parents=True, exist_ok=True)
    (od / "video.mp4").write_bytes(vid)
    pk = od / "package"; pk.mkdir(exist_ok=True)
    with cost.timer() as tk:
        for k, v in package.remote(ep).items(): (pk / k).write_bytes(v)
    cost.add(ep, "package", tk.secs, mem_gib=3)
    print("OK packaged")
    c = cost.load(ep)
    print(json.dumps({"shots": len(shots), "rendered": len(todo), "secs": round(time.time() - t0, 1), "mb": round(len(vid) / 1e6, 1), "usd": c.get("total_usd")}))
    print(f"COST run total ${c.get('total_usd', 0):.4f} (GPU {c.get('gpu_secs', 0)} s)")
    print("OK render done")
