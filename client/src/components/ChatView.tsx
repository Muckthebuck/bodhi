import { useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import type { ChatMessage, WsOutgoing } from "../types";
import { IconSend } from "./Icons";

interface Props {
  messages: ChatMessage[];
  onSend: (msg: WsOutgoing) => void;
  isConnected: boolean;
  isThinking: boolean;
}

export function ChatView({
  messages, onSend, isConnected, isThinking,
}: Props) {
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

  const isEmpty = messages.length === 0 && !isThinking;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Message list */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
        {isEmpty && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              color: "var(--text-muted)",
              gap: 8,
              userSelect: "none",
            }}
          >
            <span style={{ fontSize: 14 }}>No messages yet</span>
            <span style={{ fontSize: 12 }}>
              {isConnected ? "Say something to get started" : "Connect to start chatting"}
            </span>
          </div>
        )}
        {messages.map((m) => {
          const isUser = m.role === "user";
          return (
            <div
              key={m.id}
              style={{
                display: "flex",
                justifyContent: isUser ? "flex-end" : "flex-start",
                marginBottom: 10,
              }}
            >
              <div
                style={{
                  maxWidth: "75%",
                  padding: "10px 14px",
                  borderRadius: "var(--radius)",
                  background: isUser ? "var(--user-bubble)" : "var(--companion-bubble)",
                  color: isUser ? "var(--user-bubble-text)" : "var(--companion-text)",
                  boxShadow: "var(--shadow-sm)",
                  fontSize: 14,
                  lineHeight: 1.5,
                  wordBreak: "break-word",
                }}
              >
                {isUser ? (
                  m.text
                ) : (
                  <Markdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code({ className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || "");
                        const code = String(children).replace(/\n$/, "");
                        return match ? (
                          <SyntaxHighlighter
                            language={match[1]}
                            PreTag="div"
                            customStyle={{
                              margin: "8px 0",
                              borderRadius: 6,
                              fontSize: 13,
                            }}
                          >
                            {code}
                          </SyntaxHighlighter>
                        ) : (
                          <code
                            className={className}
                            style={{
                              background: "var(--bg-secondary)",
                              padding: "2px 5px",
                              borderRadius: 4,
                              fontSize: 13,
                            }}
                            {...props}
                          >
                            {children}
                          </code>
                        );
                      },
                      p({ children }) {
                        return <p style={{ margin: "4px 0" }}>{children}</p>;
                      },
                      a({ href, children }) {
                        return (
                          <a
                            href={href}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: "var(--accent-bright)" }}
                          >
                            {children}
                          </a>
                        );
                      },
                    }}
                  >
                    {m.text}
                  </Markdown>
                )}
              </div>
            </div>
          );
        })}
        {isThinking && (
          <div style={{ display: "flex", marginBottom: 10 }}>
            <div
              style={{
                padding: "10px 14px",
                borderRadius: "var(--radius)",
                background: "var(--companion-bubble)",
                color: "var(--text-muted)",
                boxShadow: "var(--shadow-sm)",
                fontSize: 14,
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
          alignItems: "center",
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
            background: "var(--input-bg)",
            color: "var(--text)",
            outline: "none",
            fontSize: 14,
          }}
        />
        <button
          onClick={handleSend}
          disabled={!isConnected || !input.trim()}
          aria-label="Send message"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: 40,
            height: 40,
            borderRadius: "var(--radius)",
            border: "none",
            background: "var(--accent-bright)",
            color: "var(--bg)",
            cursor: isConnected && input.trim() ? "pointer" : "not-allowed",
            opacity: isConnected && input.trim() ? 1 : 0.4,
            flexShrink: 0,
          }}
        >
          <IconSend size={18} />
        </button>
      </div>
    </div>
  );
}
