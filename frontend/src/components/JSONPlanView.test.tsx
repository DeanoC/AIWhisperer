import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import JSONPlanView from './JSONPlanView';
import { ViewProvider } from '../contexts/ViewContext';

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({ value, onChange, ...props }: any) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      {...props}
    />
  ),
}));

describe('JSONPlanView', () => {
  const mockPlanData = {
    id: 'test-plan-123',
    name: 'Test Project Plan',
    version: 1,
    tasks: [
      {
        id: 'task-1',
        name: 'Setup Project',
        description: 'Initialize project structure',
        status: 'completed',
        subtasks: [
          {
            id: 'subtask-1-1',
            name: 'Create directories',
            status: 'completed'
          },
          {
            id: 'subtask-1-2',
            name: 'Install dependencies',
            status: 'in_progress'
          }
        ]
      },
      {
        id: 'task-2',
        name: 'Implement Features',
        description: 'Build core functionality',
        status: 'pending',
        subtasks: []
      }
    ],
    metadata: {
      created: '2024-01-01T00:00:00Z',
      updated: '2024-01-02T00:00:00Z',
      author: 'AI Assistant'
    }
  };

  // Mock jsonRpcService
  const mockJsonRpcService = {
    sendRequest: jest.fn()
  };

  // Setup mock responses
  beforeEach(() => {
    mockJsonRpcService.sendRequest.mockReset();
    
    // Mock plan.list response
    mockJsonRpcService.sendRequest.mockImplementation((method: string, params: any) => {
      if (method === 'plan.list') {
        return Promise.resolve({
          plans: [
            { plan_name: 'test-plan', name: 'Test Project Plan' }
          ]
        });
      }
      if (method === 'plan.read') {
        return Promise.resolve({
          plan: mockPlanData
        });
      }
      return Promise.reject(new Error('Unknown method'));
    });
  });

  const renderWithProvider = (ui: React.ReactElement) => {
    return render(
      <ViewProvider>
        {ui}
      </ViewProvider>
    );
  };

  describe('Tree Navigation', () => {
    it('renders plan tree structure', () => {
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      expect(screen.getByText('Test Project Plan')).toBeInTheDocument();
      expect(screen.getByText('Setup Project')).toBeInTheDocument();
      expect(screen.getByText('Implement Features')).toBeInTheDocument();
    });

    it('shows task status indicators', () => {
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const setupTask = screen.getByTestId('tree-node-task-1');
      expect(setupTask).toHaveClass('status-completed');
      
      const implementTask = screen.getByTestId('tree-node-task-2');
      expect(implementTask).toHaveClass('status-pending');
    });

    it('expands and collapses tree nodes', () => {
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      // Initially collapsed
      expect(screen.queryByText('Create directories')).not.toBeInTheDocument();
      
      // Click to expand
      const expandButton = screen.getByTestId('expand-task-1');
      fireEvent.click(expandButton);
      
      expect(screen.getByText('Create directories')).toBeInTheDocument();
      expect(screen.getByText('Install dependencies')).toBeInTheDocument();
      
      // Click to collapse
      fireEvent.click(expandButton);
      expect(screen.queryByText('Create directories')).not.toBeInTheDocument();
    });

    it('navigates to node on click', () => {
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const taskNode = screen.getByText('Setup Project');
      fireEvent.click(taskNode);
      
      // Should update editor with task data
      const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
      const editorContent = JSON.parse(editor.value);
      expect(editorContent.id).toBe('task-1');
      expect(editorContent.name).toBe('Setup Project');
    });

    it('supports keyboard navigation', () => {
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const tree = screen.getByRole('tree');
      tree.focus();
      
      // Arrow down to next node
      fireEvent.keyDown(tree, { key: 'ArrowDown' });
      expect(screen.getByTestId('tree-node-task-2')).toHaveClass('focused');
      
      // Arrow up to previous node
      fireEvent.keyDown(tree, { key: 'ArrowUp' });
      expect(screen.getByTestId('tree-node-task-1')).toHaveClass('focused');
      
      // Enter to expand
      fireEvent.keyDown(tree, { key: 'Enter' });
      expect(screen.getByText('Create directories')).toBeInTheDocument();
    });
  });

  describe('JSON Editor', () => {
    it('displays formatted JSON', () => {
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
      const content = JSON.parse(editor.value);
      expect(content).toEqual(mockPlanData);
    });

    it('validates JSON on edit', async () => {
      
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
      
      // Clear and type invalid JSON
      await userEvent.clear(editor);
      await userEvent.type(editor, '{ invalid json');
      
      await waitFor(() => {
        expect(screen.getByText(/Invalid JSON/)).toBeInTheDocument();
      });
    });

    it('updates tree on valid JSON edit', async () => {
      
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
      
      // Update task name in JSON
      const updatedData = { ...mockPlanData };
      updatedData.tasks[0].name = 'Updated Task Name';
      
      await userEvent.clear(editor);
      await userEvent.type(editor, JSON.stringify(updatedData, null, 2));
      
      await waitFor(() => {
        expect(screen.getByText('Updated Task Name')).toBeInTheDocument();
      });
    });

    it('supports undo/redo', async () => {
      
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
      const originalValue = editor.value;
      
      // Make a change
      await userEvent.clear(editor);
      await userEvent.type(editor, '{"changed": true}');
      
      // Undo (Ctrl+Z)
      await userEvent.keyboard('{Control>}z{/Control}');
      expect(editor.value).toBe(originalValue);
      
      // Redo (Ctrl+Y)
      await userEvent.keyboard('{Control>}y{/Control}');
      expect(editor.value).toBe('{"changed": true}');
    });

    it('shows syntax highlighting', () => {
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const editor = screen.getByTestId('monaco-editor');
      expect(editor).toHaveAttribute('data-language', 'json');
    });
  });

  describe('Search and Filter', () => {
    it('searches through JSON content', async () => {
      
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const searchInput = screen.getByPlaceholderText('Search JSON...');
      await userEvent.type(searchInput, 'Setup');
      
      // Should highlight search results
      await waitFor(() => {
        const highlights = screen.getAllByTestId('search-highlight');
        expect(highlights).toHaveLength(1);
      });
    });

    it('filters tree nodes by search', async () => {
      
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const searchInput = screen.getByPlaceholderText('Search JSON...');
      await userEvent.type(searchInput, 'dependencies');
      
      // Expand parent to show filtered result
      fireEvent.click(screen.getByTestId('expand-task-1'));
      
      // Should show matching subtask
      expect(screen.getByText('Install dependencies')).toBeInTheDocument();
      // Should hide non-matching subtask
      expect(screen.queryByText('Create directories')).not.toBeInTheDocument();
    });

    it('clears search on escape', async () => {
      
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const searchInput = screen.getByPlaceholderText('Search JSON...');
      await userEvent.type(searchInput, 'test');
      expect(searchInput).toHaveValue('test');
      
      await userEvent.keyboard('{Escape}');
      expect(searchInput).toHaveValue('');
    });
  });

  describe('View Controls', () => {
    it('toggles between tree and editor views', () => {
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      // Both visible by default
      expect(screen.getByTestId('json-tree')).toBeInTheDocument();
      expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
      
      // Hide tree
      fireEvent.click(screen.getByRole('button', { name: 'Hide Tree' }));
      expect(screen.queryByTestId('json-tree')).not.toBeInTheDocument();
      expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
      
      // Hide editor
      fireEvent.click(screen.getByRole('button', { name: 'Show Tree' }));
      fireEvent.click(screen.getByRole('button', { name: 'Hide Editor' }));
      expect(screen.getByTestId('json-tree')).toBeInTheDocument();
      expect(screen.queryByTestId('monaco-editor')).not.toBeInTheDocument();
    });

    it('exports JSON data', () => {
      const mockDownload = jest.fn();
      global.URL.createObjectURL = jest.fn();
      
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const exportButton = screen.getByRole('button', { name: 'Export JSON' });
      fireEvent.click(exportButton);
      
      // Should trigger download
      expect(global.URL.createObjectURL).toHaveBeenCalled();
    });

    it('formats JSON on demand', async () => {
      
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
      
      // Mess up formatting
      await userEvent.clear(editor);
      await userEvent.type(editor, '{"compact":true,"no":"spacing"}');
      
      // Format
      fireEvent.click(screen.getByRole('button', { name: 'Format' }));
      
      await waitFor(() => {
        expect(editor.value).toContain('{\n  "compact": true,\n  "no": "spacing"\n}');
      });
    });
  });

  describe('Error Handling', () => {
    it('handles missing data gracefully', () => {
      renderWithProvider(<JSONPlanView />);
      
      expect(screen.getByText('No plan data available')).toBeInTheDocument();
    });

    it('handles corrupted data', () => {
      const corruptedData = { invalid: 'structure' };
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      expect(screen.getByText(/Invalid plan structure/)).toBeInTheDocument();
    });

    it('recovers from editor errors', async () => {
      
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
      
      // Type invalid JSON
      await userEvent.clear(editor);
      await userEvent.type(editor, '{ broken json');
      
      // Should show error
      expect(screen.getByText(/Invalid JSON/)).toBeInTheDocument();
      
      // Fix the JSON
      await userEvent.clear(editor);
      await userEvent.type(editor, '{"valid": true}');
      
      // Error should disappear
      await waitFor(() => {
        expect(screen.queryByText(/Invalid JSON/)).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      expect(screen.getByRole('tree')).toHaveAttribute('aria-label', 'Plan structure');
      expect(screen.getByTestId('monaco-editor')).toHaveAttribute('aria-label', 'JSON editor');
    });

    it('announces changes to screen readers', async () => {
      
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const searchInput = screen.getByPlaceholderText('Search JSON...');
      await userEvent.type(searchInput, 'test');
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent(/Found \d+ matches/);
    });

    it('supports high contrast mode', () => {
      renderWithProvider(<JSONPlanView jsonRpcService={mockJsonRpcService} />);
      
      const container = screen.getByTestId('json-plan-view');
      expect(container).toHaveClass('supports-high-contrast');
    });
  });
});