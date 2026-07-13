import { useState, useRef, useEffect } from "react";

const ALLOWED_MIME = new Set([
  "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
  "application/pdf",
  "text/plain",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]);
const MAX_IMAGE_BYTES = 3 * 1024 * 1024;
const MAX_DOC_BYTES   = 5 * 1024 * 1024;

function fileIcon(file) {
  if (!file) return "📎";
  if (file.type.startsWith("image/")) return "🖼️";
  if (file.type === "application/pdf") return "📄";
  if (file.type === "text/plain")      return "📝";
  return "📎";
}

function humanSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function InputBar({ onSend, disabled }) {
  const [value, setValue]         = useState("");
  const [file, setFile]           = useState(null);
  const [fileError, setFileError] = useState("");
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

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
    if ((!text && !file) || disabled) return;
    const msgText = text || (file ? `Analyse this file: ${file.name}` : "");
    setValue("");
    const attachedFile = file;
    setFile(null);
    setFileError("");
    onSend(msgText, attachedFile);
  }

  function handleFileChange(e) {
    const picked = e.target.files?.[0];
    e.target.value = "";
    if (!picked) return;

    if (!ALLOWED_MIME.has(picked.type)) {
      setFileError("Unsupported file type. Use: JPEG · PNG · GIF · WebP · PDF · TXT · DOCX");
      return;
    }
    const isImage = picked.type.startsWith("image/");
    const limit   = isImage ? MAX_IMAGE_BYTES : MAX_DOC_BYTES;
    if (picked.size > limit) {
      setFileError(`File too large. Max: ${isImage ? "3 MB" : "5 MB"}.`);
      return;
    }
    setFileError("");
    setFile(picked);
  }

  function removeFile() {
    setFile(null);
    setFileError("");
  }

  const canSend = !disabled && (value.trim().length > 0 || file !== null);

  return (
    <div className="input-area">
      {/* File preview pill */}
      {file && (
        <div className="attach-preview">
          <span className="attach-icon">{fileIcon(file)}</span>
          <span className="attach-name">{file.name}</span>
          <span className="attach-size">{humanSize(file.size)}</span>
          <button className="attach-remove" onClick={removeFile} title="Remove file">✕</button>
        </div>
      )}

      {/* Error message */}
      {fileError && (
        <div className="attach-error">{fileError}</div>
      )}

      <div className="input-wrap">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.txt,.docx"
          style={{ display: "none" }}
          onChange={handleFileChange}
        />

        {/* Attachment button */}
        <button
          className="btn-attach"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          title="Attach image or document"
          type="button"
        >
          📎
        </button>

        <textarea
          ref={textareaRef}
          className="input-field"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            file
              ? "Ask about this file… (Enter to send)"
              : "Ask about cybersecurity… (Enter to send, Shift+Enter for new line)"
          }
          rows={1}
          disabled={disabled}
        />
        <button className="btn-send" onClick={submit} disabled={!canSend}>
          ➤
        </button>
      </div>
      <div className="input-hint">CJ-AI · Specialized in cybersecurity &amp; information security</div>
    </div>
  );
}
