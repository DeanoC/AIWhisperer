import React from 'react';

export interface PlanTask {
  description: string;
  status: string;
}

export interface PlanPreviewProps {
  plan: {
    tasks: PlanTask[];
    format: string;
  };
}

export const PlanPreview: React.FC<PlanPreviewProps> = ({ plan }) => {
  const [expanded, setExpanded] = React.useState<boolean[]>(
    plan && plan.tasks ? plan.tasks.map(() => false) : []
  );
  if (!plan || !plan.tasks) return <div>No plan available.</div>;
  const toggle = (idx: number) => {
    setExpanded(expanded => expanded.map((v, i) => (i === idx ? !v : v)));
  };
  return (
    <div className="plan-preview">
      <h3>Plan Preview</h3>
      <ul>
        {plan.tasks.map((task, idx) => (
          <li key={idx}>
            <span
              style={{ cursor: 'pointer', fontWeight: expanded[idx] ? 'bold' : 'normal' }}
              onClick={() => toggle(idx)}
              data-testid={`plan-task-${idx}`}
            >
              {task.description}
            </span>
            <span style={{ marginLeft: 8, color: '#888', fontSize: 12 }}>({task.status})</span>
            {expanded[idx] && (
              <div style={{ marginTop: 4, fontSize: 12, color: '#444' }}>
                {/* Placeholder for expanded details */}
                Task details for: {task.description}
              </div>
            )}
          </li>
        ))}
      </ul>
      <div style={{ fontSize: 12, color: '#666' }}>Format: {plan.format}</div>
    </div>
  );
};
