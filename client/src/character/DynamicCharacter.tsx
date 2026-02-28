/** Dynamic chibi character — renders inline SVG from CharacterConfig + animation state. */

import { useEffect, useRef, useState } from "react";
import type { CharacterConfig } from "./types";
import type { AnimationAction, EmotionState } from "../types";
import { ANIMATION_POSES, ANIMATION_FPS, type AnimState } from "./poses";
import { Shadow, Legs, Body, Arms, HairBack, Face, HairFront, Eyes, Mouth, Blush, AccessoryPart, Extras } from "./svg-parts";

interface Props {
  config: CharacterConfig;
  emotion: EmotionState;
  action: AnimationAction;
  size?: number;
}

function resolveState(action: AnimationAction, emotion: EmotionState): AnimState {
  if (action === "talking") return "talking";
  if (action === "thinking") return "thinking";
  const label = emotion.label.toLowerCase();
  if (label in ANIMATION_POSES) return label as AnimState;
  if (emotion.valence > 0.3) return "happy";
  if (emotion.valence < -0.3) return "sad";
  return "idle";
}

export function DynamicCharacter({ config, emotion, action, size = 128 }: Props) {
  const [frameIndex, setFrameIndex] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval>>(undefined);
  const state = resolveState(action, emotion);
  const frames = ANIMATION_POSES[state];
  const fps = ANIMATION_FPS[state];

  useEffect(() => {
    setFrameIndex(0);
    clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => {
      setFrameIndex((prev) => (prev + 1) % frames.length);
    }, 1000 / fps);
    return () => clearInterval(intervalRef.current);
  }, [state, frames.length, fps]);

  const pose = frames[frameIndex];

  return (
    <svg
      viewBox="0 0 128 160"
      width={size}
      height={size * 1.25}
      style={{ userSelect: "none", pointerEvents: "none" }}
    >
      <Shadow />
      <Legs config={config} variant={pose.legs} />
      <Body config={config} tilt={pose.bodyTilt} />
      <Arms config={config} variant={pose.arms} />
      <g transform={`translate(0,${pose.headDy})`}>
        <HairBack config={config} />
        <Face config={config} />
        <HairFront config={config} />
        <Eyes config={config} variant={pose.eyes} />
        <Mouth variant={pose.mouth} />
        <Blush />
        <AccessoryPart config={config} />
      </g>
      <Extras items={pose.extras} />
    </svg>
  );
}
