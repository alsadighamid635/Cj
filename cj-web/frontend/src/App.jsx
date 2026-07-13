import { useState, useEffect, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import ChatWindow from "./components/ChatWindow.jsx";
import InputBar from "./components/InputBar.jsx";
import Sidebar from "./components/Sidebar.jsx";
import SourcePanel from "./components/SourcePanel.jsx";
import AuthPage from "./components/AuthPage.jsx";
import AdminPage from "./components/AdminPage.jsx";
import { useLang } from "./context/LangContext.jsx";
import {
  sendMessage, loadHistory, loadSessions, deleteSession, loadStats,
  fetchMe, getToken, clearToken, AuthError,
} from "./api.js";

// Admin username — must match config.ADMIN_USERNAME on the backend
const ADMIN_USERNAME = "249shadow";

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
  const { t, lang, setLang } = useLang();

  // ── Auth state ──────────────────────────────────────────────────
  const [user, setUser]               = useState(null);
  const [authChecked, setAuthChecked] = useState(false);

  const [sessionId, setSessionId]     = useState(getOrCreateSessionId);
  const [messages, setMessages]       = useState([]);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);
  const [sessions, setSessions]       = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 640);
  const [showSources, setShowSources] = useState(false);
  const [showAdmin, setShowAdmin]     = useState(false);
  const [stats, setStats]             = useState({});

  const isAdmin = user && user.username.toLowerCase() === ADMIN_USERNAME.toLowerCase();

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    setMessages([]);
    setSessions([]);
    setShowAdmin(false);
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

  // Load session list and global stats once authenticated
  useEffect(() => {
    if (!user) return;
    loadSessions().then(d => setSessions(d.sessions || []));
    loadStats().then(setStats);
  }, [user]);

  async function handleSend(text, attachment = null) {
    setError(null);
    const rawFile = attachment?.raw ?? null;

    const userMsg = {
      role:       "user",
      content:    text,
      timestamp:  new Date().toISOString(),
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
      if (err instanceof AuthError) { logout(); return; }
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

  if (!authChecked) return <div className="app-layout" />;

  if (!user) {
    return <AuthPage onAuthenticated={(data) => setUser(data)} />;
  }

  return (
    <div className="app-layout" dir={t.dir}>
      <Sidebar
        open={sidebarOpen}
        sessions={sessions}
        activeId={sessionId}
        onNew={newChat}
        onSwitch={switchSession}
        onDelete={removeSession}
        onSourcesClick={() => setShowSources(true)}
        showSourcesActive={showSources}
        user={user}
        isAdmin={isAdmin}
        onLogout={logout}
        onAdminClick={() => setShowAdmin(true)}
        stats={stats}
      />

      <div className="main-area">
        <div className="topbar">
          <button className="btn-menu" onClick={() => setSidebarOpen(o => !o)}>☰</button>
          <span className="topbar-title">CJ-AI</span>
          <span className="topbar-badge">Cybersecurity</span>

          <div className="topbar-right">
            <div className="status-dot" title="Online" />
            {stats.total_vectors != null && (
              <span className="topbar-stats">{stats.total_vectors} {t.vectors}</span>
            )}
            {/* Language toggle */}
            <button
              className="btn-lang"
              onClick={() => setLang(lang === "ar" ? "en" : "ar")}
              title={lang === "ar" ? "Switch to English" : "التبديل إلى العربية"}
            >
              {lang === "ar" ? "EN" : "ع"}
            </button>
          </div>
        </div>

        <ChatWindow
          messages={messages}
          loading={loading}
          suggestions={t.suggestions}
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

      {showAdmin && <AdminPage onClose={() => setShowAdmin(false)} />}
    </div>
  );
}
