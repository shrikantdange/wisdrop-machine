import { PROVIDERS, detectProvider, resolve, originPattern, chat, listModels, testConnection } from './lib/providers.js';
import * as V from './lib/store.js';
import { GitHub } from './lib/github.js';
import { AGENTS, loadSystemPrompt, runLoop, gateReply, epName } from './lib/agent.js';

const $ = id => document.getElementById(id);
const el = (tag, attrs = {}, ...kids) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs)) { if (k === 'class') e.className = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v); } for (const c of kids) e.append(c instanceof Node ? c : document.createTextNode(String(c))); return e; };
const ep = () => $('ep').value.trim().replace(/\/+$/, '');
const say = (node, text, cls = '') => { node.textContent = V.redact(text); node.className = node.className.replace(/ ?(ok|err)\b/g, '') + (cls ? ' ' + cls : ''); };

// ---------- tabs ----------
const tabs = [...document.querySelectorAll('[role=tab]')];
function showTab(t) {
  for (const b of tabs) { const on = b === t; b.setAttribute('aria-selected', on); b.tabIndex = on ? 0 : -1; $(b.getAttribute('aria-controls')).hidden = !on; }
  t.focus();
}
tabs.forEach((b, i) => {
  b.addEventListener('click', () => showTab(b));
  b.addEventListener('keydown', e => { if (e.key === 'ArrowRight') showTab(tabs[(i + 1) % tabs.length]); if (e.key === 'ArrowLeft') showTab(tabs[(i - 1 + tabs.length) % tabs.length]); });
});

// ---------- vault ----------
async function initVault() {
  const s = await V.vaultState();
  if (s.encrypted && !s.unlocked) { $('lockbar').hidden = false; return; }
  await V.openPlain(); afterUnlock();
}
$('unlockBtn').onclick = async () => {
  try { await V.unlock($('unlockPass').value); $('unlockPass').value = ''; $('lockbar').hidden = true; afterUnlock(); }
  catch (e) { $('unlockPass').setAttribute('aria-invalid', 'true'); $('unlockPass').placeholder = e.message; $('unlockPass').value = ''; }
};
async function afterUnlock() { $('ghRepo').value = (await V.getLocal('gh_repo')) || $('ghRepo').value; await renderProfiles(); }
function gh() {
  const t = V.getSecret('github'); if (!t) throw new Error('Add a GitHub token in Keys first');
  return new GitHub(t, $('ghRepo').value.trim());
}

// ---------- permissions ----------
async function ensureOrigin(base) {
  const origins = [originPattern(base)];
  if (await chrome.permissions.contains({ origins })) return true;
  return chrome.permissions.request({ origins });
}

// inline confirm card (works in the side panel, no window.confirm)
function askConfirm(container, text, yes = 'Allow', no = 'Decline') {
  return new Promise(res => {
    const card = el('div', { class: 'gate', role: 'alertdialog' }, el('p', {}, text));
    const done = v => { card.remove(); res(v); };
    const y = el('button', { class: 'btn primary', onclick: () => done(true) }, yes);
    card.append(el('div', { class: 'row' }, y, el('button', { class: 'btn ghost', onclick: () => done(false) }, no)));
    container.append(card); y.focus(); card.scrollIntoView({ block: 'nearest' });
  });
}

// ---------- KEYS: universal AI box ----------
for (const [id, p] of Object.entries(PROVIDERS)) $('kProv').append(el('option', { value: id }, p.name));
function fillDefaults(id) { const p = PROVIDERS[id]; $('kBase').value = p.base; $('kModel').value = p.model; }
$('kKey').addEventListener('input', () => {
  const d = detectProvider($('kKey').value);
  $('kDetect').textContent = d ? `detected: ${PROVIDERS[d].name}` : ($('kKey').value ? 'unknown key: set base URL' : '');
  $('kDetect').classList.toggle('on', !!d);
  if (d && d !== $('kProv').value) { $('kProv').value = d; fillDefaults(d); }
});
$('kProv').onchange = () => fillDefaults($('kProv').value);
fillDefaults('openai');
const formProfile = () => ({ provider: $('kProv').value, base: $('kBase').value.trim(), model: $('kModel').value.trim(), key: $('kKey').value.trim() });

$('kFetch').onclick = async () => {
  try {
    const p = formProfile(); if (!(await ensureOrigin(resolve(p).base))) throw new Error('permission for this host was not granted');
    const ms = await listModels(p); $('kModels').replaceChildren(...ms.map(m => el('option', { value: m })));
    say($('kMsg'), `${ms.length} models loaded. Pick one in the Model field.`, 'ok');
  } catch (e) { say($('kMsg'), `Models: ${e.message}`, 'err'); }
};
$('kTest').onclick = async () => {
  try {
    const p = formProfile(); if (!(await ensureOrigin(resolve(p).base))) throw new Error('permission for this host was not granted');
    say($('kMsg'), 'Testing…'); const r = await testConnection(p);
    say($('kMsg'), `Connected in ${r.ms} ms. Model replied: "${r.reply}"`, 'ok');
  } catch (e) { say($('kMsg'), `Test failed: ${e.message}`, 'err'); }
};
$('kSave').onclick = async () => {
  try {
    const p = formProfile(); const c = resolve(p);
    if (!c.nokey && !p.key) throw new Error('Paste a key');
    if (!(await ensureOrigin(c.base))) throw new Error('permission for this host was not granted');
    const profiles = (await V.getLocal('profiles')) || [];
    const id = Math.random().toString(36).slice(2, 10);
    profiles.push({ id, label: $('kLabel').value.trim() || `${PROVIDERS[p.provider].name} · ${c.model}`, provider: p.provider, base: c.base, model: c.model });
    await V.setSecret('profile:' + id, p.key); await V.setLocal('profiles', profiles);
    $('kKey').value = ''; $('kLabel').value = ''; say($('kMsg'), 'Saved. Key stored only in this browser.', 'ok'); renderProfiles();
  } catch (e) { say($('kMsg'), e.message, 'err'); }
};
async function renderProfiles() {
  const profiles = (await V.getLocal('profiles')) || [];
  const active = await V.getLocal('active_profile');
  $('kList').replaceChildren(...profiles.map(p => el('li', {}, el('span', {}, `${p.label}`), el('code', {}, p.model),
    el('button', { class: 'btn ghost', 'aria-label': `Delete ${p.label}`, onclick: async () => {
      await V.setLocal('profiles', profiles.filter(x => x.id !== p.id)); await V.setSecret('profile:' + p.id, ''); renderProfiles();
    } }, 'Delete'))));
  $('modelSel').replaceChildren(...(profiles.length ? profiles.map(p => el('option', { value: p.id }, p.label)) : [el('option', { value: '' }, 'add a key in Keys')]));
  if (active) $('modelSel').value = active;
}
$('modelSel').onchange = () => V.setLocal('active_profile', $('modelSel').value);
async function activeProfile() {
  const profiles = (await V.getLocal('profiles')) || [];
  const p = profiles.find(x => x.id === $('modelSel').value); if (!p) throw new Error('Pick a model profile (Keys tab)');
  return { ...p, key: V.getSecret('profile:' + p.id) };
}

$('ghTest').onclick = async () => {
  try { const t = $('ghTok').value.trim() || V.getSecret('github'); const r = await new GitHub(t, $('ghRepo').value.trim()).repoInfo();
    say($('ghMsg'), `OK: ${r.full_name} (${r.private ? 'private' : 'public'}), push ${r.permissions?.push ? 'yes' : 'no'}`, 'ok'); }
  catch (e) { say($('ghMsg'), e.message, 'err'); }
};
$('ghSave').onclick = async () => {
  try { if ($('ghTok').value.trim()) await V.setSecret('github', $('ghTok').value.trim()); await V.setLocal('gh_repo', $('ghRepo').value.trim()); $('ghTok').value = ''; say($('ghMsg'), 'Saved.', 'ok'); }
  catch (e) { say($('ghMsg'), e.message, 'err'); }
};
$('passSave').onclick = async () => { try { const p = $('passSet').value; await V.setPassphrase(p); $('passSet').value = ''; say($('ghMsg'), p ? 'Keys encrypted with your passphrase.' : 'Encryption removed.', 'ok'); } catch (e) { say($('ghMsg'), e.message, 'err'); } };
$('forget').onclick = async () => { if (await askConfirm($('p-keys'), 'Delete every saved key and token from this browser?', 'Delete all', 'Cancel')) { await V.forgetAll(); await V.setLocal('profiles', []); renderProfiles(); } };

// ---------- AGENTS ----------
for (const [id, a] of Object.entries(AGENTS)) $('agentSel').append(el('option', { value: id }, a.name));
let session = null, sessionAgent = null, pendingGate = null, abort = null, totalTokens = 0;
const chatBox = $('chat');
function bubble(cls, text) { const m = el('div', { class: `msg ${cls}` }, V.redact(text)); chatBox.append(m); m.scrollIntoView({ block: 'end' }); }
function logStep(s) { const li = el('li', { class: s.kind }, `${new Date().toLocaleTimeString()} ${s.kind}: ${V.redact(s.text)}`); $('log').append(li); li.scrollIntoView({ block: 'nearest' }); if (s.kind === 'say') bubble('agent', s.text); }
function setBusy(b) { $('send').disabled = b; $('stop').disabled = !b; }
function showTokens() { if (session) $('tokens').textContent = `tokens in ${session.tokens.in} · out ${session.tokens.out} / ${$('tokBudget').value}`; $('costTok').textContent = totalTokens; }
$('newChat').onclick = () => { session = null; pendingGate = null; $('gateCard').hidden = true; chatBox.replaceChildren(); $('log').replaceChildren(); $('tokens').textContent = ''; };
$('agentSel').onchange = () => { if (session) bubble('sys', 'Agent changed: next message starts a new chat.'); session = null; };
$('stop').onclick = () => abort?.abort();

async function fetchUrl(url) {
  const u = new URL(url); if (!/^https?:$/.test(u.protocol)) throw new Error('only http(s)');
  const origins = [`${u.protocol}//${u.hostname}/*`];
  if (!(await chrome.permissions.contains({ origins }))) {
    const ok = await new Promise(res => {
      const card = el('div', { class: 'gate' }, el('p', {}, `The agent wants to read ${u.hostname}.`));
      card.append(el('div', { class: 'row' },
        el('button', { class: 'btn primary', onclick: async () => { const g = await chrome.permissions.request({ origins }); card.remove(); res(g); } }, 'Allow this site'),
        el('button', { class: 'btn ghost', onclick: () => { card.remove(); res(false); } }, 'Decline')));
      chatBox.append(card);
    });
    if (!ok) throw new Error(`owner did not allow ${u.hostname}`);
  }
  const r = await fetch(url); const t = await r.text();
  return (r.headers.get('content-type') || '').includes('html') ? t.replace(/<(script|style)[\s\S]*?<\/\1>/gi, '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ') : t;
}

async function drive(userText) {
  setBusy(true); abort = new AbortController();
  try {
    const prof = await activeProfile(); const g = gh();
    if (!session || sessionAgent !== $('agentSel').value) {
      bubble('sys', `Loading ${AGENTS[$('agentSel').value].name} prompt from ${$('ghRepo').value}…`);
      const sys = await loadSystemPrompt(g, $('agentSel').value, $('withRef').checked);
      session = { messages: [{ role: 'system', content: sys }], tokens: { in: 0, out: 0 } }; sessionAgent = $('agentSel').value;
      userText = `Episode folder: ${ep()}. Today: ${new Date().toString()}.\n${userText}`;
    }
    session.messages.push({ role: 'user', content: userText });
    const before = session.tokens.in + session.tokens.out;
    const ctx = { gh: g, ep: ep(), looksSecret: V.looksSecret, fetchUrl, maxGpuCap: Number($('runGpu').value) || 120,
      confirmSpend: inputs => askConfirm(chatBox, `Agent wants to run episode.yml: ${JSON.stringify(inputs)}. This can spend GPU (cap ${inputs.max_gpu_seconds} s).`, 'Run it', 'Decline') };
    const llm = (msgs, o) => chat(prof, msgs, { ...o, maxTokens: 4096 });
    const r = await runLoop(session, llm, ctx, { maxSteps: +$('maxSteps').value, tokenBudget: +$('tokBudget').value }, { onStep: s => { logStep(s); showTokens(); } }, abort.signal);
    totalTokens += session.tokens.in + session.tokens.out - before; showTokens();
    if (r.status === 'gate') { pendingGate = r; $('gateText').textContent = V.redact(`${r.stage.toUpperCase()}: ${r.summary}${r.ask ? '\n\n' + r.ask : ''}`); $('gateCard').hidden = false; $('gateApprove').focus(); }
    else if (r.status === 'done') bubble('sys', 'Agent finished this step.');
    else bubble('sys', `Stopped: ${r.reason || r.status}. Send a message to continue.`);
  } catch (e) { bubble('sys', `Error: ${e.message}`); }
  finally { setBusy(false); abort = null; }
}
$('send').onclick = () => { const t = $('msg').value.trim(); if (!t) return; if (pendingGate) { bubble('sys', 'Answer the owner gate first.'); return; } bubble('user', t); $('msg').value = ''; drive(t); };
$('msg').addEventListener('keydown', e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) $('send').click(); });
function answerGate(ok) {
  if (!pendingGate) return; const notes = $('gateNotes').value.trim();
  if (!ok && !notes) { $('gateNotes').focus(); $('gateNotes').placeholder = 'Write what to change first'; return; }
  const txt = gateReply(pendingGate.stage, ok, notes); pendingGate = null; $('gateCard').hidden = true; $('gateNotes').value = '';
  bubble('user', txt); drive(txt);
}
$('gateApprove').onclick = () => answerGate(true);
$('gateBack').onclick = () => answerGate(false);

// insert-into-chat helper: copy, or put the prompt into the focused field of the current page. No clicking of other sites' buttons.
async function promptText() { return (await gh().getFile(AGENTS[$('agentSel').value].file)).text; }
$('copyPrompt').onclick = async () => { try { await navigator.clipboard.writeText(await promptText()); bubble('sys', 'Prompt copied.'); } catch (e) { bubble('sys', e.message); } };
$('insertPrompt').onclick = async () => {
  try {
    const text = await promptText();
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const [res] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, args: [text], func: t => {
      const e = document.activeElement; if (!e) return false;
      if (e.tagName === 'TEXTAREA' || (e.tagName === 'INPUT' && e.type === 'text')) {
        const set = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(e), 'value').set; set.call(e, (e.value ? e.value + '\n' : '') + t);
        e.dispatchEvent(new Event('input', { bubbles: true })); return true;
      }
      if (e.isContentEditable) { document.execCommand('insertText', false, t); return true; }
      return false;
    } });
    bubble('sys', res?.result ? 'Inserted into the focused box. Review it and press send on that page yourself.' : 'No focused text box on the page: click into the chat box first, then retry.');
  } catch (e) {
    try { await navigator.clipboard.writeText(await promptText()); } catch {}
    bubble('sys', 'Could not reach this page (click the Wisdrop icon while on that tab to allow it). Prompt copied instead.');
  }
};

// ---------- PIPELINE ----------
const STAGES = [['topics.md', 'Topic shortlist', 'gate 1 topic'], ['brief.md', 'Brief'], ['research.md', 'Research + sources'], ['beats.md', 'Beats'], ['bible.md', 'Bible'], ['hooks.md', 'Hooks'],
  ['script.md', 'Script'], ['lines.json', 'Lines', 'gate 2 script + cast'], ['chapters.json', 'Chapters'], ['scenes.md', 'Scene sheet'], ['shots.json', 'Shots'], ['director_check.md', 'Director check'],
  ['build_log.md', 'Build log', 'gate 3 chapter-1 look'], ['qa', 'QA checks'], ['package', 'Package', 'gate 4 final']];
$('pipeLoad').onclick = async () => {
  try {
    const g = gh(); const names = new Set((await g.listDir(ep())).map(e => e.name));
    let st = '?'; try { st = JSON.parse((await g.getFile(`${ep()}/state.json`)).text).state; } catch {}
    $('pipeState').textContent = `state: ${st}`; $('pipeState').classList.add('on');
    let firstMissing = true;
    $('pipeList').replaceChildren(...STAGES.map(([f, label, gate]) => {
      const has = names.has(f); const now = !has && firstMissing; if (now) firstMissing = false;
      return el('li', { class: now ? 'now' : '' }, el('span', {}, `${label}${gate ? '  ·  ' + gate : ''}`), el('span', { class: has ? 'yes' : 'no' }, has ? '✓ ' + f : (now ? 'next' : '—')));
    }));
  } catch (e) { $('pipeList').replaceChildren(el('li', {}, e.message)); }
};

// ---------- REVIEW ----------
function linkify(text) {
  const frag = document.createDocumentFragment(); const parts = String(text).split(/(https?:\/\/[^\s)|]+)/g);
  parts.forEach((p, i) => frag.append(i % 2 ? el('a', { href: p, target: '_blank', rel: 'noopener' }, p.replace(/^https?:\/\/(www\.)?/, '').slice(0, 40)) : p));
  return frag;
}
function mdTables(md) {
  const tables = []; let cur = null;
  for (const line of md.split('\n')) {
    if (/^\s*\|/.test(line)) { if (/^\s*\|[\s:|-]+\|\s*$/.test(line)) continue; (cur ||= []).push(line.trim().replace(/^\||\|$/g, '').split('|').map(s => s.trim())); }
    else if (cur) { tables.push(cur); cur = null; }
  }
  if (cur) tables.push(cur); return tables;
}
$('revLoad').onclick = async () => {
  const g = gh();
  try { const s = JSON.parse((await g.getFile('summary.json', 'preview')).text);
    $('revSum').textContent = `${s.ep || ''} · ${s.status} · $${s.cost_usd} · GPU ${s.gpu_secs}s${s.failed_checks?.length ? ' · failed: ' + s.failed_checks.join(', ') : ''}`;
    $('revVideo').src = await g.getBlobUrl('preview.mp4', 'preview'); $('revVideo').hidden = false;
  } catch (e) { $('revSum').textContent = `Preview: ${e.message}`; }
  try { const files = (await g.listDir(`${ep()}/vo`)).filter(f => /\.(wav|mp3|m4a|ogg)$/i.test(f.name)).slice(0, 60);
    $('revVoice').replaceChildren(...files.map(f => { const a = el('audio', { controls: '', preload: 'none', 'aria-label': f.name }); const b = el('button', { class: 'btn ghost', onclick: async () => { a.src = await g.getBlobUrl(f.path); a.play(); b.remove(); } }, 'Load');
      return el('div', { class: 'vl' }, el('code', {}, f.name), b, a); }));
    if (!files.length) $('revVoice').textContent = 'No voice files in the episode folder (they may live only in the run artifact).';
  } catch (e) { $('revVoice').textContent = `Voice: ${e.message}`; }
  try { const tabs = mdTables((await g.getFile(`${ep()}/research.md`)).text);
    $('revFacts').replaceChildren(...tabs.slice(0, 3).map(t => el('table', {}, el('tr', {}, ...t[0].map(h => el('th', {}, h))), ...t.slice(1).map(r => el('tr', {}, ...r.map(c => { const td = el('td'); td.append(linkify(c)); return td; }))))));
    if (!tabs.length) $('revFacts').textContent = 'research.md has no table.';
  } catch (e) { $('revFacts').textContent = `Facts: ${e.message}`; }
  try { const prs = await g.gatePRs();
    $('revPRs').replaceChildren(...(prs.length ? prs.map(p => el('li', {}, el('a', { href: p.url, target: '_blank', rel: 'noopener' }, `#${p.number} ${p.title}`),
      el('button', { class: 'btn primary', onclick: async () => { if (await askConfirm($('p-review'), `Approve = merge PR #${p.number} (${p.branch}). This is your owner approval.`, 'Approve', 'Cancel')) { await g.merge(p.number, `owner approved via Wisdrop Studio: ${p.title}`); $('revLoad').click(); } } }, 'Approve'),
      el('button', { class: 'btn warn', onclick: async () => { const n = $('revNotes').value.trim(); if (!n) { $('revNotes').focus(); return; } await g.comment(p.number, `SEND BACK (owner, via Wisdrop Studio):\n\n${n}`); $('revNotes').value = ''; } }, 'Send back with notes')))
      : [el('li', {}, 'No open gate PRs.')]));
  } catch (e) { $('revPRs').replaceChildren(el('li', {}, e.message)); }
};

// ---------- RUN ----------
$('runChapLoad').onclick = async () => {
  try { const c = JSON.parse((await gh().getFile(`${ep()}/chapters.json`)).text);
    $('runChap').replaceChildren(el('option', { value: '' }, '(manual lines)'), ...c.chapters.map(ch => el('option', { value: `${ch.lines[0]}-${ch.lines[1]}` }, `${ch.id} ${ch.title || ch.part} (${ch.lines[0]}-${ch.lines[1]})`)));
  } catch (e) { $('runChap').replaceChildren(el('option', { value: '' }, `no chapters.json: type lines`)); }
};
$('runChap').onchange = () => { if ($('runChap').value) $('runLines').value = $('runChap').value; };
async function dispatchRun(kind) {
  const lines = $('runLines').value.trim();
  if (kind !== 'final' && !/^\d+(-\d+)?(,\d+(-\d+)?)*$/.test(lines)) { $('runLines').focus(); return; }
  const inputs = { ep: ep(), test_lines: kind === 'final' ? '' : lines, preview_seconds: kind === 'final' ? '0' : String($('runPrev').value || 0),
    redo_images: $('runRedoI').value.trim(), redo_lines: $('runRedoL').value.trim(), max_gpu_seconds: String($('runGpu').value || 120) };
  if (!(await askConfirm($('p-run'), `${kind === 'final' ? 'BUILD FINAL (whole episode)' : kind + ' lines ' + lines}: ${JSON.stringify(inputs)}`, 'Dispatch', 'Cancel'))) return;
  try { await gh().dispatch('episode.yml', inputs); setTimeout(() => $('runRefresh').click(), 4000); } catch (e) { $('runList').prepend(el('li', {}, e.message)); }
}
$('runVoice').onclick = () => dispatchRun('voice');
$('runRender').onclick = () => dispatchRun('render');
$('runFinal').onclick = () => dispatchRun('final');
$('runRefresh').onclick = async () => {
  try { const rs = await gh().runs('episode.yml', 6);
    $('runList').replaceChildren(...rs.map(r => el('li', {}, el('span', { class: 'pill' + (r.conclusion === 'success' ? ' on' : '') }, r.conclusion || r.status), el('a', { href: r.url, target: '_blank', rel: 'noopener' }, `#${r.id}`), el('span', { class: 'muted' }, new Date(r.created).toLocaleString()))));
  } catch (e) { $('runList').replaceChildren(el('li', {}, e.message)); }
};

// ---------- COST ----------
$('costLoad').onclick = async () => {
  try { const c = JSON.parse((await gh().getFile('cost.json', 'preview')).text);
    $('costOut').replaceChildren(el('p', {}, `Total $${c.total_usd} · GPU ${c.gpu_secs} s`),
      el('table', {}, el('tr', {}, ...['step', 'secs', 'gpu', 'calls', 'usd'].map(h => el('th', {}, h))), ...(c.steps || []).map(s => el('tr', {}, ...[s.step, s.secs, s.gpu || 'CPU', s.calls, s.usd].map(v => el('td', {}, v ?? ''))))));
  } catch (e) { $('costOut').textContent = e.message; }
};

initVault();
