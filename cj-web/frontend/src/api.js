/**
 * API client for CJ-AI Web.
 *
 * All requests include the X-User-ID header so the backend can scope
 * conversations to individual browser identities without requiring auth.
 *
 * VITE_API_URL is set on Vercel (points to the Render backend).
 * In local dev, Vite proxies /api → localhost:8000 automatically.
 */

const BASE = (import.meta.env.VITE_API_URL ?? "") + "/api";

/** Default timeout for most requests. Chat gets a longer timeout (see sendMessage). */
const REQUEST_TIMEOUT_MS = 30_000;
const CHAT_TIMEOUT_MS    = 60_000;

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

/** Build headers common to every request. */
function buildHeaders(userId, extra = {}) {
  return {
    "Content-Type": "application/json",
    ...(userId ? { "X-User-ID": userId } : {}),
    ...extra,
  };
}

// ── Chat endpoints ────────────────────────────────────────────────────────────

export async function sendMessage(message, sessionId, userId) {
  const res = await fetchWithTimeout(`${BASE}/chat`, {
    method: "POST",
    headers: buildHeaders(userId),
    body: JSON.stringify({ message, session_id: sessionId }),
  }, CHAT_TIMEOUT_MS);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail?.detail ?? `Server error (${res.status})`);
  }
  return res.json();
}

export async function loadHistory(sessionId) {
  try {
    const res = await fetchWithTimeout(`${BASE}/chat/history/${sessionId}`);
    if (!res.ok) return { messages: [] };
    return res.json();
  } catch {
    return { messages: [] };
  }
}

export async function loadSessions(userId) {
  try {
    const res = await fetchWithTimeout(`${BASE}/chat/sessions`, {
      headers: buildHeaders(userId),
    });
    if (!res.ok) return { sessions: [] };
    return res.json();
  } catch {
    return { sessions: [] };
  }
}

export async function deleteSession(sessionId, userId) {
  await fetchWithTimeout(`${BASE}/chat/session/${sessionId}`, {
    method: "DELETE",
    headers: buildHeaders(userId),
  });
}

export async function renameSession(sessionId, title, userId) {
  await fetchWithTimeout(`${BASE}/chat/session/${sessionId}/title`, {
    method: "PATCH",
    headers: buildHeaders(userId),
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
