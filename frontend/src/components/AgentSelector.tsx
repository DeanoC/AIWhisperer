import React, { useState, useEffect } from 'react';
import { Agent } from '../types/agent';
import { AgentAvatar } from './AgentAvatar';
import './AgentSelector.css';

export interface AgentSelectorProps {
  agents: Agent[];
  currentAgent: Agent | null;
  onAgentSelect: (agentId: string) => void;
  onCompactChange?: (isCompact: boolean) => void;
}

export const AgentSelector: React.FC<AgentSelectorProps> = ({
  agents,
  currentAgent,
  onAgentSelect,
  onCompactChange
}) => {
  const [isCompact, setIsCompact] = useState(() => {
    // Load preference from localStorage
    return localStorage.getItem('agentSelector.compact') === 'true';
  });

  // Save preference to localStorage and notify parent
  useEffect(() => {
    localStorage.setItem('agentSelector.compact', String(isCompact));
    onCompactChange?.(isCompact);
  }, [isCompact, onCompactChange]);

  const toggleCompactMode = () => {
    setIsCompact(!isCompact);
  };

  if (isCompact) {
    return (
      <div className="agent-selector compact">
        <button
          className="compact-toggle"
          onClick={toggleCompactMode}
          title="Expand agent selector"
          aria-label="Expand agent selector"
        >
          ⬅️
        </button>
        <div className="agent-list">
          {agents.map(agent => (
            <div
              key={agent.id}
              className={`agent-item-compact ${currentAgent?.id === agent.id ? 'selected' : ''}`}
              onClick={() => onAgentSelect(agent.id)}
              title={`${agent.name} - ${agent.description}`}
              data-testid={`agent-${agent.id}-compact`}
            >
              <AgentAvatar agent={agent} size={28} preferIcon={true} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="agent-selector">
      <button
        className="compact-toggle"
        onClick={toggleCompactMode}
        title="Compact view"
        aria-label="Switch to compact view"
      >
        ➡️
      </button>
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
          <span className="agent-shortcut">{agent.shortcut || `[${agent.id.toUpperCase()}]`}</span>
          <span className="agent-name">{agent.name}</span>
          <span className="agent-description">{agent.description}</span>
        </div>
      ))}
    </div>
  );
};
