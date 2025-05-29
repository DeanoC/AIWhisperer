import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AgentSidebar } from './AgentSidebar';
import { Agent } from '../types/agent';
import { AIService } from '../services/aiService';

describe('AgentSidebar', () => {
  const mockAgents: Agent[] = [
    {
      id: 'P',
      name: 'Patricia',
      role: 'Planner',
      description: 'Creates project plans',
      color: '#8B5CF6',
      status: 'online'
    },
    {
      id: 'T',
      name: 'Tessa',
      role: 'Tester',
      description: 'Writes and runs tests',
      color: '#3B82F6',
      status: 'online'
    },
    {
      id: 'D',
      name: 'David',
      role: 'Developer',
      description: 'Implements features',
      color: '#F97316',
      status: 'busy'
    },
    {
      id: 'R',
      name: 'Rachel',
      role: 'Reviewer',
      description: 'Reviews code',
      color: '#10B981',
      status: 'offline'
    }
  ];

  let mockAIService: any;
  let defaultProps: any;

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockAIService = {
      listAgents: jest.fn().mockResolvedValue(mockAgents),
      getCurrentAgent: jest.fn().mockResolvedValue('P'),
      switchAgent: jest.fn().mockResolvedValue(undefined),
    };

    defaultProps = {
      aiService: mockAIService,
      onAgentSelect: jest.fn(),
      disabled: false,
    };
  });

  it('renders list of agents from agent.list API', async () => {
    // Ensure the mock is working
    expect(mockAIService.listAgents()).resolves.toEqual(mockAgents);
    
    render(<AgentSidebar {...defaultProps} />);
    
    await waitFor(() => {
      expect(mockAIService.listAgents).toHaveBeenCalled();
    });

    // Debug: log what's in the DOM
    // screen.debug();

    // Check all agents are rendered
    await waitFor(() => {
      expect(screen.getByText('Patricia')).toBeInTheDocument();
    });
    expect(screen.getByText('Tessa')).toBeInTheDocument();
    expect(screen.getByText('David')).toBeInTheDocument();
    expect(screen.getByText('Rachel')).toBeInTheDocument();
  });

  it('shows current agent as active', async () => {
    render(<AgentSidebar {...defaultProps} />);
    
    await waitFor(() => {
      expect(mockAIService.getCurrentAgent).toHaveBeenCalled();
    });

    await waitFor(() => {
      const patriciaCard = screen.getByTestId('agent-card-P');
      expect(patriciaCard).toHaveClass('active');
    });
  });

  it('click agent triggers switchAgent', async () => {
    render(<AgentSidebar {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Tessa')).toBeInTheDocument();
    });

    await waitFor(async () => {
      fireEvent.click(screen.getByTestId('agent-card-T'));
    });
    
    await waitFor(() => {
      expect(mockAIService.switchAgent).toHaveBeenCalledWith('T');
      expect(defaultProps.onAgentSelect).toHaveBeenCalledWith('T');
    });
  });

  it('disabled during agent switch', async () => {
    render(<AgentSidebar {...defaultProps} disabled={true} />);
    
    await waitFor(() => {
      expect(screen.getByText('Tessa')).toBeInTheDocument();
    });

    const tessaCard = screen.getByTestId('agent-card-T');
    expect(tessaCard).toHaveClass('disabled');
    
    fireEvent.click(tessaCard);
    expect(mockAIService.switchAgent).not.toHaveBeenCalled();
  });

  it('shows agent descriptions on hover', async () => {
    render(<AgentSidebar {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Patricia')).toBeInTheDocument();
    });

    const patriciaCard = screen.getByTestId('agent-card-P');
    
    // Description should not be visible initially
    expect(screen.queryByText('Creates project plans')).not.toBeVisible();
    
    // Hover to show description
    fireEvent.mouseEnter(patriciaCard);
    expect(screen.getByText('Creates project plans')).toBeVisible();
    
    // Leave to hide description
    fireEvent.mouseLeave(patriciaCard);
    expect(screen.queryByText('Creates project plans')).not.toBeVisible();
  });

  it('keyboard navigation (up/down arrows)', async () => {
    render(<AgentSidebar {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Patricia')).toBeInTheDocument();
    });

    const container = screen.getByTestId('agent-sidebar');
    
    // Focus the sidebar
    container.focus();
    
    // Press down arrow - should focus Tessa
    fireEvent.keyDown(container, { key: 'ArrowDown' });
    expect(document.activeElement).toBe(screen.getByTestId('agent-card-T'));
    
    // Press down again - should focus David
    fireEvent.keyDown(container, { key: 'ArrowDown' });
    expect(document.activeElement).toBe(screen.getByTestId('agent-card-D'));
    
    // Press up - should go back to Tessa
    fireEvent.keyDown(container, { key: 'ArrowUp' });
    expect(document.activeElement).toBe(screen.getByTestId('agent-card-T'));
    
    // Press Enter - should select Tessa
    fireEvent.keyDown(container, { key: 'Enter' });
    expect(mockAIService.switchAgent).toHaveBeenCalledWith('T');
  });

  it('shows agent status indicators', async () => {
    render(<AgentSidebar {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Patricia')).toBeInTheDocument();
    });

    // Check status indicators
    const patriciaStatus = screen.getByTestId('agent-status-P');
    expect(patriciaStatus).toHaveClass('status-online');
    
    const davidStatus = screen.getByTestId('agent-status-D');
    expect(davidStatus).toHaveClass('status-busy');
    
    const rachelStatus = screen.getByTestId('agent-status-R');
    expect(rachelStatus).toHaveClass('status-offline');
  });

  it('handles error when fetching agents fails', async () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation();
    mockAIService.listAgents.mockRejectedValueOnce(new Error('Network error'));
    
    render(<AgentSidebar {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load agents')).toBeInTheDocument();
    });
    
    consoleError.mockRestore();
  });

  it('refreshes agent list when aiService changes', async () => {
    const { rerender } = render(<AgentSidebar {...defaultProps} />);
    
    await waitFor(() => {
      expect(mockAIService.listAgents).toHaveBeenCalledTimes(1);
    });

    const newAIService = {
      ...mockAIService,
      listAgents: jest.fn().mockResolvedValue([mockAgents[0]]),
    } as unknown as AIService;

    rerender(<AgentSidebar {...defaultProps} aiService={newAIService} />);
    
    await waitFor(() => {
      expect(newAIService.listAgents).toHaveBeenCalled();
    });
  });

  it('shows loading state while fetching agents', () => {
    render(<AgentSidebar {...defaultProps} />);
    
    expect(screen.getByTestId('agent-sidebar-loading')).toBeInTheDocument();
  });
});