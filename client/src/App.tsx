import { useCallback, useEffect, useState } from "react";
import { emit } from "@tauri-apps/api/event";
import { ChatView } from "./components/ChatView";
import { SessionPanel } from "./components/SessionPanel";
import { SettingsPanel, loadSettings, saveSettings, type AppSettings } from "./components/SettingsPanel";
import { SkeletalCharacter } from "./components/SkeletalCharacter";
import { StatusBar } from "./components/StatusBar";
import { Onboarding } from "./components/Onboarding";
import { CharacterCreator } from "./components/CharacterCreator";
import { DynamicCharacter } from "./character/DynamicCharacter";
import {
  isOnboarded,
  setOnboarded,
  loadCharacters,
  saveCharacters,
  setActiveCharacterId,
  createDefaultCharacter,
  getActiveCharacterId as loadActiveCharId,
  type CharacterConfig,
} from "./character/types";
import { useBodhi } from "./hooks/useBodhi";
import { useTheme } from "./hooks/useTheme";
import type { AnimationAction, ChatMessage, EmotionState, WsIncoming } from "./types";

const STORAGE_KEY = "bodhi-connection";
const MESSAGES_KEY_PREFIX = "bodhi-messages-";
const MAX_STORED_MESSAGES = 500;

function loadConfig() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as { hostUrl: string; sessionId: string };
  } catch { /* ignore */ }
  return { hostUrl: "http://localhost:8000", sessionId: "default" };
}

function saveConfig(hostUrl: string, sessionId: string) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ hostUrl, sessionId }));
}

function loadMessages(sessionId: string): ChatMessage[] {
  try {
    const raw = localStorage.getItem(MESSAGES_KEY_PREFIX + sessionId);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  return [];
}

function saveMessages(sessionId: string, messages: ChatMessage[]) {
  const capped = messages.slice(-MAX_STORED_MESSAGES);
  localStorage.setItem(MESSAGES_KEY_PREFIX + sessionId, JSON.stringify(capped));
}

export function clearMessages(sessionId: string) {
  localStorage.removeItem(MESSAGES_KEY_PREFIX + sessionId);
}

const SIZE_MAP = { small: 64, medium: 128, large: 192 } as const;

export default function App() {
  const { theme, setTheme } = useTheme();
  const [config, setConfig] = useState(loadConfig);
  const [settings, setSettings] = useState<AppSettings>(loadSettings);
  const [showSettings, setShowSettings] = useState(false);

  // Character customization state
  const [onboarded, setOnboardedState] = useState(isOnboarded());
  const [characters, setCharacters] = useState<CharacterConfig[]>(loadCharacters);
  const [activeCharId, setActiveCharId] = useState<string | null>(() => {
    return loadActiveCharId();
  });
  const [editingCharacter, setEditingCharacter] = useState<CharacterConfig | null>(null);
  const [isCreatingNew, setIsCreatingNew] = useState(false);

  const activeChar =
    characters.find((c) => c.id === activeCharId) || characters[0] || createDefaultCharacter();

  const [messages, setMessages] = useState<ChatMessage[]>(() => loadMessages(config.sessionId));
  const [emotion, setEmotion] = useState<EmotionState>({
    valence: 0,
    arousal: 0,
    label: "neutral",
  });
  const [animation, setAnimation] = useState<AnimationAction>("idle");

  // Persist messages to localStorage whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      saveMessages(config.sessionId, messages);
    }
  }, [messages, config.sessionId]);

  // Always connect — no more gate screen
  const { status, lastMessage, send, disconnect, reconnect } = useBodhi(
    config.hostUrl,
    config.sessionId,
  );

  const handleConnectionChange = useCallback((hostUrl: string, sessionId: string) => {
    saveConfig(hostUrl, sessionId);
    setConfig({ hostUrl, sessionId });
    setMessages(loadMessages(sessionId));
  }, []);

  const handleSessionSwitch = useCallback((sessionId: string) => {
    saveConfig(config.hostUrl, sessionId);
    setConfig((prev) => ({ ...prev, sessionId }));
    setMessages(loadMessages(sessionId));
  }, [config.hostUrl]);

  const handleSessionDelete = useCallback((sessionId: string) => {
    clearMessages(sessionId);
  }, []);

  // Process incoming WS messages
  useEffect(() => {
    if (!lastMessage) return;
    const msg: WsIncoming = lastMessage;

    switch (msg.type) {
      case "response.text":
        setMessages((prev) => [
          ...prev,
          {
            id: msg.request_id + "-resp",
            role: "companion",
            text: msg.text,
            timestamp: Date.now(),
          },
        ]);
        break;
      case "emotion.update":
        setEmotion({ valence: msg.valence, arousal: msg.arousal, label: msg.label });
        break;
      case "animation.command":
        setAnimation(msg.action);
        break;
      case "error":
        setMessages((prev) => [
          ...prev,
          {
            id: (msg.request_id || "err") + "-" + Date.now(),
            role: "system",
            text: `Error: ${msg.detail}`,
            timestamp: Date.now(),
          },
        ]);
        break;
    }
  }, [lastMessage]);

  const handleSend = useCallback(
    (outgoing: { type: "user.message"; text: string; request_id: string }) => {
      setMessages((prev) => [
        ...prev,
        {
          id: outgoing.request_id,
          role: "user",
          text: outgoing.text,
          timestamp: Date.now(),
        },
      ]);
      send(outgoing);
    },
    [send],
  );

  // Emit overlay state to the overlay window via Tauri events
  useEffect(() => {
    emit("overlay-update", {
      emotion,
      action: animation,
      style: settings.characterStyle,
      size: SIZE_MAP[settings.characterSize],
      character: activeChar,
      visible: settings.showCharacter,
    }).catch(() => { /* overlay window may not exist yet */ });
  }, [emotion, animation, settings.characterStyle, settings.characterSize, activeChar, settings.showCharacter]);

  // ─── Onboarding ──────────────────────────────────────────
  const handleOnboardingComplete = useCallback((char: CharacterConfig) => {
    const newChars = [char];
    saveCharacters(newChars);
    setActiveCharacterId(char.id);
    setCharacters(newChars);
    setActiveCharId(char.id);
    setOnboarded();
    setOnboardedState(true);
  }, []);

  if (!onboarded) {
    return <Onboarding onComplete={handleOnboardingComplete} />;
  }

  // ─── Character editing ───────────────────────────────────
  const handleEditCharacter = (char?: CharacterConfig) => {
    setEditingCharacter({ ...(char || activeChar) });
    setIsCreatingNew(false);
  };

  const handleNewCharacter = () => {
    setEditingCharacter(createDefaultCharacter());
    setIsCreatingNew(true);
  };

  const handleSaveCharacter = (char: CharacterConfig) => {
    // Auto-increment duplicate names: find lowest available name
    const otherChars = isCreatingNew ? characters : characters.filter((c) => c.id !== char.id);
    const existingNames = new Set(otherChars.map((c) => c.name));
    let finalName = char.name;
    if (existingNames.has(finalName)) {
      // Try "Name 2", "Name 3", ... find the first gap
      for (let i = 2; ; i++) {
        const candidate = `${char.name} ${i}`;
        if (!existingNames.has(candidate)) {
          finalName = candidate;
          break;
        }
      }
    }
    const finalChar = { ...char, name: finalName };

    let newChars: CharacterConfig[];
    if (isCreatingNew) {
      newChars = [...characters, finalChar];
    } else {
      newChars = characters.map((c) => (c.id === finalChar.id ? finalChar : c));
    }
    saveCharacters(newChars);
    setActiveCharacterId(finalChar.id);
    setCharacters(newChars);
    setActiveCharId(finalChar.id);
    setEditingCharacter(null);
    setIsCreatingNew(false);
  };

  const handleDeleteCharacter = (id: string) => {
    if (characters.length <= 1) return;
    const newChars = characters.filter((c) => c.id !== id);
    saveCharacters(newChars);
    setCharacters(newChars);
    if (activeCharId === id) {
      const next = newChars[0];
      setActiveCharacterId(next.id);
      setActiveCharId(next.id);
    }
  };

  const handleSwitchCharacter = (id: string) => {
    setActiveCharacterId(id);
    setActiveCharId(id);
  };

  const charSize = SIZE_MAP[settings.characterSize];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <StatusBar
        emotion={emotion}
        status={status}
        onSettingsClick={() => setShowSettings(true)}
        characters={characters}
        activeCharacterId={activeChar.id}
        showCharacter={settings.showCharacter}
        onToggleCharacter={() => {
          const next = { ...settings, showCharacter: !settings.showCharacter };
          setSettings(next);
          saveSettings(next);
        }}
        onSwitchCharacter={handleSwitchCharacter}
      />
      <SessionPanel
        currentSession={config.sessionId}
        onSwitch={handleSessionSwitch}
        onDelete={handleSessionDelete}
      />
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <div style={{ flex: 1 }}>
          <ChatView
            messages={messages}
            onSend={handleSend}
            isConnected={status === "connected"}
            isThinking={animation === "thinking"}
          />
        </div>
        {settings.showCharacter && (
          <div
            style={{
              width: charSize + 32,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              borderLeft: "1px solid var(--border)",
              background: "var(--bg-secondary)",
            }}
          >
            {settings.characterStyle === "skeletal" ? (
              <SkeletalCharacter emotion={emotion} action={animation} size={charSize} />
            ) : (
              <DynamicCharacter config={activeChar} emotion={emotion} action={animation} size={charSize} />
            )}
          </div>
        )}
      </div>
      {showSettings && (
        <SettingsPanel
          settings={settings}
          onUpdate={setSettings}
          onClose={() => setShowSettings(false)}
          characters={characters}
          activeCharacterId={activeChar.id}
          onEditCharacter={handleEditCharacter}
          onNewCharacter={handleNewCharacter}
          onSwitchCharacter={handleSwitchCharacter}
          onDeleteCharacter={handleDeleteCharacter}
          hostUrl={config.hostUrl}
          sessionId={config.sessionId}
          connectionStatus={status}
          onConnectionChange={handleConnectionChange}
          onReconnect={reconnect}
          onDisconnect={disconnect}
          theme={theme}
          onThemeChange={setTheme}
        />
      )}
      {editingCharacter && (
        <div style={{ position: "fixed", inset: 0, zIndex: 200, background: "var(--bg)" }}>
          <div style={{ padding: "14px 24px 12px", borderBottom: "1px solid var(--border)", background: "var(--bg-secondary)" }}>
            <h2 style={{ margin: 0, fontSize: 17, fontWeight: 600, color: "var(--text)" }}>
              {isCreatingNew ? "Create New Character" : "Edit Character"}
            </h2>
          </div>
          <div style={{ height: "calc(100vh - 52px)", overflow: "hidden" }}>
            <CharacterCreator
              initial={editingCharacter}
              onSave={handleSaveCharacter}
              onCancel={() => { setEditingCharacter(null); setIsCreatingNew(false); }}
              saveLabel={isCreatingNew ? "Create" : "Save Changes"}
              useAppTheme
            />
          </div>
        </div>
      )}
    </div>
  );
}
