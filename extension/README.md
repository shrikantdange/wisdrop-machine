# Wisdrop Studio (Chrome side panel) v1

A side panel that runs the 4 Wisdrop agents (`prompts/01-04`) with **any AI key**, drives the engine on **GitHub Actions + Modal**,
and stops at every **owner gate** for Approve / Send back. Plain JS/HTML/CSS, Manifest V3, no build step, no remote code.

## Install (3 steps)
1. Download/unzip this `extension/` folder (or clone the repo).
2. Chrome -> `chrome://extensions` -> turn on **Developer mode** -> **Load unpacked** -> pick the `extension/` folder.
3. Click the Wisdrop icon (pin it) -> side panel opens -> **Keys** tab: paste an AI key + a GitHub token, press Test, Save.

## Set up
- **AI key (universal box):** paste any key. Detected by prefix: `sk-ant-` Anthropic, `AIza` Gemini, `sk-or-` OpenRouter,
  `gsk_` Groq, `sk-` OpenAI. DeepSeek, Mistral, Together, Ollama, LM Studio or any OpenAI-compatible API: pick the provider
  or set **Base URL** + **Model**. **Fetch models** fills the model list where the API offers it. Chrome asks to allow that
  provider's host the first time (optional host permission, per provider).
  - Ollama: start it with `OLLAMA_ORIGINS=chrome-extension://*` so the panel may call `http://localhost:11434/v1`.
- **GitHub:** fine-grained personal access token, **only this repo**, permissions: Contents R/W, Actions R/W,
  Pull requests R/W, Metadata R. Modal keys stay as GitHub Actions secrets; the extension never sees them.
- **Lock (optional):** set a passphrase: all keys are encrypted with AES-GCM (PBKDF2-SHA256, 250k rounds). The panel asks
  for it each time it opens.

## Panels
| panel | does |
|---|---|
| Agents | pick agent 1-4 + model, chat; the agent works with tools; step log; owner-gate card (Approve / Send back with notes). Copy prompt / Insert prompt into the focused box of the current page (you press send there yourself). |
| Pipeline | episode stages from the repo (`episodes/<ep>/` files + `state.json`), next stage highlighted. |
| Review | last test preview video (branch `preview`), voice line players (`<ep>/vo`), fact table with sources (`research.md`), open gate PRs: Approve = merge, Send back = PR comment. |
| Run | Voice chapter / Render chapter / Build final -> `episode.yml` with `test_lines` from `chapters.json`, `max_gpu_seconds`, redo lists; recent runs. Every dispatch asks you first. |
| Cost | `cost.json` of the last test run + AI tokens used this session. |
| Keys | universal AI box, GitHub token, passphrase, forget all. |

## How the agent loop works
1. The panel loads the agent prompt (`prompts/0N_*.md`) from GitHub, optionally with `docs/DIRECTOR_PROMPT.md` +
   `docs/FAILURE_MODES.md` attached (otherwise the agent reads them on demand), and appends a short tool protocol.
2. Each model reply is ONE JSON action: `{"say","tool","args"}`. Works with any chat model (no native tool calling needed).
3. Tools: `read_file`, `list_dir` (episodes/, docs/, prompts/, schemas/), `write_file` (**current episode folder only**,
   never `state.json`, refused if the text looks like a key), `dispatch_episode` (asks you; capped by Run -> max_gpu_seconds),
   `poll_run`, `read_summary`, `read_cost`, `fetch_url` (asks you to allow each new site), `gate`, `done`.
4. Plan -> tool -> result -> continue, until **gate** (hard stop: topic, script, scene_sheet, chapters, final), **done**,
   **max steps** or the **token budget**. Stop button aborts at once. Every step is in the log.
5. Approve or Send back with notes -> the agent continues from your answer. Upload is always yours (never the agent).

## Security notes
- Keys live only in `chrome.storage.local` of this browser: never synced, never committed, never written to the log
  (the log and chat redact anything key-shaped). Agent writes are scanned and refused if they look like a secret.
- Host access is requested per provider at runtime; only `api.github.com` is granted at install.
- No remote code; strict extension CSP. Insert-into-chat only types into the box you focused; it never clicks other sites' buttons.
- Agents commit to `main` inside `episodes/<ep>/` with messages starting `studio:`; owner approvals stay PR merges (gates.yml).

## Tests (free)
`cd extension && node test/run.js` - adapters' request building for every provider (mock fetch), vault crypto,
redaction, path guards, the agent loop stopping at a gate, GitHub client requests.
