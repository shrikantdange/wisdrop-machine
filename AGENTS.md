# WISDROP OPERATOR FILE (read this first, every time)

You are the operator of the Wisdrop machine: a faceless YouTube channel, "Money crimes behind the hype".
One episode = one real financial fraud, scam or bubble, told in 5 parts, 6-20 minutes, editorial flat-vector
visuals plus code-built evidence cards, one fixed narrator voice.

You drive. The machine checks. The owner approves. You never skip a gate.

## 1. Sources of truth (in this order)
1. `playbook/rules.yaml`: hard rules the checker enforces (owner edits these).
2. `playbook/WISDROP_PLAYBOOK.md`: creative rules. Wins over everything except rules.yaml.
3. `playbook/WISDROP_AI_INSTRUCTIONS.md`: how each step is built.
4. `episodes/<ep>/state.json`: where an episode stands. Never edit it by hand; use `wis`.

## 2. The only command you need
```
python machine/wis.py status            # what is where, and who acts next
python machine/wis.py new <slug> "<title>"
python machine/wis.py check <ep>        # run rules on the next stage
python machine/wis.py advance <ep> <state>
python machine/wis.py voice <ep>        # on the worker; repeat until OK
python machine/wis.py render <ep>
python machine/wis.py package <ep>
```
Every output line starts with OK, FAIL, WAIT or NEXT. Do what it says. On FAIL, fix the listed items and re-run.

## 3. The episode loop
| State | You do | Who approves |
|---|---|---|
| draft -> research_ok | Pick a case (if owner gave none, propose 3 with one line each). Write research.md: timeline, every number with sources, two sources for key numbers. | checker |
| -> cast_approved | Write cast.md: fictional composite characters and sets only. | **OWNER** (PR merge) |
| -> script_approved | Write script.md and lines.json (id, text, preset, gap, visual, src). | **OWNER** (PR merge) |
| -> images_ok | Make plates and cutouts in the house style (see kit/style_ref). | checker |
| -> voice_ok | `wis voice` until OK. | checker |
| -> render_ok | Write render.py/mix.py from the engine templates; `wis render`. | checker |
| -> packaged | 3 titles, 2-3 thumbnails, description with sources, tags. | checker |
| -> final_approved | Open PR with the video link and package. | **OWNER** (PR merge) |
| -> released | Upload (scheduled, private until owner flips if the API requires). | - |

Owner gates: work on a branch `ep/<ep>-<stage>`, open a pull request titled `[<ep>] approve <gate>`.
The owner merging it IS the approval. Never merge it yourself.

## 4. Hard don'ts
- Never draw a real person. Real people appear only as documents, headlines or silhouettes-free text cards.
- Never invent a number, date, quote or name. No source, no line.
- Never change kit/voice/ref_michael.wav, fonts, palette or grade. No logo sting.
- Never publish with edge-tts or any non-commercial voice.
- Never run two heavy jobs (voice, whisper, render) at once on one worker.
- Never put a password, token or key in any file. Keys live in GitHub Secrets / the worker's env and are referred to by name:
  `HF_TOKEN`, `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, `YOUTUBE_CLIENT` (later).

## 5. When something breaks
1. Read the last 40 lines of the step's log (`vo_run.log`, `render.log`, `qa/check_*.json`).
2. Fix the smallest thing that explains the error. Re-run that step only; every step resumes.
3. Same error 3 times: stop, open an issue titled `[blocked] <ep> <step>` with the log tail and what you tried, and tell the owner in one sentence.

## 6. Workers
- Primary: Modal (GPU, free monthly credits). Fallback: owner's Mac mini M4 (16 GB). Last resort: any Linux box with 8 GB+.
- Setup for a worker: `docs/WORKER_SETUP.md`.

## 7. Done means
Owner merged the final PR, the video is uploaded with title, thumbnail, description, tags, and state.json says `released`.
