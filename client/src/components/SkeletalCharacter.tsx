import Lottie from "lottie-react";
import { useMemo } from "react";
import type { AnimationAction, EmotionState } from "../types";

// Import all Lottie JSON animations
import idleData from "../assets/lottie/idle.json";
import talkingData from "../assets/lottie/talking.json";
import thinkingData from "../assets/lottie/thinking.json";
import happyData from "../assets/lottie/happy.json";
import sadData from "../assets/lottie/sad.json";
import surprisedData from "../assets/lottie/surprised.json";
import angryData from "../assets/lottie/angry.json";
import confusedData from "../assets/lottie/confused.json";
import neutralData from "../assets/lottie/neutral.json";
import calmData from "../assets/lottie/calm.json";

type LottieState =
  | "idle" | "talking" | "thinking"
  | "happy" | "sad" | "surprised" | "angry" | "confused" | "neutral" | "calm";

const LOTTIE_DATA: Record<LottieState, object> = {
  idle: idleData,
  talking: talkingData,
  thinking: thinkingData,
  happy: happyData,
  sad: sadData,
  surprised: surprisedData,
  angry: angryData,
  confused: confusedData,
  neutral: neutralData,
  calm: calmData,
};

function resolveState(action: AnimationAction, emotion: EmotionState): LottieState {
  if (action === "talking") return "talking";
  if (action === "thinking") return "thinking";

  const label = emotion.label.toLowerCase();
  if (label in LOTTIE_DATA) return label as LottieState;

  if (emotion.valence > 0.3) return "happy";
  if (emotion.valence < -0.3) return "sad";
  return "idle";
}

interface Props {
  emotion: EmotionState;
  action: AnimationAction;
  size?: number;
}

export function SkeletalCharacter({ emotion, action, size = 128 }: Props) {
  const state = resolveState(action, emotion);
  const animationData = useMemo(() => LOTTIE_DATA[state], [state]);

  return (
    <Lottie
      animationData={animationData}
      loop
      autoplay
      style={{ width: size, height: size, pointerEvents: "none", userSelect: "none" }}
    />
  );
}
