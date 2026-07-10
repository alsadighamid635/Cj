import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

function formatTime(ts) {
  if (!ts) return "";
  try {
    return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

const CODE_RENDERER = {
  code({ node, inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || "");
    if (!inline && match) {
      return (
        <SyntaxHighlighter
          style={oneDark}
          language={match[1]}
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

export default function MessageBubble({ message }) {
  const { role, content, confidence, sources, timestamp } = message;
  const isUser = role === "user";

  return (
    <div className={`message-row ${role}`}>
      {!isUser && <div className="message-avatar"><img src="/logo.jpg" alt="249shadow" /></div>}

      <div className="message-body">
        <div className="message-bubble">
          {isUser ? (
            <span>{content}</span>
          ) : (
            <div className="markdown">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={CODE_RENDERER}
              >
                {content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        <div className="message-meta">
          <span className="message-time">{formatTime(timestamp)}</span>
          {!isUser && confidence && (
            <span className={`confidence-badge ${confidence}`}>
              {confidence === "high" ? "✓ confident" : confidence === "medium" ? "~ partial" : "? learning"}
            </span>
          )}
        </div>

        {sources && sources.length > 0 && (
          <div className="message-sources">
            {sources.map((src, i) => {
              const urlMatch = src.match(/\((.+)\)/);
              const labelMatch = src.match(/\[(.+)\]/);
              const url = urlMatch?.[1] || src;
              const label = labelMatch?.[1] || src;
              return (
                <a key={i} href={url} target="_blank" rel="noreferrer" className="source-link">
                  📰 {label}
                </a>
              );
            })}
          </div>
        )}
      </div>

      {isUser && <div className="message-avatar" style={{ background: "#1f3a5f", borderColor: "#1f6feb" }}>👤</div>}
    </div>
  );
}
