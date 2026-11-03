"""Frame fill check (v5): share of the frame that is flat, empty board. Rule: <= 35 % (FILL_MAX).
  python machine/frame_fill.py <video.mp4 | frames_dir> [--fps 2]
Flat = 24x24 px blocks (at 480x270) whose brightness spread is tiny. Grain is ignored by a light blur.
"""
import glob, json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageFilter
FILL_MAX = 0.35
def flat_share(im):
    a = np.asarray(im.convert("L").resize((480, 270)).filter(ImageFilter.GaussianBlur(2)), float); b = 15
    blk = a[:270 // b * b, :480 // b * b].reshape(270 // b, b, 480 // b, b).swapaxes(1, 2).reshape(-1, b * b)
    return float((blk.std(1) < 2.2).mean())
def check(src, fps=2):
    if os.path.isdir(src): fs = sorted(glob.glob(os.path.join(src, "*.jpg")) + glob.glob(os.path.join(src, "*.png")))
    else:
        tmp = tempfile.mkdtemp(); subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps={fps}", os.path.join(tmp, "f%04d.jpg")], check=True)
        fs = sorted(glob.glob(os.path.join(tmp, "*.jpg")))
    vals = [round(flat_share(Image.open(f)), 3) for f in fs]; over = [(k / fps, v) for k, v in enumerate(vals) if v > FILL_MAX]
    res = {"rule": "F1 flat empty area <= 35 % of the frame", "status": "REVIEW" if over else "OK", "max": max(vals + [0]), "mean": round(float(np.mean(vals)) if vals else 0, 3), "over": over[:8]}
    print(f"{res['status']}: {res['rule']} (max {res['max']:.0%}, mean {res['mean']:.0%}, {len(over)} of {len(vals)} frames over)"); return res
if __name__ == "__main__":
    print(json.dumps(check(sys.argv[1], int(sys.argv[sys.argv.index("--fps") + 1]) if "--fps" in sys.argv else 2)))
