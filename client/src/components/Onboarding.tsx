/** First-launch onboarding — welcome + character creation. */

import { useState } from "react";
import type { CharacterConfig } from "../character/types";
import { createDefaultCharacter } from "../character/types";
import { CharacterCreator } from "./CharacterCreator";

interface Props {
  onComplete: (character: CharacterConfig) => void;
}

export function Onboarding({ onComplete }: Props) {
  const [step, setStep] = useState<"welcome" | "create">("welcome");
  const [defaultChar] = useState(createDefaultCharacter);

  if (step === "welcome") {
    return (
      <div style={welcomeStyle}>
        <div style={{ fontSize: 64, marginBottom: 16 }}>🧠</div>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>Welcome to Bodhi</h1>
        <p
          style={{
            color: "var(--text-muted)",
            maxWidth: 400,
            textAlign: "center",
            lineHeight: 1.6,
          }}
        >
          Your private AI companion. Let&apos;s start by creating your companion character.
        </p>
        <button onClick={() => setStep("create")} style={startBtnStyle}>
          Create Your Companion
        </button>
      </div>
    );
  }

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
        <h2 style={{ margin: 0, fontSize: 18 }}>Design Your Companion</h2>
        <p style={{ margin: "4px 0 0", color: "var(--text-muted)", fontSize: 13 }}>
          Customize your character. You can change this later in settings.
        </p>
      </div>
      <div style={{ flex: 1, overflow: "hidden" }}>
        <CharacterCreator
          initial={defaultChar}
          onSave={onComplete}
          saveLabel="Create Character"
        />
      </div>
    </div>
  );
}

const welcomeStyle: React.CSSProperties = {
  height: "100vh",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  gap: 16,
  padding: 40,
};

const startBtnStyle: React.CSSProperties = {
  marginTop: 16,
  padding: "14px 32px",
  borderRadius: "var(--radius)",
  border: "none",
  background: "var(--accent-bright)",
  color: "#fff",
  fontSize: 16,
  fontWeight: 600,
  cursor: "pointer",
};
