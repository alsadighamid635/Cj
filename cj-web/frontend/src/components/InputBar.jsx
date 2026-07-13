import { useState, useRef, useEffect, useId } from "react";
import { useLang } from "../context/LangContext.jsx";

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
  if (type.startsWith("image/"))  return "🖼️";
  if (type === "application/pdf") return "📄";
  if (type === "text/plain")      return "📝";
  return "📎";
}

function humanSize(bytes) {
  if (bytes < 1024)        return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function readAsDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload  = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export default function InputBar({ onSend, disabled }) {
  const { t } = useLang();
  const [value, setValue]           = useState("");
  const [attachment, setAttachment] = useState(null);
  const [fileError, setFileError]   = useState("");

  const textareaRef = useRef(null);
  const inputId = useId();

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
    const msgText = text || `${t.analyseFile} ${attachment.name}`;
    const snap    = attachment;
    setValue("");
    setAttachment(null);
    setFileError("");
    onSend(msgText, snap);
  }

  async function handleFileChange(e) {
    const picked = e.target.files?.[0];
    e.target.value = "";
    if (!picked) return;

    const ct = picked.type || "";
    if (!ALLOWED_MIME.has(ct)) {
      setFileError(t.fileTypeError);
      return;
    }
    const isImage = ct.startsWith("image/");
    const limit   = isImage ? MAX_IMAGE_BYTES : MAX_DOC_BYTES;
    if (picked.size > limit) {
      setFileError(`${t.fileSizeError} ${isImage ? "3 MB" : "5 MB"}.`);
      return;
    }
    setFileError("");

    let preview = null;
    if (isImage) {
      try { preview = await readAsDataURL(picked); } catch (_) { /* no preview */ }
    }
    setAttachment({ raw: picked, name: picked.name, type: ct, size: picked.size, preview });
  }

  function removeAttachment() { setAttachment(null); setFileError(""); }

  const canSend = !disabled && (value.trim().length > 0 || attachment !== null);

  return (
    <div className="input-area">
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
            title={t.removeFile}
            type="button"
          >✕</button>
        </div>
      )}

      {fileError && <div className="attach-error">{fileError}</div>}

      <div className="input-wrap">
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
          title={t.attachTitle}
        >
          📎
        </label>

        <textarea
          ref={textareaRef}
          className="input-field"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={attachment ? t.inputWithFile : t.inputPlaceholder}
          rows={1}
          disabled={disabled}
          dir="auto"
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

      <div className="input-hint">{t.inputHint}</div>
    </div>
  );
}
