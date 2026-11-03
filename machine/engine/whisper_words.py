"""Word timing for captions (Wisdrop, number-aware). usage: python whisper_words.py <episode_dir> -> <ep>/words.json
Like the kit version, but Whisper's digits ("25, 2017", "$4 billion") are expanded to words before aligning, so lines with
numbers still get exact timing instead of the character-length fallback."""
import json, sys, os, subprocess, re, difflib
import numpy as np
from faster_whisper import WhisperModel
from num2words import num2words
ep = sys.argv[1]
TL = json.load(open(os.path.join(ep, 'timeline.json')))
def toks(s):
    s = s.lower().replace('%', ' percent')
    if s.strip().startswith('$'): s = s.replace('$', '') + ' dollars'
    s = re.sub(r'(\d+)(st|nd|rd|th)\b', lambda g: num2words(int(g.group(1)), to='ordinal'), s)
    s = re.sub(r'\d[\d,]*(\.\d+)?', lambda g: num2words(float(g.group(0).replace(',', '')) if '.' in g.group(0) else int(g.group(0).replace(',', ''))), s)
    s = s.replace('a.i.', 'ai').replace('f.b.i.', 'fbi').replace("'s", 's')
    s = re.sub(r"[^a-z ]", ' ', s.replace('-', ' '))
    return s.split()
model = WhisperModel(os.environ.get('WHISPER_MODEL', 'small.en'), device='cpu', compute_type='int8')
pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(ep, 'vo.wav'), '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True).stdout
audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
segs, _ = model.transcribe(audio, word_timestamps=True, language='en', vad_filter=False)
WW = [(w.start, w.end, w.word) for s in segs for w in s.words]
out = []
for s in TL['segs']:
    words = s['text'].replace('...', '…').split()
    hw = [w for w in WW if s['start'] - .2 <= (w[0] + w[1]) / 2 <= s['end'] + .05]
    ht = []   # whisper tokens with evenly split times
    for a, b, w in hw:
        tk = toks(w) or ['_']
        for j in range(len(tk)): ht.append((tk[j], a + (b - a) * j / len(tk), a + (b - a) * (j + 1) / len(tk)))
    st = [toks(w) or ['_'] for w in words]
    flat = [(wi, t) for wi, x in enumerate(st) for t in x]
    tim_tok = [None] * len(flat)
    sm = difflib.SequenceMatcher(None, [t for _, t in flat], [t for t, _, _ in ht], autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): tim_tok[blk.a + k] = ht[blk.b + k][1:]
    matched = sum(x is not None for x in tim_tok)
    # interpolate unmatched tokens between anchors (line start/end as outer anchors)
    anchors = [(-1, (s['start'], s['start']))] + [(k, v) for k, v in enumerate(tim_tok) if v] + [(len(flat), (s['end'], s['end']))]
    for (k0, v0), (k1, v1) in zip(anchors, anchors[1:]):
        gap = k1 - k0
        for k in range(k0 + 1, k1):
            a = v0[1] + (v1[0] - v0[1]) * (k - k0 - 1) / max(1, gap - 1 + 1); b = v0[1] + (v1[0] - v0[1]) * (k - k0) / gap
            tim_tok[k] = (a, b)
    tim = []
    for wi in range(len(words)):
        ks = [k for k, (w_, _) in enumerate(flat) if w_ == wi]
        tim.append((max(tim_tok[ks[0]][0], s['start']), min(tim_tok[ks[-1]][1], s['end'])))
    exact = matched >= .7 * len(flat)
    out.append({'i': s['i'], 'words': [[round(a, 3), round(b, 3), w] for (a, b), w in zip(tim, words)], 'exact': exact})
json.dump(out, open(os.path.join(ep, 'words.json'), 'w'), indent=1)
print('lines', len(out), 'exact', sum(o['exact'] for o in out), 'inexact ids', [o['i'] for o in out if not o['exact']])
