import { JsonRpcRequest, JsonRpcResponse, JsonRpcNotification, JsonRpcError } from './jsonRpc';

describe('JsonRpc Types', () => {
  it('should allow valid JsonRpcRequest', () => {
    const req: JsonRpcRequest = {
      jsonrpc: '2.0',
      method: 'testMethod',
      params: { foo: 'bar' },
      id: 1,
    };
    expect(req.method).toBe('testMethod');
  });

  it('should allow valid JsonRpcResponse', () => {
    const res: JsonRpcResponse = {
      jsonrpc: '2.0',
      result: { ok: true },
      id: 1,
    };
    expect(res.result).toEqual({ ok: true });
  });

  it('should allow valid JsonRpcNotification', () => {
    const notif: JsonRpcNotification = {
      jsonrpc: '2.0',
      method: 'notify',
      params: { foo: 1 },
    };
    expect(notif.method).toBe('notify');
  });

  it('should allow valid JsonRpcError', () => {
    const err: JsonRpcError = {
      code: -32600,
      message: 'Invalid Request',
    };
    expect(err.code).toBe(-32600);
  });
});
