import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { ContextPanel } from './ContextPanel';

// Mock AgentInspectorPanel
jest.mock('./AgentInspectorPanel', () => ({
  AgentInspectorPanel: () => <div data-testid="agent-inspector">Agent Inspector Panel</div>
}));

// Mock PlanPreview
jest.mock('./PlanPreview', () => ({
  PlanPreview: ({ plan }: any) => (
    <div data-testid="plan-preview">
      Plan Preview: {plan?.name || 'No plan'}
    </div>
  )
}));

// Mock AgentAvatar
jest.mock('./AgentAvatar', () => ({
  AgentAvatar: ({ agent }: any) => (
    <div data-testid="agent-avatar" style={{ backgroundColor: agent.color }}>
      {agent.icon || agent.name.charAt(0)}
    </div>
  )
}));

describe('ContextPanel', () => {
  const mockAgent = {
    id: 'agent-1',
    name: 'Code Assistant',
    role: 'Developer',
    color: '#4CAF50',
    icon: '🤖',
    status: 'online' as const,
    context: {
      files: ['src/App.tsx', 'src/index.ts'],
      variables: { projectName: 'Test Project' },
      history: ['Created component', 'Fixed bug']
    }
  };

  const mockPlan = {
    id: 'plan-1',
    name: 'Feature Implementation',
    tasks: [
      { id: 'task-1', name: 'Setup', status: 'completed' },
      { id: 'task-2', name: 'Implementation', status: 'in_progress' }
    ]
  };

  const defaultProps = {
    collapsed: false,
    onCollapse: jest.fn(),
    disabled: false,
    currentAgent: mockAgent,
    currentPlan: mockPlan
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders context panel with header', () => {
      render(<ContextPanel {...defaultProps} />);
      
      expect(screen.getByTestId('context-panel')).toBeInTheDocument();
      expect(screen.getByText('Context')).toBeInTheDocument();
    });

    it('renders tabs for different views', () => {
      render(<ContextPanel {...defaultProps} />);
      
      expect(screen.getByRole('tab', { name: 'Agent' })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Plan' })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'History' })).toBeInTheDocument();
    });

    it('renders agent inspector panel in agent tab', () => {
      render(<ContextPanel {...defaultProps} />);
      
      expect(screen.getByTestId('agent-inspector')).toBeInTheDocument();
    });

    it('renders plan preview in plan tab', () => {
      render(<ContextPanel {...defaultProps} />);
      
      fireEvent.click(screen.getByRole('tab', { name: 'Plan' }));
      
      expect(screen.getByTestId('plan-preview')).toBeInTheDocument();
      expect(screen.getByText('Plan Preview: Feature Implementation')).toBeInTheDocument();
    });
  });

  describe('Collapsed State', () => {
    it('shows minimal view when collapsed', () => {
      render(<ContextPanel {...defaultProps} collapsed={true} />);
      
      const panel = screen.getByTestId('context-panel');
      expect(panel).toHaveClass('collapsed');
      
      // Should only show icons
      expect(screen.queryByText('Context')).not.toBeInTheDocument();
      expect(screen.getByTestId('collapsed-indicators')).toBeInTheDocument();
    });

    it('shows agent status indicator when collapsed', () => {
      render(<ContextPanel {...defaultProps} collapsed={true} />);
      
      const agentIndicator = screen.getByTestId('agent-status-indicator');
      expect(agentIndicator).toHaveClass('status-active');
    });

    it('shows plan progress when collapsed', () => {
      render(<ContextPanel {...defaultProps} collapsed={true} />);
      
      const progressIndicator = screen.getByTestId('plan-progress-indicator');
      expect(progressIndicator).toHaveTextContent('1/2');
    });

    it('calls onCollapse when header clicked', () => {
      render(<ContextPanel {...defaultProps} />);
      
      const collapseButton = screen.getByRole('button', { name: 'Collapse panel' });
      fireEvent.click(collapseButton);
      
      expect(defaultProps.onCollapse).toHaveBeenCalledWith(true);
    });
  });

  describe('Tab Navigation', () => {
    it('switches between tabs', () => {
      render(<ContextPanel {...defaultProps} />);
      
      // Agent tab is active by default
      expect(screen.getByRole('tab', { name: 'Agent' })).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByTestId('agent-inspector')).toBeInTheDocument();
      
      // Switch to Plan tab
      fireEvent.click(screen.getByRole('tab', { name: 'Plan' }));
      
      expect(screen.getByRole('tab', { name: 'Plan' })).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByTestId('plan-preview')).toBeInTheDocument();
      expect(screen.queryByTestId('agent-inspector')).not.toBeInTheDocument();
    });

    it('maintains tab selection when props change', () => {
      const { rerender } = render(<ContextPanel {...defaultProps} />);
      
      // Switch to History tab
      fireEvent.click(screen.getByRole('tab', { name: 'History' }));
      
      // Update props
      rerender(<ContextPanel {...defaultProps} currentAgent={{ ...mockAgent, name: 'Updated' }} />);
      
      // Should still be on History tab
      expect(screen.getByRole('tab', { name: 'History' })).toHaveAttribute('aria-selected', 'true');
    });

    it('supports keyboard navigation between tabs', () => {
      render(<ContextPanel {...defaultProps} />);
      
      const agentTab = screen.getByRole('tab', { name: 'Agent' });
      agentTab.focus();
      
      // Arrow right to next tab
      fireEvent.keyDown(agentTab, { key: 'ArrowRight' });
      expect(screen.getByRole('tab', { name: 'Plan' })).toHaveFocus();
      
      // Arrow left back
      fireEvent.keyDown(document.activeElement!, { key: 'ArrowLeft' });
      expect(screen.getByRole('tab', { name: 'Agent' })).toHaveFocus();
    });
  });

  describe('History Tab', () => {
    it('displays action history', () => {
      render(<ContextPanel {...defaultProps} />);
      
      fireEvent.click(screen.getByRole('tab', { name: 'History' }));
      
      expect(screen.getByText('Created component')).toBeInTheDocument();
      expect(screen.getByText('Fixed bug')).toBeInTheDocument();
    });

    it('shows empty state when no history', () => {
      const agentWithoutHistory = { ...mockAgent, context: { ...mockAgent.context, history: [] } };
      render(<ContextPanel {...defaultProps} currentAgent={agentWithoutHistory} />);
      
      fireEvent.click(screen.getByRole('tab', { name: 'History' }));
      
      expect(screen.getByText('No history available')).toBeInTheDocument();
    });

    it('allows filtering history', async () => {
      
      render(<ContextPanel {...defaultProps} />);
      
      fireEvent.click(screen.getByRole('tab', { name: 'History' }));
      
      const filterInput = screen.getByPlaceholderText('Filter history...');
      await userEvent.type(filterInput, 'bug');
      
      expect(screen.getByText('Fixed bug')).toBeInTheDocument();
      expect(screen.queryByText('Created component')).not.toBeInTheDocument();
    });
  });

  describe('Quick Actions', () => {
    it('shows quick action buttons', () => {
      render(<ContextPanel {...defaultProps} />);
      
      expect(screen.getByRole('button', { name: 'Refresh context' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Export context' })).toBeInTheDocument();
    });

    it('handles refresh action', () => {
      const onRefresh = jest.fn();
      render(<ContextPanel {...defaultProps} onRefresh={onRefresh} />);
      
      fireEvent.click(screen.getByRole('button', { name: 'Refresh context' }));
      
      expect(onRefresh).toHaveBeenCalled();
    });

    it('exports context data', () => {
      global.URL.createObjectURL = jest.fn();
      render(<ContextPanel {...defaultProps} />);
      
      fireEvent.click(screen.getByRole('button', { name: 'Export context' }));
      
      expect(global.URL.createObjectURL).toHaveBeenCalled();
    });
  });

  describe('Loading and Error States', () => {
    it('shows loading state', () => {
      render(<ContextPanel {...defaultProps} isLoading />);
      
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
      expect(screen.getByText('Loading context...')).toBeInTheDocument();
    });

    it('shows error state', () => {
      render(<ContextPanel {...defaultProps} error="Failed to load context" />);
      
      expect(screen.getByText('Failed to load context')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
    });

    it('handles retry action', () => {
      const onRetry = jest.fn();
      render(<ContextPanel {...defaultProps} error="Error" onRetry={onRetry} />);
      
      fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
      
      expect(onRetry).toHaveBeenCalled();
    });
  });

  describe('Disabled State', () => {
    it('disables all interactive elements when disabled', () => {
      render(<ContextPanel {...defaultProps} disabled={true} />);
      
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toBeDisabled();
      });
      
      const tabs = screen.getAllByRole('tab');
      tabs.forEach(tab => {
        expect(tab).toHaveAttribute('aria-disabled', 'true');
      });
    });
  });

  describe('Empty States', () => {
    it('shows no agent message when agent is null', () => {
      render(<ContextPanel {...defaultProps} currentAgent={null} />);
      
      expect(screen.getByText('No agent selected')).toBeInTheDocument();
    });

    it('shows no plan message when plan is null', () => {
      render(<ContextPanel {...defaultProps} currentPlan={null} />);
      
      fireEvent.click(screen.getByRole('tab', { name: 'Plan' }));
      
      expect(screen.getByText('No active plan')).toBeInTheDocument();
    });
  });

  describe('Real-time Updates', () => {
    it('updates when agent changes', () => {
      const { rerender } = render(<ContextPanel {...defaultProps} />);
      
      expect(screen.getByTestId('agent-inspector')).toBeInTheDocument();
      
      const newAgent = { ...mockAgent, name: 'Updated Agent' };
      rerender(<ContextPanel {...defaultProps} currentAgent={newAgent} />);
      
      // Agent inspector should receive updated props
      expect(screen.getByTestId('agent-inspector')).toBeInTheDocument();
    });

    it('shows notification badge for new history items', () => {
      const { rerender } = render(<ContextPanel {...defaultProps} />);
      
      // Add new history item
      const updatedAgent = {
        ...mockAgent,
        context: {
          ...mockAgent.context,
          history: [...mockAgent.context.history, 'New action']
        }
      };
      
      rerender(<ContextPanel {...defaultProps} currentAgent={updatedAgent} />);
      
      const historyTab = screen.getByRole('tab', { name: 'History' });
      expect(historyTab.querySelector('.notification-badge')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(<ContextPanel {...defaultProps} />);
      
      expect(screen.getByRole('complementary')).toHaveAttribute('aria-label', 'Context panel');
      expect(screen.getByRole('tablist')).toHaveAttribute('aria-label', 'Context views');
    });

    it('announces tab changes', () => {
      render(<ContextPanel {...defaultProps} />);
      
      fireEvent.click(screen.getByRole('tab', { name: 'Plan' }));
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent('Viewing Plan context');
    });

    it('manages focus correctly', () => {
      const { rerender } = render(<ContextPanel {...defaultProps} />);
      
      const planTab = screen.getByRole('tab', { name: 'Plan' });
      planTab.focus();
      
      // Collapse panel
      rerender(<ContextPanel {...defaultProps} collapsed={true} />);
      
      // Focus should move to collapse button
      expect(screen.getByRole('button', { name: 'Expand panel' })).toHaveFocus();
    });
  });
});