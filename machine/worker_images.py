"""Wisdrop images on Modal, v3: fast, cached, library-first.

Speed / cost (see docs/COST_PLAN.md):
- Qwen-Image + Lightning 8-step LoRA (both Apache 2.0): 8 passes per image
  instead of 60 (30 steps x CFG). About 6-8x less GPU time per image.
- Poses: Qwen-Image-Edit-2509 + its Lightning 8-step LoRA (Apache 2.0), fed the
  character's master sheet so face and outfit stay the same.
- Content cache: every job has a hash of everything that shapes the picture
  (model, lora, style text, prompt, seed, size, reference images). Finished
  pictures live in volume `wisdrop-assets`. A job whose hash already exists is
  never sent to the GPU again; if nothing is missing, no GPU starts at all.
- Weights downloaded once by CPU-only functions. One GPU container, all jobs in
  ONE call, shuts down 2 s after, hard timeout.
- Character cutouts (transparent PNG) made on CPU with rembg (MIT), cached too.

  modal run machine/worker_images.py::fetch_weights          # once per model, CPU only
  modal run machine/worker_images.py::images --job <jobs.json>
"""
import hashlib, io, json, pathlib
import modal

app = modal.App("wisdrop-images")
wvol = modal.Volume.from_name("wisdrop-weights", create_if_missing=True)
avol = modal.Volume.from_name("wisdrop-assets", create_if_missing=True)
HF = "/weights/hf"
BASE = "Qwen/Qwen-Image"
EDIT = "Qwen/Qwen-Image-Edit-2509"
LREPO = "lightx2v/Qwen-Image-Lightning"
LBASE = "Qwen-Image-Lightning-8steps-V2.0-bf16.safetensors"
LEDIT = "Qwen-Image-Edit-2509/Qwen-Image-Edit-2509-Lightning-8steps-V1.0-bf16.safetensors"
ENGINE = "v3-lightning8"   # part of every hash; bump only when the look must change

image = (modal.Image.debian_slim(python_version="3.11")
         .pip_install("torch==2.6.0", "diffusers>=0.36.0", "transformers>=4.51,<5", "accelerate", "peft>=0.17",
                      "safetensors", "sentencepiece", "pillow")
         .env({"HF_HOME": HF, "HF_HUB_DISABLE_TELEMETRY": "1"}))
cpu_image = (modal.Image.debian_slim(python_version="3.11")
             .pip_install("rembg[cpu]==2.0.67", "pillow", "huggingface_hub")
             .env({"U2NET_HOME": "/weights/u2net", "HF_HOME": HF}))

NO_PEOPLE = " The place is completely empty: no people, no figures, no silhouettes, no reflections of people."
NO_TEXT = " Every surface is blank: no writing, no letters, no numbers, no signs, no labels, no screens with text."


def job_hash(j: dict, style: str, ref_hashes: list) -> str:
    key = json.dumps({"e": ENGINE, "mode": j.get("mode", "t2i"), "s": style, "p": j["prompt"],
                      "seed": j.get("seed", 7), "w": j.get("w", 1664), "h": j.get("h", 928),
                      "steps": j.get("steps", 8), "refs": ref_hashes, "people": j.get("people", False)}, sort_keys=True)
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def full_prompt(j: dict, style: str) -> str:
    p = style + " " + j["prompt"]
    if not j.get("people", False):
        p += NO_PEOPLE
    return p + NO_TEXT


@app.function(image=image, volumes={"/weights": wvol}, timeout=3600, cpu=2, memory=4096, max_containers=1)
def download_weights(which: str = "base") -> str:
    from huggingface_hub import snapshot_download, hf_hub_download
    pats = ["*.json", "*.safetensors", "*.txt", "*.model", "tokenizer*", "*/tokenizer*", "*.jinja"]
    repo = EDIT if which == "edit" else BASE
    p = snapshot_download(repo, allow_patterns=pats)
    hf_hub_download(LREPO, LEDIT if which == "edit" else LBASE)
    wvol.commit()
    return p


@app.function(image=cpu_image, volumes={"/assets": avol}, timeout=120, cpu=0.25, memory=512)
def which_exist(paths: list) -> list:
    import os
    return [p for p in paths if os.path.exists("/assets/" + p)]


@app.function(image=cpu_image, volumes={"/assets": avol}, timeout=60, cpu=0.25, memory=512)
def read_assets(paths: list) -> dict:
    return {p: open("/assets/" + p, "rb").read() for p in paths}


@app.function(image=image, gpu="A100-80GB", volumes={"/weights": wvol, "/assets": avol}, timeout=1800,
              max_containers=1, scaledown_window=2, memory=32768)
def run_images(jobs: list, style: str) -> list:
    """jobs: dicts with name, mode (t2i|edit), prompt, seed, w, h, out (asset path), refs (asset paths)."""
    import math, time, torch
    from PIL import Image
    from diffusers import FlowMatchEulerDiscreteScheduler
    from huggingface_hub import hf_hub_download
    sched_cfg = {"base_image_seq_len": 256, "base_shift": math.log(3), "invert_sigmas": False,
                 "max_image_seq_len": 8192, "max_shift": math.log(3), "num_train_timesteps": 1000,
                 "shift": 1.0, "shift_terminal": None, "stochastic_sampling": False,
                 "time_shift_type": "exponential", "use_beta_sigmas": False, "use_dynamic_shifting": True,
                 "use_exponential_sigmas": False, "use_karras_sigmas": False}
    t0 = time.time(); out = []; meta = {"gpu": torch.cuda.get_device_name(0), "loads": []}
    OLD_NEG = ("text, letters, words, numbers, signage, logo, watermark, photo, photorealistic, 3d render, anime, "
               "extra fingers, deformed hands, extra people, silhouettes")
    for mode in ("t2i", "edit"):           # all text-to-image first, then all poses: each model loads once
        todo = [j for j in jobs if j.get("mode", "t2i").startswith(mode)]
        if not todo:
            continue
        tl = time.time()
        sch = FlowMatchEulerDiscreteScheduler.from_config(sched_cfg)
        if mode == "t2i":
            from diffusers import DiffusionPipeline
            pipe = DiffusionPipeline.from_pretrained(BASE, torch_dtype=torch.bfloat16).to("cuda")
            for j in [x for x in todo if x.get("mode") == "t2i_base30"]:   # A/B only: old slow path, no LoRA
                t = time.time()
                img = pipe(prompt=full_prompt(j, style), negative_prompt=OLD_NEG, width=j.get("w", 1664), height=j.get("h", 928),
                           num_inference_steps=30, true_cfg_scale=4.0, generator=torch.Generator("cuda").manual_seed(j.get("seed", 7))).images[0]
                p = pathlib.Path("/assets/" + j["out"]); p.parent.mkdir(parents=True, exist_ok=True); img.save(p, "PNG")
                out.append({"name": j["name"], "out": j["out"], "secs": round(time.time() - t, 1)})
            todo = [x for x in todo if x.get("mode") != "t2i_base30"]
            pipe.scheduler = sch
            pipe.load_lora_weights(hf_hub_download(LREPO, LBASE))
        else:
            from diffusers import QwenImageEditPlusPipeline
            pipe = QwenImageEditPlusPipeline.from_pretrained(EDIT, scheduler=sch, torch_dtype=torch.bfloat16).to("cuda")
            pipe.load_lora_weights(hf_hub_download(LREPO, LEDIT))
        pipe.fuse_lora()
        meta["loads"].append({mode: round(time.time() - tl, 1)})
        for j in todo:
            t = time.time()
            g = torch.Generator("cuda").manual_seed(j.get("seed", 7))
            kw = dict(prompt=full_prompt(j, style), negative_prompt=" ", num_inference_steps=j.get("steps", 8),
                      true_cfg_scale=1.0, generator=g)
            if mode == "t2i":
                img = pipe(width=j.get("w", 1664), height=j.get("h", 928), **kw).images[0]
            else:
                refs = [Image.open("/assets/" + r).convert("RGB") for r in j["refs"]]
                img = pipe(image=refs, **kw).images[0]
            p = pathlib.Path("/assets/" + j["out"]); p.parent.mkdir(parents=True, exist_ok=True)
            img.save(p, "PNG")
            out.append({"name": j["name"], "out": j["out"], "secs": round(time.time() - t, 1)})
        del pipe; torch.cuda.empty_cache()
    avol.commit()
    meta["total_s"] = round(time.time() - t0, 1)
    out.append({"name": "_meta", **meta})
    return out


@app.function(image=cpu_image, volumes={"/weights": wvol, "/assets": avol}, timeout=600, cpu=2, memory=3072,
              max_containers=1, scaledown_window=2)
def cutouts(pairs: list) -> list:
    """pairs: [src_asset, dst_asset]. Transparent character cutouts, CPU only."""
    from rembg import new_session, remove
    from PIL import Image
    s = new_session("isnet-general-use"); done = []
    for src, dst in pairs:
        im = Image.open("/assets/" + src).convert("RGB")
        cut = remove(im, session=s, alpha_matting=True)
        bb = cut.getbbox(); cut = cut.crop(bb) if bb else cut
        p = pathlib.Path("/assets/" + dst); p.parent.mkdir(parents=True, exist_ok=True); cut.save(p, "PNG")
        done.append(dst)
    avol.commit(); wvol.commit()
    return done


@app.local_entrypoint()
def fetch_weights(which: str = "base"):
    print("OK weights at", download_weights.remote(which))


@app.local_entrypoint()
def images(job: str, force: str = ""):
    """Resolve hashes, send only missing pictures to the GPU, then cut out characters, then
    copy previews (JPG) into out/ for the owner. force=name1,name2 re-makes those (new seed)."""
    root = pathlib.Path(__file__).resolve().parents[1]
    jp = root / job; jobs = json.loads(jp.read_text())
    style = (root / "kit" / "style_prompt.txt").read_text().strip()
    forced = set(x for x in force.split(",") if x)
    by_name = {}; ordered = []
    for j in jobs:                       # refs must point to earlier jobs (master before poses)
        j = dict(j)
        if j["name"] in forced:
            j["seed"] = j.get("seed", 7) + 1000
        rh = [by_name[r]["hash"] for r in j.get("refs_from", [])]
        j["hash"] = job_hash(j, style, rh)
        j["out"] = f"lib/{j.get('lib', 'misc')}/{j['name']}__{j['hash']}.png"
        j["refs"] = [by_name[r]["out"] for r in j.get("refs_from", [])]
        by_name[j["name"]] = j; ordered.append(j)
    have = set(which_exist.remote([j["out"] for j in ordered]))
    todo = [j for j in ordered if j["out"] not in have]
    print(f"PLAN {len(ordered)} pictures, {len(have)} cached, {len(todo)} to make")
    meta = []
    if todo:
        for r in run_images.remote(todo, style):
            meta.append(r); print("IMG", json.dumps(r))
    cut_pairs = [(j["out"], j["out"].replace(".png", "__cut.png")) for j in ordered if j.get("cutout")]
    have_cut = set(which_exist.remote([d for _, d in cut_pairs]))
    need_cut = [p for p in cut_pairs if p[1] not in have_cut]
    if need_cut:
        print("CUT", cutouts.remote(need_cut))
    # manifest + small previews for review
    od = root / "out" / jp.parent.name / "img"; od.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    want = [j["out"] for j in ordered] + [d for _, d in cut_pairs]
    blobs = read_assets.remote(want)
    for path, b in blobs.items():
        im = Image.open(io.BytesIO(b))
        name = pathlib.Path(path).name.split("__")[0] + ("_cut" if path.endswith("__cut.png") else "")
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, (128, 128, 128)); bg.paste(im, mask=im.getchannel("A")); im = bg
        im.convert("RGB").save(od / f"{name}.jpg", quality=88)
    man = {j["name"]: {"asset": j["out"], "hash": j["hash"], "cut": j["out"].replace(".png", "__cut.png") if j.get("cutout") else None}
           for j in ordered}
    (od / "asset_manifest.json").write_text(json.dumps(man, indent=1))
    (od / "img_meta.json").write_text(json.dumps(meta, indent=1))
    print("OK images done")
