"""One place that knows where things live. Works on any worker (Hark sandbox, Mac mini, Modal) via env vars."""
import os
REPO = os.environ.get('WIS_REPO') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(REPO, 'kit')
ENGINE = os.path.join(REPO, 'machine', 'engine')
EPISODES = os.path.join(REPO, 'episodes')
CACHE = os.environ.get('WIS_CACHE', os.path.expanduser('~/.wisdrop'))   # models, venvs: never committed
FP16 = os.environ.get('WIS_FP16', os.path.join(CACHE, 'cb_fp16'))
