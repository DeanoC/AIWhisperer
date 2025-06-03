import { AIService } from './aiService';
import { SessionStatus } from '../types/ai';

describe('AIService', () => {
  let rpc: any;
  let service: AIService;
  let notifications: any[];

  beforeEach(() => {
    notifications = [];
    rpc = {
      sendRequest: jest.fn(),
      setNotificationHandler: jest.fn((handler) => {
        rpc._notify = handler;
      }),
    };
    service = new AIService(rpc);
  });

  it('starts a session and updates state', async () => {
    rpc.sendRequest.mockResolvedValue({ sessionId: 'abc', status: 1, model: 'gpt-test' });
    const info = await service.startSession('user1');
    expect(info.id).toBe('abc');
    expect(service.getStatus()).toBe(SessionStatus.Active);
    expect(service.getSessionInfo()?.model).toBe('gpt-test');
  });

  it('stops a session and updates state', async () => {
    rpc.sendRequest.mockResolvedValueOnce({ sessionId: 'abc', status: 1, model: 'gpt-test' });
    await service.startSession('user1');
    rpc.sendRequest.mockResolvedValueOnce({});
    await service.stopSession();
    expect(service.getStatus()).toBe(SessionStatus.Stopped);
    expect(service.getSessionInfo()).toBeTruthy();
  });

  it('sends a user message', async () => {
    rpc.sendRequest.mockResolvedValueOnce({ sessionId: 'abc', status: 1, model: 'gpt-test' });
    await service.startSession('user1');
    rpc.sendRequest.mockResolvedValueOnce({ messageId: 'msg-1' });
    const msgId = await service.sendUserMessage('hello');
    expect(msgId).toBe('msg-1');
  });

  it('handles channel message notifications', async () => {
    rpc.sendRequest.mockResolvedValueOnce({ sessionId: 'abc', status: 1, model: 'gpt-test' });
    await service.startSession('user1');
    const channelMessages: any[] = [];
    service.onChannelMessage((message) => channelMessages.push(message));
    
    rpc._notify({ 
      method: 'ChannelMessageNotification', 
      params: { 
        channel: 'final', 
        content: 'Hello world', 
        metadata: { sequence: 1, timestamp: '2023-01-01T00:00:00Z', isPartial: false }
      } 
    });
    
    rpc._notify({ 
      method: 'ChannelMessageNotification', 
      params: { 
        channel: 'analysis', 
        content: 'Internal reasoning', 
        metadata: { sequence: 2, timestamp: '2023-01-01T00:00:01Z', isPartial: true }
      } 
    });
    
    expect(channelMessages.length).toBe(2);
    expect(channelMessages[0].channel).toBe('final');
    expect(channelMessages[1].metadata.isPartial).toBe(true);
  });

  it('handles session stopped notification', async () => {
    rpc.sendRequest.mockResolvedValueOnce({ sessionId: 'abc', status: 1, model: 'gpt-test' });
    await service.startSession('user1');
    rpc._notify({ method: 'SessionStatusNotification', params: { status: 2 } });
    expect(service.getStatus()).toBe(SessionStatus.Stopped);
  });

  it('handles errors from startSession', async () => {
    rpc.sendRequest.mockRejectedValueOnce(new Error('fail'));
    await expect(service.startSession('user1')).rejects.toThrow('fail');
    expect(service.getError()).toBe('fail');
  });
});
