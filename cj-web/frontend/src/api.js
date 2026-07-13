/**
 * API client for CJ-AI Web.
 *
 * Every account holder gets a private JWT (issued by /api/auth/login or
 * /api/auth/signup) which is sent as `Authorization: Bearer <token>` on
 * every request. The backend uses it to scope conversations to that
 * account only — no other user can read or modify them.
 *
 * VITE_API_URL is set on Vercel (points to the Render backend).
 * In local dev, Vite proxies /api → localhost:8000 automatically.
 */

const BASE = (import.meta.env.VITE_API_URL ?? "") + "/api";
const TOKEN_KEY = "cj_auth_token";

/** Default timeout for most requests. Chat gets a longer timeout (see sendMessage). */
const REQUEST_TIMEOUT_MS = 30_000;
const CHAT_TIMEOUT_MS    = 60_000;

// ── Token storage ────────────────────────────────────────────────────────────

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Thrown when the server rejects the current token (expired/invalid).
 * Callers can catch this specifically to force a logout.
 */
export class AuthError extends Error {}

/**
 * Fetch with a built-in timeout.
 * Throws a descriptive Error on timeout or network failure.
 */
async function fetchWithTimeout(url, options = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    return res;
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error("Request timed out. The server may be starting up — please try again.");
    }
    throw new Error("Network error. Please check your connection.");
  } finally {
    clearTimeout(timer);
  }
}

/** Build headers common to every authenticated request. */
function authHeaders(extra = {}) {
  const token = getToken();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

async function parseErrorDetail(res) {
  const payload = await res.json().catch(() => ({}));
  const raw = payload?.detail;
  return Array.isArray(raw)
    ? raw.map(e => e?.msg ?? String(e)).join("; ")
    : (typeof raw === "string" ? raw : `Server error (${res.status})`);
}

/** Authenticated GET/DELETE/PATCH helper. Throws AuthError on 401. */
async function authFetch(path, options = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
  const res = await fetchWithTimeout(
    `${BASE}${path}`,
    { ...options, headers: authHeaders(options.headers) },
    timeoutMs,
  );
  if (res.status === 401) {
    throw new AuthError(await parseErrorDetail(res));
  }
  return res;
}

// ── Auth endpoints ────────────────────────────────────────────────────────────

export async function signup(username, email, password) {
  const res = await fetchWithTimeout(`${BASE}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function login(identifier, password) {
  const res = await fetchWithTimeout(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identifier, password }),
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function fetchMe() {
  const res = await authFetch("/auth/me");
  if (!res.ok) throw new AuthError(await parseErrorDetail(res));
  return res.json();
}

// ── Chat endpoints ────────────────────────────────────────────────────────────

export async function sendMessage(message, sessionId, file = null) {
  // Always use multipart/form-data so the backend Form() fields work with or without a file.
  // Do NOT set Content-Type manually — the browser must set it with the correct boundary.
  const fd = new FormData();
  fd.append("message", message);
  if (sessionId) fd.append("session_id", sessionId);
  if (file)      fd.append("file", file, file.name);

  const res = await authFetch(
    "/chat",
    { method: "POST", body: fd },
    CHAT_TIMEOUT_MS,
  );
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function loadHistory(sessionId) {
  try {
    const res = await authFetch(`/chat/history/${sessionId}`);
    if (!res.ok) return { messages: [] };
    return res.json();
  } catch {
    return { messages: [] };
  }
}

export async function loadSessions() {
  try {
    const res = await authFetch("/chat/sessions");
    if (!res.ok) return { sessions: [] };
    return res.json();
  } catch {
    return { sessions: [] };
  }
}

export async function deleteSession(sessionId) {
  await authFetch(`/chat/session/${sessionId}`, { method: "DELETE" });
}

export async function renameSession(sessionId, title) {
  await authFetch(`/chat/session/${sessionId}/title`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
}

// ── Sources endpoints ─────────────────────────────────────────────────────────

export async function loadSources() {
  try {
    const res = await fetchWithTimeout(`${BASE}/sources`);
    if (!res.ok) return { sources: [] };
    return res.json();
  } catch {
    return { sources: [] };
  }
}

export async function addSource(name, url, type = "rss") {
  const res = await fetchWithTimeout(`${BASE}/sources`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, url, type }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail?.detail ?? `Failed to add source (${res.status})`);
  }
  return res.json();
}

export async function deleteSource(id) {
  await fetchWithTimeout(`${BASE}/sources/${id}`, { method: "DELETE" });
}

export async function refreshSources() {
  const res = await fetchWithTimeout(`${BASE}/sources/refresh`, { method: "POST" });
  return res.json();
}

// ── Admin endpoints ───────────────────────────────────────────────────────────

export async function loadStats() {
  try {
    const res = await fetchWithTimeout(`${BASE}/admin/stats`);
    if (!res.ok) return {};
    return res.json();
  } catch {
    return {};
  }
}
