import { describe, it, expect, beforeEach } from "vitest";
import {
  createDefaultCharacter,
  loadCharacters,
  saveCharacters,
  isOnboarded,
  setOnboarded,
} from "../character/types";

beforeEach(() => {
  localStorage.clear();
});

describe("createDefaultCharacter", () => {
  it("returns a character with all required fields", () => {
    const char = createDefaultCharacter();
    expect(char.id).toBeTruthy();
    expect(char.name).toBeTruthy();
    expect(char.skinTone).toBeTruthy();
    expect(char.hairStyle).toBeTruthy();
    expect(char.eyeStyle).toBeTruthy();
    expect(char.outfitStyle).toBeTruthy();
  });

  it("generates unique ids", () => {
    const a = createDefaultCharacter();
    const b = createDefaultCharacter();
    expect(a.id).not.toBe(b.id);
  });
});

describe("saveCharacters / loadCharacters roundtrip", () => {
  it("persists and retrieves characters", () => {
    const chars = [createDefaultCharacter(), createDefaultCharacter()];
    chars[1].name = "Buddy";
    saveCharacters(chars);
    const loaded = loadCharacters();
    expect(loaded).toHaveLength(2);
    expect(loaded[1].name).toBe("Buddy");
  });

  it("returns empty array when no data", () => {
    expect(loadCharacters()).toEqual([]);
  });
});

describe("onboarding state", () => {
  it("defaults to not onboarded", () => {
    expect(isOnboarded()).toBe(false);
  });

  it("persists onboarded state", () => {
    setOnboarded();
    expect(isOnboarded()).toBe(true);
  });
});
