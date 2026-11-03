#!/usr/bin/env python3
"""Designed thumbnails (docs/THUMBNAILS.md), never frame grabs. CPU only; the focal subject
pictures (max 2 per episode) come from worker_images.py via .github/workflows/thumbs.yml.

  python machine/thumbnail.py <ep_dir> [--cuts DIR]

Reads <ep>/thumbs/concepts.json, writes <ep>/thumbs/: thumb_<id>.jpg (1280x720),
phone_mock.png (YouTube phone feed 360x202 + suggested column 168x94), score.json.
Each concept: {id, words:[1-3 words], accent:index of accent word, subject: "cut:<name>" |
"coin_vanish" | "coin", side: "right"|"left", glow:[r,g,b], arrow: bool, source}.
Words are drawn here by code. Subjects are fictional people or objects; never a real person.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "machine", "engine"))
import motion as MO
FONT = os.path.join(ROOT, "kit", "fonts", "Anton.ttf"); MONOF = os.path.join(ROOT, "kit", "fonts", "DejaVuSansMono-Bold.ttf")
SANSF = os.path.join(ROOT, "kit", "fonts", "DejaVuSans-Bold.ttf")
from PIL import ImageFont
def F(p, s): return ImageFont.truetype(p, int(s))
TW, TH = 1280, 720
YEL, RED, CREAM, INK = (247, 209, 58), (226, 52, 40), (241, 233, 215), (14, 14, 16)
BRAND = "WISDROP"


# ---------------- background board (brand frame: same on every episode) ----------------
def board(glow, side, key):
    y, x = np.mgrid[0:TH, 0:TW].astype(np.float32)
    base = np.stack([np.full_like(x, c) for c in (14, 18, 30)], -1)
    gx = TW * (.72 if side == "right" else .28); gy = TH * .5
    r = np.sqrt(((x - gx) / TW) ** 2 + ((y - gy) / TH * .7) ** 2)
    g = np.clip(1 - r / .55, 0, 1) ** 2
    img = base + g[..., None] * np.array(glow, np.float32) * .55
    img *= (1 - .55 * np.clip(np.sqrt(((x - TW / 2) / TW) ** 2 + ((y - TH / 2) / TH) ** 2) * 1.6 - .25, 0, 1))[..., None]   # vignette
    img += MO.rng("tgrain", key).normal(0, 3, (TH, TW, 1))
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for k in range(0, TW, 64): d.line([(k, 0), (k, TH)], fill=(26, 32, 50), width=1)
    for k in range(0, TH, 64): d.line([(0, k), (TW, k)], fill=(26, 32, 50), width=1)
    return im


def brand_frame(im):
    d = ImageDraw.Draw(im)
    d.rectangle([0, TH - 12, TW, TH], fill=YEL)                        # bottom bar: the channel's signature
    f = F(MONOF, 22); w = d.textlength(BRAND, font=f)
    d.rectangle([22, 20, 22 + w + 24, 56], fill=YEL); d.text((34, 24), BRAND, font=f, fill=INK)   # top-left (timestamp sits bottom-right)
    return im


# ---------------- subject ----------------
def rim_light(cut, col, width=10):
    pad = width * 6; big = Image.new("RGBA", (cut.size[0] + 2 * pad, cut.size[1] + 2 * pad)); big.paste(cut, (pad, pad)); cut = big
    a = cut.getchannel("A")
    outer = a.filter(ImageFilter.MaxFilter(2 * (width // 2) + 1)); edge = ImageChops.subtract(outer, a)
    glow = Image.new("RGBA", cut.size, col + (0,)); glow.putalpha(outer.filter(ImageFilter.GaussianBlur(width * 2.4)).point(lambda v: int(v * .9)))
    rim = Image.new("RGBA", cut.size, (255, 250, 235, 0)); rim.putalpha(edge.filter(ImageFilter.GaussianBlur(1.5)))
    out = Image.new("RGBA", cut.size); out.alpha_composite(glow); out.alpha_composite(cut); out.alpha_composite(rim)
    return out


def code_coin(r=250, vanish=0.0, key="coin"):
    import v4fx
    c = v4fx.coin_img(r, .07, "", 0, key)
    if vanish > 0:   # right side breaks into square pixels drifting away
        a = np.asarray(c).copy(); h, w = a.shape[:2]; rg = MO.rng("vanish", key); out = np.zeros_like(a)
        cut_x = int(w * (1 - vanish)); out[:, :cut_x] = a[:, :cut_x]
        big = Image.new("RGBA", (int(w * 2.2), h)); big.paste(Image.fromarray(out), (0, 0))
        bd = ImageDraw.Draw(big)
        for _ in range(420):
            sx, sy = int(cut_x + rg.random() * (w - cut_x)), int(rg.random() * h)
            if a[sy, sx, 3] < 128: continue
            dx = (rg.random() ** 1.6) * w * 1.1; s = int(4 + rg.random() * 14 * (1 - dx / (w * 1.2)))
            col = tuple(int(v) for v in a[sy, sx, :3]) + (int(255 * (1 - dx / (w * 1.3))),)
            bd.rectangle([sx + dx, sy - s / 2, sx + dx + s, sy + s / 2], fill=col)
        c = big
    return c


def load_subject(spec, cuts, key):
    if spec.startswith("cut:"):
        p = os.path.join(cuts, spec[4:] + ".png")
        if os.path.exists(p):
            im = Image.open(p).convert("RGBA"); bb = im.getbbox(); return im.crop(bb) if bb else im
        print(f"WAIT subject {spec} missing (run workflow thumbs); using the code coin instead"); return code_coin(key=key)
    if spec == "coin_vanish": return code_coin(260, .55, key)
    return code_coin(260, 0, key)


# ---------------- text ----------------
def draw_words(im, words, accent, side, max_w):
    """1-3 words, stacked, as big as fits max_w x 72 % height. Accent word in a red box."""
    d = ImageDraw.Draw(im); lines = [w.upper() for w in words]
    size = 400
    while size > 60:
        f = F(FONT, size); lh = size * 1.02
        if max(d.textlength(l, font=f) for l in lines) <= max_w and lh * len(lines) <= TH * .74: break
        size -= 6
    f = F(FONT, size); lh = size * 1.0; y = (TH - lh * len(lines)) / 2 - size * .08
    x0 = 56 if side == "right" else TW - 56 - max_w; boxes = []
    for i, l in enumerate(lines):
        w = d.textlength(l, font=f); x = x0 if side == "right" else x0 + max_w - w
        bb = d.textbbox((x, y), l, font=f)
        if i == accent:
            d.rectangle([bb[0] - 18, bb[1] - 14, bb[2] + 18, bb[3] + 14], fill=RED)
            d.text((x, y), l, font=f, fill=CREAM)
        else:
            sh = Image.new("RGBA", im.size); ImageDraw.Draw(sh).text((x + 8, y + 10), l, font=f, fill=(0, 0, 0, 200))
            im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8))) if im.mode == "RGBA" else im.paste(sh.filter(ImageFilter.GaussianBlur(8)), (0, 0), sh.filter(ImageFilter.GaussianBlur(8)))
            d = ImageDraw.Draw(im); d.text((x, y), l, font=f, fill=YEL if i == 0 else CREAM, stroke_width=max(4, size // 28), stroke_fill=INK)
        boxes.append(bb); y += lh
    return size, boxes


def arrow(d, p0, p1, col=RED, w=16):
    d.line([p0, p1], fill=col, width=w)
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for s in (-1, 1): d.line([p1, (p1[0] - 46 * math.cos(a + s * .5), p1[1] - 46 * math.sin(a + s * .5))], fill=col, width=w)


def compose(c, cuts):
    side = c.get("side", "right"); glow = tuple(c.get("glow", YEL)); key = c["id"]
    im = board(glow, side, key).convert("RGBA")
    sub = rim_light(load_subject(c["subject"], cuts, key), glow, 12)
    sc = min(TH * c.get("h", .96) / sub.size[1], TW * .62 / sub.size[0]); sub = sub.resize((int(sub.size[0] * sc), int(sub.size[1] * sc)), Image.LANCZOS)
    sx = max(TW * .5 - 60, TW - sub.size[0] + 40) if side == "right" else min(TW * .5 + 60 - sub.size[0], -40); sy = TH - sub.size[1] + 40 if c.get("ground", True) else (TH - sub.size[1]) // 2
    im.alpha_composite(sub, (int(sx), int(sy)))
    size, boxes = draw_words(im, c["words"], c.get("accent", -1), side, int(TW * .46))
    if c.get("arrow"):
        d = ImageDraw.Draw(im); bb = boxes[-1]; arrow(d, (bb[2] + 20, bb[3] - 30), (sx + sub.size[0] * .25, sy + sub.size[1] * .45))
    im = brand_frame(im.convert("RGB"))
    return im, {"text_px": size, "text_boxes": boxes, "subject_box": [sx, sy, sx + sub.size[0], sy + sub.size[1]]}


# ---------------- auto score ----------------
def _lum(a): return (.2126 * a[..., 0] + .7152 * a[..., 1] + .0722 * a[..., 2]) / 255


def score(im, meta):
    """0-100: contrast (35), text size at 168x94 (35), focal clarity (30)."""
    small = np.asarray(im.resize((168, 94), Image.LANCZOS), np.float32); L = _lum(small)
    rms = float(L.std()); s_con = min(1, rms / .26)
    cap_px = meta["text_px"] * .74 * 94 / TH                         # Anton cap height ~74 % of size
    s_txt = min(1, cap_px / 14)                                      # >= 14 px caps at 168x94 = readable
    gy, gx = np.gradient(L); e = np.hypot(gx, gy); k = 168 / TW
    m = np.zeros_like(e)
    for b in meta["text_boxes"] + [meta["subject_box"]]:
        m[int(b[1] * k):int(b[3] * k) + 1, int(b[0] * k):int(b[2] * k) + 1] = 1
    focal = float((e * m).sum() / max(e.sum(), 1e-6)); cover = float(m.mean())
    s_foc = min(1, focal / .8) * (1 if cover < .85 else .8)
    tot = round(35 * s_con + 35 * s_txt + 30 * s_foc)
    return {"score": tot, "contrast_rms_168": round(rms, 3), "text_cap_px_168": round(cap_px, 1), "focal_share": round(focal, 2),
            "verdict": "OK" if tot >= 75 and cap_px >= 12 else "REVIEW"}


# ---------------- phone mock (YouTube home feed + suggested column, dark mode, all code-drawn) ----------------
def phone_mock(thumbs, title, channel="Wisdrop"):
    W_, H_ = 1240, 900; im = Image.new("RGB", (W_, H_), (24, 24, 26)); d = ImageDraw.Draw(im)
    # phone: 360 wide feed
    px, py = 60, 50; d.rounded_rectangle([px - 14, py - 14, px + 374, py + 800], 38, fill=(8, 8, 8)); d.rectangle([px, py, px + 360, py + 786], fill=(15, 15, 15))
    y = py + 40
    for k in range(3):
        if k == 1: t = thumbs[0].resize((360, 202), Image.LANCZOS); im.paste(t, (px, y)); tt = title
        else:
            r = MO.rng("dummy", k); col = tuple(int(30 + 60 * r.random()) for _ in range(3)); d.rectangle([px, y, px + 360, y + 202], fill=col); tt = None
        d.ellipse([px + 10, y + 214, px + 46, y + 250], fill=(70, 70, 74) if tt is None else YEL)
        if tt:
            f = F(SANSF, 15); rows = [tt[:40], tt[40:80]] if len(tt) > 40 else [tt]
            for j, r_ in enumerate(rows): d.text((px + 56, y + 214 + j * 20), r_, font=f, fill=(240, 240, 240))
            d.text((px + 56, y + 216 + len(rows) * 20), f"{channel} · new", font=F(SANSF, 12), fill=(170, 170, 170))
        else:
            d.rectangle([px + 56, y + 218, px + 320, y + 230], fill=(60, 60, 64)); d.rectangle([px + 56, y + 238, px + 230, y + 248], fill=(48, 48, 52))
        y += 266
    d.text((px, py + 806), "PHONE HOME FEED 360x202", font=F(MONOF, 16), fill=(150, 150, 150))
    # suggested column: 168x94, each concept among dummies
    sx, sy = 500, 50; d.text((sx, sy - 6), "SUGGESTED 168x94 (desktop sidebar size)", font=F(MONOF, 16), fill=(150, 150, 150)); sy += 30
    order = []
    for i, t in enumerate(thumbs): order += [None, t] if i else [t]
    order += [None, None]
    for k, t in enumerate(order[:8]):
        cx_, cy_ = sx + (k % 2) * 370, sy + (k // 2) * 130
        if t is None:
            r = MO.rng("dummy2", k); d.rectangle([cx_, cy_, cx_ + 168, cy_ + 94], fill=tuple(int(30 + 70 * r.random()) for _ in range(3)))
            d.rectangle([cx_ + 178, cy_ + 6, cx_ + 340, cy_ + 16], fill=(60, 60, 64)); d.rectangle([cx_ + 178, cy_ + 24, cx_ + 300, cy_ + 32], fill=(48, 48, 52))
        else:
            im.paste(t.resize((168, 94), Image.LANCZOS), (cx_, cy_)); f = F(SANSF, 13)
            d.text((cx_ + 178, cy_ + 2), title[:24], font=f, fill=(240, 240, 240)); d.text((cx_ + 178, cy_ + 20), title[24:48], font=f, fill=(240, 240, 240))
            d.text((cx_ + 178, cy_ + 42), channel, font=F(SANSF, 11), fill=(170, 170, 170))
    return im


def main(ep, cuts=None):
    td = os.path.join(ep, "thumbs"); os.makedirs(td, exist_ok=True)
    cfg = json.load(open(os.path.join(td, "concepts.json"))); cuts = cuts or os.path.join(td, "cuts")
    res, thumbs = {}, []
    for c in cfg["concepts"]:
        assert 1 <= len(c["words"]) <= 3 and sum(len(w.split()) for w in c["words"]) <= 3, f"{c['id']}: max 3 words"
        im, meta = compose(c, cuts); im.save(os.path.join(td, f"thumb_{c['id']}.jpg"), quality=92)
        res[c["id"]] = dict(score(im, meta), words=" ".join(c["words"]), source=c.get("source", "")); thumbs.append(im)
        print(f"{res[c['id']]['verdict']}: thumb {c['id']} score {res[c['id']]['score']} ({res[c['id']]})")
    phone_mock(thumbs, cfg.get("title", "")).save(os.path.join(td, "phone_mock.png"))
    json.dump(res, open(os.path.join(td, "score.json"), "w"), indent=1)
    print("OK thumbnails: owner approves before upload (FINAL REVIEW PR)")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    main(a[0], sys.argv[sys.argv.index("--cuts") + 1] if "--cuts" in sys.argv else None)
