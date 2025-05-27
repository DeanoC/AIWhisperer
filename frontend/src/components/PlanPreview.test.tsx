import { render, screen, fireEvent } from '@testing-library/react';
import { PlanPreview } from './PlanPreview';

describe('PlanPreview', () => {
  const plan = {
    tasks: [
      { description: 'Export all user records as CSV', status: 'pending' },
      { description: 'Write tests for export', status: 'pending' }
    ],
    format: 'json'
  };

  it('renders plan tasks', () => {
    render(<PlanPreview plan={plan} />);
    expect(screen.getByText('Export all user records as CSV')).toBeInTheDocument();
    expect(screen.getByText('Write tests for export')).toBeInTheDocument();
  });


  it('expands and collapses plan sections', () => {
    render(<PlanPreview plan={plan} />);
    const firstTask = screen.getByTestId('plan-task-0');
    // Initially collapsed
    expect(screen.queryByText((content) => content.includes('Task details for: Export all user records as CSV'))).not.toBeInTheDocument();
    // Expand
    fireEvent.click(firstTask);
    expect(screen.getByText((content) => content.includes('Task details for: Export all user records as CSV'))).toBeInTheDocument();
    // Collapse
    fireEvent.click(firstTask);
    expect(screen.queryByText((content) => content.includes('Task details for: Export all user records as CSV'))).not.toBeInTheDocument();
  });

  it('shows a message if no plan is available', () => {
    render(<PlanPreview plan={null as any} />);
    expect(screen.getByText('No plan available.')).toBeInTheDocument();
  });
});
