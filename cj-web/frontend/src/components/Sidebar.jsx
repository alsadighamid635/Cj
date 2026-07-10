export default function Sidebar({
  open, sessions, activeId, onNew, onSwitch, onDelete, onSourcesClick, showSourcesActive,
}) {
  return (
    <aside className={`sidebar ${open ? "" : "closed"}`}>
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <span className="sidebar-logo-icon">⚡</span>
          <span className="sidebar-logo-text">CJ-AI</span>
        </div>
      </div>

      <button className="btn-new-chat" onClick={onNew}>
        ✏️ New Chat
      </button>

      <div className="sidebar-section-title">Conversations</div>

      <div className="session-list">
        {sessions.length === 0 && (
          <div style={{ padding: "8px", fontSize: "12px", color: "var(--text-dim)" }}>
            No conversations yet
          </div>
        )}
        {sessions.map(s => (
          <div
            key={s.id}
            className={`session-item ${s.id === activeId ? "active" : ""}`}
            onClick={() => onSwitch(s.id)}
          >
            <span className="session-title">💬 {s.title || "Chat"}</span>
            <button
              className="session-del"
              onClick={e => { e.stopPropagation(); onDelete(s.id); }}
              title="Delete"
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
          🌐 Learning Sources
        </button>
      </div>
    </aside>
  );
}
