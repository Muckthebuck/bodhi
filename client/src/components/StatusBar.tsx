import type { CharacterConfig } from "../character/types";
import type { EmotionState } from "../types";
import { IconSettings, IconEye, IconEyeOff, IconSwap } from "./Icons";
import { CustomSelect } from "./CustomSelect";

interface Props {
  emotion: EmotionState;
  status: string;
  onSettingsClick?: () => void;
  // Quick character controls
  characters?: CharacterConfig[];
  activeCharacterId?: string;
  showCharacter?: boolean;
  onToggleCharacter?: () => void;
  onSwitchCharacter?: (id: string) => void;
}

export function StatusBar({
  emotion, status, onSettingsClick,
  characters, activeCharacterId, showCharacter,
  onToggleCharacter, onSwitchCharacter,
}: Props) {
  const statusColor =
    status === "connected"
      ? "var(--status-ok)"
      : status === "reconnecting"
        ? "var(--status-warn)"
        : "var(--status-error)";

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
        <span style={{ color: "var(--text-muted)", textTransform: "capitalize" }}>{status}</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ color: "var(--text-muted)", fontSize: 12 }}>{emotion.label}</span>

        {/* Quick character toggles */}
        {characters && characters.length > 0 && onToggleCharacter && (
          <button
            onClick={onToggleCharacter}
            aria-label={showCharacter ? "Hide character" : "Show character"}
            title={showCharacter ? "Hide character" : "Show character"}
            style={{
              background: "transparent",
              border: "none",
              color: showCharacter ? "var(--accent-bright)" : "var(--text-muted)",
              cursor: "pointer",
              padding: 4,
              display: "flex",
              alignItems: "center",
              borderRadius: 6,
            }}
          >
            {showCharacter ? <IconEye size={16} /> : <IconEyeOff size={16} />}
          </button>
        )}

        {characters && characters.length > 1 && onSwitchCharacter && (
          <div style={{ display: "inline-flex", alignItems: "center" }}>
            <CustomSelect
              value={activeCharacterId ?? ""}
              options={characters.map((c) => ({ value: c.id, label: c.name }))}
              onChange={(v) => onSwitchCharacter(v)}
              className="statusbar-char-select"
              ariaLabel="Switch character"
            />
          </div>
        )}

        <div style={{ width: 1, height: 16, background: "var(--border-subtle)", margin: "0 2px" }} />

        {onSettingsClick && (
          <button
            onClick={onSettingsClick}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-muted)",
              cursor: "pointer",
              padding: 4,
              display: "flex",
              alignItems: "center",
              borderRadius: 6,
            }}
            title="Settings"
          >
            <IconSettings size={16} />
          </button>
        )}
      </div>
    </div>
  );
}
