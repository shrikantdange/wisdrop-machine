"""Wisdrop images on Modal, v3: fast, cached, library-first.

Speed / cost (see docs/OPERATOR_GUIDE.md (cost section)):
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
         .pip_install("torch==2.6.0", "torchvision==0.21.0", "diffusers>=0.36.0", "transformers>=4.51,<5", "accelerate", "peft>=0.17",
                      "safetensors", "sentencepiece", "pillow")
         .env({"HF_HOME": HF, "HF_HUB_DISABLE_TELEMETRY": "1"}))
cpu_image = (modal.Image.debian_slim(python_version="3.11")
             .pip_install("rembg[cpu]==2.0.67", "pillow", "huggingface_hub")
             .env({"U2NET_HOME": "/weights/u2net", "HF_HOME": HF}))

qc_image = (modal.Image.debian_slim(python_version="3.11")
            .apt_install("libgl1", "libglib2.0-0")
            .pip_install("torch==2.6.0", "torchvision==0.21.0", index_url="https://download.pytorch.org/whl/cpu")
            .pip_install("rapidocr_onnxruntime==1.4.4", "pillow")
            .env({"TORCH_HOME": "/weights/torch"}))
MAX_QC_ROUNDS = 1      # a plate that keeps failing is flagged for a human look, never looped forever

NO_PEOPLE = " The place is completely empty: no people, no figures, no silhouettes, no reflections of people."
NO_TEXT = " Every surface is blank: no writing, no letters, no numbers, no signs, no labels, no screens with text."


def job_hash(j: dict, style: str, ref_hashes: list) -> str:
    key = json.dumps({"e": ENGINE, "mode": j.get("mode", "t2i"), "s": style, "p": j["prompt"],
                      "seed": j.get("seed", 7), "w": j.get("w", 1664), "h": j.get("h", 928),
                      "steps": j.get("steps", 8), "refs": ref_hashes, "people": j.get("people", False)}, sort_keys=True)
    return hashlib.sha256(key.encode()).hexdigest()[:16]


EMPTY_STYLE = (("clean inked outlines on people and objects, realistic adult proportions and believable faces,", "clean inked outlines on every object,"),
               (" No text, no letters, no numbers, no signs with writing, no logos, no watermarks.", ""))
EMPTY = " Deserted and unoccupied, a still place after hours, every seat vacant. All surfaces plain and unmarked, blank walls, blank screens."


def full_prompt(j: dict, style: str) -> str:
    """Sets: with guidance off (Lightning), naming what to avoid draws it. So the style is stripped of
    people words and 'no text' lists, and the prompt says positively that the place is deserted and blank."""
    if j.get("people", False):
        return style + " " + j["prompt"] + NO_TEXT
    for a, b in EMPTY_STYLE:
        style = style.replace(a, b)
    return style + " " + j["prompt"] + EMPTY


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
                avol.commit()
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
                ek = {"width": j["w"], "height": j["h"]} if j.get("w") else {}
                img = pipe(image=refs, **ek, **kw).images[0]
            p = pathlib.Path("/assets/" + j["out"]); p.parent.mkdir(parents=True, exist_ok=True)
            img.save(p, "PNG")
            out.append({"name": j["name"], "out": j["out"], "secs": round(time.time() - t, 1)})
            avol.commit()                    # keep every finished picture even if a later step fails
        del pipe; import gc; gc.collect(); torch.cuda.empty_cache()
    avol.commit()
    meta["total_s"] = round(time.time() - t0, 1)
    out.append({"name": "_meta", **meta})
    return out


@app.function(image=qc_image, volumes={"/weights": wvol, "/assets": avol}, timeout=600, cpu=2, memory=4096,
              max_containers=1, scaledown_window=2)
def qc(paths: list) -> dict:
    """Free CPU check for plates that must be empty and blank: people (torchvision detector,
    BSD) and readable text (RapidOCR, Apache 2.0). Result cached next to each picture."""
    import os, torch, torchvision
    from PIL import Image
    from rapidocr_onnxruntime import RapidOCR
    res = {}; todo = []
    for p in paths:
        q = "/assets/" + p + ".qc.json"
        if os.path.exists(q):
            res[p] = json.load(open(q))
        else:
            todo.append(p)
    if todo:
        wts = torchvision.models.detection.FasterRCNN_MobileNet_V3_Large_FPN_Weights.DEFAULT
        det = torchvision.models.detection.fasterrcnn_mobilenet_v3_large_fpn(weights=wts).eval()
        ocr = RapidOCR()
        for p in todo:
            im = Image.open("/assets/" + p).convert("RGB")
            x = torchvision.transforms.functional.to_tensor(im)
            with torch.inference_mode():
                o = det([x])[0]
            people = [round(float(sc), 2) for lb, sc in zip(o["labels"], o["scores"]) if int(lb) == 1 and float(sc) > 0.55]
            txt, _ = ocr("/assets/" + p)
            words = [t[1] for t in (txt or []) if float(t[2]) > 0.8 and len(t[1].strip()) >= 3]
            r = {"people": people, "text": words, "pass": not people and not words}
            json.dump(r, open("/assets/" + p + ".qc.json", "w")); res[p] = r
        avol.commit(); wvol.commit()
    return res


@app.function(image=cpu_image, volumes={"/assets": avol}, timeout=60, cpu=0.25, memory=512)
def write_asset(path: str, data: bytes):
    p = pathlib.Path("/assets/" + path); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data); avol.commit()


@app.function(image=cpu_image, volumes={"/weights": wvol, "/assets": avol}, timeout=600, cpu=2, memory=3072,
              max_containers=1, scaledown_window=2)
def cutouts(pairs: list) -> list:
    """pairs: [src_asset, dst_asset]. Transparent character cutouts, CPU only."""
    from rembg import new_session, remove
    from PIL import Image
    s = new_session("birefnet-general"); done = []
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
    def place(j):
        rh = [by_name[r]["hash"] for r in j.get("refs_from", [])]
        j["hash"] = job_hash(j, style, rh)
        j["out"] = f"lib/{j.get('lib', 'misc')}/{j['name']}__{j['hash']}.png"
        j["refs"] = [by_name[r]["out"] for r in j.get("refs_from", [])]
    have = set(which_exist.remote([j["out"] for j in ordered]))
    todo = [j for j in ordered if j["out"] not in have]
    print(f"PLAN {len(ordered)} pictures, {len(have)} cached, {len(todo)} to make")
    meta = []; flagged = {}; made = set()
    import sys as _s; _s.path.insert(0, str(root / "machine")); import cost
    ep_name = str(jp.parent.relative_to(root))
    if todo: cost.guard(ep_name, 70 * len({j.get("mode", "t2i") for j in todo}) + 50 * len(todo), f"images {len(todo)} pictures")
    for rnd in range(MAX_QC_ROUNDS + 1):
        if todo:
            for mode in ("t2i", "edit"):      # one model per call: both together do not fit in 80 GB
                part = [j for j in todo if j.get("mode", "t2i") == mode]
                if part:
                    with cost.timer() as tm:
                        for r in run_images.remote(part, style):
                            meta.append(r); print("OK img", json.dumps(r))
                    cost.add(ep_name, f"images_{mode}", tm.secs, gpu="A100-80GB"); made |= {j["name"] for j in part}
        checks = [j for j in ordered if not j.get("people") and j.get("mode", "t2i") == "t2i" and j["name"] in made]   # cached pictures passed QC when made
        res = qc.remote([j["out"] for j in checks]) if checks else {}
        bad = [j for j in checks if not res[j["out"]]["pass"]]
        for j in bad:
            print("REVIEW", j["name"], json.dumps(res[j["out"]]))
        if not bad or rnd == MAX_QC_ROUNDS:
            flagged = {j["name"]: res[j["out"]] for j in bad}; break
        todo = []
        for j in bad:                       # same prompt, next seed; hash changes so it is a new picture
            j["seed"] = j.get("seed", 7) + 1000; place(j); todo.append(j)
        have = set(which_exist.remote([j["out"] for j in todo])); todo = [j for j in todo if j["out"] not in have]
    for n, r in flagged.items():
        print("REVIEW", n, json.dumps(r))
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
        if path.endswith("__cut.png"): im.save(od / (pathlib.Path(path).name.rsplit("__", 2)[0] + "_cut.png"))   # keep alpha (thumbnails)
        stem = pathlib.Path(path).name.replace("__cut.png", ".png"); name = stem.rsplit("__", 1)[0] + ("_cut" if path.endswith("__cut.png") else "")
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, (128, 128, 128)); bg.paste(im, mask=im.getchannel("A")); im = bg
        im.convert("RGB").save(od / f"{name}.jpg", quality=88)
    man = {j["name"]: {"asset": j["out"], "hash": j["hash"], "cut": j["out"].replace(".png", "__cut.png") if j.get("cutout") else None}
           for j in ordered}
    for n in flagged:
        man[n]["review"] = flagged[n]
    (od / "asset_manifest.json").write_text(json.dumps(man, indent=1))
    write_asset.remote(f"eps/{jp.parent.name}/asset_manifest.json", json.dumps(man, indent=1).encode())
    (od / "img_meta.json").write_text(json.dumps(meta, indent=1))
    print("OK images done" if not flagged else f"WAIT images done, {len(flagged)} flagged for a look: {', '.join(flagged)}")
