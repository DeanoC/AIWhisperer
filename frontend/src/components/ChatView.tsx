import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '../types/chat';
import { Agent } from '../types/agent';
import { SessionStatus } from '../types/ai';
import { AgentSelector } from './AgentSelector';
import { AgentTransition } from './AgentTransition';
import { AgentMessageBubble } from './AgentMessageBubble';
import MessageInput from '../MessageInput';
import { FilePicker } from './FilePicker';
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
  jsonRpcService?: any; // For file picker
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
  data,
  jsonRpcService
}) => {
  const [showTransition, setShowTransition] = useState(false);
  const [transitionAgents, setTransitionAgents] = useState<{ from: string; to: string } | null>(null);
  const [isAgentSelectorCompact, setIsAgentSelectorCompact] = useState(false);
  const [showFilePicker, setShowFilePicker] = useState(false);
  const [filePickerCallback, setFilePickerCallback] = useState<((filePath: string) => void) | null>(null);
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
    
    // Try to match by agent ID in current agents list first
    if (message.metadata?.agentId) {
      const currentAgent = agents.find(a => a.id === message.metadata?.agentId);
      if (currentAgent) {
        return currentAgent;
      }
    }
    
    // If not found in current agents, use stored agent data from message
    // This preserves the original agent's color even if the agent is no longer active
    if (message.metadata?.agent) {
      return message.metadata.agent;
    }
    
    // For AI messages without any agent metadata, return undefined
    return undefined;
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
      {/* Status Bar - Compact */}
      {(wsStatus !== 'connected' || sessionStatus !== SessionStatus.Active || sessionError) && (
        <div className="chat-status-bar compact">
          <div className="status-indicators">
            <div className="status-indicators-row">
              {wsStatus !== 'connected' && (
                <span className={`status-indicator ${wsStatus === 'connected' ? 'connected' : 'disconnected'}`}>
                  WebSocket: {wsStatus}
                </span>
              )}
              {sessionStatus !== SessionStatus.Active && (
                <span className="status-indicator inactive">
                  Session: {sessionStatus}
                </span>
              )}
            </div>
            {sessionError && (
              <span className="status-error">Error: {sessionError}</span>
            )}
          </div>
        </div>
      )}

      {/* Chat Header */}
      {!isAgentSelectorCompact && (
        <div className="chat-header">
          <AgentSelector
            agents={agents}
            currentAgent={currentAgent}
            onAgentSelect={handleAgentChange}
            onCompactChange={setIsAgentSelectorCompact}
          />
        </div>
      )}

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
          onFilePickerRequest={(callback) => {
            setFilePickerCallback(() => callback);
            setShowFilePicker(true);
          }}
        />
      </div>

      {/* File Picker Modal */}
      <FilePicker
        jsonRpcService={jsonRpcService}
        isOpen={showFilePicker}
        onSelect={(filePath) => {
          if (filePickerCallback) {
            filePickerCallback(filePath);
            setFilePickerCallback(null);
          }
        }}
        onClose={() => {
          setShowFilePicker(false);
          setFilePickerCallback(null);
        }}
      />

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

      {/* Floating Compact Agent Selector */}
      {isAgentSelectorCompact && (
        <AgentSelector
          agents={agents}
          currentAgent={currentAgent}
          onAgentSelect={handleAgentChange}
          onCompactChange={setIsAgentSelectorCompact}
        />
      )}
    </div>
  );
};