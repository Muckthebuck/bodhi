import { useState } from "react";

interface Props {
  initial: { hostUrl: string; sessionId: string };
  onSave: (hostUrl: string, sessionId: string) => void;
}

export function ConnectionSetup({ initial, onSave }: Props) {
  const [hostUrl, setHostUrl] = useState(initial.hostUrl);
  const [sessionId, setSessionId] = useState(initial.sessionId);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const resp = await fetch(`${hostUrl}/health`, { signal: AbortSignal.timeout(3000) });
      if (resp.ok) {
        setTestResult("✅ Connected");
      } else {
        setTestResult(`❌ HTTP ${resp.status}`);
      }
    } catch {
      setTestResult("❌ Connection failed");
    } finally {
      setTesting(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 16,
        padding: 32,
        maxWidth: 400,
        margin: "auto",
        marginTop: "15vh",
      }}
    >
      <h2 style={{ textAlign: "center" }}>Bodhi Companion</h2>
      <p style={{ color: "var(--text-muted)", textAlign: "center" }}>
        Connect to your Bodhi host
      </p>

      <label>
        <span style={{ color: "var(--text-muted)", fontSize: 12 }}>Host URL</span>
        <input
          value={hostUrl}
          onChange={(e) => setHostUrl(e.target.value)}
          placeholder="http://192.168.1.100:8000"
          style={{
            width: "100%",
            padding: "10px 14px",
            borderRadius: "var(--radius)",
            border: "1px solid var(--border)",
            background: "var(--bg)",
            color: "var(--text)",
            outline: "none",
            fontSize: 14,
            marginTop: 4,
          }}
        />
      </label>

      <label>
        <span style={{ color: "var(--text-muted)", fontSize: 12 }}>Session ID</span>
        <input
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value.replace(/[^a-zA-Z0-9_-]/g, ""))}
          placeholder="my-session"
          style={{
            width: "100%",
            padding: "10px 14px",
            borderRadius: "var(--radius)",
            border: "1px solid var(--border)",
            background: "var(--bg)",
            color: "var(--text)",
            outline: "none",
            fontSize: 14,
            marginTop: 4,
          }}
        />
      </label>

      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={testConnection}
          disabled={testing || !hostUrl}
          style={{
            flex: 1,
            padding: "10px",
            borderRadius: "var(--radius)",
            border: "1px solid var(--border)",
            background: "var(--bg-secondary)",
            color: "var(--text)",
            cursor: "pointer",
            fontSize: 14,
          }}
        >
          {testing ? "Testing…" : "Test Connection"}
        </button>
        <button
          onClick={() => onSave(hostUrl, sessionId)}
          disabled={!hostUrl || !sessionId}
          style={{
            flex: 1,
            padding: "10px",
            borderRadius: "var(--radius)",
            border: "none",
            background: "var(--accent-bright)",
            color: "#fff",
            cursor: hostUrl && sessionId ? "pointer" : "not-allowed",
            opacity: hostUrl && sessionId ? 1 : 0.5,
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          Connect
        </button>
      </div>

      {testResult && (
        <p style={{ textAlign: "center", fontSize: 13 }}>{testResult}</p>
      )}
    </div>
  );
}
