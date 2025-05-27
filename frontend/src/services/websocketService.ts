// WebSocketService: manages connection, events, reconnection, and state

export type WebSocketEvent = 'open' | 'close' | 'error' | 'message';

export interface WebSocketServiceOptions {
  url: string;
  onEvent?: (event: WebSocketEvent, eventObj: Event | MessageEvent | CloseEvent | Event) => void;
  reconnect?: boolean;
  reconnectIntervalMs?: number;
  maxReconnectAttempts?: number;
}

export class WebSocketService {
  private url: string;
  private ws: WebSocket | null = null;
  private reconnect: boolean;
  private reconnectIntervalMs: number;
  private maxReconnectAttempts: number;
  private reconnectAttempts = 0;
  private onEvent?: (event: WebSocketEvent, eventObj: Event | MessageEvent | CloseEvent | Event) => void;
  private connectionState: 'disconnected' | 'connecting' | 'connected' = 'disconnected';

  constructor(options: WebSocketServiceOptions) {
    this.url = options.url;
    this.onEvent = options.onEvent;
    this.reconnect = options.reconnect ?? true;
    this.reconnectIntervalMs = options.reconnectIntervalMs ?? 2000;
    this.maxReconnectAttempts = options.maxReconnectAttempts ?? 10;
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }
    this.connectionState = 'connecting';
    this.ws = new WebSocket(this.url);
    this.ws.onopen = (e) => {
      this.connectionState = 'connected';
      this.reconnectAttempts = 0;
      this.onEvent?.('open', e);
    };
    this.ws.onclose = (e) => {
      this.connectionState = 'disconnected';
      this.onEvent?.('close', e);
      if (this.reconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, this.reconnectIntervalMs);
      }
    };
    this.ws.onerror = (e) => {
      this.onEvent?.('error', e);
    };
    this.ws.onmessage = (e) => {
      this.onEvent?.('message', e);
    };
  }

  disconnect() {
    this.reconnect = false;
    this.ws?.close();
    this.ws = null;
    this.connectionState = 'disconnected';
  }

  send(data: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    } else {
      throw new Error('WebSocket is not open');
    }
  }

  getState() {
    return this.connectionState;
  }
}
