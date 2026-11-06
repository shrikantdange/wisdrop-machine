# Wisdrop Studio - extension research (2026-11-06)

Scope: what similar Chrome extensions already do, how they are built, what breaks for their users, what Chrome and the AI sites allow, and what that means for Wisdrop Studio. Every claim has a numbered source [n]; all pages were opened on 2026-11-06 (a few blocked pages are marked "via search excerpt").

## 1. Short answer

1. **Two families exist.** (a) *DOM-automation queue tools* that drive a website you are signed into (Auto Flow / TurboFlow / AutoFlow for Google Flow, AutoMeta and MetaForge for Adobe Stock, MidBot / AutoJourney for Midjourney). (b) *API sidebars / agents* that call model APIs with a key (Sider, HARPA, Monica, MaxAI, Merlin, BYOK AI Chat, Nanobrowser). Wisdrop Studio is family (b) plus a GitHub/Modal engine, which is the safer family.
2. **DOM automation is fragile and often against the site's terms.** Reviews of Auto Flow are mostly negative: crashes, random stops, breaks after Flow updates [11]. AIPRM and Superpower ChatGPT broke on many ChatGPT UI updates [20][31][32]. Midjourney's terms forbid automated tools and allow bans [33][34]; Google's terms forbid automated access against machine-readable rules [19]; one Flow tool's own terms warn Google may suspend your account [35].
3. **The winning UX ideas are simple:** side panel; paste or import a list -> queue rows with status; pause / resume / reorder / retry-failed; per-batch settings; import/export JSON; auto-named outputs; speed control that slows down on rate limits; a detailed activity log [10][26][27][12].
4. **Chrome MV3 rules that matter:** service worker dies after 30 s idle or 5 min per call, so long jobs must persist state to storage and resume [1]; `storage.local` is 10 MB and readable by content scripts unless the access level is changed [3]; alarms fire at most every 30 s [5]; optional host permissions requested at runtime from a user gesture [6]; no remote code, no eval, no interpreters of fetched commands [7]; narrowest permissions [9].
5. **BYOK security reality:** extension storage is not encrypted at rest; keep keys out of `storage.sync`, out of content scripts and logs, and encourage a per-app key with a spend cap [23][29]. Anthropic needs the `anthropic-dangerous-direct-browser-access: true` header for browser calls [13]; Ollama blocks extension origins unless `OLLAMA_ORIGINS` includes `chrome-extension://*` [22]; Google says never ship Gemini keys in client code (BYOK typed by the user is the accepted pattern) [16].

## 2. Comparison table

| Tool | What it does | UI | How it works | Price | What users complain about |
|---|---|---|---|---|---|
| Auto Flow (duckmartians) [10] | batch images/videos on Google Flow, auto-save | panel + Flow tab | DOM automation in your signed-in Flow tab; uses your Flow credits; up to 1000 threads on top plan | free / $3-$10 per month | (see Auto Flow Veo below) |
| Auto Flow - Auto Veo (30K users) [11] | same | panel | DOM automation | $10/mo, free 10 prompts/day | crashes, random stops, auto-download fails, breaks after Flow updates, support |
| TurboFlow (10K users, 4.4) [26] | queue of batches, auto-chain, upscale, download | panel | DOM automation; retries, slows on rate limits, failed list, activity log, JSON import/export | paid tiers | (good rating; relies on Flow UI) |
| AutoFlow - Batch [27] | queue, pause/resume/reorder, retry | side panel | DOM automation | free/pro | small user base |
| AutoMeta for AdobeStock (1-2K users) [17] | titles + keywords on Adobe Stock upload page, "Get All Metadata" batch | in-page buttons | content script on contributor.stock.adobe.com + Gemini API (BYOK, free tier) | free | a hard-coded Gemini model was retired, so it broke (search excerpt [37]) |
| MetaForge (Adobe Stock) [28] | same, 3 providers, key rotation | side panel | content script + BYOK (Gemini/OpenAI/Groq) | free | key rotation to dodge limits is a policy grey zone |
| MidBot / AutoJourney (Midjourney) [34][36] | CSV prompt queue, auto upscale + download | popup / panel | DOM automation of midjourney.com / Discord | paid | ToS forbids automation; user-reported bans; breaks when UI changes |
| Sider (5M users) [21] | multi-model chat, summaries, agent "Hand" | sidebar | vendor cloud credits | free 30 basic credits/day, paid tiers | credit limits unclear, "unlimited" not unlimited (search excerpt [38]) |
| HARPA AI (400K users, 4.5-4.7) [18] | page-aware chat, monitors, automation | sidebar (Alt+A) | vendor cloud or BYOK or "web session" | $12 / $19 per month (annual), $240 life | steep learning curve, broad trust needed |
| MaxAI [39] | sidebar chat, rewrite | sidebar | vendor cloud | $12/mo yearly, $30 monthly | - |
| AIPRM / Superpower ChatGPT [20][31][32] | prompt library injected into ChatGPT | overlay inside chatgpt.com | content script DOM injection | freemium | UI broken after each ChatGPT update; conflicts between extensions |
| BYOK AI Chat (open source) [30] | multi-provider chat | side panel | API calls from service worker, `chrome.storage.local` | free | small, basic |
| Nanobrowser (13K stars) [14][15] | web agent, any model | side panel | agent loop + `chrome.debugger` (CDP) control layer; Ask mode before submit/send/delete/upload; stops after 3 failed checks; only while browser open | free, BYOK | needs tool-calling models |

## 3. What each family teaches

### 3.1 DOM-automation queue tools (Auto Flow family)
- Pattern: side panel queue + content script that types the prompt, clicks generate, waits, downloads, renames [10][12][26].
- Good: rows with status, threads/concurrency limit, sequential mode (output of row n is the reference for row n+1), character / reference libraries, per-batch settings, import/export JSON, retry failed only, random delay [10][26][36].
- Bad: every site redesign breaks them [11][20]; "unlimited" plans still burn the user's own credits [10]; account risk [33][35]. AIPRM even tells users to uninstall other ChatGPT extensions because injected UIs fight each other [31].
- **Lesson for Wisdrop:** copy the queue UX, not the DOM driving. Our engine already runs on GitHub Actions + Modal via APIs, so we never need to puppet a site.

### 3.2 Stock-metadata tools (AutoMeta family)
- Pattern: content script on one site + BYOK vision model to fill forms [17][28].
- Lessons: never hard-code one model name (AutoMeta broke when a preview model was retired [37]); let the user pick from a fetched model list (v1 already has Fetch models). Key rotation across many free keys to beat rate limits is abuse-prone - do not do it.

### 3.3 API sidebars (Sider, HARPA, MaxAI, Monica, Merlin)
- Pattern: sidebar chat, prompt/command library, page-aware context, credits [18][21][39].
- Complaints are about money transparency, not tech: credit systems users do not understand [21][38].
- **Lesson:** show cost live in tokens and dollars, with a hard cap per run and per day.

### 3.4 Agent extensions (Nanobrowser)
- One agent per chat, real tools, "Ask" mode that pauses before any irreversible action, site Allow/Ask/Block list, stops after 3 failed checks, long chats summarised, chat history with re-run [14][15].
- Matches the agent guidance from Anthropic: clear stopping conditions (max iterations), human checkpoints, simple loops [24]; small, well-named, namespaced tools that return token-efficient, meaningful results and clear errors [41].

## 4. Chrome MV3 facts (official docs)
- **Service worker lifetime:** terminated after 30 s idle, if one event/API call takes over 5 min, or a fetch takes over 30 s to answer; global variables are lost - persist to `chrome.storage` or IndexedDB [1]. Long agent runs must not live only in SW memory.
- **Side panel:** extension page with full Chrome API access; `setPanelBehavior({openPanelOnActionClick:true})`; `sidePanel.open()` needs a user gesture; per-tab or global panels; onOpened/onClosed events (Chrome 141/142) [2]. A side panel page lives while open, so a loop running there survives SW sleep but dies when the panel closes.
- **Storage:** `local` 10 MB (more with `unlimitedStorage`), exposed to content scripts by default (change with `setAccessLevel`); `session` 10 MB in memory, cleared on restart, not exposed to content scripts by default; `sync` ~100 KB and syncs to the Google account - wrong place for secrets [3].
- **Offscreen documents:** hidden DOM for blobs, DOMParser, audio, clipboard etc.; only `runtime` API inside; one open at a time [4]. Useful later for big-file hashing or audio checks.
- **Alarms:** min period 30 s (Chrome 120+); missed alarms fire once after sleep; re-create on startup [5]. Use for polling GitHub runs instead of setTimeout in the SW.
- **Optional permissions:** request at runtime in a user gesture; `https://*/*` in optional hosts allows runtime-discovered hosts [6].
- **activeTab:** temporary access to the current tab after the user invokes the extension; lost on navigation [42].
- **CSP:** extension pages minimum `script-src 'self' 'wasm-unsafe-eval'; object-src 'self'`; cannot be relaxed (no unsafe-eval) [8]. Avoid innerHTML; build DOM nodes; never send secrets to content scripts [43].

## 5. Chrome Web Store policy
- **No remote code:** no remote `<script>`, no eval of fetched strings, no interpreter for fetched commands "even if fetched as data" [7]. *Note for us:* loading agent **prompts** (text instructions to an LLM) from GitHub is data for a model, not code; the extension's own tool set is fixed in the package. Keep it that way: never let the repo ship JS or a "command language" the extension executes.
- **Permissions:** narrowest permissions; no "future proofing" [9].
- **Limited use of user data:** use data only for the single purpose; transfers only to provide the feature; no humans reading data [44].

## 6. BYOK key security
- Extension storage is not encrypted at rest; anyone with the profile can read it; keep keys out of `storage.sync`, out of content scripts; encourage a capped per-app key [23].
- Better builds keep keys only in privileged contexts, encrypt with WebCrypto AES-GCM (non-extractable key) and wipe on sign-out, while stating honestly that encryption only raises the bar [29].
- Anthropic: browser calls need `anthropic-dangerous-direct-browser-access: true`; risk is a leaked embedded key, acceptable when the user brings their own [13]. Anthropic's monthly spend cap returns 429 with no retry-after; retrying does not help [40].
- Gemini: never hard-code keys in client code; use a backend for shipped apps [16]. (BYOK typed by the owner is the accepted exception.)
- Ollama: allows only localhost/127.0.0.1 origins; extensions need `OLLAMA_ORIGINS=chrome-extension://*` (or the exact extension id) [22].
- GitHub REST: 5,000 req/h per token; secondary limits answer 403/429 - honour `retry-after` and `x-ratelimit-remaining: 0` [25].

## 7. Terms of the AI sites on automation
- **Midjourney:** "You may not use automated tools to access, interact with, or generate Assets through the Services"; may suspend/ban at any time [33][34].
- **Google (Flow, Gemini app):** no "automated means to access content ... in violation of the machine-readable instructions" plus the Generative AI Prohibited Use Policy [19]. Flow automation tools disclaim that Google may rate-limit, suspend or close accounts [35].
- **ChatGPT / Claude web apps:** extensions that inject UI break on each redesign [20][32]; automating the consumer chat UI is not needed when APIs exist.
- **Conclusion:** use official APIs (model APIs, GitHub, Modal). A DOM-assist mode, if ever built, must be *assist only* (fill a box the owner focused; owner presses send), opt-in per site, and never loop unattended.

## 8. Sources (opened 2026-11-06)
1. Chrome: Extension service worker lifecycle - https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle
2. Chrome: chrome.sidePanel API - https://developer.chrome.com/docs/extensions/reference/api/sidePanel
3. Chrome: chrome.storage API - https://developer.chrome.com/docs/extensions/reference/api/storage
4. Chrome: chrome.offscreen API - https://developer.chrome.com/docs/extensions/reference/api/offscreen
5. Chrome: chrome.alarms API - https://developer.chrome.com/docs/extensions/reference/api/alarms
6. Chrome: chrome.permissions API - https://developer.chrome.com/docs/extensions/reference/api/permissions
7. CWS: MV3 additional requirements (remote code) - https://developer.chrome.com/docs/webstore/program-policies/mv3-requirements
8. Chrome: Manifest content_security_policy - https://developer.chrome.com/docs/extensions/reference/manifest/content-security-policy
9. CWS: Use of permissions - https://developer.chrome.com/docs/webstore/program-policies/permissions
10. Auto Flow README (duckmartians) - https://github.com/duckmartians/Auto-Flow
11. ExtWise: Auto Flow - Auto Veo review analysis - https://extwise.com/extension/auto-flow-auto-veo-nano-banana-pro/
12. AutoFlow blog: batch generate on Google Flow - https://www.auto-flow.studio/blog/how-to-batch-generate-ai-videos-google-flow (search excerpt)
13. Simon Willison: Anthropic CORS header - https://simonwillison.net/2024/Aug/23/anthropic-dangerous-direct-browser-access/
14. Nanobrowser v0.3.0 release - https://github.com/nanobrowser/nanobrowser/releases/tag/v0.3.0
15. Nanobrowser docs - https://nanobrowser.ai/docs
16. Google AI: Gemini API keys - https://ai.google.dev/gemini-api/docs/api-key
17. CWS: AutoMeta for AdobeStock - https://chromewebstore.google.com/detail/autometa-for-adobestock/gofdlplbcbhanomlnnmihfakocoodgga
18. HARPA AI pricing - https://harpa.ai/pricing
19. Google Terms of Service - https://policies.google.com/terms?hl=en-US
20. AIPRM forum: UI broken by ChatGPT update 2025-04-03 - https://forum.aiprm.com/t/solved-aiprm-ui-partially-broken-for-some-users-due-to-chatgpt-update-on-april-3-2025/78675
21. Sider credits FAQ - https://sider.ai/help-center/faqs/sider-credit-issue
22. Ollama FAQ (origins) - https://docs.ollama.com/faq
23. Omni Sidekick: how your API key is stored - https://omnisidekick.app/trust/api-key-security
24. Anthropic: Building effective agents - https://www.anthropic.com/engineering/building-effective-agents
25. GitHub: REST API rate limits - https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
26. CWS: TurboFlow - https://chromewebstore.google.com/detail/turboflow-auto-flow-on-go/bnfjjfgjpdagdiiiifdkjbjnadgdjaoe
27. CWS: AutoFlow - Batch for Google Flow - https://chromewebstore.google.com/detail/autoflow-%E2%80%94-batch-for-goog/fohjehblomodhghkjbemblplknjinaln
28. ExtScope: MetaForge by TAS - https://extscope.org/extension/mgkncjjdibphdjhfcjfakihecmkiecmc
29. Inquiso: security and threat model - https://inquisoai.com/docs/design/05-security/
30. BYOK AI Chat (GitHub) - https://github.com/alvescrafter/byok-ai-chat
31. AIPRM: Chrome extensions that break AIPRM - https://www.aiprm.com/en-ie/blog/when-chrome-extensions-break-aiprm/
32. Superpower ChatGPT release notes - https://spchatgpt.com/release-notes/
33. Licenseware: Midjourney ToS rule (quotes ToS s.1) - https://wiki.licenseware.io/catalog/rules/midjourney-no-automated-access-or-generation/
34. Extino: Midjourney bulk prompts + ToS - https://extino.net/blog/midjourney-bulk-prompts-batch-generate
35. Flow Connector terms - https://flow-connector.flowconnector.workers.dev/terms
36. AutoJourney docs (ban disclaimer, search excerpt) - https://docs.autojourney.ai/en-US/guide
37. Chrome-Stats: AutoMeta reviews (search excerpt; page blocked) - https://chrome-stats.com/d/gofdlplbcbhanomlnnmihfakocoodgga/reviews
38. Trustpilot: Sider reviews (search excerpt; page blocked) - https://www.trustpilot.com/review/sider.ai
39. MaxAI pricing - https://www.maxai.co/pricing/
40. Anthropic API rate limits - https://docs.anthropic.com/en/api/rate-limits
41. Anthropic: Writing tools for agents - https://www.anthropic.com/engineering/writing-tools-for-agents
42. Chrome: activeTab permission - https://developer.chrome.com/docs/extensions/develop/concepts/activeTab
43. Chrome: Stay secure - https://developer.chrome.com/docs/extensions/develop/security-privacy/stay-secure
44. CWS: Limited Use - https://developer.chrome.com/docs/webstore/program-policies/limited-use
