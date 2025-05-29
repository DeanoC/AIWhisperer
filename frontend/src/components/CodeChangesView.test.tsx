import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { CodeChangesView } from './CodeChangesView';
import { ViewProvider } from '../contexts/ViewContext';

// Mock react-diff-viewer-continued
jest.mock('react-diff-viewer-continued', () => ({
  __esModule: true,
  default: ({ oldValue, newValue, splitView }: any) => (
    <div data-testid="diff-viewer">
      <div data-testid="old-value">{oldValue}</div>
      <div data-testid="new-value">{newValue}</div>
      <div data-testid="split-view">{splitView ? 'split' : 'unified'}</div>
    </div>
  ),
}));

describe('CodeChangesView', () => {
  const mockCodeChanges = {
    files: [
      {
        id: 'file-1',
        path: 'src/components/Button.tsx',
        status: 'modified' as const,
        additions: 15,
        deletions: 5,
        oldContent: 'export const Button = () => {\n  return <button>Click</button>;\n};',
        newContent: 'export const Button = ({ onClick, label }) => {\n  return <button onClick={onClick}>{label}</button>;\n};'
      },
      {
        id: 'file-2',
        path: 'src/utils/helpers.ts',
        status: 'added' as const,
        additions: 50,
        deletions: 0,
        oldContent: '',
        newContent: 'export function formatDate(date: Date): string {\n  return date.toISOString();\n}'
      },
      {
        id: 'file-3',
        path: 'src/old-file.js',
        status: 'deleted' as const,
        additions: 0,
        deletions: 30,
        oldContent: 'console.log("deprecated");',
        newContent: ''
      }
    ],
    summary: {
      totalFiles: 3,
      totalAdditions: 65,
      totalDeletions: 35
    }
  };

  const renderWithProvider = (ui: React.ReactElement) => {
    return render(
      <ViewProvider>
        {ui}
      </ViewProvider>
    );
  };

  describe('File List', () => {
    it('displays list of changed files', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      expect(screen.getByText('src/components/Button.tsx')).toBeInTheDocument();
      expect(screen.getByText('src/utils/helpers.ts')).toBeInTheDocument();
      expect(screen.getByText('src/old-file.js')).toBeInTheDocument();
    });

    it('shows file status indicators', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      const modifiedFile = screen.getByTestId('file-item-file-1');
      expect(modifiedFile).toHaveClass('status-modified');
      
      const addedFile = screen.getByTestId('file-item-file-2');
      expect(addedFile).toHaveClass('status-added');
      
      const deletedFile = screen.getByTestId('file-item-file-3');
      expect(deletedFile).toHaveClass('status-deleted');
    });

    it('displays change statistics', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      expect(screen.getByText('+15')).toBeInTheDocument();
      expect(screen.getByText('-5')).toBeInTheDocument();
      expect(screen.getByText('+50')).toBeInTheDocument();
      expect(screen.getByText('-30')).toBeInTheDocument();
    });

    it('selects file on click', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      const fileItem = screen.getByText('src/components/Button.tsx');
      fireEvent.click(fileItem);
      
      expect(screen.getByTestId('file-item-file-1')).toHaveClass('selected');
    });

    it('filters files by search', async () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      const searchInput = screen.getByPlaceholderText('Search files...');
      await userEvent.type(searchInput, 'Button');
      
      expect(screen.getByText('src/components/Button.tsx')).toBeInTheDocument();
      expect(screen.queryByText('src/utils/helpers.ts')).not.toBeInTheDocument();
      expect(screen.queryByText('src/old-file.js')).not.toBeInTheDocument();
    });
  });

  describe('Diff Viewer', () => {
    it('displays diff for selected file', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      const fileItem = screen.getByText('src/components/Button.tsx');
      fireEvent.click(fileItem);
      
      const diffViewer = screen.getByTestId('diff-viewer');
      expect(diffViewer).toBeInTheDocument();
      
      expect(screen.getByTestId('old-value')).toHaveTextContent('export const Button = () =>');
      expect(screen.getByTestId('new-value')).toHaveTextContent('export const Button = ({ onClick, label })');
    });

    it('toggles between split and unified view', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      // Select a file first
      fireEvent.click(screen.getByText('src/components/Button.tsx'));
      
      // Default is split view
      expect(screen.getByTestId('split-view')).toHaveTextContent('split');
      
      // Toggle to unified
      const viewToggle = screen.getByRole('button', { name: 'Unified View' });
      fireEvent.click(viewToggle);
      
      expect(screen.getByTestId('split-view')).toHaveTextContent('unified');
    });

    it('shows empty state for new files', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      const addedFile = screen.getByText('src/utils/helpers.ts');
      fireEvent.click(addedFile);
      
      expect(screen.getByTestId('old-value')).toHaveTextContent('');
      expect(screen.getByTestId('new-value')).toHaveTextContent('export function formatDate');
    });

    it('shows deletion for removed files', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      const deletedFile = screen.getByText('src/old-file.js');
      fireEvent.click(deletedFile);
      
      expect(screen.getByTestId('old-value')).toHaveTextContent('console.log("deprecated")');
      expect(screen.getByTestId('new-value')).toHaveTextContent('');
    });
  });

  describe('View Controls', () => {
    it('collapses/expands file list', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      const fileList = screen.getByTestId('file-list');
      expect(fileList).toBeInTheDocument();
      
      const collapseButton = screen.getByRole('button', { name: 'Hide Files' });
      fireEvent.click(collapseButton);
      
      expect(screen.queryByTestId('file-list')).not.toBeInTheDocument();
      
      const expandButton = screen.getByRole('button', { name: 'Show Files' });
      fireEvent.click(expandButton);
      
      expect(screen.getByTestId('file-list')).toBeInTheDocument();
    });

    it('copies diff to clipboard', async () => {
      Object.assign(navigator, {
        clipboard: {
          writeText: jest.fn().mockResolvedValue(undefined)
        }
      });
      
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      // Select a file
      fireEvent.click(screen.getByText('src/components/Button.tsx'));
      
      const copyButton = screen.getByRole('button', { name: 'Copy Diff' });
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalled();
      });
    });

    it('exports all changes', () => {
      const mockDownload = jest.fn();
      global.URL.createObjectURL = jest.fn();
      
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      const exportButton = screen.getByRole('button', { name: 'Export Changes' });
      fireEvent.click(exportButton);
      
      expect(global.URL.createObjectURL).toHaveBeenCalled();
    });
  });

  describe('Summary Statistics', () => {
    it('displays change summary', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      expect(screen.getByText('3 files changed')).toBeInTheDocument();
      expect(screen.getByText('+65 additions')).toBeInTheDocument();
      expect(screen.getByText('-35 deletions')).toBeInTheDocument();
    });

    it('updates summary on filter', async () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      const searchInput = screen.getByPlaceholderText('Search files...');
      await userEvent.type(searchInput, 'Button');
      
      // Should show filtered stats
      expect(screen.getByText('1 file shown')).toBeInTheDocument();
    });
  });

  describe('Keyboard Navigation', () => {
    it('navigates files with arrow keys', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      const fileList = screen.getByTestId('file-list');
      fileList.focus();
      
      // Arrow down to next file
      fireEvent.keyDown(fileList, { key: 'ArrowDown' });
      expect(screen.getByTestId('file-item-file-2')).toHaveClass('focused');
      
      // Arrow up to previous file
      fireEvent.keyDown(fileList, { key: 'ArrowUp' });
      expect(screen.getByTestId('file-item-file-1')).toHaveClass('focused');
      
      // Enter to select
      fireEvent.keyDown(fileList, { key: 'Enter' });
      expect(screen.getByTestId('file-item-file-1')).toHaveClass('selected');
    });

    it('supports vim-style navigation', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      const fileList = screen.getByTestId('file-list');
      fileList.focus();
      
      // j for down
      fireEvent.keyDown(fileList, { key: 'j' });
      expect(screen.getByTestId('file-item-file-2')).toHaveClass('focused');
      
      // k for up
      fireEvent.keyDown(fileList, { key: 'k' });
      expect(screen.getByTestId('file-item-file-1')).toHaveClass('focused');
    });
  });

  describe('Error Handling', () => {
    it('handles missing data gracefully', () => {
      renderWithProvider(<CodeChangesView />);
      
      expect(screen.getByText('No code changes available')).toBeInTheDocument();
    });

    it('handles empty file list', () => {
      const emptyData = { files: [], summary: { totalFiles: 0, totalAdditions: 0, totalDeletions: 0 } };
      renderWithProvider(<CodeChangesView data={emptyData} />);
      
      expect(screen.getByText('No files changed')).toBeInTheDocument();
    });

    it('handles files with missing content', () => {
      const brokenData = {
        files: [{
          id: 'broken',
          path: 'broken.js',
          status: 'modified' as const,
          additions: 0,
          deletions: 0
        }],
        summary: { totalFiles: 1, totalAdditions: 0, totalDeletions: 0 }
      };
      
      renderWithProvider(<CodeChangesView data={brokenData} />);
      
      fireEvent.click(screen.getByText('broken.js'));
      expect(screen.getByText('Content not available')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      expect(screen.getByRole('list')).toHaveAttribute('aria-label', 'Changed files');
      expect(screen.getByRole('region')).toHaveAttribute('aria-label', 'Code diff viewer');
    });

    it('announces file selection', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      fireEvent.click(screen.getByText('src/components/Button.tsx'));
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent('Viewing src/components/Button.tsx');
    });

    it('supports high contrast mode', () => {
      renderWithProvider(<CodeChangesView data={mockCodeChanges} />);
      
      const container = screen.getByTestId('code-changes-view');
      expect(container).toHaveClass('supports-high-contrast');
    });
  });

  describe('Performance', () => {
    it('virtualizes long file lists', () => {
      const manyFiles = {
        files: Array(100).fill(null).map((_, i) => ({
          id: `file-${i}`,
          path: `src/file-${i}.ts`,
          status: 'modified' as const,
          additions: i,
          deletions: i,
          oldContent: 'old',
          newContent: 'new'
        })),
        summary: { totalFiles: 100, totalAdditions: 5000, totalDeletions: 5000 }
      };
      
      renderWithProvider(<CodeChangesView data={manyFiles} />);
      
      // Should only render visible items
      const renderedItems = screen.getAllByTestId(/file-item-/);
      expect(renderedItems.length).toBeLessThan(100);
    });
  });
});