"""Measured spend per run + the GPU spend guard (docs/EDITING_CRAFT.md is about craft; this is about money).

Prices from modal.com/pricing (read 2026-11-03): T4 $0.000164/s, A100-80GB $0.000694/s,
CPU $0.0000131 per core-second, memory $0.00000222 per GiB-second. Time is measured around each
remote call (wall clock, includes cold start), so it is a slight over-estimate of the bill.

out/<ep>/cost.json collects every step of the current run. The guard: before a GPU call, the
worker estimates the GPU seconds it needs; if used + planned > WIS_MAX_GPU_S (workflow input
max_gpu_seconds, default 600) it prints FAIL and stops before spending anything.
"""
import json, os, pathlib, time
PRICE = {"T4": 0.000164, "A100-80GB": 0.000694, "cpu_core_s": 0.0000131, "mem_gib_s": 0.00000222}
ROOT = pathlib.Path(__file__).resolve().parents[1]

def _path(ep): p = ROOT / "out" / pathlib.Path(ep).name / "cost.json"; p.parent.mkdir(parents=True, exist_ok=True); return p
def load(ep):
    p = _path(ep); return json.loads(p.read_text()) if p.exists() else {"steps": []}
def add(ep, step, secs, gpu=None, cores=1.0, mem_gib=2.0, n=1):
    usd = secs * PRICE[gpu] if gpu else secs * (cores * PRICE["cpu_core_s"] + mem_gib * PRICE["mem_gib_s"])
    c = load(ep); c["steps"].append({"step": step, "secs": round(secs, 1), "gpu": gpu, "calls": n, "usd": round(usd, 5)})
    c["total_usd"] = round(sum(s["usd"] for s in c["steps"]), 4); c["gpu_secs"] = round(sum(s["secs"] for s in c["steps"] if s["gpu"]), 1)
    _path(ep).write_text(json.dumps(c, indent=1)); print(f"COST {step}: {secs:.1f} s{' on ' + gpu if gpu else ' CPU'} = ${usd:.4f} (run total ${c['total_usd']:.4f})")
def guard(ep, planned_gpu_s, what):
    lim = float(os.environ.get("WIS_MAX_GPU_S", "600")); used = load(ep).get("gpu_secs", 0)
    if used + planned_gpu_s > lim:
        print(f"FAIL spend guard: {what} needs ~{planned_gpu_s:.0f} GPU s, {used:.0f} used, limit {lim:.0f} (raise max_gpu_seconds only on purpose)")
        raise SystemExit(3)
    print(f"PLAN {what}: ~{planned_gpu_s:.0f} GPU s (limit {lim:.0f}, used {used:.0f})")
class timer:
    def __enter__(self): self.t = time.time(); return self
    def __exit__(self, *a): self.secs = time.time() - self.t
