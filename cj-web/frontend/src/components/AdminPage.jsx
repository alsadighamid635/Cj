import { useState, useEffect } from "react";
import { loadAdminUsers } from "../api.js";
import { useLang } from "../context/LangContext.jsx";

export default function AdminPage({ onClose }) {
  const { t } = useLang();
  const [users, setUsers]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    loadAdminUsers()
      .then(data => setUsers(data.users || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  function formatDate(iso) {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleDateString(t.lang === "ar" ? "ar-SA" : "en-GB", {
        year: "numeric", month: "short", day: "numeric",
      });
    } catch { return iso; }
  }

  return (
    <div className="admin-overlay" onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="admin-panel" dir={t.dir}>
        <div className="admin-header">
          <div className="admin-header-left">
            <span className="admin-icon">🛡️</span>
            <div>
              <h2 className="admin-title">{t.adminTitle}</h2>
              <p className="admin-subtitle">{t.adminSubtitle}</p>
            </div>
          </div>
          <button className="admin-close" onClick={onClose} title={t.closeBtn}>✕</button>
        </div>

        {!loading && !error && (
          <div className="admin-stat-bar">
            <span className="admin-stat-label">{t.totalUsers}</span>
            <span className="admin-stat-value">{users.length}</span>
          </div>
        )}

        <div className="admin-body">
          {loading && (
            <div className="admin-loading">
              <div className="typing-indicator" style={{ justifyContent: "center" }}>
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
              <span>{t.loadingUsers}</span>
            </div>
          )}

          {error && (
            <div className="auth-error" style={{ margin: "16px" }}>{error}</div>
          )}

          {!loading && !error && users.length === 0 && (
            <div className="admin-empty">{t.noUsers}</div>
          )}

          {!loading && !error && users.length > 0 && (
            <table className="admin-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>{t.usernameCol}</th>
                  <th>{t.emailCol}</th>
                  <th>{t.createdCol}</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u, i) => (
                  <tr key={u.id}>
                    <td className="admin-td-num">{i + 1}</td>
                    <td>
                      <span className="admin-username">👤 {u.username}</span>
                    </td>
                    <td className="admin-td-email">{u.email}</td>
                    <td className="admin-td-date">{formatDate(u.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="admin-footer">
          <button className="auth-secondary" onClick={onClose}
            style={{ maxWidth: "160px", padding: "10px 20px", fontSize: "13px" }}>
            {t.closeBtn}
          </button>
        </div>
      </div>
    </div>
  );
}
