import React from 'react';
import { Agent } from './AgentSelector';
import { AgentAvatar } from './AgentAvatar';

export interface AgentSwitcherProps {
  agents: Agent[];
  currentAgent: Agent;
  onSwitch: (agentId: string) => void;
}

export const AgentSwitcher: React.FC<AgentSwitcherProps> = ({ agents, currentAgent, onSwitch }) => (
  <div className="agent-switcher" style={{ display: 'flex', gap: 12 }}>
    {agents.map(agent => (
      <button
        key={agent.agentId}
        className={
          'agent-switch-btn' + (agent.agentId === currentAgent.agentId ? ' selected' : '')
        }
        style={{
          border: 'none',
          background: 'none',
          cursor: 'pointer',
          outline: 'none',
          padding: 0,
        }}
        onClick={() => onSwitch(agent.agentId)}
        title={agent.name}
        data-testid={`switch-agent-${agent.agentId}`}
      >
        <AgentAvatar agent={agent} size={28} />
      </button>
    ))}
  </div>
);
