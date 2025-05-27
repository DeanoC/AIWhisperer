import { WebSocketService } from './websocketService';
import { JsonRpcService } from './jsonRpcService';

describe('Integration: WebSocketService + JsonRpcService', () => {
  let wsBackup: any;
  let mockWebSocket: any;
  let events: any[];

  beforeAll(() => {
    wsBackup = global.WebSocket;
    mockWebSocket = class {
      static OPEN = 1;
      static CONNECTING = 0;
      readyState = 0;
      onopen: any;
      onclose: any;
      onerror: any;
      onmessage: any;
      send: any;
      close: any;
      constructor() {
        setTimeout(() => { this.readyState = 1; this.onopen && this.onopen({}); }, 10);
        this.send = jest.fn();
        this.close = jest.fn();
      }
    };
    global.WebSocket = mockWebSocket;
  });

  afterAll(() => {
    global.WebSocket = wsBackup;
  });

  beforeEach(() => {
    events = [];
  });

  it('should send a JSON-RPC request and receive a response', async () => {
    const wsService = new WebSocketService({ url: 'ws://test', onEvent: (e) => events.push(e) });
    wsService.connect();
    setTimeout(() => {
      // Simulate open
      const ws = (wsService as any).ws;
      const jsonRpc = new JsonRpcService(ws);
      // Intercept send
      ws.send = (data: string) => {
        // Simulate backend response
        const req = JSON.parse(data);
        setTimeout(() => {
          ws.onmessage({ data: JSON.stringify({ jsonrpc: '2.0', result: 'pong', id: req.id }) });
        }, 5);
      };
      jsonRpc.sendRequest('ping').then((result) => {
        expect(result).toBe('pong');
      });
    }, 20);
    await new Promise((resolve) => setTimeout(resolve, 50));
  });
});
