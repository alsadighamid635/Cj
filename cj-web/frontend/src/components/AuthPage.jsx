import { useState, useMemo, useRef, useCallback } from "react";
import { signup, login, setToken } from "../api.js";
import { useLang } from "../context/LangContext.jsx";
import AdminLogin from "./AdminLogin.jsx";

/* ── Password strength helper ────────────────────────────────── */
function calcStrength(pw) {
  if (!pw) return 0;
  let score = 0;
  if (pw.length >= 8)                                    score++;
  if (/[A-Z]/.test(pw))                                 score++;
  if (/[a-z]/.test(pw))                                 score++;
  if (/\d/.test(pw))                                     score++;
  if (/[!@#$%^&*()\-_=+\[\]{};:'",.<>/?\\|`~]/.test(pw)) score++;
  return score; // 0‒5
}

function isStrongPassword(pw) {
  return calcStrength(pw) === 5;
}

// ── Secret click to reveal admin login ────────────────────────────────────
const SECRET_CLICKS   = 7;   // number of clicks needed
const SECRET_WINDOW   = 8000; // ms window to complete the clicks

export default function AuthPage({ onAuthenticated }) {
  const { t, lang, setLang } = useLang();

  const [mode, setMode]             = useState("login");
  const [identifier, setIdentifier] = useState("");
  const [username, setUsername]     = useState("");
  const [email, setEmail]           = useState("");
  const [password, setPassword]     = useState("");
  const [confirm, setConfirm]       = useState("");
  const [remember, setRemember]     = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError]           = useState(null);
  const [busy, setBusy]             = useState(false);

  // Secret click state
  const [showAdminLogin, setShowAdminLogin] = useState(false);
  const [secretPulse, setSecretPulse]       = useState(false);
  const clickCountRef  = useRef(0);
  const clickTimerRef  = useRef(null);

  const handleSecretClick = useCallback(() => {
    clickCountRef.current += 1;
    setSecretPulse(true);
    setTimeout(() => setSecretPulse(false), 400);

    // Reset counter after window expires
    clearTimeout(clickTimerRef.current);
    clickTimerRef.current = setTimeout(() => {
      clickCountRef.current = 0;
    }, SECRET_WINDOW);

    if (clickCountRef.current >= SECRET_CLICKS) {
      clickCountRef.current = 0;
      clearTimeout(clickTimerRef.current);
      setShowAdminLogin(true);
    }
  }, []);

  const strength = useMemo(() => calcStrength(password), [password]);

  function resetFields() { setError(null); setPassword(""); setConfirm(""); }
  function switchMode(next) { setMode(next); resetFields(); }

  function strengthLabel(s) {
    if (s <= 1) return t.pwWeak;
    if (s <= 2) return t.pwFair;
    if (s <= 3) return t.pwGood;
    return t.pwStrong;
  }
  function strengthClass(s) {
    if (s <= 1) return "pw-weak";
    if (s <= 2) return "pw-fair";
    if (s <= 3) return "pw-good";
    return "pw-strong";
  }

  async function handleLogin(e) {
    e.preventDefault();
    setError(null);
    if (!identifier.trim() || !password) { setError(t.fillLoginFields); return; }
    setBusy(true);
    try {
      const data = await login(identifier.trim(), password);
      setToken(data.token, remember);
      onAuthenticated(data);
    } catch (err) {
      setError(err.message || t.loginError);
    } finally { setBusy(false); }
  }

  async function handleSignup(e) {
    e.preventDefault();
    setError(null);
    if (!username.trim() || !email.trim() || !password) { setError(t.fillAll); return; }
    if (!isStrongPassword(password)) { setError(t.passwordWeak); return; }
    if (password !== confirm)        { setError(t.passwordsNoMatch); return; }
    setBusy(true);
    try {
      const data = await signup(username.trim(), email.trim(), password);
      setToken(data.token, remember);
      onAuthenticated(data);
    } catch (err) {
      setError(err.message || t.signupError);
    } finally { setBusy(false); }
  }

  return (
    <div className="auth-page" dir={t.dir}>
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
          {t.brandDesc}<br />{t.brandSub}
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
                <button type="button" className="auth-field-toggle"
                  onClick={() => setShowPassword(s => !s)} tabIndex={-1}>
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </label>

              <div className="auth-row">
                <label className="auth-remember">
                  <input type="checkbox" checked={remember}
                    onChange={e => setRemember(e.target.checked)} />
                  {t.rememberMe}
                </label>
                <button type="button" className="auth-link"
                  onClick={() => setError(t.forgotContact)}>
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
              {/* Username — accepts Arabic + English */}
              <label className="auth-field">
                <span className="auth-field-icon">👤</span>
                <input
                  type="text"
                  placeholder={t.usernameLabel}
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  autoComplete="username"
                  dir="auto"
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
                <button type="button" className="auth-field-toggle"
                  onClick={() => setShowPassword(s => !s)} tabIndex={-1}>
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </label>

              {/* Password strength meter */}
              {password.length > 0 && (
                <div className="pw-strength-wrap">
                  <div className="pw-strength-bar">
                    {[1,2,3,4,5].map(i => (
                      <div
                        key={i}
                        className={`pw-strength-seg ${i <= strength ? strengthClass(strength) : ""}`}
                      />
                    ))}
                  </div>
                  <span className={`pw-strength-label ${strengthClass(strength)}`}>
                    {strengthLabel(strength)}
                  </span>
                </div>
              )}

              {/* Password requirements hint */}
              <p className="pw-hint">{t.pwHint}</p>

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
                <input type="checkbox" checked={remember}
                  onChange={e => setRemember(e.target.checked)} />
                {t.rememberMe}
              </label>

              <button type="submit" className="auth-submit" disabled={busy || !isStrongPassword(password)}>
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

          {/* Secret trigger — invisible dot at the bottom of the card.
              Click it 7 times within 8 seconds to open the admin login. */}
          <div
            className={`secret-trigger ${secretPulse ? "activated" : ""}`}
            onClick={handleSecretClick}
            aria-hidden="true"
          />

          <p className="auth-footer">{t.footer}</p>
        </div>
      </div>

      {/* Admin login modal — revealed by secret clicks */}
      {showAdminLogin && (
        <AdminLogin
          onClose={() => setShowAdminLogin(false)}
          onAuthenticated={onAuthenticated}
        />
      )}
    </div>
  );
}
