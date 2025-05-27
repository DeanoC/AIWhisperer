import React from 'react';
import { render } from '@testing-library/react';
import { AgentTransition } from './AgentTransition';

describe('AgentTransition', () => {
  it('renders nothing when show is false', () => {
    const { container } = render(<AgentTransition fromAgent="Patricia" toAgent="Tessa" show={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders transition message when show is true', () => {
    const { getByText } = render(<AgentTransition fromAgent="Patricia" toAgent="Tessa" show={true} />);
    expect(getByText(/Switching from/)).toBeInTheDocument();
    expect(getByText(/Patricia/)).toBeInTheDocument();
    expect(getByText(/Tessa/)).toBeInTheDocument();
  });
});
