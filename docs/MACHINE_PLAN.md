# Wisdrop Machine — product, build, architecture, risk plan (draft v0.1, 2026-11-03)

## 0. Correction to earlier proposal
GitHub's Actions terms (fetched 2026-11-03): GitHub-hosted runners may only be used for activity related to "the production, testing, deployment, or publication of the software project associated with the repository", Actions is "to develop and test your application(s)", and no "stand-alone or integrated application or service offering the Actions product ... for commercial purposes". Rendering YouTube episodes on free hosted runners risks repo disable / account suspension, and selling it as a product on that base is excluded. => GitHub = brain + memory + approvals. Heavy compute runs on a "worker" we control (self-hosted runner rule about unrelated activity does not apply to self-hosted).

## 1. Product
- Promise: hand any capable AI one Operator File + repo access; it produces a checked, owner-approved episode (6-20 min) with no coding.
- Users: Owner (approves), Operator AI (drives), Worker (computes).
- Success metrics: 20-min episode <= 2 h machine time; 0 unrecovered crashes; owner touches = 3 approvals; checker pass before every gate; marginal cost ~0 except optional image API / GPU.

## 2. Requirements
Functional: new episode scaffold; research with sources; cast/script with visual per line; images; voice with auto-QC; captions; render; mix/master; QC report; approval gates; release; (later) YouTube upload, Shorts.
Non-functional: resumable at every step; idempotent commands; deterministic voice (fixed conds + seeds + pinned versions); secrets never in repo/logs/file; AI-agnostic (CLI + state file + docs); observable (status command, reports).

## 3. Accounts and keys needed
- GitHub account; repo `wisdrop-machine` (private recommended once compute is off GitHub runners). Fine-grained token scoped to that repo only (contents, PRs, actions), expiry noted.
- Hugging Face account: private repo for voice ref + fp16 weights mirror; read token.
- Worker: (a) owner PC / spare laptop as self-hosted runner, (b) Kaggle notebooks for free GPU voice (check Kaggle terms for commercial use), (c) paid GPU on demand (cents per episode) as fallback. Oracle Always Free = only 2 OCPU/12 GB now, no better than today's sandbox.
- Image generation API key (Gemini/OpenAI) or images made by Hark and committed.
- Later: YouTube Data API OAuth client for upload.
- Password manager / vault for all of the above. Operator File references names, never values.

## 4. Build phases (each ends with an acceptance test)
P0 Freeze (0.5 d): Playbook v4 with owner overrides (timing +0.04 s, slower animations, length rule, 8.1 fix, question preset). Port tools (vo_runner, whisper_words, master, render, mix).
P1 Repo + CLI + state (1 d): `wis new|check|status|voice|render|finish|release`; episodes/epNN/state.json; config.yaml. Test: ep00 scaffold + status round-trip.
P2 Checker = rules as code (1 d): every line has VISUAL; every number in script has a source in research.md; key numbers 2 sources; links return 200; banned real-person names in image prompts; durations; owner overrides. Test: seeded bad script fails on each rule.
P3 Voice service (1 d): sharded vo_runner on worker; shard merge; fixed conds.pt; per-line loudness normalize; tonal-consistency check (pitch/energy median). Test: ep00 lines reproduce QC pass; 340-line stress run with zero lost lines after forced kill.
P4 Render service (1 d): shard on shot boundaries, same encoder settings, concat demuxer, audio mixed once over the whole timeline. Test: no seam (frame count exact, no A/V drift > 1 frame over 20 min), sync report.
P5 Images (1 d): image step behind API with reference sheets; palette check; contact sheet for owner. Test: 10 shots, same character consistent.
P6 Gates + reports (0.5 d): PR per gate; machine posts QC report as PR comment; merge = approval; state advances only on merge.
P7 Operator File + handover test (0.5 d): fresh AI session gets only the file; must take ep00 end-to-end. Fix every place it stumbles.
P8 Episode 1 pilot (1 d incl. approvals). Then v1.0 tag.
Total ~7-8 working days, mostly unattended runs.

## 5. Architecture
repo/
  AGENTS.md (short pointer to OPERATOR guide in repo; public-safe)
  playbook/ (PLAYBOOK.md v4, STYLE.md, rules.yaml machine-readable)
  machine/ (cli wis, voice/, render/, captions/, mix/, checker/, images/)
  kit/ (fonts, music, sfx, style_ref; voice ref pulled from HF at runtime)
  episodes/epNN-slug/ (state.json, research.md, cast.md, script.md, lines.json, img/, reports/)
  .github/workflows/ (light: checker on PR, report posting, dispatch to worker)
Flow: AI writes files -> PR -> checker (light) -> owner merge -> worker job (voice) -> worker job (captions+render+mix) -> reports -> final PR -> owner merge -> release (+upload later).
State machine: draft -> research_ok -> cast_approved -> script_approved -> images_ok -> voice_ok -> render_ok -> final_approved -> released. Illegal jumps refused by CLI.
Storage: text in git; images via Git LFS or HF dataset; audio/video intermediates on worker + HF; final MP4 as release asset (<2 GB) or HF.

## 6. Performance (20-min episode, ~340 lines)
- Today (2 CPU sandbox): voice ~6-7 h, render ~3.5 h.
- Owner PC 8 cores/16 GB as worker: voice ~2-2.5 h (3 shards x 2-3 threads), render ~1 h.
- Kaggle GPU voice: ~20-30 min; render on 4 CPU ~1.5 h (or split).
- Paid GPU fallback: voice ~10-15 min.

## 7. Risks and fixes
See summary card / table in chat (same content): ToS, OOM, voice drift, seams, dependency drift, secrets, hallucinated facts, AI loops, image drift, real-person likeness, YouTube inauthentic/AI disclosure policy, token expiry, storage limits, worker offline, cost creep, single point of failure.

## 8. Management
- Versioning: playbook semver, machine tags (v1.0), episode state history in git.
- Change control: owner overrides go into rules.yaml via PR only.
- Weekly: dependency check, token expiry check, backup mirror.
- Metrics per episode: machine time, retakes, checker fails, owner revision rounds.
