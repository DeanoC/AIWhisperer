import { MessageStatus } from './ai';

// Chat Message Type Definitions
export interface ChatMessage {
  id: string;
  sender: MessageSender;
  content: string;
  timestamp: string;
  status: MessageStatus;
  metadata?: {
    agentId?: string;
    [key: string]: any;
  };
  isStreaming?: boolean;
}

export enum MessageSender {
  User = 'user',
  AI = 'ai',
  System = 'system',
}
