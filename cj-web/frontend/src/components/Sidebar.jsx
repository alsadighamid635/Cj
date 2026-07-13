import { useLang } from "../context/LangContext.jsx";

export default function Sidebar({
  open, sessions, activeId, onNew, onSwitch, onDelete, onSourcesClick, showSourcesActive,
}) {
  const { t } = useLang();

  return (
    <aside className={`sidebar ${open ? "" : "closed"}`} dir={t.dir}>
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <img src="/logo.jpg" alt="249shadow" className="sidebar-logo-icon" />
          <span className="sidebar-logo-text">CJ-AI</span>
        </div>
      </div>

      <button className="btn-new-chat" onClick={onNew}>
        ✏️ {t.newChat}
      </button>

      <div className="sidebar-section-title">{t.conversations}</div>

      <div className="session-list">
        {sessions.length === 0 && (
          <div style={{ padding: "8px", fontSize: "12px", color: "var(--text-dim)" }}>
            {t.noConversations}
          </div>
        )}
        {sessions.map(s => (
          <div
            key={s.id}
            className={`session-item ${s.id === activeId ? "active" : ""}`}
            onClick={() => onSwitch(s.id)}
            title={s.title || t.newChat}
          >
            <span className="session-title">
              💬 {s.title && s.title !== "New Chat" ? s.title : t.newChat}
            </span>
            <button
              className="session-del"
              onClick={e => { e.stopPropagation(); onDelete(s.id); }}
              title="×"
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <button
          className={`btn-sources ${showSourcesActive ? "active" : ""}`}
          onClick={onSourcesClick}
        >
          🌐 {t.learningSources}
        </button>
      </div>
    </aside>
  );
}
