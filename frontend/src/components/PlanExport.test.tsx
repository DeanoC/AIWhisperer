import { render, screen, fireEvent } from '@testing-library/react';
import { PlanExport } from './PlanExport';

describe('PlanExport', () => {
  const plan = { tasks: [{ description: 'Export', status: 'pending' }], format: 'json' };

  it('renders export button', () => {
    render(<PlanExport plan={plan} />);
    expect(screen.getByTestId('export-plan-btn')).toBeInTheDocument();
  });

  it('triggers download when clicked (mocked)', () => {
    render(<PlanExport plan={plan} filename="test-plan.json" />);
    const anchor = document.createElement('a');
    anchor.setAttribute = jest.fn();
    anchor.click = jest.fn();
    anchor.remove = jest.fn();
    const createElementSpy = jest.spyOn(document, 'createElement').mockReturnValue(anchor as any);
    const appendChildSpy = jest.spyOn(document.body, 'appendChild').mockImplementation((node) => node);
    fireEvent.click(screen.getByTestId('export-plan-btn'));
    expect(createElementSpy).toHaveBeenCalledWith('a');
    expect(anchor.click).toHaveBeenCalled();
    expect(anchor.remove).toHaveBeenCalled();
    createElementSpy.mockRestore();
    appendChildSpy.mockRestore();
  });
});
