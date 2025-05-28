import React, { useState } from 'react';
import { Agent } from '../types/agent';
import { ChatMessage } from '../types/chat';
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

const renderCodeBlock = (code: string, language: string) => (
  <div className="code-block-wrapper" data-testid="code-block">
    <div className="code-block-header">{language}</div>
    <pre className="code-block">
      <code>{code}</code>
    </pre>
  </div>
);

const parseContent = (content: string) => {
  const parts: Array<{ type: 'text' | 'code' | 'link'; content: string; lang?: string; href?: string }> = [];
  let remaining = content;
  
  // Extract code blocks first
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;
  
  while ((match = codeBlockRegex.exec(content)) !== null) {
    // Add text before code block
    if (match.index > lastIndex) {
      parts.push({ 
        type: 'text', 
        content: content.substring(lastIndex, match.index) 
      });
    }
    
    // Add code block
    parts.push({
      type: 'code',
      content: match[2].trim(),
      lang: match[1] || 'text'
    });
    
    lastIndex = match.index + match[0].length;
  }
  
  // Add remaining text
  if (lastIndex < content.length) {
    parts.push({ 
      type: 'text', 
      content: content.substring(lastIndex) 
    });
  }
  
  return parts.length > 0 ? parts : [{ type: 'text' as const, content }];
};

export const AgentMessageBubble: React.FC<AgentMessageBubbleProps> = ({ 
  message, 
  agent 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
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
    message.status === 'sending' && 'sending',
    message.status === 'error' && 'error'
  ].filter(Boolean).join(' ');
  
  const ariaLabel = isUser 
    ? `Your message at ${formatTimestamp(message.timestamp)}`
    : `Message from ${agent?.name || 'Agent'} at ${formatTimestamp(message.timestamp)}`;
    
  // Parse content into parts
  const contentParts = parseContent(displayContent);
  
  const renderTextWithLinks = (text: string) => {
    // Convert links
    const linkified = text.replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
    );
    
    // Convert lists
    let processed = linkified;
    processed = processed.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
    processed = processed.replace(/(<li>.*<\/li>\n?)+/g, '<ol>$&</ol>');
    
    return <div dangerouslySetInnerHTML={{ __html: processed }} />;
  };
  
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
          
          <div className="message-text">
            {contentParts.map((part, index) => {
              if (part.type === 'code') {
                return (
                  <div key={index} className="code-block-wrapper" data-testid="code-block">
                    <div className="code-block-header">{part.lang}</div>
                    <pre className="code-block">
                      <code>{part.content}</code>
                    </pre>
                  </div>
                );
              }
              return <React.Fragment key={index}>{renderTextWithLinks(part.content)}</React.Fragment>;
            })}
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

// Post-process to replace code placeholders with actual code blocks
export const postProcessMessage = (element: HTMLElement) => {
  const codePlaceholders = element.querySelectorAll('.code-placeholder');
  codePlaceholders.forEach(placeholder => {
    const lang = placeholder.getAttribute('data-lang') || 'text';
    const code = decodeURIComponent(placeholder.getAttribute('data-code') || '');
    const codeBlock = renderCodeBlock(code, lang);
    // In a real implementation, we'd properly replace the placeholder
  });
};