import { render, screen, fireEvent } from '@testing-library/react';
import { AgentSelector } from './AgentSelector';

describe('AgentSelector', () => {
  const agents = [
    {
      id: 'P',
      name: 'Patricia the Planner',
      description: 'Creates structured implementation plans',
      color: '#4CAF50',
      shortcut: '[P]',
      role: 'planner'
    },
    {
      id: 'T',
      name: 'Tessa the Tester',
      description: 'Generates comprehensive test suites',
      color: '#2196F3',
      shortcut: '[T]',
      role: 'tester'
    }
  ];

  it('renders agent list', () => {
    render(<AgentSelector agents={agents} currentAgent={agents[0]} onAgentSelect={() => {}} />);
    expect(screen.getByText('Patricia the Planner')).toBeInTheDocument();
    expect(screen.getByText('Tessa the Tester')).toBeInTheDocument();
  });

  it('highlights the current agent', () => {
    render(<AgentSelector agents={agents} currentAgent={agents[1]} onAgentSelect={() => {}} />);
    const tessa = screen.getByText('Tessa the Tester');
    expect(tessa.parentElement).toHaveClass('selected');
  });

  it('calls onAgentSelect when an agent is clicked', () => {
    const onSelect = jest.fn();
    render(<AgentSelector agents={agents} currentAgent={agents[0]} onAgentSelect={onSelect} />);
    fireEvent.click(screen.getByText('Tessa the Tester'));
    expect(onSelect).toHaveBeenCalledWith('T');
  });

  it('displays keyboard shortcuts', () => {
    render(<AgentSelector agents={agents} currentAgent={agents[0]} onAgentSelect={() => {}} />);
    expect(screen.getByText('[P]')).toBeInTheDocument();
    expect(screen.getByText('[T]')).toBeInTheDocument();
  });

  it('toggles compact mode', () => {
    const onCompactChange = jest.fn();
    render(
      <AgentSelector 
        agents={agents} 
        currentAgent={agents[0]} 
        onAgentSelect={() => {}} 
        onCompactChange={onCompactChange}
      />
    );
    
    // Should start in expanded mode (check for agent names)
    expect(screen.getByText('Patricia the Planner')).toBeInTheDocument();
    
    // Click compact toggle
    const compactToggle = screen.getByTitle('Compact view');
    fireEvent.click(compactToggle);
    
    // Should now be in compact mode (no agent names visible)
    expect(screen.queryByText('Patricia the Planner')).not.toBeInTheDocument();
    expect(onCompactChange).toHaveBeenCalledWith(true);
    
    // But should still have agent avatars
    expect(screen.getByTestId('agent-P-compact')).toBeInTheDocument();
  });
});
