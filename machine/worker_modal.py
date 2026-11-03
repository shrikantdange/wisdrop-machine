"""Wisdrop GPU worker on Modal.

Called from GitHub Actions (thin client). Tokens come from the
MODAL_TOKEN_ID / MODAL_TOKEN_SECRET repository secrets, never from files.

  modal run machine/worker_modal.py::gpu_check      # cheap smoke test (~1 min T4)
"""
import modal

app = modal.App("wisdrop-worker")

base = modal.Image.debian_slim(python_version="3.11").pip_install("torch==2.6.0")

weights = modal.Volume.from_name("wisdrop-weights", create_if_missing=True)


@app.function(gpu="T4", image=base, timeout=300, volumes={"/weights": weights})
def gpu_probe() -> dict:
    import os, torch
    ok = torch.cuda.is_available()
    out = {"cuda": ok, "weights_files": sorted(os.listdir("/weights"))[:20]}
    if ok:
        out["gpu"] = torch.cuda.get_device_name(0)
        out["vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)
        x = torch.randn(2048, 2048, device="cuda")
        out["matmul_ok"] = bool((x @ x).isfinite().all().item())
    return out


@app.local_entrypoint()
def gpu_check():
    r = gpu_probe.remote()
    print("WORKER", r)
    if not (r.get("cuda") and r.get("matmul_ok")):
        raise SystemExit("FAIL gpu probe")
    print("OK modal GPU worker reachable")
