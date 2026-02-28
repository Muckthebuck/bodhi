/** Dynamic chibi character — renders inline SVG from CharacterConfig + animation state. */

import { useEffect, useRef, useState, useMemo, memo } from "react";
import type { CharacterConfig } from "./types";
import type { AnimationAction, EmotionState } from "../types";
import { ANIMATION_POSES, ANIMATION_FPS, type AnimState, type EyeVariant, type MouthVariant, type ArmVariant, type LegVariant, type ExtraType } from "./poses";
import {
  Shadow, Legs, Body, Arms, Neck, HairBack, Face, HairFront,
  Eyes, Mouth, Blush, Nose, AccessoryPart, Extras,
} from "./svg-parts";

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
  // ── Refs for direct DOM manipulation (no React re-renders for transforms) ──
  const headRef = useRef<SVGGElement>(null);
  const hairBackRef = useRef<SVGGElement>(null);
  const bodyRef = useRef<SVGGElement>(null);
  const rafRef = useRef(0);

  // ── Variant state — only triggers re-render when expressions/limbs change ──
  const [variants, setVariants] = useState<{
    eyes: EyeVariant; mouth: MouthVariant; arms: ArmVariant; legs: LegVariant; extras: ExtraType[];
  }>({ eyes: "normal", mouth: "smile", arms: "default", legs: "default", extras: [] });

  const state = resolveState(action, emotion);
  const frames = ANIMATION_POSES[state];
  const interval = 1000 / ANIMATION_FPS[state];

  // ── Composite layers — memoized, only rebuild when config changes ──
  const staticHairBack = useMemo(
    () => <HairBack config={config} />,
    [config.hairColor, config.hairStyle],
  );

  const staticHead = useMemo(
    () => (
      <>
        <Face config={config} />
        <HairFront config={config} />
        <Nose config={config} />
        <Blush config={config} />
        <AccessoryPart config={config} />
      </>
    ),
    [config.skinTone, config.faceShape, config.hairColor, config.hairStyle,
     config.noseStyle, config.blushStyle, config.accessory, config.accessoryColor, config.outfitColor],
  );

  const staticBody = useMemo(
    () => <Body config={config} tilt={0} />,
    [config.outfitColor, config.outfitStyle],
  );

  // ── Animation loop — lerp-based 60fps interpolation, no CSS transitions ──
  useEffect(() => {
    let frame = 0;
    let lastTick = 0;
    let prevKey = "";

    // Current interpolated values
    const p0 = frames[0];
    let curHeadDy = p0.headDy;
    let curBodyTilt = p0.bodyTilt;
    let tgtHeadDy = curHeadDy;
    let tgtBodyTilt = curBodyTilt;

    // Lerp factor — 0.15 ≈ 10 frames to 80%, feels snappy yet smooth
    const LERP = 0.15;
    const SNAP = 0.05;

    // Apply initial pose immediately (no FOUC)
    headRef.current?.setAttribute("transform", `translate(0, ${curHeadDy})`);
    hairBackRef.current?.setAttribute("transform", `translate(0, ${curHeadDy})`);
    bodyRef.current?.setAttribute("transform", `rotate(${curBodyTilt}, 64, 116)`);

    const tick = (time: number) => {
      if (!lastTick) lastTick = time;

      // Advance pose frame at the defined FPS
      if (time - lastTick >= interval) {
        lastTick = time;
        frame = (frame + 1) % frames.length;
        const pose = frames[frame];
        tgtHeadDy = pose.headDy;
        tgtBodyTilt = pose.bodyTilt;

        // Only trigger React re-render when variants actually change
        const key = `${pose.eyes}|${pose.mouth}|${pose.arms}|${pose.legs}|${pose.extras}`;
        if (key !== prevKey) {
          prevKey = key;
          setVariants({
            eyes: pose.eyes, mouth: pose.mouth,
            arms: pose.arms, legs: pose.legs, extras: pose.extras,
          });
        }
      }

      // Lerp every frame (60fps) for buttery-smooth motion
      curHeadDy += (tgtHeadDy - curHeadDy) * LERP;
      curBodyTilt += (tgtBodyTilt - curBodyTilt) * LERP;

      // Snap to target when very close to avoid sub-pixel jitter
      if (Math.abs(tgtHeadDy - curHeadDy) < SNAP) curHeadDy = tgtHeadDy;
      if (Math.abs(tgtBodyTilt - curBodyTilt) < SNAP) curBodyTilt = tgtBodyTilt;

      // Native SVG transform attribute — fastest path for SVG rendering
      const headT = `translate(0, ${curHeadDy})`;
      headRef.current?.setAttribute("transform", headT);
      hairBackRef.current?.setAttribute("transform", headT);
      bodyRef.current?.setAttribute("transform", `rotate(${curBodyTilt}, 64, 116)`);

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [state, frames.length, interval]);

  return (
    <svg
      viewBox="0 -16 128 176"
      width={size}
      height={size * 1.375}
      shapeRendering="auto"
      style={{ userSelect: "none", pointerEvents: "none" }}
    >
      <Shadow />
      {/* Composite layer: hair back (behind body, bobs with head) */}
      <g ref={hairBackRef}>
        {staticHairBack}
      </g>
      {/* Composite layer: body (legs, torso, arms tilt together) */}
      <g ref={bodyRef}>
        <Legs config={config} variant={variants.legs} />
        {staticBody}
        <Arms config={config} variant={variants.arms} />
      </g>
      {/* Neck bridge */}
      <Neck config={config} />
      {/* Composite layer: head (static face + dynamic eyes/mouth/extras) */}
      <g ref={headRef}>
        {staticHead}
        <Eyes config={config} variant={variants.eyes} />
        <Mouth variant={variants.mouth} config={config} />
        <Extras items={variants.extras} />
      </g>
    </svg>
  );
}

/** Non-animated character for preview thumbnails — memoized for performance. */
export const StaticCharacter = memo(
  function StaticCharacterInner({
    config,
    size = 64,
  }: {
    config: CharacterConfig;
    size?: number;
  }) {
    return (
      <svg
        viewBox="0 -16 128 176"
        width={size}
        height={size * 1.375}
        shapeRendering="geometricPrecision"
        style={{ userSelect: "none", pointerEvents: "none" }}
      >
        <Shadow />
        <HairBack config={config} />
        <Legs config={config} variant="default" />
        <Body config={config} tilt={0} />
        <Arms config={config} variant="default" />
        <Neck config={config} />
        <g>
          <Face config={config} />
          <HairFront config={config} />
          <Eyes config={config} variant="normal" />
          <Nose config={config} />
          <Mouth variant="smile" config={config} />
          <Blush config={config} />
          <AccessoryPart config={config} />
        </g>
      </svg>
    );
  },
  (prev, next) => {
    if (prev.size !== next.size) return false;
    const a = prev.config;
    const b = next.config;
    return (
      a.skinTone === b.skinTone &&
      a.hairColor === b.hairColor &&
      a.hairStyle === b.hairStyle &&
      a.eyeColor === b.eyeColor &&
      a.eyeStyle === b.eyeStyle &&
      a.noseStyle === b.noseStyle &&
      a.mouthStyle === b.mouthStyle &&
      a.blushStyle === b.blushStyle &&
      a.faceShape === b.faceShape &&
      a.outfitColor === b.outfitColor &&
      a.outfitStyle === b.outfitStyle &&
      a.accessory === b.accessory &&
      a.accessoryColor === b.accessoryColor
    );
  },
);

// ─── Focused preview for option cards ────────────────────────
// Only renders the relevant parts, zoomed into the changed area.

export type PreviewFocus = "face" | "hair" | "eyes" | "nose" | "mouth" | "blush" | "outfit" | "accessory";

// viewBox regions for each focus area   [x, y, w, h]
const FOCUS_VIEWBOX: Record<PreviewFocus, string> = {
  face:      "14 -8 100 100",   // head + hair outline
  hair:      "4 -16 120 108",   // full hair coverage
  eyes:      "34 46 60 28",     // tight around both eyes
  nose:      "44 56 40 28",     // nose + mouth area for context
  mouth:     "44 60 40 28",     // mouth + chin area
  blush:     "30 48 68 36",     // cheeks + eyes for context
  outfit:    "30 80 68 70",     // torso + legs
  accessory: "10 -8 108 96",    // full head for hats/bows/glasses
};

export const PartPreview = memo(
  function PartPreviewInner({
    config,
    focus,
    size = 72,
  }: {
    config: CharacterConfig;
    focus: PreviewFocus;
    size?: number;
  }) {
    const vb = FOCUS_VIEWBOX[focus];

    // Only render parts relevant to the focus area
    const needsBody = focus === "outfit";
    const needsHair = focus === "face" || focus === "hair" || focus === "accessory";
    const needsFace = focus !== "outfit";
    const needsEyes = focus !== "outfit" && focus !== "nose" && focus !== "mouth";
    const needsNose = focus === "face" || focus === "nose" || focus === "blush";
    const needsMouth = focus === "face" || focus === "mouth" || focus === "nose" || focus === "blush";
    const needsBlush = focus === "face" || focus === "blush";
    const needsAccessory = focus === "accessory";
    const needsLegs = focus === "outfit";

    return (
      <svg
        viewBox={vb}
        width={size}
        height={size}
        shapeRendering="geometricPrecision"
        style={{ userSelect: "none", pointerEvents: "none" }}
      >
        {needsHair && <HairBack config={config} />}
        {needsLegs && <Legs config={config} variant="default" />}
        {needsBody && <Body config={config} tilt={0} />}
        {needsBody && <Arms config={config} variant="default" />}
        {needsFace && <Face config={config} />}
        {needsHair && <HairFront config={config} />}
        {needsEyes && <Eyes config={config} variant="normal" />}
        {needsNose && <Nose config={config} />}
        {needsMouth && <Mouth variant="smile" config={config} />}
        {needsBlush && <Blush config={config} />}
        {needsAccessory && <AccessoryPart config={config} />}
      </svg>
    );
  },
  (prev, next) => {
    if (prev.size !== next.size || prev.focus !== next.focus) return false;
    const a = prev.config;
    const b = next.config;
    return (
      a.skinTone === b.skinTone &&
      a.hairColor === b.hairColor &&
      a.hairStyle === b.hairStyle &&
      a.eyeColor === b.eyeColor &&
      a.eyeStyle === b.eyeStyle &&
      a.noseStyle === b.noseStyle &&
      a.mouthStyle === b.mouthStyle &&
      a.blushStyle === b.blushStyle &&
      a.faceShape === b.faceShape &&
      a.outfitColor === b.outfitColor &&
      a.outfitStyle === b.outfitStyle &&
      a.accessory === b.accessory &&
      a.accessoryColor === b.accessoryColor
    );
  },
);
