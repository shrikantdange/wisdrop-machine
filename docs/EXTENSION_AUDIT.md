# Wisdrop Studio v1 audit (2026-11-06)

Audited: every file in `extension/` (manifest.json, background.js, sidepanel.html/css/js, lib/agent.js, lib/github.js, lib/providers.js, lib/store.js, test/run.js, README). Checked against `docs/EXTENSION_RESEARCH.md` (sources [n] there).
Checks run: `node --check` on all 7 JS files (pass); `node extension/test/run.js` (11 groups pass, incl. new v1.1 group). Headless Chromium: **not available in the sandbox** (no chromium/playwright) - real-Chrome load test still open (owner).

Result: v1 -> **v1.1** (manifest 1.1.0). 11 issues fixed, 14 open items (13 to do in v2 or accepted, 1 info).

Severity: **H** = can cause damage or spend / lose work; **M** = wrong behaviour or weak guard; **L** = polish.

## Fixed in v1.1

| # | Sev | Area | Finding | Fix |
|---|---|---|---|---|
| F1 | H | write guard | `checkWritePath` trusted the Episode field. If the field said `docs` (or was empty) the agent could write anywhere in the repo, e.g. `AGENTS.md` or workflows. | `checkEp()`: episode must match `episodes/<name>`; enforced in writes, dispatch, and every panel action. Test added. |
| F2 | H | agent protocol | `extractAction` cut the JSON at the first ``` fence. Any `write_file` whose markdown content has a code block was truncated or failed (most of our docs have code blocks). | Scan braces from the opening fence over the rest of the text (string-aware). Test with fenced content added. |
| F3 | H | GPU spend | `dispatch_episode` could send `max_gpu_seconds = "NaN"` (non-numeric model output) or 0/negative; workflow behaviour then undefined. Empty `test_lines` from the agent = whole-episode build. | `dispatchInputs()`: integer within owner cap (default 120 s), else the cap; line lists must match `0-15,3,7`; agent cannot dispatch a whole-episode build (owner uses Run tab, which asks). Tests added. |
| F4 | H | lost work | Agent session lived only in panel memory; closing the panel or a crash lost the whole chat, step log and a pending gate. (The loop runs in the side panel page, not the service worker, so SW sleep [1] is not the killer - panel close is.) | Session (messages, tokens, log tail, pending gate) saved to `chrome.storage.local` after every step, key-shaped strings redacted, capped ~4 MB (10 MB quota [3]); restored on open with a note; New chat clears it. |
| F5 | M | rate limits | No retry on 429/5xx/529 from model APIs; one overload error killed a run. | `fetchRetry`: 4 tries, exponential backoff + jitter, honours `retry-after` (max 30 s); never retries 4xx auth errors; stops at once on Anthropic spend-cap 429 [40]. Tests added. |
| F6 | M | rate limits | GitHub GETs had no retry on 429/5xx/secondary limit [25]. | GET-only retry (3 tries). Writes/dispatch never retried (no double dispatch). |
| F7 | M | large files | `fetch_url` read any size page into memory, no timeout, ignored HTTP errors. | 20 s timeout, refuse > 3 MB, read cap 3 MB, error on non-2xx, `credentials: 'omit'`. Result still cut to 12k chars for the model. |
| F8 | L | gate guard | `state.json` block was case-sensitive (`STATE.json` passed). | Case-insensitive. |
| F9 | L | Run tab | Bad Episode field gave a raw error deep in a call. | Run tab checks the episode first and focuses the field. |
| F10 | M | keys at rest | `storage.local` (holds the vault) is readable by content scripts by default [3]. | `setAccessLevel(TRUSTED_CONTEXTS)` in background + panel. |
| F11 | L | weak passphrase | No minimum length. | >= 10 characters. |

## Open (not fixed now; reason)

| # | Sev | Area | Finding | Plan |
|---|---|---|---|---|
| O1 | M | keys at rest | Default vault is plain `chrome.storage.local` (passphrase optional); storage is not encrypted at rest [23]. | v2: nudge passphrase on first save; recommend a capped, per-app key per provider. |
| O2 | M | long runs | Loop dies when the panel closes; v1.1 restores the chat but does not resume a run automatically. GitHub run polling is manual. | v2 job queue: jobs persisted in storage, SW `alarms` (>= 30 s [5]) poll GitHub runs and notify; panel resumes the job on open. |
| O3 | M | cost cap | Budget is tokens only; no $ estimate, no daily cap across chats. | v2: price table per model (owner-editable), $ per run and per day, hard stop. |
| O4 | M | context growth | Every tool result (up to 12k chars) stays in the chat; long runs overflow small models. | v2: summarise old tool results (keep owner messages verbatim, as Nanobrowser does [14]). |
| O5 | M | prompt injection | `fetch_url` and repo text can instruct the model. Guards: writes only inside the episode, dispatch needs owner click, gates are PR merges. | v2: mark tool output as data in the protocol; per-site Allow/Ask/Block list; show the domain in every fetch card. |
| O6 | M | permissions | `optional_host_permissions` includes `https://*/*` (needed for custom base URLs and fetch_url) - CWS reviewers may ask why [9]. `scripting`+`activeTab` only serve "Insert prompt". | If we publish: justify in listing, or drop Insert-prompt and `scripting`. Personal use (unpacked): fine. |
| O7 | L | dispatch run id | After dispatch, "latest run" may be someone else's run. | v2: match run by `created_at` > dispatch time and `display_title`/inputs. |
| O8 | L | abort | Stop aborts the model call but not an in-flight GitHub call. | Pass the signal into GitHub client. |
| O9 | L | blobs | Preview video loaded as a blob through the contents API; files > 100 MB fail. | Link to the run artifact instead of blob for big files. |
| O10 | L | a11y | Tabs, labels and live regions OK; confirm cards are `alertdialog` without focus trap; no visible focus style check; contrast not measured. | v2 UI pass with axe in a real Chrome. |
| O12 | L | model names | Default model ids may be retired (AutoMeta broke this way [37]). | v1 already has Fetch models; v2 warns when a saved model disappears from the list. |
| O13 | L | real Chrome | Never loaded in a real Chrome; no headless Chromium in sandbox. | Owner: load unpacked, Keys -> Test; report errors. |
| O15 | M | workflow (engine side) | `episode.yml` puts `${{ inputs.* }}` straight into `run:` shell lines (e.g. `--force "${{ inputs.redo_images }}"`); a crafted input could inject shell. v1.1 now validates every agent dispatch input (digits/ranges, picture ids), which closes it from the extension side. | Engine fix later: pass inputs via `env:` and quote. Not changed in this run (workflow edit = engine change, needs a test run). |
| O14 | info | secrets in commits | Agent writes are scanned for key shapes and refused; redaction in log/UI. OK. Modal keys never reach the extension (GitHub secrets). OK. | keep |

## Checklist results
- Manifest permissions: `sidePanel, storage, scripting, activeTab, clipboardWrite`; host `api.github.com` only; providers optional at runtime. Least privilege acceptable; see O6.
- CSP: `script-src 'self'; object-src 'self'` - at the MV3 minimum [8]. OK.
- Remote code: none; prompts from GitHub are LLM text, tools are fixed in the package [7]. OK.
- Key storage: local only, never sync; AES-GCM + PBKDF2 250k when a passphrase is set; redaction. See O1.
- SW sleep: background.js only sets panel behaviour; the loop runs in the panel page, so SW sleep does not kill it [1]. Panel close does (F4 restore, O2 resume).
- CORS: Anthropic header present [13]; Gemini key sent in `x-goog-api-key` header (not URL); Ollama README tells owner to set `OLLAMA_ORIGINS=chrome-extension://*` [22] (better: the exact extension id).
- GitHub token: README asks for fine-grained, this repo only, Contents/Actions/PRs R/W + Metadata R. OK.
- Error handling: per-tool errors return to the model as `ERROR:` text; two protocol failures stop the loop. OK.
- Gate enforcement: model `gate` = hard stop; owner approval in Review = PR merge (gates.yml). `state.json` never written by agent. OK.
- GPU spend: every agent dispatch asks the owner (inline card) and is capped (F3). OK.
- XSS: all model/repo text goes through `textContent`; links only for `http(s)`; no innerHTML. OK [43].
