#!/usr/bin/env python3
"""Vertical Shorts (1080x1920) cut from a rendered episode. CPU only (ffmpeg + PIL). Shorts start at ep03.

  python machine/shorts_cut.py <video.mp4> <timeline.json> <first_line> <last_line> <out.mp4> [--title "3 words max"]

Takes the span of lines first..last (line start - 0.1 s to line end + 0.4 s), keeps the 16:9 picture
full width in the middle, a blurred zoom of the same frames fills top and bottom, and a code-drawn
title sits in the top band (words drawn by code, never by an image model). Burned-in captions stay.
Keep a Short self-contained: a hook line first, one fact, a payoff; no "watch the full video" begging.
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "kit", "fonts", "Anton.ttf")


def title_png(text, path):
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if text:
        size = 150
        while size > 60 and d.textlength(text.upper(), font=ImageFont.truetype(FONT, size)) > 980: size -= 6
        f = ImageFont.truetype(FONT, size); w = d.textlength(text.upper(), font=f)
        d.rectangle([(1080 - w) / 2 - 24, 250, (1080 + w) / 2 + 24, 270 + size * 1.15], fill=(247, 209, 58, 255))
        d.text(((1080 - w) / 2, 256), text.upper(), font=f, fill=(14, 14, 16))
    d.rectangle([0, 1908, 1080, 1920], fill=(247, 209, 58, 255))
    im.save(path)


def main(video, tl_path, a, b, out, title=""):
    tl = json.load(open(tl_path)); segs = {s["i"]: s for s in tl["segs"]}
    if a not in segs or b not in segs: print(f"FAIL lines {a}-{b} not in timeline"); return 1
    t0 = max(0, segs[a]["start"] - .1); t1 = min(tl["dur"], segs[b]["end"] + .4)
    if t1 - t0 > 60: print(f"REVIEW short is {t1 - t0:.1f} s; keep it under 60 s unless the owner says otherwise")
    tmp = tempfile.mkdtemp(); tp = os.path.join(tmp, "title.png"); title_png(title, tp)
    fg = ("[0:v]split[a][b];[a]scale=1080:-2,setsar=1[fg];[b]scale=-2:1920,crop=1080:1920,boxblur=24:2,eq=brightness=-0.12[bg];"
          "[bg][fg]overlay=0:(H-h)/2[v];[v][1:v]overlay=0:0[o]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", video, "-i", tp, "-filter_complex", fg,
           "-map", "[o]", "-map", "0:a?", "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "160k", "-r", "30", out]
    subprocess.run(cmd, check=True)
    print(f"OK short {out}: lines {a}-{b}, {t1 - t0:.1f} s, 1080x1920")
    return 0


if __name__ == "__main__":
    args = [x for x in sys.argv[1:]]
    title = ""
    if "--title" in args: k = args.index("--title"); title = args[k + 1]; del args[k:k + 2]
    if len(args) != 5: print(__doc__); sys.exit(2)
    sys.exit(main(args[0], args[1], int(args[2]), int(args[3]), args[4], title))
