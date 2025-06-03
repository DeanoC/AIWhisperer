import { JsonRpcService } from './jsonRpcService';
import { SessionInfo, SessionStatus } from '../types/ai';
import { Agent, AgentHandoffContext, AgentHandoffNotification } from '../types/agent';
import { ChannelMessage, ChannelVisibilityPreferences, ChannelHistoryRequest, ChannelHistoryResponse, ChannelStats } from '../types/channel';

export type ChannelMessageHandler = (message: ChannelMessage) => void;
export type AgentChangedHandler = (agentId: string) => void;
export type AgentHandoffHandler = (handoff: AgentHandoffNotification) => void;

export class AIService {
  private rpc: JsonRpcService;
  private sessionId: string | null = null;
  private sessionInfo: SessionInfo | null = null;
  private status: SessionStatus = SessionStatus.Idle;
  private channelMessageHandler?: ChannelMessageHandler;
  private error: string | null = null;

  constructor(rpc: JsonRpcService) {
    this.rpc = rpc;
    this.rpc.setNotificationHandler(this.handleNotification.bind(this));
  }

  /**
   * Dispatch a command to the backend (e.g., /help, /echo, etc.)
   * @param command The full command string (e.g., '/help foo')
   * @returns Backend response (could be command output or error)
   */
  async dispatchCommand(command: string): Promise<any> {
    if (!this.sessionId) throw new Error('No session active');
    try {
      const result = await this.rpc.sendRequest('dispatchCommand', {
        sessionId: this.sessionId,
        command,
      });
      return result;
    } catch (err: any) {
      this.error = err.message || 'Failed to dispatch command';
      throw err;
    }
  }
// (Removed duplicate imports and class definition)

  async startSession(userId: string): Promise<SessionInfo> {
    console.log('[AIService] Starting session for user:', userId);
    try {
      const result = await this.rpc.sendRequest('startSession', {
        userId,
        sessionParams: { language: 'en' },
      });
      console.log('[AIService] Session start result:', result);
      this.sessionId = result.sessionId;
      // Convert numeric status to enum
      const statusMap: { [key: number]: SessionStatus } = {
        0: SessionStatus.Idle,
        1: SessionStatus.Active,
        2: SessionStatus.Stopped,
        3: SessionStatus.Error
      };
      const status = typeof result.status === 'number' 
        ? (statusMap[result.status] || SessionStatus.Error)
        : result.status;
      this.status = status;
      console.log('[AIService] Session status set to:', status);
      this.sessionInfo = {
        id: result.sessionId,
        status: status,
        startedAt: new Date().toISOString(),
        model: result.model || 'unknown',
      };
      return this.sessionInfo;
    } catch (err: any) {
      console.error('[AIService] Failed to start session:', err);
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
    console.log('[AIService.sendUserMessage] called with:', message);
    console.log('[AIService.sendUserMessage] sessionId:', this.sessionId);
    if (!this.sessionId) throw new Error('No session active');
    try {
      const result = await this.rpc.sendRequest('sendUserMessage', {
        sessionId: this.sessionId,
        message,
      });
      console.log('[AIService.sendUserMessage] sendRequest result:', result);
      return result.messageId;
    } catch (err: any) {
      this.error = err.message || 'Failed to send message';
      console.error('[AIService.sendUserMessage] error:', err);
      throw err;
    }
  }

  // Legacy chunk handler removed - use onChannelMessage instead

  onChannelMessage(handler: ChannelMessageHandler) {
    this.channelMessageHandler = handler;
  }

  private handleNotification(notification: any) {
    console.log('[AIService] Received notification:', notification);
    
    // Handle channel messages
    if (notification.method === 'ChannelMessageNotification') {
      const params = notification.params || {};
      const channelMessage: ChannelMessage = {
        type: 'channel_message',
        channel: params.channel,
        content: params.content,
        metadata: params.metadata
      };
      console.log('[AIService] Processing channel message:', channelMessage);
      if (this.channelMessageHandler) {
        this.channelMessageHandler(channelMessage);
      }
    }
    
    // Legacy chunk notifications removed - using channels only
    if (notification.method === 'SessionStatusNotification') {
      const params = notification.params || {};
      if (typeof params.status === 'number') {
        // Map numeric status to enum values
        const statusMap: { [key: number]: SessionStatus } = {
          0: SessionStatus.Idle,
          1: SessionStatus.Active,
          2: SessionStatus.Stopped,
          3: SessionStatus.Error
        };
        this.status = statusMap[params.status] || SessionStatus.Error;
        if (params.status === 2) {
          this.sessionId = null;
        }
      }
    }
    // Handle agent-related notifications
    if (notification.method === 'agent.switched') {
      const params = notification.params || {};
      // The 'to' field contains the new agent ID
      this.agentChangedHandlers.forEach(handler => handler(params.to));
    }
    if (notification.method === 'agent_handoff') {
      const params = notification.params || {};
      this.agentHandoffHandlers.forEach(handler => handler({
        fromAgent: params.from_agent,
        toAgent: params.to_agent,
        context: params.context
      }));
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

  // Agent-related methods
  async listAgents(): Promise<Agent[]> {
    console.log('[AIService] Listing agents...');
    try {
      const result = await this.rpc.sendRequest('agent.list', {});
      console.log('[AIService] List agents result:', result);
      // Handle both direct array and wrapped response
      const agents = result.agents || result;
      if (!Array.isArray(agents)) {
        console.error('[AIService] Invalid response: expected array of agents, got:', agents);
        throw new Error('Invalid response: expected array of agents');
      }
      console.log('[AIService] Found agents:', agents);
      return agents;
    } catch (err: any) {
      console.error('[AIService] Failed to list agents:', err);
      this.error = err.message || 'Failed to list agents';
      throw err;
    }
  }

  async getCurrentAgent(): Promise<string | null> {
    if (!this.sessionId) throw new Error('Session not initialized');
    try {
      const result = await this.rpc.sendRequest('session.current_agent', {});
      // Handle both direct string and wrapped response
      return result.current_agent || result || null;
    } catch (err: any) {
      this.error = err.message || 'Failed to get current agent';
      throw err;
    }
  }

  async switchAgent(agentId: string): Promise<void> {
    if (!this.sessionId) throw new Error('Session not initialized');
    try {
      const result = await this.rpc.sendRequest('session.switch_agent', {
        agent_id: agentId
      });
      if (result.error) {
        throw new Error(result.error);
      }
    } catch (err: any) {
      this.error = err.message || 'Failed to switch agent';
      throw err;
    }
  }

  async handoffToAgent(agentId: string, context?: AgentHandoffContext): Promise<void> {
    if (!this.sessionId) throw new Error('Session not initialized');
    try {
      await this.rpc.sendRequest('session.handoff', {
        agent_id: agentId,
        context
      });
    } catch (err: any) {
      this.error = err.message || 'Failed to handoff to agent';
      throw err;
    }
  }

  // Agent notification handlers
  private agentChangedHandlers: AgentChangedHandler[] = [];
  private agentHandoffHandlers: AgentHandoffHandler[] = [];

  onAgentChanged(handler: AgentChangedHandler): () => void {
    this.agentChangedHandlers.push(handler);
    return () => {
      const index = this.agentChangedHandlers.indexOf(handler);
      if (index > -1) {
        this.agentChangedHandlers.splice(index, 1);
      }
    };
  }

  onAgentHandoff(handler: AgentHandoffHandler): () => void {
    this.agentHandoffHandlers.push(handler);
    return () => {
      const index = this.agentHandoffHandlers.indexOf(handler);
      if (index > -1) {
        this.agentHandoffHandlers.splice(index, 1);
      }
    };
  }

  // Channel-related methods
  async getChannelHistory(request: ChannelHistoryRequest): Promise<ChannelHistoryResponse> {
    if (!this.sessionId) throw new Error('No session active');
    try {
      const result = await this.rpc.sendRequest('channel.history', request);
      return result;
    } catch (err: any) {
      this.error = err.message || 'Failed to get channel history';
      throw err;
    }
  }

  async updateChannelVisibility(preferences: ChannelVisibilityPreferences): Promise<void> {
    if (!this.sessionId) throw new Error('No session active');
    try {
      await this.rpc.sendRequest('channel.updateVisibility', {
        sessionId: this.sessionId,
        showCommentary: preferences.showCommentary,
        showAnalysis: preferences.showAnalysis
      });
    } catch (err: any) {
      this.error = err.message || 'Failed to update channel visibility';
      throw err;
    }
  }

  async getChannelStats(): Promise<ChannelStats> {
    if (!this.sessionId) throw new Error('No session active');
    try {
      const result = await this.rpc.sendRequest('channel.stats', {
        sessionId: this.sessionId
      });
      return result;
    } catch (err: any) {
      this.error = err.message || 'Failed to get channel stats';
      throw err;
    }
  }
}
