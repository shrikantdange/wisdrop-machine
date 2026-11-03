"""Wisdrop stable voice runner (replaces gen_vo.py for long episodes).
usage: python vo_runner.py <episode_dir> [--budget 1080] [--takes 3]
- Time-boxed: stops cleanly before --budget seconds so no job is ever killed mid-line. Exit 0 = all lines done, 3 = more to do (just run again).
- Resumable: a line is skipped once vo/lNN.wav exists AND vo_qc.json marks it pass (or 'review' after max takes).
- Atomic writes: audio goes to a .tmp file and is renamed only after QC, so a crash never leaves a half-written wav.
- Auto QC on every take: Whisper transcript vs script (word error rate), duration vs expected pace, clipping, long internal silences.
  Failing takes are regenerated with a new seed, best take kept; after --takes failures the line is flagged 'review' for a human listen.
- Same voice every time: voice/ref_michael.wav, presets from the playbook. Speaker conditioning computed once per run.
"""
import sys as _s, os as _o; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..")); from paths import KIT as _KIT, ENGINE as _ENG, FP16 as _FP16
import os, sys, json, time, re, argparse, gc
import numpy as np, torch, torchaudio as ta
from num2words import num2words
ap = argparse.ArgumentParser(); ap.add_argument('ep'); ap.add_argument('--budget', type=float, default=1080); ap.add_argument('--takes', type=int, default=3)
ap.add_argument('--only', default='')  # comma list of ids to force-regenerate
A = ap.parse_args(); T0 = time.time(); EP = A.ep
KIT = _KIT; REF = f'{KIT}/voice/ref_michael.wav'
PRESETS = {"facts": (0.55, 0.5), "dry": (0.6, 0.4), "tension": (0.7, 0.35), "question": (0.8, 0.3), "beat": (0.9, 0.25)}
os.makedirs(f'{EP}/vo', exist_ok=True)
LINES = json.load(open(f'{EP}/lines.json')); QCF = f'{EP}/vo_qc.json'
QC = json.load(open(QCF)) if os.path.exists(QCF) else {}
force = {int(x) for x in A.only.split(',') if x.strip()}
for i in force: QC.pop(str(i), None)
def done(L):
    q = QC.get(str(L['id'])); return q and q['status'] in ('pass', 'review') and os.path.exists(f"{EP}/vo/l{L['id']:02d}.wav")
todo = [L for L in LINES if not done(L)]
print(f'{len(todo)} of {len(LINES)} lines to make', flush=True)
if not todo: sys.exit(0)

torch.set_num_threads(max(1, os.cpu_count() or 2))
DEV = os.environ.get('WIS_DEVICE') or ('cuda' if torch.cuda.is_available() else ('mps' if getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available() else 'cpu'))
def _trim():
    try:
        import ctypes; ctypes.CDLL('libc.so.6').malloc_trim(0)
    except Exception: pass
import chatterbox.tts as _ct, safetensors.torch as _st
def _load_nommap(path, device='cpu'):
    # Stream weights tensor-by-tensor with plain reads: no mmap (mmap over the /workspace network drive threw 'Bus error')
    # and no whole-file copy (that doubled RAM and got OOM-killed). Peak RAM = model + one tensor.
    import struct
    DT = {'F32': torch.float32, 'F16': torch.float16, 'BF16': torch.bfloat16, 'I64': torch.int64, 'I32': torch.int32,
          'I16': torch.int16, 'I8': torch.int8, 'U8': torch.uint8, 'BOOL': torch.bool, 'F64': torch.float64}
    out = {}
    with open(path, 'rb') as f:
        n = struct.unpack('<Q', f.read(8))[0]; hdr = json.loads(f.read(n)); base = 8 + n
        for k, v in sorted(((k, v) for k, v in hdr.items() if k != '__metadata__'), key=lambda kv: kv[1]['data_offsets'][0]):
            a, b = v['data_offsets']; f.seek(base + a); buf = bytearray(f.read(b - a))
            t = torch.frombuffer(buf, dtype=DT[v['dtype']]) if b > a else torch.empty(0, dtype=DT[v['dtype']])
            t = t.reshape(v['shape']); out[k] = t.float() if v['dtype'] == 'F16' else t
    return out
_ct.load_file = _load_nommap
from chatterbox.tts import ChatterboxTTS
from faster_whisper import WhisperModel
FP16 = _FP16
m = ChatterboxTTS.from_local(FP16, device=DEV) if os.path.exists(FP16 + '/t3_cfg.safetensors') else ChatterboxTTS.from_pretrained(device=DEV)
gc.collect(); _trim()   # hand freed load buffers back to the OS
m.prepare_conditionals(REF, exaggeration=0.55)   # THE WISDROP VOICE: ref_michael.wav (generate() then only adjusts exaggeration per preset)
assert m.conds is not None, 'voice reference not loaded'
wm = WhisperModel('small.en', device='cuda' if DEV == 'cuda' else 'cpu', compute_type='float16' if DEV == 'cuda' else 'int8')
import resource
def rss():
    try: return round(int(open('/proc/self/statm').read().split()[1]) * 4096 / 2**30, 2)
    except Exception: return -1
def avail():
    if not os.path.exists('/proc/meminfo'): return -1
    for l in open('/proc/meminfo'):
        if l.startswith(('MemAvailable', 'MemFree')): return round(int(l.split()[1]) / 2**20, 2)
print('models loaded', round(time.time() - T0), 's  rss', rss(), 'GB  free', avail(), 'GB', flush=True)

def norm(s):
    s = s.lower().replace('-', ' ').replace('%', ' percent').replace('$', ' dollars ')
    s = re.sub(r'(\d+)(st|nd|rd|th)\b', lambda g: num2words(int(g.group(1)), to='ordinal'), s)
    s = re.sub(r'\d[\d,]*(\.\d+)?', lambda g: num2words(float(g.group(0).replace(',', '')) if '.' in g.group(0) else int(g.group(0).replace(',', ''))), s)
    s = s.replace('-', ' ').replace('a.i.', 'ai').replace('f.b.i.', 'fbi')
    s = re.sub(r"[^a-z' ]", ' ', s); s = s.replace("'s", 's')
    return s.split()
def wer(ref, hyp):
    r, h = norm(ref), norm(hyp); d = np.arange(len(h) + 1)
    for i in range(1, len(r) + 1):
        p = d.copy(); d[0] = i
        for j in range(1, len(h) + 1): d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (r[i - 1] != h[j - 1]))
    return d[len(h)] / max(1, len(r))
def qc(w, sr, L):
    w = w.cpu(); a = w.squeeze().numpy(); dur = len(a) / sr
    words = len(L['text'].split()); exp = words / 2.75   # ~165 WPM
    a16 = ta.functional.resample(w, sr, 16000).squeeze().numpy().astype(np.float32)
    segs, _ = wm.transcribe(a16, language='en', beam_size=5); heard = ''.join(s.text for s in segs).strip()
    e = wer(L['text'], heard)
    env = np.convolve(np.abs(a), np.ones(int(sr * .02)) / int(sr * .02), 'same'); thr = env.max() * .03
    sil = env < thr; core = sil[np.argmax(~sil):len(sil) - np.argmax(~sil[::-1])]
    run = mx = 0
    for s in core:
        run = run + 1 if s else 0; mx = max(mx, run)
    gap = mx / sr; clip = float(np.mean(np.abs(a) > .99))
    issues = []
    if e > .12: issues.append(f'wer {e:.2f}')
    if dur > max(1.6, exp * 1.8) + .6: issues.append(f'too long {dur:.1f}s')
    if dur < exp * .45: issues.append(f'too short {dur:.1f}s')
    if gap > 1.0: issues.append(f'silence {gap:.1f}s')
    if clip > .001: issues.append('clipping')
    score = e + max(0, gap - 1) + (1 if 'too long' in ' '.join(issues) else 0)
    return {'heard': heard, 'wer': round(e, 3), 'dur': round(dur, 2), 'gap': round(gap, 2), 'issues': issues, 'score': round(score, 3)}

avg = 90.0; n = 0
for L in todo:
    left = A.budget - (time.time() - T0)
    if left < avg * 1.6 + 20: print('budget reached, exiting cleanly', flush=True); json.dump(QC, open(QCF, 'w'), indent=1); sys.exit(3)
    ex, cfg = PRESETS[L.get('preset', 'facts')]; best = None
    for k in range(A.takes):
        t = time.time(); torch.manual_seed(1000 + L['id'] * 17 + k)
        with torch.inference_mode(): w = m.generate(L.get('say', L['text']), exaggeration=ex, cfg_weight=cfg)
        r = qc(w, m.sr, L); r['take'] = k; r['secs'] = round(time.time() - t)
        print(L['id'], L.get('preset'), 'take', k, r['secs'], 's', r['dur'], 's audio', 'OK' if not r['issues'] else r['issues'], '| rss', rss(), 'free', avail(), '|', r['heard'], flush=True)
        if best is None or r['score'] < best[1]['score']: best = (w, r)
        avg = (avg * n + r['secs']) / (n + 1); n += 1
        if not r['issues']: break
        if A.budget - (time.time() - T0) < avg + 20: break
        del w; gc.collect(); _trim()
    w, r = best; f = f"{EP}/vo/l{L['id']:02d}.wav"
    ta.save(f + '.tmp.wav', w.cpu(), m.sr); os.replace(f + '.tmp.wav', f)
    r['status'] = 'pass' if not r['issues'] else 'review'; QC[str(L['id'])] = r
    json.dump(QC, open(QCF, 'w'), indent=1); gc.collect()
rev = [k for k, v in QC.items() if v['status'] == 'review']
print('ALL DONE. review lines:', rev or 'none', flush=True); sys.exit(0)
