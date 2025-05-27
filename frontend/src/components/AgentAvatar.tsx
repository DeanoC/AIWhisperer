import React from 'react';
import { Agent } from '../types/agent';

export interface AgentAvatarProps {
  agent: Agent;
  size?: number;
}

export const AgentAvatar: React.FC<AgentAvatarProps> = ({ agent, size = 32 }) => {
  // Use the first letter of the agent's name as the avatar
  return (
    <div
      className="agent-avatar"
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        backgroundColor: agent.color,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        fontWeight: 'bold',
        fontSize: size * 0.6,
        userSelect: 'none',
      }}
      title={agent.name}
      data-testid={`agent-avatar-${agent.agentId}`}
    >
      {agent.name.charAt(0)}
    </div>
  );
};
