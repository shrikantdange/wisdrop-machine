"""Photo picker score (v5, free, numpy): prefer a clear subject; reject photos whose salient region is
signage, an empty wall, or blur.  score(path_or_img) -> (score 0-1, reasons[]).  Used by fetch_media.py.
"""
import numpy as np
from PIL import Image, ImageFilter
def _arr(x): return np.asarray((Image.open(x) if isinstance(x, str) else x).convert("RGB").resize((480, 320)), float)
def score(x):
    a = _arr(x); g = a.mean(2); why = []
    lap = np.abs(g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]); sharp = float(lap.var())
    b = 16; blk = g[:320 // b * b, :480 // b * b].reshape(320 // b, b, 480 // b, b).swapaxes(1, 2)
    sd = blk.std((2, 3)); ch, cw = sd.shape; core = sd[ch // 5: ch - ch // 5, cw // 5: cw - cw // 5]
    flat_core = float((core < 5).mean())                                   # empty wall / pillar in the middle
    sat = (a.max(2) - a.min(2)) / (a.max(2) + 1)
    sb = ((sat > .45) & (g > 60))[:320 // b * b, :480 // b * b].reshape(320 // b, b, 480 // b, b).swapaxes(1, 2).mean((2, 3))
    wb = ((g > 185) & (sat < .2))[:320 // b * b, :480 // b * b].reshape(320 // b, b, 480 // b, b).swapaxes(1, 2).mean((2, 3))
    panel = float(((sb > .45) & (wb > .04) & (wb < .5)).mean())           # saturated panel with white glyphs = a sign
    sign = panel > .025
    empty = flat_core > .45
    blur = sharp < 60
    s = .55 + .25 * min(1, sharp / 400) + .2 * (1 - flat_core)
    if sign: s -= .35; why.append(f"signage panels {panel:.0%}")
    if empty: s -= .35; why.append(f"empty surface in the middle {flat_core:.0%}")
    if blur: s -= .4; why.append("blurred")
    return round(max(0.0, min(1.0, s)), 3), why
MIN_SCORE = 0.45
if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]: print(p, *score(p))
