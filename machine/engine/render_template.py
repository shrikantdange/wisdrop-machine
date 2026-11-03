"""Wisdrop episode renderer TEMPLATE (example = Ep1 opening). usage: python render_template.py <episode_dir> out.mp4 [frame,frame..]
Copy per episode. One shot function per script VISUAL; SHOTS maps each line id to its shot (Playbook Rule 1: say it, show it).
NO logo intro. Chapter cards come from timeline.json chaps."""
import sys, json, math, subprocess
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edhelpers import *
EP = sys.argv[1]; TL = json.load(open(os.path.join(EP, 'timeline.json'))); DUR = TL['dur']; SEGS = TL['segs']
ST = {s['i']: s['start'] for s in SEGS}; EN = {s['i']: s['end'] for s in SEGS}
OUT = sys.argv[2]
WIN = Image.open(P + "ed-ray-window.png").convert("RGB").resize((int(W * 1.12), int(H * 1.12)), Image.LANCZOS)
HALLB = PL["hall"].resize((W, H)).filter(ImageFilter.GaussianBlur(6))
AMBER = (240, 170, 60)

def cw(dr, txt, f, y, col, stroke=0):
    tw = dr.textlength(txt, font=f); dr.text(((W - tw) / 2, y), txt, font=f, fill=col, stroke_width=stroke, stroke_fill=(0, 0, 0))
def board():
    fr = Image.new("RGB", (W, H), NAVY); dr = ImageDraw.Draw(fr)
    for x in range(0, W, 96): dr.line([(x, 0), (x, H)], fill=(22, 32, 54))
    for y in range(0, H, 96): dr.line([(0, y), (W, y)], fill=(22, 32, 54))
    return fr
def source(dr, txt): cw(dr, "SOURCE: " + txt, F(MONO, 26), 800, GREY)

# ---------- evidence: stat slam ----------
def stat(t, d, val, fmt, label, src, col=GOLD, pre="", strike_at=None):
    fr = board(); g = eout(t / .8)
    fr = glow(fr, 960, 380, 420, col, .18)
    dr = ImageDraw.Draw(fr)
    v = val * g; txt = pre + fmt(v)
    s = 0.9 + 0.1 * back(t / .45); f = F(ANTON, int(250 * s))
    c = col
    if strike_at is not None and t > strike_at: c = RED
    tw = dr.textlength(txt, font=f); y = 380 - f.size * .62
    dr.text(((W - tw) / 2, y), txt, font=f, fill=c)
    if strike_at is not None and t > strike_at:
        k = eout((t - strike_at) / .35); x0 = (W - tw) / 2 - 30
        dr.line([(x0, 390), (x0 + (tw + 60) * k, 360)], fill=PAPER, width=14)
    a = eout((t - .35) / .5)
    if a > 0: cw(dr, label, F(ANTON, 72), 560 + 20 * (1 - a), PAPER)
    if t > .6: source(dr, src)
    return zoom(fr, 1 + .03 * ease(t / d)), 0

# ---------- evidence: headline card ----------
HEAD = [("Unitree has lost about half its value", "since trading began in August"),
        ("MetaX and Moore Threads", "have also halved since July")]
def headlines(t, d):
    fr = board(); dr = ImageDraw.Draw(fr)
    for k, (h1, h2) in enumerate(HEAD):
        st = .1 + k * .55; a = eout((t - st) / .5)
        if a <= 0: continue
        x = 260 + (1 - a) * 900 + k * 120; y = 170 + k * 290; rot = (-1.2 if k == 0 else 1.0)
        card = Image.new("RGBA", (1280, 230), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rectangle([0, 0, 1279, 229], fill=PAPER + (255,)); cd.rectangle([0, 0, 1279, 8], fill=RED + (255,))
        cd.text((40, 30), "MARKETS  ·  27 OCT 2026", font=F(MONO, 24), fill=(110, 104, 96))
        hw = cd.textlength(h1, font=F(SERIF, 54))
        if t > st + .7: cd.rectangle([36, 78, 36 + hw * eout((t - st - .7) / .4) + 8, 142], fill=(250, 214, 130))
        cd.text((40, 78), h1, font=F(SERIF, 54), fill=(24, 24, 30))
        cd.text((40, 150), h2, font=F(SERIF, 44), fill=(60, 58, 60))
        card = card.rotate(rot, resample=Image.BICUBIC, expand=True)
        sh = Image.new("RGBA", card.size, (0, 0, 0, 0)); sh.putalpha(card.getchannel("A").point(lambda v: v * 0.45)); sh = sh.filter(ImageFilter.GaussianBlur(14))
        fr.paste(sh, (int(x + 14), int(y + 18)), sh); fr.paste(card, (int(x), int(y)), card)
    dr = ImageDraw.Draw(fr)
    if t > .8: cw(dr, "PARAPHRASED FROM: SEOUL ECONOMIC DAILY (CITING BLOOMBERG), 27 OCT 2026", F(MONO, 24), 800, GREY)
    return zoom(fr, 1 + .025 * ease(t / d)), 0

# ---------- evidence: chart ----------
PTS = [(0, .30), (.08, .33), (.16, .31), (.25, .42), (.33, .50), (.42, .63), (.48, .78), (.52, 1.0), (.58, .86), (.64, .90), (.72, .76), (.80, .70), (.88, .62), (.94, .64), (1.0, .55)]
def chart(t, d):
    fr = board(); dr = ImageDraw.Draw(fr)
    dr.text((150, 90), "CHINA'S TECH BOARD (STAR50)", font=F(ANTON, 84), fill=PAPER)
    dr.text((154, 200), "Index level, 2026  ·  shape illustrative", font=F(MONO, 26), fill=GREY)
    X0, X1, Y0, Y1 = 170, 1750, 760, 300
    dr.line([(X0, Y0), (X1, Y0)], fill=GREY, width=2)
    for k, m in enumerate(["JAN", "MAR", "MAY", "JUL", "SEP", "OCT"]):
        xx = X0 + (X1 - X0) * [0, .18, .36, .52, .74, 1.0][k]; dr.text((xx - 24, Y0 + 12), m, font=F(MONO, 24), fill=GREY)
    k = min(1, t / max(1.8, d * .75)); n = k * (len(PTS) - 1)
    pts = [(X0 + (X1 - X0) * x, Y0 - (Y0 - Y1) * y) for x, y in PTS]
    pk = 7
    for j in range(int(n) + 1):
        if j + 1 >= len(pts): break
        f_ = 1 if j + 1 <= n else n - j
        a, b = pts[j], pts[j + 1]; e = (a[0] + (b[0] - a[0]) * f_, a[1] + (b[1] - a[1]) * f_)
        dr.line([a, e], fill=(GOLD if j < pk else RED), width=9)
    if n >= pk:
        px, py = pts[pk]; dr.ellipse([px - 12, py - 12, px + 12, py + 12], fill=GOLD)
        dr.text((px - 120, py - 80), "PEAK 2,255", font=F(ANTON, 50), fill=GOLD)
    if k >= 1:
        a = eout((t - max(1.8, d * .75)) / .4); ex, ey = pts[-1]
        dr.text((ex - 330, ey + 30 - 10 * (1 - a)), "ABOUT -40%", font=F(ANTON, 76), fill=RED)
    source(dr, "REUTERS, 26 OCT 2026  ·  PEAK 2,255.25 ON 1 JUL")
    return zoom(fr, 1 + .03 * ease(t / d)), 0

# ---------- evidence: P/E bars ----------
def pe(t, d):
    fr = board(); dr = ImageDraw.Draw(fr)
    dr.text((150, 110), "PRICE-TO-EARNINGS AT THE PEAK", font=F(ANTON, 88), fill=PAPER)
    dr.text((154, 225), "How many years of profit you pay for", font=F(MONO, 30), fill=GREY)
    x0, maxw = 560, 1000
    for i, (nm, sb, val, col, st) in enumerate([("STAR50", "China tech board", 250, GOLD, .2), ("NASDAQ 100", "already called a bubble", 30, PAPER, 1.2)]):
        y = 360 + i * 210
        if t < st: continue
        g = eout((t - st) / 1.0)
        dr.text((150, y + 10), nm, font=F(ANTON, 64), fill=col); dr.text((152, y + 92), sb, font=F(MONO, 24), fill=GREY)
        w = int(maxw * val / 250 * g)
        if w > 4: dr.rounded_rectangle([x0, y, x0 + w, y + 110], 12, fill=col)
        dr.text((x0 + w + 30, y + 6), f"{int(round(val * g))}x", font=F(ANTON, 90), fill=col)
    source(dr, "REUTERS, 26 OCT 2026")
    return zoom(fr, 1 + .03 * ease(t / d)), 0

# ---------- story shots ----------
def s_hall(t, d):
    u = t / d; fr = crop_cam(PL["hall"], u, 1.0, 1.07, 1, 0)
    for lx in (470, 760, 1050): fr = glow(fr, lx, 190, 120, (255, 200, 120), .18 + .06 * math.sin(t * 7 + lx))
    ex = eout(t / 0.7)
    paste(fr, C["ray_awe"], 520 - 70 * u - (1 - ex) * 260, 1130, breathe=0.007 * math.sin(t * 2.4))
    paste(fr, C["kenzie"], 1470 + 60 * u + (1 - ex) * 260, 1110, rot=1.2 * math.sin(t * 3.1), breathe=0.005 * math.sin(t * 3))
    for ft in (0.5, 1.6, 2.9):
        if ft < t < ft + .16: fr = glow(fr, 1330, 330, 130, (235, 245, 255), 1 - (t - ft) / .16)
    dust(fr, t); return fr, 0
def s_promise(t, d):
    fr = Image.new("RGB", (W, H), NAVY); fr = glow(fr, 960, 640, 440, (255, 190, 90), .5)
    paste(fr, C["vic_prom"], 960, 1100 + 20 * (1 - eout(t / .5)), s=0.94 + 0.06 * eout(t / .6), shadow=False, breathe=0.004 * math.sin(t * 2))
    fr = glow(fr, 700 + 520 * ((t * .6) % 1), 800, 70, (255, 240, 200), .45); sparkles(fr, 960, 790, t, a=.5)
    return zoom(fr, 1.0 + .05 * ease(t / d)), 0
CHAPLABEL = ["PART", "TITLE"]
def s_chap(t, d):
    fr = board(); dr = ImageDraw.Draw(fr); a = eout(t / .5)
    cw(dr, CHAPLABEL[0], F(MONO, 40), 380, GREY)
    cw(dr, CHAPLABEL[1], F(ANTON, 190), 430 + 30 * (1 - a), PAPER)
    k = eout((t - .4) / .6); dr.rectangle([960 - 330 * k, 690, 960 + 330 * k, 700], fill=AMBER)
    if t > d - .3: fr = Image.blend(fr, Image.new("RGB", (W, H), (0, 0, 0)), (t - (d - .3)) / .3 * .6)
    return fr, 0
def s_window(t, d):
    u = ease(t / d); z = 1.0 + .09 * u
    cwid, chei = W / z, H / z; cx = W * 1.12 * (.52 + .1 * u); cy = H * 1.12 * .5
    fr = WIN.crop((int(cx - cwid / 2), int(cy - chei / 2), int(cx + cwid / 2), int(cy + chei / 2))).resize((W, H), Image.BILINEAR)
    fr = glow(fr, 1000, 240, 160, (255, 220, 160), .12 + .04 * math.sin(t * 1.3))
    rain(fr, t); return fr, 0
def s_street(t, d):
    u = t / d; fr = PL["street"].copy()
    fr = glow(fr, 1665, 380, 220, (255, 200, 110), .22 + .05 * math.sin(t * 5))
    paste(fr, C["kenzie"], 760 + 40 * u, 1090, rot=1.0 * math.sin(t * 3), breathe=.005 * math.sin(t * 3))
    if 1.0 < t < 1.16: fr = glow(fr, 640, 330, 120, (235, 245, 255), 1 - (t - 1.0) / .16)
    rain(fr, t); return zoom(fr, 1.0 + .06 * ease(u), .4, .45), 0
def s_ai(t, d):
    fr = Image.blend(HALLB, Image.new("RGB", (W, H), (6, 8, 16)), .55)
    for k in range(2):
        st = .05 + k * .32; a = back(min(1, max(0, (t - st) / .4)))
        if t < st: continue
        fr = glow(fr, 760 + k * 400, 470, 260, GOLD, .25 * min(1, (t - st) / .3))
        dr = ImageDraw.Draw(fr); f = F(ANTON, max(1, int(420 * a))); ch = "AI"[k]
        tw = dr.textlength(ch, font=f); dr.text((760 + k * 400 - tw / 2, 480 - f.size * .6), ch, font=f, fill=GOLD, stroke_width=6, stroke_fill=(0, 0, 0))
    return zoom(fr, 1 + .04 * ease(t / d)), 0
SL = [0.5, 1.6, 2.7]
def s_factory(t, d):
    u = t / d; shake = 0; fr = PL["factory"].copy()
    if int(t * 2) % 2 == 0: fr = glow(fr, 262, 270, 60, (255, 40, 30), .75)
    pressx = 760
    for j in range(7):
        p = ((j / 7.0) + t * .2) % 1.0; x = 1250 - p * 1450; sc = 0.45 + 0.95 * p
        if x < -200: continue
        y = belt(max(x, -100)); bx = C["box"].resize((int(C["box"].size[0] * sc), int(C["box"].size[1] * sc)), Image.BILINEAR)
        fr.paste(bx, (int(x - bx.size[0] / 2), int(y - bx.size[1] + 10 * sc)), bx)
        if x < pressx - 10:
            dr = ImageDraw.Draw(fr); lw, lh = int(70 * sc), int(40 * sc); lx, ly = int(x - lw / 2), int(y - bx.size[1] * .62)
            dr.rectangle([lx, ly, lx + lw, ly + lh], fill=PAPER, outline=(20, 20, 30), width=2)
            dr.text((lx + lw * .22, ly + lh * .02), "AI", font=F(ANTON, max(8, int(34 * sc))), fill=NAVY)
    by = belt(pressx); py = by - 330
    for s_ in SL:
        dt = t - s_
        if -0.18 < dt < 0: py = by - 330 + 190 * ((dt + .18) / .18) ** 2
        elif 0 <= dt < 0.45: py = by - 140 - 190 * eout(dt / .45)
        if 0 <= dt < 0.1: shake = 5 * (1 - dt / .1)
    pr = C["press"]; fr.paste(pr, (int(pressx - pr.size[0] / 2), int(py - pr.size[1])), pr)
    for s_ in SL:
        dt = t - s_
        if 0 <= dt < .3: fr = glow(fr, pressx, by - 150, 150, (255, 225, 160), .4 * (1 - dt / .3))
    lev = sum(-4 * math.cos((t - s_) / .3 * math.pi / 2) for s_ in SL if -0.3 < t - s_ < 0.3)
    paste(fr, C["vic_lever"], 1480 - 30 * u, 1070, rot=lev, breathe=0.005 * math.sin(t * 3))
    dust(fr, t, n=40, speed=.6); return zoom(fr, 1.06 - .06 * ease(u), .5, .55), shake
def s_end(t, d):
    u = ease(t / d); fr = HALLB.copy(); fr = glow(fr, 960, 300, 380, (255, 180, 90), .3)
    paste(fr, C["ray_awe"], 960, 1180 + 40 * (1 - u), s=1.15 + .1 * u, breathe=0.007 * math.sin(t * 2.2))
    dust(fr, t)
    if t > d - 1.0: fr = Image.blend(fr, Image.new("RGB", (W, H), (0, 0, 0)), (t - (d - 1.0)))
    return fr, 0

big = lambda v: f"{int(round(v)):,}x"
SHOTS = [  # (start, fn, story?)
    (0.0, s_hall, 1),
    (ST[1] - .1, lambda t, d: stat(t, d, 8000, big, "RETAIL OVERSUBSCRIPTION", "REUTERS BREAKINGVIEWS, 11 AUG 2026"), 0),
    (ST[2] - .1, lambda t, d: stat(t, d, 50, lambda v: f"-{int(round(v))}%", "UNITREE, SINCE ITS AUGUST DEBUT", "SEOUL ECONOMIC DAILY / BLOOMBERG, 27 OCT 2026", col=RED), 0),
    (ST[3] - .1, headlines, 0),
    (ST[4] - .1, chart, 0),
    (ST[5] - .1, lambda t, d: stat(t, d, 480, lambda v: f"${int(round(v))}B", "WIPED OUT", "REUTERS, 26 OCT 2026", strike_at=ST[6] - ST[5] + .05), 0),
    (ST[7] - .1, s_promise, 1),
    (TL['chaps'][0]['start'], s_chap, 0),   # one entry per chapter
    (ST[8] - .15, s_window, 1),
    (ST[10] - .1, s_street, 1),
    (ST[11] - .1, s_ai, 0),
    (ST[12] - .1, pe, 0),
    (ST[13] - .1, s_factory, 1),
    (ST[14] - .1, s_end, 1),
    (DUR, None, 0)]

# ---------- captions: words.json (whisper_words.py) if present, else estimated inside each line ----------
chunks = []
WJ = os.path.join(EP, 'words.json')
LINEWORDS = [[tuple(w) for w in L['words']] for L in json.load(open(WJ))] if os.path.exists(WJ) else None
for k, s in enumerate(SEGS):
    if LINEWORDS: lw = LINEWORDS[k]
    else:
        ws = s['text'].replace('...', '…').split(); tot = sum(len(w) + 2 for w in ws); cur = s['start']; d = s['end'] - s['start']; lw = []
        for w in ws: dd = d * (len(w) + 2) / tot; lw.append((cur, cur + dd, w)); cur += dd
    c = []
    for w in lw:
        c.append(w)
        if len(c) == 4 or w[2].endswith((".", ",", "…", "?")): chunks.append(c); c = []
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
    k = max(j for j in range(len(SHOTS) - 1) if SHOTS[j][0] <= t)
    st, fn, story = SHOTS[k]; d = SHOTS[k + 1][0] - st
    if fn is s_chap: CHAPLABEL[:] = next(c['label'] for c in TL['chaps'] if abs(c['start'] - st) < .01).split('|')
    fr, shake = fn(t - st, d)
    if 0 <= t - st < .18 and k > 0: fr = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), fr, .45 + .55 * (t - st) / .18)
    fr = finish(fr, i, shake)
    if story: fr = tag(fr)
    if fn is not s_chap: fr = bug(caption(fr, t))
    return fr

if __name__ == "__main__":
    if len(sys.argv) > 3:
        for i in [int(x) for x in sys.argv[3].split(",")]: render(i).convert("RGB").resize((960, 540)).save(f"chk_{i}.jpg", quality=85)
        sys.exit()
    n = int(DUR * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    for i in range(n): ff.stdin.write(render(i).tobytes())
    ff.stdin.close(); ff.wait(); print("done", OUT, n)
