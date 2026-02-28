import { useCallback, useEffect, useRef, useState } from "react";
import type { WsIncoming, WsOutgoing } from "../types";

type Status = "disconnected" | "connecting" | "connected" | "reconnecting";

const MAX_RECONNECT_DELAY = 30_000;

export function useBodhi(hostUrl: string, sessionId: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const retryCount = useRef(0);

  const [status, setStatus] = useState<Status>("disconnected");
  const [lastMessage, setLastMessage] = useState<WsIncoming | null>(null);

  const connect = useCallback(() => {
    if (!hostUrl || !sessionId) return;

    const wsUrl = hostUrl.replace(/^http/, "ws");
    const url = `${wsUrl}/ws/chat?session_id=${encodeURIComponent(sessionId)}`;

    setStatus("connecting");
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
      setStatus("reconnecting");
      const delay = Math.min(1000 * 2 ** retryCount.current, MAX_RECONNECT_DELAY);
      retryCount.current += 1;
      reconnectTimer.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [hostUrl, sessionId]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    wsRef.current?.close();
    wsRef.current = null;
    setStatus("disconnected");
  }, []);

  const send = useCallback((msg: WsOutgoing) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return { status, lastMessage, send, disconnect, reconnect: connect };
}
