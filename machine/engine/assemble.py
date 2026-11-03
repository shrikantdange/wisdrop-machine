"""Join voiced lines into vo.wav + timeline.json (start/end per line, caption words).

  python assemble.py <ep_dir> <vo_index.json> <vo_dir> <out_dir>

vo_dir holds <hash>.wav and <hash>.json (the voice worker's cache). Caption words keep the
script's own spelling ("$4 billion") and take their timing from Whisper's word times,
spread over the span Whisper heard; with no word times they are spread by length.
"""
import json, os, sys, wave
import numpy as np

SR = 48000; LEAD_IN = 0.4; TAIL = 1.5


def read_wav(p):
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def trim(a, thr=0.01):
    idx = np.where(np.abs(a) > thr)[0]
    if not len(idx): return a, 0.0
    s0 = max(0, idx[0] - int(.03 * SR)); s1 = min(len(a), idx[-1] + int(.08 * SR)); return a[s0:s1], s0 / SR


def main(ep, index_p, vo_dir, out_dir):
    lines = {L["id"]: L for L in json.load(open(os.path.join(ep, "lines.json")))}
    idx = json.load(open(index_p)); cur = LEAD_IN; parts = [np.zeros(int(LEAD_IN * SR), np.float32)]; segs = []
    for e in idx:
        a, off = trim(read_wav(os.path.join(vo_dir, e["hash"] + ".wav")))
        qc = json.load(open(os.path.join(vo_dir, e["hash"] + ".json"))) if os.path.exists(os.path.join(vo_dir, e["hash"] + ".json")) else {}
        dur = len(a) / SR; text = lines[e["id"]]["text"]; ws = text.split()
        hw = qc.get("words") or []
        s0 = (hw[0][0] - off) if hw else 0.0; s1 = (hw[-1][1] - off) if hw else dur
        s0 = max(0.0, s0); s1 = min(dur, max(s0 + .2, s1)); tot = sum(len(w) + 2 for w in ws) or 1; c = s0; words = []
        for w in ws:
            dd = (s1 - s0) * (len(w) + 2) / tot; words.append([round(cur + c, 3), round(cur + c + dd, 3), w]); c += dd
        segs.append({"i": e["id"], "start": round(cur, 3), "end": round(cur + dur, 3), "text": text, "words": words})
        parts.append(a); gap = float(e.get("gap", lines[e["id"]].get("gap", .3)))
        parts.append(np.zeros(int(gap * SR), np.float32)); cur += dur + gap
    parts.append(np.zeros(int(TAIL * SR), np.float32)); vo = np.concatenate(parts)
    os.makedirs(out_dir, exist_ok=True)
    with wave.open(os.path.join(out_dir, "vo.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(vo, -1, 1) * 32767).astype(np.int16).tobytes())
    json.dump({"dur": round(len(vo) / SR, 3), "segs": segs}, open(os.path.join(out_dir, "timeline.json"), "w"), indent=1)
    print(f"OK assembled {len(segs)} lines, {len(vo) / SR / 60:.2f} min")


if __name__ == "__main__":
    main(*sys.argv[1:5])
