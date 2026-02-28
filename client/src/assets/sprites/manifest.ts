/**
 * Sprite manifest — maps animation states to frame SVG imports.
 * Each state has an array of frames for animation cycling.
 */

// Idle
import idle1 from "./idle-1.svg";
import idle2 from "./idle-2.svg";
import idle3 from "./idle-3.svg";
import idle4 from "./idle-4.svg";

// Talking
import talking1 from "./talking-1.svg";
import talking2 from "./talking-2.svg";
import talking3 from "./talking-3.svg";
import talking4 from "./talking-4.svg";

// Thinking
import thinking1 from "./thinking-1.svg";
import thinking2 from "./thinking-2.svg";
import thinking3 from "./thinking-3.svg";
import thinking4 from "./thinking-4.svg";

// Emotions
import happy1 from "./happy-1.svg";
import happy2 from "./happy-2.svg";
import sad1 from "./sad-1.svg";
import sad2 from "./sad-2.svg";
import surprised1 from "./surprised-1.svg";
import surprised2 from "./surprised-2.svg";
import angry1 from "./angry-1.svg";
import angry2 from "./angry-2.svg";
import confused1 from "./confused-1.svg";
import confused2 from "./confused-2.svg";
import neutral1 from "./neutral-1.svg";
import neutral2 from "./neutral-2.svg";
import calm1 from "./calm-1.svg";
import calm2 from "./calm-2.svg";

export type SpriteState =
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

export const SPRITE_FRAMES: Record<SpriteState, string[]> = {
  idle: [idle1, idle2, idle3, idle4],
  talking: [talking1, talking2, talking3, talking4],
  thinking: [thinking1, thinking2, thinking3, thinking4],
  happy: [happy1, happy2],
  sad: [sad1, sad2],
  surprised: [surprised1, surprised2],
  angry: [angry1, angry2],
  confused: [confused1, confused2],
  neutral: [neutral1, neutral2],
  calm: [calm1, calm2],
};

/** Frames per second for each animation state. */
export const SPRITE_FPS: Record<SpriteState, number> = {
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
