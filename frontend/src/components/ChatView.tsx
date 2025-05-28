import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '../types/chat';
import { Agent } from '../types/agent';
import { SessionStatus } from '../types/ai';
import { AgentSelector } from './AgentSelector';
import { AgentTransition } from './AgentTransition';
import { CurrentAgentDisplay } from './CurrentAgentDisplay';
import { AgentMessageBubble } from './AgentMessageBubble';
import MessageInput from '../MessageInput';
import './ChatView.css';

export interface ChatViewProps {
  messages: ChatMessage[];
  currentAgent: Agent | null;
  agents: Agent[];
  onSendMessage: (message: string) => void;
  onAgentSelect: (agentId: string) => void;
  onHandoffToAgent: (agentId: string) => void;
  sessionStatus: SessionStatus;
  wsStatus: string;
  sessionError?: string;
  onThemeToggle?: () => void;
  theme?: 'light' | 'dark';
  data?: any; // For compatibility with ViewRouter
}

export const ChatView: React.FC<ChatViewProps> = ({
  messages,
  currentAgent,
  agents,
  onSendMessage,
  onAgentSelect,
  onHandoffToAgent,
  sessionStatus,
  wsStatus,
  sessionError,
  onThemeToggle,
  theme = 'light',
  data
}) => {
  const [showTransition, setShowTransition] = useState(false);
  const [transitionAgents, setTransitionAgents] = useState<{ from: string; to: string } | null>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle agent transitions
  const handleAgentChange = async (agentId: string) => {
    if (currentAgent && currentAgent.id !== agentId) {
      const newAgent = agents.find(a => a.id === agentId);
      if (newAgent) {
        setTransitionAgents({ from: currentAgent.name, to: newAgent.name });
        setShowTransition(true);
        
        // Hide transition after animation
        setTimeout(() => setShowTransition(false), 1500);
      }
    }
    await onAgentSelect(agentId);
  };

  // Get agent for message
  const getAgentForMessage = (message: ChatMessage): Agent | undefined => {
    if (message.sender === 'user') return undefined;
    
    // Try to match by agent ID in metadata
    if (message.metadata?.agentId) {
      return agents.find(a => a.id === message.metadata?.agentId);
    }
    
    // Default to current agent for AI messages
    return message.sender === 'ai' ? currentAgent || undefined : undefined;
  };

  // Fetch command list for autocomplete
  const fetchCommandList = async (): Promise<string[]> => {
    // This would be implemented to fetch from AIService
    return ['help', 'session.info', 'agent.list', 'agent.switch'];
  };

  // Use data prop if no messages provided (for ViewRouter compatibility)
  const displayMessages = messages || data?.messages || [];

  return (
    <div className="chat-view" data-testid="chat-view">
      {/* Status Bar */}
      <div className="chat-status-bar">
        <div className="status-indicators">
          <span className={`status-indicator ${wsStatus === 'connected' ? 'connected' : 'disconnected'}`}>
            WebSocket: {wsStatus}
          </span>
          <span className={`status-indicator ${sessionStatus === SessionStatus.Active ? 'active' : 'inactive'}`}>
            Session: {sessionStatus}
          </span>
          {sessionError && (
            <span className="status-error">Error: {sessionError}</span>
          )}
        </div>
        <div className="status-actions">
          {onThemeToggle && (
            <button onClick={onThemeToggle} className="theme-toggle">
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
          )}
        </div>
      </div>

      {/* Chat Header */}
      <div className="chat-header">
        <CurrentAgentDisplay agent={currentAgent} />
        <AgentSelector
          agents={agents}
          currentAgent={currentAgent}
          onAgentSelect={handleAgentChange}
        />
      </div>

      {/* Messages Container */}
      <div className="chat-messages" ref={chatContainerRef}>
        {displayMessages.length === 0 && (
          <div className="empty-chat">
            <h3>Welcome to AI Whisperer</h3>
            <p>Start a conversation with {currentAgent ? currentAgent.name : 'an AI agent'}</p>
          </div>
        )}
        
        {displayMessages.map((message: ChatMessage, index: number) => {
          const agent = getAgentForMessage(message);
          
          if (message.sender === 'system') {
            return (
              <div key={index} className="system-message">
                {message.content}
              </div>
            );
          }
          
          if (message.sender === 'user') {
            return (
              <div key={index} className="message-wrapper user">
                <div className="user-message">
                  {message.content}
                </div>
              </div>
            );
          }
          
          return (
            <div key={index} className="message-wrapper ai">
              <AgentMessageBubble
                message={message}
                agent={agent}
              />
            </div>
          );
        })}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Agent Transition Overlay */}
      {showTransition && transitionAgents && (
        <div className="transition-overlay">
          <AgentTransition
            fromAgent={transitionAgents.from}
            toAgent={transitionAgents.to}
            show={showTransition}
          />
        </div>
      )}

      {/* Message Input */}
      <div className="chat-input-container">
        <MessageInput
          onSend={onSendMessage}
          fetchCommandList={fetchCommandList}
          sessionStatus={sessionStatus}
          disabled={sessionStatus !== SessionStatus.Active}
        />
      </div>

      {/* Quick Actions */}
      <div className="chat-quick-actions">
        <button 
          onClick={() => onSendMessage('/help')}
          disabled={sessionStatus !== SessionStatus.Active}
          title="Show available commands"
        >
          Help
        </button>
        <button 
          onClick={() => onSendMessage('/session.info')}
          disabled={sessionStatus !== SessionStatus.Active}
          title="Show session information"
        >
          Session Info
        </button>
        <button 
          onClick={() => onSendMessage('/agent.list')}
          disabled={sessionStatus !== SessionStatus.Active}
          title="List available agents"
        >
          List Agents
        </button>
      </div>
    </div>
  );
};