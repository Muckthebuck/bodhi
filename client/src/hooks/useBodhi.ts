import { useCallback, useEffect, useRef, useState } from "react";
import type { WsIncoming, WsOutgoing } from "../types";

export type Status = "disconnected" | "connecting" | "connected" | "reconnecting";

const MAX_RETRIES = 5;
const BASE_DELAY = 2000;
const MAX_DELAY = 30_000;

/**
 * WebSocket hook with capped exponential backoff.
 * Stops retrying after MAX_RETRIES to avoid hammering an offline server.
 * Call `reconnect()` to manually retry after giving up.
 */
export function useBodhi(hostUrl: string, sessionId: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const retryCount = useRef(0);
  const intentionalClose = useRef(false);

  const [status, setStatus] = useState<Status>("disconnected");
  const [lastMessage, setLastMessage] = useState<WsIncoming | null>(null);

  const cleanup = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    if (wsRef.current) {
      intentionalClose.current = true;
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!hostUrl || !sessionId) {
      setStatus("disconnected");
      return;
    }

    // Clean up any existing connection
    cleanup();
    intentionalClose.current = false;
    retryCount.current = 0;

    const wsUrl = hostUrl.replace(/^http/, "ws");
    const url = `${wsUrl}/ws/chat?session_id=${encodeURIComponent(sessionId)}`;

    const attemptConnect = () => {
      setStatus(retryCount.current === 0 ? "connecting" : "reconnecting");

      const ws = new WebSocket(url);

      ws.onopen = () => {
        setStatus("connected");
        retryCount.current = 0;
      };

      ws.onmessage = (evt) => {
        try {
          const msg: WsIncoming = JSON.parse(evt.data);
          setLastMessage(msg);
        } catch {
          // ignore non-JSON
        }
      };

      ws.onclose = () => {
        if (intentionalClose.current) {
          setStatus("disconnected");
          return;
        }

        // Capped retries — don't hammer an offline server
        if (retryCount.current < MAX_RETRIES) {
          const delay = Math.min(BASE_DELAY * 2 ** retryCount.current, MAX_DELAY);
          retryCount.current += 1;
          setStatus("reconnecting");
          reconnectTimer.current = setTimeout(attemptConnect, delay);
        } else {
          setStatus("disconnected");
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    };

    attemptConnect();
  }, [hostUrl, sessionId, cleanup]);

  const disconnect = useCallback(() => {
    cleanup();
    setStatus("disconnected");
  }, [cleanup]);

  const send = useCallback((msg: WsOutgoing) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  // Connect when hostUrl/sessionId change (if non-empty)
  useEffect(() => {
    if (hostUrl && sessionId) {
      connect();
    }
    return () => cleanup();
  }, [hostUrl, sessionId, connect, cleanup]);

  return { status, lastMessage, send, disconnect, reconnect: connect };
}
