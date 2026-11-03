"""Shot timing model shared by the renderer and the free craft checks (no image libraries here).

events(s, d) -> times (seconds from shot start) when something visibly new happens in shot s
of length d. CONTINUOUS types move all the time (route drawing, typing, scrolling, ticker), so
they never count as a dead frame. accents(s, d) -> extra times the renderer adds a camera punch-in
so no shot holds still longer than MAX_HOLD (docs/EDITING_CRAFT.md rule P1).
"""
MAX_HOLD = 2.5      # P1: nothing still for longer than this
ACCENT_EVERY = 2.2  # spacing of automatic accents inside a long static stretch

CONTINUOUS = {"map", "money", "magnify", "scrub", "barrace"}
STRIKING = {"stat", "map", "phone", "stamp", "photo", "pair", "trio", "wall", "polaroids", "magnify", "split", "money", "coin"}
AI_PICTURE = {"scene"}
PHOTO_TYPES = {"photo", "pair", "trio", "wall", "polaroids", "magnify", "split"}


def _steps(n, step, t0=0.0):
    return [t0 + k * step for k in range(n)]


def events(s, d):
    t = s["type"]; ev = [0.0]
    if t == "kinetic":
        ev += _steps(len(s.get("text", "").split()), s.get("step", .28))
        if s.get("hl"): ev.append(len(s["text"].split()) * s.get("step", .28) * .5)
    elif t == "stat": ev += [.45, 1.1, .6]
    elif t in ("headline", "card"): ev += [.75, .9]
    elif t == "list": ev += _steps(len(s.get("items", [])), s.get("step", .8))
    elif t == "flow": ev += _steps(len(s.get("boxes", [])), s.get("step", .6))
    elif t == "tree": ev += _steps(s.get("levels", 4), .5)
    elif t in ("bars",): ev += _steps(len(s.get("items", [])), .5)
    elif t == "timeline": ev += _steps(len(s.get("events", [])), .45, .3)
    elif t == "chart": ev += [s.get("draw", 1.6)] + [s.get("draw", 1.6) * n.get("i", 0) / max(1, len(s.get("points", [1] * 10)) - 1) for n in s.get("notes", [])]
    elif t == "coin": ev += [s.get("drain_at", .6), s.get("drain_at", .6) + 1.6] if s.get("drain") else [.5]
    elif t == "phone":
        n = len(s.get("messages", [])) or len(s.get("notes", [])) or len(s.get("rows", [])) or 1
        ev += _steps(n, s.get("step", .9), s.get("first", .5))
    elif t in ("pair", "trio", "wall", "polaroids", "split"):
        n = len(s.get("photos", [])) or {"pair": 2, "trio": 3, "split": 2}.get(t, 4)
        ev += _steps(n, s.get("step", .45)) + [n * s.get("step", .45) + .3] + [k * s.get("step", .45) + .5 for k in range(n)]
        if s.get("circle") is not None: ev.append(n * s.get("step", .45) + .2)
    elif t == "photo": ev += [.55, .5]
    elif t == "stamp": ev += [.0, .35, .8]
    elif t == "chapter": ev += [.6]
    elif t in ("scene", "name", "screen", "end"): ev += [.5]
    if s.get("label") and t in ("scene", "photo", "phone", "map"): ev.append(.5)
    for k, _ in enumerate(s.get("stickers", [])): ev.append(.7 + k * .6)
    if t == "phone" and s.get("side"): ev += [.8, 1.05]
    for k, x in enumerate(s.get("marks", [])):       # extra marker strokes / stickers placed by the operator
        ev.append(x.get("t", .9 + k * .8))
    return sorted(x for x in set(round(e, 3) for e in ev) if 0 <= x < d)


def accents(s, d):
    """Times for automatic camera punch-ins so no static stretch is longer than MAX_HOLD."""
    if s["type"] in CONTINUOUS or s["type"] in ("chapter", "end"): return []
    ev = events(s, d) + [d]; out = []
    import math
    for a, b in zip(ev, ev[1:]):
        if b - a <= MAX_HOLD: continue
        n = math.ceil((b - a) / ACCENT_EVERY)          # n equal pieces, each <= ACCENT_EVERY
        out += [round(a + (b - a) * k / n, 3) for k in range(1, n)]
    return out


def max_gap(s, d):
    if s["type"] in CONTINUOUS: return 0.0
    ev = sorted(set(events(s, d) + accents(s, d))) + [d]
    return max([b - a for a, b in zip(ev, ev[1:])] + [0.0])


def media_keys(s):
    """Every photo/AI picture a shot shows (for the no-repeat check)."""
    t = s["type"]; out = []
    if t == "photo": out.append(s.get("file") or s.get("commons") or s.get("q"))
    if t in ("pair", "trio", "wall", "polaroids", "split", "magnify"):
        for p in s.get("photos", [s] if t == "magnify" else []):
            out.append(p.get("file") or p.get("commons") or p.get("q"))
    if t == "scene":
        cast = "+".join(f"{c['who']}-{c.get('pose', 'front_neutral')}" for c in s.get("cast", [])[:2])
        out.append(f"{s.get('set')}__{s.get('time')}__{cast}")
    return [x for x in out if x]
