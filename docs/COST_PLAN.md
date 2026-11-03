# Cost and speed plan (Modal free $30 / month)

Prices from modal.com/pricing (read 2026-11-03): A100-80GB $2.50/h, T4 $0.59/h,
CPU $0.047 per core-hour. Times below are estimates until measured.

| Step | Before | Now | How |
|---|---|---|---|
| Images | 30 steps x CFG = 60 passes, ~46 s each on A100 | 8 passes, target ~7 s | Lightning 8-step LoRA (Apache 2.0) |
| Character poses | new prompt per pose, face drifts | edit from master sheet | Qwen-Image-Edit-2509 + Lightning |
| Redo | whole batch again | only changed pictures/lines | content-hash cache in volume wisdrop-assets |
| Voice | every line every run | only changed lines | line hash (text, preset, voice ref) |
| Motion | none | code-drawn, free | PIL render, no AI video |
| Render | 1 slow sandbox CPU, ~1 h | ~20 Modal CPUs side by side, minutes | parallel chunks, about $0.04 per episode |
| Mix + master | sandbox | Modal CPU, cents | same mix.py |
| Outputs | WAV/PNG force-pushed to git | Modal volume + Actions artifacts | repo stays small |

Rules: one GPU container, one call per batch, scaledown 2 s, weights downloaded on CPU.
Nothing reaches the GPU if every hash is cached. Library first: a new episode makes only
the new cast, poses and sets it needs.

Budget estimate per episode once the library exists: images $0.20-0.60, voice ~$0.10,
render+mix ~$0.05. First library build is a one-off (~150 pictures, roughly $1-2).
Set a workspace budget in Modal (Settings > Usage & Billing) so spend cannot pass the credit.
