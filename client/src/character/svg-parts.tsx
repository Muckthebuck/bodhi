/** SVG part renderers for Animal Crossing/Loftia-style chibi character. */

import React from "react";
import type { CharacterConfig, HairStyle } from "./types";
import type { EyeVariant, MouthVariant, ArmVariant, LegVariant, ExtraType } from "./poses";

// ─── Helpers ─────────────────────────────────────────────────

export function darken(hex: string, amount = 0.2): string {
  const n = parseInt(hex.slice(1), 16);
  const r = Math.max(0, Math.round(((n >> 16) & 0xff) * (1 - amount)));
  const g = Math.max(0, Math.round(((n >> 8) & 0xff) * (1 - amount)));
  const b = Math.max(0, Math.round((n & 0xff) * (1 - amount)));
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

const SHOE_COLOR = "#5c4a42";
const PUPIL_COLOR = "#2d2d3d";
const BLUSH_COLOR = "#ff9999";
const WHITE = "#ffffff";

// ─── Shadow ──────────────────────────────────────────────────

export function Shadow(): React.JSX.Element {
  return <ellipse cx={64} cy={152} rx={24} ry={4} fill="#000" opacity={0.12} />;
}

// ─── Legs (chunkier, with big round shoes) ───────────────────

export function Legs({ config, variant }: { config: CharacterConfig; variant: LegVariant }): React.JSX.Element {
  const legColor = darken(config.outfitColor, 0.1);
  const lx = 54, rx = 74;  // leg centers
  const ly = 128;           // leg vertical center
  const lrx = 5, lry = 8;  // leg ellipse radii — slim
  const sy = 138;           // shoe y

  const shoe = (x: number) => (
    <ellipse cx={x} cy={sy} rx={7} ry={3.5} fill={SHOE_COLOR} />
  );

  if (variant === "walk0") {
    return (
      <g>
        <ellipse cx={lx - 3} cy={ly} rx={lrx} ry={lry} fill={legColor} transform={`rotate(-10,${lx - 3},${ly})`} />
        {shoe(lx - 5)}
        <ellipse cx={rx + 2} cy={ly} rx={lrx} ry={lry} fill={legColor} transform={`rotate(6,${rx + 2},${ly})`} />
        {shoe(rx + 4)}
      </g>
    );
  }

  if (variant === "walk1") {
    return (
      <g>
        <ellipse cx={lx + 2} cy={ly} rx={lrx} ry={lry} fill={legColor} transform={`rotate(6,${lx + 2},${ly})`} />
        {shoe(lx + 4)}
        <ellipse cx={rx - 3} cy={ly} rx={lrx} ry={lry} fill={legColor} transform={`rotate(-10,${rx - 3},${ly})`} />
        {shoe(rx - 5)}
      </g>
    );
  }

  return (
    <g>
      <ellipse cx={lx} cy={ly} rx={lrx} ry={lry} fill={legColor} />
      {shoe(lx)}
      <ellipse cx={rx} cy={ly} rx={lrx} ry={lry} fill={legColor} />
      {shoe(rx)}
    </g>
  );
}

// ─── Body (rounded capsule shape with outfit details) ────────

export function Body({ config, tilt }: { config: CharacterConfig; tilt: number }): React.JSX.Element {
  const c = config.outfitColor;
  const d = darken(c, 0.15);
  const wrap = (children: React.JSX.Element) =>
    tilt !== 0 ? <g transform={`rotate(${tilt}, 64, 106)`}>{children}</g> : <g>{children}</g>;

  // Base body: rounded capsule y=88 to y=122 — compact torso
  const basePath = "M50 92 Q46 88 46 96 L46 116 Q46 122 50 122 L78 122 Q82 122 82 116 L82 96 Q82 88 78 92 Z";

  switch (config.outfitStyle) {
    case "tshirt":
      return wrap(
        <>
          <path d={basePath} fill={c} />
          <path d="M54 92 Q64 96 74 92" stroke={d} strokeWidth={2} fill="none" strokeLinecap="round" />
        </>
      );
    case "dress":
      return wrap(
        <>
          <path d="M50 92 Q46 88 46 96 L42 120 Q42 128 50 128 L78 128 Q86 128 86 120 L82 96 Q82 88 78 92 Z" fill={c} />
          <path d="M46 110 Q64 114 82 110" stroke={d} strokeWidth={1.5} fill="none" opacity={0.3} strokeLinecap="round" />
          <path d="M54 92 Q64 96 74 92" stroke={d} strokeWidth={1.5} fill="none" opacity={0.4} strokeLinecap="round" />
        </>
      );
    case "overalls":
      return wrap(
        <>
          <path d={basePath} fill={c} />
          <rect x={55} y={92} width={4} height={18} rx={2} fill={d} />
          <rect x={69} y={92} width={4} height={18} rx={2} fill={d} />
          <circle cx={57} cy={98} r={1.5} fill={d} opacity={0.7} />
          <circle cx={71} cy={98} r={1.5} fill={d} opacity={0.7} />
        </>
      );
    case "jacket":
      return wrap(
        <>
          <path d={basePath} fill={c} />
          <line x1={64} y1={92} x2={64} y2={122} stroke={d} strokeWidth={2} strokeLinecap="round" />
          <path d="M60 92 L64 98 L68 92" stroke={d} strokeWidth={1.5} fill="none" strokeLinecap="round" />
        </>
      );
    default: // hoodie
      return wrap(
        <>
          <path d={basePath} fill={c} />
          <path d="M52 92 Q64 98 76 92" stroke={d} strokeWidth={2} fill="none" opacity={0.5} strokeLinecap="round" />
          <path d="M54 112 Q64 116 74 112" stroke={d} strokeWidth={1.5} fill="none" opacity={0.3} strokeLinecap="round" />
        </>
      );
  }
}

// ─── Arms (thicker, rounder, bigger hands) ───────────────────

export function Arms({ config, variant }: { config: CharacterConfig; variant: ArmVariant }): React.JSX.Element {
  const ac = config.outfitColor;
  const sc = config.skinTone;
  const SW = 8;   // stroke width
  const HR = 5;    // hand radius

  const leftDown = (
    <>
      <path d="M46 100 Q36 108 34 118" stroke={ac} strokeWidth={SW} fill="none" strokeLinecap="round" />
      <circle cx={34} cy={120} r={HR} fill={sc} />
    </>
  );
  const rightDown = (
    <>
      <path d="M82 100 Q92 108 94 118" stroke={ac} strokeWidth={SW} fill="none" strokeLinecap="round" />
      <circle cx={94} cy={120} r={HR} fill={sc} />
    </>
  );

  const waveArm = (angle: number) => (
    <g transform={`rotate(${angle}, 82, 100)`}>
      <path d="M82 100 Q90 90 96 80" stroke={ac} strokeWidth={SW} fill="none" strokeLinecap="round" />
      <circle cx={96} cy={78} r={HR} fill={sc} />
    </g>
  );

  switch (variant) {
    case "wave0": return <g>{leftDown}{waveArm(-15)}</g>;
    case "wave1": return <g>{leftDown}{waveArm(-30)}</g>;
    case "wave2": return <g>{leftDown}{waveArm(-45)}</g>;
    case "wave3": return <g>{leftDown}{waveArm(-30)}</g>;
    case "think":
      return (
        <g>
          <path d="M46 100 Q38 94 42 80" stroke={ac} strokeWidth={SW} fill="none" strokeLinecap="round" />
          <circle cx={42} cy={78} r={HR} fill={sc} />
          {rightDown}
        </g>
      );
    case "hug":
      return (
        <g>
          <path d="M46 100 Q40 104 46 116" stroke={ac} strokeWidth={SW} fill="none" strokeLinecap="round" />
          <circle cx={48} cy={118} r={HR} fill={sc} />
          <path d="M82 100 Q88 104 82 116" stroke={ac} strokeWidth={SW} fill="none" strokeLinecap="round" />
          <circle cx={80} cy={118} r={HR} fill={sc} />
        </g>
      );
    default:
      return <g>{leftDown}{rightDown}</g>;
  }
}

// ─── Neck (skin bridge between head & body — hides gap during head bob) ──

export function Neck({ config }: { config: CharacterConfig }): React.JSX.Element {
  return <ellipse cx={64} cy={88} rx={11} ry={5} fill={config.skinTone} />;
}

// ─── Hair Back ───────────────────────────────────────────────

const HAIR_BACK_PATHS: Record<HairStyle, string> = {
  short: "M18 52 Q20 2 64 -2 Q108 2 110 52 Q112 68 104 76 Q88 64 64 62 Q40 64 24 76 Q16 68 18 52 Z",
  long: "M16 50 Q18 -2 64 -6 Q110 -2 112 50 L114 104 Q112 116 102 120 Q86 110 64 108 Q42 110 26 120 Q16 116 14 104 Z",
  curly: "M16 48 Q18 -2 44 -4 Q54 -8 64 -6 Q74 -8 84 -4 Q110 -2 112 48 Q116 62 112 78 Q110 86 104 78 Q100 88 94 80 Q88 90 80 78 Q72 88 64 80 Q56 88 48 78 Q42 86 38 78 Q16 62 16 48 Z",
  spiky: "M20 52 Q22 30 30 14 Q36 4 44 -4 Q50 10 50 20 Q52 4 58 -8 Q64 4 64 16 Q66 4 70 -8 Q76 10 78 20 Q78 4 84 -4 Q92 4 98 14 Q106 30 108 52 Q104 36 90 28 Q64 18 38 28 Q24 36 20 52 Z",
  bob: "M18 52 Q20 2 64 -2 Q108 2 110 52 Q112 76 108 86 Q100 92 88 92 Q64 90 40 92 Q28 92 20 86 Q16 76 18 52 Z",
  ponytail: "M18 52 Q20 2 64 -2 Q108 2 110 52 Q112 66 104 72 L112 100 Q110 106 104 100 L102 72 Q88 62 64 60 Q40 62 26 72 Q16 66 18 52 Z",
  twintails: "M18 52 Q20 2 64 -2 Q108 2 110 52 L118 92 Q116 98 112 92 L110 66 Q100 60 88 64 L40 64 Q28 60 18 66 L16 92 Q12 98 10 92 Z",
  buns: "M18 52 Q20 2 64 -2 Q108 2 110 52 Q112 66 104 72 Q88 62 64 60 Q40 62 24 72 Q16 66 18 52 Z",
  messy: "M14 48 Q16 -2 44 -4 Q54 -6 64 -4 Q74 -6 84 -4 Q112 -2 114 48 Q118 58 112 68 Q110 62 108 70 Q100 62 98 72 Q88 64 86 74 Q76 66 72 76 Q64 68 58 78 Q48 70 44 80 Q34 72 30 82 Q12 66 14 48 Z",
  sideshave: "M18 52 Q20 2 48 -2 Q56 -4 64 -2 Q108 2 110 52 Q112 68 104 76 Q88 64 64 62 Q40 64 24 76 Q16 68 18 52 Z"
};

export function HairBack({ config }: { config: CharacterConfig }): React.JSX.Element | null {
  const path = HAIR_BACK_PATHS[config.hairStyle];
  if (!path) return null;
  
  let extras: React.JSX.Element | null = null;
  
  // Add special features for certain styles
  if (config.hairStyle === "buns") {
    extras = (
      <>
        <circle cx={28} cy={10} r={13} fill={config.hairColor} />
        <circle cx={100} cy={10} r={13} fill={config.hairColor} />
      </>
    );
  } else if (config.hairStyle === "twintails") {
    extras = (
      <>
        <path d="M10 92 Q8 106 12 114 Q16 106 14 98" fill={config.hairColor} />
        <path d="M118 92 Q120 106 116 114 Q112 106 114 98" fill={config.hairColor} />
      </>
    );
  }
  
  return (
    <g>
      <path d={path} fill={config.hairColor} />
      {extras}
    </g>
  );
}

// ─── Face ────────────────────────────────────────────────────

export function Face({ config }: { config: CharacterConfig }): React.JSX.Element {
  const cx = 64;
  const cy = 50;
  
  switch (config.faceShape) {
    case "oval":
      // Wider-than-tall oval — AC characters have horizontal egg shapes
      return <ellipse cx={cx} cy={cy} rx={40} ry={36} fill={config.skinTone} />;
      
    case "soft-square":
      // Cute squircle — very rounded corners, slightly wider than tall
      return (
        <rect
          x={cx - 38}
          y={cy - 34}
          width={76}
          height={68}
          rx={22}
          ry={22}
          fill={config.skinTone}
        />
      );
      
    default: // round
      return <circle cx={cx} cy={cy} r={40} fill={config.skinTone} />;
  }
}

// ─── Hair Front ──────────────────────────────────────────────

const HAIR_FRONT_PATHS: Record<HairStyle, string> = {
  short: "M18 52 Q20 4 64 0 Q108 4 110 52 Q104 40 90 34 Q64 24 38 34 Q24 40 18 52 Z",
  long: "M16 50 Q18 0 64 -4 Q110 0 112 50 Q106 36 90 30 Q64 20 38 30 Q22 36 16 50 Z",
  curly: "M16 50 Q18 0 50 -4 Q58 -6 64 -4 Q70 -6 78 -4 Q110 0 112 50 Q106 36 88 30 Q76 26 64 28 Q52 26 40 30 Q22 36 16 50 Z",
  spiky: "M20 52 Q22 30 30 14 Q36 4 44 -4 Q50 10 50 20 Q52 4 58 -8 Q64 4 64 16 Q66 4 70 -8 Q76 10 78 20 Q78 4 84 -4 Q92 4 98 14 Q106 30 108 52 Q104 38 90 32 Q64 22 38 32 Q24 38 20 52 Z",
  bob: "M18 52 Q20 2 64 -2 Q108 2 110 52 Q106 38 90 32 Q64 22 38 32 Q22 38 18 52 Z",
  ponytail: "M18 52 Q20 2 64 -2 Q108 2 110 52 Q104 38 86 32 Q64 22 42 32 Q24 38 18 52 Z",
  twintails: "M18 52 Q20 2 64 -2 Q108 2 110 52 Q104 38 86 32 Q64 22 42 32 Q24 38 18 52 Z",
  buns: "M18 52 Q20 2 64 -2 Q108 2 110 52 Q104 38 86 32 Q64 22 42 32 Q24 38 18 52 Z",
  messy: "M14 50 Q16 0 48 -2 Q56 -4 64 -2 Q72 -4 80 -2 Q112 0 114 50 Q110 36 96 32 Q86 26 78 34 Q72 24 64 30 Q56 24 50 34 Q40 28 34 34 Q22 38 14 50 Z",
  sideshave: "M46 52 Q48 4 64 0 Q108 4 110 52 Q104 40 90 34 Q64 24 50 36 Q46 42 46 52 Z"
};

export function HairFront({ config }: { config: CharacterConfig }): React.JSX.Element {
  const path = HAIR_FRONT_PATHS[config.hairStyle];
  
  return (
    <g>
      <path d={path} fill={config.hairColor} />
    </g>
  );
}

// ─── Eyes (AC-style: simple solid shapes with tiny highlight) ─

export function Eyes({ config, variant }: { config: CharacterConfig; variant: EyeVariant }): React.JSX.Element {
  const lx = 52;  // left eye x (closer together than before)
  const rx = 76;  // right eye x
  const ey = 62;  // eye y (lower on face — 65% down from head top)
  const c = config.eyeColor;

  // Happy: upward arcs (^_^)
  if (variant === "happy") {
    return (
      <g>
        <path d={`M${lx - 6} ${ey + 2} Q${lx} ${ey - 5} ${lx + 6} ${ey + 2}`}
              stroke={c} strokeWidth={3} fill="none" strokeLinecap="round" />
        <path d={`M${rx - 6} ${ey + 2} Q${rx} ${ey - 5} ${rx + 6} ${ey + 2}`}
              stroke={c} strokeWidth={3} fill="none" strokeLinecap="round" />
      </g>
    );
  }

  // Closed: gentle downward arcs
  if (variant === "closed") {
    return (
      <g>
        <path d={`M${lx - 5} ${ey - 1} Q${lx} ${ey + 3} ${lx + 5} ${ey - 1}`}
              stroke={c} strokeWidth={2.5} fill="none" strokeLinecap="round" />
        <path d={`M${rx - 5} ${ey - 1} Q${rx} ${ey + 3} ${rx + 5} ${ey - 1}`}
              stroke={c} strokeWidth={2.5} fill="none" strokeLinecap="round" />
      </g>
    );
  }

  // Variant offsets
  let dy = 0;
  if (variant === "sad") dy = 2;
  if (variant === "lookUp") dy = -2;

  // Render a single eye based on eyeStyle — solid fill, tiny white highlight
  const renderEye = (x: number) => {
    const y = ey + dy;
    switch (config.eyeStyle) {
      case "oval":
        return (
          <g>
            <ellipse cx={x} cy={y} rx={3.5} ry={5.5} fill={c} />
            <circle cx={x + 1} cy={y - 2} r={1.5} fill={WHITE} opacity={0.9} />
          </g>
        );
      case "wide":
        return (
          <g>
            <ellipse cx={x} cy={y} rx={5.5} ry={6} fill={c} />
            <circle cx={x + 2} cy={y - 2} r={2} fill={WHITE} opacity={0.9} />
          </g>
        );
      case "cat":
        return (
          <g>
            <path d={`M${x - 5} ${y} Q${x} ${y - 6} ${x + 5} ${y} Q${x} ${y + 4} ${x - 5} ${y}`} fill={c} />
            <circle cx={x + 1.5} cy={y - 1.5} r={1.2} fill={WHITE} opacity={0.9} />
          </g>
        );
      case "dot":
        return <circle cx={x} cy={y} r={3} fill={c} />;
      case "sparkle":
        return (
          <g>
            <circle cx={x} cy={y} r={5.5} fill={c} />
            <circle cx={x + 2} cy={y - 2} r={2} fill={WHITE} opacity={0.95} />
            <circle cx={x - 1.5} cy={y + 2} r={1} fill={WHITE} opacity={0.4} />
          </g>
        );
      default: // "round"
        return (
          <g>
            <circle cx={x} cy={y} r={4.5} fill={c} />
            <circle cx={x + 1.5} cy={y - 1.5} r={1.5} fill={WHITE} opacity={0.9} />
          </g>
        );
    }
  };

  // Eyebrows for angry/sad expressions
  let brows: React.JSX.Element | null = null;
  const bc = darken(config.hairColor, 0.3);
  if (variant === "angry") {
    brows = (
      <g>
        <path d={`M${lx - 6} ${ey - 10} L${lx + 5} ${ey - 6}`} stroke={bc} strokeWidth={2.5} strokeLinecap="round" />
        <path d={`M${rx + 6} ${ey - 10} L${rx - 5} ${ey - 6}`} stroke={bc} strokeWidth={2.5} strokeLinecap="round" />
      </g>
    );
  } else if (variant === "sad") {
    brows = (
      <g>
        <path d={`M${lx - 5} ${ey - 8} L${lx + 6} ${ey - 10}`} stroke={bc} strokeWidth={2} strokeLinecap="round" />
        <path d={`M${rx + 5} ${ey - 8} L${rx - 6} ${ey - 10}`} stroke={bc} strokeWidth={2} strokeLinecap="round" />
      </g>
    );
  }

  return (
    <g>
      {brows}
      {renderEye(lx)}
      {renderEye(rx)}
    </g>
  );
}

// ─── Mouth (positioned lower, at y=76) ──────────────────────

export function Mouth({ variant, config: _config }: { variant: MouthVariant; config?: CharacterConfig }): React.JSX.Element {
  const mx = 64;
  const my = 76;
  
  switch (variant) {
    case "bigSmile":
      return (
        <path d={`M${mx - 8} ${my - 2} Q${mx} ${my + 7} ${mx + 8} ${my - 2}`}
              stroke={PUPIL_COLOR} strokeWidth={2.5} fill="none" strokeLinecap="round" />
      );
    case "neutral":
      return <line x1={mx - 5} y1={my} x2={mx + 5} y2={my}
                   stroke={PUPIL_COLOR} strokeWidth={2} strokeLinecap="round" />;
    case "sad":
      return (
        <path d={`M${mx - 6} ${my + 2} Q${mx} ${my - 3} ${mx + 6} ${my + 2}`}
              stroke={PUPIL_COLOR} strokeWidth={2} fill="none" strokeLinecap="round" />
      );
    case "open":
      return (
        <g>
          <ellipse cx={mx} cy={my} rx={5} ry={4} fill={PUPIL_COLOR} />
          <ellipse cx={mx} cy={my - 1} rx={3} ry={2} fill="#ff6b6b" opacity={0.5} />
        </g>
      );
    case "talk1":
      return <ellipse cx={mx} cy={my} rx={4} ry={2.5} fill={PUPIL_COLOR} />;
    case "talk2":
      return (
        <g>
          <ellipse cx={mx} cy={my} rx={6} ry={3.5} fill={PUPIL_COLOR} />
          <ellipse cx={mx} cy={my - 1} rx={4} ry={1.5} fill="#ff6b6b" opacity={0.4} />
        </g>
      );
    case "smallO":
      return <circle cx={mx} cy={my} r={2.5} fill={PUPIL_COLOR} />;
    case "cat":
      return (
        <path d={`M${mx - 6} ${my - 1} L${mx} ${my + 2} L${mx + 6} ${my - 1}`}
              stroke={PUPIL_COLOR} strokeWidth={2} fill="none" strokeLinecap="round" />
      );
    default: // smile
      return (
        <path d={`M${mx - 6} ${my - 1} Q${mx} ${my + 4} ${mx + 6} ${my - 1}`}
              stroke={PUPIL_COLOR} strokeWidth={2} fill="none" strokeLinecap="round" />
      );
  }
}

// ─── Nose (positioned lower, at y=70) ────────────────────────

export function Nose({ config }: { config: CharacterConfig }): React.JSX.Element | null {
  const nx = 64;
  const ny = 70;
  
  switch (config.noseStyle) {
    case "dot":
      return <circle cx={nx} cy={ny} r={1.5} fill={darken(config.skinTone, 0.2)} />;
    case "triangle":
      return (
        <path d={`M${nx} ${ny - 2} L${nx - 2} ${ny + 1} L${nx + 2} ${ny + 1} Z`}
              fill={darken(config.skinTone, 0.2)} />
      );
    case "round":
      return <ellipse cx={nx} cy={ny} rx={2} ry={1.5} fill={darken(config.skinTone, 0.15)} />;
    case "button":
      return (
        <g>
          <circle cx={nx} cy={ny} r={2.5} fill={darken(config.skinTone, 0.1)} />
          <circle cx={nx} cy={ny - 1} r={1} fill={WHITE} opacity={0.6} />
        </g>
      );
    default:
      return null;
  }
}

// ─── Blush (on cheeks, not at head edge) ─────────────────────

export function Blush({ config }: { config: CharacterConfig }): React.JSX.Element | null {
  const lx = 44;  // on cheeks, just outside the eyes
  const rx = 84;  // symmetric
  const by = 68;  // below eye line, on cheeks
  
  switch (config.blushStyle) {
    case "circle":
      return (
        <g>
          <circle cx={lx} cy={by} r={5} fill={BLUSH_COLOR} opacity={0.25} />
          <circle cx={rx} cy={by} r={5} fill={BLUSH_COLOR} opacity={0.25} />
        </g>
      );
    case "oval":
      return (
        <g>
          <ellipse cx={lx} cy={by} rx={6} ry={3.5} fill={BLUSH_COLOR} opacity={0.25} />
          <ellipse cx={rx} cy={by} rx={6} ry={3.5} fill={BLUSH_COLOR} opacity={0.25} />
        </g>
      );
    default:
      return null;
  }
}

// ─── Accessories (positioned for new face layout) ────────────

export function AccessoryPart({ config }: { config: CharacterConfig }): React.JSX.Element | null {
  switch (config.accessory) {
    case "glasses":
      return (
        <g>
          <rect x={40} y={56} width={16} height={12} rx={3} fill="none" stroke={config.accessoryColor} strokeWidth={2} />
          <rect x={72} y={56} width={16} height={12} rx={3} fill="none" stroke={config.accessoryColor} strokeWidth={2} />
          <line x1={56} y1={62} x2={72} y2={62} stroke={config.accessoryColor} strokeWidth={2} />
        </g>
      );
    case "round-glasses":
      return (
        <g>
          <circle cx={52} cy={62} r={10} fill="none" stroke={config.accessoryColor} strokeWidth={2} />
          <circle cx={76} cy={62} r={10} fill="none" stroke={config.accessoryColor} strokeWidth={2} />
          <line x1={62} y1={62} x2={66} y2={62} stroke={config.accessoryColor} strokeWidth={2} />
        </g>
      );
    case "sunglasses":
      return (
        <g>
          <rect x={40} y={56} width={16} height={12} rx={4} fill={config.accessoryColor} opacity={0.8} />
          <rect x={72} y={56} width={16} height={12} rx={4} fill={config.accessoryColor} opacity={0.8} />
          <line x1={56} y1={62} x2={72} y2={62} stroke={config.accessoryColor} strokeWidth={3} />
          <path d="M40 62 L30 60" stroke={config.accessoryColor} strokeWidth={2} strokeLinecap="round" />
          <path d="M88 62 L98 60" stroke={config.accessoryColor} strokeWidth={2} strokeLinecap="round" />
        </g>
      );
    case "hat":
      return (
        <g>
          <ellipse cx={64} cy={14} rx={44} ry={10} fill={config.accessoryColor} />
          <path d="M24 14 Q26 -10 64 -14 Q102 -10 104 14 Z" fill={config.accessoryColor} />
          <rect x={24} y={12} width={80} height={5} rx={2} fill={darken(config.accessoryColor, 0.2)} />
        </g>
      );
    case "bow":
      return (
        <g>
          <circle cx={100} cy={30} r={4} fill={config.accessoryColor} />
          <path d="M92 30 Q96 20 100 30 Q104 20 108 30" fill={config.accessoryColor} />
          <path d="M92 30 Q96 40 100 30 Q104 40 108 30" fill={config.accessoryColor} />
        </g>
      );
    case "headband":
      return (
        <path d="M20 38 Q64 28 108 38"
              stroke={config.accessoryColor} strokeWidth={5} fill="none" strokeLinecap="round" />
      );
    case "bandaid":
      return (
        <g>
          <rect x={70} y={50} width={12} height={4} rx={2} fill={config.accessoryColor} />
          <circle cx={72} cy={52} r={1} fill={darken(config.accessoryColor, 0.3)} />
          <circle cx={80} cy={52} r={1} fill={darken(config.accessoryColor, 0.3)} />
        </g>
      );
    default:
      return null;
  }
}

// ─── Extras ──────────────────────────────────────────────────

export function Extras({ items }: { items: ExtraType[] }): React.JSX.Element {
  return (
    <g>
      {items.map((item, index) => {
        switch (item) {
          case "sparkles":
            return <text key={`${item}-${index}`} x={106} y={24} fontSize={16}>✨</text>;

          case "hearts":
            return <text key={`${item}-${index}`} x={104} y={40} fontSize={14}>💕</text>;

          case "tear":
            return (
              <path key={`${item}-${index}`}
                    d="M82 66 Q84 74 82 80 Q80 74 82 66"
                    fill="#7ec8e3" opacity={0.8} />
            );

          case "question":
            return (
              <text key={`${item}-${index}`} x={106} y={16} fontSize={22} fill="#facc15" fontWeight="bold">
                ?
              </text>
            );

          case "exclaim":
            return (
              <text key={`${item}-${index}`} x={106} y={16} fontSize={22} fill="#ef4444" fontWeight="bold">
                !
              </text>
            );

          case "zzz":
            return (
              <text key={`${item}-${index}`} x={100} y={18} fontSize={13} fill="#888" fontStyle="italic">
                z z z
              </text>
            );

          case "music":
            return <text key={`${item}-${index}`} x={12} y={30} fontSize={14}>♪</text>;

          case "steam":
            return (
              <g key={`${item}-${index}`} opacity={0.6}>
                <path d="M46 16 Q42 6 46 0" stroke="#ef4444" strokeWidth={2.5} fill="none" strokeLinecap="round" />
                <path d="M56 14 Q52 4 56 -2" stroke="#ef4444" strokeWidth={2.5} fill="none" strokeLinecap="round" />
                <path d="M66 16 Q62 6 66 0" stroke="#ef4444" strokeWidth={2.5} fill="none" strokeLinecap="round" />
              </g>
            );

          default:
            return null;
        }
      })}
    </g>
  );
}