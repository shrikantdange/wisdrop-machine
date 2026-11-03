"""Wisdrop COLLAGE look (v2, owner-approved 2026-11-03): Vox / BBC-style premium motion graphics.

Charcoal textured paper, cream torn-paper cards, real photos (CC / public domain) and the
occasional AI picture, all run through ONE treatment (duotone + halftone + torn edge + tape),
yellow highlighter, red marker. Everything here is code: no GPU, no licence risk.

shots_render.py imports this when library.json has "look": "collage". It overrides the
palette, board(), the caption and the tag, treats every picture, and adds shot types
`photo` and `kinetic`. All other shot types keep working on the new board.
"""
import math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops

W, H = 1920, 1080
CHAR = (27, 26, 24); CREAM = (241, 233, 215); INK = (22, 21, 20)
YEL = (247, 209, 58); RED = (226, 70, 54); TEAL = (42, 127, 143)
# duotone per time of day: (shadow ink, light paper)
DUO = {"dawn": ((30, 36, 58), (236, 214, 196)), "morning": ((44, 34, 26), (246, 226, 188)),
       "day": ((30, 32, 34), (238, 234, 222)), "afternoon": ((48, 30, 20), (248, 214, 160)),
       "dusk": ((40, 22, 36), (246, 196, 150)), "night": ((14, 20, 34), (214, 196, 160)),
       "rain_night": ((12, 22, 36), (170, 196, 214)), "screen_glow": ((10, 22, 40), (176, 214, 236)),
       "archive": ((26, 24, 22), (232, 222, 200))}

_rng = np.random.default_rng(11)
def _paper(base, amp, size=(W, H)):
    import zlib; _rng = np.random.default_rng(zlib.crc32(f"paper:{base}:{amp}:{size}".encode()))   # AMC-W1: same paper on any worker
    n = _rng.normal(0, 1, (size[1] // 3, size[0] // 3))
    fib = Image.fromarray(np.clip(128 + n * amp, 0, 255).astype(np.uint8)).resize(size, Image.BICUBIC)
    streak = Image.fromarray(np.clip(128 + _rng.normal(0, 1, (size[1] // 2, 8)) * amp * .8, 0, 255).astype(np.uint8)).resize(size, Image.BICUBIC)
    t = ImageChops.add(fib, streak, 2, -64 if False else 0).filter(ImageFilter.GaussianBlur(1.2))
    col = Image.new("RGB", size, base)
    return ImageChops.overlay(col, t.convert("RGB"))
BOARD = _paper(CHAR, 22)
# faint halftone corner glow on the board
_d = ImageDraw.Draw(BOARD)
for y in range(0, H, 22):
    for x in range(W - 520, W, 22):
        r = max(0, 4.2 - math.hypot(x - W, y - 0) / 140)
        if r > .4: _d.ellipse([x - r, y - r, x + r, y + r], fill=(48, 46, 42))
CREAMTEX = _paper(CREAM, 14, (1200, 900))

def board():
    return BOARD.copy()

def halftone(L, cell=7, k=.9):
    """L: grey image. Returns grey image of dots (multiply layer)."""
    w, h = L.size; sm = L.resize((max(1, w // cell), max(1, h // cell)), Image.BILINEAR)
    out = Image.new("L", (w, h), 255); d = ImageDraw.Draw(out); a = np.asarray(sm)
    for j in range(a.shape[0]):
        for i in range(a.shape[1]):
            r = (1 - a[j, i] / 255) ** .9 * cell * .62 * k
            if r > .5:
                cx, cy = i * cell + cell / 2 + (cell / 2 if j % 2 else 0), j * cell + cell / 2
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=0)
    return out

_treat = {}
def treat(img, mood="archive", key=None, dots=True):
    """Duotone + soft halftone + paper grain. Cached per key."""
    k = key or (id(img), mood)
    if k in _treat: return _treat[k]
    lo, hi = DUO.get(mood, DUO["archive"])
    L = ImageOps.autocontrast(img.convert("L"), cutoff=1)
    L = L.point(lambda v: int(255 * (v / 255) ** 1.08))
    duo = ImageOps.colorize(L, lo, hi, mid=tuple((a + b) // 2 + 6 for a, b in zip(lo, hi)))
    col = Image.blend(duo, img.convert("RGB"), .22)          # keep a breath of the original colour
    if dots:
        ht = halftone(L, cell=max(5, img.size[0] // 260))
        col = Image.composite(col, ImageChops.multiply(col, Image.merge("RGB", [ht.point(lambda v: 150 + v * 105 // 255)] * 3)), Image.new("L", col.size, 120))
    tex = CREAMTEX.resize(col.size).convert("L").point(lambda v: 128 + (v - 128) // 2)
    col = ImageChops.overlay(col, Image.merge("RGB", [tex] * 3))
    _treat[k] = col; return col

def torn_mask(w, h, seed=3, depth=10):
    r = random.Random(seed); m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
    pts = []
    for x in range(0, w + 1, 14): pts.append((x, r.uniform(0, depth)))
    for y in range(0, h + 1, 14): pts.append((w - r.uniform(0, depth), y))
    for x in range(w, -1, -14): pts.append((x, h - r.uniform(0, depth)))
    for y in range(h, -1, -14): pts.append((r.uniform(0, depth), y))
    d.polygon(pts, fill=255); return m.filter(ImageFilter.GaussianBlur(.6))

_fr = {}
def framed(img, width, seed=1, border=18, tape=True, mood="archive", key=None):
    """Treated picture on a torn cream paper card with tape and a soft shadow (RGBA)."""
    k = (key or id(img), width, seed, mood)
    if k in _fr: return _fr[k]
    tw = width - 2 * border; th = int(tw * img.size[1] / img.size[0])
    pic = treat(img, mood, key=(key, mood) if key else None).resize((tw, th), Image.LANCZOS)
    cw, ch = width, th + 2 * border
    card = CREAMTEX.resize((cw, ch)).copy(); card.paste(pic, (border, border))
    rgba = card.convert("RGBA"); rgba.putalpha(torn_mask(cw, ch, seed))
    if tape:
        r = random.Random(seed); td = ImageDraw.Draw(rgba)
        for cx in (r.uniform(.12, .25) * cw, r.uniform(.75, .88) * cw):
            tw2, th2 = 150, 44; tp = Image.new("RGBA", (tw2, th2), (236, 226, 190, 175))
            tp = tp.rotate(r.uniform(-12, 12), expand=True, resample=Image.BICUBIC)
            rgba.alpha_composite(tp, (int(cx - tp.size[0] / 2), -8 if r.random() < 2 else 0))
    _fr[k] = rgba; return rgba

def drop_card(fr, card, cx, cy, rot=0.0, a=1.0, scale=1.0):
    c = card
    if scale != 1.0: c = c.resize((max(1, int(c.size[0] * scale)), max(1, int(c.size[1] * scale))), Image.BILINEAR)
    if rot: c = c.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0)); sh.putalpha(c.split()[3].point(lambda v: int(v * .55 * a)))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    x, y = int(cx - c.size[0] / 2), int(cy - c.size[1] / 2)
    fr.paste((0, 0, 0), (x + 12, y + 18), sh)
    if a < 1: c = c.copy(); c.putalpha(c.split()[3].point(lambda v: int(v * a)))
    fr.paste(c, (x, y), c)

def highlighter(dr, box, u, col=YEL):
    """Marker swipe over box [x0,y0,x1,y1], u 0-1 progress, slightly uneven ends."""
    x0, y0, x1, y1 = box; xe = x0 + (x1 - x0) * max(0, min(1, u))
    if xe <= x0 + 2: return
    dr.polygon([(x0 - 8, y0 + 4), (xe + 6, y0), (xe + 10, y1), (x0 - 4, y1 + 4)], fill=col)

def marker_circle(dr, box, u, col=RED, w=7):
    x0, y0, x1, y1 = box; cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 + 18, (y1 - y0) / 2 + 14
    n = int(64 * max(0, min(1, u)) * 1.1); pts = []
    for k in range(n):
        a = -2.2 + k / 64 * 2 * math.pi; wob = 1 + .03 * math.sin(k * .7)
        pts.append((cx + rx * wob * math.cos(a), cy + ry * wob * math.sin(a)))
    if len(pts) > 1: dr.line(pts, fill=col, width=w, joint="curve")

def sticker(fr, text, x, y, font, bg=YEL, fg=INK, rot=-3):
    d0 = ImageDraw.Draw(fr); tw = d0.textlength(text, font=font)
    im = Image.new("RGBA", (int(tw) + 36, font.size + 26), bg + (255,))
    ImageDraw.Draw(im).text((18, 8), text, font=font, fill=fg)
    im = im.rotate(rot, expand=True, resample=Image.BICUBIC); fr.paste(im, (x, y), im)
