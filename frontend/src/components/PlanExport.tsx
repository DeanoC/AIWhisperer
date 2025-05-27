import React from 'react';

export interface PlanExportProps {
  plan: object;
  filename?: string;
}

export const PlanExport: React.FC<PlanExportProps> = ({ plan, filename = 'plan.json' }) => {
  const handleExport = () => {
    const dataStr = 'data:application/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(plan, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute('href', dataStr);
    downloadAnchorNode.setAttribute('download', filename);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };
  return (
    <button onClick={handleExport} data-testid="export-plan-btn" style={{ marginTop: 12, background: '#2196F3', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 4 }}>
      Export Plan
    </button>
  );
};
