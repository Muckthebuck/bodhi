/** SVG part renderers for dynamic chibi character. */

import type { CharacterConfig, EyeStyle, HairStyle } from "./types";
import type { EyeVariant, MouthVariant, ArmVariant, LegVariant, ExtraType } from "./poses";

// ─── Helpers ─────────────────────────────────────────────────

export function darken(hex: string, amount = 0.2): string {
  const n = parseInt(hex.slice(1), 16);
  const r = Math.max(0, Math.round(((n >> 16) & 0xff) * (1 - amount)));
  const g = Math.max(0, Math.round(((n >> 8) & 0xff) * (1 - amount)));
  const b = Math.max(0, Math.round((n & 0xff) * (1 - amount)));
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

const SHOE = "#2c3e50";
const PUPIL = "#1a1a2e";
const BLUSH = "#ff9999";
const WHITE = "#ffffff";

// ─── Shadow ──────────────────────────────────────────────────

export function Shadow() {
  return <ellipse cx={64} cy={155} rx={24} ry={4} fill="#000" opacity={0.1} />;
}

// ─── Legs ────────────────────────────────────────────────────

export function Legs({ config, variant }: { config: CharacterConfig; variant: LegVariant }) {
  const dark = darken(config.outfitColor);
  if (variant === "walk0") {
    return (
      <g>
        <rect x={48} y={118} width={10} height={20} rx={5} fill={dark} transform="rotate(-10,53,118)" />
        <ellipse cx={50} cy={140} rx={8} ry={5} fill={SHOE} />
        <rect x={70} y={118} width={10} height={20} rx={5} fill={dark} transform="rotate(10,75,118)" />
        <ellipse cx={78} cy={140} rx={8} ry={5} fill={SHOE} />
      </g>
    );
  }
  if (variant === "walk1") {
    return (
      <g>
        <rect x={48} y={118} width={10} height={20} rx={5} fill={dark} transform="rotate(10,53,118)" />
        <ellipse cx={56} cy={140} rx={8} ry={5} fill={SHOE} />
        <rect x={70} y={118} width={10} height={20} rx={5} fill={dark} transform="rotate(-10,75,118)" />
        <ellipse cx={72} cy={140} rx={8} ry={5} fill={SHOE} />
      </g>
    );
  }
  return (
    <g>
      <rect x={48} y={118} width={10} height={20} rx={5} fill={dark} />
      <ellipse cx={53} cy={140} rx={8} ry={5} fill={SHOE} />
      <rect x={70} y={118} width={10} height={20} rx={5} fill={dark} />
      <ellipse cx={75} cy={140} rx={8} ry={5} fill={SHOE} />
    </g>
  );
}

// ─── Body (outfit) ───────────────────────────────────────────

export function Body({ config, tilt }: { config: CharacterConfig; tilt: number }) {
  const c = config.outfitColor;
  const d = darken(c);

  let body: JSX.Element;
  switch (config.outfitStyle) {
    case "tshirt":
      body = (
        <>
          <rect x={42} y={88} width={44} height={30} rx={8} fill={c} />
          <path d="M54 88 Q64 92 74 88" stroke={d} strokeWidth={1.5} fill="none" opacity={0.4} />
        </>
      );
      break;
    case "dress":
      body = (
        <>
          <path
            d="M46 88 Q42 88 42 96 L40 120 Q40 124 50 126 L78 126 Q88 124 88 120 L86 96 Q86 88 82 88Z"
            fill={c}
          />
          <path d="M42 104 L86 104" stroke={d} strokeWidth={1} opacity={0.3} />
        </>
      );
      break;
    case "jacket":
      body = (
        <>
          <rect x={42} y={88} width={44} height={32} rx={10} fill={c} />
          <line x1={64} y1={88} x2={64} y2={120} stroke={d} strokeWidth={2} opacity={0.4} />
          <rect x={42} y={88} width={8} height={14} rx={3} fill={d} opacity={0.2} />
          <rect x={78} y={88} width={8} height={14} rx={3} fill={d} opacity={0.2} />
        </>
      );
      break;
    default: // hoodie
      body = (
        <>
          <rect x={42} y={88} width={44} height={32} rx={10} fill={c} />
          <rect x={42} y={88} width={44} height={8} rx={4} fill={d} opacity={0.3} />
          <rect x={50} y={106} width={28} height={8} rx={4} fill={d} opacity={0.2} />
        </>
      );
  }

  if (tilt) return <g transform={`rotate(${tilt},64,100)`}>{body}</g>;
  return <g>{body}</g>;
}

// ─── Arms ────────────────────────────────────────────────────

export function Arms({ config, variant }: { config: CharacterConfig; variant: ArmVariant }) {
  const c = config.outfitColor;
  const s = config.skinTone;
  const sw = 8;

  const leftDown = (
    <>
      <path d="M42 92 Q30 100 28 110" stroke={c} strokeWidth={sw} fill="none" strokeLinecap="round" />
      <circle cx={28} cy={112} r={5} fill={s} />
    </>
  );
  const rightDown = (
    <>
      <path d="M86 92 Q98 100 100 110" stroke={c} strokeWidth={sw} fill="none" strokeLinecap="round" />
      <circle cx={100} cy={112} r={5} fill={s} />
    </>
  );

  const waveRight = (angle: number) => (
    <g transform={`rotate(${angle},86,92)`}>
      <path d="M86 92 Q98 85 105 75" stroke={c} strokeWidth={sw} fill="none" strokeLinecap="round" />
      <circle cx={105} cy={73} r={5} fill={s} />
    </g>
  );

  switch (variant) {
    case "wave0":
      return <g>{leftDown}{waveRight(-20)}</g>;
    case "wave1":
      return <g>{leftDown}{waveRight(-35)}</g>;
    case "wave2":
      return <g>{leftDown}{waveRight(-50)}</g>;
    case "wave3":
      return <g>{leftDown}{waveRight(-35)}</g>;
    case "think":
      return (
        <g>
          <path d="M42 92 Q32 88 38 75" stroke={c} strokeWidth={sw} fill="none" strokeLinecap="round" />
          <circle cx={38} cy={73} r={5} fill={s} />
          {rightDown}
        </g>
      );
    case "hug":
      return (
        <g>
          <path d="M42 92 Q34 96 40 106" stroke={c} strokeWidth={sw} fill="none" strokeLinecap="round" />
          <circle cx={42} cy={108} r={5} fill={s} />
          <path d="M86 92 Q94 96 88 106" stroke={c} strokeWidth={sw} fill="none" strokeLinecap="round" />
          <circle cx={86} cy={108} r={5} fill={s} />
        </g>
      );
    default:
      return <g>{leftDown}{rightDown}</g>;
  }
}

// ─── Hair Back ───────────────────────────────────────────────

const HAIR_BACK_PATHS: Record<HairStyle, string> = {
  short:
    "M30 42 Q32 18 64 14 Q96 18 98 42 Q98 52 90 56 Q78 48 64 46 Q50 48 38 56 Q30 52 30 42Z",
  long:
    "M28 40 Q30 14 64 10 Q98 14 100 40 L100 85 Q98 95 88 100 Q80 92 64 90 Q48 92 40 100 Q30 95 28 85Z",
  curly:
    "M28 38 Q30 14 46 12 Q52 8 64 10 Q76 8 82 12 Q98 14 100 38 Q104 50 100 60 Q98 68 92 60 Q88 70 82 62 Q78 72 68 60 Q62 72 52 62 Q46 70 38 60 Q32 68 30 60 Q24 50 28 38Z",
  spiky:
    "M30 50 L38 16 L50 38 L56 8 L64 34 L72 6 L78 38 L90 16 L98 50 Q96 34 82 28 Q64 20 46 28 Q32 34 30 50Z",
  bob:
    "M30 42 Q32 18 64 14 Q96 18 98 42 Q100 60 94 68 Q88 72 80 72 Q64 70 48 72 Q40 72 34 68 Q28 60 30 42Z",
  ponytail:
    "M30 42 Q32 18 64 14 Q96 18 98 42 Q98 50 92 54 L100 80 Q98 86 92 80 L90 54 Q78 46 64 44 Q50 46 38 54 Q30 50 30 42Z",
};

export function HairBack({ config }: { config: CharacterConfig }) {
  return <path d={HAIR_BACK_PATHS[config.hairStyle]} fill={config.hairColor} />;
}

// ─── Face ────────────────────────────────────────────────────

export function Face({ config }: { config: CharacterConfig }) {
  switch (config.faceShape) {
    case "oval":
      return <ellipse cx={64} cy={48} rx={26} ry={30} fill={config.skinTone} />;
    case "heart":
      return (
        <path
          d="M34 45 Q36 24 64 20 Q92 24 94 45 Q90 60 80 66 Q72 72 64 74 Q56 72 48 66 Q38 60 34 45Z"
          fill={config.skinTone}
        />
      );
    default:
      return <ellipse cx={64} cy={48} rx={30} ry={28} fill={config.skinTone} />;
  }
}

// ─── Hair Front ──────────────────────────────────────────────

const HAIR_FRONT_PATHS: Record<HairStyle, string> = {
  short: "M34 40 Q44 24 64 22 Q84 24 94 40 Q88 32 76 30 Q64 28 52 30 Q40 32 34 40Z",
  long: "M34 40 Q40 22 64 18 Q88 22 94 40 Q88 30 76 28 Q64 24 52 28 Q40 30 34 40Z",
  curly:
    "M34 40 Q38 22 52 18 Q58 14 64 16 Q70 14 76 18 Q90 22 94 40 Q86 30 78 28 Q72 26 64 28 Q56 26 50 28 Q42 30 34 40Z",
  spiky:
    "M36 42 L42 22 L50 36 L56 18 L64 32 L72 18 L78 36 L86 22 L92 42 Q86 34 76 30 Q64 26 52 30 Q42 34 36 42Z",
  bob: "M34 40 Q40 22 64 18 Q88 22 94 40 Q88 32 76 30 Q64 28 52 30 Q40 32 34 40Z",
  ponytail:
    "M34 40 Q42 22 58 20 Q64 18 70 20 Q86 22 94 40 Q88 32 76 30 Q64 28 52 30 Q40 32 34 40Z",
};

const HAIR_TUFTS: Record<HairStyle, string | null> = {
  short: "M56 18 Q58 10 64 8 Q70 10 72 18",
  long: null,
  curly: "M50 16 Q56 6 64 8 Q72 6 78 16",
  spiky: null,
  bob: null,
  ponytail: "M58 18 Q62 10 66 18",
};

export function HairFront({ config }: { config: CharacterConfig }) {
  const tuft = HAIR_TUFTS[config.hairStyle];
  return (
    <g>
      <path d={HAIR_FRONT_PATHS[config.hairStyle]} fill={config.hairColor} />
      {tuft && <path d={tuft} fill={config.hairColor} stroke={config.hairColor} strokeWidth={1} />}
    </g>
  );
}

// ─── Eyes ─────────────────────────────────────────────────────

const EYE_DIM: Record<EyeStyle, { rx: number; ry: number }> = {
  round: { rx: 6, ry: 7 },
  narrow: { rx: 6, ry: 4 },
  wide: { rx: 7, ry: 9 },
  cat: { rx: 6, ry: 6 },
};

function renderSingleEye(
  cx: number,
  cy: number,
  eyeStyle: EyeStyle,
  eyeColor: string,
  pupilDx: number,
  pupilDy: number,
  pupilR: number,
  highlightR: number,
) {
  const d = EYE_DIM[eyeStyle];
  if (eyeStyle === "cat") {
    return (
      <g>
        <path
          d={`M${cx - d.rx} ${cy} Q${cx} ${cy - d.ry} ${cx + d.rx} ${cy} Q${cx} ${cy + d.ry} ${cx - d.rx} ${cy}Z`}
          fill={WHITE}
        />
        <circle cx={cx + pupilDx} cy={cy + pupilDy} r={pupilR} fill={eyeColor} />
        <circle cx={cx + pupilDx} cy={cy + pupilDy} r={pupilR * 0.5} fill={PUPIL} />
        <circle cx={cx + pupilDx + 1} cy={cy + pupilDy - 2} r={highlightR} fill={WHITE} />
      </g>
    );
  }
  return (
    <g>
      <ellipse cx={cx} cy={cy} rx={d.rx} ry={d.ry} fill={WHITE} />
      <circle cx={cx + pupilDx} cy={cy + pupilDy} r={pupilR} fill={eyeColor} />
      <circle cx={cx + pupilDx} cy={cy + pupilDy} r={pupilR * 0.5} fill={PUPIL} />
      <circle cx={cx + pupilDx + 1} cy={cy + pupilDy - 2} r={highlightR} fill={WHITE} />
    </g>
  );
}

export function Eyes({ config, variant }: { config: CharacterConfig; variant: EyeVariant }) {
  const { eyeStyle, eyeColor } = config;

  if (variant === "closed") {
    return (
      <g>
        <path d="M46 50 Q52 46 58 50" stroke={PUPIL} strokeWidth={2} fill="none" strokeLinecap="round" />
        <path d="M70 50 Q76 46 82 50" stroke={PUPIL} strokeWidth={2} fill="none" strokeLinecap="round" />
      </g>
    );
  }

  if (variant === "happy") {
    return (
      <g>
        <path d="M46 48 Q52 40 58 48" stroke={PUPIL} strokeWidth={2.5} fill="none" strokeLinecap="round" />
        <path d="M70 48 Q76 40 82 48" stroke={PUPIL} strokeWidth={2.5} fill="none" strokeLinecap="round" />
      </g>
    );
  }

  let cy = 48;
  let pupilDx = 2;
  let pupilDy = 0;
  let pupilR = eyeStyle === "wide" ? 5 : eyeStyle === "narrow" ? 3 : 4;
  const highlightR = eyeStyle === "wide" ? 2 : 1.5;
  let brows: JSX.Element | null = null;

  switch (variant) {
    case "sad":
      cy = 50;
      pupilDy = 2;
      brows = (
        <g>
          <line x1={46} y1={42} x2={56} y2={44} stroke={config.hairColor} strokeWidth={2} strokeLinecap="round" />
          <line x1={82} y1={42} x2={72} y2={44} stroke={config.hairColor} strokeWidth={2} strokeLinecap="round" />
        </g>
      );
      break;
    case "wide":
      cy = 47;
      pupilR = eyeStyle === "wide" ? 6 : 5;
      break;
    case "angry":
      cy = 50;
      brows = (
        <g>
          <line x1={44} y1={42} x2={58} y2={46} stroke={PUPIL} strokeWidth={2.5} strokeLinecap="round" />
          <line x1={84} y1={42} x2={70} y2={46} stroke={PUPIL} strokeWidth={2.5} strokeLinecap="round" />
        </g>
      );
      break;
    case "lookUp":
      pupilDy = -4;
      break;
  }

  return (
    <g>
      {brows}
      {renderSingleEye(52, cy, eyeStyle, eyeColor, pupilDx, pupilDy, pupilR, highlightR)}
      {renderSingleEye(76, cy, eyeStyle, eyeColor, pupilDx, pupilDy, pupilR, highlightR)}
    </g>
  );
}

// ─── Mouth ───────────────────────────────────────────────────

export function Mouth({ variant }: { variant: MouthVariant }) {
  switch (variant) {
    case "bigSmile":
      return (
        <path d="M54 58 Q64 70 74 58" stroke={PUPIL} strokeWidth={2} fill={WHITE} strokeLinecap="round" />
      );
    case "neutral":
      return <line x1={58} y1={62} x2={70} y2={62} stroke={PUPIL} strokeWidth={2} strokeLinecap="round" />;
    case "sad":
      return (
        <path d="M56 64 Q64 58 72 64" stroke={PUPIL} strokeWidth={2} fill="none" strokeLinecap="round" />
      );
    case "open":
      return (
        <g>
          <ellipse cx={64} cy={62} rx={6} ry={5} fill={PUPIL} />
          <ellipse cx={64} cy={61} rx={4} ry={3} fill="#ff6b6b" opacity={0.5} />
        </g>
      );
    case "talk1":
      return <ellipse cx={64} cy={62} rx={5} ry={3} fill={PUPIL} />;
    case "talk2":
      return (
        <g>
          <ellipse cx={64} cy={62} rx={7} ry={4} fill={PUPIL} />
          <ellipse cx={64} cy={61} rx={5} ry={2} fill="#ff6b6b" opacity={0.4} />
        </g>
      );
    case "smallO":
      return <circle cx={64} cy={62} r={3} fill={PUPIL} />;
    case "cat":
      return (
        <path d="M56 60 L64 64 L72 60" stroke={PUPIL} strokeWidth={2} fill="none" strokeLinecap="round" />
      );
    default:
      return (
        <path d="M56 60 Q64 68 72 60" stroke={PUPIL} strokeWidth={2} fill="none" strokeLinecap="round" />
      );
  }
}

// ─── Blush ───────────────────────────────────────────────────

export function Blush() {
  return (
    <g>
      <circle cx={42} cy={56} r={5} fill={BLUSH} opacity={0.25} />
      <circle cx={86} cy={56} r={5} fill={BLUSH} opacity={0.25} />
    </g>
  );
}

// ─── Accessories ─────────────────────────────────────────────

export function AccessoryPart({ config }: { config: CharacterConfig }) {
  switch (config.accessory) {
    case "glasses":
      return (
        <g>
          <rect x={42} y={43} width={16} height={12} rx={2} fill="none" stroke={PUPIL} strokeWidth={1.5} />
          <rect x={70} y={43} width={16} height={12} rx={2} fill="none" stroke={PUPIL} strokeWidth={1.5} />
          <line x1={58} y1={49} x2={70} y2={49} stroke={PUPIL} strokeWidth={1.5} />
        </g>
      );
    case "round-glasses":
      return (
        <g>
          <circle cx={52} cy={48} r={9} fill="none" stroke={PUPIL} strokeWidth={1.5} />
          <circle cx={76} cy={48} r={9} fill="none" stroke={PUPIL} strokeWidth={1.5} />
          <line x1={61} y1={48} x2={67} y2={48} stroke={PUPIL} strokeWidth={1.5} />
        </g>
      );
    case "sunglasses":
      return (
        <g>
          <rect x={42} y={43} width={16} height={12} rx={3} fill={PUPIL} opacity={0.7} />
          <rect x={70} y={43} width={16} height={12} rx={3} fill={PUPIL} opacity={0.7} />
          <line x1={58} y1={49} x2={70} y2={49} stroke={PUPIL} strokeWidth={2} />
          <path d="M42 49 L36 47" stroke={PUPIL} strokeWidth={1.5} />
          <path d="M86 49 L92 47" stroke={PUPIL} strokeWidth={1.5} />
        </g>
      );
    case "hat":
      return (
        <g>
          <ellipse cx={64} cy={22} rx={30} ry={6} fill={config.outfitColor} />
          <path d={`M38 22 Q40 4 64 2 Q88 4 90 22Z`} fill={config.outfitColor} />
          <rect x={38} y={20} width={52} height={4} rx={2} fill={darken(config.outfitColor)} />
        </g>
      );
    case "bow":
      return (
        <g>
          <circle cx={88} cy={30} r={3} fill="#ef4444" />
          <path d="M82 30 Q85 24 88 30 Q91 24 94 30" fill="#ef4444" />
          <path d="M82 30 Q85 36 88 30 Q91 36 94 30" fill="#ef4444" />
        </g>
      );
    case "headband":
      return (
        <path
          d="M34 36 Q64 28 94 36"
          stroke={config.outfitColor}
          strokeWidth={4}
          fill="none"
          strokeLinecap="round"
        />
      );
    default:
      return null;
  }
}

// ─── Extras ──────────────────────────────────────────────────

export function Extras({ items }: { items: ExtraType[] }) {
  return (
    <g>
      {items.map((item) => {
        switch (item) {
          case "sparkles":
            return <text key="sparkles" x={95} y={35} fontSize={16}>✨</text>;
          case "hearts":
            return <text key="hearts" x={90} y={50} fontSize={14}>💕</text>;
          case "tear":
            return (
              <path
                key="tear"
                d="M84 52 Q86 58 84 62"
                stroke="#7ec8e3"
                strokeWidth={2}
                fill="none"
                strokeLinecap="round"
              />
            );
          case "question":
            return (
              <text key="question" x={92} y={28} fontSize={20} fill="#facc15" fontWeight="bold">
                ?
              </text>
            );
          case "exclaim":
            return (
              <text key="exclaim" x={92} y={28} fontSize={20} fill="#ef4444" fontWeight="bold">
                !
              </text>
            );
          case "zzz":
            return (
              <text key="zzz" x={86} y={30} fontSize={12} fill="#888" fontStyle="italic">
                z z z
              </text>
            );
          case "music":
            return <text key="music" x={20} y={40} fontSize={14}>♪</text>;
          case "steam":
            return (
              <g key="steam" opacity={0.5}>
                <path d="M44 20 Q40 12 44 6" stroke="#ef4444" strokeWidth={2} fill="none" />
                <path d="M52 18 Q48 10 52 4" stroke="#ef4444" strokeWidth={2} fill="none" />
              </g>
            );
          default:
            return null;
        }
      })}
    </g>
  );
}
