export interface Agent {
  id: string;
  name: string;
  role: string;
  description?: string;
  color: string;
  icon?: string;
  status?: 'online' | 'busy' | 'offline';
  shortcut?: string;
}

export interface AgentHandoffContext {
  task?: string;
  files?: string[];
  previousAgent?: string;
  metadata?: Record<string, any>;
}

export interface AgentHandoffNotification {
  fromAgent: string;
  toAgent: string;
  context?: AgentHandoffContext;
}
