import { useLang } from "../context/LangContext.jsx";

export default function Sidebar({
  open, sessions, activeId, onNew, onSwitch, onDelete,
  user, isAdmin, onLogout, onAdminClick, stats,
}) {
  const { t, lang, setLang } = useLang();

  return (
    <aside className={`sidebar ${open ? "" : "closed"}`} dir={t.dir}>

      {/* ── Header ── */}
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <img src="/logo.jpg" alt="249shadow" className="sidebar-logo-icon" />
          <span className="sidebar-logo-text">CJ-AI</span>
        </div>
        {stats?.total_vectors != null && (
          <span className="sidebar-stat-pill">{stats.total_vectors} {t.vectors}</span>
        )}
      </div>

      {/* ── New chat ── */}
      <button className="btn-new-chat" onClick={onNew}>
        ✏️ {t.newChat}
      </button>

      <div className="sidebar-section-title">{t.conversations}</div>

      {/* ── Session list ── */}
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

      {/* ── Footer ── */}
      <div className="sidebar-footer">
        {/* Admin panel — only for system owner */}
        {isAdmin && (
          <button className="sidebar-btn-admin" onClick={onAdminClick}>
            <span className="sidebar-btn-icon">⚙️</span>
            <span>{t.adminPanel}</span>
          </button>
        )}

        {/* Divider */}
        <div className="sidebar-footer-divider" />

        {/* User info + logout */}
        <div className="sidebar-user-row">
          <div className="sidebar-user-info">
            <span className="sidebar-user-avatar">👤</span>
            <div className="sidebar-user-details">
              <span className="sidebar-username">{user?.username}</span>
              <span className="sidebar-user-email">{user?.email}</span>
            </div>
          </div>

          <div className="sidebar-user-actions">
            {/* Language toggle */}
            <button
              className="sidebar-btn-icon-only"
              onClick={() => setLang(lang === "ar" ? "en" : "ar")}
              title={lang === "ar" ? "Switch to English" : "التبديل إلى العربية"}
            >
              {lang === "ar" ? "EN" : "ع"}
            </button>
            {/* Logout */}
            <button
              className="sidebar-btn-logout"
              onClick={onLogout}
              title={t.logoutTooltip}
            >
              ⏻
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
