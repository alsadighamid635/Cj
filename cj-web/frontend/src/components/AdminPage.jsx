import { useState, useEffect } from "react";
import { loadAdminUsers, deleteAdminUser, loadSources, addSource, deleteSource, refreshSources, loadStats } from "../api.js";
import { useLang } from "../context/LangContext.jsx";

export default function AdminPage({ onClose, currentUser }) {
  const { t } = useLang();
  const [tab, setTab] = useState("users"); // "users" | "sources"

  return (
    <div className="admin-overlay" onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="admin-panel" dir={t.dir}>

        {/* ── Header ── */}
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

        {/* ── Tabs ── */}
        <div className="admin-tabs">
          <button
            className={`admin-tab ${tab === "users" ? "active" : ""}`}
            onClick={() => setTab("users")}
          >
            {t.tabUsers}
          </button>
          <button
            className={`admin-tab ${tab === "sources" ? "active" : ""}`}
            onClick={() => setTab("sources")}
          >
            {t.tabSources}
          </button>
        </div>

        {/* ── Tab content ── */}
        {tab === "users"   && <UsersTab t={t} currentUser={currentUser} />}
        {tab === "sources" && <SourcesTab t={t} />}

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

/* ────────────────────────────────────────────────────────────────
   Tab 1 — Users
──────────────────────────────────────────────────────────────── */
function UsersTab({ t, currentUser }) {
  const [users, setUsers]           = useState([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState(null);
  const [deleting, setDeleting]     = useState(null);   // user_id being deleted
  const [confirm, setConfirm]       = useState(null);   // user to confirm-delete
  const [search, setSearch]         = useState("");

  useEffect(() => {
    loadAdminUsers()
      .then(data => setUsers(data.users || []))
      .catch(err  => setError(err.message))
      .finally(()  => setLoading(false));
  }, []);

  function formatDate(iso) {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleDateString(t.lang === "ar" ? "ar-SA" : "en-GB", {
        year: "numeric", month: "short", day: "numeric",
      });
    } catch { return iso; }
  }

  async function handleDelete(user) {
    setDeleting(user.id);
    setConfirm(null);
    try {
      await deleteAdminUser(user.id);
      setUsers(prev => prev.filter(u => u.id !== user.id));
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(null);
    }
  }

  const filtered = users.filter(u =>
    u.username.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="admin-body">

      {/* Stats strip */}
      {!loading && !error && (
        <div className="admin-stat-bar">
          <span className="admin-stat-label">{t.totalUsers}</span>
          <span className="admin-stat-value">{users.length}</span>
          {/* Search */}
          <input
            className="form-input"
            placeholder="🔍 بحث بالاسم أو البريد..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ marginRight: "auto", maxWidth: "220px", padding: "6px 12px", fontSize: "13px" }}
          />
        </div>
      )}

      {loading && (
        <div className="admin-loading">
          <div className="typing-indicator" style={{ justifyContent: "center" }}>
            <div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" />
          </div>
          <span>{t.loadingUsers}</span>
        </div>
      )}

      {error && <div className="auth-error" style={{ margin: "16px" }}>{error}</div>}

      {!loading && !error && filtered.length === 0 && (
        <div className="admin-empty">{search ? "لا توجد نتائج مطابقة." : t.noUsers}</div>
      )}

      {/* Confirm-delete dialog */}
      {confirm && (
        <div className="admin-confirm-overlay">
          <div className="admin-confirm-box">
            <div className="admin-confirm-icon">⚠️</div>
            <p className="admin-confirm-title">تأكيد الحذف</p>
            <p className="admin-confirm-msg">
              سيتم حذف حساب <strong>{confirm.username}</strong> وجميع محادثاته نهائياً.
              لا يمكن التراجع عن هذا الإجراء.
            </p>
            <div className="admin-confirm-actions">
              <button
                className="btn-del-confirm"
                onClick={() => handleDelete(confirm)}
                disabled={!!deleting}
              >
                {deleting === confirm.id ? "جارٍ الحذف..." : "نعم، احذف الحساب"}
              </button>
              <button className="auth-secondary" onClick={() => setConfirm(null)}>
                إلغاء
              </button>
            </div>
          </div>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <table className="admin-table">
          <thead>
            <tr>
              <th>#</th>
              <th>{t.usernameCol}</th>
              <th>{t.emailCol}</th>
              <th>المحادثات</th>
              <th>الرسائل</th>
              <th>{t.createdCol}</th>
              <th>إجراء</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((u, i) => {
              const isAdmin  = u.username.toLowerCase() === "249shadow";
              const isSelf   = currentUser && u.id === currentUser.id;
              return (
                <tr key={u.id} className={isAdmin ? "admin-row-self" : ""}>
                  <td className="admin-td-num">{i + 1}</td>
                  <td>
                    <span className="admin-username">
                      {isAdmin ? "👑" : "👤"} {u.username}
                      {isAdmin && <span className="admin-badge-admin">مدير</span>}
                    </span>
                  </td>
                  <td className="admin-td-email">{u.email}</td>
                  <td className="admin-td-num">{u.session_count ?? 0}</td>
                  <td className="admin-td-num">{u.message_count ?? 0}</td>
                  <td className="admin-td-date">{formatDate(u.created_at)}</td>
                  <td>
                    {isAdmin || isSelf ? (
                      <span className="admin-td-protected" title="لا يمكن حذف حساب المدير">—</span>
                    ) : (
                      <button
                        className="btn-del-user"
                        onClick={() => setConfirm(u)}
                        disabled={!!deleting}
                        title="حذف الحساب"
                      >
                        🗑
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────
   Tab 2 — Learning Sources
──────────────────────────────────────────────────────────────── */
function SourcesTab({ t }) {
  const [sources, setSources]   = useState([]);
  const [stats, setStats]       = useState({});
  const [name, setName]         = useState("");
  const [url, setUrl]           = useState("");
  const [type, setType]         = useState("rss");
  const [refreshing, setRefreshing] = useState(false);
  const [adding, setAdding]     = useState(false);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([loadSources(), loadStats()])
      .then(([d, s]) => { setSources(d.sources || []); setStats(s); })
      .finally(() => setLoading(false));
  }, []);

  async function handleAdd(e) {
    e.preventDefault();
    if (!name.trim() || !url.trim()) return;
    setAdding(true);
    await addSource(name.trim(), url.trim(), type);
    const d = await loadSources();
    setSources(d.sources || []);
    setName(""); setUrl("");
    setAdding(false);
  }

  async function handleDelete(id) {
    await deleteSource(id);
    setSources(prev => prev.filter(s => s.id !== id));
  }

  async function handleRefresh() {
    setRefreshing(true);
    await refreshSources();
    setTimeout(async () => {
      const [d, s] = await Promise.all([loadSources(), loadStats()]);
      setSources(d.sources || []);
      setStats(s);
      setRefreshing(false);
    }, 2000);
  }

  if (loading) return (
    <div className="admin-body">
      <div className="admin-loading">
        <div className="typing-indicator" style={{ justifyContent: "center" }}>
          <div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" />
        </div>
        <span>{t.loadingUsers}</span>
      </div>
    </div>
  );

  return (
    <div className="admin-body admin-sources-body">
      {/* Stats strip */}
      <div className="admin-stat-bar" style={{ flexWrap: "wrap", gap: "16px" }}>
        <div className="admin-sources-stat">
          <span className="admin-stat-value">{stats.total_vectors ?? "—"}</span>
          <span className="admin-stat-label">{t.totalVectors}</span>
        </div>
        <div className="admin-sources-stat">
          <span className="admin-stat-value">{stats.sources ?? "—"}</span>
          <span className="admin-stat-label">{t.activeSources}</span>
        </div>
        <div className="admin-sources-stat">
          <span className="admin-stat-value">{stats.messages ?? "—"}</span>
          <span className="admin-stat-label">{t.totalMessages}</span>
        </div>
      </div>

      <div className="admin-sources-content">
        {/* Add form */}
        <form className="admin-add-form" onSubmit={handleAdd}>
          <div className="admin-add-form-title">{t.addSource}</div>
          <input
            className="form-input"
            placeholder={t.sourceName}
            value={name}
            onChange={e => setName(e.target.value)}
            required
          />
          <input
            className="form-input"
            placeholder={t.sourceUrl}
            value={url}
            onChange={e => setUrl(e.target.value)}
            type="url"
            required
          />
          <div className="form-row">
            <select className="form-select" value={type} onChange={e => setType(e.target.value)}>
              <option value="rss">{t.typeRss}</option>
              <option value="page">{t.typePage}</option>
            </select>
            <button className="btn-add" type="submit" disabled={adding}>
              {adding ? t.addingBtn : t.addBtn}
            </button>
          </div>
        </form>

        {/* Refresh */}
        <button className="btn-refresh-all" onClick={handleRefresh} disabled={refreshing}>
          {refreshing ? t.refreshing : t.refreshAll}
        </button>

        {/* Source list */}
        <div className="source-list-title">{t.configuredSources} ({sources.length})</div>

        {sources.map(src => (
          <div key={src.id} className="source-item">
            <div className="source-item-info">
              <div className="source-item-name">{src.name}</div>
              <div className="source-item-meta">
                {src.item_count ? `${src.item_count} items · ` : ""}
                {src.last_fetched
                  ? `${t.lastFetched} ${src.last_fetched.slice(0, 10)}`
                  : t.notFetchedYet}
              </div>
            </div>
            <span className="source-item-type">{src.type}</span>
            <button className="btn-del-source" onClick={() => handleDelete(src.id)} title="Remove">🗑</button>
          </div>
        ))}
      </div>
    </div>
  );
}
