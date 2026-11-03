---
title: "Wisdrop Machine: Operator Guide for any AI"
subtitle: "Read this first. Follow it exactly. Version 3, 3 November 2026"
geometry: margin=2cm
fontsize: 10pt
---

# 1. What you are running

Wisdrop is a faceless English YouTube channel: *Money crimes behind the hype*. Each episode tells one
real financial fraud in five parts, 8 to 12 minutes. **Look v3 (owner-approved):** a Vox / Johnny Harris
style paper collage drawn entirely by code: a gridded paper board whose colour rotates per part (navy,
warm off-white, sky blue, charcoal), real photos as sticker and polaroid cut-outs, maps with flight
routes, premium phone screens (texts, group chats, notifications, bank app, price ticker, inbox, live
webinar), money-flow diagrams, stamps, highlighter and marker strokes, and 4 to 6 AI pictures per episode
for story moments no photo can show (fictional composite characters only).

The **machine** is this GitHub repository plus Modal workers. You (the AI) do the thinking: research,
script, shot plan. The machine does the heavy work on Modal from the owner's credit.

**Repository:** `shrikantdange/wisdrop-machine` (private). Modal keys are GitHub secrets
`MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`. Never print, copy or ask for them.

# 2. Files you must read before any work

| File | What it is |
|---|---|
| `AGENTS.md` | Operator rules (short). Wins over your habits. |
| `playbook/WISDROP_PLAYBOOK.md`, `playbook/rules.yaml` | Creative rules and the rules the checker enforces. |
| `docs/SHOTS.md` | How to write `shots.json`: every shot type and 20 ready templates. |
| `docs/EDITING_CRAFT.md` | Editing rules from the best explainer editors, with sources; checks enforce the [check] ones. |
| `library/library.json` | Cast, poses, sets, times of day, look `v3`. Reuse it. |
| `kit/vectors/ATTRIBUTION.md` | Free icons (Tabler, MIT), emoji (OpenMoji, CC BY-SA), maps (Natural Earth, PD). |
| `episodes/ep01-onecoin/` | A complete worked example of every file, including `hooks.md`. |

# 3. The whole job in 8 steps

1. **Create the episode.** `python machine/wis.py new <slug> "<title>"`.
2. **Research** (`research.md`): every number needs a source; key numbers need two. Open every page you cite.
3. **Cast and script** (`cast.md`, `script.md`, `lines.json`, `titles.md`). Fictional composites only.
   Hook rule: a shock fact in 5 s, a question by 8 s, a promise by 15 s, an open question in every part.
   Write 3 alternative openings in `hooks.json` and score them: `python machine/score_script.py <ep> --hooks`.
4. **Shot plan** (`shots.json`, docs/SHOTS.md). Pick from the 20 templates. Something must move at least
   every 2.5 s; in the first minute a visual change every 1.5 to 3 s. Pictures come in pairs, trios,
   walls or with marks/stickers, never alone and still. No photo twice. 4 to 6 AI pictures at most.
   `python machine/fetch_media.py <ep>` fetches commercial-safe photos (credits automatic).
5. **Free checks.** `python machine/craft_check.py <ep>` must print no FAIL (REVIEW = owner's call).
   `python machine/plan_images.py <ep>` must print OK.
6. **Owner approval of cast + script** via PR `gate/<ep-folder>/script`. The owner merging it = approval.
7. **Run the machine.** Workflow **episode**: `ep`, then always a test first (`test_lines=0-3`,
   `preview_seconds=15`), then the full run. `max_gpu_seconds` (default 600) is the spend guard.
8. **Owner final review.** The run opens `<ep>: FINAL REVIEW`. The owner merging it = final approval.

# 4. What the episode workflow does

| Step | Where | Cost control |
|---|---|---|
| Owner gate check, free craft checks, script score | GitHub runner | free; FAIL stops before any spend |
| Plan pictures, fetch real photos (Wikimedia Commons) | GitHub runner | free |
| AI pictures (sets, composed story shots) | Modal A100 | hash cache; spend guard; QC only on new pictures |
| Voice with automatic listening check | Modal T4 | per-line cache; spend guard |
| Render | Modal CPUs | **shot-level cache**: only changed shots render, ~15 s batches side by side |
| Mix + master + audio QC | Modal CPU | -14 LUFS, true peak <= -1 dBTP, voice >= 10 dB over music |
| Package: description (sources, credits), tags, 5 formula titles, 3 thumbnails + phone preview | Modal CPU | cents |

Every run writes `out/<ep>/cost.json` (measured seconds x Modal list price) into the artifact and prints
`COST` lines. Read the log: PLAN / OK / WAIT / FAIL / REVIEW / COST.

# 5. Fixing things (pay only for the fix)

| Problem | What to do |
|---|---|
| A picture is wrong | `redo_images = <picture name>` (new seed) or change its prompt in `library.json` |
| A voice line sounds wrong | `redo_lines = <line ids>` |
| A shot is wrong | Edit `shots.json` and re-run: only that shot re-renders (shot cache) |
| `FAIL: P1/P2` (dead frames, slow first minute) | Add `marks`, `stickers`, split the shot, or pick a busier template |
| `FAIL spend guard` | The run wanted more GPU than allowed. Check why before raising `max_gpu_seconds` |
| `FAIL audio` | Check music levels in shots.json `music`, re-run (render is cached) |
| Run failed | Read the failed step's log, fix the cause, re-run. Never loop more than twice without telling the owner |

# 6. Rules that never bend

- Never draw a real person, not even as a silhouette. Real people appear only as names on cards.
- No number on screen or in narration without a source in `research.md`.
- Never change the voice reference, fonts, board palette or music list. No logo sting.
- Code draws all words on screen. Generated pictures never contain text.
- Licences: CC0, PD, CC BY, CC BY-SA, MIT, ISC, Apache only. Never NC or ND.
- Owner approves cast + script, and the final video + thumbnail.
- No secrets in files, logs or chat. Keep spend low: test small, reuse, redo only what failed.

# 7. Expected cost (Modal)

- Test run (15 s, voice and pictures cached): CPU only, a few cents at most; measured in `cost.json`.
- A new episode reusing the library: target under 0.25 USD (4-6 AI pictures ~0.15, voice ~0.05,
  render + mix ~0.05). Re-runs after small edits cost cents because shots, lines and pictures are cached.
- Modal Starter includes 30 USD of credit a month. Set a workspace budget in Modal settings.

# 8. First message to give a new AI

> You have access to the GitHub repo shrikantdange/wisdrop-machine. Read AGENTS.md and
> docs/OPERATOR_GUIDE.md, then make the next Wisdrop episode about **<case>**. Stop at each owner gate.
