# WISDROP OPERATOR FILE (read first, every time) - machine v3

Faceless YouTube channel "Money crimes behind the hype": one real financial fraud per episode, 5 parts,
8-12 min, collage-style code graphics + real photos + a few AI pictures, one fixed narrator voice.
You drive. The machine checks. The owner approves. You never skip a gate.

## Read in this order
1. `playbook/rules.yaml` (hard rules the checker enforces) and `playbook/WISDROP_PLAYBOOK.md` (creative rules).
2. `docs/OPERATOR_GUIDE.md` (how to run everything; the PDF copy is for the owner).
3. `docs/SHOTS.md` (every shot type and the 20 templates) and `docs/EDITING_CRAFT.md` (editing rules, cited).
4. `library/library.json` (cast, sets, look "v3") and `episodes/ep01-onecoin/` (worked example).

## Never bend
- Never draw a real person. Real people appear only as names on cards, documents, headlines.
- Every number on screen or in narration has a source in research.md (two for key numbers).
- Owner approves cast + script (PR `gate/<ep>/script`) before any picture or voice, and the final video
  + thumbnail (FINAL REVIEW PR) before upload. Never approve for the owner.
- No secrets in files, logs or chat (keys live in GitHub secrets: MODAL_TOKEN_ID, MODAL_TOKEN_SECRET).
- Frugal Modal spend: test first (`test_lines=0-3`, `preview_seconds=15`), keep `max_gpu_seconds` low,
  at most 4-6 AI pictures per episode, redo only what failed.
- Words on screen are drawn by code. Generated pictures never contain text.
- Never change the voice reference, fonts or the v3 board palette. No logo sting.

## The loop
`python machine/wis.py new|status|check|advance` -> research.md -> cast.md + script.md + lines.json ->
shots.json -> `python machine/craft_check.py <ep>` and `python machine/score_script.py <ep> --hooks`
must not FAIL -> owner script gate -> workflow **episode** (test, then full) -> FINAL REVIEW PR -> owner.

## Logs
Every tool prints PLAN / OK / WAIT / FAIL / REVIEW / COST lines. FAIL stops the run before money is spent.
REVIEW is for the owner and never blocks. Same error 3 times: stop, open issue `[blocked] <ep> <step>`.
