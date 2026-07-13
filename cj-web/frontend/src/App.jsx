import { useState, useEffect, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import ChatWindow from "./components/ChatWindow.jsx";
import InputBar from "./components/InputBar.jsx";
import Sidebar from "./components/Sidebar.jsx";
import SourcePanel from "./components/SourcePanel.jsx";
import AuthPage from "./components/AuthPage.jsx";
import {
  sendMessage, loadHistory, loadSessions, deleteSession, loadStats,
  fetchMe, getToken, clearToken, AuthError,
} from "./api.js";

const SUGGESTIONS = [
  "What is SQL injection?",
  "How does nmap work?",
  "Explain the CIA Triad",
  "What is a buffer overflow?",
  "How to detect malware?",
  "What is Kerberoasting?",
];

/**
 * Current chat session — resets when the tab is closed.
 * A fresh session ID is generated when the user clicks "New Chat".
 */
function getOrCreateSessionId() {
  const KEY = "cj_session_id";
  let id = sessionStorage.getItem(KEY);
  if (!id) {
    id = uuidv4();
    sessionStorage.setItem(KEY, id);
  }
  return id;
}

export default function App() {
  // ── Auth state ────────────────────────────────────────────────────────────
  const [user, setUser]           = useState(null);
  const [authChecked, setAuthChecked] = useState(false);

  const [sessionId, setSessionId]     = useState(getOrCreateSessionId);
  const [messages, setMessages]       = useState([]);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);
  const [sessions, setSessions]       = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 640);
  const [showSources, setShowSources] = useState(false);
  const [stats, setStats]             = useState({});

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    setMessages([]);
    setSessions([]);
  }, []);

  // Validate any stored token on first load
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setAuthChecked(true);
      return;
    }
    fetchMe()
      .then(me => setUser(me))
      .catch(() => clearToken())
      .finally(() => setAuthChecked(true));
  }, []);

  // Load message history whenever the active session changes
  useEffect(() => {
    if (!user) return;
    loadHistory(sessionId).then(d => setMessages(d.messages || []));
  }, [sessionId, user]);

  // Load this user's session list and global stats once authenticated
  useEffect(() => {
    if (!user) return;
    loadSessions().then(d => setSessions(d.sessions || []));
    loadStats().then(setStats);
  }, [user]);

  async function handleSend(text, attachment = null) {
    setError(null);

    // attachment is { raw: File, name, type, size, preview } | null
    const rawFile = attachment?.raw ?? null;

    const userMsg = {
      role:      "user",
      content:   text,
      timestamp: new Date().toISOString(),
      attachment: attachment
        ? { name: attachment.name, type: attachment.type, preview: attachment.preview }
        : null,
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await sendMessage(text, sessionId, rawFile);
      const botMsg = {
        role:       "assistant",
        content:    data.reply,
        confidence: data.confidence,
        sources:    data.sources,
        timestamp:  new Date().toISOString(),
      };
      setMessages(prev => [...prev, botMsg]);
      loadSessions().then(d => setSessions(d.sessions || []));
    } catch (err) {
      if (err instanceof AuthError) {
        logout();
        return;
      }
      const msg = err?.message && typeof err.message === "string"
        ? err.message
        : "An unexpected error occurred. Please try again.";
      setError(msg);
      setMessages(prev => [...prev, {
        role:       "assistant",
        content:    `⚠️ ${msg}`,
        confidence: "low",
        timestamp:  new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
    }
  }

  function switchSession(id) {
    setSessionId(id);
    sessionStorage.setItem("cj_session_id", id);
    setError(null);
    if (window.innerWidth <= 640) setSidebarOpen(false);
  }

  function newChat() {
    const id = uuidv4();
    sessionStorage.setItem("cj_session_id", id);
    setSessionId(id);
    setMessages([]);
    setError(null);
    if (window.innerWidth <= 640) setSidebarOpen(false);
  }

  async function removeSession(id) {
    await deleteSession(id);
    if (id === sessionId) newChat();
    setSessions(prev => prev.filter(s => s.id !== id));
  }

  if (!authChecked) {
    return <div className="app-layout" />;
  }

  if (!user) {
    return <AuthPage onAuthenticated={(data) => setUser(data)} />;
  }

  return (
    <div className="app-layout">
      <Sidebar
        open={sidebarOpen}
        sessions={sessions}
        activeId={sessionId}
        onNew={newChat}
        onSwitch={switchSession}
        onDelete={removeSession}
        onSourcesClick={() => setShowSources(true)}
        showSourcesActive={showSources}
      />

      <div className="main-area">
        <div className="topbar">
          <button className="btn-menu" onClick={() => setSidebarOpen(o => !o)}>☰</button>
          <span className="topbar-title">CJ-AI</span>
          <span className="topbar-badge">Cybersecurity</span>
          <div className="topbar-right">
            <div className="status-dot" title="Online" />
            {stats.total_vectors != null && (
              <span className="topbar-stats">{stats.total_vectors} vectors</span>
            )}
            <span className="topbar-user" title={user.email}>👤 {user.username}</span>
            <button className="btn-logout" onClick={logout} title="Log out">⏻</button>
          </div>
        </div>

        <ChatWindow
          messages={messages}
          loading={loading}
          suggestions={SUGGESTIONS}
          onSuggestion={handleSend}
        />

        <InputBar onSend={handleSend} disabled={loading} />
      </div>

      {showSources && (
        <SourcePanel
          onClose={() => {
            setShowSources(false);
            loadStats().then(setStats);
          }}
        />
      )}
    </div>
  );
}
