import { useEffect, useRef, useState } from "react";
import {
  SPRITE_FRAMES,
  SPRITE_FPS,
  type SpriteState,
} from "../assets/sprites/manifest";
import type { AnimationAction, EmotionState } from "../types";

interface Props {
  emotion: EmotionState;
  action: AnimationAction;
  size?: number;
}

/** Map emotion label → sprite state. Falls back to action-based state. */
function resolveState(action: AnimationAction, emotion: EmotionState): SpriteState {
  // Action takes priority when actively talking/thinking
  if (action === "talking") return "talking";
  if (action === "thinking") return "thinking";

  // Otherwise use emotion label
  const label = emotion.label.toLowerCase();
  if (label in SPRITE_FRAMES) return label as SpriteState;

  // Fallback: map VAD to basic states
  if (emotion.valence > 0.3) return "happy";
  if (emotion.valence < -0.3) return "sad";
  return "idle";
}

export function SpriteCharacter({ emotion, action, size = 128 }: Props) {
  const [frameIndex, setFrameIndex] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval>>(undefined);
  const state = resolveState(action, emotion);
  const frames = SPRITE_FRAMES[state];
  const fps = SPRITE_FPS[state];

  useEffect(() => {
    setFrameIndex(0);
    clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => {
      setFrameIndex((prev) => (prev + 1) % frames.length);
    }, 1000 / fps);
    return () => clearInterval(intervalRef.current);
  }, [state, frames.length, fps]);

  return (
    <img
      src={frames[frameIndex]}
      alt={`Bodhi — ${state}`}
      width={size}
      height={size}
      style={{ imageRendering: "auto", userSelect: "none", pointerEvents: "none" }}
    />
  );
}
