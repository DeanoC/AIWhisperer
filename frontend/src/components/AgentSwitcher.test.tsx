import { render, screen, fireEvent } from '@testing-library/react';
import { AgentSwitcher } from './AgentSwitcher';

describe('AgentSwitcher', () => {
  const agents = [
    {
      agentId: 'P',
      name: 'Patricia the Planner',
      description: 'Creates structured implementation plans',
      color: '#4CAF50',
      shortcut: '[P]'
    },
    {
      agentId: 'T',
      name: 'Tessa the Tester',
      description: 'Generates comprehensive test suites',
      color: '#2196F3',
      shortcut: '[T]'
    }
  ];
  it('renders all agent avatars', () => {
    render(<AgentSwitcher agents={agents} currentAgent={agents[0]} onSwitch={() => {}} />);
    expect(screen.getByTestId('switch-agent-P')).toBeInTheDocument();
    expect(screen.getByTestId('switch-agent-T')).toBeInTheDocument();
  });
  it('highlights the selected agent', () => {
    render(<AgentSwitcher agents={agents} currentAgent={agents[1]} onSwitch={() => {}} />);
    const tessaBtn = screen.getByTestId('switch-agent-T');
    expect(tessaBtn.className).toContain('selected');
  });
  it('calls onSwitch when an agent is clicked', () => {
    const onSwitch = jest.fn();
    render(<AgentSwitcher agents={agents} currentAgent={agents[0]} onSwitch={onSwitch} />);
    fireEvent.click(screen.getByTestId('switch-agent-T'));
    expect(onSwitch).toHaveBeenCalledWith('T');
  });
});
