import React from 'react';
import { Agent } from '../types/agent';
import './AgentAvatar.css';

export type AvatarSize = 'small' | 'medium' | 'large' | number;

export interface AgentAvatarProps {
  agent: Agent;
  size?: AvatarSize | number;
  showStatus?: boolean;
  isActive?: boolean;
  isLoading?: boolean;
  interactive?: boolean;
  preferIcon?: boolean;
}

const sizeMap = {
  small: 24,
  medium: 32,
  large: 48,
};

export const AgentAvatar: React.FC<AgentAvatarProps> = ({ 
  agent, 
  size = 32,
  showStatus = false,
  isActive = false,
  isLoading = false,
  interactive = true,
  preferIcon = false
}) => {
  // Handle backward compatibility - if size is a number, use it directly
  const pixelSize = typeof size === 'number' ? size : sizeMap[size];
  const fontSize = pixelSize * 0.5;
  const statusSize = Math.max(8, pixelSize * 0.25);
  
  // Determine what to show in the avatar
  const displayContent = preferIcon && agent.icon ? agent.icon : agent.name.charAt(0);
  
  // Build aria-label
  const ariaLabel = `${agent.name} avatar${showStatus && agent.status ? ` (${agent.status})` : ''}`;
  
  const classNames = [
    'agent-avatar',
    isActive && 'active',
    isLoading && 'loading',
    interactive && 'hoverable'
  ].filter(Boolean).join(' ');

  return (
    <div
      className={classNames}
      style={{
        width: pixelSize,
        height: pixelSize,
        backgroundColor: agent.color,
        fontSize: fontSize,
      }}
      title={agent.name}
      data-testid={`agent-avatar-${agent.id}`}
      role="img"
      aria-label={ariaLabel}
    >
      {isLoading && (
        <div className="loading-shimmer" data-testid="avatar-loading-shimmer" />
      )}
      <span className="avatar-content">{displayContent}</span>
      {showStatus && (
        <div 
          className={`status-indicator status-${agent.status || 'online'}`}
          data-testid="agent-status-indicator"
          style={{
            width: statusSize,
            height: statusSize,
          }}
        />
      )}
    </div>
  );
};
