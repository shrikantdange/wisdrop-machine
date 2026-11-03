"""Fetch real photos for `photo` shots from Wikimedia Commons, commercial-safe licences only.

    python machine/fetch_media.py episodes/ep01-onecoin

For every shot {"type": "photo", "q": "search words"} (or "commons": "File:Exact name.jpg")
it saves episodes/<ep>/media/<slug>.jpg (1600 px wide) and records the credit in
media/credits.json. package.py puts every credit in the description.

Allowed: CC0, public domain (PD, PDM, US government), CC BY, CC BY-SA (any version).
Refused: NC (non-commercial), ND (no-derivatives: our colour treatment is a change), unknown.
Already-fetched files are kept (free re-runs). Prints OK / FAIL lines like the rest of the machine.
"""
import json, os, re, sys, urllib.parse, urllib.request

UA = {"User-Agent": "WisdropMachine/1.0 (https://github.com/shrikantdange/wisdrop-machine)"}
API = "https://commons.wikimedia.org/w/api.php"

def slug(q): return re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")[:60]

def ok_licence(lic):
    l = (lic or "").lower()
    if any(x in l for x in ("nc", "nd", "fair use", "non-free")): return False
    return any(x in l for x in ("cc0", "public domain", "pd", "cc by", "cc-by"))

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()

def search(q=None, title=None, all_=False):
    p = {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": "1600"}
    if title: p["titles"] = title
    else: p.update({"generator": "search", "gsrnamespace": "6", "gsrsearch": q + " filetype:bitmap", "gsrlimit": "12"})
    d = json.loads(get(API + "?" + urllib.parse.urlencode(p)))
    pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda x: x.get("index", 0)); out = []
    for pg in pages:
        i = (pg.get("imageinfo") or [{}])[0]; m = i.get("extmetadata", {})
        lic = m.get("LicenseShortName", {}).get("value", "")
        if not ok_licence(lic) or i.get("width", 0) < 1200 or "svg" in i.get("mime", ""): continue
        artist = re.sub("<[^>]+>", "", m.get("Artist", {}).get("value", "unknown")).strip()[:80]
        r = {"url": i.get("thumburl") or i["url"], "page": i.get("descriptionurl", ""), "licence": lic,
             "artist": artist, "title": pg["title"]}
        if not all_: return r
        out.append(r)
    return out if all_ else None

def main(ep):
    sh = json.load(open(os.path.join(ep, "shots.json"))); md = os.path.join(ep, "media"); os.makedirs(md, exist_ok=True)
    cp = os.path.join(md, "credits.json"); cred = json.load(open(cp)) if os.path.exists(cp) else {}
    bad = 0
    items = []
    tl = os.environ.get("WIS_TEST_LINES", "").strip(); ids = None     # test runs fetch only what the voiced lines show
    if tl:
        ids = set()
        for part in tl.split(","):
            a, _, b = part.partition("-"); ids |= set(range(int(a), int(b or a) + 1))
    for s in sh["shots"]:
        if ids is not None and s["at"] not in ids: continue
        if s.get("type") in ("photo", "magnify", "parallax", "lineart"): items.append(s)
        elif s.get("type") in ("pair", "trio", "wall", "polaroids", "split"): items += s.get("photos", [])
    for s in items:
        if s.get("file") and os.path.exists(os.path.join(md, s["file"])): continue
        key = s.get("commons") or s.get("q"); fn = slug(key) + ".jpg"; path = os.path.join(md, fn)
        if os.path.exists(path) and fn in cred: print("OK cached", fn); continue
        try:
            if s.get("commons"): r = search(title=s.get("commons"))
            else:   # v5 photo picker: score up to 4 candidates, keep the clearest subject (machine/photo_score.py)
                import io, photo_score as PS
                from PIL import Image
                best = None
                for c in search(q=s["q"], all_=True)[:4]:
                    raw = get(c["url"]); sc, why = PS.score(Image.open(io.BytesIO(raw)))
                    print(f"PLAN photo candidate {c['title'][:60]} score {sc} {why}")
                    if best is None or sc > best[0]: best = (sc, c, raw)
                r = best[1] if best else None
                if best and best[0] < PS.MIN_SCORE: print(f"REVIEW best photo for {key!r} scores {best[0]} (< {PS.MIN_SCORE}); consider a code card")
        except Exception as e:
            r = None; print("FAIL", key, e)
        if not r: print("FAIL no commercial-safe photo for", repr(key), "- change q or use a card"); bad += 1; continue
        open(path, "wb").write(get(r["url"])); cred[fn] = r
        print("OK", fn, "|", r["licence"], "|", r["artist"])
    json.dump(cred, open(cp, "w"), indent=1)
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main(sys.argv[1])
