import { useState, useRef, useEffect } from "react";

export default function InputBar({ onSend, disabled }) {
  const [value, setValue] = useState("");
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [value]);

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    const text = value.trim();
    if (!text || disabled) return;
    setValue("");
    onSend(text);
  }

  return (
    <div className="input-area">
      <div className="input-wrap">
        <textarea
          ref={textareaRef}
          className="input-field"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about cybersecurity… (Enter to send, Shift+Enter for new line)"
          rows={1}
          disabled={disabled}
        />
        <button className="btn-send" onClick={submit} disabled={disabled || !value.trim()}>
          ➤
        </button>
      </div>
      <div className="input-hint">CJ-AI · Specialized in cybersecurity &amp; information security</div>
    </div>
  );
}
