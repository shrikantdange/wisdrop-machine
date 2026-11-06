// Agent runner: plan -> one tool call -> result -> continue, until a gate, done, max steps or token budget.
// Provider-agnostic: the model answers with ONE JSON action, so any chat model works (no native tool calling needed).

export const AGENTS = {
  '01': { file: 'prompts/01_research_writer.md', name: '1 Research + Writer' },
  '02': { file: 'prompts/02_director.md', name: '2 Director' },
  '03': { file: 'prompts/03_builder.md', name: '3 Builder' },
  '04': { file: 'prompts/04_voice_finish.md', name: '4 Voice + Finisher' },
};
export const GATES = ['topic', 'script', 'scene_sheet', 'chapters', 'final'];
export const REFERENCE = ['docs/DIRECTOR_PROMPT.md', 'docs/FAILURE_MODES.md'];
const READ_ROOTS = ['episodes/', 'docs/', 'prompts/', 'schemas/', 'AGENTS.md', 'library/library.json', 'playbook/rules.yaml'];

export const TOOL_PROTOCOL = `
## Wisdrop Studio tool protocol (overrides "print commands" fallbacks in the prompt above)
You run inside Wisdrop Studio, a browser side panel with real tools. Every reply = ONE JSON object in a \`\`\`json fence, nothing else:
{"say": "<one short line for the owner>", "tool": "<name>", "args": {...}}
Tools:
- read_file {"path"}            read a repo file (episodes/, docs/, prompts/, schemas/, AGENTS.md). Big files are cut at 12k chars.
- list_dir {"path"}             list a repo folder.
- write_file {"path","content","message"}  create/replace a file. ONLY inside the current episode folder. Never state.json. Never secrets.
- dispatch_episode {"test_lines","preview_seconds","redo_images","redo_lines","max_gpu_seconds"}  run .github/workflows/episode.yml on main for this episode (the owner may be asked to confirm spend).
- poll_run {"run_id"?}          status of a workflow run (latest episode run if omitted).
- read_summary {}               summary.json of the last test run (branch preview).
- read_cost {}                  cost.json of the last test run.
- fetch_url {"url"}             GET a web page (text, cut at 12k chars).
- gate {"stage","summary","ask"}  HARD STOP for the owner. stage one of: ${GATES.join(', ')}. Use at every owner gate in your prompt.
- done {"summary"}              your work for this message is finished.
Rules: one tool per reply; read before you write; free checks before spend; test small; never pass a gate for the owner; absolute dates with zone.
When a TOOL RESULT arrives, continue. When OWNER: APPROVED or OWNER: SENT BACK arrives, act on it.`;

export function extractAction(text) {
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  const cand = fence ? fence[1] : text;
  const s = cand.indexOf('{');
  if (s < 0) throw new Error('no JSON object');
  let depth = 0, inStr = false, esc = false;
  for (let i = s; i < cand.length; i++) {
    const ch = cand[i];
    if (inStr) { if (esc) esc = false; else if (ch === '\\') esc = true; else if (ch === '"') inStr = false; continue; }
    if (ch === '"') inStr = true; else if (ch === '{') depth++; else if (ch === '}' && --depth === 0) {
      const a = JSON.parse(cand.slice(s, i + 1));
      if (!a.tool) throw new Error('missing "tool"');
      a.args = a.args || {};
      return a;
    }
  }
  throw new Error('unclosed JSON');
}

export function epName(ep) { return ep.replace(/\/+$/, '').split('/').pop(); }

export function checkWritePath(ep, path) {
  const p = String(path || '').replace(/^\/+/, '');
  const root = ep.replace(/\/+$/, '') + '/';
  if (p.includes('..') || p.includes('\\')) throw new Error('path traversal refused');
  if (!p.startsWith(root)) throw new Error(`write refused: only inside ${root}`);
  if (/(^|\/)state\.json$/.test(p)) throw new Error('write refused: state.json changes only through owner gate PRs');
  return p;
}
export function checkReadPath(path) {
  const p = String(path || '').replace(/^\/+/, '');
  if (p.includes('..')) throw new Error('path traversal refused');
  if (!READ_ROOTS.some(r => p === r || p.startsWith(r))) throw new Error(`read refused: allowed ${READ_ROOTS.join(', ')}`);
  return p;
}

const cut = (s, n = 12000) => (s.length > n ? s.slice(0, n) + `\n…[cut ${s.length - n} chars]` : s);

// ctx: {gh, ep, looksSecret(fn), confirmSpend(inputs)->bool, fetchUrl(url)->text, maxGpuCap}
export async function runTool(ctx, a) {
  const { gh, ep } = ctx, args = a.args || {};
  switch (a.tool) {
    case 'read_file': return cut((await gh.getFile(checkReadPath(args.path))).text);
    case 'list_dir': return (await gh.listDir(checkReadPath(args.path))).map(e => `${e.type === 'dir' ? 'd' : '-'} ${e.path} ${e.size || ''}`).join('\n');
    case 'write_file': {
      const p = checkWritePath(ep, args.path);
      if (ctx.looksSecret && ctx.looksSecret(args.content)) throw new Error('write refused: content looks like a secret key');
      const r = await gh.putFile(p, String(args.content ?? ''), `studio: ${args.message || 'update ' + p}`);
      return `written ${r.path} (commit ${String(r.commit).slice(0, 7)})`;
    }
    case 'dispatch_episode': {
      const cap = ctx.maxGpuCap ?? 600;
      const inputs = { ep, test_lines: String(args.test_lines || ''), preview_seconds: String(args.preview_seconds ?? '0'), redo_images: String(args.redo_images || ''), redo_lines: String(args.redo_lines || ''), max_gpu_seconds: String(Math.min(Number(args.max_gpu_seconds || cap), cap)) };
      if (ctx.confirmSpend && !(await ctx.confirmSpend(inputs))) return 'OWNER DECLINED the dispatch. Ask what to change, or continue without it.';
      await gh.dispatch('episode.yml', inputs);
      await new Promise(r => setTimeout(r, ctx.dispatchWaitMs ?? 4000));
      const last = (await gh.runs('episode.yml', 1))[0];
      return `dispatched episode.yml ${JSON.stringify(inputs)}; run ${last ? last.id + ' ' + last.status + ' ' + last.url : 'pending'}. Poll with poll_run (runs take minutes; poll sparingly).`;
    }
    case 'poll_run': {
      const r = args.run_id ? await gh.run(args.run_id) : (await gh.runs('episode.yml', 1))[0];
      if (!r) return 'no runs';
      let out = JSON.stringify(r);
      if (r.status === 'completed') { try { out += '\nartifacts: ' + JSON.stringify(await gh.artifacts(r.id)); } catch {} }
      return out;
    }
    case 'read_summary': return cut((await gh.getFile('summary.json', 'preview')).text, 4000);
    case 'read_cost': return cut((await gh.getFile('cost.json', 'preview')).text, 4000);
    case 'fetch_url': return cut(await ctx.fetchUrl(String(args.url)));
    default: throw new Error(`unknown tool ${a.tool}`);
  }
}

export async function loadSystemPrompt(gh, agentId, withReference) {
  const ag = AGENTS[agentId]; if (!ag) throw new Error('unknown agent');
  let sys = (await gh.getFile(ag.file)).text;
  if (withReference) for (const f of REFERENCE) { try { sys += `\n\n---\n# ${f}\n` + (await gh.getFile(f)).text; } catch {} }
  else sys += `\n\nReference docs (read with read_file only if needed): ${REFERENCE.join(', ')}.`;
  return sys + '\n' + TOOL_PROTOCOL;
}

// session: {messages:[], tokens:{in,out}}; llm(messages, {signal}) -> {text, usage}
// hooks: onStep({kind, text}) ; returns {status:'gate'|'done'|'limit'|'stopped'|'error', ...}
export async function runLoop(session, llm, ctx, limits, hooks, signal) {
  const maxSteps = limits.maxSteps ?? 12, budget = limits.tokenBudget ?? 60000;
  let fails = 0;
  for (let step = 1; step <= maxSteps; step++) {
    if (signal?.aborted) return { status: 'stopped' };
    const used = session.tokens.in + session.tokens.out;
    if (used >= budget) return { status: 'limit', reason: `token budget ${budget} reached (${used})` };
    let r;
    try { r = await llm(session.messages, { signal }); } catch (e) { return { status: signal?.aborted ? 'stopped' : 'error', reason: String(e.message || e) }; }
    session.tokens.in += r.usage.in || 0; session.tokens.out += r.usage.out || 0;
    session.messages.push({ role: 'assistant', content: r.text });
    let a;
    try { a = extractAction(r.text); fails = 0; }
    catch (e) {
      hooks.onStep({ kind: 'model', text: r.text.slice(0, 600) });
      if (++fails >= 2) return { status: 'error', reason: 'model did not follow the JSON protocol twice' };
      session.messages.push({ role: 'user', content: `PROTOCOL ERROR: ${e.message}. Reply with ONE JSON action in a json fence.` });
      continue;
    }
    if (a.say) hooks.onStep({ kind: 'say', text: a.say });
    if (a.tool === 'gate') {
      const stage = GATES.includes(a.args.stage) ? a.args.stage : String(a.args.stage || 'gate');
      hooks.onStep({ kind: 'gate', text: `${stage}: ${a.args.summary || ''}` });
      return { status: 'gate', stage, summary: a.args.summary || '', ask: a.args.ask || '' };
    }
    if (a.tool === 'done') { hooks.onStep({ kind: 'done', text: a.args.summary || 'done' }); return { status: 'done', summary: a.args.summary || '' }; }
    hooks.onStep({ kind: 'tool', text: `${a.tool} ${JSON.stringify(a.args).slice(0, 300)}` });
    let result;
    try { result = await runTool(ctx, a); hooks.onStep({ kind: 'result', text: result.slice(0, 400) }); }
    catch (e) { result = `ERROR: ${e.message || e}`; hooks.onStep({ kind: 'error', text: result }); }
    session.messages.push({ role: 'user', content: `TOOL RESULT ${a.tool}:\n${result}` });
  }
  return { status: 'limit', reason: `max steps ${maxSteps} reached` };
}

export function gateReply(stage, approved, notes) {
  return approved ? `OWNER: APPROVED gate ${stage}. ${notes ? 'Notes: ' + notes : ''} Continue to the next stage.`
    : `OWNER: SENT BACK gate ${stage}. Notes: ${notes || '(none)'}. Fix exactly these, then return to the gate.`;
}
