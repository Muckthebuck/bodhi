import { useState } from "react";

interface Props {
  currentSession: string;
  onSwitch: (sessionId: string) => void;
  onDelete?: (sessionId: string) => void;
}

const SESSION_STORAGE_KEY = "bodhi-sessions";

function loadSessions(): string[] {
  try {
    const raw = localStorage.getItem(SESSION_STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  return ["default"];
}

function saveSessions(sessions: string[]) {
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessions));
}

export function SessionPanel({ currentSession, onSwitch, onDelete }: Props) {
  const [sessions, setSessions] = useState<string[]>(loadSessions);
  const [newName, setNewName] = useState("");
  const [expanded, setExpanded] = useState(false);

  const createSession = () => {
    const name = newName.trim().replace(/[^a-zA-Z0-9_-]/g, "");
    if (!name || sessions.includes(name)) return;
    const updated = [...sessions, name];
    setSessions(updated);
    saveSessions(updated);
    setNewName("");
    onSwitch(name);
  };

  const deleteSession = (sessionId: string) => {
    if (sessions.length <= 1) return;
    if (!confirm(`Delete session "${sessionId}"?`)) return;
    const updated = sessions.filter((s) => s !== sessionId);
    setSessions(updated);
    saveSessions(updated);
    onDelete?.(sessionId);
    if (sessionId === currentSession) {
      onSwitch(updated[0]);
    }
  };

  return (
    <div
      style={{
        borderBottom: "1px solid var(--border)",
        background: "var(--bg-secondary)",
      }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: "100%",
          padding: "6px 16px",
          border: "none",
          background: "transparent",
          color: "var(--text-muted)",
          cursor: "pointer",
          textAlign: "left",
          fontSize: 12,
        }}
      >
        Session: <strong style={{ color: "var(--text)" }}>{currentSession}</strong>
        {" "}
        {expanded ? "▲" : "▼"}
      </button>

      {expanded && (
        <div style={{ padding: "4px 16px 10px" }}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 8 }}>
            {sessions.map((s) => (
              <div key={s} style={{ display: "inline-flex", alignItems: "center", gap: 2 }}>
                <button
                  onClick={() => onSwitch(s)}
                  style={{
                    padding: "4px 10px",
                    borderRadius: 6,
                    border: s === currentSession ? "1px solid var(--accent-bright)" : "1px solid var(--border)",
                    background: s === currentSession ? "var(--accent)" : "transparent",
                    color: "var(--text)",
                    cursor: "pointer",
                    fontSize: 12,
                  }}
                >
                  {s}
                </button>
                {sessions.length > 1 && (
                  <button
                    onClick={() => deleteSession(s)}
                    title={`Delete ${s}`}
                    style={{
                      padding: "2px 5px",
                      borderRadius: 4,
                      border: "none",
                      background: "transparent",
                      color: "var(--text-muted)",
                      cursor: "pointer",
                      fontSize: 11,
                      lineHeight: 1,
                    }}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
          <div style={{ display: "flex", gap: 4 }}>
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && createSession()}
              placeholder="new-session"
              style={{
                flex: 1,
                padding: "4px 8px",
                borderRadius: 6,
                border: "1px solid var(--border)",
                background: "var(--bg)",
                color: "var(--text)",
                outline: "none",
                fontSize: 12,
              }}
            />
            <button
              onClick={createSession}
              disabled={!newName.trim()}
              style={{
                padding: "4px 10px",
                borderRadius: 6,
                border: "none",
                background: "var(--accent-bright)",
                color: "#fff",
                cursor: newName.trim() ? "pointer" : "not-allowed",
                opacity: newName.trim() ? 1 : 0.5,
                fontSize: 12,
              }}
            >
              +
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
