import React from 'react';
import { Agent } from '../types/agent';
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
        key={agent.id}
        className={
          'agent-switch-btn' + (agent.id === currentAgent.id ? ' selected' : '')
        }
        style={{
          border: 'none',
          background: 'none',
          cursor: 'pointer',
          outline: 'none',
          padding: 0,
        }}
        onClick={() => onSwitch(agent.id)}
        title={agent.name}
        data-testid={`switch-agent-${agent.id}`}
      >
        <AgentAvatar agent={agent} size={28} />
      </button>
    ))}
  </div>
);
