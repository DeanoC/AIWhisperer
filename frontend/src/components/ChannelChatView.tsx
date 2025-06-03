import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, MessageSender } from '../types/chat';
import { Agent } from '../types/agent';
import { SessionStatus, MessageStatus } from '../types/ai';
import { ChannelMessage } from '../types/channel';
import { ChannelMessage as ChannelMessageComponent } from './ChannelMessage';
import { ChannelControls } from './ChannelControls';
import { AgentSelector } from './AgentSelector';
import { AgentTransition } from './AgentTransition';
import { AgentMessageBubble } from './AgentMessageBubble';
import MessageInput from '../MessageInput';
import { FilePicker } from './FilePicker';
import { useChannels } from '../hooks/useChannels';
import './ChatView.css';

export interface ChannelChatViewProps {
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
  jsonRpcService?: any;
  aiService?: any;
  loading?: boolean;
}

export const ChannelChatView: React.FC<ChannelChatViewProps> = ({
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
  jsonRpcService,
  aiService,
  loading = false
}) => {
  const [showTransition, setShowTransition] = useState(false);
  const [transitionAgents, setTransitionAgents] = useState<{ from: string; to: string } | null>(null);
  const [isAgentSelectorCompact, setIsAgentSelectorCompact] = useState(false);
  const [showFilePicker, setShowFilePicker] = useState(false);
  const [filePickerCallback, setFilePickerCallback] = useState<((filePath: string) => void) | null>(null);
  const [showChannelControls, setShowChannelControls] = useState(false);
  
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wasAtBottomRef = useRef(true);

  // Use channels hook
  const { 
    visibleMessages, 
    visibilityPreferences, 
    updateVisibility,
    channelMessages 
  } = useChannels(aiService);

  // Count messages by channel
  const messageCount = channelMessages.reduce((acc, msg) => {
    acc[msg.channel] = (acc[msg.channel] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Track if user is at bottom in real time
  useEffect(() => {
    const container = chatContainerRef.current;
    if (!container) return;
    const threshold = 120;
    const handleScroll = () => {
      wasAtBottomRef.current = (container.scrollHeight - container.scrollTop - container.clientHeight < threshold);
    };
    container.addEventListener('scroll', handleScroll);
    handleScroll();
    return () => {
      container.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // Auto-scroll when new messages arrive
  useEffect(() => {
    if (wasAtBottomRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length, visibleMessages.length]);

  // Handle agent transitions
  const handleAgentChange = async (agentId: string) => {
    if (currentAgent && currentAgent.id !== agentId) {
      const newAgent = agents.find(a => a.id === agentId);
      if (newAgent) {
        setTransitionAgents({ from: currentAgent.name, to: newAgent.name });
        setShowTransition(true);
        setTimeout(() => setShowTransition(false), 1500);
      }
    }
    await onAgentSelect(agentId);
  };

  // Get agent for message
  const getAgentForMessage = (message: ChatMessage): Agent | undefined => {
    if (message.sender === 'user') return undefined;
    
    if (message.metadata?.agentId) {
      const currentAgent = agents.find(a => a.id === message.metadata?.agentId);
      if (currentAgent) {
        return currentAgent;
      }
    }
    
    if (message.metadata?.agent) {
      return message.metadata.agent;
    }
    
    return undefined;
  };

  // Fetch command list for autocomplete
  const fetchCommandList = async (): Promise<string[]> => {
    try {
      if (!jsonRpcService) {
        return ['help', 'status', 'debbie', 'agent.inspect', 'session.switch_agent'];
      }
      
      const response = await jsonRpcService.call('dispatchCommand', {
        command: '/help'
      });
      
      if (response?.output && typeof response.output === 'string') {
        const lines = response.output.split('\n');
        const commands: string[] = [];
        for (const line of lines) {
          const match = line.match(/^\/([^:]+):/);
          if (match) {
            commands.push(match[1]);
          }
        }
        return commands.length > 0 ? commands : ['help', 'status', 'debbie'];
      }
      
      return ['help', 'status', 'debbie', 'agent.inspect', 'session.switch_agent'];
    } catch (error) {
      console.warn('Failed to fetch command list:', error);
      return ['help', 'status', 'debbie', 'agent.inspect', 'session.switch_agent'];
    }
  };

  // Combine regular messages with channel messages
  // Channel messages will appear between regular messages based on timing
  const combinedMessages = React.useMemo(() => {
    const combined: Array<ChatMessage | ChannelMessage> = [...messages];
    
    // Insert visible channel messages at appropriate positions
    // For now, append them at the end (later we can interleave based on timestamps)
    visibleMessages.forEach(channelMsg => {
      combined.push(channelMsg);
    });
    
    return combined;
  }, [messages, visibleMessages]);

  return (
    <div className="chat-view channel-enabled" data-testid="chat-view">
      {/* Status Bar */}
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
          <button 
            className="channel-controls-toggle"
            onClick={() => setShowChannelControls(!showChannelControls)}
            title="Toggle channel visibility controls"
          >
            🔧 Channels
          </button>
        </div>
      )}

      {/* Channel Controls */}
      {showChannelControls && (
        <ChannelControls
          preferences={visibilityPreferences}
          onPreferencesChange={updateVisibility}
          messageCount={messageCount}
        />
      )}

      {/* Messages Container */}
      <div className="chat-messages" ref={chatContainerRef}>
        {combinedMessages.length === 0 && (
          <div className="empty-chat">
            <h3>Welcome to AI Whisperer</h3>
            <p>Start a conversation with {currentAgent ? currentAgent.name : 'an AI agent'}</p>
          </div>
        )}
        
        {combinedMessages.map((item, index) => {
          // Check if it's a channel message
          if ('type' in item && item.type === 'channel_message') {
            const channelMsg = item as ChannelMessage;
            return (
              <ChannelMessageComponent
                key={`channel-${channelMsg.metadata.sequence}`}
                message={channelMsg}
                agent={currentAgent || undefined}
                isVisible={true}
              />
            );
          }
          
          // Regular chat message
          const message = item as ChatMessage;
          const agent = getAgentForMessage(message);
          
          if (message.sender === 'system') {
            return (
              <div key={index} className="system-message">
                {message.content}
              </div>
            );
          }
          
          return (
            <div key={index} className="message-wrapper">
              <AgentMessageBubble
                message={message}
                agent={message.sender === MessageSender.AI ? agent : undefined}
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