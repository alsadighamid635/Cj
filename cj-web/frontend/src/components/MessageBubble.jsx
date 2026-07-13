import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

/** Format a ISO timestamp to HH:MM. */
function formatTime(ts) {
  if (!ts) return "";
  try {
    return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

/**
 * Parse a markdown-style source badge "[Label](URL)" into its parts.
 * Falls back gracefully if the format is unexpected.
 */
function parseSource(src) {
  const labelMatch = src.match(/^\[(.+?)\]/);
  const urlMatch   = src.match(/\((.+?)\)$/);
  return {
    label: labelMatch?.[1] ?? src,
    url:   urlMatch?.[1]   ?? "#",
  };
}

/** Render fenced code blocks with syntax highlighting; inline code as-is. */
const CODE_RENDERER = {
  code({ node, inline, className, children, ...props }) {
    const lang = /language-(\w+)/.exec(className || "")?.[1];
    if (!inline && lang) {
      return (
        <SyntaxHighlighter
          style={oneDark}
          language={lang}
          PreTag="div"
          customStyle={{ borderRadius: "8px", fontSize: "13px" }}
          {...props}
        >
          {String(children).replace(/\n$/, "")}
        </SyntaxHighlighter>
      );
    }
    return <code className={className} {...props}>{children}</code>;
  },
};

const CONFIDENCE_LABELS = {
  high:   "✓ confident",
  medium: "~ partial",
  low:    "? learning",
};

function AttachmentPreview({ attachment }) {
  if (!attachment) return null;
  const isImage = attachment.type?.startsWith("image/");
  return (
    <div className="msg-attachment">
      {isImage && attachment.preview ? (
        <img
          src={attachment.preview}
          alt={attachment.name}
          className="msg-attachment-img"
        />
      ) : (
        <div className="msg-attachment-doc">
          <span className="msg-attachment-icon">
            {attachment.type === "application/pdf" ? "📄" :
             attachment.type === "text/plain"      ? "📝" : "📎"}
          </span>
          <span className="msg-attachment-name">{attachment.name}</span>
        </div>
      )}
    </div>
  );
}

export default function MessageBubble({ message }) {
  const { role, content, confidence, sources, timestamp, attachment } = message;
  const isUser = role === "user";

  return (
    <div className={`message-row ${role}`}>
      {!isUser && (
        <div className="message-avatar">
          <img src="/logo.jpg" alt="CJ-AI" />
        </div>
      )}

      <div className="message-body">
        <div className="message-bubble">
          {isUser ? (
            <>
              {attachment && <AttachmentPreview attachment={attachment} />}
              {content && <span>{content}</span>}
            </>
          ) : (
            <div className="markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={CODE_RENDERER}>
                {content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        <div className="message-meta">
          <span className="message-time">{formatTime(timestamp)}</span>
          {!isUser && confidence && (
            <span className={`confidence-badge ${confidence}`}>
              {CONFIDENCE_LABELS[confidence] ?? confidence}
            </span>
          )}
        </div>

        {!isUser && sources && sources.length > 0 && (
          <div className="message-sources">
            {sources.map((src, i) => {
              const { label, url } = parseSource(src);
              return (
                <a
                  key={`${i}-${url}`}
                  href={url}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="source-link"
                >
                  📰 {label}
                </a>
              );
            })}
          </div>
        )}
      </div>

      {isUser && (
        <div
          className="message-avatar"
          style={{ background: "#1f3a5f", borderColor: "#1f6feb" }}
        >
          👤
        </div>
      )}
    </div>
  );
}
