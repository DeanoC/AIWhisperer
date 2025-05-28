import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AgentMessageBubble } from './AgentMessageBubble';
import { Agent } from '../types/agent';
import { ChatMessage } from '../types/chat';

describe('AgentMessageBubble', () => {
  const agent: Agent = {
    id: 'P',
    name: 'Patricia',
    role: 'Planner',
    description: 'Creates project plans',
    color: '#8B5CF6',
  };

  const userMessage: ChatMessage = {
    id: '1',
    sender: 'user',
    content: 'Can you help me plan this feature?',
    timestamp: '2025-05-28T10:30:00Z',
    status: 'sent'
  };

  const agentMessage: ChatMessage = {
    id: '2',
    sender: 'ai',
    content: 'I\'ll help you create a comprehensive plan for this feature.',
    timestamp: '2025-05-28T10:31:00Z',
    status: 'received'
  };

  describe('Message Rendering', () => {
    it('renders agent message with agent-specific colors', () => {
      render(<AgentMessageBubble message={agentMessage} agent={agent} />);
      
      const bubble = screen.getByTestId('message-bubble-2');
      expect(bubble).toHaveStyle(`background-color: ${agent.color}`);
    });

    it('renders user message with default styling', () => {
      render(<AgentMessageBubble message={userMessage} />);
      
      const bubble = screen.getByTestId('message-bubble-1');
      expect(bubble).toHaveClass('user-message');
    });

    it('displays message content correctly', () => {
      render(<AgentMessageBubble message={agentMessage} agent={agent} />);
      
      expect(screen.getByText(agentMessage.content)).toBeInTheDocument();
    });

    it('shows timestamp', () => {
      render(<AgentMessageBubble message={agentMessage} agent={agent} />);
      
      // Should format timestamp nicely
      expect(screen.getByText('10:31')).toBeInTheDocument();
    });
  });

  describe('Avatar Display', () => {
    it('shows agent avatar for agent messages', () => {
      render(<AgentMessageBubble message={agentMessage} agent={agent} />);
      
      expect(screen.getByTestId('agent-avatar-P')).toBeInTheDocument();
    });

    it('shows user avatar for user messages', () => {
      render(<AgentMessageBubble message={userMessage} />);
      
      expect(screen.getByTestId('user-avatar')).toBeInTheDocument();
    });

    it('positions avatar on left for agent messages', () => {
      render(<AgentMessageBubble message={agentMessage} agent={agent} />);
      
      const container = screen.getByTestId('message-container-2');
      expect(container).toHaveClass('agent-message');
    });

    it('positions avatar on right for user messages', () => {
      render(<AgentMessageBubble message={userMessage} />);
      
      const container = screen.getByTestId('message-container-1');
      expect(container).toHaveClass('user-message');
    });
  });

  describe('Message States', () => {
    it('shows sending state', () => {
      const sendingMessage = { ...userMessage, status: 'sending' as const };
      render(<AgentMessageBubble message={sendingMessage} />);
      
      const bubble = screen.getByTestId('message-bubble-1');
      expect(bubble).toHaveClass('sending');
    });

    it('shows error state', () => {
      const errorMessage = { ...userMessage, status: 'error' as const };
      render(<AgentMessageBubble message={errorMessage} />);
      
      const bubble = screen.getByTestId('message-bubble-1');
      expect(bubble).toHaveClass('error');
      expect(screen.getByText('Failed to send')).toBeInTheDocument();
    });

    it('shows thinking indicator for streaming messages', () => {
      const streamingMessage = { ...agentMessage, content: '', isStreaming: true };
      render(<AgentMessageBubble message={streamingMessage} agent={agent} />);
      
      expect(screen.getByTestId('thinking-indicator')).toBeInTheDocument();
    });
  });

  describe('Rich Content', () => {
    it('renders code blocks with syntax highlighting', () => {
      const codeMessage = {
        ...agentMessage,
        content: 'Here\'s the code:\n```javascript\nconst hello = "world";\n```'
      };
      render(<AgentMessageBubble message={codeMessage} agent={agent} />);
      
      expect(screen.getByTestId('code-block')).toBeInTheDocument();
      expect(screen.getByText('javascript')).toBeInTheDocument();
    });

    it('renders markdown links', () => {
      const linkMessage = {
        ...agentMessage,
        content: 'Check out [this documentation](https://example.com)'
      };
      render(<AgentMessageBubble message={linkMessage} agent={agent} />);
      
      const link = screen.getByRole('link', { name: 'this documentation' });
      expect(link).toHaveAttribute('href', 'https://example.com');
    });

    it('renders lists properly', () => {
      const listMessage = {
        ...agentMessage,
        content: 'Steps:\n1. First step\n2. Second step\n3. Third step'
      };
      render(<AgentMessageBubble message={listMessage} agent={agent} />);
      
      expect(screen.getByText(/First step/)).toBeInTheDocument();
      expect(screen.getByText(/Second step/)).toBeInTheDocument();
      expect(screen.getByText(/Third step/)).toBeInTheDocument();
    });
  });

  describe('Collapsible Long Messages', () => {
    it('shows expand button for long messages', () => {
      const longContent = 'Lorem ipsum '.repeat(100);
      const longMessage = { ...agentMessage, content: longContent };
      
      render(<AgentMessageBubble message={longMessage} agent={agent} />);
      
      expect(screen.getByRole('button', { name: 'Show more' })).toBeInTheDocument();
    });

    it('does not show expand button for short messages', () => {
      render(<AgentMessageBubble message={agentMessage} agent={agent} />);
      
      expect(screen.queryByRole('button', { name: 'Show more' })).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(<AgentMessageBubble message={agentMessage} agent={agent} />);
      
      const container = screen.getByTestId('message-container-2');
      expect(container).toHaveAttribute('aria-label', 'Message from Patricia at 10:31');
    });

    it('marks user messages appropriately', () => {
      render(<AgentMessageBubble message={userMessage} />);
      
      const container = screen.getByTestId('message-container-1');
      expect(container).toHaveAttribute('aria-label', 'Your message at 10:30');
    });
  });
});