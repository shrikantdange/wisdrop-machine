// Universal AI box: one adapter layer for any AI provider.
// Pure functions (build request / parse response) are unit-tested in node with a mock fetch.
// Keys never leave this module except in the request header to the provider itself.

export const PROVIDERS = {
  openai:     { name: 'OpenAI',            kind: 'openai',    base: 'https://api.openai.com/v1',            model: 'gpt-4o-mini' },
  openrouter: { name: 'OpenRouter',        kind: 'openai',    base: 'https://openrouter.ai/api/v1',         model: 'openrouter/auto' },
  groq:       { name: 'Groq',              kind: 'openai',    base: 'https://api.groq.com/openai/v1',       model: 'llama-3.3-70b-versatile' },
  deepseek:   { name: 'DeepSeek',          kind: 'openai',    base: 'https://api.deepseek.com/v1',          model: 'deepseek-chat' },
  mistral:    { name: 'Mistral',           kind: 'openai',    base: 'https://api.mistral.ai/v1',            model: 'mistral-large-latest' },
  together:   { name: 'Together',          kind: 'openai',    base: 'https://api.together.xyz/v1',          model: '' },
  anthropic:  { name: 'Anthropic (Claude)', kind: 'anthropic', base: 'https://api.anthropic.com/v1',        model: 'claude-sonnet-4-5' },
  gemini:     { name: 'Google Gemini',     kind: 'gemini',    base: 'https://generativelanguage.googleapis.com/v1beta', model: 'gemini-2.5-flash' },
  ollama:     { name: 'Ollama (local)',    kind: 'openai',    base: 'http://localhost:11434/v1',            model: 'llama3.1', nokey: true },
  lmstudio:   { name: 'LM Studio (local)', kind: 'openai',    base: 'http://localhost:1234/v1',             model: '', nokey: true },
  custom:     { name: 'Custom (OpenAI-compatible)', kind: 'openai', base: '',                               model: '' },
};

// Key prefix -> provider. Order matters: specific prefixes before the generic "sk-".
const PREFIXES = [['sk-ant-', 'anthropic'], ['sk-or-', 'openrouter'], ['gsk_', 'groq'], ['AIza', 'gemini'], ['sk-', 'openai']];
export function detectProvider(key) {
  const k = (key || '').trim();
  for (const [p, id] of PREFIXES) if (k.startsWith(p)) return id;
  return null; // unknown: use the base URL + model fields (OpenAI-compatible)
}

// Fill a profile {provider, base, model, key} with defaults.
export function resolve(profile) {
  const p = PROVIDERS[profile.provider] || PROVIDERS.custom;
  const base = (profile.base || p.base || '').replace(/\/+$/, '');
  if (!base) throw new Error('Base URL needed for a custom provider');
  return { kind: p.kind, base, model: profile.model || p.model, key: (profile.key || '').trim(), nokey: !!p.nokey, provider: profile.provider };
}

export function originPattern(base) {
  const u = new URL(base);
  return `${u.protocol}//${u.hostname}/*`;
}

function oaHeaders(c) {
  const h = { 'Content-Type': 'application/json' };
  if (c.key) h.Authorization = `Bearer ${c.key}`;
  if (c.provider === 'openrouter') { h['HTTP-Referer'] = 'https://github.com/shrikantdange/wisdrop-machine'; h['X-Title'] = 'Wisdrop Studio'; }
  return h;
}
function anHeaders(c) {
  return { 'Content-Type': 'application/json', 'x-api-key': c.key, 'anthropic-version': '2023-06-01', 'anthropic-dangerous-direct-browser-access': 'true' };
}

// messages: [{role:'system'|'user'|'assistant', content:string}]
export function buildChatRequest(profile, messages, opts = {}) {
  const c = resolve(profile);
  const maxTokens = opts.maxTokens || 2048, temperature = opts.temperature ?? 0.3;
  if (c.kind === 'anthropic') {
    const system = messages.filter(m => m.role === 'system').map(m => m.content).join('\n\n');
    const msgs = mergeSame(messages.filter(m => m.role !== 'system'));
    const body = { model: c.model, max_tokens: maxTokens, temperature, messages: msgs };
    if (system) body.system = system;
    return { url: `${c.base}/messages`, init: { method: 'POST', headers: anHeaders(c), body: JSON.stringify(body) } };
  }
  if (c.kind === 'gemini') {
    const system = messages.filter(m => m.role === 'system').map(m => m.content).join('\n\n');
    const contents = mergeSame(messages.filter(m => m.role !== 'system'))
      .map(m => ({ role: m.role === 'assistant' ? 'model' : 'user', parts: [{ text: m.content }] }));
    const body = { contents, generationConfig: { maxOutputTokens: maxTokens, temperature } };
    if (system) body.systemInstruction = { parts: [{ text: system }] };
    const model = c.model.replace(/^models\//, '');
    return { url: `${c.base}/models/${encodeURIComponent(model)}:generateContent`,
      init: { method: 'POST', headers: { 'Content-Type': 'application/json', 'x-goog-api-key': c.key }, body: JSON.stringify(body) } };
  }
  const body = { model: c.model, messages, max_tokens: maxTokens, temperature };
  return { url: `${c.base}/chat/completions`, init: { method: 'POST', headers: oaHeaders(c), body: JSON.stringify(body) } };
}

// Anthropic and Gemini want strictly alternating roles starting with user.
function mergeSame(msgs) {
  const out = [];
  for (const m of msgs) {
    if (out.length && out[out.length - 1].role === m.role) out[out.length - 1] = { role: m.role, content: out[out.length - 1].content + '\n\n' + m.content };
    else out.push({ role: m.role, content: m.content });
  }
  if (out.length && out[0].role !== 'user') out.unshift({ role: 'user', content: '(start)' });
  return out;
}

export function parseChatResponse(kind, j) {
  if (j && j.error) throw new Error(typeof j.error === 'string' ? j.error : (j.error.message || JSON.stringify(j.error)));
  if (kind === 'anthropic') {
    const text = (j.content || []).filter(b => b.type === 'text').map(b => b.text).join('');
    return { text, usage: { in: j.usage?.input_tokens || 0, out: j.usage?.output_tokens || 0 } };
  }
  if (kind === 'gemini') {
    const parts = j.candidates?.[0]?.content?.parts || [];
    return { text: parts.map(p => p.text || '').join(''), usage: { in: j.usageMetadata?.promptTokenCount || 0, out: j.usageMetadata?.candidatesTokenCount || 0 } };
  }
  return { text: j.choices?.[0]?.message?.content || '', usage: { in: j.usage?.prompt_tokens || 0, out: j.usage?.completion_tokens || 0 } };
}

export function buildModelsRequest(profile) {
  const c = resolve(profile);
  if (c.kind === 'anthropic') return { url: `${c.base}/models?limit=100`, init: { headers: anHeaders(c) } };
  if (c.kind === 'gemini') return { url: `${c.base}/models?pageSize=200`, init: { headers: { 'x-goog-api-key': c.key } } };
  return { url: `${c.base}/models`, init: { headers: oaHeaders(c) } };
}

export function parseModels(kind, j) {
  if (kind === 'gemini') return (j.models || []).filter(m => (m.supportedGenerationMethods || []).includes('generateContent')).map(m => m.name.replace(/^models\//, ''));
  return (j.data || j.models || []).map(m => m.id || m.name).filter(Boolean).sort();
}

async function readJson(res) {
  const t = await res.text();
  let j; try { j = JSON.parse(t); } catch { j = null; }
  if (!res.ok) {
    const msg = j?.error?.message || j?.error || j?.message || t.slice(0, 300);
    throw new Error(`HTTP ${res.status}: ${typeof msg === 'string' ? msg : JSON.stringify(msg)}`);
  }
  return j;
}

// Retry 429 / 5xx / 529 (overloaded) with exponential backoff + jitter, honouring Retry-After (capped 30 s).
// A chat call has no side effects, so a retry is safe. Auth/4xx errors fail at once.
export const RETRY = new Set([408, 409, 425, 429, 500, 502, 503, 504, 529]);
export async function fetchRetry(fetchImpl, url, init = {}, { tries = 4, baseMs = 1000, sleep = ms => new Promise(r => setTimeout(r, ms)) } = {}) {
  for (let i = 1; ; i++) {
    let res;
    try { res = await fetchImpl(url, init); }
    catch (e) { if (init.signal?.aborted || i >= tries) throw e; await sleep(baseMs * 2 ** (i - 1)); continue; }
    if (!RETRY.has(res.status) || i >= tries || init.signal?.aborted) return res;
    // Anthropic monthly spend cap answers 429 with no retry-after: retrying cannot help, stop at once.
    if (res.status === 429 && !res.headers?.get?.('retry-after') && res.clone) { try { if ((await res.clone().text()).includes('spend_limit')) return res; } catch {} }
    const ra = Number(res.headers?.get?.('retry-after'));
    await sleep(Math.min(30000, Number.isFinite(ra) && ra > 0 ? ra * 1000 : baseMs * 2 ** (i - 1) * (1 + Math.random() * 0.25)));
  }
}

export async function chat(profile, messages, opts = {}, fetchImpl = globalThis.fetch) {
  const { url, init } = buildChatRequest(profile, messages, opts);
  const res = await fetchRetry(fetchImpl, url, { ...init, signal: opts.signal }, opts.retry);
  return parseChatResponse(resolve(profile).kind, await readJson(res));
}

export async function listModels(profile, fetchImpl = globalThis.fetch) {
  const { url, init } = buildModelsRequest(profile);
  return parseModels(resolve(profile).kind, await readJson(await fetchImpl(url, init)));
}

export async function testConnection(profile, fetchImpl = globalThis.fetch) {
  const t0 = Date.now();
  const r = await chat(profile, [{ role: 'user', content: 'Reply with the single word: ok' }], { maxTokens: 8, temperature: 0 }, fetchImpl);
  return { ok: true, ms: Date.now() - t0, reply: r.text.trim().slice(0, 40), usage: r.usage };
}
