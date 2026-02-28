import { useEffect, useState } from "react";
import { listen } from "@tauri-apps/api/event";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { SkeletalCharacter } from "./SkeletalCharacter";
import { DynamicCharacter } from "../character/DynamicCharacter";
import { createDefaultCharacter, type CharacterConfig } from "../character/types";
import type { AnimationAction, EmotionState } from "../types";

type CharacterStyle = "sprite" | "skeletal";

interface OverlayState {
  emotion: EmotionState;
  action: AnimationAction;
  style: CharacterStyle;
  size: number;
  character?: CharacterConfig;
  visible?: boolean;
}

/**
 * Overlay window — receives state from main window via Tauri events.
 * Renders the character on a fully transparent background.
 * Only shows content when visible flag is true.
 */
export function OverlayApp() {
  const [state, setState] = useState<OverlayState>({
    emotion: { valence: 0, arousal: 0, label: "neutral" },
    action: "idle",
    style: "sprite",
    size: 128,
    visible: false,
  });

  useEffect(() => {
    const unlisten = listen<OverlayState>("overlay-update", (event) => {
      setState(event.payload);
    });
    return () => {
      unlisten.then((fn) => fn());
    };
  }, []);

  // Don't render anything when hidden
  if (!state.visible) {
    return null;
  }

  const handleDragStart = () => {
    getCurrentWindow().startDragging().catch(() => {});
  };

  return (
    <div
      onMouseDown={handleDragStart}
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "transparent",
        cursor: "grab",
      }}
    >
      {state.style === "skeletal" ? (
        <SkeletalCharacter emotion={state.emotion} action={state.action} size={state.size} />
      ) : (
        <DynamicCharacter
          config={state.character || createDefaultCharacter()}
          emotion={state.emotion}
          action={state.action}
          size={state.size}
        />
      )}
    </div>
  );
}
