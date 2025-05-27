// AI Session Type Definitions

export enum SessionStatus {
  Idle = 'idle',
  Active = 'active',
  Stopped = 'stopped',
  Error = 'error',
}

export enum MessageStatus {
  Pending = 'pending',
  Sent = 'sent',
  Received = 'received',
  Error = 'error',
}

export interface AIMessageChunk {
  content: string;
  index: number;
  isFinal: boolean;
}

export interface SessionInfo {
  id: string;
  status: SessionStatus;
  startedAt: string;
  endedAt?: string;
  model: string;
}
