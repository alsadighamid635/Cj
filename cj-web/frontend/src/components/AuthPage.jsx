import { useState } from "react";
import { signup, login, setToken } from "../api.js";
import { useLang } from "../context/LangContext.jsx";

export default function AuthPage({ onAuthenticated }) {
  const { t, lang, setLang } = useLang();

  const [mode, setMode]             = useState("login"); // "login" | "signup"
  const [identifier, setIdentifier] = useState("");
  const [username, setUsername]     = useState("");
  const [email, setEmail]           = useState("");
  const [password, setPassword]     = useState("");
  const [confirm, setConfirm]       = useState("");
  const [remember, setRemember]     = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError]           = useState(null);
  const [busy, setBusy]             = useState(false);

  function resetFields() { setError(null); setPassword(""); setConfirm(""); }
  function switchMode(next) { setMode(next); resetFields(); }

  async function handleLogin(e) {
    e.preventDefault();
    setError(null);
    if (!identifier.trim() || !password) {
      setError(t.fillLoginFields);
      return;
    }
    setBusy(true);
    try {
      const data = await login(identifier.trim(), password);
      setToken(data.token, remember);
      onAuthenticated(data);
    } catch (err) {
      setError(err.message || t.loginError);
    } finally {
      setBusy(false);
    }
  }

  async function handleSignup(e) {
    e.preventDefault();
    setError(null);
    if (!username.trim() || !email.trim() || !password) {
      setError(t.fillAll);
      return;
    }
    if (password.length < 8) { setError(t.passwordMin8); return; }
    if (password !== confirm) { setError(t.passwordsNoMatch); return; }
    setBusy(true);
    try {
      const data = await signup(username.trim(), email.trim(), password);
      setToken(data.token, remember);
      onAuthenticated(data);
    } catch (err) {
      setError(err.message || t.signupError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page" dir={t.dir}>
      {/* Language toggle on auth page */}
      <button
        className="auth-lang-toggle"
        onClick={() => setLang(lang === "ar" ? "en" : "ar")}
      >
        {lang === "ar" ? "EN" : "ع"}
      </button>

      {/* Brand panel */}
      <div className="auth-brand">
        <div className="auth-brand-glow" />
        <img src="/logo.jpg" alt="249Shadow AI" className="auth-brand-logo" />
        <h1 className="auth-brand-title">249SHADOW<span>AI</span></h1>
        <p className="auth-brand-tag">CYBERSECURITY AI ASSISTANT</p>
        <div className="auth-brand-divider" />
        <p className="auth-brand-desc">
          {t.brandDesc}
          <br />
          {t.brandSub}
        </p>
        <div className="auth-brand-shield">🛡️</div>
      </div>

      {/* Form panel */}
      <div className="auth-panel">
        <div className="auth-panel-inner">
          <div className="auth-header">
            <h2>{t.welcomeTo}</h2>
            <h1>249SHADOW AI</h1>
            <p>{mode === "login" ? t.loginTitle : t.signupTitle}</p>
          </div>

          {error && <div className="auth-error">{error}</div>}

          {mode === "login" ? (
            <form className="auth-form" onSubmit={handleLogin}>
              <label className="auth-field">
                <span className="auth-field-icon">👤</span>
                <input
                  type="text"
                  placeholder={t.usernameOrEmail}
                  value={identifier}
                  onChange={e => setIdentifier(e.target.value)}
                  autoComplete="username"
                />
              </label>

              <label className="auth-field">
                <span className="auth-field-icon">🔒</span>
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder={t.passwordLabel}
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
                  <input
                    type="checkbox"
                    checked={remember}
                    onChange={e => setRemember(e.target.checked)}
                  />
                  {t.rememberMe}
                </label>
                <button
                  type="button"
                  className="auth-link"
                  onClick={() => setError(t.forgotContact)}
                >
                  {t.forgotPassword}
                </button>
              </div>

              <button type="submit" className="auth-submit" disabled={busy}>
                {busy ? t.loggingIn : <>{t.loginBtn} <span>→</span></>}
              </button>

              <div className="auth-divider"><span>{t.orDivider}</span></div>

              <button type="button" className="auth-secondary" onClick={() => switchMode("signup")}>
                {t.createAccount} <span>➕</span>
              </button>
            </form>
          ) : (
            <form className="auth-form" onSubmit={handleSignup}>
              <label className="auth-field">
                <span className="auth-field-icon">👤</span>
                <input
                  type="text"
                  placeholder={t.usernameLabel}
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  autoComplete="username"
                />
              </label>

              <label className="auth-field">
                <span className="auth-field-icon">✉️</span>
                <input
                  type="email"
                  placeholder={t.emailLabel}
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  autoComplete="email"
                />
              </label>

              <label className="auth-field">
                <span className="auth-field-icon">🔒</span>
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder={t.passwordMin}
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
                  placeholder={t.confirmPassword}
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
                  autoComplete="new-password"
                />
              </label>

              <label className="auth-remember" style={{ alignSelf: "flex-start" }}>
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={e => setRemember(e.target.checked)}
                />
                {t.rememberMe}
              </label>

              <button type="submit" className="auth-submit" disabled={busy}>
                {busy ? t.creatingAccount : <>{t.signupBtn} <span>➕</span></>}
              </button>

              <div className="auth-divider"><span>{t.orDivider}</span></div>

              <button type="button" className="auth-secondary" onClick={() => switchMode("login")}>
                {t.haveAccount} <span>→</span>
              </button>
            </form>
          )}

          <div className="auth-features">
            {t.features.map(f => (
              <div key={f.label} className="auth-feature">
                <span className="auth-feature-icon">{f.icon}</span>
                <span>{f.label}</span>
              </div>
            ))}
          </div>

          <p className="auth-footer">{t.footer}</p>
        </div>
      </div>
    </div>
  );
}
