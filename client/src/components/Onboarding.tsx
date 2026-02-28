/** First-launch onboarding — step-by-step guided character creation. */

import { useState, useMemo, useCallback } from "react";
import "../styles/character-creator.css";
import type {
  CharacterConfig,
  HairStyle,
  EyeStyle,
  FaceShape,
  OutfitStyle,
  Accessory,
} from "../character/types";
import {
  createDefaultCharacter,
  SKIN_TONES,
  HAIR_COLORS,
  EYE_COLORS,
  OUTFIT_COLORS,
  ACCESSORY_COLORS,
  HAIR_STYLES,
  EYE_STYLES,
  FACE_SHAPES,
  OUTFIT_STYLES,
  ACCESSORIES,
} from "../character/types";
import { DynamicCharacter, PartPreview } from "../character/DynamicCharacter";

interface Props {
  onComplete: (character: CharacterConfig) => void;
}

type Step = "welcome" | "skin" | "face" | "hair" | "outfit" | "accessories" | "name";

const STEPS: Step[] = ["welcome", "skin", "face", "hair", "outfit", "accessories", "name"];

const STEP_LABELS: Record<Step, string> = {
  welcome: "Welcome",
  skin: "Skin Tone",
  face: "Face & Eyes",
  hair: "Hair",
  outfit: "Outfit",
  accessories: "Accessories",
  name: "Name",
};

function isLight(hex: string): boolean {
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 0xff, g = (n >> 8) & 0xff, b = n & 0xff;
  return r * 0.299 + g * 0.587 + b * 0.114 > 160;
}

function randomFrom<T>(arr: readonly T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomizeCharacter(): CharacterConfig {
  return {
    ...createDefaultCharacter(),
    skinTone: randomFrom(SKIN_TONES).value,
    hairColor: randomFrom(HAIR_COLORS).value,
    hairStyle: randomFrom(HAIR_STYLES).value,
    eyeColor: randomFrom(EYE_COLORS).value,
    eyeStyle: randomFrom(EYE_STYLES).value,
    faceShape: randomFrom(FACE_SHAPES).value as FaceShape,
    outfitColor: randomFrom(OUTFIT_COLORS).value,
    outfitStyle: randomFrom(OUTFIT_STYLES).value,
    accessory: randomFrom(ACCESSORIES).value as Accessory,
    accessoryColor: randomFrom(ACCESSORY_COLORS).value,
  };
}

export function Onboarding({ onComplete }: Props) {
  const defaultChar = useMemo(createDefaultCharacter, []);
  const [config, setConfig] = useState<CharacterConfig>({ ...defaultChar });
  const [step, setStep] = useState<Step>("welcome");

  const update = useCallback(<K extends keyof CharacterConfig>(key: K, value: CharacterConfig[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  }, []);

  const stepIdx = STEPS.indexOf(step);
  const isFirst = stepIdx === 0;
  const isLast = step === "name";

  const next = () => {
    if (isLast) {
      onComplete(config);
    } else {
      setStep(STEPS[stepIdx + 1]);
    }
  };
  const back = () => {
    if (!isFirst) setStep(STEPS[stepIdx - 1]);
  };

  return (
    <div className="cc-theme onboard-root">
      {/* ── Progress dots ── */}
      {step !== "welcome" && (
        <div className="onboard-progress">
          {STEPS.filter((s) => s !== "welcome").map((s) => (
            <div key={s} className={`onboard-dot ${s === step ? "active" : STEPS.indexOf(s) < stepIdx ? "done" : ""}`} />
          ))}
        </div>
      )}

      {/* ── Character preview (visible on all steps except welcome) ── */}
      {step !== "welcome" && (
        <div className="onboard-preview">
          <div className="onboard-preview-stage">
            <DynamicCharacter
              config={config}
              emotion={{ valence: 0, arousal: 0, label: "idle" }}
              action="idle"
              size={120}
            />
          </div>
        </div>
      )}

      {/* ── Step content ── */}
      <div className="onboard-content">
        {step === "welcome" && (
          <div className="onboard-welcome-inner">
            <div className="onboard-character-bounce">
              <DynamicCharacter
                config={config}
                emotion={{ valence: 0, arousal: 0, label: "idle" }}
                action="idle"
                size={140}
              />
            </div>
            <h1 className="onboard-title">Welcome to Bodhi</h1>
            <p className="onboard-subtitle">
              Your private AI companion that lives on your device.
            </p>
            <div className="onboard-welcome-buttons">
              <button className="onboard-primary-btn" onClick={next}>
                Create Your Companion
              </button>
            </div>
          </div>
        )}

        {step === "skin" && (
          <div className="onboard-step">
            <h2 className="onboard-step-title">Choose a skin tone</h2>
            <div className="onboard-step-hint">This will be your companion's base color.</div>
            <div className="onboard-swatches onboard-swatches-lg">
              {SKIN_TONES.map((c) => (
                <button
                  key={c.value}
                  className={`cc-swatch cc-swatch-lg ${config.skinTone === c.value ? "selected" : ""} ${isLight(c.value) ? "light" : ""}`}
                  style={{ background: c.value }}
                  onClick={() => update("skinTone", c.value)}
                  title={c.label}
                />
              ))}
            </div>
            <div className="onboard-section-divider" />
            <h3 className="onboard-mini-label">Face Shape</h3>
            <div className="onboard-style-row">
              {FACE_SHAPES.map((s) => (
                <button
                  key={s.value}
                  className={`cc-style-card cc-style-card-lg ${config.faceShape === s.value ? "selected" : ""}`}
                  onClick={() => update("faceShape", s.value as FaceShape)}
                >
                  <PartPreview config={{ ...config, faceShape: s.value as FaceShape }} focus="face" size={72} />
                </button>
              ))}
            </div>
          </div>
        )}

        {step === "face" && (
          <div className="onboard-step">
            <h2 className="onboard-step-title">Pick your eyes</h2>
            <div className="onboard-step-hint">Eyes give your companion personality!</div>
            <h3 className="onboard-mini-label">Eye Color</h3>
            <div className="onboard-swatches">
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
            <div className="onboard-section-divider" />
            <h3 className="onboard-mini-label">Eye Style</h3>
            <div className="onboard-style-row">
              {EYE_STYLES.map((s) => (
                <button
                  key={s.value}
                  className={`cc-style-card cc-style-card-lg ${config.eyeStyle === s.value ? "selected" : ""}`}
                  onClick={() => update("eyeStyle", s.value as EyeStyle)}
                >
                  <PartPreview config={{ ...config, eyeStyle: s.value as EyeStyle }} focus="eyes" size={72} />
                </button>
              ))}
            </div>
          </div>
        )}

        {step === "hair" && (
          <div className="onboard-step">
            <h2 className="onboard-step-title">Style your hair</h2>
            <div className="onboard-step-hint">Pick a hairstyle and color.</div>
            <h3 className="onboard-mini-label">Hair Color</h3>
            <div className="onboard-swatches">
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
            <div className="onboard-section-divider" />
            <h3 className="onboard-mini-label">Hair Style</h3>
            <div className="onboard-style-row">
              {HAIR_STYLES.map((s) => (
                <button
                  key={s.value}
                  className={`cc-style-card cc-style-card-lg ${config.hairStyle === s.value ? "selected" : ""}`}
                  onClick={() => update("hairStyle", s.value as HairStyle)}
                >
                  <PartPreview config={{ ...config, hairStyle: s.value as HairStyle }} focus="hair" size={72} />
                </button>
              ))}
            </div>
          </div>
        )}

        {step === "outfit" && (
          <div className="onboard-step">
            <h2 className="onboard-step-title">Choose an outfit</h2>
            <div className="onboard-step-hint">Dress up your companion!</div>
            <h3 className="onboard-mini-label">Outfit Color</h3>
            <div className="onboard-swatches">
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
            <div className="onboard-section-divider" />
            <h3 className="onboard-mini-label">Outfit Style</h3>
            <div className="onboard-style-row">
              {OUTFIT_STYLES.map((s) => (
                <button
                  key={s.value}
                  className={`cc-style-card cc-style-card-lg ${config.outfitStyle === s.value ? "selected" : ""}`}
                  onClick={() => update("outfitStyle", s.value as OutfitStyle)}
                >
                  <PartPreview config={{ ...config, outfitStyle: s.value as OutfitStyle }} focus="outfit" size={72} />
                </button>
              ))}
            </div>
          </div>
        )}

        {step === "accessories" && (
          <div className="onboard-step">
            <h2 className="onboard-step-title">Add an accessory</h2>
            <div className="onboard-step-hint">Give your companion some flair!</div>
            <h3 className="onboard-mini-label">Accessory Color</h3>
            <div className="onboard-swatches">
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
            <div className="onboard-section-divider" />
            <h3 className="onboard-mini-label">Accessory</h3>
            <div className="onboard-style-row">
              {ACCESSORIES.map((s) => (
                <button
                  key={s.value}
                  className={`cc-style-card cc-style-card-lg ${config.accessory === s.value ? "selected" : ""}`}
                  onClick={() => update("accessory", s.value as Accessory)}
                >
                  <PartPreview config={{ ...config, accessory: s.value as Accessory }} focus="accessory" size={72} />
                </button>
              ))}
            </div>
          </div>
        )}

        {step === "name" && (
          <div className="onboard-step onboard-name-step">
            <h2 className="onboard-step-title">Name your companion</h2>
            <div className="onboard-step-hint">Give your companion a name to make it yours.</div>
            <input
              className="onboard-name-input"
              type="text"
              value={config.name}
              onChange={(e) => update("name", e.target.value)}
              placeholder="Enter a name..."
              autoFocus
            />
          </div>
        )}
      </div>

      {/* ── Navigation buttons ── */}
      {step !== "welcome" && (
        <div className="onboard-nav">
          <button className="onboard-back-btn" onClick={back}>
            Back
          </button>
          {step !== "name" && (
            <button className="onboard-secondary-btn" onClick={() => setConfig(randomizeCharacter())}>
              Randomize
            </button>
          )}
          <button className="onboard-primary-btn" onClick={next}>
            {isLast ? "Done" : "Next"}
          </button>
        </div>
      )}
    </div>
  );
}
