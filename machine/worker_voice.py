"""Wisdrop voice on a Modal GPU, built to spend as little as possible.

Cost rules baked in:
- Cheapest GPU (T4). One container, never more (max_containers=1).
- Weights are downloaded once into the Modal volume by a CPU-only function, so
  no GPU second is ever spent downloading.
- The whole episode is voiced in ONE call: model loads once, every line reuses it.
- Container shuts down 2 s after the call (no idle billing). Hard timeout.
- Whisper QC runs on the same GPU right after each take (small.en, int8 on CPU
  fallback if CUDA libs are missing), so no second machine is needed.

  modal run machine/worker_voice.py::fetch_weights            # once, CPU only
  modal run machine/worker_voice.py::voice --ep episodes/ep00-onecoin-test --only 3,4,5
"""
import json, os, pathlib
import modal

app = modal.App("wisdrop-voice")
vol = modal.Volume.from_name("wisdrop-weights", create_if_missing=True)
avol = modal.Volume.from_name("wisdrop-assets", create_if_missing=True)
VO_ENGINE = "cb0.1.7-t4"   # part of every line hash
HF = "/weights/hf"

image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("ffmpeg")
         .pip_install("chatterbox-tts==0.1.7", "faster-whisper==1.2.1", "num2words", "soundfile")
         .env({"HF_HOME": HF, "HF_HUB_DISABLE_TELEMETRY": "1"}))

# Same presets and seeds as machine/engine/vo_runner.py (keep in sync)
PRESETS = {"facts": (0.55, 0.5), "dry": (0.6, 0.4), "tension": (0.7, 0.35), "question": (0.8, 0.3), "beat": (0.9, 0.25)}


@app.function(image=image, volumes={"/weights": vol}, timeout=1200, cpu=1, memory=2048, max_containers=1)
def download_weights() -> str:
    from huggingface_hub import snapshot_download
    p = snapshot_download("ResembleAI/chatterbox", allow_patterns=["*.safetensors", "*.json", "*.pt", "*.model"])
    from faster_whisper import download_model
    download_model("small.en", cache_dir=HF + "/whisper")
    vol.commit()
    return p


def line_hash(L: dict, ref_sha: str) -> str:
    import hashlib
    k = json.dumps({"e": VO_ENGINE, "t": L["text"], "say": L.get("say", ""), "p": L.get("preset", "facts"),
                    "ref": ref_sha, "seedbump": L.get("seedbump", 0)}, sort_keys=True)
    return hashlib.sha256(k.encode()).hexdigest()[:16]


@app.function(image=image, volumes={"/assets": avol}, timeout=120, cpu=0.25, memory=512)
def vo_cache(hashes: list, want: list = None) -> dict:
    """which line hashes exist; with want=[...] also return their wav + qc."""
    import os
    have = [h for h in hashes if os.path.exists(f"/assets/vo/{h}.wav")]
    blobs = {h: {"wav": open(f"/assets/vo/{h}.wav", "rb").read(), "qc": json.load(open(f"/assets/vo/{h}.json"))}
             for h in (want or [])}
    return {"have": have, "blobs": blobs}


@app.function(image=image, volumes={"/assets": avol}, timeout=60, cpu=0.25, memory=512)
def put_index(path: str, data: bytes):
    p = pathlib.Path("/assets/" + path); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data); avol.commit()


@app.function(image=image, gpu="T4", volumes={"/weights": vol, "/assets": avol}, timeout=1500,
              max_containers=1, scaledown_window=2)
def run_lines(lines: list, ref_wav: bytes, takes: int = 2) -> list:
    import io, re, time, numpy as np, torch, torchaudio as ta
    from num2words import num2words
    from chatterbox.tts import ChatterboxTTS
    from faster_whisper import WhisperModel
    t0 = time.time()
    ref = "/tmp/ref.wav"; open(ref, "wb").write(ref_wav)
    m = ChatterboxTTS.from_pretrained(device="cuda")
    m.prepare_conditionals(ref, exaggeration=0.55)
    try:
        wm = WhisperModel("small.en", device="cuda", compute_type="float16", download_root=HF + "/whisper")
    except Exception:
        wm = WhisperModel("small.en", device="cpu", compute_type="int8", download_root=HF + "/whisper")
    load_s = round(time.time() - t0, 1)

    def norm(s):
        s = s.lower().replace("-", " ").replace("%", " percent").replace("$", " dollars ")
        s = re.sub(r"(\d+)(st|nd|rd|th)\b", lambda g: num2words(int(g.group(1)), to="ordinal"), s)
        s = re.sub(r"\d[\d,]*", lambda g: num2words(int(g.group(0).replace(",", ""))), s)
        s = s.replace("f.b.i.", "fbi"); s = re.sub(r"[^a-z' ]", " ", s).replace("'s", "s")
        return s.split()

    def wer(a, b):
        r, h = norm(a), norm(b); d = list(range(len(h) + 1))
        for i in range(1, len(r) + 1):
            p = d[:]; d[0] = i
            for j in range(1, len(h) + 1):
                d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (r[i - 1] != h[j - 1]))
        return d[-1] / max(1, len(r))

    out = []
    for L in lines:
        ex, cfg = PRESETS[L.get("preset", "facts")]; best = None
        for k in range(takes):
            t = time.time(); torch.manual_seed(1000 + L["id"] * 17 + k + 100 * L.get("seedbump", 0))
            with torch.inference_mode():
                w = m.generate(L.get("say", L["text"]), exaggeration=ex, cfg_weight=cfg).cpu()
            a16 = ta.functional.resample(w, m.sr, 16000).squeeze().numpy().astype(np.float32)
            segs = list(wm.transcribe(a16, language="en", beam_size=1, word_timestamps=True)[0])
            heard = " ".join(s.text for s in segs).strip()
            wts = [[round(w.start, 3), round(w.end, 3), w.word.strip()] for sg in segs for w in (sg.words or [])]
            e = wer(L["text"], heard); dur = w.shape[-1] / m.sr
            clip = float((w.abs() > .99).float().mean())
            issues = ([f"wer {e:.2f}"] if e > 0.12 else []) + (["clipping"] if clip > 1e-3 else [])
            r = {"id": L["id"], "take": k, "secs": round(time.time() - t, 1), "dur": round(dur, 2),
                 "wer": round(e, 3), "heard": heard, "issues": issues, "words": wts}
            if best is None or len(issues) < len(best[0]["issues"]) or (len(issues) == len(best[0]["issues"]) and e < best[0]["wer"]):
                best = (r, w)
            if not issues:
                break
        buf = io.BytesIO(); ta.save(buf, best[1], m.sr, format="wav")
        best[0]["status"] = "ok" if not best[0]["issues"] else "review"
        if L.get("hash"):                      # cache: this line never needs the GPU again
            os.makedirs("/assets/vo", exist_ok=True)
            open(f"/assets/vo/{L['hash']}.wav", "wb").write(buf.getvalue())
            json.dump(best[0], open(f"/assets/vo/{L['hash']}.json", "w"))
        out.append({"qc": best[0], "wav": buf.getvalue()})
    avol.commit()
    out.append({"qc": {"load_s": load_s, "total_s": round(time.time() - t0, 1),
                       "gpu": torch.cuda.get_device_name(0)}})
    return out


@app.local_entrypoint()
def fetch_weights():
    print("OK weights at", download_weights.remote())


@app.local_entrypoint()
def voice(ep: str, only: str = "", takes: int = 2, redo: str = ""):
    """Cached: a line whose text, preset and voice are unchanged is never voiced again.
    redo=3,7 forces new takes (new seed) for those lines only."""
    import hashlib
    root = pathlib.Path(__file__).resolve().parents[1]
    lines = json.loads((root / ep / "lines.json").read_text())
    if only:
        keep = {int(x) for x in only.split(",")}; lines = [l for l in lines if l["id"] in keep]
    ref = (root / "kit/voice/ref_michael.wav").read_bytes(); ref_sha = hashlib.sha256(ref).hexdigest()[:16]
    rd = {int(x) for x in redo.split(",") if x}
    for L in lines:
        if L["id"] in rd:
            L["seedbump"] = L.get("seedbump", 0) + 1
        L["hash"] = line_hash(L, ref_sha)
    have = set(vo_cache.remote([L["hash"] for L in lines])["have"])
    todo = [L for L in lines if L["hash"] not in have]
    print(f"PLAN {len(lines)} lines, {len(have)} cached, {len(todo)} to voice")
    res = run_lines.remote(todo, ref, takes) if todo else []
    cached = vo_cache.remote([], [L["hash"] for L in lines if L["hash"] in have])["blobs"]
    idmap = {L["hash"]: L["id"] for L in lines}
    res = list(res) + [{"qc": dict(v["qc"], cached=True, id=idmap[h]), "wav": v["wav"]} for h, v in cached.items()]
    od = root / "out" / pathlib.Path(ep).name / "vo"; od.mkdir(parents=True, exist_ok=True)
    qc = []
    for r in res:
        if "wav" in r:
            (od / f"line_{r['qc']['id']:03d}.wav").write_bytes(r["wav"])
        qc.append(r["qc"]); print("QC", json.dumps(r["qc"]))
    (od / "vo_qc.json").write_text(json.dumps(qc, indent=1))
    index = [{"id": L["id"], "hash": L["hash"], "gap": L.get("gap", 0.3)} for L in lines]
    put_index.remote(f"eps/{pathlib.Path(ep).name}/vo_index.json", json.dumps(index, indent=1).encode())
    bad = [q for q in qc if q.get("status") == "review"]
    print("OK voice done" if not bad else f"WAIT {len(bad)} line(s) need a listen")
