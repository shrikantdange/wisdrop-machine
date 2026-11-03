"""Wisdrop v4 fx: modern, impactful looks drawn by code on CPU (PIL + numpy). No GPU.

Shot types (registered in shots_render.py, documented in docs/SHOTS.md T21-T27):
  parallax   2.5D: one photo split into 3 depth layers (mask + blur), layers drift at 1x/1.7x/2.6x
  docreveal  scanned paper, redaction bars wipe off, a quote is typed on under a highlighter
  headlines  newspaper clippings slam in one by one (sourced headlines only; text drawn by code)
  coin3d     3D-look spinning coin: shading, rim, specular sweep, floor shadow; optional "drain"
  chart3d    extruded perspective bars with top/side shading and a specular sweep
  lineart    photo -> ink sketch by edge detection, traced on left to right (flashbacks)
Transitions (shot field "trans"): "glitch" (8 frames, RGB split + block displace; crypto moments
only) and "leak" (light-leak / film-burn wipe, 0.5 s; between parts).
Beat sync: beats(path) finds music onsets with numpy spectral flux; snap(t) moves a pop or cut
onto a beat when one is within 2 frames (cuts only move later, never before the voice).
Every random thing is seeded by motion.seed / motion.rng (crc32). Never random()/time()/hash().
"""
import math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops
from edhelpers import F, ANTON, MONO, SANS, SERIF, ease, eout, back, zoom
import motion as MO
import v3kit as V

W, H, FPS = 1920, 1080, 30
INK, CREAM, YEL, RED, GOLD = V.INK, V.CREAM, V.YEL, V.RED, (232, 182, 64)
GLITCH_FRAMES = 8          # 6-10 allowed (craft_check)
LEAK_SECS = 0.5
SNAP_TOL = 2 / FPS
_cache = {}


def _cached(key, fn):
    if key not in _cache: _cache[key] = fn()
    return _cache[key]


def _fit(img, w, h):
    return ImageOps.fit(img.convert("RGB"), (w, h), Image.LANCZOS)


# ---------------- 2.5D parallax ----------------
def depth_layers(img, key):
    """3 RGBA layers (far, mid, near) from one photo. Depth guess = lower in frame + sharper/more
    detailed = nearer (cheap monocular cues). Far layer is the whole photo (blurred) so no holes."""
    def mk():
        base = _fit(img, int(W * 1.16), int(H * 1.16)); a = np.asarray(base.convert("L"), np.float32) / 255
        hh, ww = a.shape
        gy, gx = np.gradient(a); detail = np.hypot(gx, gy)
        detail = np.asarray(Image.fromarray((np.clip(detail * 6, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(28)), np.float32) / 255
        vert = np.linspace(0, 1, hh)[:, None] * np.ones((1, ww))
        cen = 1 - np.abs(np.linspace(-1, 1, ww))[None, :] * .35
        dep = .55 * vert + .45 * detail / max(detail.max(), 1e-3); dep *= cen
        q1, q2 = np.quantile(dep, [.45, .75])
        def mask(lo, soft=.06):
            m = np.clip((dep - lo) / soft + .5, 0, 1)
            return Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))
        far = base.filter(ImageFilter.GaussianBlur(3)).convert("RGBA")
        mid = base.convert("RGBA"); mid.putalpha(mask(q1))
        near = base.filter(ImageFilter.UnsharpMask(2, 80)).convert("RGBA"); near.putalpha(mask(q2))
        return far, mid, near
    return _cached(("depth", key), mk)


def s_parallax(s, t, d, part, media, credit):
    img = media(s); key = s.get("file") or s.get("q", "")
    far, mid, near = depth_layers(img, key)
    u = MO.ease("camera", min(1, t / max(d, .1))); dirx = 1 if MO.seed(key, "dir") % 2 else -1
    amp = s.get("amp", 60); fr = Image.new("RGB", (W, H))
    for lay, k, z in ((far, 1.0, 1.0), (mid, 1.7, 1.015), (near, 2.6, 1.035)):
        zz = z + .02 * k * u; lw, lh = int(lay.size[0] * zz), int(lay.size[1] * zz)
        l2 = lay.resize((lw, lh), Image.BILINEAR)
        x = (W - lw) / 2 + dirx * amp * k * (u - .5); y = (H - lh) / 2 - 10 * k * u
        fr.paste(l2, (int(x), int(y)), l2)
    vig = _cached("vig", lambda: Image.radial_gradient("L").resize((W, H)).point(lambda v: int(min(255, v * 1.1))))
    fr = Image.composite(Image.new("RGB", (W, H), (8, 8, 10)), fr, vig.point(lambda v: int(v * .55)))
    dr = ImageDraw.Draw(fr)
    if s.get("label") and t > .5: V.pop_sticker(fr, s["label"].upper(), int(W * .16), int(H * .12), MO.on_twos(t) - .5, F(ANTON, 46)); dr = ImageDraw.Draw(fr)
    c = credit(s)
    if c: dr.text((40, 1046), c, font=F(MONO, 16), fill=(190, 185, 174), anchor="lm")
    return fr


# ---------------- document reveal ----------------
def paper(w, h, key):
    def mk():
        r = MO.rng("paper", key, w, h); a = np.full((h, w, 3), (238, 231, 214), np.float32)
        a += r.normal(0, 5, (h, w, 1)); a -= np.linspace(0, 14, w)[None, :, None]           # grain + scan falloff
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
        fy = int(h * (.42 + .1 * r.random())); dr.line([(0, fy), (w, fy + 3)], fill=(214, 206, 188), width=3)  # fold
        for _ in range(6):   # specks
            x, y = int(r.random() * w), int(r.random() * h); dr.ellipse([x, y, x + 3, y + 3], fill=(170, 160, 145))
        return im.filter(ImageFilter.GaussianBlur(.6))
    return _cached(("paper", key, w, h), mk)


def s_docreveal(s, t, d, part):
    th = V.theme(part); fr = V.board(part); key = s.get("title", "doc")
    pw, ph = 1100, 640; pg = paper(pw, ph, key).copy(); dr = ImageDraw.Draw(pg)
    dr.text((70, 60), s.get("kind", "COURT FILING").upper(), font=F(MONO, 30), fill=(120, 110, 96))
    tf = 52; ttl = s.get("title", "").upper()
    while tf > 34 and dr.textlength(ttl, font=F(SERIF, tf)) > pw - 140: tf -= 2
    dr.text((70, 104 + (52 - tf) * .5), ttl, font=F(SERIF, tf), fill=INK)
    dr.line([(70, 178), (pw - 70, 178)], fill=INK, width=3)
    f = F(SERIF, 38); y = 206; red = set(s.get("redact", [])); step = s.get("step", .45)
    lines = s.get("lines", []); boxes = []
    for i, ln in enumerate(lines):
        dr.text((70, y), ln, font=f, fill=(40, 38, 34))
        if i in red: boxes.append((i, [62, y - 6, 70 + dr.textlength(ln, font=f) + 10, y + 46]))
        y += 54
    # redaction bars wipe off right-to-left, one after another (on twos, paper rule AMC-T6)
    tt = MO.on_twos(t)
    for k, (i, b) in enumerate(boxes):
        u = ease(min(1, max(0, (tt - .35 - k * step) / .3)))
        if u < 1: dr.rectangle([b[0], b[1], b[2] - (b[2] - b[0]) * u, b[3]], fill=(14, 14, 14))
    q = s.get("quote", "")
    if q:
        q0 = .45 + len(boxes) * step + .15; n = int(max(0, t - q0) * s.get("cps", 26)); qf = F(SERIF, 44)
        txt = "\u201c" + q[:n] + ("\u201d" if n >= len(q) else ""); yq = y + 20
        if n > 0:
            for row in V.wrap(dr, txt, qf, pw - 160)[:2]:
                wq = dr.textlength(row, font=qf); dr.rectangle([66, yq + 4, 82 + wq, yq + 56], fill=YEL)
                dr.text((74, yq), row, font=qf, fill=INK); yq += 64
    pg = pg.rotate(s.get("rot", -1.2), expand=True, resample=Image.BICUBIC, fillcolor=th["bg"])
    e = back(min(1, t / .5)); sc = 1.0 + .03 * ease(t / max(d, .1))
    pg2 = pg.resize((int(pg.size[0] * sc), int(pg.size[1] * sc)), Image.BILINEAR)
    V.shadow_paste(fr, pg2.convert("RGBA"), (W - pg2.size[0]) / 2, H * .40 - pg2.size[1] / 2 + 140 * (1 - e), 22, (12, 18), .45)
    if s.get("source"): V.source_line(ImageDraw.Draw(fr), s["source"], th)
    return fr


# ---------------- newspaper headline montage ----------------
def clipping(item, key):
    def mk():
        f = F(SERIF, 64); d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        rows = V.wrap(d0, item["head"], f, 820)[:3]; w = 900; h = 150 + 76 * len(rows) + 120
        im = paper(w, h, key).copy(); dr = ImageDraw.Draw(im)
        dr.text((w / 2, 52), item.get("outlet", "").upper(), font=F(SERIF, 40), fill=INK, anchor="mm")
        dr.line([(30, 86), (w - 30, 86)], fill=INK, width=2); dr.text((40, 96), item.get("date", "").upper(), font=F(MONO, 30), fill=(100, 92, 80))
        y = 132
        for r_ in rows: dr.text((40, y), r_, font=f, fill=INK); y += 76
        r = MO.rng("clip", key)
        for k in range(4):   # column texture as grey bars (never fake words)
            for j in range(3):
                x0 = 40 + j * 285; dr.rectangle([x0, y + 16 + k * 22, x0 + 250 - int(r.random() * 60), y + 26 + k * 22], fill=(178, 170, 156))
        # torn edges
        m = Image.new("L", (w, h), 255); md = ImageDraw.Draw(m)
        for x in range(0, w, 14): md.polygon([(x, 0), (x + 7, int(3 + r.random() * 9)), (x + 14, 0)], fill=0); md.polygon([(x, h), (x + 7, h - int(3 + r.random() * 9)), (x + 14, h)], fill=0)
        im = im.convert("RGBA"); im.putalpha(m); return im
    return _cached(("clip", key), mk)


SLOTS = [(.33, .3), (.66, .42), (.38, .6), (.68, .24), (.5, .45)]


def s_headlines(s, t, d, part):
    th = V.theme(part); fr = V.board(part); step = s.get("step", .7); tt = MO.on_twos(t)
    items = s.get("items", [])
    for k, it in enumerate(items):
        a = tt - .15 - k * step
        if a <= 0: continue
        key = f"{k}:{it['head']}"; r = MO.rng("hl", key)
        cl = clipping(it, key); rot = (r.random() - .5) * 9
        e = min(1, a / .12); sc = (1.45 - .45 * e) * .78
        im = cl.resize((int(cl.size[0] * sc), int(cl.size[1] * sc)), Image.BILINEAR).rotate(rot, expand=True, resample=Image.BICUBIC)
        bx, by = SLOTS[k % len(SLOTS)]; cx = W * (bx + (r.random() - .5) * .05); cy = H * (by + (r.random() - .5) * .05)
        shake = 10 * (1 - min(1, a / .25)) * (1 if k % 2 else -1)
        V.shadow_paste(fr, im, cx - im.size[0] / 2 + shake, cy - im.size[1] / 2, 14, (8, 12), .45 if e >= 1 else .25)
    if s.get("source"): V.source_line(ImageDraw.Draw(fr), s["source"], th)
    return fr


# ---------------- 3D-look coin ----------------
def coin_img(r, phase, text, drain, key):
    """r radius px, phase 0-1 spin (y-axis), drain 0-1 empties the coin to an outline."""
    ang = phase * 2 * math.pi; sx = max(.06, abs(math.cos(ang))); wd = int(2 * r * sx) + 2; th = max(6, int(r * .16 * abs(math.sin(ang))) + 6)
    im = Image.new("RGBA", (int(2 * r) + th + 40, int(2 * r) + 40), (0, 0, 0, 0)); cx, cy = im.size[0] / 2, im.size[1] / 2
    dr = ImageDraw.Draw(im)
    side = -1 if math.sin(ang) > 0 else 1
    for k in range(th, 0, -1):   # rim thickness, darker toward the back
        g = int(120 + 50 * k / th); dr.ellipse([cx - wd / 2 + side * k, cy - r, cx + wd / 2 + side * k, cy + r], fill=(g, int(g * .72), 30, 255))
    face = Image.new("RGBA", (max(2, wd), int(2 * r)), (0, 0, 0, 0))
    yy, xx = np.mgrid[0:face.size[1], 0:face.size[0]].astype(np.float32)
    nx = (xx - face.size[0] / 2) / max(1, face.size[0] / 2); ny = (yy - face.size[1] / 2) / max(1, face.size[1] / 2)
    rr = np.sqrt(nx ** 2 + ny ** 2); inside = rr <= 1
    light = np.clip(.75 - .35 * ny + .25 * nx * math.cos(ang), .3, 1.1)
    sweep = np.exp(-((nx + ny * .5) - (2.4 * ((phase * 1.7) % 1) - 1.2)) ** 2 / .02) * .55     # specular sweep
    ring = ((rr > .82) & (rr < .9)) * .25
    base = np.stack([232 * light, 182 * light, 64 * light], -1) + (sweep + ring)[..., None] * 255
    a = (inside * 255).astype(np.uint8)
    if drain > 0:
        hollow = ny < (-1 + 2 * drain)                                           # empties from the top
        a = np.where(hollow & (rr < .86), (40 * inside).astype(np.uint8), a)
    face = Image.fromarray(np.dstack([np.clip(base, 0, 255).astype(np.uint8), a]), "RGBA")
    if sx > .45 and text:
        tl = Image.new("RGBA", (int(2 * r), int(2 * r)), (0, 0, 0, 0)); td = ImageDraw.Draw(tl); f = F(ANTON, int(r * .55))
        td.text((r + 3, r + 4), text, font=f, fill=(120, 84, 20, 200), anchor="mm"); td.text((r, r), text, font=f, fill=(255, 236, 170, 255), anchor="mm")
        tl = tl.resize(face.size, Image.BILINEAR); face.alpha_composite(tl)
    im.alpha_composite(face, (int(cx - face.size[0] / 2), int(cy - r)))
    return im


def s_coin3d(s, t, d, part):
    th = V.theme(part); fr = V.board(part); dr = ImageDraw.Draw(fr); r = s.get("r", 300)
    spin = .02 + s.get("spins", 1.0) * eout(min(1, t / max(.9, min(1.6, d * .7))))
    drain = ease(min(1, max(0, (t - s.get("drain_at", 1.4)) / 1.6))) if s.get("drain") else 0
    c = coin_img(r, spin, s.get("text", ""), drain, s.get("text", ""))
    bob = 12 * math.sin(t * 2.2)
    sh = Image.new("RGBA", (int(r * 2.2), 80), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([0, 0, sh.size[0], 80], fill=(0, 0, 0, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(14)); fr.paste(sh, (int(W / 2 - sh.size[0] / 2), int(H * .45 + r + 10)), sh)
    e = back(min(1, t / .45)); cc = c.resize((max(2, int(c.size[0] * e)), max(2, int(c.size[1] * e))), Image.BILINEAR)
    fr.paste(cc, (int(W / 2 - cc.size[0] / 2), int(H * .45 - cc.size[1] / 2 + bob)), cc)
    if s.get("label") and t > .35: dr.text((W / 2, H * .45 + r + 80), s["label"].upper(), font=F(ANTON, 76), fill=th["ink"], anchor="mm")
    if s.get("source"): V.source_line(dr, s["source"], th)
    return fr


# ---------------- 3D-look bar chart ----------------
def s_chart3d(s, t, d, part):
    th = V.theme(part); fr = V.board(part); dr = ImageDraw.Draw(fr)
    items = s.get("items", []); n = max(1, len(items)); vmax = max([abs(i["value"]) for i in items] + [1e-9])
    bw, gap, depth = min(220, 1100 // n), 70, 46; x0 = W / 2 - (n * bw + (n - 1) * gap) / 2; base = H * .66; hmax = H * .44
    acc = th["acc"]; step = s.get("step", .45)
    if s.get("title"): dr.text((W / 2, 110), s["title"].upper(), font=F(ANTON, 80), fill=th["ink"], anchor="mm")
    dr.polygon([(x0 - 60, base), (x0 + n * (bw + gap) + 20, base), (x0 + n * (bw + gap) + 20 + depth, base - depth), (x0 - 60 + depth, base - depth)], fill=th["grid"])
    for k, it in enumerate(items):
        u = eout(min(1, max(0, (t - .3 - k * step) / .7))); h = hmax * abs(it["value"]) / vmax * u; x = x0 + k * (bw + gap)
        col = tuple(it.get("color", acc if k == s.get("hl", n - 1) else th["sub"]))
        top = tuple(min(255, int(c * 1.25)) for c in col); side = tuple(int(c * .62) for c in col)
        if h > 1:
            dr.polygon([(x + bw, base), (x + bw + depth, base - depth), (x + bw + depth, base - depth - h), (x + bw, base - h)], fill=side)
            dr.polygon([(x, base - h), (x + bw, base - h), (x + bw + depth, base - h - depth), (x + depth, base - h - depth)], fill=top)
            dr.rectangle([x, base - h, x + bw, base], fill=col)
            sp = ((t * .6 - k * .12) % 1.6) - .3                         # specular sweep up the front face
            if 0 < sp < 1: yb = base - h * sp; dr.rectangle([x + 6, yb - 10, x + bw - 6, yb + 10], fill=tuple(min(255, c + 60) for c in col))
        if u > .2:
            dr.text((x + bw / 2 + depth / 2, base - h - depth - 36), it.get("text", f"{it['value']:g}"), font=F(ANTON, 64), fill=th["ink"], anchor="mm")
            dr.text((x + bw / 2, base + 40), it["label"].upper(), font=F(ANTON, 40), fill=th["sub"], anchor="mm")
    if s.get("source"): V.source_line(dr, s["source"], th)
    return fr


# ---------------- line-art trace (flashbacks) ----------------
def ink_sketch(img, key):
    def mk():
        g = np.asarray(_fit(img, W, H).convert("L").filter(ImageFilter.GaussianBlur(1.4)), np.float32)
        gx = np.zeros_like(g); gy = np.zeros_like(g)
        gx[:, 1:-1] = g[:, 2:] - g[:, :-2]; gy[1:-1, :] = g[2:, :] - g[:-2, :]
        e = np.hypot(gx, gy); e = np.clip((e - np.quantile(e, .80)) / (np.quantile(e, .985) - np.quantile(e, .80) + 1e-6), 0, 1)
        return (e * 255).astype(np.uint8)   # ink strength
    return _cached(("ink", key), mk)


def s_lineart(s, t, d, part, media, credit):
    img = media(s); key = s.get("file") or s.get("q", ""); ink = ink_sketch(img, key)
    pg = np.asarray(paper(W, H, "lineart"), np.float32)
    u = MO.ease("camera", min(1, t / s.get("trace", 1.6))); xe = int(W * u * 1.08)
    m = ink.astype(np.float32) / 255; m[:, xe:] = 0
    out = pg * (1 - m[..., None]) + np.array([30, 28, 40], np.float32) * m[..., None]
    fr = Image.fromarray(out.astype(np.uint8))
    if u < 1:   # the pen tip
        dr = ImageDraw.Draw(fr); dr.line([(xe, 0), (xe, H)], fill=(200, 60, 40), width=3)
    fr = zoom(fr, 1 + .03 * ease(t / max(d, .1)))
    dr = ImageDraw.Draw(fr)
    if s.get("label") and t > .5: V.pop_sticker(fr, s["label"].upper(), int(W * .1), int(H * .1), MO.on_twos(t) - .5, F(ANTON, 46), CREAM); dr = ImageDraw.Draw(fr)
    c = credit(s)
    if c: dr.text((40, 1046), c, font=F(MONO, 16), fill=(110, 104, 94), anchor="lm")
    return fr


# ---------------- transitions ----------------
def glitch(fr, tt, key):
    """tt seconds since the cut; active for GLITCH_FRAMES frames. RGB split + block displace."""
    k = int(tt * FPS)
    if k >= GLITCH_FRAMES: return fr
    r = MO.rng("glitch", key, k); amt = 1 - k / GLITCH_FRAMES
    a = np.asarray(fr).copy(); sh = int(18 * amt + 4)
    a[..., 0] = np.roll(a[..., 0], sh, 1); a[..., 2] = np.roll(a[..., 2], -sh, 1)
    for _ in range(int(6 + 8 * amt)):
        y = int(r.random() * (H - 60)); hh = int(12 + r.random() * 60); dx = int((r.random() - .5) * 160 * amt)
        a[y:y + hh] = np.roll(a[y:y + hh], dx, 1)
    return Image.fromarray(a)


def leak(fr, tt, key):
    """Light-leak / film-burn wipe over LEAK_SECS: warm additive blobs sweep left to right."""
    if tt >= LEAK_SECS: return fr
    u = tt / LEAK_SECS; pk = math.sin(math.pi * u)
    def base():
        r = MO.rng("leak", key); g = Image.new("RGB", (480, 270)); dr = ImageDraw.Draw(g)
        for j in range(5):
            x, y, rad = r.random() * 480, r.random() * 270, 60 + r.random() * 110
            dr.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(255, int(120 + r.random() * 80), int(40 + r.random() * 40)))
        return g.filter(ImageFilter.GaussianBlur(40)).resize((W * 2, H), Image.BILINEAR)
    lk = _cached(("leak", key), base); x = int(-W * u)
    ov = lk.crop((-x, 0, -x + W, H))
    return ImageChops.add(fr, Image.blend(Image.new("RGB", (W, H)), ov, min(.85, pk * .85)))


# ---------------- beat sync ----------------
def decode(path, offset=0.0, secs=None, sr=11025):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(offset), "-i", path] + (["-t", str(secs)] if secs else []) + ["-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
    try: return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768, sr
    except Exception: return np.zeros(0, np.float32), sr


def beats(path, offset=0.0, secs=None):
    """Onset times (s, from offset) by spectral flux + adaptive threshold, >= 0.25 s apart."""
    x, sr = decode(path, offset, secs)
    hop, n = 256, 1024
    if len(x) < n * 4: return []
    fr = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * np.hanning(n)
    mag = np.log1p(np.abs(np.fft.rfft(fr, axis=1)) * 10)
    flux = np.maximum(0, np.diff(mag, axis=0)).sum(1)
    k = 16; pad = np.pad(flux, k, mode="edge")
    med = np.array([np.median(pad[i:i + 2 * k + 1]) for i in range(len(flux))])
    thr = med + .5 * flux.std()
    out, last = [], -1
    for i in range(1, len(flux) - 1):
        if flux[i] > thr[i] and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]:
            tt = (i + 1) * hop / sr
            if tt - last >= .25: out.append(round(tt, 3)); last = tt
    return out


def episode_beats(kit, music, cuts):
    """Beat times on the mix clock, matching automix: part k plays track music[k] from 4 s (part 0)
    or 0 s, placed at cut_k - 0.75 s. cuts = [0, chapter starts..., dur]."""
    out = []
    for k in range(len(cuts) - 1):
        a0, a1 = cuts[k], cuts[k + 1]
        if a1 - a0 < .5 or not music: continue
        p = os.path.join(kit, "music", music[min(k, len(music) - 1)] + ".mp3"); off = 4 if k == 0 else 0
        out += [max(0, a0 - .75) + b for b in beats(p, off, a1 - a0 + 1.5) if a0 <= max(0, a0 - .75) + b < a1]
    return sorted(out)


def snap(t, bt, forward_only=False, tol=SNAP_TOL):
    """Nearest beat within tol (2 frames); cuts use forward_only so nothing lands before the voice."""
    if not bt: return t
    i = int(np.searchsorted(bt, t)); cands = [b for b in bt[max(0, i - 1):i + 1] if abs(b - t) <= tol + 1e-6 and (b >= t or not forward_only)]
    return min(cands, key=lambda b: abs(b - t)) if cands else t


# ---------------- end screen (last 5-20 s; YouTube places its own clickable elements on top) ----------------
def s_endscreen(s, t, d, part):
    """Code-drawn slots where YouTube's end-screen elements go: a 16:9 video slot left, a round
    subscribe slot right, heading on top. Slots breathe slowly so the frame is never still."""
    th = V.theme(part); fr = V.board(part); dr = ImageDraw.Draw(fr); a = eout(min(1, t / .8))
    dr.text((W / 2, 150 - 30 * (1 - a)), s.get("text", "Next case").upper(), font=F(ANTON, 110), fill=th["ink"], anchor="mm")
    if s.get("sub"): dr.text((W / 2, 250), s["sub"].upper(), font=F(ANTON, 44), fill=th["sub"], anchor="mm")
    pulse = .5 + .5 * math.sin(t * 1.6)
    vx0, vy0, vw = 250, 340, 820; vh = int(vw * 9 / 16)
    col = tuple(int(c * (.75 + .25 * pulse)) for c in th["acc"])
    dr.rounded_rectangle([vx0, vy0, vx0 + vw, vy0 + vh], 18, outline=col, width=8)
    dr.text((vx0 + vw / 2, vy0 + vh / 2), "WATCH NEXT", font=F(ANTON, 76), fill=th["ink"], anchor="mm")
    cx, cy, r = 1430, vy0 + vh / 2, 190 + 6 * pulse
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=8)
    dr.text((cx, cy), "SUBSCRIBE", font=F(ANTON, 56), fill=th["ink"], anchor="mm")
    return zoom(fr, 1 + .01 * math.sin(t * .5))
