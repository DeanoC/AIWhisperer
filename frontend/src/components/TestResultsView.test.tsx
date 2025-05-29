import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { TestResultsView } from './TestResultsView';
import { ViewProvider } from '../contexts/ViewContext';

describe('TestResultsView', () => {
  const mockTestResults = {
    summary: {
      total: 156,
      passed: 142,
      failed: 8,
      skipped: 6,
      duration: 12.5
    },
    suites: [
      {
        id: 'suite-1',
        name: 'Component Tests',
        path: 'src/components',
        status: 'failed' as const,
        duration: 4.2,
        tests: [
          {
            id: 'test-1-1',
            name: 'renders correctly',
            status: 'passed' as const,
            duration: 0.045
          },
          {
            id: 'test-1-2',
            name: 'handles user interaction',
            status: 'failed' as const,
            duration: 0.123,
            error: {
              message: 'Expected button to be disabled',
              stack: 'at Button.test.tsx:45:23'
            }
          },
          {
            id: 'test-1-3',
            name: 'validates props',
            status: 'skipped' as const,
            duration: 0,
            skipReason: 'Pending implementation'
          }
        ]
      },
      {
        id: 'suite-2',
        name: 'API Tests',
        path: 'src/api',
        status: 'passed' as const,
        duration: 8.3,
        tests: [
          {
            id: 'test-2-1',
            name: 'fetches data successfully',
            status: 'passed' as const,
            duration: 2.1
          },
          {
            id: 'test-2-2',
            name: 'handles errors gracefully',
            status: 'passed' as const,
            duration: 1.5
          }
        ]
      }
    ]
  };

  const renderWithProvider = (ui: React.ReactElement) => {
    return render(
      <ViewProvider>
        {ui}
      </ViewProvider>
    );
  };

  describe('Test Summary', () => {
    it('displays test summary statistics', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      expect(screen.getByText('156 tests')).toBeInTheDocument();
      expect(screen.getByText('142 passed')).toBeInTheDocument();
      expect(screen.getByText('8 failed')).toBeInTheDocument();
      expect(screen.getByText('6 skipped')).toBeInTheDocument();
      expect(screen.getByText('12.5s')).toBeInTheDocument();
    });

    it('shows pass rate percentage', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      // 142/156 = 91%
      expect(screen.getByText(/91%/)).toBeInTheDocument();
    });

    it('displays visual progress bar', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      const progressBar = screen.getByTestId('progress-bar');
      expect(progressBar).toHaveStyle({ width: '91%' });
    });
  });

  describe('Test Suites', () => {
    it('displays test suite hierarchy', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      expect(screen.getByText('Component Tests')).toBeInTheDocument();
      expect(screen.getByText('API Tests')).toBeInTheDocument();
    });

    it('shows suite status indicators', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      const failedSuite = screen.getByTestId('suite-suite-1');
      expect(failedSuite).toHaveClass('status-failed');
      
      const passedSuite = screen.getByTestId('suite-suite-2');
      expect(passedSuite).toHaveClass('status-passed');
    });

    it('expands/collapses test suites', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      // Initially collapsed
      expect(screen.queryByText('renders correctly')).not.toBeInTheDocument();
      
      // Click to expand
      const expandButton = screen.getByTestId('expand-suite-1');
      fireEvent.click(expandButton);
      
      expect(screen.getByText('renders correctly')).toBeInTheDocument();
      expect(screen.getByText('handles user interaction')).toBeInTheDocument();
    });

    it('shows suite-level statistics', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      // Expand first suite
      fireEvent.click(screen.getByTestId('expand-suite-1'));
      
      const suiteStats = screen.getByTestId('suite-stats-suite-1');
      expect(suiteStats).toHaveTextContent('1/3');
      expect(suiteStats).toHaveTextContent('4.2s');
    });
  });

  describe('Individual Tests', () => {
    it('displays test results with status icons', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      // Expand suite
      fireEvent.click(screen.getByTestId('expand-suite-1'));
      
      const passedTest = screen.getByTestId('test-test-1-1');
      expect(passedTest).toHaveClass('status-passed');
      
      const failedTest = screen.getByTestId('test-test-1-2');
      expect(failedTest).toHaveClass('status-failed');
      
      const skippedTest = screen.getByTestId('test-test-1-3');
      expect(skippedTest).toHaveClass('status-skipped');
    });

    it('shows test duration', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      fireEvent.click(screen.getByTestId('expand-suite-1'));
      
      expect(screen.getByText('45ms')).toBeInTheDocument();
      expect(screen.getByText('123ms')).toBeInTheDocument();
    });

    it('displays error details for failed tests', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      fireEvent.click(screen.getByTestId('expand-suite-1'));
      
      const failedTest = screen.getByText('handles user interaction');
      fireEvent.click(failedTest);
      
      expect(screen.getByText('Expected button to be disabled')).toBeInTheDocument();
      expect(screen.getByText('at Button.test.tsx:45:23')).toBeInTheDocument();
    });

    it('shows skip reason for skipped tests', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      fireEvent.click(screen.getByTestId('expand-suite-1'));
      
      expect(screen.getByText('Pending implementation')).toBeInTheDocument();
    });
  });

  describe('Filtering and Search', () => {
    it('filters tests by status', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      // Click failed filter
      const failedFilter = screen.getByRole('button', { name: 'Failed' });
      fireEvent.click(failedFilter);
      
      // Only failed suite should be visible
      expect(screen.getByText('Component Tests')).toBeInTheDocument();
      expect(screen.queryByText('API Tests')).not.toBeInTheDocument();
    });

    it('searches through test names', async () => {
      
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      const searchInput = screen.getByPlaceholderText('Search tests...');
      await userEvent.type(searchInput, 'interaction');
      
      // Expand suite to see filtered results
      fireEvent.click(screen.getByTestId('expand-suite-1'));
      
      expect(screen.getByText('handles user interaction')).toBeInTheDocument();
      expect(screen.queryByText('renders correctly')).not.toBeInTheDocument();
    });

    it('shows filtered count', async () => {
      
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      const searchInput = screen.getByPlaceholderText('Search tests...');
      await userEvent.type(searchInput, 'API');
      
      expect(screen.getByText('2 tests shown')).toBeInTheDocument();
    });

    it('clears filters', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      // Apply filter
      fireEvent.click(screen.getByRole('button', { name: 'Failed' }));
      expect(screen.queryByText('API Tests')).not.toBeInTheDocument();
      
      // Clear filters
      fireEvent.click(screen.getByRole('button', { name: 'Clear Filters' }));
      expect(screen.getByText('API Tests')).toBeInTheDocument();
    });
  });

  describe('Actions', () => {
    it('re-runs failed tests', () => {
      const onRerun = jest.fn();
      renderWithProvider(<TestResultsView data={mockTestResults} onRerun={onRerun} />);
      
      const rerunButton = screen.getByRole('button', { name: 'Re-run Failed' });
      fireEvent.click(rerunButton);
      
      expect(onRerun).toHaveBeenCalledWith(['test-1-2']);
    });

    it('exports test results', () => {
      global.URL.createObjectURL = jest.fn();
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      const exportButton = screen.getByRole('button', { name: 'Export Results' });
      fireEvent.click(exportButton);
      
      expect(global.URL.createObjectURL).toHaveBeenCalled();
    });

    it('copies test output to clipboard', async () => {
      Object.assign(navigator, {
        clipboard: {
          writeText: jest.fn().mockResolvedValue(undefined)
        }
      });
      
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      fireEvent.click(screen.getByTestId('expand-suite-1'));
      fireEvent.click(screen.getByText('handles user interaction'));
      
      const copyButton = screen.getByRole('button', { name: 'Copy Error' });
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
          expect.stringContaining('Expected button to be disabled')
        );
      });
    });
  });

  describe('View Options', () => {
    it('toggles between tree and flat view', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      // Default is tree view
      expect(screen.getByTestId('tree-view')).toBeInTheDocument();
      
      // Switch to flat view
      const flatViewButton = screen.getByRole('button', { name: 'Flat View' });
      fireEvent.click(flatViewButton);
      
      expect(screen.getByTestId('flat-view')).toBeInTheDocument();
    });

    it('sorts tests by different criteria', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      const sortDropdown = screen.getByRole('combobox', { name: 'Sort by' });
      
      // Sort by duration
      fireEvent.change(sortDropdown, { target: { value: 'duration' } });
      
      // First item should be the longest running suite
      const suites = screen.getAllByTestId(/suite-/);
      expect(suites[0]).toHaveTextContent('API Tests');
    });

    it('groups tests by status', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      const groupCheckbox = screen.getByRole('checkbox', { name: 'Group by status' });
      fireEvent.click(groupCheckbox);
      
      expect(screen.getByText('Failed (8)')).toBeInTheDocument();
      expect(screen.getByText('Passed (142)')).toBeInTheDocument();
      expect(screen.getByText('Skipped (6)')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles missing data gracefully', () => {
      renderWithProvider(<TestResultsView />);
      
      expect(screen.getByText('No test results available')).toBeInTheDocument();
    });

    it('handles empty test results', () => {
      const emptyData = {
        summary: { total: 0, passed: 0, failed: 0, skipped: 0, duration: 0 },
        suites: []
      };
      
      renderWithProvider(<TestResultsView data={emptyData} />);
      
      expect(screen.getByText('No tests found')).toBeInTheDocument();
    });

    it('handles malformed error data', () => {
      const malformedData = {
        summary: { total: 1, passed: 0, failed: 1, skipped: 0, duration: 0.1 },
        suites: [{
          id: 'bad',
          name: 'Bad Suite',
          path: 'test',
          status: 'failed' as const,
          duration: 0.1,
          tests: [{
            id: 'bad-test',
            name: 'broken test',
            status: 'failed' as const,
            duration: 0.1
            // Missing error property
          }]
        }]
      };
      
      renderWithProvider(<TestResultsView data={malformedData} />);
      
      fireEvent.click(screen.getByTestId('expand-bad'));
      fireEvent.click(screen.getByText('broken test'));
      
      expect(screen.getByText('Error details not available')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      expect(screen.getByRole('tree')).toHaveAttribute('aria-label', 'Test results');
      expect(screen.getByRole('region')).toHaveAttribute('aria-label', 'Test summary');
    });

    it('announces test result changes', async () => {
      
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      const searchInput = screen.getByPlaceholderText('Search tests...');
      await userEvent.type(searchInput, 'API');
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent('Showing 2 of 156 tests');
    });

    it('supports keyboard navigation', () => {
      renderWithProvider(<TestResultsView data={mockTestResults} />);
      
      const tree = screen.getByRole('tree');
      tree.focus();
      
      // Arrow down to navigate
      fireEvent.keyDown(tree, { key: 'ArrowDown' });
      expect(screen.getByTestId('suite-suite-2')).toHaveClass('focused');
      
      // Enter to expand
      fireEvent.keyDown(tree, { key: 'Enter' });
      expect(screen.getByText('fetches data successfully')).toBeInTheDocument();
    });
  });
});