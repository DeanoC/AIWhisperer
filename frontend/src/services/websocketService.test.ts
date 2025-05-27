import { WebSocketService } from './websocketService';

describe('WebSocketService', () => {
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
      constructor() {
        setTimeout(() => { this.readyState = 1; this.onopen && this.onopen({}); }, 10);
      }
      send(data: string) { this.onmessage && this.onmessage({ data }); }
      close() { this.onclose && this.onclose({}); }
    };
    global.WebSocket = mockWebSocket;
  });

  afterAll(() => {
    global.WebSocket = wsBackup;
  });

  beforeEach(() => {
    events = [];
  });

  it('connects and triggers open event', (done) => {
    const service = new WebSocketService({ url: 'ws://test', onEvent: (e) => events.push(e) });
    service.connect();
    setTimeout(() => {
      expect(events).toContain('open');
      expect(service.getState()).toBe('connected');
      done();
    }, 20);
  });

  it('sends and receives messages', (done) => {
    const service = new WebSocketService({ url: 'ws://test', onEvent: (e, ev) => {
      if (e === 'message' && 'data' in (ev ?? {})) events.push((ev as MessageEvent).data);
    }});
    service.connect();
    setTimeout(() => {
      service.send('hello');
      setTimeout(() => {
        expect(events).toContain('hello');
        done();
      }, 10);
    }, 20);
  });

  it('disconnects and triggers close event', (done) => {
    const service = new WebSocketService({ url: 'ws://test', onEvent: (e) => events.push(e) });
    service.connect();
    setTimeout(() => {
      service.disconnect();
      setTimeout(() => {
        expect(events).toContain('close');
        expect(service.getState()).toBe('disconnected');
        done();
      }, 10);
    }, 20);
  });
});
