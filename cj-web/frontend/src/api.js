const BASE = "/api";

export async function sendMessage(message, sessionId) {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function loadHistory(sessionId) {
  const res = await fetch(`${BASE}/chat/history/${sessionId}`);
  if (!res.ok) return { messages: [] };
  return res.json();
}

export async function loadSessions() {
  const res = await fetch(`${BASE}/chat/sessions`);
  if (!res.ok) return { sessions: [] };
  return res.json();
}

export async function deleteSession(sessionId) {
  await fetch(`${BASE}/chat/session/${sessionId}`, { method: "DELETE" });
}

export async function loadSources() {
  const res = await fetch(`${BASE}/sources`);
  if (!res.ok) return { sources: [] };
  return res.json();
}

export async function addSource(name, url, type = "rss") {
  const res = await fetch(`${BASE}/sources`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, url, type }),
  });
  return res.json();
}

export async function deleteSource(id) {
  await fetch(`${BASE}/sources/${id}`, { method: "DELETE" });
}

export async function refreshSources() {
  const res = await fetch(`${BASE}/sources/refresh`, { method: "POST" });
  return res.json();
}

export async function loadStats() {
  const res = await fetch(`${BASE}/admin/stats`);
  if (!res.ok) return {};
  return res.json();
}
