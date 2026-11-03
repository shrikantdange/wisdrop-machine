"""Wisdrop generic episode renderer: shots.json + timeline.json + library pictures -> frames.

Every episode uses this same file, so every episode has the same visual language.
An episode never needs its own render code: it only writes shots.json (see
docs/SHOTS.md). Imported by machine/worker_render.py with sys.argv = [x, ep_dir, out].

Exposes W, H, FPS, DUR and render(i) -> PIL image.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edhelpers import *   # W, H, FPS, colours, fonts, ease/eout/back, glow, rain, dust, sparkles, paste, match, zoom, finish, bug

EP = sys.argv[1]
ASSETS = os.environ.get("WIS_ASSETS", "/assets")
TL = json.load(open(os.environ.get("WIS_TIMELINE", os.path.join(EP, "timeline.json"))))
DUR = TL["dur"]; SEGS = TL["segs"]; ST = {s["i"]: s["start"] for s in SEGS}
SH = json.load(open(os.path.join(EP, "shots.json")))
_mp = os.environ.get("WIS_MANIFEST", os.path.join(ASSETS, "eps", os.path.basename(EP.rstrip("/")), "asset_manifest.json"))
MAN = json.load(open(_mp)) if os.path.exists(_mp) else {}
LIB = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "library", "library.json")))
LEAD = 0.04; DIP = 0.22
COL = {"red": RED, "gold": GOLD, "amber": (240, 170, 60), "paper": PAPER, "grey": GREY, "green": GREEN, "white": WHITE}
TINT = {"dawn": ((200, 210, 235), .12), "morning": ((255, 220, 170), .10), "day": ((220, 220, 215), .06),
        "afternoon": ((255, 210, 150), .12), "dusk": ((255, 200, 150), .14), "night": ((255, 200, 140), .16),
        "rain_night": ((175, 190, 225), .18), "screen_glow": ((180, 200, 240), .16)}

# ---------------- assets ----------------
_pc, _cc = {}, {}
def _placeholder(label, size, rgba=False):
    im = Image.new("RGBA" if rgba else "RGB", size, (0, 0, 0, 0) if rgba else (30, 38, 58)); d = ImageDraw.Draw(im)
    d.rectangle([4, 4, size[0] - 5, size[1] - 5], outline=(120, 130, 150, 255), width=4)
    d.text((24, 24), "MISSING " + label, font=F(MONO, 28), fill=(200, 200, 210, 255)); return im
def plate_of(st, tm):
    k = f"set_{st}__{tm}"
    if k not in _pc:
        m = MAN.get(k); p = os.path.join(ASSETS, m["asset"]) if m else ""
        _pc[k] = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS) if p and os.path.exists(p) else _placeholder(k, (W, H))
    return _pc[k]
def shot_img(k):
    if k not in _pc:
        _pc[k] = Image.open(os.path.join(ASSETS, MAN[k]["asset"])).convert("RGB").resize((W, H), Image.LANCZOS)
    return _pc[k]
def cut_of(who, pose, hfrac, tm):
    k = (who, pose, round(hfrac, 3), tm)
    if k not in _cc:
        n = f"char_{who}__{pose}"; m = MAN.get(n); p = os.path.join(ASSETS, m["cut"]) if m and m.get("cut") else ""
        if p and os.path.exists(p):
            im = Image.open(p).convert("RGBA"); bb = im.getbbox(); im = im.crop(bb) if bb else im
        else:
            im = _placeholder(n, (420, 900), True)
        h = int(H * hfrac); im = im.resize((max(1, int(im.size[0] * h / im.size[1])), h), Image.LANCZOS)
        tint, kk = TINT.get(tm, ((255, 210, 160), .12)); _cc[k] = match(im, tint, kk, (255, 205, 140), .4)
    return _cc[k]

# ---------------- drawing helpers ----------------
def board():
    fr = Image.new("RGB", (W, H), NAVY); dr = ImageDraw.Draw(fr)
    for x in range(0, W, 96): dr.line([(x, 0), (x, H)], fill=(22, 32, 54))
    for y in range(0, H, 96): dr.line([(0, y), (W, y)], fill=(22, 32, 54))
    return fr
def cw(dr, txt, f, y, col, stroke=0):
    tw = dr.textlength(txt, font=f); dr.text(((W - tw) / 2, y), txt, font=f, fill=col, stroke_width=stroke, stroke_fill=(0, 0, 0))
def wrap(dr, txt, f, width):
    out, cur = [], ""
    for w in txt.split():
        t = (cur + " " + w).strip()
        if dr.textlength(t, font=f) <= width: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out
def source(dr, s, recreated=False):
    if s: cw(dr, ("RECREATED FROM: " if recreated else "SOURCE: ") + s.upper(), F(MONO, 24), 1000 - 190, GREY)
def drift(fr, t, d, k=.03): return zoom(fr, 1 + k * ease(t / max(d, .1)))

def paper_card(wd, ht, accent=RED):
    c = Image.new("RGBA", (wd, ht), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rectangle([0, 0, wd - 1, ht - 1], fill=PAPER + (255,)); d.rectangle([0, 0, wd - 1, 9], fill=accent + (255,)); return c, d
def drop(fr, card, x, y, a, rot=-1.0):
    card = card.rotate(rot, resample=Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0)); sh.putalpha(card.getchannel("A").point(lambda v: v * 0.45)); sh = sh.filter(ImageFilter.GaussianBlur(14))
    x = x + (1 - a) * 900; fr.paste(sh, (int(x + 14), int(y + 18)), sh); fr.paste(card, (int(x), int(y)), card)

def highlight_lines(cd, lines, f, x0, y0, lh, hl, t, t0=.7, ink=(24, 24, 30)):
    """draw text lines; sweep an amber highlighter over the substring hl (first line it is on)"""
    for k, ln in enumerate(lines):
        y = y0 + k * lh
        if hl and hl.lower() in ln.lower() and t > t0:
            i = ln.lower().index(hl.lower()); xa = x0 + cd.textlength(ln[:i], font=f); wb = cd.textlength(ln[i:i + len(hl)], font=f)
            cd.rectangle([xa - 4, y - 4, xa + wb * eout((t - t0) / .45) + 6, y + f.size + 8], fill=(250, 214, 130))
        cd.text((x0, y), ln, font=f, fill=ink)

# ---------------- shot types ----------------
def s_scene(s, t, d):
    st, tm = s.get("set", "board"), s.get("time", "night")
    cast = s.get("cast", [])
    shot = "shot_" + st + "__" + tm + "__" + "+".join(f"{c['who']}-{c.get('pose', 'front_neutral')}" for c in cast[:2]) if cast else ""
    composed = bool(shot) and shot in MAN and s.get("compose", True)
    fr = board() if st == "board" else (shot_img(shot) if composed else plate_of(st, tm)).copy()
    if composed: cast = []           # the cast is already painted into the picture
    for L in s.get("light", []):     # [x, y, r] in 0-1 frame units: warm lamp that breathes
        fr = glow(fr, int(L[0] * W), int(L[1] * H), int(L[2] * W), (255, 205, 130), .14 + .03 * math.sin(t * 1.9 + L[0] * 7))
    for k, c in enumerate(cast):
        sp = cut_of(c["who"], c.get("pose", "front_neutral"), c.get("h", LIB["cast"].get(c["who"], {}).get("h", .84)), tm)
        if c.get("flip"): sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        u = ease(t / max(d, .1)); par = {"pan_l": -1, "pan_r": 1}.get(s.get("move"), 0) * 26 * u
        enter = eout((t - c.get("enter", 0)) / .5) if c.get("enter") is not None else 1
        if enter <= 0: continue
        paste(fr, sp, int(c.get("x", .5) * W + par), int(H * c.get("y", .97)), breathe=.006 * math.sin(t * 2.1 + k), alpha=enter)
    for o in s.get("overlay", []):   # code text on screens, boards, envelopes
        if t < o.get("t", 0): continue
        dr = ImageDraw.Draw(fr); dr.text((o["x"] * W, o["y"] * H), o["text"], font=F(MONO if o.get("mono", True) else ANTON, o.get("size", 30)), fill=COL.get(o.get("color", "amber"), GOLD))
    fx = s.get("fx", [])
    if "rain" in fx: rain(fr, t)
    if "dust" in fx: dust(fr, t)
    if "sparks" in fx: sparkles(fr, W // 2, H // 3, t)
    if "flicker" in fx: fr = ImageEnhance.Brightness(fr).enhance(.96 + .04 * math.sin(t * 23) * math.sin(t * 7))
    if "dim" in fx: fr = Image.blend(fr, Image.new("RGB", (W, H), (6, 8, 16)), .45 * ease(t / max(d, .1)))
    u = ease(t / max(d, .1)); mv = s.get("move", "push")
    z = {"push": 1 + .07 * u, "pull": 1.07 - .07 * u, "hold": 1.02, "pan_l": 1.06, "pan_r": 1.06}.get(mv, 1.03)
    cx = {"pan_l": .53 - .06 * u, "pan_r": .47 + .06 * u}.get(mv, s.get("focus", [.5, .5])[0])
    return zoom(fr, z, cx, s.get("focus", [.5, .5])[1]), True

def s_stat(s, t, d):
    col = COL.get(s.get("color", "gold"), GOLD); fr = board(); fr = glow(fr, 960, 380, 420, col, .18); dr = ImageDraw.Draw(fr)
    v = float(s.get("value", 0)) * eout(t / 1.1); dec = s.get("decimals", 0)
    txt = s.get("prefix", "") + (f"{v:,.{dec}f}" if not s.get("text") else s["text"]) + s.get("suffix", "")
    f = F(ANTON, int(250 * (0.9 + 0.1 * back(t / .45)))); tw = dr.textlength(txt, font=f)
    dr.text(((W - tw) / 2, 380 - f.size * .62), txt, font=f, fill=col)
    a = eout((t - .5) / .6)
    if a > 0: cw(dr, s.get("label", ""), F(ANTON, 72), 560 + 20 * (1 - a), PAPER)
    if t > .6: source(dr, s.get("source", ""))
    return drift(fr, t, d), False

def s_headline(s, t, d):
    fr = board(); a = eout(t / .75); c, cd = paper_card(1440, 330, COL.get(s.get("accent", "red"), RED))
    cd.text((44, 30), (s.get("outlet", "") + "  ·  " + s.get("date", "")).upper(), font=F(MONO, 26), fill=(110, 104, 96))
    fa = F(SERIF, 50); hl = wrap(cd, s.get("title", ""), fa, 1350)[:2]
    highlight_lines(cd, hl, fa, 44, 86, 66, s.get("highlight"), t)
    if s.get("sub"): cd.text((44, 86 + 66 * len(hl) + 16), s["sub"], font=F(SERIF, 38), fill=(60, 58, 60))
    drop(fr, c, 240, 250, a)
    dr = ImageDraw.Draw(fr)
    if t > .8: source(dr, s.get("source", ""), s.get("recreated", True))
    return drift(fr, t, d, .025), False

def s_card(s, t, d):   # filing, email, quote, document: kind decides the header
    fr = board(); a = eout(t / .75); kind = s.get("kind", "filing")
    lines_in = s.get("lines", []); f = F(SERIF if kind != "email" else SANS, 40)
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8))); body = []
    for ln in lines_in: body += wrap(probe, ln, f, 1300)
    ht = 150 + 58 * len(body) + 40; c, cd = paper_card(1440, ht, COL.get(s.get("accent", "red" if kind != "email" else "grey"), RED))
    hdr = s.get("header") or {"email": "EMAIL", "filing": "COURT FILING", "quote": "QUOTE", "doc": "DOCUMENT", "post": "POST"}.get(kind, kind.upper())
    cd.text((44, 30), (hdr + ("  ·  " + s["date"] if s.get("date") else "")).upper(), font=F(MONO, 26), fill=(110, 104, 96))
    if s.get("from"): cd.text((44, 72), s["from"], font=F(SANS, 30), fill=(60, 58, 60))
    highlight_lines(cd, body, f, 44, 130, 58, s.get("highlight"), t)
    drop(fr, c, 240, max(80, (H - ht) // 2 - 40), a)
    dr = ImageDraw.Draw(fr)
    if t > .8: source(dr, s.get("source", ""), s.get("recreated", True))
    return drift(fr, t, d, .02), False

def s_name(s, t, d):
    fr = board(); dr = ImageDraw.Draw(fr); a = eout(t / .6)
    dr.rectangle([300, 420, 300 + 1320 * a, 428], fill=COL.get(s.get("color", "gold"), GOLD))
    cw(dr, s.get("name", ""), F(ANTON, 110), 270 + 20 * (1 - a), PAPER)
    if t > .35: cw(dr, s.get("role", "").upper(), F(MONO, 34), 470, GREY)
    if t > .6: source(dr, s.get("source", ""))
    return drift(fr, t, d, .02), False

def s_chapter(s, t, d):
    fr = Image.new("RGB", (W, H), (8, 10, 18)); dr = ImageDraw.Draw(fr); a = eout(t / .6)
    cw(dr, f"PART {s.get('num', '')}", F(MONO, 36), 380, GOLD)
    cw(dr, s.get("title", "").upper(), F(ANTON, 140), 440 + 30 * (1 - a), PAPER)
    return drift(fr, t, d, .02), False

def s_flow(s, t, d):   # boxes left->right with arrows, one appearing every `step` s; optional red strike on one
    fr = board(); dr = ImageDraw.Draw(fr); bx = s.get("boxes", []); n = max(1, len(bx)); step = s.get("step", .6)
    gw = 1600 // n; f = F(ANTON, 54 if n < 5 else 42)
    for k, b in enumerate(bx):
        a = eout((t - k * step) / .45)
        if a <= 0: continue
        x0 = 160 + k * gw + 20; x1 = x0 + gw - 80; y0, y1 = 420 + 30 * (1 - a), 620 + 30 * (1 - a)
        col = COL.get(b.get("color", "paper"), PAPER) if isinstance(b, dict) else PAPER; lab = b["label"] if isinstance(b, dict) else b
        dr.rounded_rectangle([x0, y0, x1, y1], 18, outline=col, width=6)
        for j, ln in enumerate(wrap(dr, lab.upper(), f, x1 - x0 - 30)[:2]):
            tw = dr.textlength(ln, font=f); dr.text(((x0 + x1 - tw) / 2, y0 + 40 + j * (f.size + 8)), ln, font=f, fill=col)
        if k and a > .5: dr.line([(x0 - 70, 520), (x0 - 12, 520)], fill=GOLD, width=6); dr.polygon([(x0 - 12, 508), (x0 - 12, 532), (x0 + 4, 520)], fill=GOLD)
        if isinstance(b, dict) and b.get("strike") and t > k * step + .8:
            kk = eout((t - k * step - .8) / .35); dr.line([(x0 - 10, y1 + 10), (x0 - 10 + (x1 - x0 + 20) * kk, y0 - 10)], fill=RED, width=14)
    if s.get("title"): cw(dr, s["title"].upper(), F(ANTON, 70), 220, GOLD)
    if t > .6: source(dr, s.get("source", ""))
    return drift(fr, t, d, .02), False

def s_tree(s, t, d):   # downline pyramid: one node on top, levels multiply
    fr = board(); dr = ImageDraw.Draw(fr); lv = s.get("levels", 4); br = s.get("branch", 3)
    for L in range(lv):
        a = eout((t - L * .5) / .45)
        if a <= 0: continue
        n = br ** L; y = 230 + L * 170; sp = 1600 / n
        for k in range(n):
            x = 160 + sp * (k + .5); r = max(6, 34 - L * 8)
            if L:
                px = 160 + (1600 / n * br) * (k // br + .5); dr.line([(px, y - 170 + r), (x, y - r)], fill=(70, 84, 110), width=3)
            dr.ellipse([x - r, y - r, x + r, y + r], fill=GOLD if L == 0 else PAPER)
    if s.get("label") and t > .5: cw(dr, s["label"].upper(), F(ANTON, 64), 900, GOLD)
    if t > .6: source(dr, s.get("source", ""))
    return drift(fr, t, d, .02), False

def s_bars(s, t, d):
    fr = board(); dr = ImageDraw.Draw(fr); it = s.get("items", []); mx = max([float(i["value"]) for i in it] + [1e-9])
    n = max(1, len(it)); gw = 1200 // n
    for k, i in enumerate(it):
        a = eout((t - k * .5) / 1.0); hh = 560 * (float(i["value"]) / mx) * a
        x0 = 360 + k * gw + 60; x1 = x0 + gw - 120; col = COL.get(i.get("color", "gold"), GOLD)
        dr.rectangle([x0, 800 - max(4, hh), x1, 800], fill=col)
        f = F(ANTON, 60); tw = dr.textlength(i.get("text", ""), font=f); dr.text(((x0 + x1 - tw) / 2, 800 - max(4, hh) - 80), i.get("text", ""), font=f, fill=col)
        f2 = F(MONO, 28); tw = dr.textlength(i.get("label", "").upper(), font=f2); dr.text(((x0 + x1 - tw) / 2, 820), i.get("label", "").upper(), font=f2, fill=PAPER)
    if t > .6: source(dr, s.get("source", ""))
    return drift(fr, t, d, .02), False

def s_timeline(s, t, d):
    fr = board(); dr = ImageDraw.Draw(fr); ev = s.get("events", []); n = max(1, len(ev))
    a0 = eout(t / .8); dr.line([(160, 540), (160 + 1600 * a0, 540)], fill=GREY, width=4)
    for k, e in enumerate(ev):
        a = eout((t - .3 - k * .45) / .4)
        if a <= 0: continue
        x = 160 + 1600 * (k + .5) / n; col = COL.get(e.get("color", "gold"), GOLD)
        dr.ellipse([x - 14, 526, x + 14, 554], fill=col)
        f = F(MONO, 28); tw = dr.textlength(e["date"], font=f); dr.text((x - tw / 2, 470 - 20 * (1 - a)), e["date"], font=f, fill=col)
        for j, ln in enumerate(wrap(dr, e["label"].upper(), F(ANTON, 40), 1600 / n - 30)[:3]):
            tw = dr.textlength(ln, font=F(ANTON, 40)); dr.text((x - tw / 2, 580 + j * 48), ln, font=F(ANTON, 40), fill=PAPER)
    if t > .6: source(dr, s.get("source", ""))
    return drift(fr, t, d, .02), False

def s_list(s, t, d):   # 1-4 bold claims that flip in one by one; optional strike on each
    fr = board(); dr = ImageDraw.Draw(fr); it = s.get("items", []); step = s.get("step", .8)
    for k, x in enumerate(it):
        a = eout((t - k * step) / .4)
        if a <= 0: continue
        lab = x["text"] if isinstance(x, dict) else x; y = 260 + k * 150; f = F(ANTON, 86)
        tw = dr.textlength(lab.upper(), font=f); x0 = (W - tw) / 2
        dr.text((x0 + 40 * (1 - a), y), lab.upper(), font=f, fill=PAPER)
        if isinstance(x, dict) and x.get("strike") and t > k * step + .6:
            kk = eout((t - k * step - .6) / .3); dr.line([(x0 - 20, y + 60), (x0 - 20 + (tw + 40) * kk, y + 50)], fill=RED, width=12)
    if t > .6: source(dr, s.get("source", ""))
    return drift(fr, t, d, .02), False

def s_screen(s, t, d):  # a phone or laptop screen with code-drawn UI, over a set or the board
    st = s.get("set"); fr = plate_of(st, s.get("time", "night")).copy() if st and st != "board" else board()
    fr = Image.blend(fr, Image.new("RGB", (W, H), (6, 8, 16)), .55)
    dev = s.get("device", "laptop"); a = eout(t / .5)
    sw, sh = (1180, 700) if dev == "laptop" else (520, 920)
    x0, y0 = (W - sw) // 2, (H - sh) // 2 + int(30 * (1 - a)); dr = ImageDraw.Draw(fr)
    dr.rounded_rectangle([x0 - 22, y0 - 22, x0 + sw + 22, y0 + sh + 22], 34 if dev == "phone" else 18, fill=(12, 14, 20))
    dr.rectangle([x0, y0, x0 + sw, y0 + sh], fill=(22, 28, 44))
    ui = s.get("ui", "text")
    if ui == "balance":
        v = float(s.get("value", 0)) * eout(t / 1.4) * (1 + s.get("tick", 0) * t); dec = s.get("decimals", 0)
        dr.text((x0 + 50, y0 + 50), s.get("title", "BALANCE").upper(), font=F(MONO, 30), fill=GREY)
        f = F(ANTON, 150 if dev == "laptop" else 96); txt = s.get("prefix", "") + f"{v:,.{dec}f}" + s.get("suffix", "")
        dr.text((x0 + 50, y0 + 130), txt, font=f, fill=GOLD)
        if s.get("sub"): dr.text((x0 + 50, y0 + 150 + f.size + 30), s["sub"], font=F(MONO, 30), fill=GREEN)
    elif ui == "chat":
        y = y0 + 40
        for k, m in enumerate(s.get("messages", [])):
            if t < k * .7: break
            f = F(SANS, 34); ln = wrap(dr, m["text"], f, sw - 160); bh = 26 + 44 * len(ln); mine = m.get("me", False)
            bx0 = x0 + (sw - 40 - min(sw - 120, max(dr.textlength(l, font=f) for l in ln) + 50) if mine else 30)
            bx1 = bx0 + min(sw - 120, max(dr.textlength(l, font=f) for l in ln) + 50)
            dr.rounded_rectangle([bx0, y, bx1, y + bh], 22, fill=(60, 110, 90) if mine else (52, 60, 84))
            for j, l in enumerate(ln): dr.text((bx0 + 24, y + 14 + j * 44), l, font=f, fill=WHITE)
            if m.get("meta"): dr.text((bx0 + 24, y + bh + 6), m["meta"], font=F(MONO, 22), fill=GREY)
            y += bh + 54
    elif ui == "banner":
        f = F(ANTON, 120 if dev == "laptop" else 80); pul = 1 + .03 * math.sin(t * 5)
        for j, ln in enumerate(wrap(dr, s.get("text", "").upper(), f, sw - 100)):
            tw = dr.textlength(ln, font=f); dr.text((x0 + (sw - tw) / 2, y0 + sh / 2 - 90 + j * (f.size + 10)), ln, font=f, fill=GOLD)
        fr = glow(fr, W // 2, H // 2, int(300 * pul), GOLD, .10)
    else:
        f = F(SANS, 40); y = y0 + 60
        for ln in s.get("lines", []):
            for l in wrap(dr, ln, f, sw - 100): dr.text((x0 + 50, y), l, font=f, fill=PAPER); y += 54
    return drift(fr, t, d, .04), bool(st)

def s_chart(s, t, d):   # a line that draws itself; "points" 0-1 heights, "shape illustrative" tag unless real data
    fr = board(); dr = ImageDraw.Draw(fr); pts = s.get("points", [.05, .06, .08, .07, .12, .2, .35, .5, .8, 1.0])
    col = COL.get(s.get("color", "gold"), GOLD); x0, x1, y0, y1 = 220, 1700, 260, 800
    dr.line([(x0, y1), (x1, y1)], fill=GREY, width=3); dr.line([(x0, y0), (x0, y1)], fill=GREY, width=3)
    k = eout(t / s.get("draw", 1.6)) * (len(pts) - 1); xy = []
    for j in range(len(pts)):
        if j > k: break
        xy.append((x0 + (x1 - x0) * j / (len(pts) - 1), y1 - (y1 - y0) * pts[j]))
    if k % 1 and int(k) + 1 < len(pts):
        j = int(k); f = k - j; a, b = pts[j], pts[j + 1]
        xy.append((x0 + (x1 - x0) * (j + f) / (len(pts) - 1), y1 - (y1 - y0) * (a + (b - a) * f)))
    if len(xy) > 1: dr.line(xy, fill=col, width=10, joint="curve")
    if xy: fr = glow(fr, int(xy[-1][0]), int(xy[-1][1]), 60, col, .35); dr = ImageDraw.Draw(fr)
    if s.get("label") and t > .5: cw(dr, s["label"].upper(), F(ANTON, 60), 120, PAPER)
    if s.get("illustrative", True): dr.text((x1 - 300, y1 + 20), "SHAPE ILLUSTRATIVE", font=F(MONO, 24), fill=GREY)
    if t > .6: source(dr, s.get("source", ""))
    return drift(fr, t, d, .02), False

def s_coin(s, t, d):    # one gold coin; "drain" empties it to a dotted outline
    fr = board(); fr = glow(fr, 960, 470, 300, GOLD, .12); dr = ImageDraw.Draw(fr); r = 230; cx, cy = 960, 470
    lvl = 1 - eout((t - s.get("drain_at", .6)) / 1.6) if s.get("drain") else 1
    if lvl > 0:
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        cut = Image.new("L", (W, H), 0); ImageDraw.Draw(cut).rectangle([0, cy + r - 2 * r * lvl, W, H], fill=255)
        m = ImageChops.multiply(m, cut); fr.paste(Image.new("RGB", (W, H), GOLD), (0, 0), m); dr = ImageDraw.Draw(fr)
        dr.ellipse([cx - r + 30, cy - r + 30, cx + r - 30, cy + r - 30], outline=(200, 150, 40), width=6)
    for a in range(0, 360, 8):
        x = cx + r * math.cos(math.radians(a)); y = cy + r * math.sin(math.radians(a)); dr.ellipse([x - 5, y - 5, x + 5, y + 5], fill=PAPER)
    if s.get("label") and t > .5: cw(dr, s["label"].upper(), F(ANTON, 70), 760, PAPER)
    return drift(fr, t, d, .06), False

def s_end(s, t, d):
    fr = Image.new("RGB", (W, H), (8, 10, 18)); dr = ImageDraw.Draw(fr); a = eout(t / .8)
    cw(dr, s.get("text", "WISDROP").upper(), F(ANTON, 120), 420 + 20 * (1 - a), PAPER)
    if s.get("sub"): cw(dr, s["sub"], F(MONO, 32), 580, GREY)
    return fr, False

TYPES = {"scene": s_scene, "stat": s_stat, "headline": s_headline, "card": s_card, "name": s_name, "chapter": s_chapter,
         "flow": s_flow, "tree": s_tree, "bars": s_bars, "timeline": s_timeline, "list": s_list, "screen": s_screen, "end": s_end, "chart": s_chart, "coin": s_coin}

# ---------------- schedule ----------------
SHOTS = []
for s in SH["shots"]:
    at = s["at"]; t0 = (ST[at] + LEAD if at in ST else 0) + s.get("offset", 0)
    SHOTS.append((0.0 if not SHOTS else t0, s))
SHOTS.sort(key=lambda x: x[0])
STARTS = [x[0] for x in SHOTS] + [DUR]

# ---------------- captions ----------------
chunks = []
for sg in SEGS:
    lw = [tuple(w) for w in sg.get("words", [])]
    if not lw:
        ws = sg["text"].split(); tot = sum(len(w) + 2 for w in ws) or 1; cur = sg["start"]; dd0 = sg["end"] - sg["start"]
        for w in ws: dd = dd0 * (len(w) + 2) / tot; lw.append((cur, cur + dd, w)); cur += dd
    c = []
    for w in lw:
        c.append(w)
        if len(c) == 4 or w[2].endswith((".", ",", "?", "!", ":")): chunks.append(c); c = []
    if c: chunks.append(c)
def caption(fr, t):
    ch = next((c for c in chunks if c[0][0] <= t < c[-1][1] + 0.12), None)
    if not ch: return fr
    dr = ImageDraw.Draw(fr); f = F(ANTON, 62); toks = [w.upper() for _, _, w in ch]
    sp = dr.textlength(" ", font=f); wd = [dr.textlength(x, font=f) for x in toks]; x = (W - sum(wd) - sp * (len(toks) - 1)) / 2
    for (a, b, _), tok, w_ in zip(ch, toks, wd):
        dr.text((x, 925), tok, font=f, fill=GOLD if a <= t < b + .02 else WHITE, stroke_width=6, stroke_fill=(0, 0, 0)); x += w_ + sp
    return fr
def tag(fr):
    dr = ImageDraw.Draw(fr); dr.rounded_rectangle([44, 40, 262, 80], 6, fill=(0, 0, 0)); dr.text((60, 48), "DRAMATISATION", font=F(MONO, 22), fill=PAPER); return fr

def render(i):
    t = i / FPS
    k = max(j for j in range(len(SHOTS)) if STARTS[j] <= t)
    st, s = SHOTS[k]; d = STARTS[k + 1] - st
    fr, story = TYPES[s["type"]](s, t - st, d)
    if 0 <= t - st < DIP and k > 0: fr = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), fr, .45 + .55 * ease((t - st) / DIP))
    fr = finish(fr, i, 0)
    if story and s["type"] == "scene": fr = tag(fr)
    return bug(caption(fr, t)) if s["type"] not in ("chapter", "end") else fr
