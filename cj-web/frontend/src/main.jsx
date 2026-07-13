import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import { LangProvider } from "./context/LangContext.jsx";
import "./index.css";

// ── Keyboard-safe height for Android ──────────────────────────────
function applyHeight() {
  const h = window.visualViewport
    ? `${window.visualViewport.height}px`
    : `${window.innerHeight}px`;
  document.documentElement.style.setProperty("--app-height", h);
}

applyHeight();

if (window.visualViewport) {
  window.visualViewport.addEventListener("resize", applyHeight);
  window.visualViewport.addEventListener("scroll", applyHeight);
} else {
  window.addEventListener("resize", applyHeight);
}
// ──────────────────────────────────────────────────────────────────

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <LangProvider>
      <App />
    </LangProvider>
  </React.StrictMode>
);
