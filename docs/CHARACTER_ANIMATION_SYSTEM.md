# Character Animation System Design

**Last Updated:** 2026-02-21  
**Status:** Design Complete  
**Target Platform:** Client Devices (Laptop, Desktop, Phone) + RPi5 Host

---

## 1. Overview & Philosophy

The Character Animation System brings the AI companion to life through an **on-screen character** that provides visual feedback, emotional expression, and interactive presence. The character is a visible embodiment of the companion's "motor module" - just as the companion can learn to control physical robots, it controls this virtual character.

### Design Principles

1. **Non-Intrusive:** Never blocks important content, smart positioning
2. **Expressive:** Rich emotional range and contextual animations
3. **Customizable:** Multiple character styles, themes, and behaviors
4. **Performant:** Lightweight rendering, minimal CPU/GPU usage
5. **Context-Aware:** Adapts animations to user activity and screen context
6. **Modular:** Follows VLA (Vision-Language-Action) embodiment abstraction

### Key Features

- **Multiple character styles:** 2D sprite, 2D skeletal, 3D low-poly, hybrid (user can switch)
- **Flexible positioning:** Corner mascot, roaming, context-aware, dockable "couch"
- **Full expressiveness:** Basic states + rich emotions + activity-aware + personality-driven
- **Smart interference avoidance:** Hides when user is focused, smart positioning, dockable
- **Lip-sync:** Synchronized with voice output
- **Interactive:** Can point at UI elements, gesture, react to user actions
- **Personality-driven:** Animations reflect Big Five personality settings

---

## 2. Architecture Overview

### 2.1 System Components

```
┌──────────────────────────────────────────────────────────────────────┐
│                  Character Animation System                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  CLIENT DEVICE (Where character is rendered)                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Character Controller (Client Agent)               │ │ │
│  │  │  - Receives animation commands from host                  │ │ │
│  │  │  - Manages character state machine                        │ │ │
│  │  │  - Handles positioning logic                              │ │ │
│  │  │  - Detects occlusion and interference                     │ │ │
│  │  └───────────────────┬────────────────────────────────────────┘ │ │
│  │                      │                                           │ │
│  │                      ▼                                           │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Animation Engine                                  │ │ │
│  │  │                                                            │ │ │
│  │  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │ │ │
│  │  │  │ 2D Sprite  │  │ 2D Skeletal│  │  3D Low-Poly       │ │ │ │
│  │  │  │ Renderer   │  │ Renderer   │  │  Renderer          │ │ │ │
│  │  │  │ (Pygame)   │  │ (Spine)    │  │  (Three.js/Godot)  │ │ │ │
│  │  │  └────────────┘  └────────────┘  └────────────────────┘ │ │ │
│  │  │                                                            │ │ │
│  │  │  Active renderer selected by user preference              │ │ │
│  │  └───────────────────┬────────────────────────────────────────┘ │ │
│  │                      │                                           │ │
│  │                      ▼                                           │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Screen Overlay (Transparent Window)               │ │ │
│  │  │  - OpenGL/DirectX hardware-accelerated rendering         │ │ │
│  │  │  - Always-on-top window                                   │ │ │
│  │  │  - Click-through transparent regions                      │ │ │
│  │  │  - Drag-and-drop to reposition                            │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                         │ mTLS                                        │
│                         │ Animation commands                          │
│                         │                                             │
│  HOST DEVICE (RPi5)                                                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Motor Control Module (Host-Side)                  │ │ │
│  │  │  - Decides what animations to play                        │ │ │
│  │  │  - Personality-driven animation selection                 │ │ │
│  │  │  - Sends commands to client                               │ │ │
│  │  │                                                            │ │ │
│  │  │  Inputs:                                                   │ │ │
│  │  │  • Emotional state (from Emotion Regulator)               │ │ │
│  │  │  • Speech output (for lip-sync)                           │ │ │
│  │  │  • User context (idle, typing, focused)                   │ │ │
│  │  │  • Personality settings (Big Five)                        │ │ │
│  │  │                                                            │ │ │
│  │  │  Outputs:                                                  │ │ │
│  │  │  • Animation commands (JSON)                              │ │ │
│  │  │  • Positioning hints                                       │ │ │
│  │  │  • Phoneme sequences (for lip-sync)                       │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Central Agent Integration                          │ │ │
│  │  │  - Triggers animations based on actions                   │ │ │
│  │  │  - "Point at this UI element"                             │ │ │
│  │  │  - "Show thinking animation"                              │ │ │
│  │  │  - "Express confusion"                                     │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  KEY DESIGN:                                                         │
│  Host decides WHAT to animate (brain)                                │
│  Client renders HOW it looks (motor execution)                       │
│  → Follows embodiment abstraction (same API for physical robots)     │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 2. Character Styles (Multi-Style Support)

### 2.1 Style Selection Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Character Style System                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  User can select from 4 rendering engines + multiple character sets  │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STYLE 1: 2D Sprite-Based (Retro Desktop Pet)                   │ │
│  │                                                                 │ │
│  │ Technology: Pygame / SDL2                                       │ │
│  │ Assets: Sprite sheets (PNG sequences)                           │ │
│  │                                                                 │ │
│  │ Characteristics:                                                │ │
│  │ • Pixel art aesthetic (32x32, 64x64, 128x128)                  │ │
│  │ • Frame-based animation (8-16 frames per animation)            │ │
│  │ • Low resource usage (~5-10 MB RAM)                            │ │
│  │ • Nostalgic feel (like Clippy, Bonzi Buddy, eSheep)           │ │
│  │                                                                 │ │
│  │ Animation states (examples):                                    │ │
│  │ • idle_01.png, idle_02.png, ..., idle_08.png                   │ │
│  │ • wave_01.png, wave_02.png, ..., wave_12.png                   │ │
│  │ • think_01.png, think_02.png, ..., think_16.png                │ │
│  │ • point_left_01.png, ..., point_right_01.png                   │ │
│  │                                                                 │ │
│  │ Pros:                                                           │ │
│  │ • Extremely lightweight                                         │ │
│  │ • Easy to create custom characters (pixel art tools)           │ │
│  │ • Nostalgic appeal                                             │ │
│  │ • Works on any hardware                                         │ │
│  │                                                                 │ │
│  │ Cons:                                                           │ │
│  │ • Limited expressiveness                                        │ │
│  │ • Discrete animations (not smooth interpolation)               │ │
│  │ • Scaling looks pixelated                                       │ │
│  │                                                                 │ │
│  │ Example Characters:                                             │ │
│  │ • "Pixel Companion" (robot mascot)                             │ │
│  │ • "Retro Cat" (8-bit cat)                                      │ │
│  │ • "Blocky Bot" (Minecraft-style)                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STYLE 2: 2D Skeletal Animation (Modern Smooth 2D)              │ │
│  │                                                                 │ │
│  │ Technology: Spine / DragonBones / Creature2D                    │ │
│  │ Assets: Skeleton + texture atlas + animation data               │ │
│  │                                                                 │ │
│  │ Characteristics:                                                │ │
│  │ • Bone-based rigging (like puppets)                            │ │
│  │ • Smooth interpolation between keyframes                        │ │
│  │ • Can blend multiple animations                                 │ │
│  │ • Higher quality, more expressive                               │ │
│  │                                                                 │ │
│  │ Skeleton structure:                                             │ │
│  │   root                                                          │ │
│  │   ├── body                                                      │ │
│  │   │   ├── head                                                  │ │
│  │   │   │   ├── eyes                                              │ │
│  │   │   │   ├── mouth                                             │ │
│  │   │   │   └── ears                                              │ │
│  │   │   ├── left_arm                                              │ │
│  │   │   │   └── left_hand                                         │ │
│  │   │   └── right_arm                                             │ │
│  │   │       └── right_hand                                        │ │
│  │   └── legs...                                                   │ │
│  │                                                                 │ │
│  │ Animation capabilities:                                         │ │
│  │ • Procedural animation (IK for pointing)                        │ │
│  │ • Lip-sync via bone control                                     │ │
│  │ • Physics simulation (hair, clothes)                            │ │
│  │ • Smooth transitions between states                             │ │
│  │                                                                 │ │
│  │ Resource usage: ~20-40 MB RAM                                   │ │
│  │                                                                 │ │
│  │ Pros:                                                           │ │
│  │ • Very smooth, professional-looking                             │ │
│  │ • Highly expressive                                             │ │
│  │ • Good for lip-sync                                             │ │
│  │ • Scalable without quality loss                                 │ │
│  │                                                                 │ │
│  │ Cons:                                                           │ │
│  │ • More complex to create                                        │ │
│  │ • Higher CPU usage than sprites                                 │ │
│  │ • Requires specialized tools (Spine license)                    │ │
│  │                                                                 │ │
│  │ Example Characters:                                             │ │
│  │ • "Smooth Companion" (anime-style assistant)                   │ │
│  │ • "Friendly Fox" (2D rigged animal)                            │ │
│  │ • "Office Assistant" (professional humanoid)                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STYLE 3: 3D Low-Poly (Simple 3D)                               │ │
│  │                                                                 │ │
│  │ Technology: Three.js (WebGL) / Godot 3D / Blender export        │ │
│  │ Assets: 3D model (FBX/GLTF), textures, rigged skeleton          │ │
│  │                                                                 │ │
│  │ Characteristics:                                                │ │
│  │ • Low polygon count (500-2000 tris)                            │ │
│  │ • Simple textures (flat colors or stylized)                    │ │
│  │ • 3D depth and rotation                                         │ │
│  │ • More lifelike than 2D                                         │ │
│  │                                                                 │ │
│  │ Polygon budget:                                                 │ │
│  │ • Head: 200 tris                                                │ │
│  │ • Body: 400 tris                                                │ │
│  │ • Arms: 150 tris each                                           │ │
│  │ • Legs: 150 tris each                                           │ │
│  │ • Total: ~1200 tris                                             │ │
│  │                                                                 │ │
│  │ Animation:                                                      │ │
│  │ • Skeletal animation (same as 2D but in 3D space)              │ │
│  │ • Can face camera (billboard mode) or rotate freely            │ │
│  │ • Better for pointing (actual 3D pointing vector)              │ │
│  │                                                                 │ │
│  │ Resource usage: ~50-80 MB RAM, GPU-accelerated                 │ │
│  │                                                                 │ │
│  │ Pros:                                                           │ │
│  │ • More expressive (3D facial expressions)                       │ │
│  │ • Can interact with "3D space" on flat screen                  │ │
│  │ • Modern aesthetic                                              │ │
│  │ • Good for AR/VR future expansion                               │ │
│  │                                                                 │ │
│  │ Cons:                                                           │ │
│  │ • Higher GPU usage                                              │ │
│  │ • More complex creation pipeline                                │ │
│  │ • May look out of place on 2D desktop                          │ │
│  │                                                                 │ │
│  │ Example Characters:                                             │ │
│  │ • "Low-Poly Robot" (geometric robot mascot)                    │ │
│  │ • "Stylized Human" (simple 3D person)                          │ │
│  │ • "Abstract Orb" (floating sphere with face)                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STYLE 4: Hybrid (Best of All Worlds)                           │ │
│  │                                                                 │ │
│  │ Concept: Use different styles for different contexts           │ │
│  │                                                                 │ │
│  │ Default: 2D Skeletal (smooth, lightweight)                     │ │
│  │ Special moments: 3D Low-Poly (celebrations, important events)  │ │
│  │ Minimal mode: 2D Sprite (when resources are constrained)       │ │
│  │                                                                 │ │
│  │ Example workflow:                                               │ │
│  │ • Normal operations: 2D skeletal character                     │ │
│  │ • User asks complex question: Character switches to 3D,        │ │
│  │   rotates head to "think"                                       │ │
│  │ • Task completed successfully: 3D celebration animation        │ │
│  │ • Low battery mode: Switch to lightweight 2D sprite            │ │
│  │                                                                 │ │
│  │ Pros:                                                           │ │
│  │ • Best of all approaches                                        │ │
│  │ • Adaptive to resource constraints                             │ │
│  │ • Special moments feel more impactful                           │ │
│  │                                                                 │ │
│  │ Cons:                                                           │ │
│  │ • Requires all renderers to be available                        │ │
│  │ • More complex state management                                 │ │
│  │ • Transitions between styles must be handled gracefully        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  USER CONFIGURATION:                                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Settings → Character → Style:                                   │ │
│  │  ( ) 2D Sprite (Retro)                                          │ │
│  │  (•) 2D Skeletal (Smooth) ← Default                            │ │
│  │  ( ) 3D Low-Poly                                                │ │
│  │  ( ) Hybrid (Adaptive)                                          │ │
│  │                                                                 │ │
│  │ Character Selection: [Dropdown with 10+ characters]            │ │
│  │  • Default Robot                                                │ │
│  │  • Friendly Fox                                                 │ │
│  │  • Office Cat                                                   │ │
│  │  • Pixel Buddy                                                  │ │
│  │  • Custom (Import your own)                                     │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3. Positioning System

### 3.1 Positioning Modes (All User-Configurable)

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Character Positioning System                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  MODE 1: Corner Mascot (Classic Desktop Pet)                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Character stays in a corner, doesn't roam                      │ │
│  │                                                                 │ │
│  │  Position options:                                              │ │
│  │  • Top-left                                                     │ │
│  │  • Top-right (default)                                          │ │
│  │  • Bottom-left                                                  │ │
│  │  • Bottom-right                                                 │ │
│  │                                                                 │ │
│  │  Behavior:                                                      │ │
│  │  • Always visible in chosen corner                             │ │
│  │  • Animates in place (wave, idle, speak)                        │ │
│  │  • Can point to other parts of screen (arm extends)            │ │
│  │  • Never moves from corner unless user drags                    │ │
│  │                                                                 │ │
│  │  Screen layout:                                                 │ │
│  │  ┌────────────────────────────────────────────────────┐        │ │
│  │  │                                        [Character] │        │ │
│  │  │                                           👋       │        │ │
│  │  │                                                     │        │ │
│  │  │          User's windows and work area              │        │ │
│  │  │                                                     │        │ │
│  │  │                                                     │        │ │
│  │  └────────────────────────────────────────────────────┘        │ │
│  │                                                                 │ │
│  │  Pros: Simple, predictable, never in the way                   │ │
│  │  Cons: Less interactive, can feel disconnected from content    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  MODE 2: Roaming Character (Free Movement)                          │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Character can move anywhere on screen                          │ │
│  │                                                                 │ │
│  │  Movement behaviors:                                            │ │
│  │  • Random walks (wander when idle)                             │ │
│  │  • Purposeful movement (walk to UI element to point)           │ │
│  │  • Gravity simulation (can "fall" to bottom, climb up)         │ │
│  │  • Avoid active windows (stay in safe zones)                   │ │
│  │                                                                 │ │
│  │  Movement animation:                                            │ │
│  │  • Walking animation when moving                                │ │
│  │  • Smooth interpolation (ease-in/ease-out)                     │ │
│  │  • Can jump, hop, fly (depending on character type)            │ │
│  │                                                                 │ │
│  │  Safe zones:                                                    │ │
│  │  ┌────────────────────────────────────────────────────┐        │ │
│  │  │ ██ Safe ██     Active Window      ██ Safe ██       │        │ │
│  │  │ ██ Zone ██   (User is typing)    ██ Zone ██       │        │ │
│  │  │ ██      ██                        ██      ██       │        │ │
│  │  │ ██████████████████████████████████████████████     │        │ │
│  │  │ ██████ Safe Zone (Bottom) █████████████████████    │        │ │
│  │  └────────────────────────────────────────────────────┘        │ │
│  │                                                                 │ │
│  │  Pros: Fun, engaging, can point directly at things             │ │
│  │  Cons: Can be distracting, may accidentally cover content      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  MODE 3: Context-Aware Positioning (Smart)                          │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Character positions itself based on what's happening           │ │
│  │                                                                 │ │
│  │  Context-aware behaviors:                                       │ │
│  │                                                                 │ │
│  │  1. Near notifications (when alerting user)                    │ │
│  │     ┌─────────────────────────────────────────────┐            │ │
│  │     │                         [Notification Area] │            │ │
│  │     │                              [Character] 📧  │            │ │
│  │     │                              "You have mail!"│            │ │
│  │     └─────────────────────────────────────────────┘            │ │
│  │                                                                 │ │
│  │  2. Near active UI element (when explaining something)         │ │
│  │     ┌─────────────────────────────────────────────┐            │ │
│  │     │  [Button]  ← [Character] "Click here!"      │            │ │
│  │     └─────────────────────────────────────────────┘            │ │
│  │                                                                 │ │
│  │  3. Center bottom (when speaking to user)                      │ │
│  │     ┌─────────────────────────────────────────────┐            │ │
│  │     │                                              │            │ │
│  │     │            [Character] 💬                    │            │ │
│  │     │  "I found 5 unread emails for you"          │            │ │
│  │     └─────────────────────────────────────────────┘            │ │
│  │                                                                 │ │
│  │  4. Docked in couch (when idle)                                │ │
│  │     ┌─────────────────────────────────────────────┐            │ │
│  │     │ [🛋️ Couch] [Character sleeping] 💤          │            │ │
│  │     └─────────────────────────────────────────────┘            │ │
│  │                                                                 │ │
│  │  Positioning logic:                                             │ │
│  │  • Detect UI element to point at → Move near it                │ │
│  │  • User asks question → Move to center bottom                  │ │
│  │  • New notification → Move near notification area              │ │
│  │  • Idle for >5 min → Move to couch                             │ │
│  │  • User starts typing → Move to corner                         │ │
│  │                                                                 │ │
│  │  Pros: Feels intelligent, helpful, context-appropriate         │ │
│  │  Cons: More complex logic, can still be distracting            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  MODE 4: Dockable with Couch (Hybrid)                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Character can be docked to a "couch" (fixed position)          │ │
│  │                                                                 │ │
│  │  Couch locations:                                               │ │
│  │  • Bottom left corner (default)                                │ │
│  │  • Bottom right corner                                          │ │
│  │  • System tray area (minimized)                                │ │
│  │  • Custom position (user drags couch to desired location)      │ │
│  │                                                                 │ │
│  │  Couch behavior:                                                │ │
│  │  • Character "sits" on couch when idle                         │ │
│  │  • Can leave couch when needed (for pointing, etc.)            │ │
│  │  • Returns to couch after activity                             │ │
│  │  • User can drag character to couch to "put away"              │ │
│  │                                                                 │ │
│  │  Visual design:                                                 │ │
│  │  ┌────────────────────────────────────────────────────┐        │ │
│  │  │                                                     │        │ │
│  │  │                                                     │        │ │
│  │  │                                                     │        │ │
│  │  │                                                     │        │ │
│  │  │ [🛋️══════] [Character sitting, reading book] 📖    │        │ │
│  │  └────────────────────────────────────────────────────┘        │ │
│  │                                                                 │ │
│  │  Couch states:                                                  │ │
│  │  • Idle: Character sits/sleeps on couch                        │ │
│  │  • Active: Character stands on/near couch                      │ │
│  │  • Away: Couch is empty (character roaming)                    │ │
│  │  • Hidden: Both couch and character hidden (minimize button)   │ │
│  │                                                                 │ │
│  │  User interactions:                                             │ │
│  │  • Click couch → Toggle minimize/maximize                       │ │
│  │  • Drag couch → Reposition                                     │ │
│  │  • Right-click couch → Settings menu                           │ │
│  │  • Drag character to couch → Force return                      │ │
│  │                                                                 │ │
│  │  Pros: User control, non-intrusive, cute aesthetic             │ │
│  │  Cons: Takes up screen space (though minimal)                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  COMBINED CONFIGURATION:                                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ User can combine multiple modes:                                │ │
│  │                                                                 │ │
│  │ Example 1: Couch + Context-Aware                                │ │
│  │ • Default: Sits on couch in bottom-left                        │ │
│  │ • When needed: Leaves couch, moves contextually                │ │
│  │ • After task: Returns to couch                                  │ │
│  │                                                                 │ │
│  │ Example 2: Roaming + Smart Positioning                          │ │
│  │ • Normal: Wanders in safe zones                                │ │
│  │ • When user typing: Moves to corner                            │ │
│  │ • When pointing: Moves near target UI element                  │ │
│  │                                                                 │ │
│  │ Example 3: Corner + Dockable                                    │ │
│  │ • Usually in top-right corner                                   │ │
│  │ • Can be minimized to couch in bottom-left                     │ │
│  │ • User drags back to corner when needed                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 3.2 Smart Interference Avoidance

```python
# interference_avoidance.py - Smart positioning logic

import asyncio
from typing import Tuple, List, Optional
from dataclasses import dataclass

@dataclass
class ScreenRegion:
    """Represents a rectangular region on screen."""
    x: int
    y: int
    width: int
    height: int
    
    def contains_point(self, px: int, py: int) -> bool:
        """Check if point is inside region."""
        return (self.x <= px < self.x + self.width and
                self.y <= py < self.y + self.height)
    
    def overlaps(self, other: 'ScreenRegion') -> bool:
        """Check if two regions overlap."""
        return not (self.x + self.width < other.x or
                    other.x + other.width < self.x or
                    self.y + self.height < other.y or
                    other.y + other.height < self.y)


class InterferenceAvoider:
    """Manages character positioning to avoid interfering with user work."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.character_size = (100, 150)  # Width, height
        self.safe_margin = 20  # Pixels from window edges
    
    async def get_safe_position(
        self,
        desired_position: Tuple[int, int],
        context: dict
    ) -> Tuple[int, int]:
        """
        Get a safe position for character that doesn't interfere.
        
        Args:
            desired_position: Where character wants to be (x, y)
            context: Current screen context (active windows, user activity, etc.)
        
        Returns:
            Adjusted position (x, y) that avoids interference
        """
        # Get all occupied regions (windows, active UI elements)
        occupied_regions = await self._get_occupied_regions(context)
        
        # Check if desired position is safe
        char_region = ScreenRegion(
            desired_position[0],
            desired_position[1],
            self.character_size[0],
            self.character_size[1]
        )
        
        if not self._collides_with_any(char_region, occupied_regions):
            return desired_position
        
        # Find nearest safe position
        safe_pos = await self._find_nearest_safe_position(
            desired_position,
            occupied_regions,
            context
        )
        
        return safe_pos
    
    async def _get_occupied_regions(self, context: dict) -> List[ScreenRegion]:
        """Get all screen regions that should be avoided."""
        regions = []
        
        # Active windows
        for window in context.get('windows', []):
            if window.get('is_focused') or window.get('is_important'):
                regions.append(ScreenRegion(
                    window['x'],
                    window['y'],
                    window['width'],
                    window['height']
                ))
        
        # Mouse cursor area (avoid covering cursor)
        if 'cursor_position' in context:
            cx, cy = context['cursor_position']
            regions.append(ScreenRegion(
                cx - 50, cy - 50, 100, 100  # 100x100 region around cursor
            ))
        
        # Active input fields (if user is typing)
        if context.get('user_typing'):
            for input_field in context.get('input_fields', []):
                regions.append(ScreenRegion(
                    input_field['x'] - self.safe_margin,
                    input_field['y'] - self.safe_margin,
                    input_field['width'] + 2 * self.safe_margin,
                    input_field['height'] + 2 * self.safe_margin
                ))
        
        return regions
    
    def _collides_with_any(
        self,
        region: ScreenRegion,
        occupied: List[ScreenRegion]
    ) -> bool:
        """Check if region collides with any occupied region."""
        return any(region.overlaps(occ) for occ in occupied)
    
    async def _find_nearest_safe_position(
        self,
        desired: Tuple[int, int],
        occupied: List[ScreenRegion],
        context: dict
    ) -> Tuple[int, int]:
        """Find nearest safe position using spiral search."""
        dx, dy = desired
        
        # Spiral search pattern
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # Right, Down, Left, Up
        steps = 1
        direction_idx = 0
        x, y = dx, dy
        
        for _ in range(1000):  # Max iterations
            for _ in range(2):  # Two directions per step increment
                for _ in range(steps):
                    x += directions[direction_idx][0] * 10
                    y += directions[direction_idx][1] * 10
                    
                    # Check if position is valid
                    if (0 <= x < self.screen_width - self.character_size[0] and
                        0 <= y < self.screen_height - self.character_size[1]):
                        
                        test_region = ScreenRegion(
                            x, y,
                            self.character_size[0],
                            self.character_size[1]
                        )
                        
                        if not self._collides_with_any(test_region, occupied):
                            return (x, y)
                
                direction_idx = (direction_idx + 1) % 4
            
            steps += 1
        
        # Fallback: default corner position
        return await self._get_default_corner_position(context)
    
    async def _get_default_corner_position(self, context: dict) -> Tuple[int, int]:
        """Get default corner position based on settings."""
        corner = context.get('default_corner', 'top-right')
        
        if corner == 'top-left':
            return (self.safe_margin, self.safe_margin)
        elif corner == 'top-right':
            return (
                self.screen_width - self.character_size[0] - self.safe_margin,
                self.safe_margin
            )
        elif corner == 'bottom-left':
            return (
                self.safe_margin,
                self.screen_height - self.character_size[1] - self.safe_margin
            )
        else:  # bottom-right
            return (
                self.screen_width - self.character_size[0] - self.safe_margin,
                self.screen_height - self.character_size[1] - self.safe_margin
            )
    
    async def should_hide_character(self, context: dict) -> bool:
        """Determine if character should hide completely."""
        # Hide if user is in focus mode
        if context.get('focus_mode_enabled'):
            return True
        
        # Hide if user is presenting (fullscreen presentation detected)
        if context.get('presentation_mode'):
            return True
        
        # Hide if user is gaming (fullscreen game detected)
        if context.get('fullscreen_game'):
            return True
        
        # Hide if user manually hid character
        if context.get('user_hid_character'):
            return True
        
        return False
```

---

## 4. Animation States & Expressiveness

### 4.1 Animation State Machine

```
┌──────────────────────────────────────────────────────────────────────┐
│                  Character Animation State Machine                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  TIER 1: Basic States (Always Available)                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  IDLE                                                           │ │
│  │  • Default state when nothing happening                        │ │
│  │  • Subtle breathing animation                                  │ │
│  │  • Occasional blink, look around                               │ │
│  │  • Can have idle variations (idle_1, idle_2, idle_bored)       │ │
│  │                                                                 │ │
│  │  SPEAKING                                                       │ │
│  │  • Mouth moves (lip-sync with voice output)                    │ │
│  │  • Head slightly bounces                                        │ │
│  │  • Eye contact (looks at "camera"/user)                        │ │
│  │  • Hand gestures while speaking                                │ │
│  │                                                                 │ │
│  │  LISTENING                                                      │ │
│  │  • Head tilted slightly                                         │ │
│  │  • Ears perk up (if character has ears)                        │ │
│  │  • Attentive posture                                            │ │
│  │  • Occasional nod                                               │ │
│  │                                                                 │ │
│  │  THINKING                                                       │ │
│  │  • Hand on chin                                                 │ │
│  │  • Eyes look up/away                                            │ │
│  │  • Thought bubble (optional visual)                            │ │
│  │  • Subtle swaying                                               │ │
│  │                                                                 │ │
│  │  POINTING                                                       │ │
│  │  • Arm extended toward target                                   │ │
│  │  • Index finger pointing                                        │ │
│  │  • Head turned toward target                                    │ │
│  │  • Eyes looking at target                                       │ │
│  │  • Can point: left, right, up, down, diagonal                  │ │
│  │                                                                 │ │
│  │  WALKING                                                        │ │
│  │  • Legs moving animation                                        │ │
│  │  • Body bobs up and down                                        │ │
│  │  • Direction: left, right                                       │ │
│  │  • Speed variations: walk, run                                  │ │
│  │                                                                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  TIER 2: Rich Expressions (Emotional States)                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  HAPPY / JOY                                                    │ │
│  │  • Big smile                                                    │ │
│  │  • Eyes crinkled                                                │ │
│  │  • Bouncy movement                                              │ │
│  │  • May jump, clap, wave enthusiastically                        │ │
│  │  • Trigger: Task completed, user praise, good news             │ │
│  │                                                                 │ │
│  │  EXCITED                                                        │ │
│  │  • Wide eyes                                                    │ │
│  │  • Rapid movements                                              │ │
│  │  • May hop or dance                                             │ │
│  │  • Trigger: Discovered something interesting, big event        │ │
│  │                                                                 │ │
│  │  CONFUSED / PUZZLED                                             │ │
│  │  • Head tilted                                                  │ │
│  │  • Question mark above head (optional)                          │ │
│  │  • Scratching head                                              │ │
│  │  • Trigger: Unclear user request, ambiguous input              │ │
│  │                                                                 │ │
│  │  FOCUSED / DETERMINED                                           │ │
│  │  • Narrowed eyes                                                │ │
│  │  • Serious expression                                           │ │
│  │  • Minimal movement                                             │ │
│  │  • Trigger: Working on complex task, analyzing data            │ │
│  │                                                                 │ │
│  │  TIRED / EXHAUSTED                                              │ │
│  │  • Half-closed eyes                                             │ │
│  │  • Slumped posture                                              │ │
│  │  • Yawning                                                      │ │
│  │  • Trigger: Heavy processing, late night, low power            │ │
│  │                                                                 │ │
│  │  WORRIED / CONCERNED                                            │ │
│  │  • Eyebrows furrowed                                            │ │
│  │  • Slight frown                                                 │ │
│  │  • Wringing hands                                               │ │
│  │  • Trigger: Error detected, potential problem, user frustrated │ │
│  │                                                                 │ │
│  │  SURPRISED                                                      │ │
│  │  • Wide eyes                                                    │ │
│  │  • Mouth open                                                   │ │
│  │  • Jump back slightly                                           │ │
│  │  • Trigger: Unexpected event, surprising information           │ │
│  │                                                                 │ │
│  │  CELEBRATING                                                    │ │
│  │  • Arms raised                                                  │ │
│  │  • Big smile                                                    │ │
│  │  • May throw confetti (particle effect)                        │ │
│  │  • Trigger: Major milestone, goal achieved                     │ │
│  │                                                                 │ │
│  │  APOLOGETIC / SORRY                                             │ │
│  │  • Bowing slightly                                              │ │
│  │  • Sad eyes                                                     │ │
│  │  • Hands clasped                                                │ │
│  │  • Trigger: Made mistake, failed task                          │ │
│  │                                                                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  TIER 3: Activity-Aware Animations                                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  CODING ACTIVITY                                                │ │
│  │  • Character sits at tiny desk/laptop                          │ │
│  │  • Typing animation on mini keyboard                           │ │
│  │  • Occasionally looks at "monitor"                             │ │
│  │  • Matches user's coding activity                              │ │
│  │                                                                 │ │
│  │  EMAIL ACTIVITY                                                 │ │
│  │  • Reading papers/letters animation                            │ │
│  │  • Writing with pen (for composing)                            │ │
│  │  • Sorting papers (for organizing)                             │ │
│  │                                                                 │ │
│  │  GAMING ACTIVITY                                                │ │
│  │  • Holding game controller                                      │ │
│  │  • Reactive movements (lean left/right)                        │ │
│  │  • Cheering for victories                                       │ │
│  │                                                                 │ │
│  │  VIDEO CALL ACTIVITY                                            │ │
│  │  • Waving at "camera"                                           │ │
│  │  • Professional posture                                         │ │
│  │  • May hold phone/tablet                                        │ │
│  │                                                                 │ │
│  │  BROWSING ACTIVITY                                              │ │
│  │  • Reading book or magazine                                     │ │
│  │  • Turning pages                                                │ │
│  │  • Looks curious/interested                                     │ │
│  │                                                                 │ │
│  │  MEDIA WATCHING                                                 │ │
│  │  • Sitting relaxed                                              │ │
│  │  • Eating popcorn (if movie/video)                             │ │
│  │  • Reacts to content (laugh, gasp, etc.)                       │ │
│  │                                                                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  TIER 4: Personality-Driven Variations                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Animations modified by Big Five personality settings:          │ │
│  │                                                                 │ │
│  │  HIGH OPENNESS:                                                 │ │
│  │  • More creative, fluid movements                              │ │
│  │  • Tries new animations randomly                               │ │
│  │  • Expressive gestures                                          │ │
│  │                                                                 │ │
│  │  HIGH CONSCIENTIOUSNESS:                                        │ │
│  │  • Precise, controlled movements                                │ │
│  │  • Professional posture                                         │ │
│  │  • Organized desk/workspace props                              │ │
│  │                                                                 │ │
│  │  HIGH EXTRAVERSION:                                             │ │
│  │  • Energetic, bouncy animations                                │ │
│  │  • Frequent waves and greetings                                │ │
│  │  • Loves celebrating                                            │ │
│  │                                                                 │ │
│  │  LOW EXTRAVERSION (Introverted):                                │ │
│  │  • Calmer, subtler movements                                   │ │
│  │  • Prefers reading, quiet activities                           │ │
│  │  • Shy wave instead of enthusiastic                            │ │
│  │                                                                 │ │
│  │  HIGH AGREEABLENESS:                                            │ │
│  │  • Friendly, warm expressions                                  │ │
│  │  • Lots of nodding, encouraging gestures                       │ │
│  │  • Empathetic reactions                                         │ │
│  │                                                                 │ │
│  │  HIGH NEUROTICISM:                                              │ │
│  │  • More nervous movements                                       │ │
│  │  • Fidgeting when idle                                          │ │
│  │  • Anxious expressions when errors occur                       │ │
│  │                                                                 │ │
│  │  LOW NEUROTICISM (Stable):                                      │ │
│  │  • Calm, composed animations                                    │ │
│  │  • Doesn't panic on errors                                     │ │
│  │  • Steady, predictable movements                                │ │
│  │                                                                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  STATE TRANSITIONS:                                                  │
│  • Smooth blending between states (0.3-0.5s transition)             │
│  • Priority system: High-priority states interrupt low-priority     │ │
│  • Can queue animations: thinking → speaking → celebration          │
│  • Emergency states (errors) can interrupt anything                 │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 4.2 Lip-Sync System

```python
# lip_sync.py - Synchronize mouth movements with speech

import asyncio
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class Phoneme:
    """Represents a phoneme (sound unit) for lip-sync."""
    sound: str  # Phoneme symbol (IPA or custom)
    start_time: float  # Seconds
    duration: float  # Seconds
    mouth_shape: str  # Mouth shape name


class LipSyncEngine:
    """Generates lip-sync data from speech output."""
    
    # Mouth shapes (visemes) mapped to phonemes
    PHONEME_TO_MOUTH = {
        # Closed mouth
        'SIL': 'closed',  # Silence
        'M': 'closed',
        'B': 'closed',
        'P': 'closed',
        
        # Open wide
        'AA': 'open',  # "father"
        'AH': 'open',
        
        # Small open
        'IH': 'small_open',  # "bit"
        'EH': 'small_open',  # "bet"
        
        # Rounded
        'UW': 'rounded',  # "boot"
        'OW': 'rounded',  # "boat"
        
        # Wide
        'IY': 'wide',  # "beat"
        'EY': 'wide',  # "bait"
        
        # Narrow
        'F': 'narrow',  # "fan"
        'V': 'narrow',
        
        # Teeth (smile-ish)
        'TH': 'teeth',
        'DH': 'teeth',
        
        # Lip round small
        'W': 'lip_round',
        
        # Default
        'default': 'neutral',
    }
    
    async def generate_lip_sync(
        self,
        audio_path: str,
        text: str
    ) -> List[Phoneme]:
        """
        Generate lip-sync data from audio file and text.
        
        Uses:
        1. Montreal Forced Aligner (or similar) for phoneme alignment
        2. Or: Simple duration-based estimation from text
        """
        # Option 1: Use forced aligner (accurate but slower)
        # phonemes = await self._align_with_mfa(audio_path, text)
        
        # Option 2: Estimate from text (fast but less accurate)
        phonemes = await self._estimate_from_text(text)
        
        return phonemes
    
    async def _estimate_from_text(self, text: str) -> List[Phoneme]:
        """
        Estimate phoneme timing from text (no audio analysis).
        Simple but works for real-time generation.
        """
        # Average speaking rate: ~150 words per minute = 2.5 words/sec
        # Average word length: ~5 characters
        # Rough estimate: 0.08 seconds per character
        
        phonemes = []
        current_time = 0.0
        
        words = text.split()
        
        for word in words:
            # Convert word to approximate phonemes
            word_phonemes = self._text_to_phonemes(word)
            
            for phon in word_phonemes:
                mouth_shape = self.PHONEME_TO_MOUTH.get(phon, 'neutral')
                
                phonemes.append(Phoneme(
                    sound=phon,
                    start_time=current_time,
                    duration=0.08,  # ~80ms per phoneme
                    mouth_shape=mouth_shape
                ))
                
                current_time += 0.08
            
            # Add silence between words
            phonemes.append(Phoneme(
                sound='SIL',
                start_time=current_time,
                duration=0.05,  # 50ms pause
                mouth_shape='closed'
            ))
            current_time += 0.05
        
        return phonemes
    
    def _text_to_phonemes(self, word: str) -> List[str]:
        """
        Convert word to phoneme sequence.
        Simplified version; use actual phonemizer in production.
        """
        # This is a VERY simplified mapping
        # In production, use espeak-ng, g2p, or similar
        
        phoneme_map = {
            'hello': ['HH', 'EH', 'L', 'OW'],
            'world': ['W', 'ER', 'L', 'D'],
            'the': ['DH', 'AH'],
            # ... full dictionary needed
        }
        
        word_lower = word.lower()
        if word_lower in phoneme_map:
            return phoneme_map[word_lower]
        
        # Fallback: simple letter-to-phoneme
        return [letter.upper() for letter in word_lower]
    
    async def apply_lip_sync_to_animation(
        self,
        character: 'CharacterController',
        phonemes: List[Phoneme],
        start_time: float
    ):
        """
        Apply lip-sync to character animation in real-time.
        """
        for phoneme in phonemes:
            # Wait until phoneme should start
            await asyncio.sleep(phoneme.start_time - start_time)
            
            # Set mouth shape
            await character.set_mouth_shape(phoneme.mouth_shape)
            
            # Wait for phoneme duration
            await asyncio.sleep(phoneme.duration)
        
        # Return to neutral
        await character.set_mouth_shape('neutral')
```

---

## 5. Motor Control Module (Host-Side)

### 5.1 Motor Controller

```python
# motor_controller.py - Host-side animation controller

import asyncio
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AnimationCommand:
    """Command to play an animation on client."""
    animation_name: str
    priority: int  # Higher = more important
    duration: Optional[float] = None  # Auto-detect if None
    loop: bool = False
    blend_time: float = 0.3  # Transition duration


class MotorController:
    """
    Motor Control Module (Host-Side)
    
    Decides WHAT animations to play based on companion's state.
    Sends commands to client for rendering.
    
    This is analogous to motor cortex in human brain.
    """
    
    def __init__(
        self,
        client_comm: 'ClientCommunicator',
        emotion_regulator: 'EmotionRegulator',
        personality_mgr: 'PersonalityManager'
    ):
        self.client_comm = client_comm
        self.emotion_regulator = emotion_regulator
        self.personality = personality_mgr
        
        self.current_animation = 'idle'
        self.animation_queue = []
    
    async def express_emotion(self, emotion: str, intensity: float):
        """
        Express an emotion through animation.
        
        Args:
            emotion: Emotion name (happy, sad, confused, etc.)
            intensity: 0.0-1.0, affects animation intensity
        """
        # Map emotion to animation
        animation_map = {
            'joy': 'happy',
            'sadness': 'sad',
            'anger': 'frustrated',
            'fear': 'worried',
            'surprise': 'surprised',
            'disgust': 'disgusted',
            'neutral': 'idle',
        }
        
        animation = animation_map.get(emotion, 'idle')
        
        # Modify animation based on personality
        animation = await self._apply_personality_filter(animation, intensity)
        
        # Send to client
        await self._send_animation_command(AnimationCommand(
            animation_name=animation,
            priority=5,  # Medium priority
            duration=None,  # Auto-detect
            loop=False
        ))
    
    async def point_at_ui_element(
        self,
        element_x: int,
        element_y: int,
        duration: float = 2.0
    ):
        """
        Point at a UI element on screen.
        
        Args:
            element_x, element_y: Screen coordinates
            duration: How long to point (seconds)
        """
        # Calculate pointing direction
        direction = await self._calculate_pointing_direction(element_x, element_y)
        
        # Select pointing animation
        animation = f'point_{direction}'  # e.g., point_left, point_up_right
        
        # Send command
        await self._send_animation_command(AnimationCommand(
            animation_name=animation,
            priority=8,  # High priority (user-initiated)
            duration=duration,
            loop=False
        ))
        
        # Also send target coordinates for procedural pointing
        await self.client_comm.send({
            'type': 'point_at',
            'target_x': element_x,
            'target_y': element_y,
            'duration': duration
        })
    
    async def speak(self, text: str, phonemes: List['Phoneme']):
        """
        Play speaking animation with lip-sync.
        
        Args:
            text: What is being said
            phonemes: Lip-sync phoneme data
        """
        # Send speaking command with lip-sync data
        await self.client_comm.send({
            'type': 'speak',
            'text': text,
            'phonemes': [
                {
                    'sound': p.sound,
                    'start_time': p.start_time,
                    'duration': p.duration,
                    'mouth_shape': p.mouth_shape
                }
                for p in phonemes
            ]
        })
    
    async def react_to_user_activity(self, activity: str):
        """
        React to user's current activity.
        
        Args:
            activity: Activity name (coding, email, gaming, etc.)
        """
        # Activity-specific animations
        activity_animations = {
            'coding': 'typing_on_laptop',
            'email': 'reading_papers',
            'gaming': 'holding_controller',
            'video_call': 'waving',
            'browsing': 'reading_book',
            'idle': 'idle_relaxed',
        }
        
        animation = activity_animations.get(activity, 'idle')
        
        # Send command (low priority, looping)
        await self._send_animation_command(AnimationCommand(
            animation_name=animation,
            priority=2,  # Low priority (background)
            duration=None,
            loop=True  # Loop until activity changes
        ))
    
    async def celebrate(self, achievement: str):
        """
        Celebrate an achievement.
        
        Args:
            achievement: What was achieved
        """
        # Select celebration based on personality
        if self.personality.get_trait('extraversion') > 0.7:
            # Extraverted: Big celebration
            animation = 'celebrate_big'
        else:
            # Introverted: Subtle celebration
            animation = 'celebrate_small'
        
        await self._send_animation_command(AnimationCommand(
            animation_name=animation,
            priority=9,  # Very high priority
            duration=3.0,
            loop=False
        ))
        
        # Add particle effects
        await self.client_comm.send({
            'type': 'particle_effect',
            'effect': 'confetti',
            'duration': 3.0
        })
    
    async def show_thinking(self):
        """Show thinking animation."""
        await self._send_animation_command(AnimationCommand(
            animation_name='thinking',
            priority=6,
            duration=None,
            loop=True  # Loop until done thinking
        ))
    
    async def stop_thinking(self):
        """Stop thinking animation, return to idle."""
        await self._send_animation_command(AnimationCommand(
            animation_name='idle',
            priority=6,
            duration=None,
            loop=True
        ))
    
    async def _apply_personality_filter(
        self,
        animation: str,
        intensity: float
    ) -> str:
        """
        Modify animation selection based on personality.
        
        For example, introverted character might use subdued versions.
        """
        traits = self.personality.get_all_traits()
        
        # Extraversion affects animation energy
        if traits['extraversion'] < 0.3 and 'big' in animation:
            # Replace big animations with small versions
            animation = animation.replace('big', 'small')
        
        # Neuroticism affects nervous animations
        if traits['neuroticism'] > 0.7:
            # Add nervous variations
            if animation == 'idle':
                animation = 'idle_fidgeting'
        
        return animation
    
    async def _calculate_pointing_direction(
        self,
        target_x: int,
        target_y: int
    ) -> str:
        """
        Calculate pointing direction from character position to target.
        
        Returns: Direction string (left, right, up, down, up_left, etc.)
        """
        # Get character position from client
        char_pos = await self.client_comm.request({
            'type': 'get_character_position'
        })
        
        char_x = char_pos['x']
        char_y = char_pos['y']
        
        # Calculate angle
        import math
        dx = target_x - char_x
        dy = target_y - char_y
        angle = math.atan2(dy, dx)
        
        # Convert to direction
        # 0° = right, 90° = down, 180° = left, 270° = up
        degrees = math.degrees(angle)
        
        if -22.5 <= degrees < 22.5:
            return 'right'
        elif 22.5 <= degrees < 67.5:
            return 'down_right'
        elif 67.5 <= degrees < 112.5:
            return 'down'
        elif 112.5 <= degrees < 157.5:
            return 'down_left'
        elif 157.5 <= degrees or degrees < -157.5:
            return 'left'
        elif -157.5 <= degrees < -112.5:
            return 'up_left'
        elif -112.5 <= degrees < -67.5:
            return 'up'
        else:  # -67.5 <= degrees < -22.5
            return 'up_right'
    
    async def _send_animation_command(self, command: AnimationCommand):
        """Send animation command to client."""
        await self.client_comm.send({
            'type': 'play_animation',
            'animation': command.animation_name,
            'priority': command.priority,
            'duration': command.duration,
            'loop': command.loop,
            'blend_time': command.blend_time
        })
```

---

## 6. Resource Estimates

### Client Device

**Memory (Character Rendered):**
- 2D Sprite: 5-10 MB
- 2D Skeletal: 20-40 MB
- 3D Low-Poly: 50-80 MB
- Hybrid (all loaded): ~100 MB

**CPU:**
- 2D Sprite: <5% (60 FPS)
- 2D Skeletal: 5-10% (60 FPS)
- 3D Low-Poly: 10-15% (60 FPS, GPU-accelerated)

**GPU:**
- 2D: Minimal (<5%)
- 3D: ~10-15%

**Storage:**
- Character assets (one style): 50-200 MB
- All character styles: ~500 MB
- Multiple characters (10): ~2-5 GB

### Host Device (RPi5)

**Memory:**
- Motor Controller: 30 MB
- Animation command queue: 5 MB
- **Total: ~35 MB**

**CPU:**
- Deciding animations: <2%

**Bandwidth:**
- Animation commands: ~1-5 KB each
- Phoneme data: ~10-50 KB per speech
- Minimal bandwidth usage

---

## 7. Summary & Next Steps

### Design Complete ✅

**Character Animation System includes:**
1. ✅ Four character styles (2D sprite, 2D skeletal, 3D low-poly, hybrid)
2. ✅ Multiple positioning modes (corner, roaming, context-aware, dockable couch)
3. ✅ Full expressiveness (basic + emotions + activity-aware + personality-driven)
4. ✅ Smart interference avoidance
5. ✅ Lip-sync system
6. ✅ Motor control module (embodiment abstraction)
7. ✅ User-configurable everything

### Key Features

- **Maximum Flexibility:** User chooses style, positioning, expressiveness level
- **Non-Intrusive:** Smart positioning, dockable couch, hide modes
- **Expressive:** Rich emotional range, activity-aware, personality-driven
- **Performant:** Lightweight 2D options, GPU-accelerated 3D
- **Embodiment Ready:** Same API for physical robots (VLA approach)

### Integration Points

**With Central Agent:**
- Motor Controller receives commands from Central Agent
- Animations triggered by companion actions

**With Emotion Regulator:**
- Emotional state drives expression animations

**With Voice Pipeline:**
- Lip-sync synchronized with speech output

**With Screen Awareness:**
- Can point at detected UI elements

**With Personality System:**
- Big Five traits modify animation selection and style

---

**Design Status:** ✅ COMPLETE  
**Ready for:** Implementation Phase 1  
**Estimated Implementation Time:** 4-5 weeks
