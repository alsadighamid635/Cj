import { useState, useEffect, useRef } from "react";
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

function getOrCreateSessionId() {
  let id = sessionStorage.getItem("cj_session_id");
  if (!id) {
    id = uuidv4();
    sessionStorage.setItem("cj_session_id", id);
  }
  return id;
}

export default function App() {
  const [sessionId, setSessionId] = useState(getOrCreateSessionId);
  const [messages, setMessages]   = useState([]);
  const [loading, setLoading]     = useState(false);
  const [sessions, setSessions]   = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 640);
  const [showSources, setShowSources] = useState(false);
  const [stats, setStats]         = useState({});

  // Load history for current session
  useEffect(() => {
    loadHistory(sessionId).then(d => setMessages(d.messages || []));
  }, [sessionId]);

  // Load sessions list
  useEffect(() => {
    loadSessions().then(d => setSessions(d.sessions || []));
    loadStats().then(setStats);
  }, []);

  async function handleSend(text) {
    const userMsg = { role: "user", content: text, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    try {
      const data = await sendMessage(text, sessionId);
      const botMsg = {
        role: "assistant",
        content: data.reply,
        confidence: data.confidence,
        sources: data.sources,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, botMsg]);
      // Refresh sessions so the new session appears in sidebar
      loadSessions().then(d => setSessions(d.sessions || []));
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "⚠️ Connection error. Please check the server.",
        confidence: "low",
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
    }
  }

  function switchSession(id) {
    setSessionId(id);
    sessionStorage.setItem("cj_session_id", id);
    if (window.innerWidth <= 640) setSidebarOpen(false);
  }

  function newChat() {
    const id = uuidv4();
    sessionStorage.setItem("cj_session_id", id);
    setSessionId(id);
    setMessages([]);
    if (window.innerWidth <= 640) setSidebarOpen(false);
  }

  async function removeSession(id) {
    await deleteSession(id);
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
        <SourcePanel onClose={() => { setShowSources(false); loadStats().then(setStats); }} />
      )}
    </div>
  );
}
