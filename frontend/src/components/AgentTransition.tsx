import React from 'react';

interface AgentTransitionProps {
  fromAgent: string;
  toAgent: string;
  show: boolean;
}

export const AgentTransition: React.FC<AgentTransitionProps> = ({ fromAgent, toAgent, show }) => {
  if (!show) return null;
  return (
    <div className="agent-transition">
      <span>Switching from <b>{fromAgent}</b> to <b>{toAgent}</b>...</span>
    </div>
  );
};
