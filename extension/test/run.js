// node test/run.js  - free unit tests with a mock fetch (no network, no keys).
import assert from 'node:assert/strict';
import * as P from '../lib/providers.js';
import { encryptJson, decryptJson, redact, looksSecret } from '../lib/store.js';
import { extractAction, checkWritePath, checkReadPath, runLoop } from '../lib/agent.js';
import { GitHub } from '../lib/github.js';

let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('ok', name); };
const msgs = [{ role: 'system', content: 'SYS' }, { role: 'user', content: 'hi' }, { role: 'assistant', content: 'a' }, { role: 'user', content: 'b' }];

await t('detect', () => {
  assert.equal(P.detectProvider('sk-ant-api03-x'), 'anthropic'); assert.equal(P.detectProvider('AIzaSyX'), 'gemini');
  assert.equal(P.detectProvider('sk-or-v1-x'), 'openrouter'); assert.equal(P.detectProvider('gsk_abc'), 'groq');
  assert.equal(P.detectProvider('sk-proj-abc'), 'openai'); assert.equal(P.detectProvider('xyz'), null);
});
await t('openai-compatible request', () => {
  for (const id of ['openai', 'groq', 'deepseek', 'mistral', 'together', 'openrouter']) {
    const { url, init } = P.buildChatRequest({ provider: id, key: 'K', model: 'm' }, msgs);
    assert.equal(url, P.PROVIDERS[id].base + '/chat/completions'); assert.equal(init.headers.Authorization, 'Bearer K');
    const b = JSON.parse(init.body); assert.equal(b.model, 'm'); assert.equal(b.messages.length, 4);
  }
  const o = P.buildChatRequest({ provider: 'ollama', model: 'llama3.1' }, msgs); assert.equal(o.url, 'http://localhost:11434/v1/chat/completions'); assert.ok(!o.init.headers.Authorization);
  const c = P.buildChatRequest({ provider: 'custom', base: 'http://127.0.0.1:1234/v1/', model: 'x', key: '' }, msgs); assert.equal(c.url, 'http://127.0.0.1:1234/v1/chat/completions');
  assert.throws(() => P.buildChatRequest({ provider: 'custom', model: 'x' }, msgs));
  assert.equal(P.buildChatRequest({ provider: 'openrouter', key: 'K' }, msgs).init.headers['X-Title'], 'Wisdrop Studio');
});
await t('anthropic request', () => {
  const { url, init } = P.buildChatRequest({ provider: 'anthropic', key: 'sk-ant-K', model: 'claude-x' }, msgs);
  assert.equal(url, 'https://api.anthropic.com/v1/messages'); assert.equal(init.headers['x-api-key'], 'sk-ant-K');
  assert.equal(init.headers['anthropic-dangerous-direct-browser-access'], 'true');
  const b = JSON.parse(init.body); assert.equal(b.system, 'SYS'); assert.deepEqual(b.messages.map(m => m.role), ['user', 'assistant', 'user']);
  const m2 = JSON.parse(P.buildChatRequest({ provider: 'anthropic', key: 'k' }, [{ role: 'user', content: 'a' }, { role: 'user', content: 'b' }]).init.body).messages;
  assert.equal(m2.length, 1); assert.equal(m2[0].content, 'a\n\nb');
});
await t('gemini request', () => {
  const { url, init } = P.buildChatRequest({ provider: 'gemini', key: 'AIzaK', model: 'models/gemini-2.5-flash' }, msgs);
  assert.equal(url, 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent');
  assert.equal(init.headers['x-goog-api-key'], 'AIzaK'); assert.ok(!url.includes('AIzaK'));
  const b = JSON.parse(init.body); assert.equal(b.systemInstruction.parts[0].text, 'SYS'); assert.deepEqual(b.contents.map(c => c.role), ['user', 'model', 'user']);
});
await t('parse responses', () => {
  assert.equal(P.parseChatResponse('openai', { choices: [{ message: { content: 'x' } }], usage: { prompt_tokens: 3, completion_tokens: 1 } }).usage.in, 3);
  assert.equal(P.parseChatResponse('anthropic', { content: [{ type: 'text', text: 'y' }], usage: { input_tokens: 2, output_tokens: 1 } }).text, 'y');
  assert.equal(P.parseChatResponse('gemini', { candidates: [{ content: { parts: [{ text: 'z' }] } }], usageMetadata: { promptTokenCount: 5 } }).usage.in, 5);
  assert.throws(() => P.parseChatResponse('openai', { error: { message: 'bad key' } }), /bad key/);
});
await t('models + mock fetch chat', async () => {
  assert.deepEqual(P.parseModels('gemini', { models: [{ name: 'models/a', supportedGenerationMethods: ['generateContent'] }, { name: 'models/e', supportedGenerationMethods: ['embedContent'] }] }), ['a']);
  assert.deepEqual(P.parseModels('openai', { data: [{ id: 'b' }, { id: 'a' }] }), ['a', 'b']);
  const seen = []; const f = async (url, init) => { seen.push(url); return new Response(JSON.stringify(url.endsWith('/models') ? { data: [{ id: 'm1' }] } : { choices: [{ message: { content: 'ok' } }], usage: {} }), { status: 200 }); };
  assert.equal((await P.testConnection({ provider: 'groq', key: 'gsk_x' }, f)).reply, 'ok');
  assert.deepEqual(await P.listModels({ provider: 'groq', key: 'gsk_x' }, f), ['m1']);
  const bad = async () => new Response('{"error":{"message":"invalid key"}}', { status: 401 });
  await assert.rejects(P.chat({ provider: 'openai', key: 'k' }, msgs, {}, bad), /401: invalid key/);
  assert.equal(P.originPattern('http://localhost:11434/v1'), 'http://localhost/*');
});
await t('vault crypto + redaction', async () => {
  const box = await encryptJson({ github: 'github_pat_abcdefghijklmnopqrstuvwxyz' }, 'pass');
  assert.ok(!JSON.stringify(box).includes('github_pat')); assert.equal((await decryptJson(box, 'pass')).github.length, 37);
  await assert.rejects(decryptJson(box, 'nope'), /Wrong passphrase/);
  assert.ok(!redact('key sk-ant-api03-abcdefghijk end').includes('abcdefghijk')); assert.ok(looksSecret('AIzaSyA1234567890123456789012')); assert.ok(!looksSecret('hello'));
});
await t('agent guards + parse', () => {
  assert.equal(extractAction('blah ```json\n{"say":"x","tool":"read_file","args":{"path":"a{b}"}}\n``` tail').args.path, 'a{b}');
  assert.throws(() => extractAction('no json'));
  assert.equal(checkWritePath('episodes/ep01-onecoin', 'episodes/ep01-onecoin/chapters.json'), 'episodes/ep01-onecoin/chapters.json');
  assert.throws(() => checkWritePath('episodes/ep01-onecoin', 'machine/wis.py'));
  assert.throws(() => checkWritePath('episodes/ep01-onecoin', 'episodes/ep01-onecoin/state.json'));
  assert.throws(() => checkWritePath('episodes/ep01-onecoin', 'episodes/ep01-onecoin/../../AGENTS.md'));
  assert.throws(() => checkReadPath('.github/workflows/episode.yml')); assert.ok(checkReadPath('docs/FAILURE_MODES.md'));
});
await t('agent loop: tool -> gate stop', async () => {
  const replies = ['```json\n{"say":"reading","tool":"read_file","args":{"path":"episodes/ep01-onecoin/lines.json"}}\n```',
    '```json\n{"say":"write","tool":"write_file","args":{"path":"episodes/ep01-onecoin/chapters.md","content":"c01","message":"chapters"}}\n```',
    '```json\n{"say":"bad","tool":"write_file","args":{"path":"machine/x.py","content":"x"}}\n```',
    '```json\n{"say":"ready","tool":"gate","args":{"stage":"chapters","summary":"5 chapters"}}\n```'];
  let i = 0; const llm = async () => ({ text: replies[i++], usage: { in: 10, out: 5 } });
  const writes = []; const gh = { getFile: async p => ({ text: `[file ${p}]` }), putFile: async (p, c) => { writes.push(p); return { path: p, commit: 'abc1234' }; } };
  const steps = []; const s = { messages: [{ role: 'system', content: 's' }, { role: 'user', content: 'go' }], tokens: { in: 0, out: 0 } };
  const r = await runLoop(s, llm, { gh, ep: 'episodes/ep01-onecoin', looksSecret }, { maxSteps: 10, tokenBudget: 1000 }, { onStep: x => steps.push(x) });
  assert.equal(r.status, 'gate'); assert.equal(r.stage, 'chapters'); assert.deepEqual(writes, ['episodes/ep01-onecoin/chapters.md']);
  assert.ok(steps.some(x => x.kind === 'error' && /write refused/.test(x.text))); assert.equal(s.tokens.in, 40);
  i = 0; const r2 = await runLoop({ messages: [], tokens: { in: 0, out: 0 } }, llm, { gh, ep: 'episodes/ep01-onecoin' }, { maxSteps: 1, tokenBudget: 1000 }, { onStep: () => {} });
  assert.equal(r2.status, 'limit');
  const r3 = await runLoop({ messages: [], tokens: { in: 999, out: 1 } }, llm, { gh, ep: 'x' }, { maxSteps: 5, tokenBudget: 1000 }, { onStep: () => {} });
  assert.equal(r3.status, 'limit');
});
await t('github client request building', async () => {
  const calls = []; const f = async (url, init) => { calls.push({ url, init }); return new Response(url.includes('/contents/') && init.method !== 'PUT' ? JSON.stringify({ content: Buffer.from('héllo').toString('base64'), encoding: 'base64', sha: 's1' }) : init.method === 'POST' ? null : '{"commit":{"sha":"c"}}', { status: init.method === 'POST' ? 204 : 200 }); };
  const g = new GitHub('TOKEN', 'o/r', f);
  assert.equal((await g.getFile('episodes/ep 1/a.md')).text, 'héllo'); assert.ok(calls[0].url.includes('/repos/o/r/contents/episodes/ep%201/a.md?ref=main'));
  assert.equal(calls[0].init.headers.Authorization, 'Bearer TOKEN');
  await g.putFile('episodes/x/a.md', 'é', 'm'); const put = calls.find(c => c.init.method === 'PUT'); assert.equal(JSON.parse(put.init.body).sha, 's1');
  await g.dispatch('episode.yml', { ep: 'episodes/x' }); const d = calls.find(c => c.init.method === 'POST'); assert.ok(d.url.endsWith('/actions/workflows/episode.yml/dispatches')); assert.equal(JSON.parse(d.init.body).ref, 'main');
});
console.log(`\n${n} test groups passed`);
