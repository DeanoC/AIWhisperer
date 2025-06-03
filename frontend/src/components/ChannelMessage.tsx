import React from 'react';
import { ChannelMessage as ChannelMessageType, ChannelType, getChannelColor, getChannelIcon, getChannelLabel } from '../types/channel';
import { Agent } from '../types/agent';
import './ChannelMessage.css';

interface ChannelMessageProps {
  message: ChannelMessageType;
  agent?: Agent;
  isVisible: boolean;
  isCompact?: boolean;
}

export const ChannelMessage: React.FC<ChannelMessageProps> = ({
  message,
  agent,
  isVisible,
  isCompact = false
}) => {
  if (!isVisible) return null;

  const channelColor = getChannelColor(message.channel);
  const channelIcon = getChannelIcon(message.channel);
  const channelLabel = getChannelLabel(message.channel);

  // Format content based on channel type
  const formatContent = (content: string, channel: ChannelType): React.ReactNode => {
    if (channel === ChannelType.COMMENTARY) {
      // Parse tool calls and format them nicely
      try {
        // Check if content looks like JSON
        if (content.trim().startsWith('{') || content.trim().startsWith('[')) {
          const parsed = JSON.parse(content);
          return (
            <pre className="channel-message-json">
              {JSON.stringify(parsed, null, 2)}
            </pre>
          );
        }
      } catch {
        // Not JSON, display as-is
      }
    }

    // For analysis and final channels, preserve line breaks
    return content.split('\n').map((line, i) => (
      <React.Fragment key={i}>
        {line}
        {i < content.split('\n').length - 1 && <br />}
      </React.Fragment>
    ));
  };

  return (
    <div 
      className={`channel-message ${message.channel} ${isCompact ? 'compact' : ''} ${message.metadata.isPartial ? 'partial' : ''}`}
      style={{ 
        '--channel-color': channelColor,
        '--agent-color': agent?.color || channelColor,
        borderLeftColor: agent?.color || channelColor,
        backgroundColor: agent?.color ? `${agent.color}15` : undefined
      } as React.CSSProperties}
    >
      {!isCompact && (
        <div className="channel-message-header">
          <span className="channel-icon">{channelIcon}</span>
          <span className="channel-label">{channelLabel}</span>
          {agent && (
            <span className="channel-agent" style={{ color: agent.color }}>
              {agent.name}
            </span>
          )}
          {message.metadata.toolCalls && message.metadata.toolCalls.length > 0 && (
            <span className="channel-tools">
              🔧 {message.metadata.toolCalls.join(', ')}
            </span>
          )}
          <span className="channel-sequence">#{message.metadata.sequence}</span>
        </div>
      )}
      
      <div className="channel-message-content">
        {formatContent(message.content, message.channel)}
      </div>

      {message.metadata.isPartial && (
        <div className="channel-message-streaming">
          <span className="streaming-indicator">●●●</span>
        </div>
      )}
    </div>
  );
};