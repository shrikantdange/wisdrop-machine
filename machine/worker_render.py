"""Wisdrop render + mix on Modal CPUs (no GPU), in parallel chunks.

Why CPU: every frame is drawn by our own code (PIL): camera moves, parallax,
breathing, lamp flicker, rain, grain, captions, evidence cards. No AI video, so
motion is free of model cost and identical in style every episode.
Cost: CPU is $0.0000131 per core-second (modal.com/pricing, 2026-11-03), so a
10-minute 1080p30 episode (~18,000 frames) at ~0.15 core-s per frame is about
45 core-minutes, roughly $0.04, finished in a few minutes wall-clock because
chunks run side by side.

Contract for an episode's render.py: importable with sys.argv = [render.py, ep_dir, out],
exposes render(i) -> PIL image and module-level FPS, W, H; timeline.json has "dur".

  modal run machine/worker_render.py::render --ep episodes/ep00-onecoin-test
"""
import json, pathlib
import modal

ROOT = pathlib.Path(__file__).resolve().parents[1]
app = modal.App("wisdrop-render")
avol = modal.Volume.from_name("wisdrop-assets", create_if_missing=True)
image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("ffmpeg")
         .pip_install("numpy", "pillow")
         .env({"WIS_REPO": "/repo"})
         .add_local_dir(str(ROOT), "/repo", ignore=[".git", "out", "**/__pycache__", "**/*.mp4", "**/vo/*.wav"]))
CHUNK_S = 15          # seconds of video per container call
MAX_PAR = 20          # containers side by side


@app.function(image=image, cpu=1.0, memory=2048, timeout=900, max_containers=MAX_PAR, scaledown_window=2,
              volumes={"/assets": avol})
def render_chunk(ep: str, a: int, b: int) -> bytes:
    import importlib.util, subprocess, sys
    ep_dir = f"/repo/{ep}"; out = f"/tmp/c_{a}.mp4"
    sys.argv = ["render.py", ep_dir, out]
    spec = importlib.util.spec_from_file_location("ep_render", f"{ep_dir}/render.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{m.W}x{m.H}",
                           "-r", str(m.FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                           "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(a, b):
        ff.stdin.write(m.render(i).convert("RGB").tobytes())
    ff.stdin.close(); ff.wait()
    return open(out, "rb").read()


@app.function(image=image, cpu=1.0, memory=2048, timeout=600, scaledown_window=2)
def join(parts: list, audio: bytes = b"") -> bytes:
    import subprocess
    lst = []
    for k, p in enumerate(parts):
        f = f"/tmp/p{k:04d}.mp4"; open(f, "wb").write(p); lst.append(f"file '{f}'")
    open("/tmp/list.txt", "w").write("\n".join(lst))
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "/tmp/list.txt"]
    if audio:
        open("/tmp/mix.wav", "wb").write(audio)
        cmd += ["-i", "/tmp/mix.wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    else:
        cmd += ["-c", "copy"]
    subprocess.run(cmd + ["/tmp/final.mp4"], check=True)
    return open("/tmp/final.mp4", "rb").read()


@app.function(image=image, cpu=1.0, memory=3072, timeout=900, scaledown_window=2)
def mix(ep: str, vo: bytes) -> bytes:
    import subprocess, sys
    d = f"/repo/{ep}"
    import shutil, os
    work = "/tmp/ep"; shutil.copytree(d, work, dirs_exist_ok=True)
    open(f"{work}/vo.wav", "wb").write(vo)
    subprocess.run([sys.executable, f"{work}/mix.py", work], check=True)
    return open(f"{work}/mix.wav", "rb").read()


@app.local_entrypoint()
def render(ep: str, with_audio: bool = True):
    import time
    t0 = time.time()
    tl = json.loads((ROOT / ep / "timeline.json").read_text())
    fps = 30; n = int(tl["dur"] * fps); step = CHUNK_S * fps
    ranges = [(a, min(n, a + step)) for a in range(0, n, step)]
    print(f"PLAN {n} frames in {len(ranges)} chunks")
    parts = list(render_chunk.starmap([(ep, a, b) for a, b in ranges]))
    audio = b""
    vo = ROOT / "out" / pathlib.Path(ep).name / "vo.wav"
    if with_audio and vo.exists() and (ROOT / ep / "mix.py").exists():
        audio = mix.remote(ep, vo.read_bytes())
    vid = join.remote(parts, audio)
    od = ROOT / "out" / pathlib.Path(ep).name; od.mkdir(parents=True, exist_ok=True)
    (od / "video.mp4").write_bytes(vid)
    print(json.dumps({"frames": n, "chunks": len(ranges), "secs": round(time.time() - t0, 1), "mb": round(len(vid) / 1e6, 1)}))
    print("OK render done")
