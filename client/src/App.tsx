import { useCallback, useEffect, useState } from "react";
import { emit } from "@tauri-apps/api/event";
import { ChatView } from "./components/ChatView";
import { ConnectionSetup } from "./components/ConnectionSetup";
import { SessionPanel } from "./components/SessionPanel";
import { SettingsPanel, loadSettings, type AppSettings } from "./components/SettingsPanel";
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
import type { AnimationAction, ChatMessage, EmotionState, WsIncoming } from "./types";

const STORAGE_KEY = "bodhi-connection";

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

const SIZE_MAP = { small: 64, medium: 128, large: 192 } as const;

export default function App() {
  const [config, setConfig] = useState(loadConfig);
  const [connected, setConnected] = useState(false);
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

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [emotion, setEmotion] = useState<EmotionState>({
    valence: 0,
    arousal: 0,
    label: "neutral",
  });
  const [animation, setAnimation] = useState<AnimationAction>("idle");

  const { status, lastMessage, send } = useBodhi(
    connected ? config.hostUrl : "",
    connected ? config.sessionId : "",
  );

  const handleConnect = useCallback((hostUrl: string, sessionId: string) => {
    saveConfig(hostUrl, sessionId);
    setConfig({ hostUrl, sessionId });
    setConnected(true);
    setMessages([]);
  }, []);

  const handleSessionSwitch = useCallback(
    (newSessionId: string) => {
      saveConfig(config.hostUrl, newSessionId);
      setConfig((prev) => ({ ...prev, sessionId: newSessionId }));
      setMessages([]);
    },
    [config.hostUrl],
  );

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
    }).catch(() => { /* overlay window may not exist yet */ });
  }, [emotion, animation, settings.characterStyle, settings.characterSize, activeChar]);

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
  const handleEditCharacter = () => {
    setEditingCharacter({ ...activeChar });
    setIsCreatingNew(false);
  };

  const handleNewCharacter = () => {
    setEditingCharacter(createDefaultCharacter());
    setIsCreatingNew(true);
  };

  const handleSaveCharacter = (char: CharacterConfig) => {
    let newChars: CharacterConfig[];
    if (isCreatingNew) {
      newChars = [...characters, char];
    } else {
      newChars = characters.map((c) => (c.id === char.id ? char : c));
    }
    saveCharacters(newChars);
    setActiveCharacterId(char.id);
    setCharacters(newChars);
    setActiveCharId(char.id);
    setEditingCharacter(null);
    setIsCreatingNew(false);
  };

  const handleSwitchCharacter = (id: string) => {
    setActiveCharacterId(id);
    setActiveCharId(id);
  };

  if (!connected) {
    return <ConnectionSetup initial={config} onSave={handleConnect} />;
  }

  const charSize = SIZE_MAP[settings.characterSize];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <StatusBar
        emotion={emotion}
        status={status}
        onSettingsClick={() => setShowSettings((v) => !v)}
      />
      <SessionPanel currentSession={config.sessionId} onSwitch={handleSessionSwitch} />
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
        />
      )}
      {editingCharacter && (
        <div style={{ position: "fixed", inset: 0, zIndex: 200, background: "var(--bg)" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
            <h2 style={{ margin: 0, fontSize: 18 }}>
              {isCreatingNew ? "Create New Character" : "Edit Character"}
            </h2>
          </div>
          <div style={{ height: "calc(100vh - 60px)", overflow: "hidden" }}>
            <CharacterCreator
              initial={editingCharacter}
              onSave={handleSaveCharacter}
              onCancel={() => { setEditingCharacter(null); setIsCreatingNew(false); }}
              saveLabel={isCreatingNew ? "Create Character" : "Save Changes"}
            />
          </div>
        </div>
      )}
    </div>
  );
}
