import { SessionStatus, MessageStatus, AIMessageChunk, SessionInfo } from './ai';

describe('AI Types', () => {
  it('should allow valid SessionStatus', () => {
    const status: SessionStatus = SessionStatus.Active;
    expect(status).toBe('active');
  });

  it('should allow valid MessageStatus', () => {
    const status: MessageStatus = MessageStatus.Received;
    expect(status).toBe('received');
  });

  it('should allow valid AIMessageChunk', () => {
    const chunk: AIMessageChunk = {
      content: 'Hello',
      index: 0,
      isFinal: false,
    };
    expect(chunk.content).toBe('Hello');
  });

  it('should allow valid SessionInfo', () => {
    const info: SessionInfo = {
      id: 'abc',
      status: SessionStatus.Idle,
      startedAt: '2025-05-27T00:00:00Z',
      model: 'gpt-4',
    };
    expect(info.model).toBe('gpt-4');
  });
});
