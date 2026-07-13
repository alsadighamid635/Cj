import { useState, useRef, useEffect, useId } from "react";

const ALLOWED_MIME = new Set([
  "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
  "application/pdf",
  "text/plain",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]);
const MAX_IMAGE_BYTES = 3 * 1024 * 1024;
const MAX_DOC_BYTES   = 5 * 1024 * 1024;

function fileIcon(type) {
  if (!type) return "📎";
  if (type.startsWith("image/"))          return "🖼️";
  if (type === "application/pdf")         return "📄";
  if (type === "text/plain")              return "📝";
  return "📎";
}

function humanSize(bytes) {
  if (bytes < 1024)        return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Read a File as a base64 data-URL using FileReader.
 * Returns a Promise<string> so we can await it safely on mobile
 * without relying on URL.createObjectURL (which can become invalid
 * when the browser suspends the tab during the file-picker flow).
 */
function readAsDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload  = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export default function InputBar({ onSend, disabled }) {
  const [value, setValue]         = useState("");
  // attachment: { raw: File, name, type, size, preview: string|null }
  const [attachment, setAttachment] = useState(null);
  const [fileError, setFileError]   = useState("");

  const textareaRef = useRef(null);
  // Stable ID for the label ↔ input pairing (required for mobile reliability)
  const inputId = useId();

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
    if ((!text && !attachment) || disabled) return;
    const msgText = text || `Analyse this file: ${attachment.name}`;
    const snap    = attachment;
    setValue("");
    setAttachment(null);
    setFileError("");
    onSend(msgText, snap);
  }

  async function handleFileChange(e) {
    const picked = e.target.files?.[0];
    // Reset input so the same file can be re-selected if needed
    e.target.value = "";
    if (!picked) return;

    const ct = picked.type || "";
    if (!ALLOWED_MIME.has(ct)) {
      setFileError("Unsupported type. Allowed: JPEG · PNG · GIF · WebP · PDF · TXT · DOCX");
      return;
    }
    const isImage = ct.startsWith("image/");
    const limit   = isImage ? MAX_IMAGE_BYTES : MAX_DOC_BYTES;
    if (picked.size > limit) {
      setFileError(`File too large. Max ${isImage ? "3 MB" : "5 MB"}.`);
      return;
    }
    setFileError("");

    // Read preview immediately so we don't depend on an object URL
    let preview = null;
    if (isImage) {
      try { preview = await readAsDataURL(picked); } catch (_) { /* no preview */ }
    }

    setAttachment({ raw: picked, name: picked.name, type: ct, size: picked.size, preview });
  }

  function removeAttachment() {
    setAttachment(null);
    setFileError("");
  }

  const canSend = !disabled && (value.trim().length > 0 || attachment !== null);

  return (
    <div className="input-area">
      {/* Attachment preview pill */}
      {attachment && (
        <div className="attach-preview">
          {attachment.preview && (
            <img src={attachment.preview} alt="" className="attach-thumb" />
          )}
          <span className="attach-icon">{fileIcon(attachment.type)}</span>
          <span className="attach-name">{attachment.name}</span>
          <span className="attach-size">{humanSize(attachment.size)}</span>
          <button
            className="attach-remove"
            onClick={removeAttachment}
            title="Remove file"
            type="button"
          >
            ✕
          </button>
        </div>
      )}

      {fileError && <div className="attach-error">{fileError}</div>}

      <div className="input-wrap">
        {/*
          Hidden file input + <label> pairing.
          Using a <label htmlFor> is the most reliable way to open the
          native file picker on Android Chrome — programmatic .click()
          from a button handler can cause page reloads on mobile.
        */}
        <input
          id={inputId}
          type="file"
          className="file-input-visually-hidden"
          accept="image/jpeg,image/jpg,image/png,image/gif,image/webp,application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={handleFileChange}
          disabled={disabled}
        />
        <label
          htmlFor={inputId}
          className={`btn-attach${disabled ? " btn-attach--disabled" : ""}`}
          title="Attach image or document"
        >
          📎
        </label>

        <textarea
          ref={textareaRef}
          className="input-field"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            attachment
              ? "Ask about this file… (Enter to send)"
              : "Ask about cybersecurity… (Enter to send, Shift+Enter for new line)"
          }
          rows={1}
          disabled={disabled}
        />

        <button
          className="btn-send"
          onClick={submit}
          disabled={!canSend}
          type="button"
        >
          ➤
        </button>
      </div>

      <div className="input-hint">
        CJ-AI · Specialized in cybersecurity &amp; information security
      </div>
    </div>
  );
}
