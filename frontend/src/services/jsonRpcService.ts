// JSON-RPC Service: manages request/response, notifications, timeouts, and errors over WebSocket
import { JsonRpcRequest, JsonRpcResponse, JsonRpcNotification } from '../types/jsonRpc';

export type JsonRpcHandler = (response: JsonRpcResponse) => void;
export type JsonRpcNotificationHandler = (notification: JsonRpcNotification) => void;

interface PendingRequest {
  resolve: (result: any) => void;
  reject: (error: any) => void;
  timeoutId: NodeJS.Timeout;
}

export class JsonRpcService {
  private ws: WebSocket;
  private requestId = 0;
  private pending: Map<string | number, PendingRequest> = new Map();
  private notificationHandler?: JsonRpcNotificationHandler;
  private timeoutMs: number;

  constructor(ws: WebSocket, timeoutMs = 10000) {
    this.ws = ws;
    this.timeoutMs = timeoutMs;
    this.ws.onmessage = (e) => this.handleMessage(e);
  }

  setNotificationHandler(handler: JsonRpcNotificationHandler) {
    this.notificationHandler = handler;
  }

  sendRequest(method: string, params?: any): Promise<any> {
    const id = ++this.requestId;
    const request: JsonRpcRequest = {
      jsonrpc: '2.0',
      method,
      params,
      id,
    };
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error('JSON-RPC request timeout'));
      }, this.timeoutMs);
      this.pending.set(id, { resolve, reject, timeoutId });
      this.ws.send(JSON.stringify(request));
    });
  }

  private handleMessage(e: MessageEvent) {
    let msg: any;
    try {
      msg = JSON.parse(e.data);
    } catch {
      return;
    }
    if (msg.method && !msg.id) {
      // Notification
      this.notificationHandler?.(msg);
    } else if (msg.id) {
      // Response
      const pending = this.pending.get(msg.id);
      if (pending) {
        clearTimeout(pending.timeoutId);
        this.pending.delete(msg.id);
        if (msg.error) {
          pending.reject(msg.error);
        } else {
          pending.resolve(msg.result);
        }
      }
    }
  }
}
