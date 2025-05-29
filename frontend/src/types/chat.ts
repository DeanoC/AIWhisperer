import { MessageStatus } from './ai';
import { Agent } from './agent';

// Chat Message Type Definitions
export interface ChatMessage {
  id: string;
  sender: MessageSender;
  content: string;
  timestamp: string;
  status: MessageStatus;
  metadata?: {
    agentId?: string;
    agent?: Agent; // Store complete agent data for persistent display
    [key: string]: any;
  };
  isStreaming?: boolean;
}

export enum MessageSender {
  User = 'user',
  AI = 'ai',
  System = 'system',
}
