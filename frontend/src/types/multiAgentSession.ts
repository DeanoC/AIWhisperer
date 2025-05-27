import { Agent } from '../types/agent';
import { ChatMessage } from '../types/chat';

export interface MultiAgentSessionState {
  agents: Agent[];
  currentAgent: Agent;
  conversationHistories: Record<string, ChatMessage[]>;
  handoff: { from: string; to: string; show: boolean } | null;
}
