/** Shared types for the Bodhi client. */

export interface ChatMessage {
  id: string;
  role: "user" | "companion" | "system";
  text: string;
  timestamp: number;
}

export interface EmotionState {
  valence: number;
  arousal: number;
  label: string;
}

export type AnimationAction = "idle" | "thinking" | "talking";

/** Messages sent TO the host. */
export interface WsOutgoing {
  type: "user.message";
  text: string;
  request_id: string;
}

/** Messages received FROM the host. */
export type WsIncoming =
  | { type: "response.text"; request_id: string; text: string }
  | { type: "emotion.update"; valence: number; arousal: number; label: string }
  | { type: "animation.command"; action: AnimationAction; request_id?: string }
  | { type: "error"; request_id?: string; detail: string };

export interface ConnectionConfig {
  hostUrl: string;
  sessionId: string;
}
