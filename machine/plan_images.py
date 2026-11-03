#!/usr/bin/env python3
"""Turn an episode's shots.json into the image job list, using the channel library.

  python machine/plan_images.py episodes/ep01-onecoin      -> episodes/ep01-onecoin/img_jobs.json

Only what the shots use is listed. Pictures already made for any episode have the same
hash and come straight from the cache, so the repertory cast and sets cost nothing twice.
Prints OK / FAIL lines.
"""
import json, os, sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def plan(ep_dir):
    lib = json.load(open(os.path.join(REPO, "library", "library.json")))
    shots = json.load(open(os.path.join(ep_dir, "shots.json")))["shots"]
    tl = os.environ.get("WIS_TEST_LINES", "").strip()     # test runs: plan only pictures the voiced lines show
    if tl:
        ids = set()
        for part in tl.split(","):
            a, _, b = part.partition("-"); ids |= set(range(int(a), int(b or a) + 1))
        shots = [x for x in shots if x["at"] in ids]
    T = lib["templates"]; jobs = {}; errs = []
    for s in shots:
        if s["type"] not in ("scene", "screen"):
            continue
        st = s.get("set")
        if st and not lib["sets"].get(st, {}).get("code"):
            if st not in lib["sets"]:
                errs.append(f"line {s['at']}: set '{st}' not in library.json (add it there first)"); continue
            tm = s.get("time", "night")
            if tm not in lib["time_light"]:
                errs.append(f"line {s['at']}: time '{tm}' not in library time_light"); continue
            S = lib["sets"][st]; name = f"set_{st}__{tm}"
            jobs.setdefault(name, {"name": name, "lib": f"sets/{st}", "seed": S["seed"],
                                   "prompt": T["set"].format(light=lib["time_light"][tm], base=S["base"])})
        for c in s.get("cast", []):
            who, pose = c["who"], c.get("pose", "front_neutral")
            if who not in lib["cast"]:
                errs.append(f"line {s['at']}: cast '{who}' not in library.json"); continue
            C = lib["cast"][who]; m = f"char_{who}__master"
            jobs.setdefault(m, {"name": m, "lib": f"cast/{who}", "seed": C["seed"], "w": 1328, "h": 1328,
                                "people": True, "cutout": True, "prompt": T["master"].format(look=C["look"])})
            if pose == "master":
                continue
            if pose not in C["poses"]:
                errs.append(f"line {s['at']}: pose '{pose}' for {who} not in library.json"); continue
            if s["type"] == "scene" and s.get("compose", True) and not s.get("cutout"):
                continue
            n = f"char_{who}__{pose}"
            jobs.setdefault(n, {"name": n, "lib": f"cast/{who}", "mode": "edit", "refs_from": [m], "seed": C["seed"] + 1,
                                "people": True, "cutout": True, "prompt": T["pose"].format(pose=C["poses"][pose])})
        # composed shot: the model paints the cast INTO the set (one light, real shadows, same identity)
        cast = s.get("cast", [])
        if s["type"] == "scene" and cast and st and not lib["sets"].get(st, {}).get("code") and s.get("compose", True) and not errs:
            tm = s.get("time", "night"); setn = f"set_{st}__{tm}"
            acts = []
            for k, c in enumerate(cast[:2]):
                C = lib["cast"][c["who"]]; pose = C["poses"].get(c.get("pose", "front_neutral"), c.get("pose", ""))
                where = "on the left" if c.get("x", .5) < .4 else "on the right" if c.get("x", .5) > .6 else "in the middle"
                acts.append(f"the person from image {k + 2} {where} of the frame, {pose.replace('on an invisible stool', 'on a stool').replace('on an invisible chair', 'on a chair').replace(' (no machine drawn)', ' at the sewing machine').replace(' (no laptop drawn)', ' at the laptop').replace(' (no keyboard drawn)', ' at the desk')}")
            n = "shot_" + st + "__" + tm + "__" + "+".join(f"{c['who']}-{c.get('pose', 'front_neutral')}" for c in cast[:2])
            jobs.setdefault(n, {"name": n, "lib": f"shots/{st}", "mode": "edit", "seed": lib["sets"][st]["seed"] + 7,
                                "people": True, "w": 1664, "h": 928, "refs_from": [setn] + [f"char_{c['who']}__master" for c in cast[:2]],
                                "prompt": T["compose"].format(acts="; ".join(acts))})
            s["_shot"] = n
    # masters first so poses can reference them
    out = sorted(jobs.values(), key=lambda j: (j.get("mode") == "edit", j["name"]))
    return out, errs


if __name__ == "__main__":
    d = os.path.abspath(sys.argv[1]); jobs, errs = plan(d)
    for e in errs:
        print("FAIL:", e)
    if errs:
        sys.exit(2)
    json.dump(jobs, open(os.path.join(d, "img_jobs.json"), "w"), indent=1)
    print(f"OK: {len(jobs)} pictures planned ({sum(1 for j in jobs if j.get('mode') == 'edit')} poses) -> img_jobs.json")
