import { useState } from "react";
import type { CharacterConfig } from "../character/types";
import { DynamicCharacter } from "../character/DynamicCharacter";
import type { Status } from "../hooks/useBodhi";
import type { ThemeMode } from "../hooks/useTheme";
import { CustomSelect } from "./CustomSelect";
import {
  IconConnection,
  IconCharacter,
  IconPalette,
  IconInfo,
  IconArrowLeft,
  IconSettings,
  IconPlus,
  IconEdit,
  IconTrash,
  IconCheck,
  IconChevronDown,
} from "./Icons";
import "../styles/settings.css";

export type CharacterStyle = "sprite" | "skeletal";
export type CharacterSize = "small" | "medium" | "large";
export type CharacterPosition = "bottom-right" | "bottom-left" | "top-right" | "top-left";

export interface AppSettings {
  characterStyle: CharacterStyle;
  characterSize: CharacterSize;
  characterPosition: CharacterPosition;
  showCharacter: boolean;
}

const SETTINGS_KEY = "bodhi-settings";

export function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) return { ...defaultSettings(), ...JSON.parse(raw) };
  } catch { /* ignore */ }
  return defaultSettings();
}

export function saveSettings(settings: AppSettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

function defaultSettings(): AppSettings {
  return {
    characterStyle: "sprite",
    characterSize: "medium",
    characterPosition: "bottom-right",
    showCharacter: false,
  };
}

/* ── Navigation ── */

type Tab = "connection" | "character" | "appearance" | "about";

interface NavItem {
  id: Tab;
  label: string;
  icon: React.ComponentType<{ size?: number }>;
}

const NAV_ITEMS: NavItem[] = [
  { id: "connection",  label: "Connection",  icon: IconConnection },
  { id: "character",   label: "Characters",  icon: IconCharacter },
  { id: "appearance",  label: "Appearance",  icon: IconPalette },
  { id: "about",       label: "About",       icon: IconInfo },
];

/* ── Theme swatch config ── */

const THEME_SWATCHES: { id: ThemeMode; label: string; left: string; right: string }[] = [
  { id: "light",    label: "Light",    left: "#f5f5f7", right: "#ffffff" },
  { id: "beige",    label: "Beige",    left: "#f5f0e8", right: "#faf6ef" },
  { id: "midnight", label: "Midnight", left: "#1a1a2e", right: "#16213e" },
  { id: "charcoal", label: "Charcoal", left: "#1e1e1e", right: "#252526" },
];

/* ── Props ── */

interface Props {
  settings: AppSettings;
  onUpdate: (settings: AppSettings) => void;
  onClose: () => void;
  characters: CharacterConfig[];
  activeCharacterId: string;
  onEditCharacter: (char?: CharacterConfig) => void;
  onNewCharacter: () => void;
  onSwitchCharacter: (id: string) => void;
  onDeleteCharacter?: (id: string) => void;
  // Connection
  hostUrl: string;
  sessionId: string;
  connectionStatus: Status;
  onConnectionChange: (hostUrl: string, sessionId: string) => void;
  onReconnect: () => void;
  onDisconnect: () => void;
  // Theme
  theme: ThemeMode;
  onThemeChange: (mode: ThemeMode) => void;
}

export function SettingsPanel({
  settings,
  onUpdate,
  onClose,
  characters,
  activeCharacterId,
  onEditCharacter,
  onNewCharacter,
  onSwitchCharacter,
  onDeleteCharacter,
  hostUrl: initialHost,
  sessionId: initialSession,
  connectionStatus,
  onConnectionChange,
  onDisconnect,
  theme,
  onThemeChange,
}: Props) {
  const [tab, setTab] = useState<Tab>("connection");
  const [local, setLocal] = useState<AppSettings>(settings);
  const [hostUrl, setHostUrl] = useState(initialHost);
  const [sessionId, setSessionId] = useState(initialSession);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const updateSetting = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    const next = { ...local, [key]: value };
    setLocal(next);
    saveSettings(next);
    onUpdate(next);
  };

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const resp = await fetch(`${hostUrl}/health`, { signal: AbortSignal.timeout(3000) });
      setTestResult(resp.ok ? "Server reachable" : `HTTP ${resp.status}`);
    } catch {
      setTestResult("Server unreachable");
    } finally {
      setTesting(false);
    }
  };

  const applyConnection = () => {
    onConnectionChange(hostUrl, sessionId);
  };

  const statusColor =
    connectionStatus === "connected" ? "var(--status-ok)"
    : connectionStatus === "reconnecting" || connectionStatus === "connecting" ? "var(--status-warn)"
    : "var(--text-muted)";

  return (
    <div className="settings-page">
      {/* ── Sidebar ── */}
      <aside className="settings-sidebar">
        <div className="settings-sidebar-header">
          <IconSettings size={18} />
          <h2>Settings</h2>
        </div>

        <nav className="settings-nav">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={`settings-nav-item${tab === item.id ? " active" : ""}`}
                onClick={() => setTab(item.id)}
              >
                <Icon size={18} />
                {item.label}
                {item.id === "connection" && (
                  <span className="nav-badge" style={{ background: statusColor }} />
                )}
              </button>
            );
          })}
        </nav>

        <div className="settings-sidebar-footer">
          <button className="settings-back-btn" onClick={onClose}>
            <IconArrowLeft size={16} />
            Back to Chat
          </button>
        </div>
      </aside>

      {/* ── Content ── */}
      <main className="settings-content">
        <div className="settings-content-inner">
          {tab === "connection" && (
            <ConnectionTab
              hostUrl={hostUrl}
              sessionId={sessionId}
              connectionStatus={connectionStatus}
              statusColor={statusColor}
              testing={testing}
              testResult={testResult}
              onHostChange={setHostUrl}
              onSessionChange={setSessionId}
              onTest={testConnection}
              onApply={applyConnection}
              onDisconnect={onDisconnect}
            />
          )}
          {tab === "character" && (
            <CharacterTab
              characters={characters}
              activeCharacterId={activeCharacterId}
              onSwitchCharacter={onSwitchCharacter}
              onEditCharacter={onEditCharacter}
              onNewCharacter={onNewCharacter}
              onDeleteCharacter={onDeleteCharacter}
              settings={local}
              updateSetting={updateSetting}
            />
          )}
          {tab === "appearance" && (
            <AppearanceTab theme={theme} onThemeChange={onThemeChange} />
          )}
          {tab === "about" && <AboutTab />}
        </div>
      </main>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   Tab components
   ═══════════════════════════════════════════════════════ */

function ConnectionTab({
  hostUrl, sessionId, connectionStatus, statusColor, testing, testResult,
  onHostChange, onSessionChange, onTest, onApply, onDisconnect,
}: {
  hostUrl: string; sessionId: string; connectionStatus: Status; statusColor: string;
  testing: boolean; testResult: string | null;
  onHostChange: (v: string) => void; onSessionChange: (v: string) => void;
  onTest: () => void; onApply: () => void; onDisconnect: () => void;
}) {
  return (
    <>
      <h2 className="settings-section-title">Connection</h2>
      <p className="settings-section-desc">
        Configure the Bodhi server endpoint and session identifier.
      </p>

      <div className="settings-card">
        <h4>Status</h4>
        <div className="settings-status-row">
          <span className="settings-status-dot" style={{ background: statusColor }} />
          <span style={{ textTransform: "capitalize" }}>{connectionStatus}</span>
        </div>
      </div>

      <div className="settings-card">
        <h4>Server</h4>
        <div className="settings-field">
          <label className="settings-label">Host URL</label>
          <input
            className="settings-input"
            value={hostUrl}
            onChange={(e) => onHostChange(e.target.value)}
            placeholder="http://localhost:8000"
          />
        </div>
        <div className="settings-field">
          <label className="settings-label">Session ID</label>
          <input
            className="settings-input"
            value={sessionId}
            onChange={(e) => onSessionChange(e.target.value.replace(/[^a-zA-Z0-9_-]/g, ""))}
            placeholder="default"
          />
        </div>

        <div className="settings-btn-row" style={{ marginTop: 8 }}>
          <button className="settings-btn-secondary" onClick={onTest} disabled={testing || !hostUrl}>
            {testing ? "Testing…" : "Test Connection"}
          </button>
          <button
            className="settings-btn-primary"
            onClick={onApply}
            disabled={!hostUrl || !sessionId}
          >
            {connectionStatus === "connected" ? "Reconnect" : "Connect"}
          </button>
          {connectionStatus === "connected" && (
            <button className="settings-btn-danger" onClick={onDisconnect}>Disconnect</button>
          )}
        </div>

        {testResult && (
          <div className="settings-test-result">
            <span style={{ color: testResult.includes("reachable") ? "var(--status-ok)" : "var(--status-error)" }}>
              {testResult}
            </span>
          </div>
        )}
      </div>
    </>
  );
}

/* ── Character inventory ── */

function CharacterTab({
  characters, activeCharacterId, onSwitchCharacter,
  onEditCharacter, onNewCharacter, onDeleteCharacter,
  settings: local, updateSetting,
}: {
  characters: CharacterConfig[]; activeCharacterId: string;
  onSwitchCharacter: (id: string) => void;
  onEditCharacter: (char?: CharacterConfig) => void;
  onNewCharacter: () => void;
  onDeleteCharacter?: (id: string) => void;
  settings: AppSettings;
  updateSetting: <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => void;
}) {
  const [showDisplay, setShowDisplay] = useState(false);

  return (
    <>
      <h2 className="settings-section-title">Characters</h2>
      <p className="settings-section-desc">
        Manage your companion characters. Click to select, hover for actions.
      </p>

      <div className="char-inventory">
        {characters.map((char) => {
          const isActive = char.id === activeCharacterId;
          return (
            <button
              key={char.id}
              className={`char-card${isActive ? " active" : ""}`}
              onClick={() => onSwitchCharacter(char.id)}
              aria-label={`Select ${char.name}${isActive ? " (active)" : ""}`}
            >
              {isActive && <span className="char-card-badge">Active</span>}
              <div className="char-card-avatar">
                <DynamicCharacter
                  config={char}
                  emotion={{ valence: 0, arousal: 0, label: "neutral" }}
                  action="idle"
                  size={48}
                />
              </div>
              <span className="char-card-name">{char.name}</span>
              <div className="char-card-actions">
                <button
                  className="settings-icon-btn"
                  title="Edit"
                  aria-label={`Edit ${char.name}`}
                  onClick={(e) => { e.stopPropagation(); onEditCharacter(char); }}
                >
                  <IconEdit size={14} />
                </button>
                {!isActive && onDeleteCharacter && characters.length > 1 && (
                  <button
                    className="settings-icon-btn danger"
                    title="Delete"
                    aria-label={`Delete ${char.name}`}
                    onClick={(e) => { e.stopPropagation(); onDeleteCharacter(char.id); }}
                  >
                    <IconTrash size={14} />
                  </button>
                )}
              </div>
            </button>
          );
        })}

        <button className="char-card-add" onClick={onNewCharacter}>
          <IconPlus size={24} />
          <span>New Character</span>
        </button>
      </div>

      {/* ── Display options (collapsible) ── */}
      <button
        className={`settings-collapse-toggle${showDisplay ? " open" : ""}`}
        onClick={() => setShowDisplay(!showDisplay)}
        aria-expanded={showDisplay}
      >
        <span>Display Options</span>
        <IconChevronDown size={16} />
      </button>

      {showDisplay && (
        <div className="settings-card" style={{ marginTop: 0, borderTopLeftRadius: 0, borderTopRightRadius: 0 }}>
          <div className="settings-field">
            <label className="settings-label">Render Style</label>
            <CustomSelect
              value={local.characterStyle}
              options={[
                { value: "sprite", label: "2D Sprite" },
                { value: "skeletal", label: "2D Skeletal (Lottie)" },
              ]}
              onChange={(v) => updateSetting("characterStyle", v as CharacterStyle)}
              ariaLabel="Render Style"
            />
          </div>
          <div className="settings-field">
            <label className="settings-label">Character Size</label>
            <CustomSelect
              value={local.characterSize}
              options={[
                { value: "small", label: "Small (64 px)" },
                { value: "medium", label: "Medium (128 px)" },
                { value: "large", label: "Large (192 px)" },
              ]}
              onChange={(v) => updateSetting("characterSize", v as CharacterSize)}
              ariaLabel="Character Size"
            />
          </div>
          <label className="settings-checkbox">
            <input
              type="checkbox"
              checked={local.showCharacter}
              onChange={(e) => updateSetting("showCharacter", e.target.checked)}
            />
            Show character in sidebar
          </label>
        </div>
      )}
    </>
  );
}

/* ── Appearance (theme picker) ── */

function AppearanceTab({
  theme, onThemeChange,
}: {
  theme: ThemeMode; onThemeChange: (m: ThemeMode) => void;
}) {
  return (
    <>
      <h2 className="settings-section-title">Appearance</h2>
      <p className="settings-section-desc">
        Choose a colour mode for the interface.
      </p>

      <div className="settings-card">
        <h4>Colour Mode</h4>
        <div className="theme-picker">
          {THEME_SWATCHES.map((s) => (
            <button
              key={s.id}
              className={`theme-swatch${theme === s.id ? " active" : ""}`}
              onClick={() => onThemeChange(s.id)}
              aria-label={`${s.label} theme${theme === s.id ? " (active)" : ""}`}
            >
              <div className="theme-swatch-preview">
                <div className="swatch-half" style={{ background: s.left }} />
                <div className="swatch-half" style={{ background: s.right }} />
              </div>
              <span className="theme-swatch-label">{s.label}</span>
              {theme === s.id && <IconCheck size={14} style={{ color: "var(--accent-bright)" }} />}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}

/* ── About ── */

function AboutTab() {
  return (
    <>
      <h2 className="settings-section-title">About</h2>
      <div className="settings-card">
        <div className="settings-about">
          <div className="settings-about-row">
            <span>Application</span>
            <strong>Bodhi Companion</strong>
          </div>
          <div className="settings-about-row">
            <span>Version</span>
            <strong>0.1.0</strong>
          </div>
          <div className="settings-about-row">
            <span>Framework</span>
            <strong>Tauri v2 + React 19</strong>
          </div>
          <div className="settings-about-row">
            <span>Character System</span>
            <strong>SVG sprite with lerp animation</strong>
          </div>
        </div>
      </div>
    </>
  );
}
