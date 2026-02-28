/** Character customization types, palettes, and persistence. */

export interface CharacterConfig {
  id: string;
  name: string;
  skinTone: string;
  hairColor: string;
  hairStyle: HairStyle;
  eyeColor: string;
  eyeStyle: EyeStyle;
  faceShape: FaceShape;
  outfitColor: string;
  outfitStyle: OutfitStyle;
  accessory: Accessory;
}

export type HairStyle = "short" | "long" | "curly" | "spiky" | "bob" | "ponytail";
export type EyeStyle = "round" | "narrow" | "wide" | "cat";
export type FaceShape = "round" | "oval" | "heart";
export type OutfitStyle = "hoodie" | "tshirt" | "dress" | "jacket";
export type Accessory =
  | "none"
  | "glasses"
  | "round-glasses"
  | "hat"
  | "bow"
  | "headband"
  | "sunglasses";

export interface ColorOption {
  value: string;
  label: string;
}

export interface StyleOption<T> {
  value: T;
  label: string;
}

// ─── Color Palettes ──────────────────────────────────────────

export const SKIN_TONES: ColorOption[] = [
  { value: "#fde8d0", label: "Light" },
  { value: "#f5d0a9", label: "Fair" },
  { value: "#d4a574", label: "Medium" },
  { value: "#c4956a", label: "Olive" },
  { value: "#8d5524", label: "Brown" },
  { value: "#5c3d2e", label: "Dark" },
];

export const HAIR_COLORS: ColorOption[] = [
  { value: "#1a1a2e", label: "Black" },
  { value: "#3d2b1f", label: "Dark Brown" },
  { value: "#6b4423", label: "Brown" },
  { value: "#922b05", label: "Auburn" },
  { value: "#c9a94e", label: "Blonde" },
  { value: "#e8dcc8", label: "Platinum" },
  { value: "#b33030", label: "Red" },
  { value: "#2c3e6b", label: "Blue" },
  { value: "#6b3fa0", label: "Purple" },
  { value: "#d4739d", label: "Pink" },
];

export const EYE_COLORS: ColorOption[] = [
  { value: "#5c3317", label: "Brown" },
  { value: "#3b82f6", label: "Blue" },
  { value: "#22c55e", label: "Green" },
  { value: "#6b7280", label: "Gray" },
  { value: "#d97706", label: "Amber" },
  { value: "#8b5cf6", label: "Purple" },
];

export const OUTFIT_COLORS: ColorOption[] = [
  { value: "#53a8b6", label: "Teal" },
  { value: "#ef4444", label: "Red" },
  { value: "#3b82f6", label: "Blue" },
  { value: "#22c55e", label: "Green" },
  { value: "#8b5cf6", label: "Purple" },
  { value: "#f97316", label: "Orange" },
  { value: "#ec4899", label: "Pink" },
  { value: "#eab308", label: "Yellow" },
  { value: "#6b7280", label: "Gray" },
  { value: "#1a1a2e", label: "Black" },
];

// ─── Style Options ───────────────────────────────────────────

export const HAIR_STYLES: StyleOption<HairStyle>[] = [
  { value: "short", label: "Short" },
  { value: "long", label: "Long" },
  { value: "curly", label: "Curly" },
  { value: "spiky", label: "Spiky" },
  { value: "bob", label: "Bob" },
  { value: "ponytail", label: "Ponytail" },
];

export const EYE_STYLES: StyleOption<EyeStyle>[] = [
  { value: "round", label: "Round" },
  { value: "narrow", label: "Narrow" },
  { value: "wide", label: "Wide" },
  { value: "cat", label: "Cat" },
];

export const FACE_SHAPES: StyleOption<FaceShape>[] = [
  { value: "round", label: "Round" },
  { value: "oval", label: "Oval" },
  { value: "heart", label: "Heart" },
];

export const OUTFIT_STYLES: StyleOption<OutfitStyle>[] = [
  { value: "hoodie", label: "Hoodie" },
  { value: "tshirt", label: "T-Shirt" },
  { value: "dress", label: "Dress" },
  { value: "jacket", label: "Jacket" },
];

export const ACCESSORIES: StyleOption<Accessory>[] = [
  { value: "none", label: "None" },
  { value: "glasses", label: "Glasses" },
  { value: "round-glasses", label: "Round Glasses" },
  { value: "hat", label: "Hat" },
  { value: "bow", label: "Bow" },
  { value: "headband", label: "Headband" },
  { value: "sunglasses", label: "Sunglasses" },
];

// ─── Defaults & Factory ─────────────────────────────────────

export function createDefaultCharacter(): CharacterConfig {
  return {
    id: crypto.randomUUID(),
    name: "Bodhi",
    skinTone: "#fde8d0",
    hairColor: "#2c3e6b",
    hairStyle: "short",
    eyeColor: "#3b82f6",
    eyeStyle: "round",
    faceShape: "round",
    outfitColor: "#53a8b6",
    outfitStyle: "hoodie",
    accessory: "none",
  };
}

// ─── Persistence ─────────────────────────────────────────────

const CHARACTERS_KEY = "bodhi-characters";
const ACTIVE_KEY = "bodhi-active-character";
const ONBOARDED_KEY = "bodhi-onboarded";

export function loadCharacters(): CharacterConfig[] {
  try {
    const raw = localStorage.getItem(CHARACTERS_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    /* ignore */
  }
  return [];
}

export function saveCharacters(chars: CharacterConfig[]) {
  localStorage.setItem(CHARACTERS_KEY, JSON.stringify(chars));
}

export function getActiveCharacterId(): string | null {
  return localStorage.getItem(ACTIVE_KEY);
}

export function setActiveCharacterId(id: string) {
  localStorage.setItem(ACTIVE_KEY, id);
}

export function isOnboarded(): boolean {
  return localStorage.getItem(ONBOARDED_KEY) === "true";
}

export function setOnboarded() {
  localStorage.setItem(ONBOARDED_KEY, "true");
}

export function getActiveCharacter(): CharacterConfig {
  const chars = loadCharacters();
  const activeId = getActiveCharacterId();
  if (activeId) {
    const found = chars.find((c) => c.id === activeId);
    if (found) return found;
  }
  if (chars.length > 0) return chars[0];
  return createDefaultCharacter();
}
