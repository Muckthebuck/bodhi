import { useEffect, useState } from "react";
import { listen } from "@tauri-apps/api/event";
import { SpriteCharacter } from "./SpriteCharacter";
import { SkeletalCharacter } from "./SkeletalCharacter";
import type { AnimationAction, EmotionState } from "../types";

type CharacterStyle = "sprite" | "skeletal";

interface OverlayState {
  emotion: EmotionState;
  action: AnimationAction;
  style: CharacterStyle;
  size: number;
}

/**
 * Overlay window — receives state from main window via Tauri events.
 * Renders the character on a fully transparent background.
 */
export function OverlayApp() {
  const [state, setState] = useState<OverlayState>({
    emotion: { valence: 0, arousal: 0, label: "neutral" },
    action: "idle",
    style: "sprite",
    size: 128,
  });

  useEffect(() => {
    const unlisten = listen<OverlayState>("overlay-update", (event) => {
      setState(event.payload);
    });
    return () => {
      unlisten.then((fn) => fn());
    };
  }, []);

  const Character =
    state.style === "skeletal" ? SkeletalCharacter : SpriteCharacter;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "transparent",
      }}
    >
      <Character emotion={state.emotion} action={state.action} size={state.size} />
    </div>
  );
}
