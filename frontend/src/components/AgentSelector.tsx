import React from 'react';
import { Agent } from '../types/agent';
import './AgentSelector.css';

export interface AgentSelectorProps {
  agents: Agent[];
  currentAgent: Agent | null;
  onAgentSelect: (agentId: string) => void;
}

export const AgentSelector: React.FC<AgentSelectorProps> = ({
  agents,
  currentAgent,
  onAgentSelect
}) => {
  return (
    <div className="agent-selector">
      {agents.map(agent => (
        <div
          key={agent.id}
          className={
            'agent-item' + (currentAgent && agent.id === currentAgent.id ? ' selected' : '')
          }
          style={{ borderLeft: `4px solid ${agent.color}` }}
          onClick={() => onAgentSelect(agent.id)}
          data-testid={`agent-${agent.id}`}
        >
          <span className="agent-shortcut">[{agent.shortcut || agent.id}]</span>
          <span className="agent-name">{agent.name}</span>
          <span className="agent-description">{agent.description}</span>
        </div>
      ))}
    </div>
  );
};
