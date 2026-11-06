# REPO MAP (read this instead of exploring the tree)

One line per file/dir: job, key functions, entry point. Outputs land in `out/<ep>/` (Modal/Actions) or `<ep>/qa/`.

## Top level
- `AGENTS.md` - operator rules + cheat sheet + caveman mode. Read first.
- `README.md` - short human intro.
- `.github/workflows/episode.yml` - ONE COMMAND. Inputs below. Ends with `out/<ep>/summary.json`.
- `.github/workflows/gates.yml` - merged PR from `gate/<ep>/<cast|script|final>` = owner approval (sets state.json).

## episode.yml inputs
| input | does |
|---|---|
| `ep` | episode folder, e.g. `episodes/ep01-onecoin` |
| `test_lines` | voice only these line ids (`0-3`); test run -> preview pushed to branch `preview` |
| `preview_seconds` | render only first N s (0 = all) |
| `redo_images` | comma list of picture keys to remake with a new seed |
| `redo_lines` | comma list of line ids to re-voice |
| `max_gpu_seconds` | spend guard (env WIS_MAX_GPU_S); GPU call that would pass it is refused |
Outputs: artifact `<run_id>-review` (video.mp4, package/, cost.json, audio_qc.json, summary.json). Test runs: branch `preview` holds preview.mp4, summary.json, cost.json, thumbs.
`summary.json` = {ep, status, test, failed_checks[], cost_usd, gpu_secs, preview_url, run_url}. AI reads only this.

## machine/ (Python, CPU unless noted)
- `wis.py` - driver: `new|status|check|advance|reach <ep> <state>`; state machine in `<ep>/state.json`.
- `checker.py` - playbook/rules.yaml as code: `checker.py <ep> <target_state>` -> `<ep>/qa/check_*.json`.
- `craft_check.py` - free editing checks (P1 dead frames, H1 hook, P4 repeats, sources, caption band, v4 fx rules) -> `<ep>/qa/craft.json`.
- `fm_check.py` - FM-* checks from docs/FAILURE_MODES.md (sources, TTS text, questions, music beds, line refs, secrets, JSON, chapters); TODO stubs for the rest -> `<ep>/qa/fm.json`.
- `motion_check.py` - AMC-* motion rules: seeds lint, theme contrast, spec; `--video <mp4>` frame checks -> `<ep>/qa/motion.json`.
- `score_script.py` - hook timing/pace/jargon; `--hooks` scores hooks.md variants.
- `plan_images.py` - shots.json + library -> `<ep>/img_jobs.json`.
- `fetch_media.py` - Wikimedia Commons photos (commercial-safe licences) -> `<ep>/media/` + credits.json.
- `worker_images.py` - Modal GPU (Qwen-Image): `images(job, force)`; cache by job_hash; CPU qc for people/text; cutouts.
- `worker_voice.py` - Modal T4 voice: `voice(ep, only, redo)`; cached lines skipped; vo_qc.json.
- `worker_render.py` - Modal CPU: prepare -> plan -> render_batch (parallel, shot cache) -> join -> automix -> package. `render(ep, seconds)`.
- `package.py` - titles, description, chapters, sources, thumbnails -> `package/`.
- `thumbnail.py` - designed thumbnails 1280x720 (cut-out subject + code text + rim light + brand frame), phone mock, auto score. `python machine/thumbnail.py <ep> [--gpu]`.
- `shorts_cut.py` - vertical 1080x1920 Shorts from a rendered video + timeline (see QUEUED Part B).
- `frame_fill.py` - F1 check: flat empty area <= 35 % on a video or frames dir.
- `photo_score.py` - free photo picker score (signage / empty middle / blur); used by fetch_media.
- `cost.py` - `add/guard/timer`; writes `out/<ep>/cost.json` (total_usd, gpu_secs).
- `cost_report.py` - one-line cost per run/episode from cost.json files.
- `paths.py` - shared paths.
- `templates/` - blank cast.md, lines.json, research.md, script.md for `wis.py new`.
- `fixtures/motion_defects/` - known-bad spec for motion_check self-test.

## machine/engine/ (render code, imported inside Modal)
- `shots_render.py` - generic renderer: shots.json + timeline.json -> frames. `render(i)`; TYPES dict maps shot type -> drawer; v3 + v4 wiring at bottom.
- `shotspec.py` - timing model shared with checks: `events, accents, max_gap, media_keys`; CONTINUOUS/STRIKING sets.
- `v3kit.py` - v3 look: boards/themes, phones (`s_phone`), photo layouts (`s_photos`), `s_map`, `s_money`, `s_stamp`, `s_scrub`, `s_barrace`, `marks`.
- `v4fx.py` - v4 modern fx (CPU): `s_parallax`, `s_docreveal`, `s_headlines`, `s_coin3d`, `s_chart3d`, `s_lineart`, transitions `glitch`/`leak`, `beats()` + `snap()`.
- `v5fx.py` - v5 look: `archive` (depth board), `floaters`, `glide` (evidence wall), `normalize`/`keywords` (captions), templates T29-T39 (`TYPES5`). Wired at the bottom of shots_render.py.
- `collage.py` - paper/sticker/highlighter/framed card helpers (C.*).
- `edhelpers.py` - W,H,FPS=1920x1080@30, fonts F(), ease/eout/back, zoom, finish, bug.
- `motion.py` - crc32 `seed/rng`, easing tokens, `on_twos`, `hold_push`, `punch`, contrast maths.
- `assemble.py` - timeline.json from voice + lines. `automix.py` - music/SFX mix (22 dB bed) -> mix.wav + audio_qc.json.
- `master.py` - loudness master. `vo_runner.py`, `run_vo.sh`, `whisper_words.py` - voice takes + word timing.

## episodes/<ep>/ (one folder per episode)
brief.md, research.md (sources), beats.md, bible.md (continuity), chapters.md, scenes.md (new per DIRECTOR_PROMPT; ep01 predates them), cast.md, script.md, lines.json (id,text,preset,gap,visual,src), shots.json (music, shots[], counter, thumb_text, title_facts), hooks.md/json, titles.md, state.json, img_jobs.json, media/ (photos+credits.json), img/, vo/, qa/ (check outputs), package/, thumbs/ (designed thumbnails + phone mock + score.json).

## Other dirs
- `prompts/` - agent chain: 00_README (chain, hand-offs, gates), 01_research_writer, 02_director, 03_builder, 04_voice_finish; each fully self-contained (rules inlined with FM ids, schemas, ep01 worked examples, gates). PDFs: prompts/WISDROP_AGENT_*.pdf.
- `schemas/chapters.schema.json` - chapters.json format (agent 2 -> 3, 4). `tools/chapter_lines.py <ep>` prints test_lines per chapter + checks counter/board/music chain.
- `docs/` - DIRECTOR_PROMPT.md (system prompt for any AI: role, look, pipeline + file formats, chapter sync, self-review, when to ask owner), FAILURE_MODES.md (134 FM-* rules), OPERATOR_GUIDE (.pdf for owner), SHOTS.md (shot types + templates), EDITING_CRAFT.md, AI_MOTION_CRAFT.md, THUMBNAILS.md, PUBLISH_CHECKLIST.md, RETENTION.md, V3_PLAN.md, REPO_MAP.md.
- `playbook/` - rules.yaml (checker), WISDROP_PLAYBOOK.md (creative), WISDROP_AI_INSTRUCTIONS.md.
- `library/` - library.json (cast, sets, look "v3"), LIBRARY.md.
- `kit/` - fonts (Anton, DejaVu), music (+ATTRIBUTION), sfx (synth, +ATTRIBUTION), voice ref (never change), style_prompt.txt, style_ref/, vectors/.
- `tools/synth_sfx.py` - makes the synth SFX. `tools/synth_amb.py` - v5 ambience (amb_*). `tools/v5_local_frames.py` - free local sample frames for any lines (estimated timeline).

## Where to look for X
- A run's result: `summary.json` (preview branch or artifact). Cost: `cost.json`. Failed check detail: `<ep>/qa/craft.json`, `motion.json`.
- Add a shot type: drawer in v3kit/v4fx -> register in shots_render TYPES -> events in shotspec -> doc in SHOTS.md.
