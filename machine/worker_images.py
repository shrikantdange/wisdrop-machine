"""Wisdrop images on a Modal GPU (frugal).

Model: Qwen-Image (Apache 2.0, not gated) for plates and character masters.
Poses with character consistency will use Qwen-Image-Edit-2509 (Apache 2.0) later.
Cost rules: weights downloaded once by a CPU-only function; one GPU container;
all images of a batch in ONE call; shuts down 2 s after; hard timeout.

  modal run machine/worker_images.py::fetch_weights
  modal run machine/worker_images.py::images --job episodes/ep01-onecoin/img_jobs_test.json
"""
import json, pathlib
import modal

app = modal.App("wisdrop-images")
vol = modal.Volume.from_name("wisdrop-weights", create_if_missing=True)
HF = "/weights/hf"
MODEL = "Qwen/Qwen-Image"

image = (modal.Image.debian_slim(python_version="3.11")
         .pip_install("torch==2.6.0", "diffusers>=0.35.1", "transformers>=4.51,<5", "accelerate",
                      "safetensors", "sentencepiece", "pillow")
         .env({"HF_HOME": HF, "HF_HUB_DISABLE_TELEMETRY": "1", "HF_HUB_ENABLE_HF_TRANSFER": "0"}))

STYLE = ("Editorial flat-vector illustration for a serious finance documentary. Calm, adult, believable. "
         "Restrained realism: realistic proportions and hands, simple flat colour shapes with 2-3 tones per surface, "
         "crisp hard-edged shadows, soft cinematic lighting from a window or lamp, subtle paper grain texture. "
         "Muted palette of deep navy, charcoal, warm amber and off-white, with small accents only. "
         "Low or eye-level cinematic camera, 16:9 composition. No text, no letters, no logos, no watermarks.")
NEG = "text, letters, words, logo, watermark, signature, photo, 3d render, anime, cartoon big eyes, extra fingers, deformed hands"


@app.function(image=image, volumes={"/weights": vol}, timeout=3600, cpu=2, memory=4096, max_containers=1)
def download_weights() -> str:
    from huggingface_hub import snapshot_download
    p = snapshot_download(MODEL, allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "tokenizer*", "*/tokenizer*", "*.jinja"])
    vol.commit()
    return p


@app.function(image=image, gpu="A100-80GB", volumes={"/weights": vol}, timeout=1200,
              max_containers=1, scaledown_window=2, memory=32768)
def run_images(jobs: list) -> list:
    import io, time, torch
    from diffusers import DiffusionPipeline
    t0 = time.time()
    pipe = DiffusionPipeline.from_pretrained(MODEL, torch_dtype=torch.bfloat16).to("cuda")
    load_s = round(time.time() - t0, 1)
    out = []
    for j in jobs:
        t = time.time()
        img = pipe(prompt=STYLE + " " + j["prompt"], negative_prompt=NEG, width=j.get("w", 1664), height=j.get("h", 928),
                   num_inference_steps=j.get("steps", 30), true_cfg_scale=4.0,
                   generator=torch.Generator("cuda").manual_seed(j.get("seed", 7))).images[0]
        b = io.BytesIO(); img.save(b, "PNG")
        out.append({"name": j["name"], "png": b.getvalue(), "secs": round(time.time() - t, 1)})
    out.append({"name": "_meta", "load_s": load_s, "total_s": round(time.time() - t0, 1), "gpu": torch.cuda.get_device_name(0)})
    return out


@app.local_entrypoint()
def fetch_weights():
    print("OK weights at", download_weights.remote())


@app.local_entrypoint()
def images(job: str):
    root = pathlib.Path(__file__).resolve().parents[1]
    jp = root / job; jobs = json.loads(jp.read_text())
    od = root / "out" / jp.parent.name / "img"; od.mkdir(parents=True, exist_ok=True)
    meta = []
    for r in run_images.remote(jobs):
        if "png" in r:
            (od / f"{r['name']}.png").write_bytes(r["png"]); meta.append({"name": r["name"], "secs": r["secs"]})
        else:
            meta.append(r)
        print("IMG", json.dumps(meta[-1]))
    (od / "img_meta.json").write_text(json.dumps(meta, indent=1))
    print("OK images done")
