import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Agent } from '../types/agent';
import { ChatMessage } from '../types/chat';
import { MessageStatus } from '../types/ai';
import { AgentAvatar } from './AgentAvatar';
import './AgentMessageBubble.css';

export interface AgentMessageBubbleProps {
  message: ChatMessage & { isStreaming?: boolean };
  agent?: Agent;
}

const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  });
};

export const AgentMessageBubble: React.FC<AgentMessageBubbleProps> = ({ 
  message, 
  agent 
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const isUser = message.sender === 'user';
  const isLongMessage = message.content.length > 300;
  const shouldCollapse = isLongMessage && !isExpanded;
  
  const displayContent = shouldCollapse 
    ? message.content.substring(0, 300) + '...' 
    : message.content;
    
  const containerClasses = [
    'message-container',
    isUser ? 'user-message' : 'agent-message'
  ].join(' ');
  
  const bubbleClasses = [
    'message-bubble',
    isUser ? 'user-message' : 'agent-message',
    message.status === MessageStatus.Pending && 'sending',
    message.status === MessageStatus.Error && 'error'
  ].filter(Boolean).join(' ');
  
  const ariaLabel = isUser 
    ? `Your message at ${formatTimestamp(message.timestamp)}`
    : `Message from ${agent?.name || 'Agent'} at ${formatTimestamp(message.timestamp)}`;
  
  return (
    <div 
      className={containerClasses}
      data-testid={`message-container-${message.id}`}
      aria-label={ariaLabel}
    >
      {!isUser && agent && (
        <AgentAvatar agent={agent} size="small" />
      )}
      
      <div className="message-content">
        <div 
          className={bubbleClasses}
          data-testid={`message-bubble-${message.id}`}
          style={!isUser && agent ? { backgroundColor: agent.color } : undefined}
        >
          {message.isStreaming && !message.content && (
            <div className="thinking-indicator" data-testid="thinking-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          )}
          
          <div className="message-text markdown-content">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Custom code block rendering
                code({ node, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  const language = match ? match[1] : 'text';
                  const isInline = !className;
                  
                  if (isInline) {
                    return <code className="inline-code" {...props}>{children}</code>;
                  }
                  
                  return (
                    <div className="code-block-wrapper" data-testid="code-block">
                      <div className="code-block-header">{language}</div>
                      <pre className="code-block">
                        <code {...props}>{children}</code>
                      </pre>
                    </div>
                  );
                },
                // Open links in new tab
                a({ node, children, ...props }) {
                  return (
                    <a target="_blank" rel="noopener noreferrer" {...props}>
                      {children}
                    </a>
                  );
                }
              }}
            >
              {displayContent}
            </ReactMarkdown>
          </div>
          
          {message.status === 'error' && (
            <div className="error-message">Failed to send</div>
          )}
          
          {isLongMessage && (
            <button 
              className="expand-button"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Show less' : 'Show more'}
            </button>
          )}
        </div>
        
        <div className="message-timestamp">
          {formatTimestamp(message.timestamp)}
        </div>
      </div>
      
      {isUser && (
        <div className="user-avatar" data-testid="user-avatar">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
          </svg>
        </div>
      )}
    </div>
  );
};