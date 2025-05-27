import { render, screen } from '@testing-library/react';
import { AgentAvatar } from './AgentAvatar';

describe('AgentAvatar', () => {
  const agent = {
    agentId: 'P',
    name: 'Patricia the Planner',
    description: 'Creates structured implementation plans',
    color: '#4CAF50',
    shortcut: '[P]'
  };

  it('renders the first letter of the agent name', () => {
    render(<AgentAvatar agent={agent} />);
    expect(screen.getByTestId('agent-avatar-P')).toHaveTextContent('P');
  });

  it('applies the agent color as background', () => {
    render(<AgentAvatar agent={agent} />);
    const avatar = screen.getByTestId('agent-avatar-P');
    expect(avatar).toHaveStyle('background-color: #4CAF50');
  });

  it('sets the correct size', () => {
    render(<AgentAvatar agent={agent} size={40} />);
    const avatar = screen.getByTestId('agent-avatar-P');
    expect(avatar).toHaveStyle('width: 40px');
    expect(avatar).toHaveStyle('height: 40px');
  });
});
