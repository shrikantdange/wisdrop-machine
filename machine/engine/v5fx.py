"""Wisdrop v5 look (CPU, code-drawn, seeded): depth layers, evidence-wall glide, keyword captions,
and 11 new templates (docs/SHOTS.md T29-T39). Every random thing = crc32 seed (AMC-W1).
Every drawer: (s, t, d, part) -> 1920x1080 RGB. All words on screen are drawn here by code.
People are only ever faceless code silhouettes (fictional); never a real face.
"""
import math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
from edhelpers import F, ANTON, MONO, SANS, SERIF, ease, eout, back, glow, zoom
import v3kit as V
import motion as MO

W, H = 1920, 1080
INK, CREAM, YEL, RED, WHITE = V.INK, V.CREAM, V.YEL, V.RED, V.WHITE
_C = {}
def cached(k, fn):
    if k not in _C: _C[k] = fn()
    return _C[k]
def R(*p): return MO.rng("v5", *p)
def on2(t): return MO.on_twos(t)

# ---------------- maths helpers ----------------
def persp_coeffs(dst, src):
    """PIL PERSPECTIVE coeffs mapping output points dst -> input points src (4 pairs)."""
    A, B = [], []
    for (x, y), (X, Y) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -X * x, -X * y]); B.append(X)
        A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y]); B.append(Y)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()
def homog(c): return np.array([[c[0], c[1], c[2]], [c[3], c[4], c[5]], [c[6], c[7], 1.0]])
def apply_h(M, x, y):
    v = M @ np.array([x, y, 1.0]); return v[0] / v[2], v[1] / v[2]
def quad(p0, c, p1, q):
    return ((1 - q) ** 2 * p0[0] + 2 * (1 - q) * q * c[0] + q * q * p1[0], (1 - q) ** 2 * p0[1] + 2 * (1 - q) * q * c[1] + q * q * p1[1])
def noise(key, w, h, octaves=4, base=6):
    """seeded fractal value noise 0-1, shape (h, w)"""
    def mk():
        acc = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
        for o in range(octaves):
            g = R("noise", key, o).random((base * 2 ** o + 1, int(base * 2 ** o * w / h) + 1)).astype(np.float32)
            im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
            acc += np.asarray(im, np.float32) / 255 * amp; tot += amp; amp *= .5
        return acc / tot
    return cached(("noise", key, w, h, octaves, base), mk)

# ---------------- 1. depth layers ----------------
def archive(part):
    """board + blurred archive layer (faint papers, photo blocks, text bars) = the far depth layer."""
    def mk():
        k = part % len(V.THEMES); th = V.THEMES[k]; base = V._make_board(th)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); r = R("arch", k)
        for j in range(26):
            w = int(r.uniform(220, 520)); h = int(w * r.uniform(1.15, 1.45))
            sh = Image.new("RGBA", (w, h), (236, 228, 210, int(r.uniform(85, 150)))); d = ImageDraw.Draw(sh)
            y = 30
            if r.random() < .4: d.rectangle([24, 24, w - 24, int(h * .42)], fill=(70, 68, 66, 150)); y = int(h * .48)
            while y < h - 30:
                d.rectangle([24, y, 24 + int((w - 48) * r.uniform(.5, 1)), y + 9], fill=(110, 104, 96, 120)); y += 22
            sh = sh.rotate(r.uniform(-16, 16), expand=True, resample=Image.BICUBIC)
            lay.paste(sh, (int(r.uniform(-160, W - 100)), int(r.uniform(-180, H - 140))), sh)
        lay = lay.filter(ImageFilter.GaussianBlur(5))
        out = base.copy(); out.paste(lay, (0, 0), lay)
        return Image.blend(out, base, .22 if th["dark"] else .4)
    return cached(("arch", part % len(V.THEMES)), mk).copy()

def floaters(fr, key, t, n=12, light=(240, 232, 214)):
    """near depth layer: drifting out-of-focus paper scraps, dust, tape bits (seeded, smooth motion)."""
    r = R("float", key); ov = Image.new("RGBA", (W // 2, H // 2), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for k in range(n):
        x0, y0 = r.uniform(0, W), r.uniform(0, H); vx, vy = r.uniform(-16, 16), r.uniform(-26, -8)
        sz = r.uniform(14, 40); ph = r.uniform(0, 6.3); spin = r.uniform(.2, .8); kind = r.random()
        if k < n // 3 and not (x0 < W * .22 or x0 > W * .78): x0 = (x0 * .22) if x0 < W / 2 else W - (W - x0) * .22   # big scraps keep to the edges
        x = ((x0 + vx * t) % (W + 200) - 100) / 2; y = ((y0 + vy * t) % (H + 200) - 100) / 2; a = ph + t * spin; s2 = sz / 2
        if kind < .5:
            pts = [(x + s2 * math.cos(a + q) * (1 + .3 * (j % 2)), y + s2 * .7 * math.sin(a + q)) for j, q in enumerate((0, 1.7, 3.3, 4.6))]
            d.polygon(pts, fill=light + (95,))
        elif kind < .85:
            rr = 1 + sz / 30; d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 238, 205, 110))
        else:
            ca, sa = math.cos(a * .3), math.sin(a * .3)
            d.polygon([(x - s2 * ca, y - s2 * sa), (x + s2 * ca, y + s2 * sa), (x + s2 * ca - 6 * sa, y + s2 * sa + 6 * ca), (x - s2 * ca - 6 * sa, y - s2 * sa + 6 * ca)], fill=(236, 226, 190, 90))
    ov = ov.filter(ImageFilter.GaussianBlur(1.3)).resize((W, H), Image.BILINEAR)
    fr.paste(ov, (0, 0), ov); return fr

def breathe(fr, t, x=W * .5, y=H * .35, r=700, col=(255, 214, 150), a=.07):
    return glow(fr, int(x), int(y), int(r), col, a + .025 * math.sin(t * 1.7))

def tilt(img, k=.045, side=1):
    """slight 3D tilt of a paper/RGBA card (one vertical edge recedes)."""
    w, h = img.size; dy = h * k
    dst = [(0, 0), (w, dy), (w, h - dy), (0, h)] if side > 0 else [(0, dy), (w, 0), (w, h), (0, h - dy)]
    return img.transform((w, h), Image.PERSPECTIVE, persp_coeffs(dst, [(0, 0), (w, 0), (w, h), (0, h)]), Image.BICUBIC)

def drop(fr, im, x, y, blur=18, off=(14, 22), a=.5):
    V.shadow_paste(fr, im, x, y, blur, off, a)

def tag(fr, text, x=44, y=40):
    d = ImageDraw.Draw(fr); f = F(MONO, 22); w = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + w + 32, y + 40], 6, fill=(0, 0, 0)); d.text((x + 16, y + 8), text, font=f, fill=CREAM); return fr

def credit(fr, text, col=(150, 145, 134)):
    if text: ImageDraw.Draw(fr).text((40, 1046), text.upper()[:150], font=F(MONO, 16), fill=col, anchor="lm")
    return fr

def silhouette(h, phase=0.0, walk=True, col=(12, 14, 20), arms_up=False):
    """faceless fictional figure seen from behind/front: no features, flat shape only."""
    w = int(h * .5); im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = col + (255,)
    cx = w / 2; hr = h * .075; d.ellipse([cx - hr, h * .02, cx + hr, h * .02 + hr * 2.2], fill=c)
    d.rectangle([cx - hr * .4, h * .15, cx + hr * .4, h * .2], fill=c)
    d.rounded_rectangle([cx - h * .115, h * .17, cx + h * .115, h * .3], int(h * .05), fill=c)                         # rounded shoulders
    d.polygon([(cx - h * .11, h * .22), (cx + h * .11, h * .22), (cx + h * .125, h * .42), (cx + h * .15, h * .6), (cx - h * .15, h * .6), (cx - h * .125, h * .42)], fill=c)   # coat, slight flare
    sw = math.sin(phase) * (h * .07 if walk else 0)
    for sgn in (-1, 1):
        x0 = cx + sgn * h * .055; x1 = x0 + sgn * 2 + sw * sgn
        d.polygon([(x0 - h * .045, h * .58), (x0 + h * .045, h * .58), (x1 + h * .035, h * .985), (x1 - h * .035, h * .985)], fill=c)
        if arms_up and sgn > 0: d.polygon([(cx + h * .1, h * .22), (cx + h * .15, h * .2), (cx + h * .2, h * .0), (cx + h * .16, h * .0)], fill=c)
        else:
            ax = cx + sgn * h * .15 - sw * sgn * .6
            d.polygon([(cx + sgn * h * .11, h * .22), (cx + sgn * h * .16, h * .23), (ax + sgn * h * .03, h * .55), (ax - sgn * h * .01, h * .55)], fill=c)
    return im

# ---------------- 2. evidence-wall glide ----------------
GLIDE = .7
def _slot(j):
    r = R("slot", j); row = j // 3; col = j % 3 if row % 2 == 0 else 2 - j % 3
    return col * 1.16 + r.uniform(-.05, .05), row * 1.16 + r.uniform(-.05, .05)
def wall_bg(part):
    def mk():
        big = Image.new("RGB", (W * 2, H * 2)); a = archive(part).resize((W, H))
        for x in (0, W):
            for y in (0, H): big.paste(a if (x + y) % (2 * W) == 0 else a.transpose(Image.FLIP_LEFT_RIGHT), (x, y))
        return ImageEnhance.Brightness(big).enhance(.72)
    return cached(("wall", part % 4), mk)
def glide(tiles, cur_j, prev_j, u, part):
    """tiles: [(img, j)] incl. prev + current; camera glides prev slot -> current slot,
    pulling back to show earlier facts pinned on one big wall. u in 0-1."""
    e = MO.ease("camera", u); z = 1 - .5 * math.sin(math.pi * e)
    (px, py), (cx, cy) = _slot(prev_j), _slot(cur_j); camx, camy = px + (cx - px) * e, py + (cy - py) * e
    bg = wall_bg(part); ox = int((camx * 300) % W); oy = int((camy * 300) % H)
    fr = bg.crop((ox, oy, ox + W, oy + H)); bw = int(16 * (1 - z) / .5)
    for img, j in tiles:
        sx, sy = _slot(j); x = W / 2 + (sx - camx) * W * z; y = H / 2 + (sy - camy) * H * z
        tw, th = int(W * z), int(H * z)
        if x + tw / 2 < -50 or x - tw / 2 > W + 50 or y + th / 2 < -50 or y - th / 2 > H + 50: continue
        tl = img.resize((tw, th), Image.BILINEAR).convert("RGBA")
        if bw > 0:
            card = Image.new("RGBA", (tw + 2 * bw, th + 2 * bw), CREAM + (255,)); card.paste(tl, (bw, bw)); tl = card
        drop(fr, tl, x - tl.size[0] / 2, y - tl.size[1] / 2, 20, (int(18 * (1 - z)), int(24 * (1 - z))), .55 * (1 - z) / .5)
        if bw > 0:
            d = ImageDraw.Draw(fr); px_, py_ = x, y - tl.size[1] / 2 + bw * .6; rr = max(6, bw)
            d.ellipse([px_ - rr, py_ - rr, px_ + rr, py_ + rr], fill=RED); d.ellipse([px_ - rr * .4, py_ - rr * .6, px_, py_ - rr * .2], fill=(255, 170, 160))
    return fr

# ---------------- 3. caption normaliser + keywords ----------------
UN = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split())}
TE = {w: 20 + 10 * i for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split())}
SC = {"hundred": 100, "thousand": 1e3, "million": 1e6, "billion": 1e9}
ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
       "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14, "fifteenth": 15, "sixteenth": 16, "seventeenth": 17,
       "eighteenth": 18, "nineteenth": 19, "twentieth": 20, "thirtieth": 30}
MON = {m: m[:3].upper() for m in "january february march april may june july august september october november december".split()}
STOP = set("""a an the and or but so of to in on at by for from with as is are was were be been being it its it's this that these those
there here then than they them their she her he him his you your we our i me my who what which when where how why do does did done
not no just also very really even still only more most much many some any all every one each into out up down over under about after
before again once while if because like can could would should will shall may might must has have had having get got gets going
said say says told tell s t own same such too both just now came come went go took take made make had least
more than over just against""".split())
def _clean(w): return re.sub(r"[^a-z0-9'\-.]", "", w.lower()).strip(".'")
def _wval(w):
    tot, o = 0, False
    for p in w.split("-"):
        if p in UN: tot += UN[p]
        elif p in TE: tot += TE[p]
        elif p in ORD: tot += ORD[p]; o = True
        else: return None
    return tot, o
def _isnum(w): return _wval(w) is not None or w in SC
def _compact(v):
    for m, s in ((1e9, "B"), (1e6, "M")):
        if v >= m: return f"{v / m:g}{s}"
    return f"{int(v):,}" if v == int(v) else f"{v:g}"
def _parse(run):
    tot, cur, half = 0.0, 0.0, False
    for w in run:
        if w in ("and", "a"): continue
        if w == "half": half = True; continue
        if w in SC:
            c = (cur or 1) + (.5 if half else 0); half = False
            if SC[w] == 100: cur = c * 100
            else: tot += c * SC[w]; cur = 0
        else: cur += _wval(w)[0]
    return tot + cur + (.5 if half else 0)

def normalize(words):
    """[(a, b, word)] -> [(a, b, token)]: numbers, money and dates as digits ('25 OCT 2017', '$4B', '3.5M', '€140')."""
    out, i, n = [], 0, len(words)
    cw = [_clean(w[2]) for w in words]
    while i < n:
        w = cw[i]; punct = words[i][2][-1] if words[i][2][-1:] in ",.?!:;" else ""
        # run of number words ('and'/'a'/'half' allowed inside)
        j = i; run = []
        while j < n and (_isnum(cw[j]) or (cw[j] in ("and", "a", "half") and run and j + 1 < n and (_isnum(cw[j + 1]) or cw[j + 1] in ("a", "half")))
                         or (cw[j] == "a" and not run and j + 1 < n and cw[j + 1] in SC)):
            run.append(cw[j]); j += 1
            if words[j - 1][2][-1:] in ",.?!:;": break
        nums = [x for x in run if x not in ("and", "a", "half")]
        if nums and not (len(nums) == 1 and nums[0] in ("one",) and not (j < n and cw[j] in ("dollars", "euros", "percent"))):
            last = words[j - 1]; punct = last[2][-1] if last[2][-1:] in ",.?!:;" else ""
            vals = [_wval(x) for x in nums if x not in SC]
            # year: 'twenty seventeen', 'twenty twenty-six', 'nineteen ninety'
            if len(nums) == 2 and nums[0] in ("twenty", "nineteen") and vals[1] and 10 <= vals[1][0] <= 99 and not vals[1][1]:
                tok = str((20 if nums[0] == "twenty" else 19) * 100 + vals[1][0])
            elif len(vals) == 1 and vals[0][1] and len(nums) == 1:
                tok = f"{vals[0][0]}#ORD"
            else:
                v = _parse(run); tok = None
                if j < n and cw[j] in ("dollars", "dollar"): tok = "$" + _compact(v); last = words[j]; punct = last[2][-1] if last[2][-1:] in ",.?!:;" else ""; j += 1
                elif j < n and cw[j] in ("euros", "euro"):
                    if j + 1 < n and cw[j + 1] == "cents": tok = f"€0.{int(v):02d}"; last = words[j + 1]; j += 2
                    else:
                        tok = "€" + _compact(v); last = words[j]; j += 1
                        k2 = j; r2 = []
                        while k2 < n and _wval(cw[k2]) and not _wval(cw[k2])[1]: r2.append(cw[k2]); k2 += 1
                        if r2 and _parse(r2) < 100: tok = f"€{int(v)}.{int(_parse(r2)):02d}"; last = words[k2 - 1]; j = k2
                    punct = last[2][-1] if last[2][-1:] in ",.?!:;" else ""
                elif j < n and cw[j] == "percent": tok = _compact(v) + "%"; last = words[j]; j += 1
                if tok is None: tok = _compact(v)
            out.append([words[i][0], last[1], tok + punct]); i = j; continue
        out.append([words[i][0], words[i][1], words[i][2]]); i += 1
    # dates: MONTH [day] [year] -> '25 OCT 2017'
    res, k = [], 0
    while k < len(out):
        w = _clean(out[k][2])
        if w in MON:
            parts = [MON[w]]; e = k; day = yr = None
            if k + 1 < len(out) and re.match(r"^\d+(#ORD)?[,.]?$", out[k + 1][2]) and int(re.match(r"\d+", out[k + 1][2]).group()) <= 31:
                day = re.match(r"\d+", out[k + 1][2]).group(); e = k + 1
            if e + 1 < len(out) and re.match(r"^\d{4}[,.?!]?$", out[e + 1][2]): yr = out[e + 1][2]; e += 1
            if day or yr:
                p = out[e][2][-1] if out[e][2][-1:] in ",.?!:;" else ""
                txt = " ".join(x for x in [day, MON[w], (yr or "").rstrip(",.?!:;")] if x) + p
                res.append([out[k][0], out[e][1], txt]); k = e + 1; continue
        res.append(out[k]); k += 1
    for r_ in res:
        if "#ORD" in r_[2]:
            m = re.match(r"(\d+)#ORD(.*)", r_[2]); v = int(m.group(1))
            r_[2] = {1: "first", 2: "second", 3: "third"}.get(v, f"{v}th") + m.group(2)
    return [tuple(x) for x in res]

def _key(w): return re.sub(r"[^A-Z0-9.]", "", w.upper().replace("€", "").replace("$", "")).strip(".")
def screen_words(s):
    """every word a shot shows on screen (to keep captions from repeating it)."""
    skip = {"type", "file", "q", "commons", "mood", "set", "time", "move", "k", "code", "trans", "n", "device", "focus", "amb", "src"}
    acc = []
    def walk(v, k=None):
        if k in skip: return
        if isinstance(v, str): acc.append(v)
        elif isinstance(v, dict): [walk(x, kk) for kk, x in v.items()]
        elif isinstance(v, (list, tuple)): [walk(x, k) for x in v]
        elif isinstance(v, (int, float)) and k in ("value",): acc.append(f"{v:g}")
    walk(s); out = set()
    for txt in acc:
        for w in re.split(r"[\s/·\-–—,:;!?()\"']+", txt):
            kk = _key(w)
            if kk: out.add(kk)
            m = re.match(r"^(\d+(?:\.\d+)?)([BMK])\+?$", kk)
            if m: out.add(m.group(1))
    return out

def keywords(chunk, scr, maxn=3):
    """chunk [(a,b,tok)] -> the few words worth showing: no stop words, nothing already on screen."""
    keep = []
    for a, b, w in chunk:
        parts = [_key(p) for p in w.split()]; parts = [p for p in parts if p]
        if not parts: continue
        lw = w.lower().strip(",.?!:;\"'")
        if lw in STOP or len(lw) < 3 and not any(c.isdigit() for c in lw): continue
        if all(p in scr for p in parts): continue
        if any(c.isdigit() for c in w) and any(p in scr or re.sub(r"[BMK]$", "", p) in scr for p in parts): continue
        keep.append((a, b, w.strip(",.;:\"")))
    if len(keep) > maxn:   # prefer numbers/capitalised/longer words, keep spoken order
        sc = sorted(range(len(keep)), key=lambda k: -(10 * any(c.isdigit() for c in keep[k][2]) + 3 * keep[k][2][:1].isupper() + len(keep[k][2])))[:maxn]
        keep = [keep[k] for k in sorted(sc)]
    return keep

# ---------------- 4. templates ----------------
FLAP = "ABCDEFGHIJKLMNOPRSTUVWXYZ0123456789-:"
def s_flapboard(s, t, d, part):
    """T29 split-flap departures board. rows: [[time, dest, status]], hl row index."""
    fr = ImageEnhance.Brightness(archive(part)).enhance(.45)
    for k in range(4): fr = glow(fr, 240 + k * 480, -40, 360, (255, 236, 200), .10)
    pw, ph = 1720, 720; x0, y0 = (W - pw) // 2, 110
    pan = Image.new("RGBA", (pw, ph), (16, 17, 20, 255)); pd = ImageDraw.Draw(pan)
    pd.rounded_rectangle([0, 0, pw - 1, ph - 1], 18, outline=(60, 62, 70), width=4)
    pd.rectangle([0, 0, pw, 110], fill=(26, 28, 34)); V.icon(pd, "plane-departure", 70, 56, 64, YEL)
    pd.text((120, 18), s.get("title", "DEPARTURES"), font=F(ANTON, 72), fill=YEL)
    pd.text((pw - 40, 32), s.get("from", "").upper(), font=F(ANTON, 54), fill=CREAM, anchor="ra")
    heads = [("TIME", 5), ("DESTINATION", 11), ("STATUS", 9)]; cwid, chh, gap = 50, 70, 6; cols_x = [40]
    for _, n in heads[:-1]: cols_x.append(cols_x[-1] + n * (cwid + gap) + 60)
    for (hd, _), cx in zip(heads, cols_x): pd.text((cx, 128), hd, font=F(MONO, 26), fill=(150, 150, 160))
    rows = s.get("rows", []); hl = s.get("hl", -1)
    for ri, row in enumerate(rows[:6]):
        ry = 172 + ri * (chh + 16)
        if ri == hl: pd.rounded_rectangle([20, ry - 8, pw - 20, ry + chh + 8], 8, fill=(60, 48, 16) if t > .25 + ri * .18 + .9 else (16, 17, 20))
        for ci, ((_, n), cx) in enumerate(zip(heads, cols_x)):
            txt = str(row[ci]).upper()[:n].ljust(n)
            for k, ch in enumerate(txt):
                x = cx + k * (cwid + gap); ts = .2 + ri * .16 + (ci * 5 + k) * .028
                pd.rounded_rectangle([x, ry, x + cwid, ry + chh], 5, fill=(34, 35, 40))
                if t < ts:
                    flips = int((ts - t) * 18); cc = FLAP[(MO.seed("flap", ri, ci, k) + flips) % len(FLAP)] if t > ts - .9 else " "
                else: cc = ch; flips = 0
                col = YEL if (ri == hl and ci == 2 and t >= ts) else CREAM
                if cc.strip(): pd.text((x + cwid / 2, ry + chh / 2 + 2), cc, font=F(MONO, 50), fill=col, anchor="mm")
                pd.line([(x, ry + chh / 2), (x + cwid, ry + chh / 2)], fill=(10, 10, 12), width=3)
                if t < ts and (t * 18) % 1 < .4: pd.rectangle([x, ry, x + cwid, ry + chh / 2], fill=(44, 45, 52))
    gl = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl); gx = -600 + (pw + 1200) * ((t * .35) % 1)
    gd.polygon([(gx, 0), (gx + 220, 0), (gx - 80, ph), (gx - 300, ph)], fill=(255, 255, 255, 18)); pan.alpha_composite(gl)
    pan = tilt(pan, .02, 1); drop(fr, pan, x0, y0 + 10 * (1 - eout(t / .5)), 26, (0, 26), .6)
    fr = floaters(fr, ("flap", s.get("at")), t, 10)
    tag(fr, s.get("tag", "ILLUSTRATION")); credit(fr, "SOURCE: " + s["source"] if s.get("source") else "")
    return zoom(fr, 1.0 + .03 * ease(t / max(d, .1)), .5, .45)

def _barcode(key, w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); r = R("bar", key); x = 0
    while x < w:
        bw = int(r.choice([2, 3, 5, 7]))
        if r.random() < .55: d.rectangle([x, 0, x + bw - 1, h], fill=INK + (255,))
        x += bw + int(r.choice([2, 3, 4]))
    return im
def s_boardingpass(s, t, d, part):
    """T30 boarding pass printing out of a slot; tilts onto the desk."""
    fr = archive(part); fr = breathe(fr, t, W * .5, 200, 800, (200, 220, 255), .06)
    pw, ph = 1240, 540
    def mk():
        p = Image.new("RGBA", (pw, ph), (247, 243, 232, 255)); d = ImageDraw.Draw(p)
        d.rectangle([0, 0, pw, 86], fill=(30, 52, 92)); d.text((40, 16), "BOARDING PASS", font=F(ANTON, 54), fill=CREAM)
        stub = pw - 330
        for y in range(0, ph, 18): d.line([(stub, y), (stub, y + 9)], fill=(150, 145, 134), width=3)
        d.text((40, 110), "FROM", font=F(MONO, 24), fill=(110, 104, 96)); d.text((420, 110), "TO", font=F(MONO, 24), fill=(110, 104, 96))
        d.text((40, 136), s.get("from", ""), font=F(ANTON, 150), fill=INK); d.text((420, 136), s.get("to", ""), font=F(ANTON, 150), fill=INK)
        V.icon(d, "plane", 345, 236, 80, (30, 52, 92))
        d.text((40, 360), s.get("from_city", "").upper(), font=F(MONO, 28), fill=(60, 58, 56)); d.text((420, 360), s.get("to_city", "").upper(), font=F(MONO, 28), fill=(60, 58, 56))
        for k, (lab, val) in enumerate(s.get("fields", [])):
            d.text((40 + k * 210, 418), lab.upper(), font=F(MONO, 22), fill=(110, 104, 96)); d.text((40 + k * 210, 446), val.upper(), font=F(ANTON, 50), fill=INK)
        d.text((stub + 30, 110), "PASSENGER", font=F(MONO, 22), fill=(110, 104, 96)); d.rectangle([stub + 30, 142, pw - 40, 186], fill=INK)
        d.text((stub + 30, 210), s.get("from", "") + "  >  " + s.get("to", ""), font=F(ANTON, 48), fill=INK)
        bc = _barcode(("bp", s.get("at")), 260, 150); p.paste(bc, (stub + 34, 330), bc)
        return p
    pas = cached(("bp", s.get("at"), s.get("from"), s.get("to"), str(s.get("fields"))), mk)
    pr = eout(min(1, max(0, (t - .15) / 1.5))); slot_y = 150
    # printer body
    d0 = ImageDraw.Draw(fr); px0 = (W - 1400) // 2
    d0.rounded_rectangle([px0, 40, px0 + 1400, slot_y + 10], 26, fill=(28, 30, 36)); d0.rectangle([px0 + 70, slot_y - 6, px0 + 1330, slot_y + 4], fill=(6, 6, 8))
    d0.ellipse([px0 + 1320, 70, px0 + 1350, 100], fill=(70, 220, 120) if (t * 2) % 1 < .6 or pr >= 1 else (30, 80, 50))
    vis = int(ph * pr)
    if vis > 4:
        part_ = pas.crop((0, ph - vis, pw, ph)) if pr < 1 else pas
        after = ease((t - 1.75) / .6)
        if after > 0: part_ = tilt(part_, .05 * after, 1).rotate(-3 * after, expand=True, resample=Image.BICUBIC)
        jitter = 0 if pr >= 1 else (MO.seed("bpj", int(t * 30)) % 3) - 1
        drop(fr, part_, (W - part_.size[0]) / 2 + jitter, slot_y + 4 + 160 * after, 22, (10 + 16 * after, 14 + 20 * after), .5)
    d0 = ImageDraw.Draw(fr); d0.rounded_rectangle([px0, 40, px0 + 1400, slot_y - 6], 26, fill=(34, 36, 44))
    d0.text((px0 + 60, 70), "PRINTING" if pr < 1 else "PRINTED", font=F(MONO, 34), fill=(150, 160, 175))
    fr = floaters(fr, ("bp", s.get("at")), t, 9)
    tag(fr, s.get("tag", "ILLUSTRATION"), 44, 980 - 60); credit(fr, "SOURCE: " + s["source"] if s.get("source") else "")
    return zoom(fr, 1.0 + .035 * ease(t / max(d, .1)), .5, .55)

def _fog_layer(k):
    def mk():
        n = noise(("fog", k), W, H // 2, 4, 3); a = np.clip((n - .35) * 2.2, 0, 1) * np.sin(np.linspace(0, np.pi, H // 2))[:, None] ** 1.5   # soft top/bottom
        im = Image.new("RGBA", (W, H // 2), (196, 206, 220, 0)); im.putalpha(Image.fromarray((a * 200).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18)))
        wide = Image.new("RGBA", (W * 2, H // 2)); wide.paste(im, (0, 0)); wide.paste(im.transpose(Image.FLIP_LEFT_RIGHT), (W, 0))   # mirrored = seamless loop
        return wide
    return cached(("fog", k), mk)
def s_fogwalk(s, t, d, part):
    """T31 faceless fictional silhouette walking away into fog (code-drawn)."""
    def bg():
        y = np.linspace(0, 1, H)[:, None]; top = np.array([18, 24, 36]); hz = np.array([120, 134, 152]); bot = np.array([26, 30, 38])
        vy = .52; c = np.where(y < vy, top + (hz - top) * (y / vy) ** 1.6, hz + (bot - hz) * ((y - vy) / (1 - vy)) ** .7)
        im = Image.fromarray(np.repeat(c[:, None, :], W, 1).reshape(H, W, 3).astype(np.uint8)); dd = ImageDraw.Draw(im)
        vx, vy_ = W / 2, H * vy
        for k in range(-9, 10): dd.line([(vx, vy_), (vx + k * 260, H)], fill=(52, 58, 70), width=2)
        for k in range(1, 12): yy = vy_ + (H - vy_) * (k / 12) ** 2.2; dd.line([(0, yy), (W, yy)], fill=(48, 54, 66), width=2)
        for k in range(6):   # far terminal lights
            x = 300 + k * 270; dd.rectangle([x, vy_ - 60, x + 120, vy_ - 52], fill=(220, 226, 236))
        return glow(im, int(vx), int(vy_ - 30), 520, (220, 232, 255), .28)
    fr = cached("fogbg", bg).copy(); u = t / max(d, .1)
    z = 1 - .62 * ease(u); vy = H * .52; feet = vy + (H * .95 - vy) * z; h = int(700 * z)
    a = 1 - .9 * ease((u - .35) / .65)
    if h > 10 and a > .02:
        sil = silhouette(h, t * 6.5, True).filter(ImageFilter.GaussianBlur(1))
        rim = silhouette(h, t * 6.5, True, (150, 170, 200)).resize((int(h * .5 * 1.04), int(h * 1.02))).filter(ImageFilter.GaussianBlur(4))
        x = W / 2 - sil.size[0] / 2 + 30 * math.sin(t * .8)
        shd = Image.new("RGBA", (int(h * .5), max(2, int(h * .08))), (0, 0, 0, 0)); ImageDraw.Draw(shd).ellipse([0, 0, shd.size[0] - 1, shd.size[1] - 1], fill=(0, 0, 0, int(120 * a)))
        fr.paste(shd, (int(x), int(feet - shd.size[1] / 2)), shd)
        for im_, dx in ((rim, -h * .01), (sil, 0)):
            im2 = im_.copy(); im2.putalpha(im2.getchannel("A").point(lambda v: int(v * a))); fr.paste(im2, (int(x + dx), int(feet - h)), im2)
    for k, (sp, yy, al) in enumerate(((22, .44, .55), (-34, .52, .7), (48, .62, .5))):
        fl = _fog_layer(k); off = int((t * sp + k * 300) % (2 * W)); al2 = al * (.6 + .4 * ease(u))
        f2 = fl.copy(); f2.putalpha(f2.getchannel("A").point(lambda v: int(v * al2)))
        for ox in (-off, 2 * W - off): fr.paste(f2, (ox, int(H * yy - H / 4)), f2)
    fr = floaters(fr, ("fog", s.get("at")), t, 6, (210, 220, 235))
    if s.get("text") and t > .6:
        dr = ImageDraw.Draw(fr); f = F(ANTON, 96); dr.text((W / 2, 160), s["text"].upper(), font=f, fill=CREAM, anchor="mm")
        if s.get("sub"): dr.text((W / 2, 240), s["sub"].upper(), font=F(MONO, 30), fill=(200, 208, 220), anchor="mm")
    tag(fr, s.get("tag", "ILLUSTRATION · NOT A REAL PERSON")); credit(fr, "SOURCE: " + s["source"] if s.get("source") else "", (190, 196, 206))
    return fr

def s_cctv(s, t, d, part):
    """T32 CCTV still: grain, scanlines, REC dot, running counter, LAST SEEN lock box (illustrative)."""
    def bg():
        im = Image.new("RGB", (W, H), (40, 44, 42)); dd = ImageDraw.Draw(im); vx, vy = W * .55, H * .42
        dd.polygon([(0, 0), (vx - 200, vy - 140), (vx - 200, vy + 160), (0, H)], fill=(58, 62, 60))
        dd.polygon([(W, 0), (vx + 200, vy - 140), (vx + 200, vy + 160), (W, H)], fill=(52, 56, 54))
        dd.polygon([(0, H), (vx - 200, vy + 160), (vx + 200, vy + 160), (W, H)], fill=(78, 82, 78))
        dd.rectangle([vx - 200, vy - 140, vx + 200, vy + 160], fill=(96, 100, 96))
        for k in range(5):
            q = (k + 1) / 6; y = vy - 140 - (vy - 140) * (1 - q) ** 1.3
            x0 = vx - 200 - (vx - 200) * (1 - q) ** 1.3; x1 = vx + 200 + (W - vx - 200) * (1 - q) ** 1.3
            dd.rectangle([x0 + (x1 - x0) * .4, y - 10, x0 + (x1 - x0) * .6, y + 4], fill=(200, 205, 196))
        for k in range(4):
            x = vx - 200 + 60 + k * 90; dd.rectangle([x, vy - 40, x + 50, vy + 160], fill=(70, 74, 70))
        dd.text((vx, vy - 100), s.get("sign", "GATE"), font=F(ANTON, 56), fill=(190, 196, 186), anchor="mm")
        return im.filter(ImageFilter.GaussianBlur(1.2))
    fr = cached(("cctvbg", s.get("sign", "GATE")), bg).copy()
    u = t / max(d, .1); h = 330; px = W * .40 + 260 * ease(u); feet = H * .78
    sil = silhouette(h, t * 6, True, (16, 18, 18)); fr.paste(sil, (int(px - sil.size[0] / 2), int(feet - h)), sil)
    g = fr.convert("L"); fr = Image.merge("RGB", (g.point(lambda v: int(v * .86)), g, g.point(lambda v: int(v * .8))))
    nz = Image.fromarray(R("cctvn", s.get("at"), int(t * 15)).integers(0, 255, (H // 6, W // 6), dtype=np.uint8)).resize((W, H)).convert("RGB")
    fr = Image.blend(fr, ImageChops.overlay(fr, nz), .35)
    def scan():
        sl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(sl)
        for y in range(0, H, 4): dd.line([(0, y), (W, y)], fill=(0, 0, 0, 46))
        return sl
    sl = cached("scan", scan); fr.paste(sl, (0, 0), sl)
    dr = ImageDraw.Draw(fr); f = F(MONO, 38); hud = (226, 232, 220)
    dr.text((70, 60), s.get("cam", "CAM 04"), font=f, fill=hud); dr.text((W - 70, 60), s.get("date", ""), font=f, fill=hud, anchor="ra")
    if (t % 1) < .6: dr.ellipse([70, 128, 100, 158], fill=(230, 40, 40))
    sec = int(t + s.get("t0", 3)); dr.text((116, 122), f"REC {sec // 3600:02d}:{sec // 60 % 60:02d}:{sec % 60:02d}", font=f, fill=hud)
    lk = s.get("lock_at", .8)
    if t > lk:
        e = eout((t - lk) / .7); bx = [px - 130, feet - h - 40, px + 130, feet + 20]
        full = [60, 40, W - 60, H - 120]; b = [full[i] + (bx[i] - full[i]) * e for i in range(4)]; L = 60
        for (x, y, sx, sy) in ((b[0], b[1], 1, 1), (b[2], b[1], -1, 1), (b[0], b[3], 1, -1), (b[2], b[3], -1, -1)):
            dr.line([(x, y), (x + sx * L, y)], fill=YEL, width=7); dr.line([(x, y), (x, y + sy * L)], fill=YEL, width=7)
        if e > .95:
            lab = s.get("label", "LAST SEEN"); fw = F(ANTON, 58); tw = dr.textlength(lab, font=fw)
            dr.rectangle([b[2] + 20, b[1], b[2] + 50 + tw, b[1] + 84], fill=YEL); dr.text((b[2] + 35, b[1] + 6), lab, font=fw, fill=INK)
            if s.get("sub"): dr.text((b[2] + 24, b[1] + 96), s["sub"].upper(), font=F(MONO, 30), fill=hud)
    tag(fr, s.get("tag", "RECREATION · ILLUSTRATIVE"), 44, 920 - 60); credit(fr, "SOURCE: " + s["source"] if s.get("source") else "", (200, 205, 196))
    return zoom(fr, 1.0 + .04 * ease(u), .45, .5)

def _stamp_img(text, sub, col, size, key):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = col + (230,)
    d.ellipse([6, 6, size - 6, size - 6], outline=c, width=8); d.ellipse([26, 26, size - 26, size - 26], outline=c, width=3)
    d.text((size / 2, size * .44), text.upper(), font=F(ANTON, int(size * .2)), fill=c, anchor="mm")
    if sub: d.text((size / 2, size * .66), sub.upper(), font=F(MONO, int(size * .085)), fill=c, anchor="mm")
    m = Image.fromarray((noise(("ink", key), size, size, 3, 8) > .32).astype(np.uint8) * 255)
    im.putalpha(ImageChops.multiply(im.getchannel("A"), m)); return im

def s_map3d(s, t, d, part):
    """T33/T34 3D tilted map with terrain texture; camera follows the plane and its glowing trail;
    optional passport stamps + ticket stub land on the map."""
    bbox = s.get("bbox", [17, 34.6, 30, 45.2]); hl = s.get("highlight", []); base, P, S = V.map_base(bbox, hl, part)
    def terr():
        b = np.asarray(base, np.float32); sea = b[5, 5]; land = (np.abs(b - sea).sum(2) > 40)
        n = noise(("terrain", tuple(bbox)), base.size[0], base.size[1], 5, 5)
        gx, gy = np.gradient(n); sh = np.clip(.5 + (gx - gy) * 90, 0, 1)
        k = np.where(land, .78 + .42 * sh, 1.0)[..., None]
        return Image.fromarray(np.clip(b * k, 0, 255).astype(np.uint8))
    tb = cached(("terr", tuple(bbox), tuple(hl), part % 4), terr)
    pins = s.get("pins", []); a = P(pins[0]["lon"], pins[0]["lat"]); b_ = P(pins[-1]["lon"], pins[-1]["lat"])
    ctrl = ((a[0] + b_[0]) / 2 + 160, (a[1] + b_[1]) / 2 - 60)
    r0, rs = s.get("route_at", .5), s.get("route_s", 2.4); ur = ease((t - r0) / rs); pl = quad(a, ctrl, b_, ur)
    mid = quad(a, ctrl, b_, .5); f_ = ease(t / max(d, .1)) * .35 + .45
    cx = a[0] + (pl[0] - a[0]) * .7 + (mid[0] - a[0]) * .3 * (1 - ur); cy = a[1] + (pl[1] - a[1]) * .7 + (mid[1] - a[1]) * .3 * (1 - ur)
    sc = s.get("scale", 420) * (1.08 - .12 * ease(t / max(d, .1)))
    hz = H * .16
    src = [(cx - sc * 2.5, cy - sc * 1.55), (cx + sc * 2.5, cy - sc * 1.55), (cx + sc * 1.05, cy + sc * .95), (cx - sc * 1.05, cy + sc * .95)]
    dst = [(0, hz), (W, hz), (W, H), (0, H)]; co = persp_coeffs(dst, src); Minv = np.linalg.inv(homog(co))
    # trail (on the flat map, so it tilts with it): wide soft glow + bright core
    q0 = int(60 * ur)
    if q0 > 1:
        pts = [quad(a, ctrl, b_, k / 60) for k in range(q0 + 1)]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; bx0, by0 = int(min(xs)) - 60, int(min(ys)) - 60
        lay = Image.new("RGBA", (int(max(xs)) - bx0 + 120, int(max(ys)) - by0 + 120), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        rel = [(x - bx0, y - by0) for x, y in pts]; ld.line(rel, fill=(255, 200, 80, 200), width=30, joint="curve")
        lay = lay.filter(ImageFilter.GaussianBlur(14)); ld = ImageDraw.Draw(lay); ld.line(rel, fill=(255, 246, 210, 255), width=8, joint="curve")
        tb2 = tb.copy(); tb2.paste(lay, (bx0, by0), lay)
    else: tb2 = tb
    sea = tuple(int(x) for x in np.asarray(base)[5, 5])
    fr = tb2.transform((W, H), Image.PERSPECTIVE, co, Image.BILINEAR, fillcolor=sea)
    # atmosphere: haze rising to the horizon + sky band
    def sky():
        y = np.linspace(0, 1, H)[:, None]; al = np.clip(1 - (y - .1) / .45, 0, 1) ** 1.6
        im = Image.new("RGBA", (W, H), (214, 226, 236, 0)); im.putalpha(Image.fromarray(np.repeat((al * 255).astype(np.uint8), W, 1))); return im
    sk = cached("sky", sky); fr.paste(sk, (0, 0), sk)
    dr = ImageDraw.Draw(fr)
    for k, p in enumerate(pins):
        tp = t - p.get("t", .2 + k * rs)
        if tp < 0: continue
        x, y = apply_h(Minv, *P(p["lon"], p["lat"])); e = back(min(1, tp / .3)); r = 16 * e
        dr.ellipse([x - r - 7, y - r - 7, x + r + 7, y + r + 7], fill=WHITE); dr.ellipse([x - r, y - r, x + r, y + r], fill=RED)
        dr.line([(x, y), (x, y - 60 * e)], fill=INK, width=4)
        if p.get("name"): V.pop_sticker(fr, p["name"].upper(), int(x + p.get("dx", 0)), int(y - 100 + p.get("dy", 0)), tp - .1, F(ANTON, 46), INK, CREAM, -2); dr = ImageDraw.Draw(fr)
    if 0 < ur:
        x, y = apply_h(Minv, *pl); x2, y2 = apply_h(Minv, *quad(a, ctrl, b_, min(1, ur + .02))); ang = -math.degrees(math.atan2(y2 - y, x2 - x)) if ur < 1 else 90
        alt = 70 * math.sin(math.pi * ur); pim = Image.new("RGBA", (160, 160), (0, 0, 0, 0)); V.icon(ImageDraw.Draw(pim), "plane", 80, 80, 110, INK)
        sh = Image.new("RGBA", (160, 160), (0, 0, 0, 0)); sh.putalpha(pim.getchannel("A").point(lambda v: v // 3))
        sh = sh.rotate(ang - 45, resample=Image.BICUBIC).filter(ImageFilter.GaussianBlur(4)); fr.paste((0, 0, 0), (int(x - 80 + 18), int(y - 80 + 14)), sh)
        pim = pim.rotate(ang - 45, resample=Image.BICUBIC); fr.paste(pim, (int(x - 80), int(y - 80 - alt)), pim)
    for k, st in enumerate(s.get("stamps", [])):
        ts = t - st.get("t", 1.0)
        if ts < 0: continue
        e = on2(ts); scl = 1.5 - .5 * min(1, e / .14); size = int(st.get("size", 300) * scl)
        im = cached(("stamp5", st["text"], st.get("sub", ""), st.get("col", "red")), lambda: _stamp_img(st["text"], st.get("sub", ""), RED if st.get("col", "red") == "red" else (40, 60, 120), 300, st["text"]))
        im = im.resize((size, size), Image.BILINEAR).rotate(st.get("rot", -12), resample=Image.BICUBIC)
        fr.paste(im, (int(st.get("x", .7) * W - size / 2), int(st.get("y", .4) * H - size / 2)), im)
    stb = s.get("stub")
    if stb and t > stb.get("t", 2.0):
        e = eout((t - stb.get("t", 2.0)) / .55)
        def mk():
            p = Image.new("RGBA", (460, 230), (246, 240, 226, 255)); dd = ImageDraw.Draw(p); dd.rectangle([0, 0, 460, 50], fill=(30, 52, 92))
            dd.text((20, 8), "TICKET", font=F(ANTON, 34), fill=CREAM)
            dd.text((20, 66), stb.get("from", "") + " > " + stb.get("to", ""), font=F(ANTON, 76), fill=INK)
            dd.text((20, 168), stb.get("date", "").upper(), font=F(MONO, 30), fill=(70, 66, 60))
            for y in range(0, 230, 14): dd.ellipse([452, y, 468, y + 8], fill=(0, 0, 0, 0))
            return p
        tk = tilt(cached(("stub", str(stb)), mk), .06, -1).rotate(7, expand=True, resample=Image.BICUBIC)
        drop(fr, tk, W - 600 + 500 * (1 - e), H * .56, 16, (12, 18), .5)
    if s.get("label"): V.pop_sticker(fr, s["label"].upper(), 360, 110, t - .25, F(ANTON, 56))
    fr = floaters(fr, ("map3d", s.get("at")), t, 7)
    credit(fr, "MAP: NATURAL EARTH (PUBLIC DOMAIN)" + (" · SOURCE: " + s["source"] if s.get("source") else ""), (60, 60, 64))
    return fr

def _brick(key):
    def mk():
        im = Image.new("RGBA", (176, 70), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rectangle([0, 10, 160, 70], fill=(150, 168, 140, 255)); d.polygon([(0, 10), (16, 0), (176, 0), (160, 10)], fill=(186, 204, 176, 255))
        d.polygon([(160, 10), (176, 0), (176, 60), (160, 70)], fill=(118, 136, 110, 255))
        for y in range(16, 66, 5): d.line([(0, y), (160, y)], fill=(132, 150, 124, 255))
        d.rectangle([66, 10, 94, 70], fill=(236, 230, 210, 255)); d.polygon([(66, 10), (82, 0), (110, 0), (94, 10)], fill=(246, 240, 222, 255))
        return im
    return cached(("brick", key), mk)
def _box(label, w=330, h=210):
    def mk():
        im = Image.new("RGBA", (w + 50, h + 50), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.polygon([(0, 50), (50, 0), (w + 50, 0), (w, 50)], fill=(150, 116, 74, 255)); d.rectangle([0, 50, w, h + 50], fill=(176, 136, 88, 255))
        d.polygon([(w, 50), (w + 50, 0), (w + 50, h), (w, h + 50)], fill=(132, 100, 62, 255))
        d.rectangle([w / 2 - 22, 50, w / 2 + 22, h + 50], fill=(196, 160, 110, 255))
        f = F(ANTON, 54); d.text((w / 2, 50 + h * .55), label.upper(), font=f, fill=(40, 30, 22, 255), anchor="mm")
        return im
    return cached(("box", label, w, h), mk)
def s_cashdrain(s, t, d, part):
    """T35 cash stacks build into a sourced number, then drain along arrows into shell-company boxes."""
    fr = archive(part); fr = breathe(fr, t, 700, 300, 700, (255, 220, 160), .06); dr = ImageDraw.Draw(fr); th = V.theme(part)
    cols, rows = s.get("cols", 6), s.get("rows", 7); b0, bs = s.get("build_at", .3), s.get("build_s", 1.6); da, ds = s.get("drain_at", 2.6), s.get("drain_s", 1.4)
    boxes = s.get("boxes", ["SHELL CO.", "SHELL CO.", "?"]); bxy = [(1460, 150 + k * 240) for k in range(len(boxes))]
    for k, lab in enumerate(boxes):
        e = eout((t - da + .5 - k * .12) / .45)
        if e > 0: bim = _box(lab); fr.paste(bim, (int(bxy[k][0] + 300 * (1 - e)), bxy[k][1]), bim)
    dr = ImageDraw.Draw(fr)
    n = cols * rows; brick = _brick("b"); basey = 840; solo = da > d   # no drain in this shot: centre the stacks
    left = (W - cols * 128) // 2 - 20 if solo else 210; nx = W // 2 if solo else 640
    drained = int(n * ease((t - da) / ds)) if t > da else 0
    order = sorted(range(n), key=lambda i: (-(i // cols), MO.seed("cd", i) % 97))   # top layers leave first
    gone = set(order[:drained])
    if t > da - .2:
        for k in range(len(boxes)):
            V.arrow(dr, (1000, 520 - 100 + k * 90), (bxy[k][0] - 10, bxy[k][1] + 140), eout((t - da + .2 - k * .1) / .5), RED, 9, .2)
    for i in range(n):
        r_, c_ = i // cols, i % cols; ti = b0 + bs * i / n; e = min(1, max(0, (on2(t) - ti) / .22))
        if e <= 0: continue
        x = left + c_ * 128 + r_ * 6; y = basey - 70 - r_ * 54 - 300 * (1 - eout(e))
        if i in gone:
            k = order.index(i); tk = da + ds * k / n; q = min(1, (t - tk) / .55)
            if q >= 1: continue
            tgt = bxy[k % len(boxes)]; p = quad((x, y), (1150, y - 260), (tgt[0] + 120, tgt[1] + 60), eout(q))
            sm = brick.resize((int(176 * (1 - .5 * q)), int(70 * (1 - .5 * q)))); fr.paste(sm, (int(p[0]), int(p[1])), sm); continue
        fr.paste(brick, (int(x), int(y)), brick)
    dr = ImageDraw.Draw(fr)
    v = s.get("value", 0); prog = ease((t - b0) / bs); dec = s.get("decimals", 0)
    if t > b0:
        txt = s.get("prefix", "") + f"{v * prog:,.{dec}f}" + s.get("suffix", "")
        f = F(ANTON, 190); dr.text((nx, 200), txt, font=f, fill=th["acc"] if not th["dark"] else YEL, anchor="mm", stroke_width=6, stroke_fill=INK)
        dr.text((nx, 320), s.get("label", "").upper(), font=F(ANTON, 64), fill=th["ink"], anchor="mm")
    lt = s.get("left")
    if lt and t > lt.get("t", .2):
        e = back(min(1, (t - lt.get("t", .2)) / .35)); x0, y0 = 110, basey - 70
        for k in range(2): fr.paste(brick, (x0, int(y0 - k * 58 - 200 * (1 - e))), brick)
        V.pop_sticker(fr, lt.get("text", "").upper(), x0 + 90, y0 - 190, t - lt.get("t", .2), F(ANTON, 50), YEL, INK, -4)
        dr = ImageDraw.Draw(fr); dr.text((x0 + 90, y0 + 90), lt.get("label", "").upper(), font=F(MONO, 26), fill=th["ink"], anchor="mm")
    fr = floaters(fr, ("cash", s.get("at")), t, 9)
    tag(fr, s.get("tag", "ILLUSTRATIVE FLOW")); V.source_line(dr, "", th); credit(fr, "SOURCE: " + s["source"] if s.get("source") else "", th["sub"])
    return zoom(fr, 1.0 + .03 * ease(t / max(d, .1)), .45, .5)

def _cork():
    def mk():
        n = noise("cork", W, H, 5, 24); r = R("cork").random((H, W)) < .02
        b = np.stack([150 + 50 * n, 104 + 40 * n, 64 + 26 * n], 2); b[r] *= .7
        return Image.fromarray(np.clip(b, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6))
    return cached("cork", mk)
def _note(c, k):
    w, h = c.get("w", 400), c.get("h", 230); kind = c.get("kind", "card")
    def mk():
        bgc = {"card": (246, 242, 230), "sticky": (247, 218, 90), "dark": (34, 36, 42)}.get(kind, (246, 242, 230))
        im = Image.new("RGBA", (w, h), bgc + (255,)); d = ImageDraw.Draw(im); ink = CREAM if kind == "dark" else INK
        if kind == "card": d.rectangle([0, 0, w, 14], fill=RED)
        if c.get("icon"): V.icon(d, c["icon"], w / 2, h * .36, h * .36, ink)
        f = F(ANTON, c.get("size", 52)); lines = V.wrap(d, c.get("text", "").upper(), f, w - 40)[:3]
        y = h * (.62 if c.get("icon") else .5) - len(lines) * f.size * .55
        for ln in lines: d.text((w / 2, y), ln, font=f, fill=ink, anchor="ma"); y += f.size * 1.1
        if c.get("sub"): d.text((w / 2, h - 34), c["sub"].upper(), font=F(MONO, 22), fill=(120, 114, 104) if kind != "dark" else (170, 170, 176), anchor="mm")
        return im
    return cached(("note", str(c)), mk)
def s_redstring(s, t, d, part):
    """T36 investigation wall: cork board, pinned cards appear on twos, red string links them."""
    fr = _cork().copy(); fr = breathe(fr, t, 380, 80, 900, (255, 214, 150), .10)
    cards = s.get("cards", []); step = s.get("step", .4); pos = []; tt = on2(t)
    for k, c in enumerate(cards):
        x, y = c.get("x", .5) * W, c.get("y", .4) * H; pos.append((x, y))
        e = min(1, max(0, (tt - .1 - k * step) / .25))
        if e <= 0: continue
        im = _note(c, k).rotate(c.get("rot", (-3, 2.5, -1.5, 3)[k % 4]), expand=True, resample=Image.BICUBIC)
        scl = 1.12 - .12 * e; im = im.resize((int(im.size[0] * scl), int(im.size[1] * scl)))
        drop(fr, im, x - im.size[0] / 2, y - im.size[1] / 2, 12, (8, 14), .55)
    dr = ImageDraw.Draw(fr); s0 = .2 + len(cards) * step
    for j, (i, k) in enumerate(s.get("links", [])):
        if i >= len(pos) or k >= len(pos): continue
        u = ease((t - s0 - j * .3) / .45)
        if u <= 0: continue
        p0 = (pos[i][0], pos[i][1] - _note(cards[i], i).size[1] / 2 + 16); p1 = (pos[k][0], pos[k][1] - _note(cards[k], k).size[1] / 2 + 16)
        L = math.dist(p0, p1); c = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + L * .12)
        pts = [quad(p0, c, p1, q / 30 * u) for q in range(31)]
        dr.line([(x + 4, y + 6) for x, y in pts], fill=(60, 30, 20), width=4); dr.line(pts, fill=(196, 28, 30), width=5)
    for k, (x, y) in enumerate(pos):
        if tt - .1 - k * step < .25: continue
        py = y - _note(cards[k], k).size[1] / 2 + 16
        dr.ellipse([x - 13, py - 13, x + 13, py + 13], fill=(200, 30, 30)); dr.ellipse([x - 6, py - 9, x, py - 3], fill=(255, 160, 150))
    if s.get("title") and t > s.get("title_at", s0):
        V.pop_sticker(fr, s["title"].upper(), int(W / 2), int(H * .1), t - s.get("title_at", s0), F(ANTON, 64), YEL, INK, -3)
    fr = floaters(fr, ("wall", s.get("at")), t, 8)
    credit(fr, "SOURCE: " + s["source"] if s.get("source") else "", (40, 30, 20))
    fx, fy = s.get("focus", [.5, .45]); u = ease(t / max(d, .1))
    return zoom(fr, 1.0 + .06 * u, .5 + (fx - .5) * u, .5 + (fy - .5) * u)

def s_wanted(s, t, d, part):
    """T37 wanted poster with a faceless silhouette (never a real face)."""
    fr = ImageEnhance.Brightness(archive(part)).enhance(.8); pw, ph = 760, 960
    def mk():
        p = Image.new("RGBA", (pw, ph), (232, 218, 186, 255)); dd = ImageDraw.Draw(p)
        n = noise(("wanted", s.get("at")), pw, ph, 4, 4); st = Image.fromarray((np.clip((n - .55) * 3, 0, 1) * 70).astype(np.uint8))
        p.paste((150, 120, 80), (0, 0), st); dd = ImageDraw.Draw(p)
        dd.text((pw / 2, 40), s.get("title", "WANTED"), font=F(ANTON, 170), fill=(60, 22, 18), anchor="ma")
        dd.rectangle([140, 250, pw - 140, 690], fill=(52, 50, 48)); sil = silhouette(560, 0, False, (20, 20, 22)).crop((0, 0, 280, 330)).resize((420, 495))
        sil = sil.crop((0, 0, 420, 440)); p.paste(sil, (int(pw / 2 - 210), 250), sil)
        dd.rectangle([140, 690, pw - 140, 720], fill=(232, 218, 186)); dd.text((pw / 2, 470), "?", font=F(ANTON, 160), fill=(120, 116, 110), anchor="mm")
        y = 740
        for ln in s.get("lines", [])[:3]: dd.text((pw / 2, y), ln.upper(), font=F(ANTON, 56), fill=(50, 30, 24), anchor="ma"); y += 72
        return p
    po = cached(("wanted", str(s.get("lines")), s.get("title")), mk)
    fl = .02 * math.sin(t * 2.2); po2 = tilt(po, .03 + fl, 1).rotate(-2, expand=True, resample=Image.BICUBIC)
    e = back(min(1, t / .5)); drop(fr, po2, W / 2 - po2.size[0] / 2, 40 + 120 * (1 - e), 20, (14, 22), .55)
    for x, y, a in ((W / 2 - 330, 70, -20), (W / 2 + 330, 70, 18)): V.tape(fr, x, y + 120 * (1 - e), a, 170, 50)
    fr = floaters(fr, ("wanted", s.get("at")), t, 8); tag(fr, s.get("tag", "ILLUSTRATION · NO REAL FACE"))
    credit(fr, "SOURCE: " + s["source"] if s.get("source") else "")
    return zoom(fr, 1.0 + .04 * ease(t / max(d, .1)), .5, .4)

def s_stage(s, t, d, part):
    """T38 seminar stage: big glowing screen, sweeping spotlights, haze, crowd silhouettes (fictional)."""
    def bg():
        y = np.linspace(0, 1, H)[:, None]; c = np.array([10, 10, 22]) + np.array([30, 22, 50]) * (1 - np.abs(y - .4) * 2).clip(0, 1)
        im = Image.fromarray(np.repeat(c[:, None, :], W, 1).reshape(H, W, 3).astype(np.uint8)); dd = ImageDraw.Draw(im)
        dd.polygon([(260, 700), (W - 260, 700), (W - 60, 820), (60, 820)], fill=(40, 34, 52)); dd.rectangle([60, 820, W - 60, 850], fill=(24, 20, 32))
        for k in range(14): x = 120 + k * 130; dd.rectangle([x, 40, x + 40, 52], fill=(70, 66, 90))
        return im
    fr = cached("stagebg", bg).copy(); scr = s.get("screen", [])
    sx0, sy0, sw, sh = 470, 110, 980, 540
    def screen():
        im = Image.new("RGB", (sw, sh), (16, 30, 70)); dd = ImageDraw.Draw(im)
        g = np.linspace(0, 1, sw)[None, :]; arr = np.zeros((sh, sw, 3)); arr[..., 0] = 20 + 60 * g; arr[..., 1] = 30 + 40 * g; arr[..., 2] = 90 + 80 * (1 - g)
        im = Image.fromarray(arr.astype(np.uint8)); dd = ImageDraw.Draw(im); y = sh / 2 - len(scr) * 60
        for k, ln in enumerate(scr[:3]):
            f = F(ANTON, 130 if k == 0 else 70); dd.text((sw / 2, y), ln.upper(), font=f, fill=YEL if k == 0 else CREAM, anchor="ma"); y += f.size * 1.15
        return im
    si = cached(("screen", str(scr)), screen); bright = .85 + .15 * ease(t / .5) + .04 * math.sin(t * 3.1)
    fr = glow(fr, sx0 + sw // 2, sy0 + sh // 2, 760, (110, 130, 230), .22 * bright)
    fr.paste(ImageEnhance.Brightness(si).enhance(bright), (sx0, sy0)); ImageDraw.Draw(fr).rectangle([sx0 - 8, sy0 - 8, sx0 + sw + 8, sy0 + sh + 8], outline=(60, 60, 76), width=8)
    if s.get("speaker", True):
        sp = silhouette(250, 0, False, (8, 8, 12)); fr.paste(sp, (int(W / 2 - 62 + 40 * math.sin(t * .6)), 470), sp)
    beams = Image.new("RGBA", (W // 2, H // 2), (0, 0, 0, 0)); bd = ImageDraw.Draw(beams)
    for k, (x0, ph) in enumerate(((180, 0), (W / 2, 2.1), (W - 180, 4.2))):
        ang = math.sin(t * .7 + ph) * .35; tx = x0 + math.sin(ang) * 900; tx = max(200, min(W - 200, W / 2 + (tx - W / 2) * .7))
        bd.polygon([(x0 / 2 - 10, 0), (x0 / 2 + 10, 0), (tx / 2 + 120, 760 / 2), (tx / 2 - 120, 760 / 2)], fill=(255, 236, 200, 46))
        bd.ellipse([tx / 2 - 130, 740 / 2, tx / 2 + 130, 800 / 2], fill=(255, 236, 200, 40))
    beams = beams.filter(ImageFilter.GaussianBlur(10)).resize((W, H)); fr.paste(beams, (0, 0), beams)
    hz = _fog_layer(1).copy(); hz.putalpha(hz.getchannel("A").point(lambda v: v // 5)); off = int(t * 18) % (2 * W)
    for ox in (-off, 2 * W - off): fr.paste(hz, (ox, 300), hz)
    cr = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(cr); hands = s.get("hands_at")
    for row in range(3):
        rr = R("crowd", row); n = 13 + row * 3; sz = 70 + row * 34; y0 = 790 + row * 95
        for k in range(n):
            x = (k + rr.uniform(-.3, .3)) * W / (n - 1); bob = 3 * math.sin(t * 2 + k * 1.7 + row); c = (6 + row * 2, 6 + row * 2, 10 + row * 2, 255)
            cd.ellipse([x - sz * .32, y0 - sz * .9 + bob, x + sz * .32, y0 - sz * .2 + bob], fill=c)
            cd.rounded_rectangle([x - sz * .75, y0 - sz * .3 + bob, x + sz * .75, y0 + sz * 1.6], int(sz * .4), fill=c)
            if hands is not None and row < 2 and (MO.seed("hand", row, k) % 5 == 0) and t > hands + (MO.seed("hand", row, k) % 7) * .1:
                cd.polygon([(x + sz * .4, y0 - sz * .2), (x + sz * .62, y0 - sz * .2), (x + sz * .75, y0 - sz * 1.5 + bob), (x + sz * .55, y0 - sz * 1.5 + bob)], fill=c)
                cd.ellipse([x + sz * .5, y0 - sz * 1.75 + bob, x + sz * .85, y0 - sz * 1.4 + bob], fill=c)
    fr.paste(cr, (0, 0), cr)
    fr = floaters(fr, ("stage", s.get("at")), t, 8, (200, 200, 230))
    tag(fr, s.get("tag", "ILLUSTRATION")); credit(fr, "SOURCE: " + s["source"] if s.get("source") else "", (170, 170, 190))
    if s.get("label"): V.pop_sticker(fr, s["label"].upper(), 1620, 120, t - .4, F(ANTON, 52))
    return zoom(fr, 1.0 + .05 * ease(t / max(d, .1)), .5, .42)

def s_ticker(s, t, d, part):
    """T39 phone price ticker climbing, then frozen at WITHDRAWALS DISABLED. Values only from research (v0 -> v1);
    the app screen itself is labelled ILLUSTRATIVE."""
    fr = archive(part); th = V.theme(part); dr = ImageDraw.Draw(fr)
    v0, v1 = s.get("v0", 0.5), s.get("v1", 29.95); fz = s.get("freeze_at", d * .62); cur = s.get("cur", "€")
    pts_n = 80; climb = min(1, t / max(fz, .1))
    def path(k):   # stepped climb that never falls (the company set it)
        q = k / (pts_n - 1); r = R("tick", s.get("at")); steps = np.cumsum(r.random(pts_n) ** 3); steps = steps / steps[-1]
        return float(steps[k])
    ghost = cached(("ghost", s.get("at")), lambda: _ghost_chart(s.get("at")))
    fr.paste(ghost, (0, 0), ghost)
    ph = 880; pw = 450; px, py = 1180, 30
    scr = Image.new("RGB", (pw - 30, ph - 30), (12, 14, 22)); sd = ImageDraw.Draw(scr)
    sd.text((30, 60), s.get("app", "MY BALANCE").upper(), font=F(SANS, 28), fill=(150, 156, 170))
    val = v0 + (v1 - v0) * (path(int(climb * (pts_n - 1))))
    frozen = t >= fz
    sd.text((30, 104), f"{cur}{val:,.2f}", font=F(ANTON, 96), fill=(120, 124, 132) if frozen else (80, 230, 140))
    sd.text((30, 230), s.get("unit", "PER COIN, SET BY THE COMPANY").upper(), font=F(MONO, 18), fill=(130, 134, 146))
    cx0, cy0, cw_, ch_ = 20, 300, pw - 70, 300; m = max(2, int(climb * (pts_n - 1)) + 1)
    pts = [(cx0 + cw_ * k / (pts_n - 1), cy0 + ch_ - ch_ * path(k)) for k in range(m)]
    if len(pts) > 1:
        sd.polygon(pts + [(pts[-1][0], cy0 + ch_), (pts[0][0], cy0 + ch_)], fill=(24, 60, 44) if not frozen else (40, 42, 48))
        sd.line(pts, fill=(80, 230, 140) if not frozen else (130, 130, 136), width=5)
        if not frozen: sd.ellipse([pts[-1][0] - 9, pts[-1][1] - 9, pts[-1][0] + 9, pts[-1][1] + 9], fill=(180, 255, 200))
    for k, lab in enumerate(("BUY", "SELL")):
        sd.rounded_rectangle([20 + k * 200, 640, 200 + k * 200, 710], 16, fill=(40, 120, 70) if k == 0 else ((60, 60, 66) if frozen else (150, 50, 50)))
        sd.text((110 + k * 200, 675), lab, font=F(ANTON, 40), fill=CREAM, anchor="mm")
    if frozen:
        e = back(min(1, (t - fz) / .3)); bw = int((pw - 70) * e)
        sd.rounded_rectangle([pw / 2 - 15 - bw / 2, 420, pw / 2 - 15 + bw / 2, 560], 18, fill=RED)
        if e > .8:
            V.icon(sd, "lock", pw / 2 - 15, 455, 52, CREAM)
            for k, ln in enumerate(s.get("frozen_text", ["WITHDRAWALS", "DISABLED"])): sd.text((pw / 2 - 15, 498 + k * 34), ln, font=F(ANTON, 34), fill=CREAM, anchor="mm")
    phone = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); pd_ = ImageDraw.Draw(phone); pd_.rounded_rectangle([0, 0, pw - 1, ph - 1], 60, fill=(18, 18, 22, 255))
    msk = Image.new("L", scr.size, 0); ImageDraw.Draw(msk).rounded_rectangle([0, 0, scr.size[0] - 1, scr.size[1] - 1], 48, fill=255); phone.paste(scr, (15, 15), msk)
    phone = tilt(phone, .035, -1); e = eout(t / .5); drop(fr, phone, px + 60 * (1 - e), py, 26, (18, 26), .55)
    fr = glow(fr, px + pw // 2, py + 380, 420, (80, 230, 140) if not frozen else (230, 70, 54), .10)
    dr = ImageDraw.Draw(fr); f = F(ANTON, 110)
    for k, ln in enumerate(s.get("headline", [])[:2]):
        dr.text((140, 250 + k * 130), ln.upper(), font=f, fill=th["ink"])
    for k, st in enumerate(s.get("stickers5", [])):
        V.pop_sticker(fr, st.upper(), 420 + (k % 2) * 260, 600 + k * 70, on2(t) - (s.get("sticker_at", .9) + k * .45), F(ANTON, 50), YEL if k % 2 == 0 else CREAM, INK, (-5, 4, -3)[k % 3])
    tag(fr, s.get("tag", "ILLUSTRATIVE APP SCREEN"), px + 30, py + ph + 6)
    fr = floaters(fr, ("tick", s.get("at")), t, 8)
    credit(fr, "SOURCE: " + s["source"] if s.get("source") else "", th["sub"])
    return zoom(fr, 1.0 + .03 * ease(t / max(d, .1)), .55, .5)
def _ghost_chart(key):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); r = R("ghost", key); y = H * .8; pts = []
    for k in range(40): y -= r.random() ** 2 * 26; pts.append((k * W / 39, y))
    d.line(pts, fill=(255, 255, 255, 60), width=26); return im.filter(ImageFilter.GaussianBlur(12))

TYPES5 = dict(flapboard=s_flapboard, boardingpass=s_boardingpass, fogwalk=s_fogwalk, cctv=s_cctv, map3d=s_map3d,
              stamps=s_map3d, cashdrain=s_cashdrain, redstring=s_redstring, wanted=s_wanted, stage=s_stage, ticker=s_ticker)
OWN_ATMOS = {"fogwalk", "cctv", "stage"}   # templates that already carry their own near layer
