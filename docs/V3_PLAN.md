# Wisdrop v3 build plan (owner-approved 2026-11-03)

Order matters: each phase ends with a commit. If usage runs low, stop at a phase boundary,
commit, and record where you stopped in the project skill.

## Phase 1: Clean the repo (keep only what is reused)
1. List every file; mark keep / delete / merge.
2. Delete: duplicate workflows (images.yml, voice.yml, render.yml, worker-check.yml) once episode.yml covers them; legacy ep00 render templates (render_template.py, mix_template.py); unused noir-only paths; stale docs and test outputs.
3. Merge overlapping docs into: AGENTS.md (short rules), docs/OPERATOR_GUIDE.md (how to run), docs/SHOTS.md (shot types), docs/EDITING_CRAFT.md (new).
4. Keep: playbook, rules.yaml, kit (voice ref, fonts, music, sfx), library, ep01 files, checker, wis.py.
5. Consistent log lines everywhere: PLAN / OK / WAIT / FAIL / REVIEW.

## Phase 2: Learn editing craft -> docs/EDITING_CRAFT.md
Research with web_search + web_fetch, cite every source:
- Vox (collage, archival treatment, highlighter, map style), Johnny Harris (maps, desk-explainer pacing), BBC (clean infographics), TED-Ed and Kurzgesagt (illustrated motion, colour scripts), The Infographics Show (retention pacing), Magnates Media / Coffeezilla style money-crime storytelling.
- Editor blogs and tutorials: pacing, J/L cuts, pattern interrupts, hook structure, open loops, sound design layers (whoosh, risers, hits, room tone), kinetic type rules, map animation, colour scripts per act, thumbnail design and title psychology.
Turn findings into machine rules, mapped to story beats: hook, setup, rise, twist, fall, aftermath.

## Phase 3: Code checks (free, run before render)
- Dead frame: nothing holds more than 2.5 s without motion.
- First minute: a visual change every 1.5 to 3 s.
- Hook: shock fact or striking visual inside 5 s, question by 8 s.
- No photo or AI picture repeated in an episode.
- No lone big image without surround motion or a pair/collage.
- Every number on screen has a source; captions never overlap cards.
- Loudness -14 LUFS, -2 dBTP; voice always above music.

## Phase 4: Visual system (code-drawn, CPU only)
- Boards rotate per part: navy, warm off-white, sky blue, charcoal, each with a faint grid and paper grain.
- Toolkit: tape, marker circles, arrows, underline, highlighter, pop stickers, stamps, white-border sticker photo cut-outs, torn paper, halftone, duotone.
- Photo layouts: pair, trio, collage wall, polaroid stack, magnifier zoom, split screen.
- Premium phone screens: SMS/iMessage-style chat, WhatsApp-style group, push notifications, bank app balance, crypto price ticker, email inbox, webinar/live stream with chat.
- Maps: animated route lines, country highlights, pins, flight path (Sofia to Athens).
- Money flow: animated arrows, coins, counters between boxes; recurring episode money counter.
- Kinetic type: centred, word pops, highlighter swipes, stamp words.
- Data: count-up stats, bar race, line chart with annotations, timeline scrubber.
- Free vectors/icons: OpenMoji (CC BY-SA), Tabler/Lucide (MIT/ISC), Wikimedia Commons SVG (CC0/PD); log licences in ATTRIBUTION; refuse NC/ND.
- 20 reusable animated templates documented in SHOTS.md.

## Phase 5: Sound
- tools/synth_sfx.py adds: swoosh, typewriter, notification ding, phone buzz, cash register, coin drop, camera shutter, riser, impact, page turn.
- Each element type has its own sound; music changes per part; room-tone beds per set.
- Ducking and loudness checked on every render.

## Phase 6: Cost and speed
- Shot-level render cache: hash each shot; re-render only changed shots.
- GPU only for voice and at most 4 to 6 AI pictures per episode.
- Spend guard: workflow stops if planned GPU seconds exceed a limit.
- Target under 0.25 USD per episode; log measured cost per run.

## Phase 7: Story upgrades
- Rewrite ep01 opening shots (lines 0-15): shock fact in 5 s, question, promise; open loop into Part 1.
- Hook bank: 3 alternative openings, scored.
- Script scorer: hook timing, open loops per part, words per minute, jargon flags.
- Title formulas and 3 thumbnails per episode built from the strongest frames, with a phone-size preview.

## Phase 8: Test and hand over
- Run episode workflow with test_lines=0-3 (about 15 s); check frames visually.
- Update AGENTS.md and OPERATOR_GUIDE.md; regenerate the operator PDF.
- One final message: what changed, test clip, PDF, measured cost, what remains.

## Later (queued, not this build)
Shorts cutter, retention map from YouTube Studio, end screens, weekly cost report, YouTube AI-disclosure and reused-content check before first upload, full ep01 shots 16-139 and full run.

## Never bend
Never draw a real person; every number sourced; owner approves cast/script and final video; no secrets anywhere; frugal Modal spend; words on screen drawn by code.
