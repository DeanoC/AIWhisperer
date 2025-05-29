import { render, screen } from '@testing-library/react';
import { CurrentAgentDisplay } from './CurrentAgentDisplay';

describe('CurrentAgentDisplay', () => {
  const agent = {
    id: 'P',
    name: 'Patricia the Planner',
    role: 'planner',
    description: 'Creates structured implementation plans',
    color: '#4CAF50',
    shortcut: '[P]'
  };

  it('renders the agent avatar and name', () => {
    render(<CurrentAgentDisplay agent={agent} />);
    expect(screen.getByText('Patricia the Planner')).toBeInTheDocument();
    expect(screen.getByText('Creates structured implementation plans')).toBeInTheDocument();
    expect(screen.getByTestId('agent-avatar-P')).toBeInTheDocument();
  });

  it('renders no agent selected when agent is null', () => {
    render(<CurrentAgentDisplay agent={null} />);
    expect(screen.getByText('No agent selected')).toBeInTheDocument();
  });
});
