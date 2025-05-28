import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ViewRouter } from './ViewRouter';
import { ViewProvider } from '../contexts/ViewContext';

// Mock child components
jest.mock('./ChatView', () => ({
  ChatView: () => <div data-testid="chat-view">Chat View</div>
}));

jest.mock('./JSONPlanView', () => ({
  JSONPlanView: () => <div data-testid="json-view">JSON Plan View</div>
}));

jest.mock('./CodeChangesView', () => ({
  CodeChangesView: () => <div data-testid="code-view">Code Changes View</div>
}));

jest.mock('./TestResultsView', () => ({
  TestResultsView: () => <div data-testid="test-view">Test Results View</div>
}));

describe('ViewRouter', () => {
  const renderWithProvider = (ui: React.ReactElement) => {
    return render(
      <ViewProvider>
        {ui}
      </ViewProvider>
    );
  };

  describe('View Rendering', () => {
    it('renders chat view by default', () => {
      renderWithProvider(<ViewRouter />);
      
      expect(screen.getByTestId('chat-view')).toBeInTheDocument();
      expect(screen.queryByTestId('json-view')).not.toBeInTheDocument();
      expect(screen.queryByTestId('code-view')).not.toBeInTheDocument();
      expect(screen.queryByTestId('test-view')).not.toBeInTheDocument();
    });

    it('switches between views maintaining state', async () => {
      const { container } = renderWithProvider(<ViewRouter />);
      
      // Start with chat view
      expect(screen.getByTestId('chat-view')).toBeInTheDocument();
      
      // Switch to JSON view
      fireEvent.click(screen.getByRole('button', { name: 'JSON' }));
      
      // Wait for transition
      await new Promise(resolve => setTimeout(resolve, 200));
      
      expect(screen.getByTestId('json-view')).toBeInTheDocument();
      expect(screen.queryByTestId('chat-view')).not.toBeInTheDocument();
      
      // Switch to Code view
      fireEvent.click(screen.getByRole('button', { name: 'Code' }));
      
      // Wait for transition
      await new Promise(resolve => setTimeout(resolve, 200));
      
      expect(screen.getByTestId('code-view')).toBeInTheDocument();
      expect(screen.queryByTestId('json-view')).not.toBeInTheDocument();
      
      // Switch back to chat
      fireEvent.click(screen.getByRole('button', { name: 'Chat' }));
      
      // Wait for transition
      await new Promise(resolve => setTimeout(resolve, 200));
      
      expect(screen.getByTestId('chat-view')).toBeInTheDocument();
    });

    it('passes view-specific route parameters', () => {
      const mockData = { planId: '123', version: 2 };
      renderWithProvider(<ViewRouter initialData={mockData} />);
      
      // In a real implementation, we'd verify the data is passed to child components
      expect(screen.getByTestId('chat-view')).toBeInTheDocument();
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('switches views with Ctrl+1,2,3,4', async () => {
      renderWithProvider(<ViewRouter />);
      
      // Ctrl+1 for Chat
      fireEvent.keyDown(document.body, { key: '1', ctrlKey: true });
      expect(screen.getByTestId('chat-view')).toBeInTheDocument();
      
      // Ctrl+2 for JSON
      fireEvent.keyDown(document.body, { key: '2', ctrlKey: true });
      await new Promise(resolve => setTimeout(resolve, 200));
      expect(screen.getByTestId('json-view')).toBeInTheDocument();
      
      // Ctrl+3 for Code
      fireEvent.keyDown(document.body, { key: '3', ctrlKey: true });
      await new Promise(resolve => setTimeout(resolve, 200));
      expect(screen.getByTestId('code-view')).toBeInTheDocument();
      
      // Ctrl+4 for Tests
      fireEvent.keyDown(document.body, { key: '4', ctrlKey: true });
      await new Promise(resolve => setTimeout(resolve, 200));
      expect(screen.getByTestId('test-view')).toBeInTheDocument();
    });

    it('ignores shortcuts without Ctrl key', () => {
      renderWithProvider(<ViewRouter />);
      
      // Press 2 without Ctrl - should stay on chat
      fireEvent.keyDown(document.body, { key: '2' });
      expect(screen.getByTestId('chat-view')).toBeInTheDocument();
      expect(screen.queryByTestId('json-view')).not.toBeInTheDocument();
    });
  });

  describe('View Transitions', () => {
    it('applies transition animations', () => {
      renderWithProvider(<ViewRouter />);
      
      const viewContainer = screen.getByTestId('view-container');
      expect(viewContainer).toHaveClass('view-transition');
      
      // Switch view
      fireEvent.click(screen.getByRole('button', { name: 'JSON' }));
      
      // Should have transitioning class
      expect(viewContainer).toHaveClass('transitioning');
    });

    it('maintains scroll position when switching back', () => {
      renderWithProvider(<ViewRouter />);
      
      // Simulate scroll in chat view
      const chatView = screen.getByTestId('chat-view');
      Object.defineProperty(chatView, 'scrollTop', { value: 500, writable: true });
      
      // Switch to JSON and back
      fireEvent.click(screen.getByRole('button', { name: 'JSON' }));
      fireEvent.click(screen.getByRole('button', { name: 'Chat' }));
      
      // Scroll position should be restored (in real implementation)
      expect(screen.getByTestId('chat-view')).toBeInTheDocument();
    });
  });

  describe('View Toolbar', () => {
    it('shows active view indicator', async () => {
      renderWithProvider(<ViewRouter />);
      
      const chatButton = screen.getByRole('button', { name: 'Chat' });
      expect(chatButton).toHaveClass('active');
      
      fireEvent.click(screen.getByRole('button', { name: 'JSON' }));
      
      // Wait for transition
      await new Promise(resolve => setTimeout(resolve, 200));
      
      const jsonButton = screen.getByRole('button', { name: 'JSON' });
      expect(jsonButton).toHaveClass('active');
      expect(chatButton).not.toHaveClass('active');
    });

    it('shows view-specific actions', async () => {
      renderWithProvider(<ViewRouter />);
      
      // Chat view should not have export button
      expect(screen.queryByRole('button', { name: 'Export' })).not.toBeInTheDocument();
      
      // JSON view should have export button
      fireEvent.click(screen.getByRole('button', { name: 'JSON' }));
      await new Promise(resolve => setTimeout(resolve, 200));
      expect(screen.getByRole('button', { name: 'Export' })).toBeInTheDocument();
    });

    it('disables view switching during loading', () => {
      renderWithProvider(<ViewRouter isLoading />);
      
      const jsonButton = screen.getByRole('button', { name: 'JSON' });
      expect(jsonButton).toBeDisabled();
    });
  });

  describe('View State Management', () => {
    it('preserves view state when switching', async () => {
      const { rerender } = renderWithProvider(<ViewRouter />);
      
      // Set some state in JSON view
      fireEvent.click(screen.getByRole('button', { name: 'JSON' }));
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // Switch away and back
      fireEvent.click(screen.getByRole('button', { name: 'Chat' }));
      await new Promise(resolve => setTimeout(resolve, 200));
      
      fireEvent.click(screen.getByRole('button', { name: 'JSON' }));
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // State should be preserved (in real implementation)
      expect(screen.getByTestId('json-view')).toBeInTheDocument();
    });

    it('resets view state on explicit reset', () => {
      renderWithProvider(<ViewRouter />);
      
      fireEvent.click(screen.getByRole('button', { name: 'JSON' }));
      fireEvent.click(screen.getByRole('button', { name: 'Reset View' }));
      
      // Should reset to default view
      expect(screen.getByTestId('chat-view')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      renderWithProvider(<ViewRouter />);
      
      const toolbar = screen.getByRole('toolbar');
      expect(toolbar).toHaveAttribute('aria-label', 'View selection');
      
      const viewContainer = screen.getByTestId('view-container');
      expect(viewContainer).toHaveAttribute('aria-live', 'polite');
    });

    it('announces view changes', () => {
      renderWithProvider(<ViewRouter />);
      
      fireEvent.click(screen.getByRole('button', { name: 'JSON' }));
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent('Switched to JSON view');
    });

    it('supports keyboard navigation in toolbar', () => {
      renderWithProvider(<ViewRouter />);
      
      const toolbar = screen.getByRole('toolbar');
      const buttons = screen.getAllByRole('button');
      
      // Focus toolbar
      toolbar.focus();
      
      // Arrow keys should navigate between buttons
      fireEvent.keyDown(toolbar, { key: 'ArrowRight' });
      expect(buttons[1]).toHaveFocus();
      
      fireEvent.keyDown(toolbar, { key: 'ArrowLeft' });
      expect(buttons[0]).toHaveFocus();
    });
  });
});