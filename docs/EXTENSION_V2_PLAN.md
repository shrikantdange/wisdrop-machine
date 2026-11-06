# Wisdrop Studio v2 plan (2026-11-06, for owner approval - NOT built yet)

Based on `docs/EXTENSION_RESEARCH.md` (sources [n]) and `docs/EXTENSION_AUDIT.md`. Goal: turn the v1.1 chat panel into a **production desk** for one episode: queue of jobs that survives closing Chrome, per-chapter batch runs, a review grid, hard cost caps, run history - all through official APIs (model APIs, GitHub, Modal via GitHub Actions). No puppeting of AI websites.

## 1. v2 in 3 lines
1. **Job queue with resume:** every agent step and every GitHub run is a job saved in storage; alarms poll runs; the panel picks up where it stopped.
2. **Chapter batch desk + review grid:** run voice/render per chapter or per shot list, see every clip/line/fact in one grid, approve or send back per item.
3. **Money and safety rails:** $ caps per run/day, Ask-before-act for writes/dispatch/merge, site Allow/Ask/Block, prompt library and run history with export.

## 2. Architecture (text diagram)

```
+--------------------------- Chrome (owner's profile) ----------------------------+
|                                                                                  |
|  Side panel (sidepanel.html)  <---- runtime messages ---->  Service worker       |
|  - UI: Desk / Queue / Review / Library / History / Keys      (background.js)     |
|  - Agent loop runs here while open (fetch to model API)     - alarms (>=30 s)    |
|  - never holds jobs only in memory                          - polls GitHub runs  |
|        |                                                    - notifications      |
|        v                                                    - no long work       |
|  chrome.storage.local (10 MB, TRUSTED_CONTEXTS)                    |             |
|   vault (AES-GCM) | jobs[] | sessions | library | history | prices |             |
|        |                                                           |             |
+--------|-----------------------------------------------------------|-------------+
         | HTTPS (optional host perms, per provider)                 | HTTPS
         v                                                           v
  Model APIs (BYOK): Anthropic*, OpenAI, Gemini, OpenRouter,   api.github.com (fine-grained PAT,
  Groq, DeepSeek, Mistral, Together, Ollama/LM Studio local    this repo only)
  (*browser-access header; Ollama needs OLLAMA_ORIGINS)          |  contents / PRs / workflow_dispatch
                                                                 v
                                                  GitHub Actions: episode.yml, thumbs.yml, gates.yml
                                                                 |  (Modal keys = Actions secrets)
                                                                 v
                                                  Modal GPU workers (voice, images, render)
                                                                 |
                                                  outputs: branch preview / artifacts / summary.json / cost.json
```

Rules: the service worker only schedules and polls (it dies after 30 s idle [1]); state always in storage; the agent loop runs in the panel page and checkpoints after each step; nothing executes code fetched from the repo [7].

## 3. Modules

| Module | File | Does |
|---|---|---|
| store | lib/store.js | vault (keep), `jobs`, `sessions`, `library`, `history`, `prices` stores; quota check (`getBytesInUse`) with pruning |
| providers | lib/providers.js | keep adapters + retry; add streaming (optional), price lookup, model-gone warning |
| github | lib/github.js | keep; add signal/abort, run matching by dispatch time + title, artifact listing for big files |
| agent | lib/agent.js | keep JSON protocol; add tool-output-as-data wrapper, history summariser, Ask policy per tool, step checkpoints |
| queue (new) | lib/queue.js | job model `{id, kind: agent_step|dispatch|poll|review, ep, chapter, inputs, status: queued|running|waiting_owner|done|failed|cancelled, tries, cost, created, updated}`; pause/resume/reorder/retry-failed; one heavy run at a time (matches `concurrency: heavy-worker`) |
| cost (new) | lib/cost.js | token -> $ from owner-editable price table; caps per run / per day / per episode; reads `cost.json` for GPU $; hard stop + banner |
| library (new) | lib/library.js | prompt snippets and agent "recipes" (e.g. "Chapter 3 voice test 0-15"); import/export JSON |
| background | background.js | alarms: poll running GitHub jobs every 1 min, update jobs, notify on done/failed/gate; re-create alarms on startup [5] |
| ui | sidepanel.* split into panels/desk.js, queue.js, review.js, history.js, keys.js | plain JS, no build step, no remote code |
| tests | test/*.js | unit (mock fetch) + a manual real-Chrome checklist |

## 4. UI wireframes (text)

```
DESK (default)                          QUEUE
+-----------------------------------+   +-----------------------------------+
| ep01-onecoin  state: chapters     |   | [Pause all] [Retry failed] [Export]|
| Today $0.42 / cap $2.00  [=== ]   |   | # job            status   cost    |
|-----------------------------------|   | 1 agent 02 ch3   done     $0.03   |
| Chapter   lines  voice  render QA |   | 2 voice ch3 0-15 running  GPU 40s |
| ch1 Hook  0-15   ok     ok    ok  |   | 3 render ch3     queued   ~60s    |
| ch2 ...   16-38  ok     run   -   |   | 4 gate chapters  WAITING OWNER    |
| ch3 ...   39-61  [Voice][Render]  |   |  [up][down][cancel] per row       |
|-----------------------------------|   +-----------------------------------+
| Agent: [02 Director v] [Ask mode] |
| > chat ...                        |   REVIEW GRID
| [Send] [Stop]  tokens 12k  $0.05  |   +-----------------------------------+
+-----------------------------------+   | filter: ch3 | clips | lines | facts|
                                        | [clip 39][clip 40][clip 41] ...    |
HISTORY                                 |  each: play, FM flags, Approve,    |
+-----------------------------------+   |  Send back + note                  |
| date  agent/run  result  $  link  |   | [Approve chapter = merge gate PR]  |
| [Export JSON] [Export markdown]   |   +-----------------------------------+
+-----------------------------------+
```

## 5. Feature set (chosen from the research)

| Feature | From | Why for us |
|---|---|---|
| Job queue with pause / resume / reorder / retry-failed, persisted | TurboFlow, AutoFlow [26][27]; MV3 lifecycle [1] | closing Chrome must not lose a chapter run |
| Per-chapter batch runs (voice/render per chapter, redo lists) | Auto Flow batches + sequential mode [10] | matches `chapters.json` and `episode.yml` test_lines |
| Review grid (clips, voice lines, fact rows) with per-item approve / send back | queue status views [26]; our gates | faster owner review; gate = PR merge stays |
| Cost caps ($ per run/day/episode) + live meter | Sider/HARPA credit complaints [21][38] | no surprise bills; GPU cap already in workflow |
| Ask mode before write / dispatch / merge; site Allow/Ask/Block for fetch | Nanobrowser [14][15] | human-in-the-loop by default |
| Stop rules: max steps, 3 failed checks, token + $ budget | Nanobrowser [14]; Anthropic [24] | no runaway loops |
| Prompt library + recipes, import/export JSON | AIPRM-style library [20], TurboFlow JSON [26] | reuse of good agent instructions |
| Run history + export (JSON/markdown) | Nanobrowser chat history [14] | audit trail, handover |
| Activity log with filters | TurboFlow [26] | debugging |
| Model list fetch + "model retired" warning | AutoMeta breakage [37] | no silent failure |
| Notifications when a run finishes or a gate waits | - | owner can leave the desk |
| Optional DOM-assist (Insert prompt into focused box only) | v1 | keep, opt-in, assist only |

## 6. What NOT to do (and why)
- **No unattended DOM automation of Flow, Midjourney, ChatGPT, Claude, Kling, Runway web apps.** Breaks on every redesign [11][20][32]; violates terms and risks bans [19][33][35]. Our engine has APIs.
- **No API-key rotation across many free keys** to dodge limits (abuse; MetaForge pattern [28]).
- **No vendor server / cloud credits / accounts.** BYOK only; nothing to breach; CWS limited-use stays simple [44].
- **No remote code or repo-defined command language** executed by the extension [7]; prompts stay text for the model.
- **No `storage.sync` for anything secret** [3][23]; no keys in logs, URLs or commits.
- **No auto-merge of gate PRs and no auto-upload to YouTube.** Owner approvals stay manual (NEVER BEND).
- **No 1000-thread parallelism.** One heavy run at a time (matches workflow concurrency) - cost and quota safety.
- **No framework/build step** unless the UI outgrows plain JS; keeps the package reviewable.

## 7. Risks
| Risk | Mitigation |
|---|---|
| Panel closed mid-agent-run | checkpoint each step (done in v1.1); resume button; GitHub runs continue server-side and alarms track them |
| Storage quota (10 MB) with long sessions | prune history, cap sessions ~4 MB, `getBytesInUse` meter, export then clear |
| Model API price changes | owner-editable price table; caps in $ and tokens |
| Prompt injection from fetched pages | tool output wrapped as data; writes only in episode folder; dispatch/merge always Ask |
| GitHub secondary rate limits | GET retries with retry-after; poll every 60 s max |
| Workflow input injection (audit O15) | extension validates inputs (done); engine: move inputs to `env:` |
| Real-Chrome bugs untested in sandbox | owner smoke test of v1.1 before v2 build |

## 8. Phased build (effort = agent work sessions of ~1-2 h)
| Phase | Content | Effort | Done when |
|---|---|---|---|
| P0 | Owner loads v1.1 in Chrome, smoke test (Keys test, one agent read, one 0-15 s test dispatch) | owner 15 min | no blocking errors |
| P1 | queue.js + background alarms + job persistence + resume; run matching | 2 sessions | close panel mid-run, reopen, job continues and finishes |
| P2 | Desk: chapter table from chapters.json, per-chapter Voice/Render, redo lists | 1 session | ch1 voice test via desk |
| P3 | cost.js: price table, $ meter, caps; GPU $ from cost.json | 1 session | cap stops a run |
| P4 | Review grid + per-item send back (PR comment) + approve chapter (merge) | 2 sessions | review ch1 entirely in grid |
| P5 | Ask policy per tool, site Allow/Ask/Block, tool-output-as-data, history summariser | 1 session | injection test page cannot trigger a write |
| P6 | Library + History + import/export; notifications | 1 session | export history JSON |
| P7 | a11y pass, real-Chrome checklist, README v2, zip | 1 session | owner sign-off |
Total ~9 sessions + owner tests. Each phase: tests, commit, zip, short owner note.

## 9. Tie-in with agents 1-4 and the engine
- **Agent 1 Research+Writer:** Desk runs it to `topic` and `script` gates; facts table feeds Review grid (sources column, R01 flags from fm_check).
- **Agent 2 Director:** produces `chapters.json` -> Desk chapter table; `scene_sheet` and `chapters` gates shown as queue rows waiting for owner.
- **Agent 3 Builder:** each chapter = jobs: voice test (episode.yml test_lines) -> render preview -> fm_check summary -> Review grid.
- **Agent 4 Voice+Finish:** final build job (whole episode) only from the owner's Desk button with $ cap; `final` gate = PR merge; upload stays manual.
- **Engine:** unchanged contract: `workflow_dispatch` inputs (ep, test_lines, preview_seconds, redo_images, redo_lines, max_gpu_seconds) -> `summary.json` / `cost.json` on branch `preview`; gates via `gates.yml` PR merges; Modal keys stay GitHub secrets.
