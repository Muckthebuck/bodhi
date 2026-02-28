/**
 * Character customization editor — Animal Crossing-style visual UI.
 * Warm pastel theme with visual preview cards for every option.
 */

import { useState } from "react";
import "../styles/character-creator.css";
import type {
  CharacterConfig,
  HairStyle,
  EyeStyle,
  NoseStyle,
  MouthStyle,
  BlushStyle,
  FaceShape,
  OutfitStyle,
  Accessory,
} from "../character/types";
import {
  SKIN_TONES,
  HAIR_COLORS,
  EYE_COLORS,
  OUTFIT_COLORS,
  ACCESSORY_COLORS,
  HAIR_STYLES,
  EYE_STYLES,
  NOSE_STYLES,
  MOUTH_STYLES,
  BLUSH_STYLES,
  FACE_SHAPES,
  OUTFIT_STYLES,
  ACCESSORIES,
} from "../character/types";
import { DynamicCharacter, PartPreview } from "../character/DynamicCharacter";

interface Props {
  initial: CharacterConfig;
  onSave: (config: CharacterConfig) => void;
  onCancel?: () => void;
  saveLabel?: string;
}

type Category = "face" | "hair" | "eyes" | "outfit" | "extras";

const CATEGORIES: { id: Category; label: string; icon: string }[] = [
  { id: "face", label: "Face", icon: "😊" },
  { id: "hair", label: "Hair", icon: "💇" },
  { id: "eyes", label: "Eyes", icon: "👁️" },
  { id: "outfit", label: "Outfit", icon: "👕" },
  { id: "extras", label: "Extras", icon: "✨" },
];

function isLight(hex: string): boolean {
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 0xff;
  const g = (n >> 8) & 0xff;
  const b = n & 0xff;
  return r * 0.299 + g * 0.587 + b * 0.114 > 160;
}

export function CharacterCreator({ initial, onSave, onCancel, saveLabel = "Save" }: Props) {
  const [config, setConfig] = useState<CharacterConfig>({ ...initial });
  const [category, setCategory] = useState<Category>("face");

  const update = <K extends keyof CharacterConfig>(key: K, value: CharacterConfig[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="cc-theme cc-container">
      {/* ─── Live Preview ─────────────────────── */}
      <div className="cc-preview">
        <div className="cc-preview-stage cc-preview-stage-lg">
          <DynamicCharacter
            config={config}
            emotion={{ valence: 0, arousal: 0, label: "idle" }}
            action="idle"
            size={120}
          />
        </div>
        <input
          className="cc-name-input"
          type="text"
          value={config.name}
          onChange={(e) => update("name", e.target.value)}
          placeholder="Name your companion"
        />
      </div>

      {/* ─── Category Tabs ────────────────────── */}
      <div className="cc-categories">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            className={`cc-cat-btn ${category === cat.id ? "active" : ""}`}
            onClick={() => setCategory(cat.id)}
          >
            <span className="cc-cat-icon">{cat.icon}</span>
            {cat.label}
          </button>
        ))}
      </div>

      {/* ─── Options Panel ────────────────────── */}
      <div className="cc-options">
        {category === "face" && (
          <>
            <div className="cc-section-label">Skin Tone</div>
            <div className="cc-colors cc-colors-lg">
              {SKIN_TONES.map((c) => (
                <button
                  key={c.value}
                  className={`cc-swatch ${config.skinTone === c.value ? "selected" : ""} ${isLight(c.value) ? "light" : ""}`}
                  style={{ background: c.value }}
                  onClick={() => update("skinTone", c.value)}
                  title={c.label}
                />
              ))}
            </div>

            <div className="cc-section-label">Face Shape</div>
            <div className="cc-styles">
              {FACE_SHAPES.map((s) => (
                <button
                  key={s.value}
                  className={`cc-style-card ${config.faceShape === s.value ? "selected" : ""}`}
                  onClick={() => update("faceShape", s.value as FaceShape)}
                >
                  <PartPreview config={{ ...config, faceShape: s.value as FaceShape }} focus="face" size={72} />
                </button>
              ))}
            </div>

            <div className="cc-section-label">Nose</div>
            <div className="cc-styles">
              {NOSE_STYLES.map((s) => (
                <button
                  key={s.value}
                  className={`cc-style-card ${config.noseStyle === s.value ? "selected" : ""}`}
                  onClick={() => update("noseStyle", s.value as NoseStyle)}
                >
                  <PartPreview config={{ ...config, noseStyle: s.value as NoseStyle }} focus="nose" size={72} />
                </button>
              ))}
            </div>

            <div className="cc-section-label">Mouth</div>
            <div className="cc-styles">
              {MOUTH_STYLES.map((s) => (
                <button
                  key={s.value}
                  className={`cc-style-card ${config.mouthStyle === s.value ? "selected" : ""}`}
                  onClick={() => update("mouthStyle", s.value as MouthStyle)}
                >
                  <PartPreview config={{ ...config, mouthStyle: s.value as MouthStyle }} focus="mouth" size={72} />
                </button>
              ))}
            </div>

            <div className="cc-section-label">Blush</div>
            <div className="cc-styles">
              {BLUSH_STYLES.map((s) => (
                <button
                  key={s.value}
                  className={`cc-style-card ${config.blushStyle === s.value ? "selected" : ""}`}
                  onClick={() => update("blushStyle", s.value as BlushStyle)}
                >
                  <PartPreview config={{ ...config, blushStyle: s.value as BlushStyle }} focus="blush" size={72} />
                </button>
              ))}
            </div>
          </>
        )}

        {category === "hair" && (
          <>
            <div className="cc-section-label">Hair Color</div>
            <div className="cc-colors">
              {HAIR_COLORS.map((c) => (
                <button
                  key={c.value}
                  className={`cc-swatch ${config.hairColor === c.value ? "selected" : ""} ${isLight(c.value) ? "light" : ""}`}
                  style={{ background: c.value }}
                  onClick={() => update("hairColor", c.value)}
                  title={c.label}
                />
              ))}
            </div>

            <div className="cc-section-label">Hair Style</div>
            <div className="cc-styles">
              {HAIR_STYLES.map((s) => (
                <button
                  key={s.value}
                  className={`cc-style-card ${config.hairStyle === s.value ? "selected" : ""}`}
                  onClick={() => update("hairStyle", s.value as HairStyle)}
                >
                  <PartPreview config={{ ...config, hairStyle: s.value as HairStyle }} focus="hair" size={72} />
                </button>
              ))}
            </div>
          </>
        )}

        {category === "eyes" && (
          <>
            <div className="cc-section-label">Eye Color</div>
            <div className="cc-colors">
              {EYE_COLORS.map((c) => (
                <button
                  key={c.value}
                  className={`cc-swatch ${config.eyeColor === c.value ? "selected" : ""} ${isLight(c.value) ? "light" : ""}`}
                  style={{ background: c.value }}
                  onClick={() => update("eyeColor", c.value)}
                  title={c.label}
                />
              ))}
            </div>

            <div className="cc-section-label">Eye Style</div>
            <div className="cc-styles">
              {EYE_STYLES.map((s) => (
                <button
                  key={s.value}
                  className={`cc-style-card ${config.eyeStyle === s.value ? "selected" : ""}`}
                  onClick={() => update("eyeStyle", s.value as EyeStyle)}
                >
                  <PartPreview config={{ ...config, eyeStyle: s.value as EyeStyle }} focus="eyes" size={72} />
                </button>
              ))}
            </div>
          </>
        )}

        {category === "outfit" && (
          <>
            <div className="cc-section-label">Outfit Color</div>
            <div className="cc-colors">
              {OUTFIT_COLORS.map((c) => (
                <button
                  key={c.value}
                  className={`cc-swatch ${config.outfitColor === c.value ? "selected" : ""} ${isLight(c.value) ? "light" : ""}`}
                  style={{ background: c.value }}
                  onClick={() => update("outfitColor", c.value)}
                  title={c.label}
                />
              ))}
            </div>

            <div className="cc-section-label">Outfit Style</div>
            <div className="cc-styles">
              {OUTFIT_STYLES.map((s) => (
                <button
                  key={s.value}
                  className={`cc-style-card ${config.outfitStyle === s.value ? "selected" : ""}`}
                  onClick={() => update("outfitStyle", s.value as OutfitStyle)}
                >
                  <PartPreview config={{ ...config, outfitStyle: s.value as OutfitStyle }} focus="outfit" size={72} />
                </button>
              ))}
            </div>
          </>
        )}

        {category === "extras" && (
          <>
            <div className="cc-section-label">Accessory Color</div>
            <div className="cc-colors">
              {ACCESSORY_COLORS.map((c) => (
                <button
                  key={c.value}
                  className={`cc-swatch ${config.accessoryColor === c.value ? "selected" : ""} ${isLight(c.value) ? "light" : ""}`}
                  style={{ background: c.value }}
                  onClick={() => update("accessoryColor", c.value)}
                  title={c.label}
                />
              ))}
            </div>

            <div className="cc-section-label">Accessory</div>
            <div className="cc-styles">
              {ACCESSORIES.map((s) => (
                <button
                  key={s.value}
                  className={`cc-style-card ${config.accessory === s.value ? "selected" : ""}`}
                  onClick={() => update("accessory", s.value as Accessory)}
                >
                  <PartPreview config={{ ...config, accessory: s.value as Accessory }} focus="accessory" size={72} />
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* ─── Action Buttons ───────────────────── */}
      <div className="cc-actions">
        {onCancel && (
          <button className="cc-cancel-btn" onClick={onCancel}>
            Cancel
          </button>
        )}
        <button className="cc-save-btn" onClick={() => onSave(config)}>
          {saveLabel}
        </button>
      </div>
    </div>
  );
}
