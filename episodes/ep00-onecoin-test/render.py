"""Wisdrop ep00 pipeline test: OneCoin cold open (~20 s). usage: python render.py <ep_dir> out.mp4 [frames]"""
import os as _o, sys as _s; _R = _o.environ.get("WIS_REPO") or _o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "..")); _s.path.insert(0, _o.path.join(_R, "machine"))
from paths import KIT as _KIT, ENGINE as _ENG
import sys, os, json, math, subprocess
sys.path.insert(0, _ENG)
from edhelpers import *
EP = sys.argv[1]; TL = json.load(open(os.path.join(EP, 'timeline.json'))); DUR = TL['dur']; SEGS = TL['segs']
ST = {s['i']: s['start'] for s in SEGS}; EN = {s['i']: s['end'] for s in SEGS}
OUT = sys.argv[2]
IMG = os.path.join(EP, "img")
AMBER = (240, 170, 60)

# ---------- assets ----------
def plate_ep(name, scale=1.18):
    return Image.open(f"{IMG}/plates/{name}").convert("RGB").resize((int(W * scale), int(H * scale)), Image.LANCZOS)
GATE = plate_ep("plate_gate.png")
# departure screen text drawn in code onto the pillar monitor (plate coords at 1.18 scale)
_d = ImageDraw.Draw(GATE)
_sx, _sy = 1720, 205
_d.text((_sx, _sy), "SOFIA  >  ATHENS", font=F(MONO, 26), fill=AMBER)
_d.text((_sx, _sy + 40), "25 OCT 2017", font=F(MONO, 26), fill=PAPER)
_d.text((_sx, _sy + 80), "DEPARTED", font=F(MONO, 26), fill=GREEN)
KITCH = plate_ep("plate_kitchen.png", 1.0)
def cut_ep(name, h):
    im = Image.open(f"{IMG}/cut/{name}").convert("RGBA"); bb = im.getbbox(); im = im.crop(bb); r = h / im.size[1]
    return im.resize((int(im.size[0] * r), int(h)), Image.LANCZOS)
MARIA = match(cut_ep("maria_worried.png", 880), (255, 205, 150), .14, (255, 200, 130), .45)

def cw(dr, txt, f, y, col, stroke=0):
    tw = dr.textlength(txt, font=f); dr.text(((W - tw) / 2, y), txt, font=f, fill=col, stroke_width=stroke, stroke_fill=(0, 0, 0))
def board():
    fr = Image.new("RGB", (W, H), NAVY); dr = ImageDraw.Draw(fr)
    for x in range(0, W, 96): dr.line([(x, 0), (x, H)], fill=(22, 32, 54))
    for y in range(0, H, 96): dr.line([(0, y), (W, y)], fill=(22, 32, 54))
    return fr
def source(dr, txt, pre="SOURCE: "): cw(dr, pre + txt, F(MONO, 26), 800, GREY)

# ---------- story shots ----------
def s_gate(t, d):   # L0: empty gate, board reads SOFIA > ATHENS 25 OCT 2017
    u = t / d; fr = crop_cam(GATE, u, 1.0, 1.06, 1, 0)
    fr = glow(fr, 1250, 470, 230, (255, 205, 130), .16 + .03 * math.sin(t * 1.7))
    fr = glow(fr, 1640, 260, 170, AMBER, .10)
    rain_ = rain(fr, t); return fr, 0
def s_vanish(t, d):  # L1: push to the empty jet-bridge door, its light dies
    u = t / d; fr = crop_cam(GATE, u, 1.04, 1.08, 0, 0)
    k = 1 - eout((t - .35) / .6)
    if k > 0: fr = glow(fr, 1190, 470, 260, (255, 210, 140), .35 * k)
    fr = Image.blend(fr, Image.new("RGB", (W, H), (6, 8, 16)), .25 * (1 - k))
    return fr, 0
def s_kitchen(t, d):  # L5: our saver, worried at her phone, kitchen at night
    u = ease(t / d); fr = KITCH.copy()
    fr = glow(fr, 590, 170, 260, (255, 200, 120), .14 + .03 * math.sin(t * 2))
    paste(fr, MARIA, 930, 1060, breathe=0.006 * math.sin(t * 2.2))
    fr = glow(fr, 1010, 470, 70, (190, 215, 255), .35 + .08 * math.sin(t * 9))  # phone glow
    fr = zoom(fr, 1.0 + .07 * u, .48, .45)
    if t > d - .9: fr = Image.blend(fr, Image.new("RGB", (W, H), (0, 0, 0)), min(1, (t - (d - .9)) / .9))
    return fr, 0

# ---------- evidence ----------
def stat(t, d, val, fmt, label, src, col=GOLD):
    fr = board(); g = eout(t / 1.1); fr = glow(fr, 960, 380, 420, col, .18); dr = ImageDraw.Draw(fr)
    txt = fmt(val * g); s = 0.9 + 0.1 * back(t / .45); f = F(ANTON, int(250 * s))
    tw = dr.textlength(txt, font=f); dr.text(((W - tw) / 2, 380 - f.size * .62), txt, font=f, fill=col)
    a = eout((t - .5) / .6)
    if a > 0: cw(dr, label, F(ANTON, 72), 560 + 20 * (1 - a), PAPER)
    if t > .6: source(dr, src)
    return zoom(fr, 1 + .03 * ease(t / d)), 0
def no_chain(t, d):  # L3: "BLOCKCHAIN" struck through in red
    fr = board(); dr = ImageDraw.Draw(fr); f = F(ANTON, 230); txt = "BLOCKCHAIN"
    a = eout(t / .6); tw = dr.textlength(txt, font=f); x0 = (W - tw) / 2; y = 380 - f.size * .62
    dr.text((x0, y + 30 * (1 - a)), txt, font=f, fill=PAPER)
    st = .55
    if t > st:
        k = eout((t - st) / .35); dr.line([(x0 - 30, 400), (x0 - 30 + (tw + 60) * k, 340)], fill=RED, width=16)
    if t > st + .3: cw(dr, "NO REAL ONE", F(ANTON, 72), 580, RED)
    if t > .6: source(dr, "U.S. DOJ (SDNY), 16 DEC 2022")
    return zoom(fr, 1 + .03 * ease(t / d)), 0
def wanted(t, d):  # L4: recreated FBI release card
    fr = board(); a = eout(t / .75)
    card = Image.new("RGBA", (1440, 300), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rectangle([0, 0, 1439, 299], fill=PAPER + (255,)); cd.rectangle([0, 0, 1439, 9], fill=RED + (255,))
    cd.text((44, 32), "FBI  ·  30 JUN 2022", font=F(MONO, 26), fill=(110, 104, 96))
    h1a, h1b = "OneCoin founder added to ", "Ten Most Wanted"
    fa = F(SERIF, 50); wa = cd.textlength(h1a, font=fa); wb = cd.textlength(h1b, font=fa)
    if t > .7: cd.rectangle([44 + wa - 4, 92, 44 + wa + wb * eout((t - .7) / .4) + 6, 162], fill=(250, 214, 130))
    cd.text((44, 92), h1a + h1b, font=fa, fill=(24, 24, 30))
    cd.text((44, 186), "Fugitives list over the multibillion-dollar fraud", font=F(SERIF, 44), fill=(60, 58, 60))
    card = card.rotate(-1.0, resample=Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0)); sh.putalpha(card.getchannel("A").point(lambda v: v * 0.45)); sh = sh.filter(ImageFilter.GaussianBlur(14))
    x = 240 + (1 - a) * 900; y = 250
    fr.paste(sh, (int(x + 14), int(y + 18)), sh); fr.paste(card, (int(x), int(y)), card)
    dr = ImageDraw.Draw(fr)
    if t > .8: source(dr, "FBI.GOV, 30 JUN 2022", pre="RECREATED FROM: ")
    return zoom(fr, 1 + .025 * ease(t / d)), 0

bill = lambda v: f"${v:.0f}B+" if v >= 3.95 else f"${v:.1f}B"
SHOTS = [
    (0.0, s_gate, 1),
    (ST[1] + .04, s_vanish, 1),
    (ST[2] + .04, lambda t, d: stat(t, d, 4, bill, "TAKEN IN BY ONECOIN", "U.S. DOJ (SDNY), 12 SEP 2023 · REUTERS"), 0),
    (ST[3] + .04, no_chain, 0),
    (ST[4] + .04, wanted, 0),
    (ST[5] + .04, s_kitchen, 1),
    (DUR, None, 0)]

# ---------- captions ----------
chunks = []
WJ = os.path.join(EP, 'words.json')
LINEWORDS = [[tuple(w) for w in L['words']] for L in json.load(open(WJ))] if os.path.exists(WJ) else None
for k, s in enumerate(SEGS):
    if LINEWORDS: lw = LINEWORDS[k]
    else:
        ws = s['text'].split(); tot = sum(len(w) + 2 for w in ws); cur = s['start']; dd0 = s['end'] - s['start']; lw = []
        for w in ws: dd = dd0 * (len(w) + 2) / tot; lw.append((cur, cur + dd, w)); cur += dd
    c = []
    for w in lw:
        c.append(w)
        if len(c) == 4 or w[2].endswith((".", ",", "?")): chunks.append(c); c = []
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
    fr, shake = fn(t - st, d)
    if 0 <= t - st < .22 and k > 0: fr = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), fr, .45 + .55 * ease((t - st) / .22))
    fr = finish(fr, i, shake)
    if story: fr = tag(fr)
    return bug(caption(fr, t))

if __name__ == "__main__":
    if len(sys.argv) > 3:
        for i in [int(x) for x in sys.argv[3].split(",")]: render(i).convert("RGB").resize((960, 540)).save(f"{EP}/chk_{i}.jpg", quality=85)
        sys.exit()
    n = int(DUR * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    for i in range(n): ff.stdin.write(render(i).tobytes())
    ff.stdin.close(); ff.wait(); print("done", OUT, n)
