/**
 * AdminLogin — hidden modal that appears after 7 secret clicks on the logo.
 * Authenticates using the normal login endpoint; the backend enforces admin-only
 * access on protected routes so no extra logic is needed here.
 */
import { useState } from "react";
import { login, setToken } from "../api.js";

export default function AdminLogin({ onClose, onAuthenticated }) {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword]     = useState("");
  const [showPw, setShowPw]         = useState(false);
  const [error, setError]           = useState(null);
  const [busy, setBusy]             = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    if (!identifier.trim() || !password) {
      setError("الرجاء إدخال اسم المستخدم وكلمة المرور.");
      return;
    }
    setBusy(true);
    try {
      const data = await login(identifier.trim(), password);
      setToken(data.token, true);
      onAuthenticated(data);
      onClose();
    } catch (err) {
      setError(err.message || "بيانات الدخول غير صحيحة.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="admin-overlay" onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="admin-login-card" dir="rtl">

        {/* Shield icon + title */}
        <div className="admin-login-header">
          <div className="admin-login-shield">🛡️</div>
          <h2 className="admin-login-title">لوحة تحكم النظام</h2>
          <p className="admin-login-sub">هذه المنطقة مقيدة بمسؤول النظام فقط</p>
        </div>

        {error && (
          <div className="auth-error" style={{ margin: "0 0 14px 0" }}>{error}</div>
        )}

        <form onSubmit={handleSubmit} autoComplete="off">
          <div className="form-group">
            <label className="form-label">اسم المستخدم</label>
            <input
              className="form-input"
              placeholder="اسم المستخدم الخاص بالمدير"
              value={identifier}
              onChange={e => setIdentifier(e.target.value)}
              autoComplete="username"
              disabled={busy}
            />
          </div>

          <div className="form-group" style={{ position: "relative" }}>
            <label className="form-label">كلمة المرور</label>
            <input
              className="form-input"
              type={showPw ? "text" : "password"}
              placeholder="••••••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
              disabled={busy}
              style={{ paddingLeft: "42px" }}
            />
            <button
              type="button"
              className="pw-toggle"
              onClick={() => setShowPw(v => !v)}
              tabIndex={-1}
              style={{ left: "12px", right: "auto" }}
            >
              {showPw ? "🙈" : "👁"}
            </button>
          </div>

          <button className="auth-primary" type="submit" disabled={busy} style={{ marginTop: "8px" }}>
            {busy ? "جارٍ التحقق..." : "دخول لوحة التحكم"}
          </button>
        </form>

        <button
          className="admin-login-cancel"
          onClick={onClose}
          style={{ marginTop: "16px", width: "100%", background: "none", border: "none",
                   color: "var(--text-dim)", cursor: "pointer", fontSize: "13px" }}
        >
          إلغاء
        </button>
      </div>
    </div>
  );
}
