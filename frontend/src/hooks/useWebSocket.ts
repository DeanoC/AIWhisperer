import { useEffect, useRef, useState, useCallback } from 'react';

export type WebSocketStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export function useWebSocket(url: string, options?: { reconnect?: boolean; reconnectIntervalMs?: number }) {
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnect = options?.reconnect ?? true;
  const reconnectIntervalMs = options?.reconnectIntervalMs ?? 2000;
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }
    setStatus('connecting');
    wsRef.current = new WebSocket(url);
    wsRef.current.onopen = () => {
      setStatus('connected');
      reconnectAttempts.current = 0;
    };
    wsRef.current.onclose = () => {
      setStatus('disconnected');
      if (reconnect) {
        reconnectTimeout.current = setTimeout(() => {
          reconnectAttempts.current++;
          connect();
        }, reconnectIntervalMs);
      }
    };
    wsRef.current.onerror = () => {
      setStatus('error');
    };
  }, [url, reconnect, reconnectIntervalMs]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
    };
  }, [connect]);

  return { ws: wsRef.current, status, connect };
}
