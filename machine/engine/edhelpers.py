"""Wisdrop shared drawing helpers (easing, glow, grain, zoom, fonts). Used by shots_render.py."""
import sys, math, random, subprocess, json, zlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance

V = "C"
W, H, FPS = 1920, 1080, 30
import os
import sys as _s; _s.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); from paths import KIT
NAVY = (16, 24, 42); PAPER = (244, 238, 224); GOLD = (236, 184, 64); RED = (232, 64, 56)
GREY = (150, 158, 176); WHITE = (255, 255, 255); GREEN = (70, 214, 120)
ANTON = os.path.join(KIT, "fonts/Anton.ttf"); MONO = os.path.join(KIT, "fonts/DejaVuSansMono-Bold.ttf")
SANS = os.path.join(KIT, "fonts/DejaVuSans-Bold.ttf")
SERIF = os.path.join(KIT, "fonts/DejaVuSerif-Bold.ttf")
_fc = {}
def F(p, s):
    k = (p, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(p, s)
    return _fc[k]
random.seed(7); np.random.seed(7)

def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def eout(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def back(t):  # overshoot
    t = max(0.0, min(1.0, t)); c = 1.7; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

def plate(name, blur=0, scale=1.18, grade=None):
    im = Image.open(P + name).convert("RGB").resize((int(W * scale), int(H * scale)), Image.LANCZOS)
    if grade: im = grade(im)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return im
def cut(name, h):
    im = Image.open(L + name).convert("RGBA"); r = h / im.size[1]
    im = im.resize((int(im.size[0] * r), int(h)), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32); al = a[:, :, 3]
    edge = al < 250; mx = np.maximum(a[:, :, 0], a[:, :, 2])
    a[:, :, 1] = np.where(edge & (a[:, :, 1] > mx), mx, a[:, :, 1])   # kill green fringe
    im = Image.fromarray(a.astype(np.uint8)); alc = im.getchannel("A").filter(ImageFilter.MinFilter(3)); im.putalpha(alc)
    return im
def match(sp, tint, k, rim=None, rk=0.0):
    """colour-match a cutout to its scene: multiply toward the key light, then a soft light-wrap rim"""
    a = np.asarray(sp).astype(np.float32); rgb = a[:, :, :3]
    rgb = rgb * (1 - k) + rgb * (np.array(tint, np.float32) / 255.0) * k
    if rim is not None:
        al = Image.fromarray(a[:, :, 3].astype(np.uint8)); inner = np.asarray(al.filter(ImageFilter.GaussianBlur(9))).astype(np.float32)
        wrap = np.clip((a[:, :, 3] - inner) / 120.0, 0, 1)[:, :, None] * rk
        rgb = rgb * (1 - wrap) + np.array(rim, np.float32) * wrap
    a[:, :, :3] = np.clip(rgb, 0, 255); return Image.fromarray(a.astype(np.uint8))

def warm(im):  # pull green out, keep amber/navy
    a = np.asarray(im).astype(np.float32)
    a[:, :, 1] *= 0.93; a[:, :, 0] *= 1.03
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

# v3: no example assets are loaded here (episode pictures come from the asset manifest)

def crop_cam(pl, t, z0, z1, dx, dy):
    z = z0 + (z1 - z0) * ease(t); bw, bh = pl.size; base = bw / (W * 1.18) if False else 1
    cw, ch = W / z * (bw / W) / 1.18, H / z * (bh / H) / 1.18
    cx = bw / 2 + dx * (ease(t) - .5) * bw * 0.05; cy = bh / 2 + dy * (ease(t) - .5) * bh * 0.05
    return pl.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.BILINEAR)

def paste(fr, sp, x, y, s=1.0, rot=0.0, breathe=0.0, alpha=1.0, shadow=True):
    if s != 1.0 or breathe:
        sp = sp.resize((max(1, int(sp.size[0] * s)), max(1, int(sp.size[1] * s * (1 + breathe)))), Image.BILINEAR)
    if rot: sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1: a = sp.getchannel("A").point(lambda v: int(v * alpha)); sp = sp.copy(); sp.putalpha(a)
    x, y = int(x - sp.size[0] / 2), int(y - sp.size[1])  # anchor = bottom centre
    if shadow:  # soft contact shadow + rim separation
        sh = Image.new("RGBA", (sp.size[0], 60), (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
        d.ellipse([sp.size[0] * .15, 10, sp.size[0] * .85, 50], fill=(0, 0, 0, int(110 * alpha)))
        sh = sh.filter(ImageFilter.GaussianBlur(12)); fr.paste(sh, (x, y + sp.size[1] - 34), sh)
    fr.paste(sp, (x, y), sp)

# ---------- particles / VFX ----------
DUST = [(random.random(), random.random(), random.uniform(1.5, 4), random.uniform(.2, 1), random.random() * 6) for _ in range(70)]
def dust(fr, t, col=(255, 210, 140), n=70, speed=1.0):
    o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    for i, (x, y, r, a, ph) in enumerate(DUST[:n]):
        px = (x * W + math.sin(t * .6 + ph) * 40 + t * 18 * speed) % W
        py = (y * H - t * 22 * speed * (0.5 + a)) % H
        al = int(90 * a * (0.6 + 0.4 * math.sin(t * 2 + ph)))
        d.ellipse([px - r, py - r, px + r, py + r], fill=col + (al,))
    o = o.filter(ImageFilter.GaussianBlur(1.2)); fr.paste(o, (0, 0), o)
RAIN = [(random.random(), random.random(), random.uniform(18, 40), random.uniform(.3, 1)) for _ in range(160)]
def rain(fr, t):
    o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    for x, y, ln, a in RAIN:
        px = (x * W + t * 120) % W; py = (y * H + t * 1400 * a) % H
        d.line([px, py, px - ln * .25, py + ln], fill=(190, 205, 230, int(70 * a)), width=2)
    fr.paste(o, (0, 0), o)
def glow(fr, cx, cy, r, col, a):
    o = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(o)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(int(c * a) for c in col))
    o = o.filter(ImageFilter.GaussianBlur(r * .5)); return ImageChops.screen(fr, o)
SPARK = [(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(.5, 1.5)) for _ in range(28)]
def sparkles(fr, cx, cy, t, a=1.0):
    d = ImageDraw.Draw(fr)
    for i, (dx, dy, s) in enumerate(SPARK):
        ph = (t * 1.6 * s + i * .37) % 1
        x = cx + dx * 260 * (0.4 + ph); y = cy + dy * 200 * (0.4 + ph) - ph * 60
        r = 9 * s * math.sin(ph * math.pi) * a
        if r < 1: continue
        d.polygon([(x, y - r * 2), (x + r * .4, y - r * .4), (x + r * 2, y), (x + r * .4, y + r * .4), (x, y + r * 2), (x - r * .4, y + r * .4), (x - r * 2, y), (x - r * .4, y - r * .4)], fill=(255, 236, 170))
VIG = None
def vignette():
    y, x = np.ogrid[:H, :W]; r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    m = np.clip((r - 0.55) / 0.75, 0, 1) ** 1.6 * 0.55
    return Image.fromarray((m * 255).astype(np.uint8))
VIG = vignette(); BLACK = Image.new("RGB", (W, H), (4, 6, 12))
GRAIN = [Image.fromarray(np.clip(np.random.default_rng(zlib.crc32(f'grain:{_g}'.encode())).normal(128, 8 if V != "B" else 11, (H // 2, W // 2)), 0, 255).astype(np.uint8)).resize((W, H)).convert("RGB") for _g in range(6)]
PAPERTEX = None
if True:
    n = np.random.normal(0, 1, (H // 4, W // 4)); n = Image.fromarray(np.clip(128 + n * 18, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2))
    PAPERTEX = n.convert("RGB")
GLUT = [min(255, int(255 * ((v / 255) ** 0.96) * 0.97 + 6)) for v in range(256)]
def grade(fr):  # one look for every shot: lifted navy blacks, gentle warm highs, -6% saturation
    r, g, b = fr.split(); r = r.point(lambda v: min(255, int(GLUT[v] * 1.015))); b = b.point(lambda v: min(255, GLUT[v] + 4)); g = g.point(GLUT)
    fr = Image.merge("RGB", (r, g, b)); return ImageEnhance.Color(fr).enhance(0.94)
def bug(fr):
    o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    d.text((W - 210, H - 66), "WISDROP", font=F(ANTON, 34), fill=(255, 255, 255, 80)); fr.paste(o, (0, 0), o); return fr
def finish(fr, i, shake=0.0):
    fr = grade(fr)
    if shake:
        r_ = np.random.default_rng(zlib.crc32(f"shake:{i}".encode()))   # AMC-W1: seeded per frame
        dx, dy = int(r_.uniform(-1, 1) * shake), int(r_.uniform(-1, 1) * shake)
        fr = ImageChops.offset(fr, dx, dy)
    fr = Image.composite(BLACK, fr, VIG)
    if PAPERTEX is not None: fr = Image.blend(fr, ImageChops.overlay(fr, PAPERTEX), .45 if V == "B" else .28)
    fr = ImageChops.overlay(fr, GRAIN[i % 6]) if i % 1 == 0 else fr
    return fr


def zoom(fr, z, cx=0.5, cy=0.5):
    if abs(z - 1) < 1e-4: return fr
    cw, ch = W / z, H / z; x0 = (W - cw) * cx; y0 = (H - ch) * cy
    return fr.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BILINEAR)

def belt(x):  # point on the diagonal belt surface (screen coords) for x
    return 838 - (x / 1296.0) * 232
