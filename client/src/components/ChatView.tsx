import { useEffect, useRef, useState } from "react";
import type { ChatMessage, WsOutgoing } from "../types";

interface Props {
  messages: ChatMessage[];
  onSend: (msg: WsOutgoing) => void;
  isConnected: boolean;
  isThinking: boolean;
}

export function ChatView({ messages, onSend, isConnected, isThinking }: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || !isConnected) return;
    const requestId = crypto.randomUUID();
    onSend({ type: "user.message", text, request_id: requestId });
    setInput("");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Message list */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
        {messages.map((m) => (
          <div
            key={m.id}
            style={{
              display: "flex",
              justifyContent: m.role === "user" ? "flex-end" : "flex-start",
              marginBottom: 8,
            }}
          >
            <div
              style={{
                maxWidth: "70%",
                padding: "10px 14px",
                borderRadius: "var(--radius)",
                background:
                  m.role === "user"
                    ? "var(--user-bubble)"
                    : "var(--companion-bubble)",
                border: "1px solid var(--border)",
              }}
            >
              {m.text}
            </div>
          </div>
        ))}
        {isThinking && (
          <div style={{ display: "flex", marginBottom: 8 }}>
            <div
              style={{
                padding: "10px 14px",
                borderRadius: "var(--radius)",
                background: "var(--companion-bubble)",
                border: "1px solid var(--border)",
                color: "var(--text-muted)",
              }}
            >
              Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div
        style={{
          display: "flex",
          gap: 8,
          padding: "12px 16px",
          borderTop: "1px solid var(--border)",
          background: "var(--bg-secondary)",
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder={isConnected ? "Type a message…" : "Disconnected"}
          disabled={!isConnected}
          style={{
            flex: 1,
            padding: "10px 14px",
            borderRadius: "var(--radius)",
            border: "1px solid var(--border)",
            background: "var(--bg)",
            color: "var(--text)",
            outline: "none",
            fontSize: 14,
          }}
        />
        <button
          onClick={handleSend}
          disabled={!isConnected || !input.trim()}
          style={{
            padding: "10px 20px",
            borderRadius: "var(--radius)",
            border: "none",
            background: "var(--accent-bright)",
            color: "#fff",
            cursor: isConnected && input.trim() ? "pointer" : "not-allowed",
            opacity: isConnected && input.trim() ? 1 : 0.5,
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
