import { render, screen, fireEvent } from '@testing-library/react';
import { PlanConfirmation } from './PlanConfirmation';

describe('PlanConfirmation', () => {
  it('calls onConfirm when confirm button is clicked', () => {
    const onConfirm = jest.fn();
    const onReject = jest.fn();
    render(<PlanConfirmation onConfirm={onConfirm} onReject={onReject} />);
    fireEvent.click(screen.getByTestId('confirm-plan-btn'));
    expect(onConfirm).toHaveBeenCalled();
  });

  it('calls onReject when reject button is clicked', () => {
    const onConfirm = jest.fn();
    const onReject = jest.fn();
    render(<PlanConfirmation onConfirm={onConfirm} onReject={onReject} />);
    fireEvent.click(screen.getByTestId('reject-plan-btn'));
    expect(onReject).toHaveBeenCalled();
  });

  it('disables buttons when disabled is true', () => {
    render(<PlanConfirmation onConfirm={() => {}} onReject={() => {}} disabled />);
    expect(screen.getByTestId('confirm-plan-btn')).toBeDisabled();
    expect(screen.getByTestId('reject-plan-btn')).toBeDisabled();
  });
});
