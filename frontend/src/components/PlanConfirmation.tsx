import React from 'react';

export interface PlanConfirmationProps {
  onConfirm: () => void;
  onReject: () => void;
  disabled?: boolean;
}

export const PlanConfirmation: React.FC<PlanConfirmationProps> = ({ onConfirm, onReject, disabled }) => (
  <div className="plan-confirmation" style={{ marginTop: 16, display: 'flex', gap: 12 }}>
    <button onClick={onConfirm} disabled={disabled} data-testid="confirm-plan-btn" style={{ background: '#4CAF50', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 4 }}>
      Confirm Plan
    </button>
    <button onClick={onReject} disabled={disabled} data-testid="reject-plan-btn" style={{ background: '#F44336', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 4 }}>
      Reject Plan
    </button>
  </div>
);
