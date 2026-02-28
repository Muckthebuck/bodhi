import type { EmotionState } from "../types";

interface Props {
  emotion: EmotionState;
  status: string;
  onSettingsClick?: () => void;
}

const EMOTION_EMOJI: Record<string, string> = {
  happy: "😊",
  sad: "😢",
  angry: "😠",
  surprised: "😲",
  fearful: "😨",
  disgusted: "🤢",
  neutral: "😐",
  calm: "😌",
  excited: "🤩",
  confused: "😕",
};

export function StatusBar({ emotion, status, onSettingsClick }: Props) {
  const emoji = EMOTION_EMOJI[emotion.label] || "😐";
  const statusColor =
    status === "connected"
      ? "#4ade80"
      : status === "reconnecting"
        ? "#facc15"
        : "#ef4444";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "8px 16px",
        borderBottom: "1px solid var(--border)",
        background: "var(--bg-secondary)",
        fontSize: 13,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: statusColor,
            display: "inline-block",
          }}
        />
        <span style={{ color: "var(--text-muted)" }}>{status}</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span>{emoji}</span>
        <span style={{ color: "var(--text-muted)" }}>{emotion.label}</span>
        {onSettingsClick && (
          <button
            onClick={onSettingsClick}
            style={{
              marginLeft: 8,
              background: "transparent",
              border: "none",
              color: "var(--text-muted)",
              cursor: "pointer",
              fontSize: 16,
            }}
            title="Settings"
          >
            ⚙
          </button>
        )}
      </div>
    </div>
  );
}
