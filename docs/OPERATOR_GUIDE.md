---
title: "Wisdrop Machine: Operator Guide for any AI"
subtitle: "Read this first. Follow it exactly. Version 1.1, 3 November 2026"
geometry: margin=2cm
fontsize: 10pt
---

# 1. What you are running

Wisdrop is a faceless English YouTube channel: *Money crimes behind the hype*. Each episode tells one
real financial fraud in five parts, 8 to 12 minutes, with noir screen-print illustrations, code-drawn
evidence cards, a fixed narrator voice and a fixed sound palette.

The **machine** is a GitHub repository plus Modal workers. You (the AI) do the thinking work: research,
script, shot plan. The machine does all heavy work (pictures, voice, render, mix, thumbnails) on Modal,
paid from the owner's Modal credit. You never generate images, audio or video yourself.

**Repository:** `shrikantdange/wisdrop-machine` (private). Ask the owner for access if you do not have it.
Modal keys are already stored as GitHub repository secrets `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`.
Never print, copy or ask for them.

# 2. Files you must read before any work

| File | What it is |
|---|---|
| `AGENTS.md` | Operator rules (short). Wins over your habits. |
| `playbook/WISDROP_PLAYBOOK.md` | Creative rules. Wins on any creative conflict. |
| `playbook/rules.yaml` | Rules the checker enforces (length, words, real people, timing, loudness). |
| `docs/SHOTS.md` | How to write `shots.json` (the only per-episode visual file). |
| `library/library.json` | The repertory: cast, poses, sets, times of day. Reuse it. |
| `episodes/ep01-onecoin/` | A complete worked example of every file. Copy its shape. |

# 3. The whole job in 7 steps

1. **Create the episode.** `python machine/wis.py new <slug> "<title>"` makes `episodes/epNN-<slug>/`.
2. **Research** (`research.md`): timeline rows `date | event | source URL`. Every number needs a source;
   key numbers need two. Open every page you cite. `python machine/wis.py check <ep>` must pass.
3. **Cast and script** (`cast.md`, `script.md`, `lines.json`, `titles.md`). Fictional composite characters
   only; real people are never drawn, only named on evidence cards. Each line in `lines.json` has
   `id, text, preset (facts|dry|tension|question|beat), gap, visual, src`.
4. **Shot plan** (`shots.json`, see `docs/SHOTS.md`). One shot per visual change, every line covered.
   Prefer existing library cast, poses, sets and times. New ones go into `library/library.json` first.
   `python machine/plan_images.py <ep>` must print `OK`.
5. **Owner approval of cast + script.** Push a branch named `gate/<ep-folder>/script` with the files and
   open a pull request. The owner merging it is the approval (workflow `gates.yml` records it).
   **Never approve for the owner. Never set `WIS_OWNER_APPROVAL` yourself.**
6. **Run the machine.** In GitHub Actions run workflow **episode** with `ep = episodes/<ep-folder>`.
   Always run a test first: `test_lines = 0-15` (about one minute, no state change). Then the full run.
7. **Owner final review.** The run opens a pull request `<ep>: FINAL REVIEW`. The video is in the run's
   artifacts. The owner merging it = final approval. Upload to YouTube is manual in v1.1 (the package
   has title, description with sources and credits, tags, two thumbnails).

# 4. What the episode workflow does (no action needed from you)

| Step | Where | Cost control |
|---|---|---|
| Plan pictures from shots + library | GitHub runner | free |
| Sets, characters, composed story shots | Modal A100, 8-step fast model | content-hash cache: a picture is never made twice, across all episodes |
| Picture check for stray people and text | Modal CPU | remakes only failures, once |
| Voice, line by line with automatic listening check | Modal T4 | cache per line; only new or changed lines are voiced |
| Join voice, render frames in parallel, mix, master -14 LUFS | Modal CPUs | 15-second chunks in parallel, containers stop after 2 s idle |
| Package: titles, description, tags, 2 thumbnails | Modal CPU | free in practice |

Read the log: every step prints `PLAN / OK / WAIT / FAIL / QC-FAIL / REVIEW` lines.

# 5. Fixing things (pay only for the fix)

| Problem | What to do |
|---|---|
| A picture is wrong | Re-run with `redo_images = <picture name>` (new seed), or change its prompt in `library.json` |
| A voice line sounds wrong | Re-run with `redo_lines = <line ids>` |
| A shot is wrong (text, timing, motion) | Edit `shots.json` and re-run; pictures and voice come from cache |
| `WAIT n line(s) need a listen` | Listen to those lines in the artifact; redo them or accept |
| `REVIEW <picture>` | Look at it in the artifact; redo it or change the prompt |
| Run failed | Open the failed step's log, fix the cause, re-run. Never loop more than twice without telling the owner |

# 6. Rules that never bend

- Never draw a real person, not even as a silhouette. Real people appear only as names on cards.
- No number on screen or in narration without a source in `research.md`.
- Never change the voice reference, fonts, palette, grade or music list. No logo sting.
- Never publish a non-commercial or edge-tts voice.
- Code draws all words on screen. Generated pictures never contain text, and code text is never laid
  over a generated picture.
- Owner approves cast + script before any picture or voice, and the final video + thumbnail before upload.
- No secrets in files, logs or chat. Do not create extra Modal accounts.
- Keep spend low: test with `test_lines` first, reuse the library, redo only what failed.

# 7. Expected cost (Modal, estimates)

- One-off library build (4 characters, 6 sets with time variants): about 1 to 2 USD, then reused.
- A new episode reusing the library: about 0.30 to 0.60 USD for 10 to 12 minutes
  (new composed shots about 0.20, voice about 0.10, render and mix about 0.10).
- Modal Starter includes 30 USD of credit a month.

# 8. Visual language (locked)

Mid-century noir screen-print poster crossed with graphic-novel inks: grain, 4 to 6 muted colours,
one warm focal light. The **technique is fixed; the palette follows each scene's time and light**
(dawn, morning, day, afternoon, dusk, night, rain night, screen glow). Story shots carry a
DRAMATISATION tag. Evidence shots are navy grid boards with paper cards, gold and red accents.

# 9. First message to give a new AI

> You have access to the GitHub repo shrikantdange/wisdrop-machine. Read AGENTS.md and
> docs/OPERATOR_GUIDE.md, then make the next Wisdrop episode about **<case>**. Stop at each owner gate.

# Appendix: cost plan (merged from COST_PLAN.md in v3)


Prices from modal.com/pricing (read 2026-11-03): A100-80GB $2.50/h, T4 $0.59/h,
CPU $0.047 per core-hour. Times below are estimates until measured.

| Step | Before | Now | How |
|---|---|---|---|
| Images | 30 steps x CFG = 60 passes, ~46 s each on A100 | 8 passes, target ~7 s | Lightning 8-step LoRA (Apache 2.0) |
| Character poses | new prompt per pose, face drifts | edit from master sheet | Qwen-Image-Edit-2509 + Lightning |
| Redo | whole batch again | only changed pictures/lines | content-hash cache in volume wisdrop-assets |
| Voice | every line every run | only changed lines | line hash (text, preset, voice ref) |
| Motion | none | code-drawn, free | PIL render, no AI video |
| Render | 1 slow sandbox CPU, ~1 h | ~20 Modal CPUs side by side, minutes | parallel chunks, about $0.04 per episode |
| Mix + master | sandbox | Modal CPU, cents | same mix.py |
| Outputs | WAV/PNG force-pushed to git | Modal volume + Actions artifacts | repo stays small |

Rules: one GPU container, one call per batch, scaledown 2 s, weights downloaded on CPU.
Nothing reaches the GPU if every hash is cached. Library first: a new episode makes only
the new cast, poses and sets it needs.

Budget estimate per episode once the library exists: images $0.20-0.60, voice ~$0.10,
render+mix ~$0.05. First library build is a one-off (~150 pictures, roughly $1-2).
Set a workspace budget in Modal (Settings > Usage & Billing) so spend cannot pass the credit.
