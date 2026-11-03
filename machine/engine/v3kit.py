"""Wisdrop v3 visual system: rotating gridded boards, collage toolkit, premium phone screens,
photo layouts, maps, money flow, stamps, scrubber, bar race. Pure code (PIL), CPU only.

shots_render.py loads this when library.json has "look": "v3". Every function draws onto a
1920x1080 RGB frame. All words on screen are drawn here by code.
"""
import json, math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops
from edhelpers import F, ANTON, MONO, SANS, SERIF, ease, eout, back, glow, zoom
import collage as C

W, H = 1920, 1080
HERE = os.path.dirname(os.path.abspath(__file__)); KIT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "kit")
VEC = os.path.join(KIT, "vectors")
INK = (22, 21, 20); CREAM = (241, 233, 215); YEL = (247, 209, 58); RED = (226, 70, 54); WHITE = (255, 255, 255)
GREEN = (52, 199, 89); BLUE = (10, 132, 255)

# ---------------- boards: one per part, rotating; faint grid + paper grain ----------------
THEMES = [  # bg, grid, ink (text), sub (secondary text), accent text colour
    {"name": "navy", "bg": (20, 31, 54), "grid": (34, 47, 74), "ink": CREAM, "sub": (150, 162, 184), "acc": YEL, "dark": True},
    {"name": "offwhite", "bg": (236, 229, 213), "grid": (214, 205, 186), "ink": INK, "sub": (110, 102, 90), "acc": (200, 60, 40), "dark": False},
    {"name": "sky", "bg": (146, 190, 222), "grid": (124, 170, 204), "ink": (16, 28, 48), "sub": (40, 64, 96), "acc": (190, 40, 30), "dark": False},
    {"name": "charcoal", "bg": (31, 30, 28), "grid": (48, 47, 44), "ink": CREAM, "sub": (150, 145, 134), "acc": YEL, "dark": True},
]
_rng = np.random.default_rng(23)
def _make_board(th):
    base = C._paper(th["bg"], 18 if th["dark"] else 12)
    d = ImageDraw.Draw(base)
    for x in range(0, W, 80): d.line([(x, 0), (x, H)], fill=th["grid"], width=1)
    for y in range(0, H, 80): d.line([(0, y), (W, y)], fill=th["grid"], width=1)
    for x in range(0, W, 400): d.line([(x, 0), (x, H)], fill=th["grid"], width=2)
    v = Image.new("L", (W, H), 0); ImageDraw.Draw(v).ellipse([-300, -260, W + 300, H + 260], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(160))
    return Image.composite(base, Image.blend(base, Image.new("RGB", (W, H), (0, 0, 0)), .28 if th["dark"] else .12), v)
BOARDS = {}
def board(part=0):
    k = part % len(THEMES)
    if k not in BOARDS: BOARDS[k] = _make_board(THEMES[k])
    return BOARDS[k].copy()
def theme(part=0): return THEMES[part % len(THEMES)]

# ---------------- icons (Tabler MIT font, OpenMoji CC BY-SA png) ----------------
_TMAP = None
def icon(dr, name, x, y, size, col, anchor="mm"):
    global _TMAP
    if _TMAP is None: _TMAP = json.load(open(os.path.join(VEC, "tabler", "map.json")))
    cp = _TMAP.get(name)
    if cp is None: return
    dr.text((x, y), chr(cp), font=F(os.path.join(VEC, "tabler", "tabler-icons.ttf"), int(size)), fill=col, anchor=anchor)
_emo = {}
def emoji(code, size):
    k = (code, size)
    if k not in _emo:
        p = os.path.join(VEC, "openmoji", code.upper() + ".png")
        _emo[k] = Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS) if os.path.exists(p) else None
    return _emo[k]

# ---------------- toolkit ----------------
def shadow_paste(fr, im, x, y, blur=16, off=(10, 16), a=.5):
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.split()[3].point(lambda v: int(v * a)))
    sh = sh.filter(ImageFilter.GaussianBlur(blur)); fr.paste((0, 0, 0), (int(x + off[0]), int(y + off[1])), sh); fr.paste(im, (int(x), int(y)), im)

def tape(fr, cx, cy, ang=-8, w=150, h=44):
    tp = Image.new("RGBA", (w, h), (236, 226, 190, 170)); d = ImageDraw.Draw(tp)
    for k in range(0, w, 6): d.line([(k, 0), (k, 3)], fill=(220, 210, 170, 120))
    tp = tp.rotate(ang, expand=True, resample=Image.BICUBIC); fr.paste(tp, (int(cx - tp.size[0] / 2), int(cy - tp.size[1] / 2)), tp)

def arrow(dr, p0, p1, u, col=RED, w=8, bend=.18):
    """hand-drawn curved arrow from p0 to p1, drawn up to progress u (0-1)."""
    if u <= 0: return
    (x0, y0), (x1, y1) = p0, p1; mx, my = (x0 + x1) / 2 - (y1 - y0) * bend, (y0 + y1) / 2 + (x1 - x0) * bend
    n = 40; m = max(2, int(n * min(1, u))); pts = []
    for k in range(m):
        t = k / (n - 1); pts.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t * t * y1))
    dr.line(pts, fill=col, width=w, joint="curve")
    if u >= 1:
        ax, ay = pts[-1]; bx, by = pts[-3]; a = math.atan2(ay - by, ax - bx)
        for s in (2.6, -2.6): dr.line([(ax, ay), (ax + 34 * math.cos(a + s), ay + 34 * math.sin(a + s))], fill=col, width=w)

def underline(dr, x0, x1, y, u, col=RED, w=8):
    if u <= 0: return
    xe = x0 + (x1 - x0) * min(1, u); pts = [(x, y + 4 * math.sin(x / 37)) for x in np.linspace(x0, xe, 24)]
    dr.line(pts, fill=col, width=w, joint="curve")

def pop_sticker(fr, text, x, y, t, font=None, bg=YEL, fg=INK, rot=-4):
    """sticker that pops in with overshoot at its own t>=0."""
    if t <= 0: return
    font = font or F(ANTON, 44); e = back(min(1, t / .3)); sz = max(6, int(font.size * e))
    f2 = F(font.path, sz); d0 = ImageDraw.Draw(fr); tw = d0.textlength(text, font=f2)
    im = Image.new("RGBA", (int(tw) + 34, sz + 24), bg + (255,)); ImageDraw.Draw(im).text((17, 6), text, font=f2, fill=fg)
    im = im.rotate(rot, expand=True, resample=Image.BICUBIC); shadow_paste(fr, im, x - im.size[0] / 2, y - im.size[1] / 2, 8, (4, 6), .35)

def stamp_img(text, col=RED, size=150, sub=""):
    f = F(ANTON, size); d0 = ImageDraw.Draw(Image.new("RGB", (8, 8))); tw = d0.textlength(text, font=f)
    w, h = int(tw) + 90, size + (110 if sub else 70); im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, w - 7, h - 7], 18, outline=col + (255,), width=12)
    d.text((45, 20), text, font=f, fill=col + (255,))
    if sub: d.text((w / 2, h - 52), sub, font=F(MONO, 30), fill=col + (255,), anchor="mm")
    noise = Image.fromarray((np.random.default_rng(len(text)).random((h, w)) > .18).astype(np.uint8) * 255)
    im.putalpha(ImageChops.multiply(im.split()[3], noise.filter(ImageFilter.GaussianBlur(.7))))
    return im

def sticker_photo(img, width, mood="archive", key=None, border=16, seed=1):
    """treated photo with a white sticker border and rounded corners (RGBA)."""
    tw = width - 2 * border; th = int(tw * img.size[1] / img.size[0])
    pic = C.treat(img, mood, key=(key, mood) if key else None).resize((tw, th), Image.LANCZOS)
    card = Image.new("RGBA", (width, th + 2 * border), (250, 248, 242, 255)); card.paste(pic, (border, border))
    m = Image.new("L", card.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, card.size[0] - 1, card.size[1] - 1], 14, fill=255); card.putalpha(m)
    return card

def polaroid(img, width, mood="archive", key=None, caption="", seed=1):
    b = int(width * .06); tw = width - 2 * b; th = int(tw * .82)
    src = img
    if img.size[0] / img.size[1] > tw / th:
        cw = int(img.size[1] * tw / th); src = img.crop(((img.size[0] - cw) // 2, 0, (img.size[0] - cw) // 2 + cw, img.size[1]))
    else:
        ch = int(img.size[0] * th / tw); src = img.crop((0, (img.size[1] - ch) // 3, img.size[0], (img.size[1] - ch) // 3 + ch))
    pic = C.treat(src, mood, key=(key, mood, "pol") if key else None).resize((tw, th), Image.LANCZOS)
    card = Image.new("RGBA", (width, th + b + int(width * .2)), (248, 246, 240, 255)); card.paste(pic, (b, b))
    if caption:
        ImageDraw.Draw(card).text((width / 2, th + b + int(width * .1)), caption, font=F(MONO, max(18, width // 16)), fill=INK, anchor="mm")
    return card

def place(fr, card, cx, cy, rot, t, delay=0, from_dir=1, scale=1.0):
    """drop a card in with a little overshoot, then let it settle."""
    tt = t - delay
    if tt <= 0: return
    e = back(min(1, tt / .5)); s = scale * (1.12 - .12 * min(1, tt / .5))
    c = card.resize((max(1, int(card.size[0] * s)), max(1, int(card.size[1] * s))), Image.BILINEAR) if s != 1 else card
    c = c.rotate(rot * (1 + (1 - e) * 1.5), expand=True, resample=Image.BICUBIC)
    x = cx - c.size[0] / 2 + (1 - e) * 220 * from_dir; y = cy - c.size[1] / 2 + (1 - e) * 90
    shadow_paste(fr, c, x, y)

def wrap(dr, txt, f, width):
    out, cur = [], ""
    for w in str(txt).split():
        t = (cur + " " + w).strip()
        if dr.textlength(t, font=f) <= width: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out

def source_line(dr, s, th, recreated=False):
    if s: dr.text((W / 2, 852), ("RECREATED FROM: " if recreated else "SOURCE: ") + s.upper(), font=F(MONO, 22), fill=th["sub"], anchor="mm")

# ---------------- premium phone screens ----------------
PW, PH = 440, 900
def phone_frame():
    im = Image.new("RGBA", (PW + 36, PH + 36), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, PW + 35, PH + 35], 64, fill=(18, 18, 22, 255))
    d.rounded_rectangle([3, 3, PW + 32, PH + 32], 62, outline=(70, 70, 78, 255), width=3)
    return im
_PF = None

def status_bar(d, dark_text=True, tm="9:41"):
    c = (12, 12, 14) if dark_text else WHITE
    d.text((40, 22), tm, font=F(SANS, 22), fill=c)
    d.rounded_rectangle([PW / 2 - 62, 12, PW / 2 + 62, 46], 17, fill=(8, 8, 10))   # island
    icon(d, "antenna-bars-5", PW - 112, 34, 24, c); icon(d, "wifi", PW - 82, 34, 24, c); icon(d, "battery-3", PW - 48, 34, 28, c)

def _bubble(d, text, y, me, f, maxw, fill, fg, meta="", meta_col=(140, 140, 146), name="", name_col=None, x_pad=18):
    ln = wrap(d, text, f, maxw - 44); bw = min(maxw, max([d.textlength(l, font=f) for l in ln] + [d.textlength(name, font=F(SANS, 18)) if name else 0]) + 40)
    nh = 24 if name else 0; bh = 22 + nh + 34 * len(ln)
    x0 = PW - x_pad - bw if me else x_pad
    d.rounded_rectangle([x0, y, x0 + bw, y + bh], 22, fill=fill)
    if name: d.text((x0 + 20, y + 10), name, font=F(SANS, 18), fill=name_col or BLUE)
    for j, l in enumerate(ln): d.text((x0 + 20, y + 11 + nh + j * 34), l, font=f, fill=fg)
    if meta: d.text((x0 + bw - 8 if me else x0 + 8, y + bh + 4), meta, font=F(SANS, 15), fill=meta_col, anchor="ra" if me else "la")
    return bh + (26 if meta else 12)

def screen_sms(s, t):
    sc = Image.new("RGB", (PW, PH), (255, 255, 255)); d = ImageDraw.Draw(sc); status_bar(d)
    d.rectangle([0, 56, PW, 150], fill=(246, 246, 248)); d.line([(0, 150), (PW, 150)], fill=(220, 220, 224))
    d.ellipse([PW / 2 - 26, 62, PW / 2 + 26, 114], fill=(170, 176, 190)); icon(d, "user", PW / 2, 88, 34, WHITE)
    d.text((PW / 2, 132), s.get("title", "Dee"), font=F(SANS, 20), fill=(20, 20, 24), anchor="mm"); icon(d, "chevron-left", 28, 100, 34, BLUE)
    y = 170; f = F(SANS, 25); step = s.get("step", .9); t0 = s.get("first", .5)
    for k, m in enumerate(s.get("messages", [])):
        tk = t - t0 - k * step
        if tk < -.45: break
        if tk < 0:   # typing dots before each incoming message
            if not m.get("me"):
                d.rounded_rectangle([18, y, 108, y + 50], 25, fill=(233, 233, 235))
                for j in range(3): d.ellipse([36 + j * 22, y + 19 + 4 * math.sin(t * 9 + j), 48 + j * 22, y + 31 + 4 * math.sin(t * 9 + j)], fill=(140, 140, 146))
            break
        y += _bubble(d, m["text"], y, m.get("me"), f, 320, BLUE if m.get("me") else (233, 233, 235), WHITE if m.get("me") else (14, 14, 16), m.get("meta", ""))
    d.rounded_rectangle([20, PH - 70, PW - 20, PH - 26], 22, outline=(210, 210, 214), width=2); d.text((40, PH - 59), "Text Message", font=F(SANS, 20), fill=(170, 170, 176))
    return sc

def screen_group(s, t):
    sc = Image.new("RGB", (PW, PH), (236, 229, 221)); d = ImageDraw.Draw(sc)
    for yy in range(160, PH, 46):
        for xx in range((yy // 46 % 2) * 23, PW, 46): d.ellipse([xx, yy, xx + 4, yy + 4], fill=(226, 218, 208))
    d.rectangle([0, 0, PW, 150], fill=(17, 94, 84)); status_bar(d, False)
    d.ellipse([60, 74, 116, 130], fill=(200, 214, 210)); icon(d, "users", 88, 102, 34, (17, 94, 84))
    d.text((132, 80), s.get("title", "Group chat"), font=F(SANS, 23), fill=WHITE); d.text((132, 110), s.get("sub", "tap for group info"), font=F(SANS, 17), fill=(200, 230, 225))
    icon(d, "arrow-left", 30, 102, 30, WHITE)
    y = 172; f = F(SANS, 23); step = s.get("step", .9); t0 = s.get("first", .5)
    cols = [(214, 56, 106), (39, 132, 210), (219, 125, 30), (120, 80, 200)]; names = {}
    for k, m in enumerate(s.get("messages", [])):
        if t < t0 + k * step: break
        nm = m.get("from", ""); names.setdefault(nm, cols[len(names) % len(cols)])
        y += _bubble(d, m["text"], y, m.get("me"), f, 330, (217, 253, 211) if m.get("me") else WHITE, (14, 14, 16), m.get("meta", ""), (120, 130, 126), "" if m.get("me") else nm, names[nm], 14)
    d.rectangle([0, PH - 84, PW, PH], fill=(240, 240, 240)); d.rounded_rectangle([16, PH - 70, PW - 76, PH - 22], 24, fill=WHITE)
    d.ellipse([PW - 66, PH - 72, PW - 14, PH - 20], fill=(17, 94, 84)); icon(d, "microphone", PW - 40, PH - 46, 26, WHITE)
    return sc

def screen_notify(s, t):
    sc = Image.new("RGB", (PW, PH), (0, 0, 0)); a = np.linspace(0, 1, PH)[:, None]
    g = (np.array([28, 34, 62]) * (1 - a) + np.array([90, 50, 80]) * a).astype(np.uint8)
    sc = Image.fromarray(np.repeat(g[:, None, :], PW, 1).reshape(PH, PW, 3)); d = ImageDraw.Draw(sc); status_bar(d, False)
    d.text((PW / 2, 150), s.get("date", "Tuesday 25 October"), font=F(SANS, 22), fill=(230, 230, 240), anchor="mm")
    d.text((PW / 2, 230), s.get("time", "9:41"), font=F(SANS, 96), fill=(245, 245, 250), anchor="mm")
    y = 330; step = s.get("step", .9); t0 = s.get("first", .5)
    for k, n in enumerate(s.get("notes", [])):
        tk = t - t0 - k * step
        if tk < 0: break
        e = back(min(1, tk / .35)); yy = y - (1 - e) * 60
        card = Image.new("RGBA", (PW - 28, 118), (245, 245, 248, int(235 * min(1, tk / .2)))); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([12, 18, 54, 60], 11, fill=n.get("color", (52, 120, 246))); icon(cd, n.get("icon", "message-circle"), 33, 39, 26, WHITE)
        cd.text((66, 16), n.get("app", "MESSAGES").upper(), font=F(SANS, 16), fill=(110, 110, 118)); cd.text((PW - 46, 16), n.get("when", "now"), font=F(SANS, 16), fill=(110, 110, 118), anchor="ra")
        cd.text((66, 40), n.get("title", ""), font=F(SANS, 21), fill=(14, 14, 16))
        for j, l in enumerate(wrap(cd, n.get("text", ""), F(SANS, 19), PW - 120)[:2]): cd.text((66, 68 + j * 24), l, font=F(SANS, 19), fill=(40, 40, 46))
        m = Image.new("L", card.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, card.size[0] - 1, card.size[1] - 1], 24, fill=255)
        card.putalpha(ImageChops.multiply(card.split()[3], m)); sc.paste(card, (14, int(yy)), card); y += 132
    return sc

def screen_bank(s, t):
    sc = Image.new("RGB", (PW, PH), (246, 247, 251)); d = ImageDraw.Draw(sc); status_bar(d)
    d.text((28, 76), s.get("title", "Savings"), font=F(SANS, 30), fill=(14, 14, 20)); icon(d, "building-bank", PW - 44, 92, 34, (14, 14, 20))
    d.rounded_rectangle([20, 130, PW - 20, 330], 26, fill=(22, 30, 60))
    d.text((44, 152), s.get("label", "AVAILABLE BALANCE"), font=F(SANS, 17), fill=(170, 180, 210))
    v0, v1 = float(s.get("from", s.get("value", 0))), float(s.get("value", 0)); u = eout((t - s.get("first", .5)) / 1.4)
    v = v0 + (v1 - v0) * u; dec = s.get("decimals", 2)
    d.text((44, 186), s.get("prefix", "€") + f"{v:,.{dec}f}" + s.get("suffix", ""), font=F(SANS, 54), fill=WHITE)
    if s.get("sub"): d.text((44, 270), s["sub"], font=F(SANS, 19), fill=(255, 120, 110) if s.get("down") else (120, 230, 150))
    d.text((28, 360), "Recent activity", font=F(SANS, 22), fill=(14, 14, 20)); y = 404; step = s.get("step", .7)
    for k, r in enumerate(s.get("rows", [])):
        tk = t - s.get("first", .5) - .6 - k * step
        if tk < 0: break
        a = eout(tk / .3); x = 20 + (1 - a) * 80
        d.rounded_rectangle([x, y, x + PW - 40, y + 76], 18, fill=WHITE)
        d.ellipse([x + 14, y + 16, x + 58, y + 60], fill=(232, 236, 246)); icon(d, r.get("icon", "arrow-up-right"), x + 36, y + 38, 24, (40, 60, 120))
        d.text((x + 72, y + 14), r.get("name", ""), font=F(SANS, 20), fill=(14, 14, 20)); d.text((x + 72, y + 44), r.get("when", ""), font=F(SANS, 16), fill=(130, 134, 146))
        d.text((x + PW - 60, y + 26), r.get("amount", ""), font=F(SANS, 21), fill=(210, 50, 40) if r.get("amount", "").startswith("-") else (30, 150, 70), anchor="ra"); y += 90
    return sc

def screen_ticker(s, t):
    sc = Image.new("RGB", (PW, PH), (12, 14, 20)); d = ImageDraw.Draw(sc); status_bar(d, False)
    d.ellipse([28, 80, 84, 136], fill=YEL); d.text((56, 108), s.get("sym", "OC")[:2], font=F(ANTON, 26), fill=INK, anchor="mm")
    d.text((100, 84), s.get("title", "OneCoin"), font=F(SANS, 26), fill=WHITE); d.text((100, 116), s.get("sym", "ONE"), font=F(SANS, 18), fill=(140, 146, 160))
    pts = s.get("points", [.1, .14, .2, .18, .3, .42, .4, .55, .7, .68, .85, 1.0]); u = eout((t - s.get("first", .4)) / s.get("draw", 2.4))
    vals = s.get("values", [0.5, float(s.get("value", 29.95))]); v = vals[0] + (vals[-1] - vals[0]) * u
    d.text((28, 170), s.get("prefix", "€") + f"{v:,.2f}", font=F(SANS, 58), fill=WHITE)
    d.text((28, 244), s.get("change", "+ 5,890%"), font=F(SANS, 24), fill=GREEN)
    x0, x1, y0, y1 = 20, PW - 20, 330, 640; k = u * (len(pts) - 1); xy = []
    for j in range(len(pts)):
        if j > k: break
        xy.append((x0 + (x1 - x0) * j / (len(pts) - 1), y1 - (y1 - y0) * pts[j]))
    if k % 1 and int(k) + 1 < len(pts):
        j = int(k); fr_ = k - j; xy.append((x0 + (x1 - x0) * (j + fr_) / (len(pts) - 1), y1 - (y1 - y0) * (pts[j] + (pts[j + 1] - pts[j]) * fr_)))
    if len(xy) > 1:
        poly = xy + [(xy[-1][0], y1), (x0, y1)]; ov = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); ImageDraw.Draw(ov).polygon(poly, fill=(52, 199, 89, 50))
        sc.paste(ov, (0, 0), ov); d = ImageDraw.Draw(sc); d.line(xy, fill=GREEN, width=5, joint="curve")
        d.ellipse([xy[-1][0] - 9, xy[-1][1] - 9, xy[-1][0] + 9, xy[-1][1] + 9], fill=WHITE)
    for j, lab in enumerate(["1D", "1W", "1M", "1Y", "ALL"]):
        xx = 40 + j * 80; on = lab == "ALL"
        if on: d.rounded_rectangle([xx - 30, 662, xx + 30, 698], 12, fill=(40, 44, 56))
        d.text((xx, 680), lab, font=F(SANS, 18), fill=WHITE if on else (130, 136, 150), anchor="mm")
    d.rounded_rectangle([20, PH - 120, PW - 20, PH - 50], 26, fill=GREEN); d.text((PW / 2, PH - 85), s.get("cta", "BUY"), font=F(SANS, 26), fill=WHITE, anchor="mm")
    if s.get("illustrative", True): d.text((PW / 2, 730), "SHAPE ILLUSTRATIVE", font=F(MONO, 16), fill=(110, 116, 130), anchor="mm")
    return sc

def screen_inbox(s, t):
    sc = Image.new("RGB", (PW, PH), WHITE); d = ImageDraw.Draw(sc); status_bar(d)
    d.text((24, 70), s.get("title", "Inbox"), font=F(SANS, 38), fill=(14, 14, 20)); y = 132; step = s.get("step", .7)
    for k, r in enumerate(s.get("rows", [])):
        tk = t - s.get("first", .5) - k * step
        if tk < 0: break
        a = eout(tk / .3); hl = r.get("hl")
        if hl: d.rectangle([0, y - 6, PW, y + 112], fill=(255, 244, 200))
        d.ellipse([18, y + 12, 32, y + 26], fill=BLUE if r.get("unread", True) else WHITE)
        d.text((44, y), r.get("from", ""), font=F(SANS, 22), fill=(14, 14, 20)); d.text((PW - 20, y + 2), r.get("when", ""), font=F(SANS, 17), fill=(130, 130, 140), anchor="ra")
        d.text((44, y + 32), r.get("subject", "")[:30], font=F(SANS, 20), fill=(30, 30, 36))
        d.text((44, y + 62), r.get("snippet", "")[:36], font=F(SANS, 18), fill=(130, 130, 140)); d.line([(44, y + 104), (PW, y + 104)], fill=(230, 230, 234))
        if a < 1: d.rectangle([0, y - 6, PW * (1 - a), y + 104], fill=WHITE)
        y += 118
    return sc

def screen_live(s, t):
    sc = Image.new("RGB", (PW, PH), (16, 16, 20)); d = ImageDraw.Draw(sc); status_bar(d, False)
    d.rectangle([0, 60, PW, 330], fill=(40, 30, 70))
    for k in range(6):   # stage lights sweeping (no person drawn)
        a = math.sin(t * 1.3 + k) * .5 + .5; d.polygon([(40 + k * 72, 60), (20 + k * 72 + 40 * a, 330), (70 + k * 72 + 40 * a, 330)], fill=(90 + 30 * k % 80, 60, 140))
    d.text((PW / 2, 200), s.get("banner", "GET IN EARLY"), font=F(ANTON, 54), fill=YEL, anchor="mm")
    d.rounded_rectangle([16, 74, 86, 104], 6, fill=(230, 40, 40)); d.text((51, 89), "LIVE", font=F(SANS, 18), fill=WHITE, anchor="mm")
    viewers = int(s.get("viewers", 0) * (1 + .02 * t)) if s.get("viewers") else 0
    if viewers: d.rounded_rectangle([96, 74, 210, 104], 6, fill=(0, 0, 0)); icon(d, "eye", 114, 89, 20, WHITE); d.text((132, 89), f"{viewers:,}", font=F(SANS, 18), fill=WHITE, anchor="lm")
    d.text((20, 346), s.get("title", "Live webinar"), font=F(SANS, 22), fill=WHITE); d.line([(0, 384), (PW, 384)], fill=(50, 50, 60))
    msgs = s.get("messages", []); step = s.get("step", .5); n = min(len(msgs), max(0, int((t - s.get("first", .3)) / step) + 1)); f = F(SANS, 19)
    y = PH - 120
    for m in reversed(msgs[:n][-9:]):
        d.text((20, y), m.get("from", "user") + ":", font=F(SANS, 19), fill=(140, 200, 255)); w0 = d.textlength(m.get("from", "user") + ": ", font=F(SANS, 19))
        d.text((20 + w0, y), m["text"][:28], font=f, fill=WHITE); y -= 52
    d.rounded_rectangle([16, PH - 70, PW - 16, PH - 24], 22, fill=(36, 36, 44)); d.text((36, PH - 58), "Say something...", font=F(SANS, 18), fill=(120, 120, 130))
    return sc

APPS = {"sms": screen_sms, "group": screen_group, "whatsapp": screen_group, "notify": screen_notify, "bank": screen_bank, "ticker": screen_ticker, "inbox": screen_inbox, "live": screen_live}

def s_phone(s, t, d, part):
    global _PF
    th = theme(part); fr = board(part); _PF = _PF or phone_frame()
    sc = APPS.get(s.get("app", "sms"), screen_sms)(s, t)
    ph = _PF.copy(); m = Image.new("L", (PW, PH), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, PW - 1, PH - 1], 48, fill=255)
    ph.paste(sc, (18, 18), m)
    e = back(min(1, t / .55)); cx = W * s.get("x", .5); cy = H * .5 + (1 - e) * 500
    buzz = 0
    for k in range(len(s.get("notes", [])) if s.get("app") == "notify" else 0):
        tk = t - s.get("first", .5) - k * s.get("step", .9)
        if 0 <= tk < .3: buzz = 6 * math.sin(tk * 90)
    rot = s.get("rot", -3) + .6 * math.sin(t * 1.1) + buzz * .3
    ph = ph.resize((int(ph.size[0] * .98), int(ph.size[1] * .98)), Image.LANCZOS).rotate(rot, expand=True, resample=Image.BICUBIC)
    if th["dark"]: fr = glow(fr, int(cx), int(cy), 520, (120, 150, 220), .10)
    shadow_paste(fr, ph, cx - ph.size[0] / 2 + buzz, cy - ph.size[1] / 2, 26, (24, 30), .55)
    dr = ImageDraw.Draw(fr)
    if s.get("label"): pop_sticker(fr, s["label"].upper(), int(W * (.2 if s.get("x", .5) >= .5 else .8)), int(H * .2), t - .5)
    if s.get("side"):   # a short line of kinetic text beside the phone
        sx = W * (.25 if s.get("x", .5) >= .5 else .75); f = F(ANTON, 76)
        for j, ln in enumerate(wrap(dr, s["side"].upper(), f, 640)[:3]):
            a = eout((t - .8 - j * .25) / .35)
            if a > 0: dr.text((sx, 420 + j * 92 + 20 * (1 - a)), ln, font=f, fill=th["ink"], anchor="mm")
    source_line(dr, s.get("source", ""), th, s.get("recreated", True) and bool(s.get("source")))
    return fr

# ---------------- photo layouts ----------------
def s_photos(s, t, d, part, media, credit_of):
    """pair, trio, wall (collage), polaroids (stack), split (two halves with labels)."""
    th = theme(part); fr = board(part); typ = s["type"]; ph = s.get("photos", []); n = len(ph); step = s.get("step", .45)
    u = ease(t / max(d, .1)); dr = ImageDraw.Draw(fr)
    if typ == "split":
        for k, p in enumerate(ph[:2]):
            img = media(p); x0 = k * W // 2
            pic = C.treat(img, p.get("mood", "archive"), key=("split", p.get("file", p.get("q")), p.get("mood")))
            r = max(W / 2 / pic.size[0], H / pic.size[1]); pz = pic.resize((int(pic.size[0] * r * (1.04 + .04 * u)), int(pic.size[1] * r * (1.04 + .04 * u))), Image.LANCZOS)
            a = eout((t - k * step) / .5)
            if a <= 0: continue
            cx = (pz.size[0] - W // 2) // 2; cy = (pz.size[1] - H) // 2
            crop = pz.crop((cx, cy, cx + W // 2, cy + H)); fr.paste(crop, (x0 + int((1 - a) * (-200 if k == 0 else 200)), 0))
            if p.get("label") and t > k * step + .4: pop_sticker(fr, p["label"].upper(), x0 + W // 4, 120, t - k * step - .4)
        dr = ImageDraw.Draw(fr); dr.rectangle([W // 2 - 5, 0, W // 2 + 5, H], fill=th["ink"] if not th["dark"] else CREAM)
        if s.get("vs", True) and t > .6: pop_sticker(fr, "VS", W // 2, H // 2 - 40, t - .6, F(ANTON, 70), RED, WHITE, 0)
    else:
        lay = {"pair": [(.3, .44, -3), (.7, .46, 3)], "trio": [(.2, .45, -4), (.5, .4, 2), (.8, .47, -2)],
               "wall": [(.22, .3, -5), (.5, .26, 3), (.78, .32, -2), (.3, .62, 4), (.62, .6, -3), (.86, .64, 5)],
               "polaroids": [(.42, .46, -9), (.5, .44, 4), (.58, .47, -3), (.5, .45, 8)]}[typ]
        wd = {"pair": 760, "trio": 560, "wall": 470, "polaroids": 620}[typ]
        for k, p in enumerate(ph[:len(lay)]):
            img = media(p); x, y, rot = lay[k]; key = p.get("file") or p.get("q")
            card = polaroid(img, wd, p.get("mood", "archive"), key, p.get("caption", "")) if typ == "polaroids" else sticker_photo(img, wd, p.get("mood", "archive"), key)
            place(fr, card, W * x, H * y, rot, t, k * step, 1 if k % 2 else -1, 1 + .03 * u)
            if p.get("label") and typ != "polaroids": pop_sticker(fr, p["label"].upper(), int(W * x), int(H * y + card.size[1] * .5 - 6), t - k * step - .5, F(ANTON, 38))
        dr = ImageDraw.Draw(fr)
        if s.get("circle") is not None and t > n * step + .2:   # marker circle on one card
            x, y, _ = lay[s["circle"]]; C.marker_circle(dr, [W * x - wd * .4, H * y - wd * .3, W * x + wd * .4, H * y + wd * .3], (t - n * step - .2) / .5)
    if s.get("title"): pop_sticker(fr, s["title"].upper(), 360, 80, t - .2, F(ANTON, 46), YEL, INK, -2)
    creds = [c for c in (credit_of(p) for p in ph) if c]
    if creds: dr = ImageDraw.Draw(fr); dr.text((W - 40, 1040), " · ".join(creds)[:180], font=F(MONO, 15), fill=th["sub"], anchor="rm")
    return zoom(fr, 1 + .025 * u)

def s_magnify(s, t, d, part, media, credit_of):
    """one photo as a stage, a loupe glides to the detail (x,y in 0-1 of the photo) and magnifies it."""
    th = theme(part); fr = board(part); img = media(s); key = s.get("file") or s.get("q"); u = ease(t / max(d, .1))
    card = sticker_photo(img, 1180, s.get("mood", "archive"), key); cx, cy = W * .5, H * .44
    place(fr, card, cx, cy, -1.5, t, 0, -1)
    if t > .6:
        tx, ty = s.get("detail", [.6, .4]); px0, py0 = cx - card.size[0] / 2, cy - card.size[1] / 2
        e = ease((t - .6) / 1.4); lx = px0 + card.size[0] * (.15 + (tx - .15) * e); ly = py0 + card.size[1] * (.8 + (ty - .8) * e)
        r = 150; z = s.get("zoom", 2.2); big = card.resize((int(card.size[0] * z), int(card.size[1] * z)), Image.LANCZOS)
        bx, by = (lx - px0) * z - r, (ly - py0) * z - r; lens = big.crop((int(bx), int(by), int(bx) + 2 * r, int(by) + 2 * r)).convert("RGB")
        m = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(m).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
        dr = ImageDraw.Draw(fr); dr.line([(lx + r * .7, ly + r * .7), (lx + r * 1.5, ly + r * 1.5)], fill=(40, 34, 30), width=26)
        fr.paste(lens, (int(lx - r), int(ly - r)), m); dr.ellipse([lx - r, ly - r, lx + r, ly + r], outline=(40, 34, 30), width=14)
        if s.get("label") and t > 2.0: pop_sticker(fr, s["label"].upper(), int(lx + r + 160), int(ly - r), t - 2.0)
    c = credit_of(s)
    if c: ImageDraw.Draw(fr).text((W - 40, 1040), c[:120], font=F(MONO, 15), fill=th["sub"], anchor="rm")
    return zoom(fr, 1 + .02 * u)

# ---------------- maps ----------------
_MAPS = None; _mapcache = {}
def _countries():
    global _MAPS
    if _MAPS is None: _MAPS = json.load(open(os.path.join(VEC, "maps", "europe_50m.json")))["countries"]
    return _MAPS
def _proj(bbox, size):
    lon0, lat0, lon1, lat1 = bbox; k = math.cos(math.radians((lat0 + lat1) / 2)); w, h = size
    sx = w / ((lon1 - lon0) * k); sy = h / (lat1 - lat0); sc = max(sx, sy)
    cxl, cyl = (lon0 + lon1) / 2, (lat0 + lat1) / 2
    return lambda lon, lat: (w / 2 + (lon - cxl) * k * sc, h / 2 - (lat - cyl) * sc)
def map_base(bbox, hl, part):
    key = (tuple(bbox), tuple(hl), part)
    if key in _mapcache: return _mapcache[key]
    S = 1.3; w, h = int(W * S), int(H * S); P = _proj(bbox, (w, h)); th = theme(part)
    sea = (183, 205, 214) if not th["name"] == "sky" else (205, 222, 230)
    im = C._paper(sea, 10, (w, h)); d = ImageDraw.Draw(im)
    for x in range(0, w, 104): d.line([(x, 0), (x, h)], fill=tuple(max(0, c - 14) for c in sea))
    for y in range(0, h, 104): d.line([(0, y), (w, y)], fill=tuple(max(0, c - 14) for c in sea))
    land = (238, 229, 208)
    for c in _countries():
        for poly in c["polys"]:
            pts = [P(a, b) for a, b in poly]
            if len(pts) > 2: d.polygon(pts, fill=YEL if c["iso"] in hl else land, outline=(120, 112, 98))
    for c in _countries():
        if c["iso"] in hl:
            for poly in c["polys"]:
                pts = [P(a, b) for a, b in poly]
                if len(pts) > 2: d.line(pts + [pts[0]], fill=RED, width=5, joint="curve")
    tex = C.CREAMTEX.resize((w, h)).convert("L").point(lambda v: 128 + (v - 128) // 2)
    im = ImageChops.overlay(im, Image.merge("RGB", [tex] * 3)); _mapcache[key] = (im, P, S); return _mapcache[key]

def s_map(s, t, d, part):
    th = theme(part); bbox = s.get("bbox", [12, 34, 32, 46]); hl = s.get("highlight", [])
    base, P, S = map_base(bbox, hl, part); u = ease(t / max(d, .1))
    pins = s.get("pins", []); route = s.get("route") or ([[pins[0]["lat"], pins[0]["lon"]], [pins[-1]["lat"], pins[-1]["lon"]]] if s.get("flight") and len(pins) > 1 else [])
    fx, fy = s.get("focus", [.5, .5]); z = 1.0 + .12 * u
    cw, ch = int(base.size[0] / z / S), int(base.size[1] / z / S)
    cx = base.size[0] * (0.5 + (fx - .5) * u * .4); cy = base.size[1] * (0.5 + (fy - .5) * u * .4)
    box = (int(cx - cw / 2), int(cy - ch / 2), int(cx - cw / 2) + cw, int(cy - ch / 2) + ch)
    fr = base.crop(box).resize((W, H), Image.BILINEAR); dr = ImageDraw.Draw(fr)
    def scr(lat, lon):
        x, y = P(lon, lat); return ((x - box[0]) * W / cw, (y - box[1]) * H / ch)
    if len(route) > 1:
        a, b = scr(*route[0]), scr(*route[-1]); mx, my = (a[0] + b[0]) / 2 + (b[1] - a[1]) * .25, (a[1] + b[1]) / 2 - abs(b[0] - a[0]) * .35 - 120
        r0 = s.get("route_at", .5); ur = ease((t - r0) / s.get("route_s", 2.2)); n = 60; m = int(n * ur); pts = []
        for k in range(m + 1):
            q = k / n; pts.append(((1 - q) ** 2 * a[0] + 2 * (1 - q) * q * mx + q * q * b[0], (1 - q) ** 2 * a[1] + 2 * (1 - q) * q * my + q * q * b[1]))
        for k in range(0, len(pts) - 1, 2): dr.line([pts[k], pts[k + 1]], fill=RED, width=8)
        if s.get("flight") and len(pts) > 2:
            (x1, y1), (x0, y0) = pts[-1], pts[-2]; ang = -math.degrees(math.atan2(y1 - y0, x1 - x0))
            pl = Image.new("RGBA", (120, 120), (0, 0, 0, 0)); icon(ImageDraw.Draw(pl), "plane", 60, 60, 84, INK)
            pl = pl.rotate(ang - 0, resample=Image.BICUBIC); fr.paste(pl, (int(x1 - 60), int(y1 - 60)), pl); dr = ImageDraw.Draw(fr)
    for k, p in enumerate(pins):
        tp = t - p.get("t", .2 + k * (s.get("route_s", 2.2) if route else .6))
        if tp < 0: continue
        x, y = scr(p["lat"], p["lon"]); e = back(min(1, tp / .3)); r = 16 * e
        dr.ellipse([x - r - 7, y - r - 7, x + r + 7, y + r + 7], fill=WHITE); dr.ellipse([x - r, y - r, x + r, y + r], fill=RED)
        if tp < 1.2: dr.ellipse([x - 20 - 60 * tp, y - 20 - 60 * tp, x + 20 + 60 * tp, y + 20 + 60 * tp], outline=RED, width=max(1, int(6 * (1 - tp / 1.2))))
        if p.get("name"): pop_sticker(fr, p["name"].upper(), int(x + p.get("dx", 0)), int(y - 70 + p.get("dy", 0)), tp - .1, F(ANTON, 42), INK, CREAM, -2); dr = ImageDraw.Draw(fr)
    if s.get("label"): pop_sticker(fr, s["label"].upper(), 380, 90, t - .3, F(ANTON, 48))
    if s.get("source"): dr.text((W - 40, 1040), "MAP: NATURAL EARTH (PUBLIC DOMAIN) · " + s["source"].upper(), font=F(MONO, 16), fill=(70, 70, 70), anchor="rm")
    else: dr.text((W - 40, 1040), "MAP: NATURAL EARTH (PUBLIC DOMAIN)", font=F(MONO, 16), fill=(70, 70, 70), anchor="rm")
    return fr

# ---------------- money flow ----------------
def s_money(s, t, d, part):
    th = theme(part); fr = board(part); dr = ImageDraw.Draw(fr); nodes = s.get("nodes", []); n = max(1, len(nodes))
    pos = [(W * nd.get("x", (k + .5) / n), H * nd.get("y", .45)) for k, nd in enumerate(nodes)]
    for k, (nd, (x, y)) in enumerate(zip(nodes, pos)):
        a = back(min(1, max(0, t - k * .35) / .4))
        if a <= 0: continue
        bw, bh = 300 * a, 230 * a; card = Image.new("RGBA", (max(2, int(bw)), max(2, int(bh))), CREAM + (255,)); cd = ImageDraw.Draw(card)
        cd.rectangle([0, 0, card.size[0] - 1, 10], fill=(nd.get("color") and tuple(nd["color"])) or RED)
        icon(cd, nd.get("icon", "user"), card.size[0] / 2, card.size[1] * .42, 96 * a, INK)
        if a > .8: cd.text((card.size[0] / 2, card.size[1] * .82), nd.get("label", "").upper(), font=F(ANTON, 36), fill=INK, anchor="mm")
        card = card.rotate(nd.get("rot", (-2 if k % 2 else 2)), expand=True, resample=Image.BICUBIC); shadow_paste(fr, card, x - card.size[0] / 2, y - card.size[1] / 2, 12, (8, 12), .45)
    dr = ImageDraw.Draw(fr)
    for j, fl in enumerate(s.get("flows", [])):
        a_, b_ = pos[fl["from"]], pos[fl["to"]]; t0 = .5 + j * .5; u = ease((t - t0) / .6)
        if u <= 0: continue
        dx = 170 if b_[0] > a_[0] else -170; p0 = (a_[0] + dx, a_[1]); p1 = (b_[0] - dx, b_[1])
        if abs(b_[0] - a_[0]) < 50: p0, p1 = (a_[0], a_[1] + 130), (b_[0], b_[1] - 130)
        arrow(dr, p0, p1, u, th["acc"] if th["dark"] else RED, 8, fl.get("bend", .12))
        if u >= 1:     # coins travel along the arrow, continuously
            for c in range(3):
                q = ((t - t0 - .6) * .55 + c / 3) % 1; mx, my = (p0[0] + p1[0]) / 2 - (p1[1] - p0[1]) * fl.get("bend", .12), (p0[1] + p1[1]) / 2 + (p1[0] - p0[0]) * fl.get("bend", .12)
                x = (1 - q) ** 2 * p0[0] + 2 * (1 - q) * q * mx + q * q * p1[0]; y = (1 - q) ** 2 * p0[1] + 2 * (1 - q) * q * my + q * q * p1[1]
                dr.ellipse([x - 22, y - 22, x + 22, y + 22], fill=YEL, outline=(170, 120, 20), width=4); dr.text((x, y), "$", font=F(ANTON, 28), fill=(140, 96, 10), anchor="mm")
            if fl.get("label"):
                lx, ly = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - 120; pop_sticker(fr, fl["label"].upper(), int(lx), int(ly), t - t0 - .6, F(ANTON, 40)); dr = ImageDraw.Draw(fr)
    if s.get("counter"):
        c = s["counter"]; v = float(c.get("value", 0)) * eout((t - c.get("t", .8)) / 1.6); dec = c.get("decimals", 0)
        txt = c.get("prefix", "") + f"{v:,.{dec}f}" + c.get("suffix", "")
        dr.text((W / 2, 800), txt, font=F(ANTON, 120), fill=th["acc"], anchor="mm"); dr.text((W / 2, 882), c.get("label", "").upper(), font=F(MONO, 30), fill=th["sub"], anchor="mm")
    if s.get("title"): pop_sticker(fr, s["title"].upper(), 380, 90, t - .1, F(ANTON, 48))
    source_line(dr, s.get("source", ""), th) if not s.get("counter") else dr.text((W / 2, 1040), ("SOURCE: " + s.get("source", "")).upper(), font=F(MONO, 20), fill=th["sub"], anchor="mm")
    return zoom(fr, 1 + .02 * ease(t / max(d, .1)))

# ---------------- stamp, scrubber, bar race ----------------
def s_stamp(s, t, d, part, under=None):
    th = theme(part); fr = under.copy() if under is not None else board(part)
    if under is not None: fr = Image.blend(fr, Image.new("RGB", (W, H), (0, 0, 0)), .35)
    dr = ImageDraw.Draw(fr)
    if s.get("pre"): dr.text((W / 2, 300), s["pre"].upper(), font=F(ANTON, 70), fill=th["ink"] if under is None else CREAM, anchor="mm")
    st = stamp_img(s.get("text", "FRAUD").upper(), tuple(s.get("color", RED)), s.get("size", 170), s.get("sub", ""))
    tt = t - s.get("at_s", .3)
    if tt > 0:
        sc = 1.9 - .9 * min(1, tt / .16) if tt < .16 else 1.0 + .03 * math.exp(-tt * 8) * math.sin(tt * 40)
        im = st.resize((int(st.size[0] * sc), int(st.size[1] * sc)), Image.BILINEAR).rotate(s.get("rot", -8), expand=True, resample=Image.BICUBIC)
        fr.paste(im, (int(W / 2 - im.size[0] / 2), int(H * .52 - im.size[1] / 2)), im)
    if t > .8 and s.get("source"): source_line(ImageDraw.Draw(fr), s["source"], th)
    shake = 9 * math.exp(-max(0, tt) * 14) if 0 < tt < .4 else 0
    return zoom(fr, 1.01 + .01 * ease(t / max(d, .1)), .5 + shake / W, .5)

def s_scrub(s, t, d, part):
    th = theme(part); fr = board(part); dr = ImageDraw.Draw(fr); ev = s.get("events", [])
    y0 = 560; x0, x1 = 160, 1760; years = [e["year"] for e in ev] or [2014, 2017]; ya, yb = s.get("from", min(years)), s.get("to", max(years))
    X = lambda yv: x0 + (x1 - x0) * (yv - ya) / max(1e-6, yb - ya)
    dr.line([(x0, y0), (x1, y0)], fill=th["sub"], width=6)
    for yv in range(int(ya), int(yb) + 1):
        dr.line([(X(yv), y0 - 14), (X(yv), y0 + 14)], fill=th["sub"], width=4); dr.text((X(yv), y0 + 44), str(yv), font=F(MONO, 30), fill=th["sub"], anchor="mm")
    hp = ya + (yb - ya) * ease(t / max(.5, d * s.get("speed", .8)))
    dr.line([(x0, y0), (X(hp), y0)], fill=th["acc"], width=10)
    for k, e in enumerate(ev):
        if hp < e["year"]: continue
        x = X(e["year"]); up = k % 2 == 0; a = eout((hp - e["year"]) / max(.1, (yb - ya) * .08))
        dr.ellipse([x - 16, y0 - 16, x + 16, y0 + 16], fill=RED)
        yy = y0 - 170 if up else y0 + 110; dr.line([(x, y0), (x, yy + (60 if up else 0))], fill=th["sub"], width=3)
        f = F(ANTON, 40)
        for j, ln in enumerate(wrap(dr, e["label"].upper(), f, 360)[:2]): dr.text((x, yy + j * 46 + 20 * (1 - a)), ln, font=f, fill=th["ink"], anchor="mm")
    dr.polygon([(X(hp) - 16, y0 - 50), (X(hp) + 16, y0 - 50), (X(hp), y0 - 22)], fill=th["acc"])
    if s.get("title"): pop_sticker(fr, s["title"].upper(), 380, 120, t - .1, F(ANTON, 48))
    if s.get("source"): dr = ImageDraw.Draw(fr); dr.text((W / 2, 1040), ("SOURCE: " + s["source"]).upper(), font=F(MONO, 20), fill=th["sub"], anchor="mm")
    return fr

def s_barrace(s, t, d, part):
    """items: [{label, values:[...per step]}], steps: labels. Bars grow and re-order step by step."""
    th = theme(part); fr = board(part); dr = ImageDraw.Draw(fr); it = s.get("items", []); steps = s.get("steps", ["", ""])
    ns = len(steps); u = min(ns - 1, max(0.0, t / max(.5, d - .6)) * (ns - 1)); k = int(u); f = u - k
    vals = [(i["values"][k] + (i["values"][min(k + 1, ns - 1)] - i["values"][k]) * ease(f)) for i in it]
    mx = max(vals + [1e-9]); order = sorted(range(len(it)), key=lambda j: -vals[j])
    for rank, j in enumerate(order):
        y = 220 + rank * 120; w_ = 1100 * vals[j] / mx
        dr.rectangle([520, y, 520 + w_, y + 84], fill=tuple(it[j].get("color", th["acc"])))
        dr.text((500, y + 42), it[j]["label"].upper(), font=F(ANTON, 44), fill=th["ink"], anchor="rm")
        dr.text((530 + w_, y + 42), s.get("prefix", "") + f"{vals[j]:,.{s.get('decimals', 0)}f}" + s.get("suffix", ""), font=F(ANTON, 44), fill=th["ink"], anchor="lm")
    dr.text((W - 120, 860), str(steps[min(ns - 1, int(round(u)))]), font=F(ANTON, 110), fill=th["sub"], anchor="rm")
    if s.get("title"): pop_sticker(fr, s["title"].upper(), 380, 110, t - .1, F(ANTON, 48))
    if s.get("source"): dr = ImageDraw.Draw(fr); dr.text((W / 2, 1040), ("SOURCE: " + s["source"]).upper(), font=F(MONO, 20), fill=th["sub"], anchor="mm")
    return fr

# ---------------- surround motion for a lone picture: drifting tape bits, marks ----------------
def marks(fr, s, t, part):
    """operator marks drawn over any shot: [{"k":"circle|arrow|underline|sticker", ..., "t": seconds}]"""
    dr = ImageDraw.Draw(fr); th = theme(part)
    for k, m in enumerate(s.get("marks", [])):
        tt = t - m.get("t", .9 + k * .8)
        if tt <= 0: continue
        kind = m.get("k", "circle")
        if kind == "circle": C.marker_circle(dr, [m["x0"] * W, m["y0"] * H, m["x1"] * W, m["y1"] * H], tt / .5, RED, 8)
        elif kind == "arrow": arrow(dr, (m["x0"] * W, m["y0"] * H), (m["x1"] * W, m["y1"] * H), tt / .45, RED, 9)
        elif kind == "underline": underline(dr, m["x0"] * W, m["x1"] * W, m["y"] * H, tt / .4, RED, 9)
        elif kind == "sticker": pop_sticker(fr, m.get("text", "").upper(), int(m["x"] * W), int(m["y"] * H), tt, F(ANTON, m.get("size", 44)), tuple(m.get("bg", YEL)), INK, m.get("rot", -4)); dr = ImageDraw.Draw(fr)
        elif kind == "emoji":
            em = emoji(m["code"], m.get("size", 140))
            if em: e = back(min(1, tt / .3)); im = em.resize((max(1, int(em.size[0] * e)), max(1, int(em.size[1] * e)))); shadow_paste(fr, im, m["x"] * W - im.size[0] / 2, m["y"] * H - im.size[1] / 2, 8, (4, 6), .3)
    return fr
