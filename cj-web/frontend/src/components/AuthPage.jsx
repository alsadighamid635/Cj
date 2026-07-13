import { useState } from "react";
import { signup, login, setToken } from "../api.js";

const FEATURES = [
  { icon: "🧠", label: "ذكاء اصطناعي" },
  { icon: "📊", label: "تحليل متقدم" },
  { icon: "🛡️", label: "حماية ذكية" },
  { icon: "⚡", label: "استجابة فورية" },
];

export default function AuthPage({ onAuthenticated }) {
  const [mode, setMode]           = useState("login"); // "login" | "signup"
  const [identifier, setIdentifier] = useState("");
  const [username, setUsername]   = useState("");
  const [email, setEmail]         = useState("");
  const [password, setPassword]   = useState("");
  const [confirm, setConfirm]     = useState("");
  const [remember, setRemember]   = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError]         = useState(null);
  const [busy, setBusy]           = useState(false);

  function resetFields() {
    setError(null);
    setPassword("");
    setConfirm("");
  }

  function switchMode(next) {
    setMode(next);
    resetFields();
  }

  async function handleLogin(e) {
    e.preventDefault();
    setError(null);
    if (!identifier.trim() || !password) {
      setError("الرجاء إدخال اسم المستخدم وكلمة المرور.");
      return;
    }
    setBusy(true);
    try {
      const data = await login(identifier.trim(), password);
      setToken(data.token);
      onAuthenticated(data);
    } catch (err) {
      setError(err.message || "تعذر تسجيل الدخول. حاول مرة أخرى.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSignup(e) {
    e.preventDefault();
    setError(null);
    if (!username.trim() || !email.trim() || !password) {
      setError("الرجاء تعبئة جميع الحقول.");
      return;
    }
    if (password.length < 8) {
      setError("يجب أن تتكون كلمة المرور من 8 أحرف على الأقل.");
      return;
    }
    if (password !== confirm) {
      setError("كلمتا المرور غير متطابقتين.");
      return;
    }
    setBusy(true);
    try {
      const data = await signup(username.trim(), email.trim(), password);
      setToken(data.token);
      onAuthenticated(data);
    } catch (err) {
      setError(err.message || "تعذر إنشاء الحساب. حاول مرة أخرى.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page" dir="rtl">
      <div className="auth-brand">
        <div className="auth-brand-glow" />
        <img src="/logo.jpg" alt="249Shadow AI" className="auth-brand-logo" />
        <h1 className="auth-brand-title">249SHADOW<span>AI</span></h1>
        <p className="auth-brand-tag">CYBERSECURITY AI ASSISTANT</p>
        <div className="auth-brand-divider" />
        <p className="auth-brand-desc">
          مساعدك الذكي في عالم الأمن السيبراني
          <br />
          تحليل · حماية · استجابة · تعلم
        </p>
        <div className="auth-brand-shield">🛡️</div>
      </div>

      <div className="auth-panel">
        <div className="auth-panel-inner">
          <div className="auth-header">
            <h2>مرحبًا بك في</h2>
            <h1>249SHADOW AI</h1>
            <p>{mode === "login" ? "سجل الدخول للوصول إلى حسابك" : "أنشئ حسابك الخاص للبدء"}</p>
          </div>

          {error && <div className="auth-error">{error}</div>}

          {mode === "login" ? (
            <form className="auth-form" onSubmit={handleLogin}>
              <label className="auth-field">
                <span className="auth-field-icon">👤</span>
                <input
                  type="text"
                  placeholder="اسم المستخدم أو البريد الإلكتروني"
                  value={identifier}
                  onChange={e => setIdentifier(e.target.value)}
                  autoComplete="username"
                />
              </label>

              <label className="auth-field">
                <span className="auth-field-icon">🔒</span>
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="كلمة المرور"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="auth-field-toggle"
                  onClick={() => setShowPassword(s => !s)}
                  tabIndex={-1}
                >
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </label>

              <div className="auth-row">
                <label className="auth-remember">
                  <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)} />
                  تذكرني
                </label>
                <button type="button" className="auth-link" onClick={() => setError("تواصل مع الدعم لاستعادة كلمة المرور.")}>
                  نسيت كلمة المرور؟
                </button>
              </div>

              <button type="submit" className="auth-submit" disabled={busy}>
                {busy ? "جارٍ الدخول..." : <>تسجيل الدخول <span>→</span></>}
              </button>

              <div className="auth-divider"><span>أو</span></div>

              <button type="button" className="auth-secondary" onClick={() => switchMode("signup")}>
                إنشاء حساب جديد <span>➕</span>
              </button>
            </form>
          ) : (
            <form className="auth-form" onSubmit={handleSignup}>
              <label className="auth-field">
                <span className="auth-field-icon">👤</span>
                <input
                  type="text"
                  placeholder="اسم المستخدم"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  autoComplete="username"
                />
              </label>

              <label className="auth-field">
                <span className="auth-field-icon">✉️</span>
                <input
                  type="email"
                  placeholder="البريد الإلكتروني"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  autoComplete="email"
                />
              </label>

              <label className="auth-field">
                <span className="auth-field-icon">🔒</span>
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="كلمة المرور (٨ أحرف على الأقل)"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="auth-field-toggle"
                  onClick={() => setShowPassword(s => !s)}
                  tabIndex={-1}
                >
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </label>

              <label className="auth-field">
                <span className="auth-field-icon">🔒</span>
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="تأكيد كلمة المرور"
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
                  autoComplete="new-password"
                />
              </label>

              <button type="submit" className="auth-submit" disabled={busy}>
                {busy ? "جارٍ إنشاء الحساب..." : <>إنشاء حساب <span>➕</span></>}
              </button>

              <div className="auth-divider"><span>أو</span></div>

              <button type="button" className="auth-secondary" onClick={() => switchMode("login")}>
                لدي حساب بالفعل — تسجيل الدخول <span>→</span>
              </button>
            </form>
          )}

          <div className="auth-features">
            {FEATURES.map(f => (
              <div key={f.label} className="auth-feature">
                <span className="auth-feature-icon">{f.icon}</span>
                <span>{f.label}</span>
              </div>
            ))}
          </div>

          <p className="auth-footer">© 2026 249Shadow AI. جميع الحقوق محفوظة.</p>
        </div>
      </div>
    </div>
  );
}
