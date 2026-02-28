/**
 * Character customization editor with live preview.
 * Used in onboarding and settings.
 */

import { useState } from "react";
import type {
  CharacterConfig,
  HairStyle,
  EyeStyle,
  FaceShape,
  OutfitStyle,
  Accessory,
} from "../character/types";
import {
  SKIN_TONES,
  HAIR_COLORS,
  EYE_COLORS,
  OUTFIT_COLORS,
  HAIR_STYLES,
  EYE_STYLES,
  FACE_SHAPES,
  OUTFIT_STYLES,
  ACCESSORIES,
} from "../character/types";
import { DynamicCharacter } from "../character/DynamicCharacter";

interface Props {
  initial: CharacterConfig;
  onSave: (config: CharacterConfig) => void;
  onCancel?: () => void;
  saveLabel?: string;
}

type Category = "face" | "hair" | "eyes" | "outfit" | "accessories";

const CATEGORIES: { id: Category; label: string; icon: string }[] = [
  { id: "face", label: "Face", icon: "😊" },
  { id: "hair", label: "Hair", icon: "💇" },
  { id: "eyes", label: "Eyes", icon: "👁" },
  { id: "outfit", label: "Outfit", icon: "👕" },
  { id: "accessories", label: "Extras", icon: "🎀" },
];

export function CharacterCreator({ initial, onSave, onCancel, saveLabel = "Save" }: Props) {
  const [config, setConfig] = useState<CharacterConfig>({ ...initial });
  const [category, setCategory] = useState<Category>("face");

  const update = <K extends keyof CharacterConfig>(key: K, value: CharacterConfig[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div style={containerStyle}>
      {/* Preview area */}
      <div style={previewStyle}>
        <DynamicCharacter
          config={config}
          emotion={{ valence: 0.3, arousal: 0.2, label: "happy" }}
          action="idle"
          size={160}
        />
        <input
          type="text"
          value={config.name}
          onChange={(e) => update("name", e.target.value)}
          placeholder="Character name"
          style={nameInputStyle}
        />
      </div>

      {/* Category tabs */}
      <div style={tabsStyle}>
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setCategory(cat.id)}
            style={{
              ...tabStyle,
              ...(category === cat.id ? activeTabStyle : {}),
            }}
          >
            {cat.icon} {cat.label}
          </button>
        ))}
      </div>

      {/* Options panel */}
      <div style={optionsStyle}>
        {category === "face" && (
          <>
            <OptionLabel>Skin Tone</OptionLabel>
            <ColorPalette
              colors={SKIN_TONES}
              selected={config.skinTone}
              onSelect={(v) => update("skinTone", v)}
            />
            <OptionLabel>Face Shape</OptionLabel>
            <StylePicker
              options={FACE_SHAPES}
              selected={config.faceShape}
              onSelect={(v) => update("faceShape", v as FaceShape)}
            />
          </>
        )}
        {category === "hair" && (
          <>
            <OptionLabel>Hair Style</OptionLabel>
            <StylePicker
              options={HAIR_STYLES}
              selected={config.hairStyle}
              onSelect={(v) => update("hairStyle", v as HairStyle)}
            />
            <OptionLabel>Hair Color</OptionLabel>
            <ColorPalette
              colors={HAIR_COLORS}
              selected={config.hairColor}
              onSelect={(v) => update("hairColor", v)}
            />
          </>
        )}
        {category === "eyes" && (
          <>
            <OptionLabel>Eye Style</OptionLabel>
            <StylePicker
              options={EYE_STYLES}
              selected={config.eyeStyle}
              onSelect={(v) => update("eyeStyle", v as EyeStyle)}
            />
            <OptionLabel>Eye Color</OptionLabel>
            <ColorPalette
              colors={EYE_COLORS}
              selected={config.eyeColor}
              onSelect={(v) => update("eyeColor", v)}
            />
          </>
        )}
        {category === "outfit" && (
          <>
            <OptionLabel>Outfit Style</OptionLabel>
            <StylePicker
              options={OUTFIT_STYLES}
              selected={config.outfitStyle}
              onSelect={(v) => update("outfitStyle", v as OutfitStyle)}
            />
            <OptionLabel>Outfit Color</OptionLabel>
            <ColorPalette
              colors={OUTFIT_COLORS}
              selected={config.outfitColor}
              onSelect={(v) => update("outfitColor", v)}
            />
          </>
        )}
        {category === "accessories" && (
          <>
            <OptionLabel>Accessory</OptionLabel>
            <StylePicker
              options={ACCESSORIES}
              selected={config.accessory}
              onSelect={(v) => update("accessory", v as Accessory)}
            />
          </>
        )}
      </div>

      {/* Action buttons */}
      <div style={actionsStyle}>
        {onCancel && (
          <button onClick={onCancel} style={cancelBtnStyle}>
            Cancel
          </button>
        )}
        <button onClick={() => onSave(config)} style={saveBtnStyle}>
          {saveLabel}
        </button>
      </div>
    </div>
  );
}

// ─── Sub-components ──────────────────────────────────────────

function OptionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 12, marginBottom: 4 }}>
      {children}
    </div>
  );
}

function ColorPalette({
  colors,
  selected,
  onSelect,
}: {
  colors: { value: string; label: string }[];
  selected: string;
  onSelect: (color: string) => void;
}) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
      {colors.map((c) => (
        <button
          key={c.value}
          onClick={() => onSelect(c.value)}
          title={c.label}
          style={{
            width: 32,
            height: 32,
            borderRadius: "50%",
            border: selected === c.value ? "3px solid var(--accent-bright)" : "2px solid var(--border)",
            background: c.value,
            cursor: "pointer",
            transition: "transform 0.1s",
            transform: selected === c.value ? "scale(1.15)" : "scale(1)",
          }}
        />
      ))}
    </div>
  );
}

function StylePicker({
  options,
  selected,
  onSelect,
}: {
  options: { value: string; label: string }[];
  selected: string;
  onSelect: (value: string) => void;
}) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
      {options.map((o) => (
        <button
          key={o.value}
          onClick={() => onSelect(o.value)}
          style={{
            padding: "6px 14px",
            borderRadius: 20,
            border:
              selected === o.value
                ? "2px solid var(--accent-bright)"
                : "1px solid var(--border)",
            background: selected === o.value ? "var(--accent)" : "var(--bg)",
            color: "var(--text)",
            cursor: "pointer",
            fontSize: 12,
          }}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

// ─── Styles ──────────────────────────────────────────────────

const containerStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  height: "100%",
  padding: 20,
  gap: 12,
  overflow: "hidden",
};

const previewStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  gap: 12,
  padding: 16,
  background: "var(--bg-secondary)",
  borderRadius: "var(--radius)",
};

const nameInputStyle: React.CSSProperties = {
  padding: "8px 12px",
  borderRadius: "var(--radius)",
  border: "1px solid var(--border)",
  background: "var(--bg)",
  color: "var(--text)",
  fontSize: 16,
  textAlign: "center",
  width: 200,
  outline: "none",
};

const tabsStyle: React.CSSProperties = {
  display: "flex",
  gap: 4,
  overflowX: "auto",
};

const tabStyle: React.CSSProperties = {
  flex: 1,
  padding: "8px 4px",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius)",
  background: "var(--bg)",
  color: "var(--text-muted)",
  cursor: "pointer",
  fontSize: 11,
  whiteSpace: "nowrap",
};

const activeTabStyle: React.CSSProperties = {
  background: "var(--accent)",
  color: "var(--text)",
  borderColor: "var(--accent-bright)",
};

const optionsStyle: React.CSSProperties = {
  flex: 1,
  overflowY: "auto",
  padding: "4px 0",
};

const actionsStyle: React.CSSProperties = {
  display: "flex",
  gap: 8,
  justifyContent: "flex-end",
  paddingTop: 8,
  borderTop: "1px solid var(--border)",
};

const saveBtnStyle: React.CSSProperties = {
  padding: "10px 24px",
  borderRadius: "var(--radius)",
  border: "none",
  background: "var(--accent-bright)",
  color: "#fff",
  cursor: "pointer",
  fontSize: 14,
  fontWeight: 600,
};

const cancelBtnStyle: React.CSSProperties = {
  padding: "10px 24px",
  borderRadius: "var(--radius)",
  border: "1px solid var(--border)",
  background: "transparent",
  color: "var(--text-muted)",
  cursor: "pointer",
  fontSize: 14,
};
