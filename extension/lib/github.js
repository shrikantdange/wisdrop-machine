// Minimal GitHub REST client for the Wisdrop repo (fine-grained PAT, repo-scoped).
// Modal keys stay as GitHub Actions secrets: the extension only dispatches workflows.

const API = 'https://api.github.com';
const utf8ToB64 = s => { const u = new TextEncoder().encode(s); let b = ''; for (let i = 0; i < u.length; i += 0x8000) b += String.fromCharCode(...u.subarray(i, i + 0x8000)); return btoa(b); };
const b64ToUtf8 = s => new TextDecoder().decode(Uint8Array.from(atob(s.replace(/\n/g, '')), c => c.charCodeAt(0)));

export class GitHub {
  constructor(token, repo = 'shrikantdange/wisdrop-machine', fetchImpl = globalThis.fetch) {
    this.token = token; this.repo = repo; this.f = fetchImpl;
  }
  headers(extra = {}) {
    const h = { Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', ...extra };
    if (this.token) h.Authorization = `Bearer ${this.token}`;
    return h;
  }
  async req(path, init = {}, raw = false) {
    const url = path.startsWith('http') ? path : `${API}${path}`, opts = { ...init, headers: this.headers(init.headers) };
    // GET only: retry 429/5xx with backoff (never retry a write or a dispatch: it could run twice).
    let res;
    for (let i = 1; ; i++) {
      res = await this.f(url, opts);
      const m = (init.method || 'GET').toUpperCase();
      if (m !== 'GET' || i >= 3 || !(res.status === 429 || res.status >= 500 || (res.status === 403 && res.headers?.get?.('x-ratelimit-remaining') === '0'))) break;
      await new Promise(r => setTimeout(r, (this.retryMs ?? 1500) * i));
    }
    if (!res.ok) { const t = await res.text(); throw new Error(`GitHub ${res.status}: ${t.slice(0, 200)}`); }
    if (raw) return res;
    return res.status === 204 ? null : res.json();
  }
  r(p) { return `/repos/${this.repo}${p}`; }
  enc(path) { return path.split('/').map(encodeURIComponent).join('/'); }

  repoInfo() { return this.req(this.r('')); }
  async getFile(path, ref = 'main') {
    const j = await this.req(this.r(`/contents/${this.enc(path)}?ref=${encodeURIComponent(ref)}`));
    if (Array.isArray(j)) throw new Error(`${path} is a folder`);
    if (j.content && j.encoding === 'base64') return { text: b64ToUtf8(j.content), sha: j.sha, size: j.size };
    const res = await this.req(this.r(`/contents/${this.enc(path)}?ref=${encodeURIComponent(ref)}`), { headers: { Accept: 'application/vnd.github.raw' } }, true);
    return { text: await res.text(), sha: j.sha, size: j.size };
  }
  async exists(path, ref = 'main') { try { await this.req(this.r(`/contents/${this.enc(path)}?ref=${ref}`)); return true; } catch { return false; } }
  async getBlobUrl(path, ref = 'main') { // for <video>/<audio> on a private repo
    const res = await this.req(this.r(`/contents/${this.enc(path)}?ref=${encodeURIComponent(ref)}`), { headers: { Accept: 'application/vnd.github.raw' } }, true);
    return URL.createObjectURL(await res.blob());
  }
  async listDir(path, ref = 'main') {
    const j = await this.req(this.r(`/contents/${this.enc(path)}?ref=${encodeURIComponent(ref)}`));
    return (Array.isArray(j) ? j : [j]).map(e => ({ name: e.name, path: e.path, type: e.type, size: e.size }));
  }
  async putFile(path, text, message, branch = 'main') {
    let sha; try { sha = (await this.getFile(path, branch)).sha; } catch { sha = undefined; }
    const body = { message, content: utf8ToB64(text), branch, ...(sha ? { sha } : {}) };
    const j = await this.req(this.r(`/contents/${this.enc(path)}`), { method: 'PUT', body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' } });
    return { commit: j.commit?.sha, path };
  }
  dispatch(workflow, inputs, ref = 'main') {
    return this.req(this.r(`/actions/workflows/${workflow}/dispatches`), { method: 'POST', body: JSON.stringify({ ref, inputs }), headers: { 'Content-Type': 'application/json' } });
  }
  async runs(workflow = 'episode.yml', n = 5) {
    const j = await this.req(this.r(`/actions/workflows/${workflow}/runs?per_page=${n}`));
    return (j.workflow_runs || []).map(r => ({ id: r.id, status: r.status, conclusion: r.conclusion, created: r.created_at, url: r.html_url, title: r.display_title }));
  }
  async run(id) { const r = await this.req(this.r(`/actions/runs/${id}`)); return { id: r.id, status: r.status, conclusion: r.conclusion, url: r.html_url, created: r.created_at, updated: r.updated_at }; }
  async artifacts(id) { const j = await this.req(this.r(`/actions/runs/${id}/artifacts`)); return (j.artifacts || []).map(a => ({ name: a.name, size: a.size_in_bytes, url: `https://github.com/${this.repo}/actions/runs/${id}/artifacts/${a.id}` })); }
  async gatePRs() {
    const j = await this.req(this.r('/pulls?state=open&per_page=30'));
    return j.filter(p => /^gate\/|final|review/i.test(p.head.ref + ' ' + p.title)).map(p => ({ number: p.number, title: p.title, branch: p.head.ref, url: p.html_url }));
  }
  merge(number, title) { return this.req(this.r(`/pulls/${number}/merge`), { method: 'PUT', body: JSON.stringify({ commit_title: title, merge_method: 'merge' }), headers: { 'Content-Type': 'application/json' } }); }
  comment(number, body) { return this.req(this.r(`/issues/${number}/comments`), { method: 'POST', body: JSON.stringify({ body }), headers: { 'Content-Type': 'application/json' } }); }
}
