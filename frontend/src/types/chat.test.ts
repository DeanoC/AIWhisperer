import { ChatMessage, MessageSender } from './chat';
import { MessageStatus } from './ai';

describe('Chat Types', () => {
  it('should allow valid ChatMessage', () => {
    const msg: ChatMessage = {
      id: '1',
      sender: MessageSender.User,
      content: 'Hello',
      timestamp: '2025-05-27T00:00:00Z',
      status: MessageStatus.Sent,
    };
    expect(msg.sender).toBe('user');
  });

  it('should allow valid MessageSender', () => {
    const sender: MessageSender = MessageSender.AI;
    expect(sender).toBe('ai');
  });
});
