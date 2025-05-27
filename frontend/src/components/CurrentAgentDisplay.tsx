import React from 'react';
import { Agent } from '../types/agent';
import { AgentAvatar } from './AgentAvatar';

export interface CurrentAgentDisplayProps {
  agent: Agent;
}

export const CurrentAgentDisplay: React.FC<CurrentAgentDisplayProps> = ({ agent }) => (
  <div className="current-agent-display" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
    <AgentAvatar agent={agent} size={32} />
    <div>
      <div style={{ fontWeight: 'bold', color: agent.color }}>{agent.name}</div>
      <div style={{ fontSize: 12, color: '#666' }}>{agent.description}</div>
    </div>
  </div>
);
