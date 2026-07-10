import { useState, useEffect } from "react";
import { loadSources, addSource, deleteSource, refreshSources, loadStats } from "../api.js";

export default function SourcePanel({ onClose }) {
  const [sources, setSources]       = useState([]);
  const [stats, setStats]           = useState({});
  const [name, setName]             = useState("");
  const [url, setUrl]               = useState("");
  const [type, setType]             = useState("rss");
  const [refreshing, setRefreshing] = useState(false);
  const [adding, setAdding]         = useState(false);

  useEffect(() => {
    loadSources().then(d => setSources(d.sources || []));
    loadStats().then(setStats);
  }, []);

  async function handleAdd(e) {
    e.preventDefault();
    if (!name.trim() || !url.trim()) return;
    setAdding(true);
    await addSource(name.trim(), url.trim(), type);
    const d = await loadSources();
    setSources(d.sources || []);
    setName("");
    setUrl("");
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
      const d = await loadSources();
      setSources(d.sources || []);
      loadStats().then(setStats);
      setRefreshing(false);
    }, 2000);
  }

  return (
    <div className="source-panel-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="source-panel">
        <div className="source-panel-header">
          <h2>🌐 Learning Sources</h2>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>

        <div className="source-panel-body">
          {/* Stats */}
          <div className="source-stats">
            <div className="stat-card">
              <div className="stat-value">{stats.total_vectors ?? "—"}</div>
              <div className="stat-label">Total Vectors</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.sources ?? "—"}</div>
              <div className="stat-label">Active Sources</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.messages ?? "—"}</div>
              <div className="stat-label">Messages</div>
            </div>
          </div>

          {/* Add source form */}
          <form className="source-add-form" onSubmit={handleAdd}>
            <h3>Add New Source</h3>
            <input
              className="form-input"
              placeholder="Source name (e.g. SANS Blog)"
              value={name}
              onChange={e => setName(e.target.value)}
              required
            />
            <input
              className="form-input"
              placeholder="URL (RSS feed or webpage)"
              value={url}
              onChange={e => setUrl(e.target.value)}
              type="url"
              required
            />
            <div className="form-row">
              <select
                className="form-select"
                value={type}
                onChange={e => setType(e.target.value)}
              >
                <option value="rss">RSS Feed</option>
                <option value="page">Web Page</option>
              </select>
              <button className="btn-add" type="submit" disabled={adding}>
                {adding ? "Adding…" : "Add Source"}
              </button>
            </div>
          </form>

          {/* Refresh all */}
          <button className="btn-refresh-all" onClick={handleRefresh} disabled={refreshing}>
            {refreshing ? "⏳ Learning in background…" : "🔄 Refresh All Sources Now"}
          </button>

          {/* Source list */}
          <div className="source-list-title">Configured Sources ({sources.length})</div>

          {sources.map(src => (
            <div key={src.id} className="source-item">
              <div className="source-item-info">
                <div className="source-item-name">{src.name}</div>
                <div className="source-item-meta">
                  {src.item_count ? `${src.item_count} items · ` : ""}
                  {src.last_fetched ? `Last: ${src.last_fetched.slice(0, 10)}` : "Not fetched yet"}
                </div>
              </div>
              <span className="source-item-type">{src.type}</span>
              <button className="btn-del-source" onClick={() => handleDelete(src.id)} title="Remove">
                🗑
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
