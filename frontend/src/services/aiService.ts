import { JsonRpcService } from './jsonRpcService';
import { SessionInfo, SessionStatus, AIMessageChunk } from '../types/ai';

export type AIMessageChunkHandler = (chunk: AIMessageChunk) => void;

export class AIService {
  private rpc: JsonRpcService;
  private sessionId: string | null = null;
  private sessionInfo: SessionInfo | null = null;
  private status: SessionStatus = SessionStatus.Idle;
  private chunkHandler?: AIMessageChunkHandler;
  private error: string | null = null;

  constructor(rpc: JsonRpcService) {
    this.rpc = rpc;
    this.rpc.setNotificationHandler(this.handleNotification.bind(this));
  }

  async startSession(userId: string): Promise<SessionInfo> {
    try {
      const result = await this.rpc.sendRequest('startSession', {
        userId,
        sessionParams: { language: 'en' },
      });
      this.sessionId = result.sessionId;
      this.status = result.status;
      this.sessionInfo = {
        id: result.sessionId,
        status: result.status,
        startedAt: new Date().toISOString(),
        model: result.model || 'unknown',
      };
      return this.sessionInfo;
    } catch (err: any) {
      this.error = err.message || 'Failed to start session';
      throw err;
    }
  }

  async stopSession(): Promise<void> {
    if (!this.sessionId) throw new Error('No session active');
    try {
      await this.rpc.sendRequest('stopSession', { sessionId: this.sessionId });
      this.status = SessionStatus.Stopped;
      this.sessionId = null;
    } catch (err: any) {
      this.error = err.message || 'Failed to stop session';
      throw err;
    }
  }

  async sendUserMessage(message: string): Promise<string> {
    if (!this.sessionId) throw new Error('No session active');
    try {
      const result = await this.rpc.sendRequest('sendUserMessage', {
        sessionId: this.sessionId,
        message,
      });
      return result.messageId;
    } catch (err: any) {
      this.error = err.message || 'Failed to send message';
      throw err;
    }
  }

  onAIMessageChunk(handler: AIMessageChunkHandler) {
    this.chunkHandler = handler;
  }

  private handleNotification(notification: any) {
    if (notification.method === 'AIMessageChunkNotification') {
      const params = notification.params || {};
      const chunk: AIMessageChunk = {
        content: params.chunk,
        index: params.index ?? 0,
        isFinal: params.isFinal ?? false,
      };
      this.chunkHandler?.(chunk);
    }
    if (notification.method === 'SessionStatusNotification') {
      const params = notification.params || {};
      if (params.status === 2) {
        this.status = SessionStatus.Stopped;
        this.sessionId = null;
      }
    }
  }

  getSessionInfo() {
    return this.sessionInfo;
  }

  getStatus() {
    return this.status;
  }

  getError() {
    return this.error;
  }
}
