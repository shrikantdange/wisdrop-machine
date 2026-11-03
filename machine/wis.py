#!/usr/bin/env python3
"""wis: the one command any operator AI uses to drive the Wisdrop machine.

  wis new <slug> "<case title>"      create episodes/epNN-<slug>/ with state.json at 'draft'
  wis status [ep]                    show state of one or all episodes
  wis check <ep>                     run the checker (rules-as-code) on the episode's current stage
  wis advance <ep> <state>           move to the next state (refused if illegal or checks fail)
  wis reach <ep> <state>             same, but OK if already there (CI uses this)
  wis approve <ep> <gate>            owner gates only: cast | script | final  (normally done by PR merge in CI)
  wis voice <ep>                     make / resume the voiceover on this worker
  wis render <ep>                    render + mix + master (needs voice_ok)
  wis package <ep>                   titles, thumbnail versions, description, tags -> package/

Every command prints one line starting with OK / FAIL / WAIT / NEXT so an AI can read it without guessing.
"""
import os, sys, json, re, datetime, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import REPO, EPISODES, ENGINE

STATES = ['draft', 'research_ok', 'cast_approved', 'script_approved', 'images_ok',
          'voice_ok', 'render_ok', 'packaged', 'final_approved', 'released']
OWNER_GATES = {'cast_approved': 'cast', 'script_approved': 'script', 'final_approved': 'final'}


def say(kind, msg):
    print(f'{kind}: {msg}', flush=True)


def ep_dir(ep):
    if os.path.isdir(ep):
        return os.path.abspath(ep)
    m = [d for d in sorted(os.listdir(EPISODES)) if d == ep or d.startswith(ep + '-')]
    if not m:
        say('FAIL', f'no episode {ep}'); sys.exit(2)
    return os.path.join(EPISODES, m[0])


def load_state(d):
    p = os.path.join(d, 'state.json')
    return json.load(open(p)) if os.path.exists(p) else {'state': 'draft', 'history': [], 'approvals': {}}


def save_state(d, st):
    p = os.path.join(d, 'state.json'); tmp = p + '.tmp'
    json.dump(st, open(tmp, 'w'), indent=1); os.replace(tmp, p)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def cmd_new(slug, title):
    os.makedirs(EPISODES, exist_ok=True)
    nums = [int(m.group(1)) for d in os.listdir(EPISODES) if (m := re.match(r'ep(\d+)-', d))]
    n = max(nums + [0]) + 1
    d = os.path.join(EPISODES, f'ep{n:02d}-{slug}')
    for sub in ['img/plates', 'img/cut', 'vo', 'out', 'package', 'qa']:
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    tpl = os.path.join(REPO, 'machine', 'templates')
    for f in os.listdir(tpl):
        dst = os.path.join(d, f)
        if not os.path.exists(dst):
            open(dst, 'w').write(open(os.path.join(tpl, f)).read().replace('{{TITLE}}', title))
    save_state(d, {'state': 'draft', 'title': title, 'created': now(), 'history': [], 'approvals': {}})
    say('OK', f'created {os.path.relpath(d, REPO)}'); say('NEXT', 'write research.md, then: wis check ' + os.path.basename(d))


def cmd_status(ep=None):
    ds = [ep_dir(ep)] if ep else [os.path.join(EPISODES, d) for d in sorted(os.listdir(EPISODES)) if os.path.isdir(os.path.join(EPISODES, d))]
    for d in ds:
        st = load_state(d)
        i = STATES.index(st['state']); nxt = STATES[i + 1] if i + 1 < len(STATES) else '-'
        who = 'OWNER' if nxt in OWNER_GATES else 'operator'
        say('OK', f"{os.path.basename(d)}: {st['state']} -> next {nxt} ({who})")


def run_checker(d, target):
    r = subprocess.run([sys.executable, os.path.join(REPO, 'machine', 'checker.py'), d, target])
    return r.returncode == 0


def cmd_advance(ep, target, owner=False):
    d = ep_dir(ep); st = load_state(d)
    if target not in STATES:
        say('FAIL', f'unknown state {target}'); sys.exit(2)
    cur = STATES.index(st['state']); want = STATES.index(target)
    if want != cur + 1:
        say('FAIL', f"illegal jump {st['state']} -> {target}; next allowed is {STATES[min(cur + 1, len(STATES) - 1)]}"); sys.exit(2)
    if target in OWNER_GATES and not owner:
        say('WAIT', f'{target} needs the owner: open a PR; merging it is the approval'); sys.exit(5)
    if not run_checker(d, target):
        say('FAIL', 'checker refused; fix the items listed above'); sys.exit(1)
    st['history'].append({'from': st['state'], 'to': target, 'at': now()}); st['state'] = target
    if target in OWNER_GATES:
        st['approvals'][OWNER_GATES[target]] = now()
    save_state(d, st); say('OK', f'{os.path.basename(d)} is now {target}')


def cmd_voice(ep):
    d = ep_dir(ep); st = load_state(d)
    if STATES.index(st['state']) < STATES.index('images_ok'):
        say('FAIL', 'voice needs script_approved and images_ok first'); sys.exit(2)
    r = subprocess.run(['bash', os.path.join(ENGINE, 'run_vo.sh'), d] + sys.argv[3:])
    {0: lambda: say('OK', 'voice done; run: wis advance %s voice_ok' % ep),
     3: lambda: say('NEXT', 'voice partly done; run wis voice again'),
     4: lambda: say('WAIT', 'another heavy job is running; try again later')}.get(r.returncode, lambda: say('FAIL', f'voice exit {r.returncode}; read vo_run.log'))()
    sys.exit(r.returncode)


def cmd_render(ep):
    d = ep_dir(ep); st = load_state(d)
    if st['state'] != 'voice_ok':
        say('FAIL', 'render needs voice_ok'); sys.exit(2)
    for step in (['render.py', d, os.path.join(d, 'out', 'video.mp4')], ['mix.py', d]):
        r = subprocess.run([sys.executable, os.path.join(d, step[0])] + step[1:])
        if r.returncode:
            say('FAIL', f'{step[0]} failed'); sys.exit(1)
    say('OK', 'rendered; run: wis advance %s render_ok' % ep)


def main(a):
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return
    c = a[0]
    if c == 'new': cmd_new(a[1], a[2] if len(a) > 2 else a[1])
    elif c == 'status': cmd_status(a[1] if len(a) > 1 else None)
    elif c == 'check': sys.exit(0 if run_checker(ep_dir(a[1]), a[2] if len(a) > 2 else STATES[STATES.index(load_state(ep_dir(a[1]))['state']) + 1]) else 1)
    elif c == 'advance': cmd_advance(a[1], a[2])
    elif c == 'reach':     # idempotent advance: OK if already there or past it (used by CI)
        st = load_state(ep_dir(a[1]))['state']
        if STATES.index(st) >= STATES.index(a[2]): say('OK', f'already {st}')
        else: cmd_advance(a[1], a[2])
    elif c == 'approve': cmd_advance(a[1], {v: k for k, v in OWNER_GATES.items()}[a[2]], owner=os.environ.get('WIS_OWNER_APPROVAL') == '1')
    elif c == 'voice': cmd_voice(a[1])
    elif c == 'render': cmd_render(a[1])
    elif c == 'package': subprocess.run([sys.executable, os.path.join(REPO, 'machine', 'package.py'), ep_dir(a[1])])
    else: say('FAIL', f'unknown command {c}'); sys.exit(2)


if __name__ == '__main__':
    main(sys.argv[1:])
