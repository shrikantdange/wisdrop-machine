#!/usr/bin/env python3
"""Package an episode for upload: titles, two thumbnails, description (chapters, sources,
credits, disclosure) and tags. Code only, no AI cost.

  python machine/package.py <ep_dir> <timeline.json> <assets_root> <out_dir>
"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); KIT = os.path.join(REPO, "kit")
ANTON = os.path.join(KIT, "fonts", "Anton.ttf"); RED = (232, 64, 56); PAPER = (244, 238, 224); NAVY = (16, 24, 42); GOLD = (236, 184, 64)
TW, TH = 1280, 720


def mmss(s): s = int(s); return f"{s // 60}:{s % 60:02d}"


def titles(ep):
    p = os.path.join(ep, "titles.md"); t = open(p).read() if os.path.exists(p) else ""
    opts = [re.sub(r"\s*<-.*$", "", m).strip() for m in re.findall(r"^\d+\.\s*(.+)$", t, re.M)]
    pick = next((re.sub(r"\s*<-.*$", "", m).strip() for m in re.findall(r"^\d+\.\s*(.+<-\s*pick.*)$", t, re.M)), opts[0] if opts else "")
    thumbs = re.findall(r'"([^"]{2,24})"', t.split("Thumbnail", 1)[1]) if "Thumbnail" in t else []
    return pick, opts, thumbs


def photo_credits(ep):
    cp = os.path.join(ep, "media", "credits.json")
    if not os.path.exists(cp): return []
    c = json.load(open(cp))
    return ["", "Photos (Wikimedia Commons; colour-treated and cropped)"] + [f"{v['title'].replace('File:', '')} by {v['artist']}, {v['licence']}: {v['page']}" for v in c.values()]


def sources(ep):
    t = open(os.path.join(ep, "research.md")).read(); seen = []
    for u in re.findall(r"https?://[^\s;|)]+", t):
        u = u.rstrip(".,")
        if u not in seen: seen.append(u)
    return seen


def fit(d, txt, maxw, size):
    while size > 40:
        f = ImageFont.truetype(ANTON, size)
        if d.textlength(txt, font=f) <= maxw: return f
        size -= 6
    return ImageFont.truetype(ANTON, size)


def thumb(bg, cut, words, red_word, path):
    im = bg.resize((TW, TH), Image.LANCZOS) if bg else Image.new("RGB", (TW, TH), NAVY)
    im = ImageEnhance.Brightness(im).enhance(1.25); im = ImageEnhance.Contrast(im).enhance(1.1)   # phones show dark art muddy
    if cut:
        h = int(TH * .92); c = cut.resize((int(cut.size[0] * h / cut.size[1]), h), Image.LANCZOS)
        glow = Image.new("RGBA", c.size, (0, 0, 0, 0)); glow.putalpha(c.getchannel("A").filter(ImageFilter.GaussianBlur(18)))
        im.paste((255, 220, 160), (TW - c.size[0] - 30, TH - h), glow); im.paste(c, (TW - c.size[0] - 40, TH - h), c)
    d = ImageDraw.Draw(im); y = 70
    for k, w in enumerate(words[:2]):
        f = fit(d, w.upper(), 700, 190); col = RED if w == red_word else PAPER
        d.text((60, y), w.upper(), font=f, fill=col, stroke_width=10, stroke_fill=(0, 0, 0)); y += f.size + 30
    im.save(path, quality=92)


def main(ep, tl_p, assets, out):
    os.makedirs(out, exist_ok=True)
    tl = json.load(open(tl_p)); shots = json.load(open(os.path.join(ep, "shots.json")))["shots"]
    st = {s["i"]: s["start"] for s in tl["segs"]}; pick, opts, thumbs = titles(ep); srcs = sources(ep)
    man_p = os.path.join(assets, "eps", os.path.basename(ep.rstrip("/")), "asset_manifest.json")
    man = json.load(open(man_p)) if os.path.exists(man_p) else {}
    # chapters: cold open + each chapter card
    ch = [("0:00", "Cold open")] + [(mmss(st.get(s["at"], 0)), f"Part {s.get('num')}: {s.get('title')}") for s in shots if s["type"] == "chapter"]
    hook = " ".join(L["text"] for L in tl["segs"][:2])
    music = open(os.path.join(KIT, "music", "ATTRIBUTION.txt")).read().split("SFX")[0].replace("MUSIC (CC BY 4.0, credit in description):", "").strip()
    desc = "\n".join([hook, "", "Chapters"] + [f"{a} {b}" for a, b in ch] + ["", "Sources"] + srcs +
                     ["", "Characters in story scenes are fictional composites; real people are never shown. Some illustrations are AI-assisted and dramatised; every number on screen is sourced above.",
                      "", "Music", music] + photo_credits(ep) + ["", "Icons: Tabler Icons (MIT). Emoji graphics: OpenMoji (openmoji.org), CC BY-SA 4.0. Maps: Natural Earth (public domain)."] + ["", "#Wisdrop #moneycrimes #fraud"])
    open(os.path.join(out, "description.txt"), "w").write(desc)
    case = re.sub(r"^ep\d+-", "", os.path.basename(ep.rstrip("/"))).replace("-", " ")
    tags = [case, f"{case} scam", f"{case} explained", "financial fraud", "crypto scam", "ponzi scheme", "pyramid scheme", "true crime", "money crimes", "documentary", "Wisdrop"]
    json.dump({"title": pick, "alternates": [o for o in opts if o != pick], "tags": tags, "chapters": ch}, open(os.path.join(out, "meta.json"), "w"), indent=1)
    # thumbnails: A = first story set + main character cutout; B = board with big text
    # thumbs come from shots.json "thumb": {"set", "time", "who", "pose"}; else the first scene that has a character
    th = json.load(open(os.path.join(ep, "shots.json"))).get("thumb")
    scene = th or next((s for s in shots if s["type"] == "scene" and s.get("cast")), None) or next((s for s in shots if s["type"] == "scene" and s.get("set") not in (None, "board")), None)
    def load(rel, rgba=False):
        p = os.path.join(assets, rel) if rel else ""
        return Image.open(p).convert("RGBA" if rgba else "RGB") if p and os.path.exists(p) else None
    shot = ("shot_" + scene["set"] + "__" + scene.get("time", "night") + "__" + "+".join(f"{c['who']}-{c.get('pose', 'front_neutral')}" for c in scene.get("cast", [])[:2])) if scene and scene.get("cast") else ""
    bg = load(man.get(shot, {}).get("asset")) if shot in man else load(man.get(f"set_{scene['set']}__{scene.get('time', 'night')}", {}).get("asset")) if scene else None
    who = ({"who": th["who"], "pose": th.get("pose", "front_neutral")} if th and th.get("who") else
           (scene.get("cast") or [None])[0] if scene else None)
    cut = load(man.get(f"char_{who['who']}__{who.get('pose', 'front_neutral')}", {}).get("cut"), True) if who else None
    tA = (thumbs[0] if thumbs else pick.split()[1] if pick else "").split() or ["WISDROP"]
    tB = (thumbs[1] if len(thumbs) > 1 else "NO COIN").split()
    if shot in man: cut = None       # the character is already in the composed picture
    sh_all = json.load(open(os.path.join(ep, "shots.json")))
    n_th = v3_thumbs(ep, tl_p, sh_all, out)
    if n_th < 2:
        thumb(bg, cut, [" ".join(tA)], " ".join(tA), os.path.join(out, "thumb_A.jpg"))
        thumb(None, None, [" ".join(tB[:-1]) or tB[0], tB[-1]], tB[-1], os.path.join(out, "thumb_B.jpg"))
    tf = title_formulas(sh_all.get("title_facts", {}))
    meta = json.load(open(os.path.join(out, "meta.json"))); meta["formula_titles"] = tf; json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=1)
    print(f"OK packaged: title '{pick}', {len(srcs)} sources, {len(ch)} chapters, {max(n_th, 2)} thumbnails, {len(tf)} formula titles")


FORMULAS = ["{money} and a Coin That Never Existed", "How {case} Fooled {people} People", "The {who}, {money}, and a Coin That Never Existed",
            "Inside {case}: The {money} Crypto Scam", "{case}: The Scam That Fooled {people}"]
def title_formulas(f):
    """K3: accurate, short (<= 60 chars), important words first. Only facts from shots.json title_facts (sourced)."""
    out = []
    for k, fm in enumerate(FORMULAS):
        try: t = fm.format(**f)
        except KeyError: continue
        if len(t) <= 60: out.append({"formula": k + 1, "title": t, "chars": len(t)})
    return out


def v3_thumbs(ep, tl_p, sh, out):
    """3 thumbnails from the strongest frames (map, stat, stamp, phone, photo), big 2-3 word text, phone-size check."""
    try:
        import importlib.util
        os.environ["WIS_TIMELINE"] = tl_p; os.environ["WIS_NO_CAPTIONS"] = "1"; sys.argv = ["r", ep, "/tmp/x.mp4"]
        sys.path.insert(0, os.path.join(REPO, "machine", "engine"))
        spec = importlib.util.spec_from_file_location("thr", os.path.join(REPO, "machine", "engine", "shots_render.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    except Exception as e:
        print("REVIEW thumbnails fell back to simple ones:", e); return 0
    pref = ["map", "stamp", "stat", "phone", "scene", "pair", "photo", "money"]
    cands = []
    for typ in pref:
        for k, (st, s) in enumerate(m.SHOTS):
            if s["type"] == typ and st < m.DUR: cands.append((k, st, m.STARTS[k + 1])); break
    words = sh.get("thumb_text") or ["WISDROP", "THE SCAM", "WATCH"]
    ims = []
    for j, (k, a, b) in enumerate(cands[:3]):
        fr = m.render(int((a + min(b - a, 3.0) * .85) * 30)).resize((TW, TH), Image.LANCZOS)
        fr = ImageEnhance.Contrast(ImageEnhance.Brightness(fr).enhance(1.12)).enhance(1.15)
        d = ImageDraw.Draw(fr); w = words[j % len(words)].upper().split(); y = 40
        lines = [" ".join(w[:2]), " ".join(w[2:])] if len(w) > 2 else [" ".join(w)]
        for i, ln in enumerate(l for l in lines if l):
            f = fit(d, ln, 760, 170); col = (226, 70, 54) if i == len(lines) - 1 else (247, 209, 58)
            d.text((50, y), ln, font=f, fill=col, stroke_width=12, stroke_fill=(0, 0, 0)); y += f.size + 18
            if f.size * 246 / TW < 14: print("REVIEW thumb text too small on phones:", ln)
        p = os.path.join(out, f"thumb_{'ABC'[j]}.jpg"); fr.save(p, quality=92); ims.append(fr)
    # phone-size preview: how they look in a feed (246 px wide)
    sheet = Image.new("RGB", (900, 120 + 210 * len(ims)), (255, 255, 255)); d = ImageDraw.Draw(sheet)
    d.text((24, 30), "Phone feed preview (246 px thumbnails)", font=ImageFont.truetype(ANTON, 36), fill=(20, 20, 20))
    for j, im in enumerate(ims):
        sm = im.resize((246, 138), Image.LANCZOS); sheet.paste(sm, (24, 100 + j * 210))
        d.text((290, 110 + j * 210), f"Thumbnail {'ABC'[j]}", font=ImageFont.truetype(ANTON, 30), fill=(20, 20, 20))
    sheet.save(os.path.join(out, "thumbs_phone_preview.jpg"), quality=90)
    print(f"OK {len(ims)} thumbnails from frames + phone preview")
    return len(ims)


if __name__ == "__main__":
    main(*sys.argv[1:5])
