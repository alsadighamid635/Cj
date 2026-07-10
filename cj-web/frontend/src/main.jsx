import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css";

// ── Keyboard-safe height for Android ──────────────────────────────
// visualViewport.height is the ONLY reliable way to get the height
// of the visible area above the keyboard on all Android browsers.
// We write it as a CSS variable that the layout reads.
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
    <App />
  </React.StrictMode>
);
