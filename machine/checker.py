#!/usr/bin/env python3
"""Wisdrop checker: playbook rules as code. usage: checker.py <episode_dir> <target_state>
Prints PASS/FAIL lines per rule, writes qa/check_<state>.json, exits 1 on any FAIL. Rules live in playbook/rules.yaml."""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import REPO

EP, TARGET = sys.argv[1], sys.argv[2]
RULES = {}
try:
    import yaml  # optional; falls back to defaults below
    RULES = yaml.safe_load(open(os.path.join(REPO, 'playbook', 'rules.yaml'))) or {}
except Exception:
    pass
R = {'min_minutes': 6, 'max_minutes': 20, 'wpm': 165, 'presets': ['facts', 'dry', 'tension', 'question', 'beat'],
     'banned_words': ['allegedly proven', 'guaranteed returns'], 'real_people': [], 'min_research_sources': 8}
R.update(RULES)
results = []


def rule(name, ok, detail=''):
    results.append({'rule': name, 'ok': bool(ok), 'detail': detail})
    print(f"{'PASS' if ok else 'FAIL'}: {name}" + (f' ({detail})' if detail and not ok else ''), flush=True)


def read(f):
    p = os.path.join(EP, f)
    return open(p, encoding='utf-8').read() if os.path.exists(p) else ''


def urls(t):
    return re.findall(r'https?://[^\s)|>\]]+', t)


def stage_at_least(s):
    order = ['research_ok', 'cast_approved', 'script_approved', 'images_ok', 'voice_ok', 'render_ok', 'packaged', 'final_approved', 'released']
    return order.index(TARGET) >= order.index(s)


research = read('research.md')
if stage_at_least('research_ok'):
    u = set(urls(research))
    rule('research has enough distinct sources', len(u) >= R['min_research_sources'], f'{len(u)} < {R["min_research_sources"]}')
    rows = [l for l in research.splitlines() if l.startswith('|') and not set(l) <= set('|-: ')][1:]
    keyrows = [l for l in rows if l.rstrip('| ').lower().endswith('yes')]
    bad = [l[:60] for l in keyrows if len(urls(l)) < 2]
    rule('every KEY number has two sources', not bad, '; '.join(bad[:3]))
    bad1 = [l[:60] for l in rows if re.search(r'\d', l) and not urls(l) and 'figure' not in l.lower()]
    rule('every number row has a source', not bad1, '; '.join(bad1[:3]))

if stage_at_least('cast_approved'):
    cast = read('cast.md').lower()
    hits = [p for p in R['real_people'] if p.lower() in cast]
    rule('no real person in cast (never drawn)', not hits, ', '.join(hits))

if stage_at_least('script_approved'):
    try:
        lines = json.load(open(os.path.join(EP, 'lines.json')))
    except Exception as e:
        lines = []; rule('lines.json is valid', False, str(e))
    if lines:
        words = sum(len(L.get('say', L['text']).split()) for L in lines)
        mins = words / R['wpm'] + sum(L.get('gap', 0.3) for L in lines) / 60
        rule(f'length within {R["min_minutes"]}-{R["max_minutes"]} min', R['min_minutes'] <= mins <= R['max_minutes'], f'{mins:.1f} min')
        rule('ids are 0..n-1 in order', [L['id'] for L in lines] == list(range(len(lines))))
        badp = [L['id'] for L in lines if L.get('preset') not in R['presets']]
        rule('every line has a valid preset', not badp, str(badp[:10]))
        novis = [L['id'] for L in lines if not str(L.get('visual', '')).strip()]
        rule('Rule 1: every line names its visual', not novis, f'lines {novis[:10]}')
        nums = [L['id'] for L in lines if re.search(r'\d|million|billion|thousand|percent', L['text'], re.I) and not L.get('src')]
        rule('every number line cites a research source', not nums, f'lines {nums[:10]}')
        txt = ' '.join(L['text'].lower() for L in lines)
        bw = [w for w in R['banned_words'] if w in txt]
        rule('no banned phrasing', not bw, ', '.join(bw))

if stage_at_least('images_ok'):
    imgs = [f for sub in ('img/plates', 'img/cut') for f in os.listdir(os.path.join(EP, sub))] if os.path.isdir(os.path.join(EP, 'img')) else []
    rule('images exist', len(imgs) > 0, 'no images in img/plates or img/cut')

if stage_at_least('voice_ok'):
    qc = json.load(open(os.path.join(EP, 'vo_qc.json'))) if os.path.exists(os.path.join(EP, 'vo_qc.json')) else {}
    n = len(json.load(open(os.path.join(EP, 'lines.json'))))
    passed = [k for k, v in qc.items() if v.get('status') == 'pass']
    review = [k for k, v in qc.items() if v.get('status') == 'review']
    rule('every voice line made', len(qc) == n, f'{len(qc)}/{n}')
    rule('no voice line left for human review', not review, f'lines {review[:10]}')

if stage_at_least('render_ok'):
    v = os.path.join(EP, 'out', 'video.mp4')
    rule('final video exists', os.path.exists(v))

if stage_at_least('packaged'):
    pk = os.path.join(EP, 'package')
    have = set(os.listdir(pk)) if os.path.isdir(pk) else set()
    for f in ['titles.md', 'description.md', 'tags.txt']:
        rule(f'package has {f}', f in have)
    rule('package has 2+ thumbnail versions', len([f for f in have if f.startswith('thumb_')]) >= 2)

os.makedirs(os.path.join(EP, 'qa'), exist_ok=True)
json.dump(results, open(os.path.join(EP, 'qa', f'check_{TARGET}.json'), 'w'), indent=1)
fails = [r for r in results if not r['ok']]
print(f"{'OK' if not fails else 'FAIL'}: {len(results) - len(fails)}/{len(results)} rules passed for {TARGET}")
sys.exit(1 if fails else 0)
