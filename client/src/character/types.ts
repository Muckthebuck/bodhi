/** Character customization types, palettes, and persistence. */

export interface CharacterConfig {
  id: string;
  name: string;
  skinTone: string;
  hairColor: string;
  hairStyle: HairStyle;
  eyeColor: string;
  eyeStyle: EyeStyle;
  noseStyle: NoseStyle;
  mouthStyle: MouthStyle;
  blushStyle: BlushStyle;
  faceShape: FaceShape;
  outfitColor: string;
  outfitStyle: OutfitStyle;
  accessory: Accessory;
  accessoryColor: string;
}

export type HairStyle =
  | "short"
  | "long"
  | "curly"
  | "spiky"
  | "bob"
  | "ponytail"
  | "twintails"
  | "buns"
  | "messy"
  | "sideshave";
export type EyeStyle = "round" | "oval" | "wide" | "cat" | "dot" | "sparkle";
export type NoseStyle = "none" | "dot" | "triangle" | "round" | "button";
export type MouthStyle = "smile" | "cat" | "line" | "open" | "smirk";
export type BlushStyle = "circle" | "oval" | "none";
export type FaceShape = "round" | "oval" | "soft-square";
export type OutfitStyle = "hoodie" | "tshirt" | "dress" | "overalls" | "jacket";
export type Accessory =
  | "none"
  | "glasses"
  | "round-glasses"
  | "hat"
  | "bow"
  | "headband"
  | "sunglasses"
  | "bandaid";

export interface ColorOption {
  value: string;
  label: string;
}

export interface StyleOption<T> {
  value: T;
  label: string;
  icon?: string;
}

// ─── Color Palettes ──────────────────────────────────────────

export const SKIN_TONES: ColorOption[] = [
  { value: "#fde8d0", label: "Light" },
  { value: "#f5d0a9", label: "Fair" },
  { value: "#e8b88a", label: "Warm" },
  { value: "#d4a574", label: "Medium" },
  { value: "#c4956a", label: "Olive" },
  { value: "#a87553", label: "Tan" },
  { value: "#8d5524", label: "Brown" },
  { value: "#5c3d2e", label: "Dark" },
];

export const HAIR_COLORS: ColorOption[] = [
  { value: "#4a4458", label: "Charcoal" },
  { value: "#8b7b6b", label: "Cocoa" },
  { value: "#c4a882", label: "Caramel" },
  { value: "#e6b8a2", label: "Peach" },
  { value: "#f2d8a8", label: "Honey" },
  { value: "#f5ede0", label: "Cream" },
  { value: "#e8a8a8", label: "Coral" },
  { value: "#f2b8d4", label: "Bubblegum" },
  { value: "#a8cce8", label: "Sky Blue" },
  { value: "#c8b4e2", label: "Lavender" },
  { value: "#a2d4c4", label: "Seafoam" },
  { value: "#e6e2ee", label: "Pearl" },
];

export const EYE_COLORS: ColorOption[] = [
  { value: "#8b7260", label: "Cocoa" },
  { value: "#8bb8e0", label: "Baby Blue" },
  { value: "#88c4a0", label: "Sage" },
  { value: "#a8a8ba", label: "Silver" },
  { value: "#d4b478", label: "Honey" },
  { value: "#b8a2d8", label: "Lilac" },
  { value: "#525264", label: "Charcoal" },
];

export const OUTFIT_COLORS: ColorOption[] = [
  { value: "#8ac4cc", label: "Soft Teal" },
  { value: "#e8a8a8", label: "Rose" },
  { value: "#a2bee8", label: "Powder Blue" },
  { value: "#a2d8b2", label: "Mint" },
  { value: "#c2a8e2", label: "Wisteria" },
  { value: "#f0c4a2", label: "Peach" },
  { value: "#f0b4c8", label: "Blush" },
  { value: "#f0dea2", label: "Buttercream" },
  { value: "#f5ede0", label: "Ivory" },
  { value: "#b2b2bc", label: "Dove" },
  { value: "#5a5a6a", label: "Charcoal" },
];

export const ACCESSORY_COLORS: ColorOption[] = [
  { value: "#4a4458", label: "Charcoal" },
  { value: "#8b7260", label: "Cocoa" },
  { value: "#c2a8e2", label: "Wisteria" },
  { value: "#e8a8a8", label: "Rose" },
  { value: "#a8cce8", label: "Sky Blue" },
  { value: "#a2d8b2", label: "Mint" },
  { value: "#f0c4a2", label: "Peach" },
  { value: "#f0dea2", label: "Buttercream" },
  { value: "#f5ede0", label: "Ivory" },
  { value: "#ef4444", label: "Cherry" },
];

// ─── Style Options ───────────────────────────────────────────

export const HAIR_STYLES: StyleOption<HairStyle>[] = [
  { value: "short", label: "Short" },
  { value: "long", label: "Long" },
  { value: "curly", label: "Curly" },
  { value: "spiky", label: "Spiky" },
  { value: "bob", label: "Bob" },
  { value: "ponytail", label: "Ponytail" },
  { value: "twintails", label: "Twintails" },
  { value: "buns", label: "Buns" },
  { value: "messy", label: "Messy" },
  { value: "sideshave", label: "Side Shave" },
];

export const EYE_STYLES: StyleOption<EyeStyle>[] = [
  { value: "round", label: "Round" },
  { value: "oval", label: "Oval" },
  { value: "wide", label: "Wide" },
  { value: "cat", label: "Cat" },
  { value: "dot", label: "Dot" },
  { value: "sparkle", label: "Sparkle" },
];

export const NOSE_STYLES: StyleOption<NoseStyle>[] = [
  { value: "none", label: "None" },
  { value: "dot", label: "Dot" },
  { value: "triangle", label: "Triangle" },
  { value: "round", label: "Round" },
  { value: "button", label: "Button" },
];

export const MOUTH_STYLES: StyleOption<MouthStyle>[] = [
  { value: "smile", label: "Smile" },
  { value: "cat", label: "Cat" },
  { value: "line", label: "Line" },
  { value: "open", label: "Open" },
  { value: "smirk", label: "Smirk" },
];

export const BLUSH_STYLES: StyleOption<BlushStyle>[] = [
  { value: "circle", label: "Circle" },
  { value: "oval", label: "Oval" },
  { value: "none", label: "None" },
];

export const FACE_SHAPES: StyleOption<FaceShape>[] = [
  { value: "round", label: "Round" },
  { value: "oval", label: "Oval" },
  { value: "soft-square", label: "Soft Square" },
];

export const OUTFIT_STYLES: StyleOption<OutfitStyle>[] = [
  { value: "hoodie", label: "Hoodie" },
  { value: "tshirt", label: "T-Shirt" },
  { value: "dress", label: "Dress" },
  { value: "overalls", label: "Overalls" },
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
  { value: "bandaid", label: "Band-Aid" },
];

// ─── Defaults & Factory ─────────────────────────────────────

export function createDefaultCharacter(): CharacterConfig {
  return {
    id: crypto.randomUUID(),
    name: "Bodhi",
    skinTone: "#fde8d0",
    hairColor: "#a8cce8",
    hairStyle: "short",
    eyeColor: "#8bb8e0",
    eyeStyle: "round",
    noseStyle: "dot",
    mouthStyle: "smile",
    blushStyle: "circle",
    faceShape: "round",
    outfitColor: "#8ac4cc",
    outfitStyle: "hoodie",
    accessory: "none",
    accessoryColor: "#4a4458",
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
