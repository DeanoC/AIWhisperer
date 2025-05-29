import React from 'react';
import { Agent } from '../types/agent';
import { AgentAvatar } from './AgentAvatar';
import './CurrentAgentDisplay.css';

export interface CurrentAgentDisplayProps {
  agent: Agent | null;
}

export const CurrentAgentDisplay: React.FC<CurrentAgentDisplayProps> = ({ agent }) => {
  if (!agent) {
    return (
      <div className="current-agent-display">
        <div className="no-agent-message">No agent selected</div>
      </div>
    );
  }

  return (
    <div className="current-agent-display">
      <AgentAvatar agent={agent} size={32} />
      <div className="agent-info">
        <div className="agent-display-name" style={{ color: agent.color }}>{agent.name}</div>
        <div className="agent-display-description">{agent.description}</div>
      </div>
    </div>
  );
};
