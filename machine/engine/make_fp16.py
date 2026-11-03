# One-time: store Chatterbox weights as fp16 on disk (half the bytes to read from the network drive). Upcast to fp32 on load.
import glob, json, struct, torch, shutil, os, sys
sys.argv = ['x', '/tmp/none']
src = open(__import__('os').path.join(__import__('os').path.dirname(__file__),'vo_runner.py')).read(); exec(src[src.index("def _load_nommap"):src.index("_ct.load_file")])
from safetensors.torch import save_file
snap = glob.glob(__import__('os').environ.get('HF_HOME', __import__('os').path.expanduser('~/.cache/huggingface'))+'/hub/models--ResembleAI--chatterbox/snapshots/*/')[0]; out = __import__('os').environ.get('WIS_FP16', __import__('os').path.expanduser('~/.wisdrop/cb_fp16'))+'/'
for f in os.listdir(snap):
    p = os.path.join(snap, f)
    if f.endswith('.safetensors'):
        d = _load_nommap(p); d = {k: (v.half() if v.dtype == torch.float32 else v.clone()).contiguous() for k, v in d.items()}
        save_file(d, out + f, metadata={'fp16': '1'}); del d; print(f, flush=True)
    else: shutil.copy(p, out + f)
