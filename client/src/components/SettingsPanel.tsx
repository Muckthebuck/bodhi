import { useState } from "react";
import type { CharacterConfig } from "../character/types";
import { DynamicCharacter } from "../character/DynamicCharacter";

export type CharacterStyle = "sprite" | "skeletal";
export type CharacterSize = "small" | "medium" | "large";
export type CharacterPosition = "bottom-right" | "bottom-left" | "top-right" | "top-left";

export interface AppSettings {
  characterStyle: CharacterStyle;
  characterSize: CharacterSize;
  characterPosition: CharacterPosition;
  showCharacter: boolean;
}

const SETTINGS_KEY = "bodhi-settings";

export function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) return { ...defaultSettings(), ...JSON.parse(raw) };
  } catch { /* ignore */ }
  return defaultSettings();
}

export function saveSettings(settings: AppSettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

function defaultSettings(): AppSettings {
  return {
    characterStyle: "sprite",
    characterSize: "medium",
    characterPosition: "bottom-right",
    showCharacter: true,
  };
}

interface Props {
  settings: AppSettings;
  onUpdate: (settings: AppSettings) => void;
  onClose: () => void;
  characters: CharacterConfig[];
  activeCharacterId: string;
  onEditCharacter: () => void;
  onNewCharacter: () => void;
  onSwitchCharacter: (id: string) => void;
}

export function SettingsPanel({
  settings,
  onUpdate,
  onClose,
  characters,
  activeCharacterId,
  onEditCharacter,
  onNewCharacter,
  onSwitchCharacter,
}: Props) {
  const [local, setLocal] = useState<AppSettings>(settings);

  const update = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    const next = { ...local, [key]: value };
    setLocal(next);
    saveSettings(next);
    onUpdate(next);
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        width: 300,
        height: "100vh",
        background: "var(--bg-secondary)",
        borderLeft: "1px solid var(--border)",
        padding: 20,
        display: "flex",
        flexDirection: "column",
        gap: 16,
        zIndex: 100,
        overflowY: "auto",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>Settings</h3>
        <button
          onClick={onClose}
          style={{
            background: "transparent",
            border: "none",
            color: "var(--text)",
            fontSize: 18,
            cursor: "pointer",
          }}
        >
          ✕
        </button>
      </div>

      {/* Character Management */}
      <div>
        <span style={{ color: "var(--text-muted)", fontSize: 12 }}>Character</span>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 8 }}>
          <DynamicCharacter
            config={characters.find((c) => c.id === activeCharacterId) || characters[0]}
            emotion={{ valence: 0, arousal: 0, label: "neutral" }}
            action="idle"
            size={48}
          />
          {characters.length > 1 ? (
            <select
              value={activeCharacterId}
              onChange={(e) => onSwitchCharacter(e.target.value)}
              style={selectStyle}
            >
              {characters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          ) : (
            <span style={{ fontSize: 14 }}>{characters[0]?.name || "Bodhi"}</span>
          )}
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button onClick={onEditCharacter} style={smallBtnStyle}>
            Edit
          </button>
          <button onClick={onNewCharacter} style={smallBtnStyle}>
            New Character
          </button>
        </div>
      </div>

      {/* Character Style */}
      <label>
        <span style={{ color: "var(--text-muted)", fontSize: 12 }}>Character Style</span>
        <select
          value={local.characterStyle}
          onChange={(e) => update("characterStyle", e.target.value as CharacterStyle)}
          style={selectStyle}
        >
          <option value="sprite">2D Sprite</option>
          <option value="skeletal">2D Skeletal (Lottie)</option>
        </select>
      </label>

      {/* Character Size */}
      <label>
        <span style={{ color: "var(--text-muted)", fontSize: 12 }}>Character Size</span>
        <select
          value={local.characterSize}
          onChange={(e) => update("characterSize", e.target.value as CharacterSize)}
          style={selectStyle}
        >
          <option value="small">Small (64px)</option>
          <option value="medium">Medium (128px)</option>
          <option value="large">Large (192px)</option>
        </select>
      </label>

      {/* Show Character */}
      <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <input
          type="checkbox"
          checked={local.showCharacter}
          onChange={(e) => update("showCharacter", e.target.checked)}
        />
        <span>Show character</span>
      </label>
    </div>
  );
}

const selectStyle: React.CSSProperties = {
  width: "100%",
  padding: "8px 10px",
  borderRadius: "var(--radius)",
  border: "1px solid var(--border)",
  background: "var(--bg)",
  color: "var(--text)",
  outline: "none",
  fontSize: 13,
  marginTop: 4,
};

const smallBtnStyle: React.CSSProperties = {
  padding: "6px 14px",
  borderRadius: "var(--radius)",
  border: "1px solid var(--border)",
  background: "var(--bg)",
  color: "var(--text)",
  cursor: "pointer",
  fontSize: 12,
};
