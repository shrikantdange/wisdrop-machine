// Key vault. Secrets live only in chrome.storage.local (never sync), optionally AES-GCM encrypted
// with a passphrase (PBKDF2-SHA256, 250k rounds). Unlocked secrets stay in memory of this panel only.

const enc = new TextEncoder(), dec = new TextDecoder();
const b64 = u8 => btoa(String.fromCharCode(...u8));
const unb64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));

async function deriveKey(pass, salt, cr = globalThis.crypto) {
  const base = await cr.subtle.importKey('raw', enc.encode(pass), 'PBKDF2', false, ['deriveKey']);
  return cr.subtle.deriveKey({ name: 'PBKDF2', salt, iterations: 250000, hash: 'SHA-256' }, base, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
}

export async function encryptJson(obj, pass, cr = globalThis.crypto) {
  const salt = cr.getRandomValues(new Uint8Array(16)), iv = cr.getRandomValues(new Uint8Array(12));
  const key = await deriveKey(pass, salt, cr);
  const ct = new Uint8Array(await cr.subtle.encrypt({ name: 'AES-GCM', iv }, key, enc.encode(JSON.stringify(obj))));
  return { v: 1, salt: b64(salt), iv: b64(iv), ct: b64(ct) };
}

export async function decryptJson(box, pass, cr = globalThis.crypto) {
  const key = await deriveKey(pass, unb64(box.salt), cr);
  try {
    const pt = await cr.subtle.decrypt({ name: 'AES-GCM', iv: unb64(box.iv) }, key, unb64(box.ct));
    return JSON.parse(dec.decode(pt));
  } catch { throw new Error('Wrong passphrase'); }
}

// ---- chrome.storage wrapper (local only) ----
const local = () => globalThis.chrome?.storage?.local;
export async function getLocal(k) { const r = await local().get(k); return r[k]; }
export async function setLocal(k, v) { await local().set({ [k]: v }); }

let secrets = null;     // {github: 'ghp..', profiles: {id: key}}
let passphrase = null;  // in memory only

export async function vaultState() {
  const box = await getLocal('vault_enc'), plain = await getLocal('vault_plain');
  return { encrypted: !!box, unlocked: secrets !== null, empty: !box && !plain };
}

export async function unlock(pass) {
  const box = await getLocal('vault_enc');
  if (box) { secrets = await decryptJson(box, pass); passphrase = pass; }
  else secrets = (await getLocal('vault_plain')) || { profiles: {} };
  return secrets;
}

export async function openPlain() {
  if (await getLocal('vault_enc')) throw new Error('Vault is encrypted: unlock with the passphrase');
  secrets = (await getLocal('vault_plain')) || { profiles: {} };
  return secrets;
}

async function persist() {
  if (passphrase) { await setLocal('vault_enc', await encryptJson(secrets, passphrase)); await local().remove('vault_plain'); }
  else { await setLocal('vault_plain', secrets); await local().remove('vault_enc'); }
}

export function getSecret(path) {
  if (!secrets) return null;
  return path.startsWith('profile:') ? secrets.profiles?.[path.slice(8)] || '' : secrets[path] || '';
}

export async function setSecret(path, value) {
  if (!secrets) throw new Error('Vault locked');
  if (path.startsWith('profile:')) { secrets.profiles = secrets.profiles || {}; secrets.profiles[path.slice(8)] = value; }
  else secrets[path] = value;
  await persist();
}

export async function setPassphrase(pass) { // '' removes encryption
  if (!secrets) throw new Error('Vault locked');
  if (pass && pass.length < 10) throw new Error('Passphrase: use at least 10 characters');
  passphrase = pass || null; await persist();
}

export async function forgetAll() {
  secrets = { profiles: {} }; passphrase = null;
  await local().remove(['vault_enc', 'vault_plain']);
}

// Redact anything that looks like a key before it reaches the step log or the UI.
const KEY_RX = /(sk-ant-[\w-]{8,}|sk-or-[\w-]{8,}|sk-[\w-]{16,}|gsk_[\w]{16,}|AIza[\w-]{20,}|ghp_[\w]{20,}|github_pat_[\w]{20,}|gho_[\w]{20,}|ak-[\w]{16,}|as-[\w]{16,})/g;
export function redact(s) {
  let out = String(s ?? '').replace(KEY_RX, m => m.slice(0, 6) + '…[redacted]');
  if (secrets) for (const v of [secrets.github, ...Object.values(secrets.profiles || {})]) if (v && v.length > 8) out = out.split(v).join('[redacted]');
  return out;
}
export function looksSecret(s) { KEY_RX.lastIndex = 0; return KEY_RX.test(String(s)); }
