import { JsonRpcService } from './jsonRpcService';
import { JsonRpcRequest, JsonRpcNotification } from '../types/jsonRpc';

describe('JsonRpcService', () => {
  let ws: any;
  let sentData: any[];
  let service: JsonRpcService;

  beforeEach(() => {
    sentData = [];
    ws = {
      send: (data: string) => sentData.push(data),
      onmessage: null as any,
    };
    service = new JsonRpcService(ws as any, 50); // short timeout for test
  });

  it('sends a request and resolves on response', async () => {
    const promise = service.sendRequest('testMethod', { foo: 1 });
    const req: JsonRpcRequest = JSON.parse(sentData[0]);
    expect(req.method).toBe('testMethod');
    // Simulate response
    ws.onmessage({ data: JSON.stringify({ jsonrpc: '2.0', result: 42, id: req.id }) });
    await expect(promise).resolves.toBe(42);
  });

  it('rejects on error response', async () => {
    const promise = service.sendRequest('failMethod');
    const req: JsonRpcRequest = JSON.parse(sentData[0]);
    ws.onmessage({ data: JSON.stringify({ jsonrpc: '2.0', error: { code: -1, message: 'fail' }, id: req.id }) });
    await expect(promise).rejects.toHaveProperty('code', -1);
  });

  it('rejects on timeout', async () => {
    const promise = service.sendRequest('timeoutMethod');
    await expect(promise).rejects.toThrow('JSON-RPC request timeout');
  });

  it('handles notifications', (done) => {
    const notification: JsonRpcNotification = { jsonrpc: '2.0', method: 'notify', params: { foo: 1 } };
    service.setNotificationHandler((msg) => {
      expect(msg.method).toBe('notify');
      done();
    });
    ws.onmessage({ data: JSON.stringify(notification) });
  });
});
