import React from 'react';
import { Agent } from '../types/agent';

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
          key={agent.agentId}
          className={
            'agent-item' + (currentAgent && agent.agentId === currentAgent.agentId ? ' selected' : '')
          }
          style={{ borderLeft: `4px solid ${agent.color}` }}
          onClick={() => onAgentSelect(agent.agentId)}
          data-testid={`agent-${agent.agentId}`}
        >
          <span className="agent-shortcut">{agent.shortcut}</span>
          <span className="agent-name">{agent.name}</span>
          <span className="agent-description">{agent.description}</span>
        </div>
      ))}
    </div>
  );
};
