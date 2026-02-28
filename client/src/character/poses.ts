/** Animation pose definitions for dynamic character rendering. */

export type EyeVariant = "normal" | "happy" | "sad" | "wide" | "closed" | "angry" | "lookUp";
export type MouthVariant =
  | "smile"
  | "bigSmile"
  | "neutral"
  | "sad"
  | "open"
  | "talk1"
  | "talk2"
  | "smallO"
  | "cat";
export type ArmVariant = "default" | "wave0" | "wave1" | "wave2" | "wave3" | "think" | "hug";
export type LegVariant = "default" | "walk0" | "walk1";
export type ExtraType =
  | "sparkles"
  | "hearts"
  | "tear"
  | "question"
  | "exclaim"
  | "zzz"
  | "music"
  | "steam";

export interface PoseFrame {
  eyes: EyeVariant;
  mouth: MouthVariant;
  arms: ArmVariant;
  legs: LegVariant;
  headDy: number;
  bodyTilt: number;
  extras: ExtraType[];
}

export type AnimState =
  | "idle"
  | "talking"
  | "thinking"
  | "happy"
  | "sad"
  | "surprised"
  | "angry"
  | "confused"
  | "neutral"
  | "calm";

export const ANIMATION_POSES: Record<AnimState, PoseFrame[]> = {
  idle: [
    { eyes: "normal", mouth: "smile", arms: "default", legs: "default", headDy: 0, bodyTilt: 0, extras: [] },
    { eyes: "normal", mouth: "smile", arms: "default", legs: "default", headDy: -2, bodyTilt: 0, extras: [] },
    { eyes: "closed", mouth: "smile", arms: "default", legs: "default", headDy: 0, bodyTilt: 0, extras: [] },
    { eyes: "normal", mouth: "smile", arms: "default", legs: "default", headDy: 1, bodyTilt: 0, extras: [] },
  ],
  talking: [
    { eyes: "normal", mouth: "talk1", arms: "wave0", legs: "default", headDy: 0, bodyTilt: 0, extras: [] },
    { eyes: "normal", mouth: "open", arms: "wave1", legs: "default", headDy: 0, bodyTilt: 0, extras: [] },
    { eyes: "normal", mouth: "talk2", arms: "wave2", legs: "default", headDy: 0, bodyTilt: 0, extras: [] },
    { eyes: "normal", mouth: "talk1", arms: "wave3", legs: "default", headDy: 0, bodyTilt: 0, extras: [] },
  ],
  thinking: [
    { eyes: "lookUp", mouth: "smallO", arms: "think", legs: "default", headDy: -2, bodyTilt: 0, extras: ["question"] },
    { eyes: "lookUp", mouth: "neutral", arms: "think", legs: "default", headDy: -1, bodyTilt: 0, extras: ["question"] },
    { eyes: "closed", mouth: "neutral", arms: "think", legs: "default", headDy: 0, bodyTilt: 0, extras: ["question"] },
    { eyes: "lookUp", mouth: "smallO", arms: "think", legs: "default", headDy: -2, bodyTilt: 0, extras: ["question"] },
  ],
  happy: [
    { eyes: "happy", mouth: "bigSmile", arms: "default", legs: "default", headDy: -3, bodyTilt: 0, extras: [] },
    { eyes: "happy", mouth: "bigSmile", arms: "default", legs: "default", headDy: -1, bodyTilt: 0, extras: [] },
  ],
  sad: [
    { eyes: "sad", mouth: "sad", arms: "hug", legs: "default", headDy: 2, bodyTilt: 0, extras: ["tear"] },
    { eyes: "closed", mouth: "sad", arms: "hug", legs: "default", headDy: 3, bodyTilt: 0, extras: ["tear"] },
  ],
  surprised: [
    { eyes: "wide", mouth: "open", arms: "default", legs: "default", headDy: -4, bodyTilt: 0, extras: ["exclaim"] },
    { eyes: "wide", mouth: "smallO", arms: "default", legs: "default", headDy: -2, bodyTilt: 0, extras: ["exclaim"] },
  ],
  angry: [
    { eyes: "angry", mouth: "neutral", arms: "default", legs: "default", headDy: 0, bodyTilt: 0, extras: ["steam"] },
    { eyes: "angry", mouth: "sad", arms: "default", legs: "default", headDy: 0, bodyTilt: -2, extras: ["steam"] },
  ],
  confused: [
    { eyes: "normal", mouth: "cat", arms: "default", legs: "default", headDy: 0, bodyTilt: 3, extras: ["question"] },
    { eyes: "wide", mouth: "smallO", arms: "default", legs: "default", headDy: 0, bodyTilt: -3, extras: ["question"] },
  ],
  neutral: [
    { eyes: "normal", mouth: "neutral", arms: "default", legs: "default", headDy: 0, bodyTilt: 0, extras: [] },
    { eyes: "closed", mouth: "neutral", arms: "default", legs: "default", headDy: 0, bodyTilt: 0, extras: [] },
  ],
  calm: [
    { eyes: "closed", mouth: "smile", arms: "default", legs: "default", headDy: 1, bodyTilt: 0, extras: ["zzz", "music"] },
    { eyes: "closed", mouth: "smile", arms: "default", legs: "default", headDy: 2, bodyTilt: 0, extras: ["zzz"] },
  ],
};

export const ANIMATION_FPS: Record<AnimState, number> = {
  idle: 2,
  talking: 8,
  thinking: 3,
  happy: 3,
  sad: 2,
  surprised: 4,
  angry: 3,
  confused: 3,
  neutral: 1,
  calm: 1,
};
