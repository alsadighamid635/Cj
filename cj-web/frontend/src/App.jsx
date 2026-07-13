import { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import ChatWindow from "./components/ChatWindow.jsx";
import InputBar from "./components/InputBar.jsx";
import Sidebar from "./components/Sidebar.jsx";
import SourcePanel from "./components/SourcePanel.jsx";
import { sendMessage, loadHistory, loadSessions, deleteSession, loadStats } from "./api.js";

const SUGGESTIONS = [
  "What is SQL injection?",
  "How does nmap work?",
  "Explain the CIA Triad",
  "What is a buffer overflow?",
  "How to detect malware?",
  "What is Kerberoasting?",
];

/**
 * Persistent browser identity — survives tab closes and browser restarts.
 * Stored in localStorage so the user always sees only their own conversations.
 * This is a UX privacy feature, not an authentication mechanism.
 */
function getOrCreateUserId() {
  const KEY = "cj_user_id";
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = uuidv4();
    localStorage.setItem(KEY, id);
  }
  return id;
}

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

// Computed once per page load; stable for the lifetime of the tab.
const USER_ID = getOrCreateUserId();

export default function App() {
  const [sessionId, setSessionId]     = useState(getOrCreateSessionId);
  const [messages, setMessages]       = useState([]);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);
  const [sessions, setSessions]       = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 640);
  const [showSources, setShowSources] = useState(false);
  const [stats, setStats]             = useState({});

  // Load message history whenever the active session changes
  useEffect(() => {
    loadHistory(sessionId).then(d => setMessages(d.messages || []));
  }, [sessionId]);

  // Load this user's session list and global stats on mount
  useEffect(() => {
    loadSessions(USER_ID).then(d => setSessions(d.sessions || []));
    loadStats().then(setStats);
  }, []);

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
      const data = await sendMessage(text, sessionId, USER_ID, rawFile);
      const botMsg = {
        role:       "assistant",
        content:    data.reply,
        confidence: data.confidence,
        sources:    data.sources,
        timestamp:  new Date().toISOString(),
      };
      setMessages(prev => [...prev, botMsg]);
      loadSessions(USER_ID).then(d => setSessions(d.sessions || []));
    } catch (err) {
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
    await deleteSession(id, USER_ID);
    if (id === sessionId) newChat();
    setSessions(prev => prev.filter(s => s.id !== id));
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
