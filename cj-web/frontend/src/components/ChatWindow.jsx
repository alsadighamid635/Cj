import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble.jsx";

export default function ChatWindow({ messages, loading, suggestions, onSuggestion }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  if (messages.length === 0 && !loading) {
    return (
      <div className="chat-window">
        <div className="chat-empty">
          <div className="chat-empty-icon">⚡</div>
          <h2>CJ-AI</h2>
          <p>Your cybersecurity AI assistant. Ask anything about network security, malware, CTF, Linux, cryptography, and more.</p>
          <div className="chat-suggestions">
            {suggestions.map(s => (
              <button key={s} className="chat-suggestion" onClick={() => onSuggestion(s)}>
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-window">
      {messages.map((msg, i) => (
        <MessageBubble key={i} message={msg} />
      ))}

      {loading && (
        <div className="message-row assistant">
          <div className="message-avatar">⚡</div>
          <div className="message-body">
            <div className="message-bubble">
              <div className="typing-indicator">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
