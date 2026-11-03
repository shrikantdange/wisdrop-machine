"""Wisdrop motion tokens (docs/AI_MOTION_CRAFT.md, W5): one module for easing, durations, seeding,
stepped paper motion, camera push and colour maths. Renderer and checks import from here.

Owner decisions 2026-11-03: punch-in only on stamps; headline >= 76 px; music 22 dB under voice
(alert under 8 dB); no coin/ding sounds; when two rules conflict the simpler option wins.
"""
import math, zlib

FPS = 30
HEADLINE_MIN_PX = 76        # AMC-L2 (owner): headline role never smaller
BODY_MIN_PX = 36            # AMC-L2
TEXT_FLOOR_PX = 25          # AMC-L2: anything smaller fails
PUSH_RATE = 0.012           # AMC-V2: +1.2 % scale per second on any hold
PUSH_CAP = 0.06             # AMC-V2: never more than +6 %
STEP_FRAMES = 2             # AMC-T6: paper elements on twos (15 fps inside 30 fps)
ACCENT_MAX = 0.15           # AMC-C2: accent colour on at most 15 % of the frame
CONTRAST_BODY = 4.5         # AMC-C3
CONTRAST_LARGE = 3.0        # AMC-C3 (>= 76 px)
MUSIC_UNDER_VOICE_DB = 22   # AMC-S3 (owner): target bed level under the voice
MUSIC_BAND_DB = (18, 25)    # AMC-S3 QA band
VOICE_OVER_BED_MIN_DB = 8   # AMC-S3 (owner): alert below this on any line
SYNC_MAX_FRAMES = 2         # AMC-S5: a sound never trails its picture by more than 2 frames
BANNED_SFX = {"coin", "coins", "coindrop", "ding", "sparkle", "cash", "register"}   # AMC-S2 (owner)

# ---------------- seeding (AMC-W1): every pixel = f(episode, element, frame) ----------------
def seed(*parts):
    """Stable 32-bit seed from any parts. Never use Python's hash() (salted per process)."""
    return zlib.crc32(":".join(str(p) for p in parts).encode())

def rng(*parts):
    import numpy as np
    return np.random.default_rng(seed(*parts))

# ---------------- easing tokens (AMC-M1) ----------------
def bezier(x1, y1, x2, y2):
    """CSS cubic-bezier(x1, y1, x2, y2) as a function of t in [0, 1]."""
    def f(t):
        t = min(1.0, max(0.0, t))
        if t in (0.0, 1.0): return t
        u = t
        for _ in range(8):      # Newton on x(u) = t
            x = 3 * (1 - u) ** 2 * u * x1 + 3 * (1 - u) * u * u * x2 + u ** 3 - t
            dx = 3 * (1 - u) ** 2 * x1 + 6 * (1 - u) * u * (x2 - x1) + 3 * u * u * (1 - x2)
            if abs(dx) < 1e-6: break
            u = min(1.0, max(0.0, u - x / dx))
        return 3 * (1 - u) ** 2 * u * y1 + 3 * (1 - u) * u * u * y2 + u ** 3
    return f

def smooth(t):              # 3b1b smooth: zero 1st and 2nd derivative at both ends
    t = min(1.0, max(0.0, t)); return t ** 3 * (10 - 15 * t + 6 * t * t)

def sine_inout(t):
    t = min(1.0, max(0.0, t)); return 0.5 - 0.5 * math.cos(math.pi * t)

def steps(n):
    return lambda t: math.floor(min(1.0, max(0.0, t)) * n) / n

EASE = {
    "premium": bezier(0.16, 1, 0.3, 1),        # entrances, reveals, snap beats
    "exit": bezier(0.3, 0, 0.8, 0.15),         # exits, 20-30 % shorter than the entrance
    "camera": bezier(0.65, 0, 0.35, 1),        # moves between two rests
    "standard": bezier(0.2, 0, 0, 1),          # UI micro-motion (phone screens)
    "emph_in": bezier(0.05, 0.7, 0.1, 1),      # notification banner enters (~400 ms)
    "emph_out": bezier(0.3, 0, 0.8, 0.15),     # notification banner leaves (~200 ms)
    "ambient": sine_inout,                     # Ken Burns / drift
    "smooth": smooth,
}
DUR = {"ui": 0.2, "enter": 0.45, "exit": 0.32, "move": 0.65, "banner_in": 0.4, "banner_out": 0.2,
       "snap": 8 / FPS, "countup": 1.2, "read_min": 1.5}

def ease(name, t): return EASE[name](t)

# ---------------- stepped paper motion (AMC-T6) ----------------
def on_twos(t, hold=STEP_FRAMES):
    """Quantise time so a paper element holds each pose `hold` frames. Camera and captions stay smooth."""
    f = math.floor(t * FPS + 1e-6); return (f - f % hold) / FPS

# ---------------- camera (AMC-V1/V2/V3) ----------------
def hold_push(t, rate=PUSH_RATE, cap=PUSH_CAP):
    """Slow anti-freeze push: +1.2 %/s, capped at +6 %, eased into its cap."""
    lin = rate * max(0.0, t)
    return 1.0 + (lin if lin < cap * .7 else cap * .7 + (cap * .3) * (1 - math.exp(-(lin - cap * .7) / (cap * .3))))

def punch(tt, amount=0.15, dur=0.3):
    """Stamp-only punch-in (owner): 1.0 -> 1+amount over dur on 'premium', stepped on twos."""
    if tt <= 0: return 1.0
    return 1.0 + amount * EASE["premium"](on_twos(tt) / dur)

# ---------------- colour maths (AMC-C2/C3) ----------------
def _lin(c):
    c = c / 255.0; return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def luminance(rgb): r, g, b = (_lin(x) for x in rgb[:3]); return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True); return (la + 0.05) / (lb + 0.05)
